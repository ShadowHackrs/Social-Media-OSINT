# -*- coding: utf-8 -*-
"""Hunter.io API - Email/domain OSINT"""
import requests
from typing import Optional, Dict, Any

from modules.config import HUNTER_API_KEY
from modules.logger import log


def hunter_domain_search(domain: str) -> Optional[Dict[str, Any]]:
    """Find emails associated with domain. Real OSINT."""
    if not HUNTER_API_KEY:
        return None
    try:
        r = requests.get(
            'https://api.hunter.io/v2/domain-search',
            params={'domain': domain, 'api_key': HUNTER_API_KEY},
            timeout=10
        )
        if r.status_code != 200:
            return None
        data = r.json().get('data', {})
        return {
            'domain': domain,
            'emails': [{'value': e.get('value'), 'type': e.get('type'), 'confidence': e.get('confidence')}
                       for e in data.get('emails', [])],
            'pattern': data.get('pattern'),
            'organization': data.get('organization'),
            'source': 'hunter',
        }
    except Exception as e:
        log.warning(f"Hunter API error: {e}")
    return None


def hunter_email_verify(email: str) -> Optional[Dict]:
    """Verify email deliverability."""
    if not HUNTER_API_KEY:
        return None
    try:
        r = requests.get(
            'https://api.hunter.io/v2/email-verifier',
            params={'email': email, 'api_key': HUNTER_API_KEY},
            timeout=10
        )
        if r.status_code != 200:
            return None
        d = r.json().get('data', {})
        return {
            'email': email,
            'status': d.get('status'),
            'result': d.get('result'),
            'score': d.get('score'),
            'regexp': d.get('regexp'),
            'smtp_check': d.get('smtp_check'),
        }
    except Exception as e:
        log.warning(f"Hunter verify error: {e}")
    return None
