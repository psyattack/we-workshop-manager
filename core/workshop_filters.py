from dataclasses import dataclass, field
from typing import List


@dataclass
class FilterConfig:
    """Complete filter configuration for Workshop"""
    
    SORT_OPTIONS = {
        "trend": "Popular",
        "mostrecent": "Most Recent",
        "lastupdated": "Recently Updated",
        "totaluniquesubscribers": "Most Subscribed"
    }

    TIME_PERIODS = {
        "1": "Today",
        "7": "This Week",
        "30": "This Month",
        "90": "3 Months",
        "180": "6 Months",
        "365": "This Year",
        "-1": "All Time"
    }

    CATEGORIES = {
        "": "All",
        "Wallpaper": "Wallpaper",
        "Preset": "Preset",
        "Asset": "Asset"
    }

    TYPES = {
        "": "Any",
        "Scene": "Scene",
        "Video": "Video",
        "Application": "Application",
        "Web": "Web"
    }

    AGE_RATINGS = {
        "": "Any",
        "Everyone": "Everyone",
        "Questionable": "Questionable",
        "Mature": "Mature"
    }
    
    RESOLUTIONS = {
        "": "Any",
        "1920 x 1080": "1080p",
        "2560 x 1440": "1440p",
        "3840 x 2160": "4K",
        "1280 x 720": "720p",
        "1366 x 768": "768p",
        "Ultrawide 2560 x 1080": "UW 1080p",
        "Ultrawide 3440 x 1440": "UW 1440p",
        "Portrait 1080 x 1920": "Portrait 1080p",
        "Dynamic resolution": "Dynamic",
        "Other resolution": "Other"
    }
    
    MISC_TAGS = [
        "Approved", "Audio responsive", "3D", "Customizable",
        "Puppet Warp", "HDR", "Media Integration", "User Shortcut",
        "Video Texture", "Asset Pack"
    ]

    GENRE_TAGS = [
        "Abstract", "Animal", "Anime", "Cartoon", "CGI", "Cyberpunk",
        "Fantasy", "Game", "Girls", "Guys", "Landscape", "Medieval",
        "Memes", "MMD", "Music", "Nature", "Pixel art", "Relaxing",
        "Retro", "Sci-Fi", "Sports", "Technology", "Television",
        "Vehicle", "Unspecified"
    ]
    
    ASSET_TYPES = {
        "": "Any",
        "Particle": "Particle",
        "Image": "Image",
        "Sound": "Sound",
        "Model": "Model",
        "Text": "Text",
        "Sprite": "Sprite",
        "Fullscreen": "Fullscreen",
        "Composite": "Composite",
        "Script": "Script",
        "Effect": "Effect"
    }

    ASSET_GENRES = {
        "": "Any",
        "Audio Visualizer": "Audio Visualizer",
        "Background": "Background",
        "Character": "Character",
        "Clock": "Clock",
        "Fire": "Fire",
        "Interactive": "Interactive",
        "Magic": "Magic",
        "Post Processing": "Post Processing",
        "Smoke": "Smoke",
        "Space": "Space"
    }

@dataclass
class WorkshopFilters:

    search: str = ""
    sort: str = "trend"
    days: str = "7"
    category: str = ""
    type_tag: str = ""
    age_rating: str = ""
    resolution: str = ""
    misc_tags: List[str] = field(default_factory=list)
    genre_tags: List[str] = field(default_factory=list)
    asset_type: str = ""
    asset_genre: str = ""
    required_flags: List[str] = field(default_factory=list)
    page: int = 1
    
    def build_url(self) -> str:
        base = "https://steamcommunity.com/workshop/browse/?"
        
        base_params = {
            "appid": "431960",
            "browsesort": self.sort,
            "section": "readytouseitems",
            "p": str(self.page),
            "childpublishedfileid": "0",
            "created_date_range_filter_start": "0",
            "created_date_range_filter_end": "0",
            "updated_date_range_filter_start": "0",
            "updated_date_range_filter_end": "0",
            "actualsort": self.sort
        }
        
        if self.sort == "trend" and self.days:
            base_params["days"] = self.days
        
        if self.search:
            base_params["searchtext"] = self.search

        parts = []
        
        for k, v in base_params.items():
            parts.append(f"{k}={v}")
        
        all_tags = []
        if self.category:
            all_tags.append(self.category)
        if self.type_tag:
            all_tags.append(self.type_tag)
        if self.age_rating:
            all_tags.append(self.age_rating)
        if self.resolution:
            all_tags.append(self.resolution)
        if self.asset_type:
            all_tags.append(self.asset_type)
        if self.asset_genre:
            all_tags.append(self.asset_genre)
        all_tags.extend(self.misc_tags)
        all_tags.extend(self.genre_tags)
        
        for tag in all_tags:
            parts.append(f"requiredtags[]={tag}")
        
        for flag in self.required_flags:
            parts.append(f"requiredflags[]={flag}")
        
        return base + "&".join(parts)
