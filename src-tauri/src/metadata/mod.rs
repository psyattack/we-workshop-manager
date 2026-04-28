//! Thin helpers around the wallpaper metadata section of the config file.

use std::sync::Arc;
use std::time::Duration;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::app_state::AppState;

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct WallpaperMetadata {
    pub pubfileid: String,
    pub title: String,
    pub description: String,
    pub preview_url: String,
    pub author: String,
    pub author_url: String,
    pub file_size: String,
    pub posted_date: String,
    pub updated_date: String,
    pub rating_star_file: String,
    pub num_ratings: String,
    pub tags: serde_json::Value,
    pub collections: serde_json::Value,
}

/// Iterate over installed wallpapers and, for any that don't yet have
/// non-trivial metadata cached in the config file, fetch the workshop
/// page and persist the parsed metadata. Mirrors the original Python
/// `MetadataBatchInitializer`.
pub async fn batch_initialize_metadata(state: Arc<AppState>) -> anyhow::Result<u32> {
    let installed = state.we_client.read().installed_wallpapers();
    let cached = state.metadata.read().get_all();

    let pending: Vec<String> = installed
        .iter()
        .map(|w| w.pubfileid.clone())
        .filter(|id| !is_metadata_complete(&cached, id))
        .collect();

    let mut count: u32 = 0;
    for pubfileid in pending {
        let workshop = state.workshop.clone();
        match workshop.item_details(&pubfileid).await {
            Ok(item) => {
                let value = serde_json::to_value(WallpaperMetadata {
                    pubfileid: item.pubfileid.clone(),
                    title: item.title,
                    description: item.description,
                    preview_url: item.preview_url,
                    author: item.author,
                    author_url: item.author_url,
                    file_size: item.file_size,
                    posted_date: item.posted_date,
                    updated_date: item.updated_date,
                    rating_star_file: item.rating_star_file,
                    num_ratings: item.num_ratings,
                    tags: item.tags,
                    collections: serde_json::to_value(&item.collections)
                        .unwrap_or(Value::Array(Vec::new())),
                })
                .unwrap_or(Value::Null);
                if !value.is_null() {
                    state.metadata.read().set_item(&item.pubfileid, value);
                    count += 1;
                }
            }
            Err(err) => {
                log::warn!("metadata batch: {pubfileid} fetch failed: {err:#}");
            }
        }
        // Rate-limit the requests so we don't hammer the workshop.
        tokio::time::sleep(Duration::from_millis(300)).await;
    }
    Ok(count)
}

fn is_metadata_complete(cached: &Value, pubfileid: &str) -> bool {
    let Some(item) = cached.get(pubfileid).and_then(|v| v.as_object()) else {
        return false;
    };
    let title_ok = item
        .get("title")
        .and_then(|v| v.as_str())
        .map(|s| !s.is_empty())
        .unwrap_or(false);
    let tags_ok = item
        .get("tags")
        .map(|v| {
            v.as_array().map(|a| !a.is_empty()).unwrap_or(false)
                || v.as_object().map(|o| !o.is_empty()).unwrap_or(false)
        })
        .unwrap_or(false);
    title_ok && tags_ok
}
