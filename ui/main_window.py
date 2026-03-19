from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    pyqtProperty,
    pyqtSignal,
    QTimer,
    QRect,
    QEvent,
    QRectF,
    QVariantAnimation,
    QParallelAnimationGroup,
)
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.background_widget import BackgroundImageWidget
from infrastructure.resources.resource_manager import get_icon
from shared.constants import APP_NAME
from shared.filesystem import clear_cache_if_needed, get_app_data_dir
from ui.dialogs.multi_download_dialog import BatchDownloadDialog
from ui.dialogs.info_dialog import InfoDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.notifications import MessageBox
from ui.tabs.wallpapers_tab import WallpapersTab
from ui.tabs.workshop_tab import WorkshopTab
from ui.dialogs.update_dialog import UpdateDialog
from ui.widgets.update_checker import UpdateCheckWorker
from ui.widgets.custom_tooltip import install_tooltip


class AnimatedIconButton(QPushButton):
    def __init__(self, icon_name: str, tooltip_text: str = "", theme_manager=None, parent=None):
        QPushButton.__init__(self, parent)
        self._icon_name = icon_name
        self._tooltip_text = tooltip_text or icon_name
        self._icon_scale = 1.0
        self._bg_opacity = 0.0
        self._is_active = False

        self.setIcon(get_icon(icon_name))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if self._tooltip_text and theme_manager:
            install_tooltip(self, self._tooltip_text, "right", theme_manager)

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

    def set_active(self, active: bool) -> None:
        self._is_active = active
        self._bg_anim.stop()
        self._bg_anim.setStartValue(self._bg_opacity)
        self._bg_anim.setEndValue(1.0 if active else 0.0)
        self._bg_anim.start()

        if active:
            self._bounce_icon()

    def _bounce_icon(self) -> None:
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
        self._layout.setContentsMargins(0, 0, 0, 12)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._top_separator_wrap = QWidget()
        self._top_separator_wrap.setFixedHeight(16)
        self._top_separator_wrap.setStyleSheet("background: transparent;")

        self._top_separator_layout = QHBoxLayout(self._top_separator_wrap)
        self._top_separator_layout.setContentsMargins(0, 6, 0, 0)
        self._top_separator_layout.setSpacing(0)
        self._top_separator_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self._top_separator = QFrame()
        self._top_separator.setFixedSize(40, 1)
        self._top_separator.setStyleSheet(
            f"background-color: {self.theme.get_color('border')}; border: none;"
        )
        self._top_separator_layout.addWidget(self._top_separator)
        self._layout.addWidget(self._top_separator_wrap)

        self._nav_container = QVBoxLayout()
        self._nav_container.setSpacing(0)
        self._nav_container.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._nav_container)

        self._actions_container = QVBoxLayout()
        self._actions_container.setSpacing(0)
        self._actions_container.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._actions_container)

        self._apply_styles()

    def addNavTab(self, icon_name: str, tooltip: str):
        tooltip = tooltip or icon_name
        index = len(self._nav_buttons)
        button = AnimatedIconButton(icon_name, tooltip, self.theme, self)
        button.setFixedSize(42, 42)
        button.setIconSize(QSize(22, 22))
        button.clicked.connect(lambda checked=False, i=index: self._on_nav_clicked(i))

        self._apply_nav_button_style(button, index == self._current_index)
        if index == self._current_index:
            button.set_active(True)

        self._nav_buttons.append(button)

        wrapper = QWidget()
        wrapper.setFixedSize(68, 58)
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(13, 8, 13, 8)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrapper_layout.addWidget(button)

        self._nav_container.addWidget(wrapper)

    def addActionButton(self, icon_name: str, tooltip: str, callback):
        tooltip = tooltip or icon_name
        button = AnimatedIconButton(icon_name, tooltip, self.theme, self)
        button.setFixedSize(42, 42)
        button.setIconSize(QSize(22, 22))
        button.clicked.connect(callback)
        self._apply_action_button_style(button)
        self._action_buttons.append(button)

        wrapper = QWidget()
        wrapper.setFixedSize(68, 48)
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(10, 0, 10, 6)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrapper_layout.addWidget(button)

        self._actions_container.addWidget(wrapper)
        return button

    def setCurrentIndex(self, index: int) -> None:
        if not (0 <= index < len(self._nav_buttons)):
            return

        old_index = self._current_index
        self._current_index = index

        for i, button in enumerate(self._nav_buttons):
            is_active = i == index
            button.set_active(is_active)
            self._apply_nav_button_style(button, is_active)

        if old_index != index:
            self.currentChanged.emit(index)

    def currentIndex(self) -> int:
        return self._current_index

    def update_theme(self) -> None:
        self._apply_styles()
        for i, button in enumerate(self._nav_buttons):
            self._apply_nav_button_style(button, i == self._current_index)
        for button in self._action_buttons:
            self._apply_action_button_style(button)

    def _on_nav_clicked(self, index: int) -> None:
        if index != self._current_index:
            self.setCurrentIndex(index)

    def _apply_styles(self) -> None:
        background = self.theme.get_color("bg_secondary")
        border = self.theme.get_color("border")
        self.setStyleSheet(
            f"""
            SideNavBar {{
                background-color: {background};
            }}
            QToolTip {{
                background-color: {self.theme.get_color('bg_primary')};
                color: {self.theme.get_color('text_primary')};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            """
        )

    def _apply_nav_button_style(self, button: AnimatedIconButton, is_active: bool) -> None:
        primary = self.theme.get_color("primary")
        bg_tertiary = self.theme.get_color("bg_tertiary")

        if is_active:
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {primary};
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {self._lighten_color(primary)};
                }}
                """
            )
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(18)
            shadow.setColor(QColor(primary))
            shadow.setOffset(0, 0)
            button.setGraphicsEffect(shadow)
        else:
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {bg_tertiary};
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {primary};
                }}
                """
            )
            button.setGraphicsEffect(None)

    def _apply_action_button_style(self, button: AnimatedIconButton) -> None:
        bg_tertiary = self.theme.get_color("bg_tertiary")
        border = self.theme.get_color("border")
        button.setStyleSheet(
            f"""
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
            """
        )

    def _lighten_color(self, hex_color: str) -> str:
        color = QColor(hex_color)
        h, s, v, a = color.getHsv()
        color.setHsv(h, max(0, s - 25), min(255, v + 30), a)
        return color.name()


class SegmentedTabButton(QPushButton):
    def __init__(self, text: str, theme_manager, parent=None):
        super().__init__(text, parent)
        self.theme = theme_manager
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFlat(True)
        self.setMinimumWidth(56)
        self.setFixedHeight(20)
        self._apply_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()

    def _apply_style(self) -> None:
        text_active = self.theme.get_color("text_primary")
        text_inactive = self.theme.get_color("text_secondary")
        color = text_active if self._active else text_inactive
        weight = "700" if self._active else "500"

        self.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {color};
                font-size: 11px;
                font-weight: {weight};
                padding: 0 10px;
                border-radius: 999px;
            }}
            QPushButton:hover {{
                background: transparent;
            }}
            """
        )


class AnimatedSegmentedTabs(QWidget):
    currentChanged = pyqtSignal(int)

    def __init__(self, labels: list[str], theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._labels = labels
        self._buttons: list[SegmentedTabButton] = []
        self._current_index = 0

        self._indicator_pos = 0.0
        self._indicator_stretch = 0.0

        self._pos_anim = QVariantAnimation(self)
        self._pos_anim.setDuration(260)
        self._pos_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._pos_anim.valueChanged.connect(self._on_pos_changed)

        self._stretch_anim = QVariantAnimation(self)
        self._stretch_anim.setDuration(260)
        self._stretch_anim.setKeyValueAt(0.0, 0.0)
        self._stretch_anim.setKeyValueAt(0.35, 10.0)
        self._stretch_anim.setKeyValueAt(0.7, 6.0)
        self._stretch_anim.setKeyValueAt(1.0, 0.0)
        self._stretch_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._stretch_anim.valueChanged.connect(self._on_stretch_changed)

        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(self._pos_anim)
        self._anim_group.addAnimation(self._stretch_anim)

        self.setFixedHeight(28)
        self.setMinimumWidth(146)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(3, 3, 3, 3)
        self._layout.setSpacing(0)

        for index, text in enumerate(labels):
            button = SegmentedTabButton(text, self.theme, self)
            button.clicked.connect(lambda checked=False, i=index: self.setCurrentIndex(i))
            self._buttons.append(button)
            self._layout.addWidget(button)

        self._apply_button_states()

    def _on_pos_changed(self, value):
        self._indicator_pos = float(value)
        self.update()

    def _on_stretch_changed(self, value):
        self._indicator_stretch = float(value)
        self.update()

    def currentIndex(self) -> int:
        return self._current_index

    def setCurrentIndex(self, index: int) -> None:
        if not (0 <= index < len(self._buttons)):
            return
        if index == self._current_index:
            return

        start_index = self._current_index
        self._current_index = index
        self._apply_button_states()

        self._pos_anim.stop()
        self._stretch_anim.stop()
        self._anim_group.stop()

        self._pos_anim.setStartValue(float(start_index))
        self._pos_anim.setEndValue(float(index))

        self._stretch_anim.setStartValue(0.0)
        self._stretch_anim.setEndValue(0.0)

        self._anim_group.start()
        self.currentChanged.emit(index)

    def update_labels(self, labels: list[str]) -> None:
        self._labels = labels
        for i, button in enumerate(self._buttons):
            if i < len(labels):
                button.setText(labels[i])
        self.update()

    def _apply_button_states(self) -> None:
        for i, button in enumerate(self._buttons):
            button.set_active(i == self._current_index)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer_rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        border_color = QColor(self.theme.get_color("border_light"))
        bg_color = QColor(self.theme.get_color("bg_secondary"))
        bg_color.setAlpha(40)

        painter.setPen(QPen(border_color, 1))
        painter.setBrush(bg_color)
        radius = outer_rect.height() / 2.0
        painter.drawRoundedRect(outer_rect, radius, radius)

        if not self._buttons:
            return

        first_geo = self._buttons[0].geometry()
        segment_width = first_geo.width()
        if len(self._buttons) > 1:
            segment_width = self._buttons[1].geometry().x() - first_geo.x()

        base_x = first_geo.x() + (segment_width * self._indicator_pos)

        extra = self._indicator_stretch
        indicator_rect = QRectF(
            base_x + 1.5 - (extra / 2.0),
            4.0,
            segment_width - 3.0 + extra,
            self.height() - 8.0,
        )

        left_limit = 2.0
        right_limit = self.width() - 2.0
        if indicator_rect.left() < left_limit:
            indicator_rect.setLeft(left_limit)
        if indicator_rect.right() > right_limit:
            indicator_rect.setRight(right_limit)

        accent = QColor(self.theme.get_color("primary"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        pill_radius = indicator_rect.height() / 2.0
        painter.drawRoundedRect(indicator_rect, pill_radius, pill_radius)


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
    RESIZE_MARGIN = 8

    def __init__(
        self,
        config_service,
        account_service,
        download_service,
        wallpaper_engine_client,
        translation_service,
        theme_service,
        metadata_service=None,
    ):
        super().__init__()
        self.config = config_service
        self.accounts = account_service
        self.dm = download_service
        self.we = wallpaper_engine_client
        self.tr = translation_service
        self.theme = theme_service
        self.metadata_service = metadata_service

        self._is_maximized = False
        self._pseudo_fullscreen = False
        self._normal_geometry_before_fullscreen: QRect | None = None
        self._geometry_anim: QPropertyAnimation | None = None
        self._minimize_pos_anim: QPropertyAnimation | None = None
        self._was_minimized_animated = False
        self._pre_minimize_geometry: QRect | None = None
        self._restoring_from_minimize = False
        self._restoring_startup_state = False
        self.old_pos = None
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self._drag_restore_pending = False
        self._drag_cursor_offset = QPoint()

        self._apply_theme()
        self._setup_ui()
        self._load_window_geometry()

        self.dm.download_completed.connect(self._on_download_completed_signal)

        self.setMouseTracking(True)
        self.centralWidget().setMouseTracking(True)

        self._update_worker = None
        QTimer.singleShot(1800, self._auto_check_updates)

    def _apply_theme(self) -> None:
        theme_name = self.config.get_theme()
        self.theme.apply_theme(theme_name, QApplication.instance())

    def _setup_ui(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 730)
        self.setMinimumSize(1025, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget()
        central_widget.setObjectName("mainCentralWidget")
        self.setCentralWidget(central_widget)

        self._main_bg = BackgroundImageWidget(central_widget, border_radius=16)
        self._main_bg.set_base_color(self.theme.get_color("bg_primary"))

        central_widget.setStyleSheet("""
            #mainCentralWidget {
                background-color: transparent;
                border-radius: 16px;
            }
        """)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = self._create_title_bar()
        self.title_bar.installEventFilter(self)
        root_layout.addWidget(self.title_bar)

        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.side_nav = self._create_side_nav()
        body_layout.addWidget(self.side_nav)

        self._create_tabs()

        content_container = QWidget()
        content_container.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 5, 15, 15)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.stack, 1)
        body_layout.addWidget(content_container, 1)

        root_layout.addLayout(body_layout, 1)

        self._create_corner_covers()

        self.apply_backgrounds()

    def _create_title_bar(self) -> QFrame:
        title_bar = QFrame()
        title_bar.setFixedHeight(52)
        title_bar.setStyleSheet(
            f"""
            QFrame {{
                background: {self.theme.get_color('bg_primary')};
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom: none;
            }}
            """
        )

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(12, 2, 10, 0)
        layout.setSpacing(8)

        left_container = QWidget()
        left_container.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        settings_block = QWidget()
        settings_block.setFixedWidth(44)
        settings_block.setStyleSheet("background: transparent;")
        settings_block_layout = QVBoxLayout(settings_block)
        settings_block_layout.setContentsMargins(0, 6, 0, 6)
        settings_block_layout.setSpacing(0)
        settings_block_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.settings_btn = AnimatedIconButton(
            "ICON_SETTINGS",
            self.tr.t("tooltips.settings"),
            self.theme,
            self,
        )
        self.settings_btn.setFixedSize(42, 42)
        self.settings_btn.setIconSize(QSize(22, 22))
        self.settings_btn.clicked.connect(self._show_settings)
        self._apply_action_button_style_like_sidenav(self.settings_btn)
        settings_block_layout.addWidget(self.settings_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        vertical_line = QFrame()
        vertical_line.setFixedSize(1, 34)
        vertical_line.setStyleSheet(
            f"background-color: {self.theme.get_color('border')}; border: none;"
        )

        vertical_line_wrap = QWidget()
        vertical_line_wrap.setFixedWidth(14)
        vertical_line_wrap.setStyleSheet("background: transparent;")
        vertical_line_wrap_layout = QVBoxLayout(vertical_line_wrap)
        vertical_line_wrap_layout.setContentsMargins(8, 0, 0, 0)
        vertical_line_wrap_layout.setSpacing(0)
        vertical_line_wrap_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        vertical_line_wrap_layout.addWidget(vertical_line, 0, Qt.AlignmentFlag.AlignVCenter)

        # app_icon = QLabel()
        # app_icon.setPixmap(get_icon("ICON_APP").pixmap(16, 16))
        # app_icon.setStyleSheet("background: transparent; border: none; margin-right: 2px;")

        app_name = QLabel(APP_NAME)
        app_name.setStyleSheet(
            f"""
            font-size: 15px;
            font-weight: 700;
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            letter-spacing: 0.5px;
            border: none;
            """
        )

        self.top_tabs = AnimatedSegmentedTabs(
            [self.tr.t("tabs.workshop"), self.tr.t("tabs.wallpapers")],
            self.theme,
            self,
        )
        self.top_tabs.currentChanged.connect(self._on_top_tab_changed)

        left_layout.addWidget(settings_block, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        left_layout.addWidget(vertical_line_wrap, 0, Qt.AlignmentFlag.AlignVCenter)
        left_layout.addSpacing(4)
        # left_layout.addWidget(app_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        left_layout.addWidget(app_name, 0, Qt.AlignmentFlag.AlignVCenter)
        left_layout.addSpacing(8)
        left_layout.addWidget(self.top_tabs, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(left_container)
        layout.addStretch()

        window_buttons_layout = QHBoxLayout()
        window_buttons_layout.setSpacing(2)

        min_btn = self._create_window_button("minimize", self._animate_minimize)
        self.max_btn = self._create_window_button("maximize", self._toggle_maximize)
        close_btn = self._create_window_button("close", self._on_close)

        window_buttons_layout.addWidget(min_btn)
        window_buttons_layout.addWidget(self.max_btn)
        window_buttons_layout.addWidget(close_btn)
        layout.addLayout(window_buttons_layout)

        return title_bar

    def _create_side_nav(self) -> SideNavBar:
        nav = SideNavBar(self.theme, self)

        self.downloads_btn = nav.addActionButton(
            "ICON_TASK",
            self.tr.t("tooltips.tasks"),
            self._toggle_downloads_popup,
        )
        self.batch_btn = nav.addActionButton(
            "ICON_EXTRACT",
            self.tr.t("tooltips.multi_download"),
            self._show_multi_download,
        )
        self.info_btn = nav.addActionButton(
            "ICON_INFO",
            self.tr.t("tooltips.info"),
            self._show_info,
        )
        return nav

    def _on_top_tab_changed(self, index: int) -> None:
        self.stack.setCurrentIndex(index)

    def _apply_action_button_style_like_sidenav(self, button: AnimatedIconButton) -> None:
        bg_tertiary = self.theme.get_color("bg_tertiary")
        border = self.theme.get_color("border")
        button.setStyleSheet(
            f"""
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
            """
        )

    def _create_tabs(self) -> None:
        self.stack = ContentSwitcher()
        self.stack.setStyleSheet("border: none; background: transparent;")

        self.workshop_tab = WorkshopTab(
            self.config,
            self.accounts,
            self.dm,
            self.we,
            self.tr,
            self.theme,
            self.metadata_service,
            self,
        )
        self.wallpapers_tab = WallpapersTab(
            self.config,
            self.dm,
            self.we,
            self.tr,
            self.theme,
            self.metadata_service,
            self,
        )

        self.stack.addWidget(self.workshop_tab)
        self.stack.addWidget(self.wallpapers_tab)

    def _create_corner_covers(self) -> None:
        self._corner_covers = []
        bg_color = self.theme.get_color("bg_primary")
        colors = [bg_color, bg_color, bg_color, bg_color]
        for i in range(4):
            cover = QWidget(self.centralWidget())
            cover.setFixedSize(16, 16)
            cover.setStyleSheet(f"background-color: {colors[i]}; border: none;")
            cover.hide()
            cover.lower()
            self._corner_covers.append(cover)

    def apply_backgrounds(self) -> None:
        self._main_bg.set_image_from_base64(self.config.get_background_image("main"))
        self._main_bg.set_blur_percent(self.config.get_background_blur("main"))
        self._main_bg.set_opacity_percent(self.config.get_background_opacity("main"))
        self._main_bg.set_base_color(self.theme.get_color("bg_primary"))
        self._main_bg.lower()

        extend = self.config.get_background_extend_titlebar()
        if extend:
            self.title_bar.setStyleSheet("""
                QFrame {
                    background: transparent;
                    border-top-left-radius: 16px;
                    border-top-right-radius: 16px;
                    border-bottom: none;
                }
            """)
        else:
            self.title_bar.setStyleSheet(f"""
                QFrame {{
                    background: {self.theme.get_color('bg_primary')};
                    border-top-left-radius: 16px;
                    border-top-right-radius: 16px;
                    border-bottom: none;
                }}
            """)

        for tab in [self.workshop_tab, self.wallpapers_tab]:
            if hasattr(tab, "apply_backgrounds"):
                tab.apply_backgrounds(self.config, self.theme)

    def _update_corner_covers(self) -> None:
        if not hasattr(self, "_corner_covers"):
            return

        width = self.centralWidget().width()
        height = self.centralWidget().height()
        size = 16
        positions = [
            (0, 0),
            (width - size, 0),
            (0, height - size),
            (width - size, height - size),
        ]
        for cover, pos in zip(self._corner_covers, positions):
            cover.move(pos[0], pos[1])
            cover.setVisible(self._pseudo_fullscreen)

    def _auto_check_updates(self) -> None:
        if not self.config.get_auto_check_updates():
            return
        self.check_for_updates(silent=True)

    def check_for_updates(self, silent: bool = False) -> None:
        if self._update_worker is not None and self._update_worker.isRunning():
            return

        skipped_version = self.config.get_skip_version() if silent else ""
        self._update_worker = UpdateCheckWorker(skipped_version=skipped_version, parent=self)
        self._update_worker.completed.connect(lambda result: self._on_update_check_completed(result, silent))
        self._update_worker.start()

    def _on_update_check_completed(self, result, silent: bool) -> None:
        self._update_worker = None

        if result.error:
            if not silent:
                MessageBox.warning(
                    self,
                    self.tr.t("dialog.warning"),
                    f"Update check failed:\n{result.error}",
                )
            return

        if result.update_available:
            dialog = UpdateDialog(self.tr, self.theme, result, self.config, self)
            dialog.exec()
            return

        if not silent:
            MessageBox.information(
                self,
                self.tr.t("dialog.about"),
                f"You are using the latest version: v{result.current_version}",
            )

    def _get_available_screen_geometry(self) -> QRect:
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            return screen.availableGeometry()
        return QRect(0, 0, 1200, 730)

    def _update_window_state_ui(self) -> None:
        self._is_maximized = self._pseudo_fullscreen
        if hasattr(self, "max_btn"):
            self.max_btn.setIcon(get_icon("ICON_RESTORE" if self._pseudo_fullscreen else "ICON_MAXIMIZE"))
        self._update_corner_covers()

    def _animate_geometry_to(self, target_rect: QRect, on_finished=None, duration: int = 260) -> None:
        if self._geometry_anim is not None:
            try:
                self._geometry_anim.stop()
                self._geometry_anim.deleteLater()
            except Exception:
                pass

        self._geometry_anim = QPropertyAnimation(self, b"geometry")
        self._geometry_anim.setDuration(duration)
        self._geometry_anim.setStartValue(self.geometry())
        self._geometry_anim.setEndValue(target_rect)
        self._geometry_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        if on_finished is not None:
            self._geometry_anim.finished.connect(on_finished)

        self._geometry_anim.start()

    def _enter_pseudo_fullscreen(self, animated: bool = True) -> None:
        if self._pseudo_fullscreen:
            return

        if not self._restoring_startup_state:
            self._normal_geometry_before_fullscreen = QRect(self.geometry())
        elif self._normal_geometry_before_fullscreen is None:
            saved = self.config.get_window_geometry()
            self._normal_geometry_before_fullscreen = QRect(
                saved.get("x", self.x()),
                saved.get("y", self.y()),
                saved.get("width", self.width()),
                saved.get("height", self.height()),
            )

        target = self._get_available_screen_geometry()
        self._pseudo_fullscreen = True
        self._update_window_state_ui()

        if animated and not self._restoring_startup_state:
            self._animate_geometry_to(target)
        else:
            self.setGeometry(target)

    def _exit_pseudo_fullscreen(self, animated: bool = True) -> None:
        if not self._pseudo_fullscreen:
            return

        target = self._normal_geometry_before_fullscreen
        if target is None or not target.isValid():
            target = QRect(100, 100, 1200, 730)

        self._pseudo_fullscreen = False
        self._update_window_state_ui()

        if animated and not self._restoring_startup_state:
            self._animate_geometry_to(target)
        else:
            self.setGeometry(target)

    def _toggle_maximize(self) -> None:
        if self._restoring_from_minimize:
            return

        if self._pseudo_fullscreen:
            self._exit_pseudo_fullscreen(animated=True)
        else:
            self._enter_pseudo_fullscreen(animated=True)

    def _get_minimize_target_pos(self) -> QPoint:
        screen_rect = self._get_available_screen_geometry()
        current = self.geometry()
        target_x = screen_rect.x() + (screen_rect.width() - current.width()) // 2
        target_y = screen_rect.y() + screen_rect.height() - current.height()
        return QPoint(target_x, target_y)

    def _animate_minimize(self) -> None:
        if self.isMinimized() or self._restoring_from_minimize:
            return

        if self._geometry_anim is not None:
            try:
                self._geometry_anim.stop()
            except Exception:
                pass

        self._pre_minimize_geometry = QRect(self.geometry())
        self._was_minimized_animated = True

        start_pos = self.pos()
        end_pos = self._get_minimize_target_pos()

        if self._minimize_pos_anim is not None:
            try:
                self._minimize_pos_anim.stop()
                self._minimize_pos_anim.deleteLater()
            except Exception:
                pass

        self._minimize_pos_anim = QPropertyAnimation(self, b"pos")
        self._minimize_pos_anim.setDuration(220)
        self._minimize_pos_anim.setStartValue(start_pos)
        self._minimize_pos_anim.setEndValue(end_pos)
        self._minimize_pos_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        def finish_minimize():
            self.showMinimized()
            if self._pseudo_fullscreen:
                self.setGeometry(self._get_available_screen_geometry())
            elif self._pre_minimize_geometry and self._pre_minimize_geometry.isValid():
                self.setGeometry(self._pre_minimize_geometry)

        self._minimize_pos_anim.finished.connect(finish_minimize)
        self._minimize_pos_anim.start()

    def _animate_restore_from_minimize(self) -> None:
        if not self._was_minimized_animated or self._restoring_from_minimize:
            return

        self._restoring_from_minimize = True

        if self._minimize_pos_anim is not None:
            try:
                self._minimize_pos_anim.stop()
                self._minimize_pos_anim.deleteLater()
            except Exception:
                pass

        end_rect = (
            self._get_available_screen_geometry()
            if self._pseudo_fullscreen
            else self._pre_minimize_geometry
            if self._pre_minimize_geometry and self._pre_minimize_geometry.isValid()
            else QRect(self.geometry())
        )

        start_pos = QPoint(
            self._get_available_screen_geometry().x() + (self._get_available_screen_geometry().width() - end_rect.width()) // 2,
            self._get_available_screen_geometry().y() + self._get_available_screen_geometry().height() - end_rect.height(),
        )

        self.showNormal()
        self.resize(end_rect.size())
        self.move(start_pos)
        self.raise_()
        self.activateWindow()

        self._minimize_pos_anim = QPropertyAnimation(self, b"pos")
        self._minimize_pos_anim.setDuration(260)
        self._minimize_pos_anim.setStartValue(start_pos)
        self._minimize_pos_anim.setEndValue(end_rect.topLeft())
        self._minimize_pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def finish_restore():
            self.setGeometry(end_rect)
            self._restoring_from_minimize = False
            self._was_minimized_animated = False

        self._minimize_pos_anim.finished.connect(finish_restore)
        self._minimize_pos_anim.start()

    def _create_window_button(self, button_type: str, callback):
        button = QPushButton()
        button.setFixedSize(38, 38)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

        icon_map = {
            "minimize": "ICON_MINIMIZE",
            "maximize": "ICON_MAXIMIZE",
            "restore": "ICON_RESTORE",
            "close": "ICON_CLOSE",
        }
        button.setIcon(get_icon(icon_map.get(button_type, "ICON_CLOSE")))
        button.setIconSize(QSize(16, 16))

        hover_color = self.theme.get_color("overlay_light")
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            """
        )
        button.clicked.connect(callback)
        return button

    def _toggle_downloads_popup(self) -> None:
        if self.workshop_tab.downloads_dialog.isVisible():
            self.workshop_tab.hide_downloads_popup()
        else:
            button_pos = self.downloads_btn.mapToGlobal(self.downloads_btn.rect().topRight())
            self.workshop_tab.show_downloads_popup(button_pos)

    def _show_settings(self) -> None:
        self.settings_popup = SettingsDialog(
            self.config,
            self.accounts,
            self.tr,
            self.theme,
            self,
            self,
        )
        self.settings_popup.exec()

    def _show_multi_download(self) -> None:
        dialog = BatchDownloadDialog(self.tr, self, self.theme)
        if dialog.exec() == dialog.DialogCode.Accepted:
            pubfileids = dialog.get_pubfileids()
            new_ids = [
                pubfileid
                for pubfileid in pubfileids
                if not self.we.is_installed(pubfileid) and not self.dm.is_downloading(pubfileid)
            ]
            if not new_ids:
                return

            account_index = self.config.get_account_number()
            for pubfileid in new_ids:
                self.dm.start_download(pubfileid, account_index)

    def _show_info(self) -> None:
        dialog = InfoDialog(self.tr, self, self.theme, self)
        dialog.exec()

    def _on_download_completed_signal(self, pubfileid: str, success: bool) -> None:
        if success:
            QTimer.singleShot(300, self.refresh_wallpapers)

    def refresh_wallpapers(self) -> None:
        if hasattr(self, "wallpapers_tab"):
            self.wallpapers_tab.refresh()

    def _on_close(self) -> None:
        has_downloads = len(self.dm.downloading) > 0
        has_extractions = len(self.dm.extracting) > 0

        if has_downloads or has_extractions:
            if has_downloads and has_extractions:
                msg = self.tr.t("messages.exit_with_downloads")
            elif has_downloads:
                msg = self.tr.t("messages.exit_with_downloads_only")
            else:
                msg = self.tr.t("messages.exit_with_extractions_only")

            reply = MessageBox.question(self, self.tr.t("dialog.exit"), msg)
            if reply != MessageBox.StandardButton.Yes:
                return

            self.dm.cleanup_all()

        if hasattr(self, "workshop_tab"):
            self.workshop_tab.cleanup()

        clear_cache_if_needed(get_app_data_dir() / "cookies" / "Cache", 200)
        self._save_window_geometry()
        self.close()

    def _load_window_geometry(self) -> None:
        if not self.config.get_save_window_state():
            self._update_window_state_ui()
            return

        geometry = self.config.get_window_geometry()
        x = geometry.get("x", -1)
        y = geometry.get("y", -1)
        width = geometry.get("width", 1200)
        height = geometry.get("height", 730)
        is_maximized = geometry.get("is_maximized", False)

        if width > 0 and height > 0:
            self.resize(width, height)
        if x >= 0 and y >= 0:
            self.move(x, y)

        self._normal_geometry_before_fullscreen = QRect(
            x if x >= 0 else self.x(),
            y if y >= 0 else self.y(),
            width if width > 0 else self.width(),
            height if height > 0 else self.height(),
        )

        if is_maximized:
            self._restoring_startup_state = True
            self._enter_pseudo_fullscreen(animated=False)
            self._restoring_startup_state = False
        else:
            self._pseudo_fullscreen = False
            self._update_window_state_ui()

    def _save_window_geometry(self) -> None:
        if not self.config.get_save_window_state():
            return

        if self._pseudo_fullscreen:
            normal = self._normal_geometry_before_fullscreen
            if normal is None or not normal.isValid():
                normal = QRect(self.x(), self.y(), self.width(), self.height())
            self.config.set_window_geometry(
                normal.x(),
                normal.y(),
                normal.width(),
                normal.height(),
                True,
            )
        else:
            self.config.set_window_geometry(
                self.x(),
                self.y(),
                self.width(),
                self.height(),
                False,
            )

    def _is_in_title_bar_drag_zone(self, pos: QPoint) -> bool:
        if pos.y() > self.title_bar.height():
            return False

        widget = self.childAt(pos)
        if widget is None:
            return True

        current = widget
        while current is not None:
            if isinstance(current, QPushButton):
                return False
            if current == self.top_tabs:
                return False
            if current.parentWidget() == self.top_tabs:
                return False
            if current == self.title_bar:
                return True
            current = current.parentWidget()
        return False

    def _begin_drag_from_pseudo_fullscreen(self, global_pos: QPoint) -> None:
        if not self._pseudo_fullscreen:
            return

        screen_rect = self._get_available_screen_geometry()
        normal = self._normal_geometry_before_fullscreen
        if normal is None or not normal.isValid():
            normal = QRect(100, 100, 1200, 730)

        ratio_x = 0.5
        if screen_rect.width() > 0:
            ratio_x = max(0.0, min(1.0, (global_pos.x() - screen_rect.x()) / screen_rect.width()))

        target_width = normal.width()
        target_height = normal.height()
        new_x = global_pos.x() - int(target_width * ratio_x)
        new_y = global_pos.y() - 18

        max_x = screen_rect.right() - target_width + 1
        min_x = screen_rect.left()
        new_x = max(min_x, min(new_x, max_x))
        new_y = max(screen_rect.top(), new_y)

        self._pseudo_fullscreen = False
        self._update_window_state_ui()
        self.setGeometry(new_x, new_y, target_width, target_height)
        self.old_pos = global_pos
        self._drag_cursor_offset = global_pos - self.frameGeometry().topLeft()

    def eventFilter(self, obj, event):
        if obj == self.title_bar and event.type() == QEvent.Type.MouseButtonDblClick:
            if event.button() == Qt.MouseButton.LeftButton:
                pos = event.position().toPoint()
                if self._is_in_title_bar_drag_zone(pos):
                    self._toggle_maximize()
                    return True
        return super().eventFilter(obj, event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if not self.isMinimized() and self._was_minimized_animated:
                QTimer.singleShot(0, self._animate_restore_from_minimize)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_corner_covers()

    def _get_resize_edge(self, pos: QPoint) -> str:
        if self._pseudo_fullscreen:
            return ""

        rect = self.rect()
        x = pos.x()
        y = pos.y()
        margin = self.RESIZE_MARGIN
        edges = ""

        if y <= margin:
            edges += "top"
        elif y >= rect.height() - margin:
            edges += "bottom"

        if x <= margin:
            edges += "left"
        elif x >= rect.width() - margin:
            edges += "right"

        return edges

    def _update_cursor_for_edge(self, edge: str) -> None:
        cursor_map = {
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "topleft": Qt.CursorShape.SizeFDiagCursor,
            "topright": Qt.CursorShape.SizeBDiagCursor,
            "bottomleft": Qt.CursorShape.SizeBDiagCursor,
            "bottomright": Qt.CursorShape.SizeFDiagCursor,
        }
        if edge in cursor_map:
            self.setCursor(cursor_map[edge])
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            edge = self._get_resize_edge(pos)
            if edge:
                self._resize_edge = edge
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
            elif self._is_in_title_bar_drag_zone(pos):
                global_pos = event.globalPosition().toPoint()
                if self._pseudo_fullscreen:
                    self._begin_drag_from_pseudo_fullscreen(global_pos)
                else:
                    self.old_pos = global_pos
                    self._drag_cursor_offset = global_pos - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        global_pos = event.globalPosition().toPoint()
        if self._resize_edge and event.buttons() == Qt.MouseButton.LeftButton:
            self._perform_resize(global_pos)
        elif self.old_pos and event.buttons() == Qt.MouseButton.LeftButton:
            if not self._drag_cursor_offset.isNull():
                self.move(global_pos - self._drag_cursor_offset)
            else:
                delta = global_pos - self.old_pos
                self.move(self.pos() + delta)
                self.old_pos = global_pos
        else:
            edge = self._get_resize_edge(event.position().toPoint())
            self._update_cursor_for_edge(edge)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self._drag_cursor_offset = QPoint()
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def _perform_resize(self, global_pos: QPoint) -> None:
        if not self._resize_edge or not self._resize_start_geometry:
            return

        delta = global_pos - self._resize_start_pos
        geometry = self._resize_start_geometry

        new_x = geometry.x()
        new_y = geometry.y()
        new_width = geometry.width()
        new_height = geometry.height()

        min_width = self.minimumWidth()
        min_height = self.minimumHeight()

        if "left" in self._resize_edge:
            new_width = geometry.width() - delta.x()
            if new_width >= min_width:
                new_x = geometry.x() + delta.x()
            else:
                new_width = min_width
                new_x = geometry.x() + geometry.width() - min_width

        if "right" in self._resize_edge:
            new_width = geometry.width() + delta.x()
            if new_width < min_width:
                new_width = min_width

        if "top" in self._resize_edge:
            new_height = geometry.height() - delta.y()
            if new_height >= min_height:
                new_y = geometry.y() + delta.y()
            else:
                new_height = min_height
                new_y = geometry.y() + geometry.height() - min_height

        if "bottom" in self._resize_edge:
            new_height = geometry.height() + delta.y()
            if new_height < min_height:
                new_height = min_height

        self.setGeometry(new_x, new_y, new_width, new_height)