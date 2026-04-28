//! Account management. Ports the Python `AccountService` 1:1 including the
//! same built-in public accounts and preserving the custom-account behaviour.
//! User-added accounts are stored encrypted on disk via `user_accounts::UserAccountsStore`.

use std::sync::Arc;

use base64::{engine::general_purpose, Engine as _};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};

pub mod user_accounts;

use user_accounts::UserAccountsStore;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountCredentials {
    pub username: String,
    pub password: String,
    pub is_custom: bool,
}

pub struct AccountManager {
    /// Default + CLI-injected accounts (never persisted to disk).
    builtin: RwLock<Vec<AccountCredentials>>,
    /// Encrypted user accounts persisted to `<app_data>/user_accounts.enc`.
    user_store: Arc<UserAccountsStore>,
}

const DEFAULT_ACCOUNTS: &[(&str, &str)] = &[
    ("ruiiixx", "UzY3R0JUQjgzRDNZ"),
    ("premexilmenledgconis", "M3BYYkhaSmxEYg=="),
    ("vAbuDy", "Qm9vbHE4dmlw"),
    ("adgjl1182", "UUVUVU85OTk5OQ=="),
    ("gobjj16182", "enVvYmlhbzgyMjI="),
    ("787109690", "SHVjVXhZTVFpZzE1"),
];

/// Dedicated account used exclusively for the hidden Steam webview that
/// drives the Workshop parser. It is intentionally NOT part of
/// `DEFAULT_ACCOUNTS`, so it never appears in the "Download account"
/// selector — mirroring the way the original Python app separated
/// "parser login" from "download account".
const PARSER_ACCOUNT: (&str, &str) = ("weworkshopmanager2", "a2Fpem9rdV9vX2h5b3U=");

impl AccountManager {
    pub fn from_runtime(app_data_dir: &std::path::Path) -> Self {
        let builtin = build_default();
        let user_store = Arc::new(UserAccountsStore::open(app_data_dir));
        Self {
            builtin: RwLock::new(builtin),
            user_store,
        }
    }

    fn merged(&self) -> Vec<AccountCredentials> {
        let mut all = self.builtin.read().clone();
        for stored in self.user_store.list() {
            all.push(AccountCredentials {
                username: stored.username,
                password: stored.password,
                is_custom: true,
            });
        }
        all
    }

    pub fn list_usernames(&self) -> Vec<String> {
        self.merged().into_iter().map(|a| a.username).collect()
    }

    /// Return per-account metadata without leaking passwords to the frontend.
    pub fn list_detailed(&self) -> Vec<AccountCredentials> {
        self.merged()
            .into_iter()
            .map(|a| AccountCredentials {
                username: a.username,
                password: String::new(),
                is_custom: a.is_custom,
            })
            .collect()
    }

    pub fn credentials(&self, index: usize) -> AccountCredentials {
        let all = self.merged();
        if all.is_empty() {
            return AccountCredentials {
                username: String::new(),
                password: String::new(),
                is_custom: false,
            };
        }
        all.get(index).cloned().unwrap_or_else(|| all[0].clone())
    }

    pub fn username_at(&self, index: usize) -> String {
        self.credentials(index).username
    }

    pub fn add_user_account(&self, username: &str, password: &str) -> Result<(), String> {
        self.user_store.add(username, password)
    }

    pub fn remove_user_account(&self, username: &str) -> Result<(), String> {
        self.user_store.remove(username)
    }

    pub fn clear_user_accounts(&self) -> Result<(), String> {
        self.user_store.clear()
    }

    /// Custom accounts (only) — used by the SettingsDialog.
    pub fn list_custom_usernames(&self) -> Vec<String> {
        self.user_store
            .list()
            .into_iter()
            .map(|a| a.username)
            .collect()
    }

    /// Credentials for the dedicated parser login account
    /// (`weworkshopmanager2`). Used by `steam_auto_login` when no specific
    /// download account was requested, so the hidden webview always logs
    /// in under this identity regardless of the user's Download Account
    /// selection.
    pub fn parser_credentials(&self) -> AccountCredentials {
        let password = general_purpose::STANDARD
            .decode(PARSER_ACCOUNT.1)
            .ok()
            .and_then(|bytes| String::from_utf8(bytes).ok())
            .unwrap_or_default();
        AccountCredentials {
            username: PARSER_ACCOUNT.0.into(),
            password,
            is_custom: false,
        }
    }
}

fn build_default() -> Vec<AccountCredentials> {
    DEFAULT_ACCOUNTS
        .iter()
        .map(|(user, encoded)| {
            let password = general_purpose::STANDARD
                .decode(encoded)
                .ok()
                .and_then(|bytes| String::from_utf8(bytes).ok())
                .unwrap_or_default();
            AccountCredentials {
                username: (*user).into(),
                password,
                is_custom: false,
            }
        })
        .collect()
}
