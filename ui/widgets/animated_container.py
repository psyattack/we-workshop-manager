from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout


class AnimatedContainer(QWidget):
    height_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._animation = QPropertyAnimation(self, b"maximumHeight")
        self._animation.setDuration(250)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.valueChanged.connect(self._on_animation_value_changed)

        self._expanded = False
        self._content_height = 0

        self.setMaximumHeight(0)

        self._inner_layout = QVBoxLayout(self)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        self._inner_layout.setSpacing(4)

    def set_content_widget(self, widget: QWidget) -> None:
        self._inner_layout.addWidget(widget)

    def is_expanded(self) -> bool:
        return self._expanded

    def snap_open(self) -> None:
        self._expanded = True
        self._recalculate_content_height()
        self.setMaximumHeight(self._content_height)

    def toggle(self, expand: bool) -> None:
        if expand == self._expanded:
            return

        self._expanded = expand
        self._recalculate_content_height()

        self._animation.stop()
        self._animation.setStartValue(self.maximumHeight())
        self._animation.setEndValue(self._content_height if expand else 0)
        self._animation.start()

    def update_height(self) -> None:
        if not self._expanded:
            return

        self._recalculate_content_height()
        self.setMaximumHeight(self._content_height)

    def animate_height_change(self, height_delta: int, duration: int = 250) -> None:
        if not self._expanded:
            return

        self._animation.stop()
        self._animation.setDuration(duration)
        self._animation.setStartValue(self.maximumHeight())
        self._animation.setEndValue(max(0, self.maximumHeight() + height_delta))
        self._animation.start()

    def _recalculate_content_height(self) -> None:
        self._content_height = self._inner_layout.sizeHint().height()

    def _on_animation_value_changed(self) -> None:
        self.height_changed.emit()