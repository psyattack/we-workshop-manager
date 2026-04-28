use std::path::PathBuf;

use tauri::command;

use crate::commands::{map_err, AppStateHandle};
use crate::we_client::{delete_wallpaper_folder, InstalledWallpaper, WallpaperEngineClient};

#[command]
pub fn we_detect() -> Option<String> {
    WallpaperEngineClient::detect_installation()
        .map(|p| p.to_string_lossy().to_string())
}

#[command]
pub fn we_get_directory(state: AppStateHandle<'_>) -> Option<String> {
    state
        .we_client
        .read()
        .directory
        .as_ref()
        .map(|p| p.to_string_lossy().to_string())
}

#[command]
pub fn we_set_directory(state: AppStateHandle<'_>, path: String) -> Result<(), String> {
    let dir = PathBuf::from(&path);
    if !dir.join("wallpaper64.exe").exists() && !dir.join("wallpaper32.exe").exists() {
        return Err("Not a Wallpaper Engine directory".into());
    }
    state.we_client.write().set_directory(Some(dir));
    state.settings.read().set_directory(&path);
    Ok(())
}

#[command]
pub fn we_list_installed(state: AppStateHandle<'_>) -> Vec<InstalledWallpaper> {
    state.we_client.read().installed_wallpapers()
}

#[command]
pub fn we_apply(
    state: AppStateHandle<'_>,
    project_path: String,
    monitor: Option<u32>,
    force: Option<bool>,
) -> Result<(), String> {
    state
        .we_client
        .read()
        .apply(&PathBuf::from(project_path), monitor, force.unwrap_or(false))
        .map_err(map_err)
}

#[command]
pub fn we_open(state: AppStateHandle<'_>, show_window: Option<bool>) -> Result<(), String> {
    state
        .we_client
        .read()
        .open_wallpaper_engine(show_window.unwrap_or(true))
        .map_err(map_err)
}

#[command]
pub fn we_delete_wallpaper(
    state: AppStateHandle<'_>,
    pubfileid: String,
) -> Result<(), String> {
    let Some(projects) = state.we_client.read().projects_path() else {
        return Err("Wallpaper Engine directory not set".into());
    };
    // Refuse to delete a wallpaper that's currently being displayed on any
    // monitor — otherwise Wallpaper Engine keeps a file handle and the
    // delete fails with a confusing OS error halfway through. The caller
    // matches on the "ACTIVE:" prefix to show a friendly prompt.
    let active = state.we_client.read().active_pubfileids();
    if active.iter().any(|id| id == &pubfileid) {
        return Err(format!("ACTIVE:{pubfileid}"));
    }
    state.metadata.read().remove_item(&pubfileid);
    delete_wallpaper_folder(&projects, &pubfileid).map_err(map_err)
}

#[command]
pub fn we_current_pubfileid(state: AppStateHandle<'_>, monitor: u32) -> Option<String> {
    state.we_client.read().current_wallpaper_pubfileid(monitor)
}

/// Every pubfileid that Wallpaper Engine is currently displaying on any
/// monitor. Frontend uses this to disable the Delete button / warn the
/// user before they try to remove a wallpaper that's live on screen.
#[command]
pub fn we_active_pubfileids(state: AppStateHandle<'_>) -> Vec<String> {
    state.we_client.read().active_pubfileids()
}
