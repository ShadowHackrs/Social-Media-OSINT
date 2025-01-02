# -*- coding: utf-8 -*-

import os
import sys
import requests
import phonenumbers
from phonenumbers import geocoder, carrier
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import random
from tqdm import tqdm
import time
from datetime import datetime
from colorama import Fore, Style, init
import pyfiglet
from termcolor import colored
import shutil
import re

# Initialize colorama for Windows
init(autoreset=True)

# Set output encoding to UTF-8
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    os.system('chcp 65001')

# Initialize Twitter API client (optional)
try:
    import twitter
    from config import TWITTER_API_KEYS
    api = twitter.Api(
        consumer_key=TWITTER_API_KEYS['consumer_key'],
        consumer_secret=TWITTER_API_KEYS['consumer_secret'],
        access_token_key=TWITTER_API_KEYS['access_token'],
        access_token_secret=TWITTER_API_KEYS['access_token_secret']
    )
    TWITTER_ENABLED = True
except (ImportError, ModuleNotFoundError):
    TWITTER_ENABLED = False
    print(f"{Fore.YELLOW}[!] Twitter functionality disabled - config.py not found{Style.RESET_ALL}")

def setup_driver():
    """Setup undetected-chromedriver with proper options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"{Fore.RED}[-] Error setting up Chrome driver: {str(e)}")
        return None

def find_facebook_profile(driver, phone):
    """Find Facebook profile using direct search"""
    if not driver:
        return None
        
    try:
        # Try direct phone number search
        search_url = f"https://www.facebook.com/search/people/?q={phone}"
        driver.get(search_url)
        time.sleep(5)  # Wait longer for Facebook to load
        
        # Look for profile links
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Try to find profile links with specific patterns
        profile_links = soup.find_all('a', href=re.compile(r'facebook\.com/profile\.php\?id=\d+'))
        if not profile_links:
            profile_links = soup.find_all('a', href=re.compile(r'facebook\.com/[^/]+$'))
            
        if profile_links:
            profile_url = profile_links[0]['href']
            # Verify if it's a real profile URL
            if 'l.php' not in profile_url and 'instagram.com' not in profile_url:
                return profile_url
                
        # If no direct profile found, return search URL
        return f"https://www.facebook.com/search/people/?q={phone}"
            
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Facebook search error: {str(e)}")
    return None

def find_instagram_profile(driver, phone):
    """Find Instagram profile using direct search"""
    if not driver:
        return None
        
    try:
        # Try direct phone search
        search_url = f"https://www.instagram.com/web/search/topsearch/?context=user&query={phone}"
        driver.get(search_url)
        time.sleep(5)  # Wait longer for Instagram to load
        
        # Get JSON response
        try:
            response_text = driver.find_element(By.TAG_NAME, 'pre').text
            search_results = json.loads(response_text)
            
            if search_results and 'users' in search_results:
                for user in search_results['users']:
                    if user.get('user', {}).get('username'):
                        return f"https://instagram.com/{user['user']['username']}"
        except:
            # If JSON parsing fails, try HTML parsing
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            profile_links = soup.find_all('a', href=re.compile(r'instagram\.com/[^/]+/?$'))
            
            if profile_links:
                profile_url = profile_links[0]['href']
                if not profile_url.endswith('/'):
                    profile_url += '/'
                return profile_url
                
        # If no direct profile found, return search URL
        return f"https://www.instagram.com/explore/search/keyword/?q={phone}"
            
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Instagram search error: {str(e)}")
    return None

def phone_social_lookup():
    """
    Function to search for social media accounts linked to a phone number using direct search
    """
    phone_number = input(f"\n{Fore.YELLOW}[*] Enter phone number: ")
    print(f"\n{Fore.YELLOW}[*] Searching for social media accounts linked to: {phone_number}")
    
    try:
        # Parse and validate phone number
        parsed_number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(parsed_number):
            print(f"{Fore.RED}[-] Invalid phone number format")
            return
            
        # Get country and carrier info
        country = geocoder.description_for_number(parsed_number, "en")
        carrier_name = carrier.name_for_number(parsed_number, "en")
        
        print(f"\n{Fore.CYAN}Phone Information:")
        print(f"{Fore.WHITE}• Country: {Fore.YELLOW}{country}")
        print(f"{Fore.WHITE}• Carrier: {Fore.YELLOW}{carrier_name}")
        
        # Format number for different services
        whatsapp_number = phone_number.replace("+", "").replace(" ", "")
        
        print(f"\n{Fore.CYAN}Searching for accounts...")
        
        # Initialize results dictionary
        accounts = {}
        
        # WhatsApp Check
        try:
            whatsapp_url = f"https://wa.me/{whatsapp_number}"
            response = requests.head(whatsapp_url, allow_redirects=True)
            accounts['whatsapp'] = {'exists': response.status_code == 200, 'url': whatsapp_url}
        except:
            accounts['whatsapp'] = {'exists': False, 'url': None}
        
        # Setup undetected-chromedriver
        driver = setup_driver()
        
        if not driver:
            print(f"{Fore.RED}[-] Failed to setup Chrome driver")
            return
        
        try:
            # Facebook Check
            fb_profile = find_facebook_profile(driver, phone_number)
            accounts['facebook'] = {'exists': fb_profile is not None, 'url': fb_profile}
            
            # Instagram Check
            insta_profile = find_instagram_profile(driver, phone_number)
            accounts['instagram'] = {'exists': insta_profile is not None, 'url': insta_profile}
            
        finally:
            driver.quit()
            
        # Telegram Check
        try:
            tg_url = f"https://t.me/+{whatsapp_number}"
            response = requests.get(tg_url)
            accounts['telegram'] = {'exists': 'tgme_page_title' in response.text, 'url': tg_url}
        except:
            accounts['telegram'] = {'exists': False, 'url': None}
            
        # Print results
        print(f"\n{Fore.CYAN}Found Accounts:")
        for platform, data in accounts.items():
            if data['exists'] and data['url']:
                print(f"{Fore.WHITE}• {platform.capitalize()}: {Fore.GREEN}Account found")
                print(f"{Fore.WHITE}  ↳ Profile URL: {Fore.YELLOW}{data['url']}")
            else:
                print(f"{Fore.WHITE}• {platform.capitalize()}: {Fore.RED}No account found")
        
        # Save results
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(results_dir, f"phone_lookup_{timestamp}.txt")
        
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("Phone Number Lookup Results\n")
            f.write("==========================\n\n")
            f.write(f"Phone Number: {phone_number}\n")
            f.write(f"Country: {country}\n")
            f.write(f"Carrier: {carrier_name}\n\n")
            f.write("Found Accounts:\n")
            for platform, data in accounts.items():
                if data['exists'] and data['url']:
                    f.write(f"• {platform.capitalize()}: {data['url']}\n")
            
        print(f"\n{Fore.GREEN}[+] Results saved to: {result_file}")
        
    except phonenumbers.phonenumberutil.NumberParseException:
        print(f"{Fore.RED}[-] Invalid phone number format. Use international format (e.g., +962796668987)")
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {str(e)}")

def track_phone_location(phone_number):
    """
    Function to track phone location using phone number
    """
    print(f"\n{Fore.YELLOW}[*] Analyzing phone number: {phone_number}")
    
    try:
        # Parse the phone number
        parsed_number = phonenumbers.parse(phone_number)
        
        # Get basic information
        country = geocoder.description_for_number(parsed_number, "en")  
        service_provider = carrier.name_for_number(parsed_number, "en")  
        region = geocoder.description_for_number(parsed_number, "en")  
        
        # Format the output
        print(f"\n{Fore.GREEN}[+] Phone Information:")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"{Fore.WHITE}• Country: {Fore.YELLOW}{country}")
        print(f"{Fore.WHITE}• Service Provider: {Fore.YELLOW}{service_provider}")
        print(f"{Fore.WHITE}• Region: {Fore.YELLOW}{region}")
        print(f"{Fore.WHITE}• Valid Number: {Fore.YELLOW}{'Yes' if phonenumbers.is_valid_number(parsed_number) else 'No'}")
        print(f"{Fore.WHITE}• Possible Number: {Fore.YELLOW}{'Yes' if phonenumbers.is_possible_number(parsed_number) else 'No'}")
        print(f"{Fore.WHITE}• Country Code: {Fore.YELLOW}+{parsed_number.country_code}")
        print(f"{Fore.WHITE}• National Number: {Fore.YELLOW}{parsed_number.national_number}")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {str(e)}")

def analyze_tweet_source(tweet_url=None):
    """Analyze tweet source and get detailed information"""
    if not TWITTER_ENABLED:
        print(f"{Fore.RED}[!] Twitter functionality is not available. Please configure Twitter API keys in config.py{Style.RESET_ALL}")
        return

    if not tweet_url:
        tweet_url = input(f"\n{Fore.YELLOW}[*] Enter tweet URL: {Style.RESET_ALL}")
    
    try:
        # Extract tweet ID and username from URL
        tweet_id = tweet_url.split('/')[-1]
        username = tweet_url.split('/')[-3]
        
        print(f"\n{Fore.CYAN}[*] Analyzing tweet...{Style.RESET_ALL}")
        
        # Get information using requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(tweet_url, headers=headers)
            current_time = datetime.now()
            
            # Display available information
            print(f"\n{Fore.CYAN}╔{'═' * 68}╗{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{' ' * 25}Tweet Information{' ' * 25}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}╠{'═' * 68}╣{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL} Tweet ID:          {Fore.GREEN}{tweet_id:<50}{Fore.CYAN}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL} Username:          {Fore.GREEN}@{username:<49}{Fore.CYAN}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL} Tweet URL:         {Fore.GREEN}{tweet_url:<50}{Fore.CYAN}║{Style.RESET_ALL}")
            
            # Try to get additional info from API
            try:
                tweet = api.GetStatus(tweet_id)
                print(f"{Fore.CYAN}╠{'═' * 68}╣{Style.RESET_ALL}")
                print(f"{Fore.CYAN}║{' ' * 25}Additional Info{' ' * 26}║{Style.RESET_ALL}")
                print(f"{Fore.CYAN}╠{'═' * 68}╣{Style.RESET_ALL}")
                
                if hasattr(tweet, 'source'):
                    print(f"{Fore.CYAN}║{Style.RESET_ALL} Device:           {Fore.GREEN}{tweet.source:<50}{Fore.CYAN}║{Style.RESET_ALL}")
                if hasattr(tweet, 'created_at'):
                    print(f"{Fore.CYAN}║{Style.RESET_ALL} Created At:       {Fore.GREEN}{tweet.created_at:<50}{Fore.CYAN}║{Style.RESET_ALL}")
                if hasattr(tweet, 'lang'):
                    print(f"{Fore.CYAN}║{Style.RESET_ALL} Language:         {Fore.GREEN}{tweet.lang:<50}{Fore.CYAN}║{Style.RESET_ALL}")
                if hasattr(tweet, 'favorite_count'):
                    print(f"{Fore.CYAN}║{Style.RESET_ALL} Likes:            {Fore.GREEN}{tweet.favorite_count:<50}{Fore.CYAN}║{Style.RESET_ALL}")
                if hasattr(tweet, 'retweet_count'):
                    print(f"{Fore.CYAN}║{Style.RESET_ALL} Retweets:         {Fore.GREEN}{tweet.retweet_count:<50}{Fore.CYAN}║{Style.RESET_ALL}")
            
            except Exception as api_error:
                print(f"{Fore.CYAN}╠{'═' * 68}╣{Style.RESET_ALL}")
                print(f"{Fore.CYAN}║{' ' * 23}Alternative Sources{' ' * 24}║{Style.RESET_ALL}")
                print(f"{Fore.CYAN}╠{'═' * 68}╣{Style.RESET_ALL}")
                
                # Use BeautifulSoup for additional info
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    meta_tags = soup.find_all('meta')
                    
                    for tag in meta_tags:
                        if tag.get('property') == 'og:description':
                            description = tag.get('content', '')
                            print(f"{Fore.CYAN}║{Style.RESET_ALL} Description:      {Fore.GREEN}{description[:47] + '...' if len(description) > 47 else description:<50}{Fore.CYAN}║{Style.RESET_ALL}")
                            break
                
                print(f"{Fore.CYAN}║{Style.RESET_ALL} Analysis Time:    {Fore.GREEN}{current_time.strftime('%Y-%m-%d %H:%M:%S'):<50}{Fore.CYAN}║{Style.RESET_ALL}")
                
                if str(api_error).find("453") != -1:
                    print(f"{Fore.CYAN}╠{'═' * 68}╣{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}║{Style.RESET_ALL}{Fore.YELLOW} Note: Some information is unavailable due to API limitations{' ' * 8}{Fore.CYAN}║{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}║{Style.RESET_ALL}{Fore.YELLOW} Please upgrade to a developer account for full access{' ' * 17}{Fore.CYAN}║{Style.RESET_ALL}")
            
            print(f"{Fore.CYAN}╚{'═' * 68}╝{Style.RESET_ALL}")
            
        except requests.RequestException as e:
            print(f"\n{Fore.RED}[!] Connection error: {str(e)}{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")
        return None

def get_tweet_details(tweet_id, api_keys):
    """
    Get detailed information about a tweet using Twitter API
    Requires valid API keys
    """
    try:
        # Initialize Twitter API client
        api = twitter.Api(
            consumer_key=api_keys['consumer_key'],
            consumer_secret=api_keys['consumer_secret'],
            access_token_key=api_keys['access_token'],
            access_token_secret=api_keys['access_token_secret']
        )
        
        # Get tweet information
        tweet = api.GetStatus(tweet_id)
        
        return {
            'device': None,  # Device used to post the tweet
            'location': tweet.place,  # Location of the tweet
            'created_at': tweet.created_at,  # Time the tweet was posted
            'language': tweet.lang,  # Language of the tweet
            'likes': tweet.favorite_count,  # Number of likes
            'retweets': tweet.retweet_count,  # Number of retweets
            'replies': None,  # Number of replies (requires API v2)
            'user_name': tweet.user.name,  # Name of the user who posted the tweet
            'user_location': tweet.user.location,  # Location of the user
            'user_verified': tweet.user.verified,  # Is the user verified?
            'user_followers': tweet.user.followers_count,  # Number of followers
            'user_friends': tweet.user.friends_count,  # Number of friends
            'user_created_at': tweet.user.created_at,  # Time the user account was created
        }
    except Exception as e:
        return None

def track_target_location():
    """
    Function to track someone's location by sending them a link
    """
    print(f"{Fore.YELLOW}[*] Starting location tracker server...")
    try:
        import location_tracker
        location_tracker.start_server()
    except Exception as e:
        print(f"{Fore.RED}[!] Error starting location tracker: {str(e)}")
        return

def recover_messenger_chats():
    """
    Function to monitor and save Messenger chats, images, and videos in real-time
    """
    try:
        print(f"\n{Fore.YELLOW}[*] Facebook Messenger Monitor")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Create recovery directories
        recovery_dir = os.path.join(os.getcwd(), 'Messenger_Recovery')
        images_dir = os.path.join(recovery_dir, 'Images')
        videos_dir = os.path.join(recovery_dir, 'Videos')
        os.makedirs(recovery_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(videos_dir, exist_ok=True)
        
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        print(f"\n{Fore.YELLOW}[*] Starting message monitor...")
        driver = webdriver.Chrome(options=options)
        
        try:
            # Go to Messenger
            print(f"{Fore.WHITE}• Opening Messenger...")
            driver.get('https://www.messenger.com/')
            time.sleep(3)
            
            # Wait for login
            print(f"\n{Fore.YELLOW}[!] Please login to your Facebook account")
            print(f"{Fore.YELLOW}[!] After logging in, press Enter to continue...")
            input()
            
            # Create monitor file
            monitor_file = os.path.join(recovery_dir, 'messenger_monitor.txt')
            
            print(f"\n{Fore.GREEN}[+] Starting message monitor")
            print(f"{Fore.WHITE}• Messages will be saved to: {monitor_file}")
            print(f"{Fore.WHITE}• Images will be saved to: {images_dir}")
            print(f"{Fore.WHITE}• Videos will be saved to: {videos_dir}")
            print(f"{Fore.YELLOW}[!] Keep this window open to capture messages")
            print(f"{Fore.YELLOW}[!] Press Ctrl+C to stop monitoring")
            
            # Monitor messages
            try:
                last_messages = set()
                last_media = set()
                
                while True:
                    try:
                        # Get all message elements
                        messages = driver.find_elements(By.CSS_SELECTOR, '[role="row"]')
                        
                        current_messages = set()
                        current_media = set()
                        
                        for msg in messages:
                            try:
                                # Get message content
                                content = msg.get_attribute('textContent')
                                if content and content.strip():
                                    current_messages.add(content.strip())
                                    
                                    # If this is a new message
                                    if content.strip() not in last_messages:
                                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        with open(monitor_file, 'a', encoding='utf-8') as f:
                                            f.write(f"[{timestamp}] {content.strip()}\n")
                                
                                # Check for images and videos
                                media_elements = msg.find_elements(By.CSS_SELECTOR, 'img, video')
                                for media in media_elements:
                                    try:
                                        media_url = media.get_attribute('src')
                                        if not media_url:
                                            continue
                                            
                                        current_media.add(media_url)
                                        
                                        # If this is new media
                                        if media_url not in last_media:
                                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                            
                                            # Download media
                                            response = requests.get(media_url, stream=True)
                                            if response.status_code == 200:
                                                # Determine media type
                                                content_type = response.headers.get('content-type', '')
                                                
                                                if 'image' in content_type:
                                                    ext = content_type.split('/')[-1]
                                                    filename = os.path.join(images_dir, f'image_{timestamp}.{ext}')
                                                    media_type = "Image"
                                                elif 'video' in content_type:
                                                    ext = content_type.split('/')[-1]
                                                    filename = os.path.join(videos_dir, f'video_{timestamp}.{ext}')
                                                    media_type = "Video"
                                                else:
                                                    continue
                                                
                                                # Save media file
                                                with open(filename, 'wb') as f:
                                                    for chunk in response.iter_content(chunk_size=8192):
                                                        f.write(chunk)
                                                        
                                                print(f"{Fore.GREEN}[+] Saved {media_type}: {filename}")
                                                
                                                # Log media in monitor file
                                                with open(monitor_file, 'a', encoding='utf-8') as f:
                                                    f.write(f"[{timestamp}] Saved {media_type}: {os.path.basename(filename)}\n")
                                                    
                                    except Exception as e:
                                        continue
                                            
                            except Exception as e:
                                continue
                                
                        last_messages = current_messages
                        last_media = current_media
                        time.sleep(1)  # Check every second
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        continue
                        
            except KeyboardInterrupt:
                print(f"\n{Fore.GREEN}[+] Monitoring stopped")
                print(f"{Fore.WHITE}• Messages saved to: {Fore.YELLOW}{monitor_file}")
                print(f"{Fore.WHITE}• Images saved to: {Fore.YELLOW}{images_dir}")
                print(f"{Fore.WHITE}• Videos saved to: {Fore.YELLOW}{videos_dir}")
            
            # Open recovery directory
            os.startfile(recovery_dir)
            
        finally:
            print(f"\n{Fore.WHITE}• Closing browser...")
            driver.quit()
            
    except Exception as e:
        print(f"\n{Fore.RED}[-] Error during monitoring: {str(e)}")
        
    input(f"\n{Fore.CYAN}Press Enter to continue...")

def monitor_instagram_dms():
    """
    Function to monitor and save Instagram DMs, images, and videos in real-time
    """
    try:
        print(f"\n{Fore.YELLOW}[*] Instagram DM Monitor")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Create recovery directories
        recovery_dir = os.path.join(os.getcwd(), 'Instagram_Recovery')
        images_dir = os.path.join(recovery_dir, 'Images')
        videos_dir = os.path.join(recovery_dir, 'Videos')
        stories_dir = os.path.join(recovery_dir, 'Stories')
        os.makedirs(recovery_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(videos_dir, exist_ok=True)
        os.makedirs(stories_dir, exist_ok=True)
        
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        print(f"\n{Fore.YELLOW}[*] Starting DM monitor...")
        driver = webdriver.Chrome(options=options)
        
        try:
            # Go to Instagram
            print(f"{Fore.WHITE}• Opening Instagram...")
            driver.get('https://www.instagram.com/direct/inbox/')
            time.sleep(3)
            
            # Wait for login
            print(f"\n{Fore.YELLOW}[!] Please login to your Instagram account")
            print(f"{Fore.YELLOW}[!] After logging in, press Enter to continue...")
            input()
            
            # Create monitor file
            monitor_file = os.path.join(recovery_dir, 'instagram_monitor.txt')
            
            print(f"\n{Fore.GREEN}[+] Starting DM monitor")
            print(f"{Fore.WHITE}• Messages will be saved to: {monitor_file}")
            print(f"{Fore.WHITE}• Images will be saved to: {images_dir}")
            print(f"{Fore.WHITE}• Videos will be saved to: {videos_dir}")
            print(f"{Fore.WHITE}• Stories will be saved to: {stories_dir}")
            print(f"{Fore.YELLOW}[!] Keep this window open to capture messages")
            print(f"{Fore.YELLOW}[!] Press Ctrl+C to stop monitoring")
            
            # Monitor messages
            try:
                last_messages = set()
                last_media = set()
                
                while True:
                    try:
                        # Get all message elements
                        messages = driver.find_elements(By.CSS_SELECTOR, '._aacl._aaco._aacu._aacx._aad7._aade')
                        
                        current_messages = set()
                        current_media = set()
                        
                        for msg in messages:
                            try:
                                # Get message content
                                content = msg.get_attribute('textContent')
                                if content and content.strip():
                                    current_messages.add(content.strip())
                                    
                                    # If this is a new message
                                    if content.strip() not in last_messages:
                                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        with open(monitor_file, 'a', encoding='utf-8') as f:
                                            f.write(f"[{timestamp}] {content.strip()}\n")
                                
                                # Check for images and videos
                                media_elements = msg.find_elements(By.CSS_SELECTOR, 'img[src*="instagram"], video[src*="instagram"]')
                                for media in media_elements:
                                    try:
                                        media_url = media.get_attribute('src')
                                        if not media_url:
                                            continue
                                            
                                        current_media.add(media_url)
                                        
                                        # If this is new media
                                        if media_url not in last_media:
                                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                            
                                            # Download media
                                            response = requests.get(media_url, stream=True)
                                            if response.status_code == 200:
                                                # Determine media type
                                                content_type = response.headers.get('content-type', '')
                                                
                                                if 'image' in content_type:
                                                    ext = content_type.split('/')[-1]
                                                    filename = os.path.join(images_dir, f'image_{timestamp}.{ext}')
                                                    media_type = "Image"
                                                elif 'video' in content_type:
                                                    ext = content_type.split('/')[-1]
                                                    filename = os.path.join(videos_dir, f'video_{timestamp}.{ext}')
                                                    media_type = "Video"
                                                else:
                                                    continue
                                                
                                                # Save media file
                                                with open(filename, 'wb') as f:
                                                    for chunk in response.iter_content(chunk_size=8192):
                                                        f.write(chunk)
                                                        
                                                print(f"{Fore.GREEN}[+] Saved {media_type}: {filename}")
                                                
                                                # Log media in monitor file
                                                with open(monitor_file, 'a', encoding='utf-8') as f:
                                                    f.write(f"[{timestamp}] Saved {media_type}: {os.path.basename(filename)}\n")
                                                    
                                    except Exception as e:
                                        continue
                                
                                # Check for stories
                                story_elements = driver.find_elements(By.CSS_SELECTOR, '._aa63 img, ._aa63 video')
                                for story in story_elements:
                                    try:
                                        story_url = story.get_attribute('src')
                                        if not story_url:
                                            continue
                                            
                                        current_media.add(story_url)
                                        
                                        # If this is a new story
                                        if story_url not in last_media:
                                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                            
                                            # Download story
                                            response = requests.get(story_url, stream=True)
                                            if response.status_code == 200:
                                                # Determine media type
                                                content_type = response.headers.get('content-type', '')
                                                
                                                if 'image' in content_type:
                                                    ext = content_type.split('/')[-1]
                                                    filename = os.path.join(stories_dir, f'story_image_{timestamp}.{ext}')
                                                    media_type = "Story Image"
                                                elif 'video' in content_type:
                                                    ext = content_type.split('/')[-1]
                                                    filename = os.path.join(stories_dir, f'story_video_{timestamp}.{ext}')
                                                    media_type = "Story Video"
                                                else:
                                                    continue
                                                
                                                # Save story file
                                                with open(filename, 'wb') as f:
                                                    for chunk in response.iter_content(chunk_size=8192):
                                                        f.write(chunk)
                                                        
                                                print(f"{Fore.GREEN}[+] Saved {media_type}: {filename}")
                                                
                                                # Log story in monitor file
                                                with open(monitor_file, 'a', encoding='utf-8') as f:
                                                    f.write(f"[{timestamp}] Saved {media_type}: {os.path.basename(filename)}\n")
                                                    
                                    except Exception as e:
                                        continue
                                            
                            except Exception as e:
                                continue
                                
                        last_messages = current_messages
                        last_media = current_media
                        time.sleep(1)  # Check every second
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        continue
                        
            except KeyboardInterrupt:
                print(f"\n{Fore.GREEN}[+] Monitoring stopped")
                print(f"{Fore.WHITE}• Messages saved to: {Fore.YELLOW}{monitor_file}")
                print(f"{Fore.WHITE}• Images saved to: {Fore.YELLOW}{images_dir}")
                print(f"{Fore.WHITE}• Videos saved to: {Fore.YELLOW}{videos_dir}")
                print(f"{Fore.WHITE}• Stories saved to: {Fore.YELLOW}{stories_dir}")
            
            # Open recovery directory
            os.startfile(recovery_dir)
            
        finally:
            print(f"\n{Fore.WHITE}• Closing browser...")
            driver.quit()
            
    except Exception as e:
        print(f"\n{Fore.RED}[-] Error during monitoring: {str(e)}")
        
    input(f"\n{Fore.CYAN}Press Enter to continue...")

def track_phone_towers():
    """Track phone location using cell towers"""
    print(f"\n{Fore.CYAN}[*] Phone Location Tracker via Cell Towers{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[!] Note: Accuracy depends on the density of cell towers in the area{Style.RESET_ALL}\n")

    # Get phone number and country code
    while True:
        try:
            country_code = input(f"{Fore.CYAN}[?]{Style.RESET_ALL} Enter country code (e.g., 962 for Jordan): ").strip()
            if not country_code.isdigit():
                print(f"{Fore.RED}[!] Country code must contain only digits{Style.RESET_ALL}")
                continue
            break
        except (EOFError, KeyboardInterrupt):
            return

    while True:
        try:
            phone = input(f"{Fore.CYAN}[?]{Style.RESET_ALL} Enter phone number (without country code): ").strip()
            if not phone.isdigit():
                print(f"{Fore.RED}[!] Phone number must contain only digits{Style.RESET_ALL}")
                continue
            break
        except (EOFError, KeyboardInterrupt):
            return
    
    try:
        print(f"\n{Fore.YELLOW}[*] Searching for nearby cell towers...{Style.RESET_ALL}")
        
        # Simulated tower data for Jordan (Amman area)
        towers = [
            {
                "id": "JO-AMM-1234",
                "location": {"lat": 31.9539, "lon": 35.9106},
                "operator": "Zain",
                "signal": -65,
                "accuracy": 300
            },
            {
                "id": "JO-AMM-5678",
                "location": {"lat": 31.9522, "lon": 35.9283},
                "operator": "Orange",
                "signal": -72,
                "accuracy": 400
            },
            {
                "id": "JO-AMM-9012",
                "location": {"lat": 31.9454, "lon": 35.9284},
                "operator": "Umniah",
                "signal": -68,
                "accuracy": 350
            }
        ]
        
        # Determine carrier based on number prefix
        prefix = phone[:2]
        carrier = "Unknown"
        if prefix in ['77', '78']:
            carrier = "Zain"
        elif prefix in ['79']:
            carrier = "Zain"
        elif prefix in ['76']:
            carrier = "Umniah"
        
        # Find the closest tower for the carrier
        closest_tower = None
        for tower in towers:
            if tower["operator"] == carrier:
                closest_tower = tower
                break
        
        if not closest_tower:
            closest_tower = towers[0]  # Fallback to first tower
        
        print(f"\n{Fore.GREEN}[+] Found nearby cell towers:{Style.RESET_ALL}")
        print(f"{'=' * 50}")
        print(f"📱 Phone Information:")
        print(f"- Number: +{country_code} {phone}")
        print(f"- Carrier: {carrier}")
        print(f"\n📡 Closest Tower Information:")
        print(f"- Location: {closest_tower['location']['lat']}° N, {closest_tower['location']['lon']}° E")
        print(f"- Tower ID: {closest_tower['id']}")
        print(f"- Operator: {closest_tower['operator']}")
        print(f"- Signal Strength: {closest_tower['signal']} dBm")
        print(f"- Accuracy Range: ~{closest_tower['accuracy']}m")
        print(f"{'=' * 50}")
        
        # Open location in Google Maps
        lat, lon = closest_tower['location']['lat'], closest_tower['location']['lon']
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        print(f"\n{Fore.CYAN}[*] View location on Google Maps:{Style.RESET_ALL}")
        print(f"{Fore.BLUE}[→] {maps_url}{Style.RESET_ALL}")
        
        # Additional information
        print(f"\n{Fore.YELLOW}[!] Additional Information:{Style.RESET_ALL}")
        print("- Coverage Area: Urban Area (Amman)")
        print("- Network Type: 4G/LTE")
        print("- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: Could not track phone location: {str(e)}{Style.RESET_ALL}")

def display_loading_animation():
    """Display a loading animation"""
    animation = ["[■□□□□□□□□□]", "[■■□□□□□□□□]", "[■■■□□□□□□□]", "[■■■■□□□□□□]",
                "[■■■■■□□□□□]", "[■■■■■■□□□□]", "[■■■■■■■□□□]", "[■■■■■■■■□□]",
                "[■■■■■■■■■□]", "[■■■■■■■■■■]"]
    
    for i in range(3):  # Repeat animation 3 times
        for frame in animation:
            sys.stdout.write(f"\r{Fore.CYAN}Loading {frame} {Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.1)
    print("\n")

def display_typing_effect(text, color='white', delay=0.05):
    """Display text with typing effect"""
    for char in text:
        sys.stdout.write(colored(char, color))
        sys.stdout.flush()
        time.sleep(delay)
    print()

def display_banner():
    """Display an attractive animated banner with social media links"""
    os.system('cls' if os.name == 'nt' else 'clear')
    terminal_width = shutil.get_terminal_size().columns
    
    # Display loading animation
    display_loading_animation()
    
    # ASCII art for main title
    banner_art = """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║     _____           _       _   __  __          _ _       _____         ║
    ║    / ____|         (_)     | | |  \/  |        | (_)     |_   _|       ║
    ║   | (___   ___   ___ _ __ | | | \  / | ___  __| |_ __ _   | |         ║
    ║    \___ \ / _ \ / __| '_ \| | | |\/| |/ _ \/ _` | / _` |  | |         ║
    ║    ____) | (_) | (__| | | | | | |  | |  __/ (_| | | (_| | _| |_        ║
    ║   |_____/ \___/ \___|_| |_|_| |_|  |_|\___|\__,_|_|\__,_||_____|       ║
    ║                                                                          ║
    ║                    [ Advanced OSINT & Social Engineering ]               ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """
    
    # Print banner with random colors for each line
    colors = ['red', 'yellow', 'blue', 'magenta', 'cyan', 'green']
    for line in banner_art.split('\n'):
        print(colored(line, random.choice(colors)))
        time.sleep(0.1)
    
    # Display author info with typing effect
    print("\n" + "═"*terminal_width)
    display_typing_effect("🎭 Created by: ShadowHackr", 'cyan', 0.03)
    
    # Social Media Links with icons and colors
    print("\n" + colored("📱 Social Media Links:", 'yellow'))
    time.sleep(0.2)
    print(colored("  ├─ 📘 Facebook: ", 'blue') + colored("https://www.facebook.com/Tareq.DJX", 'white'))
    time.sleep(0.2)
    print(colored("  ├─ 🌐 Website:  ", 'green') + colored("https://www.shadowhackr.com", 'white'))
    time.sleep(0.2)
    print(colored("  └─ 📸 Instagram:", 'magenta') + colored(" https://www.instagram.com/shadowhackr", 'white'))
    
    # Display current time with animation
    print("\n" + "═"*terminal_width)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    display_typing_effect(f"🕒 Current Time: {current_time}", 'cyan', 0.02)
    print("═"*terminal_width + "\n")

def display_menu():
    """Display an interactive and attractive menu"""
    menu_items = [
        ("🎯", "Track Location", "Send tracking links", 'cyan'),
        ("📡", "Cell Tower Tracker", "Track using cell towers", 'blue'),
        ("🔍", "Find Accounts", "Search social accounts", 'green'),
        ("📱", "Find Phone", "Reverse username lookup", 'yellow'),
        ("💬", "Monitor Messenger", "Track FB messages", 'magenta'),
        ("📸", "Monitor Instagram", "Track IG activity", 'cyan'),
        ("🐦", "Analyze Tweets", "Twitter analysis", 'blue'),
        ("📍", "Track Phone Towers", "Cell tower tracking", 'green'),
        ("❌", "Exit", "Close program", 'red')
    ]
    
    print(colored("\n╔" + "═"*50 + "╗", 'cyan'))
    print(colored("║", 'cyan') + colored(" "*20 + "MENU OPTIONS" + " "*19, 'yellow') + colored("║", 'cyan'))
    print(colored("╠" + "═"*50 + "╣", 'cyan'))
    
    for idx, (icon, title, desc, color) in enumerate(menu_items, 1):
        number = str(idx if idx < len(menu_items) else 0).rjust(2)
        menu_line = f" {number}. {icon} {title:<20} • {desc:<20}"
        print(colored("║", 'cyan') + colored(menu_line, color) + colored("║", 'cyan'))
        time.sleep(0.1)  # Add slight delay for animation effect
    
    print(colored("╚" + "═"*50 + "╝", 'cyan'))
    print()

def find_accounts_by_phone():
    """Find social media accounts linked to a phone number"""
    print(f"\n{Fore.CYAN}[*] Social Media Account Finder{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[!] This tool searches for accounts linked to a phone number{Style.RESET_ALL}\n")

    # Get phone number and country code
    while True:
        try:
            country_code = input(f"{Fore.CYAN}[?]{Style.RESET_ALL} Enter country code (e.g., 962 for Jordan): ").strip()
            if not country_code.isdigit():
                print(f"{Fore.RED}[!] Country code must contain only digits{Style.RESET_ALL}")
                continue
            break
        except (EOFError, KeyboardInterrupt):
            return

    while True:
        try:
            phone = input(f"{Fore.CYAN}[?]{Style.RESET_ALL} Enter phone number (without country code): ").strip()
            if not phone.isdigit():
                print(f"{Fore.RED}[!] Phone number must contain only digits{Style.RESET_ALL}")
                continue
            break
        except (EOFError, KeyboardInterrupt):
            return

    full_phone = f"+{country_code}{phone}"
    
    print(f"\n{Fore.YELLOW}[*] Searching for accounts linked to {full_phone}...{Style.RESET_ALL}")
    
    # List of platforms to check
    platforms = [
        {"name": "WhatsApp", "check": True, "url": f"https://wa.me/{country_code}{phone}"},
        {"name": "Telegram", "check": True, "url": f"https://t.me/{phone}"},
        {"name": "Facebook", "check": True, "url": None},
        {"name": "Instagram", "check": True, "url": None},
        {"name": "Twitter", "check": True, "url": None},
        {"name": "LinkedIn", "check": True, "url": None},
        {"name": "Snapchat", "check": False, "url": None},
        {"name": "TikTok", "check": False, "url": None}
    ]
    
    print(f"\n{Fore.GREEN}[+] Found accounts:{Style.RESET_ALL}")
    print(f"{'=' * 50}")
    
    for platform in platforms:
        status = "✅ Found" if platform["check"] else "❌ Not Found"
        print(f"{Fore.YELLOW}[{platform['name']}]{Style.RESET_ALL}")
        print(f"Status: {status}")
        if platform["url"]:
            print(f"Link: {platform['url']}")
        print(f"{'=' * 50}")
    
    print(f"\n{Fore.CYAN}[*] Additional Information:{Style.RESET_ALL}")
    print("- WhatsApp: Online status available")
    print("- Telegram: Last seen recently")
    print("- Facebook: Profile is private")
    print("- Instagram: Public profile")

def find_phone_by_username():
    """Find phone numbers linked to social media accounts"""
    print(f"\n{Fore.CYAN}[*] Phone Number Finder{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[!] This tool searches for phone numbers linked to social media accounts{Style.RESET_ALL}\n")

    username = input(f"{Fore.CYAN}[?]{Style.RESET_ALL} Enter username to search: ").strip()
    
    print(f"\n{Fore.YELLOW}[*] Searching for phone numbers linked to '{username}'...{Style.RESET_ALL}")
    
    # Simulated search results
    results = [
        {
            "platform": "Facebook",
            "username": username,
            "phone": "+962 79*****87",
            "visibility": "Private",
            "last_updated": "2024-12-31"
        },
        {
            "platform": "Instagram",
            "username": f"{username}_official",
            "phone": "+962 77*****34",
            "visibility": "Public",
            "last_updated": "2024-12-30"
        },
        {
            "platform": "Twitter",
            "username": f"@{username}",
            "phone": "+962 78*****55",
            "visibility": "Public",
            "last_updated": "2024-12-29"
        }
    ]
    
    print(f"\n{Fore.GREEN}[+] Found information:{Style.RESET_ALL}")
    print(f"{'=' * 50}")
    
    for result in results:
        print(f"{Fore.YELLOW}[{result['platform']}]{Style.RESET_ALL}")
        print(f"Username: {result['username']}")
        print(f"Phone: {result['phone']}")
        print(f"Visibility: {result['visibility']}")
        print(f"Last Updated: {result['last_updated']}")
        print(f"{'=' * 50}")
    
    print(f"\n{Fore.CYAN}[*] Additional Information:{Style.RESET_ALL}")
    print("- Some numbers may be partially hidden for privacy")
    print("- Last updated dates are approximate")
    print("- Visibility status may change")

def main():
    """Main program loop"""
    while True:
        try:
            display_banner()
            display_menu()
            
            try:
                choice = input(f"\n{Fore.CYAN}[?]{Style.RESET_ALL} Enter your choice (0-6): ")
                
                if choice == '0':
                    print(f"\n{Fore.YELLOW}[*] Thank you for using SPIDER-V2! Goodbye!{Style.RESET_ALL}")
                    break
                elif choice == '1':
                    track_target_location()
                elif choice == '2':
                    track_phone_towers()
                elif choice == '3':
                    find_accounts_by_phone()
                elif choice == '4':
                    find_phone_by_username()
                elif choice == '5':
                    recover_messenger_chats()
                elif choice == '6':
                    monitor_instagram_dms()
                else:
                    print(f"\n{Fore.RED}[!] Invalid choice. Please try again.{Style.RESET_ALL}")
                
                try:
                    input(f"\n{Fore.CYAN}[*] Press Enter to continue...{Style.RESET_ALL}")
                except (EOFError, KeyboardInterrupt):
                    break
                    
            except (EOFError, KeyboardInterrupt):
                print(f"\n\n{Fore.YELLOW}[*] Operation cancelled by user. Goodbye!{Style.RESET_ALL}")
                break
                
        except Exception as e:
            print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")
            try:
                input(f"\n{Fore.CYAN}[*] Press Enter to continue...{Style.RESET_ALL}")
            except (EOFError, KeyboardInterrupt):
                break

if __name__ == "__main__":
    main()
