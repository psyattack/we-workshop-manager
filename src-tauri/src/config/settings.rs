//! Settings service for application configuration.

use std::fs;
use std::path::{Path, PathBuf};

use parking_lot::Mutex;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use super::{deep_merge, remove_value, resolve_value, set_value};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WindowGeometry {
    pub x: i32,
    pub y: i32,
    pub width: i32,
    pub height: i32,
    pub is_maximized: bool,
}

pub struct SettingsService {
    pub path: PathBuf,
    data: Mutex<Value>,
}

impl SettingsService {
    pub fn load(path: &Path) -> anyhow::Result<Self> {
        let data = match fs::read_to_string(path) {
            Ok(raw) => serde_json::from_str::<Value>(&raw).unwrap_or_else(|_| default_settings()),
            Err(_) => default_settings(),
        };
        let merged = deep_merge(default_settings(), data);
        Ok(Self {
            path: path.to_path_buf(),
            data: Mutex::new(merged),
        })
    }

    pub fn snapshot(&self) -> Value {
        self.data.lock().clone()
    }

    pub fn save(&self) -> anyhow::Result<()> {
        if let Some(parent) = self.path.parent() {
            fs::create_dir_all(parent).ok();
        }
        let raw = serde_json::to_string_pretty(&*self.data.lock())?;
        fs::write(&self.path, raw)?;
        Ok(())
    }

    pub fn get(&self, path: &str) -> Option<Value> {
        resolve_value(&self.data.lock(), path).cloned()
    }

    pub fn set(&self, path: &str, value: Value) -> anyhow::Result<()> {
        {
            let mut guard = self.data.lock();
            set_value(&mut guard, path, value);
        }
        self.save()
    }

    pub fn remove(&self, path: &str) -> anyhow::Result<()> {
        {
            let mut guard = self.data.lock();
            remove_value(&mut guard, path);
        }
        self.save()
    }

    // --- convenience getters ---

    pub fn get_directory(&self) -> Option<String> {
        self.get("system.directory")
            .and_then(|v| v.as_str().map(ToString::to_string))
            .filter(|s| !s.is_empty())
    }

    pub fn set_directory(&self, value: &str) {
        self.set("system.directory", Value::String(value.to_string()))
            .ok();
    }

    pub fn get_language(&self) -> String {
        self.get("general.appearance.language")
            .and_then(|v| v.as_str().map(ToString::to_string))
            .unwrap_or_else(|| "en".to_string())
    }

    pub fn set_language(&self, value: &str) {
        self.set(
            "general.appearance.language",
            Value::String(value.to_string()),
        )
        .ok();
    }

    pub fn get_theme(&self) -> String {
        self.get("general.appearance.theme")
            .and_then(|v| v.as_str().map(ToString::to_string))
            .unwrap_or_else(|| "dark".to_string())
    }

    pub fn get_account_number(&self) -> u32 {
        self.get("account.account.account_number")
            .and_then(|v| v.as_u64())
            .unwrap_or(3) as u32
    }

    pub fn set_account_number(&self, value: u32) {
        self.set(
            "account.account.account_number",
            Value::Number(value.into()),
        )
        .ok();
    }

    pub fn set_window_geometry(&self, geom: WindowGeometry) {
        if !self.get_save_window_state() {
            return;
        }
        if let Ok(value) = serde_json::to_value(geom) {
            self.set("general.behavior.window_geometry", value).ok();
        }
    }

    pub fn get_save_window_state(&self) -> bool {
        self.get("general.behavior.save_window_state")
            .and_then(|v| v.as_bool())
            .unwrap_or(true)
    }

    pub fn get_skip_version(&self) -> String {
        self.get("general.behavior.skip_version")
            .and_then(|v| v.as_str().map(ToString::to_string))
            .unwrap_or_default()
    }
}

fn default_settings() -> Value {
    json!({
        "system": {
            "directory": ""
        },
        "account": {
            "account": {
                "account_number": 3
            }
        },
        "general": {
            "appearance": {
                "language": "en",
                "theme": "dark",
                "accent": "indigo"
            },
            "behavior": {
                "minimize_on_apply": false,
                "preload_next_page": true,
                "auto_check_updates": true,
                "auto_init_metadata": true,
                "auto_apply_last_downloaded": false,
                "skip_version": "",
                "save_window_state": true,
                "window_geometry": {
                    "x": -1,
                    "y": -1,
                    "width": 1280,
                    "height": 800,
                    "is_maximized": false
                }
            }
        }
    })
}
