use tauri::command;

use crate::commands::{map_err, AppStateHandle};
use crate::workshop::{CollectionContents, WorkshopFilters, WorkshopItem, WorkshopPage};

#[command]
pub async fn workshop_browse(
    state: AppStateHandle<'_>,
    filters: WorkshopFilters,
) -> Result<WorkshopPage, String> {
    state.workshop.browse(&filters).await.map_err(map_err)
}

#[command]
pub async fn workshop_browse_collections(
    state: AppStateHandle<'_>,
    filters: WorkshopFilters,
) -> Result<WorkshopPage, String> {
    state
        .workshop
        .browse_collections(&filters)
        .await
        .map_err(map_err)
}

#[command]
pub async fn workshop_get_item(
    state: AppStateHandle<'_>,
    pubfileid: String,
) -> Result<WorkshopItem, String> {
    let item = state
        .workshop
        .item_details(&pubfileid)
        .await
        .map_err(map_err)?;
    // Persist metadata so that it's available offline next time (mirrors
    // the Python `MetadataService.save_from_workshop_item`).
    if let Ok(value) = serde_json::to_value(&item) {
        state.metadata.read().set_item(&pubfileid, value);
    }
    Ok(item)
}

#[command]
pub async fn workshop_get_collection(
    state: AppStateHandle<'_>,
    collection_id: String,
) -> Result<CollectionContents, String> {
    state
        .workshop
        .collection_contents(&collection_id)
        .await
        .map_err(map_err)
}

#[command]
pub async fn workshop_get_author_items(
    state: AppStateHandle<'_>,
    profile_url: String,
    filters: WorkshopFilters,
) -> Result<WorkshopPage, String> {
    state
        .workshop
        .author_items(&profile_url, &filters)
        .await
        .map_err(map_err)
}

#[command]
pub async fn workshop_get_author_collections(
    state: AppStateHandle<'_>,
    profile_url: String,
    filters: WorkshopFilters,
) -> Result<WorkshopPage, String> {
    state
        .workshop
        .author_collections(&profile_url, &filters)
        .await
        .map_err(map_err)
}

#[command]
pub fn workshop_refresh_cache(state: AppStateHandle<'_>) {
    state.workshop.clear_caches();
}

/// Return the in-memory parser debug log (last N HTTP responses Steam
/// returned). Used by the Settings → Debug → "Parser log" dialog as a
/// replacement for the original Python app's visible-webview debug mode.
#[command]
pub fn workshop_debug_log() -> Vec<crate::workshop::debug::DebugEntry> {
    crate::workshop::debug::snapshot()
}

#[command]
pub fn workshop_debug_clear() {
    crate::workshop::debug::clear();
}
