from PyQt6.QtCore import Qt, QSize, pyqtSignal, QUrl, QByteArray, QBuffer
from PyQt6.QtGui import QPixmap, QFontMetrics, QMovie
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import weakref

class WorkshopGridItem(QWidget):
    
    clicked = pyqtSignal(str)  # pubfileid
    
    _network_manager = None
    
    STATUS_AVAILABLE = "available"
    STATUS_INSTALLED = "installed"
    STATUS_DOWNLOADING = "downloading"
    
    def __init__(
        self,
        pubfileid: str,
        title: str = "",
        preview_url: str = "",
        item_size: int = 185,
        parent=None
    ):
        super().__init__(parent)
        
        self.pubfileid = pubfileid
        self.title = title
        self.preview_url = preview_url
        self.item_size = item_size
        self.status = self.STATUS_AVAILABLE
        
        self._pixmap = None
        self._movie = None
        self._gif_buffer = None
        self._buffer = None
        self._is_gif = False
        self._is_loading = False
        self._is_hovered = False
        self._is_destroyed = False
        self._current_reply = None
        
        self._setup_ui()
        self._load_preview()
    
    @classmethod
    def get_network_manager(cls) -> QNetworkAccessManager:
        if cls._network_manager is None:
            cls._network_manager = QNetworkAccessManager()
        return cls._network_manager
    
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
        self._set_elided_text(self.title if self.title else self.pubfileid)
        name_layout.addWidget(self.name_label)
        
        self.status_indicator = QLabel(self.overlay_container)
        self.status_indicator.setFixedSize(24, 24)
        self.status_indicator.move(self.item_size - 28, 4)
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_indicator.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
            border-radius: 12px;
            font-size: 12px;
        """)
        self.status_indicator.hide()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.overlay_container)
    
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
    
    def _load_preview(self):
        if not self.preview_url or self._is_loading or self._is_destroyed:
            self._show_placeholder()
            return
        
        self._is_loading = True
        self._show_loading()
        
        manager = self.get_network_manager()
        request = QNetworkRequest(QUrl(self.preview_url))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy
        )
        
        self._current_reply = manager.get(request)

        weak_self = weakref.ref(self)
        
        def on_finished():
            self_ref = weak_self()
            if self_ref is not None and not self_ref._is_destroyed:
                self_ref._on_preview_loaded()
        
        self._current_reply.finished.connect(on_finished)
    
    def _on_preview_loaded(self):
        if self._is_destroyed:
            return
        
        self._is_loading = False
        
        reply = self._current_reply
        if reply is None:
            return
        
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self._show_placeholder()
                reply.deleteLater()
                self._current_reply = None
                return
            
            data = reply.readAll()
            content_type = reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader)
            url = reply.url().toString().lower()
            
            is_gif = False
            if content_type and 'gif' in str(content_type).lower():
                is_gif = True
            elif url.endswith('.gif'):
                is_gif = True
            
            if is_gif:
                self._is_gif = True
                self._load_gif(data)
            else:
                self._is_gif = False
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    self._pixmap = pixmap
                    self._apply_pixmap(self.item_size)
                else:
                    self._show_placeholder()
            
            reply.deleteLater()
            self._current_reply = None
            
        except Exception as e:
            print(f"[WorkshopGridItem] Preview load error: {e}")
            self._show_placeholder()
            if self._current_reply:
                self._current_reply.deleteLater()
                self._current_reply = None
    
    def _load_gif(self, data: QByteArray):
        if self._is_destroyed:
            return
        
        try:
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
            print(f"[WorkshopGridItem] GIF load error: {e}")
            self._show_placeholder()
    
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
    
    def _show_loading(self):
        if self._is_destroyed:
            return
        try:
            self.preview_label.setText("⏳")
            self.preview_label.setStyleSheet("""
                color: #6B6E7C;
                font-size: 32px;
                background-color: #25283d;
            """)
        except RuntimeError:
            pass
    
    def _show_placeholder(self):
        if self._is_destroyed:
            return
        try:
            self.preview_label.setText("🖼️")
            self.preview_label.setStyleSheet("""
                color: #6B6E7C;
                font-size: 32px;
                background-color: #25283d;
            """)
        except RuntimeError:
            pass
    
    def set_status(self, status: str):
        if self._is_destroyed:
            return
        
        self.status = status
        
        try:
            if status == self.STATUS_INSTALLED:
                self.status_indicator.setText("✅")
                self.status_indicator.show()
            elif status == self.STATUS_DOWNLOADING:
                self.status_indicator.setText("⬇️")
                self.status_indicator.show()
            else:
                self.status_indicator.hide()
        except RuntimeError:
            pass
    
    def set_title(self, title: str):
        self.title = title
        self._set_elided_text(title)
    
    def enterEvent(self, event):
        if self._is_destroyed:
            return
        
        self._is_hovered = True
        
        try:
            enlarged_size = self.item_size + 15
            
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
            self.clicked.emit(self.pubfileid)
        super().mousePressEvent(event)
    
    def release_resources(self):
        self._is_destroyed = True

        if self._current_reply is not None:
            try:
                self._current_reply.abort()
                self._current_reply.deleteLater()
            except RuntimeError:
                pass
            self._current_reply = None
        
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


class SkeletonGridItem(QWidget):

    def __init__(self, item_size: int = 185, parent=None):
        super().__init__(parent)
        
        self.item_size = item_size
        
        self.setFixedSize(item_size, item_size)
        
        self.setStyleSheet(f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #25283d,
                stop:0.5 #2d3148,
                stop:1 #25283d
            );
            border-radius: 0px;
        """)
