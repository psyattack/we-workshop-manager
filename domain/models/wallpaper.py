from dataclasses import dataclass, field


@dataclass
class WallpaperMetadata:
    pubfileid: str
    title: str = ""
    description: str = ""
    preview_url: str = ""
    author: str = ""
    author_url: str = ""
    file_size: str = ""
    rating: int = 0
    num_ratings: str = ""
    rating_star_file: str = ""
    posted_date: int = 0
    posted_date_str: str = ""
    updated_date: int = 0
    updated_date_str: str = ""
    tags: dict = field(default_factory=dict)
    collections: list = field(default_factory=list)

@dataclass
class LocalWallpaperEntry:
    path: str
    pubfileid: str
    title: str
    install_date: float
    size: int
    tags: dict = field(default_factory=dict)
    rating: int = 0
    posted_date: int = 0
    updated_date: int = 0