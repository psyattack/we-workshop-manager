from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame, QGraphicsDropShadowEffect, QWidget, QMessageBox
)
from resources.icons import get_icon
import re

class CustomDialog(QDialog):
    def __init__(self, title: str = "Dialog", parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #1A1D2E;
                border-radius: 12px;
                border: 2px solid #3A3F52;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.container)
        
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        
        self._create_title_bar(title)
        
        # For moving
        self.old_pos = None
    
    def _create_title_bar(self, title):
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("QWidget { background: transparent; border: none; }")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 10)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
        font-size: 16px;
        font-weight: 700;
        color: white;
        background: transparent;
        """)

        close_btn = QPushButton()
        close_btn.setFixedSize(32, 32)
        close_btn.setIcon(get_icon("ICON_CLOSE"))
        close_btn.setIconSize(QSize(20, 20))
        close_btn.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 16px;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: rgba(239, 91, 91, 0.2);
        }
        QPushButton:pressed {
            background-color: rgba(239, 91, 91, 0.3);
        }
        """)
        close_btn.clicked.connect(self.reject)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        self.content_layout.addWidget(title_bar)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event):
        self.old_pos = None

class CustomMessageBox(CustomDialog):
    def __init__(self, title="Message", message=None, link_url=None, pubfileid=None, 
                 we_directory=None, translator=None, parent=None):
        super().__init__(title, parent)
        
        self.setFixedWidth(400)
        
        if message:
            msg_label = QLabel(message)
            msg_label.setStyleSheet("""
                color: white;
                font-size: 14px;
                background: transparent;
            """)
            msg_label.setWordWrap(True)
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(msg_label)
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(40)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A7FD9;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5B8FE9;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        self.content_layout.addWidget(ok_btn)

class BatchDownloadDialog(CustomDialog):
    def __init__(self, translator, parent=None):
        super().__init__("Batch Download", parent)
        
        self.tr = translator
        self.pubfileids = []
        
        self.setFixedSize(450, 350)

        label = QLabel(self.tr.t("messages.batch_input_placeholder"))
        label.setStyleSheet("color: white; background: transparent;")
        label.setWordWrap(True)
        self.content_layout.addWidget(label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("ID, URL...")
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #252938;
                color: white;
                border: 2px solid #3A3F52;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        self.content_layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()
        
        download_btn = QPushButton(self.tr.t("buttons.download_all"))
        download_btn.setFixedHeight(40)
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A7FD9;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5B8FE9;
            }
        """)
        download_btn.clicked.connect(self._on_download)
        
        btn_layout.addWidget(download_btn)
        
        self.content_layout.addLayout(btn_layout)
    
    def _on_download(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        
        tokens = re.split(r'\s+', text.replace('\n', ' ').replace('\r', ' '))
        
        seen = set()
        valid_ids = []
        
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            
            pubfileid = None
            
            if token.isdigit() and len(token) >= 8:
                pubfileid = token
            else:
                match = re.search(r'[?&]id=(\d{8,})', token)
                if match:
                    pubfileid = match.group(1)
            
            if pubfileid and pubfileid not in seen:
                valid_ids.append(pubfileid)
                seen.add(pubfileid)
        
        self.pubfileids = valid_ids
        
        if valid_ids:
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", self.tr.t("messages.invalid_input"))
    
    def get_pubfileids(self):
        return self.pubfileids

class InfoDialog(CustomDialog):
    def __init__(self, translator, parent=None):
        super().__init__("About", parent)
        
        self.tr = translator
        self.setFixedSize(400, 280)
        
        # May be add later
        # icon = QLabel("🎨")
        # icon.setStyleSheet("font-size: 48px; background: transparent;")
        # icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.content_layout.addWidget(icon)
        
        info_text = QLabel(
            f"{self.tr.t('info.version')}\n\n"
            f"{self.tr.t('info.description')}\n\n"
            f"{self.tr.t('info.developed')}"
        )
        info_text.setStyleSheet("""
            color: white;
            font-size: 13px;
            background: transparent;
        """)
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(info_text)

        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(40)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A7FD9;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5B8FE9;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        self.content_layout.addWidget(ok_btn)
