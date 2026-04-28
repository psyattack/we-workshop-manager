//! Translation service. Loads JSON bundles at startup and resolves keys
//! with dot-separated paths and optional `{placeholder}` substitutions.
//! Language can be switched at runtime without restarting the app.

use serde_json::Value;
use std::collections::HashMap;

const EN_JSON: &str = include_str!("../../locales/en.json");
const RU_JSON: &str = include_str!("../../locales/ru.json");

pub struct I18nService {
    pub current: String,
    pub bundles: HashMap<String, Value>,
}

impl I18nService {
    pub fn load(current: &str) -> Self {
        let mut bundles: HashMap<String, Value> = HashMap::new();
        if let Ok(v) = serde_json::from_str::<Value>(EN_JSON) {
            bundles.insert("en".into(), v);
        }
        if let Ok(v) = serde_json::from_str::<Value>(RU_JSON) {
            bundles.insert("ru".into(), v);
        }
        Self {
            current: current.to_string(),
            bundles,
        }
    }

    pub fn available(&self) -> Vec<(String, String)> {
        vec![
            ("en".into(), "English".into()),
            ("ru".into(), "Русский".into()),
        ]
    }

    pub fn set_language(&mut self, code: &str) {
        if self.bundles.contains_key(code) {
            self.current = code.to_string();
        }
    }

    pub fn bundle_for(&self, code: &str) -> Value {
        self.bundles
            .get(code)
            .cloned()
            .unwrap_or_else(|| serde_json::json!({}))
    }

    pub fn bundle_all(&self) -> Value {
        let mut out = serde_json::Map::new();
        for (k, v) in &self.bundles {
            out.insert(k.clone(), v.clone());
        }
        Value::Object(out)
    }
}
