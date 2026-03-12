from PyQt6.QtCore import QRectF, QPropertyAnimation, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = True, theme_manager=None, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._checked = checked
        self._handle_pos = 1.0 if checked else 0.0

        self.setFixedSize(36, 18)
        self.setCursor(self.cursor().shape().PointingHandCursor)

        self._animation = QPropertyAnimation(self, b"handlePos")
        self._animation.setDuration(150)

    def _get_primary_color(self) -> str:
        if self.theme:
            return self.theme.get_color("primary")
        return "#4A7FD9"

    def _get_background_color(self) -> str:
        if self.theme:
            return self.theme.get_color("bg_tertiary")
        return "#252938"

    def isChecked(self) -> bool:
        return self._checked

    def get_handle_pos(self) -> float:
        return self._handle_pos

    def set_handle_pos(self, pos: float) -> None:
        self._handle_pos = pos
        self.update()

    handlePos = pyqtProperty(float, get_handle_pos, set_handle_pos)

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self._animation.setStartValue(self._handle_pos)
        self._animation.setEndValue(1.0 if self._checked else 0.0)
        self._animation.start()
        self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        radius = height / 2

        background_color = QColor(
            self._get_primary_color() if self._checked else self._get_background_color()
        )

        painter.setBrush(QBrush(background_color))
        painter.setPen(QPen(background_color, 1))
        painter.drawRoundedRect(QRectF(0, 0, width, height), radius, radius)

        handle_diameter = height - 4
        x = 2 + self._handle_pos * (width - handle_diameter - 4)

        painter.setPen(QPen(QColor("white"), 1))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawEllipse(QRectF(x, 2, handle_diameter, handle_diameter))

        painter.end()