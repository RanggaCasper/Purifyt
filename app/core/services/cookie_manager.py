import json
import logging
import re
from pathlib import Path
from typing import Optional

from selenium import webdriver

logger = logging.getLogger(__name__)

# Default cookie root
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
COOKIES_DIR = _ROOT_DIR / "cookies"


def _sanitize_email_folder(email: str) -> str:
    """Sanitize an email address into a valid folder name."""
    return re.sub(r'[<>:"/\\|?*]', "_", email.strip().lower())

class CookieManager:
    """Save and load YouTube cookies to/from a JSON file via CDP (multi-account)."""

    def __init__(self, email: Optional[str] = None, cookie_path: Optional[Path] = None):
        """
        Args:
            email: Google account email — a folder is created automatically: cookies/{email}/
            cookie_path: Direct path override (use when the path is already known from the DB)
        """
        if cookie_path:
            self.cookie_path = Path(cookie_path)
        elif email:
            folder = _sanitize_email_folder(email)
            self.cookie_path = COOKIES_DIR / folder / "youtube_cookies.json"
        else:
            # Fallback to the legacy path for backward compatibility
            self.cookie_path = COOKIES_DIR / "youtube_cookies.json"

        self.cookie_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def email_folder(self) -> str:
        """Name of the email folder (parent of the cookie file)."""
        return self.cookie_path.parent.name

    def save(self, driver: webdriver.Chrome) -> int:
        """
        Save all cookies from the browser to a JSON file via CDP.
        Returns the number of cookies saved.
        """
        cdp_cookies = driver.execute_cdp_cmd("Network.getAllCookies", {})
        cookies = cdp_cookies.get("cookies", [])
        with open(self.cookie_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        logger.info(f"Cookie tersimpan ke {self.cookie_path} ({len(cookies)} cookies)")
        return len(cookies)

    def load(self, driver: webdriver.Chrome) -> int:
        """
        Load cookies from the JSON file into the browser via CDP.
        Returns the number of cookies successfully loaded.
        """
        if not self.cookie_path.exists():
            logger.warning(f"File cookie tidak ditemukan: {self.cookie_path}")
            return 0

        try:
            with open(self.cookie_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Gagal membaca cookie: {e}")
            return 0

        loaded = 0
        for cookie in cookies:
            try:
                cdp_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie.get("domain", ""),
                    "path": cookie.get("path", "/"),
                }
                if cookie.get("secure"):
                    cdp_cookie["secure"] = True
                if cookie.get("httpOnly"):
                    cdp_cookie["httpOnly"] = True
                if cookie.get("expires") and cookie["expires"] > 0:
                    cdp_cookie["expires"] = cookie["expires"]
                if cookie.get("sameSite"):
                    cdp_cookie["sameSite"] = cookie["sameSite"]

                driver.execute_cdp_cmd("Network.setCookie", cdp_cookie)
                loaded += 1
            except Exception as e:
                logger.debug(f"Skip cookie {cookie.get('name')}: {e}")

        logger.info(f"Dimuat {loaded}/{len(cookies)} cookie via CDP")
        return loaded

    def exists(self) -> bool:
        """Check whether the cookie file exists."""
        return self.cookie_path.exists()

    def get_cookie_info(self) -> dict:
        """Return metadata about the cookie file (for API status checks)."""
        if not self.cookie_path.exists():
            return {"exists": False, "path": str(self.cookie_path)}

        try:
            with open(self.cookie_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            stat = self.cookie_path.stat()
            return {
                "exists": True,
                "path": str(self.cookie_path),
                "cookie_count": len(cookies),
                "file_size_bytes": stat.st_size,
                "last_modified": stat.st_mtime,
            }
        except Exception as e:
            return {"exists": True, "path": str(self.cookie_path), "error": str(e)}

    def delete(self) -> bool:
        """Delete the cookie file, and remove the parent folder if it is now empty."""
        if self.cookie_path.exists():
            self.cookie_path.unlink()
            logger.info(f"Cookie dihapus: {self.cookie_path}")
            # Remove the parent folder if it is now empty
            parent = self.cookie_path.parent
            if parent != COOKIES_DIR and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                logger.info(f"Folder kosong dihapus: {parent}")
            return True
        return False

    @staticmethod
    def list_all_accounts() -> list[dict]:
        """List all cookie accounts currently stored on disk."""
        accounts = []
        if not COOKIES_DIR.exists():
            return accounts

        for folder in sorted(COOKIES_DIR.iterdir()):
            if folder.is_dir():
                cookie_file = folder / "youtube_cookies.json"
                if cookie_file.exists():
                    try:
                        with open(cookie_file, "r", encoding="utf-8") as f:
                            cookies = json.load(f)
                        stat = cookie_file.stat()
                        accounts.append({
                            "email_folder": folder.name,
                            "cookie_path": str(cookie_file),
                            "cookie_count": len(cookies),
                            "last_modified": stat.st_mtime,
                        })
                    except Exception:
                        accounts.append({
                            "email_folder": folder.name,
                            "cookie_path": str(cookie_file),
                            "error": "Gagal membaca cookie",
                        })

        return accounts