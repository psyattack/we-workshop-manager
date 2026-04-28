pub mod accounts;
pub mod app;
pub mod config;
pub mod download;
pub mod extract;
pub mod i18n;
pub mod image;
pub mod metadata;
pub mod translator;
pub mod updater;
pub mod steam;
pub mod we;
pub mod workshop;

use std::sync::Arc;

use tauri::State;

use crate::app_state::AppState;

pub type AppStateHandle<'a> = State<'a, Arc<AppState>>;

pub fn map_err<E: std::fmt::Display>(e: E) -> String {
    e.to_string()
}
