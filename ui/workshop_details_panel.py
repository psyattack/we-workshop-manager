import os
import json
import shutil
import webbrowser
from pathlib import Path
from typing import Optional
import tempfile

from PyQt6.QtCore import Qt, QSize, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QMovie
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from core.workshop_parser import WorkshopItem
from ui.custom_widgets import NotificationLabel
from resources.icons import get_icon
from utils.helpers import human_readable_size, format_timestamp, get_directory_size, get_folder_mtime
import weakref


class WorkshopDetailsPanel(QWidget):
    _network_manager = None
    
    def __init__(self, wallpaper_engine, download_manager, translator, theme_manager, parent=None):
        super().__init__(parent)
        
        self.we = wallpaper_engine
        self.dm = download_manager
        self.tr = translator
        self.theme = theme_manager
        
        self.current_pubfileid: str = ""
        self.current_folder: str = ""
        self.is_installed_mode = False
        self.movie: Optional[QMovie] = None
        self._current_reply: Optional[QNetworkReply] = None
        self._temp_gif_file: Optional[str] = None
        self._current_item: Optional[WorkshopItem] = None
        
        self._setup_ui()
        self.setVisible(False)
    
    @classmethod
    def get_network_manager(cls) -> QNetworkAccessManager:
        if cls._network_manager is None:
            cls._network_manager = QNetworkAccessManager()
        return cls._network_manager
    
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
        self.id_label.mousePressEvent = self._copy_id

        layout.addWidget(self.id_label)
    
    def _create_details_section(self, layout):
        details_container = QWidget()
        details_container.setObjectName("detailsContainer")
        details_container.setStyleSheet("""
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
        
        container_layout = QVBoxLayout(details_container)
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
        
        layout.addWidget(details_container)
    
    def _reset_preview(self):
        if self._current_reply is not None:
            try:
                self._current_reply.abort()
                self._current_reply.deleteLater()
            except:
                pass
            self._current_reply = None
        
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
    
    def set_workshop_item(self, item: WorkshopItem):
        self._reset_preview()
        
        self.is_installed_mode = False
        self.current_pubfileid = item.pubfileid
        self.current_folder = ""
        self._current_item = item
        
        self.setVisible(True)
        
        self.title_label.setText(item.title or item.pubfileid)
        self.id_label.setText(self.tr.t("labels.id", id=item.pubfileid))
        
        self._load_remote_preview(item.preview_url)
        self._setup_remote_buttons()
        self._setup_remote_details(item)
    
    def set_installed_folder(self, folder_path: str):
        self._reset_preview()
        
        self.is_installed_mode = True
        self.current_folder = folder_path
        self.current_pubfileid = Path(folder_path).name
        self._current_item = None
        
        self.setVisible(True)
        
        project_data = self._load_project_json(folder_path)
        
        title = project_data.get("title", Path(folder_path).name)
        self.title_label.setText(title)
        self.id_label.setText(self.tr.t("labels.id", id=self.current_pubfileid))
        
        self._load_local_preview(folder_path)
        self._setup_installed_buttons()
        self._setup_installed_details(folder_path, project_data)
    
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
                if parent:
                    parent.parser.load_item_details(self.current_pubfileid)
    
    def _setup_remote_buttons(self):
        self._clear_buttons()
        
        download_btn = QPushButton()
        download_btn.setToolTip(self.tr.t("buttons.install"))
        download_btn.setIcon(get_icon("ICON_UPLOAD"))
        download_btn.setIconSize(QSize(24, 24))
        download_btn.setFixedSize(150, 35)
        download_btn.setText("Install")
        download_btn.setStyleSheet("""
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
        download_btn.clicked.connect(self._on_download)
        self.buttons_layout.addWidget(download_btn)

        browser_btn = QPushButton()
        browser_btn.setToolTip(self.tr.t("tooltips.open_workshop"))
        browser_btn.setIcon(get_icon("ICON_WORLD"))
        browser_btn.setIconSize(QSize(22, 22))
        browser_btn.setFixedSize(150, 35)
        browser_btn.setText("Browser")
        browser_btn.setStyleSheet("""
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
        browser_btn.clicked.connect(self._on_open_browser)
        self.buttons_layout.addWidget(browser_btn)
        
        self.buttons_layout.addStretch()
    
    def _setup_installed_buttons(self):
        self._clear_buttons()
        
        folder_btn = self._create_icon_button(
            "ICON_FOLDER", 
            self.tr.t("tooltips.open_folder"), 
            self._on_open_folder
        )
        browser_btn = self._create_icon_button(
            "ICON_WORLD", 
            self.tr.t("tooltips.open_workshop"), 
            self._on_open_browser
        )
        delete_btn = self._create_icon_button(
            "ICON_DELETE", 
            self.tr.t("tooltips.delete_wallpaper"), 
            self._on_delete,
            color='#ff5c5c',
            hover_color='#ff7c7c'
        )
        extract_btn = self._create_icon_button(
            "ICON_DOWNLOAD", 
            self.tr.t("tooltips.extract_wallpaper"), 
            self._on_extract
        )
        apply_btn = self._create_icon_button(
            "ICON_UPLOAD", 
            self.tr.t("tooltips.install_wallpaper"), 
            self._on_apply
        )
        install_open_btn = self._create_icon_button(
            "ICON_LINK", 
            self.tr.t("tooltips.install_open_we"), 
            self._on_install_and_open
        )
        
        self.buttons_layout.addWidget(folder_btn)
        self.buttons_layout.addWidget(browser_btn)
        self.buttons_layout.addWidget(delete_btn)
        self.buttons_layout.addWidget(extract_btn)
        self.buttons_layout.addWidget(apply_btn)
        self.buttons_layout.addWidget(install_open_btn)
    
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
    
    def _clear_buttons(self):
        while self.buttons_layout.count():
            child = self.buttons_layout.takeAt(0)
            if child is not None and child.widget() is not None:
                child.widget().deleteLater()
    
    def _setup_remote_details(self, item: WorkshopItem):
        self._clear_details()
        
        if item.file_size:
            size_label = QLabel("📦 " + self.tr.t("labels.size", size=item.file_size))
            size_label.setStyleSheet("color: #a3a3a3; font-size: 14px; background: transparent; border: none;")
            self.details_layout.addWidget(size_label)
        
        if item.posted_date:
            date_label = QLabel("📅 " + f"Posted: {item.posted_date}")
            date_label.setStyleSheet("color: #a3a3a3; font-size: 14px; background: transparent; border: none;")
            self.details_layout.addWidget(date_label)
        
        if item.updated_date:
            updated_label = QLabel("🔄 " + f"Updated: {item.updated_date}")
            updated_label.setStyleSheet("color: #a3a3a3; font-size: 14px; background: transparent; border: none;")
            self.details_layout.addWidget(updated_label)
        
        if item.author:
            author_label = QLabel("👤 " + f"Author: {item.author}")
            author_label.setStyleSheet("color: #a3a3a3; font-size: 14px; background: transparent; border: none;")
            self.details_layout.addWidget(author_label)
        
        if item.tags:
            self._add_separator()
            
            tags_title = QLabel("Tags:")
            tags_title.setStyleSheet("font-weight: bold; color: white; font-size: 14px; background: transparent; border: none;")
            self.details_layout.addWidget(tags_title)
            
            for key, value in item.tags.items():
                if isinstance(value, bool):
                    tag_label = QLabel(f"• {key}")
                else:
                    tag_label = QLabel(f"• {key}: {value}")
                
                tag_label.setStyleSheet("color: #dcdcdc; font-size: 13px; background: transparent; border: none;")
                tag_label.setWordWrap(True)
                self.details_layout.addWidget(tag_label)
        
        if item.description:
            self._add_separator()
            
            desc_title = QLabel(self.tr.t("labels.description"))
            desc_title.setStyleSheet("font-weight: bold; color: white; font-size: 14px; background: transparent; border: none;")
            self.details_layout.addWidget(desc_title)
            
            desc_text = QLabel(item.description[:500] + ("..." if len(item.description) > 500 else ""))
            desc_text.setStyleSheet("color: #dcdcdc; font-size: 13px; line-height: 1.4; background: transparent; border: none;")
            desc_text.setWordWrap(True)
            desc_text.setAlignment(Qt.AlignmentFlag.AlignTop)
            desc_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.details_layout.addWidget(desc_text)
        
        self.details_layout.addStretch()
    
    def _setup_installed_details(self, folder_path: str, project_data: dict):
        self._clear_details()
        
        size_bytes = get_directory_size(folder_path)
        self.size_label = QLabel("📦 " + self.tr.t("labels.size", size=human_readable_size(size_bytes)))
        self.size_label.setStyleSheet("color: #a3a3a3; font-size: 14px; background: transparent; border: none;")
        self.details_layout.addWidget(self.size_label)
        
        mtime = get_folder_mtime(folder_path)
        date_str = format_timestamp(mtime)
        self.date_label = QLabel("📅 " + self.tr.t("labels.installed", date=date_str))
        self.date_label.setStyleSheet("color: #a3a3a3; font-size: 14px; background: transparent; border: none;")
        self.details_layout.addWidget(self.date_label)

        self._add_separator()

        desc_title = QLabel(self.tr.t("labels.description"))
        desc_title.setStyleSheet("font-weight: bold; color: white; font-size: 14px; background: transparent; border: none;")
        self.details_layout.addWidget(desc_title)

        description = project_data.get("description", "")
        if description:
            self.description_text = QLabel(description)
        else:
            self.description_text = QLabel(self.tr.t("labels.no_description"))
        
        self.description_text.setStyleSheet("color: #dcdcdc; font-size: 13px; line-height: 1.4; background: transparent; border: none;")
        self.description_text.setWordWrap(True)
        self.description_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.description_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_layout.addWidget(self.description_text)
        
        self.details_layout.addStretch()
    
    def _clear_details(self):
        while self.details_layout.count():
            child = self.details_layout.takeAt(0)
            if child is not None and child.widget() is not None:
                child.widget().deleteLater()
    
    def _add_separator(self):
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #3c3f58; border: none;")
        self.details_layout.addWidget(separator)
    
    def _load_remote_preview(self, url: str):
        if not url:
            self.preview_label.setText("🖼️")
            return
        
        manager = self.get_network_manager()
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy
        )
        
        self._current_reply = manager.get(request)
        
        expected_pubfileid = self.current_pubfileid
        weak_self = weakref.ref(self)
        
        def on_finished():
            self_ref = weak_self()
            if self_ref is None:
                return
            if self_ref.current_pubfileid != expected_pubfileid:
                if self_ref._current_reply:
                    try:
                        self_ref._current_reply.deleteLater()
                    except:
                        pass
                    self_ref._current_reply = None
                return
            self_ref._on_preview_loaded()
        
        self._current_reply.finished.connect(on_finished)
    
    def _on_preview_loaded(self):
        if self._current_reply is None:
            return
        
        reply = self._current_reply
        
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.preview_label.setText("🖼️")
                reply.deleteLater()
                self._current_reply = None
                return
            
            data = reply.readAll()
            content_type = reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader)
            url = reply.url().toString().lower()
            
            is_gif = False
            if content_type and 'gif' in str(content_type).lower():
                is_gif = True
            elif url.endswith('.gif'):
                is_gif = True
            
            if is_gif:
                try:
                    fd, self._temp_gif_file = tempfile.mkstemp(suffix='.gif')
                    os.write(fd, bytes(data))
                    os.close(fd)
                    
                    self.movie = QMovie(self._temp_gif_file)
                    self.movie.setScaledSize(self.preview_label.size())
                    self.preview_label.setMovie(self.movie)
                    self.movie.start()
                except Exception as e:
                    print(f"[DetailsPanel] GIF load error: {e}")
                    self.preview_label.setText("🖼️")
            else:
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    scaled = pixmap.scaled(
                        self.preview_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled)
                else:
                    self.preview_label.setText("🖼️")
            
            reply.deleteLater()
            self._current_reply = None
            
        except Exception as e:
            print(f"[DetailsPanel] Preview load error: {e}")
            self.preview_label.setText("🖼️")
            if self._current_reply:
                try:
                    self._current_reply.deleteLater()
                except:
                    pass
                self._current_reply = None
    
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
            ext = preview_file.suffix.lower()
            
            if ext == ".gif":
                self.movie = QMovie(str(preview_file))
                self.movie.setScaledSize(self.preview_label.size())
                self.preview_label.setMovie(self.movie)
                self.movie.start()
            else:
                pixmap = QPixmap(str(preview_file))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        self.preview_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled)
        
        except Exception as e:
            self.preview_label.clear()
            self.preview_label.setText("Error")
    
    def _load_project_json(self, folder_path: str) -> dict:
        json_path = Path(folder_path) / "project.json"
        if not json_path.exists():
            return {}
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    
    def _on_download(self):
        if not self.current_pubfileid:
            return
        
        parent = self.parent()
        while parent and not hasattr(parent, 'start_download'):
            parent = parent.parent()
        
        if parent:
            parent.start_download(self.current_pubfileid)
    
    def _on_open_folder(self):
        if self.current_folder and Path(self.current_folder).exists():
            os.startfile(self.current_folder)
    
    def _on_open_browser(self):
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={self.current_pubfileid}"
        webbrowser.open(url)
    
    def _on_delete(self):
        if not self.current_folder:
            return

        if self.we.is_wallpaper_active(Path(self.current_folder)):
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

        main_window = self.window()
        if hasattr(main_window, 'wallpapers_tab'):
            main_window.wallpapers_tab.release_resources_for_folder(self.current_folder)
        self.release_resources()

        folder_to_delete = self.current_folder

        def perform_deletion():
            try:
                folder = Path(folder_to_delete)
                if folder.exists():
                    shutil.rmtree(folder)
                self._show_notification(self.tr.t("messages.wallpaper_deleted"))

                QTimer.singleShot(100, self.refresh_after_state_change)
                if hasattr(main_window, 'refresh_wallpapers'):
                    main_window.refresh_wallpapers()
                parent = self.parent()
                while parent and not hasattr(parent, '_update_item_statuses'):
                    parent = parent.parent()
                if parent:
                    parent._update_item_statuses()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{str(e)}")

        QTimer.singleShot(200, perform_deletion)
    
    def _on_extract(self):
        if not self.current_folder:
            self._show_notification(self.tr.t("messages.no_wallpaper_selected"))
            return
        
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        
        if not output_dir:
            return
        
        success = self.dm.start_extraction(self.current_pubfileid, Path(output_dir))
        
        if success:
            self._show_notification(self.tr.t("messages.extraction_started"))
        else:
            self._show_notification(self.tr.t("messages.no_pkg_file"))
    
    def _on_apply(self):
        if not self.current_folder:
            return
        
        project_json = Path(self.current_folder) / "project.json"
        
        if self.we.is_wallpaper_active(Path(self.current_folder)):
            return
        
        self.we.apply_wallpaper(project_json)
    
    def _on_install_and_open(self):
        self._on_apply()
        self.we.open_wallpaper_engine(show_window=True)

    def _copy_id(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_pubfileid)
            self._show_notification(self.tr.t("messages.id_copied"))
    
    def _show_notification(self, message: str):
        NotificationLabel.show_notification(self.parent(), message, 55, 15)
    
    def release_resources(self):
        self._reset_preview()
