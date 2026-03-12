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