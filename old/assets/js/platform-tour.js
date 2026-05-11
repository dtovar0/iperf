/**
 * NEXUS PLATFORM GUIDED TOUR
 * Comprehensive guide for new users covering navigation and dashboard controls.
 */

class GlobalNexusTour {
    constructor(steps) {
        this.steps = steps;
        this.currentStep = -1;
        this.overlay = null;
        this.stepEl = null;
        this.spotlight = null;
        this._keyHandler = null;
        this.isDashboard = window.location.pathname === '/' || window.location.pathname === '/index';
        
        this.init();
    }

    init() {
        const oldOverlay = document.querySelector('.nx-tour-overlay');
        if (oldOverlay) oldOverlay.remove();
        const oldStep = document.querySelector('.nx-tour-step');
        if (oldStep) oldStep.remove();
        const oldSpot = document.querySelector('.nx-tour-spotlight');
        if (oldSpot) oldSpot.remove();

        this.overlay = document.createElement('div');
        this.overlay.className = 'nx-tour-overlay';
        this.overlay.onclick = () => this.end();
        document.body.appendChild(this.overlay);

        this.spotlight = document.createElement('div');
        this.spotlight.className = 'nx-tour-spotlight';
        document.body.appendChild(this.spotlight);

        this.stepEl = document.createElement('div');
        this.stepEl.className = 'nx-tour-step';
        document.body.appendChild(this.stepEl);
    }

    start() {
        this.currentStep = 0;
        this.overlay.classList.add('active');
        this.spotlight.classList.add('active');
        this.showStep();

        // Keyboard navigation
        this._keyHandler = (e) => {
            if (this.currentStep < 0) return;
            if (e.key === 'Enter' || e.key === 'ArrowRight') { e.preventDefault(); this.next(); }
            else if (e.key === 'Backspace' || e.key === 'ArrowLeft') { e.preventDefault(); this.prev(); }
            else if (e.key === 'Escape') { e.preventDefault(); this.end(); }
        };
        document.addEventListener('keydown', this._keyHandler);
    }

    next() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.showStep();
        } else {
            this.end();
        }
    }

    prev() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep();
        }
    }

    end() {
        this.overlay.classList.remove('active');
        this.stepEl.classList.remove('active');
        this.spotlight.classList.remove('active');
        this.currentStep = -1;

        // Cleanup any opened UI elements from the tour
        if (typeof closeModal === 'function') closeModal('settingsModal');
        const notifDropdown = document.getElementById('notificationDropdown');
        if (notifDropdown) {
            notifDropdown.style.opacity = '0';
            notifDropdown.style.pointerEvents = 'none';
        }

        if (this._keyHandler) {
            document.removeEventListener('keydown', this._keyHandler);
            this._keyHandler = null;
        }

        // Mark as completed in localStorage and DB to avoid auto-activation next time
        localStorage.setItem('nexus_tour_completed', 'true');
        window.nexusSettings.tourEnabled = false;

        fetch('/auth/preferences/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tour_enabled: false })
        }).catch(err => console.error('Error syncing tour state:', err));
    }

    showStep() {
        const step = this.steps[this.currentStep];
        const target = document.querySelector(step.target);
        
        if (target) {
            // Execute automated action if defined
            if (step.action && typeof step.action === 'function') {
                try {
                    step.action(target);
                } catch (e) {
                    console.error('Error executing tour step action:', e);
                }
            }

            const rect = target.getBoundingClientRect();
            const padding = 10;
            
            this.spotlight.style.top = `${rect.top - padding}px`;
            this.spotlight.style.left = `${rect.left - padding}px`;
            this.spotlight.style.width = `${rect.width + (padding * 2)}px`;
            this.spotlight.style.height = `${rect.height + (padding * 2)}px`;

            // Build pagination
            const dots = this.steps.map((_, i) => 
                `<div class="nx-tour-dot ${i === this.currentStep ? 'active' : ''}"></div>`
            ).join('');

            const arrowLeft = `<svg class="nx-tour-arrow ${this.currentStep === 0 ? 'disabled' : ''}" onclick="window.platformTour.prev()" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 19l-7-7 7-7"></path></svg>`;
            const arrowRight = `<svg class="nx-tour-arrow" onclick="window.platformTour.next()" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"></path></svg>`;

            this.stepEl.innerHTML = `
                <div class="nx-tour-step-header">
                    <span class="nx-tour-type">${step.type}</span>
                    <h3>${step.title}</h3>
                </div>
                <div class="nx-tour-content">
                    <p>${step.content}</p>
                </div>
                <div class="nx-tour-footer">
                    <div class="nx-tour-pagination">
                        ${arrowLeft}
                        <div class="nx-tour-dots">${dots}</div>
                        ${arrowRight}
                    </div>
                    <div class="nx-tour-counter">${this.currentStep + 1} / ${this.steps.length}</div>
                </div>
            `;

            const stepWidth = 400;
            // POSICIÓN LATERAL (IZQUIERDA)
            let stepLeft = (rect.left + window.scrollX) - stepWidth - 40;
            let stepTop = (rect.top + window.scrollY) + (rect.height / 2) - 150;

            // Si no hay espacio a la izquierda, ponerlo a la derecha
            if (stepLeft < 20) {
                stepLeft = (rect.right + window.scrollX) + 40;
            }

            // Screen bounds protection vertical
            if (stepTop < window.scrollY + 20) stepTop = window.scrollY + 20;
            if (stepTop + 400 > document.documentElement.scrollHeight) {
                stepTop = document.documentElement.scrollHeight - 420;
            }

            this.stepEl.style.width = `${stepWidth}px`;
            this.stepEl.style.top = `${stepTop}px`;
            this.stepEl.style.left = `${stepLeft}px`;
            this.stepEl.classList.add('active');
            
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            console.warn(`Tour Target not found: ${step.target}, skipping...`);
            this.next();
        }
    }
}

/**
 * INITIALIZATION & STEPS
 */
document.addEventListener('DOMContentLoaded', () => {
    const isDashboard = window.location.pathname === '/' || window.location.pathname === '/index';
    
    const steps = [
        {
            type: 'Menu',
            target: '#sidebar',
            title: 'Módulos Nexus',
            content: 'Accede a todas las herramientas: Terminal PSX5K, Gestión de Usuarios, Auditorías y Configuración del Sistema.'
        },
        {
            type: 'Navegación',
            target: '#sidebarToggle',
            title: 'Botón de Menú',
            content: 'Utiliza este botón para <b>colapsar o expandir</b> el menú lateral. Maximiza tu espacio de trabajo cuando lo necesites.'
        },
        {
            type: 'Orientación',
            target: '#locationBar',
            title: 'Barra de Ubicación',
            content: 'Aquí puedes ver en qué sección de la plataforma te encuentras en todo momento. Te ayuda a mantener el contexto de tu navegación.'
        },
        {
            type: 'Topbar',
            target: '#systemSearch',
            title: 'Búsqueda Inteligente',
            content: 'Realiza búsquedas globales en el historial o comandos. Encuentra números de ticket o usuarios de forma instantánea.'
        },
        {
            type: 'Alertas',
            target: '#notificationBtn',
            title: 'Notificaciones',
            content: 'Mantente informado sobre el estado de tus tareas. Verás una alerta aquí cuando un proceso finalice o requiera tu atención.'
        },
        {
            type: 'Personalización',
            target: '#themeToggle',
            title: 'Selector de Temas',
            content: 'Personaliza tu experiencia visual. Alterna entre <b>6 temas premium</b> (Sapphire, Emerald, Crimson, etc.) con un solo clic.'
        }
    ];

    // Add dashboard specific steps
    if (isDashboard) {
        steps.push({
            type: 'Panel de Control',
            target: '#mainContent',
            title: 'Área de Trabajo',
            content: 'Zona principal donde se despliegan tus módulos y herramientas operativas según la sección seleccionada.'
        });
    }

    // Add final configuration step
    steps.push({
        type: 'Configuración Personal',
        target: '#settingsBtn',
        title: 'Ajustes de Interfaz',
        content: 'Abre este panel para ajustar la frecuencia de refresco, activar notificaciones de escritorio o personalizar los colores de los estados.'
    });

    window.platformTour = new GlobalNexusTour(steps);

    // Auto-start logic
    setTimeout(() => {
        const hasCompleted = localStorage.getItem('nexus_tour_completed');
        const isTourEnabled = window.nexusSettings ? window.nexusSettings.tourEnabled : true;

        if (!hasCompleted && isTourEnabled) {
            window.platformTour.start();
        }
    }, 1500); 
});

/**
 * Global triggers
 */
window.startPlatformTour = function() {
    if (window.platformTour) {
        if (typeof closeModal === 'function') closeModal('settingsModal');
        window.platformTour.start();
    }
};
