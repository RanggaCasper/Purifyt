import logging
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

from app.core.services.cookie_manager import CookieManager, COOKIES_DIR, _sanitize_email_folder

logger = logging.getLogger(__name__)

# URLs
YOUTUBE_STUDIO_BASE = "https://studio.youtube.com"
YOUTUBE_STUDIO_COMMENTS = "https://studio.youtube.com/channel/{channel_id}/comments/"
YOUTUBE_STUDIO_VIDEO_COMMENTS = "https://studio.youtube.com/video/{video_id}/comments/"

# Timing
PAGE_LOAD_WAIT = 15

# Chrome profiles root
_PROFILES_DIR = COOKIES_DIR / "_profiles"

def create_driver(
    headless: bool = False,
    enable_network_capture: bool = False,
    email: str | None = None,
) -> webdriver.Chrome:
    """
    Create a Chrome WebDriver instance with anti-detection settings.

    Args:
        headless: Run without a GUI window
        enable_network_capture: Enable CDP performance logging
        email: Account email — if provided, a separate Chrome profile is used
               to prevent sessions from conflicting across accounts

    Returns:
        Chrome WebDriver instance
    """
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    # Per-email Chrome profile to isolate sessions between accounts
    if email:
        profile_dir = _PROFILES_DIR / _sanitize_email_folder(email)
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_dir}")

    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=id")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    if enable_network_capture:
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=options)

    # Remove the webdriver detection flag
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    return driver

def wait_page_ready(driver: webdriver.Chrome, timeout: int = PAGE_LOAD_WAIT):
    """Wait until the DOM is fully loaded."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def is_logged_in(driver: webdriver.Chrome) -> bool:
    """Check whether the current session is logged in to YouTube Studio."""
    try:
        current_url = driver.current_url
        if "accounts.google.com" in current_url:
            return False
        if "studio.youtube.com" in current_url:
            return True
        driver.find_element(By.CSS_SELECTOR, "#avatar-btn, img#img[alt]")
        return True
    except NoSuchElementException:
        return False

def login_with_cookies(
    driver: webdriver.Chrome,
    cookie_mgr: CookieManager,
    target_url: str | None = None,
) -> bool:
    """
    Log in to YouTube Studio using stored cookies.

    Args:
        driver: Chrome WebDriver instance
        cookie_mgr: CookieManager instance
        target_url: Destination URL after login (defaults to YouTube Studio base)

    Returns:
        True if login succeeded
    """
    url = target_url or YOUTUBE_STUDIO_BASE

    if not cookie_mgr.exists():
        logger.warning("Cookie tidak ditemukan")
        return False

    logger.info("Memuat cookie tersimpan via CDP...")
    loaded = cookie_mgr.load(driver)
    if loaded == 0:
        logger.warning("Tidak ada cookie yang dimuat")
        return False

    logger.info(f"Membuka {url}")
    driver.get(url)
    wait_page_ready(driver)
    time.sleep(3)

    if is_logged_in(driver):
        logger.info("Login berhasil dengan cookie!")
        # Refresh stored cookies after a successful login
        cookie_mgr.save(driver)
        return True
    else:
        logger.warning("Cookie expired/invalid")
        return False

def login_manual(
    driver: webdriver.Chrome,
    cookie_mgr: CookieManager,
    target_url: str | None = None,
) -> bool:
    """
    Log in manually via the browser GUI.
    The user must complete login in the browser, then press ENTER in the terminal.

    Args:
        driver: Chrome WebDriver instance
        cookie_mgr: CookieManager instance
        target_url: Destination URL after login

    Returns:
        True if login succeeded
    """
    url = target_url or YOUTUBE_STUDIO_BASE

    logger.info("=" * 60)
    logger.info("MANUAL LOGIN DIPERLUKAN")
    logger.info("=" * 60)
    logger.info("Browser akan terbuka. Silakan:")
    logger.info("  1. Login ke akun YouTube/Google kamu")
    logger.info("  2. Pastikan masuk ke YouTube Studio")
    logger.info("  3. Tekan ENTER di terminal setelah login")
    logger.info("=" * 60)

    driver.get("https://accounts.google.com/ServiceLogin?service=youtube")
    wait_page_ready(driver)

    input("\n>>> Tekan ENTER setelah login berhasil di browser... ")

    driver.get(url)
    wait_page_ready(driver)
    time.sleep(3)

    if is_logged_in(driver):
        logger.info("Login manual berhasil!")
        cookie_mgr.save(driver)
        return True
    else:
        logger.error("Login gagal.")
        return False

def login_youtube(
    driver: webdriver.Chrome,
    cookie_mgr: CookieManager,
    target_url: str | None = None,
) -> bool:
    """
    Log in to YouTube Studio — tries cookies first, falls back to manual login.

    Args:
        driver: Chrome WebDriver instance
        cookie_mgr: CookieManager instance
        target_url: Destination URL after login

    Returns:
        True if login succeeded
    """
    # Try cookie login first
    if cookie_mgr.exists():
        if login_with_cookies(driver, cookie_mgr, target_url):
            return True

    # Fallback to manual login
    return login_manual(driver, cookie_mgr, target_url)