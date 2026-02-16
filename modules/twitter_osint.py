# -*- coding: utf-8 -*-
"""
Twitter/X OSINT analysis
"""
import requests
from datetime import datetime
from typing import Dict, Optional

from bs4 import BeautifulSoup

from modules.logger import log


def analyze_tweet_web(tweet_url: str) -> Optional[Dict]:
    """Analyze tweet using web scraping (no API)"""
    try:
        parts = tweet_url.strip('/').split('/')
        tweet_id = parts[-1] if parts[-1].isdigit() else parts[-1].split('?')[0]
        username = parts[-3] if len(parts) >= 3 else "unknown"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(tweet_url, headers=headers, timeout=15)

        result = {
            "tweet_id": tweet_id,
            "username": f"@{username}",
            "url": tweet_url,
            "description": None,
            "analysis_time": datetime.now().isoformat(),
        }

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup.find_all('meta', property='og:description'):
                result['description'] = tag.get('content', '')
                break

        return result
    except Exception as e:
        log.error(f"Tweet analysis error: {e}")
    return None


def analyze_tweet_api(tweet_url: str, api_keys: Dict) -> Optional[Dict]:
    """Analyze tweet using Twitter API v1.1 (if configured)"""
    try:
        import twitter
        api = twitter.Api(
            consumer_key=api_keys['consumer_key'],
            consumer_secret=api_keys['consumer_secret'],
            access_token_key=api_keys['access_token'],
            access_token_secret=api_keys['access_token_secret']
        )
        parts = tweet_url.strip('/').split('/')
        tweet_id = parts[-1] if parts[-1].isdigit() else None
        if not tweet_id:
            return None

        tweet = api.GetStatus(tweet_id)
        return {
            "tweet_id": tweet_id,
            "username": f"@{tweet.user.screen_name}",
            "url": tweet_url,
            "device": getattr(tweet, 'source', None),
            "created_at": str(tweet.created_at),
            "language": getattr(tweet, 'lang', None),
            "likes": getattr(tweet, 'favorite_count', 0),
            "retweets": getattr(tweet, 'retweet_count', 0),
            "user_name": tweet.user.name,
            "user_location": tweet.user.location,
            "user_followers": tweet.user.followers_count,
            "user_friends": tweet.user.friends_count,
        }
    except Exception as e:
        log.warning(f"Twitter API error: {e}")
    return None
