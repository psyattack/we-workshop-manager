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
            #mainContents {
                top: 15px;
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
            '#ig_bottom > div.breadcrumbs',
            '#ItemControls',
            '#profileBlock > div > div.game_area_purchase_margin > div > h1 > span',
            '#profileBlock > div > div.game_area_purchase_margin > div > h1 > br',
            '#rightContents > div > div:nth-child(2)',
            '.friendBlockLinkOverlay',
            '.sectionTab.discussions',
            '.sectionTab.comments',
            '.breadcrumbs',
            '#mainContentsCollectionTop',
            '.subscribeCollection',
            '.workshopItemDescriptionTitle'
        ];
        
        selectors.forEach(selector => {
            const el = document.querySelector(selector);
            if (el) el.remove();
        });
        
        const selectorsAll = [
            '.subscriptionControls'
        ];
        
        selectorsAll.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => el.remove());
        });
        
        const detailBoxes = document.querySelectorAll(".detailBox");
        if (detailBoxes.length === 3) {
            detailBoxes[2].style.pointerEvents = "none";
        } else if (detailBoxes.length === 4) {
            detailBoxes[3].style.pointerEvents = "none";
        }
        
        const commentPagination = document.querySelector(".commentthread_pagelinks_ctn");
        if (commentPagination) {
            commentPagination.style.pointerEvents = "auto";
            commentPagination.style.zIndex = "9999";
        }
    }
    
    function hookSubscribeButton(customEvent, buttonText) {
        const btn = document.querySelector("#SubscribeItemOptionAdd.subscribeOption.subscribe.selected");
        
        if (btn && !btn.hasAttribute("data-hooked")) {
            btn.setAttribute("data-hooked", "true");
            
            btn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log(customEvent);
            };
            
            btn.innerText = buttonText;
        }
    }
    
    // Init
    try {
        const bgUrl = window.CUSTOM_BG_URL || '';
        const customEvent = window.CUSTOM_EVENT || 'CUSTOM_EVENT:' + window.location.href;
        const buttonText = window.BUTTON_TEXT || 'Get & Install';
        
        applyCustomStyles(bgUrl);
        removeElements();
        hookSubscribeButton(customEvent, buttonText);
        
        return true;
    } catch (e) {
        console.error("Workshop details script failed:", e);
        return false;
    }
})();
