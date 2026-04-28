//! Description translation via the unofficial Google Translate endpoint.
//! Mirrors the Python `description_translation_service` using
//! `deep_translator` — we call the single-endpoint JSON API directly.

use parking_lot::Mutex;
use std::collections::HashMap;
use url::form_urlencoded;

#[derive(Default)]
pub struct TranslatorCache {
    cache: Mutex<HashMap<String, String>>,
}

impl TranslatorCache {
    pub fn new() -> Self {
        Self::default()
    }

    fn key(target: &str, source: &str, text: &str) -> String {
        format!("{target}::{source}::{text}")
    }

    pub fn get(&self, target: &str, source: &str, text: &str) -> Option<String> {
        self.cache.lock().get(&Self::key(target, source, text)).cloned()
    }

    pub fn put(&self, target: &str, source: &str, text: &str, value: String) {
        self.cache
            .lock()
            .insert(Self::key(target, source, text), value);
    }
}

pub async fn translate_text(
    text: &str,
    source_lang: &str,
    target_lang: &str,
) -> anyhow::Result<String> {
    if text.trim().is_empty() {
        return Ok(text.to_string());
    }

    let source = map_language(source_lang);
    let target = map_language(target_lang);
    if source == target {
        return Ok(text.to_string());
    }

    let params: String = form_urlencoded::Serializer::new(String::new())
        .append_pair("client", "gtx")
        .append_pair("sl", source)
        .append_pair("tl", target)
        .append_pair("dt", "t")
        .append_pair("q", text)
        .finish();

    let url = format!("https://translate.googleapis.com/translate_a/single?{params}");

    let client = reqwest::Client::builder()
        .user_agent("Mozilla/5.0 WEave")
        .timeout(std::time::Duration::from_secs(10))
        .build()?;

    let body = client.get(url).send().await?.text().await?;
    let json: serde_json::Value = serde_json::from_str(&body)?;

    let mut result = String::new();
    if let Some(arr) = json.get(0).and_then(|v| v.as_array()) {
        for entry in arr {
            if let Some(s) = entry.get(0).and_then(|v| v.as_str()) {
                result.push_str(s);
            }
        }
    }

    if result.is_empty() {
        anyhow::bail!("translation returned empty result");
    }

    Ok(result)
}

fn map_language(code: &str) -> &str {
    match code {
        // Google's translate_a/single endpoint accepts `auto` as the
        // source language and infers it from the text. The previous
        // mapping silently fell through to "en", which broke detection
        // of any non-English Workshop description.
        "auto" | "" => "auto",
        "en" => "en",
        "ru" => "ru",
        "de" => "de",
        "es" => "es",
        "fr" => "fr",
        "pt" => "pt",
        "it" => "it",
        "pl" => "pl",
        "ja" => "ja",
        "ko" => "ko",
        "zh" => "zh-CN",
        "zh-CN" | "zh-Hans" => "zh-CN",
        "zh-TW" | "zh-Hant" => "zh-TW",
        other => {
            // For an unknown locale, ask Google to auto-detect rather
            // than mistranslating from English.
            if other.contains('-') {
                other
            } else {
                "auto"
            }
        }
    }
}
