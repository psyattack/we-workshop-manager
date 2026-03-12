from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorkshopItem:
    pubfileid: str
    title: str = ""
    preview_url: str = ""
    author: str = ""
    author_url: str = ""
    description: str = ""
    file_size: str = ""
    posted_date: str = ""
    updated_date: str = ""
    tags: dict = field(default_factory=dict)
    rating_star_file: str = ""
    num_ratings: str = ""
    is_installed: bool = False
    is_downloading: bool = False


@dataclass
class WorkshopFilters:
    search: str = ""
    sort: str = "trend"
    days: str = "7"
    category: str = ""
    type_tag: str = ""
    age_rating: str = ""
    resolution: str = ""
    misc_tags: list[str] = field(default_factory=list)
    genre_tags: list[str] = field(default_factory=list)
    excluded_misc_tags: list[str] = field(default_factory=list)
    excluded_genre_tags: list[str] = field(default_factory=list)
    asset_type: str = ""
    asset_genre: str = ""
    script_type: str = ""
    required_flags: list[str] = field(default_factory=list)
    page: int = 1


@dataclass
class WorkshopPage:
    items: list[WorkshopItem] = field(default_factory=list)
    current_page: int = 1
    total_pages: int = 1
    total_items: int = 0
    filters: Optional[WorkshopFilters] = None