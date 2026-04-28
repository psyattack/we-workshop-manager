//! GitHub release update checker. Equivalent of the Python
//! `update_service.py`: fetches the latest GitHub release of the upstream
//! repo and compares the version with the currently running one.

use serde::{Deserialize, Serialize};

use crate::constants::{APP_VERSION, UPDATE_REPO_NAME, UPDATE_REPO_OWNER};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct UpdateInfo {
    pub current_version: String,
    pub latest_version: String,
    pub update_available: bool,
    pub release_notes: String,
    pub html_url: String,
    pub error: Option<String>,
}

pub async fn check_for_updates() -> UpdateInfo {
    let url = format!(
        "https://api.github.com/repos/{}/{}/releases/latest",
        UPDATE_REPO_OWNER, UPDATE_REPO_NAME
    );

    let client = match reqwest::Client::builder()
        .user_agent(format!("WEave/{}", APP_VERSION))
        .timeout(std::time::Duration::from_secs(10))
        .build()
    {
        Ok(c) => c,
        Err(e) => {
            return UpdateInfo {
                current_version: APP_VERSION.into(),
                error: Some(e.to_string()),
                ..Default::default()
            }
        }
    };

    let res = match client.get(url).send().await {
        Ok(r) => r,
        Err(e) => {
            return UpdateInfo {
                current_version: APP_VERSION.into(),
                error: Some(e.to_string()),
                ..Default::default()
            }
        }
    };

    let json: serde_json::Value = match res.json().await {
        Ok(j) => j,
        Err(e) => {
            return UpdateInfo {
                current_version: APP_VERSION.into(),
                error: Some(e.to_string()),
                ..Default::default()
            }
        }
    };

    let latest_version = json
        .get("tag_name")
        .and_then(|v| v.as_str())
        .unwrap_or_default()
        .trim_start_matches('v')
        .to_string();

    let release_notes = json
        .get("body")
        .and_then(|v| v.as_str())
        .unwrap_or_default()
        .to_string();

    let html_url = json
        .get("html_url")
        .and_then(|v| v.as_str())
        .unwrap_or_default()
        .to_string();

    let update_available =
        !latest_version.is_empty() && version_is_newer(&latest_version, APP_VERSION);

    UpdateInfo {
        current_version: APP_VERSION.into(),
        latest_version,
        update_available,
        release_notes,
        html_url,
        error: None,
    }
}

fn version_is_newer(remote: &str, local: &str) -> bool {
    let parse = |v: &str| -> Vec<u32> {
        v.split('.')
            .filter_map(|p| p.chars().take_while(|c| c.is_ascii_digit()).collect::<String>().parse::<u32>().ok())
            .collect()
    };
    let r = parse(remote);
    let l = parse(local);
    let len = r.len().max(l.len());
    for i in 0..len {
        let ri = r.get(i).copied().unwrap_or(0);
        let li = l.get(i).copied().unwrap_or(0);
        if ri != li {
            return ri > li;
        }
    }
    false
}
