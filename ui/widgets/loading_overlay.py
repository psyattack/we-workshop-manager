from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ui.widgets.animated_icon_label import AnimatedIconLabel


class LoadingOverlay(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)

        self.theme = theme_manager

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")

        self._container = QWidget(self)
        self._container.setFixedSize(80, 80)
        self._container.setStyleSheet(
            """
            background-color: rgba(0, 0, 0, 150);
            border-radius: 16px;
            """
        )

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = AnimatedIconLabel("ICON_HOURGLASS", 48, self._container)
        container_layout.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self._icon.start_animation()
        self._center_container()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._icon.stop_animation()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center_container()

    def update_position(self) -> None:
        self._center_container()

    def _center_container(self) -> None:
        if not self.parent():
            return

        parent_rect = self.parent().rect()
        self.setGeometry(parent_rect)

        x = (self.width() - self._container.width()) // 2
        y = (self.height() - self._container.height()) // 2
        self._container.move(x, y)