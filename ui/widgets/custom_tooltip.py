from enum import Enum

from PyQt6.QtCore import QEvent, QPoint, QRect, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QApplication, QLabel, QWidget


class ToolTipPosition(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class CustomToolTip(QWidget):
    PADDING_X = 10
    PADDING_Y = 6
    ARROW_SIZE = 8
    BORDER_RADIUS = 8
    OFFSET = 10
    MIN_WIDTH = 60
    MIN_HEIGHT = 28
    MAX_TEXT_WIDTH = 260

    def __init__(self, text: str, position: ToolTipPosition, theme_manager=None, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self.text = text
        self.position = position

        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._setup_colors()

        self.label = QLabel(text, self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.c_text};
                background: transparent;
                border: none;
                font-size: 12px;
                font-weight: 500;
            }}
            """
        )

        self.adjustSize()

    def _setup_colors(self) -> None:
        if self.theme:
            self.c_bg = self.theme.get_color("bg_primary")
            self.c_border = self.theme.get_color("border_light")
            self.c_text = self.theme.get_color("text_primary")
        else:
            self.c_bg = "#11141D"
            self.c_border = "#3A3F52"
            self.c_text = "#FFFFFF"

    def set_text(self, text: str) -> None:
        self.text = text
        self.label.setText(text)
        self.adjustSize()
        self.update()

    def sizeHint(self):
        self.label.setMaximumWidth(self.MAX_TEXT_WIDTH)
        self.label.adjustSize()
        label_size = self.label.sizeHint()

        width = max(self.MIN_WIDTH, label_size.width() + self.PADDING_X * 2)
        height = max(self.MIN_HEIGHT, label_size.height() + self.PADDING_Y * 2)

        if self.position in (ToolTipPosition.TOP, ToolTipPosition.BOTTOM):
            return QRect(0, 0, width, height + self.ARROW_SIZE).size()
        return QRect(0, 0, width + self.ARROW_SIZE, height).size()

    def adjustSize(self) -> None:
        self.label.setMaximumWidth(self.MAX_TEXT_WIDTH)
        self.label.adjustSize()
        label_size = self.label.sizeHint()

        width = max(self.MIN_WIDTH, label_size.width() + self.PADDING_X * 2)
        height = max(self.MIN_HEIGHT, label_size.height() + self.PADDING_Y * 2)

        if self.position in (ToolTipPosition.TOP, ToolTipPosition.BOTTOM):
            total_width = width
            total_height = height + self.ARROW_SIZE
        else:
            total_width = width + self.ARROW_SIZE
            total_height = height

        self.resize(total_width, total_height)
        self._update_label_geometry()

    def _update_label_geometry(self) -> None:
        body_rect = self._get_body_rect()
        self.label.setGeometry(
            QRect(
                int(body_rect.left() + self.PADDING_X),
                int(body_rect.top() + self.PADDING_Y),
                int(body_rect.width() - self.PADDING_X * 2),
                int(body_rect.height() - self.PADDING_Y * 2),
            )
        )

    def show_for(self, target_widget: QWidget) -> None:
        if not target_widget:
            return

        self.adjustSize()

        target_rect = target_widget.rect()
        global_top_left = target_widget.mapToGlobal(target_rect.topLeft())
        global_bottom_right = target_widget.mapToGlobal(target_rect.bottomRight())
        global_rect = QRect(global_top_left, global_bottom_right)

        pos = self._calculate_position(global_rect)
        self.move(pos)
        self.show()
        self.raise_()

    def _calculate_position(self, target_rect: QRect) -> QPoint:
        tooltip_rect = self.rect()

        if self.position == ToolTipPosition.TOP:
            x = target_rect.center().x() - tooltip_rect.width() // 2
            y = target_rect.top() - tooltip_rect.height() - self.OFFSET
        elif self.position == ToolTipPosition.BOTTOM:
            x = target_rect.center().x() - tooltip_rect.width() // 2
            y = target_rect.bottom() + self.OFFSET
        elif self.position == ToolTipPosition.LEFT:
            x = target_rect.left() - tooltip_rect.width() - self.OFFSET
            y = target_rect.center().y() - tooltip_rect.height() // 2
        else:
            x = target_rect.right() + self.OFFSET
            y = target_rect.center().y() - tooltip_rect.height() // 2

        screen = QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            margin = 8
            x = max(available.left() + margin, min(x, available.right() - tooltip_rect.width() - margin))
            y = max(available.top() + margin, min(y, available.bottom() - tooltip_rect.height() - margin))

        return QPoint(x, y)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        fill_path = self._build_shape_path()
        border_path = self._build_border_path()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.c_bg))
        painter.drawPath(fill_path)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(self.c_border), 1))
        painter.drawPath(border_path)

    def _get_body_rect(self) -> QRectF:
        rect = QRectF(self.rect())

        if self.position == ToolTipPosition.TOP:
            return QRectF(0, 0, rect.width(), rect.height() - self.ARROW_SIZE)
        if self.position == ToolTipPosition.BOTTOM:
            return QRectF(0, self.ARROW_SIZE, rect.width(), rect.height() - self.ARROW_SIZE)
        if self.position == ToolTipPosition.LEFT:
            return QRectF(0, 0, rect.width() - self.ARROW_SIZE, rect.height())
        return QRectF(self.ARROW_SIZE, 0, rect.width() - self.ARROW_SIZE, rect.height())

    def _build_shape_path(self) -> QPainterPath:
        body = self._get_body_rect()
        path = QPainterPath()

        path.addRoundedRect(body, self.BORDER_RADIUS, self.BORDER_RADIUS)

        arrow = QPainterPath()
        a = self.ARROW_SIZE

        if self.position == ToolTipPosition.TOP:
            cx = body.center().x()
            y = body.bottom()
            arrow.moveTo(cx - a, y)
            arrow.lineTo(cx, y + a)
            arrow.lineTo(cx + a, y)
            arrow.closeSubpath()

        elif self.position == ToolTipPosition.BOTTOM:
            cx = body.center().x()
            y = body.top()
            arrow.moveTo(cx - a, y)
            arrow.lineTo(cx, y - a)
            arrow.lineTo(cx + a, y)
            arrow.closeSubpath()

        elif self.position == ToolTipPosition.LEFT:
            cy = body.center().y()
            x = body.right()
            arrow.moveTo(x, cy - a)
            arrow.lineTo(x + a, cy)
            arrow.lineTo(x, cy + a)
            arrow.closeSubpath()

        elif self.position == ToolTipPosition.RIGHT:
            cy = body.center().y()
            x = body.left()
            arrow.moveTo(x, cy - a)
            arrow.lineTo(x - a, cy)
            arrow.lineTo(x, cy + a)
            arrow.closeSubpath()

        path.addPath(arrow)
        return path

    def _build_border_path(self) -> QPainterPath:
        body = self._get_body_rect()
        r = self.BORDER_RADIUS
        a = self.ARROW_SIZE

        left = body.left()
        right = body.right()
        top = body.top()
        bottom = body.bottom()
        cx = body.center().x()
        cy = body.center().y()

        path = QPainterPath()

        if self.position == ToolTipPosition.TOP:
            path.moveTo(left + r, top)
            path.lineTo(right - r, top)
            path.arcTo(QRectF(right - 2 * r, top, 2 * r, 2 * r), 90, -90)
            path.lineTo(right, bottom - r)
            path.arcTo(QRectF(right - 2 * r, bottom - 2 * r, 2 * r, 2 * r), 0, -90)
            path.lineTo(cx + a, bottom)
            path.lineTo(cx, bottom + a)
            path.lineTo(cx - a, bottom)
            path.lineTo(left + r, bottom)
            path.arcTo(QRectF(left, bottom - 2 * r, 2 * r, 2 * r), 270, -90)
            path.lineTo(left, top + r)
            path.arcTo(QRectF(left, top, 2 * r, 2 * r), 180, -90)
            path.closeSubpath()

        elif self.position == ToolTipPosition.BOTTOM:
            path.moveTo(left + r, top)
            path.lineTo(cx - a, top)
            path.lineTo(cx, top - a)
            path.lineTo(cx + a, top)
            path.lineTo(right - r, top)
            path.arcTo(QRectF(right - 2 * r, top, 2 * r, 2 * r), 90, -90)
            path.lineTo(right, bottom - r)
            path.arcTo(QRectF(right - 2 * r, bottom - 2 * r, 2 * r, 2 * r), 0, -90)
            path.lineTo(left + r, bottom)
            path.arcTo(QRectF(left, bottom - 2 * r, 2 * r, 2 * r), 270, -90)
            path.lineTo(left, top + r)
            path.arcTo(QRectF(left, top, 2 * r, 2 * r), 180, -90)
            path.closeSubpath()

        elif self.position == ToolTipPosition.LEFT:
            path.moveTo(left + r, top)
            path.lineTo(right - r, top)
            path.arcTo(QRectF(right - 2 * r, top, 2 * r, 2 * r), 90, -90)
            path.lineTo(right, cy - a)
            path.lineTo(right + a, cy)
            path.lineTo(right, cy + a)
            path.lineTo(right, bottom - r)
            path.arcTo(QRectF(right - 2 * r, bottom - 2 * r, 2 * r, 2 * r), 0, -90)
            path.lineTo(left + r, bottom)
            path.arcTo(QRectF(left, bottom - 2 * r, 2 * r, 2 * r), 270, -90)
            path.lineTo(left, top + r)
            path.arcTo(QRectF(left, top, 2 * r, 2 * r), 180, -90)
            path.closeSubpath()

        elif self.position == ToolTipPosition.RIGHT:
            path.moveTo(left + r, top)
            path.lineTo(right - r, top)
            path.arcTo(QRectF(right - 2 * r, top, 2 * r, 2 * r), 90, -90)
            path.lineTo(right, bottom - r)
            path.arcTo(QRectF(right - 2 * r, bottom - 2 * r, 2 * r, 2 * r), 0, -90)
            path.lineTo(left + r, bottom)
            path.arcTo(QRectF(left, bottom - 2 * r, 2 * r, 2 * r), 270, -90)
            path.lineTo(left, cy + a)
            path.lineTo(left - a, cy)
            path.lineTo(left, cy - a)
            path.lineTo(left, top + r)
            path.arcTo(QRectF(left, top, 2 * r, 2 * r), 180, -90)
            path.closeSubpath()

        return path


class ToolTipFilter(QWidget):
    def __init__(self, target_widget: QWidget, text: str, position: ToolTipPosition, theme_manager=None):
        super().__init__(target_widget)
        self.target_widget = target_widget
        self.text = text
        self.position = position
        self.theme = theme_manager
        self.tooltip = None
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._show_tooltip)

        self.target_widget.installEventFilter(self)

    def _ensure_tooltip(self) -> CustomToolTip:
        if self.tooltip is None:
            self.tooltip = CustomToolTip(self.text, self.position, self.theme)
        return self.tooltip

    def set_text(self, text: str) -> None:
        self.text = text
        if self.tooltip is not None:
            self.tooltip.set_text(text)

    def eventFilter(self, obj, event):
        if obj == self.target_widget:
            if event.type() == QEvent.Type.Enter:
                self._hover_timer.start(750)
            elif event.type() == QEvent.Type.Leave:
                self._hover_timer.stop()
                if self.tooltip is not None:
                    self.tooltip.hide()
            elif event.type() == QEvent.Type.MouseButtonPress:
                if self.tooltip is not None:
                    self.tooltip.hide()
            elif event.type() == QEvent.Type.Hide:
                if self.tooltip is not None:
                    self.tooltip.hide()
        return False

    def _show_tooltip(self) -> None:
        if not self.target_widget.isVisible():
            return
        tooltip = self._ensure_tooltip()
        tooltip.show_for(self.target_widget)


def install_tooltip(widget: QWidget, text: str, position: str = "top", theme_manager=None) -> ToolTipFilter:
    pos = ToolTipPosition(position)
    tooltip_filter = ToolTipFilter(widget, text, pos, theme_manager)
    widget._custom_tooltip_filter = tooltip_filter
    return tooltip_filter