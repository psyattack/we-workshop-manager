import json
import weakref
from pathlib import Path
from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QByteArray, QBuffer, QRectF,
    QPropertyAnimation, QEasingCurve, pyqtProperty
)
from PyQt6.QtGui import (
    QPixmap, QFontMetrics, QMovie, QPixmapCache,
    QPainter, QPen, QColor, QFont, QTransform
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from core.image_cache import ImageCache
from core.resources import get_pixmap
from utils.helpers import parse_file_size_to_bytes, format_bytes_short, parse_depot_status


class AnimatedHourglassLabel(QLabel):
    def __init__(self, size: int = 32, parent=None):
        super().__init__(parent)
        self._size = size
        self._rotation = 0.0
        self._direction = 1
        self._base_pixmap = get_pixmap("ICON_HOURGLASS", size)
        
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent;")
        self._update_pixmap()
        
        self._animation = QPropertyAnimation(self, b"rotation")
        self._animation.setDuration(1000)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(30.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._animation.finished.connect(self._on_animation_finished)
    
    def get_rotation(self) -> float:
        return self._rotation
    
    def set_rotation(self, value: float):
        self._rotation = value
        self._update_pixmap()
    
    rotation = pyqtProperty(float, get_rotation, set_rotation)
    
    def _update_pixmap(self):
        if self._base_pixmap.isNull():
            return
        transform = QTransform()
        transform.rotate(self._rotation)
        rotated = self._base_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        x = (rotated.width() - self._size) // 2
        y = (rotated.height() - self._size) // 2
        if x >= 0 and y >= 0:
            cropped = rotated.copy(x, y, self._size, self._size)
        else:
            cropped = rotated
        self.setPixmap(cropped)
    
    def _on_animation_finished(self):
        self._direction *= -1
        self._animation.setStartValue(self._rotation)
        self._animation.setEndValue(30.0 * self._direction)
        self._animation.start()
    
    def start_animation(self):
        self._animation.start()
    
    def stop_animation(self):
        self._animation.stop()
        self._rotation = 0.0
        self._update_pixmap()


class _DownloadOverlay(QWidget):
    def __init__(self, size: int, parent=None):
        super().__init__(parent)
        self._size = size
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 150))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self._size, self._size)
        painter.end()


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
            return QColor(self.theme.get_color('primary'))
        return QColor(70, 130, 240)

    def update_from_status(self, status_text: str, file_size_bytes: int = 0):
        parsed = parse_depot_status(status_text)
        dl_bytes = parsed['downloaded_bytes']
        total_bytes = parsed['total_bytes']
        percent = parsed['percent']

        if percent >= 0:
            self._progress = min(1.0, max(0.0, percent / 100.0))
        elif dl_bytes > 0:
            effective_total = total_bytes if total_bytes > 0 else file_size_bytes
            if effective_total > 0:
                self._progress = min(1.0, max(0.0, dl_bytes / effective_total))
            else:
                self._progress = 0.0
        else:
            self._progress = 0.0

        pct_int = int(self._progress * 100)
        if self._progress > 0 or percent >= 0:
            self._display_text = f"{pct_int}%"
        else:
            self._display_text = "0%"

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = self._line_width / 2 + 1
        rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)

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
        painter.drawText(
            QRectF(0, 0, w, h),
            Qt.AlignmentFlag.AlignCenter,
            self._display_text,
        )
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
            return QColor(self.theme.get_color('primary'))
        return QColor(70, 130, 240)

    def update_from_status(self, status_text: str, file_size_bytes: int = 0, is_extraction: bool = False):
        parsed = parse_depot_status(status_text)
        dl_bytes = parsed['downloaded_bytes']
        total_bytes = parsed['total_bytes']
        percent = parsed['percent']

        if percent >= 0:
            self._progress = min(1.0, max(0.0, percent / 100.0))
        elif dl_bytes > 0:
            effective_total = total_bytes if total_bytes > 0 else file_size_bytes
            if effective_total > 0:
                self._progress = min(1.0, max(0.0, dl_bytes / effective_total))
            else:
                self._progress = 0.0
        else:
            self._progress = 0.0

        if is_extraction:
            self._display_text = "%"
        elif dl_bytes > 0:
            self._display_text = format_bytes_short(dl_bytes)
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

        w = self.width()
        h = self.height()
        margin = self._line_width / 2 + 1
        rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)

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
        painter.drawText(
            QRectF(0, 0, w, h),
            Qt.AlignmentFlag.AlignCenter,
            self._display_text,
        )
        painter.end()


class BaseGridItem(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, item_id: str, item_size: int = 185, theme_manager=None, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.item_size = item_size
        self.theme = theme_manager
        self._original_title = ""
        self._pixmap: QPixmap = None
        self._movie: QMovie = None
        self._gif_buffer: QByteArray = None
        self._buffer: QBuffer = None
        self._is_gif = False
        self._is_hovered = False
        self._is_destroyed = False
        self._loading_icon: AnimatedHourglassLabel = None
        
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._setup_ui()

    def _get_bg_color(self) -> str:
        if self.theme:
            return self.theme.get_color('bg_tertiary')
        return '#25283d'

    def _get_placeholder_color(self) -> str:
        if self.theme:
            return self.theme.get_color('text_disabled')
        return '#6B6E7C'

    def _setup_ui(self):
        self.setFixedSize(self.item_size, self.item_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.overlay_container = QWidget(self)
        self.overlay_container.setFixedSize(self.item_size, self.item_size)
        self.overlay_container.setStyleSheet("background-color: transparent;")

        self.preview_label = QLabel(self.overlay_container)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(self.item_size, self.item_size)
        self.preview_label.setStyleSheet(f"background-color: {self._get_bg_color()};")

        name_container_height = max(24, int(self.item_size * 0.22))
        self.name_container = QWidget(self.overlay_container)
        self.name_container.setFixedHeight(name_container_height)
        self.name_container.setFixedWidth(self.item_size)
        self.name_container.setStyleSheet(
            "background-color: rgba(0, 0, 0, 180); border-radius: 0px;"
        )
        self.name_container.move(0, self.item_size - name_container_height)

        name_layout = QVBoxLayout(self.name_container)
        name_layout.setContentsMargins(5, 2, 5, 2)
        name_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_size = max(6, min(12, int(self.item_size / 12)))
        self.name_label.setStyleSheet(f"""
            color: white;
            font-size: {font_size}px;
            font-weight: bold;
            background: transparent;
        """)
        self.name_label.setMaximumHeight(name_container_height - 4)
        self.name_label.setMaximumWidth(self.item_size - 10)
        name_layout.addWidget(self.name_label)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.overlay_container)

    def set_title(self, title: str):
        self._original_title = title
        self._set_elided_text(title)

    def _set_elided_text(self, text: str):
        if self._is_destroyed:
            return
        try:
            metrics = QFontMetrics(self.name_label.font())
            max_width = (
                self.name_label.maximumWidth()
                if self.name_label.maximumWidth() > 0
                else self.item_size - 10
            )
            elided = metrics.elidedText(text, Qt.TextElideMode.ElideRight, max_width)
            self.name_label.setText(elided)
        except RuntimeError:
            pass

    def _apply_pixmap(self, size: int):
        if self._is_destroyed or self._pixmap is None or self._pixmap.isNull():
            return
        try:
            scaled = self._pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            if scaled.width() > size or scaled.height() > size:
                x = (scaled.width() - size) // 2
                y = (scaled.height() - size) // 2
                scaled = scaled.copy(x, y, size, size)
            if not self._is_destroyed:
                self.preview_label.setPixmap(scaled)
        except RuntimeError:
            pass

    def _stop_loading_animation(self):
        if self._loading_icon is not None:
            try:
                self._loading_icon.stop_animation()
                self._loading_icon.setParent(None)
                self._loading_icon.deleteLater()
            except:
                pass
            self._loading_icon = None

    def _show_loading_placeholder(self):
        if self._is_destroyed:
            return
        try:
            self._stop_loading_animation()
            self.preview_label.setText("")
            self.preview_label.setStyleSheet(f"background-color: {self._get_bg_color()};")
            
            icon_size = max(24, int(self.item_size * 0.17))
            self._loading_icon = AnimatedHourglassLabel(icon_size, self.preview_label)
            x = (self.item_size - icon_size) // 2
            y = (self.item_size - icon_size) // 2
            self._loading_icon.move(x, y)
            self._loading_icon.show()
            self._loading_icon.start_animation()
        except RuntimeError:
            pass

    def _show_placeholder(self, text: str = ""):
        if self._is_destroyed:
            return
        try:
            self._stop_loading_animation()
            self.preview_label.setText("")
            self.preview_label.setStyleSheet(f"background-color: {self._get_bg_color()};")
            
            icon_size = max(24, int(self.item_size * 0.17))
            pixmap = get_pixmap("ICON_WALLPAPER", icon_size)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except RuntimeError:
            pass

    def _load_gif_from_data(self, data: QByteArray):
        if self._is_destroyed:
            return
        try:
            self._stop_loading_animation()
            self._is_gif = True
            self._gif_buffer = QByteArray(data)
            self._buffer = QBuffer(self._gif_buffer)
            self._buffer.open(QBuffer.OpenModeFlag.ReadOnly)
            self._movie = QMovie()
            self._movie.setDevice(self._buffer)
            self._movie.setScaledSize(QSize(self.item_size, self.item_size))
            if not self._is_destroyed:
                self.preview_label.setMovie(self._movie)
                self._movie.start()
        except Exception as e:
            print(f"[BaseGridItem] GIF load error: {e}")
            self._show_placeholder()

    def _load_gif_from_file(self, file_path: str):
        if self._is_destroyed:
            return
        try:
            self._stop_loading_animation()
            self._is_gif = True
            self._movie = QMovie(file_path)
            self._movie.setScaledSize(QSize(self.item_size, self.item_size))
            self.preview_label.setMovie(self._movie)
            self._movie.start()
        except Exception as e:
            print(f"[BaseGridItem] GIF file load error: {e}")
            self._show_placeholder()

    def enterEvent(self, event):
        if self._is_destroyed:
            return
        self._is_hovered = True
        enlarged_size = self.item_size + 15
        try:
            if self._is_gif and self._movie:
                self._movie.setScaledSize(QSize(enlarged_size, enlarged_size))
            elif self._pixmap and not self._pixmap.isNull():
                self._apply_pixmap(enlarged_size)
            self.name_container.setStyleSheet(
                "background-color: rgba(0, 0, 0, 120); border-radius: 0px;"
            )
        except RuntimeError:
            pass
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._is_destroyed:
            return
        self._is_hovered = False
        try:
            if self._is_gif and self._movie:
                self._movie.setScaledSize(QSize(self.item_size, self.item_size))
            elif self._pixmap and not self._pixmap.isNull():
                self._apply_pixmap(self.item_size)
            self.name_container.setStyleSheet(
                "background-color: rgba(0, 0, 0, 180); border-radius: 0px;"
            )
        except RuntimeError:
            pass
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._is_destroyed:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item_id)
        super().mousePressEvent(event)

    def release_resources(self):
        self._is_destroyed = True
        self._stop_loading_animation()
        if self._movie is not None:
            try:
                self._movie.stop()
                self.preview_label.setMovie(None)
                self._movie.deleteLater()
            except RuntimeError:
                pass
            self._movie = None
        if self._buffer is not None:
            try:
                self._buffer.close()
            except Exception:
                pass
            self._buffer = None
        self._gif_buffer = None
        self._pixmap = None
        try:
            self.preview_label.clear()
        except RuntimeError:
            pass

    def deleteLater(self):
        self.release_resources()
        super().deleteLater()


class WorkshopGridItem(BaseGridItem):
    STATUS_AVAILABLE = "available"
    STATUS_INSTALLED = "installed"
    STATUS_DOWNLOADING = "downloading"

    def __init__(self, pubfileid: str, title: str = "", preview_url: str = "",
                 item_size: int = 185, theme_manager=None, parent=None):
        super().__init__(item_id=pubfileid, item_size=item_size, theme_manager=theme_manager, parent=parent)
        self.pubfileid = pubfileid
        self.preview_url = preview_url
        self.status = self.STATUS_AVAILABLE
        self._is_loading = False
        self._file_size_bytes = 0
        self._overlay_visible = False

        self._setup_status_indicator()
        self._setup_download_overlay()
        self.set_title(title if title else pubfileid)
        self._load_preview()

    def _setup_status_indicator(self):
        self.status_indicator = QLabel(self.overlay_container)
        self.status_indicator.setFixedSize(30, 30)
        self.status_indicator.move(self.item_size - 33, 4)
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_indicator.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
            border-radius: 12px;
            font-size: 12px;
        """)
        self.status_indicator.hide()

    def _setup_download_overlay(self):
        self.download_overlay = _DownloadOverlay(
            self.item_size, parent=self.overlay_container
        )
        self.download_overlay.move(0, 0)
        self.download_overlay.hide()

        circle_size = max(50, int(self.item_size * 0.38))
        line_width = max(3, int(circle_size / 14))
        self.circular_progress = CircularProgressWidget(
            size=circle_size, line_width=line_width, theme_manager=self.theme, parent=self.download_overlay
        )
        cx = (self.item_size - circle_size) // 2
        cy = (self.item_size - circle_size) // 2
        self.circular_progress.move(cx, cy)

    def set_file_size(self, file_size_str: str):
        self._file_size_bytes = parse_file_size_to_bytes(file_size_str)

    def set_file_size_bytes(self, size_bytes: int):
        self._file_size_bytes = size_bytes

    def _load_preview(self):
        if not self.preview_url or self._is_loading or self._is_destroyed:
            self._show_placeholder()
            return
        cache = ImageCache.instance()
        pixmap = cache.get_pixmap(self.preview_url)
        if pixmap:
            self._stop_loading_animation()
            self._pixmap = pixmap
            self._is_gif = False
            self._apply_pixmap(self.item_size)
            return
        gif_data = cache.get_gif(self.preview_url)
        if gif_data:
            self._load_gif_from_data(gif_data)
            return
        self._is_loading = True
        self._show_loading_placeholder()
        weak_self = weakref.ref(self)
        expected_url = self.preview_url

        def on_loaded(url: str, data, is_gif: bool):
            self_ref = weak_self()
            if self_ref is None or self_ref._is_destroyed:
                return
            if url != expected_url:
                return
            self_ref._is_loading = False
            if data is None:
                self_ref._show_placeholder()
                return
            if is_gif:
                self_ref._load_gif_from_data(data)
            else:
                self_ref._stop_loading_animation()
                self_ref._is_gif = False
                self_ref._pixmap = data
                self_ref._apply_pixmap(self_ref.item_size)

        cache.load_image(self.preview_url, callback=on_loaded)

    def set_status(self, status: str, status_text: str = ""):
        if self._is_destroyed:
            return
        self.status = status
        try:
            if status == self.STATUS_INSTALLED:
                if self._overlay_visible:
                    self.download_overlay.hide()
                    self._overlay_visible = False
                self.status_indicator.setPixmap(get_pixmap("IMG_CHECK", 18))
                self.status_indicator.show()
            elif status == self.STATUS_DOWNLOADING:
                self.status_indicator.hide()
                if not self._overlay_visible:
                    self.download_overlay.show()
                    self.download_overlay.raise_()
                    self.name_container.raise_()
                    self._overlay_visible = True
                self.circular_progress.update_from_status(
                    status_text, self._file_size_bytes
                )
            else:
                if self._overlay_visible:
                    self.download_overlay.hide()
                    self._overlay_visible = False
                self.status_indicator.hide()
        except RuntimeError:
            pass

    def release_resources(self):
        super().release_resources()


class LocalGridItem(BaseGridItem):
    def __init__(self, folder_path: str, item_size: int = 185, theme_manager=None, parent=None):
        super().__init__(item_id=folder_path, item_size=item_size, theme_manager=theme_manager, parent=parent)
        self.folder_path = folder_path
        self.pubfileid = Path(folder_path).name
        self._load_data()

    def _load_data(self):
        title = self._load_title_from_json()
        self.set_title(title if title else Path(self.folder_path).name)
        self._load_preview()

    def _load_title_from_json(self) -> str:
        json_path = Path(self.folder_path) / "project.json"
        if not json_path.exists():
            return ""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("title", "").strip()
        except Exception as e:
            print(f"Error reading project.json: {e}")
            return ""

    def _load_preview(self):
        preview_file = None
        for ext in ["png", "gif", "jpg"]:
            candidate = Path(self.folder_path) / f"preview.{ext}"
            if candidate.exists():
                preview_file = candidate
                break
        if not preview_file:
            self._show_placeholder()
            return
        try:
            if preview_file.suffix.lower() == ".gif":
                self._load_gif_from_file(str(preview_file))
            else:
                self._stop_loading_animation()
                pixmap = QPixmap(str(preview_file))
                if not pixmap.isNull():
                    self._pixmap = pixmap
                    self._is_gif = False
                    self._apply_pixmap(self.item_size)
                else:
                    self._show_placeholder()
        except Exception as e:
            print(f"Error loading preview: {e}")
            self._show_placeholder()

    def release_resources(self):
        super().release_resources()
        QPixmapCache.clear()


class SkeletonGridItem(QWidget):
    def __init__(self, item_size: int = 185, theme_manager=None, parent=None):
        super().__init__(parent)
        self.item_size = item_size
        self.theme = theme_manager
        self.setFixedSize(item_size, item_size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        bg_color = self.theme.get_color('bg_tertiary') if self.theme else '#25283d'
        bg_lighter = self.theme.get_color('bg_elevated') if self.theme else '#2d3148'
        
        self.setStyleSheet(f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {bg_color},
                stop:0.5 {bg_lighter},
                stop:1 {bg_color}
            );
            border-radius: 0px;
        """)