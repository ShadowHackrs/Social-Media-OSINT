# -*- coding: utf-8 -*-
"""
Phone number intelligence - REAL data (Numverify API + phonenumbers fallback)
"""
import phonenumbers
from phonenumbers import geocoder, carrier
from typing import Dict, Any, Optional

from modules.apis.numverify import numverify_lookup
from modules.logger import log


def parse_phone(phone_input: str) -> Optional[phonenumbers.PhoneNumber]:
    """Parse and validate phone number"""
    try:
        parsed = phonenumbers.parse(phone_input)
        if phonenumbers.is_valid_number(parsed):
            return parsed
        if phonenumbers.is_possible_number(parsed):
            return parsed
        return None
    except phonenumbers.phonenumberutil.NumberParseException:
        return None


def get_phone_info(phone_number: str, use_api: bool = True) -> Optional[Dict[str, Any]]:
    """
    Get REAL phone info: Numverify API first (carrier, line_type, location),
    fallback to phonenumbers (offline).
    """
    if use_api:
        api_result = numverify_lookup(phone_number)
        if api_result:
            return {
                "phone": api_result.get('number', phone_number),
                "country": api_result.get('country', ''),
                "carrier": api_result.get('carrier', ''),
                "country_code": api_result.get('country_code', ''),
                "valid": api_result.get('valid', False),
                "line_type": api_result.get('line_type', ''),
                "location": api_result.get('location', ''),
                "source": api_result.get('source', 'numverify'),
            }

    parsed = parse_phone(phone_number)
    if not parsed:
        return None
    try:
        country = geocoder.description_for_number(parsed, "en")
        carrier_name = carrier.name_for_number(parsed, "en") or "Unknown"
        return {
            "phone": phone_number,
            "country": country,
            "carrier": carrier_name,
            "country_code": f"+{parsed.country_code}",
            "national_number": parsed.national_number,
            "valid": phonenumbers.is_valid_number(parsed),
            "possible": phonenumbers.is_possible_number(parsed),
            "source": "phonenumbers",
        }
    except Exception as e:
        log.error(f"Phone info error: {e}")
        return None


def format_for_whatsapp(phone: str) -> str:
    """Format phone for WhatsApp link"""
    return phone.replace("+", "").replace(" ", "").replace("-", "")
