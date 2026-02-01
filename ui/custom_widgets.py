from PyQt6.QtCore import Qt, QTimer, QEventLoop
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QFrame, QGraphicsDropShadowEffect, QFileDialog, QApplication, QMessageBox
)
import base64
from pathlib import Path
import traceback
from resources.images import BG_BASE64

class LoadingLabel(QLabel):
    def __init__(self, base_text: str = "⏳ Loading", parent=None):
        super().__init__(parent)
        
        self.base_text = base_text
        self.dots = ""
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                color: #4A7FD9;
                font-size: 24px;
                font-weight: 800;
                background: transparent;
                letter-spacing: 2px;
            }
        """)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_text)
        self.timer.start(400)
        
        self._update_text()
    
    def _update_text(self):
        if len(self.dots) >= 3:
            self.dots = ""
        else:
            self.dots += "."
        
        self.setText(self.base_text + self.dots)
    
    def stop(self):
        self.timer.stop()

class NotificationLabel(QLabel):
    def __init__(self, message: str, parent=None):
        super().__init__(message, parent)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(74, 127, 217, 240);
                color: white;
                padding: 12px 20px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(74, 127, 217, 120))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        QTimer.singleShot(2000, self.deleteLater)
    
    @staticmethod
    def show_notification(parent, message: str, x: int = 5, y: int = 135):
        if not parent or not message:
            return
        
        notification = NotificationLabel(message, parent)
        notification.adjustSize()
        
        if notification.width() < 200:
            notification.setFixedWidth(200)
        
        notification.move(x, y)
        notification.show()
        notification.raise_()

class ModernSettingsPopup(QWidget):
    def __init__(self, config, accounts, translator, theme_manager, main_window, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.accounts = accounts
        self.tr = translator
        self.theme = theme_manager
        self.main_window = main_window
        
        self.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedSize(360, 480)

        container = QFrame(self)
        container.setGeometry(0, 0, 360, 480)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('bg_elevated')};
                border-radius: 16px;
                border: 2px solid {self.theme.get_color('border_light')};
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 6)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        header = QLabel("SETTINGS")
        header.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 800;
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            border: none;
        """)
        layout.addWidget(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {self.theme.get_color('border')}; max-height: 2px;")
        layout.addWidget(divider)

        section_label = QLabel("🎨 Theme (In Dev)")
        section_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            margin-top: 2px;
            border-radius: 5px;
        """)
        layout.addWidget(section_label)

        self._add_section(layout, "👤 Steam Account", self._create_account_combo())
        
        self._add_section(layout, "🌍 Language", self._create_language_combo())

        self._add_section(layout, "🖼️ Background", self._create_background_controls())
        
        layout.addStretch()
    
    def _add_section(self, layout, title, widget):
        section_label = QLabel(title)
        section_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            margin-top: 2px;
            border-radius: 5px;
        """)
        layout.addWidget(section_label)
        layout.addWidget(widget)
    
    def _create_account_combo(self):
        combo = QComboBox()
        last_loggin_acc = 1
        for i in range(len(self.accounts.get_accounts()) - last_loggin_acc):
            combo.addItem(f"Account {i + 1}")
        combo.setCurrentIndex(self.config.get_account_number())
        combo.currentIndexChanged.connect(lambda idx: self.config.set_account_number(idx))
        combo.setStyleSheet(self._combo_style())
        return combo
    
    def _create_theme_combo(self):
        combo = QComboBox()
        combo.addItems(["🌙 Dark", "☀️ Light"])
        combo.setCurrentIndex(0 if self.config.get_theme() == "dark" else 1)
        combo.currentIndexChanged.connect(self._on_theme_changed)
        combo.setStyleSheet(self._combo_style())
        return combo
    
    def _create_language_combo(self):
        combo = QComboBox()
        combo.addItems(["English", "Русский"])
        combo.setCurrentIndex(0 if self.config.get_language() == "en" else 1)
        combo.currentIndexChanged.connect(self._on_language_changed)
        combo.setStyleSheet(self._combo_style())
        return combo
    
    def _create_background_controls(self):
        container = QWidget()
        container.setStyleSheet("QWidget { background: transparent; border: none; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self.bg_status = QLabel()
        self.bg_status.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 12px;
            background: transparent;
        """)
        self._update_bg_status()
        layout.addWidget(self.bg_status)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self._select_background)
        select_btn.setStyleSheet(self._button_style())
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_background)
        remove_btn.setStyleSheet(self._button_style())
        
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(remove_btn)
        
        layout.addLayout(btn_layout)
        
        return container
    
    def _combo_style(self):
        return f"""
            QComboBox {{
                background-color: {self.theme.get_color('bg_tertiary')};
                color: {self.theme.get_color('text_primary')};
                border: 2px solid {self.theme.get_color('border')};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            QComboBox:hover {{
                border-color: {self.theme.get_color('primary')};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.theme.get_color('bg_elevated')};
                color: {self.theme.get_color('text_primary')};
                selection-background-color: {self.theme.get_color('primary')};
                border: 2px solid {self.theme.get_color('border')};
                border-radius: 6px;
            }}
        """
    
    def _button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.theme.get_color('primary')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('primary_hover')};
            }}
        """
    
    def _on_theme_changed(self, index):
        theme = "dark" if index == 0 else "light"
        self.config.set_theme(theme)
        self.theme.set_theme(theme, QApplication.instance())
        
        if self.parent():
            NotificationLabel.show_notification(self.parent(), "Theme changed!")
    
    def _on_language_changed(self, index):
        lang = "en" if index == 0 else "ru"
        self.config.set_language(lang)
        self.tr.set_language(lang)

        QMessageBox.information(
            self,
            "Language Changed",
            "Please restart the application for language changes to take effect."
        )
    
    def _update_bg_status(self):
        if self.config.get_custom_background():
            self.bg_status.setText(" Background: Custom")
        else:
            self.bg_status.setText(" Background: Default")
    
    def _select_background(self):
        try:
            parent = self.main_window if self.main_window else None
            
            self.hide()

            loop = QEventLoop()
            QTimer.singleShot(100, loop.quit)
            loop.exec()

            file_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Select Background Image",
                str(Path.home() / "Pictures"),
                "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)"
            )
            
            self.show()
            
            if not file_path:
                return

            if not Path(file_path).exists():
                QMessageBox.warning(parent, "Error", "File not found!")
                return

            with open(file_path, "rb") as f:
                image_data = f.read()

            base64_data = base64.b64encode(image_data).decode('utf-8')
            self.config.set_custom_background(base64_data)
            self._update_bg_status()

            if self.main_window:
                NotificationLabel.show_notification(self.main_window, "Background updated!")

            self._apply_background_immediately()
            
        except Exception as e:
            traceback.print_exc()
            
            self.show()

            QMessageBox.critical(
                self.main_window if self.main_window else None,
                "Error",
                f"Failed to set background:\n{str(e)}"
            )
    
    def _remove_background(self):
        try:
            self.config.set_custom_background(None)
            self._update_bg_status()
            
            if self.main_window:
                NotificationLabel.show_notification(self.main_window, "Background removed!")
            
            self._apply_background_immediately()
            
        except Exception as e:
            traceback.print_exc()
    
    def _apply_background_immediately(self):
        try:
            if not self.main_window:
                return
            
            if not hasattr(self.main_window, 'browser_tab'):
                return
            
            browser_tab = self.main_window.browser_tab
            
            if not hasattr(browser_tab, 'webview'):
                return

            bg_base64 = self.config.get_custom_background()
            if not bg_base64:
                bg_base64 = BG_BASE64
            
            bg_url = f"data:image/jpeg;base64,{bg_base64}"

            js_code = f"""
            (function() {{
                let styleId = 'dynamic-bg-style';
                let styleEl = document.getElementById(styleId);
                if (!styleEl) {{
                    styleEl = document.createElement('style');
                    styleEl.id = styleId;
                    document.head.appendChild(styleEl);
                }}
                styleEl.textContent = `
                    body.apphub_blue::before {{
                        content: "";
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: url("{bg_url}") no-repeat center center;
                        background-size: cover;
                        z-index: -1;
                    }}
                `;
            }})();
            """
            
            browser_tab.webview.page().runJavaScript(js_code)
            
        except Exception as e:
            traceback.print_exc()
