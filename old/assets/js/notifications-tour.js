/**
 * NEXUS PREMIUM GUIDED TOUR - NOTIFICATIONS & TEMPLATES (V8)
 */

class NotificationNexusTour {
    constructor(steps) {
        this.steps = steps;
        this.currentStep = -1;
        this.overlay = null;
        this.stepEl = null;
        this.spotlight = null;
        this._keyHandler = null;
    }

    init() {
        console.log('🏁 Initializing Notification Tour Elements...');
        document.querySelectorAll('.nx-tour-overlay, .nx-tour-step, .nx-tour-spotlight').forEach(el => el.remove());

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
        console.log('🚀 Starting Notification Guided Tour');
        this.init();

        this.currentStep = 0;
        this.overlay.classList.add('active');
        this.spotlight.classList.add('active');
        this.showStep();

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
        if (this.overlay) this.overlay.classList.remove('active');
        if (this.stepEl) this.stepEl.classList.remove('active');
        if (this.spotlight) this.spotlight.classList.remove('active');
        this.currentStep = -1;

        if (this._keyHandler) {
            document.removeEventListener('keydown', this._keyHandler);
            this._keyHandler = null;
        }
    }

    showStep() {
        const step = this.steps[this.currentStep];
        const target = document.querySelector(step.target);

        if (target) {
            const rect = target.getBoundingClientRect();
            const padding = 10;

            this.spotlight.style.top = `${rect.top - padding}px`;
            this.spotlight.style.left = `${rect.left - padding}px`;
            this.spotlight.style.width = `${rect.width + (padding * 2)}px`;
            this.spotlight.style.height = `${rect.height + (padding * 2)}px`;

            const dots = this.steps.map((_, i) => 
                `<div class="nx-tour-dot ${i === this.currentStep ? 'active' : ''}"></div>`
            ).join('');

            const arrowLeft = `<svg class="nx-tour-arrow ${this.currentStep === 0 ? 'disabled' : ''}" onclick="window.notificationTour.prev()" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 19l-7-7 7-7"></path></svg>`;
            const arrowRight = `<svg class="nx-tour-arrow" onclick="window.notificationTour.next()" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"></path></svg>`;

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
            let stepLeft, stepTop;

            if (step.position === 'right') {
                stepLeft = (rect.right + window.scrollX) + 40;
                stepTop = (rect.top + window.scrollY) + (rect.height / 2) - 150;
            } else if (step.position === 'left') {
                stepLeft = (rect.left + window.scrollX) - stepWidth - 40;
                stepTop = (rect.top + window.scrollY) + (rect.height / 2) - 150;
            } else if (step.position === 'top') {
                stepLeft = (rect.left + window.scrollX) + (rect.width / 2) - (stepWidth / 2);
                stepTop = (rect.top + window.scrollY) - 300;
            } else {
                // Default: Bottom
                stepLeft = (rect.left + window.scrollX) + (rect.width / 2) - (stepWidth / 2);
                stepTop = (rect.bottom + window.scrollY) + 30;
                
                // Adjustment if bottom fails
                if (stepTop + 250 > document.documentElement.scrollHeight) {
                    stepTop = (rect.top + window.scrollY) - 280;
                }
            }

            // Screen bounds protection
            if (stepLeft < 20) stepLeft = 20;
            if (stepLeft + stepWidth > window.innerWidth - 20) {
                stepLeft = window.innerWidth - stepWidth - 20;
            }
            if (stepTop < 20) stepTop = 20;

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

(function() {
    window.notificationTour = new NotificationNexusTour([
        {
            type: 'Navegación',
            target: '.tab-trigger#tab-trigger-template',
            title: 'Configuración de Plantillas',
            content: 'Desde aquí puedes personalizar el diseño de los correos electrónicos que envía el sistema para cada evento operativo.'
        },
        {
            type: 'Librería',
            target: '#tour-template-library',
            title: 'Plantillas Predefinidas',
            content: 'Selecciona una base de nuestra librería (Test, Inicio, Error, etc.) para cargar su estructura y empezar a editar de forma rápida.',
            position: 'right'
        },
        {
            type: 'Editor de Contenido',
            target: '#tour-template-editor',
            title: 'Control de Mensaje',
            content: 'Define el <b>Asunto</b> y el <b>Cuerpo</b> del mensaje. Puedes usar etiquetas dinámicas que el sistema reemplazará automáticamente.',
            position: 'left'
        },
        {
            type: 'Variables Dinámicas',
            target: '#tour-template-shortcuts',
            title: 'Atajos Rápidos',
            content: 'Utiliza estos botones para insertar etiquetas inteligentes como <b>{nombre}, {evento} o {hora}</b>. El sistema las sustituirá por datos reales al enviar.',
            position: 'top'
        },
        {
            type: 'Vista Previa Reacción',
            target: '#tour-template-preview',
            title: 'Visualización Táctica',
            content: 'Observa en tiempo real cómo se verá el correo final. El renderizado es <b>exacto</b> a lo que recibirá el usuario.',
            position: 'left'
        },
        {
            type: 'Acción Final',
            target: '#tab-panel-template .nexus-btn-save',
            title: 'Persistencia de Datos',
            content: 'No olvides <b>Guardar</b> tus cambios. La nueva configuración se aplicará instantáneamente a todas las notificaciones futuras.',
            position: 'left'
        }
    ]);

    document.addEventListener('DOMContentLoaded', () => {
        const helpBtn = document.getElementById('helpNotificationTourBtn');
        if (helpBtn) {
            helpBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                window.notificationTour.start();
            });
        }
    });
})();
