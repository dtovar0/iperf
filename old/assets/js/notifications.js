document.addEventListener('DOMContentLoaded', function() {
    const authToggle = document.getElementById('smtpAuthToggle');
    const authStatusText = document.getElementById('authStatusText');

    function updateAuthFields() {
        const isEnabled = authToggle.checked;
        const passInput = document.getElementById('smtpPass');
        
        if (passInput) {
            passInput.disabled = !isEnabled;
            if (!isEnabled) {
                passInput.classList.add('opacity-30', 'cursor-not-allowed');
            } else {
                passInput.classList.remove('opacity-30', 'cursor-not-allowed');
            }
        }
        if (authStatusText) {
            authStatusText.innerText = isEnabled ? 'Activo' : 'Inactivo';
            authStatusText.className = isEnabled 
                ? 'text-[12px] text-primary/60 font-bold uppercase tracking-widest' 
                : 'text-[12px] text-label/40 font-bold uppercase tracking-widest';
        }
    }

    if (authToggle) {
        authToggle.addEventListener('change', updateAuthFields);
        updateAuthFields(); // Initialize state
    }
    
    // Password Visibility Toggle
    const togglePassBtn = document.getElementById('togglePassVisibility');
    if (togglePassBtn) {
        togglePassBtn.addEventListener('click', function() {
            const passInput = document.getElementById('smtpPass');
            if (passInput) {
                passInput.type = passInput.type === 'password' ? 'text' : 'password';
            }
        });
    }

    // Initialize Editor Line Numbers
    if (document.getElementById('templateEditor')) {
        updateLineNumbers();
    }
});

function saveNotifications(containerId) {
    if (!validateNexusForm(containerId)) return;

    const data = {
        server: document.querySelector('#tab-panel-config input[data-validation-type="server"]')?.value,
        port: document.querySelector('#tab-panel-config input[data-validation-type="port"]')?.value,
        encryption: document.querySelector('#tab-panel-config select')?.value,
        auth_enabled: document.getElementById('smtpAuthToggle')?.checked,
        sender_name: document.getElementById('smtpName')?.value,
        username: document.getElementById('smtpUser')?.value,
        password: document.getElementById('smtpPass')?.value
    };

    showToast('Guardando configuración...', 'info');

    fetch('/notifications/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showToast(result.message, 'success');
        } else {
            showToast('Error: ' + result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error de conexión', 'error');
    });
}

function sendTestEmail() {
    const targetEmail = document.getElementById('testTargetEmail')?.value;
    
    if (!targetEmail) {
        showToast('Ingresa un correo destinatario', 'warning');
        return;
    }

    showToast('Iniciando transferencia SMTP...', 'info');

    fetch('/notifications/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_email: targetEmail })
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showToast(result.message, 'success');
            closeModal('modal-test-email');
        } else {
            showToast('Falla SMTP: ' + result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error crítico de conexión', 'error');
    });
}

/**
 * TEMPLATE EDITOR LOGIC
 */
let editorMode = 'text'; // 'text' or 'html'
let currentTemplateSlug = 'test'; // Track current active template

function syncPreview() {
    const preview = document.getElementById('livePreviewContent');
    const editor = document.getElementById('templateEditor');
    const subjectInput = document.getElementById('templateSubject');
    if (!preview || !editor) return;

    let val = editor.value;
    let subject = subjectInput ? subjectInput.value : "";

    // Simulate variable replacement with slightly dynamic data
    const mockReplacer = (text) => {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const dateStr = now.toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' });
        
        return text
            .replace(/{nombre}/g, 'DOMINGO TOVAR')
            .replace(/{usuario}/g, 'ADMIN_NEXUS')
            .replace(/{evento}/g, currentTemplateSlug.toUpperCase() + '_TRIGGERED')
            .replace(/{hora}/g, `${dateStr} @ ${timeStr}`)
            .replace(/{ip}/g, '189.210.45.' + Math.floor(Math.random() * 255))
            .replace(/{base_url}/g, 'https://nexus-portal.ai')
            .replace(/{url}/g, 'https://nexus-portal.ai/api/psx/detail/000420 [EJEMPLO]')
            .replace(/{correo}/g, 'security-ops@nexus-group.ai');
    };

    let mockedText = mockReplacer(val);
    let mockedSubject = mockReplacer(subject);

    // Update Preview Area (Body) based on mode
    if (editorMode === 'html') {
        preview.innerHTML = mockedText;
        preview.classList.remove('font-mono', 'text-sky-400/90');
        preview.classList.add('font-sans', 'text-[rgb(var(--color-ntf-text-editor))]/90');
    } else {
        preview.innerText = mockedText;
        preview.classList.remove('font-sans', 'text-[rgb(var(--color-ntf-text-editor))]/90');
        preview.classList.add('font-mono', 'text-sky-400/90');
    }
    
    // Update New High-Fidelity Subject Preview
    const liveSubject = document.getElementById('livePreviewSubject');
    if (liveSubject && mockedSubject) {
        liveSubject.innerText = mockedSubject;
    }
}

function updateLineNumbers() {
    const editor = document.getElementById('templateEditor');
    const gutter = document.getElementById('lineNumbers');
    if (!editor || !gutter) return;

    const lines = editor.value.split('\n').length;
    let html = '';
    for (let i = 1; i <= lines; i++) {
        html += `<span>${i}</span>`;
    }
    gutter.innerHTML = html;
}

function syncScroll() {
    const editor = document.getElementById('templateEditor');
    const gutter = document.getElementById('lineNumbers');
    if (!editor || !gutter) return;

    gutter.scrollTop = editor.scrollTop;
}

function toggleEditorMode() {
    const btn = document.getElementById('editorModeBtn');
    const label = document.getElementById('editorModeLabel');
    
    if (editorMode === 'text') {
        editorMode = 'html';
        label.textContent = 'MODO HTML';
        btn.classList.replace('bg-primary/20', 'bg-emerald-500/20');
        btn.classList.replace('text-primary', 'text-emerald-500');
        btn.classList.replace('border-primary/20', 'border-emerald-500/20');
        showToast('Modo HTML Activado (Renderizado de etiquetas)', 'info');
    } else {
        editorMode = 'text';
        label.textContent = 'TEXTO PLANO';
        btn.classList.replace('bg-emerald-500/20', 'bg-primary/20');
        btn.classList.replace('text-emerald-500', 'text-primary');
        btn.classList.replace('border-emerald-500/20', 'border-primary/20');
        showToast('Modo Texto Plano Activado', 'info');
    }
    
    syncPreview();
}

function insertVariable(variable) {
    const textarea = document.getElementById('templateEditor');
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    
    textarea.value = text.substring(0, start) + variable + text.substring(end);
    
    // Position cursor after inserted variable
    textarea.selectionStart = textarea.selectionEnd = start + variable.length;
    textarea.focus();
    
    // Sync the preview after insertion
    syncPreview();
    
    // Haptic/Visual feedback
    showToast(`Variable ${variable} insertada`, 'info');
}

function copyVariable(variable) {
    navigator.clipboard.writeText(variable).then(() => {
        showToast(`Copiado: ${variable}`, 'success');
    });
}


function loadTemplate(type) {
    currentTemplateSlug = type;
    const textarea = document.getElementById('templateEditor');
    const subjectInput = document.getElementById('templateSubject');
    if (!textarea || !subjectInput) return;

    // Primero intentamos cargar desde la Base de Datos
    fetch(`/notifications/templates/get/${type}`)
        .then(response => {
            if (!response.ok) throw new Error('Not found in DB');
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                textarea.value = data.template.body;
                subjectInput.value = data.template.subject;
                
                // Sincronizar el modo de renderizado (HTML/Texto)
                if (data.template.is_html && editorMode === 'text') {
                    toggleEditorMode();
                } else if (!data.template.is_html && editorMode === 'html') {
                    toggleEditorMode();
                }
                
                syncPreview();
                updateLineNumbers();
                showToast(`Cargada plantilla: ${type.toUpperCase()} (Base de Datos)`, 'info');
            }
        })
        .catch(() => {
            // Fallback a valores predeterminados de JS si no existe en DB
            let content = "";
            let subject = "";

            switch(type) {
                case 'test':
                    subject = "🟢 NEXUS: VERIFICACIÓN_SISTEMA";
                    content = "⚡ ALERTA DE PRUEBA\nEstado: SISTEMA_OK\nUsuario: {usuario}\nVerificación: EXITOSA";
                    break;
                case 'inicio':
                    subject = "🚀 NEXUS: ARRANQUE_INICIAL_{usuario}";
                    content = "🚀 ARRANQUE NEXUS\nOperación: INICIALIZANDO\nUsuario: {usuario}\nHora: {hora}\nBienvenido de vuelta a la matriz.";
                    break;
                case 'error':
                    subject = "🛑 NEXUS: ALERTA_SEGURIDAD_CRÍTICA";
                    content = "🛑 NEXUS CRÍTICO\nError: ACCESO_DENEGADO\nUsuario: {usuario}\nIP: {ip}\nAcción: BLOQUEO_SEGURIDAD";
                    break;
                case 'guardado':
                    subject = "💾 NEXUS: SINCRONIZACIÓN_DATOS";
                    content = "💾 SINCRONIZACIÓN NEXUS\nDestino: BASE_DATOS_CORE\nEstado: DATOS_GUARDADOS\nUsuario: {usuario}";
                    break;
                case 'terminado':
                    subject = "✅ NEXUS: PROCESO_FINALIZADO";
                    content = "✅ NEXUS COMPLETADO\nProceso: TAREA_FINALIZADA\nEjecutor: {usuario}\nEstado: ARCHIVOS_SINCRONIZADOS";
                    break;
                case 'usuario_creado':
                    subject = "👋 NEXUS: BIENVENIDO AL SISTEMA";
                    content = "👋 ¡Hola {nombre}!\nTu acceso al Nexus ha sido creado exitosamente.\nPortal: {base_url}\nBienvenido a la red.";
                    break;
            }

            if (content) {
                textarea.value = content;
                subjectInput.value = subject;
                syncPreview();
                updateLineNumbers();
                
                const friendlyNames = {
                    'test': 'TEST SYSTEM',
                    'guardado': 'TAREA NUEVA',
                    'inicio': 'INICIO TAREA',
                    'terminado': 'TAREA TERMINADA',
                    'usuario_creado': 'BIENVENIDA USUARIO',
                    'error': 'ERROR CRÍTICO'
                };
                
                showToast(`Cargada plantilla predeterminada: ${friendlyNames[type] || type.toUpperCase()}`, 'info');
            }
        });
}

function saveTemplate() {
    const textarea = document.getElementById('templateEditor');
    const subjectInput = document.getElementById('templateSubject');
    if (!textarea || !subjectInput) return;

    const payload = {
        slug: currentTemplateSlug,
        name: currentTemplateSlug.toUpperCase(),
        subject: subjectInput.value,
        body: textarea.value,
        is_html: editorMode === 'html'
    };

    fetch('/notifications/templates/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error de red al guardar plantilla', 'error');
    });
}

