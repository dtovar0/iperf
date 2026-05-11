// Authentication Management Module
document.addEventListener('DOMContentLoaded', function() {
    // Role Mapping Initialization
    initRoleMappings();
});

/**
 * Initializes Dynamic Role Mappings from hidden input
 */
function initRoleMappings() {
    const list = document.getElementById('mappingList');
    const hiddenData = document.getElementById('ldap_role_mappings_data');
    if (!list || !hiddenData) return;

    try {
        const mappings = JSON.parse(hiddenData.value || '[]');
        list.innerHTML = '';
        
        if (mappings.length === 0) {
            document.getElementById('mappingEmptyState')?.classList.remove('hidden');
        } else {
            document.getElementById('mappingEmptyState')?.classList.add('hidden');
            mappings.forEach(m => addMappingRow(m.group, m.role));
        }
    } catch (e) {
        console.error('Error initializing mappings:', e);
        addMappingRow();
    }
}

/**
 * Adds a new row to the mapping list
 */
function addMappingRow(group = '', role = 'usuario') {
    const list = document.getElementById('mappingList');
    const emptyState = document.getElementById('mappingEmptyState');
    if (!list) return;

    if (emptyState) emptyState.classList.add('hidden');

    const row = document.createElement('div');
    row.className = 'mapping-row flex items-end gap-6 animate-in fade-in slide-in-from-left-2 duration-300';
    row.innerHTML = `
        <div class="flex-grow space-y-2 group">
            <label class="block text-[12px] font-black text-label/40 uppercase tracking-[0.2em] ml-1 group-focus-within:text-primary transition-colors">GRUPO LDAP (DN)</label>
            <div class="relative">
                <svg class="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-label/40 group-focus-within:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
                <input type="text" class="mapping-group w-full bg-input-bg border-2 border-panel-border rounded-xl pl-12 pr-4 py-3 text-sm font-bold text-input outline-none focus:border-primary transition-all placeholder:text-label/20" 
                       placeholder="CN=AdminGroup,OU=Groups,DC=nexus,DC=local" value="${group}">
            </div>
        </div>
        <div class="w-60 shrink-0 space-y-2 group">
            <label class="block text-[12px] font-black text-label/40 uppercase tracking-[0.2em] ml-1 group-focus-within:text-primary transition-colors">ROL ASIGNADO</label>
            <div class="relative">
                <svg class="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-label/40 group-focus-within:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                <select class="mapping-role w-full bg-input-bg border-2 border-panel-border rounded-xl pl-12 pr-10 py-3 text-[12px] font-black uppercase tracking-widest text-input outline-none focus:border-primary transition-all cursor-pointer appearance-none">
                    <option value="administrador" ${role === 'administrador' ? 'selected' : ''}>Administrador</option>
                    <option value="usuario" ${role === 'usuario' ? 'selected' : ''}>Usuario</option>
                </select>
                <svg class="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 text-label/40 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
        </div>
        <div class="pb-0.5">
            <button onclick="removeMappingRow(this)" class="w-12 h-12 flex items-center justify-center rounded-xl bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white transition-all active:scale-95 group/del shadow-lg shadow-red-500/5">
                <svg class="w-5 h-5 transition-transform group-hover/del:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
    `;
    list.appendChild(row);
}

/**
 * Removes a row from the mapping list
 */
function removeMappingRow(button) {
    const row = button.closest('.mapping-row');
    row.classList.add('animate-out', 'fade-out', 'slide-out-to-right-4', 'duration-300');
    setTimeout(() => {
        row.remove();
        const list = document.getElementById('mappingList');
        if (list && list.children.length === 0) {
            document.getElementById('mappingEmptyState')?.classList.remove('hidden');
        }
    }, 280);
}

/**
 * Saves Auth Configuration to backend
 * @param {string} containerId 
 */
function saveAuthConfig(containerId) {
    // Collect role mappings
    const mappings = [];
    document.querySelectorAll('.mapping-row').forEach(row => {
        const group = row.querySelector('.mapping-group').value.trim();
        const role = row.querySelector('.mapping-role').value;
        if (group) {
            mappings.push({ group, role });
        }
    });

    const data = {
        ldap_host: document.getElementById('ldap_host')?.value,
        ldap_port: document.getElementById('ldap_port')?.value,
        ldap_ssl: document.getElementById('ldap_ssl')?.checked,
        ldap_user: document.getElementById('ldap_user')?.value,
        ldap_pass: document.getElementById('ldap_pass')?.value,
        ldap_base_dn: document.getElementById('ldap_base_dn')?.value,
        ldap_user_attr: document.getElementById('ldap_user_attr')?.value,
        ldap_group_admin: document.getElementById('ldap_group_admin')?.value,
        ldap_group_user: document.getElementById('ldap_group_user')?.value,
        ldap_role_mappings: JSON.stringify(mappings)
    };

    showToast('Sincronizando Directorio...', 'info');

    fetch('/auth/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showToast(result.message, 'success');
            // Update hidden data to reflect current state
            const hiddenData = document.getElementById('ldap_role_mappings_data');
            if (hiddenData) hiddenData.value = data.ldap_role_mappings;
        } else {
            showToast('Error: ' + result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error de conexión', 'error');
    });
}


/**
 * Tests the LDAP connection with current parameters
 */
function testLdapConnection() {
    const data = {
        ldap_host: document.getElementById('ldap_host')?.value,
        ldap_port: document.getElementById('ldap_port')?.value,
        ldap_ssl: document.getElementById('ldap_ssl')?.checked,
        ldap_user: document.getElementById('ldap_user')?.value,
        ldap_pass: document.getElementById('ldap_pass')?.value,
        ldap_base_dn: document.getElementById('ldap_base_dn')?.value,
        ldap_user_attr: document.getElementById('ldap_user_attr')?.value,
        ldap_group_admin: document.getElementById('ldap_group_admin')?.value,
        ldap_group_user: document.getElementById('ldap_group_user')?.value
    };

    if (!data.ldap_host || !data.ldap_port) {
        showToast('Host y Puerto son obligatorios', 'error');
        return;
    }

    showToast('Validando parámetros LDAP...', 'info');

    fetch('/auth/test_ldap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showToast('Conexión LDAP Exitosa', 'success');
        } else {
            showToast('Error de Conexión: ' + result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error al conectar con el servidor', 'error');
    });
}
