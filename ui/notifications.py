from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QLabel, QMessageBox, QGraphicsDropShadowEffect


class NotificationLabel(QLabel):
    def __init__(self, message: str, theme_service=None, parent=None):
        super().__init__(message, parent)
        self.theme_service = theme_service

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_style()

        QTimer.singleShot(2000, self.deleteLater)

    def _get_primary_color(self) -> str:
        if self.theme_service:
            return self.theme_service.get_color("primary")
        return "#4A7FD9"

    def _get_primary_rgb(self) -> tuple[int, int, int]:
        color = QColor(self._get_primary_color())
        return color.red(), color.green(), color.blue()

    def _apply_style(self) -> None:
        red, green, blue = self._get_primary_rgb()

        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: rgba({red}, {green}, {blue}, 240);
                color: white;
                padding: 12px 20px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
            }}
            """
        )

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(red, green, blue, 120))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    @staticmethod
    def _find_theme_service(widget):
        current = widget
        while current:
            if hasattr(current, "theme"):
                return current.theme
            current = current.parent() if hasattr(current, "parent") else None
        return None

    @staticmethod
    def show_notification(parent, message: str, x: int = 935, y: int = 15, theme_service=None) -> None:
        if not parent or not message:
            return

        if theme_service is None:
            theme_service = NotificationLabel._find_theme_service(parent)

        notification = NotificationLabel(message, theme_service, parent)
        notification.adjustSize()

        if notification.width() < 200:
            notification.setFixedWidth(200)

        notification.move(x, y)
        notification.show()
        notification.raise_()


class MessageBox(QMessageBox):
    Icon = QMessageBox.Icon
    StandardButton = QMessageBox.StandardButton
    ButtonRole = QMessageBox.ButtonRole

    def __init__(self, theme_service, title, text, icon=QMessageBox.Icon.Information, parent=None):
        super().__init__(parent)
        self.theme_service = theme_service
        self._setup_colors()

        self.setWindowTitle(title)
        self.setText(text)
        self.setIcon(icon)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)

        self._apply_style()

    def _setup_colors(self) -> None:
        if self.theme_service:
            self.c_bg_primary = self.theme_service.get_color("bg_primary")
            self.c_bg_secondary = self.theme_service.get_color("bg_secondary")
            self.c_bg_tertiary = self.theme_service.get_color("bg_tertiary")
            self.c_border = self.theme_service.get_color("border")
            self.c_border_light = self.theme_service.get_color("border_light")
            self.c_text_primary = self.theme_service.get_color("text_primary")
            self.c_text_secondary = self.theme_service.get_color("text_secondary")
            self.c_primary = self.theme_service.get_color("primary")
            self.c_primary_hover = self.theme_service.get_color("primary_hover")
            self.c_accent_red = self.theme_service.get_color("accent_red")
        else:
            self.c_bg_primary = "#0F111A"
            self.c_bg_secondary = "#1A1D2E"
            self.c_bg_tertiary = "#252938"
            self.c_border = "#2A2F42"
            self.c_border_light = "#3A3F52"
            self.c_text_primary = "#FFFFFF"
            self.c_text_secondary = "#B4B7C3"
            self.c_primary = "#4A7FD9"
            self.c_primary_hover = "#5B8FE9"
            self.c_accent_red = "#EF5B5B"

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QMessageBox {{
                background-color: {self.c_bg_secondary};
                border: 2px solid {self.c_border_light};
            }}

            QMessageBox QLabel {{
                color: {self.c_text_primary};
                background: transparent;
                font-size: 13px;
            }}

            QMessageBox QPushButton {{
                background-color: {self.c_primary};
                color: {self.c_text_primary};
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
                min-width: 80px;
            }}

            QMessageBox QPushButton:hover {{
                background-color: {self.c_primary_hover};
            }}
            """
        )

    @staticmethod
    def _find_theme_service(widget):
        current = widget
        while current:
            if hasattr(current, "theme"):
                return current.theme
            current = current.parent() if hasattr(current, "parent") else None
        return None

    @staticmethod
    def show(
        parent,
        title: str,
        text: str,
        icon=QMessageBox.Icon.Information,
        buttons=QMessageBox.StandardButton.Ok,
        default_button=None,
        theme_service=None,
    ):
        if theme_service is None and parent:
            theme_service = MessageBox._find_theme_service(parent)

        msg_box = MessageBox(theme_service, title, text, icon, parent)
        msg_box.setStandardButtons(buttons)

        if default_button:
            msg_box.setDefaultButton(default_button)

        return msg_box.exec()

    @staticmethod
    def information(parent, title: str, text: str, buttons=QMessageBox.StandardButton.Ok, theme_service=None):
        return MessageBox.show(
            parent,
            title,
            text,
            QMessageBox.Icon.Information,
            buttons,
            theme_service=theme_service,
        )

    @staticmethod
    def warning(parent, title: str, text: str, buttons=QMessageBox.StandardButton.Ok, theme_service=None):
        return MessageBox.show(
            parent,
            title,
            text,
            QMessageBox.Icon.Warning,
            buttons,
            theme_service=theme_service,
        )

    @staticmethod
    def critical(parent, title: str, text: str, buttons=QMessageBox.StandardButton.Ok, theme_service=None):
        return MessageBox.show(
            parent,
            title,
            text,
            QMessageBox.Icon.Critical,
            buttons,
            theme_service=theme_service,
        )

    @staticmethod
    def question(
        parent,
        title: str,
        text: str,
        buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        default_button=QMessageBox.StandardButton.Yes,
        theme_service=None,
    ):
        return MessageBox.show(
            parent,
            title,
            text,
            QMessageBox.Icon.Question,
            buttons,
            default_button,
            theme_service,
        )

    @staticmethod
    def confirm(parent, title: str, text: str, theme_service=None) -> bool:
        result = MessageBox.question(
            parent,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
            theme_service,
        )
        return result == QMessageBox.StandardButton.Yes