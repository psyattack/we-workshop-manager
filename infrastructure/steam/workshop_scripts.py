def build_preload_page_script(url: str, request_id: int) -> str:
    return f"""
    (async function() {{
        window.__workshopPreloadResult = null;
        window.__workshopPreloadLoading = true;
        window.__workshopPreloadRequestId = {request_id};

        try {{
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000);

            const response = await fetch('{url}', {{
                credentials: 'include',
                signal: controller.signal
            }});

            clearTimeout(timeoutId);

            if (!response.ok) {{
                window.__workshopPreloadResult = {{ error: 'HTTP ' + response.status }};
                window.__workshopPreloadLoading = false;
                return;
            }}

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const result = {{
                items: [],
                current_page: 1,
                total_pages: 1,
                total_items: 0
            }};

            const containers = doc.querySelectorAll('.workshopItem, .workshopItemCollection');

            result.items = Array.from(containers).map(item => {{
                try {{
                    const link = item.querySelector('a[href*="filedetails"]');
                    if (!link) return null;

                    const href = link.href || '';
                    const idMatch = href.match(/id=(\\d+)/);
                    if (!idMatch) return null;

                    const pubfileid = idMatch[1];

                    let title = '';
                    const titleEl = item.querySelector('.workshopItemTitle');
                    if (titleEl) title = titleEl.innerText.trim();

                    let previewUrl = '';
                    const imgEl = item.querySelector('img');
                    if (imgEl) previewUrl = imgEl.src || imgEl.dataset.src || '';

                    let author = '';
                    let authorUrl = '';
                    const authorEl = item.querySelector('.workshopItemAuthorName a');
                    if (authorEl) {{
                        author = authorEl.innerText.trim();
                        authorUrl = authorEl.href || '';
                    }}

                    return {{
                        pubfileid,
                        title: title || ('Wallpaper ' + pubfileid),
                        preview_url: previewUrl,
                        author,
                        author_url: authorUrl
                    }};
                }} catch (e) {{
                    return null;
                }}
            }}).filter(Boolean);

            const urlParams = new URLSearchParams('{url}'.split('?')[1] || '');
            result.current_page = parseInt(urlParams.get('p') || '1');

            const pagingInfo = doc.querySelector('.workshopBrowsePagingInfo');
            if (pagingInfo) {{
                const text = pagingInfo.innerText;
                const match = text.match(/(\\d+)[\\s\\-–](\\d+)\\s+(?:of|из)\\s+([\\d,\\. ]+)/i);
                if (match) {{
                    const start = parseInt(match[1].replace(/[,\\.\\s]/g, ''));
                    const end = parseInt(match[2].replace(/[,\\.\\s]/g, ''));
                    const total = parseInt(match[3].replace(/[,\\.\\s]/g, ''));
                    result.total_items = total;
                    const itemsPerPage = end - start + 1;
                    result.total_pages = Math.ceil(total / itemsPerPage);
                }}
            }}

            if (result.items.length > 0 && result.total_items === 0) {{
                const itemsPerPage = 15;
                result.total_items = Math.max(result.items.length, result.current_page * itemsPerPage);
                result.total_pages = Math.max(result.current_page, Math.ceil(result.total_items / itemsPerPage));
            }}

            result.current_page = Math.min(result.current_page, result.total_pages);
            result.total_pages = Math.max(1, result.total_pages);

            window.__workshopPreloadResult = result;
        }} catch (err) {{
            window.__workshopPreloadResult = {{
                error: err.name === 'AbortError' ? 'Timeout' : err.message
            }};
        }}

        window.__workshopPreloadLoading = false;
    }})();
    """


def build_preload_poll_script(request_id: int) -> str:
    return f"""
    (function() {{
        if (window.__workshopPreloadRequestId !== {request_id}) {{
            return {{ cancelled: true }};
        }}

        if (window.__workshopPreloadLoading === false) {{
            const result = window.__workshopPreloadResult;
            window.__workshopPreloadResult = null;
            return result;
        }}

        return null;
    }})();
    """


def build_item_details_fetch_script(pubfileid: str, request_id: int) -> str:
    return f"""
    (async function() {{
        window.__workshopDetailsResult = null;
        window.__workshopDetailsLoading = true;
        window.__workshopRequestId = {request_id};

        try {{
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000);

            const response = await fetch(
                'https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}',
                {{
                    credentials: 'include',
                    signal: controller.signal
                }}
            );

            clearTimeout(timeoutId);

            if (!response.ok) {{
                window.__workshopDetailsResult = {{ error: 'HTTP ' + response.status }};
                window.__workshopDetailsLoading = false;
                return;
            }}

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const result = {{
                pubfileid: '{pubfileid}',
                title: '',
                description: '',
                preview_url: '',
                file_size: '',
                posted_date: '',
                updated_date: '',
                tags: {{}},
                rating_star_file: '',
                num_ratings: '',
                author: '',
                author_url: ''
            }};

            const titleEl = doc.querySelector('.workshopItemTitle');
            if (titleEl) result.title = titleEl.innerText.trim();

            const descEl = doc.querySelector('.workshopItemDescription');
            if (descEl) result.description = descEl.innerText.trim().substring(0, 1000);

            for (const sel of ['#previewImageMain', '.workshopItemPreviewImage img', '.highlight_screenshot img']) {{
                const el = doc.querySelector(sel);
                if (el && el.src) {{
                    result.preview_url = el.src;
                    break;
                }}
            }}

            const authorLink = doc.querySelector('.friendBlockContent a, .workshopItemAuthorName a, .creatorsBlock .friendBlock a');
            if (authorLink) {{
                result.author_url = authorLink.href || '';
            }}

            const authorNameEl = doc.querySelector('.friendBlockContent');
            if (authorNameEl) {{
                const textNodes = [];
                for (const node of authorNameEl.childNodes) {{
                    if (node.nodeType === Node.TEXT_NODE) {{
                        const text = node.textContent.trim();
                        if (text) textNodes.push(text);
                    }}
                }}
                if (textNodes.length > 0) {{
                    result.author = textNodes[0];
                }}
            }}

            if (!result.author) {{
                const authorEl = doc.querySelector('.workshopItemAuthorName a');
                if (authorEl) {{
                    result.author = authorEl.innerText.trim();
                    if (!result.author_url) result.author_url = authorEl.href || '';
                }}
            }}

            if (!result.author) {{
                const creatorsBlock = doc.querySelector('.creatorsBlock');
                if (creatorsBlock) {{
                    const nameEl = creatorsBlock.querySelector('.friendBlockContent');
                    if (nameEl) {{
                        const text = nameEl.innerText.trim().split('\\n')[0].trim();
                        if (text) result.author = text;
                    }}
                }}
            }}

            const ratingImg = doc.querySelector('#detailsHeaderRight > div > div.fileRatingDetails img');
            if (ratingImg) {{
                const src = ratingImg.getAttribute('src') || '';
                if (src) {{
                    const urlPath = src.split('?')[0];
                    const filename = urlPath.split('/').pop() || '';
                    result.rating_star_file = filename
                        .replace('.png', '')
                        .replace('.jpg', '')
                        .replace('.gif', '');
                }}
            }}

            const numRatingsEl = doc.querySelector('#detailsHeaderRight > div > div.numRatings');
            if (numRatingsEl) {{
                const rawText = numRatingsEl.innerText.trim();
                const numMatch = rawText.match(/(\\d[\\d\\s,\\.]*)/);
                if (numMatch) {{
                    result.num_ratings = numMatch[1].replace(/[\\s,\\.]/g, '');
                }}
            }}

            const rightCol = doc.querySelector('#mainContents .col_right.responsive_local_menu');
            const text = (rightCol ? rightCol.innerText : doc.body.innerText)
                .replace(/[\\t\\n]+/g, ' ')
                .replace(/\\s+/g, ' ')
                .trim();

            const sizeMatch = text.match(/File Size.*?(\\d+(?:[.,]\\d+)?)\\s*(GB|MB|KB)/i);
            if (sizeMatch) result.file_size = sizeMatch[1] + ' ' + sizeMatch[2].toUpperCase();

            const postedMatch = text.match(/Posted.*?(\\d{{1,2}}\\s+\\w{{3}},?\\s*(?:\\d{{4}})?\\s*@\\s*\\d{{1,2}}:\\d{{2}}(?:am|pm)?)/i);
            if (postedMatch) result.posted_date = postedMatch[1];

            const datePattern = /(\\d{{1,2}}\\s+\\w{{3}},?\\s*(?:\\d{{4}})?\\s*@\\s*\\d{{1,2}}:\\d{{2}}(?:am|pm)?)/gi;
            const dateMatches = [...text.matchAll(datePattern)];
            if (dateMatches.length >= 2) result.updated_date = dateMatches[1][1];

            const tagPatterns = {{
                "Miscellaneous": /Miscellaneous:\\s*(.*?)(?=Type:|Age Rating:|Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                "Type": /Type:\\s*(.*?)(?=Age Rating:|Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                "Age Rating": /Age Rating:\\s*(.*?)(?=Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                "Genre": /Genre:\\s*(.*?)(?=Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                "Resolution": /Resolution:\\s*(.*?)(?=Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                "Category": /Category:\\s*(.*?)(?=Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                "Content Descriptors": /Content Descriptors:\\s*(.*?)(?=Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                "Script Type": /Script Type:\\s*(.*?)(?=Asset Type:|Asset Genre:|File Size|Posted|$)/i,
                "Asset Type": /Asset Type:\\s*(.*?)(?=Asset Genre:|File Size|Posted|$)/i,
                "Asset Genre": /Asset Genre:\\s*(.*?)(?=File Size|Posted|$)/i
            }};

            for (const [key, pattern] of Object.entries(tagPatterns)) {{
                const match = text.match(pattern);
                if (match && match[1]) {{
                    const value = match[1].trim();
                    if (value && value.length < 100) result.tags[key] = value;
                }}
            }}

            // Parse collections that contain this item
            result.collections = [];
            const parentColDivs = doc.querySelectorAll('.parentCollection');
            for (const pc of parentColDivs) {{
                try {{
                    const oc = pc.getAttribute('onClick') || pc.getAttribute('onclick') || '';
                    const im = oc.match(/id=(\\d+)/);
                    if (!im) continue;
                    let t = '';
                    const te = pc.querySelector('.parentCollectionTitle');
                    if (te) t = te.innerText.trim();
                    let ic = 0;
                    const ce = pc.querySelector('.parentCollectionNumChildren');
                    if (ce) {{ const cm = ce.innerText.match(/(\\d+)/); if (cm) ic = parseInt(cm[1]); }}
                    result.collections.push({{ id: im[1], title: t || ('Collection ' + im[1]), item_count: ic }});
                }} catch(e) {{}}
            }}

            window.__workshopDetailsResult = result;
        }} catch (err) {{
            window.__workshopDetailsResult = {{
                error: err.name === 'AbortError' ? 'Timeout' : err.message
            }};
        }}

        window.__workshopDetailsLoading = false;
    }})();
    """


def build_item_details_poll_script(request_id: int) -> str:
    return f"""
    (function() {{
        if (window.__workshopRequestId !== {request_id}) {{
            return {{ cancelled: true }};
        }}

        if (window.__workshopDetailsLoading === false) {{
            const result = window.__workshopDetailsResult;
            window.__workshopDetailsResult = null;
            return result;
        }}

        return null;
    }})();
    """


def browse_page_parse_script() -> str:
    return """
    (function() {
        const result = {
            items: [],
            current_page: 1,
            total_pages: 1,
            total_items: 0
        };

        const containers = document.querySelectorAll('.workshopItem, .workshopItemCollection');

        result.items = Array.from(containers).map(item => {
            try {
                const link = item.querySelector('a[href*="filedetails"]');
                if (!link) return null;

                const href = link.href || '';
                const idMatch = href.match(/id=(\\d+)/);
                if (!idMatch) return null;

                const pubfileid = idMatch[1];

                let title = '';
                const titleEl = item.querySelector('.workshopItemTitle');
                if (titleEl) title = titleEl.innerText.trim();

                let previewUrl = '';
                const imgEl = item.querySelector('img');
                if (imgEl) previewUrl = imgEl.src || imgEl.dataset.src || '';

                let author = '';
                let authorUrl = '';
                const authorEl = item.querySelector('.workshopItemAuthorName a');
                if (authorEl) {
                    author = authorEl.innerText.trim();
                    authorUrl = authorEl.href || '';
                }

                return {
                    pubfileid,
                    title: title || ('Wallpaper ' + pubfileid),
                    preview_url: previewUrl,
                    author,
                    author_url: authorUrl
                };
            } catch (e) {
                return null;
            }
        }).filter(Boolean);

        const urlParams = new URLSearchParams(window.location.search);
        result.current_page = parseInt(urlParams.get('p') || '1');

        const pagingInfo = document.querySelector('.workshopBrowsePagingInfo');
        if (pagingInfo) {
            const text = pagingInfo.innerText;
            const match = text.match(/(\\d+)[\\s\\-–](\\d+)\\s+(?:of|из)\\s+([\\d,\\. ]+)/i);
            if (match) {
                const start = parseInt(match[1].replace(/[,\\.\\s]/g, ''));
                const end = parseInt(match[2].replace(/[,\\.\\s]/g, ''));
                const total = parseInt(match[3].replace(/[,\\.\\s]/g, ''));
                result.total_items = total;
                const itemsPerPage = end - start + 1;
                result.total_pages = Math.ceil(total / itemsPerPage);
            }
        }

        if (result.items.length > 0 && result.total_items === 0) {
            const itemsPerPage = 15;
            result.total_items = Math.max(result.items.length, result.current_page * itemsPerPage);
            result.total_pages = Math.max(result.current_page, Math.ceil(result.total_items / itemsPerPage));
        }

        result.current_page = Math.min(result.current_page, result.total_pages);
        result.total_pages = Math.max(1, result.total_pages);

        return result;
    })();
    """


def login_form_fill_script(username: str, password: str) -> str:
    username_escaped = username.replace("\\", "\\\\").replace('"', '\\"')
    password_escaped = password.replace("\\", "\\\\").replace('"', '\\"')

    return f"""
    (function() {{
        const loginInput = document.querySelector('input[type="text"]');
        const passwordInput = document.querySelector('input[type="password"]');

        if (!loginInput || !passwordInput) {{
            return {{ ready: false }};
        }}

        function fillInput(input, value) {{
            input.focus();
            const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setter.call(input, value);
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}

        fillInput(loginInput, "{username_escaped}");
        fillInput(passwordInput, "{password_escaped}");

        let submitBtn = document.querySelector('button[type="submit"]');
        if (!submitBtn) {{
            for (const btn of document.querySelectorAll('button')) {{
                if (btn.innerText.toLowerCase().includes('sign in')) {{
                    submitBtn = btn;
                    break;
                }}
            }}
        }}

        if (submitBtn) {{
            submitBtn.disabled = false;
            submitBtn.click();
            return {{ ready: true, clicked: true }};
        }}

        return {{ ready: true, clicked: false }};
    }})();
    """


def login_state_check_script() -> str:
    return """
    (function() {
        const err = document.querySelector('[class*="error"], [class*="Error"]');
        const guard = document.querySelector('[class*="guard"], [class*="twofactor"], [class*="authcode"]');

        return {
            hasError: !!(err && err.innerText.trim()),
            errorText: err ? err.innerText.trim().substring(0, 100) : '',
            hasGuard: !!guard
        };
    })();
    """

def _build_details_parse_body(pubfileid: str) -> str:
    return f"""
        const result = {{ pubfileid: '{pubfileid}', title: '', description: '', preview_url: '',
            file_size: '', posted_date: '', updated_date: '', tags: {{}},
            rating_star_file: '', num_ratings: '', author: '', author_url: '' }};

        const titleEl = doc.querySelector('.workshopItemTitle');
        if (titleEl) result.title = titleEl.innerText.trim();

        const descEl = doc.querySelector('.workshopItemDescription');
        if (descEl) result.description = descEl.innerText.trim().substring(0, 1000);

        for (const sel of ['#previewImageMain', '.workshopItemPreviewImage img', '.highlight_screenshot img']) {{
            const el = doc.querySelector(sel);
            if (el && el.src) {{ result.preview_url = el.src; break; }}
        }}

        const authorLink = doc.querySelector('.friendBlockContent a, .workshopItemAuthorName a, .creatorsBlock .friendBlock a');
        if (authorLink) {{ result.author_url = authorLink.href || ''; }}

        const authorNameEl = doc.querySelector('.friendBlockContent');
        if (authorNameEl) {{
            const textNodes = [];
            for (const node of authorNameEl.childNodes) {{
                if (node.nodeType === Node.TEXT_NODE) {{
                    const text = node.textContent.trim();
                    if (text) textNodes.push(text);
                }}
            }}
            if (textNodes.length > 0) {{ result.author = textNodes[0]; }}
        }}

        if (!result.author) {{
            const authorEl = doc.querySelector('.workshopItemAuthorName a');
            if (authorEl) {{
                result.author = authorEl.innerText.trim();
                if (!result.author_url) result.author_url = authorEl.href || '';
            }}
        }}

        if (!result.author) {{
            const creatorsBlock = doc.querySelector('.creatorsBlock');
            if (creatorsBlock) {{
                const nameEl = creatorsBlock.querySelector('.friendBlockContent');
                if (nameEl) {{
                    const text = nameEl.innerText.trim().split('\\n')[0].trim();
                    if (text) result.author = text;
                }}
            }}
        }}

        const ratingImg = doc.querySelector('#detailsHeaderRight > div > div.fileRatingDetails img');
        if (ratingImg) {{
            const src = ratingImg.getAttribute('src') || '';
            if (src) {{
                const urlPath = src.split('?')[0];
                const filename = urlPath.split('/').pop() || '';
                result.rating_star_file = filename
                    .replace('.png', '').replace('.jpg', '').replace('.gif', '');
            }}
        }}

        const numRatingsEl = doc.querySelector('#detailsHeaderRight > div > div.numRatings');
        if (numRatingsEl) {{
            const rawText = numRatingsEl.innerText.trim();
            const numMatch = rawText.match(/(\\d[\\d\\s,\\.]*)/);
            if (numMatch) {{ result.num_ratings = numMatch[1].replace(/[\\s,\\.]/g, ''); }}
        }}

        const rightCol = doc.querySelector('#mainContents .col_right.responsive_local_menu');
        const text = (rightCol ? rightCol.innerText : doc.body.innerText)
            .replace(/[\\t\\n]+/g, ' ').replace(/\\s+/g, ' ').trim();

        const sizeMatch = text.match(/File Size.*?(\\d+(?:[.,]\\d+)?)\\s*(GB|MB|KB)/i);
        if (sizeMatch) result.file_size = sizeMatch[1] + ' ' + sizeMatch[2].toUpperCase();

        const postedMatch = text.match(/Posted.*?(\\d{{1,2}}\\s+\\w{{3}},?\\s*(?:\\d{{4}})?\\s*@\\s*\\d{{1,2}}:\\d{{2}}(?:am|pm)?)/i);
        if (postedMatch) result.posted_date = postedMatch[1];

        const datePattern = /(\\d{{1,2}}\\s+\\w{{3}},?\\s*(?:\\d{{4}})?\\s*@\\s*\\d{{1,2}}:\\d{{2}}(?:am|pm)?)/gi;
        const dateMatches = [...text.matchAll(datePattern)];
        if (dateMatches.length >= 2) result.updated_date = dateMatches[1][1];

        const tagPatterns = {{
            "Miscellaneous": /Miscellaneous:\\s*(.*?)(?=Type:|Age Rating:|Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Type": /Type:\\s*(.*?)(?=Age Rating:|Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Age Rating": /Age Rating:\\s*(.*?)(?=Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Genre": /Genre:\\s*(.*?)(?=Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Resolution": /Resolution:\\s*(.*?)(?=Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Category": /Category:\\s*(.*?)(?=Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Content Descriptors": /Content Descriptors:\\s*(.*?)(?=Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Script Type": /Script Type:\\s*(.*?)(?=Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Asset Type": /Asset Type:\\s*(.*?)(?=Asset Genre:|File Size|Posted|$)/i,
            "Asset Genre": /Asset Genre:\\s*(.*?)(?=File Size|Posted|$)/i
        }};

        for (const [key, pattern] of Object.entries(tagPatterns)) {{
            const match = text.match(pattern);
            if (match && match[1]) {{
                const value = match[1].trim();
                if (value && value.length < 100) result.tags[key] = value;
            }}
        }}

        for (const [key, pattern] of Object.entries(tagPatterns)) {{
            const match = text.match(pattern);
            if (match && match[1]) {{
                const value = match[1].trim();
                if (value && value.length < 100) result.tags[key] = value;
            }}
        }}

        result.collections = [];
        const parentColDivs = doc.querySelectorAll('.parentCollection');
        for (const pc of parentColDivs) {{
            try {{
                const oc = pc.getAttribute('onClick') || pc.getAttribute('onclick') || '';
                const im = oc.match(/id=(\\d+)/);
                if (!im) continue;
                let t = '';
                const te = pc.querySelector('.parentCollectionTitle');
                if (te) t = te.innerText.trim();
                let ic = 0;
                const ce = pc.querySelector('.parentCollectionNumChildren');
                if (ce) {{ const cm = ce.innerText.match(/(\\d+)/); if (cm) ic = parseInt(cm[1]); }}
                result.collections.push({{ id: im[1], title: t || ('Collection ' + im[1]), item_count: ic }});
            }} catch(e) {{}}
        }}"""


def build_bg_item_details_fetch_script(pubfileid: str, request_id: int) -> str:
    body = _build_details_parse_body(pubfileid)
    rv = f"window.__bgDR{request_id}"
    lv = f"window.__bgDL{request_id}"
    return f"""
(async function() {{
    {rv} = null;
    {lv} = true;
    try {{
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);
        const response = await fetch(
            'https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}',
            {{ credentials: 'include', signal: controller.signal }}
        );
        clearTimeout(timeoutId);
        if (!response.ok) {{
            {rv} = {{ error: 'HTTP ' + response.status }};
            {lv} = false;
            return;
        }}
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
{body}
        {rv} = result;
    }} catch (err) {{
        {rv} = {{ error: err.name === 'AbortError' ? 'Timeout' : err.message }};
    }}
    {lv} = false;
}})();
"""


def build_bg_item_details_poll_script(request_id: int) -> str:
    rv = f"window.__bgDR{request_id}"
    lv = f"window.__bgDL{request_id}"
    return f"""
(function() {{
    if ({lv} === false) {{
        const r = {rv};
        {rv} = undefined;
        {lv} = undefined;
        return r;
    }}
    return null;
}})();
"""


def collection_listing_parse_script() -> str:
    """Parse a page that lists collections (browse or author)."""
    return r"""
    (function() {
        const result = { items: [], current_page: 1, total_pages: 1, total_items: 0 };

        const collections = document.querySelectorAll('a.workshopItemCollection');

        result.items = Array.from(collections).map(item => {
            try {
                const href = item.getAttribute('href') || item.href || '';
                const idMatch = href.match(/id=(\d+)/);
                if (!idMatch) return null;
                const pubfileid = idMatch[1];

                let title = '';
                const titleEl = item.querySelector('.workshopItemTitle');
                if (titleEl) title = titleEl.innerText.trim();

                let previewUrl = '';
                const imgEl = item.querySelector('.workshopItemPreviewImage');
                if (imgEl) previewUrl = imgEl.src || '';
                if (!previewUrl) {
                    const anyImg = item.querySelector('img');
                    if (anyImg) previewUrl = anyImg.src || '';
                }

                let author = '';
                let authorUrl = '';
                const authorSpan = item.querySelector('.workshopItemAuthorName');
                if (authorSpan) {
                    author = authorSpan.innerText.trim();
                    const authorLink = authorSpan.querySelector('a');
                    if (authorLink) authorUrl = authorLink.href || '';
                }

                return {
                    pubfileid,
                    title: title || ('Collection ' + pubfileid),
                    preview_url: previewUrl,
                    author,
                    author_url: authorUrl,
                    is_collection: true
                };
            } catch (e) { return null; }
        }).filter(Boolean);

        const urlParams = new URLSearchParams(window.location.search);
        result.current_page = parseInt(urlParams.get('p') || '1');

        const pagingInfo = document.querySelector('.workshopBrowsePagingInfo');
        if (pagingInfo) {
            const text = pagingInfo.innerText;
            const match = text.match(/(\d+)[\s\-\u2013](\d+)\s+(?:of|\u0438\u0437)\s+([\d,\.\s]+)/i);
            if (match) {
                const start = parseInt(match[1].replace(/[,\.\s]/g, ''));
                const end = parseInt(match[2].replace(/[,\.\s]/g, ''));
                const total = parseInt(match[3].replace(/[,\.\s]/g, ''));
                result.total_items = total;
                const itemsPerPage = end - start + 1;
                result.total_pages = Math.ceil(total / itemsPerPage);
            }
        }

        if (result.items.length > 0 && result.total_items === 0) {
            result.total_items = result.items.length;
            result.total_pages = 1;
        }

        result.current_page = Math.min(result.current_page, Math.max(1, result.total_pages));
        result.total_pages = Math.max(1, result.total_pages);
        return result;
    })();
    """


def build_collection_contents_fetch_script(collection_id: str, request_id: int) -> str:
    return f"""
    (async function() {{
        window.__collectionResult = null;
        window.__collectionLoading = true;
        window.__collectionRequestId = {request_id};
        try {{
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            const response = await fetch(
                'https://steamcommunity.com/sharedfiles/filedetails/?id={collection_id}',
                {{ credentials: 'include', signal: controller.signal }}
            );
            clearTimeout(timeoutId);
            if (!response.ok) {{
                window.__collectionResult = {{ error: 'HTTP ' + response.status }};
                window.__collectionLoading = false;
                return;
            }}
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const result = {{
                collection_id: '{collection_id}',
                title: '',
                description: '',
                preview_url: '',
                author: '',
                author_url: '',
                items: [],
                related_collections: [],
                info: {{}}
            }};

            // Title
            const titleEl = doc.querySelector('.workshopItemTitle');
            if (titleEl) result.title = titleEl.innerText.trim();

            // Description
            const descEl = doc.querySelector('.workshopItemDescription');
            if (descEl) result.description = descEl.innerText.trim().substring(0, 1000);

            // Preview — collectionBackgroundImage first, then fallbacks
            const bgImg = doc.querySelector('.collectionBackgroundImage');
            if (bgImg && bgImg.src) {{
                result.preview_url = bgImg.src;
            }} else {{
                for (const sel of ['#previewImageMain', '.workshopItemPreviewImage', '.highlight_screenshot img']) {{
                    const el = doc.querySelector(sel);
                    if (el && el.src) {{ result.preview_url = el.src; break; }}
                }}
            }}

            // Rating
            const ratingImg = doc.querySelector('.fileRatingDetails img');
            if (ratingImg) {{
                const src = ratingImg.getAttribute('src') || '';
                if (src) {{
                    const urlPath = src.split('?')[0];
                    const filename = urlPath.split('/').pop() || '';
                    result.info.rating_star_file = filename
                        .replace('.png', '').replace('.jpg', '').replace('.gif', '');
                }}
            }}

            // Num ratings
            const numRatingsEl = doc.querySelector('.numRatings');
            if (numRatingsEl) {{
                const rawText = numRatingsEl.innerText.trim();
                const numMatch = rawText.match(/(\\d[\\d\\s,\\.]*)/);
                if (numMatch) {{
                    result.info.num_ratings = numMatch[1].replace(/[\\s,\\.]/g, '');
                }}
            }}

            // Author from creatorsBlock
            const creatorsBlock = doc.querySelector('.creatorsBlock');
            if (creatorsBlock) {{
                const authorLink = creatorsBlock.querySelector('.friendBlockLinkOverlay');
                if (authorLink) result.author_url = authorLink.href || '';
                const nameEl = creatorsBlock.querySelector('.friendBlockContent');
                if (nameEl) {{
                    const textNodes = [];
                    for (const node of nameEl.childNodes) {{
                        if (node.nodeType === Node.TEXT_NODE) {{
                            const t = node.textContent.trim();
                            if (t) textNodes.push(t);
                        }}
                    }}
                    if (textNodes.length > 0) result.author = textNodes[0];
                }}
            }}
            if (!result.author) {{
                const ae = doc.querySelector('.workshopItemAuthorName a');
                if (ae) {{
                    result.author = ae.innerText.trim();
                    if (!result.author_url) result.author_url = ae.href || '';
                }}
            }}

            // Stats from detailsStatLeft / detailsStatRight pairs
            const leftStats = doc.querySelectorAll('.detailsStatLeft');
            const rightStats = doc.querySelectorAll('.detailsStatRight');
            const minLen = Math.min(leftStats.length, rightStats.length);
            for (let i = 0; i < minLen; i++) {{
                const left = leftStats[i].innerText.trim();
                const right = rightStats[i].innerText.trim();
                const r = right.toLowerCase();
                const l = left.toLowerCase();

                if (r.includes('unique') || r.includes('уникальн')) {{
                    result.info.unique_visitors = left;
                }} else if ((r.includes('всего') && r.includes('избранн')) || r.includes('total') && r.includes('favorit')) {{
                    result.info.total_favorited = left;
                }} else if (r.includes('избранн') || r.includes('favorit')) {{
                    result.info.favorited = left;
                }} else if (r.includes('подписч') || r.includes('subscriber')) {{
                    result.info.subscribers = left;
                }} else if (l.includes('добавлен') || l.includes('posted') || l.includes('added') || l.includes('created')) {{
                    result.info.posted_date = right;
                }} else if (l.includes('изменён') || l.includes('updated') || l.includes('changed')) {{
                    result.info.updated_date = right;
                }}
            }}

            // Item count from rightSectionTopTitle
            const topTitle = doc.querySelector('.rightSectionTopTitle');
            if (topTitle) {{
                const m = topTitle.innerText.match(/(\\d+)/);
                if (m) result.info.item_count = parseInt(m[1]);
            }}

            // Tags from .workshopTags
            const tagDivs = doc.querySelectorAll('.workshopTags');
            for (const td of tagDivs) {{
                const titleSpan = td.querySelector('.workshopTagsTitle');
                if (titleSpan) {{
                    const key = titleSpan.innerText.replace(/[:\\s\\u00a0]+$/g, '').trim();
                    const links = td.querySelectorAll('a');
                    const values = Array.from(links).map(a => a.innerText.trim()).filter(Boolean);
                    if (key && values.length > 0) {{
                        result.info[key] = values.join(', ');
                    }}
                }}
            }}

            // Content descriptors
            const descBlocks = doc.querySelectorAll('.rightDetailsBlock');
            for (const block of descBlocks) {{
                const titleSpan = block.querySelector('.workshopTagsTitle');
                if (titleSpan) {{
                    const titleText = titleSpan.innerText.trim().toLowerCase();
                    if (titleText.includes('дескриптор') || titleText.includes('content descriptor')) {{
                        let descText = block.innerText.replace(titleSpan.innerText, '').trim();
                        if (descText) result.info['Content Descriptors'] = descText;
                    }}
                }}
            }}

            // Regular items: .collectionItem
            const collectionItems = doc.querySelectorAll('.collectionItem');
            const seenIds = new Set();
            for (const ci of collectionItems) {{
                try {{
                    const link = ci.querySelector('a[href*="filedetails"]');
                    if (!link) continue;
                    const href = link.href || '';
                    const idMatch = href.match(/id=(\\d+)/);
                    if (!idMatch || idMatch[1] === '{collection_id}') continue;
                    const pid = idMatch[1];
                    if (seenIds.has(pid)) continue;
                    seenIds.add(pid);

                    let title = '';
                    const te = ci.querySelector('.workshopItemTitle');
                    if (te) title = te.innerText.trim();

                    let previewUrl = '';
                    const img = ci.querySelector('.workshopItemPreviewImage');
                    if (img) previewUrl = img.src || '';

                    let author = '';
                    let authorUrl = '';
                    const authorEl = ci.querySelector('.workshopItemAuthorName a');
                    if (authorEl) {{
                        author = authorEl.innerText.trim();
                        authorUrl = authorEl.href || '';
                    }}

                    result.items.push({{
                        pubfileid: pid,
                        title: title || ('Item ' + pid),
                        preview_url: previewUrl,
                        author: author,
                        author_url: authorUrl,
                        is_collection: false
                    }});
                }} catch(e) {{}}
            }}

            // Related collections: .collections > .workshopItem
            const relatedItems = doc.querySelectorAll('.collections > .workshopItem');
            for (const ri of relatedItems) {{
                try {{
                    const link = ri.querySelector('a[href*="filedetails"]');
                    if (!link) continue;
                    const href = link.href || '';
                    const idMatch = href.match(/id=(\\d+)/);
                    if (!idMatch || idMatch[1] === '{collection_id}') continue;
                    const pid = idMatch[1];
                    if (seenIds.has(pid)) continue;
                    seenIds.add(pid);

                    let title = '';
                    const te = ri.querySelector('.workshopItemTitle');
                    if (te) title = te.innerText.trim();

                    let previewUrl = '';
                    const img = ri.querySelector('.workshopItemPreviewImage');
                    if (img) previewUrl = img.src || '';

                    let itemCount = 0;
                    const countEl = ri.querySelector('.workshopCollectionNumChildren');
                    if (countEl) {{
                        const cm = countEl.innerText.match(/(\\d+)/);
                        if (cm) itemCount = parseInt(cm[1]);
                    }}

                    result.related_collections.push({{
                        pubfileid: pid,
                        title: title || ('Collection ' + pid),
                        preview_url: previewUrl,
                        is_collection: true,
                        item_count: itemCount
                    }});
                }} catch(e) {{}}
            }}

            window.__collectionResult = result;
        }} catch (err) {{
            window.__collectionResult = {{ error: err.name === 'AbortError' ? 'Timeout' : err.message }};
        }}
        window.__collectionLoading = false;
    }})();
    """


def build_collection_contents_poll_script(request_id: int) -> str:
    return f"""
    (function() {{
        if (window.__collectionRequestId !== {request_id}) {{
            return {{ cancelled: true }};
        }}
        if (window.__collectionLoading === false) {{
            const result = window.__collectionResult;
            window.__collectionResult = null;
            return result;
        }}
        return null;
    }})();
    """