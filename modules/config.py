# -*- coding: utf-8 -*-
"""
Configuration module - All API keys and settings
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = BASE_DIR / "data" / "osint.db"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)

# Twitter/X API
TWITTER_API_KEYS = {
    'consumer_key': os.getenv('TWITTER_CONSUMER_KEY', ''),
    'consumer_secret': os.getenv('TWITTER_CONSUMER_SECRET', ''),
    'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
    'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', ''),
}
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')

# OpenCellID - Real cell tower data (free: https://opencellid.org)
OPENCELLID_API_KEY = os.getenv('OPENCELLID_API_KEY', '')

# Numverify - Real phone validation (free: https://numverify.com)
NUMVERIFY_API_KEY = os.getenv('NUMVERIFY_API_KEY', '')

# Hunter.io - Email/domain OSINT (free tier)
HUNTER_API_KEY = os.getenv('HUNTER_API_KEY', '')

# HaveIBeenPwned - Breach check
HIBP_API_KEY = os.getenv('HIBP_API_KEY', '')

# Google Maps - for Location Tracker viewer (optional)
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

PROXY_URL = os.getenv('PROXY_URL', '')
HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
CHROME_TIMEOUT = int(os.getenv('CHROME_TIMEOUT', '30'))

# Rate limiting (requests per minute)
RATE_LIMIT_RPM = int(os.getenv('RATE_LIMIT_RPM', '60'))
