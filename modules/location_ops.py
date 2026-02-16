# -*- coding: utf-8 -*-
"""
Location / Cell Tower - REAL data via OpenCellID API
"""
from typing import Dict, List, Optional, Any

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from modules.apis.opencellid import opencellid_get_cell, opencellid_get_in_area
from modules.config import OPENCELLID_API_KEY
from modules.phone_intel import get_phone_info

# Country dial code -> MCC for OpenCellID
DIAL_TO_MCC = {
    '1': 310, '44': 234, '49': 262, '33': 208, '39': 222, '34': 214,
    '81': 440, '86': 460, '91': 404, '7': 250, '55': 724, '82': 450,
    '962': 416,  # Jordan
    '966': 420,  # Saudi
    '971': 424,  # UAE
    '20': 602, '212': 604, '213': 603, '90': 286,
}

# Capital/major city coordinates for fallback (avoid country centroid in desert)
COUNTRY_DEFAULT_COORDS = {
    '962': (31.9454, 35.9284),   # Jordan -> Amman
    '966': (24.7136, 46.6753),   # Saudi -> Riyadh
    '971': (25.2048, 55.2708),   # UAE -> Dubai
    '20': (30.0444, 31.2357),    # Egypt -> Cairo
    '212': (33.5731, -7.5898),   # Morocco -> Casablanca
    '1': (40.7128, -74.0060),    # US -> NYC
    '44': (51.5074, -0.1278),    # UK -> London
    '49': (52.5200, 13.4050),    # Germany -> Berlin
    '33': (48.8566, 2.3522),     # France -> Paris
    '90': (41.0082, 28.9784),    # Turkey -> Istanbul
}
JORDAN_CARRIERS = {'77': 'Zain', '78': 'Zain', '79': 'Zain', '76': 'Umniah', '70': 'Orange', '71': 'Orange', '72': 'Orange'}


def get_carrier_from_prefix(phone: str, country_code: str = "962") -> str:
    if country_code == "962" and len(phone) >= 2:
        return JORDAN_CARRIERS.get(phone[:2], "Unknown")
    return "Unknown"


def get_country_bbox(country_name: str) -> Optional[tuple]:
    """Get approximate bounding box for country (lat_min, lon_min, lat_max, lon_max)"""
    try:
        geolocator = Nominatim(user_agent="osint-tool")
        loc = geolocator.geocode(country_name, timeout=5)
        if loc:
            # Approximate ~200km box around centroid
            lat, lon = loc.latitude, loc.longitude
            delta = 1.5
            return (lat - delta, lon - delta, lat + delta, lon + delta)
    except Exception:
        pass
    return None


def get_cell_tower_data(country_code: str, phone: str,
                        mcc: Optional[int] = None, mnc: Optional[int] = None,
                        lac: Optional[int] = None, cellid: Optional[int] = None) -> Dict[str, Any]:
    """
    REAL cell tower data:
    - If mcc,mnc,lac,cellid provided: OpenCellID cell/get (exact position)
    - Else if OpenCellID key: get towers in country region
    - Else: phonenumbers-based carrier estimate (no position)
    """
    full_phone = f"+{country_code}{phone}"
    carrier = get_carrier_from_prefix(phone, country_code)
    result = {
        "phone": full_phone,
        "carrier": carrier,
        "source": "estimate",
        "towers": [],
        "maps_url": None,
    }

    if mcc is not None and lac is not None and cellid is not None:
        cell = opencellid_get_cell(mcc, mnc or 0, lac, cellid)
        if cell:
            result["tower"] = cell
            result["source"] = "opencellid"
            result["maps_url"] = f"https://www.google.com/maps?q={cell['lat']},{cell['lon']}"
            return result

    if OPENCELLID_API_KEY:
        info = get_phone_info(full_phone, use_api=False)
        if info and info.get('country'):
            bbox = get_country_bbox(info['country'])
            if bbox:
                mcc_val = DIAL_TO_MCC.get(country_code.lstrip('+'), mcc)
                towers = opencellid_get_in_area(*bbox, mcc=mcc_val, limit=10)
                if towers:
                    result["towers"] = towers
                    result["source"] = "opencellid"
                    t = towers[0]
                    result["maps_url"] = f"https://www.google.com/maps?q={t['lat']},{t['lon']}"
                    result["tower"] = t
                    return result

    # Fallback: use capital/major city for country (not country centroid - often in desert)
    cc = str(country_code).lstrip('+')
    if cc in COUNTRY_DEFAULT_COORDS:
        lat, lon = COUNTRY_DEFAULT_COORDS[cc]
        result["tower"] = {"lat": lat, "lon": lon, "accuracy": 15000, "source": "capital_estimate"}
        result["maps_url"] = f"https://www.google.com/maps?q={lat},{lon}"
    else:
        info = get_phone_info(full_phone, use_api=False)
        if info:
            bbox = get_country_bbox(info.get('country', ''))
            if bbox:
                lat, lon = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
                result["tower"] = {"lat": lat, "lon": lon, "accuracy": 50000, "source": "country_estimate"}
                result["maps_url"] = f"https://www.google.com/maps?q={lat},{lon}"
    return result
