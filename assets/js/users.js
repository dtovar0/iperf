/**
 * Users Management Interactivity - Nexus Premium Edition
 * Simplified: Removed Areas and Access management.
 */

// Global state
var currentPage = 1;
var rowsPerPage = 10;
var currentFilteredUsers = [];
var currentEditUserId = null;

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

        tbody.innerHTML = `<tr><td colspan="6">${createPremiumEmptyState(title, text, icon)}</td></tr>`;
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
                <span class="nx-badge ${statusCls}">${user.status.toUpperCase()}</span>
            </td>
        `;
        
        tr.addEventListener('click', (e) => {
            if (e.target.type === 'checkbox') return;
            document.querySelectorAll('.user-checkbox').forEach(c => c.checked = false);
            const cb = tr.querySelector('.user-checkbox');
            if (cb) {
                cb.checked = true;
                updateActionButtons();
                const editBtn = document.querySelector('[data-action="users-edit-selected"]');
                if (editBtn) editBtn.click();
            }
        });

        tbody.appendChild(tr);
    });

    renderGhostRows(6); // 6 columns
    renderPagination();
    updateActionButtons();
}

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
        
        let cells = '';
        for(let c=0; c<columns; c++) cells += '<td class="text-center"><div></div></td>';
        tr.innerHTML = cells;
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

    if (btnEdit) btnEdit.disabled = (checkedCount !== 1);
    if (btnDelete) btnDelete.disabled = (checkedCount === 0);
    
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

    document.getElementById('usersTableBody')?.addEventListener('change', (e) => {
        if (e.target.classList.contains('user-checkbox')) {
            updateActionButtons();
        }
    });

    document.addEventListener('click', (event) => {
        const trigger = event.target.closest('[data-action]');
        if (!trigger) return;

        const action = trigger.getAttribute('data-action');

        if (action === 'users-edit-selected') return editSelectedUser();
        if (action === 'users-delete-selected') return deleteSelectedUsers();
        if (action === 'users-close-edit-modal') return closeModal('editUserModal');
        if (action === 'users-close-add-modal') return closeModal('addUserModal');
        if (action === 'users-submit-new') return saveNewUser(event);
        
        if (action === 'users-open-type-modal') return openModal('userTypeModal');
        if (action === 'users-close-type-modal') return closeModal('userTypeModal');
        if (action === 'users-open-local-flow') {
            closeModal('userTypeModal');
            setTimeout(() => {
                const form = document.querySelector('#addUserModal form');
                if (form) {
                    form.reset();
                    $(form.querySelector('#addUserStatusToggle')).prop('checked', true).trigger('change');
                    $(form.querySelector('#addUserRoleToggle')).prop('checked', false).trigger('change');
                    const roleInput = document.getElementById('addUserRole');
                    if (roleInput) roleInput.value = 'usuario';
                }
            }, 50);
            
            const sourceInput = document.getElementById('addUserAuthSource');
            if (sourceInput) sourceInput.value = 'local';
            
            const passRow = document.getElementById('addUserPassword')?.closest('.grid');
            if (passRow) passRow.classList.remove('hidden');
            document.getElementById('addUserPassword').required = true;
            document.getElementById('addUserPasswordConfirm').required = true;

            openModal('addUserModal');
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
        if (action === 'users-change-page') {
            currentPage += parseInt(trigger.dataset.offset);
            renderUsersTable();
            return;
        }
        
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

async function saveNewUser(event) {
    if (event) event.preventDefault();
    const form = document.getElementById('addUserForm');
    if (!form || (typeof validateNexusForm === 'function' && !validateNexusForm('addUserStep1'))) return;

    const fd = new FormData(form);
    fd.set('status', document.getElementById('addUserStatusToggle').checked ? 'Activo' : 'Inactivo');

    const procModal = document.getElementById('processingModal');
    if (procModal) { procModal.classList.remove('hidden'); procModal.classList.add('flex'); }

    try {
        const res = await fetch('/admin/add-user', { 
            method: 'POST', body: fd,
            headers: { 'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '' }
        });
        const data = await res.json();
        if (data.success) startSuccessCountdown("Usuario registrado exitosamente.");
        else showToast(data.error || 'Error al registrar', 'error');
    } catch (e) { showToast('Error de red', 'error'); }
}

async function editSelectedUser() {
    const checked = document.querySelector('.user-checkbox:checked');
    if (!checked) return;
    const user = allUsersData.find(u => u.id == checked.value);
    if (!user) return;

    const form = document.getElementById('editUserForm');
    if (form) form.reset();

    currentEditUserId = user.id;
    document.getElementById('editUserId').value = user.id;
    document.getElementById('editUserNameDisplay').innerText = user.name + ' (' + user.email + ')';
    
    setTimeout(() => {
        const isActive = (user.status || '').toLowerCase() === 'activo';
        $('#editUserStatusToggle').prop('checked', isActive).trigger('change');
        
        const isAdmin = (user.role || '').toLowerCase() === 'administrador';
        $('#editUserRoleToggle').prop('checked', isAdmin).trigger('change');
        
        const passSection = document.getElementById('editUserPasswordSection');
        if (passSection) user.source === 'local' ? passSection.classList.remove('hidden') : passSection.classList.add('hidden');
    }, 50);

    openModal('editUserModal');
}

async function saveUserChanges() {
    const userId = document.getElementById('editUserId').value || currentEditUserId;
    if (!userId) return showToast('ID faltante', 'error');
    
    const form = document.getElementById('editUserForm');
    const fd = new FormData(form);
    fd.set('status', document.getElementById('editUserStatusToggle').checked ? 'Activo' : 'Inactivo');

    const pass = document.getElementById('editUserPassword').value;
    const confirm = document.getElementById('editUserPasswordConfirm').value;
    if ((pass || confirm) && (pass !== confirm || pass.length < 6)) return showToast('Error en contraseña', 'error');

    const procModal = document.getElementById('processingModal');
    if (procModal) { procModal.classList.remove('hidden'); procModal.classList.add('flex'); }

    try {
        const res = await fetch(`/admin/edit-user/${userId}`, { 
            method: 'POST', body: fd,
            headers: { 'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '' }
        });
        const data = await res.json();
        if (data.success) startSuccessCountdown("Perfil actualizado.");
        else showToast(data.error || 'Error al actualizar', 'error');
    } catch (e) { showToast('Error de red', 'error'); }
}

function deleteSelectedUsers() {
    const checked = document.querySelectorAll('.user-checkbox:checked');
    if (checked.length === 0) return;

    Swal.fire({
        title: '¿Confirmar Eliminación?',
        text: `Se eliminarán ${checked.length} registros permanentemente.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f43f5e',
        background: '#1e293b', color: '#ffffff'
    }).then(async (result) => {
        if (result.isConfirmed) {
            const ids = Array.from(checked).map(cb => cb.value);
            for (let id of ids) {
                await fetch(`/admin/delete-user/${id}`, { method: 'POST', headers: { 'X-CSRFToken': CSRF_TOKEN } });
            }
            location.reload();
        }
    });
}

async function searchLDAP() {
    const q = document.getElementById('ldapQuery').value;
    const container = document.getElementById('ldapResultsContainer');
    const list = document.getElementById('ldapResultsList');
    if(!q) return;

    list.innerHTML = '<div class="p-8 text-center"><i class="fas fa-circle-notch fa-spin text-primary text-2xl"></i></div>';
    container.classList.remove('hidden');

    try {
        const res = await fetch(`/admin/ldap-search-api?q=${q}`);
        const data = await res.json();
        list.innerHTML = '';
        if (data.success && data.users.length) {
            data.users.forEach(u => {
                const div = document.createElement('div');
                div.className = "p-4 border border-panel-border rounded-xl hover:bg-primary/5 cursor-pointer flex justify-between items-center group transition-all";
                div.innerHTML = `<div><div class="font-black text-primary text-sm uppercase">${u.displayName}</div><div class="text-[10px] text-label/40 font-bold uppercase">${u.mail || u.sAMAccountName}</div></div><i class="fas fa-plus text-label/20 group-hover:text-primary transition-colors"></i>`;
                div.onclick = () => importLDAPUser(u);
                list.appendChild(div);
            });
        } else list.innerHTML = '<div class="p-8 text-center text-label/40 font-bold uppercase text-xs">No se encontraron resultados</div>';
    } catch(e) { showToast('Error LDAP', 'error'); }
}

function importLDAPUser(u) {
    closeModal('ldapUserModal');
    setTimeout(() => {
        const form = document.querySelector('#addUserModal form');
        if (form) {
            form.reset();
            document.getElementById('addUserAuthSource').value = 'ldap';
            document.getElementById('addUserName').value = u.displayName;
            document.getElementById('addUserEmail').value = u.mail || u.sAMAccountName;
            document.getElementById('addUserPassword').closest('.grid').classList.add('hidden');
            document.getElementById('addUserPassword').required = false;
            document.getElementById('addUserPasswordConfirm').required = false;
        }
        openModal('addUserModal');
    }, 50);
}
