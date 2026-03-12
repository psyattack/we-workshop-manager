from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QPainter, QPen
from PyQt6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from shared.helpers import restart_application
from ui.dialogs.base_dialog import BaseDialog
from ui.notifications import MessageBox


class AnimatedToggle(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._checked = False
        self._circle_position = 3.0
        self._background_color = QColor(self._get_color("bg_tertiary"))

        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._position_animation = QPropertyAnimation(self, b"circle_position")
        self._position_animation.setDuration(200)
        self._position_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._color_animation = QPropertyAnimation(self, b"background_color")
        self._color_animation.setDuration(200)
        self._color_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def _get_color(self, color_name: str) -> str:
        if self.theme:
            return self.theme.get_color(color_name)

        colors = {
            "bg_tertiary": "#252938",
            "primary": "#4A7FD9",
            "border": "#2A2F42",
        }
        return colors.get(color_name, "#FFFFFF")

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if self._checked == checked:
            return

        self._checked = checked
        self._animate()

    def toggle(self) -> None:
        self._checked = not self._checked
        self._animate()
        self.toggled.emit(self._checked)

    def get_circle_position(self) -> float:
        return self._circle_position

    def set_circle_position(self, position: float) -> None:
        self._circle_position = position
        self.update()

    circle_position = pyqtProperty(float, get_circle_position, set_circle_position)

    def get_background_color(self) -> QColor:
        return self._background_color

    def set_background_color(self, color: QColor) -> None:
        self._background_color = color
        self.update()

    background_color = pyqtProperty(QColor, get_background_color, set_background_color)

    def _animate(self) -> None:
        self._position_animation.stop()
        self._color_animation.stop()

        if self._checked:
            self._position_animation.setStartValue(self._circle_position)
            self._position_animation.setEndValue(self.width() - 21.0)
            self._color_animation.setStartValue(self._background_color)
            self._color_animation.setEndValue(QColor(self._get_color("primary")))
        else:
            self._position_animation.setStartValue(self._circle_position)
            self._position_animation.setEndValue(3.0)
            self._color_animation.setStartValue(self._background_color)
            self._color_animation.setEndValue(QColor(self._get_color("bg_tertiary")))

        self._position_animation.start()
        self._color_animation.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(QColor(self._get_color("border")), 1))
        painter.setBrush(QBrush(self._background_color))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 12, 12)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))

        circle_y = (self.height() - 18) / 2
        painter.drawEllipse(QRectF(self._circle_position, circle_y, 18, 18))


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

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def add_widget(self, widget) -> None:
        self._content_layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._content_layout.addLayout(layout)

    def set_expanded(self, expanded: bool) -> None:
        self._is_expanded = expanded
        self._header.setChecked(expanded)
        self._update_header_text()
        self._content_area.setVisible(expanded)

    def _setup_colors(self) -> None:
        if self.theme:
            self.c_bg_secondary = self.theme.get_color("bg_secondary")
            self.c_bg_tertiary = self.theme.get_color("bg_tertiary")
            self.c_border = self.theme.get_color("border")
            self.c_border_light = self.theme.get_color("border_light")
            self.c_text_primary = self.theme.get_color("text_primary")
            self.c_text_secondary = self.theme.get_color("text_secondary")
            self.c_primary = self.theme.get_color("primary")
        else:
            self.c_bg_secondary = "#1A1D2E"
            self.c_bg_tertiary = "#252938"
            self.c_border = "#2A2F42"
            self.c_border_light = "#3A3F52"
            self.c_text_primary = "#FFFFFF"
            self.c_text_secondary = "#B4B7C3"
            self.c_primary = "#4A7FD9"

    def _apply_header_style(self) -> None:
        self._header.setStyleSheet(
            f"""
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
            """
        )

    def _apply_content_style(self) -> None:
        self._content_area.setStyleSheet(
            f"""
            QWidget {{
                background-color: {self.c_bg_secondary};
                border: 1px solid {self.c_border_light};
                border-top: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            """
        )

    def _update_header_text(self) -> None:
        arrow = "▼" if self._is_expanded else ""
        self._header.setText(f" {arrow} {self._title_text}")

    def _on_toggle(self, checked: bool) -> None:
        self._is_expanded = checked
        self._update_header_text()
        self._content_area.setVisible(checked)


class SettingsField(QWidget):
    def __init__(self, label_text: str, control_widget, description: str = None, stacked: bool = False, parent=None, theme_manager=None):
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
                label.setStyleSheet(
                    f"""
                    font-size: 12px;
                    font-weight: 600;
                    color: {self.c_text_secondary};
                    background: transparent;
                    border: none;
                    """
                )
                layout.addWidget(label)

            if description:
                desc = QLabel(description)
                desc.setWordWrap(True)
                desc.setStyleSheet(
                    f"""
                    font-size: 11px;
                    color: {self.c_text_disabled};
                    background: transparent;
                    border: none;
                    margin-bottom: 2px;
                    """
                )
                layout.addWidget(desc)

            layout.addWidget(control_widget)
            return

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(2)

        if label_text:
            label = QLabel(label_text)
            label.setStyleSheet(
                f"""
                font-size: 12px;
                font-weight: 600;
                color: {self.c_text_secondary};
                background: transparent;
                border: none;
                """
            )
            left.addWidget(label)

        if description:
            desc = QLabel(description)
            desc.setWordWrap(True)
            desc.setStyleSheet(
                f"""
                font-size: 11px;
                color: {self.c_text_disabled};
                background: transparent;
                border: none;
                """
            )
            left.addWidget(desc)

        layout.addLayout(left, 1)

        if isinstance(control_widget, AnimatedToggle):
            layout.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        elif isinstance(control_widget, QComboBox):
            control_widget.setFixedWidth(140)
            control_widget.setFixedHeight(32)
            layout.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            control_widget.setFixedWidth(160)
            layout.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _setup_colors(self) -> None:
        if self.theme:
            self.c_text_secondary = self.theme.get_color("text_secondary")
            self.c_text_disabled = self.theme.get_color("text_disabled")
        else:
            self.c_text_secondary = "#B4B7C3"
            self.c_text_disabled = "#6B6E7C"


class SettingsDialog(BaseDialog):
    def __init__(self, config, accounts, translator, theme_manager, main_window, parent=None):
        super().__init__(translator.t("settings.title"), parent, theme_manager)

        self.config = config
        self.accounts = accounts
        self.tr = translator
        self.main_window = main_window

        self.setFixedSize(900, 650)
        self._apply_container_style()
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.content_layout.setSpacing(10)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._tab_widget_style())
        self.content_layout.addWidget(self.tab_widget)

        self._create_general_tab()
        self._create_account_tab()
        self._create_advanced_tab()

    def _create_general_tab(self) -> None:
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        appearance_section = CollapsibleSection(
            self.tr.t("settings.appearance") if self.tr.t("settings.appearance") != "settings.appearance" else "Appearance",
            expanded=True,
            theme_manager=self.theme,
        )

        theme_combo = self._create_theme_combo()
        appearance_section.add_widget(
            SettingsField(
                self.tr.t("settings.theme_dev"),
                theme_combo,
                description=self.tr.t("settings.theme_description") if self.tr.t("settings.theme_description") != "settings.theme_description" else "Select the visual theme for the application",
                theme_manager=self.theme,
            )
        )

        language_combo = self._create_language_combo()
        appearance_section.add_widget(
            SettingsField(
                self.tr.t("settings.language"),
                language_combo,
                description=self.tr.t("settings.language_description") if self.tr.t("settings.language_description") != "settings.language_description" else "Change interface language (requires restart)",
                theme_manager=self.theme,
            )
        )

        show_id_toggle = self._create_show_id_toggle()
        appearance_section.add_widget(
            SettingsField(
                self.tr.t("settings.show_id_section") if self.tr.t("settings.show_id_section") != "settings.show_id_section" else "Show ID Section",
                show_id_toggle,
                description=self.tr.t("settings.show_id_description") if self.tr.t("settings.show_id_description") != "settings.show_id_description" else "Show or hide the ID section in details panel",
                theme_manager=self.theme,
            )
        )

        layout.addWidget(appearance_section)

        behavior_section = CollapsibleSection(
            self.tr.t("settings.behavior") if self.tr.t("settings.behavior") != "settings.behavior" else "Behavior",
            expanded=True,
            theme_manager=self.theme,
        )

        minimize_toggle = self._create_minimize_toggle()
        behavior_section.add_widget(
            SettingsField(
                self.tr.t("labels.minimize_on_apply"),
                minimize_toggle,
                description=self.tr.t("settings.minimize_description") if self.tr.t("settings.minimize_description") != "settings.minimize_description" else "Minimize window after applying changes",
                theme_manager=self.theme,
            )
        )

        preload_toggle = self._create_preload_toggle()
        behavior_section.add_widget(
            SettingsField(
                self.tr.t("settings.preload_next_page") if self.tr.t("settings.preload_next_page") != "settings.preload_next_page" else "Preload Next Page",
                preload_toggle,
                description=self.tr.t("settings.preload_description") if self.tr.t("settings.preload_description") != "settings.preload_description" else "Preload the next workshop page in background for faster navigation",
                theme_manager=self.theme,
            )
        )

        layout.addWidget(behavior_section)
        layout.addStretch()

        self.tab_widget.addTab(
            tab,
            self.tr.t("settings.tab_general") if self.tr.t("settings.tab_general") != "settings.tab_general" else "General",
        )

    def _create_account_tab(self) -> None:
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        account_section = CollapsibleSection(
            self.tr.t("settings.account_selection") if self.tr.t("settings.account_selection") != "settings.account_selection" else "Account Selection",
            expanded=True,
            theme_manager=self.theme,
        )

        account_combo = self._create_account_combo()
        account_section.add_widget(
            SettingsField(
                self.tr.t("settings.account"),
                account_combo,
                description=self.tr.t("settings.account_description") if self.tr.t("settings.account_description") != "settings.account_description" else "Select the active Steam account",
                theme_manager=self.theme,
            )
        )
        layout.addWidget(account_section)

        login_section = CollapsibleSection(
            self.tr.t("settings.steam_login"),
            expanded=True,
            theme_manager=self.theme,
        )
        login_widget = self._create_steam_login_section()
        login_section.add_widget(login_widget)

        layout.addWidget(login_section)
        layout.addStretch()

        self.tab_widget.addTab(
            tab,
            self.tr.t("settings.tab_account") if self.tr.t("settings.tab_account") != "settings.tab_account" else "Account",
        )

    def _create_advanced_tab(self) -> None:
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        debug_section = CollapsibleSection(
            self.tr.t("settings.debug") if self.tr.t("settings.debug") != "settings.debug" else "Debug",
            expanded=True,
            theme_manager=self.theme,
        )

        debug_toggle = self._create_debug_toggle()
        debug_description = self.tr.t("settings.debug_description") if self.tr.t("settings.debug_description") != "settings.debug_description" else "Enable debug mode for webview testing"

        debug_section.add_widget(
            SettingsField(
                self.tr.t("settings.debug_mode"),
                debug_toggle,
                description=debug_description,
                theme_manager=self.theme,
            )
        )

        layout.addWidget(debug_section)
        layout.addStretch()

        self.tab_widget.addTab(
            tab,
            self.tr.t("settings.tab_advanced") if self.tr.t("settings.tab_advanced") != "settings.tab_advanced" else "Advanced",
        )

    def _create_scrollable_tab(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"""
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
            """
        )

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")

        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 8, 4, 8)
        inner_layout.setSpacing(12)

        scroll.setWidget(inner)
        scroll._inner_layout = inner_layout
        return scroll

    def _create_account_combo(self) -> QComboBox:
        combo = QComboBox()

        last_login_account = 1
        for index in range(len(self.accounts.get_accounts()) - last_login_account):
            combo.addItem(f"{self.tr.t('labels.account')} {index + 1}")

        combo.setCurrentIndex(self.config.get_account_number())
        combo.currentIndexChanged.connect(lambda idx: self.config.set_account_number(idx))
        combo.setStyleSheet(self._combo_style())

        return combo

    def _create_theme_combo(self) -> QComboBox:
        combo = QComboBox()

        self._theme_keys = list(self.theme.get_available_themes())
        display_names = []

        for key in self._theme_keys:
            translation_key = f"labels.theme_{key}"
            translated = self.tr.t(translation_key)
            if translated == translation_key:
                translated = key.capitalize()
            display_names.append(translated)

        combo.addItems(display_names)

        current_theme = self.config.get_theme()
        if current_theme in self._theme_keys:
            combo.setCurrentIndex(self._theme_keys.index(current_theme))
        else:
            combo.setCurrentIndex(0)

        combo.currentIndexChanged.connect(self._on_theme_changed)
        combo.setStyleSheet(self._combo_style())

        return combo

    def _create_language_combo(self) -> QComboBox:
        combo = QComboBox()

        languages = list(self.tr.get_available_languages().values())
        combo.addItems(languages)

        current_language = self.config.get_language()
        language_codes = list(self.tr.get_available_languages().keys())

        current_index = language_codes.index(current_language) if current_language in language_codes else 0
        combo.setCurrentIndex(current_index)
        combo.currentIndexChanged.connect(self._on_language_changed)
        combo.setStyleSheet(self._combo_style())

        return combo

    def _create_steam_login_section(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        desc = QLabel(
            self.tr.t("settings.login_description") if self.tr.t("settings.login_description") != "settings.login_description" else "Enter your Steam credentials to authenticate"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"""
            font-size: 11px;
            color: {self.theme.get_color('text_disabled') if self.theme else '#6B6E7C'};
            background: transparent;
            border: none;
            margin-bottom: 4px;
            """
        )
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

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        login_btn = QPushButton(self.tr.t("settings.login_button"))
        login_btn.setFixedHeight(36)
        login_btn.setStyleSheet(self._button_style())
        login_btn.clicked.connect(self._on_login_clicked)

        reset_btn = QPushButton(self.tr.t("settings.reset_button"))
        reset_btn.setFixedHeight(36)
        reset_btn.setStyleSheet(
            f"""
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
            """
        )
        reset_btn.clicked.connect(self._on_reset_clicked)

        button_layout.addWidget(login_btn)
        button_layout.addWidget(reset_btn)
        layout.addLayout(button_layout)

        return container

    def _create_show_id_toggle(self):
        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_show_id_section())
        toggle.toggled.connect(self._on_show_id_changed)
        return toggle

    def _create_preload_toggle(self):
        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_preload_next_page())
        toggle.toggled.connect(self._on_preload_changed)
        return toggle

    def _create_minimize_toggle(self):
        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_minimize_on_apply())
        toggle.toggled.connect(self._on_minimize_changed)
        return toggle

    def _create_debug_toggle(self):
        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_debug_mode())
        toggle.toggled.connect(self._on_debug_mode_changed)
        return toggle

    def _on_show_id_changed(self, checked: bool) -> None:
        self.config.set_show_id_section(checked)

        if self.main_window:
            if hasattr(self.main_window, "wallpapers_tab") and hasattr(self.main_window.wallpapers_tab, "details_panel"):
                self.main_window.wallpapers_tab.details_panel._update_id_section_visibility()

            if hasattr(self.main_window, "workshop_tab") and hasattr(self.main_window.workshop_tab, "details_panel"):
                self.main_window.workshop_tab.details_panel._update_id_section_visibility()

    def _on_preload_changed(self, checked: bool) -> None:
        self.config.set_preload_next_page(checked)

    def _on_minimize_changed(self, checked: bool) -> None:
        self.config.set_minimize_on_apply(checked)

    def _on_debug_mode_changed(self, checked: bool) -> None:
        current_value = self.config.get_debug_mode()
        if checked == current_value:
            return

        self.config.set_debug_mode(checked)

        msg_box = MessageBox(
            self.theme,
            self.tr.t("messages.restart_title"),
            self.tr.t("messages.restart_debug_message"),
            MessageBox.Icon.Question,
            self,
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            restart_application()

    def _on_login_clicked(self) -> None:
        login = self.login_input.text().strip()
        password = self.password_input.text()

        if not login or not password:
            msg_box = MessageBox(
                self.theme,
                self.tr.t("dialog.warning"),
                self.tr.t("settings.fill_all_fields"),
                MessageBox.Icon.Warning,
                self,
            )
            msg_box.exec()
            return

        msg_box = MessageBox(
            self.theme,
            self.tr.t("messages.restart_title"),
            self.tr.t("settings.restart_message"),
            MessageBox.Icon.Question,
            self,
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(yes_btn)
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            self._clear_cookies()
            restart_application(quit_app=True, login=login, password=password)

    def _on_reset_clicked(self) -> None:
        msg_box = MessageBox(
            self.theme,
            self.tr.t("settings.reset_button"),
            self.tr.t("settings.reset_success"),
            MessageBox.Icon.Information,
            self,
        )
        msg_box.addButton(self.tr.t("buttons.ok"), MessageBox.ButtonRole.AcceptRole)
        msg_box.exec()

        self._clear_cookies()
        restart_application()

    def _clear_cookies(self) -> None:
        try:
            if self.main_window and hasattr(self.main_window, "workshop_tab"):
                workshop_tab = self.main_window.workshop_tab
                if hasattr(workshop_tab, "parser") and workshop_tab.parser:
                    workshop_tab.parser.clear_cookies()
        except Exception:
            pass

    def _on_theme_changed(self, index: int) -> None:
        theme = self._theme_keys[index] if 0 <= index < len(self._theme_keys) else "dark"

        current_theme = self.config.get_theme()
        if theme == current_theme:
            return

        self.config.set_theme(theme)

        msg_box = MessageBox(
            self.theme,
            self.tr.t("messages.restart_title"),
            self.tr.t("messages.restart_theme_message"),
            MessageBox.Icon.Question,
            self,
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            restart_application()

    def _on_language_changed(self, index: int) -> None:
        language_codes = list(self.tr.get_available_languages().keys())
        language = language_codes[index] if index < len(language_codes) else "en"

        self.config.set_language(language)
        self.tr.set_language(language)

        has_downloads = False
        has_extractions = False
        download_service = None

        if self.main_window and hasattr(self.main_window, "dm"):
            download_service = self.main_window.dm
            has_downloads = len(download_service.downloading) > 0
            has_extractions = len(download_service.extracting) > 0

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
            self,
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(yes_btn)
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            if download_service:
                download_service.cleanup_all()

            if self.main_window and hasattr(self.main_window, "workshop_tab"):
                self.main_window.workshop_tab.cleanup()

            restart_application()

    def _combo_style(self) -> str:
        return f"""
        QComboBox {{
            background-color: {self.c_bg_tertiary};
            color: {self.c_text_primary};
            border: 1px solid {self.c_border};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 500;
            min-height: 18px;
        }}

        QComboBox:hover {{
            border-color: {self.c_primary};
            background-color: {self.c_bg_secondary};
        }}

        QComboBox:focus {{
            border-color: {self.c_primary};
        }}

        QComboBox::drop-down {{
            width: 0px;
            border: none;
        }}

        QComboBox::down-arrow {{
            width: 0px;
            height: 0px;
            image: none;
        }}

        QComboBox:on {{
            border-color: {self.c_primary};
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {self.c_bg_tertiary};
            color: {self.c_text_primary};
            selection-background-color: {self.c_primary};
            selection-color: {self.c_text_primary};
            border: 1px solid {self.c_primary};
            border-top: none;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
            padding: 4px;
            outline: none;
        }}

        QComboBox QAbstractItemView::item {{
            padding: 6px 10px;
            border-radius: 4px;
            margin: 2px 4px;
            min-height: 20px;
        }}

        QComboBox QAbstractItemView::item:hover {{
            background-color: {self.c_bg_secondary};
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {self.c_primary};
        }}
        """

    def _input_style(self) -> str:
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

    def _button_style(self) -> str:
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

    def _tab_widget_style(self) -> str:
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