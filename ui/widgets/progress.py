from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from shared.formatting import format_bytes_short
from shared.helpers import parse_depot_status


class CircularProgressWidget(QWidget):
    def __init__(self, size: int = 60, line_width: int = 4, theme_manager=None, parent=None):
        super().__init__(parent)

        self._progress = 0.0
        self._display_text = "0%"
        self._circle_size = size
        self._line_width = line_width
        self.theme = theme_manager

        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _get_progress_color(self) -> QColor:
        if self.theme:
            return QColor(self.theme.get_color("primary"))
        return QColor(70, 130, 240)

    def update_from_status(self, status_text: str, file_size_bytes: int = 0) -> None:
        parsed = parse_depot_status(status_text)
        downloaded_bytes = parsed["downloaded_bytes"]
        total_bytes = parsed["total_bytes"]
        percent = parsed["percent"]

        if percent >= 0:
            self._progress = min(1.0, max(0.0, percent / 100.0))
        elif downloaded_bytes > 0:
            effective_total = total_bytes if total_bytes > 0 else file_size_bytes
            if effective_total > 0:
                self._progress = min(1.0, max(0.0, downloaded_bytes / effective_total))
            else:
                self._progress = 0.0
        else:
            self._progress = 0.0

        percent_int = int(self._progress * 100)
        self._display_text = f"{percent_int}%" if self._progress > 0 or percent >= 0 else "0%"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        margin = self._line_width / 2 + 1
        rect = QRectF(margin, margin, width - 2 * margin, height - 2 * margin)

        track_pen = QPen(QColor(255, 255, 255, 60), self._line_width)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        if self._progress > 0:
            progress_pen = QPen(self._get_progress_color(), self._line_width)
            progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(progress_pen)
            span_angle = int(-self._progress * 360 * 16)
            painter.drawArc(rect, 90 * 16, span_angle)

        font_size = max(7, int(self._circle_size / 5.5))
        font = QFont("Segoe UI", font_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 230))
        painter.drawText(QRectF(0, 0, width, height), Qt.AlignmentFlag.AlignCenter, self._display_text)
        painter.end()


class SmallCircularProgress(QWidget):
    def __init__(self, size: int = 40, line_width: int = 3, theme_manager=None, parent=None):
        super().__init__(parent)

        self._progress = 0.0
        self._display_text = "0B"
        self._circle_size = size
        self._line_width = line_width
        self.theme = theme_manager

        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _get_progress_color(self) -> QColor:
        if self.theme:
            return QColor(self.theme.get_color("primary"))
        return QColor(70, 130, 240)

    def update_from_status(self, status_text: str, file_size_bytes: int = 0, is_extraction: bool = False) -> None:
        parsed = parse_depot_status(status_text)
        downloaded_bytes = parsed["downloaded_bytes"]
        total_bytes = parsed["total_bytes"]
        percent = parsed["percent"]

        if percent >= 0:
            self._progress = min(1.0, max(0.0, percent / 100.0))
        elif downloaded_bytes > 0:
            effective_total = total_bytes if total_bytes > 0 else file_size_bytes
            if effective_total > 0:
                self._progress = min(1.0, max(0.0, downloaded_bytes / effective_total))
            else:
                self._progress = 0.0
        else:
            self._progress = 0.0

        if is_extraction:
            self._display_text = "%"
        elif downloaded_bytes > 0:
            self._display_text = format_bytes_short(downloaded_bytes)
        elif percent >= 0:
            effective_total = total_bytes if total_bytes > 0 else file_size_bytes
            if effective_total > 0:
                estimated = int(effective_total * percent / 100.0)
                self._display_text = format_bytes_short(estimated)
            else:
                self._display_text = f"{int(percent)}%"
        else:
            self._display_text = "0B"

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        margin = self._line_width / 2 + 1
        rect = QRectF(margin, margin, width - 2 * margin, height - 2 * margin)

        track_pen = QPen(QColor(255, 255, 255, 50), self._line_width)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        if self._progress > 0:
            progress_pen = QPen(self._get_progress_color(), self._line_width)
            progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(progress_pen)
            span_angle = int(-self._progress * 360 * 16)
            painter.drawArc(rect, 90 * 16, span_angle)

        font_size = max(6, int(self._circle_size / 6.5))
        font = QFont("Segoe UI", font_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 220))
        painter.drawText(QRectF(0, 0, width, height), Qt.AlignmentFlag.AlignCenter, self._display_text)
        painter.end()