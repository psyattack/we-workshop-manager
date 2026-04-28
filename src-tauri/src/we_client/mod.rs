//! Wallpaper Engine client. Full port of the Python
//! `wallpaper_engine_client.py`: detection, project enumeration, current
//! wallpaper lookup and the `-control openWallpaper / applyProperties`
//! command surface.

use std::path::{Path, PathBuf};
use std::process::Command;

use serde::{Deserialize, Serialize};
use sysinfo::System;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstalledWallpaper {
    pub pubfileid: String,
    pub folder: String,
    pub project_json_path: String,
    pub has_pkg: bool,
    pub title: String,
    pub preview: String,
    pub description: String,
    pub file_type: String,
    pub tags: Vec<String>,
    pub size_bytes: u64,
    pub installed_ts: i64,
}

pub struct WallpaperEngineClient {
    pub directory: Option<PathBuf>,
}

impl WallpaperEngineClient {
    pub fn new(directory: Option<PathBuf>) -> Self {
        Self { directory }
    }

    pub fn set_directory(&mut self, directory: Option<PathBuf>) {
        self.directory = directory;
    }

    pub fn config_path(&self) -> Option<PathBuf> {
        self.directory.as_ref().map(|d| d.join("config.json"))
    }

    pub fn projects_path(&self) -> Option<PathBuf> {
        self.directory
            .as_ref()
            .map(|d| d.join("projects").join("myprojects"))
    }

    /// Best-effort detection of the Wallpaper Engine install. We look in,
    /// in order:
    ///   1. The legacy hard-coded `Program Files / Program Files (x86) /
    ///      Wallpaper Engine` paths (matches the original Python).
    ///   2. The default Steam install (`Steam/steamapps/common/wallpaper_engine`).
    ///   3. Every Steam library listed in `Steam/steamapps/libraryfolders.vdf` —
    ///      this is the common case because most users install Wallpaper
    ///      Engine on a separate drive (`D:\SteamLibrary`, etc.).
    ///   4. Currently running `wallpaper64.exe / wallpaper32.exe` processes.
    pub fn detect_installation() -> Option<PathBuf> {
        let mut candidates: Vec<PathBuf> = Vec::new();
        candidates.push(PathBuf::from(r"C:\Program Files (x86)\Wallpaper Engine"));
        candidates.push(PathBuf::from(r"C:\Program Files\Wallpaper Engine"));
        if let Ok(p) = std::env::var("ProgramFiles") {
            candidates.push(PathBuf::from(p).join("Wallpaper Engine"));
        }
        if let Ok(p) = std::env::var("ProgramFiles(x86)") {
            candidates.push(PathBuf::from(p).join("Wallpaper Engine"));
        }

        // Resolve every Steam library and add the `wallpaper_engine` install
        // folder under it.
        for steam_root in steam_install_dirs() {
            candidates.push(
                steam_root
                    .join("steamapps")
                    .join("common")
                    .join("wallpaper_engine"),
            );
            for lib in steam_library_folders(&steam_root) {
                candidates.push(lib.join("steamapps").join("common").join("wallpaper_engine"));
            }
        }

        let mut seen = std::collections::HashSet::new();
        for candidate in &candidates {
            let key = candidate.to_string_lossy().to_lowercase();
            if !seen.insert(key) {
                continue;
            }
            if candidate.exists()
                && (candidate.join("wallpaper64.exe").exists()
                    || candidate.join("wallpaper32.exe").exists())
            {
                return Some(candidate.clone());
            }
        }

        let mut system = System::new();
        system.refresh_processes(sysinfo::ProcessesToUpdate::All, true);
        for process in system.processes().values() {
            let name = process.name().to_string_lossy().to_lowercase();
            if name == "wallpaper64.exe" || name == "wallpaper32.exe" {
                if let Some(exe) = process.exe() {
                    if let Some(parent) = exe.parent() {
                        if parent.join("projects").exists() {
                            return Some(parent.to_path_buf());
                        }
                    }
                }
            }
        }

        None
    }

    pub fn executable(&self) -> Option<PathBuf> {
        let dir = self.directory.as_ref()?;
        let win64 = dir.join("wallpaper64.exe");
        if win64.exists() {
            return Some(win64);
        }
        let win32 = dir.join("wallpaper32.exe");
        if win32.exists() {
            return Some(win32);
        }
        None
    }

    pub fn is_installed(&self, pubfileid: &str) -> bool {
        self.projects_path()
            .map(|p| p.join(pubfileid).exists())
            .unwrap_or(false)
    }

    pub fn installed_wallpapers(&self) -> Vec<InstalledWallpaper> {
        let Some(projects) = self.projects_path() else {
            return Vec::new();
        };
        if !projects.exists() {
            return Vec::new();
        }

        let mut out = Vec::new();
        if let Ok(entries) = std::fs::read_dir(projects) {
            for entry in entries.flatten() {
                let folder = entry.path();
                if !folder.is_dir() {
                    continue;
                }
                let pubfileid = folder
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or_default()
                    .to_string();
                if pubfileid.is_empty() {
                    continue;
                }
                let wallpaper = parse_project(&folder, &pubfileid);
                out.push(wallpaper);
            }
        }
        out
    }

    pub fn current_wallpaper_pubfileid(&self, monitor: u32) -> Option<String> {
        let config_path = self.config_path()?;
        let raw = std::fs::read_to_string(&config_path).ok()?;
        let value: serde_json::Value = serde_json::from_str(&raw).ok()?;
        let selected = value
            .pointer(&format!(
                "/Main/general/wallpaperconfig/selectedwallpapers/Monitor{monitor}/file"
            ))?
            .as_str()?
            .to_string();
        Path::new(&selected)
            .parent()
            .and_then(|p| p.file_name())
            .map(|n| n.to_string_lossy().to_string())
    }

    /// Enumerate every pubfileid currently attached to a monitor (Monitor0,
    /// Monitor1, …). Used to refuse deleting a wallpaper that Wallpaper
    /// Engine is still displaying right now.
    pub fn active_pubfileids(&self) -> Vec<String> {
        let Some(config_path) = self.config_path() else {
            return Vec::new();
        };
        let Ok(raw) = std::fs::read_to_string(&config_path) else {
            return Vec::new();
        };
        let Ok(value) = serde_json::from_str::<serde_json::Value>(&raw) else {
            return Vec::new();
        };
        let Some(selected) = value
            .pointer("/Main/general/wallpaperconfig/selectedwallpapers")
            .and_then(|v| v.as_object())
        else {
            return Vec::new();
        };
        let mut out = Vec::new();
        for (_monitor, entry) in selected {
            let Some(file) = entry.get("file").and_then(|f| f.as_str()) else {
                continue;
            };
            if let Some(id) = Path::new(file)
                .parent()
                .and_then(|p| p.file_name())
                .map(|n| n.to_string_lossy().to_string())
            {
                if !out.contains(&id) {
                    out.push(id);
                }
            }
        }
        out
    }

    pub fn apply(
        &self,
        project_path: &Path,
        monitor: Option<u32>,
        force: bool,
    ) -> anyhow::Result<()> {
        let executable = self
            .executable()
            .ok_or_else(|| anyhow::anyhow!("Wallpaper Engine executable not found"))?;

        let (folder, json_path) = if project_path.is_dir() {
            (project_path.to_path_buf(), project_path.join("project.json"))
        } else {
            (
                project_path
                    .parent()
                    .map(|p| p.to_path_buf())
                    .unwrap_or_default(),
                project_path.to_path_buf(),
            )
        };

        if !force {
            if let Some(name) = folder.file_name().and_then(|n| n.to_str()) {
                if self.current_wallpaper_pubfileid(monitor.unwrap_or(0)).as_deref() == Some(name) {
                    return Ok(());
                }
            }
        }

        let mut cmd = Command::new(executable);
        cmd.arg("-control")
            .arg("openWallpaper")
            .arg("-file")
            .arg(json_path.canonicalize().unwrap_or(json_path));
        if let Some(m) = monitor {
            cmd.arg("-monitor").arg(m.to_string());
        }
        spawn_detached(cmd)?;
        Ok(())
    }

    pub fn open_wallpaper_engine(&self, show_window: bool) -> anyhow::Result<()> {
        let executable = self
            .executable()
            .ok_or_else(|| anyhow::anyhow!("Wallpaper Engine executable not found"))?;

        let name = executable
            .file_name()
            .and_then(|n| n.to_str())
            .map(|s| s.to_ascii_lowercase())
            .unwrap_or_default();

        let mut system = System::new();
        system.refresh_processes(sysinfo::ProcessesToUpdate::All, true);
        let is_running = system
            .processes()
            .iter()
            .any(|(_, p)| p.name().to_string_lossy().to_ascii_lowercase() == name);

        let mut cmd = Command::new(executable);
        if is_running && show_window {
            cmd.arg("-showwindow");
        }

        if !is_running || show_window {
            spawn_detached(cmd)?;
        }
        Ok(())
    }
}

fn parse_project(folder: &Path, pubfileid: &str) -> InstalledWallpaper {
    let project_json_path = folder.join("project.json");
    let mut title = pubfileid.to_string();
    let mut preview = String::new();
    let mut description = String::new();
    let mut file_type = String::new();
    let mut tags: Vec<String> = Vec::new();

    if let Ok(raw) = std::fs::read_to_string(&project_json_path) {
        if let Ok(value) = serde_json::from_str::<serde_json::Value>(&raw) {
            if let Some(s) = value.get("title").and_then(|v| v.as_str()) {
                title = s.to_string();
            }
            if let Some(s) = value.get("preview").and_then(|v| v.as_str()) {
                preview = folder.join(s).to_string_lossy().to_string();
            }
            if let Some(s) = value.get("description").and_then(|v| v.as_str()) {
                description = s.to_string();
            }
            if let Some(s) = value.get("type").and_then(|v| v.as_str()) {
                file_type = s.to_string();
            }
            if let Some(arr) = value.get("tags").and_then(|v| v.as_array()) {
                tags = arr
                    .iter()
                    .filter_map(|v| v.as_str().map(ToString::to_string))
                    .collect();
            }
        }
    }

    let mut size_bytes: u64 = 0;
    walk_size(folder, &mut size_bytes);

    let installed_ts = std::fs::metadata(folder)
        .and_then(|m| m.modified())
        .ok()
        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
        .map(|d| d.as_secs() as i64)
        .unwrap_or_default();

    let has_pkg = std::fs::read_dir(folder)
        .map(|iter| {
            iter.flatten().any(|e| {
                e.path()
                    .extension()
                    .and_then(|s| s.to_str())
                    .map(|s| s.eq_ignore_ascii_case("pkg"))
                    .unwrap_or(false)
            })
        })
        .unwrap_or(false);

    InstalledWallpaper {
        pubfileid: pubfileid.into(),
        folder: folder.to_string_lossy().to_string(),
        project_json_path: project_json_path.to_string_lossy().to_string(),
        has_pkg,
        title,
        preview,
        description,
        file_type,
        tags,
        size_bytes,
        installed_ts,
    }
}

/// Locate every Steam install on the machine. We look at default
/// directories first, then on Windows we read the `Software\Valve\Steam`
/// registry key.
fn steam_install_dirs() -> Vec<PathBuf> {
    let mut out: Vec<PathBuf> = Vec::new();
    let push_if_exists = |out: &mut Vec<PathBuf>, p: PathBuf| {
        if p.join("steamapps").exists() || p.join("Steam.exe").exists() {
            out.push(p);
        }
    };

    push_if_exists(&mut out, PathBuf::from(r"C:\Program Files (x86)\Steam"));
    push_if_exists(&mut out, PathBuf::from(r"C:\Program Files\Steam"));
    if let Ok(p) = std::env::var("ProgramFiles(x86)") {
        push_if_exists(&mut out, PathBuf::from(p).join("Steam"));
    }
    if let Ok(p) = std::env::var("ProgramFiles") {
        push_if_exists(&mut out, PathBuf::from(p).join("Steam"));
    }

    #[cfg(target_os = "windows")]
    {
        if let Some(p) = read_steam_install_path_from_registry() {
            push_if_exists(&mut out, p);
        }
    }

    out
}

#[cfg(target_os = "windows")]
fn read_steam_install_path_from_registry() -> Option<PathBuf> {
    // Avoid an extra `winreg` dep — shell out to `reg query`. Output is
    // a few lines like:
    //     HKEY_CURRENT_USER\Software\Valve\Steam
    //         SteamPath    REG_SZ    C:\Program Files (x86)\Steam
    let try_query = |hive: &str| -> Option<PathBuf> {
        let out = std::process::Command::new("reg")
            .args(["query", hive, "/v", "SteamPath"])
            .output()
            .ok()?;
        if !out.status.success() {
            return None;
        }
        let text = String::from_utf8_lossy(&out.stdout);
        for line in text.lines() {
            let line = line.trim();
            if let Some(rest) = line.strip_prefix("SteamPath") {
                let rest = rest.trim_start();
                if let Some(rest) = rest.strip_prefix("REG_SZ") {
                    let p = rest.trim();
                    if !p.is_empty() {
                        return Some(PathBuf::from(p.replace('/', "\\")));
                    }
                }
            }
        }
        None
    };
    try_query(r"HKCU\Software\Valve\Steam")
        .or_else(|| try_query(r"HKLM\SOFTWARE\WOW6432Node\Valve\Steam"))
        .or_else(|| try_query(r"HKLM\SOFTWARE\Valve\Steam"))
}



/// Parse `<steam>/steamapps/libraryfolders.vdf`. Returns every library
/// path Steam knows about (the file is a Valve KeyValues format —
/// quoted-string pairs we can extract with a regex).
fn steam_library_folders(steam_root: &Path) -> Vec<PathBuf> {
    let vdf = steam_root.join("steamapps").join("libraryfolders.vdf");
    let Ok(text) = std::fs::read_to_string(&vdf) else {
        return Vec::new();
    };
    let re = regex::Regex::new(r#""path"\s*"([^"]+)""#).unwrap();
    let mut out = Vec::new();
    for cap in re.captures_iter(&text) {
        // Steam writes `\\` for backslashes — collapse them.
        let path = cap[1].replace(r"\\", r"\");
        out.push(PathBuf::from(path));
    }
    out
}

fn walk_size(path: &Path, total: &mut u64) {
    if let Ok(entries) = std::fs::read_dir(path) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_dir() {
                walk_size(&p, total);
            } else if let Ok(meta) = entry.metadata() {
                *total = total.saturating_add(meta.len());
            }
        }
    }
}

#[cfg(windows)]
fn spawn_detached(mut cmd: Command) -> anyhow::Result<()> {
    use std::os::windows::process::CommandExt;
    const CREATE_NO_WINDOW: u32 = 0x0800_0000;
    cmd.creation_flags(CREATE_NO_WINDOW).spawn()?;
    Ok(())
}

#[cfg(not(windows))]
fn spawn_detached(mut cmd: Command) -> anyhow::Result<()> {
    cmd.spawn()?;
    Ok(())
}

pub fn delete_wallpaper_folder(projects_path: &Path, pubfileid: &str) -> anyhow::Result<()> {
    let target = projects_path.join(pubfileid);
    if target.exists() {
        std::fs::remove_dir_all(target)?;
    }
    Ok(())
}
