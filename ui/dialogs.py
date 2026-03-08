from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QGraphicsDropShadowEffect, QWidget,
    QComboBox, QLineEdit, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor
from resources.icons import get_icon, get_pixmap
from ui.notifications import MessageBox
import re
from utils.helpers import restart_application

class CustomDialog(QDialog):
    def __init__(self, title: str = "Dialog", parent=None, theme_manager=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._setup_colors()

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.container = QFrame(self)
        self._apply_container_style()

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

        self.old_pos = None

    def _setup_colors(self):
        if self.theme:
            self.c_bg_primary = self.theme.get_color('bg_primary')
            self.c_bg_secondary = self.theme.get_color('bg_secondary')
            self.c_bg_tertiary = self.theme.get_color('bg_tertiary')
            self.c_border = self.theme.get_color('border')
            self.c_border_light = self.theme.get_color('border_light')
            self.c_text_primary = self.theme.get_color('text_primary')
            self.c_text_secondary = self.theme.get_color('text_secondary')
            self.c_primary = self.theme.get_color('primary')
            self.c_primary_hover = self.theme.get_color('primary_hover')
            self.c_accent_red = self.theme.get_color('accent_red')
        else:
            self.c_bg_primary = '#0F111A'
            self.c_bg_secondary = '#1A1D2E'
            self.c_bg_tertiary = '#252938'
            self.c_border = '#2A2F42'
            self.c_border_light = '#3A3F52'
            self.c_text_primary = '#FFFFFF'
            self.c_text_secondary = '#B4B7C3'
            self.c_primary = '#4A7FD9'
            self.c_primary_hover = '#5B8FE9'
            self.c_accent_red = '#EF5B5B'

    def _apply_container_style(self):
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.c_bg_secondary};
                border-radius: 12px;
                border: 2px solid {self.c_border_light};
            }}
        """)

    def _create_title_bar(self, title):
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("QWidget { background: transparent; border: none; }")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 10)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
        font-size: 16px;
        font-weight: 700;
        color: {self.c_text_primary};
        background: transparent;
        """)

        close_btn = QPushButton()
        close_btn.setFixedSize(32, 32)
        close_btn.setIcon(get_icon("ICON_CLOSE"))
        close_btn.setIconSize(QSize(20, 20))
        close_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: 16px;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: rgba(239, 91, 91, 0.2);
        }}
        QPushButton:pressed {{
            background-color: rgba(239, 91, 91, 0.3);
        }}
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

class BatchDownloadDialog(CustomDialog):
    def __init__(self, translator, parent=None, theme_manager=None):
        super().__init__(translator.t("dialog.batch_download"), parent, theme_manager)

        self.tr = translator
        self.pubfileids = []

        self.setFixedSize(450, 350)

        label = QLabel(self.tr.t("messages.batch_input_placeholder"))
        label.setStyleSheet(f"color: {self.c_text_primary}; background: transparent;")
        label.setWordWrap(True)
        self.content_layout.addWidget(label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(self.tr.t("labels.id_url_placeholder"))
        self.text_edit.setStyleSheet(f"""
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
        """)
        self.content_layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()

        download_btn = QPushButton(self.tr.t("buttons.download_all"))
        download_btn.setFixedHeight(40)
        download_btn.setStyleSheet(f"""
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
            self._show_warning(self.tr.t("dialog.warning"), self.tr.t("messages.invalid_input"))

    def _show_warning(self, title, message):
        msg_box = MessageBox(self.theme, title, message, MessageBox.Icon.Warning, self)
        msg_box.exec()

    def get_pubfileids(self):
        return self.pubfileids

class InfoDialog(CustomDialog):
    def __init__(self, translator, parent=None, theme_manager=None):
        super().__init__(translator.t("dialog.about"), parent, theme_manager)

        self.tr = translator
        self.setMinimumSize(400, 280)
        self.adjustSize()

        icon = QLabel()
        icon.setPixmap(get_pixmap("ICON_APP", size=128))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("""
            border: none;
            margin-bottom: -10px;
            margin-top: -10px;
        """)
        self.content_layout.addWidget(icon)

        info_text = QLabel(
            f"{self.tr.t('info.version')}\n\n"
            f"{self.tr.t('info.description')}\n\n"
            f"{self.tr.t('info.developed')}"
        )
        info_text.setStyleSheet(f"""
            color: {self.c_text_primary};
            font-size: 13px;
            background: transparent;
        """)
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
            f'<a href="https://github.com/psyattack/we-workshop-manager" style="color: {self.c_primary}; text-decoration: none;">GitHub</a>')
        github_link.setOpenExternalLinks(True)
        github_link.setStyleSheet("border: none; font-size: 14px; font-weight: bold;")

        github_container.addWidget(github_icon)
        github_container.addWidget(github_link)

        self.content_layout.addLayout(github_container)

        ok_btn = QPushButton(self.tr.t("buttons.ok"))
        ok_btn.setFixedHeight(40)
        ok_btn.setStyleSheet(f"""
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
        """)
        ok_btn.clicked.connect(self.accept)
        self.content_layout.addWidget(ok_btn)

class CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None, expanded: bool = True, theme_manager=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._setup_colors()

        self._is_expanded = expanded
        self._title_text = title

        self.setStyleSheet("background: transparent; border: none;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._header = QPushButton()
        self._header.setCheckable(True)
        self._header.setChecked(expanded)
        self._header.clicked.connect(self._on_toggle)
        self._header.setFixedHeight(38)
        self._update_header_text()
        self._apply_header_style()
        self._main_layout.addWidget(self._header)

        self._content_area = QWidget()
        self._apply_content_style()
        self._content_layout = QVBoxLayout(self._content_area)
        self._content_layout.setContentsMargins(14, 12, 14, 12)
        self._content_layout.setSpacing(10)

        self._main_layout.addWidget(self._content_area)

        self._content_area.setVisible(expanded)

    def _setup_colors(self):
        if self.theme:
            self.c_bg_secondary = self.theme.get_color('bg_secondary')
            self.c_bg_tertiary = self.theme.get_color('bg_tertiary')
            self.c_border = self.theme.get_color('border')
            self.c_border_light = self.theme.get_color('border_light')
            self.c_text_primary = self.theme.get_color('text_primary')
            self.c_text_secondary = self.theme.get_color('text_secondary')
            self.c_primary = self.theme.get_color('primary')
        else:
            self.c_bg_secondary = '#1A1D2E'
            self.c_bg_tertiary = '#252938'
            self.c_border = '#2A2F42'
            self.c_border_light = '#3A3F52'
            self.c_text_primary = '#FFFFFF'
            self.c_text_secondary = '#B4B7C3'
            self.c_primary = '#4A7FD9'

    def _apply_header_style(self):
        self._header.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_secondary};
                border: 1px solid {self.c_border_light};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 700;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.c_bg_secondary};
                border-color: {self.c_primary};
                color: {self.c_text_primary};
            }}
            QPushButton:checked {{
                background-color: {self.c_bg_secondary};
                color: {self.c_text_primary};
                border-color: {self.c_primary};
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)

    def _apply_content_style(self):
        self._content_area.setStyleSheet(f"""
            QWidget {{
                background-color: {self.c_bg_secondary};
                border: 1px solid {self.c_border_light};
                border-top: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """)

    def _update_header_text(self):
        arrow = "▼" if self._is_expanded else "▶"
        self._header.setText(f"  {arrow}  {self._title_text}")

    def _on_toggle(self, checked):
        self._is_expanded = checked
        self._update_header_text()
        self._content_area.setVisible(checked)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)

    def set_expanded(self, expanded: bool):
        self._is_expanded = expanded
        self._header.setChecked(expanded)
        self._update_header_text()
        self._content_area.setVisible(expanded)

class SettingsField(QWidget):
    def __init__(self, label_text: str, control_widget: QWidget, description: str = None,
                 stacked: bool = False, parent=None, theme_manager=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._setup_colors()

        self.setStyleSheet("background: transparent; border: none;")

        if stacked:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)

            if label_text:
                label = QLabel(label_text)
                label.setStyleSheet(f"""
                    font-size: 12px;
                    font-weight: 600;
                    color: {self.c_text_secondary};
                    background: transparent;
                    border: none;
                """)
                layout.addWidget(label)

            if description:
                desc = QLabel(description)
                desc.setWordWrap(True)
                desc.setStyleSheet(f"""
                    font-size: 11px;
                    color: {self.c_text_disabled};
                    background: transparent;
                    border: none;
                    margin-bottom: 2px;
                """)
                layout.addWidget(desc)

            layout.addWidget(control_widget)
        else:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(12)

            left = QVBoxLayout()
            left.setSpacing(2)

            if label_text:
                label = QLabel(label_text)
                label.setStyleSheet(f"""
                    font-size: 12px;
                    font-weight: 600;
                    color: {self.c_text_secondary};
                    background: transparent;
                    border: none;
                """)
                left.addWidget(label)

            if description:
                desc = QLabel(description)
                desc.setWordWrap(True)
                desc.setStyleSheet(f"""
                    font-size: 11px;
                    color: {self.c_text_disabled};
                    background: transparent;
                    border: none;
                """)
                left.addWidget(desc)

            layout.addLayout(left, 1)
            control_widget.setFixedWidth(160)
            layout.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _setup_colors(self):
        if self.theme:
            self.c_text_secondary = self.theme.get_color('text_secondary')
            self.c_text_disabled = self.theme.get_color('text_disabled')
        else:
            self.c_text_secondary = '#B4B7C3'
            self.c_text_disabled = '#6B6E7C'

class SettingsPopup(CustomDialog):
    def __init__(self, config, accounts, translator, theme_manager, main_window, parent=None):
        super().__init__(translator.t("settings.title"), parent, theme_manager)

        self.config = config
        self.accounts = accounts
        self.tr = translator
        self.main_window = main_window

        self.setFixedSize(900, 650)

        self._apply_container_style()
        self._setup_ui()

    def _setup_ui(self):
        self.content_layout.setSpacing(10)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._tab_widget_style())
        self.content_layout.addWidget(self.tab_widget)

        self._create_general_tab()
        self._create_account_tab()
        self._create_advanced_tab()

    def _create_general_tab(self):
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        appearance_section = CollapsibleSection(
            self.tr.t("settings.appearance") if self.tr.t("settings.appearance") != "settings.appearance" else "Appearance",
            expanded=True,
            theme_manager=self.theme
        )

        theme_combo = self._create_theme_combo()
        appearance_section.add_widget(SettingsField(
            self.tr.t("settings.theme_dev"),
            theme_combo,
            description=self.tr.t("settings.theme_description") if self.tr.t("settings.theme_description") != "settings.theme_description" else "Select the visual theme for the application",
            theme_manager=self.theme
        ))

        lang_combo = self._create_language_combo()
        appearance_section.add_widget(SettingsField(
            self.tr.t("settings.language"),
            lang_combo,
            description=self.tr.t("settings.language_description") if self.tr.t("settings.language_description") != "settings.language_description" else "Change interface language (requires restart)",
            theme_manager=self.theme
        ))

        layout.addWidget(appearance_section)

        behavior_section = CollapsibleSection(
            self.tr.t("settings.behavior") if self.tr.t("settings.behavior") != "settings.behavior" else "Behavior",
            expanded=True,
            theme_manager=self.theme
        )

        minimize_combo = self._create_minimize_combo()
        behavior_section.add_widget(SettingsField(
            self.tr.t("labels.minimize_on_apply"),
            minimize_combo,
            description=self.tr.t("settings.minimize_description") if self.tr.t("settings.minimize_description") != "settings.minimize_description" else "Minimize window after applying changes",
            theme_manager=self.theme
        ))

        layout.addWidget(behavior_section)

        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr.t("settings.tab_general") if self.tr.t("settings.tab_general") != "settings.tab_general" else "General")

    def _create_account_tab(self):
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        account_section = CollapsibleSection(
            self.tr.t("settings.account_selection") if self.tr.t("settings.account_selection") != "settings.account_selection" else "Account Selection",
            expanded=True,
            theme_manager=self.theme
        )

        account_combo = self._create_account_combo()
        account_section.add_widget(SettingsField(
            self.tr.t("settings.account"),
            account_combo,
            description=self.tr.t("settings.account_description") if self.tr.t("settings.account_description") != "settings.account_description" else "Select the active Steam account",
            theme_manager=self.theme
        ))

        layout.addWidget(account_section)

        login_section = CollapsibleSection(self.tr.t("settings.steam_login"), expanded=True, theme_manager=self.theme)
        login_widget = self._create_steam_login_section()
        login_section.add_widget(login_widget)

        layout.addWidget(login_section)

        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr.t("settings.tab_account") if self.tr.t("settings.tab_account") != "settings.tab_account" else "Account")

    def _create_advanced_tab(self):
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        notif_section = CollapsibleSection(
            self.tr.t("settings.notifications") if self.tr.t("settings.notifications") != "settings.notifications" else "Notifications",
            expanded=False,
            theme_manager=self.theme
        )

        placeholder3 = QLabel(self.tr.t("settings.coming_soon") if self.tr.t("settings.coming_soon") != "settings.coming_soon" else "More settings coming soon...")
        placeholder3.setStyleSheet(f"""
            color: {self.theme.get_color('text_disabled') if self.theme else '#6B6E7C'};
            font-size: 12px;
            font-style: italic;
            background: transparent;
            border: none;
            padding: 8px;
        """)
        placeholder3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        notif_section.add_widget(placeholder3)

        layout.addWidget(notif_section)

        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr.t("settings.tab_advanced") if self.tr.t("settings.tab_advanced") != "settings.tab_advanced" else "Advanced")

    def _create_scrollable_tab(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {self.c_bg_secondary};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.c_border_light};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.c_primary};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 8, 4, 8)
        inner_layout.setSpacing(12)

        scroll.setWidget(inner)

        scroll._inner_layout = inner_layout
        return scroll

    def _create_account_combo(self):
        combo = QComboBox()
        last_loggin_acc = 1
        for i in range(len(self.accounts.get_accounts()) - last_loggin_acc):
            combo.addItem(f"{self.tr.t('labels.account')} {i + 1}")
        combo.setCurrentIndex(self.config.get_account_number())
        combo.currentIndexChanged.connect(lambda idx: self.config.set_account_number(idx))
        combo.setStyleSheet(self._combo_style())
        return combo

    def _create_theme_combo(self):
        combo = QComboBox()

        self._theme_keys = list(self.theme.THEMES.keys())

        display_names = []
        for key in self._theme_keys:
            tr_key = f"labels.theme_{key}"
            translated = self.tr.t(tr_key)
            if translated == tr_key:
                translated = key.capitalize()
            display_names.append(translated)

        combo.addItems(display_names)

        current = self.config.get_theme()
        if current in self._theme_keys:
            combo.setCurrentIndex(self._theme_keys.index(current))
        else:
            combo.setCurrentIndex(0)

        combo.currentIndexChanged.connect(self._on_theme_changed)
        combo.setStyleSheet(self._combo_style())
        return combo

    def _create_language_combo(self):
        combo = QComboBox()
        languages = list(self.tr.SUPPORTED_LANGUAGES.values())
        combo.addItems(languages)
        
        current_lang = self.config.get_language()
        lang_codes = list(self.tr.SUPPORTED_LANGUAGES.keys())
        current_index = lang_codes.index(current_lang) if current_lang in lang_codes else 0
        combo.setCurrentIndex(current_index)
        combo.currentIndexChanged.connect(self._on_language_changed)
        combo.setStyleSheet(self._combo_style())
        return combo

    def _create_minimize_combo(self):
        combo = QComboBox()
        combo.addItems([self.tr.t("labels.disabled"), self.tr.t("labels.enabled")])
        combo.setCurrentIndex(1 if self.config.get_minimize_on_apply() else 0)
        combo.currentIndexChanged.connect(self._on_minimize_changed)
        combo.setStyleSheet(self._combo_style())
        return combo

    def _create_steam_login_section(self):
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        desc = QLabel(self.tr.t("settings.login_description") if self.tr.t("settings.login_description") != "settings.login_description" else "Enter your Steam credentials to authenticate")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            font-size: 11px;
            color: {self.theme.get_color('text_disabled') if self.theme else '#6B6E7C'};
            background: transparent;
            border: none;
            margin-bottom: 4px;
        """)
        layout.addWidget(desc)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText(self.tr.t("settings.login_placeholder"))
        self.login_input.setStyleSheet(self._input_style())
        layout.addWidget(self.login_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(self.tr.t("settings.password_placeholder"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self._input_style())
        layout.addWidget(self.password_input)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        login_btn = QPushButton(self.tr.t("settings.login_button"))
        login_btn.setFixedHeight(36)
        login_btn.setStyleSheet(self._button_style())
        login_btn.clicked.connect(self._on_login_clicked)

        reset_btn = QPushButton(self.tr.t("settings.reset_button"))
        reset_btn.setFixedHeight(36)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border_light};
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {self.c_primary};
                background-color: {self.c_bg_secondary};
            }}
        """)
        reset_btn.clicked.connect(self._on_reset_clicked)

        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(reset_btn)
        layout.addLayout(btn_layout)

        return container

    def _on_login_clicked(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()

        if not login or not password:
            msg_box = MessageBox(
                self.theme,
                self.tr.t("dialog.warning"),
                self.tr.t("messages.fill_all_fields"),
                MessageBox.Icon.Warning,
                self
            )
            msg_box.exec()
            return

        msg_box = MessageBox(
            self.theme,
            self.tr.t("settings.restart_required"),
            self.tr.t("settings.restart_message"),
            MessageBox.Icon.Question,
            self
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(yes_btn)

        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            self._clear_cookies()
            restart_application(quit_app=True, login=login, password=password)

    def _on_reset_clicked(self):
        msg_box = MessageBox(
            self.theme,
            self.tr.t("settings.reset_button"),
            self.tr.t("settings.reset_success"),
            MessageBox.Icon.Information,
            self
        )
        msg_box.addButton(self.tr.t("buttons.ok"), MessageBox.ButtonRole.AcceptRole)
        msg_box.exec()

        self._clear_cookies()
        restart_application()

    def _clear_cookies(self):
        try:
            if self.main_window and hasattr(self.main_window, 'workshop_tab'):
                workshop_tab = self.main_window.workshop_tab
                if hasattr(workshop_tab, 'parser') and workshop_tab.parser:
                    workshop_tab.parser.clear_cookies()
        except Exception as e:
            print(f"Error clearing cookies: {e}")

    def _on_theme_changed(self, index):
        if 0 <= index < len(self._theme_keys):
            theme = self._theme_keys[index]
        else:
            theme = "dark"

        current_theme = self.config.get_theme()

        if theme == current_theme:
            return

        self.config.set_theme(theme)

        msg_box = MessageBox(
            self.theme,
            self.tr.t("messages.restart_title"),
            self.tr.t("messages.restart_theme_message"),
            MessageBox.Icon.Question,
            self
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            restart_application()

    def _on_language_changed(self, index):
        lang_codes = list(self.tr.SUPPORTED_LANGUAGES.keys())
        lang = lang_codes[index] if index < len(lang_codes) else "en"
        self.config.set_language(lang)
        self.tr.set_language(lang)

        has_downloads = False
        has_extractions = False
        dm = None

        if self.main_window and hasattr(self.main_window, 'dm'):
            dm = self.main_window.dm
            has_downloads = len(dm.downloading) > 0
            has_extractions = len(dm.extracting) > 0

        if has_downloads or has_extractions:
            if has_downloads and has_extractions:
                msg = self.tr.t("messages.restart_with_tasks")
            elif has_downloads:
                msg = self.tr.t("messages.restart_with_downloads_only")
            else:
                msg = self.tr.t("messages.restart_with_extractions_only")
        else:
            msg = self.tr.t("messages.restart_now_question")

        msg_box = MessageBox(
            self.theme,
            self.tr.t("messages.language_changed"),
            msg,
            MessageBox.Icon.Question,
            self
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(yes_btn)

        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            if dm:
                dm.cleanup_all()

            if self.main_window and hasattr(self.main_window, 'workshop_tab'):
                self.main_window.workshop_tab.cleanup()

            restart_application()

    def _on_minimize_changed(self, index):
        value = index == 1
        self.config.set_minimize_on_apply(value)

    def _combo_style(self):
        return f"""
            QComboBox {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            QComboBox:hover {{
                border-color: {self.c_primary};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.c_bg_secondary};
                color: {self.c_text_primary};
                selection-background-color: {self.c_primary};
                border: 2px solid {self.c_border_light};
                border-radius: 6px;
            }}
        """

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {self.c_primary};
            }}
        """

    def _button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.c_primary};
                color: {self.c_text_primary};
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.c_primary_hover};
            }}
        """

    def _tab_widget_style(self):
        return f"""
            QTabBar {{
                background-color: {self.c_bg_secondary};
            }}
            QTabWidget::pane {{
                background-color: transparent;
                border: 1px solid {self.c_border_light};
                border-radius: 8px;
                margin-top: 15px;
            }}
            QTabBar::tab {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_secondary};
                border: 1px solid {self.c_border_light};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 20px;
                margin-right: 2px;
                font-size: 12px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {self.c_bg_secondary};
                color: {self.c_text_primary};
                border-bottom: 2px solid {self.c_primary};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self.c_bg_secondary};
                color: {self.c_text_primary};
            }}
            QTabBar::tab:first {{
                margin-left: 0px;
            }}
        """
