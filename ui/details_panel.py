import os
import json
import shutil
from pathlib import Path
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QMovie, QMouseEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QMessageBox, QFileDialog, QApplication
)
from utils.helpers import human_readable_size, format_timestamp
from ui.custom_widgets import NotificationLabel
from resources.icons import get_icon
from utils.helpers import get_directory_size, get_folder_mtime

class ClickableLabel(QLabel):
    clicked = pyqtSignal(str)
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            text = self.text()
            id_value = text.split("ID: ", 1)[-1].strip()
            self.clicked.emit(id_value)
        super().mousePressEvent(event)

class DetailsPanel(QWidget):
    def __init__(self, wallpaper_engine, download_manager, translator, theme_manager, parent=None):
        super().__init__(parent)
        
        self.we = wallpaper_engine
        self.dm = download_manager
        self.tr = translator
        self.theme = theme_manager
        
        self.folder_path = None
        self.movie = None
        
        self._setup_ui()
        self.setVisible(False)
    
    def _setup_ui(self):
        self.setMinimumWidth(310)
        self.setMaximumWidth(310)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)
        main_layout.setSpacing(14)

        self.large_preview = QLabel()
        self.large_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.large_preview.setFixedSize(310, 275)
        self.large_preview.setStyleSheet("""
            QLabel {
                background-color: #2c2f48;
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.large_preview)
        
        self._create_action_buttons(main_layout)

        self._create_id_section(main_layout)

        self._create_title_section(main_layout)

        self._create_details_section(main_layout)
        
        main_layout.addStretch()
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                border-left: 1px solid #3c3f58;
            }
        """)
    
    def _create_action_buttons(self, layout):
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        self.open_button = self._create_icon_button(
            "ICON_FOLDER",
            self.tr.t("tooltips.open_folder"),
            self._on_open_folder
        )

        self.workshop_button = self._create_icon_button(
            "ICON_WORLD",
            self.tr.t("tooltips.open_workshop"),
            self._on_open_workshop
        )

        self.delete_button = self._create_icon_button(
            "ICON_DELETE",
            self.tr.t("tooltips.delete_wallpaper"),
            self._on_delete,
            color='#ff5c5c',
            hover_color='#ff7c7c'
        )

        self.extract_button = self._create_icon_button(
            "ICON_DOWNLOAD",
            self.tr.t("tooltips.extract_wallpaper"),
            self._on_extract
        )

        self.install_button = self._create_icon_button(
            "ICON_UPLOAD",
            self.tr.t("tooltips.install_wallpaper"),
            self._on_install
        )
        
        self.install_open_button = self._create_icon_button(
            "ICON_LINK",
            self.tr.t("tooltips.install_open_we"),
            self._on_install_and_open
        )
        
        buttons_layout.addWidget(self.open_button)
        buttons_layout.addWidget(self.workshop_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.extract_button)
        buttons_layout.addWidget(self.install_button)
        buttons_layout.addWidget(self.install_open_button)
        
        buttons_widget.setStyleSheet("QWidget { background: transparent; border: none; }")
        layout.addWidget(buttons_widget)
    
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
        id_widget = QWidget()
        id_layout = QHBoxLayout(id_widget)
        id_layout.setContentsMargins(0, 0, 0, 0)
        
        self.id_label = ClickableLabel()
        self.id_label.setStyleSheet("""
            QLabel {
                color: #a3a3a3; 
                font-size: 14px;
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QLabel:hover {
                background-color: rgba(78, 140, 255, 0.25);
            }
        """)
        self.id_label.clicked.connect(self._copy_id)
        
        id_layout.addWidget(self.id_label)
        id_layout.addStretch()
        
        id_widget.setStyleSheet("QWidget { background: transparent; border: none; }")
        layout.addWidget(id_widget)
    
    def _create_details_section(self, layout):
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_scroll.setMaximumHeight(280)
        self.details_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        details_content = QWidget()
        details_layout = QVBoxLayout(details_content)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)
        
        self.size_label = QLabel()
        self.size_label.setStyleSheet("color: #a3a3a3; font-size: 14px;")
        details_layout.addWidget(self.size_label)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #a3a3a3; font-size: 14px;")
        details_layout.addWidget(self.date_label)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #3c3f58; margin: 8px 0px;")
        details_layout.addWidget(separator)

        desc_title = QLabel(self.tr.t("labels.description"))
        desc_title.setStyleSheet("font-weight: bold; color: white; font-size: 14px;")
        details_layout.addWidget(desc_title)

        self.description_text = QLabel()
        self.description_text.setStyleSheet("color: #dcdcdc; font-size: 13px; line-height: 1.4;")
        self.description_text.setWordWrap(True)
        self.description_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.description_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addWidget(self.description_text)
        
        details_layout.addStretch()
        
        self.details_scroll.setWidget(details_content)
        layout.addWidget(self.details_scroll)
    
    def set_folder(self, folder_path: str):
        self.folder_path = folder_path
        self.setVisible(True)
        
        project_data = self._load_project_json()

        title = project_data.get("title", Path(folder_path).name)
        self.title_label.setText(title)

        pubfileid = Path(folder_path).name
        self.id_label.setText(self.tr.t("labels.id", id=pubfileid))

        size_bytes = get_directory_size(folder_path)
        self.size_label.setText(self.tr.t("labels.size", size=human_readable_size(size_bytes)))

        mtime = get_folder_mtime(folder_path)
        date_str = format_timestamp(mtime)
        self.date_label.setText(self.tr.t("labels.installed", date=date_str))
        
        description = project_data.get("description", "")
        if description:
            self.description_text.setText(description)
        else:
            self.description_text.setText(self.tr.t("labels.no_description"))
        
        self._load_preview()
    
    def _load_project_json(self) -> dict:
        json_path = Path(self.folder_path) / "project.json"
        if not json_path.exists():
            return {}
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading project.json: {e}")
            return {}
    
    def _load_preview(self):
        if self.movie:
            self.movie.stop()
            self.large_preview.setMovie(None)
            self.movie = None

        preview_file = None
        for ext in ["png", "gif", "jpg"]:
            candidate = Path(self.folder_path) / f"preview.{ext}"
            if candidate.exists():
                preview_file = candidate
                break
        
        if not preview_file:
            self.large_preview.clear()
            self.large_preview.setText(self.tr.t("labels.no_preview"))
            return
        
        try:
            ext = preview_file.suffix.lower()
            
            if ext == ".gif":
                self.movie = QMovie(str(preview_file))
                self.movie.setScaledSize(self.large_preview.size())
                self.large_preview.setMovie(self.movie)
                self.movie.start()
            else:
                pixmap = QPixmap(str(preview_file))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        self.large_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.large_preview.setPixmap(scaled)
        
        except Exception as e:
            self.large_preview.clear()
            self.large_preview.setText("Error")
    
    def _on_open_folder(self):
        if self.folder_path and Path(self.folder_path).exists():
            os.startfile(self.folder_path)
    
    def _on_open_workshop(self):
        if not self.folder_path:
            return
        
        pubfileid = Path(self.folder_path).name
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}"

        main_window = self.window()
        if hasattr(main_window, 'open_in_browser'):
            main_window.open_in_browser(url)
    
    def _on_delete(self):
        if not self.folder_path:
            return
        
        if self.we.is_wallpaper_active(Path(self.folder_path)):
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
            main_window.wallpapers_tab.release_resources_for_folder(self.folder_path)
        
        self.release_resources()
        
        def perform_deletion():
            try:
                folder = Path(self.folder_path)
                if folder.exists():
                    shutil.rmtree(folder)
                    self._show_notification(self.tr.t("messages.wallpaper_deleted"))
                    
                    QTimer.singleShot(100, lambda: main_window.refresh_wallpapers())
            
            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.tr.t("dialog.error"),
                    f"Failed to delete:\n{str(e)}"
                )
        
        QTimer.singleShot(200, perform_deletion)
    
    def _on_extract(self):
        if not self.folder_path:
            self._show_notification(self.tr.t("messages.no_wallpaper_selected"))
            return
        
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        
        if not output_dir:
            return
        
        pubfileid = Path(self.folder_path).name

        success = self.dm.start_extraction(pubfileid, Path(output_dir))
        
        if success:
            self._show_notification(self.tr.t("messages.extraction_started"))
        else:
            self._show_notification(self.tr.t("messages.no_pkg_file"))
    
    def _on_install(self):
        if not self.folder_path:
            return
        
        project_json = Path(self.folder_path) / "project.json"

        if self.we.is_wallpaper_active(Path(self.folder_path)):
            return
        
        self.we.apply_wallpaper(project_json)
    
    def _on_install_and_open(self):
        self._on_install()
        self.we.open_wallpaper_engine(show_window=True)
    
    def _copy_id(self, id_value: str):
        clipboard = QApplication.clipboard()
        clipboard.setText(id_value)
        self._show_notification(self.tr.t("messages.id_copied"))
    
    def _show_notification(self, message: str):
        NotificationLabel.show_notification(self.parent(), message, 55, 5)
    
    def release_resources(self):
        if self.movie:
            self.movie.stop()
            self.large_preview.setMovie(None)
            self.movie = None
