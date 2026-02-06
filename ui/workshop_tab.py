from typing import Optional, List, Dict
import weakref
import webbrowser
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QEvent, QPoint, QByteArray, QBuffer, QIODevice
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QSplitter, QSizePolicy, QLineEdit
)
from PyQt6.QtGui import QPixmap, QMovie, QPainter, QPainterPath

from core.image_cache import ImageCache
from core.workshop_parser import WorkshopParser, WorkshopItem, WorkshopPage
from core.workshop_filters import WorkshopFilters
from ui.workshop_filters import CompactFilterBar
from ui.workshop_item import WorkshopGridItem, SkeletonGridItem
from ui.workshop_details_panel import WorkshopDetailsPanel
from ui.custom_widgets import NotificationLabel
from resources.icons import get_icon
from typing import Optional, Dict

class PreviewPopup(QWidget):
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(156, 156)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QWidget()
        self.container.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, 230);
            border-radius: 8px;
            border: 2px solid {self.theme.get_color('primary')};
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(3, 3, 3, 3)
        
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(150, 150)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: transparent; border: none;")
        container_layout.addWidget(self.preview_label)
        
        layout.addWidget(self.container)

        self._current_url: str = ""
        self._current_movie: Optional[QMovie] = None
        self._current_buffer: Optional[QBuffer] = None

    def show_preview(self, preview_url: str, global_pos: QPoint):
        if not preview_url:
            self._stop_current_movie()
            self.preview_label.setText("No preview")
            self.show()
            return

        x_pos = global_pos.x() - self.width() - 10
        if x_pos < 0:
            x_pos = global_pos.x() + 10
        self.move(x_pos, global_pos.y() - 35)
        self.show()
        
        if preview_url == self._current_url:
            return
        
        self._current_url = preview_url
        cache = ImageCache.instance()

        gif_data = cache.get_gif(preview_url)
        if gif_data:
            self._play_gif_from_data(gif_data)
            return
        
        pixmap = cache.get_pixmap(preview_url)
        if pixmap:
            self._stop_current_movie()
            self._set_pixmap(self._create_rounded_pixmap(pixmap.scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )))
            return

        self._stop_current_movie()
        self.preview_label.setText("Loading...")
        
        weak_self = weakref.ref(self)
        expected_url = preview_url
        
        def on_loaded(url: str, data, is_gif: bool):
            self_ref = weak_self()
            if self_ref is None or not self_ref.isVisible():
                return
            if self_ref._current_url != expected_url:
                return
            
            if data is None:
                self_ref._show_error("Load failed")
                return
            
            if is_gif:
                self_ref._play_gif_from_data(data)
            else:
                scaled = data.scaled(
                    150, 150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self_ref._stop_current_movie()
                self_ref._set_pixmap(self_ref._create_rounded_pixmap(scaled))
        
        cache.load_image(preview_url, callback=on_loaded)

    def _is_gif_data(self, data: QByteArray) -> bool:
        if data.size() < 6:
            return False
        header = bytes(data[:6])
        return header.startswith(b'GIF87a') or header.startswith(b'GIF89a')

    def _play_gif_from_data(self, data: QByteArray):
        self._stop_current_movie()
        
        self._current_buffer = QBuffer()
        self._current_buffer.setData(data)
        self._current_buffer.open(QIODevice.OpenModeFlag.ReadOnly)

        self._current_movie = QMovie()
        self._current_movie.setDevice(self._current_buffer)
        self._current_movie.setScaledSize(self._calculate_scaled_size(self._current_movie))
        
        self.preview_label.setStyleSheet("background: transparent; border: none;")
        self.preview_label.setText("")
        self.preview_label.setMovie(self._current_movie)

        self._current_movie.frameChanged.connect(self._on_gif_frame_changed)
        
        self._current_movie.start()
    
    def _on_gif_frame_changed(self, frame_number: int):
        if self._current_movie is None:
            return
        
        current_pixmap = self._current_movie.currentPixmap()
        if not current_pixmap.isNull():
            rounded = self._create_rounded_pixmap(current_pixmap, radius=6)
            self.preview_label.setPixmap(rounded)

    def _calculate_scaled_size(self, movie: QMovie) -> 'QSize':
        movie.jumpToFrame(0)
        original_size = movie.currentImage().size()
        
        if original_size.isEmpty():
            return QSize(150, 150)

        scaled = original_size.scaled(
            150, 150,
            Qt.AspectRatioMode.KeepAspectRatio
        )
        return scaled

    def _stop_current_movie(self):
        if self._current_movie is not None:
            self._current_movie.stop()
            self.preview_label.setMovie(None)
            self._current_movie.deleteLater()
            self._current_movie = None
        
        if self._current_buffer is not None:
            self._current_buffer.close()
            self._current_buffer = None

    def _set_pixmap(self, pixmap: QPixmap):
        self.preview_label.setStyleSheet("background: transparent; border: none;")
        self.preview_label.setText("")
        
        rounded_pixmap = self._create_rounded_pixmap(pixmap, radius=6)
        self.preview_label.setPixmap(rounded_pixmap)

    def _create_rounded_pixmap(self, pixmap: QPixmap, radius: int = 6) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        path = QPainterPath()
        path.addRoundedRect(
            0, 0, 
            pixmap.width(), pixmap.height(), 
            radius, radius
        )

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        return rounded

    def _show_error(self, message: str):
        self._stop_current_movie()
        self.preview_label.setText(message)
        self.preview_label.setStyleSheet("""
            background: transparent; 
            border: none;
            color: #888;
            font-size: 11px;
        """)

    def hide_preview(self):
        self._current_url = ""
        self._stop_current_movie()
        self.hide()

    def force_cancel(self):
        self._current_url = ""
        self._stop_current_movie()

class WorkshopTab(QWidget):
    download_requested = pyqtSignal(str)

    def __init__(
        self,
        config_manager,
        account_manager,
        download_manager,
        wallpaper_engine,
        translator,
        theme_manager,
        parent=None
    ):
        super().__init__(parent)
        
        self.config = config_manager
        self.accounts = account_manager
        self.dm = download_manager
        self.we = wallpaper_engine
        self.tr = translator
        self.theme = theme_manager
        
        self.current_page = 1
        self.total_pages = 1
        self.selected_pubfileid: Optional[str] = None
        self.grid_items: List[WorkshopGridItem] = []
        self.skeleton_items: List[SkeletonGridItem] = []
        self._current_page_data: Optional[WorkshopPage] = None
        
        self._is_loading_page = False
        self._is_loading_details = False
        
        self._preview_url_cache: Dict[str, str] = {}
        
        self._setup_ui()
        self._setup_parser()
        self._setup_downloads_popup()
        
        self.dm.download_completed.connect(self._on_download_completed)

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_item_statuses)
        self._status_timer.start(3000)

    def _setup_parser(self):
        self.parser = WorkshopParser(self.accounts, self)
        self.parser.page_loaded.connect(self._on_page_loaded)
        self.parser.item_details_loaded.connect(self._on_item_details_loaded)
        self.parser.page_loading_started.connect(self._on_page_loading_started)
        self.parser.error_occurred.connect(self._on_error)

        self.parser.login_successful.connect(self._on_login_success)
        self.parser.login_failed.connect(self._on_login_failed)
        self.parser.ensure_logged_in(account_index=6)

    def _on_login_success(self):
        self._initial_load()

    def _on_login_failed(self, error: str):
        print("[Workshop Tab]: Login failed (May be lie)")
        self._initial_load()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self._create_left_panel()
        
        self.details_panel = WorkshopDetailsPanel(
            self.we, self.dm, self.tr, self.theme, self
        )
        
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFixedWidth(320)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.details_scroll.setWidget(self.details_panel)
        
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.details_scroll)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        
        main_layout.addWidget(self.splitter)
        
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._recalculate_grid)

        self.preview_popup = PreviewPopup(self.theme, self)

    def _create_left_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 10, 5, 10)
        layout.setSpacing(10)
        
        self.filter_bar = CompactFilterBar(self.theme, self)
        self.filter_bar.filters_changed.connect(self._on_filters_changed)
        layout.addWidget(self.filter_bar)

        self.info_bar = self._create_info_bar()
        layout.addWidget(self.info_bar)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(2)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area, 1)
        
        pagination = self._create_pagination_bar()
        layout.addWidget(pagination)
        
        return widget

    def _create_info_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(30)
        bar.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.get_color('bg_elevated')};
            border-radius: 8px;
            padding: 0px;
        }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        
        self.results_label = QLabel("Loading...")
        self.results_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 10px;
            font-weight: 600;
        """)
        layout.addWidget(self.results_label)
        layout.addStretch()
        
        return bar

    def _create_pagination_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(50)
        bar.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.get_color('bg_secondary')};
            border-radius: 10px;
        }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 6)
        
        self.first_btn = self._create_page_btn("« First")
        self.first_btn.clicked.connect(lambda: self._go_to_page(1))
        layout.addWidget(self.first_btn)
        
        self.prev_btn = self._create_page_btn("‹ Prev")
        self.prev_btn.clicked.connect(lambda: self._go_to_page(self.current_page - 1))
        layout.addWidget(self.prev_btn)
        
        layout.addStretch()
        
        self.page_label1 = QLabel("Page")
        self.page_label1.setStyleSheet(f"""
        color: {self.theme.get_color('text_primary')};
        font-weight: 600;
        font-size: 13px;
        background: transparent;
        """)
        layout.addWidget(self.page_label1)

        self.page_input = QLineEdit()
        self.page_input.setFixedWidth(50)
        self.page_input.setPlaceholderText("Page")
        self.page_input.setStyleSheet(self._input_style())
        self.page_input.returnPressed.connect(self._on_page_input)
        layout.addWidget(self.page_input)
        
        self.page_label2 = QLabel("of 1")
        self.page_label2.setStyleSheet(f"""
        color: {self.theme.get_color('text_primary')};
        font-weight: 600;
        font-size: 13px;
        background: transparent;
        """)
        layout.addWidget(self.page_label2)
        
        layout.addStretch()
        
        self.next_btn = self._create_page_btn("Next ›")
        self.next_btn.clicked.connect(lambda: self._go_to_page(self.current_page + 1))
        layout.addWidget(self.next_btn)
        
        self.last_btn = self._create_page_btn("Last »")
        self.last_btn.clicked.connect(lambda: self._go_to_page(self.total_pages))
        layout.addWidget(self.last_btn)
        
        return bar

    def _input_style(self) -> str:
        return f"""
        QLineEdit {{
            background-color: {self.theme.get_color('bg_tertiary')};
            border: 2px solid {self.theme.get_color('border')};
            border-radius: 6px;
            padding: 4px 8px;
            color: {self.theme.get_color('text_primary')};
            font-size: 12px;
            text-align: center;
        }}
        QLineEdit:focus {{
            border-color: {self.theme.get_color('primary')};
        }}
        """

    def _on_page_input(self):
        try:
            page = int(self.page_input.text().strip())
            if 1 <= page <= self.total_pages:
                self._go_to_page(page)
            self.page_input.clear()
        except ValueError:
            self.page_input.clear()
            NotificationLabel.show_notification(self, "Invalid page number")

    def _create_page_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(70, 32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.get_color('primary')};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('primary_hover')};
            }}
            QPushButton:disabled {{
                background-color: {self.theme.get_color('bg_tertiary')};
                color: {self.theme.get_color('text_disabled')};
            }}
        """)
        return btn

    def _setup_downloads_popup(self):
        self.downloads_popup = QWidget()
        self.downloads_popup.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.downloads_popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.downloads_popup.setFixedSize(260, 350)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.scroll_container = QWidget()
        self.scroll_container.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.setSpacing(3)
        scroll.setWidget(self.scroll_container)
        
        popup_layout = QVBoxLayout(self.downloads_popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.addWidget(scroll)

        self.downloads_update_timer = QTimer()
        self.downloads_update_timer.timeout.connect(self._auto_update_downloads_popup)
        self.downloads_update_timer.setInterval(500)
        
        self.downloads_popup.showEvent = self._on_downloads_popup_show
        self.downloads_popup.hideEvent = self._on_downloads_popup_hide

    def _on_downloads_popup_show(self, event):
        self.downloads_update_timer.start()
        self._update_downloads_list()
        if event:
            event.accept()

    def _on_downloads_popup_hide(self, event):
        self.downloads_update_timer.stop()
        self.preview_popup.hide_preview()
        self.preview_popup.force_cancel()
        if event:
            event.accept()

    def _auto_update_downloads_popup(self):
        if self.downloads_popup.isVisible():
            self._update_downloads_list()

    def _initial_load(self):
        filters = self.filter_bar.get_current_filters()
        self.parser.load_page(filters)

    def _on_filters_changed(self, filters: WorkshopFilters):
        if self._is_loading_page:
            return
        
        self.current_page = 1
        filters.page = 1
        self.filter_bar.set_page(1)
        self.selected_pubfileid = None
        self.parser.load_page(filters)

    def _on_page_loading_started(self):
        self._is_loading_page = True
        self._show_skeleton_grid()
        self._update_pagination_buttons()

    def _on_page_loaded(self, page_data: WorkshopPage):
        self._is_loading_page = False
        self._current_page_data = page_data
        self.current_page = page_data.current_page
        self.total_pages = max(1, page_data.total_pages)
        
        cache = ImageCache.instance()
        urls = [item.preview_url for item in page_data.items if item.preview_url]
        cache.preload(urls)
        
        self._clear_grid()
        self._populate_grid(page_data.items)
        self._update_pagination()
        
        if page_data.items and not self.selected_pubfileid:
            self._select_item(page_data.items[0].pubfileid)

    def cleanup(self):
        if hasattr(self, '_status_timer'):
            self._status_timer.stop()
        if hasattr(self, 'parser'):
            self.parser.cleanup()
        
        ImageCache.instance().clear()
        
        self._preview_url_cache.clear()
        self._clear_grid()

    def _on_item_details_loaded(self, item: WorkshopItem):
        self._is_loading_details = False
        
        if item.preview_url:
            self._preview_url_cache[item.pubfileid] = item.preview_url
        
        self.details_panel.set_workshop_item(item)

    def _on_error(self, error_msg: str):
        print(f"[WorkshopTab] Error: {error_msg}")
        self._is_loading_page = False
        self._is_loading_details = False
        NotificationLabel.show_notification(self, f"Error: {error_msg}")
        self._clear_skeleton_grid()
        self._update_pagination_buttons()

    def _on_download_completed(self, pubfileid: str, success: bool):
        if success:
            self._update_item_statuses()

            if self.selected_pubfileid == pubfileid:
                self.details_panel.refresh_after_state_change()

    def _show_skeleton_grid(self):
        self._clear_grid()
        
        columns = self._calculate_columns()
        item_size = self._calculate_item_size(columns)
        
        for i in range(30):
            row = i // columns
            col = i % columns
            
            skeleton = SkeletonGridItem(item_size, self)
            self.grid_layout.addWidget(skeleton, row, col)
            self.skeleton_items.append(skeleton)

    def _clear_skeleton_grid(self):
        for item in self.skeleton_items:
            try:
                if item is not None:
                    item.setParent(None)
                    item.deleteLater()
            except RuntimeError:
                pass
        self.skeleton_items.clear()

    def _populate_grid(self, items: List[WorkshopItem]):
        self._clear_skeleton_grid()
        
        if not items:
            label = QLabel("No wallpapers found")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                color: {self.theme.get_color('text_secondary')};
                font-size: 16px;
                padding: 50px;
            """)
            self.grid_layout.addWidget(label, 0, 0, 1, 4)
            return
        
        columns = self._calculate_columns()
        item_size = self._calculate_item_size(columns)
        
        for i, item_data in enumerate(items):
            row = i // columns
            col = i % columns
            
            grid_item = WorkshopGridItem(
                pubfileid=item_data.pubfileid,
                title=item_data.title,
                preview_url=item_data.preview_url,
                item_size=item_size,
                parent=self
            )
            
            if self.dm.is_downloading(item_data.pubfileid):
                grid_item.set_status(WorkshopGridItem.STATUS_DOWNLOADING)
            elif self._is_fully_installed(item_data.pubfileid):
                grid_item.set_status(WorkshopGridItem.STATUS_INSTALLED)
            else:
                grid_item.set_status(WorkshopGridItem.STATUS_AVAILABLE)
            
            grid_item.clicked.connect(self._on_item_clicked)
            
            self.grid_layout.addWidget(grid_item, row, col)
            self.grid_items.append(grid_item)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.grid_layout.addWidget(spacer, len(items) // columns + 1, 0, 1, columns)

    def _is_fully_installed(self, pubfileid: str) -> bool:
        return (
            self.we.is_installed(pubfileid) and
            not self.dm.is_downloading(pubfileid)
        )

    def _clear_grid(self):
        for item in self.grid_items:
            try:
                if item is not None and hasattr(item, 'release_resources'):
                    item.release_resources()
            except RuntimeError:
                pass
        
        self._clear_skeleton_grid()
        
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child is not None:
                widget = child.widget()
                if widget is not None:
                    try:
                        widget.setParent(None)
                        widget.deleteLater()
                    except RuntimeError:
                        pass
        
        self.grid_items.clear()

    def _calculate_columns(self) -> int:
        try:
            available_width = self.scroll_area.viewport().width()
            if available_width <= 0:
                return 4
            
            TARGET_SIZE = 190
            columns = max(1, available_width // (TARGET_SIZE + 2))
            return min(columns, 8)
        except:
            return 4

    def _calculate_item_size(self, columns: int) -> int:
        try:
            if columns <= 0:
                return 185
            
            available_width = self.scroll_area.viewport().width()
            if available_width <= 0:
                return 185
            
            total_spacing = (columns - 1) * 2
            ideal_size = (available_width - total_spacing) // columns
            
            return max(160, min(ideal_size, 240))
        except:
            return 185

    def _on_item_clicked(self, pubfileid: str):
        self._select_item(pubfileid)

    def _select_item(self, pubfileid: str):
        self.selected_pubfileid = pubfileid
        is_fully_installed = (
            self.we.is_installed(pubfileid) and
            not self.dm.is_downloading(pubfileid)
        )
        if is_fully_installed:
            folder_path = self.we.projects_path / pubfileid
            self.details_panel.set_installed_folder(str(folder_path))
            return
        self.parser.load_item_details(pubfileid)

    def _update_item_statuses(self):
        for item in self.grid_items:
            try:
                if item is None:
                    continue
                if self.dm.is_downloading(item.pubfileid):
                    item.set_status(WorkshopGridItem.STATUS_DOWNLOADING)
                elif self._is_fully_installed(item.pubfileid):
                    item.set_status(WorkshopGridItem.STATUS_INSTALLED)
                else:
                    item.set_status(WorkshopGridItem.STATUS_AVAILABLE)
            except RuntimeError:
                pass

    def _update_pagination(self):
        self.page_label2.setText(f"of {self.total_pages}")
        self.page_input.setText(str(self.current_page))
        self._update_pagination_buttons()

        if self._current_page_data:
            total_items = self._current_page_data.total_items
            current_count = len(self._current_page_data.items)
            start_item = (self.current_page - 1) * 15 + 1
            end_item = min(start_item + current_count - 1, total_items)
            
            if total_items > 0:
                results_text = f"Showing {start_item}-{end_item} of {total_items:,} wallpapers"
            else:
                results_text = "No wallpapers found"
                
            self.results_label.setText(results_text)
        else:
            self.results_label.setText("Loading...")

    def _update_pagination_buttons(self):
        can_go_back = self.current_page > 1 and not self._is_loading_page
        can_go_forward = self.current_page < self.total_pages and not self._is_loading_page
        
        self.first_btn.setEnabled(can_go_back)
        self.prev_btn.setEnabled(can_go_back)
        self.next_btn.setEnabled(can_go_forward)
        self.last_btn.setEnabled(can_go_forward)

    def _go_to_page(self, page: int):
        if self._is_loading_page:
            return

        page = max(1, min(page, self.total_pages))
        
        if page != self.current_page:
            self.current_page = page
            self.selected_pubfileid = None
            filters = self.filter_bar.get_current_filters()
            filters.page = page
            self.filter_bar.set_page(page)
            self.parser.load_page(filters)
            self.scroll_area.verticalScrollBar().setValue(0)

    def _recalculate_grid(self):
        if self._current_page_data and self._current_page_data.items:
            self._clear_grid()
            self._populate_grid(self._current_page_data.items)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'resize_timer'):
            self.resize_timer.start(200)

    def start_download(self, pubfileid: str):
        if self.dm.is_downloading(pubfileid):
            return

        cached_item = self.parser.get_cached_item(pubfileid)
        if cached_item and cached_item.preview_url:
            self._preview_url_cache[pubfileid] = cached_item.preview_url
        
        account_index = self.config.get_account_number()
        self.dm.start_download(pubfileid, account_index)
        self._update_item_statuses()
        NotificationLabel.show_notification(self.details_panel, self.tr.t("messages.download_started"), 55, 15)

    def show_downloads_popup(self, button_pos):
        self.downloads_popup.move(button_pos.x() - 90, button_pos.y())
        self.downloads_popup.show()

    def _update_downloads_list(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child is not None:
                widget = child.widget()
                if widget is not None:
                    try:
                        widget.deleteLater()
                    except RuntimeError:
                        pass
        
        all_tasks = []
        for pubfileid, info in self.dm.downloading.items():
            all_tasks.append(("download", pubfileid, info))
        for pubfileid, info in self.dm.extracting.items():
            all_tasks.append(("extract", pubfileid, info))
        
        if not all_tasks:
            label = QLabel(self.tr.t("labels.no_tasks"))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("""
                color: white;
                font-size: 14px;
                background-color: rgba(0, 0, 0, 200);
                padding: 8px 12px;
                border-radius: 6px;
            """)
            label.setFixedSize(250, 70)
            self.scroll_layout.addWidget(label)
        else:
            for task_type, pubfileid, info in all_tasks:
                self._create_task_item(task_type, pubfileid, info)
        
        self.scroll_layout.addStretch()

    def _create_task_item(self, task_type: str, pubfileid: str, info: dict):
        item_widget = QWidget()
        item_widget.setFixedSize(250, 70)
        
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        
        bg_container = QWidget()
        bg_container.setStyleSheet("background-color: rgba(0, 0, 0, 200); border-radius: 6px;")
        
        bg_layout = QHBoxLayout(bg_container)
        bg_layout.setContentsMargins(8, 6, 8, 6)
        bg_layout.setSpacing(8)
        
        if task_type == "download":
            prefix = self.tr.t("labels.download_prefix", id=pubfileid)
        else:
            prefix = self.tr.t("labels.extract_prefix", id=pubfileid)
        
        status = info.get("status", "...")
        text = f"<b>{prefix}</b><br><small>{status[:50]}</small>"
        
        text_label = QLabel(text)
        text_label.setStyleSheet("color: white; font-size: 14px; background: none")
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setWordWrap(True)
        text_label.setFixedSize(200, 50)
        text_label.setCursor(Qt.CursorShape.PointingHandCursor)

        text_label.setProperty("pubfileid", pubfileid)
        text_label.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        text_label.installEventFilter(self)
        
        text_label.mousePressEvent = lambda e, pid=pubfileid: self._on_open_browser(pid)
        
        bg_layout.addWidget(text_label)
        bg_layout.addStretch()
        
        if task_type == "download":
            delete_btn = QPushButton()
            delete_btn.setIcon(get_icon("ICON_DELETE"))
            delete_btn.setIconSize(QSize(30, 30))
            delete_btn.setFixedSize(30, 30)
            delete_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
            delete_btn.clicked.connect(lambda checked, pid=pubfileid: self._cancel_download(pid))
            bg_layout.addWidget(delete_btn)
        
        item_layout.addWidget(bg_container)
        self.scroll_layout.addWidget(item_widget)

    def eventFilter(self, obj: QWidget, event: QEvent) -> bool:
        if isinstance(obj, QLabel):
            pubfileid = obj.property("pubfileid")
            if pubfileid:
                if event.type() == QEvent.Type.Enter:
                    self._show_item_preview(pubfileid, obj)
                    return False
                    
                elif event.type() == QEvent.Type.Leave:
                    self.preview_popup.hide_preview()
                    return False
        
        return super().eventFilter(obj, event)

    def _show_item_preview(self, pubfileid: str, widget: QWidget):
        preview_url = self._preview_url_cache.get(pubfileid)
        
        if not preview_url:
            cached_item = self.parser.get_cached_item(pubfileid)
            if cached_item and cached_item.preview_url:
                preview_url = cached_item.preview_url
                self._preview_url_cache[pubfileid] = preview_url
        
        if not preview_url and self._current_page_data:
            for page_item in self._current_page_data.items:
                if page_item.pubfileid == pubfileid:
                    if page_item.preview_url:
                        preview_url = page_item.preview_url
                        self._preview_url_cache[pubfileid] = preview_url
                    break
        
        global_pos = widget.mapToGlobal(QPoint(0, widget.height() // 2))
        self.preview_popup.show_preview(preview_url or "", global_pos)

    def _on_open_browser(self, pubfileid):
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}"
        webbrowser.open(url)

    def _cancel_download(self, pubfileid: str):
        self.dm.cancel_download(pubfileid)
        QTimer.singleShot(100, self._update_downloads_list)
        self._update_item_statuses()
