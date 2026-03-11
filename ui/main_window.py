from pathlib import Path
from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QTimer, QPropertyAnimation,
    QEasingCurve, pyqtProperty
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QApplication,
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from ui.notifications import MessageBox
from ui.workshop_tab import WorkshopTab
from ui.wallpapers_tab import WallpapersTab
from ui.dialogs import BatchDownloadDialog, InfoDialog, SettingsPopup
from resources.icons import get_icon
from utils.helpers import clear_cache_if_needed

class AnimatedIconButton(QPushButton):

    def __init__(self, icon_name: str, text: str = "", parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._label_text = text
        self._icon_scale = 1.0
        self._bg_opacity = 0.0
        self._is_active = False

        self.setIcon(get_icon(icon_name))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._scale_anim = QPropertyAnimation(self, b"icon_scale")
        self._scale_anim.setDuration(200)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self._bg_anim = QPropertyAnimation(self, b"bg_opacity")
        self._bg_anim.setDuration(250)
        self._bg_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def get_icon_scale(self):
        return self._icon_scale

    def set_icon_scale(self, value):
        self._icon_scale = value
        base = 22
        scaled = int(base * value)
        self.setIconSize(QSize(scaled, scaled))

    icon_scale = pyqtProperty(float, get_icon_scale, set_icon_scale)

    def get_bg_opacity(self):
        return self._bg_opacity

    def set_bg_opacity(self, value):
        self._bg_opacity = value
        self.update()

    bg_opacity = pyqtProperty(float, get_bg_opacity, set_bg_opacity)

    def set_active(self, active: bool):
        self._is_active = active

        self._bg_anim.stop()
        self._bg_anim.setStartValue(self._bg_opacity)
        self._bg_anim.setEndValue(1.0 if active else 0.0)
        self._bg_anim.start()

        if active:
            self._bounce_icon()

    def _bounce_icon(self):
        self._scale_anim.stop()
        self._scale_anim.setStartValue(0.7)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.setDuration(350)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._scale_anim.start()

    def enterEvent(self, event):
        if not self._is_active:
            self._scale_anim.stop()
            self._scale_anim.setStartValue(self._icon_scale)
            self._scale_anim.setEndValue(1.15)
            self._scale_anim.setDuration(200)
            self._scale_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._scale_anim.start()

            self._bg_anim.stop()
            self._bg_anim.setStartValue(self._bg_opacity)
            self._bg_anim.setEndValue(0.4)
            self._bg_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._is_active:
            self._scale_anim.stop()
            self._scale_anim.setStartValue(self._icon_scale)
            self._scale_anim.setEndValue(1.0)
            self._scale_anim.setDuration(200)
            self._scale_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._scale_anim.start()

            self._bg_anim.stop()
            self._bg_anim.setStartValue(self._bg_opacity)
            self._bg_anim.setEndValue(0.0)
            self._bg_anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._icon_scale)
        self._scale_anim.setEndValue(0.8)
        self._scale_anim.setDuration(100)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scale_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._icon_scale)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.setDuration(250)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._scale_anim.start()
        super().mouseReleaseEvent(event)

class SideNavBar(QWidget):
    currentChanged = pyqtSignal(int)

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._current_index = 0
        self._nav_buttons: list[AnimatedIconButton] = []
        self._action_buttons: list[AnimatedIconButton] = []

        self.setFixedWidth(68)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 12, 0, 12)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._nav_container = QVBoxLayout()
        self._nav_container.setSpacing(0)
        self._nav_container.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._nav_container)

        self._layout.addStretch(1)

        sep_container = QWidget()
        sep_container.setStyleSheet("background: transparent;")
        sep_layout = QHBoxLayout(sep_container)
        sep_layout.setContentsMargins(14, 6, 14, 6)
        self._sep_line = QFrame()
        self._sep_line.setFixedHeight(1)
        sep_layout.addWidget(self._sep_line)
        self._layout.addWidget(sep_container)

        self._actions_container = QVBoxLayout()
        self._actions_container.setSpacing(0)
        self._actions_container.setContentsMargins(0, 4, 0, 4)
        self._layout.addLayout(self._actions_container)

        self._apply_styles()

    def _apply_styles(self):
        bg = self.theme.get_color('bg_secondary')
        border = self.theme.get_color('border')

        self.setStyleSheet(f"""
            SideNavBar {{
                background-color: {bg};
            }}
        """)
        self._sep_line.setStyleSheet(f"background-color: {border};")

    def addNavTab(self, icon_name: str, tooltip: str):
        index = len(self._nav_buttons)
        btn = AnimatedIconButton(icon_name, tooltip)
        btn.setToolTip(tooltip)
        btn.setFixedSize(42, 42)
        btn.setIconSize(QSize(22, 22))

        btn.clicked.connect(lambda checked, i=index: self._on_nav_clicked(i))
        self._apply_nav_button_style(btn, index == self._current_index)

        if index == self._current_index:
            btn.set_active(True)

        self._nav_buttons.append(btn)

        wrapper = QWidget()
        wrapper.setFixedSize(68, 58)
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(13, 8, 13, 8)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrapper_layout.addWidget(btn)
        self._nav_container.addWidget(wrapper)

    def addActionButton(self, icon_name: str, tooltip: str, callback):
        btn = AnimatedIconButton(icon_name, tooltip)
        btn.setToolTip(tooltip)
        btn.setFixedSize(42, 42)
        btn.setIconSize(QSize(22, 22))
        btn.clicked.connect(callback)
        self._apply_action_button_style(btn)

        self._action_buttons.append(btn)

        wrapper = QWidget()
        wrapper.setFixedSize(68, 48)
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(10, 6, 10, 6)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrapper_layout.addWidget(btn)
        self._actions_container.addWidget(wrapper)

        return btn

    def _on_nav_clicked(self, index: int):
        if index != self._current_index:
            self.setCurrentIndex(index)

    def setCurrentIndex(self, index: int):
        if 0 <= index < len(self._nav_buttons):
            old_index = self._current_index
            self._current_index = index

            for i, btn in enumerate(self._nav_buttons):
                is_active = (i == index)
                btn.set_active(is_active)
                self._apply_nav_button_style(btn, is_active)

            if old_index != index:
                self.currentChanged.emit(index)

    def currentIndex(self) -> int:
        return self._current_index

    def _apply_nav_button_style(self, btn: AnimatedIconButton, is_active: bool):
        primary = self.theme.get_color('primary')
        bg_tertiary = self.theme.get_color('bg_tertiary')
        text_primary = self.theme.get_color('text_primary')
        border = self.theme.get_color('border')

        if is_active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary};
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {self._lighten_color(primary)};
                }}
                QToolTip {{
                    background-color: {self.theme.get_color('bg_primary')};
                    color: {text_primary};
                    border: 1px solid {border};
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 12px;
                }}
            """)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(18)
            shadow.setColor(QColor(primary))
            shadow.setOffset(0, 0)
            btn.setGraphicsEffect(shadow)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {bg_tertiary};
                }}
                QToolTip {{
                    background-color: {self.theme.get_color('bg_primary')};
                    color: {text_primary};
                    border: 1px solid {border};
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 12px;
                }}
            """)
            btn.setGraphicsEffect(None)

    def _apply_action_button_style(self, btn: AnimatedIconButton):
        bg_tertiary = self.theme.get_color('bg_tertiary')
        text_primary = self.theme.get_color('text_primary')
        border = self.theme.get_color('border')

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {bg_tertiary};
            }}
            QPushButton:pressed {{
                background-color: {border};
            }}
            QToolTip {{
                background-color: {self.theme.get_color('bg_primary')};
                color: {text_primary};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
        """)

    def _lighten_color(self, hex_color):
        color = QColor(hex_color)
        h, s, v, a = color.getHsv()
        color.setHsv(h, max(0, s - 25), min(255, v + 30), a)
        return color.name()

    def update_theme(self):
        self._apply_styles()
        for i, btn in enumerate(self._nav_buttons):
            self._apply_nav_button_style(btn, i == self._current_index)
        for btn in self._action_buttons:
            self._apply_action_button_style(btn)

class ContentSwitcher(QStackedWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fade_duration = 200
        self._animation_running = False

    def setCurrentIndex(self, index: int):
        if index == self.currentIndex() or self._animation_running:
            return

        current_widget = self.currentWidget()
        next_widget = self.widget(index)

        if current_widget is None or next_widget is None:
            super().setCurrentIndex(index)
            return

        self._animation_running = True

        fade_out_effect = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(fade_out_effect)

        fade_out = QPropertyAnimation(fade_out_effect, b"opacity")
        fade_out.setDuration(self._fade_duration // 2)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        def on_fade_out_finished():
            current_widget.setGraphicsEffect(None)
            super(ContentSwitcher, self).setCurrentIndex(index)

            fade_in_effect = QGraphicsOpacityEffect(next_widget)
            next_widget.setGraphicsEffect(fade_in_effect)

            fade_in = QPropertyAnimation(fade_in_effect, b"opacity")
            fade_in.setDuration(self._fade_duration // 2)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.InCubic)

            def on_fade_in_finished():
                next_widget.setGraphicsEffect(None)
                self._animation_running = False

            fade_in.finished.connect(on_fade_in_finished)
            self._current_fade_in = fade_in
            self._current_fade_in_effect = fade_in_effect
            fade_in.start()

        fade_out.finished.connect(on_fade_out_finished)
        self._current_fade_out = fade_out
        self._current_fade_out_effect = fade_out_effect
        fade_out.start()

class MainWindow(QMainWindow):
    download_completed = pyqtSignal(str)

    def __init__(self, config_manager, account_manager, download_manager,
                 wallpaper_engine, translator, theme_manager):
        super().__init__()

        self.config = config_manager
        self.accounts = account_manager
        self.dm = download_manager
        self.we = wallpaper_engine
        self.tr = translator
        self.theme = theme_manager

        self._is_maximized = False
        self.old_pos = None

        self._apply_theme()
        self._setup_ui()

        self.dm.download_completed.connect(self._on_download_completed_signal)

    def _on_download_completed_signal(self, pubfileid: str, success: bool):
        if success:
            QTimer.singleShot(300, self.refresh_wallpapers)

    def refresh_wallpapers(self):
        if hasattr(self, 'wallpapers_tab'):
            self.wallpapers_tab.refresh()

    def _apply_theme(self):
        theme_name = self.config.get_theme()
        self.theme.set_theme(theme_name, QApplication.instance())

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

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = self._create_title_bar()
        root_layout.addWidget(self.title_bar)

        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.side_nav = self._create_side_nav()
        body_layout.addWidget(self.side_nav)

        divider_container = QWidget()
        divider_container.setFixedWidth(1)
        divider_container.setStyleSheet("background: transparent;")
        divider_layout = QVBoxLayout(divider_container)
        divider_layout.setContentsMargins(0, 12, 0, 12)
        divider_layout.setSpacing(0)
        self._nav_divider = QFrame()
        self._nav_divider.setFixedWidth(1)
        self._nav_divider.setStyleSheet(
            f"background-color: {self.theme.get_color('border')};"
        )
        divider_layout.addWidget(self._nav_divider)
        body_layout.addWidget(divider_container)

        self._create_tabs()
        body_layout.addWidget(self.stack, 1)

        root_layout.addLayout(body_layout, 1)

        self._create_corner_covers()

    def _create_title_bar(self) -> QFrame:
        title_bar = QFrame()
        title_bar.setFixedHeight(52)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme.get_color('bg_secondary')},
                    stop:1 {self.theme.get_color('bg_primary')});
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom: 1px solid {self.theme.get_color('border')};
            }}
        """)

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 0, 10, 0)
        layout.setSpacing(12)

        app_name = QLabel("WE Workshop Manager")
        app_name.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 700;
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            letter-spacing: 0.5px;
            border: none;
        """)
        layout.addWidget(app_name)

        layout.addStretch()

        window_btns_layout = QHBoxLayout()
        window_btns_layout.setSpacing(2)

        min_btn = self._create_window_button('minimize', self.showMinimized)
        self.max_btn = self._create_window_button('maximize', self._toggle_maximize)
        close_btn = self._create_window_button('close', self._on_close)

        window_btns_layout.addWidget(min_btn)
        window_btns_layout.addWidget(self.max_btn)
        window_btns_layout.addWidget(close_btn)

        layout.addLayout(window_btns_layout)

        return title_bar

    def _create_side_nav(self) -> SideNavBar:
        nav = SideNavBar(self.theme, self)

        nav.addNavTab("ICON_WORKSHOP", self.tr.t("tabs.workshop"))
        nav.addNavTab("ICON_WALLPAPER", self.tr.t("tabs.wallpapers"))

        self.downloads_btn = nav.addActionButton(
            "ICON_TASK",
            self.tr.t("tooltips.tasks"),
            self._toggle_downloads_popup
        )
        self.batch_btn = nav.addActionButton(
            "ICON_UPLOAD",
            self.tr.t("tooltips.batch_download"),
            self._show_batch_download
        )
        self.settings_btn = nav.addActionButton(
            "ICON_USER_SETTINGS",
            self.tr.t("tooltips.settings"),
            self._show_settings
        )
        self.info_btn = nav.addActionButton(
            "ICON_INFO",
            self.tr.t("tooltips.info"),
            self._show_info
        )

        return nav

    def _create_tabs(self):
        self.stack = ContentSwitcher()
        self.stack.setStyleSheet("border: none; background: transparent;")

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

        self.side_nav.currentChanged.connect(self.stack.setCurrentIndex)

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

    def _create_window_button(self, button_type: str, callback):
        btn = QPushButton()
        btn.setFixedSize(38, 38)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        icon_map = {
            'minimize': "ICON_MINIMIZE",
            'maximize': "ICON_MAXIMIZE",
            'restore': "ICON_RESTORE",
            'close': "ICON_CLOSE"
        }

        btn.setIcon(get_icon(icon_map.get(button_type, "ICON_CLOSE")))
        btn.setIconSize(QSize(16, 16))

        hover_color = self.theme.get_color('overlay_light')

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        btn.clicked.connect(callback)

        return btn

    def _toggle_downloads_popup(self):
        if self.workshop_tab.downloads_dialog.isVisible():
            self.workshop_tab.hide_downloads_popup()
        else:
            btn_pos = self.downloads_btn.mapToGlobal(
                self.downloads_btn.rect().topRight()
            )
            self.workshop_tab.show_downloads_popup(btn_pos)

    def _show_settings(self):
        self.settings_popup = SettingsPopup(
            self.config, self.accounts, self.tr, self.theme, self, self
        )
        self.settings_popup.exec()

    def _show_batch_download(self):
        dialog = BatchDownloadDialog(self.tr, self, self.theme)
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
        dialog = InfoDialog(self.tr, self, self.theme)
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

            reply = MessageBox.question(
                self,
                self.tr.t("dialog.exit"),
                msg
            )

            if reply != MessageBox.StandardButton.Yes:
                return

        self.dm.cleanup_all()

        if hasattr(self, 'workshop_tab'):
            self.workshop_tab.cleanup()

        clear_cache_if_needed(Path("cookies/Cache"), 200)

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
