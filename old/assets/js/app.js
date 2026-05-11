/**
 * NEXUS CORE APP LOGIC
 * Framework-compliant script separation.
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Auth Error Handler (Shake effect for login form)
    const errorMarker = document.querySelector('.auth-trigger-error');
    const loginForm = document.getElementById('loginForm');
    
    if (errorMarker && loginForm) {
        loginForm.classList.add('auth-error');
        setTimeout(() => {
            loginForm.classList.remove('auth-error');
        }, 1000);
    }

    // 2. Global Brand Identity Sync
    const body = document.body;
    if (body.dataset.brandBg || body.dataset.brandText) {
        const root = document.documentElement;
        if (body.dataset.brandBg) root.style.setProperty('--color-brand-identity-bg', body.dataset.brandBg);
        if (body.dataset.brandText) root.style.setProperty('--color-brand-identity-text', body.dataset.brandText);
    }

    // 3. Login/Logout Specific Brand Identity
    const brandIcon = document.querySelector('.brand-icon-container');
    if (brandIcon) {
        const bgColor = brandIcon.dataset.bgColor;
        const textColor = brandIcon.dataset.textColor;
        
        if (bgColor) {
            brandIcon.style.backgroundColor = bgColor;
            brandIcon.style.boxShadow = `0 0 40px ${bgColor}60`;
        }
        if (textColor) {
            brandIcon.style.color = textColor;
        }
    }

    // 4. Logout Countdown Logic
    const logoutConfig = document.getElementById('logout-config');
    if (logoutConfig) {
        let count = 5;
        const countdownEl = document.getElementById('countdown');
        const progressEl = document.getElementById('progress');
        const loginUrl = logoutConfig.dataset.loginUrl;
        const dashArray = 377;

        if (countdownEl && progressEl) {
            const timer = setInterval(() => {
                count--;
                countdownEl.textContent = count;
                
                // Update progress circle
                const offset = dashArray - (dashArray * (count / 5));
                progressEl.style.strokeDashoffset = offset;

                if (count <= 0) {
                    clearInterval(timer);
                    if (loginUrl) window.location.href = loginUrl;
                }
            }, 1000);
        }
    }
});
