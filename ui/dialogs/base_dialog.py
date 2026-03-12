from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from infrastructure.resources.resource_manager import get_icon
from shared.formatting import hex_to_rgba


class BaseDialog(QDialog):
    def __init__(self, title: str = "Dialog", parent=None, theme_manager=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._setup_colors()

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
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

    def _setup_colors(self) -> None:
        if self.theme:
            self.c_bg_primary = self.theme.get_color("bg_primary")
            self.c_bg_secondary = self.theme.get_color("bg_secondary")
            self.c_bg_tertiary = self.theme.get_color("bg_tertiary")
            self.c_border = self.theme.get_color("border")
            self.c_border_light = self.theme.get_color("border_light")
            self.c_text_primary = self.theme.get_color("text_primary")
            self.c_text_secondary = self.theme.get_color("text_secondary")
            self.c_text_disabled = self.theme.get_color("text_disabled")
            self.c_primary = self.theme.get_color("primary")
            self.c_primary_hover = self.theme.get_color("primary_hover")
            self.c_accent_red = self.theme.get_color("accent_red")
            self.c_overlay = self.theme.get_color("overlay")
        else:
            self.c_bg_primary = "#0F111A"
            self.c_bg_secondary = "#1A1D2E"
            self.c_bg_tertiary = "#252938"
            self.c_border = "#2A2F42"
            self.c_border_light = "#3A3F52"
            self.c_text_primary = "#FFFFFF"
            self.c_text_secondary = "#B4B7C3"
            self.c_text_disabled = "#6B6E7C"
            self.c_primary = "#4A7FD9"
            self.c_primary_hover = "#5B8FE9"
            self.c_accent_red = "#EF5B5B"
            self.c_overlay = "rgba(0, 0, 0, 0.4)"

    def _apply_container_style(self) -> None:
        background_rgba = hex_to_rgba(self.c_bg_secondary, 240)
        self.container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {background_rgba};
                border-radius: 12px;
                border: 2px solid {self.c_border_light};
            }}
            """
        )

    def _create_title_bar(self, title: str) -> None:
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("QWidget { background: transparent; border: none; }")

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 10)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"""
            font-size: 16px;
            font-weight: 700;
            color: {self.c_text_primary};
            background: transparent;
            """
        )

        close_button = QPushButton()
        close_button.setFixedSize(32, 32)
        close_button.setIcon(get_icon("ICON_CLOSE"))
        close_button.setIconSize(close_button.size() * 0.6)
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
                padding: 0px;
            }

            QPushButton:hover {
                background-color: rgba(239, 91, 91, 0.2);
            }

            QPushButton:pressed {
                background-color: rgba(239, 91, 91, 0.3);
            }
            """
        )
        close_button.clicked.connect(self.reject)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)

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