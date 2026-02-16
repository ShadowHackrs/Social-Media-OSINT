# social_media_tools.py - OSINT Pro
# ShadowHackr | 2026

import os
import sys
import time
from datetime import datetime

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    os.system('chcp 65001 >nul 2>&1')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text
from rich import box

c = Console()

# load config
try:
    from config import TWITTER_API_KEYS as _cfg
    if _cfg.get('consumer_key') or _cfg.get('access_token'):
        TWITTER_API_KEYS = _cfg
    else:
        raise ImportError
except (ImportError, AttributeError):
    from modules.config import TWITTER_API_KEYS

from modules.database import init_db, save_phone_lookup, save_tweet_analysis
from modules.phone_intel import get_phone_info
from modules.social_lookup import phone_social_lookup
from modules.twitter_osint import analyze_tweet_web, analyze_tweet_api
from modules.location_ops import get_cell_tower_data
from modules.exif import extract_exif, get_gps_coordinates
from modules.utils import export_results, open_url
from modules.monitors import monitor_messenger, monitor_instagram
from modules.username_search import username_search
from modules.ocr import extract_text_from_image
from modules.apis import hunter_domain_search, hibp_check_breach

VERSION = "3.0.2"


def _has_twitter():
    k = TWITTER_API_KEYS
    return bool(k.get('consumer_key') and k.get('access_token'))


def _clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def _banner():
    _clear()
    with c.status("[cyan]Loading...", spinner="dots"):
        time.sleep(0.6)

    t = Text()
    t.append("██╗ ███████╗███╗   ██╗████████╗\n", style="bold cyan")
    t.append("██║ ██╔════╝████╗  ██║╚══██╔══╝\n", style="bold blue")
    t.append("██║ ███████╗██╔██╗ ██║   ██║\n", style="bold magenta")
    t.append("██║ ╚════██║██║╚██╗██║   ██║\n", style="bold blue")
    t.append("██║ ███████║██║ ╚████║   ██║\n", style="bold cyan")
    t.append("╚═╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝", style="bold magenta")

    c.print(Panel(t, title=f"[bold white]OSINT Pro[/] v{VERSION}", subtitle="[green]Real Data[/] | [blue]Advanced Intel[/]", box=box.DOUBLE, border_style="cyan", padding=(0, 2)))
    c.print(Rule("[yellow]ShadowHackr[/]  |  [link=https://shadowhackr.com]shadowhackr.com[/]  |  [blue]fb.com/ShadowHackr[/]  |  [magenta]@shadowhackr[/]", style="dim"))
    c.print(f"  [dim]{datetime.now().strftime('%Y-%m-%d %H:%M')}[/]\n")


def _menu():
    tbl = Table(show_header=True, header_style="bold yellow", box=box.ROUNDED, border_style="blue")
    tbl.add_column("#", style="dim", width=3)
    tbl.add_column("Tool", style="cyan")
    tbl.add_column("Description", style="white")

    tbl.add_row("", "[bold]Location[/]", "")
    tbl.add_row("1", "Track Location", "Send link, get GPS")
    tbl.add_row("2", "Cell Tower Tracker", "OpenCellID / MCC,LAC,CellID")

    tbl.add_row("", "[bold]Phone & Social[/]", "")
    tbl.add_row("3", "Find Accounts (Phone)", "WhatsApp, FB, IG, Telegram")
    tbl.add_row("4", "Username Search", "12 platforms")
    tbl.add_row("8", "Phone Info", "Carrier, country, validity")

    tbl.add_row("", "[bold]Monitors[/]", "")
    tbl.add_row("5", "Monitor Messenger", "FB messages & media")
    tbl.add_row("6", "Monitor Instagram", "DMs & stories")

    tbl.add_row("", "[bold]Tools[/]", "")
    tbl.add_row("7", "Analyze Tweets", "Twitter/X")
    tbl.add_row("9", "Extract EXIF", "Image metadata & GPS")
    tbl.add_row("10", "OCR Image", "Extract text from image")
    tbl.add_row("11", "Domain/Email OSINT", "Hunter.io, HIBP")

    tbl.add_row("0", "[red]Exit[/]", "")

    c.print(Panel(tbl, title="[bold]Main Menu[/]", border_style="cyan"))
    c.print()


def _ask(txt, default=""):
    out = Prompt.ask(f"[cyan]>>[/] [white]{txt}[/]", default=default)
    return (out or default).strip()


def _ok(msg):
    c.print(f"  [green]+[/] {msg}")


def _err(msg):
    c.print(f"  [red]X[/] {msg}")


def _info(msg):
    c.print(f"  [cyan]-[/] {msg}")


def _section(title, icon=">"):
    c.print()
    c.print(Panel(f"[yellow]{icon} {title}[/]", border_style="yellow"))


def _results(data, title="Results"):
    tbl = Table(show_header=True, header_style="green", box=box.SIMPLE)
    tbl.add_column("Field", style="yellow")
    tbl.add_column("Value", style="white")
    for k, v in data.items():
        tbl.add_row(str(k), str(v)[:55] if v else "-")
    c.print(Panel(tbl, title=f"[green]{title}[/]", border_style="green"))


# --- Handlers ---

def _track_location():
    _section("Track Location", ">")
    _info("Starting server...")
    try:
        import location_tracker
        location_tracker.start_server()
    except Exception as ex:
        _err(str(ex))


def _cell_tower():
    _section("Cell Tower Tracker", ">")
    mode = _ask("Mode [1=Phone | 2=MCC,MNC,LAC,CellID]", "1")
    mcc = mnc = lac = cellid = None
    if mode == "2":
        try:
            mcc = int(_ask("MCC:"))
            mnc = int(_ask("MNC:", "0"))
            lac = int(_ask("LAC:"))
            cellid = int(_ask("Cell ID:"))
        except ValueError:
            _err("Invalid numbers")
            return
        cc, ph = "0", "0"
    else:
        cc = _ask("Country code (e.g. 962)")
        ph = _ask("Phone (no country code)")
        if not cc.isdigit() or not ph.isdigit():
            _err("Invalid input")
            return
    try:
        data = get_cell_tower_data(cc, ph, mcc=mcc, mnc=mnc, lac=lac, cellid=cellid)
        t = data.get('tower') or {}
        lat = t.get('lat') or (t.get('location') or {}).get('lat')
        lon = t.get('lon') or (t.get('location') or {}).get('lon')
        _results({"Phone": data.get('phone'), "Carrier": data.get('carrier'), "Source": data.get('source'), "Position": f"{lat},{lon}" if lat and lon else "-"})
        if data.get('maps_url'):
            open_url(data['maps_url'])
        export_results(data, "cell_tower", ['json', 'txt', 'html'])
        _ok("Saved to results/")
    except Exception as ex:
        _err(str(ex))


def _find_accounts():
    _section("Find Accounts by Phone", ">")
    phone = _ask("Phone (e.g. +962xxxxxxxxx)")
    if not phone:
        return
    with c.status("[cyan]Searching...", spinner="dots"):
        res = phone_social_lookup(phone)
    if res.get('error'):
        _err(res['error'])
        return
    pi = res['phone_info']
    acc = res['accounts']
    _results({"Country": pi.get('country'), "Carrier": pi.get('carrier')})
    c.print()
    for plat, d in acc.items():
        found = d.get('exists') and d.get('url')
        c.print(f"  [{'green' if found else 'red'}]{'Y' if found else 'N'}[/] {plat:<12} [dim]{d.get('url', '-')}[/]")
    save_phone_lookup(phone, pi.get('country', ''), pi.get('carrier', ''), acc)
    saved = export_results(res, "phone_lookup", ['txt', 'json'])
    _ok(f"Saved: {saved[0].name}" if saved else "Done")


def _username_search():
    _section("Username Search", ">")
    user = _ask("Username")
    if not user:
        return
    with c.status("[cyan]Checking 12 platforms...", spinner="dots"):
        res = username_search(user)
    if res.get('error'):
        _err(res['error'])
        return
    found = res.get('found_on', [])
    _ok(f"Found on: {', '.join(found)}" if found else "No matches")
    c.print()
    for plat, d in res.get('results', {}).items():
        c.print(f"  [{'green' if d.get('exists') else 'red'}]{'Y' if d.get('exists') else 'N'}[/] {plat:<12} [dim]{(d.get('url') or '')[:50]}[/]")
    export_results(res, "username_search", ['json', 'txt', 'html'])


def _analyze_tweets():
    _section("Tweet Analysis", ">")
    if _has_twitter():
        _ok("Twitter API OK")
    url = _ask("Tweet URL")
    if not url or ('twitter.com' not in url and 'x.com' not in url):
        _err("Invalid URL")
        return
    data = analyze_tweet_api(url, TWITTER_API_KEYS) if _has_twitter() else None
    if not data:
        data = analyze_tweet_web(url)
    if data:
        tbl = Table(box=box.SIMPLE)
        tbl.add_column("Field", style="yellow")
        tbl.add_column("Value", style="white")
        for k, v in data.items():
            if v:
                tbl.add_row(str(k), str(v))
        c.print(Panel(tbl, title="[green]Results[/]", border_style="green"))
        save_tweet_analysis(data.get('tweet_id', ''), data.get('username', ''), url, data)
        export_results(data, "tweet_analysis", ['json', 'txt'])
        _ok("Saved")
    else:
        _err("Analysis failed")


def _phone_info():
    _section("Phone Info", ">")
    phone = _ask("Phone (e.g. +962xxxxxxxxx)")
    if not phone:
        return
    info = get_phone_info(phone)
    if not info:
        _err("Invalid phone")
        return
    _results(info)
    export_results(info, "phone_info", ['json', 'txt'])


def _ocr():
    _section("OCR - Extract Text", ">")
    path = _ask("Image path").strip().strip('"')
    if not path or not os.path.isfile(path):
        _err("File not found")
        return
    data = extract_text_from_image(path)
    if not data:
        _err("OCR failed (install pytesseract + Tesseract)")
        return
    c.print(Panel((data.get('text') or '(empty)')[:500], title="[green]Extracted Text[/]", border_style="green"))
    _info(f"Confidence: {data.get('confidence', 0):.0f}% | Words: {data.get('word_count', 0)}")
    export_results(data, "ocr", ['txt', 'json'])


def _domain_email():
    _section("Domain/Email OSINT", ">")
    q = _ask("Domain (e.g. company.com) or Email")
    if not q:
        return
    out = {}
    if '@' in q:
        breaches = hibp_check_breach(q)
        if breaches is not None:
            names = [b.get('Name') for b in breaches] if breaches else []
            out['breaches'] = names
            _ok(f"Breaches: {', '.join(names) or 'None'}")
        else:
            _info("HIBP API key required (.env)")
    else:
        h = hunter_domain_search(q)
        if h:
            out['hunter'] = h
            ems = h.get('emails', [])[:10]
            _ok(f"Found {len(h.get('emails', []))} emails")
            for e in ems:
                c.print(f"  [green]-[/] {e.get('value')} [dim]({e.get('type','')})[/]")
        else:
            _info("Hunter API key required (.env)")
    if out:
        export_results(out, "domain_email_osint", ['json'])


def _exif():
    _section("EXIF Extraction", ">")
    path = _ask("Image path").strip().strip('"')
    if not path or not os.path.isfile(path):
        _err("File not found")
        return
    data = extract_exif(path)
    if not data:
        _err("No EXIF data")
        return
    tbl = Table(box=box.SIMPLE)
    tbl.add_column("Field", style="yellow")
    tbl.add_column("Value", style="white")
    for k, v in list(data.items())[:12]:
        if k != 'gps_raw' and v:
            tbl.add_row(str(k), str(v)[:60])
    gps = get_gps_coordinates(data)
    if gps:
        tbl.add_row("GPS", f"{gps[0]:.4f}, {gps[1]:.4f}")
        open_url(f"https://www.google.com/maps?q={gps[0]},{gps[1]}")
    c.print(Panel(tbl, title="[green]EXIF Data[/]", border_style="green"))
    export_results(data, "exif")


def main():
    init_db()
    HANDLERS = {
        '1': _track_location, '2': _cell_tower,
        '3': _find_accounts, '4': _username_search,
        '5': monitor_messenger, '6': monitor_instagram,
        '7': _analyze_tweets, '8': _phone_info,
        '9': _exif, '10': _ocr, '11': _domain_email,
    }
    while True:
        try:
            _banner()
            _menu()
            ch = _ask("Choice (0-11)")
            if ch == '0':
                c.print(Panel("[cyan]Thanks for using OSINT Pro![/]\n[dim]shadowhackr.com[/]", border_style="cyan"))
                break
            if ch in HANDLERS:
                HANDLERS[ch]()
            else:
                _err("Invalid choice")
            c.print()
            Prompt.ask("[dim]Press Enter[/]", default="")
        except (EOFError, KeyboardInterrupt):
            c.print("\n[yellow]Bye.[/]\n")
            break
        except Exception as ex:
            _err(str(ex))
            try:
                Prompt.ask("[dim]Press Enter[/]", default="")
            except (EOFError, KeyboardInterrupt):
                break


if __name__ == "__main__":
    main()
