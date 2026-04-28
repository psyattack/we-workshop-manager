//! WEave — Tauri 2 + Rust port of the WEave (Wallpaper Engine Workshop Manager)
//! Python/PyQt6 application. Preserves full feature parity with the original
//! while adding a modern, animated web-based UI.

pub mod accounts;
pub mod app_state;
pub mod commands;
pub mod config;
pub mod constants;
pub mod download;
pub mod extract;
pub mod i18n;
pub mod metadata;
pub mod plugin_paths;
pub mod translator;
pub mod updater;
pub mod we_client;
pub mod workshop;

use std::sync::Arc;
use tauri::Manager;

use crate::app_state::AppState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::try_init().ok();

    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
                let _ = window.unminimize();
            }
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_os::init())
        .setup(|app| {
            let state = AppState::initialize(app.handle().clone())?;
            app.manage(Arc::new(state));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::app::app_get_info,
            commands::app::app_get_data_dir,
            commands::app::app_open_data_dir,
            commands::app::app_minimize,
            commands::app::app_quit,
            commands::app::app_get_window_geometry,
            commands::app::app_save_window_geometry,
            commands::app::app_restore_window_geometry,
            commands::app::app_init_metadata,
            commands::config::config_get_all,
            commands::config::config_set,
            commands::config::config_get,
            commands::config::config_save_window_geometry,
            commands::i18n::i18n_get_translations,
            commands::i18n::i18n_get_available_languages,
            commands::i18n::i18n_set_language,
            commands::accounts::accounts_list,
            commands::accounts::accounts_list_custom,
            commands::accounts::accounts_get_current,
            commands::accounts::accounts_set_current,
            commands::accounts::accounts_set_custom,
            commands::accounts::accounts_remove_custom,
            commands::accounts::accounts_reset_custom,
            commands::updater::updater_check,
            commands::updater::updater_skip_version,
            commands::metadata::metadata_get_all,
            commands::metadata::metadata_get,
            commands::metadata::metadata_save,
            commands::metadata::metadata_remove,
            commands::translator::translator_translate,
            commands::we::we_detect,
            commands::we::we_set_directory,
            commands::we::we_get_directory,
            commands::we::we_list_installed,
            commands::we::we_apply,
            commands::we::we_open,
            commands::we::we_delete_wallpaper,
            commands::we::we_current_pubfileid,
            commands::we::we_active_pubfileids,
            commands::workshop::workshop_browse,
            commands::workshop::workshop_browse_collections,
            commands::workshop::workshop_get_item,
            commands::workshop::workshop_get_collection,
            commands::workshop::workshop_get_author_items,
            commands::workshop::workshop_get_author_collections,
            commands::workshop::workshop_refresh_cache,
            commands::workshop::workshop_debug_log,
            commands::workshop::workshop_debug_clear,
            commands::download::download_start,
            commands::download::download_cancel,
            commands::download::download_status_all,
            commands::download::download_multi_start,
            commands::extract::extract_start,
            commands::extract::extract_status_all,
            commands::image::open_path,
            commands::steam::steam_login_show,
            commands::steam::steam_login_hide,
            commands::steam::steam_sync_cookies,
            commands::steam::steam_is_logged_in,
            commands::steam::steam_current_account,
            commands::steam::steam_auto_login,
        ]);

    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
