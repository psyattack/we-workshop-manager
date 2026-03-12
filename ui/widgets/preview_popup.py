import weakref
from typing import Optional

from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QPoint, Qt
from PyQt6.QtGui import QMovie, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from infrastructure.cache.image_cache import ImageCache
from shared.formatting import hex_to_rgba


class PreviewPopup(QWidget):
    def __init__(self, theme_manager, translator, parent=None):
        super().__init__(parent)

        self.theme = theme_manager
        self.tr = translator

        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(156, 156)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        background = hex_to_rgba(self.theme.get_color("bg_secondary"), 230)
        self.container.setStyleSheet(
            f"""
            background-color: {background};
            border-radius: 8px;
            border: 2px solid {self.theme.get_color('primary')};
            """
        )

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(3, 3, 3, 3)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(150, 150)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: transparent; border: none;")

        container_layout.addWidget(self.preview_label)
        layout.addWidget(self.container)

        self._current_url: str = ""
        self._current_movie: Optional[QMovie] = None
        self._current_buffer: Optional[QBuffer] = None

    def show_preview(self, preview_url: str, global_pos: QPoint) -> None:
        if not preview_url:
            self._stop_current_movie()
            self.preview_label.setText(self.tr.t("labels.no_preview"))
            self.show()
            return

        x_position = global_pos.x() - self.width() - 10
        if x_position < 0:
            x_position = global_pos.x() + 10

        self.move(x_position, global_pos.y() - 35)
        self.show()

        if preview_url == self._current_url:
            return

        self._current_url = preview_url
        cache = ImageCache.instance()

        gif_data = cache.get_gif(preview_url)
        if gif_data:
            self._play_gif_from_data(gif_data)
            return

        pixmap = cache.get_pixmap(preview_url)
        if pixmap:
            self._stop_current_movie()
            self._set_pixmap(
                pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            return

        self._stop_current_movie()
        self.preview_label.setText(self.tr.t("labels.loading_dots"))

        weak_self = weakref.ref(self)
        expected_url = preview_url

        def on_loaded(url: str, data, is_gif: bool):
            self_ref = weak_self()
            if self_ref is None or not self_ref.isVisible():
                return
            if self_ref._current_url != expected_url:
                return

            if data is None:
                self_ref._show_error(self_ref.tr.t("messages.load_failed"))
                return

            if is_gif:
                self_ref._play_gif_from_data(data)
            else:
                self_ref._stop_current_movie()
                self_ref._set_pixmap(
                    data.scaled(
                        150,
                        150,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        cache.load_image(preview_url, callback=on_loaded)

    def hide_preview(self) -> None:
        self._current_url = ""
        self._stop_current_movie()
        self.hide()

    def force_cancel(self) -> None:
        self._current_url = ""
        self._stop_current_movie()

    def _play_gif_from_data(self, data: QByteArray) -> None:
        self._stop_current_movie()

        self._current_buffer = QBuffer()
        self._current_buffer.setData(data)
        self._current_buffer.open(QIODevice.OpenModeFlag.ReadOnly)

        self._current_movie = QMovie()
        self._current_movie.setDevice(self._current_buffer)
        self._current_movie.setScaledSize(self._calculate_scaled_size(self._current_movie))

        self.preview_label.setStyleSheet("background: transparent; border: none;")
        self.preview_label.setText("")
        self.preview_label.setMovie(self._current_movie)

        self._current_movie.frameChanged.connect(self._on_gif_frame_changed)
        self._current_movie.start()

    def _calculate_scaled_size(self, movie: QMovie):
        movie.jumpToFrame(0)
        original_size = movie.currentImage().size()
        if original_size.isEmpty():
            return movie.scaledSize()
        return original_size.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)

    def _on_gif_frame_changed(self, frame_number: int) -> None:
        if self._current_movie is None:
            return

        current_pixmap = self._current_movie.currentPixmap()
        if not current_pixmap.isNull():
            self.preview_label.setPixmap(self._create_rounded_pixmap(current_pixmap, radius=6))

    def _stop_current_movie(self) -> None:
        if self._current_movie is not None:
            self._current_movie.stop()
            self.preview_label.setMovie(None)
            self._current_movie.deleteLater()
            self._current_movie = None

        if self._current_buffer is not None:
            self._current_buffer.close()
            self._current_buffer = None

    def _set_pixmap(self, pixmap: QPixmap) -> None:
        self.preview_label.setStyleSheet("background: transparent; border: none;")
        self.preview_label.setText("")
        self.preview_label.setPixmap(self._create_rounded_pixmap(pixmap, radius=6))

    def _create_rounded_pixmap(self, pixmap: QPixmap, radius: int = 6) -> QPixmap:
        if pixmap.isNull():
            return pixmap

        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        path = QPainterPath()
        path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return rounded

    def _show_error(self, message: str) -> None:
        self._stop_current_movie()
        self.preview_label.setText(message)
        self.preview_label.setStyleSheet(
            f"""
            background: transparent;
            border: none;
            color: {self.theme.get_color('text_disabled')};
            font-size: 11px;
            """
        )