//! Metadata service for wallpaper metadata storage.

use std::fs;
use std::path::{Path, PathBuf};

use parking_lot::Mutex;
use serde_json::{json, Value};

use super::{remove_value, resolve_value, set_value};

pub struct MetadataService {
    pub path: PathBuf,
    data: Mutex<Value>,
}

impl MetadataService {
    pub fn load(path: &Path) -> anyhow::Result<Self> {
        let data = match fs::read_to_string(path) {
            Ok(raw) => serde_json::from_str::<Value>(&raw).unwrap_or_else(|_| json!({})),
            Err(_) => json!({}),
        };
        Ok(Self {
            path: path.to_path_buf(),
            data: Mutex::new(data),
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

    pub fn get_all(&self) -> Value {
        self.snapshot()
    }

    pub fn get_item(&self, pubfileid: &str) -> Option<Value> {
        self.get(pubfileid)
    }

    pub fn set_item(&self, pubfileid: &str, value: Value) {
        self.set(pubfileid, value).ok();
    }

    pub fn remove_item(&self, pubfileid: &str) {
        self.remove(pubfileid).ok();
    }
}
