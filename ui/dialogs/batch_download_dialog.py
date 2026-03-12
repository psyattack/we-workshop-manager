import re

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit

from ui.dialogs.base_dialog import BaseDialog
from ui.notifications import MessageBox


class BatchDownloadDialog(BaseDialog):
    def __init__(self, translator, parent=None, theme_manager=None):
        super().__init__(translator.t("dialog.batch_download"), parent, theme_manager)

        self.tr = translator
        self.pubfileids: list[str] = []

        self.setFixedSize(450, 350)

        label = QLabel(self.tr.t("messages.batch_input_placeholder"))
        label.setStyleSheet(f"color: {self.c_text_primary}; background: transparent;")
        label.setWordWrap(True)
        self.content_layout.addWidget(label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(self.tr.t("labels.id_url_placeholder"))
        self.text_edit.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border};
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }}

            QTextEdit:focus {{
                border-color: {self.c_primary};
            }}
            """
        )
        self.content_layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()

        download_btn = QPushButton(self.tr.t("buttons.download_all"))
        download_btn.setFixedHeight(40)
        download_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.c_primary};
                color: {self.c_text_primary};
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: {self.c_primary_hover};
            }}
            """
        )
        download_btn.clicked.connect(self._on_download)

        button_layout.addWidget(download_btn)
        self.content_layout.addLayout(button_layout)

    def get_pubfileids(self) -> list[str]:
        return self.pubfileids

    def _on_download(self) -> None:
        text = self.text_edit.toPlainText().strip()
        if not text:
            return

        tokens = re.split(r"\s+", text.replace("\n", " ").replace("\r", " "))
        seen = set()
        valid_ids: list[str] = []

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            pubfileid = None
            if token.isdigit() and len(token) >= 8:
                pubfileid = token
            else:
                match = re.search(r"[?&]id=(\d{8,})", token)
                if match:
                    pubfileid = match.group(1)

            if pubfileid and pubfileid not in seen:
                valid_ids.append(pubfileid)
                seen.add(pubfileid)

        self.pubfileids = valid_ids

        if valid_ids:
            self.accept()
        else:
            self._show_warning(self.tr.t("dialog.warning"), self.tr.t("messages.invalid_input"))

    def _show_warning(self, title: str, message: str) -> None:
        msg_box = MessageBox(self.theme, title, message, MessageBox.Icon.Warning, self)
        msg_box.exec()