//! Encrypted storage for user-added Steam accounts.
//!
//! Faithful Rust port of the Python `EncryptedStorage` + `UserAccountsService`:
//! keys are derived from a machine-bound seed via PBKDF2-HMAC-SHA256
//! (100 000 iterations, identical to the original) and the resulting 32-byte
//! key is fed to AES-256-GCM (the Python version used Fernet, which is
//! AES-128-CBC + HMAC; we upgrade to AES-GCM for authenticated encryption).
//!
//! On-disk layout: `<app_data>/user_accounts.enc`
//!   first 12 bytes: nonce
//!   remaining: AES-256-GCM ciphertext + 16-byte tag of a UTF-8 JSON array
//!   `[{"username": "...", "password": "..."}, ...]`.

use std::path::PathBuf;

use aes_gcm::aead::{Aead, KeyInit};
use aes_gcm::{Aes256Gcm, Key, Nonce};
use parking_lot::Mutex;
use pbkdf2::pbkdf2_hmac;
use rand::RngCore;
use serde::{Deserialize, Serialize};
use sha2::Sha256;

const SALT: &[u8] = b"WEave_Salt_2026_v1";
const ITERATIONS: u32 = 100_000;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoredUserAccount {
    pub username: String,
    pub password: String,
}

pub struct UserAccountsStore {
    file_path: PathBuf,
    cipher: Aes256Gcm,
    accounts: Mutex<Vec<StoredUserAccount>>,
}

impl UserAccountsStore {
    pub fn open(app_data_dir: &std::path::Path) -> Self {
        let file_path = app_data_dir.join("user_accounts.enc");
        let cipher = build_cipher();
        let accounts = Mutex::new(load_accounts(&file_path, &cipher));
        Self {
            file_path,
            cipher,
            accounts,
        }
    }

    pub fn list(&self) -> Vec<StoredUserAccount> {
        self.accounts.lock().clone()
    }

    pub fn add(&self, username: &str, password: &str) -> Result<(), String> {
        if username.is_empty() || password.is_empty() {
            return Err("Username and password are required".into());
        }
        let mut guard = self.accounts.lock();
        if guard.iter().any(|a| a.username == username) {
            return Err("Account with this username already exists".into());
        }
        guard.push(StoredUserAccount {
            username: username.into(),
            password: password.into(),
        });
        save_accounts(&self.file_path, &self.cipher, &guard)
    }

    pub fn remove(&self, username: &str) -> Result<(), String> {
        let mut guard = self.accounts.lock();
        let before = guard.len();
        guard.retain(|a| a.username != username);
        if guard.len() == before {
            return Err("Account not found".into());
        }
        save_accounts(&self.file_path, &self.cipher, &guard)
    }

    pub fn clear(&self) -> Result<(), String> {
        let mut guard = self.accounts.lock();
        guard.clear();
        save_accounts(&self.file_path, &self.cipher, &guard)
    }
}

fn machine_seed() -> Vec<u8> {
    let node = hostname_string();
    let machine = std::env::consts::ARCH.to_string();
    format!("{node}{machine}").into_bytes()
}

fn hostname_string() -> String {
    // Read the same identifiers that the Python `platform.node()` returns.
    if let Ok(name) = std::env::var("COMPUTERNAME") {
        if !name.is_empty() {
            return name;
        }
    }
    if let Ok(name) = std::env::var("HOSTNAME") {
        if !name.is_empty() {
            return name;
        }
    }
    if let Ok(bytes) = std::fs::read("/etc/hostname") {
        if let Ok(text) = std::str::from_utf8(&bytes) {
            let trimmed = text.trim();
            if !trimmed.is_empty() {
                return trimmed.to_string();
            }
        }
    }
    "localhost".into()
}

fn build_cipher() -> Aes256Gcm {
    let seed = machine_seed();
    let mut key = [0u8; 32];
    pbkdf2_hmac::<Sha256>(&seed, SALT, ITERATIONS, &mut key);
    Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&key))
}

fn load_accounts(path: &std::path::Path, cipher: &Aes256Gcm) -> Vec<StoredUserAccount> {
    let Ok(bytes) = std::fs::read(path) else {
        return Vec::new();
    };
    if bytes.len() < 12 {
        return Vec::new();
    }
    let (nonce_bytes, ct) = bytes.split_at(12);
    let nonce = Nonce::from_slice(nonce_bytes);
    let plaintext = match cipher.decrypt(nonce, ct) {
        Ok(p) => p,
        Err(_) => return Vec::new(),
    };
    serde_json::from_slice(&plaintext).unwrap_or_default()
}

fn save_accounts(
    path: &std::path::Path,
    cipher: &Aes256Gcm,
    accounts: &[StoredUserAccount],
) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let json = serde_json::to_vec(accounts).map_err(|e| e.to_string())?;
    let mut nonce_bytes = [0u8; 12];
    rand::thread_rng().fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    let ct = cipher
        .encrypt(nonce, json.as_ref())
        .map_err(|e| e.to_string())?;
    let mut out = Vec::with_capacity(12 + ct.len());
    out.extend_from_slice(&nonce_bytes);
    out.extend_from_slice(&ct);
    std::fs::write(path, out).map_err(|e| e.to_string())
}
