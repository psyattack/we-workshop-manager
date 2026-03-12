from collections import OrderedDict
from typing import Optional

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class ImageCache(QObject):
    image_loaded = pyqtSignal(str, QPixmap)
    gif_loaded = pyqtSignal(str, QByteArray)
    load_failed = pyqtSignal(str, str)

    _instance: Optional["ImageCache"] = None

    MAX_PIXMAP_CACHE = 400
    MAX_GIF_CACHE = 200
    MAX_MEMORY_MB = 300

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        super().__init__()
        self._initialized = True

        self._pixmap_cache: OrderedDict[str, QPixmap] = OrderedDict()
        self._gif_cache: OrderedDict[str, QByteArray] = OrderedDict()
        self._pixmap_sizes: dict[str, int] = {}
        self._gif_sizes: dict[str, int] = {}
        self._total_memory = 0

        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._on_request_finished)

        self._pending_requests: dict[str, tuple[QNetworkReply, list]] = {}

    @classmethod
    def instance(cls) -> "ImageCache":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_pixmap(self, url: str) -> Optional[QPixmap]:
        if url in self._pixmap_cache:
            self._pixmap_cache.move_to_end(url)
            return self._pixmap_cache[url]
        return None

    def get_gif(self, url: str) -> Optional[QByteArray]:
        if url in self._gif_cache:
            self._gif_cache.move_to_end(url)
            return self._gif_cache[url]
        return None

    def is_cached(self, url: str) -> bool:
        return url in self._pixmap_cache or url in self._gif_cache

    def is_gif_cached(self, url: str) -> bool:
        return url in self._gif_cache

    def load_image(self, url: str, callback=None, priority: bool = False) -> bool:
        if not url:
            return False

        if url in self._pixmap_cache:
            self._pixmap_cache.move_to_end(url)
            if callback:
                callback(url, self._pixmap_cache[url], False)
            return True

        if url in self._gif_cache:
            self._gif_cache.move_to_end(url)
            if callback:
                callback(url, self._gif_cache[url], True)
            return True

        if url in self._pending_requests:
            if callback:
                self._pending_requests[url][1].append(callback)
            return False

        request = QNetworkRequest(QUrl(url))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0")

        reply = self._network_manager.get(request)
        callbacks = [callback] if callback else []
        self._pending_requests[url] = (reply, callbacks)
        return False

    def _on_request_finished(self, reply: QNetworkReply):
        url = reply.url().toString()
        callbacks = []

        if url in self._pending_requests:
            _, callbacks = self._pending_requests.pop(url)

        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_message = reply.errorString()
            self.load_failed.emit(url, error_message)

            for callback in callbacks:
                if callback:
                    try:
                        callback(url, None, False)
                    except Exception:
                        pass

            reply.deleteLater()
            return

        data = reply.readAll()
        is_gif = self._is_gif_data(data)

        if is_gif:
            self._cache_gif(url, data)
            self.gif_loaded.emit(url, data)

            for callback in callbacks:
                if callback:
                    try:
                        callback(url, data, True)
                    except Exception:
                        pass
        else:
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                self._cache_pixmap(url, pixmap)
                self.image_loaded.emit(url, pixmap)

                for callback in callbacks:
                    if callback:
                        try:
                            callback(url, pixmap, False)
                        except Exception:
                            pass
            else:
                self.load_failed.emit(url, "Failed to decode image")
                for callback in callbacks:
                    if callback:
                        try:
                            callback(url, None, False)
                        except Exception:
                            pass

        reply.deleteLater()

    def _is_gif_data(self, data: QByteArray) -> bool:
        if data.size() < 6:
            return False

        header = bytes(data[:6])
        return header.startswith(b"GIF87a") or header.startswith(b"GIF89a")

    def _cache_pixmap(self, url: str, pixmap: QPixmap) -> None:
        size_bytes = pixmap.width() * pixmap.height() * 4
        self._enforce_limits(size_bytes, is_gif=False)
        self._pixmap_cache[url] = pixmap
        self._pixmap_sizes[url] = size_bytes
        self._total_memory += size_bytes

    def _cache_gif(self, url: str, data: QByteArray) -> None:
        size_bytes = data.size()
        self._enforce_limits(size_bytes, is_gif=True)
        self._gif_cache[url] = QByteArray(data)
        self._gif_sizes[url] = size_bytes
        self._total_memory += size_bytes

    def _enforce_limits(self, new_size: int, is_gif: bool) -> None:
        max_memory = self.MAX_MEMORY_MB * 1024 * 1024

        while self._total_memory + new_size > max_memory:
            if len(self._pixmap_cache) > self.MAX_PIXMAP_CACHE:
                self._evict_pixmap()
            elif len(self._gif_cache) > self.MAX_GIF_CACHE:
                self._evict_gif()
            elif self._pixmap_cache:
                self._evict_pixmap()
            elif self._gif_cache:
                self._evict_gif()
            else:
                break

        while len(self._pixmap_cache) >= self.MAX_PIXMAP_CACHE:
            self._evict_pixmap()

        if is_gif:
            while len(self._gif_cache) >= self.MAX_GIF_CACHE:
                self._evict_gif()

    def _evict_pixmap(self) -> None:
        if not self._pixmap_cache:
            return

        url, _ = self._pixmap_cache.popitem(last=False)
        self._total_memory -= self._pixmap_sizes.pop(url, 0)

    def _evict_gif(self) -> None:
        if not self._gif_cache:
            return

        url, _ = self._gif_cache.popitem(last=False)
        self._total_memory -= self._gif_sizes.pop(url, 0)

    def cancel_request(self, url: str) -> None:
        if url not in self._pending_requests:
            return

        reply, _ = self._pending_requests.pop(url)
        try:
            reply.abort()
            reply.deleteLater()
        except Exception:
            pass

    def clear(self) -> None:
        for _, (reply, _) in list(self._pending_requests.items()):
            try:
                reply.abort()
                reply.deleteLater()
            except Exception:
                pass

        self._pending_requests.clear()
        self._pixmap_cache.clear()
        self._gif_cache.clear()
        self._pixmap_sizes.clear()
        self._gif_sizes.clear()
        self._total_memory = 0

    def clear_except(self, keep_urls: set[str]) -> None:
        for url in list(self._pixmap_cache.keys()):
            if url not in keep_urls:
                self._pixmap_cache.pop(url, None)
                self._total_memory -= self._pixmap_sizes.pop(url, 0)

        for url in list(self._gif_cache.keys()):
            if url not in keep_urls:
                self._gif_cache.pop(url, None)
                self._total_memory -= self._gif_sizes.pop(url, 0)

    def get_stats(self) -> dict:
        return {
            "pixmap_count": len(self._pixmap_cache),
            "gif_count": len(self._gif_cache),
            "total_memory_mb": self._total_memory / (1024 * 1024),
            "pending_requests": len(self._pending_requests),
        }

    def preload(self, urls: list[str]) -> None:
        for url in urls:
            if url and not self.is_cached(url):
                self.load_image(url)