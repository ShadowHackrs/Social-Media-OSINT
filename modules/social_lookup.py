# -*- coding: utf-8 -*-
"""
Social media account lookup by phone number
"""
import json
import re
import time
import requests
from typing import Dict, Optional

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from modules.driver import setup_driver
from modules.phone_intel import get_phone_info, format_for_whatsapp
from modules.logger import log


def find_facebook_profile(driver, phone: str) -> Optional[str]:
    """Find Facebook profile using phone search"""
    if not driver:
        return None
    try:
        search_url = f"https://www.facebook.com/search/people/?q={phone}"
        driver.get(search_url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        profile_links = soup.find_all('a', href=re.compile(r'facebook\.com/profile\.php\?id=\d+'))
        if not profile_links:
            profile_links = soup.find_all('a', href=re.compile(r'facebook\.com/[^/]+$'))
        if profile_links:
            url = profile_links[0]['href']
            if 'l.php' not in url and 'instagram.com' not in url:
                return url
        return search_url
    except Exception as e:
        log.warning(f"Facebook search error: {e}")
    return None


def find_instagram_profile(driver, phone: str) -> Optional[str]:
    """Find Instagram profile using phone search"""
    if not driver:
        return None
    try:
        search_url = f"https://www.instagram.com/web/search/topsearch/?context=user&query={phone}"
        driver.get(search_url)
        time.sleep(5)
        try:
            elem = driver.find_element(By.TAG_NAME, 'pre')
            data = json.loads(elem.text)
            if data and 'users' in data:
                for user in data['users']:
                    if user.get('user', {}).get('username'):
                        return f"https://instagram.com/{user['user']['username']}"
        except Exception:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'instagram\.com/[^/]+/?$'))
            if links:
                url = links[0]['href']
                return url + '/' if not url.endswith('/') else url
        return f"https://www.instagram.com/explore/search/keyword/?q={phone}"
    except Exception as e:
        log.warning(f"Instagram search error: {e}")
    return None


def phone_social_lookup(phone_number: str) -> Dict:
    """
    Search for social media accounts linked to a phone number.
    Returns dict with accounts, phone_info, etc.
    """
    phone_info = get_phone_info(phone_number)
    if not phone_info:
        return {"error": "Invalid phone number", "accounts": {}}

    whatsapp_num = format_for_whatsapp(phone_number)
    accounts = {}

    # WhatsApp
    try:
        url = f"https://wa.me/{whatsapp_num}"
        r = requests.head(url, allow_redirects=True, timeout=10)
        accounts['whatsapp'] = {'exists': r.status_code == 200, 'url': url}
    except Exception:
        accounts['whatsapp'] = {'exists': False, 'url': None}

    # Selenium for Facebook & Instagram
    driver = setup_driver()
    if driver:
        try:
            fb = find_facebook_profile(driver, phone_number)
            accounts['facebook'] = {'exists': fb is not None, 'url': fb}
            insta = find_instagram_profile(driver, phone_number)
            accounts['instagram'] = {'exists': insta is not None, 'url': insta}
        finally:
            driver.quit()
    else:
        accounts['facebook'] = {'exists': False, 'url': None}
        accounts['instagram'] = {'exists': False, 'url': None}

    # Telegram
    try:
        url = f"https://t.me/+{whatsapp_num}"
        r = requests.get(url, timeout=10)
        accounts['telegram'] = {'exists': 'tgme_page_title' in r.text, 'url': url}
    except Exception:
        accounts['telegram'] = {'exists': False, 'url': None}

    return {
        "phone_number": phone_number,
        "phone_info": phone_info,
        "accounts": accounts,
    }
