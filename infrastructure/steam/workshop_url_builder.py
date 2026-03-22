from urllib.parse import urlencode
from domain.models.workshop import WorkshopFilters
from shared.constants import STEAM_APP_ID


class WorkshopUrlBuilder:
    BASE_URL = "https://steamcommunity.com/workshop/browse/"

    @classmethod
    def build(cls, filters: WorkshopFilters) -> str:
        params: dict[str, object] = {
            "appid": STEAM_APP_ID,
            "browsesort": filters.sort,
            "section": "readytouseitems",
            "p": str(filters.page),
            "childpublishedfileid": "0",
            "created_date_range_filter_start": "0",
            "created_date_range_filter_end": "0",
            "updated_date_range_filter_start": "0",
            "updated_date_range_filter_end": "0",
            "actualsort": filters.sort,
        }
        if filters.sort == "trend" and filters.days:
            params["days"] = filters.days
        if filters.search:
            params["searchtext"] = filters.search
        cls._add_tag_params(params, filters)
        return f"{cls.BASE_URL}?{urlencode(params, doseq=True)}"

    @classmethod
    def build_collections_browse(cls, filters: WorkshopFilters) -> str:
        params: dict[str, object] = {
            "appid": STEAM_APP_ID,
            "browsesort": filters.sort,
            "section": "collections",
            "p": str(filters.page),
            "actualsort": filters.sort,
        }
        if filters.sort == "trend" and filters.days:
            params["days"] = filters.days
        if filters.search:
            params["searchtext"] = filters.search
        cls._add_tag_params(params, filters)
        return f"{cls.BASE_URL}?{urlencode(params, doseq=True)}"

    @classmethod
    def build_author_items(cls, author_profile_url: str, filters: WorkshopFilters) -> str:
        base = author_profile_url.rstrip("/") + "/myworkshopfiles/"
        params: dict[str, object] = {
            "appid": STEAM_APP_ID,
            "p": str(filters.page),
        }
        if filters.search:
            params["searchtext"] = filters.search
        cls._add_tag_params(params, filters)
        return f"{base}?{urlencode(params, doseq=True)}"

    @classmethod
    def build_author_collections(cls, author_profile_url: str, filters: WorkshopFilters) -> str:
        base = author_profile_url.rstrip("/") + "/myworkshopfiles/"
        params: dict[str, object] = {
            "appid": STEAM_APP_ID,
            "section": "collections",
            "p": str(filters.page),
        }
        if filters.search:
            params["searchtext"] = filters.search
        cls._add_tag_params(params, filters)
        return f"{base}?{urlencode(params, doseq=True)}"

    @classmethod
    def build_collection_url(cls, collection_id: str) -> str:
        return f"https://steamcommunity.com/sharedfiles/filedetails/?id={collection_id}"

    @classmethod
    def _add_tag_params(cls, params: dict, filters: WorkshopFilters) -> None:
        required_tags: list[str] = []
        if filters.category:
            required_tags.append(filters.category)
        if filters.type_tag:
            required_tags.append(filters.type_tag)
        if filters.age_rating:
            required_tags.append(filters.age_rating)
        if filters.resolution:
            required_tags.append(filters.resolution)
        if filters.asset_type:
            required_tags.append(filters.asset_type)
        if filters.asset_genre:
            required_tags.append(filters.asset_genre)
        if filters.script_type:
            required_tags.append(filters.script_type)
        required_tags.extend(filters.misc_tags)
        required_tags.extend(filters.genre_tags)
        excluded_tags = list(filters.excluded_misc_tags) + list(filters.excluded_genre_tags)
        if required_tags:
            params["requiredtags[]"] = required_tags
        if excluded_tags:
            params["excludedtags[]"] = excluded_tags
        if filters.required_flags:
            params["requiredflags[]"] = filters.required_flags
