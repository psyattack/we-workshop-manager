//! Resolve where the DepotDownloaderMod / RePKG executables live on disk.
//!
//! The Python app shipped the two plugin folders right next to the Python
//! sources (`plugins/DepotDownloaderMod/` and `plugins/RePKG/`). We keep the
//! same convention, but the Tauri build places the compiled executable
//! either next to the app binary (production bundle) or deep inside
//! `src-tauri/target/<profile>/` during `tauri dev`. We therefore try a
//! handful of reasonable candidates before giving up.

use std::path::{Path, PathBuf};

fn candidate_roots() -> Vec<PathBuf> {
    let mut out = Vec::new();

    if let Ok(exe) = std::env::current_exe() {
        let mut cur = exe.as_path();
        // Walk up at most 6 levels looking for a `plugins/` sibling — this
        // covers production (exe next to plugins) as well as
        // `src-tauri/target/debug/<bin>` during `tauri dev`.
        for _ in 0..6 {
            if let Some(parent) = cur.parent() {
                out.push(parent.to_path_buf());
                cur = parent;
            } else {
                break;
            }
        }
    }

    if let Ok(cwd) = std::env::current_dir() {
        out.push(cwd.clone());
        if let Some(p) = cwd.parent() {
            out.push(p.to_path_buf());
        }
    }

    if let Ok(manifest_dir) = std::env::var("CARGO_MANIFEST_DIR") {
        let manifest_dir = PathBuf::from(manifest_dir);
        if let Some(parent) = manifest_dir.parent() {
            out.push(parent.to_path_buf());
        }
        out.push(manifest_dir);
    }

    out
}

fn find_plugin_binary(plugin_folder: &str, binary_name: &str) -> Option<PathBuf> {
    for root in candidate_roots() {
        let candidate = root
            .join("plugins")
            .join(plugin_folder)
            .join(binary_name);
        if candidate.is_file() {
            return Some(candidate);
        }
    }
    None
}

pub fn depot_downloader() -> Result<PathBuf, String> {
    let name = if cfg!(windows) {
        "DepotDownloaderMod.exe"
    } else {
        "DepotDownloaderMod"
    };
    find_plugin_binary("DepotDownloaderMod", name).ok_or_else(|| {
        format!(
            "DepotDownloaderMod not found. Place the plugin at `plugins/DepotDownloaderMod/{name}` next to the app or in the repository root."
        )
    })
}

pub fn repkg() -> Result<PathBuf, String> {
    let name = if cfg!(windows) { "RePKG.exe" } else { "RePKG" };
    find_plugin_binary("RePKG", name).ok_or_else(|| {
        format!(
            "RePKG not found. Place the plugin at `plugins/RePKG/{name}` next to the app or in the repository root."
        )
    })
}

#[allow(dead_code)]
pub fn exists(path: &Path) -> bool {
    path.is_file()
}
