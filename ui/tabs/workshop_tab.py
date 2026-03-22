import copy
from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtCore import QPoint, QTimer, Qt, QSize, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from ui.widgets.background_widget import BackgroundImageWidget
from infrastructure.cache.image_cache import ImageCache
from infrastructure.resources.resource_manager import get_icon
from shared.helpers import parse_file_size_to_bytes
from ui.dialogs.downloads_dialog import DownloadsDialog
from ui.notifications import NotificationLabel
from ui.widgets.details_panel import DetailsPanel
from ui.widgets.filter_bar import UnifiedFilterBar
from ui.widgets.flow_layout import AdaptiveGridWidget
from ui.widgets.grid_items import SkeletonGridItem, WorkshopGridItem
from ui.widgets.grid_items import CollectionGridItem
from ui.widgets.loading_overlay import LoadingOverlay
from ui.widgets.preview_popup import PreviewPopup
from infrastructure.steam.workshop_parser import WorkshopParser
from infrastructure.steam.workshop_url_builder import WorkshopUrlBuilder


@dataclass
class WorkshopNavigationState:
    nav_mode: str
    current_page: int
    total_pages: int
    filters: object = None
    author_name: str = ""
    author_url: str = ""
    selected_pubfileid: str | None = None
    browse_toggle_index: int = 0
    collection_stack: list[str] = field(default_factory=list)
    current_collection_id: str | None = None


class AnimatedDetailsContainer(QWidget):
    animation_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_width = 320
        self._current_width = 320
        self._is_panel_visible = True

        self._animation = QPropertyAnimation(self, b"panelWidth")
        self._animation.setDuration(250)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.finished.connect(self._on_animation_finished)

        self.setFixedWidth(self._target_width)
        self.setMinimumWidth(0)

    def get_panel_width(self) -> int:
        return self._current_width

    def set_panel_width(self, width: int) -> None:
        self._current_width = width
        self.setFixedWidth(max(0, width))

    panelWidth = pyqtProperty(int, get_panel_width, set_panel_width)

    def set_target_width(self, width: int) -> None:
        self._target_width = width
        if self._is_panel_visible:
            self._current_width = width
            self.setFixedWidth(width)

    def is_panel_visible(self) -> bool:
        return self._is_panel_visible

    def show_panel(self) -> None:
        if self._is_panel_visible:
            return
        self._is_panel_visible = True
        self.setVisible(True)
        for child in self.findChildren(QWidget):
            child.setVisible(True)
        self._animation.stop()
        self._animation.setStartValue(0)
        self._animation.setEndValue(self._target_width)
        self._animation.start()

    def hide_panel(self) -> None:
        if not self._is_panel_visible:
            return
        self._is_panel_visible = False
        self._animation.stop()
        self._animation.setStartValue(self._current_width)
        self._animation.setEndValue(0)
        self._animation.start()

    def _on_animation_finished(self) -> None:
        if not self._is_panel_visible:
            self.setVisible(False)
        self.animation_finished.emit()


class WorkshopTab(QWidget):
    download_requested = pyqtSignal(str)

    NAV_NORMAL = "normal"
    NAV_AUTHOR_ITEMS = "author_items"
    NAV_AUTHOR_COLLECTIONS = "author_collections"
    NAV_COLLECTION_CONTENTS = "collection_contents"
    NAV_GLOBAL_COLLECTIONS = "global_collections"

    def __init__(
        self,
        config_service,
        account_service,
        download_service,
        wallpaper_engine_client,
        translator,
        theme_manager,
        metadata_service=None,
        parent=None,
    ):
        super().__init__(parent)
        self.config = config_service
        self.accounts = account_service
        self.dm = download_service
        self.we = wallpaper_engine_client
        self.tr = translator
        self.theme = theme_manager
        self.metadata_service = metadata_service

        self.current_page = 1
        self.total_pages = 1
        self.selected_pubfileid: Optional[str] = None
        self.grid_items: list[WorkshopGridItem] = []
        self.skeleton_items: list[SkeletonGridItem] = []
        self._current_page_data = None
        self._is_loading_page = False
        self._is_loading_details = False
        self._initial_load_done = False
        self._preview_url_cache: dict[str, str] = {}
        self._file_size_cache: dict[str, int] = {}
        self._details_panel_margin = 15
        self._loading_overlay: Optional[LoadingOverlay] = None
        self._empty_state_container: Optional[QWidget] = None
        self._current_collection_contents = None
        self._collection_items_per_page = 30
        self._collection_total_pages = 1
        self._navigation_history: list[WorkshopNavigationState] = []

        self._nav_mode = self.NAV_NORMAL
        self._author_name = ""
        self._author_url = ""
        self._collection_stack: list[str] = []

        self._setup_ui()
        self._setup_parser()
        self._setup_downloads_dialog()

        self.details_panel.author_clicked.connect(self._on_author_clicked)
        self.parser.collection_contents_loaded.connect(self._on_collection_contents_loaded)
        self.filter_bar.search_panel.author_close_requested.connect(self._exit_author_mode)
        self.filter_bar.search_panel.browse_mode_changed.connect(
            self._on_browse_mode_changed
        )

        self.dm.download_completed.connect(self._on_download_completed)

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_item_statuses)
        self._status_timer.start(1000)

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        self.left_panel = self._create_left_panel()
        main_layout.addWidget(self.left_panel, 1)

        self.details_container = AnimatedDetailsContainer(self)
        self.details_container.set_target_width(322)
        self.details_container.animation_finished.connect(self._on_details_animation_finished)

        details_outer_layout = QVBoxLayout(self.details_container)
        details_outer_layout.setContentsMargins(0, 0, 0, 0)
        details_outer_layout.setSpacing(0)

        self.details_card = QFrame()
        self.details_card.setObjectName("workshopDetailsCard")
        self.details_card.setStyleSheet(
            f"""
            QFrame#workshopDetailsCard {{
                background-color: transparent;
                border: 1px solid {self.theme.get_color('border')};
                border-radius: 16px;
            }}
            """
        )

        details_layout = QVBoxLayout(self.details_card)
        details_layout.setContentsMargins(0, 0, 0, 0)

        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.details_panel = DetailsPanel(
            self.we,
            self.dm,
            self.tr,
            self.theme,
            self.config,
            self.metadata_service,
            self,
        )
        self.details_panel.panel_collapse_requested.connect(self._on_collapse_requested)
        self.details_scroll.setWidget(self.details_panel)

        details_layout.addWidget(self.details_scroll)
        details_outer_layout.addWidget(self.details_card)

        main_layout.addWidget(self.details_container)

        self._content_bg = BackgroundImageWidget(self.content_card, border_radius=15, border_inset=1)
        self._content_bg.set_base_color(self.theme.get_color("bg_secondary"))

        self._details_bg = BackgroundImageWidget(self.details_card, border_radius=15, border_inset=1)
        self._details_bg.set_base_color(self.theme.get_color("bg_secondary"))

        self.preview_popup = PreviewPopup(self.theme, self.tr, self)

    def apply_backgrounds(self, config, theme) -> None:
        self._content_bg.set_image_from_base64(config.get_background_image("tabs"))
        self._content_bg.set_blur_percent(config.get_background_blur("tabs"))
        self._content_bg.set_opacity_percent(config.get_background_opacity("tabs"))
        self._content_bg.set_base_color(theme.get_color("bg_secondary"))
        self._content_bg.lower()

        self._details_bg.set_image_from_base64(config.get_background_image("details"))
        self._details_bg.set_blur_percent(config.get_background_blur("details"))
        self._details_bg.set_opacity_percent(config.get_background_opacity("details"))
        self._details_bg.set_base_color(theme.get_color("bg_secondary"))
        self._details_bg.lower()

    def _create_left_panel(self) -> QWidget:
        widget = QWidget()
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.content_card = QFrame()
        self.content_card.setObjectName("workshopContentCard")
        self.content_card.setStyleSheet(f"""
            QFrame#workshopContentCard {{
                background-color: transparent;
                border: 1px solid {self.theme.get_color('border')};
                border-radius: 16px;
            }}
        """)
        layout = QVBoxLayout(self.content_card)
        layout.setContentsMargins(10, 10, 10, 7)
        layout.setSpacing(10)

        self.filter_bar = UnifiedFilterBar(
            self.theme, self.tr, UnifiedFilterBar.MODE_WORKSHOP, self
        )
        self.filter_bar.filters_changed.connect(self._on_filters_changed)
        self.filter_bar.refresh_requested.connect(self._on_refresh_requested)
        layout.addWidget(self.filter_bar, 0, Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{
                background-color: {self.theme.get_color('bg_secondary')};
                width: 10px; margin: 2px 2px 2px 2px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.theme.get_color('border')};
                min-height: 30px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.theme.get_color('primary')};
            }}
            QScrollBar::handle:vertical:pressed {{
                background-color: {self.theme.get_color('primary_hover')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)

        self.grid_widget = AdaptiveGridWidget()
        self.grid_widget.set_item_size_range(160, 240, 185)
        self.grid_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.scroll_area.setWidget(self.grid_widget)
        self._loading_overlay = LoadingOverlay(self.theme, self.scroll_area)

        layout.addWidget(self.scroll_area, 1)

        self._pagination_bar = self._create_pagination_bar()
        layout.addWidget(self._pagination_bar, 0, Qt.AlignmentFlag.AlignHCenter)

        outer_layout.addWidget(self.content_card)
        return widget

    def _create_pagination_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(35)
        bar.setFixedWidth(500)
        bar.setStyleSheet(
            f"""
            QWidget {{
                background-color: transparent;
                border-radius: 10px;
                border: 1px solid {self.theme.get_color('border')};
            }}
            """
        )

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 4, 12, 4)

        self.first_btn = self._create_page_btn("ICON_ARROW_DOUBLE_LEFT")
        self.first_btn.clicked.connect(lambda: self._go_to_page(1))
        layout.addWidget(self.first_btn)

        self.prev_btn = self._create_page_btn("ICON_ARROW_LEFT")
        self.prev_btn.clicked.connect(lambda: self._go_to_page(self.current_page - 1))
        layout.addWidget(self.prev_btn)

        layout.addStretch()

        self.page_label1 = QLabel(self.tr.t("labels.page"))
        self.page_label1.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_primary')};
            font-weight: 600;
            font-size: 13px;
            background: transparent;
            border: none;
            """
        )
        layout.addWidget(self.page_label1)

        self.page_input = QLineEdit()
        self.page_input.setFixedWidth(40)
        self.page_input.setPlaceholderText(self.tr.t("labels.page"))
        self.page_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {self.theme.get_color('bg_secondary')};
                border: none;
                border-radius: 6px;
                padding: 2px 8px;
                color: {self.theme.get_color('text_primary')};
                font-size: 12px;
                text-align: center;
            }}
            QLineEdit:focus {{
                border-color: {self.theme.get_color('primary')};
            }}
            """
        )
        self.page_input.returnPressed.connect(self._on_page_input)
        layout.addWidget(self.page_input)

        self.page_label2 = QLabel(self.tr.t("labels.of", total=1))
        self.page_label2.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_primary')};
            font-weight: 600;
            font-size: 13px;
            background: transparent;
            border: none;
            """
        )
        layout.addWidget(self.page_label2)

        layout.addStretch()

        self.next_btn = self._create_page_btn("ICON_ARROW_RIGHT")
        self.next_btn.clicked.connect(lambda: self._go_to_page(self.current_page + 1))
        layout.addWidget(self.next_btn)

        self.last_btn = self._create_page_btn("ICON_ARROW_DOUBLE_RIGHT")
        self.last_btn.clicked.connect(lambda: self._go_to_page(self.total_pages))
        layout.addWidget(self.last_btn)

        return bar

    def _create_page_btn(self, icon_name: str) -> QPushButton:
        button = QPushButton()
        button.setIcon(get_icon(icon_name))
        button.setIconSize(QSize(18, 18))
        button.setFixedSize(32, 28)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.2);
            }}
            """
        )
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def _on_collapse_requested(self) -> None:
        self.details_container.hide_panel()
        self._update_grid_margin(False)

    def _on_details_animation_finished(self) -> None:
        self.grid_widget.schedule_layout_update(50)

    def _update_grid_margin(self, panel_visible: bool) -> None:
        if panel_visible:
            self.content_card.layout().setContentsMargins(10, 10, 10, 10)
        else:
            self.content_card.layout().setContentsMargins(10, 10, 10, 10)

    def _setup_parser(self) -> None:
        self.parser = WorkshopParser(self.accounts, self.config, self)
        self.parser.page_loaded.connect(self._on_page_loaded)
        self.parser.item_details_loaded.connect(self._on_item_details_loaded)
        self.parser.page_loading_started.connect(self._on_page_loading_started)
        self.parser.error_occurred.connect(self._on_error)
        self.parser.login_successful.connect(self._on_login_success)
        self.parser.login_failed.connect(self._on_login_failed)
        self.parser.ensure_logged_in(account_index=6)

    def _setup_downloads_dialog(self) -> None:
        self.downloads_dialog = DownloadsDialog(self.tr, self.theme, self.dm, self.parser, self)
        self.downloads_dialog.download_cancelled.connect(self._on_download_cancelled)

    def _on_download_cancelled(self, pubfileid: str) -> None:
        self.dm.cancel_download(pubfileid)
        self._update_item_statuses()

    def _on_page_input(self) -> None:
        self.page_input.clearFocus()
        try:
            page = int(self.page_input.text().strip())
            if 1 <= page <= self.total_pages:
                self._go_to_page(page)
            self.page_input.clear()
        except ValueError:
            self.page_input.clear()
            NotificationLabel.show_notification(self.parent(), self.tr.t("messages.invalid_page_number"))

    def _go_to_page(self, page: int) -> None:
        if self._is_loading_page:
            return

        self.page_input.clearFocus()
        page = max(1, min(page, self.total_pages))
        if page == self.current_page:
            return

        self.current_page = page
        self.selected_pubfileid = None
        self.filter_bar.set_page(page)

        if self._nav_mode == self.NAV_COLLECTION_CONTENTS and self._current_collection_contents is not None:
            self._render_collection_contents_page()
        else:
            self._load_current_mode_page()

        self.scroll_area.verticalScrollBar().setValue(0)

    def _create_navigation_state(self) -> WorkshopNavigationState:
        filters = self.filter_bar.get_current_filters()
        filters_copy = copy.deepcopy(filters) if filters is not None else None

        current_collection_id = None
        if self._current_collection_contents is not None:
            current_collection_id = self._current_collection_contents.collection_id

        return WorkshopNavigationState(
            nav_mode=self._nav_mode,
            current_page=self.current_page,
            total_pages=self.total_pages,
            filters=filters_copy,
            author_name=self._author_name,
            author_url=self._author_url,
            selected_pubfileid=self.selected_pubfileid,
            browse_toggle_index=self.filter_bar.search_panel.browse_toggle.currentIndex()
            if hasattr(self.filter_bar.search_panel, "browse_toggle") else 0,
            collection_stack=list(self._collection_stack),
            current_collection_id=current_collection_id,
        )

    def _push_navigation_state(self) -> None:
        self._navigation_history.append(self._create_navigation_state())

    def _restore_navigation_state(self, state: WorkshopNavigationState) -> None:
        self._nav_mode = state.nav_mode
        self.current_page = max(1, state.current_page)
        self.total_pages = max(1, state.total_pages)
        self._author_name = state.author_name
        self._author_url = state.author_url
        self.selected_pubfileid = state.selected_pubfileid
        self._collection_stack = list(state.collection_stack)

        if hasattr(self.filter_bar.search_panel, "browse_toggle"):
            self.filter_bar.search_panel.browse_toggle.setCurrentIndex(state.browse_toggle_index)

        if self._author_url:
            self.filter_bar.search_panel.show_author_close()
            self._set_sort_period_enabled(False)
        else:
            self.filter_bar.search_panel.hide_author_close()
            self._set_sort_period_enabled(True)

        if state.filters is not None:
            state.filters.page = self.current_page
            self.filter_bar.set_page(self.current_page)

        self._current_collection_contents = None

        if self._nav_mode == self.NAV_COLLECTION_CONTENTS and state.current_collection_id:
            self.parser.load_collection_contents(state.current_collection_id)
        elif self._nav_mode in (
            self.NAV_AUTHOR_ITEMS,
            self.NAV_AUTHOR_COLLECTIONS,
            self.NAV_GLOBAL_COLLECTIONS,
            self.NAV_NORMAL,
        ):
            self._load_current_mode_page()

    def _pop_and_restore_navigation_state(self) -> bool:
        if not self._navigation_history:
            return False
        state = self._navigation_history.pop()
        self._restore_navigation_state(state)
        return True

    def _on_login_success(self) -> None:
        self._initial_load()

    def _on_login_failed(self, error: str) -> None:
        self._initial_load()

    def _initial_load(self) -> None:
        self._initial_load_done = True
        self._nav_mode = self.NAV_NORMAL
        if hasattr(self, '_browse_toggle'):
            self.filter_bar.search_panel.browse_toggle.setCurrentIndex(0)
        self.parser.load_page(self.filter_bar.get_current_filters())

    def _on_refresh_requested(self, filters) -> None:
        if self._is_loading_page:
            return
        filters.page = self.current_page
        self.filter_bar.set_page(self.current_page)
        self.selected_pubfileid = None
        self._load_current_mode_page()

    def _on_filters_changed(self, filters) -> None:
        if self._is_loading_page:
            return
        self.current_page = 1
        filters.page = 1
        self.filter_bar.set_page(1)
        self.selected_pubfileid = None
        self._collection_stack.clear()
        self._load_current_mode_page()

    def _on_page_loading_started(self) -> None:
        self._is_loading_page = True
        self._show_skeleton_grid()
        self._update_pagination_buttons()

    def _on_page_loaded(self, page_data) -> None:
        self._is_loading_page = False
        self._current_page_data = page_data
        self.current_page = page_data.current_page
        self.total_pages = max(1, page_data.total_pages)

        if self._loading_overlay:
            self._loading_overlay.hide()

        cache = ImageCache.instance()
        cache.preload([item.preview_url for item in page_data.items if item.preview_url])

        self._clear_grid()
        self._populate_grid(page_data.items)
        self._update_pagination()
        self._update_info_text()

        if hasattr(self, '_pagination_bar'):
            self._pagination_bar.setVisible(True)

        QTimer.singleShot(50, self._force_grid_update)

        is_collection_mode = self._nav_mode in (
            self.NAV_GLOBAL_COLLECTIONS,
            self.NAV_AUTHOR_COLLECTIONS,
            self.NAV_COLLECTION_CONTENTS,
        )
        has_collection_items = any(
            getattr(item, 'is_collection', False) for item in page_data.items
        )

        if (page_data.items
                and not self.selected_pubfileid
                and self.details_container.is_panel_visible()
                and not is_collection_mode
                and not has_collection_items):
            self._select_item(page_data.items[0].pubfileid)

        self._try_preload_next_page()

    def _force_grid_update(self) -> None:
        self.grid_widget.update_layout()
        self.grid_widget.updateGeometry()
        self.scroll_area.updateGeometry()

    def _try_preload_next_page(self) -> None:
        if not self.config.get_preload_next_page():
            return
        if not self._current_page_data or not self._current_page_data.filters:
            return
        if self.current_page >= self.total_pages:
            return
        self.parser.preload_next_page(self._current_page_data.filters)

    def _on_item_details_loaded(self, item) -> None:
        self._is_loading_details = False

        if item.preview_url:
            self._preview_url_cache[item.pubfileid] = item.preview_url

        if item.file_size:
            size_bytes = parse_file_size_to_bytes(item.file_size)
            if size_bytes > 0:
                self._file_size_cache[item.pubfileid] = size_bytes
                for grid_item in self.grid_items:
                    try:
                        if grid_item and grid_item.pubfileid == item.pubfileid:
                            grid_item.set_file_size_bytes(size_bytes)
                            break
                    except RuntimeError:
                        pass

        self.details_panel.set_workshop_item(item)

    def _open_current_collection_details(self, contents) -> None:
        if not self.details_container.is_panel_visible():
            self.details_container.show_panel()
            self._update_grid_margin(True)

        self.details_panel.set_collection_info(contents)

    def _on_browse_mode_changed(self, index: int) -> None:
        self.current_page = 1
        self.selected_pubfileid = None
        self._collection_stack.clear()
        filters = self.filter_bar.get_current_filters()
        filters.page = 1
        self.filter_bar.set_page(1)

        if self._author_url:
            if index == 1:
                self._nav_mode = self.NAV_AUTHOR_COLLECTIONS
            else:
                self._nav_mode = self.NAV_AUTHOR_ITEMS
            self._load_current_mode_page()
        else:
            if index == 1:
                self._nav_mode = self.NAV_GLOBAL_COLLECTIONS
            else:
                self._nav_mode = self.NAV_NORMAL
            self._load_current_mode_page()

    def _load_current_mode_page(self) -> None:
        filters = self.filter_bar.get_current_filters()
        filters.page = self.current_page

        if self._nav_mode == self.NAV_AUTHOR_ITEMS:
            url = WorkshopUrlBuilder.build_author_items(self._author_url, filters)
            self.parser.load_author_page(url, is_collections=False)
        elif self._nav_mode == self.NAV_AUTHOR_COLLECTIONS:
            url = WorkshopUrlBuilder.build_author_collections(self._author_url, filters)
            self.parser.load_author_page(url, is_collections=True)
        elif self._nav_mode == self.NAV_GLOBAL_COLLECTIONS:
            url = WorkshopUrlBuilder.build_collections_browse(filters)
            self.parser.load_author_page(url, is_collections=True)
        else:
            self.parser.load_page(filters)

    def _on_author_clicked(self, author_name: str, author_url: str) -> None:
        if not author_url:
            return

        self._push_navigation_state()

        self._author_name = author_name
        self._author_url = author_url
        self._nav_mode = self.NAV_AUTHOR_ITEMS
        self._collection_stack.clear()
        self.current_page = 1
        self.selected_pubfileid = None

        self.filter_bar.search_panel.show_author_close()
        self.filter_bar.search_panel.browse_toggle.setCurrentIndex(0)
        self._set_sort_period_enabled(False)
        self._load_current_mode_page()

    def _exit_author_mode(self) -> None:
        self._author_name = ""
        self._author_url = ""
        self._collection_stack.clear()
        self.selected_pubfileid = None

        self.filter_bar.search_panel.hide_author_close()
        self._set_sort_period_enabled(True)

        restored = self._pop_and_restore_navigation_state()
        if restored:
            return

        self.current_page = 1
        self._nav_mode = self.NAV_NORMAL
        self.filter_bar.search_panel.browse_toggle.setCurrentIndex(0)
        filters = self.filter_bar.get_current_filters()
        filters.page = 1
        self.filter_bar.set_page(1)
        self.parser.load_page(filters)

    def _set_sort_period_enabled(self, enabled: bool) -> None:
        if hasattr(self.filter_bar, 'filters_popup'):
            fp = self.filter_bar.filters_popup
            if hasattr(fp, 'sort_combo'):
                fp.sort_combo["combo"].setEnabled(enabled)
            if hasattr(fp, 'time_combo'):
                fp.time_combo["combo"].setEnabled(enabled)

    def _on_collection_item_clicked(self, pubfileid: str) -> None:
        self._push_navigation_state()

        self._nav_mode = self.NAV_COLLECTION_CONTENTS
        self._collection_stack.append(pubfileid)
        self.selected_pubfileid = None
        self.current_page = 1
        self.total_pages = 1
        self._current_collection_contents = None
        self.parser.load_collection_contents(pubfileid)

    def _on_collection_back(self) -> None:
        self._current_collection_contents = None
        self.current_page = 1
        self.total_pages = 1

        if self._pop_and_restore_navigation_state():
            return

        self._nav_mode = self.NAV_NORMAL
        if hasattr(self, '_pagination_bar'):
            self._pagination_bar.setVisible(True)
        self._load_current_mode_page()

    def _render_collection_contents_page(self) -> None:
        contents = self._current_collection_contents
        if contents is None:
            return

        self._clear_grid()

        if self.details_container.is_panel_visible():
            self.details_panel.set_collection_info(contents)

        total_items = len(contents.items)
        start_index = (self.current_page - 1) * self._collection_items_per_page
        end_index = start_index + self._collection_items_per_page
        page_items = contents.items[start_index:end_index]

        start_num = start_index + 1 if total_items > 0 else 0
        end_num = min(end_index, total_items)

        self.filter_bar.set_info_text(
            f"{contents.title} ({start_num}-{end_num} / {total_items})"
            if total_items > 0 else f"{contents.title} (0 / 0)"
        )

        item_size = self.grid_widget.get_current_item_size()

        primary_card = CollectionGridItem(
            pubfileid=contents.collection_id,
            title=contents.title,
            preview_url=contents.preview_url,
            item_size=item_size,
            theme_manager=self.theme,
            parent=self,
            is_primary_collection_card=True,
            related_count=len(contents.related_collections),
            show_back_button=True,
            current_collection_text=self.tr.t("labels.current_collection"),
            related_collections_text=self.tr.t("labels.related_collections"),
        )
        primary_card.clicked.connect(
            lambda _pid=contents.collection_id: self._open_current_collection_details(contents)
        )
        primary_card.back_clicked.connect(self._on_collection_back)
        self.grid_widget.add_item(primary_card)
        self.grid_items.append(primary_card)

        if self.current_page == 1 and contents.related_collections:
            for col in contents.related_collections:
                ci = CollectionGridItem(
                    pubfileid=col.pubfileid,
                    title=col.title,
                    preview_url=col.preview_url,
                    item_count=getattr(col, 'item_count', 0),
                    item_size=item_size,
                    theme_manager=self.theme,
                    parent=self,
                )
                ci.clicked.connect(self._on_collection_item_clicked)
                self.grid_widget.add_item(ci)
                self.grid_items.append(ci)

        for item_data in page_items:
            grid_item = WorkshopGridItem(
                pubfileid=item_data.pubfileid,
                title=item_data.title,
                preview_url=item_data.preview_url,
                item_size=item_size,
                theme_manager=self.theme,
                parent=self,
            )

            if self.dm.is_downloading(item_data.pubfileid):
                st = self.dm.get_download_status(item_data.pubfileid)
                grid_item.set_status(WorkshopGridItem.STATUS_DOWNLOADING, st)
            elif self._is_fully_installed(item_data.pubfileid):
                grid_item.set_status(WorkshopGridItem.STATUS_INSTALLED)
            else:
                grid_item.set_status(WorkshopGridItem.STATUS_AVAILABLE)

            grid_item.clicked.connect(self._select_item)
            self.grid_widget.add_item(grid_item)
            self.grid_items.append(grid_item)

        if hasattr(self, "_pagination_bar"):
            self._pagination_bar.setVisible(True)

        self._update_pagination()
        QTimer.singleShot(50, self._force_grid_update)

    def _on_collection_contents_loaded(self, contents) -> None:
        self._is_loading_page = False
        if self._loading_overlay:
            self._loading_overlay.hide()

        self._current_collection_contents = contents
        total_items = len(contents.items)
        self._collection_total_pages = max(
            1,
            (total_items + self._collection_items_per_page - 1) // self._collection_items_per_page
        )
        self.total_pages = self._collection_total_pages
        self.current_page = max(1, min(self.current_page, self.total_pages))

        self._render_collection_contents_page()

    def _on_error(self, error_msg: str) -> None:
        self._is_loading_page = False
        self._is_loading_details = False

        if self._loading_overlay:
            self._loading_overlay.hide()

        NotificationLabel.show_notification(self.parent(), f"Error: {error_msg}")
        self._clear_skeleton_grid()
        self._update_pagination_buttons()

    def _on_download_completed(self, pubfileid: str, success: bool) -> None:
        if not success:
            return

        if self.we.is_installed(pubfileid):
            cached_item = self.parser.get_cached_item(pubfileid)
            if cached_item and self.metadata_service:
                self.metadata_service.save_from_workshop_item(cached_item)

        self._update_item_statuses()

        if self.selected_pubfileid == pubfileid:
            self.details_panel.refresh_after_state_change()

    def _is_fully_installed(self, pubfileid: str) -> bool:
        return self.we.is_installed(pubfileid) and not self.dm.is_downloading(pubfileid)

    def _show_skeleton_grid(self) -> None:
        self._clear_grid()

        if self._loading_overlay:
            self._loading_overlay.show()
            self._loading_overlay.raise_()
            self._loading_overlay.update_position()

        item_size = self.grid_widget.get_current_item_size()
        for _ in range(30):
            skeleton = SkeletonGridItem(item_size, self.theme, self)
            self.grid_widget.add_item(skeleton)
            self.skeleton_items.append(skeleton)

        QTimer.singleShot(50, self._force_grid_update)

    def _clear_skeleton_grid(self) -> None:
        for item in self.skeleton_items:
            try:
                if item is not None:
                    item.setParent(None)
                    item.deleteLater()
            except RuntimeError:
                pass
        self.skeleton_items.clear()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._empty_state_container is not None:
            self._empty_state_container.setMinimumHeight(self.scroll_area.viewport().height())
            self.grid_widget.update_layout()

    def _show_empty_state(self, text: str) -> None:
        container = QWidget()
        container.span_full_width = True
        container.setMinimumHeight(self.scroll_area.viewport().height())
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        layout.addStretch()

        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 16px;
            padding: 10px;
            background: transparent;
            """
        )
        layout.addWidget(label)

        layout.addStretch()

        self._empty_state_container = container
        self.grid_widget.add_item(container)

    def _populate_grid(self, items) -> None:
        self._clear_skeleton_grid()

        if not items:
            is_collections = self._nav_mode in (
                self.NAV_GLOBAL_COLLECTIONS,
                self.NAV_AUTHOR_COLLECTIONS,
            )
            key = "labels.no_collections_found" if is_collections else "labels.no_wallpapers_found"
            self._show_empty_state(self.tr.t(key))
            return

        item_size = self.grid_widget.get_current_item_size()

        for item_data in items:
            if getattr(item_data, 'is_collection', False):
                grid_item = CollectionGridItem(
                    pubfileid=item_data.pubfileid,
                    title=item_data.title,
                    preview_url=item_data.preview_url,
                    item_size=item_size,
                    theme_manager=self.theme,
                    parent=self,
                )
                grid_item.clicked.connect(self._on_collection_item_clicked)
                self.grid_widget.add_item(grid_item)
                self.grid_items.append(grid_item)
            else:
                grid_item = WorkshopGridItem(
                    pubfileid=item_data.pubfileid,
                    title=item_data.title,
                    preview_url=item_data.preview_url,
                    item_size=item_size,
                    theme_manager=self.theme,
                    parent=self,
                )

                cached_size = self._file_size_cache.get(item_data.pubfileid, 0)
                if cached_size > 0:
                    grid_item.set_file_size_bytes(cached_size)

                if self.dm.is_downloading(item_data.pubfileid):
                    status_text = self.dm.get_download_status(item_data.pubfileid)
                    grid_item.set_status(WorkshopGridItem.STATUS_DOWNLOADING, status_text)
                elif self._is_fully_installed(item_data.pubfileid):
                    grid_item.set_status(WorkshopGridItem.STATUS_INSTALLED)
                else:
                    grid_item.set_status(WorkshopGridItem.STATUS_AVAILABLE)

                grid_item.clicked.connect(self._select_item)
                self.grid_widget.add_item(grid_item)
                self.grid_items.append(grid_item)

    def _clear_grid(self) -> None:
        for item in self.grid_items:
            try:
                if item is not None and hasattr(item, "release_resources"):
                    item.release_resources()
            except RuntimeError:
                pass

        self._clear_skeleton_grid()
        self.grid_widget.clear_items()
        self.grid_items.clear()
        self._empty_state_container = None

    def _select_item(self, pubfileid: str) -> None:
        if not self.details_container.is_panel_visible():
            self.details_container.show_panel()
            self._update_grid_margin(True)

        self.selected_pubfileid = pubfileid

        for grid_item in self.grid_items:
            try:
                if hasattr(grid_item, 'pubfileid') and grid_item.pubfileid == pubfileid:
                    if isinstance(grid_item, CollectionGridItem):
                        self._on_collection_item_clicked(pubfileid)
                        return
            except RuntimeError:
                continue

        if self._is_fully_installed(pubfileid):
            folder_path = self.we.projects_path / pubfileid
            self.details_panel.set_installed_folder(str(folder_path))
            return

        self.parser.load_item_details(pubfileid)

    def _update_item_statuses(self) -> None:
        for item in self.grid_items:
            try:
                if item is None:
                    continue
                if not hasattr(item, 'set_status'):
                    continue
                if self.dm.is_downloading(item.pubfileid):
                    status_text = self.dm.get_download_status(item.pubfileid)
                    item.set_status(WorkshopGridItem.STATUS_DOWNLOADING, status_text)
                elif self._is_fully_installed(item.pubfileid):
                    item.set_status(WorkshopGridItem.STATUS_INSTALLED)
                else:
                    item.set_status(WorkshopGridItem.STATUS_AVAILABLE)
            except RuntimeError:
                pass

        if hasattr(self, "details_panel") and self.details_panel:
            try:
                self.details_panel.update_download_state()
            except Exception:
                pass

    def _update_info_text(self) -> None:
        if self._nav_mode == self.NAV_COLLECTION_CONTENTS:
            return

        prefix = ""
        if self._author_url and self._author_name:
            prefix = f"{self._author_name}  ·  "

        is_collections = self._nav_mode in (
            self.NAV_GLOBAL_COLLECTIONS,
            self.NAV_AUTHOR_COLLECTIONS,
        )

        if self._current_page_data:
            total_items = self._current_page_data.total_items
            current_count = len(self._current_page_data.items)
            start_item = (self.current_page - 1) * 15 + 1
            end_item = min(start_item + current_count - 1, total_items)
            if total_items > 0:
                if is_collections:
                    text = prefix + self.tr.t(
                        "labels.showing_collections",
                        start=start_item, end=end_item, total=total_items,
                    )
                else:
                    text = prefix + self.tr.t(
                        "labels.showing_wallpapers",
                        start=start_item, end=end_item, total=total_items,
                    )
            else:
                if is_collections:
                    text = prefix + self.tr.t("labels.no_collections_found")
                else:
                    text = prefix + self.tr.t("labels.no_wallpapers_found")
        else:
            text = self.tr.t("labels.loading_dots")

        self.filter_bar.set_info_text(text)

    def _update_pagination(self) -> None:
        self.page_label2.setText(self.tr.t("labels.of", total=self.total_pages))
        self.page_input.setText(str(self.current_page))
        self._update_pagination_buttons()

    def _update_pagination_buttons(self) -> None:
        can_go_back = self.current_page > 1 and not self._is_loading_page
        can_go_forward = self.current_page < self.total_pages and not self._is_loading_page

        self.first_btn.setEnabled(can_go_back)
        self.prev_btn.setEnabled(can_go_back)
        self.next_btn.setEnabled(can_go_forward)
        self.last_btn.setEnabled(can_go_forward)

    def start_download(self, pubfileid: str) -> None:
        if self.dm.is_downloading(pubfileid):
            return

        cached_item = self.parser.get_cached_item(pubfileid)
        if cached_item and cached_item.preview_url:
            self._preview_url_cache[pubfileid] = cached_item.preview_url

        if cached_item and cached_item.file_size:
            size_bytes = parse_file_size_to_bytes(cached_item.file_size)
            if size_bytes > 0:
                self._file_size_cache[pubfileid] = size_bytes
                for grid_item in self.grid_items:
                    try:
                        if grid_item and grid_item.pubfileid == pubfileid:
                            grid_item.set_file_size_bytes(size_bytes)
                            break
                    except RuntimeError:
                        pass

        self.dm.start_download(pubfileid, self.config.get_account_number())
        self._update_item_statuses()

        NotificationLabel.show_notification(self.parent(), self.tr.t("messages.download_started")
        )

    def show_downloads_popup(self, button_pos: QPoint) -> None:
        self.downloads_dialog.set_caches(self._preview_url_cache, self._file_size_cache)
        self.downloads_dialog.show()

    def hide_downloads_popup(self) -> None:
        self.downloads_dialog.hide()

    def cleanup(self) -> None:
        if hasattr(self, "_status_timer"):
            self._status_timer.stop()
        if hasattr(self, "parser"):
            self.parser.cleanup()
        if self._loading_overlay:
            self._loading_overlay.hide()
        ImageCache.instance().clear()
        self._preview_url_cache.clear()
        self._file_size_cache.clear()
        self._clear_grid()

        self._nav_mode = self.NAV_NORMAL
        self._author_name = ""
        self._author_url = ""
        self._collection_stack.clear()
        if hasattr(self, 'filter_bar'):
            self.filter_bar.search_panel.hide_author_close()