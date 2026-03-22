from dataclasses import asdict
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from domain.models.wallpaper import WallpaperMetadata
from shared.date_utils import parse_workshop_date_to_timestamp


class MetadataBatchInitializer(QObject):
    progress_updated = pyqtSignal(int, int)  # initialized, total
    finished = pyqtSignal()

    def __init__(self, pubfileids: list[str], parser, metadata_service, parent=None):
        super().__init__(parent)
        self._pubfileids = list(pubfileids)
        self._parser = parser
        self._metadata_service = metadata_service
        self._total = len(self._pubfileids)
        self._initialized = 0
        self._current_index = 0
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running or not self._pubfileids:
            self.finished.emit()
            return
        self._running = True
        self._current_index = 0
        self._initialized = 0
        self._fetch_next()

    def cancel(self) -> None:
        self._running = False

    def _fetch_next(self) -> None:
        if not self._running:
            return

        if self._current_index >= self._total:
            self._running = False
            self.finished.emit()
            return

        try:
            current_url = self._parser._webview.url().toString()
            if "steamcommunity.com" not in current_url:
                QTimer.singleShot(2000, self._fetch_next)
                return
        except Exception:
            QTimer.singleShot(2000, self._fetch_next)
            return

        pubfileid = self._pubfileids[self._current_index]
        self._parser.fetch_item_details_background(
            pubfileid, self._on_item_fetched
        )

    def _on_item_fetched(self, item) -> None:
        if not self._running:
            return

        if item is not None:
            try:
                self._metadata_service.save_from_workshop_item(item)
            except Exception:
                pass

        self._initialized += 1
        self._current_index += 1
        self.progress_updated.emit(self._initialized, self._total)

        QTimer.singleShot(300, self._fetch_next)


class MetadataService:
    def __init__(self, config_service):
        self.config_service = config_service

    def get(self, pubfileid: str) -> Optional[WallpaperMetadata]:
        raw = self.config_service.get_wallpaper_metadata(pubfileid)
        if not raw or not isinstance(raw, dict):
            return None
        try:
            return WallpaperMetadata(**raw)
        except Exception:
            return None

    def get_all(self) -> dict[str, WallpaperMetadata]:
        raw_all = self.config_service.get_all_wallpaper_metadata()
        result: dict[str, WallpaperMetadata] = {}
        for pubfileid, raw in raw_all.items():
            try:
                result[pubfileid] = WallpaperMetadata(**raw)
            except Exception:
                continue
        return result

    def save(self, metadata: WallpaperMetadata) -> None:
        self.config_service.set_wallpaper_metadata(
            metadata.pubfileid,
            asdict(metadata),
        )

    def remove(self, pubfileid: str) -> None:
        self.config_service.remove_wallpaper_metadata(pubfileid)

    def save_from_workshop_item(self, item) -> WallpaperMetadata:
        raw_collections = getattr(item, "collections", []) or []
        normalized_collections = []

        for col in raw_collections:
            if not isinstance(col, dict):
                continue

            col_id = str(col.get("id", "")).strip()
            if not col_id:
                continue

            normalized_collections.append({
                "id": col_id,
                "title": col.get("title", "") or f"Collection {col_id}",
                "item_count": int(col.get("item_count", 0) or 0),
                "url": f"https://steamcommunity.com/sharedfiles/filedetails/?id={col_id}",
            })

        metadata = WallpaperMetadata(
            pubfileid=item.pubfileid,
            title=item.title or item.pubfileid,
            description=item.description or "",
            preview_url=item.preview_url or "",
            author=item.author or "",
            author_url=getattr(item, "author_url", "") or "",
            file_size=item.file_size or "",
            rating=self._rating_from_star_file(
                getattr(item, "rating_star_file", "")
            ),
            num_ratings=getattr(item, "num_ratings", ""),
            rating_star_file=getattr(item, "rating_star_file", ""),
            posted_date=parse_workshop_date_to_timestamp(
                item.posted_date or ""
            ),
            posted_date_str=item.posted_date or "",
            updated_date=parse_workshop_date_to_timestamp(
                item.updated_date or ""
            ),
            updated_date_str=item.updated_date or "",
            tags=item.tags or {},
            collections=normalized_collections,
        )
        self.save(metadata)
        return metadata

    def get_uninitialized_pubfileids(self, installed_folders) -> list[str]:
        result = []
        for folder in installed_folders:
            pubfileid = folder.name
            if not self.get(pubfileid):
                result.append(pubfileid)
        return result

    @staticmethod
    def _rating_from_star_file(star_file: str) -> int:
        return {
            "5-star_large": 5,
            "4-star_large": 4,
            "3-star_large": 3,
            "2-star_large": 2,
            "1-star_large": 1,
        }.get(star_file, 0)