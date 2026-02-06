from pathlib import Path
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabBar, QStackedWidget, QMessageBox, QApplication, 
    QFrame, QGraphicsDropShadowEffect
)
from ui.workshop_tab import WorkshopTab
from ui.wallpapers_tab import WallpapersTab
from ui.dialogs import BatchDownloadDialog, InfoDialog
from resources.icons import get_icon
from ui.custom_widgets import ModernSettingsPopup
from utils.helpers import clear_cache_if_needed

class MainWindow(QMainWindow):
    download_completed = pyqtSignal(str)
    
    def __init__(self, config_manager, account_manager, download_manager, wallpaper_engine, translator, theme_manager):
        super().__init__()
        
        self.config = config_manager
        self.accounts = account_manager
        self.dm = download_manager
        self.we = wallpaper_engine
        self.tr = translator
        self.theme = theme_manager
        
        self._is_maximized = False
        self.old_pos = None
        
        self._setup_ui()
        self._apply_theme()
        
        self.dm.download_completed.connect(self._on_download_completed_signal)

    def _on_download_completed_signal(self, pubfileid: str, success: bool):
        if success:
            QTimer.singleShot(300, self.refresh_wallpapers)

    def refresh_wallpapers(self):
        if hasattr(self, 'wallpapers_tab'):
            self.wallpapers_tab.refresh()
    
    def _setup_ui(self):
        self.setWindowTitle("WE Workshop Manager")
        self.resize(1200, 730)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        central_widget = QWidget()
        central_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme.get_color('bg_primary')};
                border-radius: 16px;
            }}
        """)
        
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.title_bar = self._create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        self.nav_bar = self._create_tab_bar()
        main_layout.addWidget(self.nav_bar)

        self._create_tabs()
        main_layout.addWidget(self.stack)
        
        # Temp placeholder
        self._create_corner_covers()

    def _create_corner_covers(self):
        self._corner_covers = []
        
        bg_color = self.theme.get_color('bg_primary')
        title_bg = self.theme.get_color('bg_secondary')
        
        colors = [title_bg, bg_color, bg_color, bg_color]
        
        for i in range(4):
            cover = QWidget(self.centralWidget()) 
            cover.setFixedSize(16, 16)
            cover.setStyleSheet(f"background-color: {colors[i]}; border: none;")
            cover.hide()
            cover.lower()
            self._corner_covers.append(cover)

    def _update_corner_covers(self):
        if not hasattr(self, '_corner_covers'):
            return
        
        w, h = self.centralWidget().width(), self.centralWidget().height()
        size = 16
        
        positions = [
            (0, 0),
            (w - size, 0),
            (0, h - size),
            (w - size, h - size)
        ]
        
        for cover, pos in zip(self._corner_covers, positions):
            cover.move(pos[0], pos[1])
            cover.setVisible(self._is_maximized)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_corner_covers()

    def _toggle_maximize(self):
        if self._is_maximized:
            self.showNormal()
            self.max_btn.setIcon(get_icon("ICON_MAXIMIZE"))
            self._is_maximized = False
        else:
            self.showMaximized()
            self.max_btn.setIcon(get_icon("ICON_RESTORE"))
            self._is_maximized = True
        
        self._update_corner_covers()
    
    def _create_title_bar(self) -> QFrame:
        title_bar = QFrame()
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme.get_color('bg_secondary')},
                    stop:1 {self.theme.get_color('bg_primary')});
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                margin-top: 1px;
                margin-bottom: 5px;
            }}
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 0, 10, 0)
        layout.setSpacing(12)

        app_name = QLabel("WE Workshop Manager")
        app_name.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 800;
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            letter-spacing: 1px;
        """)
        layout.addWidget(app_name)
        
        layout.addStretch()

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet(f"background-color: {self.theme.get_color('border')}; max-width: 1px;")
        layout.addWidget(divider)

        window_btns_layout = QHBoxLayout()
        window_btns_layout.setSpacing(4)
        
        min_btn = self._create_window_button('minimize', self.showMinimized)
        self.max_btn = self._create_window_button('maximize', self._toggle_maximize)
        close_btn = self._create_window_button('close', self._on_close)
        
        window_btns_layout.addWidget(min_btn)
        window_btns_layout.addWidget(self.max_btn)
        window_btns_layout.addWidget(close_btn)
        
        layout.addLayout(window_btns_layout)
        
        return title_bar
    
    def _create_tab_bar(self) -> QFrame:
        nav_bar = QFrame()
        nav_bar.setFixedHeight(70)
        nav_bar.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.get_color('bg_secondary')};
            border: none;
        }}
        """)
        layout = QHBoxLayout(nav_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        
        self.tab_bar = QTabBar()
        self.tab_bar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.addTab(self.tr.t("tabs.workshop"))
        self.tab_bar.addTab(self.tr.t("tabs.wallpapers"))
        self.tab_bar.setExpanding(False)
        self.tab_bar.setStyleSheet(f"""
        QTabBar {{
            background-color: {self.theme.get_color('bg_elevated')};
        }}
        """)
        layout.addWidget(self.tab_bar)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        self.downloads_btn = self._create_toolbar_button(
            "ICON_TASK",
            self.tr.t("tooltips.tasks"),
            "#5B8DEF",
            self._toggle_downloads_popup
        )
        self.batch_btn = self._create_toolbar_button(
            "ICON_UPLOAD",
            self.tr.t("tooltips.batch_download"),
            "#5B8DEF",
            self._show_batch_download
        )
        self.settings_btn = self._create_toolbar_button(
            "ICON_USER_SETTINGS",
            self.tr.t("tooltips.settings"),
            "#5B8DEF",
            self._show_settings
        )
        self.info_btn = self._create_toolbar_button(
            "ICON_INFO",
            self.tr.t("tooltips.info"),
            "#5B8DEF",
            self._show_info
        )
        
        actions_layout.addWidget(self.downloads_btn)
        actions_layout.addWidget(self.batch_btn)
        actions_layout.addWidget(self.settings_btn)
        actions_layout.addWidget(self.info_btn)
        
        layout.addLayout(actions_layout)
        
        return nav_bar
    
    def _create_toolbar_button(self, icon_name, tooltip, color, callback):
        btn = QPushButton()
        btn.setIcon(get_icon(icon_name))
        btn.setIconSize(QSize(22, 22))
        btn.setFixedSize(44, 44)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color)};
            }}
        """)
        btn.clicked.connect(callback)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(color))
        shadow.setOffset(0, 3)
        btn.setGraphicsEffect(shadow)
        
        return btn
    
    def _create_window_button(self, button_type: str, callback):
        btn = QPushButton()
        btn.setFixedSize(42, 42)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        icon_map = {
            'minimize': "ICON_MINIMIZE",
            'maximize': "ICON_MAXIMIZE",
            'restore': "ICON_RESTORE",
            'close': "ICON_CLOSE"
        }
        
        btn.setIcon(get_icon(icon_map.get(button_type, "ICON_CLOSE")))
        btn.setIconSize(QSize(20, 20))
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        btn.clicked.connect(callback)
        
        return btn
    
    def _lighten_color(self, hex_color):
        color = QColor(hex_color)
        h, s, v, a = color.getHsv()
        color.setHsv(h, max(0, s - 30), min(255, v + 40), a)
        return color.name()
    
    def _darken_color(self, hex_color):
        color = QColor(hex_color)
        h, s, v, a = color.getHsv()
        color.setHsv(h, min(255, s + 30), max(0, v - 40), a)
        return color.name()
    
    def _create_tabs(self):
        self.stack = QStackedWidget()
        
        self.workshop_tab = WorkshopTab(
            self.config, self.accounts, self.dm, self.we,
            self.tr, self.theme, self
        )

        self.wallpapers_tab = WallpapersTab(
            self.config, self.dm, self.we,
            self.tr, self.theme, self
        )
        
        self.stack.addWidget(self.workshop_tab)
        self.stack.addWidget(self.wallpapers_tab)
        
        self.tab_bar.currentChanged.connect(self.stack.setCurrentIndex)
    
    def _apply_theme(self):
        theme_name = self.config.get_theme()
        self.theme.set_theme(theme_name, QApplication.instance())
    
    def _toggle_downloads_popup(self):
        if self.workshop_tab.downloads_popup.isVisible():
            self.workshop_tab.hide_downloads_popup()
        else:
            btn_pos = self.downloads_btn.mapToGlobal(self.downloads_btn.rect().bottomLeft())
            self.workshop_tab.show_downloads_popup(btn_pos)
    
    def _show_settings(self):
        if hasattr(self, 'settings_popup') and self.settings_popup.isVisible():
            self.settings_popup.hide()
            return
        
        self.settings_popup = ModernSettingsPopup(
            self.config, self.accounts, self.tr, self.theme, self
        )
        
        btn_pos = self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft())
        self.settings_popup.move(btn_pos.x() - 250, btn_pos.y() + 10)
        self.settings_popup.show()
    
    def _show_batch_download(self):
        dialog = BatchDownloadDialog(self.tr, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            pubfileids = dialog.get_pubfileids()
            
            new_ids = [
                pid for pid in pubfileids
                if not self.we.is_installed(pid) and not self.dm.is_downloading(pid)
            ]
            
            if not new_ids:
                return
            
            account_index = self.config.get_account_number()
            
            for pid in new_ids:
                self.dm.start_download(pid, account_index)
    
    def _show_info(self):
        dialog = InfoDialog(self.tr, self)
        dialog.exec()
    
    def _on_close(self):
        has_downloads = len(self.dm.downloading) > 0
        has_extractions = len(self.dm.extracting) > 0
        
        if has_downloads or has_extractions:
            if has_downloads and has_extractions:
                msg = self.tr.t("messages.exit_with_downloads")
            elif has_downloads:
                msg = self.tr.t("messages.exit_with_downloads_only")
            else:
                msg = self.tr.t("messages.exit_with_extractions_only")
            
            reply = QMessageBox.question(
                self,
                self.tr.t("dialog.exit"),
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.dm.cleanup_all()
        
        if hasattr(self, 'workshop_tab'):
            self.workshop_tab.cleanup()
        
        clear_cache_if_needed(Path("Cookies/Cache"), 200)
        
        self.close()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_maximized and event.position().y() <= self.title_bar.height():
                self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event):
        self.old_pos = None
