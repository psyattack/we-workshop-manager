//! In-memory parser debug log. The original PyQt app exposes a
//! "Debug Mode" toggle that turns the headless QWebEngineView into a
//! visible window so the developer can inspect what Steam returns. We
//! don't have a webview-backed parser anymore, so the Tauri port keeps
//! a rolling history of the last N raw HTTP responses (URL, status,
//! latency, length, head of the HTML) and exposes them through a
//! command for a simple in-app dialog.

use std::sync::OnceLock;

use parking_lot::Mutex;
use serde::Serialize;

const MAX_ENTRIES: usize = 30;
const PREVIEW_LIMIT: usize = 200_000; // ~200 KB cap per entry

#[derive(Debug, Clone, Serialize)]
pub struct DebugEntry {
    pub url: String,
    pub status: u16,
    pub elapsed_ms: u64,
    pub size_bytes: usize,
    pub timestamp_ms: u128,
    pub kind: String,
    /// Truncated raw response body (first PREVIEW_LIMIT bytes).
    pub html: String,
    pub items_parsed: u32,
}

static LOG: OnceLock<Mutex<Vec<DebugEntry>>> = OnceLock::new();

fn log() -> &'static Mutex<Vec<DebugEntry>> {
    LOG.get_or_init(|| Mutex::new(Vec::with_capacity(MAX_ENTRIES)))
}

pub fn record(
    kind: &str,
    url: &str,
    status: u16,
    elapsed_ms: u64,
    html: &str,
    items_parsed: u32,
) {
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let preview = if html.len() > PREVIEW_LIMIT {
        let mut s = String::with_capacity(PREVIEW_LIMIT + 32);
        s.push_str(&html[..PREVIEW_LIMIT]);
        s.push_str("\n\n[…truncated…]");
        s
    } else {
        html.to_string()
    };
    let entry = DebugEntry {
        url: url.to_string(),
        status,
        elapsed_ms,
        size_bytes: html.len(),
        timestamp_ms: now,
        kind: kind.to_string(),
        html: preview,
        items_parsed,
    };
    let mut guard = log().lock();
    guard.push(entry);
    let len = guard.len();
    if len > MAX_ENTRIES {
        guard.drain(0..len - MAX_ENTRIES);
    }
}

pub fn snapshot() -> Vec<DebugEntry> {
    log().lock().clone()
}

pub fn clear() {
    log().lock().clear();
}
