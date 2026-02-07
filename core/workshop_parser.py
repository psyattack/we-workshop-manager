from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from collections import OrderedDict

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, QTimer
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget

from core.workshop_filters import WorkshopFilters


@dataclass
class WorkshopItem:
    pubfileid: str
    title: str = ""
    preview_url: str = ""
    author: str = ""
    author_url: str = ""

    # Details
    description: str = ""
    file_size: str = ""
    posted_date: str = ""
    updated_date: str = ""
    tags: dict = field(default_factory=dict)

    # Rating
    rating_star_file: str = ""   # e.g. "4-star_large", "5-star_large", "not-yet_large"
    num_ratings: str = ""        # e.g. "154"

    # State
    is_installed: bool = False
    is_downloading: bool = False


@dataclass
class WorkshopPage:
    items: List[WorkshopItem] = field(default_factory=list)
    current_page: int = 1
    total_pages: int = 1
    total_items: int = 0
    filters: Optional[WorkshopFilters] = None


class LRUCache:

    def __init__(self, max_pages: int = 20, max_items: int = 100):
        self.max_pages = max_pages
        self.max_items = max_items
        self._pages: OrderedDict[str, WorkshopPage] = OrderedDict()
        self._items: OrderedDict[str, WorkshopItem] = OrderedDict()

    def get_page(self, url: str) -> Optional[WorkshopPage]:
        if url in self._pages:
            self._pages.move_to_end(url)
            return self._pages[url]
        return None

    def set_page(self, url: str, page: WorkshopPage):
        if url in self._pages:
            self._pages.move_to_end(url)
        else:
            if len(self._pages) >= self.max_pages:
                self._pages.popitem(last=False)
        self._pages[url] = page

    def get_item(self, pubfileid: str) -> Optional[WorkshopItem]:
        if pubfileid in self._items:
            self._items.move_to_end(pubfileid)
            return self._items[pubfileid]
        return None

    def set_item(self, pubfileid: str, item: WorkshopItem):
        if pubfileid in self._items:
            self._items.move_to_end(pubfileid)
        else:
            if len(self._items) >= self.max_items:
                self._items.popitem(last=False)
        self._items[pubfileid] = item

    def clear(self):
        self._pages.clear()
        self._items.clear()


class WorkshopParser(QObject):

    page_loaded = pyqtSignal(WorkshopPage)
    item_details_loaded = pyqtSignal(WorkshopItem)
    page_loading_started = pyqtSignal()
    details_loading_started = pyqtSignal()
    loading_finished = pyqtSignal()
    login_required = pyqtSignal()
    login_successful = pyqtSignal()
    login_failed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    # Timeouts
    FETCH_TIMEOUT_MS = 10000
    POLL_INTERVAL_MS = 50
    LOGIN_CHECK_INTERVAL_MS = 500
    LOGIN_TIMEOUT_MS = 30000

    def __init__(self, account_manager, parent=None):
        super().__init__(parent)

        self.accounts = account_manager
        self._current_page_data: Optional[WorkshopPage] = None
        self._current_filters: Optional[WorkshopFilters] = None
        self._current_url: str = ""
        self._is_loading_page = False
        self._is_loading_details = False
        self._login_attempted = False
        self._request_type = "browse"
        self._current_pubfileid = ""

        self._is_logged_in = False
        self._login_in_progress = False
        self._login_check_count = 0
        self._account_index = 6

        self._poll_count = 0
        self._max_polls = self.FETCH_TIMEOUT_MS // self.POLL_INTERVAL_MS
        self._details_request_id = 0

        self._cache = LRUCache(max_pages=30, max_items=150)

        self._setup_webview()

    def _setup_webview(self):
        self._container = QWidget()
        self._container.setFixedSize(1, 1)
        self._container.hide()

        profile_path = Path.cwd() / "Cookies"
        self._profile = QWebEngineProfile("Workshop_Parser", self._container)
        self._profile.setPersistentStoragePath(str(profile_path))
        self._profile.setCachePath(str(profile_path))
        self._profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )

        self._page = QWebEnginePage(self._profile, self._container)
        self._webview = QWebEngineView(self._container)
        self._webview.setPage(self._page)
        self._webview.setFixedSize(1, 1)

        self._webview.loadFinished.connect(self._on_load_finished)

    def ensure_logged_in(self, account_index: int = 6):
        if self._login_in_progress:
            return

        if self._is_logged_in:
            self.login_successful.emit()
            return

        self._login_in_progress = True
        self._request_type = "login_check"
        self._account_index = account_index

        self._webview.load(QUrl("https://steamcommunity.com/login/home/"))

    def is_logged_in(self) -> bool:
        return self._is_logged_in

    def is_busy(self) -> bool:
        return self._is_loading_page

    def load_page(self, filters: WorkshopFilters, use_cache: bool = True):
        if self._is_loading_page:
            return

        url = filters.build_url()

        if use_cache:
            cached = self._cache.get_page(url)
            if cached:
                self._current_page_data = cached
                self.page_loaded.emit(cached)
                return

        self._is_loading_page = True
        self._is_loading_details = False
        self._request_type = "browse"
        self._current_filters = filters
        self._current_url = url

        self.page_loading_started.emit()

        self._webview.load(QUrl(url))

    def load_item_details(self, pubfileid: str, use_cache: bool = True):
        if use_cache:
            cached = self._cache.get_item(pubfileid)
            if cached and cached.file_size:
                self.item_details_loaded.emit(cached)
                return

        self._details_request_id += 1
        current_request_id = self._details_request_id

        self._is_loading_details = True
        self._current_pubfileid = pubfileid
        self._poll_count = 0

        self.details_loading_started.emit()

        current_url = self._webview.url().toString()
        if "steamcommunity.com" in current_url and not self._is_loading_page:
            self._fetch_item_details(pubfileid, current_request_id)
        else:
            self._request_type = "details_init"
            url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}"
            self._webview.load(QUrl(url))

    def _fetch_item_details(self, pubfileid: str, request_id: int):
        js_code = f"""
        (async function() {{
            window.__workshopDetailsResult = null;
            window.__workshopDetailsLoading = true;
            window.__workshopRequestId = {request_id};

            try {{
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 8000);

                const response = await fetch(
                    'https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}',
                    {{ credentials: 'include', signal: controller.signal }}
                );

                clearTimeout(timeoutId);

                if (!response.ok) {{
                    window.__workshopDetailsResult = {{ error: 'HTTP ' + response.status }};
                    window.__workshopDetailsLoading = false;
                    return;
                }}

                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');

                const result = {{
                    pubfileid: '{pubfileid}',
                    title: '',
                    description: '',
                    preview_url: '',
                    file_size: '',
                    posted_date: '',
                    updated_date: '',
                    tags: {{}},
                    rating_star_file: '',
                    num_ratings: ''
                }};

                const titleEl = doc.querySelector('.workshopItemTitle');
                if (titleEl) result.title = titleEl.innerText.trim();

                const descEl = doc.querySelector('.workshopItemDescription');
                if (descEl) result.description = descEl.innerText.trim().substring(0, 1000);

                for (const sel of ['#previewImageMain', '.workshopItemPreviewImage img', '.highlight_screenshot img']) {{
                    const el = doc.querySelector(sel);
                    if (el && el.src) {{ result.preview_url = el.src; break; }}
                }}

                // ── Rating stars ──────────────────────────────────────
                const ratingImg = doc.querySelector(
                    '#detailsHeaderRight > div > div.fileRatingDetails img'
                );
                if (ratingImg) {{
                    const src = ratingImg.getAttribute('src') || '';
                    if (src) {{
                        // "https://…/4-star_large.png?v=2" → "4-star_large"
                        const urlPath = src.split('?')[0];
                        const filename = urlPath.split('/').pop() || '';
                        result.rating_star_file = filename.replace('.png', '')
                                                          .replace('.jpg', '')
                                                          .replace('.gif', '');
                    }}
                }}

                // ── Number of ratings ─────────────────────────────────
                const numRatingsEl = doc.querySelector(
                    '#detailsHeaderRight > div > div.numRatings'
                );
                if (numRatingsEl) {{
                    const rawText = numRatingsEl.innerText.trim();
                    // "Оценок: 154" / "154 ratings" → "154"
                    const numMatch = rawText.match(/(\\d[\\d\\s,\\.]*)/);
                    if (numMatch) {{
                        result.num_ratings = numMatch[1].replace(/[\\s,\\.]/g, '');
                    }}
                }}

                const rightCol = doc.querySelector('#mainContents .col_right.responsive_local_menu');
                const text = (rightCol ? rightCol.innerText : doc.body.innerText)
                    .replace(/[\\t\\n]+/g, ' ').replace(/\\s+/g, ' ').trim();

                const sizeMatch = text.match(/File Size.*?(\\d+(?:[.,]\\d+)?)\\s*(GB|MB|KB)/i);
                if (sizeMatch) result.file_size = sizeMatch[1] + ' ' + sizeMatch[2].toUpperCase();

                const postedMatch = text.match(/Posted.*?(\\d{{1,2}}\\s+\\w{{3}},?\\s*(?:\\d{{4}})?\\s*@\\s*\\d{{1,2}}:\\d{{2}}(?:am|pm)?)/i);
                if (postedMatch) result.posted_date = postedMatch[1];

                const datePattern = /(\\d{{1,2}}\\s+\\w{{3}},?\\s*(?:\\d{{4}})?\\s*@\\s*\\d{{1,2}}:\\d{{2}}(?:am|pm)?)/gi;
                const dateMatches = [...text.matchAll(datePattern)];
                if (dateMatches.length >= 2) result.updated_date = dateMatches[1][1];

                const tagPatterns = {{
                    "Miscellaneous": /Miscellaneous:\\s*(.*?)(?=Type:|Age Rating:|Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                    "Type": /Type:\\s*(.*?)(?=Age Rating:|Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                    "Age Rating": /Age Rating:\\s*(.*?)(?=Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                    "Genre": /Genre:\\s*(.*?)(?=Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                    "Resolution": /Resolution:\\s*(.*?)(?=Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                    "Category": /Category:\\s*(.*?)(?=Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                    "Content Descriptors": /Content Descriptors:\\s*(.*?)(?=Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                    "Script Type": /Script Type:\\s*(.*?)(?=Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                    "Asset Type": /Asset Type:\\s*(.*?)(?=Asset Genre:|File Size|Posted|$)/i,
                    "Asset Genre": /Asset Genre:\\s*(.*?)(?=File Size|Posted|$)/i
                }};

                for (const [key, pattern] of Object.entries(tagPatterns)) {{
                    const match = text.match(pattern);
                    if (match && match[1]) {{
                        const value = match[1].trim();
                        if (value && value.length < 100) result.tags[key] = value;
                    }}
                }}

                window.__workshopDetailsResult = result;
            }} catch (err) {{
                window.__workshopDetailsResult = {{ error: err.name === 'AbortError' ? 'Timeout' : err.message }};
            }}

            window.__workshopDetailsLoading = false;
        }})();
        """

        self._page.runJavaScript(js_code)
        self._poll_details_result(request_id)

    def _poll_details_result(self, request_id: int):
        if request_id != self._details_request_id:
            return

        self._poll_count += 1
        if self._poll_count > self._max_polls:
            self._is_loading_details = False
            self.loading_finished.emit()
            self.error_occurred.emit("Details fetch timeout")
            return

        js = f"""
        (function() {{
            if (window.__workshopRequestId !== {request_id}) {{
                return {{ cancelled: true }};
            }}
            if (window.__workshopDetailsLoading === false) {{
                const result = window.__workshopDetailsResult;
                window.__workshopDetailsResult = null;
                return result;
            }}
            return null;
        }})();
        """
        self._page.runJavaScript(js, lambda result: self._check_details_result(result, request_id))

    def _check_details_result(self, result, request_id: int):
        if request_id != self._details_request_id:
            return

        if result is None:
            QTimer.singleShot(self.POLL_INTERVAL_MS, lambda: self._poll_details_result(request_id))
        elif isinstance(result, dict) and result.get("cancelled"):
            return
        else:
            self._on_details_parsed(result)

    def _on_load_finished(self, ok: bool):
        current_url = self._webview.url().toString()

        if self._request_type in ["login_check", "login"]:
            if "/login" not in current_url:
                self._login_in_progress = False
                self._is_logged_in = True
                self.login_successful.emit()
                return

            if ok:
                self._request_type = "login"
                QTimer.singleShot(500, self._fill_login_form)
            else:
                self._login_in_progress = False
                self.login_failed.emit("Failed to load login page")
            return

        if not ok:
            self._is_loading_page = False
            self._is_loading_details = False
            self.loading_finished.emit()
            self.error_occurred.emit("Failed to load page")
            return

        if "/login" in current_url:
            self._handle_login()
            return

        if self._request_type == "browse":
            QTimer.singleShot(500, self._parse_browse_page)
        elif self._request_type == "details_init":
            QTimer.singleShot(100, lambda: self._fetch_item_details(
                self._current_pubfileid,
                self._details_request_id
            ))

    def _handle_login(self):
        if self._login_attempted:
            self.login_required.emit()
            self._is_loading_page = False
            self._is_loading_details = False
            self.loading_finished.emit()
            return

        self._login_attempted = True
        self._fill_login_form()

    def _fill_login_form(self, attempts: int = 0):
        if attempts > 20:
            print("[Parser] Login form not found")
            self._login_in_progress = False
            self.login_failed.emit("Login form not found")
            return

        username, password = self.accounts.get_credentials(self._account_index)

        if not username or not password:
            print("[Parser] No credentials")
            self._login_in_progress = False
            self.login_failed.emit("No credentials")
            self.login_required.emit()
            return

        username_escaped = username.replace("\\", "\\\\").replace('"', '\\"')
        password_escaped = password.replace("\\", "\\\\").replace('"', '\\"')

        js = f"""
        (function() {{
            const loginInput = document.querySelector('input[type="text"]');
            const passwordInput = document.querySelector('input[type="password"]');

            if (!loginInput || !passwordInput) {{
                return {{ ready: false }};
            }}

            function fillInput(input, value) {{
                input.focus();
                const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                setter.call(input, value);
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}

            fillInput(loginInput, "{username_escaped}");
            fillInput(passwordInput, "{password_escaped}");

            let submitBtn = document.querySelector('button[type="submit"]');
            if (!submitBtn) {{
                for (const btn of document.querySelectorAll('button')) {{
                    if (btn.innerText.toLowerCase().includes('sign in')) {{
                        submitBtn = btn;
                        break;
                    }}
                }}
            }}

            if (submitBtn) {{
                submitBtn.disabled = false;
                submitBtn.click();
                return {{ ready: true, clicked: true }};
            }}

            return {{ ready: true, clicked: false }};
        }})();
        """

        def on_result(result):
            if not result or not result.get("ready"):
                QTimer.singleShot(250, lambda: self._fill_login_form(attempts + 1))
                return

            if result.get("clicked"):
                self._login_check_count = 0
                QTimer.singleShot(2000, self._check_login_success)
            else:
                self._login_in_progress = False
                self.login_failed.emit("Submit button not found")

        self._page.runJavaScript(js, on_result)

    def _check_login_success(self):
        self._login_check_count += 1
        max_checks = self.LOGIN_TIMEOUT_MS // self.LOGIN_CHECK_INTERVAL_MS

        if self._login_check_count > max_checks:
            self._login_in_progress = False
            self.login_failed.emit("Login timeout")
            return

        current_url = self._webview.url().toString()

        if "/login" not in current_url:
            self._login_in_progress = False
            self._is_logged_in = True
            self.login_successful.emit()
            return

        check_js = """
        (function() {
            const err = document.querySelector('[class*="error"], [class*="Error"]');
            const guard = document.querySelector('[class*="guard"], [class*="twofactor"], [class*="authcode"]');
            return {
                hasError: !!(err && err.innerText.trim()),
                errorText: err ? err.innerText.trim().substring(0, 100) : '',
                hasGuard: !!guard
            };
        })();
        """

        def on_check(result):
            if result and result.get("hasGuard"):
                self._login_in_progress = False
                self.login_failed.emit("Steam Guard required")
                self.login_required.emit()
                return

            if result and result.get("hasError"):
                self._login_in_progress = False
                self.login_failed.emit(result.get("errorText", "Login error"))
                return

            QTimer.singleShot(self.LOGIN_CHECK_INTERVAL_MS, self._check_login_success)

        self._page.runJavaScript(check_js, on_check)

    def _parse_browse_page(self):
        js_code = """
        (function() {
            const result = {
                items: [],
                current_page: 1,
                total_pages: 1,
                total_items: 0
            };

            const containers = document.querySelectorAll('.workshopItem, .workshopItemCollection');
            result.items = Array.from(containers).map(item => {
                try {
                    const link = item.querySelector('a[href*="filedetails"]');
                    if (!link) return null;
                    const href = link.href || '';
                    const idMatch = href.match(/id=(\\d+)/);
                    if (!idMatch) return null;
                    const pubfileid = idMatch[1];

                    let title = '';
                    const titleEl = item.querySelector('.workshopItemTitle');
                    if (titleEl) title = titleEl.innerText.trim();

                    let previewUrl = '';
                    const imgEl = item.querySelector('img');
                    if (imgEl) previewUrl = imgEl.src || imgEl.dataset.src || '';

                    let author = '';
                    let authorUrl = '';
                    const authorEl = item.querySelector('.workshopItemAuthorName a');
                    if (authorEl) {
                        author = authorEl.innerText.trim();
                        authorUrl = authorEl.href || '';
                    }

                    return {
                        pubfileid,
                        title: title || ('Wallpaper ' + pubfileid),
                        preview_url: previewUrl,
                        author,
                        author_url: authorUrl
                    };
                } catch (e) {
                    return null;
                }
            }).filter(Boolean);

            const urlParams = new URLSearchParams(window.location.search);
            result.current_page = parseInt(urlParams.get('p') || '1');

            const pagingInfo = document.querySelector('.workshopBrowsePagingInfo');
            if (pagingInfo) {
                const text = pagingInfo.innerText;
                const match = text.match(/(\\d+)[\\s\\-–](\\d+)\\s+(?:of|из)\\s+([\\d,\\. ]+)/i);
                if (match) {
                    const start = parseInt(match[1].replace(/[,\\.\\s]/g, ''));
                    const end = parseInt(match[2].replace(/[,\\.\\s]/g, ''));
                    const total = parseInt(match[3].replace(/[,\\.\\s]/g, ''));
                    result.total_items = total;
                    const itemsPerPage = end - start + 1;
                    result.total_pages = Math.ceil(total / itemsPerPage);
                }
            }

            if (result.items.length > 0 && result.total_items === 0) {
                const itemsPerPage = 15;
                result.total_items = Math.max(result.items.length, result.current_page * itemsPerPage);
                result.total_pages = Math.max(result.current_page, Math.ceil(result.total_items / itemsPerPage));
            }

            result.current_page = Math.min(result.current_page, result.total_pages);
            result.total_pages = Math.max(1, result.total_pages);

            return result;
        })();
        """
        self._page.runJavaScript(js_code, self._on_browse_parsed)

    def _on_browse_parsed(self, result):
        self._is_loading_page = False
        self.loading_finished.emit()

        if not result:
            self.error_occurred.emit("Failed to parse page")
            return

        items = []
        for item_data in result.get("items", []):
            item = WorkshopItem(
                pubfileid=item_data.get("pubfileid", ""),
                title=item_data.get("title", ""),
                preview_url=item_data.get("preview_url", ""),
                author=item_data.get("author", ""),
                author_url=item_data.get("author_url", "")
            )
            items.append(item)
            self._cache.set_item(item.pubfileid, item)

        page_data = WorkshopPage(
            items=items,
            current_page=result.get("current_page", 1),
            total_pages=max(1, result.get("total_pages", 1)),
            total_items=result.get("total_items", 0),
            filters=self._current_filters
        )

        self._cache.set_page(self._current_url, page_data)
        self._current_page_data = page_data
        self.page_loaded.emit(page_data)

    def _on_details_parsed(self, result):
        self._is_loading_details = False
        self.loading_finished.emit()

        if not result:
            self.error_occurred.emit("Failed to parse details")
            return

        if isinstance(result, dict) and "error" in result:
            print(f"[Parser] Fetch error: {result['error']}")
            self.error_occurred.emit(f"Fetch failed: {result['error']}")
            return

        pubfileid = result.get("pubfileid", self._current_pubfileid)
        existing = self._cache.get_item(pubfileid)

        item = WorkshopItem(
            pubfileid=pubfileid,
            title=result.get("title", "") or (existing.title if existing else ""),
            preview_url=result.get("preview_url", "") or (existing.preview_url if existing else ""),
            description=result.get("description", ""),
            file_size=result.get("file_size", ""),
            posted_date=result.get("posted_date", ""),
            updated_date=result.get("updated_date", ""),
            tags=result.get("tags", {}),
            rating_star_file=result.get("rating_star_file", ""),
            num_ratings=result.get("num_ratings", ""),
            author=existing.author if existing else "",
            author_url=existing.author_url if existing else ""
        )

        self._cache.set_item(pubfileid, item)
        self.item_details_loaded.emit(item)

    def is_loading(self) -> bool:
        return self._is_loading_page or self._is_loading_details

    def get_current_page_data(self) -> Optional[WorkshopPage]:
        return self._current_page_data

    def get_cached_item(self, pubfileid: str) -> Optional[WorkshopItem]:
        return self._cache.get_item(pubfileid)

    def clear_cache(self):
        self._cache.clear()

    def cleanup(self):
        try:
            if hasattr(self, '_webview'):
                self._webview.setPage(None)
            if hasattr(self, '_container'):
                self._container.deleteLater()
        except RuntimeError:
            pass
