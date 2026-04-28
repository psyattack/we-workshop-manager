use std::path::PathBuf;

use tauri::command;

use crate::commands::{map_err, AppStateHandle};
use crate::download::TaskStatus;
use crate::plugin_paths;

#[command]
pub async fn extract_start(
    state: AppStateHandle<'_>,
    pubfileid: String,
    output_dir: String,
) -> Result<(), String> {
    let Some(we_directory) = state.settings.read().get_directory() else {
        return Err("Wallpaper Engine directory is not configured".into());
    };
    let exe = plugin_paths::repkg()?;
    state
        .extracts
        .start(
            &pubfileid,
            PathBuf::from(we_directory),
            PathBuf::from(output_dir),
            exe,
        )
        .await
        .map_err(map_err)
}

#[command]
pub fn extract_status_all(state: AppStateHandle<'_>) -> Vec<TaskStatus> {
    state.extracts.list()
}
