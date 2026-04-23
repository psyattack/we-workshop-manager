from PyQt6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QRectF,
    QSize,
    Qt,
    QVariantAnimation,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QWidget

from infrastructure.resources.resource_manager import get_icon


class BrowseTabButton(QPushButton):
    def __init__(self, icon_name: str, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._active = False
        self._icon_name = icon_name

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFlat(True)
        self.setFixedSize(36, 28)
        self.setIcon(get_icon(icon_name))
        self.setIconSize(self._get_icon_size())
        self._apply_style()

    def _get_icon_size(self) -> QSize:
        return self.size() * 0.70

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setIconSize(self._get_icon_size())

    def _apply_style(self) -> None:
        color = (
            self.theme.get_color("text_primary")
            if self._active
            else self.theme.get_color("text_secondary")
        )

        self.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
                color: {color};
            }}
            """
        )


class BrowseToggle(QWidget):
    currentChanged = pyqtSignal(int)

    def __init__(self, icon_names: list[str], theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._icon_names = icon_names
        self._buttons: list[BrowseTabButton] = []
        self._current_index = 0

        self._indicator_x = 0.0
        self._indicator_width = 0.0
        self._indicator_stretch = 0.0

        self._is_animating = False
        self._pending_snap = False

        self._x_anim = QVariantAnimation(self)
        self._x_anim.setDuration(260)
        self._x_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._x_anim.valueChanged.connect(self._on_x_changed)

        self._w_anim = QVariantAnimation(self)
        self._w_anim.setDuration(260)
        self._w_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._w_anim.valueChanged.connect(self._on_w_changed)

        self._stretch_anim = QVariantAnimation(self)
        self._stretch_anim.setDuration(260)
        self._stretch_anim.setKeyValueAt(0.0, 0.0)
        self._stretch_anim.setKeyValueAt(0.35, 8.0)
        self._stretch_anim.setKeyValueAt(0.7, 4.0)
        self._stretch_anim.setKeyValueAt(1.0, 0.0)
        self._stretch_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._stretch_anim.valueChanged.connect(self._on_stretch_changed)

        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(self._x_anim)
        self._anim_group.addAnimation(self._w_anim)
        self._anim_group.addAnimation(self._stretch_anim)
        self._anim_group.finished.connect(self._on_animation_finished)

        self.setFixedHeight(28)
        self.setFixedWidth(72)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        for index, icon_name in enumerate(icon_names):
            button = BrowseTabButton(icon_name, self.theme, self)
            button.clicked.connect(lambda checked=False, i=index: self.setCurrentIndex(i))
            self._buttons.append(button)
            self._layout.addWidget(button)

        self._apply_button_states()
        QTimer.singleShot(0, self._snap_indicator_to_current)
    
    def _get_button_rect(self, index: int) -> QRectF:
        if 0 <= index < len(self._buttons):
            return QRectF(self._buttons[index].geometry())
        return QRectF()

    def _on_x_changed(self, value):
        self._indicator_x = float(value)
        self.update()

    def _on_w_changed(self, value):
        self._indicator_width = float(value)
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

        self._current_index = index
        self._apply_button_states()

        self._start_indicator_animation_to(index)
        self.currentChanged.emit(index)

    def _start_indicator_animation_to(self, index: int) -> None:
        def start():
            target = self._get_button_rect(index)
            if target.isNull():
                return

            self._is_animating = True
            self._anim_group.stop()

            self._x_anim.setStartValue(self._indicator_x)
            self._x_anim.setEndValue(target.x())

            self._w_anim.setStartValue(self._indicator_width)
            self._w_anim.setEndValue(target.width())

            self._stretch_anim.setStartValue(0.0)
            self._stretch_anim.setEndValue(0.0)

            self._anim_group.start()

        QTimer.singleShot(0, start)

    def _on_animation_finished(self) -> None:
        self._is_animating = False
        if self._pending_snap:
            self._pending_snap = False
            self._snap_indicator_to_current()

    def _snap_indicator_to_current(self) -> None:
        if self._is_animating:
            self._pending_snap = True
            return

        rect = self._get_button_rect(self._current_index)
        if rect.isNull():
            return

        self._indicator_x = rect.x()
        self._indicator_width = rect.width()
        self._indicator_stretch = 0.0
        self.update()

    def _apply_button_states(self) -> None:
        for i, button in enumerate(self._buttons):
            button.set_active(i == self._current_index)

    def update_labels(self, icon_names: list[str]) -> None:
        self._icon_names = icon_names
        for i, button in enumerate(self._buttons):
            if i < len(icon_names):
                button.setIcon(get_icon(icon_names[i]))
        QTimer.singleShot(0, self._snap_indicator_to_current)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._snap_indicator_to_current)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._snap_indicator_to_current)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer_rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        border_color = QColor(self.theme.get_color("border"))
        bg_color = QColor(self.theme.get_color("bg_secondary"))

        painter.setPen(QPen(border_color, 1))
        painter.setBrush(bg_color)
        painter.drawRoundedRect(outer_rect, 8.0, 8.0)

        if not self._buttons:
            return

        extra = self._indicator_stretch
        indicator_rect = QRectF(
            self._indicator_x + 1.5 - (extra / 2.0),
            1.5,
            self._indicator_width - 3.0 + extra,
            self.height() - 3.0,
        )

        left_limit = 1.5
        right_limit = self.width() - 1.5
        if indicator_rect.left() < left_limit:
            indicator_rect.setLeft(left_limit)
        if indicator_rect.right() > right_limit:
            indicator_rect.setRight(right_limit)

        if indicator_rect.width() < 10:
            return

        highlight = QColor(255, 255, 255, 28)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(highlight)
        painter.drawRoundedRect(indicator_rect, 8.0, 8.0)