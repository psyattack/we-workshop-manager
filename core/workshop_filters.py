from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional

@dataclass
class FilterConfig:

    SORT_KEYS = ["trend", "mostrecent", "lastupdated", "totaluniquesubscribers"]
    TIME_PERIOD_KEYS = ["1", "7", "30", "90", "180", "365", "-1"]
    CATEGORY_KEYS = ["", "Wallpaper", "Preset", "Asset"]
    TYPE_KEYS = ["", "Scene", "Video", "Application", "Web"]
    AGE_RATING_KEYS = ["", "Everyone", "Questionable", "Mature"]
    RESOLUTION_KEYS = ["", "1920 x 1080", "2560 x 1440", "3840 x 2160", "1280 x 720", 
                       "1366 x 768", "Ultrawide 2560 x 1080", "Ultrawide 3440 x 1440", 
                       "Portrait 1080 x 1920", "Dynamic resolution", "Other resolution"]
    MISC_TAG_KEYS = ["Approved", "Audio responsive", "3D", "Customizable",
                     "Puppet Warp", "HDR", "Media Integration", "User Shortcut",
                     "Video Texture", "Asset Pack"]
    GENRE_TAG_KEYS = ["Abstract", "Animal", "Anime", "Cartoon", "CGI", "Cyberpunk",
                      "Fantasy", "Game", "Girls", "Guys", "Landscape", "Medieval",
                      "Memes", "MMD", "Music", "Nature", "Pixel art", "Relaxing",
                      "Retro", "Sci-Fi", "Sports", "Technology", "Television",
                      "Vehicle", "Unspecified"]
    ASSET_TYPE_KEYS = ["", "Particle", "Image", "Sound", "Model", "Text", 
                       "Sprite", "Fullscreen", "Composite", "Script", "Effect"]
    ASSET_GENRE_KEYS = ["", "Audio Visualizer", "Background", "Character", "Clock",
                        "Fire", "Interactive", "Magic", "Post Processing", "Smoke", "Space"]
    SCRIPT_TYPE_KEYS = ["", "Boolean", "Number", "Vec2", "Vec3", "Vec4", 
                        "String", "No Animation", "Oversized"]

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

    SCRIPT_TYPES = {
        "": "Any",
        "Boolean": "Boolean",
        "Number": "Number",
        "Vec2": "Vec2",
        "Vec3": "Vec3",
        "Vec4": "Vec4",
        "String": "String",
        "No Animation": "No Animation",
        "Oversized": "Oversized"
    }
    
    @classmethod
    def get_translated_sort_options(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.SORT_KEYS:
            translated = translator(f"filters.sort.{key}")
            result[key] = translated if translated != f"filters.sort.{key}" else cls.SORT_OPTIONS[key]
        return result
    
    @classmethod
    def get_translated_time_periods(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.TIME_PERIOD_KEYS:
            translated = translator(f"filters.time_period.{key}")
            result[key] = translated if translated != f"filters.time_period.{key}" else cls.TIME_PERIODS[key]
        return result
    
    @classmethod
    def get_translated_categories(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.CATEGORY_KEYS:
            translated = translator(f"filters.category.{key if key else 'empty'}")
            result[key] = translated if translated != f"filters.category.{key if key else 'empty'}" else cls.CATEGORIES[key]
        return result
    
    @classmethod
    def get_translated_types(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.TYPE_KEYS:
            translated = translator(f"filters.type.{key if key else 'empty'}")
            result[key] = translated if translated != f"filters.type.{key if key else 'empty'}" else cls.TYPES[key]
        return result
    
    @classmethod
    def get_translated_age_ratings(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.AGE_RATING_KEYS:
            translated = translator(f"filters.age_rating.{key if key else 'empty'}")
            result[key] = translated if translated != f"filters.age_rating.{key if key else 'empty'}" else cls.AGE_RATINGS[key]
        return result
    
    @classmethod
    def get_translated_resolutions(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.RESOLUTION_KEYS:
            safe_key = key.replace(" ", "_").replace("x", "x") if key else "empty"
            translated = translator(f"filters.resolution.{safe_key}")
            result[key] = translated if translated != f"filters.resolution.{safe_key}" else cls.RESOLUTIONS[key]
        return result
    
    @classmethod
    def get_translated_misc_tags(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.MISC_TAG_KEYS:
            translated = translator(f"filters.misc_tags.{key}")
            result[key] = translated if translated != f"filters.misc_tags.{key}" else key
        return result
    
    @classmethod
    def get_translated_genre_tags(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.GENRE_TAG_KEYS:
            translated = translator(f"filters.genre_tags.{key}")
            result[key] = translated if translated != f"filters.genre_tags.{key}" else key
        return result
    
    @classmethod
    def get_translated_asset_types(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.ASSET_TYPE_KEYS:
            translated = translator(f"filters.asset_type.{key if key else 'empty'}")
            result[key] = translated if translated != f"filters.asset_type.{key if key else 'empty'}" else cls.ASSET_TYPES[key]
        return result
    
    @classmethod
    def get_translated_asset_genres(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.ASSET_GENRE_KEYS:
            translated = translator(f"filters.asset_genre.{key if key else 'empty'}")
            result[key] = translated if translated != f"filters.asset_genre.{key if key else 'empty'}" else cls.ASSET_GENRES[key]
        return result
    
    @classmethod
    def get_translated_script_types(cls, translator: Callable) -> Dict[str, str]:
        result = {}
        for key in cls.SCRIPT_TYPE_KEYS:
            translated = translator(f"filters.script_type.{key if key else 'empty'}")
            result[key] = translated if translated != f"filters.script_type.{key if key else 'empty'}" else cls.SCRIPT_TYPES[key]
        return result

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
    excluded_misc_tags: List[str] = field(default_factory=list)
    excluded_genre_tags: List[str] = field(default_factory=list)
    asset_type: str = ""
    asset_genre: str = ""
    script_type: str = ""
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
        if self.script_type:
            all_tags.append(self.script_type)
        all_tags.extend(self.misc_tags)
        all_tags.extend(self.genre_tags)
        
        for tag in all_tags:
            parts.append(f"requiredtags[]={tag}")
        
        excluded_tags = list(self.excluded_misc_tags) + list(self.excluded_genre_tags)
        for tag in excluded_tags:
            parts.append(f"excludedtags[]={tag}")
        
        for flag in self.required_flags:
            parts.append(f"requiredflags[]={flag}")
        
        return base + "&".join(parts)
