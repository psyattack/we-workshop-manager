import json
import os
import shutil
import webbrowser
import weakref
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QThread, QTimer, Qt, QSize, pyqtSignal, QRectF, QEvent, QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QMovie, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from infrastructure.cache.image_cache import ImageCache
from infrastructure.resources.resource_manager import get_icon, get_pixmap
from services.description_translation_service import DescriptionTranslationService
from shared.date_utils import format_timestamp
from shared.filesystem import get_directory_size, get_folder_mtime
from shared.formatting import human_readable_size
from ui.notifications import MessageBox, NotificationLabel
from ui.widgets.animated_icon_label import AnimatedIconLabel
from ui.widgets.custom_tooltip import install_tooltip
from ui.widgets.tag_widgets import TagGroupWidget


class TranslationWorker(QThread):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, text: str, target_lang: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.target_lang = target_lang

    def run(self):
        try:
            translated = DescriptionTranslationService.translate(self.text, self.target_lang)
            if translated:
                self.finished.emit(self.text, translated)
            else:
                self.error.emit("Translation failed")
        except Exception as error:
            self.error.emit(str(error))


class DetailsPanel(QWidget):
    MODE_NONE = 0
    MODE_INSTALLED = 1
    MODE_WORKSHOP = 2
    DESCRIPTION_PREVIEW_LINES = 4

    panel_collapse_requested = pyqtSignal()
    author_clicked = pyqtSignal(str, str)

    CONTENT_WIDTH = 310

    def __init__(
        self,
        wallpaper_engine_client,
        download_service,
        translator,
        theme_manager,
        config_service=None,
        metadata_service=None,
        parent=None,
    ):
        super().__init__(parent)

        self.we = wallpaper_engine_client
        self.dm = download_service
        self.tr = translator
        self.theme = theme_manager
        self.config = config_service
        self.metadata_service = metadata_service

        self._mode = self.MODE_NONE
        self.current_pubfileid: str = ""
        self.folder_path: Optional[str] = None
        self._current_item = None
        self._current_preview_url: str = ""

        self.movie: Optional[QMovie] = None
        self._gif_buffer = None
        self._project_data: dict = {}

        self._original_description: str = ""
        self._translated_description: str = ""
        self._is_translated = False
        self._translation_worker: Optional[TranslationWorker] = None
        self._description_label: Optional[QLabel] = None
        self._translate_button: Optional[QPushButton] = None
        self._expand_description_button: Optional[QPushButton] = None
        self._description_expanded = False
        self._displayed_description_full: str = ""
        self._description_animation: Optional[QPropertyAnimation] = None
        self._pending_metadata_fetch = False

        self._pending_metadata_fetch = False
        self._metadata_fetch_pubfileid = ""
        self._is_parser_connected = False
        self._retry_timer: Optional[QTimer] = None
        self._loading_icon: Optional[AnimatedIconLabel] = None
        self._download_btn = None
        self._external_lock = False

        self._setup_ui()
        self.setVisible(False)
        
        self.preview_label.installEventFilter(self)

    @property
    def large_preview(self):
        return self.preview_label

    def _setup_ui(self) -> None:
        self.setMinimumWidth(320)
        self.setMaximumWidth(320)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 8, 5, 8)
        main_layout.setSpacing(8)

        preview_container = QWidget(self)
        preview_container.setFixedSize(self.CONTENT_WIDTH, 275)

        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)

        self.preview_label = QLabel(preview_container)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(self.CONTENT_WIDTH, 275)
        self.preview_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {self.theme.get_color('bg_tertiary')};
                border-radius: 8px;
            }}
            """
        )
        preview_layout.addWidget(self.preview_label)

        self.collapse_btn = QPushButton(preview_container)
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setIcon(get_icon("ICON_COLLAPSE"))
        self.collapse_btn.setIconSize(QSize(16, 16))
        self.collapse_btn.move(8, 8)
        self.collapse_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                border-radius: 6px;
                border: none;
            }

            QPushButton:hover {
                background-color: rgba(0, 0, 0, 200);
            }
            """
        )
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_btn.clicked.connect(self._on_collapse_clicked)
        self.collapse_btn.raise_()

        main_layout.addWidget(preview_container, 0, Qt.AlignmentFlag.AlignHCenter)

        self._create_action_buttons(main_layout)
        self._create_title_section(main_layout)
        self._create_id_section(main_layout)
        self._create_details_section(main_layout)

        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: transparent;
                border: none;
            }}

            QToolTip {{
                background-color: {self.theme.get_color('bg_primary')};
                color: {self.theme.get_color('text_primary')};
                border: 1px solid {self.theme.get_color('border')};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            """
        )

    def _on_collapse_clicked(self) -> None:
        self.panel_collapse_requested.emit()

    def _create_action_buttons(self, layout) -> None:
        self.buttons_widget = QWidget(self)
        self.buttons_widget.setFixedWidth(self.CONTENT_WIDTH)

        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setContentsMargins(4, 0, 0, 0)
        self.buttons_layout.setSpacing(5)

        self.buttons_widget.setStyleSheet("QWidget { background: transparent; border: none; }")
        layout.addWidget(self.buttons_widget, 0, Qt.AlignmentFlag.AlignHCenter)

    def _create_title_section(self, layout) -> None:
        self.title_container = QWidget(self)
        self.title_container.setObjectName("titleContainer")
        self.title_container.setFixedSize(self.CONTENT_WIDTH, 74)
        self.title_container.setStyleSheet(
            f"""
            #titleContainer {{
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                border: 1px solid {self.theme.get_color('border')};
            }}
            """
        )

        container_layout = QVBoxLayout(self.title_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.title_scroll = QScrollArea(self.title_container)
        self.title_scroll.setObjectName("titleScroll")
        self.title_scroll.setWidgetResizable(True)
        self.title_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.title_scroll.setStyleSheet(
            """
            #titleScroll { border: none; background: transparent; }
            QScrollBar:vertical { width: 0px; }
            """
        )

        title_content = QWidget(self.title_scroll)
        title_content.setStyleSheet("background: transparent; border: none;")

        title_layout = QHBoxLayout(title_content)
        title_layout.setContentsMargins(8, 4, 8, 4)

        self.title_label = QLabel(title_content)
        self.title_label.setStyleSheet(
            f"""
            font-weight: bold;
            font-size: 18px;
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            border: none;
            """
        )
        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        title_layout.addWidget(self.title_label)

        self.title_scroll.setWidget(title_content)
        container_layout.addWidget(self.title_scroll)

        layout.addWidget(self.title_container, 0, Qt.AlignmentFlag.AlignHCenter)

    def _create_id_section(self, layout) -> None:
        self.id_widget = QWidget(self)
        self.id_widget.setFixedWidth(self.CONTENT_WIDTH)
        self.id_widget.setStyleSheet(
            f"""
            QWidget {{
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                border: 1px solid {self.theme.get_color('border')};
            }}

            QWidget:hover {{
                background-color: {self.theme.get_color('primary')};
            }}
            """
        )
        self.id_widget.setCursor(Qt.CursorShape.PointingHandCursor)

        id_layout = QHBoxLayout(self.id_widget)
        id_layout.setContentsMargins(8, 4, 8, 4)
        id_layout.setSpacing(6)

        icon_label = QLabel(self.id_widget)
        icon_label.setPixmap(get_pixmap("ICON_ID", width=22, height=18))
        icon_label.setFixedSize(18, 16)
        icon_label.setStyleSheet("background: transparent; border: none;")
        id_layout.addWidget(icon_label)

        self.id_label = QLabel(self.id_widget)
        self.id_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 14px;
                background: transparent;
                border: none;
            }}
            """
        )
        id_layout.addWidget(self.id_label)
        id_layout.addStretch()

        self.id_widget.mousePressEvent = self._on_id_clicked
        layout.addWidget(self.id_widget, 0, Qt.AlignmentFlag.AlignHCenter)

        self._update_id_section_visibility()

    def _update_id_section_visibility(self) -> None:
        if not hasattr(self, "id_widget") or self.id_widget is None:
            return

        show_id = True
        if self.config:
            show_id = bool(self.config.get_show_id_section())

        self.id_widget.setVisible(show_id)

    def _create_details_section(self, layout) -> None:
        self.details_container = QWidget(self)
        self.details_container.setObjectName("detailsContainer")
        self.details_container.setFixedWidth(self.CONTENT_WIDTH)
        self.details_container.setStyleSheet(f"""
            #detailsContainer {{
                background-color: transparent;
                border-radius: 8px;
                border: none;
            }}
            #detailsContainer * {{
                border: none;
                border-left: none;
                border-radius: 0px;
            }}
        """)

        container_layout = QVBoxLayout(self.details_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.details_scroll = QScrollArea(self.details_container)
        self.details_scroll.setObjectName("detailsScroll")
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_scroll.setStyleSheet(
            """
            #detailsScroll { border: none; border-left: none; background: transparent; }
            #detailsScroll > QWidget { border: none; border-left: none; background: transparent; }
            QScrollBar:vertical { width: 0px; }
            """
        )

        details_content = QWidget(self.details_scroll)
        details_content.setObjectName("detailsContent")
        details_content.setStyleSheet(
            """
            #detailsContent {
                background: transparent;
                border: none;
                border-left: none;
            }
            """
        )

        self.details_layout = QVBoxLayout(details_content)
        self.details_layout.setContentsMargins(8, 8, 8, 0)
        self.details_layout.setSpacing(8)

        self.details_scroll.setWidget(details_content)
        container_layout.addWidget(self.details_scroll)

        layout.addWidget(self.details_container, 0, Qt.AlignmentFlag.AlignHCenter)

    def _get_main_parser(self):
        main_window = self.window()
        if main_window and hasattr(main_window, "workshop_tab"):
            workshop_tab = main_window.workshop_tab
            if hasattr(workshop_tab, "parser"):
                return workshop_tab.parser
        return None

    def _get_workshop_details_panel(self):
        main_window = self.window()
        if main_window and hasattr(main_window, "workshop_tab"):
            workshop_tab = main_window.workshop_tab
            if hasattr(workshop_tab, "details_panel"):
                return workshop_tab.details_panel
        return None

    def _get_main_window(self):
        window = self.window()
        return window if window is not None else None

    def _switch_to_workshop_tab(self):
        main_window = self._get_main_window()
        if not main_window:
            return None

        if hasattr(main_window, "top_tabs"):
            main_window.top_tabs.setCurrentIndex(0)
        if hasattr(main_window, "stack"):
            main_window.stack.setCurrentIndex(0)

        if hasattr(main_window, "workshop_tab"):
            return main_window.workshop_tab
        return None

    def _navigate_to_author(self, author_name: str, author_url: str) -> None:
        if not author_url:
            return

        workshop_tab = self._switch_to_workshop_tab()
        if workshop_tab is None:
            webbrowser.open(author_url)
            return

        workshop_tab._on_author_clicked(author_name, author_url)

    def _navigate_to_collection(self, collection_id: str) -> None:
        if not collection_id:
            return

        workshop_tab = self._switch_to_workshop_tab()
        if workshop_tab is None:
            webbrowser.open(f"https://steamcommunity.com/sharedfiles/filedetails/?id={collection_id}")
            return

        workshop_tab._on_collection_item_clicked(collection_id)

    def _is_workshop_tab_initialized(self) -> bool:
        main_window = self.window()
        if main_window and hasattr(main_window, "workshop_tab"):
            workshop_tab = main_window.workshop_tab
            if hasattr(workshop_tab, "_current_page_data") and workshop_tab._current_page_data is not None:
                return True
            if hasattr(workshop_tab, "_initial_load_done"):
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

    def _connect_to_parser(self, parser) -> None:
        if self._is_parser_connected:
            return

        parser.item_details_loaded.connect(self._on_metadata_loaded)
        parser.error_occurred.connect(self._on_metadata_load_error)
        parser.page_loaded.connect(self._on_workshop_page_loaded)
        self._is_parser_connected = True

    def _disconnect_from_parser(self, parser) -> None:
        if not self._is_parser_connected:
            return

        try:
            parser.item_details_loaded.disconnect(self._on_metadata_loaded)
        except Exception:
            pass

        try:
            parser.error_occurred.disconnect(self._on_metadata_load_error)
        except Exception:
            pass

        try:
            parser.page_loaded.disconnect(self._on_workshop_page_loaded)
        except Exception:
            pass

        self._is_parser_connected = False

    def _on_workshop_page_loaded(self, page_data) -> None:
        if self._pending_metadata_fetch and self._metadata_fetch_pubfileid:
            QTimer.singleShot(100, lambda: self._retry_fetch(self._metadata_fetch_pubfileid))

    def _lock_workshop_details_panel(self, lock: bool) -> None:
        workshop_panel = self._get_workshop_details_panel()
        if workshop_panel and workshop_panel is not self:
            workshop_panel._external_lock = lock

    def _is_externally_locked(self) -> bool:
        return getattr(self, "_external_lock", False)

    def _fetch_metadata_from_workshop(self, pubfileid: str) -> None:
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

    def _schedule_retry(self, pubfileid: str) -> None:
        if self._retry_timer is not None:
            self._retry_timer.stop()
            self._retry_timer.deleteLater()

        self._retry_timer = QTimer(self)
        self._retry_timer.setSingleShot(True)
        self._retry_timer.timeout.connect(lambda: self._retry_fetch(pubfileid))
        self._retry_timer.start(500)

    def _retry_fetch(self, pubfileid: str) -> None:
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

    def _on_metadata_loaded(self, item) -> None:
        if not self._pending_metadata_fetch:
            return
        if item.pubfileid != self._metadata_fetch_pubfileid:
            return

        self._pending_metadata_fetch = False
        self._lock_workshop_details_panel(False)

        if self.metadata_service:
            self.metadata_service.save_from_workshop_item(item)

        if self._mode == self.MODE_INSTALLED and self.current_pubfileid == item.pubfileid:
            self._setup_installed_details()
            self._update_id_section_visibility()

    def _on_metadata_load_error(self, error_msg: str) -> None:
        if not self._pending_metadata_fetch:
            return

        self._pending_metadata_fetch = False
        self._lock_workshop_details_panel(False)

    def set_installed_folder(self, folder_path: str) -> None:
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
        self._update_id_section_visibility()

        if not self._try_copy_from_grid_item(self.current_pubfileid):
            self._load_local_preview(folder_path)

        metadata = self.metadata_service.get(self.current_pubfileid) if self.metadata_service else None
        if not metadata:
            QTimer.singleShot(200, lambda: self._fetch_metadata_from_workshop(self.current_pubfileid))

    def set_workshop_item(self, item) -> None:
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
        self._update_id_section_visibility()

        if not self._try_copy_from_grid_item(item.pubfileid):
            self._load_remote_preview(item.preview_url)

    def refresh_after_state_change(self) -> None:
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

    def release_resources(self) -> None:
        self._reset_preview()
        self._cancel_pending_fetch()

        parser = self._get_main_parser()
        if parser:
            self._disconnect_from_parser(parser)

    def _cancel_pending_fetch(self) -> None:
        if self._retry_timer is not None:
            self._retry_timer.stop()
            self._retry_timer.deleteLater()
            self._retry_timer = None

        if self._pending_metadata_fetch:
            self._pending_metadata_fetch = False
            self._lock_workshop_details_panel(False)

    def _reset_state(self) -> None:
        self._reset_preview()
        self._clear_details()
        self._clear_buttons()

        if self._translation_worker and self._translation_worker.isRunning():
            self._translation_worker.terminate()
        self._translation_worker = None

        if self._description_animation is not None:
            try:
                self._description_animation.stop()
                self._description_animation.deleteLater()
            except Exception:
                pass
            self._description_animation = None

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
        self._expand_description_button = None
        self._description_expanded = False
        self._displayed_description_full = ""
        self._download_btn = None

    def _stop_movie(self) -> None:
        if self.movie is not None:
            try:
                self.movie.stop()
                try:
                    self.movie.frameChanged.disconnect(self._on_gif_frame_changed)
                except Exception:
                    pass
                self.preview_label.setMovie(None)
                self.movie.deleteLater()
            except Exception:
                pass
            self.movie = None

        if self._gif_buffer is not None:
            try:
                self._gif_buffer.close()
                self._gif_buffer.deleteLater()
            except Exception:
                pass
            self._gif_buffer = None

    def eventFilter(self, obj, event):
        if obj is self.preview_label and event.type() == QEvent.Type.Resize:
            self._update_loading_icon_position()
        return super().eventFilter(obj, event)

    def _update_loading_icon_position(self) -> None:
        if self._loading_icon is None:
            return
        
        try:
            icon_size = self._loading_icon.width()
            x = (self.preview_label.width() - icon_size) // 2
            y = (self.preview_label.height() - icon_size) // 2
            self._loading_icon.move(x - 5, y)
        except RuntimeError:
            pass

    def _stop_loading_animation(self) -> None:
        if self._loading_icon is not None:
            try:
                self._loading_icon.stop_animation()
                self._loading_icon.hide()
                self._loading_icon.deleteLater()
            except Exception:
                pass
            self._loading_icon = None

    def _reset_preview(self) -> None:
        self._current_preview_url = ""
        self._stop_movie()
        self._stop_loading_animation()
        self.preview_label.clear()
        self._show_loading_placeholder()

    def _show_loading_placeholder(self) -> None:
        self._stop_loading_animation()
        self.preview_label.setText("")
        self.preview_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {self.theme.get_color('bg_tertiary')};
                border-radius: 8px;
            }}
            """
        )

        self._loading_icon = AnimatedIconLabel("ICON_HOURGLASS", 48, self.preview_label)
        x = (self.preview_label.width() - 48) // 2
        y = (self.preview_label.height() - 48) // 2
        self._loading_icon.move(x - 5, y)
        self._loading_icon.show()
        self._loading_icon.start_animation()

    def _show_image_placeholder(self) -> None:
        self._stop_loading_animation()
        self.preview_label.setText("")
        self.preview_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {self.theme.get_color('bg_tertiary')};
                border-radius: 8px;
            }}
            """
        )
        self.preview_label.setPixmap(get_pixmap("ICON_WALLPAPER", 48))
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _clear_buttons(self) -> None:
        while self.buttons_layout.count():
            child = self.buttons_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def _clear_details(self) -> None:
        while self.details_layout.count():
            child = self.details_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def _button_tooltip_style(self) -> str:
        return f"""
        QPushButton {{
            border: none;
        }}

        QToolTip {{
            background-color: {self.theme.get_color('bg_primary')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border')};
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12px;
        }}
        """

    def _create_icon_button(self, icon_name, tooltip, callback, color=None, hover_color=None):
        button_color = color or self.theme.get_color("primary")
        button_hover = hover_color or self.theme.get_color("primary_hover")

        button = QPushButton(self)
        install_tooltip(button, tooltip, "bottom", self.theme)
        button.setFixedSize(45, 35)
        button.setIcon(get_icon(icon_name))
        button.setIconSize(QSize(22, 22))
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {button_color};
                border-radius: 10px;
                border: none;
            }}

            QPushButton:hover {{
                background-color: {button_hover};
            }}
            """
        )
        button.clicked.connect(callback)
        return button

    def _create_text_button(self, icon_name, text, tooltip, callback):
        button = QPushButton(self)
        install_tooltip(button, tooltip, "bottom", self.theme)
        button.setIcon(get_icon(icon_name))
        button.setIconSize(QSize(24, 24))
        button.setFixedSize(148, 35)
        button.setText(text)
        button.setStyleSheet(
            f"""
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
            """
        )
        button.clicked.connect(callback)
        return button

    def _setup_installed_buttons(self) -> None:
        self._clear_buttons()

        self.buttons_layout.addWidget(
            self._create_icon_button(
                "ICON_UPLOAD",
                self.tr.t("tooltips.install_wallpaper"),
                self._on_apply,
            )
        )
        self.buttons_layout.addWidget(
            self._create_icon_button(
                "ICON_LINK",
                self.tr.t("tooltips.install_open_we"),
                self._on_install_and_open,
            )
        )
        self.buttons_layout.addWidget(
            self._create_icon_button(
                "ICON_EXTRACT",
                self.tr.t("tooltips.extract_wallpaper"),
                self._on_extract,
            )
        )
        self.buttons_layout.addWidget(
            self._create_icon_button(
                "ICON_FOLDER",
                self.tr.t("tooltips.open_folder"),
                self._on_open_folder,
            )
        )
        self.buttons_layout.addWidget(
            self._create_icon_button(
                "ICON_WORLD",
                self.tr.t("tooltips.open_workshop"),
                self._on_open_browser,
            )
        )
        self.buttons_layout.addWidget(
            self._create_icon_button(
                "ICON_DELETE",
                self.tr.t("tooltips.delete_wallpaper"),
                self._on_delete,
                color=self.theme.get_color("accent_red"),
                hover_color=self.theme.get_color("accent_red_hover"),
            )
        )

    def _setup_workshop_buttons(self) -> None:
        self._clear_buttons()

        is_downloading = self.dm.is_downloading(self.current_pubfileid)

        if is_downloading:
            self._download_btn = self._create_downloading_button()
            self.buttons_layout.addWidget(self._download_btn)
        else:
            self._download_btn = self._create_text_button(
                "ICON_UPLOAD",
                self.tr.t("buttons.install"),
                self.tr.t("buttons.install"),
                self._on_download,
            )
            self.buttons_layout.addWidget(self._download_btn)

        self.buttons_layout.addWidget(
            self._create_text_button(
                "ICON_WORLD",
                self.tr.t("buttons.open_workshop"),
                self.tr.t("tooltips.open_workshop"),
                self._on_open_browser,
            )
        )
        self.buttons_layout.addStretch()

    def _create_downloading_button(self):
        button = QPushButton(self)
        button.setFixedSize(148, 35)
        button.setEnabled(False)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.theme.get_color('bg_tertiary')};
                color: {self.theme.get_color('text_secondary')};
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid {self.theme.get_color('border')};
            }}
            """
        )

        btn_layout = QHBoxLayout(button)
        btn_layout.setContentsMargins(8, 0, 8, 0)
        btn_layout.setSpacing(6)

        spinner = AnimatedIconLabel("ICON_REFRESH", 18, button)
        spinner.start_animation()
        spinner.setStyleSheet("background: transparent; border: none;")
        btn_layout.addWidget(spinner)

        text_lbl = QLabel("Downloading...", button)
        text_lbl.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 13px; font-weight: bold;
            background: transparent; border: none;
            """
        )
        btn_layout.addWidget(text_lbl)
        btn_layout.addStretch()

        button._spinner = spinner
        return button

    def update_download_state(self) -> None:
        if self._mode != self.MODE_WORKSHOP:
            return
        if not self.current_pubfileid:
            return

        is_downloading = self.dm.is_downloading(self.current_pubfileid)
        has_btn = hasattr(self, "_download_btn") and self._download_btn is not None

        if not has_btn:
            return

        btn_is_disabled = not self._download_btn.isEnabled()

        if is_downloading and not btn_is_disabled:
            self._setup_workshop_buttons()
        elif not is_downloading and btn_is_disabled:
            if self.we.is_installed(self.current_pubfileid):
                folder_path = self.we.projects_path / self.current_pubfileid
                self.set_installed_folder(str(folder_path))
            else:
                self._setup_workshop_buttons()

    def _create_icon_label(self, icon_name: str, size: int = 16) -> QLabel:
        label = QLabel(self)
        label.setPixmap(get_pixmap(icon_name, size))
        label.setFixedSize(size, size)
        label.setStyleSheet("background: transparent; border: none;")
        return label

    def _add_detail_row(self, icon_name: str, text: str):
        row_widget = QWidget(self)
        row_widget.setStyleSheet("background: transparent; border: none;")

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        icon_label = self._create_icon_label(icon_name, 16)
        row_layout.addWidget(icon_label)

        text_label = QLabel(text, row_widget)
        text_label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 14px;
            background: transparent;
            border: none;
            """
        )
        text_label.setWordWrap(True)
        row_layout.addWidget(text_label, 1)

        self.details_layout.addWidget(row_widget)
        return text_label

    def _add_author_row(self, author: str, author_url: str = "") -> None:
        row_widget = QWidget(self)
        row_widget.setStyleSheet("background: transparent; border: none;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        icon_label = self._create_icon_label("ICON_USER", 16)
        row_layout.addWidget(icon_label)

        full_text = self.tr.t("labels.author", author="__PLACEHOLDER__")
        prefix = full_text.split("__PLACEHOLDER__")[0]

        if prefix.strip():
            prefix_label = QLabel(prefix.rstrip(), row_widget)
            prefix_label.setStyleSheet(f"""
                color: {self.theme.get_color('text_secondary')};
                font-size: 14px;
                background: transparent;
                border: none;
            """)
            row_layout.addWidget(prefix_label)

        name_label = QLabel(author, row_widget)
        name_label.setStyleSheet(f"""
            color: {self.theme.get_color('primary')};
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        if author_url:
            name_label.setCursor(Qt.CursorShape.PointingHandCursor)
            name_label.mousePressEvent = lambda e, a=author, u=author_url: (
                self._navigate_to_author(a, u) if e.button() == Qt.MouseButton.LeftButton else None
            )

        row_layout.addWidget(name_label)
        row_layout.addStretch()

        self.details_layout.addWidget(row_widget)

    def _add_detail_label(self, text: str, icon_name: str = ""):
        if icon_name:
            return self._add_detail_row(icon_name, text)

        label = QLabel(text, self)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 14px;
            background: transparent;
            border: none;
            """
        )
        label.setWordWrap(True)
        self.details_layout.addWidget(label)
        return label

    def _add_separator(self) -> None:
        separator = QWidget(self)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self.theme.get_color('border')}; border: none;")
        self.details_layout.addWidget(separator)

    def _add_section_title(self, text: str, icon_name: str = None):
        header_widget = QWidget(self)
        header_widget.setStyleSheet("background: transparent; border: none;")

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        if icon_name:
            icon_label = QLabel(header_widget)
            icon_label.setPixmap(get_pixmap(icon_name, 18))
            icon_label.setStyleSheet("background: transparent; border: none;")
            header_layout.addWidget(icon_label)

        label = QLabel(text, header_widget)
        label.setStyleSheet(
            f"""
            font-weight: bold;
            color: {self.theme.get_color('text_primary')};
            font-size: 14px;
            background: transparent;
            border: none;
            """
        )
        header_layout.addWidget(label)
        header_layout.addStretch()

        self.details_layout.addWidget(header_widget)
        return label

    def _add_description_label(self, text: str):
        label = QLabel(text, self)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_primary')};
            font-size: 13px;
            line-height: 1.4;
            background: transparent;
            border: none;
            """
        )
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setFixedWidth(self.CONTENT_WIDTH - 16)
        self.details_layout.addWidget(label)
        return label

    def _description_expand_button_style(self) -> str:
        hover_bg = "rgba(255, 255, 255, 0.08)"
        pressed_bg = "rgba(255, 255, 255, 0.12)"
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
            }}
        """

    def _create_expand_description_button(self) -> QPushButton:
        button = QPushButton(self)
        button.setFixedWidth(self.CONTENT_WIDTH - 16)
        button.setFixedHeight(24)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(self._description_expand_button_style())

        button.setIcon(get_icon("ICON_ARROW_DOWN"))
        button.setIconSize(QSize(18, 18))
        button.clicked.connect(self._expand_description)

        return button

    def _set_description_text(self, text: str) -> None:
        if self._description_label:
            self._description_label.setText(text)

    def _max_description_height(self) -> int:
        if not self._description_label:
            return 0
        metrics = self._description_label.fontMetrics()
        line_height = metrics.lineSpacing()
        return line_height * self.DESCRIPTION_PREVIEW_LINES

    def _description_exceeds_preview(self, text: str) -> bool:
        if not text or not self._description_label:
            return False

        probe = QLabel(self)
        probe.setWordWrap(True)
        probe.setAlignment(Qt.AlignmentFlag.AlignTop)
        probe.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        probe.setFont(self._description_label.font())
        probe.setStyleSheet(self._description_label.styleSheet())
        probe.setText(text)

        width = self.CONTENT_WIDTH - 16
        probe.setFixedWidth(width)
        probe.adjustSize()

        return probe.sizeHint().height() > self._max_description_height()

    def _truncate_description_to_height(self, text: str) -> str:
        if not text or not self._description_label:
            return text

        clean = text.strip()
        if not clean:
            return clean

        if not self._description_exceeds_preview(clean):
            return clean

        left = 0
        right = len(clean)
        best = ""

        probe = QLabel(self)
        probe.setWordWrap(True)
        probe.setAlignment(Qt.AlignmentFlag.AlignTop)
        probe.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        probe.setFont(self._description_label.font())
        probe.setStyleSheet(self._description_label.styleSheet())
        probe.setFixedWidth(self.CONTENT_WIDTH - 16)

        max_height = self._max_description_height()

        while left <= right:
            mid = (left + right) // 2
            candidate = clean[:mid].rstrip()

            last_space = candidate.rfind(" ")
            if last_space > 0 and mid < len(clean):
                candidate = candidate[:last_space].rstrip()

            candidate_with_ellipsis = candidate + "…"
            probe.setText(candidate_with_ellipsis)
            probe.adjustSize()

            if probe.sizeHint().height() <= max_height:
                best = candidate_with_ellipsis
                left = mid + 1
            else:
                right = mid - 1

        return best if best else clean[:50].rstrip() + "…"

    def _expand_description(self) -> None:
        self._description_expanded = True
        self._set_description_text(self._displayed_description_full)

        if self._expand_description_button is not None:
            self._expand_description_button.hide()

    def _update_description_display(self) -> None:
        if self._description_label is None:
            return

        full_text = self._displayed_description_full or self.tr.t("labels.no_description")
        should_collapse = self._description_exceeds_preview(full_text)

        if self._description_expanded or not should_collapse:
            self._set_description_text(full_text)
            if self._expand_description_button is not None:
                self._expand_description_button.hide()
        else:
            self._set_description_text(self._truncate_description_to_height(full_text))
            if self._expand_description_button is not None:
                self._expand_description_button.show()

    def _add_description_section(self, description: str) -> None:
        self._original_description = description or ""
        self._translated_description = ""
        self._is_translated = False
        self._description_expanded = False
        self._displayed_description_full = description if description else self.tr.t("labels.no_description")

        header_widget = QWidget(self)
        header_widget.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        if description and description.strip():
            self._translate_button = QPushButton(header_widget)
            install_tooltip(self._translate_button, self.tr.t("tooltips.translate_description"), "bottom", self.theme)
            self._translate_button.setFixedSize(18, 18)
            self._translate_button.setIcon(get_icon("ICON_TRANSLATE"))
            self._translate_button.setIconSize(QSize(24, 24))
            self._translate_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    border-radius: 6px;
                    border: none;
                }}
                """
            )
            self._translate_button.clicked.connect(self._on_translate_clicked)
            header_layout.addWidget(self._translate_button)

        title_label = QLabel(self.tr.t("labels.description"), header_widget)
        title_label.setStyleSheet(
            f"""
            font-weight: bold;
            color: {self.theme.get_color('text_primary')};
            font-size: 14px;
            background: transparent;
            border: none;
            """
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.details_layout.addWidget(header_widget)

        self._description_label = self._add_description_label(self._displayed_description_full)

        self._expand_description_button = self._create_expand_description_button()
        self.details_layout.addWidget(self._expand_description_button)

        self._update_description_display()

    def _on_translate_clicked(self) -> None:
        if not self._original_description:
            return

        if self._is_translated:
            self._displayed_description_full = self._original_description
            self._is_translated = False
            self._description_expanded = False
            self._update_description_display()
            if self._translate_button and hasattr(self._translate_button, '_custom_tooltip_filter'):
                self._translate_button._custom_tooltip_filter.set_text(self.tr.t("tooltips.translate_description"))
            return

        if self._translated_description:
            self._displayed_description_full = self._translated_description
            self._is_translated = True
            self._description_expanded = False
            self._update_description_display()
            if self._translate_button and hasattr(self._translate_button, '_custom_tooltip_filter'):
                self._translate_button._custom_tooltip_filter.set_text(self.tr.t("tooltips.show_original"))
            return

        target_language = self.tr.get_language()

        if self._translation_worker and self._translation_worker.isRunning():
            self._translation_worker.terminate()

        self._translation_worker = TranslationWorker(self._original_description, target_language)
        self._translation_worker.finished.connect(self._on_translation_finished)
        self._translation_worker.error.connect(self._on_translation_error)

        if self._translate_button:
            self._translate_button.setEnabled(False)

        self._description_label.setText(self.tr.t("labels.translating"))
        if self._expand_description_button is not None:
            self._expand_description_button.hide()

        self._translation_worker.start()

    def _on_translation_finished(self, original: str, translated: str) -> None:
        if original != self._original_description:
            return

        self._translated_description = translated
        self._is_translated = True
        self._description_expanded = False
        self._displayed_description_full = translated

        self._update_description_display()

        if self._translate_button:
            self._translate_button.setEnabled(True)
            self._translate_button._custom_tooltip_filter.set_text(self.tr.t("tooltips.show_original"))
        self._translation_worker = None

    def _on_translation_error(self, error_msg: str) -> None:
        self._displayed_description_full = self._original_description
        self._description_expanded = False
        self._update_description_display()

        if self._translate_button:
            self._translate_button.setEnabled(True)
            self._translate_button._custom_tooltip_filter.set_text(self.tr.t("tooltips.translate_description"))

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
                safe_value = value.replace(" ", "_")
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

    def _star_file_to_text(self, rating_star_file: str) -> str:
        mapping = {
            "5-star_large": "★★★★★",
            "4-star_large": "★★★★☆",
            "3-star_large": "★★★☆☆",
            "2-star_large": "★★☆☆☆",
            "1-star_large": "★☆☆☆☆",
            "not-yet_large": "",
        }
        return mapping.get(rating_star_file, "")

    def _add_rating_row(self, rating_star_file: str, num_ratings: str) -> None:
        stars_text = self._star_file_to_text(rating_star_file)
        if not stars_text:
            return

        row_widget = QWidget(self)
        row_widget.setStyleSheet("background: transparent; border: none;")

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        icon_label = self._create_icon_label("ICON_STAR", 16)
        row_layout.addWidget(icon_label)

        rating_text = QLabel(self.tr.t("labels.rating"), row_widget)
        rating_text.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 14px;
            background: transparent;
            border: none;
            """
        )
        row_layout.addWidget(rating_text)
        row_layout.addSpacing(4)

        count_part = f" ({num_ratings})" if num_ratings else ""
        stars_label = QLabel(f"{stars_text}{count_part}", row_widget)
        stars_label.setStyleSheet(
            """
            color: #f5c518;
            font-size: 14px;
            background: transparent;
            border: none;
            """
        )
        row_layout.addWidget(stars_label)
        row_layout.addStretch()

        self.details_layout.addWidget(row_widget)

    def _add_tags_section(self, tags: dict) -> None:
        if not tags:
            return

        self._add_separator()
        self._add_section_title(self.tr.t("labels.tags"), "ICON_TAGS")

        for key, value in tags.items():
            translated_key = self._translate_tag_key(key)
            clean_key = translated_key.rstrip(":")

            if isinstance(value, bool):
                values = []
            elif isinstance(value, str) and value.strip():
                if "," in value:
                    values = [self._translate_single_tag_value(key, v.strip()) for v in value.split(",")]
                else:
                    values = [self._translate_single_tag_value(key, value)]
            else:
                values = []

            tag_group = TagGroupWidget(clean_key, values, self.theme, max_width=280, parent=self)
            self.details_layout.addWidget(tag_group)

    def _setup_installed_details(self) -> None:
        self._clear_details()

        metadata = self.metadata_service.get(self.current_pubfileid) if self.metadata_service else None

        if metadata:
            if metadata.rating_star_file:
                self._add_rating_row(metadata.rating_star_file, metadata.num_ratings)

            size_bytes = get_directory_size(self.folder_path)
            self._add_detail_row("ICON_PACKAGE", self.tr.t("labels.size", size=human_readable_size(size_bytes)))

            if metadata.posted_date_str:
                self._add_detail_row("ICON_CALENDAR", self.tr.t("labels.posted", date=metadata.posted_date_str))

            if metadata.updated_date_str:
                self._add_detail_row("ICON_REFRESH", self.tr.t("labels.updated", date=metadata.updated_date_str))

            mtime = get_folder_mtime(self.folder_path)
            self._add_detail_row("ICON_CALENDAR", self.tr.t("labels.installed", date=format_timestamp(mtime)))

            if metadata.author:
                author_url = getattr(metadata, 'author_url', '') or ''
                if not author_url:
                    parser = self._get_main_parser()
                    if parser:
                        cached_item = parser.get_cached_item(self.current_pubfileid)
                        if cached_item and cached_item.author_url:
                            author_url = cached_item.author_url
                if author_url:
                    self._add_author_row(metadata.author, author_url)
                else:
                    self._add_detail_row("ICON_USER", self.tr.t("labels.author", author=metadata.author))

            if metadata.tags:
                self._add_tags_section(metadata.tags)

            description = metadata.description or self._project_data.get("description", "")
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

        collections = []
        if metadata:
            collections = getattr(metadata, "collections", []) or []
        if not collections:
            parser = self._get_main_parser()
            if parser:
                cached_item = parser.get_cached_item(self.current_pubfileid)
                if cached_item:
                    collections = getattr(cached_item, "collections", []) or []
        if collections:
            self._add_separator()
            self._add_section_title(
                self.tr.t("labels.collections"),
                "ICON_COLLECTION"
            )
            for col in collections:
                col_id = col.get("id", "") if isinstance(col, dict) else ""
                col_title = col.get("title", "") if isinstance(col, dict) else ""
                link_widget = self._create_collection_link(col_id, col_title)
                if link_widget:
                    self.details_layout.addWidget(link_widget)

        self.details_layout.addStretch()

    def _setup_workshop_details(self, item) -> None:
        self._clear_details()

        if getattr(item, "rating_star_file", ""):
            self._add_rating_row(item.rating_star_file, getattr(item, "num_ratings", ""))

        if item.file_size:
            self._add_detail_row("ICON_PACKAGE", self.tr.t("labels.size", size=item.file_size))

        if item.posted_date:
            self._add_detail_row("ICON_CALENDAR", self.tr.t("labels.posted", date=item.posted_date))

        if item.updated_date:
            self._add_detail_row("ICON_REFRESH", self.tr.t("labels.updated", date=item.updated_date))

        if item.author:
            if item.author_url:
                self._add_author_row(item.author, item.author_url)
            else:
                self._add_detail_row("ICON_USER", self.tr.t("labels.author", author=item.author))

        if item.tags:
            self._add_tags_section(item.tags)

        if item.description:
            self._add_separator()
            self._add_description_section(item.description)

        collections = getattr(item, 'collections', [])
        if collections:
            self._add_separator()
            self._add_section_title(
                self.tr.t("labels.collections"), "ICON_COLLECTION"
            )
            for col in collections:
                col_id = col.get('id', '') if isinstance(col, dict) else ''
                col_title = col.get('title', '') if isinstance(col, dict) else ''
                link_widget = self._create_collection_link(col_id, col_title)
                if link_widget:
                    self.details_layout.addWidget(link_widget)

        self.details_layout.addStretch()

    def set_collection_info(self, contents) -> None:
        self._reset_state()
        self._mode = self.MODE_WORKSHOP
        self.current_pubfileid = contents.collection_id
        self._current_preview_url = contents.preview_url or ""
        self.setVisible(True)

        self.title_label.setText(contents.title or f"Collection {contents.collection_id}")
        self.id_label.setText(self.current_pubfileid)

        self._clear_buttons()
        browser_btn = self._create_text_button(
            "ICON_WORLD",
            self.tr.t("buttons.open_workshop"),
            self.tr.t("tooltips.open_workshop"),
            self._on_open_browser,
        )
        browser_btn.setFixedSize(300, 35)
        self.buttons_layout.addWidget(browser_btn)
        self.buttons_layout.addStretch()

        self._clear_details()
        info = contents.info or {}

        rating_file = info.get('rating_star_file', '')
        num_ratings = info.get('num_ratings', '')
        if rating_file:
            self._add_rating_row(rating_file, num_ratings)

        item_count = info.get('item_count', len(contents.items))
        if item_count:
            self._add_detail_row("ICON_PACKAGE", f"Items: {item_count}")

        if contents.author:
            if contents.author_url:
                self._add_author_row(contents.author, contents.author_url)
            else:
                self._add_detail_row("ICON_USER", self.tr.t("labels.author", author=contents.author))

        visitors = info.get('unique_visitors', '')
        if visitors:
            self._add_detail_row("ICON_WORLD", f"Unique visitors: {visitors}")

        subscribers = info.get('subscribers', '')
        if subscribers:
            self._add_detail_row("ICON_USER", f"Subscribers: {subscribers}")

        favorited = info.get('favorited', '')
        if favorited:
            self._add_detail_row("ICON_HEART", f"Favorited: {favorited}")

        total_fav = info.get('total_favorited', '')
        if total_fav and total_fav != favorited:
            self._add_detail_row("ICON_HEART", f"Total favorited: {total_fav}")

        posted = info.get('posted_date', '')
        if posted:
            self._add_detail_row("ICON_CALENDAR", self.tr.t("labels.posted", date=posted))

        updated = info.get('updated_date', '')
        if updated:
            self._add_detail_row("ICON_REFRESH", self.tr.t("labels.updated", date=updated))

        tag_keys = ['Miscellaneous', 'Genre', 'Category', 'Age Rating',
                     'Type', 'Resolution', 'Content Descriptors']
        tags_to_show = {}
        for key in tag_keys:
            if key in info and info[key]:
                tags_to_show[key] = info[key]
        if tags_to_show:
            self._add_tags_section(tags_to_show)

        if contents.description:
            self._add_separator()
            self._add_description_section(contents.description)

        self.details_layout.addStretch()
        self._update_id_section_visibility()

        if contents.preview_url:
            self._load_remote_preview(contents.preview_url)
        else:
            self._show_image_placeholder()

    def _create_collection_link(self, collection_id: str, title: str):
        if not collection_id:
            return None

        row = QWidget(self)
        row.setStyleSheet("background: transparent; border: none;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(4, 0, 4, 0)
        row_layout.setSpacing(6)

        link_label = QLabel(title or f"Collection {collection_id}", row)
        link_label.setStyleSheet(f"""
            color: {self.theme.get_color('primary')};
            font-size: 12px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        link_label.setCursor(Qt.CursorShape.PointingHandCursor)
        link_label.mousePressEvent = lambda e, cid=collection_id: (
            self._navigate_to_collection(cid) if e.button() == Qt.MouseButton.LeftButton else None
        )

        row_layout.addWidget(link_label, 1)
        row_layout.addStretch()
        return row

    def _on_collection_link_clicked(self, collection_id: str) -> None:
        self._navigate_to_collection(collection_id)

    def _find_grid_item(self, pubfileid: str):
        parent = self.parent()
        while parent and not hasattr(parent, "grid_items"):
            parent = parent.parent()

        if parent and hasattr(parent, "grid_items"):
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
            if hasattr(grid_item, "_is_gif") and grid_item._is_gif and hasattr(grid_item, "_gif_buffer") and grid_item._gif_buffer:
                self._apply_preview_gif(grid_item._gif_buffer)
                return True

            if hasattr(grid_item, "_pixmap") and grid_item._pixmap and not grid_item._pixmap.isNull():
                self._apply_preview_pixmap(grid_item._pixmap)
                return True
        except Exception:
            pass

        return False

    def _load_local_preview(self, folder_path: str) -> None:
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
                self.preview_label.setStyleSheet(
                    f"""
                    QLabel {{
                        background-color: {self.theme.get_color('bg_tertiary')};
                        border-radius: 8px;
                    }}
                    """
                )
                self.movie.start()
            else:
                pixmap = QPixmap(str(preview_file))
                if not pixmap.isNull():
                    self._apply_preview_pixmap(pixmap)
        except Exception:
            self._stop_loading_animation()
            self.preview_label.clear()
            self.preview_label.setText(self.tr.t("messages.error"))

    def _load_remote_preview(self, url: str) -> None:
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

    def _apply_preview_pixmap(self, pixmap: QPixmap) -> None:
        if pixmap is None or pixmap.isNull():
            self._show_image_placeholder()
            return

        try:
            self._stop_loading_animation()

            label_size = self.preview_label.size()
            scaled = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )

            x = (scaled.width() - label_size.width()) // 2
            y = (scaled.height() - label_size.height()) // 2
            cropped = scaled.copy(x, y, label_size.width(), label_size.height())
            rounded = self._create_rounded_pixmap(cropped, radius=8)

            self.preview_label.setPixmap(rounded)
            self.preview_label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {self.theme.get_color('bg_tertiary')};
                    border-radius: 8px;
                }}
                """
            )
        except Exception:
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

    def _apply_preview_gif(self, data: QByteArray) -> None:
        if data is None or data.isEmpty():
            self._show_image_placeholder()
            return

        try:
            self._stop_movie()
            self._stop_loading_animation()

            self._gif_buffer = QBuffer(self)
            self._gif_buffer.setData(data)
            self._gif_buffer.open(QIODevice.OpenModeFlag.ReadOnly)

            self.movie = QMovie(self._gif_buffer, QByteArray(), self)
            self.movie.setScaledSize(self.preview_label.size())
            self.preview_label.setMovie(self.movie)
            self.movie.frameChanged.connect(self._on_gif_frame_changed)
            self.preview_label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {self.theme.get_color('bg_tertiary')};
                    border-radius: 8px;
                }}
                """
            )
            self.movie.start()
        except Exception:
            self._show_image_placeholder()

    def _on_gif_frame_changed(self, frame_number: int) -> None:
        if self.movie is None:
            return

        current_pixmap = self.movie.currentPixmap()
        if not current_pixmap.isNull():
            label_size = self.preview_label.size()
            x = max(0, (current_pixmap.width() - label_size.width()) // 2)
            y = max(0, (current_pixmap.height() - label_size.height()) // 2)
            crop_w = min(current_pixmap.width(), label_size.width())
            crop_h = min(current_pixmap.height(), label_size.height())

            cropped = current_pixmap.copy(x, y, crop_w, crop_h)
            rounded = self._create_rounded_pixmap(cropped, radius=8)
            self.preview_label.setPixmap(rounded)

    def _on_open_folder(self) -> None:
        if self.folder_path and Path(self.folder_path).exists():
            os.startfile(self.folder_path)

    def _on_open_browser(self) -> None:
        webbrowser.open(f"https://steamcommunity.com/sharedfiles/filedetails/?id={self.current_pubfileid}")

    def _on_download(self) -> None:
        if not self.current_pubfileid:
            return

        parent = self.parent()
        while parent and not hasattr(parent, "start_download"):
            parent = parent.parent()

        if parent:
            parent.start_download(self.current_pubfileid)

    def _on_delete(self) -> None:
        if not self.folder_path:
            return

        if self.we.is_wallpaper_current(Path(self.folder_path)):
            MessageBox.warning(
                None,
                self.tr.t("dialog.warning"),
                self.tr.t("messages.cannot_delete_active"),
            )
            return

        reply = MessageBox.question(
            None,
            self.tr.t("dialog.confirm_deletion"),
            self.tr.t("messages.confirm_delete"),
        )
        if reply != MessageBox.StandardButton.Yes:
            return

        pubfileid = self.current_pubfileid
        main_window = self.window()

        if hasattr(main_window, "wallpapers_tab"):
            main_window.wallpapers_tab.release_resources_for_folder(self.folder_path)

        if hasattr(main_window, "workshop_tab"):
            workshop_tab = main_window.workshop_tab
            if (
                hasattr(workshop_tab, "details_panel")
                and hasattr(workshop_tab.details_panel, "current_pubfileid")
                and workshop_tab.details_panel.current_pubfileid == pubfileid
            ):
                workshop_tab.details_panel.release_resources()

            for item in getattr(workshop_tab, "grid_items", []):
                if hasattr(item, "pubfileid") and item.pubfileid == pubfileid:
                    if hasattr(item, "release_resources"):
                        item.release_resources()

        self.release_resources()
        folder_to_delete = self.folder_path

        def perform_deletion():
            try:
                folder = Path(folder_to_delete)
                if folder.exists():
                    shutil.rmtree(folder)

                if self.metadata_service:
                    self.metadata_service.remove(pubfileid)

                self._show_notification(self.tr.t("messages.wallpaper_deleted"))

                if hasattr(main_window, "workshop_tab"):
                    if hasattr(main_window.workshop_tab, "_on_page_loaded"):
                        main_window.workshop_tab._on_page_loaded(
                            getattr(main_window.workshop_tab, "_current_page_data", None)
                        )
                    if hasattr(main_window.workshop_tab, "_on_download_completed"):
                        main_window.workshop_tab._on_download_completed(pubfileid, True)

                QTimer.singleShot(100, self.refresh_after_state_change)

                if hasattr(main_window, "refresh_wallpapers"):
                    main_window.refresh_wallpapers()
            except Exception as error:
                MessageBox.critical(self, self.tr.t("dialog.error"), f"Failed to delete:\n{str(error)}")

        QTimer.singleShot(200, perform_deletion)

    def _on_extract(self) -> None:
        if not self.folder_path:
            self._show_notification(self.tr.t("messages.no_wallpaper_selected"))
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            self.tr.t("messages.select_output_directory"),
            str(Path.home()),
        )
        if not output_dir:
            return

        success = self.dm.start_extraction(self.current_pubfileid, Path(output_dir))
        if success:
            self._show_notification(self.tr.t("messages.extraction_started"))
        else:
            self._show_notification(self.tr.t("messages.no_pkg_file"))

    def _on_apply(self) -> None:
        if not self.folder_path:
            return

        self.we.apply_wallpaper(Path(self.folder_path) / "project.json")

        if self.config and self.config.get_minimize_on_apply():
            window = self.window()
            if window:
                window.showMinimized()

    def _on_install_and_open(self) -> None:
        self._on_apply()
        self.we.open_wallpaper_engine(show_window=True)

    def _on_id_clicked(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            QApplication.clipboard().setText(self.current_pubfileid)
            self._show_notification(self.tr.t("messages.id_copied"))

    def _load_project_json(self, folder_path: str) -> dict:
        json_path = Path(folder_path) / "project.json"
        if not json_path.exists():
            return {}

        try:
            with json_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}

    def _show_notification(self, message: str) -> None:
        NotificationLabel.show_notification(self.parent(), message)