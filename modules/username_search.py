# -*- coding: utf-8 -*-
"""
Real username search across multiple platforms - Sherlock style
Checks if username exists via HTTP (no fake data)
"""
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from dataclasses import dataclass

from modules.logger import log

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Platform: (url_template, check_pattern or None for 200)
PLATFORMS = [
    ('Instagram', 'https://www.instagram.com/{}/', r'"user":\s*\{[^}]*"username"'),
    ('Twitter', 'https://twitter.com/{}', r'"screen_name"|data-screen-name='),
    ('GitHub', 'https://api.github.com/users/{}', r'"login"'),
    ('TikTok', 'https://www.tiktok.com/@{}', r'"uniqueId"|"secUid"'),
    ('Reddit', 'https://www.reddit.com/user/{}/', r'"name"|"author"'),
    ('YouTube', 'https://www.youtube.com/@{}/about', r'"channelId"'),
    ('Facebook', 'https://www.facebook.com/{}', r'"profile"|"entity_id"'),
    ('LinkedIn', 'https://www.linkedin.com/in/{}/', r'<!DOCTYPE html>'),  # 999 = not found often
    ('Pinterest', 'https://www.pinterest.com/{}/', r'profileName|"username"'),
    ('Twitch', 'https://www.twitch.tv/{}', r'twitch\.tv'),
    ('Steam', 'https://steamcommunity.com/id/{}', r'games_count|profile_private_info'),
    ('Vimeo', 'https://vimeo.com/{}', r'"name"|"url"'),
]


@dataclass
class UsernameResult:
    platform: str
    url: str
    exists: bool
    status_code: Optional[int] = None


def _check_one(platform: str, url: str, pattern: Optional[str]) -> UsernameResult:
    """Check single platform - real HTTP request"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        exists = r.status_code == 200
        if exists and pattern:
            exists = bool(re.search(pattern, r.text))
        # LinkedIn often returns 999 for rate limit, 200 for found
        if platform == 'LinkedIn' and r.status_code == 999:
            exists = False
        return UsernameResult(platform=platform, url=url, exists=exists, status_code=r.status_code)
    except Exception as e:
        log.debug(f"Username check {platform}: {e}")
        return UsernameResult(platform=platform, url=url, exists=False, status_code=None)


def username_search(username: str, platforms: Optional[List[str]] = None, max_workers: int = 6) -> Dict:
    """
    Real multi-platform username existence check.
    Returns dict with platform -> {url, exists, status_code}
    """
    username = username.strip().lstrip('@')
    if not username or not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return {'error': 'Invalid username', 'results': {}}

    to_check = [(n, u.format(username), p) for n, u, p in PLATFORMS
                if platforms is None or n in platforms]

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_check_one, name, url, pat): name for name, url, pat in to_check}
        for fut in as_completed(futures):
            try:
                res = fut.result()
                results[res.platform] = {'url': res.url, 'exists': res.exists, 'status_code': res.status_code}
            except Exception as e:
                name = futures.get(fut, '?')
                results[name] = {'url': '', 'exists': False, 'error': str(e)}

    found = [p for p, d in results.items() if d.get('exists')]
    return {
        'username': username,
        'results': results,
        'found_on': found,
        'total_checked': len(results),
        'count_found': len(found),
        'source': 'real_http',
    }
