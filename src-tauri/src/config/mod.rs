//! Configuration module split into settings and metadata services.

mod metadata;
mod settings;

use serde_json::{json, Value};

pub use metadata::MetadataService;
pub use settings::{SettingsService, WindowGeometry};

// Shared utility functions
pub fn deep_merge(mut base: Value, override_val: Value) -> Value {
    match (&mut base, override_val) {
        (Value::Object(base_map), Value::Object(over_map)) => {
            for (key, over) in over_map {
                let entry = base_map.entry(key).or_insert(Value::Null);
                *entry = deep_merge(entry.clone(), over);
            }
            base
        }
        (_, other) => other,
    }
}

pub fn resolve_value<'a>(root: &'a Value, path: &str) -> Option<&'a Value> {
    let mut current = root;
    for part in path.split('.') {
        current = current.get(part)?;
    }
    Some(current)
}

pub fn set_value(root: &mut Value, path: &str, value: Value) {
    let parts: Vec<&str> = path.split('.').collect();
    if parts.is_empty() {
        return;
    }

    let mut current = root;
    for (i, part) in parts.iter().enumerate() {
        let is_last = i == parts.len() - 1;
        if !current.is_object() {
            *current = json!({});
        }
        let map = current.as_object_mut().unwrap();
        if is_last {
            map.insert(part.to_string(), value);
            return;
        }
        current = map.entry(part.to_string()).or_insert_with(|| json!({}));
    }
}

pub fn remove_value(root: &mut Value, path: &str) {
    let parts: Vec<&str> = path.split('.').collect();
    if parts.is_empty() {
        return;
    }

    let mut current = root;
    for (i, part) in parts.iter().enumerate() {
        let is_last = i == parts.len() - 1;
        match current {
            Value::Object(map) => {
                if is_last {
                    map.remove(*part);
                    return;
                }
                match map.get_mut(*part) {
                    Some(next) => current = next,
                    None => return,
                }
            }
            _ => return,
        }
    }
}
