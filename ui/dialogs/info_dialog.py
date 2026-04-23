import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from infrastructure.resources.resource_manager import get_pixmap
from shared.constants import APP_FULL_NAME
from shared.filesystem import get_app_data_dir
from ui.dialogs.base_dialog import BaseDialog


class InfoDialog(BaseDialog):
    def __init__(self, translator, parent=None, theme_manager=None, main_window=None):
        super().__init__(translator.t("dialog.about"), parent, theme_manager, icon="ICON_INFO")
        self.tr = translator
        self.main_window = main_window

        self.setMinimumSize(400, 330)
        self.adjustSize()

        icon = QLabel(self.content_layout.parentWidget())
        icon.setPixmap(get_pixmap("ICON_APP128", size=100))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("border: none; background: none;")
        self.content_layout.addWidget(icon)

        top_text = QLabel(
            f"{APP_FULL_NAME}\n\n"
            f"{self.tr.t('info.description')}",
            self.content_layout.parentWidget()
        )
        top_text.setStyleSheet(
            f"""
            color: {self.c_text_primary};
            font-size: 13px;
            background: transparent;
            border: none;
            """
        )
        top_text.setWordWrap(True)
        top_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(top_text)

        developed_text = self.tr.t('info.developed')
        self._add_developed_label(developed_text)

        github_container = QHBoxLayout()
        github_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_container.setSpacing(8)

        github_icon = QLabel(self.content_layout.parentWidget())
        github_icon.setPixmap(get_pixmap("ICON_GITHUB", size=28))
        github_icon.setStyleSheet("border: none; margin-right: -2px;")

        github_link = QLabel(
            f'<a href="https://github.com/psyattack/we-workshop-manager" '
            f'style="color: {self.c_primary}; text-decoration: none;">GitHub</a>',
            self.content_layout.parentWidget()
        )
        github_link.setOpenExternalLinks(True)
        github_link.setStyleSheet("border: none; font-size: 14px; font-weight: bold;")

        github_container.addWidget(github_icon)
        github_container.addWidget(github_link)
        self.content_layout.addLayout(github_container)

        self._add_links_block(
            author=("psyattack", "https://github.com/psyattack"),
            tools=[
                ("PyQt6", "https://www.riverbankcomputing.com/software/pyqt/"),
                ("DepotDownloader", "https://github.com/SteamRE/DepotDownloader/releases"),
                ("RePKG", "https://github.com/notscuffed/repkg"),
                ("icons8", "https://icons8.com/")
            ]
        )

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.setSpacing(8)

        check_updates_btn = QPushButton(self.tr.t("buttons.check_updates"))
        check_updates_btn.setFixedHeight(38)
        check_updates_btn.setMinimumWidth(175)
        check_updates_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border_light};
                border-radius: 8px;
                font-weight: 600;
                padding: 0px;
            }}
            QPushButton:hover {{
                border-color: {self.c_primary};
                background-color: {self.c_bg_secondary};
            }}
            """
        )
        check_updates_btn.clicked.connect(self._on_check_updates_clicked)
        buttons_layout.addWidget(check_updates_btn)

        open_data_folder_btn = QPushButton(self.tr.t("buttons.open_data_folder"))
        open_data_folder_btn.setFixedHeight(38)
        open_data_folder_btn.setMinimumWidth(175)
        open_data_folder_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border_light};
                border-radius: 8px;
                font-weight: 600;
                padding: 0px;
            }}
            QPushButton:hover {{
                border-color: {self.c_primary};
                background-color: {self.c_bg_secondary};
            }}
            """
        )
        open_data_folder_btn.clicked.connect(self._on_open_data_folder_clicked)
        buttons_layout.addWidget(open_data_folder_btn)

        self.content_layout.addLayout(buttons_layout)

    def _add_links_block(self, author: tuple[str, str], tools: list[tuple[str, str]]) -> None:
        container = QWidget(self.content_layout.parentWidget())
        container.setStyleSheet(
            """
            QWidget {
                background-color: transparent;
                border: none;
            }
            """
        )

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)

        muted_color = self.c_text_secondary if hasattr(self, "c_text_secondary") else "#8a8f98"

        author_name, author_url = author
        author_label = QLabel(
            f'Author: <a href="{author_url}" '
            f'style="color: {muted_color}; text-decoration: underline;">{author_name}</a>',
            container
        )
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_label.setOpenExternalLinks(True)
        author_label.setWordWrap(True)
        author_label.setStyleSheet(
            """
            background: transparent;
            border: none;
            font-size: 12px;
            """
        )
        layout.addWidget(author_label)

        tools_links = ", ".join(
            f'<a href="{url}" style="color: {muted_color}; text-decoration: underline;">{name}</a>'
            for name, url in tools
        )

        tools_label = QLabel(f"Powered by: {tools_links}", container)
        tools_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tools_label.setOpenExternalLinks(True)
        tools_label.setWordWrap(True)
        tools_label.setStyleSheet(
            """
            background: transparent;
            border: none;
            font-size: 12px;
            """
        )
        layout.addWidget(tools_label)

        self.content_layout.addWidget(container)

    def _add_developed_label(self, text: str) -> None:
        label_style = f"""
            color: {self.c_text_primary};
            font-size: 13px;
            background: transparent;
            border: none;
        """

        separator = None
        for sep in ["❤"]:
            if sep in text:
                separator = sep
                break

        if separator is None:
            fallback = QLabel(text, self.content_layout.parentWidget())
            fallback.setStyleSheet(label_style)
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(fallback)
            return

        parts = text.split(separator, 1)

        row_layout = QHBoxLayout()
        row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        before_label = QLabel(parts[0].rstrip(), self.content_layout.parentWidget())
        before_label.setStyleSheet(label_style)
        row_layout.addWidget(before_label)

        heart_icon = QLabel(self.content_layout.parentWidget())
        heart_icon.setPixmap(get_pixmap("ICON_HEART", size=16))
        heart_icon.setStyleSheet("border: none; background: transparent;")
        heart_icon.setFixedSize(16, 16)
        row_layout.addWidget(heart_icon)

        if len(parts) > 1 and parts[1].strip():
            after_label = QLabel(parts[1].lstrip(), self.content_layout.parentWidget())
            after_label.setStyleSheet(label_style)
            row_layout.addWidget(after_label)

        self.content_layout.addLayout(row_layout)

    def _on_check_updates_clicked(self) -> None:
        if self.main_window and hasattr(self.main_window, "check_for_updates"):
            self.main_window.check_for_updates(silent=False)

    def _on_open_data_folder_clicked(self) -> None:
        app_data_path = get_app_data_dir()
        if app_data_path.exists():
            os.startfile(app_data_path)