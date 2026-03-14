from PyQt6.QtCore import QEvent, QPoint, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QApplication, QDialog, QFrame, QVBoxLayout


class PopupPanel(QDialog):
    closed = pyqtSignal()

    def __init__(self, theme_manager, title: str = "", parent=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._title = title
        self._anchor_widget = None
        self._anchor_window = None

        self._outside_filter_installed = False
        self._anchor_filter_installed = False
        self._side = "right"

        self._show_mode = None
        self._show_args = {}

        self._seam_right = False
        self._seam_rect_top = 0
        self._seam_rect_height = 0

        self._outer_margin = 8

        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("popupPanelDialog")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(
            self._outer_margin,
            self._outer_margin,
            self._outer_margin,
            self._outer_margin,
        )
        self._main_layout.setSpacing(0)

        self.container = QFrame(self)
        self.container.setObjectName("popupPanelContainer")
        self.container.setStyleSheet("background: transparent; border: none;")

        self._content_layout = QVBoxLayout(self.container)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        self._main_layout.addWidget(self.container)

        self.hide()

    def body_layout(self) -> QVBoxLayout:
        return self._content_layout

    def set_title(self, title: str) -> None:
        self._title = title
        self.update()

    def set_right_seam(self, enabled: bool, top: int = 0, height: int = 0) -> None:
        self._seam_right = enabled
        self._seam_rect_top = top
        self._seam_rect_height = height
        self.update()

    def _install_anchor_tracking(self, anchor_widget) -> None:
        self._remove_anchor_tracking()

        self._anchor_widget = anchor_widget
        if self._anchor_widget is not None:
            self._anchor_widget.installEventFilter(self)

        self._anchor_window = anchor_widget.window() if anchor_widget is not None else None
        if self._anchor_window is not None and self._anchor_window is not self._anchor_widget:
            self._anchor_window.installEventFilter(self)

        self._anchor_filter_installed = True

    def _remove_anchor_tracking(self) -> None:
        if not self._anchor_filter_installed:
            return

        if self._anchor_widget is not None:
            try:
                self._anchor_widget.removeEventFilter(self)
            except Exception:
                pass

        if self._anchor_window is not None:
            try:
                self._anchor_window.removeEventFilter(self)
            except Exception:
                pass

        self._anchor_widget = None
        self._anchor_window = None
        self._anchor_filter_installed = False

    def _screen_geometry_for_anchor(self):
        if self._anchor_widget is not None:
            window = self._anchor_widget.window().windowHandle()
            if window is not None and window.screen() is not None:
                return window.screen().availableGeometry()

            screen = QApplication.screenAt(
                self._anchor_widget.mapToGlobal(self._anchor_widget.rect().center())
            )
            if screen is not None:
                return screen.availableGeometry()

        screen = QApplication.primaryScreen()
        return screen.availableGeometry() if screen else None

    def _fit_to_screen(self, x: int, y: int) -> QPoint:
        available = self._screen_geometry_for_anchor()
        if not available:
            return QPoint(x, y)

        margin = 8
        x = max(
            available.left() + margin,
            min(x, available.right() - self.width() - margin),
        )
        y = max(
            available.top() + margin,
            min(y, available.bottom() - self.height() - margin),
        )
        return QPoint(x, y)

    def _reposition_to_anchor(self) -> None:
        if not self.isVisible() or self._anchor_widget is None or self._show_mode is None:
            return

        self.adjustSize()

        if self._show_mode == "below":
            x_offset = self._show_args.get("x_offset", 0)
            y_overlap = self._show_args.get("y_overlap", 1)

            anchor_rect = self._anchor_widget.rect()
            anchor_global = self._anchor_widget.mapToGlobal(anchor_rect.bottomLeft())

            x = anchor_global.x() + x_offset
            y = anchor_global.y() - y_overlap

            fitted = self._fit_to_screen(x, y)
            self.move(fitted)

        elif self._show_mode == "right_of":
            x_overlap = self._show_args.get("x_overlap", 6)
            y_offset = self._show_args.get("y_offset", 0)
            x_gap = self._show_args.get("x_gap", None)

            anchor_rect = self._anchor_widget.rect()
            anchor_top_right = self._anchor_widget.mapToGlobal(anchor_rect.topRight())
            anchor_top_left = self._anchor_widget.mapToGlobal(anchor_rect.topLeft())

            if x_gap is not None:
                right_x = anchor_top_right.x() + x_gap
                left_x = anchor_top_left.x() - self.width() - x_gap
            else:
                right_x = anchor_top_right.x() - x_overlap
                left_x = anchor_top_left.x() - self.width() + x_overlap

            y = anchor_top_right.y() + y_offset

            self._side = "right"
            x = right_x

            available = self._screen_geometry_for_anchor()
            if available is not None:
                margin = 8
                if right_x + self.width() > available.right() - margin:
                    self._side = "left"
                    x = left_x

            fitted = self._fit_to_screen(x, y)
            self.move(fitted)
            self.update()

    def show_below(self, anchor_widget, x_offset: int = 0, y_overlap: int = 1) -> None:
        if anchor_widget is None:
            return

        self._show_mode = "below"
        self._show_args = {
            "x_offset": x_offset,
            "y_overlap": y_overlap,
        }

        self._install_anchor_tracking(anchor_widget)
        self.adjustSize()
        self._reposition_to_anchor()
        self.show()
        self.raise_()
        self.activateWindow()

    def show_right_of(
        self,
        anchor_widget,
        x_overlap: int = 6,
        y_offset: int = 0,
        x_gap: int | None = None,
    ) -> None:
        if anchor_widget is None:
            return

        self._show_mode = "right_of"
        self._show_args = {
            "x_overlap": x_overlap,
            "y_offset": y_offset,
            "x_gap": x_gap,
        }

        self._install_anchor_tracking(anchor_widget)
        self.adjustSize()
        self._reposition_to_anchor()
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_and_emit(self) -> None:
        self.hide()
        self.closed.emit()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._outside_filter_installed:
            QApplication.instance().installEventFilter(self)
            self._outside_filter_installed = True
        self._reposition_to_anchor()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        if self._outside_filter_installed:
            QApplication.instance().removeEventFilter(self)
            self._outside_filter_installed = False

    def eventFilter(self, obj, event):
        if obj is self._anchor_widget or obj is self._anchor_window:
            if event.type() in (
                QEvent.Type.Move,
                QEvent.Type.Resize,
                QEvent.Type.Show,
                QEvent.Type.Hide,
                QEvent.Type.LayoutRequest,
                QEvent.Type.WindowStateChange,
            ):
                if event.type() == QEvent.Type.Hide and obj is self._anchor_widget:
                    if self.isVisible():
                        self.hide_and_emit()
                    return False

                self._reposition_to_anchor()
                return False

        if not self.isVisible():
            return False

        if event.type() == QEvent.Type.MouseButtonPress:
            try:
                global_pos = event.globalPosition().toPoint()
            except Exception:
                return False

            inside_popup = self.frameGeometry().contains(global_pos)

            inside_anchor = False
            if self._anchor_widget is not None:
                local_pos = self._anchor_widget.mapFromGlobal(global_pos)
                inside_anchor = self._anchor_widget.rect().contains(local_pos)

            if not inside_popup and not inside_anchor:
                self.hide_and_emit()

            return False

        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self.hide_and_emit()
            return True

        return False

    def _build_popup_path(self, rect: QRectF, radius: float) -> QPainterPath:
        left = rect.left()
        top = rect.top()
        right = rect.right()
        bottom = rect.bottom()

        path = QPainterPath()

        if self._side == "right":
            path.moveTo(left, top)
            path.lineTo(right - radius, top)
            path.arcTo(QRectF(right - 2 * radius, top, 2 * radius, 2 * radius), 90, -90)
            path.lineTo(right, bottom - radius)
            path.arcTo(
                QRectF(right - 2 * radius, bottom - 2 * radius, 2 * radius, 2 * radius),
                0,
                -90,
            )
            path.lineTo(left + radius, bottom)
            path.arcTo(
                QRectF(left, bottom - 2 * radius, 2 * radius, 2 * radius),
                270,
                -90,
            )
            path.lineTo(left, top)
            path.closeSubpath()
        else:
            path.moveTo(left + radius, top)
            path.lineTo(right, top)
            path.lineTo(right, bottom - radius)
            path.arcTo(
                QRectF(right - 2 * radius, bottom - 2 * radius, 2 * radius, 2 * radius),
                0,
                -90,
            )
            path.lineTo(left + radius, bottom)
            path.arcTo(
                QRectF(left, bottom - 2 * radius, 2 * radius, 2 * radius),
                270,
                -90,
            )
            path.lineTo(left, top + radius)
            path.arcTo(QRectF(left, top, 2 * radius, 2 * radius), 180, -90)
            path.lineTo(right, top)
            path.closeSubpath()

        return path

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.container.geometry())
        radius = 10

        bg_path = self._build_popup_path(rect, radius)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.theme.get_color("bg_tertiary")))
        painter.drawPath(bg_path)