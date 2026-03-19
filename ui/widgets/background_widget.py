import base64

from PyQt6.QtCore import QByteArray, QBuffer, QEvent, QIODevice, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QGraphicsBlurEffect,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QWidget,
)


def encode_image_to_base64(file_path: str, max_size: int = 1920) -> str:
    pixmap = QPixmap(file_path)
    if pixmap.isNull():
        return ""
    if pixmap.width() > max_size or pixmap.height() > max_size:
        pixmap = pixmap.scaled(
            max_size,
            max_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buf, "JPEG", 85)
    buf.close()
    return base64.b64encode(ba.data()).decode("utf-8")


def decode_base64_to_pixmap(data: str) -> QPixmap:
    if not data:
        return QPixmap()
    try:
        raw = base64.b64decode(data)
        pm = QPixmap()
        pm.loadFromData(raw)
        return pm
    except Exception:
        return QPixmap()


def blur_pixmap(pixmap: QPixmap, radius: float) -> QPixmap:
    if radius <= 0.5 or pixmap.isNull():
        return QPixmap(pixmap)
    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(pixmap)
    effect = QGraphicsBlurEffect()
    effect.setBlurRadius(radius)
    effect.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
    item.setGraphicsEffect(effect)
    scene.addItem(item)
    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    scene.render(painter)
    painter.end()
    return result


class BackgroundImageWidget(QWidget):

    def __init__(self, parent: QWidget = None, border_radius: int = 16, border_inset: int = 0):
        super().__init__(parent)
        self._source_pixmap: QPixmap | None = None
        self._blur_percent: int = 0
        self._opacity_percent: int = 100
        self._border_radius: int = border_radius
        self._border_inset: int = border_inset
        self._base_color: QColor = QColor("#0F111A")

        self._cached_blurred: QPixmap | None = None
        self._cached_blur_val: float = -1.0
        self._cached_scaled: QPixmap | None = None
        self._cached_scaled_key: tuple[int, int] = (0, 0)

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background:transparent;border:none;")
        if parent is not None:
            parent.installEventFilter(self)
            self._fit_to_parent()
            self.lower()

    def set_image(self, pixmap: QPixmap | None) -> None:
        self._source_pixmap = pixmap
        self._invalidate()
        self.update()

    def set_image_from_base64(self, data: str) -> None:
        self.set_image(decode_base64_to_pixmap(data) if data else None)

    def set_blur_percent(self, v: int) -> None:
        self._blur_percent = max(0, min(100, v))
        self._invalidate()
        self.update()

    def set_opacity_percent(self, v: int) -> None:
        self._opacity_percent = max(0, min(100, v))
        self.update()

    def set_base_color(self, c) -> None:
        self._base_color = QColor(c) if isinstance(c, str) else QColor(c)
        self.update()

    def set_border_radius(self, r: int) -> None:
        self._border_radius = r
        self.update()

    def has_image(self) -> bool:
        return self._source_pixmap is not None and not self._source_pixmap.isNull()

    def _invalidate(self) -> None:
        self._cached_blurred = None
        self._cached_scaled = None
        self._cached_scaled_key = (0, 0)

    def _get_blurred(self) -> QPixmap | None:
        if not self._source_pixmap or self._source_pixmap.isNull():
            return None
        r = self._blur_percent * 0.5
        if self._cached_blurred is not None and self._cached_blur_val == r:
            return self._cached_blurred
        self._cached_blurred = blur_pixmap(self._source_pixmap, r)
        self._cached_blur_val = r
        self._cached_scaled = None
        return self._cached_blurred

    def _get_scaled(self) -> QPixmap | None:
        bl = self._get_blurred()
        if bl is None:
            return None
        key = (self.width(), self.height())
        if self._cached_scaled is not None and self._cached_scaled_key == key:
            return self._cached_scaled
        self._cached_scaled = bl.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._cached_scaled_key = key
        return self._cached_scaled

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type() == QEvent.Type.Resize:
            self._fit_to_parent()
            self._cached_scaled = None
        return super().eventFilter(obj, event)

    def _fit_to_parent(self) -> None:
        p = self.parent()
        if p is None:
            return
        b = self._border_inset
        self.setGeometry(b, b, p.width() - 2 * b, p.height() - 2 * b)

    def paintEvent(self, event) -> None:
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), self._border_radius, self._border_radius)
        painter.setClipPath(path)
        opacity = self._opacity_percent / 100.0

        if self._source_pixmap and not self._source_pixmap.isNull():
            sc = self._get_scaled()
            if sc and not sc.isNull():
                painter.setOpacity(opacity)
                ox = (sc.width() - w) // 2
                oy = (sc.height() - h) // 2
                painter.drawPixmap(-ox, -oy, sc)
        else:
            c = QColor(self._base_color)
            c.setAlpha(int(opacity * 255))
            painter.fillRect(self.rect(), c)
        painter.end()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._cached_scaled = None