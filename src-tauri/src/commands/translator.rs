use tauri::command;

use crate::commands::map_err;
use crate::translator::translate_text;

#[command]
pub async fn translator_translate(
    text: String,
    source_lang: String,
    target_lang: String,
) -> Result<String, String> {
    translate_text(&text, &source_lang, &target_lang)
        .await
        .map_err(map_err)
}
