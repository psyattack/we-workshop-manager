from PyQt6.QtCore import (
    QEasingCurve, QParallelAnimationGroup, QRectF, Qt,
    QVariantAnimation, QTimer, pyqtSignal,
)
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QWidget


class BrowseTabButton(QPushButton):
    def __init__(self, text: str, theme_manager, parent=None):
        super().__init__(text, parent)
        self.theme = theme_manager
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFlat(True)
        self.setMinimumWidth(56)
        self.setFixedHeight(28)
        self._apply_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()

    def _apply_style(self) -> None:
        text_active = self.theme.get_color("text_primary")
        text_inactive = self.theme.get_color("text_secondary")
        color = text_active if self._active else text_inactive
        weight = "700" if self._active else "500"
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {color}; font-size: 11px; font-weight: {weight};
                padding: 0 10px; border-radius: 6px;
            }}
            QPushButton:hover {{ background: transparent; }}
        """)


class BrowseToggle(QWidget):
    currentChanged = pyqtSignal(int)

    def __init__(self, labels: list[str], theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._labels = labels
        self._buttons: list[BrowseTabButton] = []
        self._current_index = 0

        self._indicator_x = 0.0
        self._indicator_width = 0.0
        self._indicator_stretch = 0.0

        self._x_anim = QVariantAnimation(self)
        self._x_anim.setDuration(260)
        self._x_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._x_anim.valueChanged.connect(self._on_x)

        self._w_anim = QVariantAnimation(self)
        self._w_anim.setDuration(260)
        self._w_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._w_anim.valueChanged.connect(self._on_w)

        self._s_anim = QVariantAnimation(self)
        self._s_anim.setDuration(260)
        self._s_anim.setKeyValueAt(0.0, 0.0)
        self._s_anim.setKeyValueAt(0.35, 8.0)
        self._s_anim.setKeyValueAt(0.7, 4.0)
        self._s_anim.setKeyValueAt(1.0, 0.0)
        self._s_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._s_anim.valueChanged.connect(self._on_s)

        self._group = QParallelAnimationGroup(self)
        self._group.addAnimation(self._x_anim)
        self._group.addAnimation(self._w_anim)
        self._group.addAnimation(self._s_anim)

        self.setFixedHeight(36)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(0)

        for i, text in enumerate(labels):
            btn = BrowseTabButton(text, self.theme, self)
            btn.clicked.connect(lambda c=False, idx=i: self.setCurrentIndex(idx))
            self._buttons.append(btn)
            self._layout.addWidget(btn)

        self._apply_states()

    def _rect(self, i: int) -> QRectF:
        if 0 <= i < len(self._buttons):
            return QRectF(self._buttons[i].geometry())
        return QRectF()

    def _on_x(self, v):
        self._indicator_x = float(v)
        self.update()

    def _on_w(self, v):
        self._indicator_width = float(v)
        self.update()

    def _on_s(self, v):
        self._indicator_stretch = float(v)
        self.update()

    def currentIndex(self) -> int:
        return self._current_index

    def setCurrentIndex(self, index: int) -> None:
        if not (0 <= index < len(self._buttons)):
            return
        if index == self._current_index:
            return
        self._current_index = index
        self._apply_states()
        target = self._rect(index)
        self._group.stop()
        self._x_anim.setStartValue(self._indicator_x)
        self._x_anim.setEndValue(target.x())
        self._w_anim.setStartValue(self._indicator_width)
        self._w_anim.setEndValue(target.width())
        self._s_anim.setStartValue(0.0)
        self._s_anim.setEndValue(0.0)
        self._group.start()
        self.currentChanged.emit(index)

    def _snap(self) -> None:
        r = self._rect(self._current_index)
        self._indicator_x = r.x()
        self._indicator_width = r.width()
        self._indicator_stretch = 0.0
        self.update()

    def _apply_states(self) -> None:
        for i, b in enumerate(self._buttons):
            b.set_active(i == self._current_index)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._snap()

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self._snap)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        border_c = QColor(self.theme.get_color("border"))
        bg_c = QColor(self.theme.get_color("bg_secondary"))
        p.setPen(QPen(border_c, 1))
        p.setBrush(bg_c)
        radius = 8.0
        p.drawRoundedRect(outer, radius, radius)

        if not self._buttons:
            return

        extra = self._indicator_stretch
        ind = QRectF(
            self._indicator_x + 2.0 - (extra / 2.0),
            4.0,
            self._indicator_width - 4.0 + extra,
            self.height() - 8.0,
        )

        ll = 3.0
        rl = self.width() - 3.0
        if ind.left() < ll:
            ind.setLeft(ll)
        if ind.right() > rl:
            ind.setRight(rl)
        if ind.width() < 10:
            return

        accent = QColor(self.theme.get_color("primary"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(accent)
        p.drawRoundedRect(ind, 5.0, 5.0)