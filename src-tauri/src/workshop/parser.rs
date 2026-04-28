//! HTML parsers for the Steam Workshop. Steam recently redesigned the
//! browse page so the legacy `.workshopItem` markup is gone; items are
//! now in an obfuscated-class grid. We still have stable markers:
//!   - `<a href=".../filedetails/?id=PUBFILEID">` (appears once per tile,
//!     wrapping both the preview image and the title block)
//!   - `<img alt="Title" src="https://images.steamusercontent.com/...">`
//!   - `<a href=".../id/NAME/myworkshopfiles/?appid=431960">By Author</a>`
//!
//! The parser is tolerant: whatever we can't find is simply left blank.

use regex::Regex;
use scraper::{ElementRef, Html, Selector};
use serde_json::{Map, Value};
use std::collections::HashMap;

use crate::workshop::{CollectionContents, CollectionRef, WorkshopItem, WorkshopPage};

pub fn parse_browse(html: &str, current_page: u32) -> WorkshopPage {
    let doc = Html::parse_document(html);

    // Fast path: try SSR data first — Steam embeds the items as a JSON
    // payload in a `<script>` tag. This is what the Python WebView code
    // does in `parseSSRData()`, and it gives us pubfileid/title/preview
    // straight away (without ever depending on obfuscated CSS classes).
    let mut items = parse_browse_ssr(html);

    // The SSR payload doesn't include `author` / `author_url`, so always
    // fall back to the per-tile container parser (`.tmIrUKf-Mh8-, …`).
    // It's also our only recovery if SSR data is missing.
    let mut html_items = parse_browse_html(&doc);
    if html_items.is_empty() && items.is_empty() {
        // Last-ditch fallback: scan loose `a[href*="filedetails"]` links.
        // This is what we used to do unconditionally — keep it as a safety
        // net for unexpected markup changes / synthetic test fixtures.
        html_items = parse_browse_loose(&doc, html);
    }
    if items.is_empty() {
        items = html_items;
    } else {
        // Merge author info from html parsing into SSR items.
        let by_id: HashMap<String, &WorkshopItem> = html_items
            .iter()
            .map(|i| (i.pubfileid.clone(), i))
            .collect();
        for it in &mut items {
            if it.author.is_empty() {
                if let Some(src) = by_id.get(&it.pubfileid) {
                    it.author = src.author.clone();
                    it.author_url = src.author_url.clone();
                    if it.preview_url.is_empty() {
                        it.preview_url = src.preview_url.clone();
                    }
                }
            }
        }
    }

    for it in &mut items {
        if it.preview_url.is_empty() {
            it.is_collection = true;
        }
        if it.title.is_empty() {
            it.title = format!("Wallpaper {}", it.pubfileid);
        }
        if !it.preview_url.is_empty() {
            it.preview_url = upscale_preview(&it.preview_url);
        }
    }

    let (total_pages, total_items) = parse_pagination(html, &items);
    WorkshopPage {
        items,
        current_page,
        total_pages: total_pages.max(1),
        total_items,
    }
}

/// Parse the per-tile containers used by Steam's redesigned Workshop
/// browse page. Mirrors `_build_html_item_parser()` from the original
/// `workshop_scripts.py`:
///
///   `doc.querySelectorAll('.tmIrUKf-Mh8-, .sDK5fonBQMA-, .workshopItem, .workshopItemCollection')`
fn parse_browse_html(doc: &Html) -> Vec<WorkshopItem> {
    let container_sel = Selector::parse(
        ".tmIrUKf-Mh8-, .sDK5fonBQMA-, .workshopItem, .workshopItemCollection, \
         a.workshopItemCollection",
    )
    .unwrap();
    let link_sel = Selector::parse(r#"a[href*="filedetails"]"#).unwrap();
    let title_sel = Selector::parse("._3rvey4VpXts- a, .workshopItemTitle").unwrap();
    let img_sel = Selector::parse("img").unwrap();
    // Author chip selectors. On the Collections browse tiles Steam ships
    // just `<span class="workshopItemAuthorName">NAME</span>` (preceded by
    // a loose "Collection by" text node — no link, no URL). On regular
    // Workshop tiles it's `<div class="workshopItemAuthorName">by&nbsp;<a
    // class="workshop_author_link" href="…">NAME</a></div>`. We try the
    // linked form first so `author_url` is populated when available, then
    // fall back to plain text.
    let author_link_sel = Selector::parse(
        ".CmHGWYJjMk0- a, .workshopItemAuthorName a, \
         a.workshop_author_link, \
         a[href*=\"/myworkshopfiles/\"], a[href*=\"/myworkshopcollections/\"]",
    )
    .unwrap();
    let author_text_sel = Selector::parse(".workshopItemAuthorName").unwrap();
    let author_re = Regex::new(r"(?i)^\s*(?:by|collection\s+by)\s+").unwrap();

    let mut items = Vec::new();
    let mut seen = std::collections::HashSet::new();

    for tile in doc.select(&container_sel) {
        // The tile itself may be the link (collection tiles use
        // `<a class="workshopItemCollection" href="…filedetails?id=…">`).
        let tile_name = tile.value().name();
        let tile_href = if tile_name == "a" {
            tile.value().attr("href")
        } else {
            None
        };
        let href = tile_href
            .or_else(|| {
                tile.select(&link_sel)
                    .next()
                    .and_then(|l| l.value().attr("href"))
            });
        let Some(href) = href else { continue };
        let Some(id) = extract_pubfileid(href) else {
            continue;
        };
        if !seen.insert(id.clone()) {
            continue;
        }

        let mut item = WorkshopItem {
            pubfileid: id,
            ..Default::default()
        };

        // Title — explicit element first, then fall back to the link text /
        // image alt attribute (used when the tile is a collection card).
        if let Some(t) = tile.select(&title_sel).next() {
            item.title = inner_text(t);
        }
        if item.title.is_empty() {
            if let Some(link) = tile.select(&link_sel).next() {
                let lt = inner_text(link);
                if !lt.starts_with("By ") {
                    item.title = lt;
                }
            }
        }
        if item.title.is_empty() {
            if let Some(img) = tile.select(&img_sel).next() {
                if let Some(alt) = img.value().attr("alt") {
                    item.title = alt.trim().to_string();
                }
            }
        }

        // Preview image
        if let Some(img) = tile.select(&img_sel).next() {
            if let Some(src) = img
                .value()
                .attr("src")
                .or_else(|| img.value().attr("data-src"))
            {
                item.preview_url = src.to_string();
            }
        }

        // Author — prefer the anchor form (gets us URL for click-through),
        // fall back to the plain `.workshopItemAuthorName` span for
        // collection tiles where Steam doesn't render a link at all.
        if let Some(a) = tile.select(&author_link_sel).next() {
            let raw = inner_text(a);
            item.author = author_re.replace(&raw, "").trim().to_string();
            item.author_url = a.value().attr("href").unwrap_or("").to_string();
        } else if let Some(span) = tile.select(&author_text_sel).next() {
            let raw = inner_text(span);
            item.author = author_re.replace(&raw, "").trim().to_string();
        }

        items.push(item);
    }

    items
}

/// Loose, marker-based fallback when neither SSR nor container parsing
/// matches anything. Walks every `a[href*="filedetails"]` link, merges
/// duplicates by pubfileid, and pairs nearby `By NAME` author links.
fn parse_browse_loose(doc: &Html, html: &str) -> Vec<WorkshopItem> {
    let link_sel = Selector::parse(r#"a[href*="filedetails/?id="]"#).unwrap();
    let img_sel = Selector::parse("img").unwrap();
    let mut by_id: HashMap<String, WorkshopItem> = HashMap::new();

    for a in doc.select(&link_sel) {
        let Some(href) = a.value().attr("href") else {
            continue;
        };
        let Some(id) = extract_pubfileid(href) else {
            continue;
        };
        let entry = by_id.entry(id.clone()).or_insert_with(|| WorkshopItem {
            pubfileid: id.clone(),
            ..Default::default()
        });
        let txt = inner_text(a);
        if !txt.is_empty() && entry.title.is_empty() && !txt.starts_with("By ") {
            entry.title = txt;
        }
        if entry.preview_url.is_empty() {
            if let Some(img) = a.select(&img_sel).next() {
                if let Some(src) = img
                    .value()
                    .attr("src")
                    .or_else(|| img.value().attr("data-src"))
                {
                    entry.preview_url = src.to_string();
                }
                if entry.title.is_empty() {
                    if let Some(alt) = img.value().attr("alt") {
                        if !alt.is_empty() {
                            entry.title = alt.trim().to_string();
                        }
                    }
                }
            }
        }
    }

    // Pair `By NAME` links with the nearest preceding filedetails link.
    // Collection tiles link to `myworkshopcollections` instead of
    // `myworkshopfiles` so both have to be matched here.
    let author_re = Regex::new(
        r#"<a href="(https://steamcommunity\.com/(?:id|profiles)/[^"]+/(?:myworkshopfiles|myworkshopcollections)/[^"]*)"[^>]*>By\s+([^<]+)</a>"#,
    )
    .unwrap();
    let id_re = Regex::new(r#"filedetails/\?id=(\d+)"#).unwrap();
    let id_positions: Vec<(String, usize)> = id_re
        .captures_iter(html)
        .map(|c| (c[1].to_string(), c.get(0).unwrap().start()))
        .collect();
    for cap in author_re.captures_iter(html) {
        let start = cap.get(0).unwrap().start();
        let url = cap[1].to_string();
        let name = cap[2].trim().to_string();
        if let Some(id) = id_positions
            .iter()
            .rev()
            .find(|(_, p)| *p < start)
            .map(|(id, _)| id.clone())
        {
            if let Some(entry) = by_id.get_mut(&id) {
                if entry.author.is_empty() {
                    entry.author = name;
                    entry.author_url = url;
                }
            }
        }
    }

    let mut ordered: Vec<(usize, WorkshopItem)> = by_id
        .into_iter()
        .filter_map(|(id, item)| {
            id_positions
                .iter()
                .find(|(p_id, _)| p_id == &id)
                .map(|(_, p)| (*p, item))
        })
        .collect();
    ordered.sort_by_key(|(p, _)| *p);
    ordered.into_iter().map(|(_, it)| it).collect()
}

/// Parse the SSR JSON payload Steam ships in a `<script>` tag. This
/// mirrors `parseSSRData()` from the original Python.
fn parse_browse_ssr(html: &str) -> Vec<WorkshopItem> {
    if !html.contains("window.SSR.renderContext") {
        return Vec::new();
    }
    // Pull out the queries blob: `queries":"…escaped JSON…"`
    let re = Regex::new(r#"queries"\s*:\s*"((?:\\.|[^"\\])*)""#).unwrap();
    let Some(cap) = re.captures(html) else {
        return Vec::new();
    };
    let raw = cap[1].replace(r"\\", r"\");
    let unescaped = unescape_json_string(&raw);
    let Ok(value) = serde_json::from_str::<Value>(&unescaped) else {
        return Vec::new();
    };
    let Some(arr) = value.as_array() else {
        return Vec::new();
    };

    // Each Steam SSR query carries one or more queryKey strings —
    // the "items" payload we want lives under the workshop browse key
    // OR the user-files key (author wallpapers tab) OR the collection
    // browse key (Collections tab). Just grab the *first* query that
    // exposes `state.data.items` so the SSR path works in every view
    // without us hard-coding query names.
    let mut found = None;
    for q in arr {
        if let Some(items) = q.pointer("/state/data/items") {
            if items.as_array().map(|a| !a.is_empty()).unwrap_or(false) {
                found = Some(items.clone());
                break;
            }
        }
    }
    let Some(items_val) = found else {
        return Vec::new();
    };
    let Some(items_arr) = items_val.as_array() else {
        return Vec::new();
    };
    items_arr
        .iter()
        .filter_map(|i| {
            let pubfileid = i
                .get("publishedfileid")
                .and_then(|v| v.as_str())
                .map(|s| s.to_string())
                .or_else(|| i.get("publishedfileid").and_then(|v| v.as_u64()).map(|n| n.to_string()))?;
            let title = i
                .get("title")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            let preview_url = i
                .get("preview_url")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();

            // Steam ships the author inside the SSR items in a couple of
            // shapes:
            //   - top-level fields: `creator_persona_name` / `creator`
            //   - a nested `creator_info` / `creator_data` object with
            //     `persona_name` and `profile_url`.
            // We sniff all of them so author chips are populated on the
            // first paint, before the in-card HTML fallback fires.
            let mut author = i
                .get("creator_persona_name")
                .and_then(|v| v.as_str())
                .map(String::from)
                .unwrap_or_default();
            let mut author_url = String::new();
            for key in ["creator_info", "creator_data", "creator"] {
                if author.is_empty() {
                    if let Some(name) = i
                        .pointer(&format!("/{}/persona_name", key))
                        .and_then(|v| v.as_str())
                    {
                        author = name.to_string();
                    }
                }
                if author_url.is_empty() {
                    if let Some(url) = i
                        .pointer(&format!("/{}/profile_url", key))
                        .and_then(|v| v.as_str())
                    {
                        author_url = url.to_string();
                    }
                }
            }
            // Sometimes the creator's SteamID64 is inlined and the
            // profile URL has to be reconstructed.
            if author_url.is_empty() {
                if let Some(steamid) = i
                    .get("creator")
                    .and_then(|v| v.as_str())
                    .or_else(|| i.get("creator_steamid").and_then(|v| v.as_str()))
                {
                    author_url =
                        format!("https://steamcommunity.com/profiles/{steamid}");
                }
            }

            Some(WorkshopItem {
                pubfileid,
                title,
                preview_url,
                author,
                author_url,
                ..Default::default()
            })
        })
        .collect()
}

fn unescape_json_string(s: &str) -> String {
    // The queries blob is double-escaped. After we unescape `\\` → `\`
    // we still need to handle simple JSON escapes.
    let mut out = String::with_capacity(s.len());
    let mut chars = s.chars().peekable();
    while let Some(c) = chars.next() {
        if c == '\\' {
            match chars.next() {
                Some('"') => out.push('"'),
                Some('n') => out.push('\n'),
                Some('t') => out.push('\t'),
                Some('r') => out.push('\r'),
                Some('/') => out.push('/'),
                Some('\\') => out.push('\\'),
                Some('u') => {
                    let hex: String = (&mut chars).take(4).collect();
                    if let Ok(n) = u32::from_str_radix(&hex, 16) {
                        if let Some(ch) = char::from_u32(n) {
                            out.push(ch);
                        }
                    }
                }
                Some(other) => {
                    out.push('\\');
                    out.push(other);
                }
                None => break,
            }
        } else {
            out.push(c);
        }
    }
    out
}

fn parse_pagination(html: &str, items: &[WorkshopItem]) -> (u32, u64) {
    let re_total = Regex::new(r#"(?:Showing|Отображаются?)\s+(\d+)[\s\-–](\d+)\s+(?:of|из)\s+([\d,\.\s]+)"#).unwrap();
    if let Some(cap) = re_total.captures(html) {
        let start: u64 = cap[1].replace([',', '.', ' '], "").parse().unwrap_or(0);
        let end: u64 = cap[2].replace([',', '.', ' '], "").parse().unwrap_or(0);
        let total: u64 = cap[3].replace([',', '.', ' '], "").parse().unwrap_or(0);
        if total > 0 {
            let per_page = (end - start + 1).max(1);
            return (total.div_ceil(per_page) as u32, total);
        }
    }
    let re_pages =
        Regex::new(r#"(?:p|page)=(\d+)[^"]*"\s*class="[^"]*"\s*>\s*(\d+)\s*<"#).unwrap();
    let max_page = re_pages
        .captures_iter(html)
        .filter_map(|c| c[2].parse::<u32>().ok())
        .max();
    if let Some(max) = max_page {
        let per_page = items.len().max(30) as u64;
        return (max, (max as u64) * per_page);
    }
    // Fallback: assume more pages exist if we filled a full page of 30
    if items.len() >= 30 {
        return (99, (items.len() as u64) * 99);
    }
    (1, items.len() as u64)
}

fn extract_pubfileid(href: &str) -> Option<String> {
    let re = Regex::new(r#"[?&]id=(\d+)"#).unwrap();
    re.captures(href).map(|c| c[1].to_string())
}

fn upscale_preview(src: &str) -> String {
    // Steam serves thumbs at imw=288&imh=288. Replace with a larger size when
    // hinted via the `ima=fit` letterbox template so the UI has crisp
    // previews.
    src.replace("imw=288", "imw=512").replace("imh=288", "imh=512")
}

fn inner_text(el: ElementRef<'_>) -> String {
    el.text().collect::<String>().trim().to_string()
}

fn text(el: ElementRef<'_>) -> String {
    inner_text(el)
}

fn select_first<'a>(doc: &'a Html, sel: &str) -> Option<ElementRef<'a>> {
    Selector::parse(sel).ok().and_then(|s| doc.select(&s).next())
}

pub fn parse_item_details(html: &str, pubfileid: &str) -> WorkshopItem {
    let doc = Html::parse_document(html);
    let mut item = WorkshopItem {
        pubfileid: pubfileid.to_string(),
        ..Default::default()
    };

    if let Some(el) = select_first(&doc, ".workshopItemTitle") {
        item.title = text(el);
    }
    if item.title.is_empty() {
        if let Some(el) = select_first(&doc, "title") {
            let t = text(el);
            item.title = t.replace("Steam Workshop::", "").trim().to_string();
        }
    }
    if let Some(el) = select_first(&doc, ".workshopItemDescription") {
        let t = text(el);
        item.description = if t.len() > 1000 {
            t.char_indices()
                .nth(1000)
                .map(|(idx, _)| &t[..idx])
                .unwrap_or(&t)
                .to_string()
        } else {
            t
        };
    }
    for sel in [
        "#previewImageMain",
        ".workshopItemPreviewImageEnlarge img",
        ".workshopItemPreviewImage img",
        ".highlight_screenshot img",
        "meta[property=\"og:image\"]",
    ] {
        if let Some(el) = select_first(&doc, sel) {
            let src = el
                .value()
                .attr("src")
                .or_else(|| el.value().attr("content"))
                .unwrap_or("");
            if !src.is_empty() {
                item.preview_url = src.to_string();
                break;
            }
        }
    }

    if let Some(el) = select_first(
        &doc,
        ".friendBlockContent a, .workshopItemAuthorName a, .creatorsBlock .friendBlock a",
    ) {
        if let Some(href) = el.value().attr("href") {
            item.author_url = href.to_string();
        }
    }

    if let Some(el) = select_first(&doc, ".friendBlockContent") {
        let children: Vec<_> = el
            .children()
            .filter_map(|c| c.value().as_text().map(|t| t.trim().to_string()))
            .filter(|s| !s.is_empty())
            .collect();
        if let Some(first) = children.first() {
            item.author = first.clone();
        }
    }

    if let Some(el) = select_first(&doc, ".detailsStatRight") {
        item.file_size = text(el);
    }

    let stat_keys = ["Posted", "Posted:", "Updated", "Updated:"];
    let labels = Selector::parse(".detailsStatLeft").unwrap();
    let values = Selector::parse(".detailsStatRight").unwrap();
    let lbls: Vec<_> = doc.select(&labels).map(text).collect();
    let vals: Vec<_> = doc.select(&values).map(text).collect();
    for (i, lbl) in lbls.iter().enumerate() {
        if stat_keys.iter().any(|k| lbl.trim_end_matches(':').eq_ignore_ascii_case(k.trim_end_matches(':'))) {
            let v = vals.get(i).cloned().unwrap_or_default();
            if lbl.to_lowercase().contains("post") {
                item.posted_date = v;
            } else if lbl.to_lowercase().contains("updat") {
                item.updated_date = v;
            }
        }
    }

    let rating_sel = Selector::parse(".fileRatingDetails img").unwrap();
    if let Some(img) = doc.select(&rating_sel).next() {
        if let Some(src) = img.value().attr("src") {
            item.rating_star_file = src.to_string();
        }
    }

    let num_sel = Selector::parse(".numRatings").unwrap();
    if let Some(el) = doc.select(&num_sel).next() {
        let raw = text(el);
        let digits: String = raw
            .chars()
            .filter(|c| c.is_ascii_digit() || *c == ',')
            .collect();
        item.num_ratings = digits;
    }

    // Workshop tags. Steam lists them as `<div class="workshopTags">Category:
    // <a>Tag1</a>, <a>Tag2</a></div>` — we extract both the category label
    // (e.g. "Type", "Genre", "Resolution") and the list of values so the UI
    // can render them grouped like the Python app does.
    let tag_block_sel = Selector::parse(".workshopTags").unwrap();
    let tag_link_sel = Selector::parse("a").unwrap();
    let mut tags = Vec::new();
    for block in doc.select(&tag_block_sel) {
        // The category label is the leading text node before the <a> tags.
        // We pick the first text node that contains *real* content, not
        // just punctuation or whitespace — Steam sometimes renders a
        // leading "." or ", " separator that would otherwise become a
        // bogus category header in the UI.
        let mut category = String::new();
        for child in block.children() {
            if let Some(t) = child.value().as_text() {
                let raw = t.trim().trim_end_matches(':').trim();
                if raw.is_empty() {
                    continue;
                }
                // Skip pure-punctuation noise (".", ",", "·", etc.).
                if raw.chars().all(|c| !c.is_alphanumeric()) {
                    continue;
                }
                category = raw.to_string();
                break;
            }
        }
        for a in block.select(&tag_link_sel) {
            let value = text(a);
            if value.is_empty() {
                continue;
            }
            let mut m = Map::new();
            m.insert("tag".into(), Value::String(value));
            if !category.is_empty() {
                m.insert("category".into(), Value::String(category.clone()));
            }
            tags.push(Value::Object(m));
        }
    }
    item.tags = Value::Array(tags);

    // Parent collections this item appears in. Steam emits:
    //   <div class="parentCollection" onClick="... id=12345 ...">
    //     <div class="parentCollectionTitle">Title</div>
    //     <div class="parentCollectionNumChildren">42 items</div>
    //   </div>
    let pc_sel = Selector::parse(".parentCollection").unwrap();
    let title_sel = Selector::parse(".parentCollectionTitle").unwrap();
    let count_sel = Selector::parse(".parentCollectionNumChildren").unwrap();
    let id_re = Regex::new(r#"id=(\d+)"#).unwrap();
    let num_re = Regex::new(r#"(\d+)"#).unwrap();
    for pc in doc.select(&pc_sel) {
        let onclick = pc
            .value()
            .attr("onClick")
            .or_else(|| pc.value().attr("onclick"))
            .unwrap_or("");
        let Some(cap) = id_re.captures(onclick) else {
            continue;
        };
        let id = cap[1].to_string();
        let title = pc
            .select(&title_sel)
            .next()
            .map(text)
            .unwrap_or_default();
        let count = pc
            .select(&count_sel)
            .next()
            .map(|e| text(e))
            .and_then(|s| num_re.captures(&s).map(|c| c[1].to_string()))
            .and_then(|s| s.parse::<u32>().ok())
            .unwrap_or(0);
        item.collections.push(CollectionRef {
            id,
            title: if title.is_empty() {
                "Collection".to_string()
            } else {
                title
            },
            item_count: count,
        });
    }

    item
}

pub fn parse_collection_contents(html: &str, collection_id: &str) -> CollectionContents {
    let doc = Html::parse_document(html);
    let mut c = CollectionContents {
        collection_id: collection_id.to_string(),
        ..Default::default()
    };

    if let Some(el) = select_first(&doc, ".workshopItemTitle") {
        c.title = text(el);
    }
    // The original PyQt build kept the *full* description (and only
    // truncated it for display when needed). Earlier we used inner_text
    // which strips whitespace and silently drops <br>-separated lines.
    // Switch to a newline-preserving extractor so the panel shows the
    // entire description Steam returns.
    if let Some(el) = select_first(&doc, ".workshopItemDescription") {
        c.description = inner_text_multiline(el);
    }
    // Background image first (Steam uses it as the hero on collection
    // pages); fall back to the standard og:image / preview slots.
    if let Some(bg) = select_first(&doc, ".collectionBackgroundImage") {
        if let Some(src) = bg.value().attr("src") {
            c.preview_url = src.to_string();
        }
    }
    if c.preview_url.is_empty() {
        for sel in [
            "#previewImageMain",
            ".workshopItemPreviewImage",
            ".highlight_screenshot img",
            "meta[property=\"og:image\"]",
        ] {
            if let Some(el) = select_first(&doc, sel) {
                let val = el
                    .value()
                    .attr("src")
                    .or_else(|| el.value().attr("content"))
                    .unwrap_or("");
                if !val.is_empty() {
                    c.preview_url = val.to_string();
                    break;
                }
            }
        }
    }

    // Author + author_url. Steam's collection page renders this as
    //   <div class="friendBlockContent"> Author<br>Author Name </div>
    //   with a sibling <a class="friendBlockLinkOverlay" href="…">.
    // Older variants: `.workshopItemAuthorName a`.
    if let Some(a) = select_first(&doc, ".workshopItemAuthorName a") {
        c.author = text(a);
        if let Some(href) = a.value().attr("href") {
            c.author_url = href.to_string();
        }
    } else if let Some(a) = select_first(&doc, ".friendBlockContent a") {
        c.author = text(a);
        if let Some(href) = a.value().attr("href") {
            c.author_url = href.to_string();
        }
    }
    if c.author_url.is_empty() {
        if let Some(a) = select_first(&doc, ".friendBlockLinkOverlay") {
            if let Some(href) = a.value().attr("href") {
                c.author_url = href.to_string();
            }
        }
    }

    // -------- info dictionary (rating, counts, dates, tag groups) --------
    let mut info = serde_json::Map::new();
    if let Some(img) = select_first(&doc, ".fileRatingDetails img") {
        if let Some(src) = img.value().attr("src") {
            let path = src.split('?').next().unwrap_or(src);
            let filename = path.rsplit('/').next().unwrap_or("");
            let stem = filename
                .trim_end_matches(".png")
                .trim_end_matches(".jpg")
                .trim_end_matches(".gif");
            if !stem.is_empty() {
                info.insert(
                    "rating_star_file".into(),
                    Value::String(stem.to_string()),
                );
            }
        }
    }
    if let Some(el) = select_first(&doc, ".numRatings") {
        let raw = text(el);
        let digits: String = raw
            .chars()
            .filter(|c| c.is_ascii_digit())
            .collect();
        if !digits.is_empty() {
            info.insert("num_ratings".into(), Value::String(digits));
        }
    }
    if let Some(el) = select_first(&doc, ".rightSectionTopTitle") {
        let raw = text(el);
        if let Some(m) = Regex::new(r"(\d+)").unwrap().captures(&raw) {
            if let Ok(n) = m[1].parse::<u64>() {
                info.insert(
                    "item_count".into(),
                    Value::Number(serde_json::Number::from(n)),
                );
            }
        }
    }
    let stat_left_sel = Selector::parse(".detailsStatLeft").unwrap();
    let stat_right_sel = Selector::parse(".detailsStatRight").unwrap();
    let lefts: Vec<_> = doc.select(&stat_left_sel).collect();
    let rights: Vec<_> = doc.select(&stat_right_sel).collect();
    for (l, r) in lefts.iter().zip(rights.iter()) {
        let left = text(*l);
        let right = text(*r);
        let lr = right.to_lowercase();
        let ll = left.to_lowercase();
        if lr.contains("unique") || lr.contains("уникальн") {
            info.insert("unique_visitors".into(), Value::String(left));
        } else if (lr.contains("всего") && lr.contains("избранн"))
            || (lr.contains("total") && lr.contains("favorit"))
        {
            info.insert("total_favorited".into(), Value::String(left));
        } else if lr.contains("избранн") || lr.contains("favorit") {
            info.insert("favorited".into(), Value::String(left));
        } else if lr.contains("подписч") || lr.contains("subscriber") {
            info.insert("subscribers".into(), Value::String(left));
        } else if ll.contains("добавлен")
            || ll.contains("posted")
            || ll.contains("added")
            || ll.contains("created")
        {
            info.insert("posted_date".into(), Value::String(right));
        } else if ll.contains("изменён") || ll.contains("updated") || ll.contains("changed") {
            info.insert("updated_date".into(), Value::String(right));
        }
    }
    // Tag groups (.workshopTags > .workshopTagsTitle + <a> links).
    let tag_block_sel = Selector::parse(".workshopTags").unwrap();
    let tag_title_sel = Selector::parse(".workshopTagsTitle").unwrap();
    let tag_link_sel = Selector::parse("a").unwrap();
    for td in doc.select(&tag_block_sel) {
        let Some(title_el) = td.select(&tag_title_sel).next() else {
            continue;
        };
        let mut key = text(title_el);
        key = key
            .trim_end_matches(|c: char| c == ':' || c.is_whitespace() || c == '\u{00a0}')
            .trim()
            .to_string();
        if key.is_empty() {
            continue;
        }
        let values: Vec<String> = td
            .select(&tag_link_sel)
            .map(text)
            .filter(|v| !v.is_empty())
            .collect();
        if !values.is_empty() {
            info.insert(key, Value::String(values.join(", ")));
        }
    }
    c.info = Value::Object(info);

    // -------- items in this collection (with their own author chips) ----
    let item_sel = Selector::parse(".collectionItem").unwrap();
    let link_sel = Selector::parse(r#"a[href*="filedetails"]"#).unwrap();
    let preview_sel = Selector::parse(".workshopItemPreviewImage").unwrap();
    let img_sel = Selector::parse("img").unwrap();
    let title_sel = Selector::parse(".workshopItemTitle").unwrap();
    let author_sel = Selector::parse(".workshopItemAuthorName a").unwrap();

    let mut seen = std::collections::HashSet::new();
    for e in doc.select(&item_sel) {
        let Some(link) = e.select(&link_sel).next() else {
            continue;
        };
        let Some(id) = extract_pubfileid(link.value().attr("href").unwrap_or("")) else {
            continue;
        };
        if id == collection_id || !seen.insert(id.clone()) {
            continue;
        }
        let title = e.select(&title_sel).next().map(text).unwrap_or_default();
        let preview = e
            .select(&preview_sel)
            .next()
            .and_then(|i| i.value().attr("src"))
            .or_else(|| {
                e.select(&img_sel)
                    .next()
                    .and_then(|i| i.value().attr("src"))
            })
            .unwrap_or("")
            .to_string();
        let mut author = String::new();
        let mut author_url = String::new();
        if let Some(a) = e.select(&author_sel).next() {
            author = text(a);
            if let Some(href) = a.value().attr("href") {
                author_url = href.to_string();
            }
        }
        c.items.push(WorkshopItem {
            pubfileid: id,
            title,
            preview_url: preview,
            author,
            author_url,
            ..Default::default()
        });
    }

    // -------- related collections sidebar ------------------------------
    let related_sel = Selector::parse(".collections > .workshopItem").unwrap();
    let count_sel = Selector::parse(".workshopCollectionNumChildren").unwrap();
    let digits_re = Regex::new(r"(\d+)").unwrap();
    for r in doc.select(&related_sel) {
        let Some(link) = r.select(&link_sel).next() else {
            continue;
        };
        let Some(id) = extract_pubfileid(link.value().attr("href").unwrap_or("")) else {
            continue;
        };
        if id == collection_id || !seen.insert(id.clone()) {
            continue;
        }
        let title = r.select(&title_sel).next().map(text).unwrap_or_default();
        let preview = r
            .select(&preview_sel)
            .next()
            .and_then(|i| i.value().attr("src"))
            .unwrap_or("")
            .to_string();
        let mut item_count: u32 = 0;
        if let Some(ce) = r.select(&count_sel).next() {
            let raw = text(ce);
            if let Some(m) = digits_re.captures(&raw) {
                if let Ok(n) = m[1].parse::<u32>() {
                    item_count = n;
                }
            }
        }
        let collections = if item_count > 0 {
            vec![CollectionRef {
                id: id.clone(),
                title: String::new(),
                item_count,
            }]
        } else {
            Vec::new()
        };
        c.related_collections.push(WorkshopItem {
            pubfileid: id,
            title,
            preview_url: preview,
            is_collection: true,
            collections,
            ..Default::default()
        });
    }

    c
}

/// `<element>...</element>` -> visible text, preserving line breaks for
/// `<br>` and block-level descendants. Used for collection descriptions
/// where the raw `el.text()` join collapses paragraphs.
fn inner_text_multiline(el: ElementRef<'_>) -> String {
    use ego_tree::iter::Edge;
    let mut out = String::new();
    for edge in el.traverse() {
        match edge {
            Edge::Open(node) => {
                if let Some(t) = node.value().as_text() {
                    out.push_str(t);
                } else if let Some(e) = node.value().as_element() {
                    let name = e.name();
                    if name == "br" {
                        out.push('\n');
                    }
                }
            }
            Edge::Close(node) => {
                if let Some(e) = node.value().as_element() {
                    let name = e.name();
                    if matches!(
                        name,
                        "p" | "div" | "li" | "h1" | "h2" | "h3" | "h4" | "h5" | "h6"
                    ) {
                        out.push('\n');
                    }
                }
            }
        }
    }
    // Collapse runs of 3+ newlines to 2 to keep descriptions tidy.
    let re = Regex::new(r"\n{3,}").unwrap();
    re.replace_all(out.trim(), "\n\n").to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Tiny synthetic fixture that mirrors the stable markup Steam still
    /// emits on the Workshop browse page (filedetails links with images +
    /// a "By Author" link per tile). Verifies that the regex-based parser
    /// can recover (pubfileid, title, preview_url, author) pairs even
    /// when everything around them uses obfuscated CSS class names.
    #[test]
    fn parses_minimal_browse_fixture() {
        let html = r##"
            <html><body>
            <div class="rKsVn">
                <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=111">
                    <img src="https://example.com/a.jpg?imw=288" alt="Title A">
                </a>
                <a href="https://steamcommunity.com/id/user1/myworkshopfiles/?appid=431960">By Author One</a>
            </div>
            <div class="rKsVn">
                <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=222">
                    <img src="https://example.com/b.jpg?imw=288" alt="Title B">
                </a>
                <a href="https://steamcommunity.com/id/user2/myworkshopfiles/?appid=431960">By Author Two</a>
            </div>
            </body></html>
        "##;
        let page = parse_browse(html, 1);
        assert_eq!(page.items.len(), 2);
        assert_eq!(page.items[0].pubfileid, "111");
        assert_eq!(page.items[0].title, "Title A");
        assert!(page.items[0].preview_url.contains("imw=512"));
        assert_eq!(page.items[0].author, "Author One");
        assert_eq!(page.items[1].pubfileid, "222");
        assert_eq!(page.items[1].author, "Author Two");
    }
}
