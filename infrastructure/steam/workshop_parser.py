from collections import OrderedDict
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from domain.models.workshop import WorkshopFilters, WorkshopItem, WorkshopPage
from infrastructure.steam.workshop_scripts import (
    browse_page_parse_script,
    build_item_details_fetch_script,
    build_item_details_poll_script,
    build_preload_page_script,
    build_preload_poll_script,
    login_form_fill_script,
    login_state_check_script,
)
from infrastructure.steam.workshop_url_builder import WorkshopUrlBuilder


class WorkshopPageCache:
    def __init__(self, max_pages: int = 20):
        self.max_pages = max_pages
        self._pages: OrderedDict[str, WorkshopPage] = OrderedDict()

    def get(self, url: str) -> Optional[WorkshopPage]:
        if url not in self._pages:
            return None
        self._pages.move_to_end(url)
        return self._pages[url]

    def set(self, url: str, page: WorkshopPage) -> None:
        if url in self._pages:
            self._pages.move_to_end(url)
        self._pages[url] = page

        while len(self._pages) > self.max_pages:
            self._pages.popitem(last=False)

    def clear(self) -> None:
        self._pages.clear()


class WorkshopItemCache:
    def __init__(self, max_items: int = 600):
        self.max_items = max_items
        self._items: OrderedDict[str, WorkshopItem] = OrderedDict()

    def get(self, pubfileid: str) -> Optional[WorkshopItem]:
        if pubfileid not in self._items:
            return None
        self._items.move_to_end(pubfileid)
        return self._items[pubfileid]

    def set(self, pubfileid: str, item: WorkshopItem) -> None:
        if pubfileid in self._items:
            self._items.move_to_end(pubfileid)
        self._items[pubfileid] = item

        while len(self._items) > self.max_items:
            self._items.popitem(last=False)

    def clear(self) -> None:
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
    preload_completed = pyqtSignal(str)

    FETCH_TIMEOUT_MS = 10000
    POLL_INTERVAL_MS = 50
    LOGIN_CHECK_INTERVAL_MS = 500
    LOGIN_TIMEOUT_MS = 30000

    def __init__(
        self,
        account_service,
        config_service=None,
        parent=None,
        profile_name: str = "Workshop_Parser",
    ):
        super().__init__(parent)

        self.account_service = account_service
        self.config_service = config_service
        self.profile_name = profile_name

        self.debug_webview_enabled = bool(
            config_service.get_debug_mode() if config_service else False
        )

        self._current_page_data: Optional[WorkshopPage] = None
        self._current_filters: Optional[WorkshopFilters] = None
        self._current_url = ""
        self._current_pubfileid = ""

        self._is_loading_page = False
        self._is_loading_details = False
        self._is_preloading = False

        self._is_logged_in = False
        self._login_attempted = False
        self._login_in_progress = False
        self._login_check_count = 0
        self._account_index = 6

        self._request_type = "browse"

        self._poll_count = 0
        self._max_polls = self.FETCH_TIMEOUT_MS // self.POLL_INTERVAL_MS
        self._details_request_id = 0
        self._preload_request_id = 0
        self._preload_poll_count = 0

        self._page_cache = WorkshopPageCache()
        self._item_cache = WorkshopItemCache()

        self._setup_webview()

    def _setup_webview(self) -> None:
        debug_width = 1200
        debug_height = 800

        self._container = QWidget()
        if self.debug_webview_enabled:
            self._container.setFixedSize(debug_width, debug_height)
            self._container.show()
        else:
            self._container.setFixedSize(1, 1)
            self._container.hide()

        profile_path = Path.cwd() / "cookies" / self.profile_name

        self._profile = QWebEngineProfile(self.profile_name, self._container)
        self._profile.setPersistentStoragePath(str(profile_path))
        self._profile.setCachePath(str(profile_path / "cache"))
        self._profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )

        self._page = QWebEnginePage(self._profile, self._container)
        self._webview = QWebEngineView(self._container)
        self._webview.setPage(self._page)

        if self.debug_webview_enabled:
            layout = QVBoxLayout(self._container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self._webview)
            self._webview.setFixedSize(debug_width, debug_height)
            self._webview.show()
        else:
            self._webview.setFixedSize(1, 1)

        self._webview.loadFinished.connect(self._on_load_finished)

    def ensure_logged_in(self, account_index: int = 6) -> None:
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

    def is_loading(self) -> bool:
        return self._is_loading_page or self._is_loading_details

    def get_current_page_data(self) -> Optional[WorkshopPage]:
        return self._current_page_data

    def get_cached_item(self, pubfileid: str) -> Optional[WorkshopItem]:
        return self._item_cache.get(pubfileid)

    def clear_cache(self) -> None:
        self._page_cache.clear()
        self._item_cache.clear()

    def clear_cookies(self) -> None:
        try:
            if hasattr(self, "_profile") and self._profile is not None:
                self._profile.cookieStore().deleteAllCookies()
        except Exception:
            pass

    def load_page(self, filters: WorkshopFilters, use_cache: bool = True) -> None:
        if self._is_loading_page:
            return

        url = WorkshopUrlBuilder.build(filters)

        if use_cache:
            cached_page = self._page_cache.get(url)
            if cached_page:
                self._current_page_data = cached_page
                self.page_loaded.emit(cached_page)
                return

        self._is_loading_page = True
        self._is_loading_details = False
        self._request_type = "browse"
        self._current_filters = filters
        self._current_url = url

        self.page_loading_started.emit()
        self._webview.load(QUrl(url))

    def preload_next_page(
        self,
        current_filters: WorkshopFilters,
        callback: Optional[Callable[[bool], None]] = None,
    ) -> None:
        if self._is_preloading:
            if callback:
                callback(False)
            return

        next_page = current_filters.page + 1
        next_filters = WorkshopFilters(
            search=current_filters.search,
            sort=current_filters.sort,
            days=current_filters.days,
            category=current_filters.category,
            type_tag=current_filters.type_tag,
            age_rating=current_filters.age_rating,
            resolution=current_filters.resolution,
            misc_tags=list(current_filters.misc_tags),
            genre_tags=list(current_filters.genre_tags),
            excluded_misc_tags=list(current_filters.excluded_misc_tags),
            excluded_genre_tags=list(current_filters.excluded_genre_tags),
            asset_type=current_filters.asset_type,
            asset_genre=current_filters.asset_genre,
            script_type=current_filters.script_type,
            required_flags=list(current_filters.required_flags),
            page=next_page,
        )

        next_url = WorkshopUrlBuilder.build(next_filters)
        cached_page = self._page_cache.get(next_url)
        if cached_page:
            if callback:
                callback(True)
            return

        self._is_preloading = True
        self._preload_request_id += 1
        request_id = self._preload_request_id
        self._preload_poll_count = 0

        self._fetch_page_in_background(next_url, next_filters, request_id, callback)

    def _fetch_page_in_background(
        self,
        url: str,
        filters: WorkshopFilters,
        request_id: int,
        callback: Optional[Callable[[bool], None]],
    ) -> None:
        script = build_preload_page_script(url, request_id)
        self._page.runJavaScript(script)
        self._poll_preload_result(url, filters, request_id, callback)

    def _poll_preload_result(
        self,
        url: str,
        filters: WorkshopFilters,
        request_id: int,
        callback: Optional[Callable[[bool], None]],
    ) -> None:
        if request_id != self._preload_request_id:
            return

        self._preload_poll_count += 1
        if self._preload_poll_count > self._max_polls:
            self._is_preloading = False
            if callback:
                callback(False)
            return

        script = build_preload_poll_script(request_id)
        self._page.runJavaScript(
            script,
            lambda result: self._check_preload_result(result, url, filters, request_id, callback),
        )

    def _check_preload_result(
        self,
        result,
        url: str,
        filters: WorkshopFilters,
        request_id: int,
        callback: Optional[Callable[[bool], None]],
    ) -> None:
        if request_id != self._preload_request_id:
            return

        if result is None:
            QTimer.singleShot(
                self.POLL_INTERVAL_MS,
                lambda: self._poll_preload_result(url, filters, request_id, callback),
            )
            return

        if isinstance(result, dict) and result.get("cancelled"):
            self._is_preloading = False
            if callback:
                callback(False)
            return

        if isinstance(result, dict) and "error" in result:
            self._is_preloading = False
            if callback:
                callback(False)
            return

        self._on_preload_parsed(result, url, filters, callback)

    def _on_preload_parsed(
        self,
        result,
        url: str,
        filters: WorkshopFilters,
        callback: Optional[Callable[[bool], None]],
    ) -> None:
        self._is_preloading = False

        if not result or not result.get("items"):
            if callback:
                callback(False)
            return

        items: list[WorkshopItem] = []
        for item_data in result.get("items", []):
            item = WorkshopItem(
                pubfileid=item_data.get("pubfileid", ""),
                title=item_data.get("title", ""),
                preview_url=item_data.get("preview_url", ""),
                author=item_data.get("author", ""),
                author_url=item_data.get("author_url", ""),
            )
            items.append(item)
            self._item_cache.set(item.pubfileid, item)

        page_data = WorkshopPage(
            items=items,
            current_page=result.get("current_page", 1),
            total_pages=max(1, result.get("total_pages", 1)),
            total_items=result.get("total_items", 0),
            filters=filters,
        )
        self._page_cache.set(url, page_data)

        self.preload_completed.emit(url)
        if callback:
            callback(True)

    def load_item_details(self, pubfileid: str, use_cache: bool = True) -> None:
        if use_cache:
            cached_item = self._item_cache.get(pubfileid)
            if cached_item and cached_item.file_size:
                self.item_details_loaded.emit(cached_item)
                return

        self._details_request_id += 1
        request_id = self._details_request_id

        self._is_loading_details = True
        self._current_pubfileid = pubfileid
        self._poll_count = 0

        self.details_loading_started.emit()

        current_url = self._webview.url().toString()
        if "steamcommunity.com" in current_url and not self._is_loading_page:
            self._fetch_item_details(pubfileid, request_id)
            return

        self._request_type = "details_init"
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}"
        self._webview.load(QUrl(url))

    def _fetch_item_details(self, pubfileid: str, request_id: int) -> None:
        script = build_item_details_fetch_script(pubfileid, request_id)
        self._page.runJavaScript(script)
        self._poll_details_result(request_id)

    def _poll_details_result(self, request_id: int) -> None:
        if request_id != self._details_request_id:
            return

        self._poll_count += 1
        if self._poll_count > self._max_polls:
            self._is_loading_details = False
            self.loading_finished.emit()
            self.error_occurred.emit("Details fetch timeout")
            return

        script = build_item_details_poll_script(request_id)
        self._page.runJavaScript(
            script,
            lambda result: self._check_details_result(result, request_id),
        )

    def _check_details_result(self, result, request_id: int) -> None:
        if request_id != self._details_request_id:
            return

        if result is None:
            QTimer.singleShot(
                self.POLL_INTERVAL_MS,
                lambda: self._poll_details_result(request_id),
            )
            return

        if isinstance(result, dict) and result.get("cancelled"):
            return

        self._on_details_parsed(result)

    def _on_load_finished(self, ok: bool) -> None:
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
            QTimer.singleShot(50, self._parse_browse_page)
        elif self._request_type == "details_init":
            QTimer.singleShot(
                20,
                lambda: self._fetch_item_details(self._current_pubfileid, self._details_request_id),
            )

    def _handle_login(self) -> None:
        if self._login_attempted:
            self.login_required.emit()
            self._is_loading_page = False
            self._is_loading_details = False
            self.loading_finished.emit()
            return

        self._login_attempted = True
        self._fill_login_form()

    def _fill_login_form(self, attempts: int = 0) -> None:
        if attempts > 20:
            self._login_in_progress = False
            self.login_failed.emit("Login form not found")
            return

        username, password = self.account_service.get_credentials(self._account_index)
        if not username or not password:
            self._login_in_progress = False
            self.login_failed.emit("No credentials")
            self.login_required.emit()
            return

        script = login_form_fill_script(username, password)

        def on_result(result):
            if not result or not result.get("ready"):
                QTimer.singleShot(250, lambda: self._fill_login_form(attempts + 1))
                return

            if result.get("clicked"):
                self._login_check_count = 0
                QTimer.singleShot(2000, self._check_login_success)
                return

            self._login_in_progress = False
            self.login_failed.emit("Submit button not found")

        self._page.runJavaScript(script, on_result)

    def _check_login_success(self) -> None:
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
            self.clear_cache()
            self.login_successful.emit()
            return

        script = login_state_check_script()

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

        self._page.runJavaScript(script, on_check)

    def _parse_browse_page(self) -> None:
        self._page.runJavaScript(browse_page_parse_script(), self._on_browse_parsed)

    def _on_browse_parsed(self, result) -> None:
        self._is_loading_page = False
        self.loading_finished.emit()

        if not result:
            self.error_occurred.emit("Failed to parse page")
            return

        items: list[WorkshopItem] = []
        for item_data in result.get("items", []):
            item = WorkshopItem(
                pubfileid=item_data.get("pubfileid", ""),
                title=item_data.get("title", ""),
                preview_url=item_data.get("preview_url", ""),
                author=item_data.get("author", ""),
                author_url=item_data.get("author_url", ""),
            )
            items.append(item)
            self._item_cache.set(item.pubfileid, item)

        page_data = WorkshopPage(
            items=items,
            current_page=result.get("current_page", 1),
            total_pages=max(1, result.get("total_pages", 1)),
            total_items=result.get("total_items", 0),
            filters=self._current_filters,
        )

        self._page_cache.set(self._current_url, page_data)
        self._current_page_data = page_data
        self.page_loaded.emit(page_data)

    def _on_details_parsed(self, result) -> None:
        self._is_loading_details = False
        self.loading_finished.emit()

        if not result:
            self.error_occurred.emit("Failed to parse details")
            return

        if isinstance(result, dict) and "error" in result:
            self.error_occurred.emit(f"Fetch failed: {result['error']}")
            return

        pubfileid = result.get("pubfileid", self._current_pubfileid)
        existing = self._item_cache.get(pubfileid)

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
            author=result.get("author", "") or (existing.author if existing else ""),
            author_url=result.get("author_url", "") or (existing.author_url if existing else ""),
        )

        self._item_cache.set(pubfileid, item)
        self.item_details_loaded.emit(item)

    def cleanup(self) -> None:
        try:
            if hasattr(self, "_webview") and self._webview is not None:
                self._webview.setPage(None)
                self._webview.deleteLater()
                self._webview = None

            if hasattr(self, "_page") and self._page is not None:
                self._page.deleteLater()
                self._page = None

            if hasattr(self, "_profile") and self._profile is not None:
                self._profile.deleteLater()
                self._profile = None

            if hasattr(self, "_container") and self._container is not None:
                self._container.deleteLater()
                self._container = None
        except RuntimeError:
            pass