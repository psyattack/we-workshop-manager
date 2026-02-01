(function() {
    'use strict';
    
    const USERNAME = window.STEAM_USERNAME || '';
    const PASSWORD = window.STEAM_PASSWORD || '';
    
    if (!USERNAME || !PASSWORD) {
        console.error("Steam credentials not provided");
        return;
    }

    const blocker = document.createElement('div');
    blocker.id = 'input-blocker';
    blocker.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 99999;
        background-color: rgba(0, 0, 0, 0);
        pointer-events: all;
    `;
    
    function setNativeValue(input, value) {
        const lastValue = input.value;
        input.value = value;
        
        const event = new Event('input', { bubbles: true });
        const tracker = input._valueTracker;
        if (tracker) tracker.setValue(lastValue);
        input.dispatchEvent(event);
    }

    if (window.location.href.includes("/login")) {
        document.body.appendChild(blocker);
        
        const interval = setInterval(() => {
            const loginInput = document.querySelector('input[type="text"]');
            const passwordInput = document.querySelector('input[type="password"]');
            const submitButton = document.querySelector('button[type="submit"]');
            
            if (loginInput && passwordInput && submitButton) {
                clearInterval(interval);
                
                loginInput.style.filter = 'blur(4px)';
                passwordInput.style.filter = 'blur(4px)';

                setNativeValue(loginInput, USERNAME);
                setNativeValue(passwordInput, PASSWORD);
                
                setTimeout(() => {
                    submitButton.click();
                }, 1000);
            }
        }, 100);
        
    } else {
        const loginLink = document.querySelector('a.global_action_link[href*="login"]');
        if (loginLink) {
            document.body.appendChild(blocker);
            loginLink.click();
        }
    }
})();