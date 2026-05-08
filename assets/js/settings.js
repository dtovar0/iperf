/**
 * SETTINGS MODULE LOGIC
 * Manages identity mode toggling, live preview synchronization, and state recovery.
 */

let currentIdentityMode = 'icon'; // Global track for save logic

document.addEventListener('DOMContentLoaded', () => {
    initLivePreview();
    recoverState();
});

/**
 * Recovers state from the 'settings-state' data attributes
 */
function recoverState() {
    const stateEl = document.getElementById('settings-state');
    if (!stateEl) return;

    if (stateEl.dataset.configExists === 'true') {
        const identityType = stateEl.dataset.identityType;
        const savedIconPath = stateEl.dataset.portalIconPath;
        
        toggleIdentityMode(identityType);

        if (identityType === 'icon' && savedIconPath) {
            // INFALLIBLE FINGERPRINT HIGHLIGHTING
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = savedIconPath;
            const targetD = tempDiv.querySelector('path')?.getAttribute('d');
            
            if (targetD) {
                const iconButtons = document.querySelectorAll('#group-icon-picker button');
                iconButtons.forEach(btn => {
                    const btnPath = btn.querySelector('path')?.getAttribute('d');
                    if (btnPath === targetD) {
                        btn.classList.add('bg-primary/20', 'text-primary', 'shadow-lg', 'shadow-primary/20', 'z-10');
                        btn.classList.remove('text-primary/60');
                        btn.scrollIntoView({ behavior: 'auto', block: 'center' });
                    }
                });
            }
        }
    }
}

/**
 * Initializes all live preview listeners
 */
function initLivePreview() {
    const portalNameInput = document.getElementById('portal-name-input');
    const previewPortalName = document.getElementById('preview-portal-name');
    const previewPortalIcon = document.getElementById('preview-portal-icon');
    const imageInput = document.getElementById('portal-image-input');
    const iconButtons = document.querySelectorAll('#group-icon-picker button');

    if (!portalNameInput || !previewPortalName || !previewPortalIcon) return;

    // 1. Live Sync: Portal Name
    portalNameInput.addEventListener('input', (e) => {
        previewPortalName.textContent = e.target.value || 'Nexus Core AI';
        previewPortalName.classList.add('scale-105', 'text-primary');
        setTimeout(() => previewPortalName.classList.remove('scale-105', 'text-primary'), 200);
    });

    // 2. Live Sync: Icon Picker
    iconButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active state from all
            iconButtons.forEach(b => {
                b.classList.remove('bg-primary/20', 'text-primary', 'shadow-lg', 'shadow-primary/20', 'z-10');
                b.classList.add('text-primary/60');
            });

            // Add active state to selected
            btn.classList.add('bg-primary/20', 'text-primary', 'shadow-lg', 'shadow-primary/20', 'z-10');
            btn.classList.remove('text-primary/60');

            // Get the SVG from the button
            const svg = btn.querySelector('svg').outerHTML;
            previewPortalIcon.innerHTML = svg;
            
            animatePreviewBoard();
        });
    });

    // 3. Live Sync: Image Upload
    if (imageInput) {
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    previewPortalIcon.innerHTML = `<img src="${event.target.result}" class="w-full h-full object-cover">`;
                    animatePreviewBoard();
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 5. Live Sync: Banner Upload
    const bannerInput = document.getElementById('portal-banner-input');
    const bannerPreviewImg = document.getElementById('banner-preview-img');
    const bannerDropZone = document.getElementById('banner-drop-zone');

    if (bannerInput && bannerDropZone) {
        bannerInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    let img = document.getElementById('banner-preview-img');
                    if (!img) {
                        img = document.createElement('img');
                        img.id = 'banner-preview-img';
                        img.className = 'absolute inset-0 w-full h-full object-cover opacity-30';
                        bannerDropZone.prepend(img);
                    }
                    img.src = event.target.result;
                    showToast('Banner actualizado en vista previa', 'info');
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 4. Live Sync: Color Pickers
    const bgColorInput = document.getElementById('portal-bg-color');
    const textColorInput = document.getElementById('portal-text-color');

    if (bgColorInput) {
        bgColorInput.addEventListener('input', (e) => {
            previewPortalIcon.style.backgroundColor = e.target.value;
            const sidebarLogo = document.querySelector('#sidebar div.brand-text > div');
            if (sidebarLogo) sidebarLogo.style.backgroundColor = e.target.value;
        });
    }

    if (textColorInput) {
        textColorInput.addEventListener('input', (e) => {
            previewPortalIcon.style.color = e.target.value;
            const sidebarLogo = document.querySelector('#sidebar div.brand-text > div');
            if (sidebarLogo) sidebarLogo.style.color = e.target.value;
        });
    }
}

/**
 * Toggles between Icon selection and Image upload modes
 */
function toggleIdentityMode(mode) {
    currentIdentityMode = mode;
    const iconGroup = document.getElementById('group-icon-picker');
    const imageGroup = document.getElementById('group-image-upload');
    const btnIcon = document.getElementById('btn-toggle-icon');
    const btnImage = document.getElementById('btn-toggle-image');
    const imageInput = document.getElementById('portal-image-input');

    if (!iconGroup || !imageGroup || !btnIcon || !btnImage) return;

    if (mode === 'icon') {
        iconGroup.classList.remove('hidden');
        imageGroup.classList.add('hidden');
        if (imageInput) imageInput.disabled = true;
        btnIcon.className = "flex-grow py-4 bg-button-bg text-button-text shadow-lg shadow-button-bg/20 rounded-2xl text-xs font-black uppercase tracking-widest hover:opacity-90 transition-all active:scale-95 flex items-center justify-center gap-2";
        btnImage.className = "flex-grow py-4 bg-panel-fill border-2 border-button-bg/20 text-label rounded-2xl text-xs font-black uppercase tracking-widest hover:border-button-bg transition-all active:scale-95 flex items-center justify-center gap-2";
    } else {
        iconGroup.classList.add('hidden');
        imageGroup.classList.remove('hidden');
        if (imageInput) imageInput.disabled = false;
        btnImage.className = "flex-grow py-4 bg-button-bg text-button-text shadow-lg shadow-button-bg/20 rounded-2xl text-xs font-black uppercase tracking-widest hover:opacity-90 transition-all active:scale-95 flex items-center justify-center gap-2";
        btnIcon.className = "flex-grow py-4 bg-panel-fill border-2 border-button-bg/20 text-label rounded-2xl text-xs font-black uppercase tracking-widest hover:border-button-bg transition-all active:scale-95 flex items-center justify-center gap-2";
    }

    animatePreviewBoard();
}

/**
 * Kinetic feedback to the preview board
 */
function animatePreviewBoard() {
    const previewIconContainer = document.getElementById('preview-portal-icon')?.parentElement;
    if (previewIconContainer) {
        previewIconContainer.classList.add('animate-in', 'fade-in', 'zoom-in-95', 'duration-300');
        setTimeout(() => previewIconContainer.classList.remove('animate-in', 'fade-in', 'zoom-in-95', 'duration-300'), 300);
    }
}

/**
 * Updates default port based on engine selection
 */
function updateDefaultPort(engine) {
    const portInput = document.getElementById('db-port');
    if (!portInput) return;
    
    if (engine === 'mysql') {
        portInput.value = '3306';
        portInput.placeholder = '3306';
    } else if (engine === 'postgres') {
        portInput.value = '5432';
        portInput.placeholder = '5432';
    }
    
    portInput.parentElement.classList.add('scale-[1.02]');
    setTimeout(() => portInput.parentElement.classList.remove('scale-[1.02]'), 200);
}

/**
 * Saves settings to the backend
 */
function saveSettings(containerId) {
    const portalName = document.getElementById('portal-name-input')?.value;
    const previewBoard = document.getElementById('preview-portal-icon');
    const bannerImg = document.getElementById('banner-preview-img');
    
    let portalIconValue = '';
    if (currentIdentityMode === 'icon') {
        portalIconValue = previewBoard?.innerHTML; 
    } else {
        const img = previewBoard?.querySelector('img');
        portalIconValue = img ? img.src : ''; 
    }

    const data = {
        portal_name: portalName,
        portal_identity_type: currentIdentityMode,
        portal_icon: portalIconValue,
        portal_banner: bannerImg ? bannerImg.src : '',
        bg_color: document.getElementById('portal-bg-color')?.value,
        text_color: document.getElementById('portal-text-color')?.value
    };

    if (containerId === 'tab-panel-database') {
        showToast('Sincronizando...', 'info');
    }

    fetch('/settings/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        setTimeout(() => {
            if (result.status === 'success') {
                showToast(result.message, 'success', true);
            } else {
                showToast('Error: ' + result.message, 'error', true);
            }
        }, 500);
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showToast('Error de Conexión', 'error');
    });
}

/**
 * EXPORT SYSTEM CONFIGURATION
 * Generates a master ZIP package for full portal restoration.
 */
function exportSystemConfig() {
    showToast('Generando paquete maestro...', 'info');
    
    fetch('/settings/export')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            const dateStr = new Date().toISOString().split('T')[0];
            
            a.href = url;
            a.download = `nexus_backup_${dateStr}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showToast('Respaldo ZIP generado con éxito', 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showToast('Error de conexión al exportar', 'error');
        });
}

/**
 * IMPORT SYSTEM CONFIGURATION
 * Uploads and applies a master ZIP package.
 */
function importSystemConfig(input) {
    const file = input.files[0];
    if (!file) return;

    // 1. Validation: MUST BE ZIP
    if (!file.name.toLowerCase().endsWith('.zip')) {
        showToast('Archivo Inválido: Solo se permiten paquetes .zip', 'error');
        input.value = '';
        return;
    }

    // 2. Open Luxury Confirmation Modal
    openModal('confirmImportModal');

    // 3. Setup Action Listener
    const confirmBtn = document.getElementById('confirmBtnAction');
    
    // Use a fresh cloned button to clear previous listeners (prevent accumulation)
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    newConfirmBtn.addEventListener('click', () => {
        closeModal('confirmImportModal');
        showToast('Procesando paquete ZIP...', 'info');
        
        const formData = new FormData();
        formData.append('file', file);

        fetch('/settings/import', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                showToast(result.message, 'success', true);
                setTimeout(() => window.location.reload(), 2000);
            } else {
                showToast('Error: ' + result.message, 'error');
            }
            input.value = '';
        })
        .catch(error => {
            console.error('Import error:', error);
            showToast('Error crítico al procesar el ZIP', 'error');
            input.value = '';
        });
    });
}
/**
 * INITIALIZE DROP ZONE LOGIC
 */
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('import-drop-zone');
    const fileInput = document.getElementById('importFile');

    if (dropZone && fileInput) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('border-violet-500', 'bg-violet-500/10', 'scale-[1.02]');
                dropZone.classList.remove('border-panel-border', 'bg-surface-container/20');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-violet-500', 'bg-violet-500/10', 'scale-[1.02]');
                dropZone.classList.add('border-panel-border', 'bg-surface-container/20');
            }, false);
        });

        // Handle dropped files
        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                // Manually trigger the input change logic
                fileInput.files = files;
                importSystemConfig(fileInput);
            }
        }, false);
    }
});
