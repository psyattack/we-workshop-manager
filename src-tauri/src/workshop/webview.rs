//! Hidden Steam WebView: keeps a persistent browser profile (matches the
//! Python app's `QWebEngineProfile` with persistent cookies) so that the
//! user can log in to Steam once, and the authenticated cookies are reused
//! for reqwest-based Workshop scraping on every subsequent run.
//!
//! Ports of:
//!   - `infrastructure/steam/workshop_scripts.py::login_form_fill_script`
//!   - `ui/tabs/workshop_tab.py::_handle_load_finished` (auto-login driver)
//!
//! The webview is created invisible and remains invisible while we drive the
//! login form in JavaScript; only when auto-login fails do we prompt the
//! user to click "Open Steam login" and show the window so they can log in
//! (or answer a Steam Guard challenge) manually.

use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;

use reqwest::cookie::{CookieStore, Jar};
use reqwest::header::HeaderValue;
use tauri::{AppHandle, Manager, WebviewUrl, WebviewWindowBuilder};
use tokio::sync::Mutex;
use tokio::time::sleep;

pub const LABEL: &str = "steam-webview";
const STEAM_LOGIN_URL: &str = "https://steamcommunity.com/login/home/?goto=workshop%2Fbrowse%2F%3Fappid%3D431960";
const STEAM_HOME_URL: &str = "https://steamcommunity.com/workshop/browse/?appid=431960";

pub type CookiePersistFn = Arc<dyn Fn(&[(String, String, String, String)]) + Send + Sync>;

pub struct SteamWebview {
    app: AppHandle,
    data_dir: PathBuf,
    jar: Arc<Jar>,
    cookies_file: PathBuf,
    persist: Option<CookiePersistFn>,
    lock: Mutex<()>,
}

impl SteamWebview {
    pub fn new(
        app: AppHandle,
        data_dir: PathBuf,
        jar: Arc<Jar>,
        cookies_file: PathBuf,
        persist: Option<CookiePersistFn>,
    ) -> Self {
        std::fs::create_dir_all(&data_dir).ok();
        Self {
            app,
            data_dir,
            jar,
            cookies_file,
            persist,
            lock: Mutex::new(()),
        }
    }

    pub fn jar(&self) -> Arc<Jar> {
        self.jar.clone()
    }

    /// Create (if missing) and return the hidden Steam webview. Idempotent.
    fn ensure_window(&self) -> Result<(), tauri::Error> {
        if self.app.get_webview_window(LABEL).is_some() {
            return Ok(());
        }
        let url = WebviewUrl::External(STEAM_LOGIN_URL.parse().expect("valid url"));
        WebviewWindowBuilder::new(&self.app, LABEL, url)
            .title("Steam")
            .data_directory(self.data_dir.clone())
            .visible(false)
            .decorations(true)
            .skip_taskbar(true)
            .inner_size(1000.0, 720.0)
            .resizable(true)
            .build()?;
        Ok(())
    }

    /// Show the webview window so the user can interact with Steam's login
    /// form. Cookies are persisted to disk automatically by WebView2.
    pub async fn show_login(&self) -> Result<(), tauri::Error> {
        let _g = self.lock.lock().await;
        self.ensure_window()?;
        if let Some(w) = self.app.get_webview_window(LABEL) {
            let _ = w.set_skip_taskbar(false);
            w.eval(format!("window.location.href = {:?}", STEAM_LOGIN_URL))?;
            w.show()?;
            w.set_focus()?;
        }
        Ok(())
    }

    pub async fn hide(&self) -> Result<(), tauri::Error> {
        if let Some(w) = self.app.get_webview_window(LABEL) {
            w.hide()?;
        }
        Ok(())
    }

    /// Pull all `steamcommunity.com` cookies from the webview and load them
    /// into our reqwest jar. Also writes them to `cookies.json` so that they
    /// survive across restarts (Python-style persistence).
    pub async fn sync_cookies(&self) -> Result<usize, String> {
        let _g = self.lock.lock().await;
        self.ensure_window().map_err(|e| e.to_string())?;
        let Some(w) = self.app.get_webview_window(LABEL) else {
            return Ok(0);
        };
        let cookies = w.cookies().map_err(|e| e.to_string())?;
        let steam_com = "https://steamcommunity.com"
            .parse::<url::Url>()
            .map_err(|e| e.to_string())?;
        let steam_pow = "https://store.steampowered.com"
            .parse::<url::Url>()
            .map_err(|e| e.to_string())?;
        let mut n = 0;
        let mut persisted: Vec<(String, String, String, String)> = Vec::new();
        for c in cookies {
            let domain = c.domain().unwrap_or("steamcommunity.com").to_string();
            if !(domain.ends_with("steamcommunity.com") || domain.ends_with("steampowered.com")) {
                continue;
            }
            let path = c.path().unwrap_or("/").to_string();
            let name = c.name().to_string();
            let value = c.value().to_string();
            let header = format!("{}={}; Path={}; Domain={}", name, value, path, domain);
            if let Ok(hv) = header.parse::<HeaderValue>() {
                let values = [hv];
                let target = if domain.ends_with("steampowered.com") {
                    &steam_pow
                } else {
                    &steam_com
                };
                self.jar.set_cookies(&mut values.iter(), target);
                n += 1;
            }
            persisted.push((name, value, domain, path));
        }
        if let Some(persist) = &self.persist {
            (persist)(&persisted);
        } else if !persisted.is_empty() {
            // Fallback: write straight to cookies_file.
            #[derive(serde::Serialize)]
            struct C<'a> {
                name: &'a str,
                value: &'a str,
                domain: &'a str,
                path: &'a str,
            }
            let out: Vec<C> = persisted
                .iter()
                .map(|(n, v, d, p)| C {
                    name: n,
                    value: v,
                    domain: d,
                    path: p,
                })
                .collect();
            if let Ok(json) = serde_json::to_vec_pretty(&out) {
                if let Some(parent) = self.cookies_file.parent() {
                    std::fs::create_dir_all(parent).ok();
                }
                let _ = std::fs::write(&self.cookies_file, json);
            }
        }
        Ok(n)
    }

    /// True if the webview believes it's logged in (i.e. has a
    /// `steamLoginSecure` cookie).
    pub async fn is_logged_in(&self) -> bool {
        let Some(w) = self.app.get_webview_window(LABEL) else {
            return false;
        };
        let Ok(cookies) = w.cookies() else {
            return false;
        };
        cookies
            .iter()
            .any(|c| c.name() == "steamLoginSecure" && !c.value().is_empty())
    }

    /// Drive the hidden webview through Steam's login form using the given
    /// credentials. The window stays invisible throughout. Returns true if
    /// we end up with a `steamLoginSecure` cookie within the timeout.
    pub async fn auto_login(&self, username: &str, password: &str) -> Result<bool, String> {
        let _g = self.lock.lock().await;
        self.ensure_window().map_err(|e| e.to_string())?;

        // Early return if we're already logged in from a previous run.
        if self.is_logged_in_inner() {
            return Ok(true);
        }

        let Some(w) = self.app.get_webview_window(LABEL) else {
            return Ok(false);
        };

        // Navigate to the login page and wait a moment for the SPA to render.
        w.eval(format!("window.location.href = {:?}", STEAM_LOGIN_URL))
            .map_err(|e| e.to_string())?;
        sleep(Duration::from_millis(2500)).await;

        // Fill + submit the login form. Retry a few times: the SPA may render
        // the inputs asynchronously, and the first eval can land before them.
        let script = build_login_script(username, password);
        for _ in 0..6 {
            w.eval(&script).map_err(|e| e.to_string())?;
            sleep(Duration::from_millis(800)).await;
            if self.is_logged_in_inner() {
                break;
            }
        }

        // Poll for the auth cookie to arrive after submit.
        for _ in 0..25 {
            sleep(Duration::from_millis(800)).await;
            if self.is_logged_in_inner() {
                // Navigate to a plain Workshop page so any further state
                // (age-gate, community country) is picked up.
                let _ = w.eval(format!("window.location.href = {:?}", STEAM_HOME_URL));
                sleep(Duration::from_millis(1500)).await;
                return Ok(true);
            }
        }

        Ok(false)
    }

    fn is_logged_in_inner(&self) -> bool {
        let Some(w) = self.app.get_webview_window(LABEL) else {
            return false;
        };
        let Ok(cookies) = w.cookies() else {
            return false;
        };
        cookies
            .iter()
            .any(|c| c.name() == "steamLoginSecure" && !c.value().is_empty())
    }
}

/// Builds a JS snippet that locates the login/password inputs, fills them
/// in via the native `value` setter (so React's onChange handlers fire),
/// and submits the form. This is a near-direct port of
/// `infrastructure/steam/workshop_scripts.py::login_form_fill_script`.
fn build_login_script(username: &str, password: &str) -> String {
    let user = escape_js_string(username);
    let pass = escape_js_string(password);
    format!(
        r#"
        (function() {{
            try {{
                var login = document.querySelector('input[type="text"]');
                var pass = document.querySelector('input[type="password"]');
                if (!login || !pass) return {{ready:false}};
                function fill(el, v) {{
                    el.focus();
                    var s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                    s.call(el, v);
                    el.dispatchEvent(new Event('input', {{bubbles:true}}));
                    el.dispatchEvent(new Event('change', {{bubbles:true}}));
                }}
                fill(login, "{user}");
                fill(pass, "{pass}");
                var btn = document.querySelector('button[type="submit"]');
                if (!btn) {{
                    var btns = document.querySelectorAll('button');
                    for (var i = 0; i < btns.length; i++) {{
                        if ((btns[i].innerText || '').toLowerCase().indexOf('sign in') >= 0) {{
                            btn = btns[i];
                            break;
                        }}
                    }}
                }}
                if (btn) {{
                    btn.disabled = false;
                    btn.click();
                    return {{ready:true, clicked:true}};
                }}
                return {{ready:true, clicked:false}};
            }} catch (e) {{
                return {{error: String(e)}};
            }}
        }})();
        "#
    )
}

fn escape_js_string(s: &str) -> String {
    s.replace('\\', "\\\\")
        .replace('"', "\\\"")
        .replace('\n', "\\n")
        .replace('\r', "\\r")
}
