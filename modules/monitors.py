# -*- coding: utf-8 -*-
"""
Messenger and Instagram DM monitors
"""
import os
import time
import requests
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By

from modules.driver import setup_driver_visible
from modules.utils import open_folder


def monitor_messenger() -> None:
    """Monitor Facebook Messenger chats and save media"""
    from colorama import Fore, Style

    recovery_dir = Path.cwd() / 'Messenger_Recovery'
    images_dir = recovery_dir / 'Images'
    videos_dir = recovery_dir / 'Videos'
    for d in (recovery_dir, images_dir, videos_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n{Fore.YELLOW}[*] Starting message monitor...{Style.RESET_ALL}")
    driver = setup_driver_visible()
    if not driver:
        print(f"{Fore.RED}[-] Failed to start Chrome{Style.RESET_ALL}")
        return

    try:
        print(f"{Fore.WHITE}• Opening Messenger...{Style.RESET_ALL}")
        driver.get('https://www.messenger.com/')
        time.sleep(3)
        print(f"\n{Fore.YELLOW}[!] Please log in to Facebook, then press Enter...{Style.RESET_ALL}")
        input()

        monitor_file = recovery_dir / 'messenger_monitor.txt'
        print(f"\n{Fore.GREEN}[+] Monitoring started. Messages → {monitor_file}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Press Ctrl+C to stop{Style.RESET_ALL}\n")

        last_messages, last_media = set(), set()
        while True:
            try:
                msgs = driver.find_elements(By.CSS_SELECTOR, '[role="row"]')
                curr_msgs, curr_media = set(), set()
                for msg in msgs:
                    try:
                        content = msg.get_attribute('textContent')
                        if content and content.strip():
                            curr_msgs.add(content.strip())
                            if content.strip() not in last_messages:
                                with open(monitor_file, 'a', encoding='utf-8') as f:
                                    f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {content.strip()}\n")
                        for media in msg.find_elements(By.CSS_SELECTOR, 'img, video'):
                            url = media.get_attribute('src')
                            if url and url not in last_media:
                                curr_media.add(url)
                                _download_media(url, images_dir, videos_dir, monitor_file)
                    except Exception:
                        continue
                last_messages, last_media = curr_msgs, curr_media
            except KeyboardInterrupt:
                break
            except Exception:
                pass
            time.sleep(1)

        print(f"\n{Fore.GREEN}[+] Monitoring stopped. Results in: {recovery_dir}{Style.RESET_ALL}")
        open_folder(recovery_dir)
    finally:
        driver.quit()


def monitor_instagram() -> None:
    """Monitor Instagram DMs and save media"""
    from colorama import Fore, Style

    recovery_dir = Path.cwd() / 'Instagram_Recovery'
    images_dir = recovery_dir / 'Images'
    videos_dir = recovery_dir / 'Videos'
    stories_dir = recovery_dir / 'Stories'
    for d in (recovery_dir, images_dir, videos_dir, stories_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n{Fore.YELLOW}[*] Starting Instagram DM monitor...{Style.RESET_ALL}")
    driver = setup_driver_visible()
    if not driver:
        print(f"{Fore.RED}[-] Failed to start Chrome{Style.RESET_ALL}")
        return

    try:
        driver.get('https://www.instagram.com/direct/inbox/')
        time.sleep(3)
        print(f"\n{Fore.YELLOW}[!] Please log in to Instagram, then press Enter...{Style.RESET_ALL}")
        input()

        monitor_file = recovery_dir / 'instagram_monitor.txt'
        print(f"\n{Fore.GREEN}[+] Monitoring started. Press Ctrl+C to stop{Style.RESET_ALL}\n")

        last_messages, last_media = set(), set()
        while True:
            try:
                msgs = driver.find_elements(By.CSS_SELECTOR, '._aacl._aaco._aacu._aacx._aad7._aade, [role="row"]')
                curr_msgs, curr_media = set(), set()
                for msg in msgs:
                    try:
                        content = msg.get_attribute('textContent')
                        if content and content.strip():
                            curr_msgs.add(content.strip())
                            if content.strip() not in last_messages:
                                with open(monitor_file, 'a', encoding='utf-8') as f:
                                    f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {content.strip()}\n")
                        for media in msg.find_elements(By.CSS_SELECTOR, 'img[src*="instagram"], video[src*="instagram"]'):
                            url = media.get_attribute('src')
                            if url and url not in last_media:
                                curr_media.add(url)
                                _download_media(url, images_dir, videos_dir, monitor_file, None)
                    except Exception:
                        continue
                for story_el in driver.find_elements(By.CSS_SELECTOR, '._aa63 img, ._aa63 video'):
                    try:
                        url = story_el.get_attribute('src')
                        if url and url not in last_media:
                            curr_media.add(url)
                            _download_media(url, images_dir, videos_dir, monitor_file, stories_dir)
                    except Exception:
                        continue
                last_messages, last_media = curr_msgs, curr_media
            except KeyboardInterrupt:
                break
            except Exception:
                pass
            time.sleep(1)

        print(f"\n{Fore.GREEN}[+] Monitoring stopped. Results in: {recovery_dir}{Style.RESET_ALL}")
        open_folder(recovery_dir)
    finally:
        driver.quit()


def _download_media(url: str, images_dir: Path, videos_dir: Path, monitor_file: Path, stories_dir: Path = None) -> None:
    """Download media from URL and log"""
    from colorama import Fore
    try:
        r = requests.get(url, stream=True, timeout=15)
        if r.status_code != 200:
            return
        ct = r.headers.get('content-type', '')
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        if 'image' in ct:
            ext = ct.split('/')[-1].split(';')[0] or 'jpg'
            folder = stories_dir or images_dir
            path = folder / f"{'story_' if stories_dir else ''}image_{ts}.{ext}"
        elif 'video' in ct:
            ext = ct.split('/')[-1].split(';')[0] or 'mp4'
            folder = stories_dir or videos_dir
            path = folder / f"{'story_' if stories_dir else ''}video_{ts}.{ext}"
        else:
            return
        with open(path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        print(f"{Fore.GREEN}[+] Saved: {path.name}{Fore.RESET}")
        with open(monitor_file, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] Saved: {path.name}\n")
    except Exception:
        pass
