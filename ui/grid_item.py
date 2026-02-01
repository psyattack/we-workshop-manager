import json
from pathlib import Path
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QMovie, QFontMetrics, QPixmapCache
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class GridItemWidget(QWidget):
    clicked = pyqtSignal(str)  # folder_path

    def __init__(self, folder_path: str, item_size: int = 185, parent=None):
        super().__init__(parent)

        self.folder_path = folder_path
        self.item_size = item_size
        self.movie = None
        self._original_title = ""

        self.setFixedSize(self.item_size, self.item_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.overlay_container = QWidget()
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
        self.name_container.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, 180);
            border-radius: 0px;
        """)
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

        self._load_data()

    def _load_data(self):
        title = self._load_title_from_json()
        self._original_title = title if title else Path(self.folder_path).name
        self._set_elided_text(self._original_title)

        self._load_preview()

    def _set_elided_text(self, text: str):
        metrics = QFontMetrics(self.name_label.font())
        max_width = self.name_label.maximumWidth()
        elided = metrics.elidedText(text, Qt.TextElideMode.ElideRight, max_width)
        self.name_label.setText(elided)

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
            self.preview_label.setText("No preview")
            self.preview_label.setStyleSheet("color: gray; font-size: 14px; background-color: #25283d;")
            return

        try:
            ext = preview_file.suffix.lower()

            if ext == ".gif":
                self.movie = QMovie(str(preview_file))
                self.movie.setScaledSize(QSize(self.item_size, self.item_size))
                self.preview_label.setMovie(self.movie)
                self.movie.start()
            else:
                pixmap = QPixmap(str(preview_file))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        self.item_size, self.item_size,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled)
                else:
                    self.preview_label.setText("Invalid image")
                    self.preview_label.setStyleSheet("color: gray; font-size: 14px;")

        except Exception as e:
            print(f"Error loading preview: {e}")
            self.preview_label.setText("Error loading")
            self.preview_label.setStyleSheet("color: gray; font-size: 14px;")

    def enterEvent(self, event):
        enlarged_size = self.item_size + 15

        if self.movie:
            self.movie.setScaledSize(QSize(enlarged_size, enlarged_size))
        elif self.preview_label.pixmap() and not self.preview_label.pixmap().isNull():
            pixmap = self.preview_label.pixmap()
            scaled = pixmap.scaled(
                enlarged_size, enlarged_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)

        self.name_container.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, 120);
            border-radius: 0px;
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.movie:
            self.movie.setScaledSize(QSize(self.item_size, self.item_size))
        elif self.preview_label.pixmap() and not self.preview_label.pixmap().isNull():
            pixmap = self.preview_label.pixmap()
            scaled = pixmap.scaled(
                self.item_size, self.item_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)

        self.name_container.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, 180);
            border-radius: 0px;
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.folder_path)
        super().mousePressEvent(event)

    def release_resources(self):
        try:
            if hasattr(self, 'movie') and self.movie:
                self.movie.stop()
                self.movie.setPaused(True)
                self.preview_label.setMovie(None)
                self.movie.deleteLater()
                self.movie = None

            if hasattr(self, 'preview_label'):
                self.preview_label.clear()
                self.preview_label.setPixmap(QPixmap())

            QPixmapCache.clear()

        except Exception as e:
            print(f"Error in release_resources: {e}")
