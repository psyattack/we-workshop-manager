//! Download orchestration. Spawns `DepotDownloaderMod.exe` per task, streams
//! stdout/stderr, emits `download://status` events to the frontend, and
//! supports cancellation. Replicates Python `download_service.py` behaviour.

use std::collections::HashMap;
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;

use once_cell::sync::Lazy;
use parking_lot::Mutex;
use regex::Regex;
use serde::Serialize;
use tauri::{AppHandle, Emitter};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::{Child, Command};
use tokio::sync::Mutex as AsyncMutex;

static PROGRESS_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(\d{1,3}(?:[.,]\d+)?)\s*%").expect("progress regex")
});

use crate::accounts::AccountCredentials;
use crate::constants::STEAM_APP_ID;

#[derive(Debug, Clone, Serialize)]
pub struct TaskStatus {
    pub pubfileid: String,
    pub status: String,
    pub account: String,
    pub phase: Phase,
    pub progress: Option<f32>,
}

#[derive(Debug, Clone, Copy, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Phase {
    Starting,
    Running,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Debug, Clone, Serialize)]
pub struct DownloadCompleted {
    pub pubfileid: String,
    pub success: bool,
}

type ChildHandle = Arc<AsyncMutex<Option<Child>>>;
type HandleMap = HashMap<String, ChildHandle>;

pub struct DownloadManager {
    app: AppHandle,
    tasks: Arc<Mutex<HashMap<String, TaskStatus>>>,
    handles: Arc<Mutex<HandleMap>>,
}

impl DownloadManager {
    pub fn new(app: AppHandle) -> Self {
        Self {
            app,
            tasks: Arc::new(Mutex::new(HashMap::new())),
            handles: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn list(&self) -> Vec<TaskStatus> {
        self.tasks.lock().values().cloned().collect()
    }

    pub async fn start(
        &self,
        pubfileid: &str,
        credentials: AccountCredentials,
        we_directory: PathBuf,
        plugin_path: PathBuf,
    ) -> anyhow::Result<()> {
        if self.tasks.lock().contains_key(pubfileid) {
            return Ok(());
        }

        let output_dir = we_directory
            .join("projects")
            .join("myprojects")
            .join(pubfileid);
        let login_id: u32 = rand::random();

        let status = TaskStatus {
            pubfileid: pubfileid.into(),
            status: "Starting…".into(),
            account: credentials.username.clone(),
            phase: Phase::Starting,
            progress: None,
        };
        self.tasks.lock().insert(pubfileid.into(), status.clone());
        self.emit_status(&status);

        let mut cmd = Command::new(plugin_path);
        cmd.args([
            "-app",
            STEAM_APP_ID,
            "-pubfile",
            pubfileid,
            "-verify-all",
            "-username",
            &credentials.username,
            "-password",
            &credentials.password,
            "-loginid",
            &login_id.to_string(),
            "-max-downloads",
            "32",
            "-dir",
        ])
        .arg(&output_dir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true);

        #[cfg(windows)]
        {
            const CREATE_NO_WINDOW: u32 = 0x0800_0000;
            cmd.creation_flags(CREATE_NO_WINDOW);
        }

        let mut child = cmd.spawn()?;
        let stdout = child.stdout.take();
        let stderr = child.stderr.take();

        let child_holder = Arc::new(AsyncMutex::new(Some(child)));
        self.handles
            .lock()
            .insert(pubfileid.into(), child_holder.clone());

        let tasks = self.tasks.clone();
        let handles = self.handles.clone();
        let app = self.app.clone();
        let pubfileid_owned = pubfileid.to_string();
        let username = credentials.username.clone();
        let output_dir_string = output_dir.to_string_lossy().to_string();

        tokio::spawn(async move {
            let pubfileid = pubfileid_owned;

            if let Some(stdout) = stdout {
                let mut reader = BufReader::new(stdout).lines();
                while let Ok(Some(line)) = reader.next_line().await {
                    let trimmed = line.trim();
                    if trimmed.is_empty() {
                        continue;
                    }
                    let cleaned = trimmed
                        .replace(&format!("{}\\", output_dir_string), ": ")
                        .replace(&format!("{}/", output_dir_string), ": ");
                    let progress = PROGRESS_RE
                        .captures(&cleaned)
                        .and_then(|c| c.get(1))
                        .and_then(|m| m.as_str().replace(',', ".").parse::<f32>().ok())
                        .map(|p| p.clamp(0.0, 100.0));
                    let status = TaskStatus {
                        pubfileid: pubfileid.clone(),
                        status: cleaned,
                        account: username.clone(),
                        phase: Phase::Running,
                        progress,
                    };
                    tasks.lock().insert(pubfileid.clone(), status.clone());
                    app.emit("download://status", &status).ok();
                }
            }

            let mut stderr_tail: Vec<String> = Vec::new();
            if let Some(stderr) = stderr {
                let mut reader = BufReader::new(stderr).lines();
                while let Ok(Some(line)) = reader.next_line().await {
                    log::warn!("[DepotDownloader] {line}");
                    if stderr_tail.len() >= 10 {
                        stderr_tail.remove(0);
                    }
                    stderr_tail.push(line);
                }
            }

            let holder = handles.lock().remove(&pubfileid);
            let mut exit_ok = false;
            if let Some(holder) = holder {
                let mut guard = holder.lock().await;
                if let Some(child) = guard.as_mut() {
                    if let Ok(status) = child.wait().await {
                        exit_ok = status.success();
                    }
                }
            }

            // Trust disk state over the exit code: DepotDownloaderMod sometimes
            // exits with a non-zero code while still successfully writing the
            // requested files, and vice-versa. The canonical check used by the
            // Python app is "did the target folder get populated with at least
            // one .pkg or project.json file" — we mirror that here.
            let output_dir = std::path::Path::new(&output_dir_string);
            let has_output = dir_has_files(output_dir);
            let success = exit_ok || has_output;

            let phase = if success { Phase::Completed } else { Phase::Failed };
            let status_text = if success {
                "Completed".to_string()
            } else if !stderr_tail.is_empty() {
                format!("Failed: {}", stderr_tail.join(" | "))
            } else {
                "Failed".to_string()
            };
            let final_status = TaskStatus {
                pubfileid: pubfileid.clone(),
                status: status_text,
                account: username,
                phase,
                progress: if success { Some(100.0) } else { None },
            };
            app.emit("download://status", &final_status).ok();
            app.emit(
                "download://completed",
                DownloadCompleted {
                    pubfileid: pubfileid.clone(),
                    success,
                },
            )
            .ok();
            tasks.lock().remove(&pubfileid);
        });

        Ok(())
    }

    pub async fn cancel(&self, pubfileid: &str, we_directory: &std::path::Path) -> bool {
        let holder = self.handles.lock().remove(pubfileid);
        if let Some(holder) = holder {
            let mut guard = holder.lock().await;
            if let Some(child) = guard.as_mut() {
                let _ = child.kill().await;
            }
        }

        let folder = we_directory
            .join("projects")
            .join("myprojects")
            .join(pubfileid);
        if folder.exists() {
            let _ = std::fs::remove_dir_all(&folder);
        }

        let removed = self.tasks.lock().remove(pubfileid).is_some();
        if removed {
            let status = TaskStatus {
                pubfileid: pubfileid.into(),
                status: "Cancelled".into(),
                account: String::new(),
                phase: Phase::Cancelled,
                progress: None,
            };
            self.app.emit("download://status", status).ok();
            self.app
                .emit(
                    "download://completed",
                    DownloadCompleted {
                        pubfileid: pubfileid.into(),
                        success: false,
                    },
                )
                .ok();
        }
        removed
    }

    fn emit_status(&self, status: &TaskStatus) {
        self.app.emit("download://status", status).ok();
    }
}

/// Returns true if the directory exists and contains at least one regular
/// file. Used to detect "the plugin actually produced output" even when the
/// exit code is misleading.
fn dir_has_files(dir: &std::path::Path) -> bool {
    let Ok(read) = std::fs::read_dir(dir) else {
        return false;
    };
    for entry in read.flatten() {
        if entry.file_type().map(|t| t.is_file()).unwrap_or(false) {
            return true;
        }
        if entry.file_type().map(|t| t.is_dir()).unwrap_or(false)
            && dir_has_files(&entry.path())
        {
            return true;
        }
    }
    false
}
