import json
import weakref
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QByteArray, QBuffer
from PyQt6.QtGui import QPixmap, QFontMetrics, QMovie, QPixmapCache
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from core.image_cache import ImageCache
from resources.icons import get_pixmap

class BaseGridItem(QWidget):

    clicked = pyqtSignal(str)

    def __init__(self, item_id: str, item_size: int = 185, parent=None):
        super().__init__(parent)

        self.item_id = item_id
        self.item_size = item_size
        self._original_title = ""

        self._pixmap: QPixmap = None
        self._movie: QMovie = None
        self._gif_buffer: QByteArray = None
        self._buffer: QBuffer = None
        self._is_gif = False
        self._is_hovered = False
        self._is_destroyed = False

        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(self.item_size, self.item_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.overlay_container = QWidget(self)
        self.overlay_container.setFixedSize(self.item_size, self.item_size)
        self.overlay_container.setStyleSheet("background-color: transparent;")

        self.preview_label = QLabel(self.overlay_container)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(self.item_size, self.item_size)
        self.preview_label.setStyleSheet("background-color: #25283d;")

        name_container_height = max(24, int(self.item_size * 0.22))
        self.name_container = QWidget(self.overlay_container)
        self.name_container.setFixedHeight(name_container_height)
        self.name_container.setFixedWidth(self.item_size)
        self.name_container.setStyleSheet("background-color: rgba(0, 0, 0, 180); border-radius: 0px;")
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
            max_width = self.name_label.maximumWidth() if self.name_label.maximumWidth() > 0 else self.item_size - 10
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
                Qt.TransformationMode.SmoothTransformation
            )
            if scaled.width() > size or scaled.height() > size:
                x = (scaled.width() - size) // 2
                y = (scaled.height() - size) // 2
                scaled = scaled.copy(x, y, size, size)
            if not self._is_destroyed:
                self.preview_label.setPixmap(scaled)
        except RuntimeError:
            pass

    def _show_placeholder(self, text: str = "🖼️"):
        if self._is_destroyed:
            return
        try:
            self.preview_label.setText(text)
            self.preview_label.setStyleSheet("""
                color: #6B6E7C;
                font-size: 32px;
                background-color: #25283d;
            """)
        except RuntimeError:
            pass

    def _load_gif_from_data(self, data: QByteArray):
        if self._is_destroyed:
            return
        try:
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
            self.name_container.setStyleSheet("background-color: rgba(0, 0, 0, 120); border-radius: 0px;")
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
            self.name_container.setStyleSheet("background-color: rgba(0, 0, 0, 180); border-radius: 0px;")
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
            except:
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

    def __init__(self, pubfileid: str, title: str = "", preview_url: str = "", item_size: int = 185, parent=None):
        super().__init__(item_id=pubfileid, item_size=item_size, parent=parent)

        self.pubfileid = pubfileid
        self.preview_url = preview_url
        self.status = self.STATUS_AVAILABLE
        self._is_loading = False

        self._setup_status_indicator()
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

    def _load_preview(self):
        if not self.preview_url or self._is_loading or self._is_destroyed:
            self._show_placeholder()
            return

        cache = ImageCache.instance()

        pixmap = cache.get_pixmap(self.preview_url)
        if pixmap:
            self._pixmap = pixmap
            self._is_gif = False
            self._apply_pixmap(self.item_size)
            return

        gif_data = cache.get_gif(self.preview_url)
        if gif_data:
            self._load_gif_from_data(gif_data)
            return

        self._is_loading = True
        self._show_placeholder("⏳")

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
                self_ref._is_gif = False
                self_ref._pixmap = data
                self_ref._apply_pixmap(self_ref.item_size)

        cache.load_image(self.preview_url, callback=on_loaded)

    def set_status(self, status: str):
        if self._is_destroyed:
            return
        self.status = status
        try:
            if status == self.STATUS_INSTALLED:
                self.status_indicator.setPixmap(get_pixmap("IMG_CHECK", 18))
                self.status_indicator.show()
            elif status == self.STATUS_DOWNLOADING:
                self.status_indicator.setPixmap(get_pixmap("IMG_DOWNLOAD", 18))
                self.status_indicator.show()
            else:
                self.status_indicator.hide()
        except RuntimeError:
            pass


class LocalGridItem(BaseGridItem):

    def __init__(self, folder_path: str, item_size: int = 185, parent=None):
        super().__init__(item_id=folder_path, item_size=item_size, parent=parent)
        self.folder_path = folder_path
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
            self._show_placeholder("No preview")
            return

        try:
            if preview_file.suffix.lower() == ".gif":
                self._load_gif_from_file(str(preview_file))
            else:
                pixmap = QPixmap(str(preview_file))
                if not pixmap.isNull():
                    self._pixmap = pixmap
                    self._is_gif = False
                    self._apply_pixmap(self.item_size)
                else:
                    self._show_placeholder("Invalid")
        except Exception as e:
            print(f"Error loading preview: {e}")
            self._show_placeholder("Error")

    def release_resources(self):
        super().release_resources()
        QPixmapCache.clear()

class SkeletonGridItem(QWidget):

    def __init__(self, item_size: int = 185, parent=None):
        super().__init__(parent)
        self.item_size = item_size
        self.setFixedSize(item_size, item_size)
        self.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #25283d,
                stop:0.5 #2d3148,
                stop:1 #25283d
            );
            border-radius: 0px;
        """)
 