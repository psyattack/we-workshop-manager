use tauri::command;

use crate::commands::AppStateHandle;
use crate::updater::{check_for_updates, UpdateInfo};

#[command]
pub async fn updater_check(state: AppStateHandle<'_>) -> Result<UpdateInfo, ()> {
    let mut info = check_for_updates().await;
    let skip = state.settings.read().get_skip_version();
    if !skip.is_empty() && info.latest_version == skip {
        info.update_available = false;
    }
    Ok(info)
}

/// Persist a "skip this version" preference (mirror of the original
/// Python `UpdateService.skip_version`).
#[command]
pub fn updater_skip_version(state: AppStateHandle<'_>, version: String) {
    state
        .settings
        .read()
        .set("general.behavior.skip_version", serde_json::Value::String(version))
        .ok();
}
