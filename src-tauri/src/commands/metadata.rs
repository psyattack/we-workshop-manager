use serde_json::Value;
use tauri::command;

use crate::commands::AppStateHandle;

#[command]
pub fn metadata_get_all(state: AppStateHandle<'_>) -> Value {
    state.metadata.read().get_all()
}

#[command]
pub fn metadata_get(state: AppStateHandle<'_>, pubfileid: String) -> Option<Value> {
    state.metadata.read().get_item(&pubfileid)
}

#[command]
pub fn metadata_save(state: AppStateHandle<'_>, pubfileid: String, data: Value) {
    state.metadata.read().set_item(&pubfileid, data);
}

#[command]
pub fn metadata_remove(state: AppStateHandle<'_>, pubfileid: String) {
    state.metadata.read().remove_item(&pubfileid);
}
