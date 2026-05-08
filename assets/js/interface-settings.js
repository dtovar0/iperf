/**
 * INTERFACE SETTINGS MODULE
 * Manages global UI preferences stored in localStorage.
 */

window.nexusSettings = {
    notifications: true,
    emailNotifications: true,
    refreshInterval: 60, // seconds
    tourEnabled: true,
    initialized: false
};

document.addEventListener('DOMContentLoaded', () => {
    loadInterfaceSettings();
    initSettingsUI();
});

/**
 * Loads settings from localStorage or defaults
 */
function loadInterfaceSettings() {
    const saved = localStorage.getItem('nexus_interface_settings');
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            if (parsed.refreshInterval) {
                parsed.refreshInterval = parseInt(parsed.refreshInterval);
            }
            // Merge but keep internal defaults if missing
            window.nexusSettings = { ...window.nexusSettings, ...parsed };
        } catch (e) {
            console.error('Error parsing settings:', e);
        }
    }

    // Recover from Database
    const body = document.body;
    if (body.dataset.prefNotifications !== undefined) {
        window.nexusSettings.notifications = body.dataset.prefNotifications === 'true';
        window.nexusSettings.emailNotifications = body.dataset.prefEmail === 'true';
        window.nexusSettings.refreshInterval = parseInt(body.dataset.prefRefresh) || 60;
        window.nexusSettings.tourEnabled = body.dataset.prefTour === 'true';
        
        localStorage.setItem('nexus_interface_settings', JSON.stringify(window.nexusSettings));
    }
    
    window.nexusSettings.initialized = true;
    startGlobalPolling();
}

/**
 * Initializes the Modal UI interaction
 */
function initSettingsUI() {
    const settingsBtn = document.getElementById('settingsBtn');
    const saveBtn = document.getElementById('saveSettingsBtn');
    const refreshRange = document.getElementById('settingRefreshRange');
    const refreshDisplay = document.getElementById('refreshValueDisplay');
    const notifyToggle = document.getElementById('settingNotifyToggle');
    const emailNotifyToggle = document.getElementById('settingEmailNotifyToggle');
    const tourToggle = document.getElementById('settingTourToggle');

    if (!settingsBtn) return;

    settingsBtn.addEventListener('click', () => {
        if (typeof openModal === 'function') {
            openModal('settingsModal');
            
            setTimeout(() => {
                const $range = $('#settingRefreshRange');
                const $display = $('#refreshValueDisplay');
                const $notif = $('#settingNotifyToggle');
                const $email = $('#settingEmailNotifyToggle');
                const $tour = $('#settingTourToggle');
                const val = window.nexusSettings.refreshInterval;

                if ($range.length) {
                    $range.val(val).attr('value', val);
                    $range.trigger('input').trigger('change');
                }
                if ($display.length) $display.text(val + 's');
                if ($notif.length) $notif.prop('checked', window.nexusSettings.notifications);
                if ($email.length) $email.prop('checked', window.nexusSettings.emailNotifications);
                if ($tour.length) $tour.prop('checked', window.nexusSettings.tourEnabled);
            }, 50);
        }
    });

    if (refreshRange && refreshDisplay) {
        refreshRange.addEventListener('input', (e) => {
            refreshDisplay.textContent = e.target.value + 's';
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const newSettings = {
                notifications: notifyToggle ? notifyToggle.checked : true,
                emailNotifications: emailNotifyToggle ? emailNotifyToggle.checked : true,
                refreshInterval: refreshRange ? parseInt(refreshRange.value) : 60,
                tourEnabled: tourToggle ? tourToggle.checked : true
            };

            const changedInterval = newSettings.refreshInterval !== window.nexusSettings.refreshInterval;
            window.nexusSettings = { ...window.nexusSettings, ...newSettings };
            
            localStorage.setItem('nexus_interface_settings', JSON.stringify(window.nexusSettings));

            fetch('/auth/preferences/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    notifications: newSettings.notifications,
                    email_notifications: newSettings.emailNotifications,
                    refresh_interval: newSettings.refreshInterval,
                    tour_enabled: newSettings.tourEnabled
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    if (typeof showToast === 'function') {
                        showToast('Configuración sincronizada', 'success');
                    }
                    document.dispatchEvent(new CustomEvent('nexus:settingsUpdated', { detail: window.nexusSettings }));
                }
            })
            .catch(err => console.error('Error syncing preferences:', err));

            if (changedInterval) startGlobalPolling();
            if (typeof closeModal === 'function') closeModal('settingsModal');
        });
    }
}

function startGlobalPolling() {
    window.nexusPollers = window.nexusPollers || [];
    window.nexusPollers.forEach(p => clearInterval(p.id));
    window.nexusPollers = [];

    const intervalMs = window.nexusSettings.refreshInterval * 1000;
    const tableTarget = $('#psxDataTable');
    if (tableTarget.length && $.fn.dataTable.isDataTable('#psxDataTable')) {
        const psxTable = tableTarget.DataTable();
        const id = setInterval(() => {
            psxTable.ajax.reload(null, false);
        }, intervalMs);
        window.nexusPollers.push({ name: 'psx_table', id });
    }
}

window.canNotify = function() {
    return window.nexusSettings.notifications;
};

document.addEventListener('nexus:viewChanged', startGlobalPolling);
