/**
 * Iperf3 Servers Management - Nexus Premium Edition
 * CRUD completo para gestión de servidores iperf3 remotos.
 */

// ── Estado Global ────────────────────────────────────────────────────────────
var srvCurrentPage = 1;
var srvFilteredServers = [];
var srvCurrentEditId = null;

// ── Utilidades ───────────────────────────────────────────────────────────────

function generateSecureToken(length = 32) {
    const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, b => charset[b % charset.length]).join('');
}

function createServerEmptyState(title, text, iconClass = 'fa-server') {
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

// ── Renderizado de Tabla ─────────────────────────────────────────────────────

function getServerPageLength() {
    const h = window.innerHeight;
    return h < 900 ? 9 : 10;
}

function handleServerSearch() {
    const term = document.getElementById('serverSearch').value.toLowerCase();
    if (typeof allServersData === 'undefined') return;
    
    srvFilteredServers = allServersData.filter(s => {
        const name = (s.name || '').toLowerCase();
        const host = (s.host || '').toLowerCase();
        return name.includes(term) || host.includes(term);
    });
    
    srvCurrentPage = 1;
    renderServersTable();
}

function renderServersTable() {
    const tbody = document.getElementById('serversTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const rowsPerPage = getServerPageLength();
    const pageData = srvFilteredServers.slice((srvCurrentPage - 1) * rowsPerPage, srvCurrentPage * rowsPerPage);

    if (pageData.length === 0) {
        const isSearch = document.getElementById('serverSearch')?.value.trim() !== "";
        const icon = isSearch ? 'fa-search' : 'fa-server';
        const title = isSearch ? 'Sin resultados' : 'Sin Servidores';
        const text = isSearch ? 'No encontramos servidores con ese criterio.' : 'Registre un servidor para comenzar.';

        tbody.innerHTML = `<tr><td colspan="5">${createServerEmptyState(title, text, icon)}</td></tr>`;
        renderServerPagination();
        return;
    }

    pageData.forEach(server => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-primary/5 transition-all group cursor-pointer";
        
        const statusCls = server.status === 'Activo' ? 'nx-badge-success' : 'nx-badge-error';
        const tokenDisplay = server.token 
            ? `<span class="font-mono text-[11px] font-bold text-emerald-500/70 bg-emerald-500/10 px-2 py-0.5 rounded-md">${server.token.substring(0, 12)}•••</span>` 
            : '<span class="opacity-10 text-[10px] font-black uppercase tracking-widest">—</span>';

        tr.innerHTML = `
            <td class="text-center" style="border-left:3px solid transparent;padding:0 1.25rem 0 1rem;">
                <div class="flex items-center justify-center">
                    <input type="checkbox" class="server-checkbox w-5 h-5 rounded-md border-2 border-primary/30 text-primary focus:ring-primary/20 cursor-pointer transition-all" value="${server.id}">
                </div>
            </td>
            <td>
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
                        <i class="fas fa-server text-xs"></i>
                    </div>
                    <span class="text-[15px] font-black text-label uppercase italic tracking-tighter truncate">${server.name}</span>
                </div>
            </td>
            <td>
                <span class="text-[13px] font-bold text-label/60 font-mono tracking-wide truncate">${server.host}</span>
            </td>
            <td>${tokenDisplay}</td>
            <td class="text-center">
                <span class="nx-badge ${statusCls}">${server.status.toUpperCase()}</span>
            </td>
        `;
        
        tr.addEventListener('click', (e) => {
            if (e.target.type === 'checkbox') return;
            document.querySelectorAll('.server-checkbox').forEach(c => c.checked = false);
            const cb = tr.querySelector('.server-checkbox');
            if (cb) {
                cb.checked = true;
                updateServerActionButtons();
                const editBtn = document.querySelector('[data-action="servers-edit-selected"]');
                if (editBtn) editBtn.click();
            }
        });

        tbody.appendChild(tr);
    });

    renderServerGhostRows(5);
    renderServerPagination();
    updateServerActionButtons();
}

function renderServerGhostRows(columns) {
    const tbody = document.getElementById('serversTableBody');
    if (!tbody) return;
    
    const pageLen = getServerPageLength();
    const realRows = tbody.children.length;
    const ghostCount = pageLen - realRows;
    
    if (ghostCount <= 0) return;

    for (let i = 0; i < ghostCount; i++) {
        const tr = document.createElement('tr');
        tr.className = "ghost-row pointer-events-none select-none border-b border-panel-border/10";
        tr.style.height = "var(--row-h, 60px)";
        
        let cells = '';
        for (let c = 0; c < columns; c++) {
            cells += `<td><div></div></td>`;
        }
        tr.innerHTML = cells;
        tbody.appendChild(tr);
    }
}

function renderServerPagination() {
    const container = document.getElementById('serversPagination');
    if (!container) return;
    
    const rowsPerPage = getServerPageLength();
    const totalPages = Math.ceil(srvFilteredServers.length / rowsPerPage);
    const start = srvFilteredServers.length ? (srvCurrentPage - 1) * rowsPerPage + 1 : 0;
    const end = Math.min(srvFilteredServers.length, srvCurrentPage * rowsPerPage);

    container.innerHTML = `
        <div class="dt-layout-row" style="display: flex !important; align-items: center; justify-content: space-between; height: 52px !important; padding: 0 1.25rem !important; border-top: 1px solid rgb(var(--color-panel-border) / 0.4) !important;">
            <div class="dt-layout-cell dt-layout-start">
                <div class="dt-info" style="font-size: 13px !important; font-weight: 800 !important; color: rgb(var(--color-text-body)) !important;">
                    Mostrando ${start}-${end} de ${srvFilteredServers.length} servidores
                </div>
            </div>
            <div class="dt-layout-cell dt-layout-end">
                <div class="dt-paging paging_simple">
                    <button class="dt-paging-button previous ${srvCurrentPage === 1 ? 'disabled' : ''}" 
                        data-action="servers-change-page" data-offset="-1" ${srvCurrentPage === 1 ? 'disabled' : ''}>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"></path></svg>
                    </button>
                    <button class="dt-paging-button next ${srvCurrentPage >= totalPages ? 'disabled' : ''}" 
                        data-action="servers-change-page" data-offset="1" ${srvCurrentPage >= totalPages ? 'disabled' : ''}>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"></path></svg>
                    </button>
                </div>
            </div>
        </div>
    `;
}

function updateServerActionButtons() {
    const rows = document.querySelectorAll('#serversTableBody tr:not(.ghost-row)');
    let checkedCount = 0;
    let totalCheckboxes = 0;

    rows.forEach(tr => {
        const cb = tr.querySelector('.server-checkbox');
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

    const btnEdit = document.getElementById('btnEditServer');
    const btnDelete = document.getElementById('btnDeleteServer');

    if (btnEdit) btnEdit.disabled = (checkedCount !== 1);
    if (btnDelete) btnDelete.disabled = (checkedCount === 0);
    
    const selectAll = document.getElementById('selectAllServers');
    if (selectAll) {
        selectAll.checked = (totalCheckboxes > 0 && checkedCount === totalCheckboxes);
        selectAll.indeterminate = (checkedCount > 0 && checkedCount < totalCheckboxes);
    }
}

function changeServerPage(offset) {
    const rowsPerPage = getServerPageLength();
    const totalPages = Math.ceil(srvFilteredServers.length / rowsPerPage);
    const newPage = srvCurrentPage + offset;
    if (newPage >= 1 && newPage <= totalPages) {
        srvCurrentPage = newPage;
        renderServersTable();
    }
}

// ── CRUD Operations ──────────────────────────────────────────────────────────

async function saveNewServer() {
    const name = document.getElementById('addServerName').value.trim();
    const host = document.getElementById('addServerHost').value.trim();
    const statusToggle = document.getElementById('addServerStatusToggle');
    const token = document.getElementById('addServerToken').value.trim();

    if (!name || !host) {
        return showToast('Nombre y Host son obligatorios.', 'error');
    }

    const payload = {
        name: name,
        host: host,
        status: statusToggle && statusToggle.checked ? 'Activo' : 'Inactivo',
        token: token
    };

    try {
        const res = await fetch('/iperf/api/add-server', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : ''
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (data.success) {
            closeModal('addServerModal');
            showToast('Servidor registrado exitosamente.', 'success');
            // Agregar a la data local y refrescar
            allServersData.unshift(data.server);
            srvFilteredServers = [...allServersData];
            renderServersTable();
        } else {
            showToast(data.error || 'Error al registrar servidor.', 'error');
        }
    } catch (e) {
        console.error("Add Server Error:", e);
        showToast('Error de red al registrar servidor.', 'error');
    }
}

function editSelectedServer() {
    const checked = document.querySelector('.server-checkbox:checked');
    if (!checked) return;
    const server = allServersData.find(s => s.id == checked.value);
    if (!server) return;

    srvCurrentEditId = server.id;

    document.getElementById('editServerId').value = server.id;
    document.getElementById('editServerNameDisplay').textContent = `${server.name} (${server.host})`;
    document.getElementById('editServerName').value = server.name;
    document.getElementById('editServerHost').value = server.host;
    document.getElementById('editServerToken').value = server.token || '';

    // Status toggle
    const statusToggle = document.getElementById('editServerStatusToggle');
    const statusText = document.getElementById('editServerStatusText');
    if (statusToggle) {
        statusToggle.checked = (server.status === 'Activo');
        if (statusText) statusText.textContent = server.status;
    }

    openModal('editServerModal');
}

async function saveServerChanges() {
    const id = document.getElementById('editServerId').value || srvCurrentEditId;
    if (!id) return showToast('ID de servidor no encontrado.', 'error');

    const statusToggle = document.getElementById('editServerStatusToggle');

    const payload = {
        name: document.getElementById('editServerName').value.trim(),
        host: document.getElementById('editServerHost').value.trim(),
        status: statusToggle && statusToggle.checked ? 'Activo' : 'Inactivo',
        token: document.getElementById('editServerToken').value.trim()
    };

    if (!payload.name || !payload.host) {
        return showToast('Nombre y Host son obligatorios.', 'error');
    }

    try {
        const res = await fetch(`/iperf/api/edit-server/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : ''
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (data.success) {
            closeModal('editServerModal');
            showToast('Servidor actualizado exitosamente.', 'success');
            // Actualizar en la data local
            const idx = allServersData.findIndex(s => s.id == id);
            if (idx !== -1) allServersData[idx] = data.server;
            srvFilteredServers = [...allServersData];
            renderServersTable();
        } else {
            showToast(data.error || 'Error al actualizar servidor.', 'error');
        }
    } catch (e) {
        console.error("Edit Server Error:", e);
        showToast('Error de red al actualizar servidor.', 'error');
    }
}

function deleteSelectedServers() {
    const checked = document.querySelectorAll('.server-checkbox:checked');
    if (checked.length === 0) return;

    const count = checked.length;
    
    Swal.fire({
        title: '<span class="text-white uppercase italic font-black tracking-tighter">¿Eliminar Servidor?</span>',
        html: `<div class="text-xs font-bold text-slate-300 leading-relaxed uppercase tracking-widest">
                Estás por eliminar <span class="text-rose-500 font-black">${count > 1 ? count + ' servidores' : 'el servidor'}</span> permanentemente.<br>
                Esta acción no se puede deshacer.
               </div>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f43f5e',
        confirmButtonText: 'Sí, Eliminar',
        cancelButtonText: 'Cancelar',
        background: '#1e293b',
        color: '#ffffff',
        backdrop: 'rgba(15, 23, 42, 0.75)'
    }).then(async (result) => {
        if (result.isConfirmed) {
            const ids = Array.from(checked).map(cb => cb.value);
            let errors = 0;
            
            for (let id of ids) {
                try {
                    const res = await fetch(`/iperf/api/delete-server/${id}`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '' }
                    });
                    const d = await res.json();
                    if (d.success) {
                        allServersData = allServersData.filter(s => s.id != id);
                    } else { errors++; }
                } catch(e) { errors++; }
            }
            
            srvFilteredServers = [...allServersData];
            renderServersTable();

            if (errors === 0) {
                showToast('Servidor(es) eliminado(s) correctamente.', 'success');
            } else {
                showToast(`Hubo ${errors} error(es) al eliminar.`, 'warning');
            }
        }
    });
}

// ── Inicialización ───────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    if (typeof allServersData !== 'undefined') {
        srvFilteredServers = [...allServersData];
        renderServersTable();
    }
    
    const searchInput = document.getElementById('serverSearch');
    if (searchInput) {
        searchInput.addEventListener('input', handleServerSearch);
    }

    // Checkbox delegation
    document.getElementById('serversTableBody')?.addEventListener('change', (e) => {
        if (e.target.classList.contains('server-checkbox')) {
            updateServerActionButtons();
        }
    });

    // Action delegation
    document.addEventListener('click', (event) => {
        const trigger = event.target.closest('[data-action]');
        if (!trigger) return;

        const action = trigger.getAttribute('data-action');

        if (action === 'servers-open-add-modal') {
            // Reset form
            const form = document.getElementById('addServerForm');
            if (form) form.reset();
            document.getElementById('addServerStatusToggle').checked = true;
            document.getElementById('addServerStatusText').textContent = 'Activo';
            return openModal('addServerModal');
        }
        if (action === 'servers-close-add-modal') return closeModal('addServerModal');
        if (action === 'servers-submit-new') return saveNewServer();
        
        if (action === 'servers-edit-selected') return editSelectedServer();
        if (action === 'servers-close-edit-modal') return closeModal('editServerModal');
        if (action === 'servers-submit-edit') return saveServerChanges();
        
        if (action === 'servers-delete-selected') return deleteSelectedServers();
        
        if (action === 'servers-change-page') return changeServerPage(parseInt(trigger.dataset.offset));

        if (action === 'servers-select-all') {
            const checkboxes = document.querySelectorAll('.server-checkbox');
            checkboxes.forEach(cb => cb.checked = event.target.checked);
            updateServerActionButtons();
        }

        if (action === 'servers-generate-token') {
            const targetId = trigger.dataset.target;
            const input = document.getElementById(targetId);
            if (input) {
                input.value = generateSecureToken(32);
                input.select();
            }
        }
    });

    // Status Toggle Live Text
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('js-status-toggle')) {
            const labelOn = e.target.dataset.onLabel || 'Activo';
            const labelOff = e.target.dataset.offLabel || 'Inactivo';
            const targetId = e.target.dataset.targetId;
            
            if (targetId) {
                const textEl = document.getElementById(targetId);
                if (textEl) textEl.textContent = e.target.checked ? labelOn : labelOff;
            }
        }
    });
});
