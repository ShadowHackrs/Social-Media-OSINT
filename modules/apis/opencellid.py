# -*- coding: utf-8 -*-
"""OpenCellID API - Real cell tower geolocation"""
import requests
from typing import Optional, Dict, Any, List

from modules.config import OPENCELLID_API_KEY
from modules.logger import log

BASE = 'https://opencellid.org'


def opencellid_get_cell(mcc: int, mnc: int, lac: int, cellid: int, radio: str = '') -> Optional[Dict]:
    """Get real cell tower position from OpenCellID. Requires MCC, MNC, LAC, CellID."""
    if not OPENCELLID_API_KEY:
        return None
    try:
        params = {'key': OPENCELLID_API_KEY, 'mcc': mcc, 'mnc': mnc, 'lac': lac, 'cellid': cellid, 'format': 'json'}
        if radio:
            params['radio'] = radio
        r = requests.get(f'{BASE}/cell/get', params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if 'lat' in data and 'lon' in data:
            return {
                'lat': data['lat'],
                'lon': data['lon'],
                'range': data.get('range'),
                'samples': data.get('samples'),
                'radio': data.get('radio'),
                'mcc': mcc, 'mnc': mnc, 'lac': lac, 'cellid': cellid,
                'source': 'opencellid',
            }
    except Exception as e:
        log.warning(f"OpenCellID API error: {e}")
    return None


def opencellid_get_in_area(lat_min: float, lon_min: float, lat_max: float, lon_max: float,
                           mcc: Optional[int] = None, mnc: Optional[int] = None,
                           limit: int = 20) -> List[Dict]:
    """Get list of real cell towers in bounding box. Optional MCC/MNC filter."""
    if not OPENCELLID_API_KEY:
        return []
    try:
        params = {
            'key': OPENCELLID_API_KEY,
            'BBOX': f'{lat_min},{lon_min},{lat_max},{lon_max}',
            'format': 'json',
            'limit': min(limit, 50),
        }
        if mcc is not None:
            params['mcc'] = mcc
        if mnc is not None:
            params['mnc'] = mnc
        r = requests.get(f'{BASE}/cell/getInArea', params=params, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        cells = data if isinstance(data, list) else (data.get('cells') or data.get('cell') or [])
        if not isinstance(cells, list):
            cells = []
        return [
            {'lat': c.get('lat'), 'lon': c.get('lon'), 'mcc': c.get('mcc'), 'mnc': c.get('mnc'),
             'lac': c.get('lac'), 'cellid': c.get('cellid'), 'radio': c.get('radio'),
             'range': c.get('range'), 'samples': c.get('samples')}
            for c in (cells[:limit] if isinstance(cells, list) else [])
            if c.get('lat') and c.get('lon')
        ]
    except Exception as e:
        log.warning(f"OpenCellID getInArea error: {e}")
    return []
