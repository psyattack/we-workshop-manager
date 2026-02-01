import re
from pathlib import Path
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import QSize
from utils.mouse_listener import MouseListenerThread
from utils.web_engine import CustomWebEnginePage
from ui.custom_widgets import LoadingLabel, NotificationLabel
from resources.icons import get_icon
from resources.images import BG_BASE64

class BrowserTab(QWidget):
    update_downloads_signal = pyqtSignal()
    
    def __init__(self, config_manager, account_manager, download_manager, translator, theme_manager, parent=None):
        super().__init__(parent)
        
        self.config = config_manager
        self.accounts = account_manager
        self.dm = download_manager
        self.tr = translator
        self.theme = theme_manager
        
        self.start_url = "https://steamcommunity.com/workshop/browse/?appid=431960"
        
        self._setup_ui()
        self._setup_webview()
        self._setup_downloads_popup()
        
        self.update_downloads_signal.connect(self._safe_update_downloads_list)
        
        self.downloads_timer = QTimer()
        self.downloads_timer.timeout.connect(self.update_downloads_signal.emit)
        self.downloads_timer.start(1000)
    
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.loader_label = LoadingLabel(self.tr.t("labels.loading"))
        self.layout.addWidget(self.loader_label)
    
    def _setup_webview(self):
        profile_path = Path.cwd() / "Cookies"
        profile = QWebEngineProfile("Default_Profile", self)
        profile.setPersistentStoragePath(str(profile_path))
        profile.setCachePath(str(profile_path))
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        
        page = CustomWebEnginePage(profile, self)
        page.download_requested.connect(self._on_download_requested)
        page.already_installed.connect(self._on_already_installed)
        page.check_status_requested.connect(self._on_check_status)
        
        self.webview = QWebEngineView()
        self.webview.setPage(page)
        self.webview.setVisible(False)
        self.webview.loadStarted.connect(self._on_load_started)
        self.webview.loadFinished.connect(self._on_load_finished)
        
        self.layout.addWidget(self.webview)
        
        self.webview.load(QUrl(self.start_url))

        self.mouse_thread = MouseListenerThread(self.window())
        self.mouse_thread.forward_clicked.connect(self.go_forward)
        self.mouse_thread.back_clicked.connect(self.go_back)
        self.mouse_thread.start()
    
    def _setup_downloads_popup(self):
        self.downloads_popup = QWidget()
        self.downloads_popup.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.downloads_popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.downloads_popup.setFixedSize(260, 350)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.scroll_container = QWidget()
        self.scroll_container.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.setSpacing(3)
        
        scroll_area.setWidget(self.scroll_container)
        
        popup_layout = QVBoxLayout(self.downloads_popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.addWidget(scroll_area)
    
    def _on_download_requested(self, pubfileid: str, go_back: bool):
        if go_back:
            self.go_back()
        
        account_index = self.config.get_account_number()
        self.dm.start_download(pubfileid, account_index)
    
    def _on_already_installed(self):
        NotificationLabel.show_notification(self.window(), self.tr.t("messages.already_installed"))
    
    def _on_check_status(self, pubfileid: str, old_text: str):
        main_window = self.window()
        
        is_downloading = self.dm.is_downloading(pubfileid)
        is_installed = hasattr(main_window, 'we') and main_window.we.is_installed(pubfileid)
        
        if is_downloading:
            status = "🌐 Download"
        elif is_installed:
            status = "✅ Installed"
        elif old_text == "🔽 Get & Install":
            status = "🌐 Download"
            self._on_download_requested(pubfileid, go_back=False)
        else:
            status = "🔽 Get & Install"
        
        QTimer.singleShot(0, lambda: self._update_button_status(pubfileid, status))
    
    def _update_button_status(self, pubfileid: str, status: str):
        js = f"""
            btn = document.querySelector('button.copy-link-btn[data-pubfileid="{pubfileid}"]');
            if (btn) {{
                btn.innerText = "{status}";
            }}
        """
        self.webview.page().runJavaScript(js)
    
    def _on_load_started(self):
        self.webview.setVisible(False)
        self.loader_label.setVisible(True)
    
    def _on_load_finished(self, ok):
        if ok:
            self._inject_scripts()
    
    def _inject_scripts(self):
        """JavaScript"""
        current_url = self.webview.url().toString()
        
        bg_base64 = self.config.get_custom_background()
        if not bg_base64:
            bg_base64 = BG_BASE64
        
        bg_url = f"data:image/jpeg;base64,{bg_base64}"
        
        is_details = re.search(r'\b\d{8,10}\b', current_url) is not None
        
        if is_details:
            self._inject_details_page(current_url, bg_url)
        else:
            self._inject_browse_page(bg_url)
    
    def _inject_details_page(self, url: str, bg_url: str):
        pubfileid = re.search(r'\b\d{8,10}\b', url).group(0)

        main_window = self.window()
        is_downloading = self.dm.is_downloading(pubfileid)
        is_installed = hasattr(main_window, 'we') and main_window.we.is_installed(pubfileid)
        
        if is_downloading:
            custom_event = "DOWNLOADING"
            button_text = "Downloading..."
        elif is_installed:
            custom_event = "ALREADY_INSTALLED"
            button_text = "Installed"
        else:
            custom_event = f"CUSTOM_EVENT:{url}"
            button_text = "Get & Install"
        
        script_path = Path(__file__).parent.parent / "resources" / "scripts" / "workshop_details.js"
        
        if script_path.exists():
            with open(script_path, 'r', encoding='utf-8') as f:
                script_template = f.read()
        else:
            script_template = "(function() { return true; })();"
        
        js = f"""
            window.CUSTOM_BG_URL = "{bg_url}";
            window.CUSTOM_EVENT = "{custom_event}";
            window.BUTTON_TEXT = "{button_text}";
            {script_template}
        """
        
        self.webview.page().runJavaScript(js, self._on_script_finished)
    
    def _inject_browse_page(self, bg_url: str):
        account_index = self.config.get("account_number_for_logging", 6)
        username, password = self.accounts.get_credentials(account_index)
        
        scripts_dir = Path(__file__).parent.parent / "resources" / "scripts"
        
        login_script = ""
        browse_script = ""
        
        login_path = scripts_dir / "auto_login.js"
        if login_path.exists():
            with open(login_path, 'r', encoding='utf-8') as f:
                login_script = f.read()
        
        browse_path = scripts_dir / "workshop_browse.js"
        if browse_path.exists():
            with open(browse_path, 'r', encoding='utf-8') as f:
                browse_script = f.read()
        
        combined_js = f"""
            window.STEAM_USERNAME = "{username}";
            window.STEAM_PASSWORD = "{password}";
            {login_script}
            
            window.CUSTOM_BG_URL = "{bg_url}";
            {browse_script}
        """
        
        self.webview.page().runJavaScript(combined_js, self._on_script_finished)
    
    def _on_script_finished(self, result):
        if result:
            self.loader_label.hide()
            self.webview.setVisible(True)
            self.webview.setFocus()
    
    def _safe_update_downloads_list(self):
        self._clear_downloads_widgets()

        all_tasks = []
        
        try:
            for pubfileid, info in self.dm.downloading.items():
                all_tasks.append(("download", pubfileid, info))
            
            for pubfileid, info in self.dm.extracting.items():
                all_tasks.append(("extract", pubfileid, info))
        except RuntimeError:
            return
        
        if not all_tasks:
            self._show_no_tasks_widget()
        else:
            for task_type, pubfileid, info in all_tasks:
                try:
                    self._create_task_item(task_type, pubfileid, info)
                except Exception as e:
                    print(f"Error creating task item: {e}")
        
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.scroll_layout.addItem(spacer)
    
    def _clear_downloads_widgets(self):
        while self.scroll_layout.count():
            try:
                child = self.scroll_layout.takeAt(0)
                if child.widget():
                    widget = child.widget()
                    widget.setParent(None)
                    widget.deleteLater()
                elif child.spacerItem():
                    pass
            except Exception as e:
                print(f"Error clearing download widget: {e}")
    
    def _show_no_tasks_widget(self):
        label = QLabel(self.tr.t("labels.no_tasks"))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            color: white;
            font-size: 14px;
            background-color: rgba(0, 0, 0, 160);
            padding: 8px 12px;
            border-radius: 6px;
        """)
        label.setFixedSize(250, 70)
        self.scroll_layout.addWidget(label)
    
    def _create_task_item(self, task_type: str, pubfileid: str, info: dict):
        item_widget = QWidget()
        item_widget.setFixedSize(250, 70)
        
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        
        bg_container = QWidget()
        bg_container.setStyleSheet("background-color: rgba(0, 0, 0, 160); border-radius: 6px;")
        
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
        text_label.setStyleSheet("color: white; font-size: 14px;")
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setWordWrap(True)
        text_label.setFixedSize(200, 50)
        text_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        text_label.mousePressEvent = lambda e, pid=pubfileid: self._open_workshop_page(pid)
        
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
    
    def _open_workshop_page(self, pubfileid: str):
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}"
        self.webview.load(QUrl(url))
        self.downloads_popup.hide()
    
    def _cancel_download(self, pubfileid: str):
        self.dm.cancel_download(pubfileid)
        
        QTimer.singleShot(100, self.update_downloads_signal.emit)
        
        main_window = self.window()
        if hasattr(main_window, 'refresh_wallpapers'):
            QTimer.singleShot(200, main_window.refresh_wallpapers)
    
    def go_home(self):
        self.webview.load(QUrl(self.start_url))
    
    def go_back(self):
        self.webview.back()
    
    def go_forward(self):
        self.webview.forward()
    
    def show_downloads_popup(self, button_pos):
        self.downloads_popup.move(button_pos.x() - 12, button_pos.y() - 5)

        self.update_downloads_signal.emit()
        self.downloads_popup.show()
    
    def hide_downloads_popup(self):
        self.downloads_popup.hide()
    
    def closeEvent(self, event):
        if hasattr(self, 'downloads_timer'):
            self.downloads_timer.stop()
        
        if hasattr(self, 'mouse_thread'):
            self.mouse_thread.stop()
        
        event.accept()
