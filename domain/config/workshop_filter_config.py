class WorkshopFilterConfig:
    SORT_KEYS = ["trend", "mostrecent", "lastupdated", "totaluniquesubscribers"]
    TIME_PERIOD_KEYS = ["1", "7", "30", "90", "180", "365", "-1"]
    CATEGORY_KEYS = ["", "Wallpaper", "Preset", "Asset"]
    TYPE_KEYS = ["", "Scene", "Video", "Application", "Web"]
    AGE_RATING_KEYS = ["", "Everyone", "Questionable", "Mature"]
    RESOLUTION_KEYS = [
        "",
        "1920 x 1080",
        "2560 x 1440",
        "3840 x 2160",
        "1280 x 720",
        "1366 x 768",
        "Ultrawide 2560 x 1080",
        "Ultrawide 3440 x 1440",
        "Portrait 1080 x 1920",
        "Dynamic resolution",
        "Other resolution",
    ]
    MISC_TAG_KEYS = [
        "Approved",
        "Audio responsive",
        "3D",
        "Customizable",
        "Puppet Warp",
        "HDR",
        "Media Integration",
        "User Shortcut",
        "Video Texture",
        "Asset Pack",
    ]
    GENRE_TAG_KEYS = [
        "Abstract",
        "Animal",
        "Anime",
        "Cartoon",
        "CGI",
        "Cyberpunk",
        "Fantasy",
        "Game",
        "Girls",
        "Guys",
        "Landscape",
        "Medieval",
        "Memes",
        "MMD",
        "Music",
        "Nature",
        "Pixel art",
        "Relaxing",
        "Retro",
        "Sci-Fi",
        "Sports",
        "Technology",
        "Television",
        "Vehicle",
        "Unspecified",
    ]
    ASSET_TYPE_KEYS = [
        "",
        "Particle",
        "Image",
        "Sound",
        "Model",
        "Text",
        "Sprite",
        "Fullscreen",
        "Composite",
        "Script",
        "Effect",
    ]
    ASSET_GENRE_KEYS = [
        "",
        "Audio Visualizer",
        "Background",
        "Character",
        "Clock",
        "Fire",
        "Interactive",
        "Magic",
        "Post Processing",
        "Smoke",
        "Space",
    ]
    SCRIPT_TYPE_KEYS = [
        "",
        "Boolean",
        "Number",
        "Vec2",
        "Vec3",
        "Vec4",
        "String",
        "No Animation",
        "Oversized",
    ]

    SORT_OPTIONS = {
        "trend": "Popular",
        "mostrecent": "Most Recent",
        "lastupdated": "Recently Updated",
        "totaluniquesubscribers": "Most Subscribed",
    }

    TIME_PERIODS = {
        "1": "Today",
        "7": "This Week",
        "30": "This Month",
        "90": "3 Months",
        "180": "6 Months",
        "365": "This Year",
        "-1": "All Time",
    }

    CATEGORIES = {
        "": "All",
        "Wallpaper": "Wallpaper",
        "Preset": "Preset",
        "Asset": "Asset",
    }

    TYPES = {
        "": "Any",
        "Scene": "Scene",
        "Video": "Video",
        "Application": "Application",
        "Web": "Web",
    }

    AGE_RATINGS = {
        "": "Any",
        "Everyone": "Everyone",
        "Questionable": "Questionable",
        "Mature": "Mature",
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
        "Other resolution": "Other",
    }

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
        "Effect": "Effect",
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
        "Space": "Space",
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
        "Oversized": "Oversized",
    }

    @classmethod
    def get_translated_sort_options(cls, translator):
        result = {}
        for key in cls.SORT_KEYS:
            translated = translator(f"filters.sort.{key}")
            result[key] = translated if translated != f"filters.sort.{key}" else cls.SORT_OPTIONS[key]
        return result

    @classmethod
    def get_translated_time_periods(cls, translator):
        result = {}
        for key in cls.TIME_PERIOD_KEYS:
            translated = translator(f"filters.time_period.{key}")
            result[key] = translated if translated != f"filters.time_period.{key}" else cls.TIME_PERIODS[key]
        return result

    @classmethod
    def get_translated_categories(cls, translator):
        result = {}
        for key in cls.CATEGORY_KEYS:
            translation_key = key if key else "empty"
            translated = translator(f"filters.category.{translation_key}")
            result[key] = translated if translated != f"filters.category.{translation_key}" else cls.CATEGORIES[key]
        return result

    @classmethod
    def get_translated_types(cls, translator):
        result = {}
        for key in cls.TYPE_KEYS:
            translation_key = key if key else "empty"
            translated = translator(f"filters.type.{translation_key}")
            result[key] = translated if translated != f"filters.type.{translation_key}" else cls.TYPES[key]
        return result

    @classmethod
    def get_translated_age_ratings(cls, translator):
        result = {}
        for key in cls.AGE_RATING_KEYS:
            translation_key = key if key else "empty"
            translated = translator(f"filters.age_rating.{translation_key}")
            result[key] = translated if translated != f"filters.age_rating.{translation_key}" else cls.AGE_RATINGS[key]
        return result

    @classmethod
    def get_translated_resolutions(cls, translator):
        result = {}
        for key in cls.RESOLUTION_KEYS:
            translation_key = key.replace(" ", "_") if key else "empty"
            translated = translator(f"filters.resolution.{translation_key}")
            result[key] = translated if translated != f"filters.resolution.{translation_key}" else cls.RESOLUTIONS[key]
        return result

    @classmethod
    def get_translated_misc_tags(cls, translator):
        result = {}
        for key in cls.MISC_TAG_KEYS:
            translated = translator(f"filters.misc_tags.{key}")
            result[key] = translated if translated != f"filters.misc_tags.{key}" else key
        return result

    @classmethod
    def get_translated_genre_tags(cls, translator):
        result = {}
        for key in cls.GENRE_TAG_KEYS:
            translated = translator(f"filters.genre_tags.{key}")
            result[key] = translated if translated != f"filters.genre_tags.{key}" else key
        return result

    @classmethod
    def get_translated_asset_types(cls, translator):
        result = {}
        for key in cls.ASSET_TYPE_KEYS:
            translation_key = key if key else "empty"
            translated = translator(f"filters.asset_type.{translation_key}")
            result[key] = translated if translated != f"filters.asset_type.{translation_key}" else cls.ASSET_TYPES[key]
        return result

    @classmethod
    def get_translated_asset_genres(cls, translator):
        result = {}
        for key in cls.ASSET_GENRE_KEYS:
            translation_key = key if key else "empty"
            translated = translator(f"filters.asset_genre.{translation_key}")
            result[key] = translated if translated != f"filters.asset_genre.{translation_key}" else cls.ASSET_GENRES[key]
        return result

    @classmethod
    def get_translated_script_types(cls, translator):
        result = {}
        for key in cls.SCRIPT_TYPE_KEYS:
            translation_key = key if key else "empty"
            translated = translator(f"filters.script_type.{translation_key}")
            result[key] = translated if translated != f"filters.script_type.{translation_key}" else cls.SCRIPT_TYPES[key]
        return result