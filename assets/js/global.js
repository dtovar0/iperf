// 0. Fetch Interceptor for CSRF Protection
(function() {
    const originalFetch = window.fetch;
    window.fetch = function() {
        const args = Array.from(arguments);
        let [url, config] = args;
        
        if (config && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method?.toUpperCase())) {
            config.headers = config.headers || {};
            
            // Avoid double setting if already present
            if (!config.headers['X-CSRFToken'] && typeof CSRF_TOKEN !== 'undefined') {
                config.headers['X-CSRFToken'] = CSRF_TOKEN;
            }
        }
        
        return originalFetch.apply(this, args);
    };

    // Global jQuery setup if available
    window.addEventListener('load', () => {
        if (window.jQuery) {
            window.jQuery.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        if (typeof CSRF_TOKEN !== 'undefined') {
                            xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
                        }
                    }
                }
            });
        }
    });
})();

// 1. Theme Engine — 6-Theme Cycling System
const NEXUS_THEMES = [
    { name: 'Sapphire',       'class': 'light',              isDark: false },
    { name: 'Midnight Ocean',  'class': 'dark',               isDark: true  },
    { name: 'Emerald Forest',  'class': 'theme-emerald-light', isDark: false },
    { name: 'Obsidian',        'class': 'theme-obsidian-dark', isDark: true  },
    { name: 'Rose Quartz',     'class': 'theme-rose-light',   isDark: false },
    { name: 'Cyber Violet',    'class': 'theme-violet-dark',  isDark: true  }
];

function applyNexusTheme(index) {
    const html = document.documentElement;
    const allClasses = NEXUS_THEMES.map(t => t['class']);
    html.classList.remove('dark', 'light', ...allClasses);

    const theme = NEXUS_THEMES[index];
    html.classList.add(theme['class']);
    if (theme.isDark) html.classList.add('dark');
    else html.classList.add('light');

    localStorage.setItem('nexusThemeIndex', index);
}

// Immediate Apply (Prevent Flickering)
(() => {
    const html = document.documentElement;
    const storedIndex = parseInt(localStorage.getItem('nexusThemeIndex'));
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    const isMobile = window.innerWidth < 1024;
    
    if (!isNaN(storedIndex) && storedIndex >= 0 && storedIndex < NEXUS_THEMES.length) {
        applyNexusTheme(storedIndex);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        applyNexusTheme(1);
    } else {
        applyNexusTheme(0);
    }

    if (isCollapsed && !isMobile) {
        html.classList.add('sidebar-is-collapsed');
    }
})();


// 2. DOM Interaction Logic
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const html = document.documentElement;
    
    // Sidebar State Sync (Apply local styling if global class is present)
    if (sidebar && html.classList.contains('sidebar-is-collapsed')) {
        sidebar.classList.remove('w-64', 'min-w-64');
        sidebar.classList.add('w-16', 'min-w-16', 'is-collapsed');
        document.querySelectorAll('.sidebar-text').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.sidebar-divider').forEach(el => el.classList.remove('hidden'));
    }

    // Dynamic Brand Color Injection (Sync with DB)
    const brandBg = document.body.getAttribute('data-brand-bg');
    const brandText = document.body.getAttribute('data-brand-text');
    if (brandBg) html.style.setProperty('--color-brand-identity-bg', brandBg);
    if (brandText) html.style.setProperty('--color-brand-identity-text', brandText);

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            const isMobile = window.innerWidth < 1024;
            
            if (isMobile) {
                sidebar.classList.toggle('-translate-x-full');
            } else {
                sidebar.classList.toggle('w-64');
                sidebar.classList.toggle('min-w-64');
                sidebar.classList.toggle('w-16');
                sidebar.classList.toggle('min-w-16');
                sidebar.classList.toggle('is-collapsed');
                
                document.querySelectorAll('.sidebar-text').forEach(el => {
                    el.classList.toggle('hidden');
                });
                document.querySelectorAll('.sidebar-divider').forEach(el => {
                    el.classList.toggle('hidden');
                });

                const isCollapsed = sidebar.classList.contains('is-collapsed');
                localStorage.setItem('sidebarCollapsed', isCollapsed);
                
                // Keep HTML class in sync
                if (isCollapsed) html.classList.add('sidebar-is-collapsed');
                else html.classList.remove('sidebar-is-collapsed');
            }
        });
    }

    // 3. Theme Toggle Listener — 6-Theme Cycler
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = parseInt(localStorage.getItem('nexusThemeIndex')) || 0;
            const next = (current + 1) % NEXUS_THEMES.length;
            applyNexusTheme(next);
            
            if (typeof showToast === 'function') {
                const t = NEXUS_THEMES[next];
                const icon = t.isDark ? '🌙' : '☀️';
                showToast(`${icon} ${t.name}`, 'info');
            }
        });
    }

    // 4. Global System Search Dispatcher - Deep History Mode
    const systemSearch = document.getElementById('systemSearch');
    const deepSearchBtn = document.getElementById('deepHistorySearchBtn');

    if (systemSearch && deepSearchBtn) {
        deepSearchBtn.addEventListener('click', async () => {
            const query = systemSearch.value.trim();
            if (!query) {
                showToast('Ingresa un término para buscar en historial', 'info');
                return;
            }

            deepSearchBtn.classList.add('animate-pulse', 'text-primary');
            const searchTitle = document.getElementById('searchQueryDisplay');
            if (searchTitle) searchTitle.textContent = `Resultados para: "${query}"`;
                
            try {
                const response = await fetch(`/api/psx/history/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                const tbody = document.getElementById('globalSearchResultsBody');
                const noResults = document.getElementById('noHistoryResults');
                
                if (data.status === 'success' && data.results.length > 0) {
                    noResults.classList.add('hidden');
                    tbody.innerHTML = data.results.map(r => `
                        <tr class="hover:bg-primary/5 transition-colors group">
                            <td class="px-6 py-4 text-[12px] font-bold text-label uppercase tracking-tighter">#${r.task_id}</td>
                            <td class="px-6 py-4 text-[12px] font-bold text-label/80">${r.routing_label || '-'}</td>
                            <td class="px-6 py-4 text-center">
                                <span class="px-2 py-0.5 rounded-md text-[12px] font-black uppercase
                                    ${r.estado === 'OK' ? 'bg-emerald-500/10 text-emerald-500' : 
                                      r.estado === 'FAIL' ? 'bg-rose-500/10 text-rose-500' : 
                                      r.estado === 'DUP' ? 'bg-amber-500/10 text-amber-500' : 
                                      'bg-slate-500/10 text-slate-500'}">
                                    ${r.estado || 'UNKNOWN'}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-[12px] font-bold text-label/60">${r.fecha ? new Date(r.fecha).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                        </tr>
                    `).join('');
                    openModal('globalSearchModal');
                } else {
                    if (tbody) tbody.innerHTML = '';
                    if (noResults) noResults.classList.remove('hidden');
                    openModal('globalSearchModal');
                }
            } catch (error) {
                console.error('History Search Error:', error);
                showToast('Error al buscar en el historial', 'error');
            } finally {
                deepSearchBtn.classList.remove('animate-pulse', 'text-primary');
            }
        });

        // Clear search on focus loss if empty
        systemSearch.addEventListener('blur', function() {
            if (this.value === '' && window.activeNexusTable) {
                window.activeNexusTable.search('').draw();
            }
        });

        // Trigger search on Enter key
        systemSearch.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                deepSearchBtn.click();
            }
        });
    }

    // 5. Global Search Keyboard Shortcut (/)
    document.addEventListener('keydown', (e) => {
        // Prevent trigger if focused on an input field
        const isTyping = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable;
        
        if (e.key === '/' && !isTyping) {
            e.preventDefault();
            const searchInput = document.getElementById('systemSearch');
            if (searchInput) {
                searchInput.focus();
                // feedback effect
                searchInput.parentElement.classList.add('ring-2', 'ring-primary/40');
                setTimeout(() => searchInput.parentElement.classList.remove('ring-2', 'ring-primary/40'), 300);
            }
        }
    });

    // 6. Initialize Premium Selects
    initNexusSelects();
});

/**
 * NEXUS LUXURY SELECT ENGINE
 * Transforms native selects into premium UI components while maintaining data integrity.
 */
function initNexusSelects() {
    // Only target visible selects that haven't been processed
    document.querySelectorAll('select:not(.nx-hidden-native)').forEach(select => {
        // Skip if inside a template or special container that shouldn't be touched yet
        if (select.closest('.nx-select-wrapper')) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'nx-select-wrapper';
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);

        const trigger = document.createElement('div');
        trigger.className = 'nx-select-trigger';
        trigger.innerHTML = `
            <span class="nx-select-text">${select.options[select.selectedIndex]?.text || 'Seleccione...'}</span>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19.5 8.25l-7.5 7.5-7.5-7.5"></path></svg>
        `;

        const dropdown = document.createElement('div');
        dropdown.className = 'nx-select-dropdown';
        
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'nx-select-options custom-scrollbar';

        Array.from(select.options).forEach((option, index) => {
            if (option.disabled && index === 0) return; // Skip placeholder if needed

            const optEl = document.createElement('div');
            optEl.className = `nx-select-option ${option.selected ? 'is-selected' : ''}`;
            optEl.dataset.value = option.value;
            optEl.innerText = option.text;

            optEl.addEventListener('click', (e) => {
                e.stopPropagation();
                select.value = option.value;
                trigger.querySelector('.nx-select-text').innerText = option.text;
                
                // Update active state
                dropdown.querySelectorAll('.nx-select-option').forEach(el => el.classList.remove('is-selected'));
                optEl.classList.add('is-selected');

                // Trigger native change event
                select.dispatchEvent(new Event('change', { bubbles: true }));
                
                wrapper.classList.remove('is-open');
            });

            optionsContainer.appendChild(optEl);
        });

        dropdown.appendChild(optionsContainer);
        wrapper.appendChild(trigger);
        wrapper.appendChild(dropdown);

        // Hide native
        select.classList.add('nx-hidden-native');

        // Toggle dropdown
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            // Close others
            document.querySelectorAll('.nx-select-wrapper').forEach(w => {
                if (w !== wrapper) w.classList.remove('is-open');
            });
            wrapper.classList.toggle('is-open');
        });

        // Sync back if native changes externally
        select.addEventListener('sync', () => {
             const selectedOption = select.options[select.selectedIndex];
             if (selectedOption) {
                 trigger.querySelector('.nx-select-text').innerText = selectedOption.text;
                 dropdown.querySelectorAll('.nx-select-option').forEach(opt => {
                     opt.classList.toggle('is-selected', opt.dataset.value === select.value);
                 });
             }
        });
    });
}

// Global click-to-close listener
document.addEventListener('click', () => {
    document.querySelectorAll('.nx-select-wrapper.is-open').forEach(w => w.classList.remove('is-open'));
});

// Registry for the active table instance
window.activeNexusTable = null;

/**
 * PREMIUM TOAST SYSTEM
 * Usage: showToast('Message', 'success' | 'error' | 'info' | 'warning', clearAll = false)
 */
function showToast(message, type = 'info', clearAll = false) {
    // Check user preference (if initialized)
    // We allow 'error' and 'warning' types to bypass the block for safety
    if (window.nexusSettings && !window.nexusSettings.notifications) {
        if (type === 'info' || type === 'success') {
            console.log(`[Toast Blocked]: ${message}`);
            return;
        }
    }

    if (clearAll) {
        document.querySelectorAll('.toast').forEach(t => {
            t.classList.remove('show');
            setTimeout(() => t.remove(), 300);
        });
    }

    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast`;
    
    const icons = {
        success: `<div class="toast-icon w-12 h-12 bg-emerald-500/20 text-emerald-500 shadow-lg shadow-emerald-500/10"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div>`,
        error: `<div class="toast-icon w-12 h-12 bg-rose-500/20 text-rose-500 shadow-lg shadow-rose-500/10"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg></div>`,
        warning: `<div class="toast-icon w-12 h-12 bg-amber-500/20 text-amber-500 shadow-lg shadow-amber-500/10"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg></div>`,
        info: `<div class="toast-icon w-12 h-12 bg-sky-500/20 text-sky-500 shadow-lg shadow-sky-500/10"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div>`
    };

    toast.innerHTML = `
        ${icons[type] || icons.info}
        <div class="toast-content py-1">
            <h4 class="text-[12px] font-black uppercase text-primary/60 tracking-[0.2em] mb-0.5">${type === 'success' ? 'Nexus Success' : type === 'error' ? 'nexus error' : 'nexus system'}</h4>
            <p class="toast-message leading-tight">${message}</p>
        </div>
        <div class="toast-progress" style="background-color: ${type === 'success' ? '#10b981' : type === 'error' ? '#f43f5e' : type === 'warning' ? '#f59e0b' : '#0ea5e9'}"></div>
    `;

    container.appendChild(toast);

    // Initial Trigger
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);

    // Auto Close
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 3000);
}

/**
 * PREMIUM FORM VALIDATION
 * Returns true if all visible inputs in container are filled
 */
function validateNexusForm(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return true;

    const inputs = container.querySelectorAll('input:not([type="hidden"]), select, textarea');
    let isValid = true;

    inputs.forEach(input => {
        // Skip disabled inputs
        if (input.disabled) return;

        // Clean previous states
        input.classList.remove('border-error', 'animate-shake');

        const value = input.value ? input.value.trim() : '';
        let inputError = false;

        // skip empty and optional
        if (value === '' && !input.required) {
            return;
        }

        // check empty required
        if (value === '' && input.required) {
            inputError = true;
        } 
        
        // check password rules
        else if (input.dataset.validationType === 'password') {
            const hasLetters = /[a-zA-Z]/.test(value);
            const hasNumbers = /\d/.test(value);
            const hasSpecial = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(value);
            
            if (value.length < 12) {
                inputError = true;
                showToast('Seguridad: La contraseña debe tener al menos 12 caracteres', 'warning');
            } else if (!hasLetters || !hasNumbers || !hasSpecial) {
                inputError = true;
                showToast('Seguridad: Usa letras, números y al menos 1 carácter especial', 'warning');
            }
        }
        
        // check match (passwords)
        else if (input.dataset.validationType === 'match') {
            const targetId = input.dataset.matchTarget;
            const targetEl = document.getElementById(targetId);
            if (!targetEl || value !== targetEl.value) {
                inputError = true;
                showToast('Las contraseñas no coinciden', 'error');
            }
        }

        if (inputError) {
            isValid = false;
            
            // Apply error styles
            input.classList.add('border-error', 'animate-shake');
            
            // Remove shake after animation to allow repeat
            setTimeout(() => {
                input.classList.remove('animate-shake');
            }, 600);
        }
    });

    if (!isValid && !container.querySelector('.border-error[type="email"]')) {
        showToast('Campos Requeridos: Por favor completa la información resaltada.', 'error');
    }

    return isValid;
}

/**
 * PREMIUM MODAL CONTROLLER
 * Optimized for nexus-modal architecture with smooth transitions.
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        // Clear previous state
        const allInputs = modal.querySelectorAll('input, select, textarea');
        allInputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else if (!input.getAttribute('name')?.includes('user_id')) {
                input.value = '';
            }
            
            // Clean visual validation state
            input.classList.remove('border-error', 'animate-shake');
            input.style.borderColor = '';
        });

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        // Force reflow
        modal.offsetWidth;
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus first input
        const firstInput = modal.querySelector('input:not([type="hidden"])');
        if (firstInput) setTimeout(() => firstInput.focus(), 400);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        // If no ID, attempt to close the currently open modal
        const openModal = document.querySelector('.nexus-modal.show');
        if (openModal) modalId = openModal.id;
        else return;
    }
    
    const targetModal = document.getElementById(modalId);
    if (targetModal) {
        targetModal.classList.remove('show');
        document.body.style.overflow = '';
        setTimeout(() => {
            targetModal.classList.remove('flex');
            targetModal.classList.add('hidden');
        }, 300);
    }
}

/**
 * GLOBAL SUCCESS HUD CONTROLLER
 * START SUCCESS COUNTDOWN (3s)
 * Centralized handler for successful management operations with cascading effect
 */
function startSuccessCountdown(customMessage = null) {
    const procModal = document.getElementById('processingModal');
    const successModal = document.getElementById('successManagementModal');
    const messageEl = document.getElementById('successModalMessage');
    const textEl = document.getElementById('successCountdownText');

    // ─── STAGE 1: CLEANUP & SPINNER ───
    // Close any active modal
    document.querySelectorAll('.nexus-modal').forEach(m => {
        m.classList.add('hidden');
        m.classList.remove('flex', 'show');
    });

    // Show Spinner immediately
    if (procModal) {
        procModal.classList.remove('hidden');
        procModal.classList.add('flex');
        setTimeout(() => procModal.classList.add('show'), 10);
    }

    // ─── STAGE 2: CASCADE DELAY (1200ms) ───
    setTimeout(() => {
        // Hide Spinner first
        if (procModal) {
            procModal.classList.remove('show');
            
            // WAIT for spinner exit transition (300ms) before showing success
            setTimeout(() => {
                procModal.classList.add('hidden');
                procModal.classList.remove('flex');

                // ─── STAGE 3: SHOW SUCCESS HUD ───
                if (successModal) {
                    if (customMessage && messageEl) messageEl.textContent = customMessage;
                    
                    successModal.classList.remove('hidden');
                    successModal.classList.add('flex');
                    
                    // Trigger Reflow for Animation
                    void successModal.offsetWidth;
                    successModal.classList.add('show');

                    // ─── STAGE 4: 3s COUNTDOWN ───
                    let seconds = 3;
                    if (textEl) textEl.textContent = `(${seconds}s)`;

                    const interval = setInterval(() => {
                        seconds--;
                        if (textEl) textEl.textContent = `(${seconds}s)`;
                        
                        if (seconds <= 0) {
                            clearInterval(interval);
                            location.reload();
                        }
                    }, 1000);
                }
            }, 300);
        } else {
            // Fallback if no spinner
            if (successModal) {
                successModal.classList.remove('hidden');
                successModal.classList.add('flex');
                setTimeout(() => successModal.classList.add('show'), 50);
            }
        }
    }, 1200);
}

// Global Listener for ESC key (Close Modals, Dropdowns, and Clear Search)
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const activeEl = document.activeElement;
        
        // 1. Logic for Search Inputs (If focused and has content)
        if (activeEl && activeEl.tagName === 'INPUT' && (activeEl.id.toLowerCase().includes('search') || activeEl.placeholder.toLowerCase().includes('buscar'))) {
            if (activeEl.value !== '') {
                activeEl.value = '';
                activeEl.dispatchEvent(new Event('input', { bubbles: true }));
                return; // Consume the event if we cleared a search
            }
        }

        // 2. Logic for Modals
        const activeModal = document.querySelector('.nexus-modal:not(.hidden)');
        if (activeModal) {
            closeModal(activeModal.id);
        }
    }
});

/**
 * PREMIUM LIVE VALIDATION
 * Actively monitors .premium-validate fields to provide real-time kinetic feedback.
 */
document.addEventListener('input', (e) => {
    if (e.target.classList.contains('premium-validate')) {
        const input = e.target;
        const type = input.dataset.validationType;
        const val = input.value.trim();
        
        let isValid = val.length > 0; // Baseline check
        
        // Context-aware deep validation
        if (type === 'email' && val.length > 0) {
            isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
        } else if (type === 'password' && val.length > 0) {
            // Enterprise rules: min 12 chars, alphanumeric, 1 special char
            const hasLetters = /[a-zA-Z]/.test(val);
            const hasNumbers = /\d/.test(val);
            const hasSpecial = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(val);
            isValid = val.length >= 12 && hasLetters && hasNumbers && hasSpecial;
        } else if (type === 'server' && val.length > 0) {
            isValid = /^([a-zA-Z0-9.-]+)\.([a-zA-Z]{2,})$/.test(val) || /^localhost$/.test(val);
        } else if (type === 'port' && val.length > 0) {
            const portNum = parseInt(val, 10);
            isValid = /^\d+$/.test(val) && portNum > 0 && portNum <= 65535;
        } else if (type === 'text' && val.length > 0) {
            // Basic text requirement: min 3 chars
            isValid = val.length >= 3;
        } else if (type === 'match' && val.length > 0) {
            const targetId = input.dataset.matchTarget;
            const targetEl = document.getElementById(targetId);
            isValid = targetEl && val === targetEl.value && val.length >= 12;
        }

        // Apply visual premium token feedback
        if (isValid) {
            input.classList.remove('border-error');
            input.style.borderColor = '#10b981'; // Emerald 500
            input.style.boxShadow = '0 0 0 4px rgba(16, 185, 129, 0.1)';
        } else {
            // Only show error if there is content or it's a required mismatch
            if (val.length > 0 || input.required) {
                input.classList.add('border-error');
                input.style.borderColor = ''; 
                input.style.boxShadow = '';
            }
        }
    }
});

/**
 * TAB NAVIGATION LOGIC (Global)
 */
function switchTab(tabId) {
    const activeClasses = ['text-tab-active-text', 'bg-tab-active', 'shadow-xl', 'shadow-tab-active/20'];
    const standbyClasses = ['text-tab-inactive-text', 'bg-tab-inactive', 'border', 'border-panel-border'];

    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.add('hidden'));
    document.querySelectorAll('.tab-trigger').forEach(trigger => {
        trigger.classList.remove(...activeClasses);
        trigger.classList.add(...standbyClasses);
    });
    
    const targetPanel = document.getElementById('tab-panel-' + tabId);
    if (targetPanel) targetPanel.classList.remove('hidden');
    
    const activeTrigger = document.getElementById('tab-trigger-' + tabId);
    if (activeTrigger) {
        activeTrigger.classList.remove(...standbyClasses);
        activeTrigger.classList.add(...activeClasses);
    }
}

/**
 * AUTH CONTROLLER
 * Toggles disabled state of password inputs based on their authentication toggle.
 */
document.addEventListener('change', (e) => {
    if (e.target.id === 'smtpAuthToggle') {
        const isAuth = e.target.checked;
        const smtpPass = document.getElementById('smtpPass');
        const authStatusText = document.getElementById('authStatusText');
        
        if (authStatusText) {
            authStatusText.textContent = isAuth ? 'Activo' : 'Inactivo';
        }
        
            if (smtpPass) {
                smtpPass.disabled = !isAuth;
                if (!isAuth) {
                    // Clear validation tokens when disabling
                    smtpPass.classList.remove('border-error');
                    smtpPass.style.borderColor = '';
                    smtpPass.style.boxShadow = '';
                } else {
                    // Re-evaluate validity instantly when enabling
                    smtpPass.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
    }
});

// 4. Notification Dropdown Logic (Encapsulated)
document.addEventListener('DOMContentLoaded', () => {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationDropdown = document.getElementById('notificationDropdown');
    const notificationBadge = document.getElementById('notificationBadge');

    if (notificationBtn && notificationDropdown) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = notificationDropdown.classList.contains('opacity-0');
            
            if (isHidden) {
                // Open
                notificationDropdown.classList.remove('opacity-0', 'translate-y-4', 'pointer-events-none');
                // Hide badge on open
                if (notificationBadge) {
                    notificationBadge.style.opacity = '0';
                    notificationBadge.style.transform = 'scale(0)';
                    setTimeout(() => notificationBadge.classList.add('hidden'), 300);
                }
            } else {
                // Close
                notificationDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !notificationDropdown.classList.contains('opacity-0')) {
                notificationDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (!notificationDropdown.contains(e.target) && !notificationBtn.contains(e.target)) {
                notificationDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // --- DYNAMIC NOTIFICATION SYSTEM ---
        let allNotifications = [];
        let activeFilter = 'all';
        
        async function fetchNotifications() {
            try {
                const response = await fetch('/notifications/api/active');
                if (!response.ok) return;
                
                // VALIDACIÓN DE SEGURIDAD: Verificar que sea JSON
                const contentType = response.headers.get("content-type");
                if (!contentType || !contentType.includes("application/json")) {
                    return; 
                }

                const data = await response.json();
                if (data.status === 'success') {
                    allNotifications = data.notifications;
                    renderNotifications(allNotifications, data.unread_count);
                }
            } catch (error) {
                // Silencio en producción para no saturar consola con errores de sesión
                if (window.location.hostname === 'localhost') {
                    console.debug('Notification fetch silent error (Check session/auth)');
                }
            }
        }

        function renderNotifications(notifications, unreadCount) {
            const list = document.getElementById('notificationList');
            const badge = document.getElementById('notificationBadge');
            if (!list) return;

            // Update Badge (Always show total unread of ALL)
            if (unreadCount > 0) {
                badge.classList.remove('hidden');
                const oldText = badge.textContent;
                badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
                
                // Pulse effect if count changed
                if (oldText !== badge.textContent) {
                    badge.classList.add('scale-150');
                    setTimeout(() => badge.classList.remove('scale-150'), 300);
                }
                
                badge.style.opacity = '1';
                badge.style.transform = 'scale(1)';
            } else {
                badge.style.opacity = '0';
                badge.style.transform = 'scale(0)';
                setTimeout(() => badge.classList.add('hidden'), 300);
            }

            // Filter logic
            const filtered = activeFilter === 'all' 
                ? notifications 
                : notifications.filter(n => n.type === activeFilter || (activeFilter === 'warning' && n.type === 'system')); 
                // Note: warning/system mapping depends on how you label them, 
                // but let's stick to strict type match for now:
            
            const displayList = activeFilter === 'all' ? notifications : notifications.filter(n => n.type === activeFilter);

            if (displayList.length === 0) {
                list.innerHTML = `
                    <div class="p-8 text-center opacity-40">
                        <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg>
                        <p class="text-[12px] font-black uppercase tracking-widest italic">Sin avisos en esta categoría</p>
                    </div>
                `;
                return;
            }

            const icons = {
                success: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
                error: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
                warning: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
                info: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
                system: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>'
            };

            const colors = {
                success: 'bg-emerald-500/10 text-emerald-500',
                error: 'bg-rose-500/10 text-rose-500',
                warning: 'bg-amber-500/10 text-amber-500',
                info: 'bg-sky-500/10 text-sky-500',
                system: 'bg-primary/10 text-primary'
            };

            list.innerHTML = displayList.map(n => `
                <div class="p-4 border-b border-panel-border/50 hover:bg-surface-container/40 cursor-pointer transition-colors group relative ${n.is_read ? 'opacity-60' : ''}" 
                     onclick="markAsRead(${n.id}, event)">
                    <div class="flex gap-3">
                        <div class="w-8 h-8 rounded-lg ${colors[n.type] || colors.info} flex-shrink-0 flex items-center justify-center group-hover:scale-110 transition-transform">
                            ${icons[n.type] || icons.info}
                        </div>
                        <div class="flex-grow">
                            <p class="text-xs font-bold text-text mb-0.5 line-clamp-1 italic">${n.title}</p>
                            <p class="text-[12px] text-label/60 leading-tight line-clamp-2">${n.message}</p>
                            <span class="text-[12px] font-bold opacity-40 mt-1 block">${n.time}</span>
                        </div>
                        ${!n.is_read ? '<div class="w-1.5 h-1.5 rounded-full bg-primary mt-1 flex-shrink-0 shadow-lg shadow-primary/20"></div>' : ''}
                    </div>
                </div>
            `).join('');
        }

        // Filter Click Handling
        document.querySelectorAll('.notif-filter').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                activeFilter = btn.dataset.filter;
                
                // Update UI of buttons
                document.querySelectorAll('.notif-filter').forEach(b => {
                    b.classList.remove('active', 'bg-primary', 'text-white');
                    b.classList.add('opacity-40');
                });
                btn.classList.add('active', 'bg-primary', 'text-white');
                btn.classList.remove('opacity-40');

                renderNotifications(allNotifications, 0); // unreadCount doesn't matter for filter re-render
            });
        });

        // Global exposing for onclick
        window.markAsRead = async (id, event) => {
            if (event) event.stopPropagation();
            try {
                const response = await fetch('/notifications/api/mark-read', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id })
                });
                if (response.ok) fetchNotifications();
            } catch (error) {
                console.error('Error marking as read:', error);
            }
        };

        window.markAllAsRead = async () => {
            try {
                const response = await fetch('/notifications/api/mark-read', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({}) // all
                });
                if (response.ok) {
                    showToast('Todas marcadas como leídas', 'success');
                    fetchNotifications();
                }
            } catch (error) {
                console.error('Error marking all as read:', error);
            }
        };

        window.deleteAllNotifications = async () => {
            try {
                const response = await fetch('/notifications/api/delete-all', {
                    method: 'DELETE'
                });
                if (response.ok) {
                    showToast('Bandeja de entrada vaciada', 'info');
                    fetchNotifications();
                }
            } catch (error) {
                console.error('Error deleting all:', error);
            }
        };

        // Initial fetch and set interval
        fetchNotifications();
        setInterval(fetchNotifications, 60000); // 1 minute polling
    }
});

// 5. Sidebar User Dropdown Logic
document.addEventListener('DOMContentLoaded', () => {
    const userProfileBtn = document.getElementById('userProfileBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userProfileBtn && userDropdown) {
        userProfileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = userDropdown.classList.contains('opacity-0');
            
            if (isHidden) {
                // Open
                userDropdown.classList.remove('opacity-0', 'translate-y-4', 'pointer-events-none');
            } else {
                // Close
                userDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !userDropdown.classList.contains('opacity-0')) {
                userDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // Close on click away
        document.addEventListener('click', (e) => {
            if (!userDropdown.contains(e.target) && !userProfileBtn.contains(e.target)) {
                userDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });
    }
});

// --- PREMIUM TOOLTIP ENGINE ---
(() => {
    let tooltip = null;

    function initTooltip() {
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.className = 'nx-tooltip';
            document.body.appendChild(tooltip);
        }
    }

    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('[data-nx-tooltip]');
        if (target) {
            initTooltip();
            const text = target.getAttribute('data-nx-tooltip');
            tooltip.innerText = text;
            tooltip.classList.add('show');
            
            const rect = target.getBoundingClientRect();
            const isSidebar = target.closest('#sidebar');
            
            if (isSidebar) {
                // Position to the RIGHT of the sidebar item
                const top = rect.top + (rect.height / 2) - (tooltip.offsetHeight / 2);
                const left = rect.right + 12;
                tooltip.style.top = top + 'px';
                tooltip.style.left = left + 'px';
            } else {
                // Default: position ABOVE the element
                const top = rect.top - tooltip.offsetHeight - 10;
                const left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2);
                tooltip.style.top = (top < 10 ? rect.bottom + 10 : top) + 'px';
                tooltip.style.left = left + 'px';
            }
        }
    });

    document.addEventListener('mouseout', (e) => {
        const target = e.target.closest('[data-nx-tooltip]');
        if (target && tooltip) {
            tooltip.classList.remove('show');
        }
    });
})();
