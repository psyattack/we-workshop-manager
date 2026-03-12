import json
import os
import shutil
import tempfile
import webbrowser
import weakref
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QByteArray, QThread, pyqtSignal,
    QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
)
from PyQt6.QtGui import QPixmap, QMovie, QMouseEvent, QTransform, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFileDialog, QApplication,
    QFrame, QSizePolicy
)
from ui.notifications import NotificationLabel, MessageBox
from core.resources import get_icon, get_pixmap
from utils.helpers import human_readable_size, format_timestamp, get_directory_size, get_folder_mtime
from core.image_cache import ImageCache
from utils.translation_helper import DescriptionTranslator
from datetime import datetime


class TagChip(QFrame):
    
    def __init__(self, text: str, theme_manager, is_key: bool = False, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._is_key = is_key
        self._setup_ui(text)
    
    def _setup_ui(self, text: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(0)
        
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {self.theme.get_color('text_primary')};
            font-size: 11px;
            font-weight: {'600' if self._is_key else 'normal'};
            background: transparent;
            border: none;
        """)
        layout.addWidget(label)
        
        if self._is_key:
            bg_color = self.theme.get_color('primary')
            border_color = self.theme.get_color('primary_hover')
        else:
            bg_color = self.theme.get_color('bg_tertiary')
            border_color = self.theme.get_color('border')
        
        self.setStyleSheet(f"""
            TagChip {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)
        
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(20)


class TagGroupWidget(QWidget):
    
    def __init__(self, key: str, values: list, theme_manager, max_width: int = 280, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._max_width = max_width
        self._setup_ui(key, values)
    
    def _setup_ui(self, key: str, values: list):
        self.setStyleSheet("background: transparent; border: none;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(3)

        chips = []
        chips.append(TagChip(key, self.theme, is_key=True))
        
        for value in values:
            if value.strip():
                chips.append(TagChip(value.strip(), self.theme, is_key=False))
        
        h_spacing = 4
        current_row_layout = None
        current_row_width = 0
        
        for chip in chips:
            chip_width = chip.sizeHint().width() + h_spacing
            
            if current_row_layout is None or current_row_width + chip_width > self._max_width:
                row_widget = QWidget()
                row_widget.setStyleSheet("background: transparent; border: none;")
                current_row_layout = QHBoxLayout(row_widget)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                current_row_layout.setSpacing(h_spacing)
                current_row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
                main_layout.addWidget(row_widget)
                current_row_width = 0
            
            current_row_layout.addWidget(chip)
            current_row_width += chip_width

        if current_row_layout:
            current_row_layout.addStretch()


class FlowLayout(QVBoxLayout):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._current_row = None
        self._max_width = 280
        self._current_row_width = 0
        self._h_spacing = 6
        self._v_spacing = 6
        self.setSpacing(self._v_spacing)
    
    def set_max_width(self, width: int):
        self._max_width = width
    
    def add_widget_flow(self, widget: QWidget):
        widget_width = widget.sizeHint().width() + self._h_spacing
        
        if self._current_row is None or self._current_row_width + widget_width > self._max_width:
            self._start_new_row()
        
        self._current_row.addWidget(widget)
        self._current_row_width += widget_width
    
    def _start_new_row(self):
        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent; border: none;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(self._h_spacing)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.addWidget(row_widget)
        self._rows.append(row_widget)
        self._current_row = row_layout
        self._current_row_width = 0
    
    def finish(self):
        if self._current_row:
            self._current_row.addStretch()


class TagsContainer(QWidget):
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("background: transparent; border: none;")
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(8)
    
    def clear(self):
        while self._main_layout.count():
            child = self._main_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()
    
    def add_tag_group(self, key: str, values: list):
        group_widget = QWidget()
        group_widget.setStyleSheet("background: transparent; border: none;")
        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(6)
        
        key_chip = TagChip(key, self.theme, is_key=True)
        
        key_row = QWidget()
        key_row.setStyleSheet("background: transparent; border: none;")
        key_row_layout = QHBoxLayout(key_row)
        key_row_layout.setContentsMargins(0, 0, 0, 0)
        key_row_layout.setSpacing(0)
        key_row_layout.addWidget(key_chip)
        key_row_layout.addStretch()
        group_layout.addWidget(key_row)
        
        if values:
            flow = FlowLayout()
            flow.set_max_width(270)
            
            values_widget = QWidget()
            values_widget.setStyleSheet("background: transparent; border: none;")
            values_widget.setLayout(flow)
            
            for value in values:
                if value.strip():
                    chip = TagChip(value.strip(), self.theme, is_key=False)
                    flow.add_widget_flow(chip)
            
            flow.finish()
            group_layout.addWidget(values_widget)
        
        self._main_layout.addWidget(group_widget)


class AnimatedIconLabel(QLabel):
    def __init__(self, icon_name: str, size: int = 32, parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._size = size
        self._rotation = 0.0
        self._direction = 1
        self._base_pixmap = get_pixmap(icon_name, size)
        
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: none;")
        self._update_pixmap()
        
        self._animation = QPropertyAnimation(self, b"rotation")
        self._animation.setDuration(1000)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(30.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._animation.finished.connect(self._on_animation_finished)
    
    def get_rotation(self) -> float:
        return self._rotation
    
    def set_rotation(self, value: float):
        self._rotation = value
        self._update_pixmap()
    
    rotation = pyqtProperty(float, get_rotation, set_rotation)
    
    def _update_pixmap(self):
        if self._base_pixmap.isNull():
            return
        transform = QTransform()
        transform.rotate(self._rotation)
        rotated = self._base_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        x = (rotated.width() - self._size) // 2
        y = (rotated.height() - self._size) // 2
        cropped = rotated.copy(x, y, self._size, self._size)
        self.setPixmap(cropped)
    
    def _on_animation_finished(self):
        self._direction *= -1
        self._animation.setStartValue(self._rotation)
        self._animation.setEndValue(30.0 * self._direction)
        self._animation.start()
    
    def start_animation(self):
        self._animation.start()
    
    def stop_animation(self):
        self._animation.stop()
        self._rotation = 0.0
        self._update_pixmap()


class TranslationWorker(QThread):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, text: str, target_lang: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.target_lang = target_lang

    def run(self):
        try:
            translated = DescriptionTranslator.translate(self.text, self.target_lang)
            if translated:
                self.finished.emit(self.text, translated)
            else:
                self.error.emit("Translation failed")
        except Exception as e:
            self.error.emit(str(e))


class DetailsPanel(QWidget):
    MODE_NONE = 0
    MODE_INSTALLED = 1
    MODE_WORKSHOP = 2
    
    panel_collapse_requested = pyqtSignal()

    def __init__(self, wallpaper_engine, download_manager, translator, theme_manager, config_manager=None, parent=None):
        super().__init__(parent)

        self.we = wallpaper_engine
        self.dm = download_manager
        self.tr = translator
        self.theme = theme_manager
        self.config = config_manager

        self._mode = self.MODE_NONE
        self.current_pubfileid: str = ""
        self.folder_path: Optional[str] = None

        self._current_item = None
        self._current_preview_url: str = ""

        self.movie: Optional[QMovie] = None
        self._temp_gif_file: Optional[str] = None

        self._project_data: dict = {}

        self._original_description: str = ""
        self._translated_description: str = ""
        self._is_translated: bool = False
        self._translation_worker: Optional[TranslationWorker] = None
        self._description_label: Optional[QLabel] = None
        self._translate_button: Optional[QPushButton] = None

        self._pending_metadata_fetch: bool = False
        self._metadata_fetch_pubfileid: str = ""
        self._is_parser_connected: bool = False
        self._retry_timer: Optional[QTimer] = None
        
        self._loading_icon: Optional[AnimatedIconLabel] = None
        
        self._tags_container: Optional[TagsContainer] = None

        self._setup_ui()
        self.setVisible(False)

    def _setup_ui(self):
        self.setMinimumWidth(310)
        self.setMaximumWidth(310)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 10)
        main_layout.setSpacing(14)

        preview_container = QWidget()
        preview_container.setFixedSize(310, 275)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(310, 275)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme.get_color('bg_tertiary')};
                border-radius: 8px;
            }}
        """)
        preview_layout.addWidget(self.preview_label)
        
        self.collapse_btn = QPushButton(preview_container)
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setIcon(get_icon("ICON_COLLAPSE"))
        self.collapse_btn.setIconSize(QSize(16, 16))
        self.collapse_btn.move(8, 8)
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 150);
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 200);
            }}
        """)
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_btn.clicked.connect(self._on_collapse_clicked)
        self.collapse_btn.raise_()
        
        main_layout.addWidget(preview_container)

        self._create_action_buttons(main_layout)
        self._create_title_section(main_layout)
        self._create_id_section(main_layout)
        self._create_details_section(main_layout)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-left: 1px solid {self.theme.get_color('border')};
            }}
        """)

    def _on_collapse_clicked(self):
        self.panel_collapse_requested.emit()

    def _create_action_buttons(self, layout):
        self.buttons_widget = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(10)
        self.buttons_widget.setStyleSheet("QWidget { background: transparent; border: none; }")
        layout.addWidget(self.buttons_widget)

    def _create_title_section(self, layout):
        self.title_container = QWidget()
        self.title_container.setObjectName("titleContainer")
        self.title_container.setFixedHeight(80)
        self.title_container.setStyleSheet(f"""
            #titleContainer {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-radius: 12px;
            }}
        """)

        container_layout = QVBoxLayout(self.title_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.title_scroll = QScrollArea()
        self.title_scroll.setObjectName("titleScroll")
        self.title_scroll.setWidgetResizable(True)
        self.title_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.title_scroll.setStyleSheet("""
            #titleScroll {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 0px;
            }
        """)

        title_content = QWidget()
        title_content.setStyleSheet("background: transparent; border: none;")
        title_layout = QHBoxLayout(title_content)
        title_layout.setContentsMargins(5, 0, 5, 0)

        self.title_label = QLabel()
        self.title_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 18px;
            color: {self.theme.get_color('text_primary')};
            background: transparent;
        """)
        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        title_layout.addWidget(self.title_label)

        self.title_scroll.setWidget(title_content)
        container_layout.addWidget(self.title_scroll)
        layout.addWidget(self.title_container)

    def _create_id_section(self, layout):
        self.id_widget = QWidget()
        self.id_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-radius: 8px;
            }}
            QWidget:hover {{
                background-color: {self.theme.get_color('primary')};
            }}
        """)
        self.id_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        id_layout = QHBoxLayout(self.id_widget)
        id_layout.setContentsMargins(8, 4, 8, 4)
        id_layout.setSpacing(6)
        
        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap("ICON_ID", width=22, height=18))
        icon_label.setFixedSize(18, 16)
        icon_label.setStyleSheet("background: transparent; border: none;")
        id_layout.addWidget(icon_label)
        
        self.id_label = QLabel()
        self.id_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 14px;
                background: transparent;
                border: none;
            }}
        """)
        id_layout.addWidget(self.id_label)
        id_layout.addStretch()
        
        self.id_widget.mousePressEvent = self._on_id_clicked
        layout.addWidget(self.id_widget)
        
        self._update_id_section_visibility()

    def _update_id_section_visibility(self):
        if self.config:
            show_id = self.config.get_show_id_section()
            self.id_widget.setVisible(show_id)  

    def _create_details_section(self, layout):
        self.details_container = QWidget()
        self.details_container.setObjectName("detailsContainer")
        self.details_container.setStyleSheet(f"""
            #detailsContainer {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-radius: 8px;
            }}
            #detailsContainer * {{
                border: none;
                border-left: none;
                border-radius: 0px;
            }}
        """)

        container_layout = QVBoxLayout(self.details_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.details_scroll = QScrollArea()
        self.details_scroll.setObjectName("detailsScroll")
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_scroll.setStyleSheet("""
            #detailsScroll {
                border: none;
                border-left: none;
                background: transparent;
            }
            #detailsScroll > QWidget {
                border: none;
                border-left: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 0px;
            }
        """)

        details_content = QWidget()
        details_content.setObjectName("detailsContent")
        details_content.setStyleSheet("""
            #detailsContent {
                background: transparent;
                border: none;
                border-left: none;
            }
        """)

        self.details_layout = QVBoxLayout(details_content)
        self.details_layout.setContentsMargins(10, 10, 10, 10)
        self.details_layout.setSpacing(8)

        self.details_scroll.setWidget(details_content)
        container_layout.addWidget(self.details_scroll)
        layout.addWidget(self.details_container)

    @staticmethod
    def _star_file_to_text(rating_star_file: str) -> str:
        mapping = {
            "5-star_large": "★★★★★",
            "4-star_large": "★★★★☆",
            "3-star_large": "★★★☆☆",
            "2-star_large": "★★☆☆☆",
            "1-star_large": "★☆☆☆☆",
            "not-yet_large": "☆☆☆☆☆",
        }
        return mapping.get(rating_star_file, "")

    def _get_main_parser(self):
        main_window = self.window()
        if main_window and hasattr(main_window, 'workshop_tab'):
            workshop_tab = main_window.workshop_tab
            if hasattr(workshop_tab, 'parser'):
                return workshop_tab.parser
        return None

    def _get_workshop_details_panel(self):
        main_window = self.window()
        if main_window and hasattr(main_window, 'workshop_tab'):
            workshop_tab = main_window.workshop_tab
            if hasattr(workshop_tab, 'details_panel'):
                return workshop_tab.details_panel
        return None

    def _is_workshop_tab_initialized(self) -> bool:
        main_window = self.window()
        if main_window and hasattr(main_window, 'workshop_tab'):
            workshop_tab = main_window.workshop_tab
            if hasattr(workshop_tab, '_current_page_data') and workshop_tab._current_page_data is not None:
                return True
            if hasattr(workshop_tab, '_initial_load_done'):
                return workshop_tab._initial_load_done
        return False

    def _is_parser_busy_with_priority(self, parser) -> bool:
        if not self._is_workshop_tab_initialized():
            return True
        
        if parser._is_loading_page:
            return True
        
        if parser._request_type == "browse" and parser.is_loading():
            return True
        
        return False

    def _connect_to_parser(self, parser):
        if self._is_parser_connected:
            return
        
        parser.item_details_loaded.connect(self._on_metadata_loaded)
        parser.error_occurred.connect(self._on_metadata_load_error)
        parser.page_loaded.connect(self._on_workshop_page_loaded)
        self._is_parser_connected = True

    def _disconnect_from_parser(self, parser):
        if not self._is_parser_connected:
            return
        
        try:
            parser.item_details_loaded.disconnect(self._on_metadata_loaded)
        except (TypeError, RuntimeError):
            pass
        try:
            parser.error_occurred.disconnect(self._on_metadata_load_error)
        except (TypeError, RuntimeError):
            pass
        try:
            parser.page_loaded.disconnect(self._on_workshop_page_loaded)
        except (TypeError, RuntimeError):
            pass
        self._is_parser_connected = False

    def _on_workshop_page_loaded(self, page_data):
        if self._pending_metadata_fetch and self._metadata_fetch_pubfileid:
            QTimer.singleShot(100, lambda: self._retry_fetch(self._metadata_fetch_pubfileid))

    def _lock_workshop_details_panel(self, lock: bool):
        workshop_panel = self._get_workshop_details_panel()
        if workshop_panel and workshop_panel is not self:
            workshop_panel._external_lock = lock

    def _is_externally_locked(self) -> bool:
        return getattr(self, '_external_lock', False)

    def _fetch_metadata_from_workshop(self, pubfileid: str):
        parser = self._get_main_parser()
        if not parser:
            return
        
        self._metadata_fetch_pubfileid = pubfileid
        self._pending_metadata_fetch = True
        
        self._connect_to_parser(parser)
        
        if self._is_parser_busy_with_priority(parser):
            self._schedule_retry(pubfileid)
            return
        
        self._lock_workshop_details_panel(True)
        parser.load_item_details(pubfileid, use_cache=False)

    def _schedule_retry(self, pubfileid: str):
        if self._retry_timer is not None:
            self._retry_timer.stop()
            self._retry_timer.deleteLater()
        
        self._retry_timer = QTimer(self)
        self._retry_timer.setSingleShot(True)
        self._retry_timer.timeout.connect(lambda: self._retry_fetch(pubfileid))
        self._retry_timer.start(500)

    def _retry_fetch(self, pubfileid: str):
        if not self._pending_metadata_fetch:
            return
        
        if pubfileid != self._metadata_fetch_pubfileid:
            return
        
        parser = self._get_main_parser()
        if not parser:
            self._pending_metadata_fetch = False
            return
        
        if self._is_parser_busy_with_priority(parser):
            self._schedule_retry(pubfileid)
            return
        
        self._lock_workshop_details_panel(True)
        parser.load_item_details(pubfileid, use_cache=False)

    def _on_metadata_loaded(self, item):
        if not self._pending_metadata_fetch:
            return
        
        if item.pubfileid != self._metadata_fetch_pubfileid:
            return
        
        self._pending_metadata_fetch = False
        self._lock_workshop_details_panel(False)
        
        self._save_workshop_metadata(item)
        
        if self._mode == self.MODE_INSTALLED and self.current_pubfileid == item.pubfileid:
            self._setup_installed_details()

    def _on_metadata_load_error(self, error_msg: str):
        if not self._pending_metadata_fetch:
            return
        
        self._pending_metadata_fetch = False
        self._lock_workshop_details_panel(False)

    def set_installed_folder(self, folder_path: str):
        self._reset_state()

        self._mode = self.MODE_INSTALLED
        self.folder_path = folder_path
        self.current_pubfileid = Path(folder_path).name

        self.setVisible(True)

        self._project_data = self._load_project_json(folder_path)

        self.title_label.setText(self._project_data.get("title", Path(folder_path).name))
        self.id_label.setText(self.current_pubfileid)

        self._setup_installed_buttons()
        self._setup_installed_details()

        if not self._try_copy_from_grid_item(self.current_pubfileid):
            self._load_local_preview(folder_path)

        metadata = None
        if self.config:
            metadata = self.config.get_wallpaper_metadata(self.current_pubfileid)
        
        if not metadata:
            QTimer.singleShot(200, lambda: self._fetch_metadata_from_workshop(self.current_pubfileid))

    def set_workshop_item(self, item):
        if self._is_externally_locked():
            return
        
        self._reset_state()

        self._mode = self.MODE_WORKSHOP
        self._current_item = item
        self.current_pubfileid = item.pubfileid
        self._current_preview_url = item.preview_url or ""
        self.folder_path = None

        self.setVisible(True)

        self.title_label.setText(item.title or item.pubfileid)
        self.id_label.setText(self.current_pubfileid)

        self._setup_workshop_buttons()
        self._setup_workshop_details(item)

        if not self._try_copy_from_grid_item(item.pubfileid):
            self._load_remote_preview(item.preview_url)

    def _save_workshop_metadata(self, item):
        if not self.config or not item.pubfileid:
            return
        
        rating = 0
        rating_star_file = getattr(item, 'rating_star_file', '')
        if rating_star_file:
            rating_map = {
                "5-star_large": 5,
                "4-star_large": 4,
                "3-star_large": 3,
                "2-star_large": 2,
                "1-star_large": 1,
            }
            rating = rating_map.get(rating_star_file, 0)
        
        posted_timestamp = 0
        updated_timestamp = 0
        
        if item.posted_date:
            posted_timestamp = self._parse_date_to_timestamp(item.posted_date)
        if item.updated_date:
            updated_timestamp = self._parse_date_to_timestamp(item.updated_date)
        
        metadata = {
            "title": item.title or item.pubfileid,
            "tags": item.tags or {},
            "rating": rating,
            "num_ratings": getattr(item, 'num_ratings', ''),
            "rating_star_file": rating_star_file,
            "file_size": item.file_size or "",
            "posted_date": posted_timestamp,
            "posted_date_str": item.posted_date or "",
            "updated_date": updated_timestamp,
            "updated_date_str": item.updated_date or "",
            "author": item.author or "",
            "description": item.description or "",
            "preview_url": item.preview_url or "",
        }
        
        self.config.set_wallpaper_metadata(item.pubfileid, metadata)

    def _parse_date_to_timestamp(self, date_str: str) -> int:
        if not date_str:
            return 0
        
        formats = [
            "%d %b, %Y @ %I:%M%p",
            "%d %b @ %I:%M%p",
            "%b %d, %Y @ %I:%M%p",
            "%b %d @ %I:%M%p",
            "%Y-%m-%d",
            "%d.%m.%Y",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                if dt.year == 1900:
                    dt = dt.replace(year=datetime.now().year)
                return int(dt.timestamp())
            except ValueError:
                continue
        
        return 0

    def refresh_after_state_change(self):
        if not self.current_pubfileid:
            return

        if self.we.is_installed(self.current_pubfileid):
            folder_path = self.we.projects_path / self.current_pubfileid
            if folder_path.exists():
                self.set_installed_folder(str(folder_path))
        else:
            if self._current_item:
                self.set_workshop_item(self._current_item)
            else:
                parser = self._get_main_parser()
                if parser:
                    parser.load_item_details(self.current_pubfileid)

    def release_resources(self):
        self._reset_preview()
        self._cancel_pending_fetch()
        
        parser = self._get_main_parser()
        if parser:
            self._disconnect_from_parser(parser)

    def _cancel_pending_fetch(self):
        if self._retry_timer is not None:
            self._retry_timer.stop()
            self._retry_timer.deleteLater()
            self._retry_timer = None
        
        if self._pending_metadata_fetch:
            self._pending_metadata_fetch = False
            self._lock_workshop_details_panel(False)

    @property
    def large_preview(self):
        return self.preview_label

    def _reset_state(self):
        self._reset_preview()
        self._clear_details()
        self._clear_buttons()

        if self._translation_worker and self._translation_worker.isRunning():
            self._translation_worker.terminate()
            self._translation_worker = None

        self._cancel_pending_fetch()
        self._metadata_fetch_pubfileid = ""

        self._current_item = None
        self._current_preview_url = ""
        self._project_data = {}

        self._original_description = ""
        self._translated_description = ""
        self._is_translated = False
        self._description_label = None
        self._translate_button = None
        self._tags_container = None

    def _stop_movie(self):
        if self.movie is not None:
            try:
                self.movie.stop()
                try:
                    self.movie.frameChanged.disconnect(self._on_gif_frame_changed)
                except:
                    pass
                self.preview_label.setMovie(None)
                self.movie.deleteLater()
            except:
                pass
            self.movie = None

        if self._temp_gif_file and os.path.exists(self._temp_gif_file):
            try:
                os.remove(self._temp_gif_file)
            except:
                pass
            self._temp_gif_file = None

    def _stop_loading_animation(self):
        if self._loading_icon is not None:
            try:
                self._loading_icon.stop_animation()
                self._loading_icon.setParent(None)
                self._loading_icon.deleteLater()
            except:
                pass
            self._loading_icon = None

    def _reset_preview(self):
        self._current_preview_url = ""
        self._stop_movie()
        self._stop_loading_animation()
        self.preview_label.clear()
        self._show_loading_placeholder()

    def _show_loading_placeholder(self):
        self._stop_loading_animation()
        self.preview_label.setText("")
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme.get_color('bg_tertiary')};
                border-radius: 8px;
            }}
        """)
        
        self._loading_icon = AnimatedIconLabel("ICON_HOURGLASS", 48, self.preview_label)
        x = (self.preview_label.width() - 48) // 2
        y = (self.preview_label.height() - 48) // 2
        self._loading_icon.move(x - 5, y)
        self._loading_icon.show()
        self._loading_icon.start_animation()

    def _show_image_placeholder(self):
        self._stop_loading_animation()
        self.preview_label.setText("")
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme.get_color('bg_tertiary')};
                border-radius: 8px;
            }}
        """)
        
        pixmap = get_pixmap("ICON_WALLPAPER", 48)
        self.preview_label.setPixmap(pixmap)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _clear_buttons(self):
        while self.buttons_layout.count():
            child = self.buttons_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def _clear_details(self):
        while self.details_layout.count():
            child = self.details_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def _create_icon_button(self, icon_name, tooltip, callback, color=None, hover_color=None):
        if color is None:
            color = self.theme.get_color('primary')
        if hover_color is None:
            hover_color = self.theme.get_color('primary_hover')

        btn = QPushButton()
        btn.setToolTip(tooltip)
        btn.setFixedSize(43, 35)
        btn.setIcon(get_icon(icon_name))
        btn.setIconSize(QSize(22, 22))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _create_text_button(self, icon_name, text, tooltip, callback):
        btn = QPushButton()
        btn.setToolTip(tooltip)
        btn.setIcon(get_icon(icon_name))
        btn.setIconSize(QSize(24, 24))
        btn.setFixedSize(150, 35)
        btn.setText(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.get_color('primary')};
                color: {self.theme.get_color('text_primary')};
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('primary')};
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _setup_installed_buttons(self):
        self._clear_buttons()

        self.buttons_layout.addWidget(self._create_icon_button(
            "ICON_FOLDER", self.tr.t("tooltips.open_folder"), self._on_open_folder
        ))
        self.buttons_layout.addWidget(self._create_icon_button(
            "ICON_WORLD", self.tr.t("tooltips.open_workshop"), self._on_open_browser
        ))
        self.buttons_layout.addWidget(self._create_icon_button(
            "ICON_DELETE", self.tr.t("tooltips.delete_wallpaper"), self._on_delete,
            color=self.theme.get_color('accent_red'),
            hover_color=self.theme.get_color('accent_red_hover')
        ))
        self.buttons_layout.addWidget(self._create_icon_button(
            "ICON_DOWNLOAD", self.tr.t("tooltips.extract_wallpaper"), self._on_extract
        ))
        self.buttons_layout.addWidget(self._create_icon_button(
            "ICON_UPLOAD", self.tr.t("tooltips.install_wallpaper"), self._on_apply
        ))
        self.buttons_layout.addWidget(self._create_icon_button(
            "ICON_LINK", self.tr.t("tooltips.install_open_we"), self._on_install_and_open
        ))

    def _setup_workshop_buttons(self):
        self._clear_buttons()

        self.buttons_layout.addWidget(self._create_text_button(
            "ICON_UPLOAD", self.tr.t("buttons.install"), self.tr.t("buttons.install"), self._on_download
        ))
        self.buttons_layout.addWidget(self._create_text_button(
            "ICON_WORLD", self.tr.t("buttons.open_workshop"), self.tr.t("tooltips.open_workshop"), self._on_open_browser
        ))
        self.buttons_layout.addStretch()

    def _create_icon_label(self, icon_name: str, size: int = 16) -> QLabel:
        label = QLabel()
        label.setPixmap(get_pixmap(icon_name, size))
        label.setFixedSize(size, size)
        label.setStyleSheet("background: transparent; border: none;")
        return label

    def _add_detail_row(self, icon_name: str, text: str):
        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent; border: none;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        
        icon_label = self._create_icon_label(icon_name, 16)
        row_layout.addWidget(icon_label)
        
        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        text_label.setWordWrap(True)
        row_layout.addWidget(text_label, 1)
        
        self.details_layout.addWidget(row_widget)
        return text_label

    def _add_detail_label(self, text: str, icon_name: str = ""):
        if icon_name:
            return self._add_detail_row(icon_name, text)
        
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        label.setWordWrap(True)
        self.details_layout.addWidget(label)
        return label

    def _add_separator(self):
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self.theme.get_color('border')}; border: none;")
        self.details_layout.addWidget(separator)

    def _add_section_title(self, text: str, icon_name: str = None):
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(get_pixmap(icon_name, 18))
            icon_label.setStyleSheet("background: transparent; border: none;")
            header_layout.addWidget(icon_label)
        
        label = QLabel(text)
        label.setStyleSheet(f"""
            font-weight: bold;
            color: {self.theme.get_color('text_primary')};
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(label)
        header_layout.addStretch()
        self.details_layout.addWidget(header_widget)
        return label

    def _add_description_label(self, text: str):
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {self.theme.get_color('text_primary')};
            font-size: 13px;
            line-height: 1.4;
            background: transparent;
            border: none;
        """)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_layout.addWidget(label)
        return label

    def _add_description_section(self, description: str):
        self._original_description = description if description else ""
        self._translated_description = ""
        self._is_translated = False

        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        if description and description.strip():
            self._translate_button = QPushButton()
            self._translate_button.setToolTip(self.tr.t("tooltips.translate_description"))
            self._translate_button.setFixedSize(22, 22)
            self._translate_button.setIcon(get_icon("ICON_TRANSLATE"))
            self._translate_button.setIconSize(QSize(21, 21))
            self._translate_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border-radius: 6px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {self.theme.get_color('primary')};
                }}
            """)
            self._translate_button.clicked.connect(self._on_translate_clicked)
            header_layout.addWidget(self._translate_button)

        title_label = QLabel(self.tr.t("labels.description"))
        title_label.setStyleSheet(f"""
            font-weight: bold;
            color: {self.theme.get_color('text_primary')};
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        self.details_layout.addWidget(header_widget)

        display_text = description if description else self.tr.t("labels.no_description")
        self._description_label = self._add_description_label(display_text)

    def _on_translate_clicked(self):
        if not self._original_description:
            return

        if self._is_translated:
            self._description_label.setText(self._original_description)
            self._is_translated = False
            if self._translate_button:
                self._translate_button.setToolTip(self.tr.t("tooltips.translate_description"))
            return

        if self._translated_description:
            self._description_label.setText(self._translated_description)
            self._is_translated = True
            if self._translate_button:
                self._translate_button.setToolTip(self.tr.t("tooltips.show_original"))
            return

        target_lang = self.tr.get_language()

        if self._translation_worker and self._translation_worker.isRunning():
            self._translation_worker.terminate()

        self._translation_worker = TranslationWorker(self._original_description, target_lang)
        self._translation_worker.finished.connect(self._on_translation_finished)
        self._translation_worker.error.connect(self._on_translation_error)

        if self._translate_button:
            self._translate_button.setEnabled(False)
        self._description_label.setText(self.tr.t("labels.translating"))

        self._translation_worker.start()

    def _on_translation_finished(self, original: str, translated: str):
        if original != self._original_description:
            return

        self._translated_description = translated
        self._is_translated = True

        if self._description_label:
            self._description_label.setText(translated)

        if self._translate_button:
            self._translate_button.setEnabled(True)
            self._translate_button.setToolTip(self.tr.t("tooltips.show_original"))

        self._translation_worker = None

    def _on_translation_error(self, error_msg: str):
        print(f"[DetailsPanel] Translation error: {error_msg}")

        if self._description_label:
            self._description_label.setText(self._original_description)

        if self._translate_button:
            self._translate_button.setEnabled(True)
            self._translate_button.setToolTip(self.tr.t("tooltips.translate_description"))

        self._show_notification(self.tr.t("messages.translation_error"))
        self._translation_worker = None

    def _translate_tag_key(self, key: str) -> str:
        key_mapping = {
            "Type": "labels.type",
            "Resolution": "labels.resolution",
            "Category": "labels.category",
            "Age Rating": "labels.age",
            "Content Descriptors": "labels.content_descriptors",
            "Script Type": "labels.script_type",
            "Asset Type": "labels.asset_type",
            "Asset Genre": "labels.asset_genre",
            "Genre": "labels.genre",
            "Miscellaneous": "labels.miscellaneous",
        }
        if key in key_mapping:
            translated = self.tr.t(key_mapping[key])
            if translated != key_mapping[key]:
                return translated
        return key

    def _translate_single_tag_value(self, key: str, value: str) -> str:
        if not value:
            return value

        value_mappings = {
            "Type": "filters.type",
            "Resolution": "filters.resolution",
            "Category": "filters.category",
            "Age Rating": "filters.age_rating",
            "Script Type": "filters.script_type",
            "Asset Type": "filters.asset_type",
            "Asset Genre": "filters.asset_genre",
            "Genre": "filters.genre_tags",
        }

        if key in value_mappings:
            base_path = value_mappings[key]
            translated = self.tr.t(f"{base_path}.{value}")
            if translated != f"{base_path}.{value}":
                return translated
            if key == "Resolution":
                safe_value = value.replace(" ", "_").replace("x", "x")
                translated = self.tr.t(f"{base_path}.{safe_value}")
                if translated != f"{base_path}.{safe_value}":
                    return translated
            if value == "":
                translated = self.tr.t(f"{base_path}.empty")
                if translated != f"{base_path}.empty":
                    return translated

        translated = self.tr.t(f"filters.content_descriptors.{value}")
        if translated != f"filters.content_descriptors.{value}":
            return translated

        for tag_type in ["misc_tags", "genre_tags"]:
            translated = self.tr.t(f"filters.{tag_type}.{value}")
            if translated != f"filters.{tag_type}.{value}":
                return translated

        return value

    def _translate_tag_value(self, key: str, value: str) -> str:
        if not value:
            return value

        if "," in value:
            items = [item.strip() for item in value.split(",")]
            translated_items = [self._translate_single_tag_value(key, item) for item in items]
            return ", ".join(translated_items)

        return self._translate_single_tag_value(key, value)

    def _add_rating_row(self, rating_star_file: str, num_ratings: str):
        stars_text = self._star_file_to_text(rating_star_file)
        if not stars_text:
            return
        
        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent; border: none;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        
        icon_label = self._create_icon_label("ICON_STAR", 16)
        row_layout.addWidget(icon_label)
        
        rating_text = QLabel(self.tr.t("labels.rating"))
        rating_text.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        row_layout.addWidget(rating_text)
        
        row_layout.addSpacing(4)
        
        count_part = f"  ({num_ratings})" if num_ratings else ""
        stars_label = QLabel(f"{stars_text}{count_part}")
        stars_label.setStyleSheet(f"""
            color: #f5c518;
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        row_layout.addWidget(stars_label)
        
        row_layout.addStretch()
        self.details_layout.addWidget(row_widget)

    def _add_tags_section(self, tags: dict):
        if not tags:
            return
        
        self._add_separator()
        self._add_section_title(self.tr.t("labels.tags"), "ICON_TAGS")
        
        for key, value in tags.items():
            translated_key = self._translate_tag_key(key)
            clean_key = translated_key.rstrip(':')
            
            if isinstance(value, bool):
                values = []
            elif isinstance(value, str) and value.strip():
                if "," in value:
                    values = [self._translate_single_tag_value(key, v.strip()) for v in value.split(",")]
                else:
                    values = [self._translate_single_tag_value(key, value)]
            else:
                values = []
            
            tag_group = TagGroupWidget(clean_key, values, self.theme, max_width=280)
            self.details_layout.addWidget(tag_group)

    def _setup_installed_details(self):
        self._clear_details()

        metadata = None
        if self.config:
            metadata = self.config.get_wallpaper_metadata(self.current_pubfileid)

        if metadata:
            rating_star_file = metadata.get('rating_star_file', '')
            num_ratings = metadata.get('num_ratings', '')
            
            if rating_star_file:
                self._add_rating_row(rating_star_file, num_ratings)

            size_bytes = get_directory_size(self.folder_path)
            self._add_detail_row("ICON_PACKAGE", self.tr.t("labels.size", size=human_readable_size(size_bytes)))

            if metadata.get('posted_date_str'):
                self._add_detail_row("ICON_CALENDAR", self.tr.t("labels.posted", date=metadata['posted_date_str']))
            if metadata.get('updated_date_str'):
                self._add_detail_row("ICON_REFRASH", self.tr.t("labels.updated", date=metadata['updated_date_str']))

            mtime = get_folder_mtime(self.folder_path)
            self._add_detail_row("ICON_CALENDAR", self.tr.t("labels.installed", date=format_timestamp(mtime)))

            if metadata.get('author'):
                self._add_detail_row("ICON_USER", self.tr.t("labels.author", author=metadata['author']))

            tags = metadata.get('tags', {})
            if tags:
                self._add_tags_section(tags)

            description = metadata.get('description', '') or self._project_data.get("description", "")
            if description and description.strip():
                self._add_separator()
                self._add_description_section(description)
        else:
            size_bytes = get_directory_size(self.folder_path)
            self._add_detail_row("ICON_PACKAGE", self.tr.t("labels.size", size=human_readable_size(size_bytes)))
            
            mtime = get_folder_mtime(self.folder_path)
            self._add_detail_row("ICON_CALENDAR", self.tr.t("labels.installed", date=format_timestamp(mtime)))
            
            description = self._project_data.get("description", "")
            if description and description.strip():
                self._add_separator()
                self._add_description_section(description)

        self.details_layout.addStretch()

    def _setup_workshop_details(self, item):
        self._clear_details()

        rating_star_file = getattr(item, 'rating_star_file', '')
        num_ratings = getattr(item, 'num_ratings', '')

        if rating_star_file:
            self._add_rating_row(rating_star_file, num_ratings)

        if item.file_size:
            self._add_detail_row("ICON_PACKAGE", self.tr.t("labels.size", size=item.file_size))
        if item.posted_date:
            self._add_detail_row("ICON_CALENDAR", self.tr.t("labels.posted", date=item.posted_date))
        if item.updated_date:
            self._add_detail_row("ICON_REFRASH", self.tr.t("labels.updated", date=item.updated_date))
        if item.author:
            self._add_detail_row("ICON_USER", self.tr.t("labels.author", author=item.author))

        if item.tags:
            self._add_tags_section(item.tags)

        if item.description:
            self._add_separator()
            self._add_description_section(item.description)

        self.details_layout.addStretch()

    def _find_grid_item(self, pubfileid: str):
        parent = self.parent()
        while parent and not hasattr(parent, 'grid_items'):
            parent = parent.parent()
        if parent and hasattr(parent, 'grid_items'):
            for item in parent.grid_items:
                try:
                    if item and item.pubfileid == pubfileid:
                        return item
                except RuntimeError:
                    continue
        return None

    def _try_copy_from_grid_item(self, pubfileid: str) -> bool:
        grid_item = self._find_grid_item(pubfileid)
        if not grid_item:
            return False
        try:
            if hasattr(grid_item, '_is_gif') and grid_item._is_gif and hasattr(grid_item, '_gif_buffer') and grid_item._gif_buffer:
                self._apply_preview_gif(grid_item._gif_buffer)
                return True
            if hasattr(grid_item, '_pixmap') and grid_item._pixmap and not grid_item._pixmap.isNull():
                self._apply_preview_pixmap(grid_item._pixmap)
                return True
        except (RuntimeError, AttributeError):
            pass
        return False

    def _load_local_preview(self, folder_path: str):
        preview_file = None
        for ext in ["png", "gif", "jpg"]:
            candidate = Path(folder_path) / f"preview.{ext}"
            if candidate.exists():
                preview_file = candidate
                break

        if not preview_file:
            self._stop_loading_animation()
            self.preview_label.clear()
            self.preview_label.setText(self.tr.t("labels.no_preview"))
            return

        try:
            if preview_file.suffix.lower() == ".gif":
                self._stop_movie()
                self._stop_loading_animation()
                self.movie = QMovie(str(preview_file))
                self.movie.setScaledSize(self.preview_label.size())
                self.preview_label.setMovie(self.movie)
                self.movie.frameChanged.connect(self._on_gif_frame_changed)
                self.preview_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {self.theme.get_color('bg_tertiary')};
                        border-radius: 8px;
                    }}
                """)
                self.movie.start()
            else:
                pixmap = QPixmap(str(preview_file))
                if not pixmap.isNull():
                    self._apply_preview_pixmap(pixmap)
        except Exception as e:
            print(f"[DetailsPanel] Load local preview error: {e}")
            self._stop_loading_animation()
            self.preview_label.clear()
            self.preview_label.setText(self.tr.t("messages.error"))

    def _load_remote_preview(self, url: str):
        if not url:
            self._show_image_placeholder()
            return

        self._current_preview_url = url
        cache = ImageCache.instance()

        pixmap = cache.get_pixmap(url)
        if pixmap:
            self._apply_preview_pixmap(pixmap)
            return

        gif_data = cache.get_gif(url)
        if gif_data:
            self._apply_preview_gif(gif_data)
            return

        expected_pubfileid = self.current_pubfileid
        expected_url = url
        weak_self = weakref.ref(self)

        def on_loaded(loaded_url: str, data, is_gif: bool):
            self_ref = weak_self()
            if self_ref is None:
                return
            if self_ref.current_pubfileid != expected_pubfileid:
                return
            if self_ref._current_preview_url != expected_url:
                return
            if data is None:
                self_ref._show_image_placeholder()
                return
            if is_gif:
                self_ref._apply_preview_gif(data)
            else:
                self_ref._apply_preview_pixmap(data)

        cache.load_image(url, callback=on_loaded)

    def _apply_preview_pixmap(self, pixmap: QPixmap):
        if pixmap is None or pixmap.isNull():
            self._show_image_placeholder()
            return
        try:
            self._stop_loading_animation()
            label_size = self.preview_label.size()
            scaled = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (scaled.width() - label_size.width()) // 2
            y = (scaled.height() - label_size.height()) // 2
            cropped = scaled.copy(x, y, label_size.width(), label_size.height())
            rounded = self._create_rounded_pixmap(cropped, radius=8)
            self.preview_label.setPixmap(rounded)
            self.preview_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.theme.get_color('bg_tertiary')};
                    border-radius: 8px;
                }}
            """)
        except Exception as e:
            print(f"[DetailsPanel] Apply pixmap error: {e}")
            self._show_image_placeholder()

    def _create_rounded_pixmap(self, pixmap: QPixmap, radius: int = 8) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, pixmap.width(), pixmap.height()), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return rounded

    def _apply_preview_gif(self, data: QByteArray):
        if data is None or data.isEmpty():
            self._show_image_placeholder()
            return
        try:
            self._stop_movie()
            self._stop_loading_animation()

            fd, self._temp_gif_file = tempfile.mkstemp(suffix='.gif')
            os.write(fd, bytes(data))
            os.close(fd)

            self.movie = QMovie(self._temp_gif_file)
            self.movie.setScaledSize(self.preview_label.size())
            self.preview_label.setMovie(self.movie)
            self.movie.frameChanged.connect(self._on_gif_frame_changed)
            self.preview_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.theme.get_color('bg_tertiary')};
                    border-radius: 8px;
                }}
            """)
            self.movie.start()
        except Exception as e:
            print(f"[DetailsPanel] Apply GIF error: {e}")
            self._show_image_placeholder()

    def _on_gif_frame_changed(self, frame_number: int):
        if self.movie is None:
            return
        current_pixmap = self.movie.currentPixmap()
        if not current_pixmap.isNull():
            label_size = self.preview_label.size()
            x = (current_pixmap.width() - label_size.width()) // 2
            y = (current_pixmap.height() - label_size.height()) // 2
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            crop_w = min(current_pixmap.width(), label_size.width())
            crop_h = min(current_pixmap.height(), label_size.height())
            cropped = current_pixmap.copy(x, y, crop_w, crop_h)
            rounded = self._create_rounded_pixmap(cropped, radius=8)
            self.preview_label.setPixmap(rounded)

    def _on_open_folder(self):
        if self.folder_path and Path(self.folder_path).exists():
            os.startfile(self.folder_path)

    def _on_open_browser(self):
        webbrowser.open(f"https://steamcommunity.com/sharedfiles/filedetails/?id={self.current_pubfileid}")

    def _on_download(self):
        if not self.current_pubfileid:
            return
        parent = self.parent()
        while parent and not hasattr(parent, 'start_download'):
            parent = parent.parent()
        if parent:
            parent.start_download(self.current_pubfileid)

    def _on_delete(self):
        if not self.folder_path:
            return

        if self.we.is_wallpaper_current(Path(self.folder_path)):
            MessageBox.warning(
                None,
                self.tr.t("dialog.warning"),
                self.tr.t("messages.cannot_delete_active")
            )
            return

        reply = MessageBox.question(
            None,
            self.tr.t("dialog.confirm_deletion"),
            self.tr.t("messages.confirm_delete")
        )
        if reply != MessageBox.StandardButton.Yes:
            return

        pubfileid = self.current_pubfileid
        main_window = self.window()

        if hasattr(main_window, 'wallpapers_tab'):
            main_window.wallpapers_tab.release_resources_for_folder(self.folder_path)

        if hasattr(main_window, 'workshop_tab'):
            workshop_tab = main_window.workshop_tab
            if (hasattr(workshop_tab, 'details_panel') and
                hasattr(workshop_tab.details_panel, 'current_pubfileid') and
                workshop_tab.details_panel.current_pubfileid == pubfileid):
                workshop_tab.details_panel.release_resources()
            for item in getattr(workshop_tab, 'grid_items', []):
                if hasattr(item, 'pubfileid') and item.pubfileid == pubfileid:
                    if hasattr(item, 'release_resources'):
                        item.release_resources()

        self.release_resources()
        folder_to_delete = self.folder_path

        def perform_deletion():
            try:
                folder = Path(folder_to_delete)
                if folder.exists():
                    shutil.rmtree(folder)
                
                if self.config:
                    self.config.remove_wallpaper_metadata(pubfileid)
                
                self._show_notification(self.tr.t("messages.wallpaper_deleted"))

                if hasattr(main_window, 'workshop_tab'):
                    if hasattr(main_window.workshop_tab, '_on_page_loaded'):
                        main_window.workshop_tab._on_page_loaded(
                            getattr(main_window.workshop_tab, '_current_page_data', None)
                        )
                    if hasattr(main_window.workshop_tab, '_on_download_completed'):
                        main_window.workshop_tab._on_download_completed(pubfileid, True)

                QTimer.singleShot(100, self.refresh_after_state_change)
                if hasattr(main_window, 'refresh_wallpapers'):
                    main_window.refresh_wallpapers()
            except Exception as e:
                MessageBox.critical(self, self.tr.t("dialog.error"), f"Failed to delete:\n{str(e)}")

        QTimer.singleShot(200, perform_deletion)

    def _on_extract(self):
        if not self.folder_path:
            self._show_notification(self.tr.t("messages.no_wallpaper_selected"))
            return

        output_dir = QFileDialog.getExistingDirectory(self, self.tr.t("messages.select_output_directory"), str(Path.home()))
        if not output_dir:
            return

        success = self.dm.start_extraction(self.current_pubfileid, Path(output_dir))
        if success:
            self._show_notification(self.tr.t("messages.extraction_started"))
        else:
            self._show_notification(self.tr.t("messages.no_pkg_file"))

    def _on_apply(self):
        if not self.folder_path:
            return
        self.we.apply_wallpaper(Path(self.folder_path) / "project.json")

        if self.config and self.config.get_minimize_on_apply():
            window = self.window()
            if window:
                window.showMinimized()

    def _on_install_and_open(self):
        self._on_apply()
        self.we.open_wallpaper_engine(show_window=True)

    def _on_id_clicked(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            QApplication.clipboard().setText(self.current_pubfileid)
            self._show_notification(self.tr.t("messages.id_copied"))

    def _load_project_json(self, folder_path: str) -> dict:
        json_path = Path(folder_path) / "project.json"
        if not json_path.exists():
            return {}
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[DetailsPanel] Error loading project.json: {e}")
            return {}

    def _show_notification(self, message: str):
        NotificationLabel.show_notification(self.parent(), message, 55, 15)