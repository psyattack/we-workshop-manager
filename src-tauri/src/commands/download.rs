use std::path::PathBuf;

use tauri::command;

use crate::commands::{map_err, AppStateHandle};
use crate::download::TaskStatus;
use crate::plugin_paths;

#[command]
pub async fn download_start(
    state: AppStateHandle<'_>,
    pubfileid: String,
    account_index: Option<usize>,
) -> Result<(), String> {
    let Some(we_directory) = state.settings.read().get_directory() else {
        return Err("Wallpaper Engine directory is not configured".into());
    };
    let exe = plugin_paths::depot_downloader()?;
    let index = account_index.unwrap_or_else(|| state.settings.read().get_account_number() as usize);
    let credentials = state.accounts.credentials(index);
    state
        .downloads
        .start(
            &pubfileid,
            credentials,
            PathBuf::from(we_directory),
            exe,
        )
        .await
        .map_err(map_err)
}

#[command]
pub async fn download_cancel(
    state: AppStateHandle<'_>,
    pubfileid: String,
) -> Result<bool, String> {
    let we_directory = state
        .settings
        .read()
        .get_directory()
        .map(PathBuf::from)
        .unwrap_or_default();
    Ok(state.downloads.cancel(&pubfileid, &we_directory).await)
}

#[command]
pub fn download_status_all(state: AppStateHandle<'_>) -> Vec<TaskStatus> {
    state.downloads.list()
}

#[command]
pub async fn download_multi_start(
    state: AppStateHandle<'_>,
    pubfileids: Vec<String>,
    account_index: Option<usize>,
) -> Result<(), String> {
    for id in pubfileids {
        if let Err(err) = download_start(state.clone(), id, account_index).await {
            log::warn!("download_multi_start failed: {err}");
        }
    }
    Ok(())
}
