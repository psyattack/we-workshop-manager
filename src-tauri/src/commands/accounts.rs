use serde::Serialize;
use tauri::command;

use crate::accounts::AccountCredentials;
use crate::commands::AppStateHandle;

#[derive(Serialize)]
pub struct AccountSummary {
    pub index: usize,
    pub username: String,
    pub is_custom: bool,
}

#[command]
pub fn accounts_list(state: AppStateHandle<'_>) -> Vec<AccountSummary> {
    state
        .accounts
        .list_detailed()
        .into_iter()
        .enumerate()
        .map(|(index, a)| AccountSummary {
            index,
            username: a.username,
            is_custom: a.is_custom,
        })
        .collect()
}

#[command]
pub fn accounts_get_current(state: AppStateHandle<'_>) -> AccountCredentials {
    let index = state.settings.read().get_account_number() as usize;
    let mut credentials = state.accounts.credentials(index);
    credentials.password = String::new();
    credentials
}

#[command]
pub fn accounts_set_current(state: AppStateHandle<'_>, index: u32) {
    state.settings.read().set_account_number(index);
}

/// Add a new user account. The password is stored encrypted via
/// `UserAccountsStore` (PBKDF2 + AES-256-GCM, machine-bound key).
#[command]
pub fn accounts_set_custom(
    state: AppStateHandle<'_>,
    username: String,
    password: String,
) -> Result<(), String> {
    state
        .accounts
        .add_user_account(username.trim(), password.as_str())
}

/// Remove a single user account by username.
#[command]
pub fn accounts_remove_custom(
    state: AppStateHandle<'_>,
    username: String,
) -> Result<(), String> {
    state.accounts.remove_user_account(username.trim())
}

/// Wipe all encrypted user accounts.
#[command]
pub fn accounts_reset_custom(state: AppStateHandle<'_>) -> Result<(), String> {
    state.accounts.clear_user_accounts()
}

/// List the usernames of user-added accounts (the SettingsDialog shows
/// these so the user can remove them individually).
#[command]
pub fn accounts_list_custom(state: AppStateHandle<'_>) -> Vec<String> {
    state.accounts.list_custom_usernames()
}
