import json
from dataclasses import dataclass, field
from typing import Generator, Optional

from selenium import webdriver

from app.config.logging_config import get_logger
from app.core.services.cookie_manager import CookieManager
from app.core.services.browser_driver import (
    create_driver,
    login_with_cookies,
    is_logged_in,
    wait_page_ready,
    YOUTUBE_STUDIO_BASE,
    YOUTUBE_STUDIO_VIDEO_COMMENTS,
)
from app.core.services.youtube_studio_api import YouTubeStudioAPI

logger = get_logger(__name__)

def _detect_channel_name(driver) -> str | None:
    """Detect the channel name from YouTube Studio."""
    try:
        driver.get(YOUTUBE_STUDIO_BASE)

        import time
        time.sleep(3)

        channel_name = driver.execute_script("""
            const el = document.querySelector('#entity-name');
            if (el) {
                return el.textContent.trim();
            }

            return null;
        """)

        return channel_name

    except Exception as e:
        logger.debug(f"Channel name detect failed: {e}")
        return None

def _save_cookie_account_sync(
    email: str,
    cookie_path: str,
    cookie_count: int,
    channel_name: str | None,
):
    """
    Save cookie account info to database (synchronous, direct SQL).
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session as SyncSession
    from app.config.settings import get_settings

    settings = get_settings()
    sync_engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)

    try:
        with SyncSession(sync_engine) as session:
            # Upsert: check if the record already exists
            row = session.execute(
                text("SELECT id FROM cookie_accounts WHERE email = :email"),
                {"email": email},
            ).fetchone()

            if row:
                session.execute(
                    text(
                        "UPDATE cookie_accounts "
                        "SET cookie_path = :cookie_path, "
                        "    cookie_count = :cookie_count, "
                        "    channel_name = :channel_name, "
                        "    is_active = 1, "
                        "    updated_at = NOW() "
                        "WHERE email = :email"
                    ),
                    {
                        "cookie_path": cookie_path,
                        "cookie_count": cookie_count,
                        "channel_name": channel_name,
                        "email": email,
                    },
                )
            else:
                session.execute(
                    text(
                        "INSERT INTO cookie_accounts "
                        "(email, cookie_path, cookie_count, channel_name, is_active) "
                        "VALUES (:email, :cookie_path, :cookie_count, :channel_name, 1)"
                    ),
                    {
                        "email": email,
                        "cookie_path": cookie_path,
                        "cookie_count": cookie_count,
                        "channel_name": channel_name,
                    },
                )

            session.commit()
            logger.info(f"Cookie account {email} saved to DB.")
    except Exception as e:
        logger.error(f"Gagal simpan cookie account ke DB: {e}")
    finally:
        sync_engine.dispose()

@dataclass
class ScanResult:
    """Result of a comment scan and delete operation."""
    scanned: int = 0
    detected: int = 0
    deleted: int = 0
    errors: int = 0
    comments: list = field(default_factory=list)
    judi_comments: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scanned": self.scanned,
            "detected": self.detected,
            "deleted": self.deleted,
            "errors": self.errors,
            "judi_comments": self.judi_comments,
        }

def _sse_event(event: str, data: dict) -> str:
    """Format SSE event string."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

class AutoDeleteService:
    """
    Main service for auto-deleting gambling comments on YouTube.

    Flow:
      - Open a browser and log in via stored cookies
      - Navigate to the video comments page
      - Capture the internal API context
      - Fetch all comments via the API
      - Run predictions directly via model_service (in-process, no HTTP)
      - Delete gambling comments via DOM batch delete
    """

    def __init__(
        self,
        email: str | None = None,
        cookie_path: str | None = None,
        threshold: float = 0.7,
        headless: bool = True,
    ):
        self.email = email
        self.threshold = threshold
        self.headless = headless
        self.cookie_mgr = CookieManager(
            email=email,
            cookie_path=cookie_path,
        )
        self._driver: Optional[webdriver.Chrome] = None
        self._yt_api: Optional[YouTubeStudioAPI] = None

    # Lifecycle 
    def start_browser(self) -> bool:
        """Start Chrome browser."""
        logger.info("Memulai browser Chrome...")
        self._driver = create_driver(
            headless=self.headless,
            enable_network_capture=True,
            email=self.email,
        )

        if not self.cookie_mgr.exists():
            logger.error("Cookie tidak ditemukan! Jalankan save_cookies.py dulu.")
            return False

        self._yt_api = YouTubeStudioAPI(self._driver)
        self._yt_api.enable_network_capture()
        return True

    def stop_browser(self):
        """Close the browser."""
        if self._driver:
            self._driver.quit()
            self._driver = None
            self._yt_api = None
            logger.info("Browser ditutup.")

    def __enter__(self):
        self.start_browser()
        return self

    def __exit__(self, *args):
        self.stop_browser()

    # Login Flow (SSE) 
    @staticmethod
    def login_stream(
        email: str,
        password: str,
        headless: bool = True,
        timeout: int = 120,
    ) -> Generator[str, None, None]:
        """
        Automatically log in to a Google account via browser and stream SSE events.

        Flow:
          - Open a browser
          - Navigate to the Google login page
          - Auto-fill email and click Next
          - Auto-fill password and click Next
          - Wait for the redirect to YouTube Studio
          - Save cookies to cookies/{email}/youtube_cookies.json
          - Store the cookie path in the database (cookie_accounts table)

        Yields SSE events:
          - status  → progress update
          - done    → {logged_in, email, cookies_saved, cookie_count}
          - error   → error message
        """
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException

        driver = None
        email_lower = email.strip().lower()

        try:
            yield _sse_event("status", {
                "step": "browser",
                "message": "Memulai browser untuk login...",
            })

            driver = create_driver(headless=headless, enable_network_capture=False, email=email_lower)
            wait = WebDriverWait(driver, 30)

            # Open the Google login page
            yield _sse_event("status", {
                "step": "navigate",
                "message": "Membuka halaman login Google...",
            })

            driver.get("https://accounts.google.com/ServiceLogin?service=youtube")
            wait_page_ready(driver)
            time.sleep(2)

            # Helper: klik tombol Lewati / Skip jika muncul
            def try_click_skip():
                from selenium.webdriver.common.by import By

                # Jangan klik Skip jika sedang di halaman verifikasi 2 langkah (2FA)
                try:
                    page_src = driver.page_source.lower()
                    current_url = driver.current_url.lower()
                    two_step_signals = [
                        "2-step verification",
                        "verifikasi 2 langkah",
                        "2 langkah",
                        "two-step",
                        "twosv",
                        "totp",
                        "authenticator",
                        "verification code",
                        "kode verifikasi",
                        "enter the code",
                        "masukkan kode",
                        "challenge",
                    ]
                    url_signals = ["challenge", "twosv", "signin/v2/challenge"]

                    if any(sig in current_url for sig in url_signals):
                        logger.debug("Skip 2FA page — tidak klik tombol Lewati/Skip")
                        return False

                    if any(sig in page_src for sig in two_step_signals):
                        logger.debug("Halaman 2FA terdeteksi — tidak klik tombol Lewati/Skip")
                        return False
                except Exception:
                    pass

                skip_selectors = [
                    # Teks tombol (case-insensitive via XPath)
                    '//button[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "lewati")]',
                    '//button[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "skip")]',
                    '//span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "lewati")]/ancestor::button',
                    '//span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "skip")]/ancestor::button',
                    # Selector CSS umum Google
                    'button[jsname="LgbsSe"]',
                    'button[data-action="skip"]',
                    '#skipButton',
                    '.skip-button',
                ]
                from selenium.webdriver.common.by import By
                for sel in skip_selectors:
                    try:
                        if sel.startswith("//"):
                            els = driver.find_elements(By.XPATH, sel)
                        else:
                            els = driver.find_elements(By.CSS_SELECTOR, sel)
                        for el in els:
                            if el.is_displayed() and el.is_enabled():
                                el.click()
                                logger.info(f"Tombol Lewati/Skip diklik (selector: {sel})")
                                return True
                    except Exception:
                        pass
                return False

            # Helper: deteksi CAPTCHA dan tunggu user menyelesaikannya manual
            def wait_for_captcha() -> bool:
                """
                Returns True jika tidak ada captcha (atau sudah selesai),
                False jika captcha muncul tapi tidak bisa diselesaikan (headless).
                """
                captcha_selectors = [
                    'img#captchaimg',
                    'input#ca',
                    'input[name="ca"]',
                    'input[aria-label*="captcha" i]',
                    'input[aria-label*="Ketik teks" i]',
                ]
                captcha_present = False
                for sel in captcha_selectors:
                    try:
                        els = driver.find_elements(By.CSS_SELECTOR, sel)
                        if any(el.is_displayed() for el in els):
                            captcha_present = True
                            break
                    except Exception:
                        pass
                return not captcha_present

            # Enter the email address
            yield _sse_event("status", {
                "step": "input_email",
                "message": f"Memasukkan email {email_lower}...",
            })

            try:
                # Google email field: id=identifierId (primary), fallback ke type=email
                email_input = None
                for locator in [
                    (By.ID, "identifierId"),
                    (By.CSS_SELECTOR, 'input[type="email"]'),
                    (By.NAME, "identifier"),
                ]:
                    try:
                        email_input = wait.until(EC.element_to_be_clickable(locator))
                        if email_input:
                            break
                    except TimeoutException:
                        continue

                if not email_input:
                    yield _sse_event("error", {
                        "message": "Field email tidak ditemukan di halaman login Google.",
                    })
                    return

                # Fokus + isi email
                email_input.click()
                time.sleep(0.5)
                email_input.clear()
                email_input.send_keys(email_lower)
                time.sleep(1)

                # Verifikasi value terisi, retry via JS jika kosong
                entered = email_input.get_attribute("value") or ""
                if entered.strip().lower() != email_lower:
                    logger.warning(f"Email belum terisi (value='{entered}'), retry via JS...")
                    driver.execute_script(
                        "arguments[0].value = arguments[1];"
                        "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        email_input, email_lower,
                    )
                    time.sleep(1)
                    entered = email_input.get_attribute("value") or ""

                if entered.strip().lower() != email_lower:
                    yield _sse_event("error", {
                        "message": f"Gagal mengisi email (value terbaca: '{entered}').",
                    })
                    return

                # Click Next
                next_btn = wait.until(
                    EC.element_to_be_clickable((By.ID, "identifierNext"))
                )
                next_btn.click()

                # Wait for the password page to appear (transition animation ~2-5 s)
                time.sleep(4)

                # Cek apakah Google menolak email (akun tidak ditemukan)
                try:
                    err_el = driver.find_element(By.CSS_SELECTOR, '.o6cuMc, .Ekjuhf, [jsname="B34EJ"]')
                    if err_el and err_el.text.strip():
                        yield _sse_event("error", {
                            "message": f"Login gagal: {err_el.text.strip()}",
                        })
                        return
                except NoSuchElementException:
                    pass

                # Deteksi CAPTCHA gambar — perlu diselesaikan manual
                if not wait_for_captcha():
                    if headless:
                        yield _sse_event("error", {
                            "message": "CAPTCHA terdeteksi. Login otomatis tidak bisa "
                                       "menyelesaikan CAPTCHA dalam mode headless. "
                                       "Aktifkan mode 'Tampilkan Browser' lalu coba lagi "
                                       "untuk mengisi CAPTCHA secara manual.",
                        })
                        return

                    # Mode non-headless: tunggu user mengisi CAPTCHA manual
                    yield _sse_event("status", {
                        "step": "captcha",
                        "message": "CAPTCHA terdeteksi! Silakan isi CAPTCHA secara manual "
                                   "di jendela browser, lalu klik Berikutnya/Next.",
                    })

                    captcha_wait_start = time.time()
                    captcha_timeout = min(timeout, 180)
                    while time.time() - captcha_wait_start < captcha_timeout:
                        time.sleep(3)
                        elapsed_cap = int(time.time() - captcha_wait_start)
                        # Captcha selesai jika field captcha sudah hilang dari DOM
                        if wait_for_captcha():
                            yield _sse_event("status", {
                                "step": "captcha",
                                "message": "CAPTCHA selesai ✓",
                            })
                            break
                        yield _sse_event("status", {
                            "step": "captcha",
                            "message": f"Menunggu CAPTCHA diisi manual... "
                                       f"({elapsed_cap}s/{captcha_timeout}s)",
                            "elapsed": elapsed_cap,
                            "timeout": captcha_timeout,
                        })
                    else:
                        yield _sse_event("error", {
                            "message": f"Timeout menunggu CAPTCHA ({captcha_timeout}s). "
                                       f"Silakan coba lagi.",
                        })
                        return

                    time.sleep(2)

                try_click_skip()
            except Exception as e:
                yield _sse_event("error", {
                    "message": f"Gagal input email: {e}",
                })
                return

            # Enter the password
            yield _sse_event("status", {
                "step": "input_password",
                "message": "Memasukkan password...",
            })

            try:
                # Wait until the password field is visible and clickable (not just present)
                pw_input = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="password"]'))
                )
                # Click first to focus, then type
                pw_input.click()
                time.sleep(0.5)
                pw_input.clear()
                pw_input.send_keys(password)
                time.sleep(1)

                # Click Next
                pw_next = wait.until(
                    EC.element_to_be_clickable((By.ID, "passwordNext"))
                )
                pw_next.click()
                time.sleep(4)
                try_click_skip()
            except Exception as e:
                yield _sse_event("error", {
                    "message": f"Gagal input password: {e}. Mungkin ada verifikasi tambahan (2FA).",
                })
                return

            # Wait for the redirect after login
            yield _sse_event("status", {
                "step": "verify",
                "message": "Menunggu login berhasil...",
            })

            start = time.time()
            logged_in = False

            while time.time() - start < timeout:
                time.sleep(3)
                elapsed = int(time.time() - start)
                current_url = driver.current_url

                # Klik tombol Lewati/Skip jika muncul di tengah proses
                try_click_skip()

                # Check whether we have left the Google login page
                if "accounts.google.com" not in current_url:
                    # Redirected — navigate to YouTube Studio
                    driver.get(YOUTUBE_STUDIO_BASE)
                    wait_page_ready(driver)
                    time.sleep(3)

                    if is_logged_in(driver):
                        logged_in = True
                        break

                # Check for an error message on the page (wrong password, etc.)
                try:
                    error_el = driver.find_element(
                        By.CSS_SELECTOR,
                        '.o6cuMc, .GQ8Pzc, [jsname="B34EJ"]'
                    )
                    if error_el and error_el.text.strip():
                        yield _sse_event("error", {
                            "message": f"Login gagal: {error_el.text.strip()}",
                        })
                        return
                except Exception:
                    pass

                yield _sse_event("status", {
                    "step": "verify",
                    "message": f"Menunggu login... ({elapsed}s/{timeout}s)",
                    "elapsed": elapsed,
                    "timeout": timeout,
                })

            if not logged_in:
                yield _sse_event("error", {
                    "message": f"Login timeout setelah {timeout} detik. "
                               f"Mungkin ada verifikasi tambahan (2FA/captcha).",
                })
                return

            yield _sse_event("status", {
                "step": "verify",
                "message": "Login berhasil ✓",
            })

            # Detect the channel name
            channel_name = _detect_channel_name(driver)

            # Save the cookies
            yield _sse_event("status", {
                "step": "save_cookies",
                "message": f"Menyimpan cookie untuk {email_lower}...",
            })

            cookie_mgr = CookieManager(email=email_lower)
            count = cookie_mgr.save(driver)

            # Save account info to the database
            yield _sse_event("status", {
                "step": "save_db",
                "message": "Menyimpan info akun ke database...",
            })

            _save_cookie_account_sync(
                email=email_lower,
                cookie_path=str(cookie_mgr.cookie_path),
                cookie_count=count,
                channel_name=channel_name,
            )

            yield _sse_event("done", {
                "logged_in": True,
                "email": email_lower,
                "channel_name": channel_name,
                "cookies_saved": True,
                "cookie_count": count,
                "cookie_path": str(cookie_mgr.cookie_path),
                "message": f"Login berhasil! {count} cookie tersimpan untuk {email_lower}.",
            })

        except Exception as e:
            logger.error(f"Login stream error: {e}", exc_info=True)
            yield _sse_event("error", {"message": str(e)})
        finally:
            if driver:
                driver.quit()
                logger.info("Browser login ditutup.")

    # ML Prediction (in-process) 
    @staticmethod
    def predict_batch(texts: list[str]) -> list[dict]:
        """
        Run batch text prediction directly via model_service (in-process).
        No HTTP call — the model is pre-loaded at FastAPI startup.
        """
        from app.core.services.model_service import predict_batch as _predict_batch
        return _predict_batch(texts)

    @staticmethod
    def predict_single(text: str) -> dict:
        """Run a single text prediction directly via model_service."""
        from app.core.services.model_service import predict as _predict
        return _predict(text)

    # Main Operations 
    def scan_video(
        self,
        video_id: str,
        dry_run: bool = False,
    ) -> ScanResult:
        """
        Scan and delete gambling comments on a given video (synchronous, non-streaming).

        Args:
            video_id: YouTube video ID
            dry_run: If True, scan without deleting

        Returns:
            ScanResult with operation statistics
        """
        result = ScanResult()

        if not self._driver or not self._yt_api:
            logger.error("Browser belum dimulai!")
            result.errors += 1
            return result

        try:
            # Log in using stored cookies
            target_url = YOUTUBE_STUDIO_VIDEO_COMMENTS.format(video_id=video_id)
            if not login_with_cookies(self._driver, self.cookie_mgr, target_url):
                logger.error("Login gagal!")
                result.errors += 1
                return result

            # Capture the internal API context
            if not self._yt_api.capture_context_with_retry():
                logger.error("Gagal capture API context!")
                result.errors += 1
                return result

            # Fetch all comments
            logger.info("Mengambil semua komentar via API...")
            all_comments = self._yt_api.fetch_all_comments(video_id)

            if not all_comments:
                logger.info("Tidak ada komentar ditemukan.")
                return result

            # Run ML predictions (in-process)
            texts = [c["text"] for c in all_comments]
            predictions = self._predict_in_batches(texts)

            if len(predictions) != len(all_comments):
                logger.error(
                    f"Jumlah prediksi ({len(predictions)}) != komentar ({len(all_comments)})"
                )
                result.errors += 1
                return result

            # Filter out gambling comments
            logger.info(f"Mulai scan {len(all_comments)} komentar...")
            logger.info("-" * 60)

            judi_comment_ids = []

            for idx, (comment, pred) in enumerate(
                zip(all_comments, predictions), 1
            ):
                result.scanned += 1
                label_str = "JUDI" if pred["label"] == 1 else "AMAN"
                confidence = (
                    pred["judi"] if pred["label"] == 1 else pred.get("normal", 0)
                )
                preview = comment["text"][:70].replace("\n", " ")

                comment_detail = {
                    "comment_id": comment["comment_id"],
                    "text": comment["text"],
                    "author": comment.get("author", ""),
                    "label": pred["label"],
                    "confidence": confidence,
                }

                if pred["label"] == 1 and pred["judi"] >= self.threshold:
                    result.detected += 1
                    result.judi_comments.append(comment_detail)
                    judi_comment_ids.append(comment["comment_id"])
                    logger.warning(
                        f"  [{idx}/{len(all_comments)}] ⚠ {label_str} ({confidence:.1%}) "
                        f'"{preview}"'
                    )
                else:
                    logger.info(
                        f"  [{idx}/{len(all_comments)}] ✓ {label_str} ({confidence:.1%}) "
                        f'"{preview}"'
                    )

                result.comments.append(comment_detail)

            # Delete the detected gambling comments
            if judi_comment_ids and not dry_run:
                logger.info("")
                logger.info("-" * 60)
                logger.info(
                    f"Menghapus {len(judi_comment_ids)} komentar judi via DOM batch delete..."
                )
                deleted = self._yt_api.delete_comments_batch(
                    judi_comment_ids,
                    judi_comments=result.judi_comments,
                )
                result.deleted = deleted
                if deleted > 0:
                    logger.info(f"✓ {deleted}/{len(judi_comment_ids)} komentar dihapus")
                else:
                    logger.error("✗ Tidak ada komentar yang berhasil dihapus!")
                    result.errors += len(judi_comment_ids)
            elif judi_comment_ids and dry_run:
                logger.info(
                    f"\n[DRY-RUN] {len(judi_comment_ids)} komentar judi akan dihapus"
                )

        except Exception as e:
            logger.error(f"Error saat scan video: {e}", exc_info=True)
            result.errors += 1

        return result

    def scan_video_stream(
        self,
        video_id: str,
        dry_run: bool = False,
    ) -> Generator[str, None, None]:
        """
        Scan and delete gambling comments, streaming SSE events throughout.

        Yields SSE-formatted strings for each stage:
          - event: status        → progress update
          - event: comment       → per-comment scan result
          - event: judi_detected → gambling comment detected
          - event: delete        → deletion result
          - event: done          → final summary
          - event: error         → error message
        """
        result = ScanResult()

        if not self._driver or not self._yt_api:
            yield _sse_event("error", {"message": "Browser belum dimulai!"})
            return

        try:
            # Log in using stored cookies
            yield _sse_event("status", {"step": "login", "message": "Login via cookie..."})
            target_url = YOUTUBE_STUDIO_VIDEO_COMMENTS.format(video_id=video_id)
            if not login_with_cookies(self._driver, self.cookie_mgr, target_url):
                yield _sse_event("error", {"message": "Login gagal! Cookie mungkin expired."})
                return

            yield _sse_event("status", {"step": "login", "message": "Login berhasil ✓"})

            # Capture the internal API context
            yield _sse_event("status", {"step": "capture_context", "message": "Menangkap API context..."})
            if not self._yt_api.capture_context_with_retry():
                yield _sse_event("error", {"message": "Gagal capture API context!"})
                return

            yield _sse_event("status", {"step": "capture_context", "message": "API context berhasil ✓"})

            # Fetch all comments for the video
            yield _sse_event("status", {"step": "fetch_comments", "message": "Mengambil komentar..."})
            all_comments = self._yt_api.fetch_all_comments(video_id)

            if not all_comments:
                yield _sse_event("status", {"step": "fetch_comments", "message": "Tidak ada komentar ditemukan."})
                yield _sse_event("done", result.to_dict())
                return

            yield _sse_event("status", {
                "step": "fetch_comments",
                "message": f"{len(all_comments)} komentar ditemukan ✓",
                "total_comments": len(all_comments),
            })

            # Run ML predictions in-process
            yield _sse_event("status", {"step": "predict", "message": "Menjalankan deteksi ML..."})

            texts = [c["text"] for c in all_comments]
            predictions = self._predict_in_batches(texts)

            if len(predictions) != len(all_comments):
                yield _sse_event("error", {
                    "message": f"Prediction mismatch: {len(predictions)} vs {len(all_comments)}"
                })
                return

            yield _sse_event("status", {"step": "predict", "message": "Deteksi ML selesai ✓"})

            # Scan each comment for gambling content
            yield _sse_event("status", {"step": "scan", "message": f"Scanning {len(all_comments)} komentar..."})

            judi_comment_ids = []

            for idx, (comment, pred) in enumerate(zip(all_comments, predictions), 1):
                result.scanned += 1
                confidence = pred["judi"] if pred["label"] == 1 else pred.get("normal", 0)

                comment_detail = {
                    "comment_id": comment["comment_id"],
                    "text": comment["text"],
                    "author": comment.get("author", ""),
                    "label": pred["label"],
                    "confidence": round(confidence, 4),
                }

                is_judi = pred["label"] == 1 and pred["judi"] >= self.threshold

                if is_judi:
                    result.detected += 1
                    result.judi_comments.append(comment_detail)
                    judi_comment_ids.append(comment["comment_id"])

                    yield _sse_event("judi_detected", {
                        "index": idx,
                        "total": len(all_comments),
                        **comment_detail,
                    })
                else:
                    yield _sse_event("comment", {
                        "index": idx,
                        "total": len(all_comments),
                        **comment_detail,
                    })

                result.comments.append(comment_detail)

            # Delete detected gambling comments
            if judi_comment_ids and not dry_run:
                yield _sse_event("status", {
                    "step": "delete",
                    "message": f"Menghapus {len(judi_comment_ids)} komentar judi...",
                })

                deleted = self._yt_api.delete_comments_batch(
                    judi_comment_ids,
                    judi_comments=result.judi_comments,
                )
                result.deleted = deleted

                if deleted > 0:
                    yield _sse_event("delete", {
                        "deleted": deleted,
                        "requested": len(judi_comment_ids),
                        "message": f"✓ {deleted}/{len(judi_comment_ids)} komentar dihapus",
                    })
                else:
                    result.errors += len(judi_comment_ids)
                    yield _sse_event("delete", {
                        "deleted": 0,
                        "requested": len(judi_comment_ids),
                        "message": "✗ Tidak ada komentar yang berhasil dihapus",
                    })
            elif judi_comment_ids and dry_run:
                yield _sse_event("status", {
                    "step": "dry_run",
                    "message": f"[DRY-RUN] {len(judi_comment_ids)} komentar judi akan dihapus",
                })

            # Emit the final summary event
            yield _sse_event("done", result.to_dict())

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            result.errors += 1
            yield _sse_event("error", {"message": str(e)})
            yield _sse_event("done", result.to_dict())

    def delete_specific_comments(
        self,
        video_id: str,
        comment_ids: list[str],
    ) -> int:
        """
        Delete specific comments by their comment_id.

        Args:
            video_id: YouTube video ID (used to navigate to the comments page)
            comment_ids: list of comment IDs to delete

        Returns:
            Number of comments successfully deleted
        """
        if not self._driver or not self._yt_api:
            logger.error("Browser belum dimulai!")
            return 0

        target_url = YOUTUBE_STUDIO_VIDEO_COMMENTS.format(video_id=video_id)
        if not login_with_cookies(self._driver, self.cookie_mgr, target_url):
            logger.error("Login gagal!")
            return 0

        self._yt_api.capture_context_with_retry()
        return self._yt_api.delete_comments_batch(comment_ids)

    def fetch_video_comments(self, video_id: str) -> list[dict]:
        """
        Fetch all comments for a video without scanning or deleting.
        """
        if not self._driver or not self._yt_api:
            logger.error("Browser belum dimulai!")
            return []

        target_url = YOUTUBE_STUDIO_VIDEO_COMMENTS.format(video_id=video_id)
        if not login_with_cookies(self._driver, self.cookie_mgr, target_url):
            logger.error("Login gagal!")
            return []

        if not self._yt_api.capture_context_with_retry():
            logger.error("Gagal capture API context!")
            return []

        return self._yt_api.fetch_all_comments(video_id)

    # Helpers 
    def _predict_in_batches(
        self, texts: list[str], batch_size: int = 50
    ) -> list[dict]:
        """Run predictions in fixed-size batches."""
        all_predictions = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            preds = self.predict_batch(batch)
            all_predictions.extend(preds)
            if len(texts) > batch_size:
                logger.info(
                    f"  Prediksi batch {i // batch_size + 1}: "
                    f"{len(all_predictions)}/{len(texts)} selesai"
                )
        return all_predictions
