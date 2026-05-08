/**
 * DESIGN MODULE LOGIC
 * Nexus Premium Design Studio Ultimate
 */

function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `${r} ${g} ${b}`;
}

function updateTokenValue(token, hexValue) {
    const rgbValue = hexToRgb(hexValue);
    document.documentElement.style.setProperty(token, rgbValue);
    // Force update non-rgb tokens if needed
    if(token === '--color-panel-fill' || token === '--color-input-bg') {
        document.documentElement.style.setProperty(token + '-direct', hexValue);
    }
}

function updatePixelToken(token, value) {
    document.documentElement.style.setProperty(token, `${value}px`);
}

function switchDesignTab(tabId) {
    // Hide all panels
    document.querySelectorAll('.dt-panel').forEach(p => p.classList.add('hidden'));
    // Remove active styles from all triggers
    document.querySelectorAll('.dt-trigger').forEach(t => {
        t.classList.remove('bg-primary', 'text-white', 'shadow-lg', 'shadow-primary/20');
        t.classList.add('text-label/60');
    });

    // Show target panel
    const panel = document.getElementById('dt-panel-' + tabId);
    if (panel) panel.classList.remove('hidden');
    
    // Set active trigger
    const activeTrigger = document.getElementById('dt-trigger-' + tabId);
    if (activeTrigger) {
        activeTrigger.classList.remove('text-label/60');
        activeTrigger.classList.add('bg-primary', 'text-white', 'shadow-lg', 'shadow-primary/20');
    }
}

async function saveDesign() {
    showToast('Analizando Configuración...', 'info');
    
    // In a real scenario, this would gather all token values and send to server.
    // For now, mimicking the demo behavior.
    setTimeout(() => showToast('Visión de Diseño Sincronizada', 'success'), 1500);
}
