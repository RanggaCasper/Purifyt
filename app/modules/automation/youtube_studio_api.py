import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

from app.core.logging import get_logger
from app.modules.automation.browser_driver import (
    wait_page_ready,
    YOUTUBE_STUDIO_VIDEO_COMMENTS,
    YOUTUBE_STUDIO_COMMENTS,
)

logger = get_logger(__name__)

# Timing
ACTION_DELAY = 1.5
SCROLL_PAUSE = 3.0

# JS templates for fetch() calls executed inside Chrome
_JS_FETCH_COMMENTS = """
    var callback = arguments[arguments.length - 1];
    var ctx = arguments[0];
    var videoId = arguments[1];
    var continuation = arguments[2];

    var sapisid = '';
    document.cookie.split(';').forEach(function(c) {
        c = c.trim();
        if (c.startsWith('SAPISID=')) sapisid = c.substring(8);
    });
    var origin = 'https://studio.youtube.com';
    var ts = Math.floor(Date.now() / 1000);
    var encoder = new TextEncoder();

    crypto.subtle.digest('SHA-1', encoder.encode(ts + ' ' + sapisid + ' ' + origin))
    .then(function(hash) {
        var hex = Array.from(new Uint8Array(hash)).map(function(b) {
            return b.toString(16).padStart(2, '0');
        }).join('');
        var auth = 'SAPISIDHASH ' + ts + '_' + hex + ' ' +
                   'SAPISID1PHASH ' + ts + '_' + hex + '_u ' +
                   'SAPISID3PHASH ' + ts + '_' + hex + '_u';

        var visitorData = (typeof ytcfg !== 'undefined') ? ytcfg.get('VISITOR_DATA') || '' : '';
        var clientVer = (typeof ytcfg !== 'undefined') ? ytcfg.get('INNERTUBE_CLIENT_VERSION') || '' : '';
        var pageCl = (typeof ytcfg !== 'undefined') ? ytcfg.get('PAGE_CL') || '' : '';
        var pageLabel = (typeof ytcfg !== 'undefined') ? ytcfg.get('PAGE_BUILD_LABEL') || '' : '';
        var delegation = ctx.user && ctx.user.serializedDelegationContext || '';

        var body = { context: ctx };
        if (continuation) {
            body.continuation = continuation;
        } else {
            body.sortOrder = 'NEWEST';
            body.searchQuery = '';
            body.maxReplies = 10;
            body.videoId = videoId;
            body.moderationState = 'PUBLISHED';
            body.commentsFilter = {sortBy: 'SORT_BY_NEWEST'};
        }

        var headers = {
            'accept': '*/*',
            'authorization': auth,
            'content-type': 'application/json',
            'x-goog-authuser': '0',
            'x-goog-visitor-id': visitorData,
            'x-origin': origin,
            'x-youtube-client-name': '62',
            'x-youtube-client-version': clientVer,
            'x-youtube-delegation-context': delegation,
            'x-youtube-page-cl': String(pageCl),
            'x-youtube-page-label': pageLabel,
            'x-youtube-time-zone': 'Asia/Jakarta',
            'x-youtube-utc-offset': '420'
        };

        return fetch('https://studio.youtube.com/youtubei/v1/comment/get_comments?alt=json', {
            method: 'POST', headers: headers,
            body: JSON.stringify(body),
            credentials: 'include'
        });
    })
    .then(function(r) { return r.json(); })
    .then(function(data) { callback(data); })
    .catch(function(e) { callback({_error: e.toString()}); });
"""

# JS to scan the DOM and return a mapping of commentId → thread index.
# No clicks performed — identification only.
_JS_FIND_COMMENT_THREADS = """
    var judiIds = new Set(arguments[0]);
    var result = {found: [], notFound: [], domIds: [], totalThreads: 0};
    var threads = document.querySelectorAll('ytcp-comment-thread');
    result.totalThreads = threads.length;

    for (var i = 0; i < threads.length; i++) {
        var thread = threads[i];
        var comment = thread.querySelector('ytcp-comment');
        if (!comment) continue;

        var commentId = null;
        try {
            if (comment.data && comment.data.commentId) {
                commentId = comment.data.commentId;
            }
        } catch(e) {}

        if (commentId) result.domIds.push(commentId);
        if (commentId && judiIds.has(commentId)) {
            result.found.push({commentId: commentId, index: i});
        }
    }

    judiIds.forEach(function(id) {
        var isFound = result.found.some(function(f) { return f.commentId === id; });
        if (!isFound) result.notFound.push(id);
    });

    return result;
"""

_JS_SCROLL_DOWN = """
    var container = document.querySelector('ytcp-activity-section');
    if (container) {
        container.scrollTop = container.scrollHeight;
        return 'ytcp-activity-section:' + container.scrollHeight;
    }
    window.scrollTo(0, document.documentElement.scrollHeight);
    return 'window';
"""

_JS_GET_CONTAINER_HEIGHT = """
    var container = document.querySelector('ytcp-activity-section');
    return container ? container.scrollHeight : document.documentElement.scrollHeight;
"""

# YouTubeStudioAPI class
class YouTubeStudioAPI:
    """
    Interface to the YouTube Studio internal API via Selenium and CDP.

    Features:
      - Capture API context from network traffic
      - Fetch all comments (with pagination)
      - Delete comments via DOM batch delete
    """

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self._captured_context: Optional[dict] = None
        self._captured_headers: Optional[dict] = None
        self._get_comments_request_ids: list[str] = []
        self._captured_request_body: Optional[dict] = None

        # Debug log file
        self._log_dir = Path("logs")
        self._log_dir.mkdir(exist_ok=True)
        self._debug_log_path = self._log_dir / "batch_delete_debug.log"

    def _debug_log(self, msg: str):
        """Write a debug log entry to file for post-analysis."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] {msg}\n"
        with open(self._debug_log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def _dump_dom_threads(self, judi_ids: set[str]) -> list[dict]:
        """Dump all threads currently in the DOM with their commentId, text preview, and checkbox state."""
        js_dump = """
            var judiIds = new Set(arguments[0]);
            var threads = document.querySelectorAll('ytcp-comment-thread');
            var result = [];
            for (var i = 0; i < threads.length; i++) {
                var thread = threads[i];
                var comment = thread.querySelector('ytcp-comment');
                var commentId = null;
                var text = '';
                var checkboxState = 'NOT_FOUND';
                try {
                    if (comment && comment.data && comment.data.commentId) {
                        commentId = comment.data.commentId;
                    }
                } catch(e) {}
                try {
                    var el = comment ? comment.querySelector('#content-text, #plain-text, .comment-text') : null;
                    text = el ? el.textContent.trim().substring(0, 80) : '';
                } catch(e) {}
                try {
                    var cb = thread.querySelector('ytcp-checkbox-lit#batch-select, ytcp-checkbox-lit, #checkbox');
                    if (cb) {
                        var checked = cb.hasAttribute('checked') || cb.checked === true
                            || cb.getAttribute('aria-checked') === 'true';
                        checkboxState = checked ? 'CHECKED' : 'UNCHECKED';
                    }
                } catch(e) {}
                var isJudi = commentId && judiIds.has(commentId);
                result.push({
                    index: i,
                    commentId: commentId || '(null)',
                    text: text,
                    checkbox: checkboxState,
                    isJudi: isJudi
                });
            }
            return result;
        """
        try:
            return self.driver.execute_script(js_dump, list(judi_ids))
        except Exception as e:
            self._debug_log(f"DOM dump error: {e}")
            return []

    # Network Capture 

    def enable_network_capture(self):
        """Enable CDP Network capture to intercept API requests."""
        try:
            self.driver.execute_cdp_cmd("Network.enable", {})
            logger.debug("CDP Network capture diaktifkan")
        except Exception as e:
            logger.warning(f"Gagal aktifkan Network capture: {e}")

    def capture_api_context(self) -> bool:
        """
        Parse the CDP performance log to extract context from a YouTube Studio
        API request (eats, sessionInfo, delegationCtx).

        Returns True on success.
        """
        logger.info("Menangkap API context dari network traffic...")

        try:
            logs = self.driver.get_log("performance")
        except Exception as e:
            logger.error(f"Gagal baca performance log: {e}")
            return False

        logger.debug(f"  {len(logs)} log entries ditemukan")

        context_found = False
        self._get_comments_request_ids = []

        for entry in logs:
            try:
                msg = json.loads(entry["message"])["message"]
                if msg["method"] != "Network.requestWillBeSent":
                    continue

                params = msg.get("params", {})
                url = params.get("request", {}).get("url", "")

                if "youtubei/v1/" not in url:
                    continue

                if "comment/get_comments" in url:
                    req_id = params.get("requestId", "")
                    if req_id:
                        self._get_comments_request_ids.append(req_id)

                post_data = params.get("request", {}).get("postData", "")
                if not post_data:
                    continue

                body = json.loads(post_data)
                ctx = body.get("context", {})
                eats = ctx.get("request", {}).get("eats", "")

                if eats and not context_found:
                    self._captured_context = ctx
                    self._captured_headers = params.get("request", {}).get("headers", {})
                    self._captured_request_body = body
                    context_found = True
                    logger.info("API context berhasil ditangkap!")

            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        if context_found:
            logger.info(
                f"  {len(self._get_comments_request_ids)} get_comments request(s) ditemukan"
            )
        else:
            logger.warning("Tidak ada API context yang tertangkap")

        return context_found

    def capture_context_with_retry(self, max_retries: int = 3) -> bool:
        """Capture context dengan retry."""
        for attempt in range(max_retries):
            if self.capture_api_context():
                return True
            logger.info(f"  Retry capture context ({attempt + 1}/{max_retries})...")
            time.sleep(3)
        return False

    @property
    def has_context(self) -> bool:
        return self._captured_context is not None

    # Fetch Comments 

    def fetch_comments(
        self, video_id: str, continuation: str | None = None
    ) -> dict:
        """
        Fetch comments by running a fetch() call inside the Chrome browser.
        Chrome handles authentication cookies automatically.
        """
        if not self._captured_context:
            logger.error("API context belum ditangkap!")
            return {}

        self.driver.set_script_timeout(30)
        try:
            result = self.driver.execute_async_script(
                _JS_FETCH_COMMENTS,
                self._captured_context,
                video_id,
                continuation,
            )
            if result and result.get("_error"):
                logger.error(f"fetch error: {result['_error']}")
                return {}
            return result or {}
        except Exception as e:
            logger.error(f"execute_async_script error: {e}")
            return {}

    def read_initial_comments(self) -> tuple[list[dict], str | None]:
        """
        Read the initial comments from the network response cache (CDP).
        Returns (comments_list, continuation_token).
        """
        logger.info("Membaca komentar awal dari network response...")

        if not self._get_comments_request_ids:
            return [], None

        for req_id in self._get_comments_request_ids:
            try:
                resp = self.driver.execute_cdp_cmd(
                    "Network.getResponseBody", {"requestId": req_id}
                )
                data = json.loads(resp.get("body", "{}"))
                comments, continuation = self.parse_comments_response(data)
                if comments:
                    logger.info(f"  {len(comments)} komentar awal dari network cache")
                    return comments, continuation
            except Exception as e:
                logger.debug(f"  Gagal baca response {req_id}: {e}")

        return [], None

    def fetch_all_comments(self, video_id: str) -> list[dict]:
        """
        Fetch ALL comments for a video (automatic pagination).
        Returns a list of comment dicts.
        """
        all_comments = []

        # Try reading from the network response cache first
        initial_comments, continuation = self.read_initial_comments()
        if initial_comments:
            all_comments.extend(initial_comments)
            logger.info(f"  Halaman 1: {len(initial_comments)} komentar (cache)")
        else:
            logger.info("  Network cache kosong, fetch manual...")
            result = self.fetch_comments(video_id)
            initial_comments, continuation = self.parse_comments_response(result)
            all_comments.extend(initial_comments)
            logger.info(f"  Halaman 1: {len(initial_comments)} komentar (API)")

        # Pagination
        page = 1
        while continuation:
            page += 1
            result = self.fetch_comments(video_id, continuation)
            page_comments, continuation = self.parse_comments_response(result)
            all_comments.extend(page_comments)
            logger.info(
                f"  Halaman {page}: +{len(page_comments)} (total: {len(all_comments)})"
            )
            if not page_comments:
                break
            time.sleep(0.5)

        logger.info(f"Total komentar diambil: {len(all_comments)}")
        return all_comments

    # Delete Comments 

    def delete_comments_batch(
        self,
        comment_ids: list[str],
        judi_comments: list[dict] | None = None,
    ) -> int:
        """
        Delete gambling comments via DOM batch delete.

        Flow:
          - Scroll to load all comments into the DOM
          - Select checkboxes one by one (with delays)
          - Verify the selection count
          - Click the batch delete button (trash icon)
          - Confirm the delete dialog

        Args:
            comment_ids: List of comment IDs to delete
            judi_comments: Optional list of comment dicts with 'comment_id'
                           and 'text' for text-based fallback matching

        Returns:
            Number of comments successfully deleted
        """
        if not comment_ids:
            return 0

        judi_ids = set(comment_ids)

        # === START DEBUG LOG ===
        self._debug_log("=" * 70)
        self._debug_log(f"DELETE_COMMENTS_BATCH START")
        self._debug_log(f"  Jumlah comment_ids: {len(comment_ids)}")
        self._debug_log(f"  comment_ids: {comment_ids}")
        if judi_comments:
            for jc in judi_comments:
                self._debug_log(
                    f"  judi_comment: id={jc.get('comment_id', '?')[:30]} "
                    f"text=\"{jc.get('text', '')[:60]}\""
                )
        self._debug_log("=" * 70)

        logger.info(f"Mencari {len(judi_ids)} komentar di DOM untuk batch delete...")

        # Scroll to load all comments into the DOM
        self._scroll_load_all_dom_comments()

        # Dump all threads currently in the DOM
        self._debug_log("--- DOM THREAD DUMP (setelah scroll) ---")
        dom_threads = self._dump_dom_threads(judi_ids)
        for t in dom_threads:
            marker = " <<< JUDI" if t.get("isJudi") else ""
            self._debug_log(
                f"  [{t['index']:3d}] id={t['commentId'][:40]:40s} "
                f"cb={t['checkbox']:10s} "
                f"text=\"{t['text'][:60]}\"{marker}"
            )
        self._debug_log(f"  Total threads in DOM: {len(dom_threads)}")
        judi_in_dom = [t for t in dom_threads if t.get("isJudi")]
        self._debug_log(f"  Judi threads ditemukan di DOM: {len(judi_in_dom)}")
        self._debug_log("---")

        # Build a text lookup dict for fallback matching
        judi_texts = None
        if judi_comments:
            judi_texts = {
                c["comment_id"]: c["text"]
                for c in judi_comments
                if c.get("comment_id") and c.get("text")
            }

        # 3. Select checkboxes
        self._debug_log("STEP 3: _select_checkboxes()")
        selected_count = self._select_checkboxes(judi_ids, judi_texts=judi_texts)
        self._debug_log(f"  selected_count = {selected_count}")

        # Dump checkbox states after selection
        self._debug_log("--- DOM THREAD DUMP (setelah select) ---")
        dom_threads_after = self._dump_dom_threads(judi_ids)
        checked_count = 0
        for t in dom_threads_after:
            if t.get("checkbox") == "CHECKED":
                checked_count += 1
                self._debug_log(
                    f"  CHECKED [{t['index']:3d}] id={t['commentId'][:40]:40s} "
                    f"text=\"{t['text'][:60]}\""
                )
        self._debug_log(f"  Total checked di DOM: {checked_count}")
        self._debug_log("---")

        if selected_count == 0:
            self._debug_log("ABORT: selected_count == 0")
            logger.warning("Tidak ada komentar ditemukan di DOM!")
            return 0

        logger.info(f"{selected_count} komentar dipilih, memulai batch delete...")

        # Wait for the batch action bar to appear
        self._debug_log("STEP 4: _wait_batch_action_bar()")
        if not self._wait_batch_action_bar():
            self._debug_log("ABORT: batch action bar tidak muncul")
            logger.error("Batch action bar tidak muncul setelah select!")
            return 0

        # Read the batch action bar text (e.g. "X selected")
        try:
            bar_text = self.driver.execute_script("""
                var bar = document.querySelector(
                    'ytcp-comment-batch-action-bar, #batch-action-bar'
                );
                return bar ? bar.textContent.trim().substring(0, 100) : '(not found)';
            """)
            self._debug_log(f"  Batch action bar text: \"{bar_text}\"")
        except Exception:
            pass

        # Click the batch delete button (trash icon)
        self._debug_log("STEP 5: _click_batch_delete()")
        if not self._click_batch_delete():
            self._debug_log("ABORT: tombol batch delete tidak ditemukan")
            logger.error("Tombol batch delete tidak ditemukan!")
            return 0
        self._debug_log("  batch delete diklik OK")

        # Confirm the delete dialog
        self._debug_log("STEP 6: _confirm_delete_dialog()")
        if not self._confirm_delete_dialog():
            self._debug_log("  confirm dialog tidak muncul / gagal diklik")
            logger.warning("Dialog konfirmasi tidak muncul (mungkin langsung terhapus)")
        else:
            self._debug_log("  confirm dialog diklik OK")

        # Wait for the deletion to complete
        time.sleep(ACTION_DELAY * 2)
        self._debug_log(f"DELETE_COMMENTS_BATCH END: selected_count={selected_count}")
        self._debug_log("=" * 70)
        logger.info(f"Batch delete {selected_count} komentar berhasil!")
        return selected_count

    def _scroll_load_all_dom_comments(self):
        """
        Scroll ytcp-activity-section sampai semua komentar ter-load di DOM.
        Berhenti setelah scrollHeight tidak berubah selama 3 iterasi berturut-turut.
        """
        last_height = 0
        stable_count = 0
        iteration = 0
        max_iterations = 100  # safety cap

        while stable_count < 3 and iteration < max_iterations:
            iteration += 1

            # Scroll container ke bawah
            self.driver.execute_script(_JS_SCROLL_DOWN)
            time.sleep(SCROLL_PAUSE)

            current_height = self.driver.execute_script(_JS_GET_CONTAINER_HEIGHT)
            current_count = self.driver.execute_script(
                "return document.querySelectorAll('ytcp-comment-thread').length;"
            )

            logger.debug(
                f"Scroll #{iteration}: scrollHeight={current_height} "
                f"threads={current_count} stable={stable_count}/3"
            )

            if current_height == last_height:
                stable_count += 1
                logger.debug(f"  Tidak ada konten baru ({stable_count}/3)")
            else:
                stable_count = 0
                last_height = current_height
                logger.debug(f"  Loaded more comments (height: {current_height})")

        logger.debug(
            f"Scroll selesai: {iteration} iterasi, "
            f"{self.driver.execute_script('return document.querySelectorAll(\"ytcp-comment-thread\").length;')} threads di DOM"
        )

    def _select_checkboxes(self, comment_ids: set[str], judi_texts: dict[str, str] | None = None) -> int:
        """
        Select gambling comment checkboxes one by one via Python/Selenium (by commentId only).

        Strategy:
          - Identify thread positions via a JS scan (fast, no clicks)
          - Click each checkbox from Python with a delay (by DOM index)
          - Fallback: iterate all threads from Python side (by commentId)

        Args:
            comment_ids: set of comment IDs
            judi_texts: ignored (kept for backward compatibility)
        """
        total_selected = 0
        remaining_ids = set(comment_ids)  # Track IDs not yet selected

        # Phase 1: Identify thread positions via JS scan (no clicks)
        self._debug_log("  _select_checkboxes: Fase 1 - JS scan")
        try:
            scan_result = self.driver.execute_script(
                _JS_FIND_COMMENT_THREADS, list(comment_ids)
            )
        except Exception as e:
            logger.error(f"JS scan error: {e}")
            self._debug_log(f"  JS scan error: {e}")
            scan_result = None

        not_found_ids = set()  # IDs not present in the DOM (from JS scan)

        if scan_result and isinstance(scan_result, dict):
            found = scan_result.get("found", [])
            not_found = scan_result.get("notFound", [])
            dom_ids = scan_result.get("domIds", [])
            total = scan_result.get("totalThreads", 0)

            not_found_ids = set(not_found)

            self._debug_log(f"  JS scan result: found={len(found)}, notFound={len(not_found)}, totalThreads={total}")
            for f_item in found:
                self._debug_log(f"    FOUND: index={f_item['index']}, commentId={f_item['commentId'][:40]}")
            for nf_id in not_found:
                self._debug_log(f"    NOT_FOUND: {nf_id[:40]}")

            logger.info(f"DOM scan: {len(found)} cocok dari {total} thread")
            if not_found:
                logger.debug(f"  Not found IDs: {not_found[:5]}")
            if dom_ids and not_found:
                logger.debug(f"  DOM IDs sample: {dom_ids[:5]}")

            # Phase 2: Click each found checkbox by DOM index
            if found:
                self._debug_log(f"  Fase 2: _click_checkboxes_by_index({[item['index'] for item in found]})")
                selected = self._click_checkboxes_by_index(
                    [item["index"] for item in found]
                )
                self._debug_log(f"  Fase 2 result: selected={selected}")
                total_selected += selected
                # Remove found IDs from the remaining set
                for f_item in found:
                    remaining_ids.discard(f_item["commentId"])

        # Check whether any IDs are still unselected
        if remaining_ids:
            self._debug_log(f"  Masih ada {len(remaining_ids)} ID belum ter-select: {list(remaining_ids)[:5]}")

            # Phase 2b: Fallback — iterate all threads from Python side (by commentId)
            self._debug_log("  Fase 2b: _select_checkboxes_python()")
            logger.info(f"Coba Python fallback untuk {len(remaining_ids)} ID yang belum ditemukan...")
            selected = self._select_checkboxes_python(remaining_ids)
            self._debug_log(f"  Fase 2b result: selected={selected}")
            total_selected += selected
            # Update remaining IDs by removing those selected in phase 2b
            if selected > 0:
                remaining_ids -= self._last_selected_ids if hasattr(self, '_last_selected_ids') else set()

        if remaining_ids:
            self._debug_log(f"  WARNING: {len(remaining_ids)} ID masih belum ter-select setelah semua fase")
            logger.warning(f"{len(remaining_ids)} comment IDs tidak ditemukan di DOM")

        self._debug_log(f"  _select_checkboxes TOTAL: {total_selected}")
        return total_selected

    def _click_checkboxes_by_index(self, indices: list[int]) -> int:
        """
        Click checkboxes by their thread index in the DOM.
        Each click is followed by a delay so YouTube Studio can update its state.
        """
        selected = 0

        for idx in indices:
            try:
                # Re-query threads each iteration since the DOM can change
                threads = self.driver.find_elements(
                    By.CSS_SELECTOR, "ytcp-comment-thread"
                )
                if idx >= len(threads):
                    self._debug_log(f"    index {idx} OUT OF RANGE (total={len(threads)})")
                    logger.debug(f"  Index {idx} out of range ({len(threads)} threads)")
                    continue

                thread = threads[idx]
                # Log a text preview before clicking
                try:
                    text_preview = self.driver.execute_script(
                        "var c = arguments[0].querySelector('ytcp-comment');"
                        "if (!c) return '';"
                        "var el = c.querySelector('#content-text, #plain-text');"
                        "return el ? el.textContent.trim().substring(0, 60) : '';",
                        thread,
                    )
                except Exception:
                    text_preview = "?"

                self._debug_log(f"    clicking index={idx}, text=\"{text_preview}\"")
                result = self._click_checkbox_on_element(thread)
                self._debug_log(f"    click result={result}")

                if result:
                    selected += 1
                    logger.debug(f"  Checkbox {selected} selected (index {idx})")
                    # Extra delay to let YouTube Studio update its internal state
                    time.sleep(0.8)

            except Exception as e:
                self._debug_log(f"    index {idx} EXCEPTION: {e}")
                logger.debug(f"  Click by index {idx} error: {e}")

        self._debug_log(f"    _click_checkboxes_by_index DONE: {selected}/{len(indices)}")
        logger.info(f"  {selected}/{len(indices)} checkbox berhasil dipilih")
        return selected

    def _select_checkboxes_python(self, comment_ids: set[str]) -> int:
        """Fallback: select checkboxes one by one via Python/Selenium (by commentId)."""
        selected = 0
        self._last_selected_ids = set()  # Track IDs yang berhasil di-select
        threads = self.driver.find_elements(By.CSS_SELECTOR, "ytcp-comment-thread")

        for thread in threads:
            try:
                cid = self.driver.execute_script(
                    "var c = arguments[0].querySelector('ytcp-comment');"
                    "return (c && c.data && c.data.commentId) ? c.data.commentId : null;",
                    thread,
                )
                if not cid or cid not in comment_ids:
                    continue

                # Skip if the checkbox was already checked in a previous phase
                already_checked = self.driver.execute_script("""
                    var cb = arguments[0].querySelector('ytcp-checkbox-lit#batch-select, ytcp-checkbox-lit');
                    return cb && (cb.hasAttribute('checked') || cb.checked === true
                        || cb.getAttribute('aria-checked') === 'true');
                """, thread)
                if already_checked:
                    self._debug_log(f"    Python: skip {cid[:20]} (already checked)")
                    self._last_selected_ids.add(cid)  # Already selected in a previous phase
                    continue

                if self._click_checkbox_on_element(thread):
                    selected += 1
                    self._last_selected_ids.add(cid)
                    logger.debug(f"  Python selected: {cid[:20]}...")
                    # Delay to let YouTube Studio update its Polymer state
                    time.sleep(0.8)

            except Exception as e:
                logger.debug(f"Checkbox select error: {e}")

        return selected

    def _click_checkbox_on_element(self, element) -> bool:
        """Click the checkbox on a comment thread element and verify it is checked."""
        try:
            # Scroll the element into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            time.sleep(0.3)

            # Find the checkbox using YouTube Studio DOM selectors
            # Ref: ytcp-comment > #row-container > #comment-row > #body > ytcp-checkbox-lit#batch-select
            checkbox_selectors = [
                "ytcp-checkbox-lit#batch-select",
                "#batch-select",
                "ytcp-checkbox-lit",
                "#checkbox",
                "tp-yt-paper-checkbox",
                "[role='checkbox']",
                "input[type='checkbox']",
                "#select-checkbox",
            ]

            checkbox = None
            for sel in checkbox_selectors:
                try:
                    checkbox = element.find_element(By.CSS_SELECTOR, sel)
                    if checkbox:
                        break
                except NoSuchElementException:
                    continue

            if not checkbox:
                self._debug_log("      checkbox element NOT FOUND")
                logger.debug("  Checkbox tidak ditemukan di element")
                return False

            # Log which selector matched
            cb_tag = self.driver.execute_script(
                "return arguments[0].tagName + '#' + (arguments[0].id || '') + '.' + (arguments[0].className || '');",
                checkbox,
            )
            self._debug_log(f"      checkbox found: {cb_tag}")

            # Check the initial checkbox state
            pre_state = self.driver.execute_script("""
                var el = arguments[0];
                return {
                    hasChecked: el.hasAttribute('checked'),
                    checked: el.checked || false,
                    ariaChecked: el.getAttribute('aria-checked'),
                    tagName: el.tagName,
                    displayed: el.offsetParent !== null
                };
            """, checkbox)
            self._debug_log(f"      pre-click state: {json.dumps(pre_state)}")

            # Click the checkbox — Selenium click first, JS click as fallback
            click_method = "selenium"
            try:
                checkbox.click()
            except ElementClickInterceptedException:
                click_method = "js_fallback"
                self.driver.execute_script("arguments[0].click();", checkbox)
            self._debug_log(f"      click_method: {click_method}")

            time.sleep(0.5)

            # Verify the checkbox is now checked
            post_state = self.driver.execute_script("""
                var el = arguments[0];
                return {
                    hasChecked: el.hasAttribute('checked'),
                    checked: el.checked || false,
                    ariaChecked: el.getAttribute('aria-checked')
                };
            """, checkbox)
            self._debug_log(f"      post-click state: {json.dumps(post_state)}")

            is_checked = (
                post_state.get("hasChecked") is True
                or post_state.get("checked") is True
                or post_state.get("ariaChecked") == "true"
            )

            if not is_checked:
                self._debug_log("      NOT checked, retrying JS click...")
                logger.debug("  Checkbox was clicked but not yet checked, retrying...")
                # Retry with a direct JS click
                self.driver.execute_script("arguments[0].click();", checkbox)
                time.sleep(0.5)
                # Re-check
                post_state2 = self.driver.execute_script("""
                    var el = arguments[0];
                    return {
                        hasChecked: el.hasAttribute('checked'),
                        checked: el.checked || false,
                        ariaChecked: el.getAttribute('aria-checked')
                    };
                """, checkbox)
                self._debug_log(f"      retry post-click state: {json.dumps(post_state2)}")
                is_checked = (
                    post_state2.get("hasChecked") is True
                    or post_state2.get("checked") is True
                    or post_state2.get("ariaChecked") == "true"
                )

            if is_checked:
                self._debug_log("      VERIFIED: checked ✓")
                logger.debug("  Checkbox tercentang ✓")
            else:
                self._debug_log("      FAILED: NOT checked after retry ✗")
                logger.debug("  Checkbox TIDAK tercentang setelah retry")

            return is_checked

        except Exception as e:
            logger.debug(f"  Click checkbox error: {e}")
            return False

    def _wait_batch_action_bar(self) -> bool:
        """
        Wait for the batch action bar to appear after checkboxes are selected.
        The batch action bar is the toolbar showing '_ selected' and the trash icon.
        """
        bar_selectors = [
            "ytcp-comment-batch-action-bar#batch-action-bar",
            "#batch-action-bar",
            "ytcp-comment-batch-action-bar",
        ]
        for selector in bar_selectors:
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.info("Batch action bar terlihat ✓")
                time.sleep(0.5)
                return True
            except TimeoutException:
                continue

        logger.warning("Batch action bar tidak ditemukan")
        return False

    def _click_batch_delete(self) -> bool:
        """
        Click the batch delete button (trash icon) in the batch action bar.
        Ref DOM: YTCP-COMMENT-BATCH-ACTION-BAR > YTCP-COMMENT-BUTTON#remove-batch-button
                   > YTCP-ICON-BUTTON [aria-label='Delete selected comments']
        """
        # Strategy 1: Click the inner icon-button directly (most reliable)
        inner_selectors = [
            "ytcp-comment-batch-action-bar #remove-batch-button ytcp-icon-button",
            "#batch-action-bar #remove-batch-button ytcp-icon-button",
            "ytcp-comment-batch-action-bar ytcp-icon-button[aria-label*='Hapus']",
            "ytcp-comment-batch-action-bar ytcp-icon-button[aria-label*='Remove']",
            "ytcp-comment-batch-action-bar ytcp-icon-button[aria-label*='Delete']",
        ]
        for selector in inner_selectors:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].click();", btn)
                logger.info(f"Batch delete diklik via: {selector}")
                time.sleep(ACTION_DELAY)
                return True
            except TimeoutException:
                continue

        # Strategy 2: Click the outer button
        outer_selectors = [
            "#remove-batch-button",
            "ytcp-comment-button#remove-batch-button",
            "ytcp-comment-batch-action-bar #remove-batch-button",
        ]
        for selector in outer_selectors:
            try:
                btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", btn)
                logger.info(f"Batch delete diklik via: {selector}")
                time.sleep(ACTION_DELAY)
                return True
            except TimeoutException:
                continue

        # Strategy 3: XPath fallback
        xpath_selectors = [
            "//ytcp-comment-button[@id='remove-batch-button']//ytcp-icon-button",
            "//ytcp-icon-button[@aria-label='Hapus beberapa komentar']",
            "//ytcp-icon-button[contains(@aria-label, 'Hapus')]",
            "//ytcp-comment-batch-action-bar//ytcp-icon-button",
        ]
        for xpath in xpath_selectors:
            try:
                btn = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                self.driver.execute_script("arguments[0].click();", btn)
                logger.info(f"Batch delete diklik via xpath")
                time.sleep(ACTION_DELAY)
                return True
            except TimeoutException:
                continue

        logger.error("Tombol batch delete tidak ditemukan di mana pun!")
        return False

    def _confirm_delete_dialog(self) -> bool:
        """
        Wait for and confirm the delete confirmation dialog.
        Ref DOM: YTCP-CONFIRMATION-DIALOG#batch-remove-confirmation-dialog
                   > TP-YT-PAPER-DIALOG#dialog > YTCP-BUTTON#confirm-button
        """
        # Wait for the dialog to appear
        dialog_visible = False
        dialog_selectors = [
            "ytcp-confirmation-dialog#batch-remove-confirmation-dialog",
            "#batch-remove-confirmation-dialog",
            "ytcp-confirmation-dialog",
            "tp-yt-paper-dialog[aria-modal='true']",
        ]
        for selector in dialog_selectors:
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                dialog_visible = True
                logger.debug(f"Dialog ditemukan: {selector}")
                break
            except TimeoutException:
                continue

        if not dialog_visible:
            logger.debug("Dialog konfirmasi tidak muncul")
            return False

        time.sleep(0.5)  # Tunggu dialog fully rendered

        # Click the confirm button
        confirm_selectors = [
            # CSS selectors — most specific first
            (By.CSS_SELECTOR, "#batch-remove-confirmation-dialog #confirm-button"),
            (By.CSS_SELECTOR, "ytcp-confirmation-dialog #confirm-button"),
            (By.CSS_SELECTOR, "#confirm-button"),
            # XPath — more flexible fallback
            (By.XPATH, "//ytcp-button[@id='confirm-button']"),
            (By.XPATH, "//*[@slot='submit-button']"),
            (By.XPATH, "//ytcp-button[contains(., 'Hapus')]"),
            (By.XPATH, "//ytcp-button[contains(., 'Delete')]"),
            (By.XPATH, "//ytcp-button[contains(., 'Remove')]"),
            (By.XPATH, "//*[@role='dialog']//ytcp-button[contains(@class, 'primary')]"),
        ]
        for by, selector in confirm_selectors:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.driver.execute_script("arguments[0].click();", btn)
                logger.info("Konfirmasi hapus diklik ✓")
                time.sleep(ACTION_DELAY)
                return True
            except TimeoutException:
                continue

        logger.warning("Tombol konfirmasi tidak ditemukan di dialog")
        return False

    # Navigate 

    def navigate_to_video_comments(self, video_id: str):
        """Navigate to the video comments page in YouTube Studio."""
        url = YOUTUBE_STUDIO_VIDEO_COMMENTS.format(video_id=video_id)
        current = self.driver.current_url
        if f"/video/{video_id}/comments" not in current:
            logger.info(f"Navigasi ke: {url}")
            self.driver.get(url)
            wait_page_ready(self.driver)
            time.sleep(5)
        else:
            logger.info(f"Sudah di halaman komentar video {video_id}")
            time.sleep(5)

    def navigate_to_channel_comments(self, channel_id: str):
        """Navigate to the channel comments page in YouTube Studio."""
        url = YOUTUBE_STUDIO_COMMENTS.format(channel_id=channel_id)
        logger.info(f"Navigasi ke: {url}")
        self.driver.get(url)
        wait_page_ready(self.driver)
        time.sleep(5)

    # Response Parser 

    @staticmethod
    def parse_comments_response(data: dict) -> tuple[list[dict], str | None]:
        """
        Parse a get_comments API response.
        Returns (comments_list, continuation_token).

        Each comment dict contains: {comment_id, text, author, published, likes}
        """
        comments = []
        continuation = None

        if not data:
            return comments, continuation

        section = None

        # Format 1: continuationContents (pagination)
        cc = data.get("continuationContents", {})
        isc = cc.get("itemSectionContinuation", {})
        if isc:
            section = isc

        # Format 2: contents (initial load)
        if not section:
            ct = data.get("contents", {})
            isr = ct.get("itemSectionRenderer", {})
            if isr:
                section = isr

        if section:
            contents = section.get("contents", [])
            for item in contents:
                ctr = item.get("commentThreadRenderer", {})
                cr = ctr.get("comment", {}).get("commentRenderer", {})
                if not cr:
                    continue

                content_text = cr.get("contentText", {})
                if isinstance(content_text, dict):
                    runs = content_text.get("runs", [])
                    text = "".join(r.get("text", "") for r in runs)
                else:
                    text = str(content_text) if content_text else ""

                if not text.strip():
                    continue

                comment_id = cr.get("commentId", "")
                author_data = cr.get("authorText", {})
                author = (
                    author_data.get("simpleText", "")
                    if isinstance(author_data, dict)
                    else str(author_data)
                )
                published_data = cr.get("publishedTimeText", {})
                published = (
                    published_data.get("simpleText", "")
                    if isinstance(published_data, dict)
                    else ""
                )
                likes = cr.get("likeCount", 0)

                if comment_id:
                    comments.append({
                        "comment_id": comment_id,
                        "text": text.strip(),
                        "author": author,
                        "published": published,
                        "likes": likes,
                    })

            continuations = section.get("continuations", [])
            if continuations:
                cont_data = continuations[0].get("nextContinuationData", {})
                continuation = cont_data.get("continuation")

        # Format 3: comments array (fallback)
        if not comments:
            raw_comments = data.get("comments", [])
            for c in raw_comments:
                props = c.get("properties", {})
                text = props.get("content", {}).get("content", "")
                comment_id = props.get("commentId", "")
                author = props.get("authorText", "")
                if text.strip() and comment_id:
                    comments.append({
                        "comment_id": comment_id,
                        "text": text.strip(),
                        "author": author,
                        "published": "",
                        "likes": 0,
                    })
            continuation = data.get("continuation")

        return comments, continuation


