from dataclasses import asdict
from typing import Optional

from domain.models.wallpaper import WallpaperMetadata
from shared.date_utils import parse_workshop_date_to_timestamp


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
        metadata = WallpaperMetadata(
            pubfileid=item.pubfileid,
            title=item.title or item.pubfileid,
            description=item.description or "",
            preview_url=item.preview_url or "",
            author=item.author or "",
            file_size=item.file_size or "",
            rating=self._rating_from_star_file(getattr(item, "rating_star_file", "")),
            num_ratings=getattr(item, "num_ratings", ""),
            rating_star_file=getattr(item, "rating_star_file", ""),
            posted_date=parse_workshop_date_to_timestamp(item.posted_date or ""),
            posted_date_str=item.posted_date or "",
            updated_date=parse_workshop_date_to_timestamp(item.updated_date or ""),
            updated_date_str=item.updated_date or "",
            tags=item.tags or {},
        )
        self.save(metadata)
        return metadata

    @staticmethod
    def _rating_from_star_file(star_file: str) -> int:
        return {
            "5-star_large": 5,
            "4-star_large": 4,
            "3-star_large": 3,
            "2-star_large": 2,
            "1-star_large": 1,
        }.get(star_file, 0)