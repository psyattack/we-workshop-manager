//! Account management. Built-in public accounts are embedded as an encrypted
//! bundle; user-added accounts are stored encrypted on disk via
//! `user_accounts::UserAccountsStore`.

use std::sync::Arc;

use aes_gcm::aead::{Aead, KeyInit};
use aes_gcm::{Aes256Gcm, Key, Nonce};
use base64::{engine::general_purpose, Engine as _};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

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

const BUILTIN_ACCOUNT_BUNDLE_KEY: &[u8] = b"WEave built-in Steam accounts bundle v1";
const BUILTIN_ACCOUNT_BUNDLE: &str = concat!(
    "V0VhdmVBY2N0MDAxI0OedwXdnRGyKIzyG9DqJSrCmfP5uvje40DeXiI+e4qdETXVxWl0Nh3GKfZtnKRMyE4GZvum",
    "OBc/XEGHW4KHyh6zzAMr6L/nuqCLbTxvvTzLWs4kKQdPbN55ts+ue3SqAWJVTOJ0MXaGQUCdQ/ejH7PQot84sz3J",
    "HYO1vIKoYIanoC1LmcuMZlkkKlmwPyh/Km82n/2nlDMsgD6qP7/+GcqW+EeFcqCKSfsje8PM27d+IwqXmrSmWSRM",
    "zzBxtA33SJ/1AStLq38dG6vW8dv3GNercy0JTt48uL5qCJM7I9aDVqueRAfRIp7WyLX7dTmqUK7CkYI4Xd22GK8/"
);

#[derive(Debug, Deserialize)]
struct BuiltinAccountsBundle {
    download: Vec<(String, String)>,
    parser: (String, String),
}

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
        let bundle = load_builtin_bundle().unwrap_or_default();
        AccountCredentials {
            username: bundle.parser.0,
            password: bundle.parser.1,
            is_custom: false,
        }
    }
}

fn build_default() -> Vec<AccountCredentials> {
    load_builtin_bundle()
        .map(|bundle| {
            bundle
                .download
                .into_iter()
                .map(|(username, password)| AccountCredentials {
                    username,
                    password,
                    is_custom: false,
                })
                .collect()
        })
        .unwrap_or_default()
}

fn load_builtin_bundle() -> Result<BuiltinAccountsBundle, String> {
    let raw = general_purpose::STANDARD
        .decode(BUILTIN_ACCOUNT_BUNDLE)
        .map_err(|e| e.to_string())?;
    if raw.len() < 12 {
        return Err("Built-in account bundle is malformed".into());
    }
    let (nonce, ciphertext) = raw.split_at(12);
    let key = Sha256::digest(BUILTIN_ACCOUNT_BUNDLE_KEY);
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&key));
    let plaintext = cipher
        .decrypt(Nonce::from_slice(nonce), ciphertext)
        .map_err(|e| e.to_string())?;
    serde_json::from_slice(&plaintext).map_err(|e| e.to_string())
}

impl Default for BuiltinAccountsBundle {
    fn default() -> Self {
        Self {
            download: Vec::new(),
            parser: (String::new(), String::new()),
        }
    }
}
