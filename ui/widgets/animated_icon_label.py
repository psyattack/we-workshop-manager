from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtProperty
from PyQt6.QtGui import QTransform
from PyQt6.QtWidgets import QLabel, QWidget

from infrastructure.resources.resource_manager import get_pixmap


class AnimatedIconLabel(QWidget):
    def __init__(self, icon_name: str, size: int = 48, parent=None):
        super().__init__(parent)

        self._icon_name = icon_name
        self._size = size
        self._rotation = 0.0
        self._direction = 1

        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")

        self._label = QLabel(self)
        self._label.setFixedSize(size, size)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background: transparent; border: none;")

        self._base_pixmap = get_pixmap(icon_name, size)
        self._update_pixmap()

        self._animation = QPropertyAnimation(self, b"rotation")
        self._animation.setDuration(1000)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(30.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._animation.finished.connect(self._on_animation_finished)

    def get_rotation(self) -> float:
        return self._rotation

    def set_rotation(self, value: float) -> None:
        self._rotation = value
        self._update_pixmap()

    rotation = pyqtProperty(float, get_rotation, set_rotation)

    def start_animation(self) -> None:
        self._animation.start()

    def stop_animation(self) -> None:
        self._animation.stop()
        self._rotation = 0.0
        self._update_pixmap()

    def _on_animation_finished(self) -> None:
        self._direction *= -1
        self._animation.setStartValue(self._rotation)
        self._animation.setEndValue(30.0 * self._direction)
        self._animation.start()

    def _update_pixmap(self) -> None:
        if self._base_pixmap.isNull():
            return

        transform = QTransform()
        transform.rotate(self._rotation)
        rotated = self._base_pixmap.transformed(
            transform,
            Qt.TransformationMode.SmoothTransformation,
        )

        x = max(0, (rotated.width() - self._size) // 2)
        y = max(0, (rotated.height() - self._size) // 2)
        cropped = rotated.copy(x, y, self._size, self._size)
        self._label.setPixmap(cropped)