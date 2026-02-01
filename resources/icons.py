from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QByteArray

from content_storage import (
    ICON_FOLDER,
    ICON_WORLD,
    ICON_DELETE,
    ICON_DOWNLOAD,
    ICON_UPLOAD,
    ICON_LINK,
    ICON_TASK,
    ICON_USER_SETTINGS,
    ICON_INFO,
    ICON_HOME,
    ICON_BACK,
    ICON_FORWARD,
    ICON_MINIMIZE,
    ICON_MAXIMIZE,
    ICON_RESTORE,
    ICON_CLOSE
)


def load_icon_from_base64(b64_data: str) -> QIcon:
    byte_array = QByteArray.fromBase64(b64_data.encode('utf-8'))
    pixmap = QPixmap()
    pixmap.loadFromData(byte_array)
    return QIcon(pixmap)


def get_icon(name: str) -> QIcon:
    icons_map = {
        "ICON_FOLDER": ICON_FOLDER,
        "ICON_WORLD": ICON_WORLD,
        "ICON_DELETE": ICON_DELETE,
        "ICON_DOWNLOAD": ICON_DOWNLOAD,
        "ICON_UPLOAD": ICON_UPLOAD,
        "ICON_LINK": ICON_LINK,
        "ICON_TASK": ICON_TASK,
        "ICON_USER_SETTINGS": ICON_USER_SETTINGS,
        "ICON_INFO": ICON_INFO,
        "ICON_HOME": ICON_HOME,
        "ICON_BACK": ICON_BACK,
        "ICON_FORWARD": ICON_FORWARD,
        "ICON_MINIMIZE": ICON_MINIMIZE,
        "ICON_MAXIMIZE": ICON_MAXIMIZE,
        "ICON_RESTORE": ICON_RESTORE,
        "ICON_CLOSE": ICON_CLOSE,
    }
    
    b64_data = icons_map.get(name, ICON_FOLDER)
    return load_icon_from_base64(b64_data)
