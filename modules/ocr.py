# -*- coding: utf-8 -*-
"""
OCR - Extract text from images (real)
"""
from pathlib import Path
from typing import Optional, Dict

from modules.logger import log


def extract_text_from_image(image_path: str | Path) -> Optional[Dict]:
    """Extract text from image using Tesseract OCR. Returns dict with text and meta."""
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        return None
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        log.warning("Install: pip install pytesseract Pillow. Tesseract engine must be installed.")
        return None
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        return {
            'text': text.strip(),
            'confidence': _avg_confidence(data) if data else 0,
            'word_count': len([w for w in (data.get('text') or []) if w.strip()]),
            'source': 'tesseract',
        }
    except Exception as e:
        log.error(f"OCR error: {e}")
    return None


def _avg_confidence(data: dict) -> float:
    confs = [int(x) for x in (data.get('conf') or []) if x != '-1']
    return sum(confs) / len(confs) if confs else 0
