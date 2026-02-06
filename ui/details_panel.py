import json
import os
import shutil
import tempfile
import webbrowser
import weakref
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSize, QTimer, QByteArray
from PyQt6.QtGui import QPixmap, QMovie, QMouseEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QMessageBox, QFileDialog, QApplication
)

from ui.custom_widgets import NotificationLabel
# from ui.preset_panel import PresetPanel
from resources.icons import get_icon
from utils.helpers import human_readable_size, format_timestamp, get_directory_size, get_folder_mtime
from core.image_cache import ImageCache


class DetailsPanel(QWidget):

    MODE_NONE = 0
    MODE_INSTALLED = 1
    MODE_WORKSHOP = 2

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

        self._setup_ui()
        self.setVisible(False)

    def _setup_ui(self):
        self.setMinimumWidth(310)
        self.setMaximumWidth(310)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 10)
        main_layout.setSpacing(14)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(310, 275)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2c2f48;
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.preview_label)

        self._create_action_buttons(main_layout)

        # self.preset_panel = PresetPanel(self.we, self.tr, self.config, self)
        # self.preset_panel.property_changed.connect(self._on_preset_property_changed)
        # self.preset_panel.panel_toggled.connect(self._on_preset_panel_toggled)
        # main_layout.addWidget(self.preset_panel)

        self._create_title_section(main_layout)
        self._create_id_section(main_layout)
        self._create_details_section(main_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                border-left: 1px solid #3c3f58;
            }
        """)

    def _create_action_buttons(self, layout):
        self.buttons_widget = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(10)
        self.buttons_widget.setStyleSheet("QWidget { background: transparent; border: none; }")
        layout.addWidget(self.buttons_widget)

    def _create_title_section(self, layout):
        self.title_scroll = QScrollArea()
        self.title_scroll.setWidgetResizable(True)
        self.title_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.title_scroll.setMaximumHeight(80)
        self.title_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        title_content = QWidget()
        title_layout = QHBoxLayout(title_content)
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 18px; color: white;")
        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        title_layout.addWidget(self.title_label)

        self.title_scroll.setWidget(title_content)
        layout.addWidget(self.title_scroll)

    def _create_id_section(self, layout):
        self.id_label = QLabel()
        self.id_label.setStyleSheet("""
            QLabel {
                color: #a3a3a3;
                font-size: 14px;
                background-color: #1e1e2f;
                padding: 4px 8px;
                border-radius: 8px;
            }
            QLabel:hover {
                background-color: rgba(78, 140, 255, 0.25);
            }
        """)
        self.id_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.id_label.mousePressEvent = self._on_id_clicked
        layout.addWidget(self.id_label)

    def _create_details_section(self, layout):
        self.details_container = QWidget()
        self.details_container.setObjectName("detailsContainer")
        self.details_container.setStyleSheet("""
            #detailsContainer {
                background-color: #1e1e2f;
                border-radius: 8px;
            }
            #detailsContainer * {
                border: none;
                border-left: none;
                border-radius: 0px;
            }
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

    # ==================== PRESET PANEL HANDLERS ====================

    # def _on_preset_panel_toggled(self, is_visible: bool):
    #     self.preview_label.setVisible(not is_visible)
    #     self.buttons_widget.setVisible(not is_visible)
    #     self.title_scroll.setVisible(not is_visible)
    #     self.id_label.setVisible(not is_visible)
    #     self.details_container.setVisible(not is_visible)

    # def _on_preset_property_changed(self, pubfileid: str, key: str, value):
    #     main_window = self.window()
    #     if hasattr(main_window, 'wallpapers_tab'):
    #         panel = getattr(main_window.wallpapers_tab, 'details_panel', None)
    #         if panel and panel is not self and hasattr(panel, 'preset_panel'):
    #             panel.preset_panel.sync_property(pubfileid, key, value)
    #     if hasattr(main_window, 'workshop_tab'):
    #         panel = getattr(main_window.workshop_tab, 'details_panel', None)
    #         if panel and panel is not self and hasattr(panel, 'preset_panel'):
    #             panel.preset_panel.sync_property(pubfileid, key, value)

    def set_installed_folder(self, folder_path: str):
        self._reset_state()

        self._mode = self.MODE_INSTALLED
        self.folder_path = folder_path
        self.current_pubfileid = Path(folder_path).name

        self.setVisible(True)

        self._project_data = self._load_project_json(folder_path)

        self.title_label.setText(self._project_data.get("title", Path(folder_path).name))
        self.id_label.setText(self.tr.t("labels.id", id=self.current_pubfileid))

        self._setup_installed_buttons()
        self._setup_installed_details()

        if not self._try_copy_from_grid_item(self.current_pubfileid):
            self._load_local_preview(folder_path)

    def set_workshop_item(self, item):
        self._reset_state()

        self._mode = self.MODE_WORKSHOP
        self._current_item = item
        self.current_pubfileid = item.pubfileid
        self._current_preview_url = item.preview_url or ""
        self.folder_path = None

        self.setVisible(True)

        self.title_label.setText(item.title or item.pubfileid)
        self.id_label.setText(self.tr.t("labels.id", id=item.pubfileid))

        self._setup_workshop_buttons()
        self._setup_workshop_details(item)

        if not self._try_copy_from_grid_item(item.pubfileid):
            self._load_remote_preview(item.preview_url)

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
                parent = self.parent()
                while parent and not hasattr(parent, 'parser'):
                    parent = parent.parent()
                if parent and hasattr(parent, 'parser'):
                    parent.parser.load_item_details(self.current_pubfileid)

    def release_resources(self):
        self._reset_preview()
        # if self.preset_panel.isVisible():
        #     self.preset_panel.hide_panel()

    @property
    def large_preview(self):
        return self.preview_label

    def _reset_state(self):
        self._reset_preview()
        # if self.preset_panel.isVisible():
        #     self.preset_panel.hide_panel()
        self._clear_details()
        self._clear_buttons()

        self._current_item = None
        self._current_preview_url = ""
        self._project_data = {}

    def _stop_movie(self):
        if self.movie is not None:
            try:
                self.movie.stop()
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

    def _reset_preview(self):
        self._current_preview_url = ""
        self._stop_movie()
        self.preview_label.clear()
        self.preview_label.setText("⏳")
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2c2f48;
                border-radius: 8px;
                color: #6B6E7C;
                font-size: 32px;
            }
        """)

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

    def _create_icon_button(self, icon_name, tooltip, callback, color='#4e8cff', hover_color='#6ea4ff'):
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
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(78, 140, 255, 0.1);
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(78, 140, 255, 0.25);
            }
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
            color='#ff5c5c', hover_color='#ff7c7c'
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

        # self.buttons_layout.addWidget(self._create_icon_button(
        #     "ICON_SETTINGS",
        #     self.tr.t("tooltips.preset_settings") if hasattr(self.tr, 't') else "Preset Settings",
        #     self._on_toggle_preset_panel,
        #     color='#9b59b6', hover_color='#a569bd'
        # ))

    def _setup_workshop_buttons(self):
        self._clear_buttons()

        self.buttons_layout.addWidget(self._create_text_button(
            "ICON_UPLOAD", "Install", self.tr.t("buttons.install"), self._on_download
        ))
        self.buttons_layout.addWidget(self._create_text_button(
            "ICON_WORLD", "Browser", self.tr.t("tooltips.open_workshop"), self._on_open_browser
        ))
        self.buttons_layout.addStretch()

    def _add_detail_label(self, text: str, icon: str = ""):
        label = QLabel(f"{icon} {text}" if icon else text)
        label.setStyleSheet("color: #a3a3a3; font-size: 14px; background: transparent; border: none;")
        label.setWordWrap(True)
        self.details_layout.addWidget(label)
        return label

    def _add_separator(self):
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #3c3f58; border: none;")
        self.details_layout.addWidget(separator)

    def _add_section_title(self, text: str):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; color: white; font-size: 14px; background: transparent; border: none;")
        self.details_layout.addWidget(label)
        return label

    def _add_description_label(self, text: str):
        label = QLabel(text)
        label.setStyleSheet("color: #dcdcdc; font-size: 13px; line-height: 1.4; background: transparent; border: none;")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_layout.addWidget(label)
        return label

    def _setup_installed_details(self):
        self._clear_details()

        size_bytes = get_directory_size(self.folder_path)
        self._add_detail_label(self.tr.t("labels.size", size=human_readable_size(size_bytes)), "📦")

        mtime = get_folder_mtime(self.folder_path)
        self._add_detail_label(self.tr.t("labels.installed", date=format_timestamp(mtime)), "📅")

        self._add_separator()
        self._add_section_title(self.tr.t("labels.description"))

        description = self._project_data.get("description", "")
        self._add_description_label(description if description else self.tr.t("labels.no_description"))

        self.details_layout.addStretch()

    def _setup_workshop_details(self, item):
        self._clear_details()

        if item.file_size:
            self._add_detail_label(self.tr.t("labels.size", size=item.file_size), "📦")
        if item.posted_date:
            self._add_detail_label(f"Posted: {item.posted_date}", "📅")
        if item.updated_date:
            self._add_detail_label(f"Updated: {item.updated_date}", "🔄")
        if item.author:
            self._add_detail_label(f"Author: {item.author}", "👤")

        if item.tags:
            self._add_separator()
            self._add_section_title("Tags:")
            for key, value in item.tags.items():
                tag_text = f"• {key}" if isinstance(value, bool) else f"• {key}: {value}"
                tag_label = QLabel(tag_text)
                tag_label.setStyleSheet("color: #dcdcdc; font-size: 13px; background: transparent; border: none;")
                tag_label.setWordWrap(True)
                self.details_layout.addWidget(tag_label)

        if item.description:
            self._add_separator()
            self._add_section_title(self.tr.t("labels.description"))
            desc_text = item.description[:500] + ("..." if len(item.description) > 500 else "")
            self._add_description_label(desc_text)

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
            self.preview_label.clear()
            self.preview_label.setText(self.tr.t("labels.no_preview"))
            return

        try:
            if preview_file.suffix.lower() == ".gif":
                self._stop_movie()
                self.movie = QMovie(str(preview_file))
                self.movie.setScaledSize(self.preview_label.size())
                self.preview_label.setMovie(self.movie)
                self.preview_label.setStyleSheet("""
                    QLabel {
                        background-color: #2c2f48;
                        border-radius: 8px;
                    }
                """)
                self.movie.start()
            else:
                pixmap = QPixmap(str(preview_file))
                if not pixmap.isNull():
                    self._apply_preview_pixmap(pixmap)
        except Exception as e:
            print(f"[DetailsPanel] Load local preview error: {e}")
            self.preview_label.clear()
            self.preview_label.setText("Error")

    def _load_remote_preview(self, url: str):
        if not url:
            self.preview_label.setText("🖼️")
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
                self_ref.preview_label.setText("🖼️")
                return
            if is_gif:
                self_ref._apply_preview_gif(data)
            else:
                self_ref._apply_preview_pixmap(data)

        cache.load_image(url, callback=on_loaded)

    def _apply_preview_pixmap(self, pixmap: QPixmap):
        if pixmap is None or pixmap.isNull():
            self.preview_label.setText("🖼️")
            return
        try:
            scaled = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
            self.preview_label.setStyleSheet("""
                QLabel {
                    background-color: #2c2f48;
                    border-radius: 8px;
                }
            """)
        except Exception as e:
            print(f"[DetailsPanel] Apply pixmap error: {e}")
            self.preview_label.setText("🖼️")

    def _apply_preview_gif(self, data: QByteArray):
        if data is None or data.isEmpty():
            self.preview_label.setText("🖼️")
            return
        try:
            self._stop_movie()

            fd, self._temp_gif_file = tempfile.mkstemp(suffix='.gif')
            os.write(fd, bytes(data))
            os.close(fd)

            self.movie = QMovie(self._temp_gif_file)
            self.movie.setScaledSize(self.preview_label.size())
            self.preview_label.setMovie(self.movie)
            self.preview_label.setStyleSheet("""
                QLabel {
                    background-color: #2c2f48;
                    border-radius: 8px;
                }
            """)
            self.movie.start()
        except Exception as e:
            print(f"[DetailsPanel] Apply GIF error: {e}")
            self.preview_label.setText("🖼️")

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
            QMessageBox.warning(
                self,
                self.tr.t("dialog.warning"),
                self.tr.t("messages.cannot_delete_active")
            )
            return

        reply = QMessageBox.question(
            self,
            self.tr.t("dialog.confirm_deletion"),
            self.tr.t("messages.confirm_delete"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
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
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{str(e)}")

        QTimer.singleShot(200, perform_deletion)

    def _on_extract(self):
        if not self.folder_path:
            self._show_notification(self.tr.t("messages.no_wallpaper_selected"))
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory", str(Path.home()))
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

    def _on_install_and_open(self):
        self._on_apply()
        self.we.open_wallpaper_engine(show_window=True)

    # def _on_toggle_preset_panel(self):
    #     self.preset_panel.toggle_panel(self.folder_path, self._project_data)

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
