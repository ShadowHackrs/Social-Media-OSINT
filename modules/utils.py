# -*- coding: utf-8 -*-
"""
Utility functions - cross-platform, export, etc.
"""
import os
import sys
import json
import csv
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from modules.config import RESULTS_DIR
from modules.logger import log


def open_folder(path: str | Path) -> None:
    """Cross-platform open folder in file manager"""
    path = Path(path)
    if not path.exists():
        return
    try:
        if sys.platform == 'win32':
            os.startfile(str(path))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(path)], check=False)
        else:
            subprocess.run(['xdg-open', str(path)], check=False)
    except Exception as e:
        log.warning(f"Could not open folder: {e}")


def open_url(url: str) -> None:
    """Open URL in default browser"""
    try:
        webbrowser.open(url)
    except Exception as e:
        log.warning(f"Could not open URL: {e}")


def export_results(
    data: Dict[str, Any],
    base_name: str,
    formats: Optional[List[str]] = None
) -> List[Path]:
    """Export results to TXT, JSON, CSV, and optionally HTML"""
    formats = formats or ['txt', 'json', 'csv']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []

    for fmt in formats:
        try:
            if fmt == 'txt':
                path = RESULTS_DIR / f"{base_name}_{timestamp}.txt"
                _save_txt(data, path)
            elif fmt == 'json':
                path = RESULTS_DIR / f"{base_name}_{timestamp}.json"
                _save_json(data, path)
            elif fmt == 'csv':
                path = RESULTS_DIR / f"{base_name}_{timestamp}.csv"
                _save_csv(data, path)
            elif fmt == 'html':
                path = RESULTS_DIR / f"{base_name}_{timestamp}.html"
                _save_html(data, path, base_name)
            else:
                continue
            saved.append(path)
        except Exception as e:
            log.error(f"Export to {fmt} failed: {e}")

    return saved


def _save_txt(data: Dict, path: Path) -> None:
    """Save data as readable text"""
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    path.write_text('\n'.join(str(x) for x in lines), encoding='utf-8')


def _save_json(data: Dict, path: Path) -> None:
    """Save data as JSON"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_csv(data: Dict, path: Path) -> None:
    """Save flat data as CSV"""
    flat = _flatten_dict(data)
    if not flat:
        return
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['key', 'value'])
        for k, v in flat.items():
            writer.writerow([k, str(v)])


def _save_html(data: Dict, path: Path, title: str = 'OSINT Report') -> None:
    """Save data as HTML report"""
    rows = []
    for k, v in data.items():
        if isinstance(v, dict):
            rows.append(f'<tr><td><b>{k}</b></td><td><pre>{_dict_to_html(v)}</pre></td></tr>')
        elif isinstance(v, list):
            rows.append(f'<tr><td><b>{k}</b></td><td><ul>{"".join(f"<li>{x}</li>" for x in v)}</ul></td></tr>')
        else:
            rows.append(f'<tr><td><b>{k}</b></td><td>{v}</td></tr>')
    html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:sans-serif;margin:20px;}} table{{border-collapse:collapse;}} td{{border:1px solid #ccc;padding:8px;}} pre{{margin:0;}}</style></head>
<body><h1>{title}</h1><p>Generated: {datetime.now().isoformat()}</p><table>{"".join(rows)}</table></body></html>'''
    path.write_text(html, encoding='utf-8')


def _dict_to_html(d: Dict) -> str:
    return '\n'.join(f'{k}: {v}' for k, v in d.items())


def _flatten_dict(d: Dict, parent_key: str = '') -> Dict:
    """Flatten nested dict for CSV"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict) and not any(isinstance(x, (dict, list)) for x in v.values()):
            items.extend(_flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)
