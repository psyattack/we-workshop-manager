import webbrowser

from PyQt6.QtWidgets import QLabel, QPushButton, QTextEdit, QHBoxLayout

from domain.models.update import UpdateCheckResult
from ui.dialogs.base_dialog import BaseDialog


class UpdateDialog(BaseDialog):
    def __init__(self, translator, theme_manager, result: UpdateCheckResult, config_service, parent=None):
        super().__init__("Update Available", parent, theme_manager, icon="ICON_REFRESH")
        self.tr = translator
        self.result = result
        self.config = config_service

        self.setMinimumSize(620, 420)
        self._build_ui()

    def _build_ui(self) -> None:
        release = self.result.release_info

        title = QLabel(f"New version available: v{self.result.latest_version}", self.content_layout.parentWidget())
        title.setStyleSheet(
            f"""
            color: {self.c_text_primary};
            font-size: 18px;
            font-weight: 700;
            background: transparent;
            """
        )
        self.content_layout.addWidget(title)

        current = QLabel(f"Current version: v{self.result.current_version}", self.content_layout.parentWidget())
        current.setStyleSheet(
            f"""
            color: {self.c_text_secondary};
            font-size: 13px;
            background: transparent;
            """
        )
        self.content_layout.addWidget(current)

        changelog_label = QLabel("Changelog", self.content_layout.parentWidget())
        changelog_label.setStyleSheet(
            f"""
            color: {self.c_text_primary};
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            margin-top: 8px;
            """
        )
        self.content_layout.addWidget(changelog_label)

        changelog = QTextEdit(self.content_layout.parentWidget())
        changelog.setReadOnly(True)
        changelog.setPlainText(release.body if release else "")
        changelog.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border};
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }}
            """
        )
        self.content_layout.addWidget(changelog)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        skip_btn = QPushButton("Skip this version", self.content_layout.parentWidget())
        skip_btn.setFixedHeight(38)
        skip_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border_light};
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {self.c_primary};
            }}
            """
        )
        skip_btn.clicked.connect(self._skip_version)

        later_btn = QPushButton("Later", self.content_layout.parentWidget())
        later_btn.setFixedHeight(38)
        later_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border_light};
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {self.c_primary};
            }}
            """
        )
        later_btn.clicked.connect(self.reject)

        download_btn = QPushButton("Download", self.content_layout.parentWidget())
        download_btn.setFixedHeight(38)
        download_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.c_primary};
                color: {self.c_text_primary};
                border: none;
                border-radius: 8px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {self.c_primary_hover};
            }}
            """
        )
        download_btn.clicked.connect(self._download)

        buttons_layout.addWidget(skip_btn)
        buttons_layout.addWidget(later_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(download_btn)

        self.content_layout.addLayout(buttons_layout)

    def _skip_version(self) -> None:
        if self.result.release_info:
            self.config.set_skip_version(self.result.release_info.version)
        self.accept()

    def _download(self) -> None:
        if self.result.release_info and self.result.release_info.download_url:
            webbrowser.open(self.result.release_info.download_url)
        self.accept()