/**
 * Users Management Interactivity - Nexus Premium Edition
 */

// Global state
var currentPage = 1;
var rowsPerPage = 10;
var currentFilteredUsers = [];
var currentEditUserId = null;

var iconsMap = {
    'server': '<i class="fas fa-server"></i>',
    'cloud': '<i class="fas fa-cloud"></i>',
    'cpu': '<i class="fas fa-cpu"></i>',
    'database': '<i class="fas fa-database"></i>',
    'lock': '<i class="fas fa-lock"></i>',
    'box': '<i class="fas fa-box"></i>'
};

function createPremiumEmptyState(title, text, iconClass = 'fa-search') {
    return `
        <div class="flex flex-col items-center justify-center py-16 opacity-40">
            <div class="w-20 h-20 rounded-full bg-surface-container/20 flex items-center justify-center mb-6">
                <i class="fas ${iconClass} text-3xl"></i>
            </div>
            <h3 class="text-lg font-black uppercase tracking-widest text-primary italic">${title}</h3>
            <p class="text-xs font-bold uppercase tracking-tighter mt-2">${text}</p>
        </div>
    `;
}

function getAreaColor(name) {
    if (!name) return 'linear-gradient(135deg, #2563eb, #3b82f6)';
    const colors = [
        '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9'
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return colors[Math.abs(hash) % colors.length];
}

// ─── Modal Functions ───
async function refreshPicklistAreas(prefix, selectedNames = []) {
    try {
        const res = await fetch('/admin/areas-api');
        const areas = await res.json();
        
        // selectedNames can be array of strings or array of objects with .name
        const normalizedSelected = selectedNames.map(n => typeof n === 'string' ? n : n.name);

        const available = areas.filter(a => !normalizedSelected.includes(a.name));
        const assigned = areas.filter(a => normalizedSelected.includes(a.name));

        populateUserAreasPicklist(`${prefix}AvailableList`, available, prefix);
        populateUserAreasPicklist(`${prefix}SelectedList`, assigned, prefix);
        
        updateUserAreasHiddenInput(prefix);
    } catch (e) { 
        console.error("Areas API error:", e); 
        if (typeof showToast === 'function') showToast('Error al cargar áreas', 'error');
    }
}

function populateUserAreasPicklist(containerId, items, prefix) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const isSelected = containerId.includes('Selected');
    
    items.forEach(item => {
        const card = createAreaCardModern(item, isSelected, prefix);
        container.appendChild(card);
    });

    if (prefix === 'addUser') {
        const countEl = document.getElementById('areaCount');
        if (countEl) {
            const count = document.querySelectorAll('#addUserSelectedList .picklist-card-premium').length;
            countEl.textContent = `${count} SELECCIONADAS`;
        }
    }
}

function createAreaCardModern(area, isSelected, prefix) {
    const card = document.createElement('div');
    card.className = 'group flex items-center justify-between p-3 rounded-2xl border border-panel-border bg-white hover:border-primary/40 hover:shadow-lg transition-all cursor-pointer select-none picklist-card-premium mb-3' + (isSelected ? ' ring-1 ring-primary/20' : '');
    card.setAttribute('data-action', 'users-toggle-area');
    card.setAttribute('data-area-name', area.name);
    card.setAttribute('data-list-id', isSelected ? `${prefix}SelectedList` : `${prefix}AvailableList`);
    
    const colors = area.color || getAreaColor(area.name);

    card.innerHTML = `
        <div class="flex items-center gap-4 flex-grow min-w-0">
            <div class="w-11 h-11 rounded-xl flex items-center justify-center text-white shadow-lg flex-shrink-0" style="background: ${colors}">
                <i class="fas fa-${area.icon || 'box'} text-lg"></i>
            </div>
            <div class="text-[13px] font-black text-label uppercase tracking-tighter italic truncate card-name">${area.name}</div>
        </div>
        <div class="w-9 h-9 rounded-full border-2 border-panel-border/60 group-hover:border-primary/40 flex items-center justify-center text-label/20 group-hover:text-primary transition-all flex-shrink-0 ml-2">
            <i class="fas ${isSelected ? 'fa-times' : 'fa-plus'} text-[10px]"></i>
        </div>
    `;
    return card;
}

function toggleUserAreaPremium(area, isAvailable, prefix) {
    const availList = document.getElementById(`${prefix}AvailableList`);
    const selectedList = document.getElementById(`${prefix}SelectedList`);
    
    if (!availList || !selectedList) return;

    const isNowSelected = isAvailable;
    const currentList = isAvailable ? availList : selectedList;
    const targetList = isNowSelected ? selectedList : availList;

    // Find and remove
    const items = Array.from(currentList.children);
    const itemToMove = items.find(el => el.querySelector('.card-name').textContent === area.name);
    if (itemToMove) itemToMove.remove();

    // Add to target
    const areasData = window.__areaData || [];
    const areaFull = areasData.find(a => a.name === area.name) || area;
    const newCard = createAreaCardModern(areaFull, isNowSelected, prefix);
    targetList.appendChild(newCard);
    
    updateUserAreasHiddenInput(prefix);
}

function updateUserAreasHiddenInput(prefix) {
    const selector = `#${prefix}SelectedList .card-name`;
    const selected = Array.from(document.querySelectorAll(selector)).map(el => el.textContent);
    const inputId = prefix === 'editUser' ? 'editSelectedUserAreasInput' : 'selectedUserAreasInput';
    const input = document.getElementById(inputId);
    if (input) input.value = JSON.stringify(selected);

    if (prefix === 'addUser') {
        const countEl = document.getElementById('areaCount');
        if (countEl) countEl.textContent = `${selected.length} SELECCIONADAS`;
    }
}

// ─── Search & Render ───

function getPageLength() {
    const h = window.innerHeight;
    if (h < 900) return 9;
    return 10;
}

function handleUserSearch() {
    const term = document.getElementById('userSearch').value.toLowerCase();
    if (typeof allUsersData === 'undefined') return;
    
    currentFilteredUsers = allUsersData.filter(u => {
        const name = (u.name || '').toLowerCase();
        const email = (u.email || '').toLowerCase();
        const role = (u.role || '').toLowerCase();
        return name.includes(term) || email.includes(term) || role.includes(term);
    });
    
    currentPage = 1;
    renderUsersTable();
}

function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const rowsPerPage = getPageLength();
    const pageData = currentFilteredUsers.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);

    if (pageData.length === 0) {
        const isSearch = document.getElementById('userSearch')?.value.trim() !== "";
        const icon = isSearch ? 'fa-search' : 'fa-users-slash';
        const title = isSearch ? 'Sin resultados' : 'Sin Usuarios';
        const text = isSearch ? 'No pudimos encontrar usuarios vinculados.' : 'No hay usuarios registrados.';

        tbody.innerHTML = `<tr><td colspan="8">${createPremiumEmptyState(title, text, icon)}</td></tr>`;
        renderPagination();
        return;
    }

    pageData.forEach(user => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-primary/5 transition-all group cursor-pointer";
        
        const r = (user.role || '').toLowerCase();
        let roleCls = 'nx-badge-slate';
        let roleIcon = 'fa-user';
        if (r.includes('admin')) { roleCls = 'nx-badge-primary'; roleIcon = 'fa-shield-alt'; }
        if (r.includes('audit')) { roleCls = 'nx-badge-warning'; roleIcon = 'fa-eye'; }

        const statusCls = user.status === 'Activo' ? 'nx-badge-success' : 'nx-badge-error';

        tr.innerHTML = `
            <td class="text-center" style="border-left:3px solid transparent;padding:0 1.25rem 0 1rem;">
                <div class="flex items-center justify-center">
                    <input type="checkbox" class="user-checkbox w-5 h-5 rounded-md border-2 border-primary/30 text-primary focus:ring-primary/20 cursor-pointer transition-all" value="${user.id}">
                </div>
            </td>
            <td>
                <span class="text-[15px] font-black text-label uppercase italic tracking-tighter truncate">${user.name}</span>
            </td>
            <td>
                <span class="text-[13px] font-bold text-label/60 uppercase tracking-widest truncate">${user.email}</span>
            </td>
            <td class="text-center">
                <div class="flex justify-center">
                    <span class="nx-badge ${roleCls} flex items-center gap-2 px-3 py-1 rounded-full whitespace-nowrap text-[9px] font-black tracking-widest border border-current/10 shadow-sm">
                        <i class="fas ${roleIcon} text-[8px] opacity-70"></i> 
                        ${user.role.toUpperCase()}
                    </span>
                </div>
            </td>
            <td class="text-center">
                <span class="nx-badge ${user.source === 'local' ? 'nx-badge-success' : (user.source === 'ldap' ? 'nx-badge-primary' : 'nx-badge-violet')}">
                    ${(user.source || 'LOCAL').toUpperCase()}
                </span>
            </td>
            <td class="text-center">
                ${user.platforms_count > 0 ? `<span class="nx-badge nx-badge-cyan inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black tracking-widest border border-cyan-500/10 shadow-sm">${user.platforms_count} <i class="fas fa-eye text-[9px] opacity-70"></i></span>` : '<span class="opacity-10 text-[10px] font-black uppercase tracking-widest">—</span>'}
            </td>
            <td>
                <div class="flex items-center -space-x-2 overflow-hidden">
                    ${(user.areas || []).slice(0, 5).map(a => `
                        <div class="w-8 h-8 rounded-lg flex items-center justify-center text-white border-2 border-panel-fill shadow-md hover:-translate-y-1 transition-transform flex-shrink-0" 
                             style="background: ${a.color || getAreaColor(a.name || a)}" 
                             title="${a.name || a}">
                             <i class="fas fa-${a.icon || 'box'} text-[10px]"></i>
                        </div>
                    `).join('')}
                    ${user.areas && user.areas.length > 5 ? `<div class="w-8 h-8 rounded-lg bg-surface-container border-2 border-panel-fill flex items-center justify-center text-[10px] font-black text-label/40">+${user.areas.length - 5}</div>` : (user.areas && user.areas.length === 0 ? '<span class="opacity-10 text-[10px] uppercase font-black tracking-widest">—</span>' : '')}
                </div>
            </td>
            <td class="text-center">
                <span class="nx-badge ${statusCls}">${user.status.toUpperCase()}</span>
            </td>
        `;
        
        tr.addEventListener('click', (e) => {
            // Ignore if clicking directly on checkbox
            if (e.target.type === 'checkbox') return;
            
            // Clear other selections for single-edit clarity
            document.querySelectorAll('.user-checkbox').forEach(c => c.checked = false);
            
            const cb = tr.querySelector('.user-checkbox');
            if (cb) {
                cb.checked = true;
                updateActionButtons();
                
                // Trigger the edit modal
                const editBtn = document.querySelector('[data-action="users-edit-selected"]');
                if (editBtn) editBtn.click();
            }
        });

        tbody.appendChild(tr);
    });

    renderGhostRows(8); // 8 columns
    renderPagination();
    updateActionButtons();
}

/**
 * Sizes all rows equally and adds ghost rows 1:1 like Audit
 */
function renderGhostRows(columns) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    const pageLen = getPageLength();
    const realRows = tbody.children.length;
    const ghostCount = pageLen - realRows;
    
    if (ghostCount <= 0) return;

    for (let i = 0; i < ghostCount; i++) {
        const tr = document.createElement('tr');
        tr.className = "ghost-row pointer-events-none select-none border-b border-panel-border/10";
        tr.style.height = "var(--row-h, 60px)";
        
        tr.innerHTML = `
            <td class="text-center"><div></div></td>
            <td class="text-left"><div></div></td>
            <td class="text-left"><div></div></td>
            <td class="text-center"><div></div></td>
            <td class="text-center"><div></div></td>
            <td class="text-center"><div></div></td>
            <td class="text-left"><div></div></td>
            <td class="text-center"><div></div></td>
        `;
        tbody.appendChild(tr);
    }
}

function renderPagination() {
    const container = document.getElementById('usersPagination');
    if (!container) return;
    
    const rowsPerPage = getPageLength();
    const totalPages = Math.ceil(currentFilteredUsers.length / rowsPerPage);
    const start = currentFilteredUsers.length ? (currentPage - 1) * rowsPerPage + 1 : 0;
    const end = Math.min(currentFilteredUsers.length, currentPage * rowsPerPage);

    // Reconstrucción 1:1 con Auditoría (DataTables Engine)
    container.innerHTML = `
        <div class="dt-layout-row" style="display: flex !important; align-items: center; justify-content: space-between; height: 52px !important; padding: 0 1.25rem !important; border-top: 1px solid rgb(var(--color-panel-border) / 0.4) !important;">
            <div class="dt-layout-cell dt-layout-start">
                <div class="dt-info" style="font-size: 13px !important; font-weight: 800 !important; color: rgb(var(--color-text-body)) !important; text-transform: none !important; letter-spacing: normal !important;">
                    Mostrando ${start}-${end} de ${currentFilteredUsers.length} registros
                </div>
            </div>
            <div class="dt-layout-cell dt-layout-end">
                <div class="dt-paging paging_simple">
                    <button class="dt-paging-button previous ${currentPage === 1 ? 'disabled' : ''}" 
                        data-action="users-change-page" data-offset="-1" ${currentPage === 1 ? 'disabled' : ''}>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"></path></svg>
                    </button>
                    <button class="dt-paging-button next ${currentPage >= totalPages ? 'disabled' : ''}" 
                        data-action="users-change-page" data-offset="1" ${currentPage >= totalPages ? 'disabled' : ''}>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"></path></svg>
                    </button>
                </div>
            </div>
        </div>
    `;
}

function updateActionButtons() {
    const rows = document.querySelectorAll('#usersTableBody tr:not(.ghost-row)');
    let checkedCount = 0;
    let totalCheckboxes = 0;

    rows.forEach(tr => {
        const cb = tr.querySelector('.user-checkbox');
        if (cb) {
            totalCheckboxes++;
            if (cb.checked) {
                tr.classList.add('nx-row-selected');
                checkedCount++;
            } else {
                tr.classList.remove('nx-row-selected');
            }
        }
    });

    const btnEdit = document.getElementById('btnEditUser');
    const btnDelete = document.getElementById('btnDeleteUser');
    const btnAccess = document.getElementById('btnAccessUser');
    const btnAreas = document.getElementById('btnAreasUser');

    if (btnEdit) btnEdit.disabled = (checkedCount !== 1);
    if (btnAccess) btnAccess.disabled = (checkedCount !== 1);
    if (btnAreas) btnAreas.disabled = (checkedCount !== 1);
    if (btnDelete) btnDelete.disabled = (checkedCount === 0);
    
    // Header Select All sync
    const selectAll = document.getElementById('selectAllUsers');
    if (selectAll) {
        selectAll.checked = (totalCheckboxes > 0 && checkedCount === totalCheckboxes);
        selectAll.indeterminate = (checkedCount > 0 && checkedCount < totalCheckboxes);
    }
}

// ─── Initialization & Listeners ───

document.addEventListener('DOMContentLoaded', () => {
    if (typeof allUsersData !== 'undefined') {
        currentFilteredUsers = [...allUsersData];
        renderUsersTable();
    }
    
    const searchInput = document.getElementById('userSearch');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            handleUserSearch();
        });
    }

    // Checkbox Change Delegation
    document.getElementById('usersTableBody')?.addEventListener('change', (e) => {
        if (e.target.classList.contains('user-checkbox')) {
            updateActionButtons();
        }
    });

    // Static Control Listeners
    document.addEventListener('click', (event) => {
        const trigger = event.target.closest('[data-action]');
        if (!trigger) return;

        const action = trigger.getAttribute('data-action');

        if (action === 'users-open-access') return openSelectedUserAccess();
        if (action === 'users-edit-selected') return editSelectedUser();
        if (action === 'users-delete-selected') return deleteSelectedUsers();
        if (action === 'users-close-edit-modal') return closeModal('editUserModal');
        if (action === 'users-close-add-modal') return closeModal('addUserModal');
        if (action === 'users-step-next') return changeUserStep(2);
        if (action === 'users-step-back') return changeUserStep(1);
        if (action === 'users-submit-new') return saveNewUser(event);

        if (action === 'users-toggle-area') {
            const areaName = trigger.dataset.areaName;
            const listId = trigger.dataset.listId;
            const prefix = listId.includes('edit') ? 'editUser' : 'addUser';
            const area = (window.__areaData || []).find(a => a.name === areaName) || { name: areaName };
            return toggleUserAreaPremium(area, listId.includes('Available'), prefix);
        }
        
        if (action === 'users-open-type-modal') return openModal('userTypeModal');
        if (action === 'users-close-type-modal') return closeModal('userTypeModal');
        if (action === 'users-open-local-flow') {
            closeModal('userTypeModal');
            
            // Reset form and ensure status is active with a micro-delay
            setTimeout(() => {
                const form = document.querySelector('#addUserModal form');
                if (form) {
                    form.reset();
                    const statusToggle = form.querySelector('#addUserStatusToggle');
                    if (statusToggle) {
                        $(statusToggle).prop('checked', true).trigger('change');
                    }
                    const roleToggle = form.querySelector('#addUserRoleToggle');
                    if (roleToggle) {
                        $(roleToggle).prop('checked', false).trigger('change');
                        const roleInput = document.getElementById('addUserRole');
                        if (roleInput) roleInput.value = 'usuario';
                    }
                }
            }, 50);
            
            const sourceInput = document.getElementById('addUserAuthSource');
            if (sourceInput) sourceInput.value = 'local';
            
            // Show password row for local users
            const passRow = document.getElementById('addUserPassword')?.closest('.grid');
            if (passRow) passRow.classList.remove('hidden');
            // Make fields required
            document.getElementById('addUserPassword').required = true;
            document.getElementById('addUserPasswordConfirm').required = true;

            openModal('addUserModal');
            changeUserStep(1);
            refreshPicklistAreas('addUser');
            return;
        }
        if (action === 'users-open-ldap-flow') {
            closeModal('userTypeModal');
            openModal('ldapUserModal');
            return;
        }
        if (action === 'users-close-ldap-modal') return closeModal('ldapUserModal');
        if (action === 'users-back-ldap-to-type') {
            closeModal('ldapUserModal');
            openModal('userTypeModal');
        }
        if (action === 'users-submit-edit') {
            event.preventDefault();
            return saveUserChanges();
        }
        if (action === 'users-close-access-modal') return closeModal('userAccessModal');
        if (action === 'users-change-page') return changeUserPage(parseInt(trigger.dataset.offset));
        
        if (action === 'users-toggle-access') {
            return toggleUserAccess(trigger.dataset.platformName, trigger.dataset.isSelected === 'true');
        }
        if (action === 'users-save-access') return saveUserPlatformAccess();

        if (action === 'users-select-all') {
            const checkboxes = document.querySelectorAll('.user-checkbox');
            checkboxes.forEach(cb => cb.checked = event.target.checked);
            updateActionButtons();
        }
    });

    // LDAP Form
    const ldapForm = document.getElementById('ldapSearchForm');
    if (ldapForm) {
        ldapForm.addEventListener('submit', (e) => {
            e.preventDefault();
            searchLDAP();
        });
    }

    // Status & Role Toggles Live Text
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('js-status-toggle') || e.target.classList.contains('js-role-toggle')) {
            const isRole = e.target.classList.contains('js-role-toggle');
            const labelOn = e.target.dataset.onLabel || (isRole ? 'Administrador' : 'Activo');
            const labelOff = e.target.dataset.offLabel || (isRole ? 'Usuario' : 'Inactivo');
            const targetId = e.target.dataset.targetId;
            
            if (targetId) {
                const textEl = document.getElementById(targetId);
                if (textEl) textEl.textContent = e.target.checked ? labelOn : labelOff;
            }

            // If it's a role toggle, update the hidden input
            if (isRole) {
                const hiddenInputId = e.target.id.replace('Toggle', '');
                const hiddenInput = document.getElementById(hiddenInputId);
                if (hiddenInput) {
                    hiddenInput.value = e.target.checked ? 'administrador' : 'usuario';
                }
            }
        }
    });
});

// ─── CRUD Logic ───

function changeUserStep(step) {
    const s1 = document.getElementById('addUserStep1');
    const s2 = document.getElementById('addUserStep2');
    const progress = document.getElementById('addUserStepProgress');
    const btnBack = document.getElementById('btnAddUserBack');
    const btnNext = document.getElementById('btnAddUserNext');
    const btnSubmit = document.getElementById('btnAddUserSubmit');
    const btnCancel = document.getElementById('btnAddUserCancel');

    if (step === 2) {
        // Validation for step 1
        if (typeof validateNexusForm === 'function' && !validateNexusForm('addUserStep1')) return;
        
        s1.classList.add('hidden');
        s2.classList.remove('hidden');
        progress.style.width = '100%';
        btnBack.classList.remove('hidden');
        btnNext.classList.add('hidden');
        btnSubmit.classList.remove('hidden');
        btnCancel.classList.add('hidden');
    } else {
        s1.classList.remove('hidden');
        s2.classList.add('hidden');
        progress.style.width = '0%';
        btnBack.classList.add('hidden');
        btnNext.classList.remove('hidden');
        btnSubmit.classList.add('hidden');
        btnCancel.classList.remove('hidden');
    }
}

async function saveNewUser(event) {
    if (event) event.preventDefault();
    
    const form = document.getElementById('addUserForm');
    if (!form) return;

    // Validation for step 1 was done in changeUserStep, but let's be sure
    if (typeof validateNexusForm === 'function' && !validateNexusForm('addUserStep1')) return;

    const fd = new FormData(form);
    // Add areas manually as JSON
    const areasInput = document.getElementById('selectedUserAreasInput');
    const areas = areasInput ? areasInput.value : '[]';
    fd.set('areas', areas);
    
    fd.set('status', (statusToggle && statusToggle.checked) ? 'Activo' : 'Inactivo');

    const procModal = document.getElementById('processingModal');
    if (procModal) {
        procModal.classList.remove('hidden');
        procModal.classList.add('flex');
        setTimeout(() => procModal.classList.add('show'), 50);
    }

    try {
        const res = await fetch('/admin/add-user', { 
            method: 'POST', 
            body: fd,
            headers: { 'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '' }
        });
        const data = await res.json();
        
        if (data.success) {
            startSuccessCountdown("El nuevo usuario ha sido registrado y configurado exitosamente en el ecosistema.");
        } else {
            showToast(data.error || 'Fallo al registrar usuario', 'error');
        }
    } catch (e) {
        console.error("Save User Error:", e);
        showToast('Error de red al registrar usuario', 'error');
    }
}

async function editSelectedUser() {
    const checked = document.querySelector('.user-checkbox:checked');
    if (!checked) return;
    const user = allUsersData.find(u => u.id == checked.value);
    if (!user) return;

    const form = document.getElementById('editUserForm');
    if (form) form.reset();

    currentEditUserId = user.id;
    console.log("Nexus Debug: Opening edit modal for User ID:", currentEditUserId);
    
    document.getElementById('editUserId').value = user.id;
    document.getElementById('editUserNameDisplay').innerText = user.name + ' (' + user.email + ')';
    // Use setTimeout to ensure the modal is ready and no other resets are pending
    setTimeout(() => {
        const stEl = document.getElementById('editUserStatusToggle');
        if (stEl) {
            const isActive = (user.status || '').toLowerCase() === 'activo';
            $(stEl).prop('checked', isActive).trigger('change');
            
            const statusText = document.getElementById('editUserStatusText');
            if (statusText) statusText.textContent = isActive ? 'Activo' : 'Inactivo';
        }

        // Map other fields inside timeout for safety
        const roleToggle = document.getElementById('editUserRoleToggle');
        const roleInput = document.getElementById('editUserRole');
        const roleText = document.getElementById('editUserRoleText');
        if (roleToggle && roleInput) {
            const isAdmin = (user.role || '').toLowerCase() === 'administrador';
            $(roleToggle).prop('checked', isAdmin).trigger('change');
            roleInput.value = isAdmin ? 'administrador' : 'usuario';
            if (roleText) roleText.textContent = isAdmin ? 'Administrador' : 'Usuario';
        }
        
        // Password visibility for local users
        const passSection = document.getElementById('editUserPasswordSection');
        if (passSection) {
            if (user.source === 'local') {
                passSection.classList.remove('hidden');
                document.getElementById('editUserPassword').value = '';
                document.getElementById('editUserPasswordConfirm').value = '';
            } else {
                passSection.classList.add('hidden');
            }
        }
    }, 50);

    await refreshPicklistAreas('editUser', user.areas || []);
    openModal('editUserModal');
}

async function saveUserChanges() {
    let userId = document.getElementById('editUserId').value;
    if (!userId) userId = currentEditUserId;
    
    console.log("Nexus Debug: Attempting to save User ID:", userId);

    if (!userId) {
        return showToast('Error crítico: No se identificó al usuario (ID faltante).', 'error');
    }
    
    const form = document.getElementById('editUserForm');
    const fd = new FormData(form);
    const areas = document.getElementById('editSelectedUserAreasInput').value;
    fd.set('areas', areas);
    fd.set('status', document.getElementById('editUserStatusToggle').checked ? 'Activo' : 'Inactivo');

    // Password Validation: Require BOTH if either is touched
    const pass = document.getElementById('editUserPassword').value;
    const confirm = document.getElementById('editUserPasswordConfirm').value;
    
    if (pass || confirm) {
        if (!pass || !confirm) {
            return showToast('Para cambiar la contraseña, debe completar ambos campos.', 'warning');
        }
        if (pass !== confirm) {
            return showToast('Las contraseñas no coinciden.', 'error');
        }
        if (pass.length < 6) {
            return showToast('La nueva contraseña debe tener al menos 6 caracteres.', 'error');
        }
    }

    // 1. Show Processing Modal
    const procModal = document.getElementById('processingModal');
    const procMsg = document.getElementById('procMessage');
    if (procModal) {
        procModal.classList.remove('hidden');
        procModal.classList.add('flex');
    }

    try {
        const res = await fetch(`/admin/edit-user/${userId}`, { 
            method: 'POST', 
            body: fd,
            headers: { 'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '' }
        });
        
        const data = await res.json();
        
        if (procModal) procModal.classList.add('hidden');

        if (data.success) {
            startSuccessCountdown("El perfil del usuario ha sido actualizado exitosamente.");
        } else {
            showToast(data.error || 'Error al actualizar', 'error');
        }
    } catch (e) {
        if (procModal) procModal.classList.add('hidden');
        console.error("Edit User Error:", e);
        showToast('Error de red al actualizar usuario', 'error');
    }
}

function deleteSelectedUsers() {
    const checked = document.querySelectorAll('.user-checkbox:checked');
    if (checked.length === 0) return;

    const count = checked.length;
    
    Swal.fire({
        title: '<span class="text-white uppercase italic font-black tracking-tighter">¿Confirmar Purga?</span>',
        html: `<div class="text-xs font-bold text-slate-300 leading-relaxed uppercase tracking-widest">
                Estás por eliminar <span class="text-rose-500 font-black">${count > 1 ? count + ' registros' : 'el registro'}</span> permanentemente.<br>
                Esta acción revocará todos los accesos vinculados de forma irreversible.
               </div>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f43f5e',
        confirmButtonText: 'Sí, Eliminar Ahora',
        cancelButtonText: 'Cancelar',
        background: '#1e293b',
        color: '#ffffff',
        backdrop: 'rgba(15, 23, 42, 0.75)'
    }).then(async (result) => {
        if (result.isConfirmed) {
            // Show Global Spinner
            const procModal = document.getElementById('processingModal');
            if (procModal) {
                procModal.classList.remove('hidden');
                procModal.classList.add('flex');
                setTimeout(() => procModal.classList.add('show'), 50);
            }

            const ids = Array.from(checked).map(cb => cb.value);
            let errors = 0;
            
            for (let id of ids) {
                try {
                    const res = await fetch(`/admin/delete-user/${id}`, { 
                        method: 'POST',
                        headers: { 'X-CSRFToken': CSRF_TOKEN }
                    });
                    const d = await res.json();
                    if (!d.success) errors++;
                } catch(e) { errors++; }
            }
            
            if (errors === 0) {
                startSuccessCountdown("Los registros de usuario y sus accesos asociados han sido purgados permanentemente del sistema.");
            } else {
                if (procModal) procModal.classList.add('hidden');
                showToast(`Se eliminaron algunos usuarios pero hubo ${errors} fallas.`, 'warning');
                setTimeout(() => location.reload(), 1500);
            }
        }
    });
}

// ─── Access Management ───

var currentAccessUserId = null;
async function openSelectedUserAccess() {
    const checked = document.querySelector('.user-checkbox:checked');
    if (!checked) return;
    
    currentAccessUserId = checked.value;
    const user = allUsersData.find(u => u.id == currentAccessUserId);
    
    document.getElementById('accessUserName').textContent = `Usuario: ${user.name || user.email}`;
    
    const availList = document.getElementById('accessAvailableList');
    const selectedList = document.getElementById('accessSelectedList');
    
    availList.innerHTML = '<div class="flex items-center justify-center h-full"><i class="fas fa-circle-notch fa-spin text-primary"></i></div>';
    selectedList.innerHTML = '';
    
    openModal('userAccessModal');

    try {
        const res = await fetch(`/admin/user-access/${currentAccessUserId}`);
        const data = await res.json();
        
        if (data.success) {
            window.__allPlatforms = data.platforms || [];
            availList.innerHTML = '';
            selectedList.innerHTML = '';

            data.platforms.forEach(p => {
                const card = createPlatformAccessCard(p, p.has_access);
                if (p.has_access) selectedList.appendChild(card);
                else availList.appendChild(card);
            });
            updateAccessHiddenInput();
        }
    } catch (e) {
        showToast('Error al cargar accesos', 'error');
    }
}

function createPlatformAccessCard(p, isSelected) {
    const card = document.createElement('div');
    card.className = 'group flex items-center gap-3 p-3 rounded-xl border border-panel-border bg-surface-container/20 hover:border-primary/40 hover:bg-primary/5 transition-all cursor-pointer select-none picklist-card-premium' + (isSelected ? ' ring-1 ring-primary/20' : '');
    card.setAttribute('data-action', 'users-toggle-access');
    card.setAttribute('data-platform-name', p.name);
    card.setAttribute('data-is-selected', isSelected);
    
    card.innerHTML = `
        <div class="w-10 h-10 rounded-lg flex items-center justify-center text-white shadow-lg flex-shrink-0" style="background: ${p.bg_color || '#334155'}">
            <i class="fas fa-layer-group text-[14px]"></i>
        </div>
        <div class="flex-grow min-w-0 flex flex-col">
            <div class="flex items-center gap-2 mb-1">
                <span class="text-[11px] font-black text-label uppercase tracking-tighter truncate card-name">${p.name}</span>
            </div>
            <div class="flex items-center">
                <span class="px-2 py-0.5 rounded-md bg-panel-border/30 text-[9px] font-black text-label/60 uppercase tracking-widest border border-panel-border/50">
                    <i class="fas fa-tag text-[7px] mr-1 opacity-50"></i> ${p.area_name || 'General'}
                </span>
            </div>
        </div>
        <div class="w-8 h-8 rounded-full border border-panel-border group-hover:border-primary/40 flex items-center justify-center text-label/20 group-hover:text-primary transition-all shadow-inner">
            <i class="fas ${isSelected ? 'fa-times' : 'fa-plus'} text-xs"></i>
        </div>
    `;
    return card;
}

function toggleUserAccess(platformName, isSelected) {
    const availList = document.getElementById('accessAvailableList');
    const selectedList = document.getElementById('accessSelectedList');
    const platforms = window.__allPlatforms || [];
    const platform = platforms.find(p => p.name === platformName);
    if (!platform) return;

    const isNowSelected = !isSelected;
    const currentList = isSelected ? selectedList : availList;
    const targetList = isNowSelected ? selectedList : availList;

    // Find and remove
    const items = Array.from(currentList.children);
    const itemToMove = items.find(el => el.querySelector('.card-name').textContent === platformName);
    if (itemToMove) itemToMove.remove();

    // Add to target
    const newCard = createPlatformAccessCard(platform, isNowSelected);
    targetList.appendChild(newCard);
    
    updateAccessHiddenInput();
}

function updateAccessHiddenInput() {
    const selected = Array.from(document.querySelectorAll('#accessSelectedList .card-name')).map(el => el.textContent);
    const platforms = window.__allPlatforms || [];
    const ids = selected.map(name => {
        const p = platforms.find(pl => pl.name === name);
        return p ? p.id : null;
    }).filter(id => id !== null);
    
    const input = document.getElementById('selectedUserPlatformsInput');
    if (input) input.value = JSON.stringify(ids);
}

async function saveUserPlatformAccess() {
    if (!currentAccessUserId) return;
    const val = document.getElementById('selectedUserPlatformsInput').value;
    const platformIds = JSON.parse(val || '[]');

    const procModal = document.getElementById('processingModal');
    if (procModal) {
        procModal.classList.remove('hidden');
        procModal.classList.add('flex');
        setTimeout(() => procModal.classList.add('show'), 50);
    }

    try {
        const res = await fetch(`/admin/update-user-access/${currentAccessUserId}`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ platform_ids: platformIds })
        });
        const data = await res.json();
        if (data.success) {
            startSuccessCountdown("Los permisos de acceso a las plataformas han sido sincronizados correctamente.");
        } else {
            showToast(data.error || 'Error al actualizar accesos', 'error');
        }
    } catch (err) { 
        showToast('Error de red', 'error');
    }
}

// ─── LDAP Logic ───

async function searchLDAP() {
    const query = document.getElementById('ldapQuery').value.trim();
    if (!query) return;

    const resultsList = document.getElementById('ldapResultsList');
    const container = document.getElementById('ldapResultsContainer');
    
    container.classList.remove('hidden');
    resultsList.innerHTML = '<div class="text-center py-8 opacity-40"><i class="fas fa-circle-notch fa-spin text-xl mb-4"></i><p class="text-[10px] uppercase font-black tracking-widest">Consultando Directorio...</p></div>';

    try {
        const res = await fetch(`/admin/ldap-search-api?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        
        resultsList.innerHTML = '';
        if (data.success && data.users.length > 0) {
            data.users.forEach(user => {
                const item = document.createElement('div');
                item.className = 'flex items-center justify-between p-4 rounded-2xl bg-surface-container/20 border border-panel-border hover:border-primary/40 transition-all group';
                item.innerHTML = `
                    <div class="flex items-center gap-4">
                        <div class="w-10 h-10 rounded-xl bg-primary/20 text-primary flex items-center justify-center font-black">
                            ${(user.displayName || user.cn || 'U').charAt(0)}
                        </div>
                        <div>
                            <div class="text-[12px] font-black text-label uppercase italic tracking-tighter">${user.displayName || user.cn}</div>
                            <div class="text-[10px] text-label/40 font-bold uppercase tracking-widest">${user.mail || 'Sin correo asociado'}</div>
                        </div>
                    </div>
                    <button class="h-10 px-4 rounded-xl bg-primary text-white text-[10px] font-black uppercase tracking-widest hover:scale-105 active:scale-95 transition-all" onclick="importLDAPUser('${user.sAMAccountName || user.uid}', '${user.displayName || user.cn}', '${user.mail || ''}')">
                        Importar
                    </button>
                `;
                resultsList.appendChild(item);
            });
        } else {
            resultsList.innerHTML = '<div class="text-center py-12 opacity-30 italic text-xs uppercase font-black">No se encontraron registros</div>';
        }
    } catch (e) {
        resultsList.innerHTML = '<div class="text-center py-12 text-rose-500 italic text-xs font-black uppercase">Fallo crítico al conectar con el servidor</div>';
    }
}

window.importLDAPUser = function(username, name, email) {
    closeModal('ldapUserModal');
    
    const sourceInput = document.getElementById('addUserAuthSource');
    if (sourceInput) sourceInput.value = 'ldap';
    
    // Hide password row for LDAP users
    const passRow = document.getElementById('addUserPassword')?.closest('.grid');
    if (passRow) {
        passRow.classList.add('hidden');
        // Disable required validation for these fields
        document.getElementById('addUserPassword').required = false;
        document.getElementById('addUserPasswordConfirm').required = false;
    }

    openModal('addUserModal');
    changeUserStep(1);
    
    document.getElementById('addUserName').value = name;
    document.getElementById('addUserEmail').value = email || username;
    
    // Hint that it is LDAP
    showToast(`Datos de ${username} cargados`, 'info');
};


// ─── Areas Management Logic (New Dedicated Flow) ───

let currentManagementUserId = null;

async function openUserAreasModal() {
    const checked = document.querySelector('.user-checkbox:checked');
    if (!checked) return;
    const user = allUsersData.find(u => u.id == checked.value);
    if (!user) return;

    currentManagementUserId = user.id;
    document.getElementById('areasUserName').innerText = user.name;
    
    renderManagementAreas(user);
    openModal('userAreasModal');
}

function renderManagementAreas(user) {
    const allAreas = window.__areaData || [];
    const userAreaNames = (user.areas || []).map(a => a.name || a);
    
    const availList = document.getElementById('areasAvailableList');
    const selectedList = document.getElementById('areasSelectedList');
    const hiddenInput = document.getElementById('selectedManagementAreasInput');
    
    if (availList && selectedList) {
        availList.innerHTML = '';
        selectedList.innerHTML = '';
        
        allAreas.forEach(area => {
            const isSelected = userAreaNames.includes(area.name);
            const card = createAreaManagementCard(area, isSelected);
            if (isSelected) selectedList.appendChild(card);
            else availList.appendChild(card);
        });
        
        if (hiddenInput) {
            const userAreaIds = (user.areas || []).map(a => a.id);
            hiddenInput.value = JSON.stringify(userAreaIds);
        }
    }
}

function createAreaManagementCard(area, isSelected) {
    const card = document.createElement('div');
    card.className = `flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer group hover:scale-[1.02] active:scale-95 ${isSelected ? 'bg-violet-500/10 border-violet-500/30' : 'bg-surface-container/20 border-panel-border hover:border-violet-500/40'}`;
    card.onclick = () => toggleManagementArea(area.name, isSelected);
    
    card.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center text-white" style="background: ${area.color || '#6366f1'}">
                <i class="fas fa-${area.icon || 'box'} text-xs"></i>
            </div>
            <div>
                <div class="text-[11px] font-black uppercase italic tracking-tighter ${isSelected ? 'text-violet-400' : 'text-label'} card-name">${area.name}</div>
            </div>
        </div>
        <div class="w-6 h-6 rounded-full border border-panel-border group-hover:border-violet-500/40 flex items-center justify-center text-label/20 group-hover:text-violet-500 transition-all shadow-inner">
            <i class="fas ${isSelected ? 'fa-times' : 'fa-plus'} text-[10px]"></i>
        </div>
    `;
    return card;
}

function toggleManagementArea(areaName, isSelected) {
    const availList = document.getElementById('areasAvailableList');
    const selectedList = document.getElementById('areasSelectedList');
    const allAreas = window.__areaData || [];
    const area = allAreas.find(a => a.name === areaName);
    if (!area) return;

    const isNowSelected = !isSelected;
    const currentList = isSelected ? selectedList : availList;
    
    // Remove from current
    const items = Array.from(currentList.children);
    const itemToMove = items.find(el => el.querySelector('.card-name').textContent === areaName);
    if (itemToMove) itemToMove.remove();

    // Add to target
    const targetList = isNowSelected ? selectedList : availList;
    const newCard = createAreaManagementCard(area, isNowSelected);
    targetList.appendChild(newCard);
    
    // Update hidden input
    const selectedIds = Array.from(document.querySelectorAll('#areasSelectedList .card-name')).map(el => {
        const name = el.textContent;
        const a = allAreas.find(areaObj => areaObj.name === name);
        return a ? a.id : null;
    }).filter(id => id !== null);
    
    document.getElementById('selectedManagementAreasInput').value = JSON.stringify(selectedIds);
}

async function saveUserAreas() {
    if (!currentManagementUserId) return;
    const val = document.getElementById('selectedManagementAreasInput').value;
    const areaIds = JSON.parse(val || '[]');

    const procModal = document.getElementById('processingModal');
    if (procModal) {
        procModal.classList.remove('hidden');
        procModal.classList.add('flex');
        setTimeout(() => procModal.classList.add('show'), 50);
    }

    try {
        const res = await fetch(`/admin/update-user-areas/${currentManagementUserId}`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ area_ids: areaIds })
        });
        const data = await res.json();
        if (data.success) {
            startSuccessCountdown("La asignación estructural de áreas de trabajo ha sido actualizada. Se han sincronizado los accesos en cascada.");
        } else {
            showToast(data.error || 'Error al actualizar áreas', 'error');
        }
    } catch (err) { 
        showToast('Error de red', 'error');
    }
}

function changeUserPage(offset) {
    currentPage += offset;
    renderUsersTable();
}

// Attach New Listeners
document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const action = btn.getAttribute('data-action');

    if (action === 'users-open-areas') openUserAreasModal();
    if (action === 'users-close-areas-modal') closeModal('userAreasModal');
    if (action === 'users-save-areas') saveUserAreas();
});
