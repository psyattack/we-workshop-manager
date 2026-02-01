(function() {
    'use strict';
    
    function applyCustomStyles(bgUrl) {
        document.body.classList.add("apphub_blue");
        
        const style = document.createElement('style');
        style.innerHTML = `
            ::-webkit-scrollbar {
                width: 8px;
                background: transparent;
            }
            ::-webkit-scrollbar-track {
                background: transparent;
            }
            ::-webkit-scrollbar-thumb {
                background-color: rgba(0, 0, 0, 0);
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background-color: rgba(78, 140, 255, 0.3);
            }
            body.apphub_blue::before {
                content: "";
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url("${bgUrl}") no-repeat center center;
                background-size: cover;
                z-index: -1;
            }
            .workshop_header {
                background: transparent !important;
                background-repeat: no-repeat;
                background-position: center center;
                background-size: cover;
                height: 45px;
                right: 327px;
                background-color: transparent !important;
                box-shadow: 0 0 0px 0 #000000;
            }
            .workshop_browse_menu_area {
                background: transparent !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    function removeElements() {
        const selectors = [
            '#global_header',
            '.apphub_HomeHeaderContent',
            '#footer',
            '#footer_spacer',
            '#NotLoggedInWarning.modal_frame',
            '.browseAppDetails',
            '#rightContents > div > div:nth-child(1)',
            '.workshop_browse_tab.drop.active',
            '#SaveQueryButton',
            '.sharedfiles_header_ctn',
            '.sectionTab.screenshots',
            '.sectionTab.images',
            '.sectionTab.videos',
            '.sectionTab.merchandise',
            '.sectionTab.guides',
            '.searchedTermsContainer',
            '#workshop_item_hover'
        ];
        
        selectors.forEach(selector => {
            const el = document.querySelector(selector);
            if (el) el.remove();
        });
        
        const selectorsAll = [
            '.workshopItemSubscriptionControls.aspectratio_square',
            '.workshop_browse_tab',
            '.ugc_options'
        ];
        
        selectorsAll.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => el.remove());
        });

        const elements = document.querySelectorAll('.ugc.has_adult_content.ugc_show_warning_image');
        elements.forEach(el => {
            el.className = 'ugc';
        });
        
        const rightSectionHolder = document.querySelectorAll(".rightSectionHolder");
        if (rightSectionHolder.length === 4) {
            rightSectionHolder[0].remove();
            rightSectionHolder[1].remove();
            rightSectionHolder[3].remove();
        } else if (rightSectionHolder.length === 3) {
            rightSectionHolder[0].remove();
            rightSectionHolder[1].remove();
        }
    }
    
    function addCustomButtons() {
        const items = document.querySelectorAll('.workshopBrowseItems > *');
        
        items.forEach(item => {
            const link = item.querySelector('a');
            if (!link || item.querySelector('.copy-link-btn')) return;
            
            const pubfileid = link.href.match(/(\d{8,10})/)?.[1];
            if (!pubfileid) return;
            
            const statusBtn = createButton('🔗 Status', 'copy-link-btn', pubfileid);
            statusBtn.onclick = function() {
                const info = {
                    pubfileid: pubfileid,
                    text: this.innerText
                };
                setTimeout(() => {
                    this.innerText = "🔗 Status";
                }, 2000);
                console.log("CHECK_STATUS:" + JSON.stringify(info));
            };
            
            const infoBtn = createButton('👁️‍🗨️ Info', 'fancy-tooltip');
            setupInfoButton(infoBtn, pubfileid);
            
            item.appendChild(statusBtn);
            item.appendChild(infoBtn);
        });
    }
    
    function createButton(text, className, dataAttr = null) {
        const btn = document.createElement('button');
        btn.innerText = text;
        btn.className = className;
        if (dataAttr) btn.setAttribute('data-pubfileid', dataAttr);
        
        btn.style.cssText = `
            margin-right: 5px;
            margin-top: 6px;
            padding: 6px 12px;
            font-size: 13px;
            background: #4e8cff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.3s;
            outline: none;
            user-select: none;
        `;
        
        btn.onmouseenter = () => btn.style.background = '#6ea4ff';
        btn.onmouseleave = () => btn.style.background = '#4e8cff';
        
        return btn;
    }
    
    function setupInfoButton(btn, pubfileid) {
        addTooltipStyles();
        
        let tooltipDiv = null;
        
        btn.onclick = async function() {
            try {
                const response = await fetch(`https://steamcommunity.com/sharedfiles/filedetails/?id=${pubfileid}`);
                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                
                const infoBlock = doc.querySelector('#mainContents .col_right.responsive_local_menu');
                if (infoBlock) {
                    const infoText = infoBlock.innerText.trim().replace(/\n{2,}/g, '\n');
                    showTooltip(btn, formatInfo(infoText));
                } else {
                    showTooltip(btn, "Hidden content :(");
                }
            } catch (err) {
                console.error("Error fetching info:", err);
            }
        };
        
        btn.addEventListener("mouseleave", hideTooltip);
        
        function showTooltip(el, text) {
            if (tooltipDiv) tooltipDiv.remove();
            
            const rect = el.getBoundingClientRect();
            tooltipDiv = document.createElement("div");
            tooltipDiv.className = "custom-tooltip";
            tooltipDiv.innerText = text;
            document.body.appendChild(tooltipDiv);
            
            const tooltipRect = tooltipDiv.getBoundingClientRect();
            let top = rect.top;
            let left = rect.right + 10;
            
            if (top + tooltipRect.height > window.innerHeight) {
                top = window.innerHeight - tooltipRect.height - 5;
            }
            
            tooltipDiv.style.top = `${top}px`;
            tooltipDiv.style.left = `${left}px`;
            tooltipDiv.style.opacity = "1";
        }
        
        function hideTooltip() {
            if (tooltipDiv) {
                tooltipDiv.remove();
                tooltipDiv = null;
            }
        }
    }
    
    function addTooltipStyles() {
        if (document.getElementById("custom-tooltip-style")) return;
        
        const style = document.createElement("style");
        style.id = "custom-tooltip-style";
        style.textContent = `
            .custom-tooltip {
                position: fixed;
                background: #222;
                color: #fff;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 13px;
                white-space: pre-line;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                z-index: 2147483647;
                max-width: 400px;
                width: max-content;
                word-break: break-word;
                text-align: left;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.15s ease;
            }
        `;
        document.head.appendChild(style);
    }

    function formatInfo(text) {
        text = text.replace(/[\t\n]+/g, ' ').replace(/\s+/g, ' ').trim();
        const results = [];
        
        // File Size
        const fileSizeMatch = text.match(/File Size.*?(\d+(\.\d+)?)\s*(GB|MB|KB)/i);
        if (fileSizeMatch) {
            results.push(`File Size: ${fileSizeMatch[1]} ${fileSizeMatch[3].toUpperCase()}`);
        }
        
        // Posted
        const postedMatch = text.match(/Posted.*?(\d{1,2}\s+\w{3},?\s*(\d{4})?\s*@\s*\d{1,2}:\d{2}(am|pm)?)/i);
        if (postedMatch) {
            results.push(`Posted: ${postedMatch[1]}`);
        }
        
        // Updated
        const updatedMatches = [...text.matchAll(/(\d{1,2}\s+\w{3},?\s*(\d{4})?\s*@\s*\d{1,2}:\d{2}(am|pm)?)/gi)];
        if (updatedMatches.length >= 2) {
            results.push(`Updated: ${updatedMatches[1][1]}`);
        }
        
        results.push('');
        
        // Other tags
        const tags = {
            "Miscellaneous": /Miscellaneous:\s*(.*?)(?=Type:|Age Rating:|Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Type": /Type:\s*(.*?)(?=Age Rating:|Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Age Rating": /Age Rating:\s*(.*?)(?=Genre:|Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Genre": /Genre:\s*(.*?)(?=Resolution:|Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Resolution": /Resolution:\s*(.*?)(?=Category:|Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Category": /Category:\s*(.*?)(?=Content Descriptors:|Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Content Descriptors": /Content Descriptors:\s*(.*?)(?=Script Type:|Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Script Type": /Script Type:\s*(.*?)(?=Asset Type:|Asset Genre:|File Size|Posted|$)/i,
            "Asset Type": /Asset Type:\s*(.*?)(?=Asset Genre:|File Size|Posted|$)/i,
            "Asset Genre": /Asset Genre:\s*(.*?)(?=File Size|Posted|$)/i
        };
        
        for (const [key, regex] of Object.entries(tags)) {
            const match = text.match(regex);
            if (match && match[1]) {
                results.push(`${key}: ${match[1].trim()}`);
            }
        }
        
        return results.join('\n');
    }
    
    // Init
    try {
        const bgUrl = window.CUSTOM_BG_URL || '';
        applyCustomStyles(bgUrl);
        removeElements();
        addCustomButtons();
        return true;
    } catch (e) {
        console.error("Workshop browse script failed:", e);
        return false;
    }
})();
