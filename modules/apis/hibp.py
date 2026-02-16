# -*- coding: utf-8 -*-
"""HaveIBeenPwned API - Breach check"""
import hashlib
import requests
from typing import Optional, List, Dict

from modules.config import HIBP_API_KEY
from modules.logger import log


def hibp_check_breach(email: str) -> Optional[List[Dict]]:
    """Check if email appears in known breaches. Returns list of breaches."""
    if not HIBP_API_KEY:
        return None
    try:
        r = requests.get(
            f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}',
            headers={'hibp-api-key': HIBP_API_KEY, 'User-Agent': 'OSINT-Tool'},
            timeout=10
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        log.warning(f"HIBP API error: {e}")
    return None


def hibp_check_password(password: str) -> int:
    """Check how many times password has been seen in breaches (k-anonymity)."""
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        r = requests.get(
            f'https://api.pwnedpasswords.com/range/{prefix}',
            timeout=10
        )
        if r.status_code != 200:
            return 0
        for line in r.text.splitlines():
            h, count = line.split(':')
            if h == suffix:
                return int(count)
    except Exception:
        pass
    return 0
