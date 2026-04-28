//! Extraction orchestration — spawns `RePKG.exe` for any wallpaper package.

use std::collections::HashMap;
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;

use parking_lot::Mutex;
use serde::Serialize;
use tauri::{AppHandle, Emitter};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;

use crate::download::{Phase, TaskStatus};

#[derive(Debug, Clone, Serialize)]
pub struct ExtractCompleted {
    pub pubfileid: String,
    pub success: bool,
    pub output_dir: String,
}

pub struct ExtractManager {
    app: AppHandle,
    tasks: Arc<Mutex<HashMap<String, TaskStatus>>>,
}

impl ExtractManager {
    pub fn new(app: AppHandle) -> Self {
        Self {
            app,
            tasks: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn list(&self) -> Vec<TaskStatus> {
        self.tasks.lock().values().cloned().collect()
    }

    pub async fn start(
        &self,
        pubfileid: &str,
        we_directory: PathBuf,
        output_dir: PathBuf,
        repkg_path: PathBuf,
    ) -> anyhow::Result<()> {
        let source = we_directory
            .join("projects")
            .join("myprojects")
            .join(pubfileid);
        if !source.exists() {
            anyhow::bail!("source folder does not exist");
        }

        let pkg_file = std::fs::read_dir(&source)?
            .flatten()
            .find(|entry| {
                entry
                    .path()
                    .extension()
                    .and_then(|s| s.to_str())
                    .map(|s| s.eq_ignore_ascii_case("pkg"))
                    .unwrap_or(false)
            })
            .map(|entry| entry.path());

        let Some(pkg_file) = pkg_file else {
            anyhow::bail!("no .pkg file found");
        };

        if !repkg_path.exists() {
            anyhow::bail!("RePKG.exe not found at {}", repkg_path.display());
        }

        let extract_folder = output_dir.join(pubfileid);

        if self.tasks.lock().contains_key(pubfileid) {
            return Ok(());
        }

        let status = TaskStatus {
            pubfileid: pubfileid.into(),
            status: "Starting…".into(),
            account: String::new(),
            phase: Phase::Starting,
            progress: None,
        };
        self.tasks.lock().insert(pubfileid.into(), status.clone());
        self.app.emit("extract://status", &status).ok();

        let mut cmd = Command::new(repkg_path);
        cmd.arg("extract")
            .arg("-c")
            .arg("-n")
            .arg("-o")
            .arg(&extract_folder)
            .arg(&pkg_file)
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

        let tasks = self.tasks.clone();
        let app = self.app.clone();
        let pubfileid_owned = pubfileid.to_string();
        let output_dir_str = extract_folder.to_string_lossy().to_string();

        tokio::spawn(async move {
            let pubfileid = pubfileid_owned;
            if let Some(stdout) = stdout {
                let mut reader = BufReader::new(stdout).lines();
                while let Ok(Some(line)) = reader.next_line().await {
                    let trimmed = line.trim();
                    if trimmed.is_empty() {
                        continue;
                    }
                    let status = TaskStatus {
                        pubfileid: pubfileid.clone(),
                        status: trimmed.to_string(),
                        account: String::new(),
                        phase: Phase::Running,
                        progress: None,
                    };
                    tasks.lock().insert(pubfileid.clone(), status.clone());
                    app.emit("extract://status", &status).ok();
                }
            }

            let mut stderr_tail: Vec<String> = Vec::new();
            if let Some(stderr) = stderr {
                let mut reader = BufReader::new(stderr).lines();
                while let Ok(Some(line)) = reader.next_line().await {
                    log::warn!("[RePKG] {line}");
                    if stderr_tail.len() >= 10 {
                        stderr_tail.remove(0);
                    }
                    stderr_tail.push(line);
                }
            }

            let exit_ok = child
                .wait()
                .await
                .map(|s| s.success())
                .unwrap_or(false);

            // Same defensive check as the download manager: if the plugin
            // wrote the output folder we treat it as success even if it
            // returned a non-zero exit code (RePKG is noisy on stderr but
            // still produces valid output).
            let output_dir = std::path::Path::new(&output_dir_str);
            let has_output = dir_has_files(output_dir);
            let success = exit_ok || has_output;

            let status_text = if success {
                "Completed".to_string()
            } else if !stderr_tail.is_empty() {
                format!("Failed: {}", stderr_tail.join(" | "))
            } else {
                "Failed".to_string()
            };
            let status = TaskStatus {
                pubfileid: pubfileid.clone(),
                status: status_text,
                account: String::new(),
                phase: if success { Phase::Completed } else { Phase::Failed },
                progress: if success { Some(100.0) } else { None },
            };
            app.emit("extract://status", &status).ok();
            app.emit(
                "extract://completed",
                ExtractCompleted {
                    pubfileid: pubfileid.clone(),
                    success,
                    output_dir: output_dir_str,
                },
            )
            .ok();
            tasks.lock().remove(&pubfileid);
        });

        Ok(())
    }
}

/// Recursively returns true if the directory contains at least one regular
/// file. Mirrors the helper used by the download manager.
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
