# -*- coding: utf-8 -*-
"""Numverify API - Real phone validation & lookup"""
import requests
from typing import Optional, Dict, Any

from modules.config import NUMVERIFY_API_KEY
from modules.logger import log


def numverify_lookup(phone: str) -> Optional[Dict[str, Any]]:
    """
    Real phone validation via Numverify API.
    Returns: valid, number, local_format, intl_format, country_code, country, location, carrier, line_type
    """
    if not NUMVERIFY_API_KEY:
        return None
    phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')
    if phone_clean.startswith('+'):
        pass
    else:
        phone_clean = '+' + phone_clean
    try:
        r = requests.get(
            'http://apilayer.net/api/validate',
            params={'access_key': NUMVERIFY_API_KEY, 'number': phone_clean},
            timeout=10
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get('valid') is False and not data.get('number'):
            return None
        return {
            'valid': data.get('valid', False),
            'number': data.get('international_format', phone_clean),
            'local_format': data.get('local_format', ''),
            'country_code': data.get('country_code', ''),
            'country': data.get('country_name', ''),
            'location': data.get('location', ''),
            'carrier': data.get('carrier', ''),
            'line_type': data.get('line_type', ''),
            'source': 'numverify',
        }
    except Exception as e:
        log.warning(f"Numverify API error: {e}")
    return None
