// Areas Management Module - Nexus Premium
let currentAreas = [...AREAS_DATA];
let filteredAreas = [...AREAS_DATA];
let selectedAreas = [];
let currentPage = 1;

// Wizard State (Create)
let currentStep = 1;
let selectedUserIdList = [];

// Wizard State (Edit)
let currentEditStep = 1;
let selectedEditUserIdList = [];

// Configuration
const iconsMap = {
    'server': '<i class="fas fa-server"></i>',
    'cloud': '<i class="fas fa-cloud"></i>',
    'cpu': '<i class="fas fa-microchip"></i>',
    'database': '<i class="fas fa-database"></i>',
    'lock': '<i class="fas fa-lock"></i>',
    'code': '<i class="fas fa-code"></i>',
    'terminal': '<i class="fas fa-terminal"></i>',
    'monitor': '<i class="fas fa-desktop"></i>',
    'activity': '<i class="fas fa-chart-line"></i>',
    'shield': '<i class="fas fa-shield-alt"></i>',
    'wifi': '<i class="fas fa-wifi"></i>',
    'globe': '<i class="fas fa-globe"></i>',
    'hard-drive': '<i class="fas fa-hdd"></i>',
    'key': '<i class="fas fa-key"></i>',
    'settings': '<i class="fas fa-cog"></i>',
    'layers': '<i class="fas fa-layer-group"></i>',
    'smartphone': '<i class="fas fa-mobile-alt"></i>',
    'tablet': '<i class="fas fa-tablet-alt"></i>',
    'git-branch': '<i class="fas fa-code-branch"></i>',
    'hash': '<i class="fas fa-hashtag"></i>',
    'headphones': '<i class="fas fa-headphones"></i>',
    'tool': '<i class="fas fa-tools"></i>',
    'box': '<i class="fas fa-box"></i>',
    'folder': '<i class="fas fa-folder"></i>',
    'users': '<i class="fas fa-users"></i>',
    'heart': '<i class="fas fa-heart"></i>',
    'briefcase': '<i class="fas fa-briefcase"></i>',
    'award': '<i class="fas fa-award"></i>',
    'book': '<i class="fas fa-book"></i>',
    'rocket': '<i class="fas fa-rocket"></i>'
};

const colorsPalette = [
    '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#475569', '#065f46', '#7c2d12',
    '#1e3a8a', '#581c87', '#991b1b', '#166534', '#115e59', '#4c1d95',
    '#134e4a', '#0f172a'
];

function getPageLength() {
    const h = window.innerHeight;
    return h < 900 ? 9 : 10;
}

document.addEventListener('DOMContentLoaded', () => {
    initAreasModule();
});

function initAreasModule() {
    renderAreasTable();

    // Buscar
    document.getElementById('areaSearch')?.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        filteredAreas = currentAreas.filter(a => 
            a.name.toLowerCase().includes(term) || 
            (a.description && a.description.toLowerCase().includes(term))
        );
        currentPage = 1;
        selectedAreas = [];
        renderAreasTable();
    });

    // Checkbox Mestro
    document.getElementById('selectAllAreas')?.addEventListener('change', (e) => {
        if (e.target.checked) {
            selectedAreas = filteredAreas.map(a => a.id);
        } else {
            selectedAreas = [];
        }
        renderAreasTable();
    });

    // Acción Global: Modificar
    document.getElementById('btnEditArea')?.addEventListener('click', () => {
        if (selectedAreas.length === 1) {
            const area = currentAreas.find(a => a.id === selectedAreas[0]);
            if (area) editArea(area.id);
        }
    });

    // Action Global: Eliminar with Structural Block Validation
    document.getElementById('btnDeleteArea')?.addEventListener('click', () => {
        if (selectedAreas.length > 0) {
            let totalPlatformsAffected = 0;
            
            // Analyze Structural Impact
            selectedAreas.forEach(id => {
                const area = currentAreas.find(a => a.id === id);
                if (area) totalPlatformsAffected += (area.platforms_count || 0);
            });

            // BLOCK LOGIC: Cannot delete if has platforms
            if (totalPlatformsAffected > 0) {
                return Swal.fire({
                    title: '<span class="text-rose-500 uppercase italic font-black tracking-tighter">Baja Bloqueada</span>',
                    html: `<div class="text-xs font-bold text-slate-300 leading-relaxed uppercase tracking-widest">
                            No es posible eliminar áreas que contienen infraestructura activa.<br><br>
                            Se detectaron <span class="text-rose-500 font-black">${totalPlatformsAffected} plataformas vinculadas</span>.<br>
                            Por favor, elimine o mueva los servicios antes de intentar dar de baja el departamento.
                           </div>`,
                    icon: 'error',
                    confirmButtonText: 'Entendido',
                    confirmButtonColor: '#6366f1',
                    background: '#1e293b',
                    color: '#ffffff',
                    backdrop: 'rgba(15, 23, 42, 0.75)'
                });
            }

            // Standard Confirmation for empty areas
            Swal.fire({
                title: '<span class="text-white uppercase italic font-black tracking-tighter">¿Confirmar eliminación?</span>',
                html: `<div class="text-xs font-bold text-slate-300 uppercase tracking-widest">Se eliminarán ${selectedAreas.length} área(s) de forma permanente.</div>`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#ef4444',
                cancelButtonColor: '#334155',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar',
                background: '#1e293b',
                color: '#ffffff',
                backdrop: 'rgba(15, 23, 42, 0.75)'
            }).then(async (result) => {
                if (result.isConfirmed) {
                    const procModal = document.getElementById('processingModal');
                    if (procModal) {
                        procModal.classList.remove('hidden');
                        procModal.classList.add('flex');
                        setTimeout(() => procModal.classList.add('show'), 50);
                    }

                    try {
                        const response = await fetch('/admin/areas/delete-bulk', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ ids: selectedAreas })
                        });
                        const data = await response.json();
                        if (data.status === 'success') {
                            startSuccessCountdown("El área ha sido purgada exitosamente del sistema.");
                        } else {
                            if (procModal) procModal.classList.add('hidden');
                            showToast(data.message, 'error');
                        }
                    } catch (error) {
                        if (procModal) procModal.classList.add('hidden');
                        showToast('Error crítico al eliminar', 'error');
                    }
                }
            });
        }
    });

    // Validar status en UI modal
    const areaStatus = document.getElementById('areaStatus');
    const areaStatusLabel = document.getElementById('areaStatusLabel');
    if(areaStatus && areaStatusLabel) {
        areaStatus.addEventListener('change', (e) => {
            areaStatusLabel.textContent = e.target.checked ? 'ACTIVO' : 'INACTIVO';
            areaStatusLabel.className = e.target.checked ? 'text-xs font-black text-primary uppercase tracking-widest' : 'text-xs font-black text-label/40 uppercase tracking-widest';
        });
    }

    window.addEventListener('resize', renderAreasTable);
}

function updateActionButtonsAreas() {
    const btnEdit = document.getElementById('btnEditArea');
    const btnDelete = document.getElementById('btnDeleteArea');
    const count = selectedAreas.length;

    if (btnEdit) btnEdit.disabled = count !== 1;
    if (btnDelete) btnDelete.disabled = count === 0;

    const selectAllCheckbox = document.getElementById('selectAllAreas');
    if (selectAllCheckbox) {
        const allOnPage = document.querySelectorAll('.area-checkbox').length;
        selectAllCheckbox.checked = count > 0 && count === filteredAreas.length;
        selectAllCheckbox.indeterminate = count > 0 && count < filteredAreas.length;
    }
}

function toggleAreaSelection(id, isSelected) {
    if (isSelected) {
        if (!selectedAreas.includes(id)) selectedAreas.push(id);
    } else {
        selectedAreas = selectedAreas.filter(areaId => areaId !== id);
    }
    renderAreasTable();
}

function renderAreasTable() {
    const tbody = document.getElementById('areasTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const recordsPerPage = getPageLength();
    const start = (currentPage - 1) * recordsPerPage;
    const end = start + recordsPerPage;
    const pageData = filteredAreas.slice(start, end);

    pageData.forEach((area, index) => {
        const isSelected = selectedAreas.includes(area.id);
        const isActive = area.status === 'Activo' || area.status === 'activo' || area.status === true;
        const areaIconHtml = iconsMap[area.icon] || iconsMap['box'];
        
        tbody.innerHTML += `
            <tr class="group hover:bg-primary/5 transition-all cursor-pointer border-b border-panel-border/30 last:border-none ${isSelected ? 'bg-primary/5' : ''}" 
                onclick="toggleAreaSelection(${area.id}, ${!isSelected})">
                <td class="text-center" style="border-left:3px solid ${isSelected ? 'rgb(var(--color-primary))' : 'transparent'};padding:0 0.5rem;" onclick="event.stopPropagation()">
                    <div class="flex items-center justify-center">
                        <input type="checkbox" class="area-checkbox w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" 
                            ${isSelected ? 'checked' : ''} onchange="toggleAreaSelection(${area.id}, this.checked)">
                    </div>
                </td>
                <td class="text-center">
                    <div class="w-9 h-9 mx-auto rounded-xl flex items-center justify-center text-white shadow-lg ring-1 ring-white/10" style="background: ${area.color || '#6366f1'}">
                        <div class="text-base">${areaIconHtml}</div>
                    </div>
                </td>
                <td>
                    <span class="text-xs font-black text-primary uppercase tracking-tight">${area.name}</span>
                </td>
                <td>
                    <div class="text-[11px] font-bold text-label/50 truncate italic line-clamp-1 max-w-[280px]" title="${area.description || ''}">
                        ${area.description || '-'}
                    </div>
                </td>
                <td class="text-center">
                    <div class="flex items-center justify-center">
                        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${isActive ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-500 border border-rose-500/20'}">
                            <span class="w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-rose-500'}"></span>
                            ${isActive ? 'ACTIVO' : 'INACTIVO'}
                        </div>
                    </div>
                </td>
                <td class="text-center">
                    <div class="flex items-center justify-center gap-2 text-label/60 font-black text-[11px]">
                         <i class="fas fa-users opacity-30 text-[10px]"></i>
                         ${area.users_count || 0}
                    </div>
                </td>
                <td class="text-center">
                    <div class="inline-flex items-center justify-center gap-2 bg-surface-container/30 px-4 py-1.5 rounded-xl border border-panel-border transition-all group-hover:border-primary/30 group-hover:bg-primary/5">
                        <span class="text-[11px] font-black text-primary italic leading-none">${area.platforms_count || 0}</span>
                        <i class="fas fa-layer-group text-[10px] text-label/20 group-hover:text-primary transition-colors"></i>
                    </div>
                </td>
            </tr>
        `;
    });

    renderGhostRows(7);
    renderPagination();
    updateActionButtonsAreas();
}

function renderGhostRows(columns) {
    const tbody = document.getElementById('areasTableBody');
    const recordsPerPage = getPageLength();
    const currentRows = tbody.children.length;
    const ghostCount = recordsPerPage - currentRows;

    if (ghostCount <= 0) return;

    for (let i = 0; i < ghostCount; i++) {
        const tr = document.createElement('tr');
        tr.className = 'pointer-events-none select-none';
        tr.innerHTML = `
            <td class="text-center" style="border-left:3px solid transparent;"></td>
            <td class="text-center"></td>
            <td class="text-left"></td>
            <td class="text-left"></td>
            <td class="text-center"></td>
            <td class="text-center"></td>
            <td class="text-center"></td>
        `;
        tbody.appendChild(tr);
    }
}

function renderPagination() {
    const container = document.getElementById('areasPagination');
    if (!container) return;
    
    const rowsPerPage = getPageLength();
    const totalPages = Math.ceil(filteredAreas.length / rowsPerPage);
    const start = filteredAreas.length ? (currentPage - 1) * rowsPerPage + 1 : 0;
    const end = Math.min(filteredAreas.length, currentPage * rowsPerPage);

    container.innerHTML = `
        <div class="dt-layout-row" style="display: flex !important; align-items: center; justify-content: space-between; height: 52px !important; padding: 0 1.25rem !important; border-top: 1px solid rgb(var(--color-panel-border) / 0.4) !important;">
            <div class="dt-layout-cell dt-layout-start">
                <div class="dt-info" style="font-size: 13px !important; font-weight: 800 !important; color: rgb(var(--color-text-body)) !important; text-transform: none !important; letter-spacing: normal !important;">
                    Mostrando ${start}-${end} de ${filteredAreas.length} registros
                </div>
            </div>
            <div class="dt-layout-cell dt-layout-end">
                <div class="dt-paging paging_simple">
                    <button class="dt-paging-button previous ${currentPage === 1 ? 'disabled' : ''}" 
                        onclick="changePage(currentPage - 1)" ${currentPage === 1 ? 'disabled' : ''}>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
                    </button>
                    <button class="dt-paging-button next ${currentPage >= totalPages || totalPages === 0 ? 'disabled' : ''}" 
                        onclick="changePage(currentPage + 1)" ${currentPage >= totalPages || totalPages === 0 ? 'disabled' : ''}>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                    </button>
                </div>
            </div>
        </div>
    `;
}

function generatePaginationPills(totalPages) {
    let pills = '';
    for (let i = 1; i <= totalPages; i++) {
        pills += `
            <button onclick="changePage(${i})" class="w-7 h-7 rounded-md flex items-center justify-center text-[11px] font-black transition-all ${currentPage === i ? 'bg-primary text-white shadow-md shadow-primary/20' : 'text-label/40 hover:bg-label/5 hover:text-label'}">
                ${i}
            </button>
        `;
    }
    return pills;
}

function changePage(page) {
    const rowsPerPage = getPageLength();
    const totalPages = Math.ceil(filteredAreas.length / rowsPerPage);
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        renderAreasTable();
    }
}

// Modal Logic
function openAreaModal() {
    openModal('areaModal');
    document.getElementById('areaForm').reset();
    document.getElementById('areaId').value = '';
    document.getElementById('modalTitle').textContent = 'Nueva Área';
    
    // Default Identity
    document.getElementById('areaIcon').value = 'box';
    document.getElementById('areaColor').value = '#6366f1';
    selectedUserIdList = [];

    // Reset to Step 1
    changeStep(1);
    
    // Status
    document.getElementById('areaStatus').checked = true;
    document.getElementById('areaStatusLabel').textContent = 'ACTIVO';

    renderPickers();
    renderUserPicklist();
}

function closeAreaModal() {
    closeModal('areaModal');
}

function closeEditAreaModal() {
    closeModal('editAreaModal');
}

/**
 * STEP NAVIGATION (CREATE)
 */
function changeStep(step) {
    if (step < 1 || step > 3) return;
    
    if (step > currentStep && currentStep === 1) {
        const name = document.getElementById('areaName').value.trim();
        if (!name) return showToast('El nombre es obligatorio', 'error');
    }

    currentStep = step;
    document.querySelectorAll('.step-section').forEach((s, idx) => s.classList.toggle('hidden', idx !== (step - 1)));
    
    const progress = document.getElementById('stepProgress');
    if (progress) progress.style.width = `${(step - 1) * 50}%`;

    document.querySelectorAll('.step-item').forEach((item, idx) => {
        const itemStep = idx + 1;
        const icon = item.querySelector('div');
        const label = item.querySelector('span');
        if (itemStep < step) {
            icon.className = "w-10 h-10 rounded-full bg-emerald-500 text-white flex items-center justify-center font-black text-sm shadow-lg shadow-emerald-500/20 ring-4 ring-panel-fill transition-all";
            icon.innerHTML = '<i class="fas fa-check"></i>';
            label.className = "text-[9px] font-black uppercase tracking-widest text-emerald-500";
        } else if (itemStep === step) {
            icon.className = "w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-black text-sm shadow-lg shadow-primary/20 ring-4 ring-panel-fill transition-all";
            icon.innerHTML = itemStep;
            label.className = "text-[9px] font-black uppercase tracking-widest text-primary";
        } else {
            icon.className = "w-10 h-10 rounded-full bg-panel-border text-label/40 flex items-center justify-center font-black text-sm ring-4 ring-panel-fill transition-all";
            icon.innerHTML = itemStep;
            label.className = "text-[9px] font-black uppercase tracking-widest text-label/40";
        }
    });

    const btnPrev = document.getElementById('btnPrevStep');
    const btnNext = document.getElementById('btnNextStep');
    const btnSave = document.getElementById('btnSaveArea');
    const btnCancel = document.getElementById('btnCancelArea');

    if (step === 1) { 
        btnCancel.classList.remove('hidden');
        btnPrev.classList.add('hidden'); 
        btnNext.classList.remove('hidden'); 
        btnSave.classList.add('hidden'); 
    }
    else if (step === 3) { 
        btnCancel.classList.add('hidden');
        btnPrev.classList.remove('hidden'); 
        btnNext.classList.add('hidden'); 
        btnSave.classList.remove('hidden'); 
    }
    else { 
        btnCancel.classList.add('hidden');
        btnPrev.classList.remove('hidden'); 
        btnNext.classList.remove('hidden'); 
        btnSave.classList.add('hidden'); 
    }
}

/**
 * STEP NAVIGATION (EDIT)
 */
function changeEditStep(step) {
    if (step < 1 || step > 3) return;
    
    if (step > currentEditStep && currentEditStep === 1) {
        const name = document.getElementById('editAreaName').value.trim();
        if (!name) return showToast('El nombre es obligatorio', 'error');
    }

    currentEditStep = step;
    document.querySelectorAll('.edit-step-section').forEach((s, idx) => s.classList.toggle('hidden', idx !== (step - 1)));
    
    const progress = document.getElementById('editStepProgress');
    if (progress) progress.style.width = `${(step - 1) * 50}%`;

    document.querySelectorAll('.edit-step-item').forEach((item, idx) => {
        const itemStep = idx + 1;
        const icon = item.querySelector('div');
        const label = item.querySelector('span');
        if (itemStep < step) {
            icon.className = "w-10 h-10 rounded-full bg-emerald-500 text-white flex items-center justify-center font-black text-sm shadow-lg shadow-emerald-500/20 ring-4 ring-panel-fill transition-all";
            icon.innerHTML = '<i class="fas fa-check"></i>';
            label.className = "text-[9px] font-black uppercase tracking-widest text-emerald-500";
        } else if (itemStep === step) {
            icon.className = "w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-black text-sm shadow-lg shadow-primary/20 ring-4 ring-panel-fill transition-all";
            icon.innerHTML = itemStep;
            label.className = "text-[9px] font-black uppercase tracking-widest text-primary";
        } else {
            icon.className = "w-10 h-10 rounded-full bg-panel-border text-label/40 flex items-center justify-center font-black text-sm ring-4 ring-panel-fill transition-all";
            icon.innerHTML = itemStep;
            label.className = "text-[9px] font-black uppercase tracking-widest text-label/40";
        }
    });

    const btnPrev = document.getElementById('btnEditPrevStep');
    const btnNext = document.getElementById('btnEditNextStep');
    const btnSave = document.getElementById('btnSaveEditedArea');
    const btnCancel = document.getElementById('btnCancelEditArea');

    if (step === 1) { 
        btnCancel.classList.remove('hidden');
        btnPrev.classList.add('hidden'); 
        btnNext.classList.remove('hidden'); 
        btnSave.classList.add('hidden'); 
    }
    else if (step === 3) { 
        btnCancel.classList.add('hidden');
        btnPrev.classList.remove('hidden'); 
        btnNext.classList.add('hidden'); 
        btnSave.classList.remove('hidden'); 
    }
    else { 
        btnCancel.classList.add('hidden');
        btnPrev.classList.remove('hidden'); 
        btnNext.classList.remove('hidden'); 
        btnSave.classList.add('hidden'); 
    }
}

/**
 * PICKER RENDERING
 */
function renderPickers() {
    const iconGrid = document.getElementById('iconGrid');
    const colorGrid = document.getElementById('colorGrid');
    const editIconGrid = document.getElementById('editIconGrid');
    const editColorGrid = document.getElementById('editColorGrid');

    const currentIcon = document.getElementById('areaIcon').value;
    const currentColor = document.getElementById('areaColor').value;
    const currentEditIcon = document.getElementById('editAreaIcon').value;
    const currentEditColor = document.getElementById('editAreaColor').value;

    // Create Pickers
    if (iconGrid && colorGrid) {
        iconGrid.innerHTML = ''; colorGrid.innerHTML = '';
        Object.entries(iconsMap).forEach(([key, svg]) => {
            const b = document.createElement('button'); b.type='button';
            b.className = `w-full aspect-square flex items-center justify-center border-r border-b border-panel-border/30 transition-all ${currentIcon === key ? 'bg-primary text-white z-10' : 'bg-transparent text-label/40 hover:bg-primary/5 hover:text-primary'}`;
            b.innerHTML = svg; b.onclick = () => { document.getElementById('areaIcon').value = key; renderPickers(); };
            iconGrid.appendChild(b);
        });
        colorsPalette.forEach(color => {
            const b = document.createElement('button'); b.type='button';
            b.className = `w-full aspect-square border-r border-b border-panel-border/30 transition-all flex items-center justify-center ${currentColor === color ? 'z-10' : 'opacity-80 hover:opacity-100 hover:scale-[0.95]'}`;
            b.style.background = color;
            if (currentColor === color) {
                b.innerHTML = '<i class="fas fa-check text-white text-xs drop-shadow-md"></i>';
                b.style.boxShadow = 'inset 0 0 0 3px rgba(255,255,255,0.4)';
            }
            b.onclick = () => { document.getElementById('areaColor').value = color; renderPickers(); };
            colorGrid.appendChild(b);
        });
    }

    // Edit Pickers
    if (editIconGrid && editColorGrid) {
        editIconGrid.innerHTML = ''; editColorGrid.innerHTML = '';
        Object.entries(iconsMap).forEach(([key, svg]) => {
            const b = document.createElement('button'); b.type='button';
            b.className = `w-full aspect-square flex items-center justify-center border-r border-b border-panel-border/30 transition-all ${currentEditIcon === key ? 'bg-primary text-white z-10' : 'bg-transparent text-label/40 hover:bg-primary/5 hover:text-primary'}`;
            b.innerHTML = svg; b.onclick = () => { document.getElementById('editAreaIcon').value = key; renderPickers(); };
            editIconGrid.appendChild(b);
        });
        colorsPalette.forEach(color => {
            const b = document.createElement('button'); b.type='button';
            b.className = `w-full aspect-square border-r border-b border-panel-border/30 transition-all flex items-center justify-center ${currentEditColor === color ? 'z-10' : 'opacity-80 hover:opacity-100 hover:scale-[0.95]'}`;
            b.style.background = color;
            if (currentEditColor === color) {
                b.innerHTML = '<i class="fas fa-check text-white text-xs drop-shadow-md"></i>';
                b.style.boxShadow = 'inset 0 0 0 3px rgba(255,255,255,0.4)';
            }
            b.onclick = () => { document.getElementById('editAreaColor').value = color; renderPickers(); };
            editColorGrid.appendChild(b);
        });
    }
}

/**
 * USER PICKLIST
 */
function renderUserPicklist(isEdit = false) {
    const availList = document.getElementById(isEdit ? 'editAvailableUsersList' : 'availableUsersList');
    const selList = document.getElementById(isEdit ? 'editSelectedUsersList' : 'selectedUsersList');
    if (!availList || !selList) return;

    availList.innerHTML = ''; selList.innerHTML = '';
    const currentList = isEdit ? selectedEditUserIdList : selectedUserIdList;

    ALL_USERS.forEach(user => {
        const isSelected = currentList.includes(user.id);
        const item = document.createElement('button'); item.type = 'button';
        item.className = "w-full flex items-center justify-between p-3 rounded-xl transition-all group " + (isSelected ? "bg-primary/10 hover:bg-primary/20" : "bg-panel-fill/40 hover:bg-surface-container/60");
        item.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg ${isSelected ? 'bg-primary text-white' : 'bg-label/10 text-label/60'} flex items-center justify-center text-xs">
                    <i class="fas fa-user"></i>
                </div>
                <div class="text-left font-black uppercase text-label leading-none">
                    <div class="text-[11px] mb-1">${user.name}</div>
                    <div class="text-[9px] text-label/40 tracking-tighter">${user.email}</div>
                </div>
            </div>
            <i class="fas ${isSelected ? 'fa-minus-circle text-primary' : 'fa-plus-circle text-label/20 group-hover:text-primary'} text-sm transition-colors"></i>
        `;
        item.onclick = () => toggleUserSelection(user.id, isEdit);
        if (isSelected) selList.appendChild(item); else availList.appendChild(item);
    });
}

function toggleUserSelection(userId, isEdit = false) {
    const list = isEdit ? selectedEditUserIdList : selectedUserIdList;
    const idx = list.indexOf(userId);
    if (idx === -1) list.push(userId); else list.splice(idx, 1);
    renderUserPicklist(isEdit);
}

function editArea(id) {
    const area = currentAreas.find(a => a.id === id);
    if (!area) return;

    openModal('editAreaModal');
    
    document.getElementById('editAreaId').value = area.id;
    document.getElementById('editAreaName').value = area.name;
    document.getElementById('editAreaDescription').value = area.description || '';
    
    const isActive = area.status === 'Activo' || area.status === 'activo';
    document.getElementById('editAreaStatus').checked = isActive;
    document.getElementById('editAreaStatusLabel').textContent = isActive ? 'ACTIVO' : 'INACTIVO';
    
    document.getElementById('editAreaIcon').value = area.icon || 'box';
    document.getElementById('editAreaColor').value = area.color || '#6366f1';

    selectedEditUserIdList = [];
    fetch(`/admin/areas/users/${id}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                selectedEditUserIdList = data.selected_ids || [];
                renderUserPicklist(true);
            }
        });

    changeEditStep(1);
    renderPickers();
}

async function saveArea() {
    const editId = document.getElementById('editAreaId')?.value;
    const createId = document.getElementById('areaId')?.value;
    const id = editId || createId || ""; // If editId exists, we are editing

    const prefix = editId ? 'editArea' : 'area';
    const name = document.getElementById(`${prefix}Name`).value.trim();
    const description = document.getElementById(`${prefix}Description`).value.trim();
    const status = document.getElementById(`${prefix}Status`).checked ? 'Activo' : 'Inactivo';
    
    if (!name) return showToast('El nombre es obligatorio', 'error');

    const url = editId ? `/admin/areas/edit/${editId}` : '/admin/areas/add';
    const method = 'POST'; 

    const icon = document.getElementById(`${prefix}Icon`).value;
    const color = document.getElementById(`${prefix}Color`).value;
    const user_ids = editId ? selectedEditUserIdList : selectedUserIdList;

    const procModal = document.getElementById('processingModal');
    if (procModal) {
        procModal.classList.remove('hidden');
        procModal.classList.add('flex');
        setTimeout(() => procModal.classList.add('show'), 50);
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description, status, icon, color, user_ids })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            startSuccessCountdown("La configuración del área ha sido sincronizada exitosamente.");
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error de conexión con el servidor', 'error');
    }
    
    if (editId) closeEditAreaModal(); else closeAreaModal();
}
