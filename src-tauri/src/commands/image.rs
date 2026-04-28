use std::path::PathBuf;

use tauri::command;

use crate::commands::map_err;

#[command]
pub fn open_path(path: String) -> Result<(), String> {
    let p = PathBuf::from(&path);
    if !p.exists() {
        return Err("path does not exist".into());
    }
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer").arg(&p).spawn().map_err(map_err)?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open").arg(&p).spawn().map_err(map_err)?;
    }
    #[cfg(all(unix, not(target_os = "macos")))]
    {
        std::process::Command::new("xdg-open").arg(&p).spawn().map_err(map_err)?;
    }
    Ok(())
}
