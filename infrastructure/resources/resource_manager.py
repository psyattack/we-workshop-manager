from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPixmap

from infrastructure.resources.resource_data import ICONS_MAP


def _load_pixmap_from_base64(b64_data: str) -> QPixmap:
    byte_array = QByteArray.fromBase64(b64_data.encode("utf-8"))
    pixmap = QPixmap()
    pixmap.loadFromData(byte_array)
    return pixmap


def get_pixmap(
    name: str,
    size: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> QPixmap:
    b64_data = ICONS_MAP.get(name, ICONS_MAP.get("ICON_FOLDER", ""))
    pixmap = _load_pixmap_from_base64(b64_data)

    if pixmap.isNull():
        return pixmap

    if width and height:
        return pixmap.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    if size:
        return pixmap.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    return pixmap


def get_icon(
    name: str,
    size: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> QIcon:
    return QIcon(get_pixmap(name, size=size, width=width, height=height))