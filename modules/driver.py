# -*- coding: utf-8 -*-
"""
Chrome/WebDriver setup - auto-matching Chrome version via webdriver-manager
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from modules.config import HEADLESS, PROXY_URL, CHROME_TIMEOUT
from modules.logger import log


def _get_chrome_service():
    """Get ChromeDriver that matches installed Chrome version"""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        return Service(ChromeDriverManager().install())
    except ImportError:
        return None


def setup_driver(headless: bool = None, use_undetected: bool = True) -> webdriver.Chrome | None:
    """Setup Chrome WebDriver - uses webdriver-manager for correct version matching"""
    headless = headless if headless is not None else HEADLESS

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    if headless:
        options.add_argument('--headless=new')
    if PROXY_URL:
        options.add_argument(f'--proxy-server={PROXY_URL}')

    # Use webdriver-manager FIRST (auto-matches Chrome version - no 144 vs 145 mismatch)
    service = _get_chrome_service()
    try:
        if service:
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(CHROME_TIMEOUT)
        return driver
    except Exception as e:
        log.warning(f"webdriver-manager failed: {e}")
        pass

    # Fallback: undetected_chromedriver (may have version mismatch)
    if use_undetected:
        try:
            import undetected_chromedriver as uc
            uc_options = uc.ChromeOptions()
            if headless:
                uc_options.add_argument('--headless=new')
            if PROXY_URL:
                uc_options.add_argument(f'--proxy-server={PROXY_URL}')
            driver = uc.Chrome(options=uc_options)
            driver.set_page_load_timeout(CHROME_TIMEOUT)
            return driver
        except Exception as e:
            log.error(f"Chrome driver failed: {e}")
    return None


def setup_driver_visible(use_undetected: bool = False) -> webdriver.Chrome | None:
    """Setup visible Chrome for interactive use (Messenger, Instagram)"""
    return setup_driver(headless=False, use_undetected=use_undetected)
