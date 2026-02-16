# -*- coding: utf-8 -*-
"""
EXIF metadata extraction from images
"""
from pathlib import Path
from typing import Dict, Optional

from modules.logger import log


def extract_exif(image_path: str | Path) -> Optional[Dict]:
    """Extract EXIF metadata from image file"""
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        log.warning(f"File not found: {path}")
        return None

    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
    except ImportError:
        log.warning("Pillow required for EXIF extraction: pip install Pillow")
        return None

    try:
        img = Image.open(path)
        exif_data = img._getexif()
        if not exif_data:
            return {"info": "No EXIF data found", "format": img.format}

        result = {"format": img.format, "size": img.size}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='ignore')
                except Exception:
                    value = "<binary>"
            result[str(tag)] = value

        # GPS extraction
        if 'GPSInfo' in result:
            gps = result['GPSInfo']
            if isinstance(gps, dict):
                result['gps_raw'] = gps

        return result
    except Exception as e:
        log.error(f"EXIF extraction error: {e}")
    return None


def get_gps_coordinates(exif_data: Dict) -> Optional[tuple]:
    """Extract lat/lon from EXIF GPS data"""
    gps = exif_data.get('GPSInfo') or exif_data.get('gps_raw')
    if not gps or not isinstance(gps, dict):
        return None
    try:
        def to_degrees(coord):
            # coord = ((d,1), (m,1), (s,1)) - PIL EXIF format
            d = float(coord[0][0]) / float(coord[0][1])
            m = float(coord[1][0]) / float(coord[1][1])
            s = float(coord[2][0]) / float(coord[2][1])
            return d + (m / 60.0) + (s / 3600.0)

        lat_ref = gps.get(1, b'N')
        lat = gps.get(2)
        lon_ref = gps.get(3, b'E')
        lon = gps.get(4)
        if isinstance(lat_ref, bytes):
            lat_ref = lat_ref.decode()
        if isinstance(lon_ref, bytes):
            lon_ref = lon_ref.decode()

        if lat and lon and len(lat) >= 3 and len(lon) >= 3:
            lat_val = to_degrees(lat) * (-1 if str(lat_ref) == 'S' else 1)
            lon_val = to_degrees(lon) * (-1 if str(lon_ref) == 'W' else 1)
            return (lat_val, lon_val)
    except Exception:
        pass
    return None
