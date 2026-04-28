//! URL construction for Steam Workshop browsing. Ports
//! `workshop_url_builder.py` — including the exact parameter names so
//! results match 1:1 with the original app.

use url::form_urlencoded;

use crate::constants::STEAM_APP_ID;
use crate::workshop::WorkshopFilters;

const BASE_URL: &str = "https://steamcommunity.com/workshop/browse/";

pub fn build_browse(filters: &WorkshopFilters) -> String {
    let mut builder = form_urlencoded::Serializer::new(String::new());
    builder
        .append_pair("appid", STEAM_APP_ID)
        .append_pair("browsesort", &filters.sort)
        .append_pair("section", "readytouseitems")
        .append_pair("p", &filters.page.max(1).to_string())
        .append_pair("childpublishedfileid", "0")
        .append_pair("created_date_range_filter_start", "0")
        .append_pair("created_date_range_filter_end", "0")
        .append_pair("updated_date_range_filter_start", "0")
        .append_pair("updated_date_range_filter_end", "0")
        .append_pair("actualsort", &filters.sort);

    if filters.sort == "trend" && !filters.days.is_empty() {
        builder.append_pair("days", &filters.days);
    }
    if !filters.search.is_empty() {
        builder.append_pair("searchtext", &filters.search);
    }
    add_tag_params(&mut builder, filters);
    format!("{BASE_URL}?{}", builder.finish())
}

pub fn build_collections_browse(filters: &WorkshopFilters) -> String {
    let mut builder = form_urlencoded::Serializer::new(String::new());
    builder
        .append_pair("appid", STEAM_APP_ID)
        .append_pair("browsesort", &filters.sort)
        .append_pair("section", "collections")
        .append_pair("p", &filters.page.max(1).to_string())
        .append_pair("actualsort", &filters.sort);

    if filters.sort == "trend" && !filters.days.is_empty() {
        builder.append_pair("days", &filters.days);
    }
    if !filters.search.is_empty() {
        builder.append_pair("searchtext", &filters.search);
    }
    add_tag_params(&mut builder, filters);
    format!("{BASE_URL}?{}", builder.finish())
}

pub fn build_author_items(profile_url: &str, filters: &WorkshopFilters) -> String {
    let base = format!("{}/myworkshopfiles/", profile_url.trim_end_matches('/'));
    let mut builder = form_urlencoded::Serializer::new(String::new());
    builder
        .append_pair("appid", STEAM_APP_ID)
        .append_pair("p", &filters.page.max(1).to_string());
    if !filters.search.is_empty() {
        builder.append_pair("searchtext", &filters.search);
    }
    add_tag_params(&mut builder, filters);
    format!("{base}?{}", builder.finish())
}

pub fn build_author_collections(profile_url: &str, filters: &WorkshopFilters) -> String {
    let base = format!("{}/myworkshopfiles/", profile_url.trim_end_matches('/'));
    let mut builder = form_urlencoded::Serializer::new(String::new());
    builder
        .append_pair("appid", STEAM_APP_ID)
        .append_pair("section", "collections")
        .append_pair("p", &filters.page.max(1).to_string());
    if !filters.search.is_empty() {
        builder.append_pair("searchtext", &filters.search);
    }
    add_tag_params(&mut builder, filters);
    format!("{base}?{}", builder.finish())
}

pub fn build_collection_url(collection_id: &str) -> String {
    format!(
        "https://steamcommunity.com/sharedfiles/filedetails/?id={collection_id}"
    )
}

fn add_tag_params<'a>(
    builder: &mut form_urlencoded::Serializer<'a, String>,
    filters: &WorkshopFilters,
) {
    let mut required: Vec<&str> = Vec::new();
    if !filters.category.is_empty() {
        required.push(&filters.category);
    }
    if !filters.type_tag.is_empty() {
        required.push(&filters.type_tag);
    }
    if !filters.age_rating.is_empty() {
        required.push(&filters.age_rating);
    }
    if !filters.resolution.is_empty() {
        required.push(&filters.resolution);
    }
    if !filters.asset_type.is_empty() {
        required.push(&filters.asset_type);
    }
    if !filters.asset_genre.is_empty() {
        required.push(&filters.asset_genre);
    }
    if !filters.script_type.is_empty() {
        required.push(&filters.script_type);
    }
    for tag in &filters.misc_tags {
        required.push(tag);
    }
    for tag in &filters.genre_tags {
        required.push(tag);
    }
    for tag in required {
        builder.append_pair("requiredtags[]", tag);
    }

    let mut excluded: Vec<&str> = Vec::new();
    for tag in &filters.excluded_misc_tags {
        excluded.push(tag);
    }
    for tag in &filters.excluded_genre_tags {
        excluded.push(tag);
    }
    for tag in excluded {
        builder.append_pair("excludedtags[]", tag);
    }

    for flag in &filters.required_flags {
        builder.append_pair("requiredflags[]", flag);
    }
}
