//! Steam Workshop scraping. The original Python app uses a logged-in
//! QWebEngineView to evaluate JS and read DOM; in the Rust port we hit the
//! very same HTML endpoints via `reqwest` + `scraper` and pull the exact
//! same fields out of the resulting markup. Login (cookies) is optional
//! and persisted on disk.

pub mod debug;
pub mod parser;
pub mod url_builder;
pub mod webview;

use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;

use parking_lot::Mutex;
use regex::Regex;
use reqwest::cookie::Jar;
use reqwest::Client;
use serde::{Deserialize, Serialize};

use crate::constants::APP_VERSION;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkshopFilters {
    pub search: String,
    pub sort: String,
    pub days: String,
    pub category: String,
    pub type_tag: String,
    pub age_rating: String,
    pub resolution: String,
    pub misc_tags: Vec<String>,
    pub genre_tags: Vec<String>,
    pub excluded_misc_tags: Vec<String>,
    pub excluded_genre_tags: Vec<String>,
    pub asset_type: String,
    pub asset_genre: String,
    pub script_type: String,
    pub required_flags: Vec<String>,
    pub page: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkshopItem {
    pub pubfileid: String,
    pub title: String,
    pub preview_url: String,
    pub author: String,
    pub author_url: String,
    pub description: String,
    pub file_size: String,
    pub posted_date: String,
    pub updated_date: String,
    pub tags: serde_json::Value,
    pub rating_star_file: String,
    pub num_ratings: String,
    pub is_collection: bool,
    /// Collections this item appears in (parsed from `.parentCollection` on
    /// the details page). Empty if not yet fetched.
    #[serde(default)]
    pub collections: Vec<CollectionRef>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct CollectionRef {
    pub id: String,
    pub title: String,
    pub item_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkshopPage {
    pub items: Vec<WorkshopItem>,
    pub current_page: u32,
    pub total_pages: u32,
    pub total_items: u64,
}

/// Snapshot of the Steam account that the Workshop client is scraping as.
/// Populated from `https://steamcommunity.com/my/home/` — mirrors whatever
/// Steam itself reports, so it matches the cookies the parser uses
/// regardless of which download account is selected in Settings.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SteamAccount {
    pub persona_name: String,
    pub account_name: String,
    pub steamid: String,
    pub profile_url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct CollectionContents {
    pub collection_id: String,
    pub title: String,
    pub description: String,
    pub preview_url: String,
    pub author: String,
    pub author_url: String,
    pub items: Vec<WorkshopItem>,
    pub related_collections: Vec<WorkshopItem>,
    pub info: serde_json::Value,
}

pub struct WorkshopClient {
    client: Client,
    cookie_jar: Arc<Jar>,
    cookies_file: PathBuf,
    page_cache: Arc<Mutex<lru::LruCache<String, WorkshopPage>>>,
    item_cache: Arc<Mutex<lru::LruCache<String, WorkshopItem>>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct PersistedCookie {
    name: String,
    value: String,
    domain: String,
    path: String,
}

impl WorkshopClient {
    pub fn new(cookies_dir: PathBuf) -> Self {
        std::fs::create_dir_all(&cookies_dir).ok();
        let cookie_jar = Arc::new(Jar::default());
        let cookies_file = cookies_dir.join("cookies.json");

        // Load persisted cookies into the jar so that subsequent runs remain
        // "logged in" even before the hidden webview has a chance to sync —
        // this mirrors the Python app's QWebEngineProfile persistence.
        if let Ok(bytes) = std::fs::read(&cookies_file) {
            if let Ok(cookies) = serde_json::from_slice::<Vec<PersistedCookie>>(&bytes) {
                for c in cookies {
                    let url_str = format!(
                        "https://{}{}",
                        c.domain.trim_start_matches('.'),
                        if c.path.is_empty() { "/" } else { &c.path }
                    );
                    if let Ok(url) = url_str.parse::<url::Url>() {
                        let header = format!(
                            "{}={}; Path={}; Domain={}",
                            c.name, c.value, c.path, c.domain
                        );
                        cookie_jar.add_cookie_str(&header, &url);
                    }
                }
            }
        }

        let client = Client::builder()
            .cookie_provider(cookie_jar.clone())
            .gzip(true)
            .brotli(true)
            .timeout(Duration::from_secs(20))
            .user_agent(format!(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 WEave/{}",
                APP_VERSION
            ))
            .build()
            .expect("reqwest client");

        Self {
            client,
            cookie_jar,
            cookies_file,
            page_cache: Arc::new(Mutex::new(lru::LruCache::new(
                std::num::NonZeroUsize::new(20).unwrap(),
            ))),
            item_cache: Arc::new(Mutex::new(lru::LruCache::new(
                std::num::NonZeroUsize::new(600).unwrap(),
            ))),
        }
    }

    /// Persist the list of cookies we just scraped from the hidden webview
    /// to `cookies.json` so that they survive across restarts. Takes a
    /// vector of (name, value, domain, path) tuples — the jar doesn't expose
    /// enumeration directly, so we feed it from the webview sync path.
    pub fn save_cookies(&self, cookies: &[(String, String, String, String)]) {
        let persisted: Vec<PersistedCookie> = cookies
            .iter()
            .map(|(n, v, d, p)| PersistedCookie {
                name: n.clone(),
                value: v.clone(),
                domain: d.clone(),
                path: p.clone(),
            })
            .collect();
        if let Ok(json) = serde_json::to_vec_pretty(&persisted) {
            if let Some(parent) = self.cookies_file.parent() {
                std::fs::create_dir_all(parent).ok();
            }
            let _ = std::fs::write(&self.cookies_file, json);
        }
    }

    pub fn client(&self) -> Client {
        self.client.clone()
    }

    pub fn cookie_jar(&self) -> Arc<Jar> {
        self.cookie_jar.clone()
    }

    pub fn clear_caches(&self) {
        self.page_cache.lock().clear();
        self.item_cache.lock().clear();
    }

    /// Ask Steam itself who we're logged in as, by following the redirect on
    /// `https://steamcommunity.com/my/` and pulling `g_rgProfileData` /
    /// `g_steamID` out of the returned profile HTML. Returns `None` when the
    /// session cookies don't resolve to a logged-in account.
    ///
    /// This powers the "parser login check" the user asked for — it's the
    /// single source of truth for which Steam account the Workshop scraper
    /// is currently acting as, independent of whatever's selected in the
    /// Settings → Download account UI.
    pub async fn current_account(&self) -> Option<SteamAccount> {
        let resp = self
            .client
            .get("https://steamcommunity.com/my/home/")
            .send()
            .await
            .ok()?;
        // `/my` redirects to `/id/<vanity>` or `/profiles/<steamid>` when
        // logged in; anonymous sessions land on the login page.
        let final_url = resp.url().clone();
        let url_str = final_url.to_string();
        if url_str.contains("/login/") {
            return None;
        }
        let body = resp.text().await.ok()?;

        // Try `g_rgProfileData = { ... };` — this JSON is rendered into
        // every profile page and has both the vanity URL and the persona.
        let persona_name = Regex::new(r#""personaname"\s*:\s*"([^"]+)""#)
            .ok()?
            .captures(&body)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string());
        let steamid = Regex::new(r#""steamid"\s*:\s*"(\d+)""#)
            .ok()
            .and_then(|re| re.captures(&body))
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string())
            .or_else(|| {
                Regex::new(r#"g_steamID\s*=\s*"(\d+)""#)
                    .ok()
                    .and_then(|re| re.captures(&body))
                    .and_then(|c| c.get(1))
                    .map(|m| m.as_str().to_string())
            });
        // Fallback for the account login name: parse `AccountName` out of
        // the embedded JS if present (older skin).
        let account_name = Regex::new(r#"g_AccountName\s*=\s*"([^"]+)""#)
            .ok()
            .and_then(|re| re.captures(&body))
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string());

        // If we couldn't even find a persona or a steamid, treat as
        // logged-out rather than returning an empty struct.
        if persona_name.is_none() && steamid.is_none() && account_name.is_none() {
            return None;
        }

        Some(SteamAccount {
            persona_name: persona_name.unwrap_or_default(),
            account_name: account_name.unwrap_or_default(),
            steamid: steamid.unwrap_or_default(),
            profile_url: url_str,
        })
    }

    pub async fn browse(&self, filters: &WorkshopFilters) -> anyhow::Result<WorkshopPage> {
        let url = url_builder::build_browse(filters);
        self.browse_url(&url, filters.page.max(1)).await
    }

    pub async fn browse_collections(
        &self,
        filters: &WorkshopFilters,
    ) -> anyhow::Result<WorkshopPage> {
        let url = url_builder::build_collections_browse(filters);
        self.browse_url(&url, filters.page.max(1)).await
    }

    pub async fn author_items(
        &self,
        profile_url: &str,
        filters: &WorkshopFilters,
    ) -> anyhow::Result<WorkshopPage> {
        let url = url_builder::build_author_items(profile_url, filters);
        self.browse_url(&url, filters.page.max(1)).await
    }

    pub async fn author_collections(
        &self,
        profile_url: &str,
        filters: &WorkshopFilters,
    ) -> anyhow::Result<WorkshopPage> {
        let url = url_builder::build_author_collections(profile_url, filters);
        self.browse_url(&url, filters.page.max(1)).await
    }

    async fn browse_url(&self, url: &str, page: u32) -> anyhow::Result<WorkshopPage> {
        if let Some(cached) = self.page_cache.lock().get(url) {
            return Ok(cached.clone());
        }
        let started = std::time::Instant::now();
        let resp = self.client.get(url).send().await?;
        let status = resp.status().as_u16();
        let html = resp.text().await?;
        let mut parsed = parser::parse_browse(&html, page);
        parsed.current_page = page.max(parsed.current_page);
        debug::record(
            "browse",
            url,
            status,
            started.elapsed().as_millis() as u64,
            &html,
            parsed.items.len() as u32,
        );
        self.page_cache
            .lock()
            .put(url.to_string(), parsed.clone());
        Ok(parsed)
    }

    pub async fn item_details(&self, pubfileid: &str) -> anyhow::Result<WorkshopItem> {
        if let Some(cached) = self.item_cache.lock().get(pubfileid) {
            return Ok(cached.clone());
        }
        let url = format!(
            "https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}"
        );
        let started = std::time::Instant::now();
        let resp = self.client.get(&url).send().await?;
        let status = resp.status().as_u16();
        let html = resp.text().await?;
        let item = parser::parse_item_details(&html, pubfileid);
        debug::record(
            "item",
            &url,
            status,
            started.elapsed().as_millis() as u64,
            &html,
            1,
        );
        self.item_cache
            .lock()
            .put(pubfileid.to_string(), item.clone());
        Ok(item)
    }

    pub async fn collection_contents(
        &self,
        collection_id: &str,
    ) -> anyhow::Result<CollectionContents> {
        let url = url_builder::build_collection_url(collection_id);
        let started = std::time::Instant::now();
        let resp = self.client.get(&url).send().await?;
        let status = resp.status().as_u16();
        let html = resp.text().await?;
        let contents = parser::parse_collection_contents(&html, collection_id);
        debug::record(
            "collection",
            &url,
            status,
            started.elapsed().as_millis() as u64,
            &html,
            contents.items.len() as u32,
        );
        Ok(contents)
    }
}
