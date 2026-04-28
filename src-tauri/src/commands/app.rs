//! Top-level application commands: version, window minimize/restore,
//! window-state save & restore, batch metadata initialization.

use serde::{Deserialize, Serialize};
use tauri::command;
use tauri::{AppHandle, Manager, PhysicalPosition, PhysicalSize};

use crate::commands::AppStateHandle;
use crate::config::WindowGeometry;
use crate::constants::APP_VERSION;
use crate::metadata::batch_initialize_metadata;

#[derive(Serialize)]
pub struct AppInfo {
    pub version: String,
    pub name: String,
}

#[command]
pub fn app_get_info() -> AppInfo {
    AppInfo {
        version: APP_VERSION.into(),
        name: "WEave".into(),
    }
}

/// Return the absolute path of the application's data directory
/// (`%LOCALAPPDATA%/WEave` on Windows). Used by the About dialog so the
/// user can copy or open the path.
#[command]
pub fn app_get_data_dir(state: AppStateHandle<'_>) -> String {
    state.app_data_dir.to_string_lossy().to_string()
}

/// Reveal the application data directory in the OS file manager.
#[command]
pub fn app_open_data_dir(state: AppStateHandle<'_>) -> Result<(), String> {
    let path = state.app_data_dir.clone();
    std::fs::create_dir_all(&path).ok();
    open_path_in_explorer(&path).map_err(|e| e.to_string())
}

#[cfg(target_os = "windows")]
fn open_path_in_explorer(path: &std::path::Path) -> std::io::Result<()> {
    std::process::Command::new("explorer")
        .arg(path)
        .spawn()
        .map(|_| ())
}

#[cfg(target_os = "macos")]
fn open_path_in_explorer(path: &std::path::Path) -> std::io::Result<()> {
    std::process::Command::new("open")
        .arg(path)
        .spawn()
        .map(|_| ())
}

#[cfg(all(unix, not(target_os = "macos")))]
fn open_path_in_explorer(path: &std::path::Path) -> std::io::Result<()> {
    std::process::Command::new("xdg-open")
        .arg(path)
        .spawn()
        .map(|_| ())
}

/// Minimize the main window. Used by the "minimize on apply" behavior.
#[command]
pub fn app_minimize(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.minimize().map_err(|e| e.to_string())?;
    }
    Ok(())
}

/// Hard-quit the application. We need this because the user closes the
/// app via our custom title bar's close button — and there's a hidden
/// `steam-webview` window kept around for cookie syncing, so calling
/// `WebviewWindow::close()` only on the main window leaves the process
/// alive on some platforms.
///
/// This command:
///   1. asks every webview window to close (so any "save state" cleanup
///      runs from `on_window_event` if we wire it later),
///   2. then calls `AppHandle::exit(0)` to terminate the process.
#[command]
pub fn app_quit(app: AppHandle) {
    for w in app.webview_windows().values() {
        let _ = w.hide();
        let _ = w.destroy();
    }
    // Tauri's `app.exit(0)` is best-effort and on Windows sometimes never
    // returns when a hidden Steam webview is still around.  Schedule a hard
    // process exit on a background thread so even if the runtime locks up
    // the process actually terminates.
    std::thread::spawn(|| {
        std::thread::sleep(std::time::Duration::from_millis(150));
        std::process::exit(0);
    });
    app.exit(0);
}

/// Read the persisted window geometry. Returns `None` if none has been
/// saved yet or `save_window_state` is disabled.
#[command]
pub fn app_get_window_geometry(state: AppStateHandle<'_>) -> Option<WindowGeometry> {
    let cfg = state.settings.read();
    if !cfg.get_save_window_state() {
        return None;
    }
    cfg.get("general.behavior.window_geometry")
        .and_then(|v| serde_json::from_value::<WindowGeometry>(v).ok())
        .filter(|g| g.width > 0 && g.height > 0)
}

#[derive(Deserialize)]
pub struct WindowGeometryInput {
    pub x: i32,
    pub y: i32,
    pub width: i32,
    pub height: i32,
    #[serde(default)]
    pub is_maximized: bool,
}

/// Persist the current window geometry. The frontend calls this before the
/// window closes so we can restore size/position on next launch (mirror of
/// the original Python behavior).
#[command]
pub fn app_save_window_geometry(state: AppStateHandle<'_>, geom: WindowGeometryInput) {
    state.settings.read().set_window_geometry(WindowGeometry {
        x: geom.x,
        y: geom.y,
        width: geom.width,
        height: geom.height,
        is_maximized: geom.is_maximized,
    });
}

/// Best-effort restore of the saved window geometry. Returns whether any
/// geometry was actually applied so the frontend can avoid flashing.
#[command]
pub fn app_restore_window_geometry(
    state: AppStateHandle<'_>,
    app: AppHandle,
) -> Result<bool, String> {
    let Some(geom) = app_get_window_geometry(state) else {
        return Ok(false);
    };
    let Some(window) = app.get_webview_window("main") else {
        return Ok(false);
    };
    if geom.is_maximized {
        window.maximize().map_err(|e| e.to_string())?;
    } else {
        if geom.width > 0 && geom.height > 0 {
            window
                .set_size(PhysicalSize::new(geom.width as u32, geom.height as u32))
                .map_err(|e| e.to_string())?;
        }
        if geom.x >= 0 && geom.y >= 0 {
            window
                .set_position(PhysicalPosition::new(geom.x, geom.y))
                .map_err(|e| e.to_string())?;
        }
    }
    Ok(true)
}

/// Run the metadata batch initializer. Mirrors the Python
/// `MetadataBatchInitializer` — for every installed wallpaper that does
/// not yet have full metadata, fetch the workshop page and persist the
/// derived fields (tags, posted/updated date, file size, description).
#[command]
pub async fn app_init_metadata(state: AppStateHandle<'_>) -> Result<u32, String> {
    batch_initialize_metadata(state.inner().clone())
        .await
        .map_err(|e| e.to_string())
}
