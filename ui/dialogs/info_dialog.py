from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton

from infrastructure.resources.resource_manager import get_pixmap
from shared.constants import APP_FULL_NAME
from ui.dialogs.base_dialog import BaseDialog


class InfoDialog(BaseDialog):
    def __init__(self, translator, parent=None, theme_manager=None):
        super().__init__(translator.t("dialog.about"), parent, theme_manager)

        self.tr = translator

        self.setMinimumSize(400, 280)
        self.adjustSize()

        icon = QLabel()
        icon.setPixmap(get_pixmap("ICON_APP", size=96))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("border: none; background: none;")
        self.content_layout.addWidget(icon)

        info_text = QLabel(
            f"{APP_FULL_NAME}\n\n"
            f"{self.tr.t('info.description')}\n\n"
            f"{self.tr.t('info.developed')}"
        )
        info_text.setStyleSheet(
            f"""
            color: {self.c_text_primary};
            font-size: 13px;
            background: transparent;
            """
        )
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(info_text)

        github_container = QHBoxLayout()
        github_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_container.setSpacing(8)

        github_icon = QLabel()
        github_icon.setPixmap(get_pixmap("ICON_GITHUB", size=34))
        github_icon.setStyleSheet("border: none; margin-right: -5px;")

        github_link = QLabel(
            f'<a href="https://github.com/psyattack/we-workshop-manager" '
            f'style="color: {self.c_primary}; text-decoration: none;">GitHub</a>'
        )
        github_link.setOpenExternalLinks(True)
        github_link.setStyleSheet("border: none; font-size: 14px; font-weight: bold;")

        github_container.addWidget(github_icon)
        github_container.addWidget(github_link)
        self.content_layout.addLayout(github_container)

        ok_btn = QPushButton(self.tr.t("buttons.ok"))
        ok_btn.setFixedHeight(40)
        ok_btn.setStyleSheet(
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
        ok_btn.clicked.connect(self.accept)
        self.content_layout.addWidget(ok_btn)