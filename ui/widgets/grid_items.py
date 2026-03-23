import json
import weakref
from pathlib import Path

from PyQt6.QtCore import QByteArray, QBuffer, QSize, Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QFontMetrics, QMovie, QPainter, QPixmap, QPixmapCache
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from infrastructure.cache.image_cache import ImageCache
from infrastructure.resources.resource_manager import get_icon, get_pixmap
from shared.helpers import parse_file_size_to_bytes
from ui.widgets.animated_icon_label import AnimatedIconLabel
from ui.widgets.progress import CircularProgressWidget


class DownloadOverlay(QWidget):
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


class BaseGridItem(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, item_id: str, item_size: int = 185, theme_manager=None, parent=None):
        super().__init__(parent)

        self.item_id = item_id
        self.item_size = item_size
        self.theme = theme_manager

        self._original_title = ""
        self._pixmap: QPixmap | None = None
        self._movie: QMovie | None = None
        self._gif_buffer: QByteArray | None = None
        self._buffer: QBuffer | None = None
        self._is_gif = False
        self._is_hovered = False
        self._is_destroyed = False
        self._loading_icon: AnimatedIconLabel | None = None

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._setup_ui()

        self.preview_label.installEventFilter(self)

    def _get_background_color(self) -> str:
        if self.theme:
            return self.theme.get_color("bg_tertiary")
        return "#25283d"

    def _get_placeholder_color(self) -> str:
        if self.theme:
            return self.theme.get_color("text_disabled")
        return "#6B6E7C"

    def _setup_ui(self) -> None:
        self.setFixedSize(self.item_size, self.item_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.overlay_container = QWidget(self)
        self.overlay_container.setFixedSize(self.item_size, self.item_size)
        self.overlay_container.setStyleSheet("background-color: transparent;")

        self.preview_label = QLabel(self.overlay_container)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(self.item_size, self.item_size)
        self.preview_label.setStyleSheet(f"background-color: {self._get_background_color()};")

        name_container_height = max(24, int(self.item_size * 0.22))
        self.name_container = QWidget(self.overlay_container)
        self.name_container.setFixedHeight(name_container_height)
        self.name_container.setFixedWidth(self.item_size)
        self.name_container.setStyleSheet("background-color: rgba(0, 0, 0, 180); border-radius: 0px;")
        self.name_container.move(0, self.item_size - name_container_height)

        name_layout = QVBoxLayout(self.name_container)
        name_layout.setContentsMargins(5, 2, 5, 2)
        name_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.name_label = QLabel(self.name_container)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font_size = max(6, min(12, int(self.item_size / 12)))
        self.name_label.setStyleSheet(
            f"""
            color: white;
            font-size: {font_size}px;
            font-weight: bold;
            background: transparent;
            """
        )
        self.name_label.setMaximumHeight(name_container_height - 4)
        self.name_label.setMaximumWidth(self.item_size - 10)
        name_layout.addWidget(self.name_label)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.overlay_container)

    def set_title(self, title: str) -> None:
        self._original_title = title
        self._set_elided_text(title)

    def _set_elided_text(self, text: str) -> None:
        if self._is_destroyed:
            return

        try:
            metrics = QFontMetrics(self.name_label.font())
            max_width = self.name_label.maximumWidth() if self.name_label.maximumWidth() > 0 else self.item_size - 10
            elided = metrics.elidedText(text, Qt.TextElideMode.ElideRight, max_width)
            self.name_label.setText(elided)
        except RuntimeError:
            pass

    def _apply_pixmap(self, size: int) -> None:
        if self._is_destroyed or self._pixmap is None or self._pixmap.isNull():
            return

        try:
            scaled = self._pixmap.scaled(
                size,
                size,
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

    def eventFilter(self, obj, event):
        if obj is self.preview_label and event.type() == QEvent.Type.Resize:
            self._update_loading_icon_position()
        return super().eventFilter(obj, event)

    def _update_loading_icon_position(self) -> None:
        if self._loading_icon is None or self._is_destroyed:
            return
        
        try:
            icon_size = self._loading_icon.width()
            x = (self.preview_label.width() - icon_size) // 2
            y = (self.preview_label.height() - icon_size) // 2
            self._loading_icon.move(x, y)
        except RuntimeError:
            pass

    def _stop_loading_animation(self) -> None:
        if self._loading_icon is not None:
            try:
                self._loading_icon.stop_animation()
                self._loading_icon.hide()
                self._loading_icon.deleteLater()
            except Exception:
                pass
            self._loading_icon = None

    def _show_loading_placeholder(self) -> None:
        if self._is_destroyed:
            return

        try:
            self._stop_loading_animation()
            self.preview_label.setText("")
            self.preview_label.setStyleSheet(f"background-color: {self._get_background_color()};")

            icon_size = max(24, int(self.item_size * 0.17))
            self._loading_icon = AnimatedIconLabel("ICON_HOURGLASS", icon_size, self.preview_label)

            # Позиционируем относительно текущего размера preview_label
            x = (self.preview_label.width() - icon_size) // 2
            y = (self.preview_label.height() - icon_size) // 2
            self._loading_icon.move(x, y)
            self._loading_icon.show()
            self._loading_icon.start_animation()
        except RuntimeError:
            pass

    def _show_placeholder(self, text: str = "") -> None:
        if self._is_destroyed:
            return

        try:
            self._stop_loading_animation()
            self.preview_label.setText("")
            self.preview_label.setStyleSheet(f"background-color: {self._get_background_color()};")

            icon_size = max(24, int(self.item_size * 0.17))
            pixmap = get_pixmap("ICON_WALLPAPER", icon_size)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except RuntimeError:
            pass

    def _load_gif_from_data(self, data: QByteArray) -> None:
        if self._is_destroyed:
            return

        try:
            self._stop_loading_animation()

            self._is_gif = True
            self._gif_buffer = QByteArray(data)
            self._buffer = QBuffer(self._gif_buffer)
            self._buffer.open(QBuffer.OpenModeFlag.ReadOnly)

            self._movie = QMovie(self)
            self._movie.setDevice(self._buffer)
            self._movie.setScaledSize(QSize(self.item_size, self.item_size))

            if not self._is_destroyed:
                self.preview_label.setMovie(self._movie)

            self._movie.start()
        except Exception:
            self._show_placeholder()

    def _load_gif_from_file(self, file_path: str) -> None:
        if self._is_destroyed:
            return

        try:
            self._stop_loading_animation()

            self._is_gif = True
            self._movie = QMovie(file_path, QByteArray(), self)
            self._movie.setScaledSize(QSize(self.item_size, self.item_size))
            self.preview_label.setMovie(self._movie)
            self._movie.start()
        except Exception:
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

    def release_resources(self) -> None:
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

    def __init__(
        self,
        pubfileid: str,
        title: str = "",
        preview_url: str = "",
        item_size: int = 185,
        theme_manager=None,
        parent=None,
    ):
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

    def _setup_status_indicator(self) -> None:
        self.status_indicator = QLabel(self.overlay_container)
        self.status_indicator.setFixedSize(30, 30)
        self.status_indicator.move(self.item_size - 33, 4)
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_indicator.setStyleSheet(
            """
            background-color: rgba(0, 0, 0, 150);
            border-radius: 12px;
            font-size: 12px;
            """
        )
        self.status_indicator.hide()

    def _setup_download_overlay(self) -> None:
        self.download_overlay = DownloadOverlay(self.item_size, parent=self.overlay_container)
        self.download_overlay.move(0, 0)
        self.download_overlay.hide()

        circle_size = max(50, int(self.item_size * 0.38))
        line_width = max(3, int(circle_size / 14))

        self.circular_progress = CircularProgressWidget(
            size=circle_size,
            line_width=line_width,
            theme_manager=self.theme,
            parent=self.download_overlay,
        )

        cx = (self.item_size - circle_size) // 2
        cy = (self.item_size - circle_size) // 2
        self.circular_progress.move(cx, cy)

    def set_file_size(self, file_size_str: str) -> None:
        self._file_size_bytes = parse_file_size_to_bytes(file_size_str)

    def set_file_size_bytes(self, size_bytes: int) -> None:
        self._file_size_bytes = size_bytes

    def _load_preview(self) -> None:
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

    def set_status(self, status: str, status_text: str = "") -> None:
        if self._is_destroyed:
            return

        self.status = status

        try:
            if status == self.STATUS_INSTALLED:
                if self._overlay_visible:
                    self.download_overlay.hide()
                    self._overlay_visible = False

                self.status_indicator.setPixmap(get_pixmap("ICON_CHECK", 18))
                self.status_indicator.show()

            elif status == self.STATUS_DOWNLOADING:
                self.status_indicator.hide()

                if not self._overlay_visible:
                    self.download_overlay.show()
                    self.download_overlay.raise_()
                    self.name_container.raise_()
                    self._overlay_visible = True

                self.circular_progress.update_from_status(status_text, self._file_size_bytes)

            else:
                if self._overlay_visible:
                    self.download_overlay.hide()
                    self._overlay_visible = False

                self.status_indicator.hide()
        except RuntimeError:
            pass

    def release_resources(self) -> None:
        super().release_resources()


class CollectionGridItem(BaseGridItem):
    back_clicked = pyqtSignal()

    def __init__(
        self,
        pubfileid: str,
        title: str = "",
        preview_url: str = "",
        item_count: int = 0,
        item_size: int = 185,
        theme_manager=None,
        parent=None,
        is_primary_collection_card: bool = False,
        related_count: int = 0,
        show_back_button: bool = False,
        current_collection_text: str = "Current collection",
        related_collections_text: str = "Related Collections",
    ):
        super().__init__(
            item_id=pubfileid,
            item_size=item_size,
            theme_manager=theme_manager,
            parent=parent,
        )
        self.pubfileid = pubfileid
        self.preview_url = preview_url
        self._is_loading = False

        self.is_primary_collection_card = is_primary_collection_card
        self.related_count = related_count
        self.show_back_button = show_back_button
        self.current_collection_text = current_collection_text
        self.related_collections_text = related_collections_text

        self.set_title(title if title else f"Collection {pubfileid}")

        if self.is_primary_collection_card:
            self._setup_primary_collection_overlay()
            if self.show_back_button:
                self._setup_back_button()
        else:
            self._setup_collection_badge(item_count)

        self._load_preview()

    def _setup_collection_badge(self, item_count: int) -> None:
        self.badge = QWidget(self.overlay_container)
        self.badge.setStyleSheet("""
            background-color: rgba(74, 127, 217, 200);
            border-radius: 4px;
            padding: 0;
        """)

        badge_layout = QHBoxLayout(self.badge)
        badge_layout.setContentsMargins(4, 2, 6, 2)
        badge_layout.setSpacing(3)

        folder_icon = QLabel(self.badge)
        folder_icon.setPixmap(get_pixmap("ICON_COLLECTION2", 24))
        folder_icon.setFixedSize(24, 28)
        folder_icon.setStyleSheet("background: transparent; border: none;")
        badge_layout.addWidget(folder_icon)

        if item_count > 0:
            count_label = QLabel(str(item_count))
            count_label.setStyleSheet("""
                color: white;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
                border: none;
            """)
            badge_layout.addWidget(count_label)

        self.badge.adjustSize()
        self.badge.move(4, 4)
        self.badge.raise_()

    def _setup_primary_collection_overlay(self) -> None:
        self.name_container.setStyleSheet(
            "background-color: rgba(0, 0, 0, 160); border-radius: 0px;"
        )
        self.name_container.setFixedHeight(self.item_size)
        self.name_container.setFixedWidth(self.item_size)
        self.name_container.move(0, 0)
        self.name_container.show()

        if hasattr(self, "name_label") and self.name_label is not None:
            self.name_label.hide()

        self.primary_title_label = QLabel(self.current_collection_text, self.name_container)
        self.primary_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.primary_title_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)

        self.primary_related_label = None
        if self.related_count > 0:
            self.primary_related_label = QLabel(
                f"{self.related_collections_text}: {self.related_count}",
                self.name_container,
            )
            self.primary_related_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.primary_related_label.setStyleSheet("""
                color: rgba(255, 255, 255, 220);
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                border: none;
            """)

        self._update_primary_overlay_geometry()
        self.name_container.raise_()

    def _update_primary_overlay_geometry(self) -> None:
        if not self.is_primary_collection_card:
            return

        width = self.item_size
        height = self.item_size

        title_height = 28
        related_height = 22 if self.primary_related_label is not None else 0
        spacing = 4 if self.primary_related_label is not None else 0
        total_height = title_height + related_height + spacing

        start_y = (height - total_height) // 2

        if hasattr(self, "primary_title_label") and self.primary_title_label is not None:
            self.primary_title_label.setGeometry(12, start_y, width - 24, title_height)

        if self.primary_related_label is not None:
            self.primary_related_label.setGeometry(
                12,
                start_y + title_height + spacing,
                width - 24,
                related_height,
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_primary_collection_layout()

    def update_primary_collection_layout(self) -> None:
        if not self.is_primary_collection_card:
            return

        try:
            self.setFixedSize(self.item_size, self.item_size)
            self.overlay_container.setFixedSize(self.item_size, self.item_size)
            self.preview_label.setFixedSize(self.item_size, self.item_size)

            self.name_container.setFixedWidth(self.item_size)
            self.name_container.setFixedHeight(self.item_size)
            self.name_container.move(0, 0)

            if hasattr(self, "name_label") and self.name_label is not None:
                self.name_label.hide()

            self._update_primary_overlay_geometry()

            self.name_container.raise_()

            if hasattr(self, "back_button") and self.back_button is not None:
                self.back_button.move(8, 8)
                self.back_button.raise_()

        except RuntimeError:
            pass

    def _setup_back_button(self) -> None:
        self.back_button = QPushButton(self.overlay_container)
        self.back_button.setFixedSize(28, 28)
        self.back_button.setIcon(get_icon("ICON_BACK"))
        self.back_button.setIconSize(QSize(16, 16))
        self.back_button.move(8, 8)
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 200);
            }
        """)
        self.back_button.clicked.connect(self.back_clicked.emit)
        self.back_button.raise_()

    def mousePressEvent(self, event):
        if self.is_primary_collection_card and self.show_back_button:
            if hasattr(self, "back_button"):
                try:
                    if self.back_button.geometry().contains(event.position().toPoint()):
                        event.accept()
                        return
                except Exception:
                    pass
        super().mousePressEvent(event)

    def _load_preview(self) -> None:
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


class LocalGridItem(BaseGridItem):
    def __init__(self, folder_path: str, item_size: int = 185, theme_manager=None, parent=None):
        super().__init__(item_id=folder_path, item_size=item_size, theme_manager=theme_manager, parent=parent)

        self.folder_path = folder_path
        self.pubfileid = Path(folder_path).name
        self._load_data()

    def _load_data(self) -> None:
        title = self._load_title_from_json()
        self.set_title(title if title else Path(self.folder_path).name)
        self._load_preview()

    def _load_title_from_json(self) -> str:
        json_path = Path(self.folder_path) / "project.json"
        if not json_path.exists():
            return ""

        try:
            with json_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data.get("title", "").strip()
        except Exception:
            return ""

    def _load_preview(self) -> None:
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
        except Exception:
            self._show_placeholder()

    def release_resources(self) -> None:
        super().release_resources()
        QPixmapCache.clear()


class SkeletonGridItem(QWidget):
    def __init__(self, item_size: int = 185, theme_manager=None, parent=None):
        super().__init__(parent)

        self.item_size = item_size
        self.theme = theme_manager

        self.setFixedSize(item_size, item_size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        background = self.theme.get_color("bg_tertiary") if self.theme else "#25283d"
        lighter = self.theme.get_color("bg_elevated") if self.theme else "#2d3148"

        self.setStyleSheet(
            f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {background},
                stop:0.5 {lighter},
                stop:1 {background}
            );
            border-radius: 0px;
            """
        )