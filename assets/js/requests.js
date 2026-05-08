/* ═══════════════════════════════════════════════════════════════════
   NEXUS PREMIUM — requests.js v3.0 "Enterprise Edition"
   Requiere: jQuery, DataTables, ApexCharts
   Datos globales: REQUESTS_DATA, COUNTS_DATA (inyectados en template)
═══════════════════════════════════════════════════════════════════ */

'use strict';

let requestsDataTable  = null;
let selectedRequests   = [];

/* ─── Bootstrap ─── */
$(document).ready(function () {
    initRequestsDataTable();
    initCharts();
    bindEvents();
});

/* ─── Bind eventos globales ─── */
function bindEvents() {
    /* Búsqueda */
    $('#requestSearch').on('input', function () {
        if (requestsDataTable) requestsDataTable.search(this.value).draw();
    });

    /* Select-all (delegado al wrapper para sobrevivir redraws de DT) */
    $('#tableView').on('change', '#selectAll', function () {
        $('.row-checkbox:not(:disabled)').prop('checked', $(this).prop('checked'));
        updateSelectionStatus();
    });

    /* Checkboxes de fila */
    $('#requestsDT').on('change', '.row-checkbox', function () {
        updateSelectionStatus();
    });

    /* Click en fila → abrir modal */
    $('#requestsDT').on('click', 'tbody tr', function (e) {
        if ($(e.target).closest('.row-checkbox, .nx-action-btn').length) return;
        const data = requestsDataTable.row(this).data();
        if (data) openEditModal(data);
    });

    /* Cerrar modal al hacer click en overlay */
    $('#editRequestModal').on('click', function (e) {
        if (e.target === this) closeModal('editRequestModal');
    });

    /* Cerrar modal con Escape */
    $(document).on('keydown', function (e) {
        if (e.key === 'Escape') closeModal('editRequestModal');
    });
}

/* ─── Actualizar estado de selección masiva ─── */
function updateSelectionStatus() {
    selectedRequests = [];
    $('.row-checkbox:checked').each(function () {
        selectedRequests.push(parseInt($(this).data('id')));
    });

    const count    = selectedRequests.length;
    const hasItems = count > 0;
    const label    = count === 1 ? '1 seleccionada' : `${count} seleccionadas`;

    /* Barra del dashboard */
    const $bulkDash = $('#bulkActionsDash');
    $bulkDash.toggleClass('hidden', !hasItems);
    if (hasItems) $('#bulkCountDash').text(label);
    $('#bulkBtnApproveDash, #bulkBtnRejectDash').prop('disabled', !hasItems);

    /* Barra de la tabla */
    const $bulkTable = $('#bulkActionsTable');
    $bulkTable.toggle(hasItems);
    if (hasItems) $('#bulkCountTable').text(count);
    $('#bulkBtnApprove, #bulkBtnReject').prop('disabled', !hasItems);
}

/* ═══════════════════════════════════════
   DATATABLE — Inicialización
═══════════════════════════════════════ */
function getPageLength() {
    return window.innerHeight < 900 ? 9 : 10;
}

function initRequestsDataTable() {
    requestsDataTable = $('#requestsDT').DataTable({
        data: REQUESTS_DATA,
        createdRow: function (row, data) {
            $(row).addClass('cursor-pointer').attr('data-id', data.id);
        },
        columns: [
            /* Checkbox */
            {
                data: 'id',
                orderable: false,
                width: '48px',
                render: (data, type, row) => {
                    const statusStr = String(row.status || '').toLowerCase();
                    const disabled  = statusStr !== 'pendiente';
                    return `<input type="checkbox" data-id="${data}"
                        class="nx-checkbox row-checkbox"
                        style="margin:0 auto;display:block"
                        ${disabled ? 'disabled' : ''}
                    >`;
                }
            },
            /* Solicitante */
            {
                data: 'user_name',
                render: (data, type, row) => `
                    <div>
                        <span class="nx-td-user-name">${escHtml(data)}</span>
                        <span class="nx-td-user-email">${escHtml(row.user_email)}</span>
                    </div>`
            },
            /* Plataforma */
            {
                data: 'platform_name',
                render: (data, type, row) => `
                    <div>
                        <span class="nx-td-platform-name">${escHtml(data)}</span>
                        <span class="nx-td-area-name">${escHtml(row.area_name || 'Servicio activo')}</span>
                    </div>`
            },
            /* Estado */
            {
                data: 'status',
                className: 'text-center',
                render: (data) => {
                    const { cls, label } = statusMeta(data);
                    return `<div style="display:flex;align-items:center;justify-content:center;height:100%">
                        <span class="nx-badge ${cls}">
                            <span class="nx-badge__dot"></span>${escHtml(label)}
                        </span>
                    </div>`;
                }
            },
            /* Fecha */
            {
                data: 'created_at',
                className: 'text-center',
                render: (data) => `<span class="nx-td-date">${escHtml(data)}</span>`
            },
        ],
        autoWidth:   false,
        pageLength:  getPageLength(),
        pagingType:  'simple',
        order:       [[4, 'desc']],
        layout: {
            topStart: null, topEnd: null,
            bottomStart: 'info', bottomEnd: 'paging'
        },
        language: {
            zeroRecords:  'No se encontraron solicitudes',
            info:         'Mostrando _START_-_END_ de _TOTAL_ registros',
            infoEmpty:    'Mostrando 0-0 de 0 registros',
            infoFiltered: '(filtrado de _MAX_ registros)',
            paginate: {
                previous: `<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M7.5 9L4.5 6l3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
                next:     `<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4.5 9L7.5 6l-3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
            }
        },
        drawCallback: function (settings) {
            renderGhostRows(settings, 5);
        }
    });

    window.activeNexusTable = requestsDataTable;
}

/* ─── Ghost rows para rellenar espacio vacío ─── */
function renderGhostRows(settings, cols) {
    const api       = new $.fn.dataTable.Api(settings);
    const tbody     = $(settings.nTBody);
    const pageLen   = api.page.len();
    const info      = api.page.info();
    const container = api.table().container();
    const gridH     = $(container).height();
    const rowH      = gridH > 0 ? Math.max(44, Math.floor((gridH - 56) / (pageLen + 1))) : 48;

    $(container).css('--row-h', rowH + 'px');
    tbody.find('.nx-ghost-row').remove();

    const ghostCount = pageLen - (info.end - info.start);
    if (ghostCount <= 0) return;

    let html = '';
    for (let i = 0; i < ghostCount; i++) {
        html += `<tr class="nx-ghost-row" style="pointer-events:none;opacity:0.04">${'<td></td>'.repeat(cols)}</tr>`;
    }
    tbody.append(html);
}

/* ═══════════════════════════════════════
   MODAL
═══════════════════════════════════════ */
function openEditModalById(id) {
    const row = REQUESTS_DATA.find(r => r.id === id);
    if (row) openEditModal(row);
}

function openEditModal(data) {
    /* ID */
    $('#modalRequestIdDisplay').text(`ID #${String(data.id).padStart(4, '0')}`);

    /* Usuario */
    const initial = (data.user_name || 'U').charAt(0).toUpperCase();
    $('#modalUserInitial').text(initial);
    $('#modalUserName').text(data.user_name || '—');
    $('#modalUserEmail').text(data.user_email || '—');

    /* Plataforma */
    $('#modalPlatformName').text(data.platform_name || '—');
    $('#modalAreaName').text(data.area_name || 'Área técnica');

    /* Fecha */
    $('#modalRequestDate').text(data.created_at || '—');

    /* Badge de estado */
    const { cls, label } = statusMeta(data.status);
    $('#modalStatusBadge').html(
        `<span class="nx-badge ${cls}"><span class="nx-badge__dot"></span>${escHtml(label)}</span>`
    );

    /* Footer de acciones: sólo si pendiente */
    const statusStr = String(data.status || '').toLowerCase();
    const isPending = statusStr === 'pendiente';
    const $actions  = $('.nx-modal__footer-actions');
    
    if (isPending) {
        $actions.show();
        $('#modalBtnApprove').off('click').on('click', () => quickAction(data.id, 'approve'));
        $('#modalBtnReject').off('click').on('click',  () => quickAction(data.id, 'reject'));
    } else {
        $actions.hide();
    }

    $('#editRequestModal').removeClass('hidden');
}

function closeModal(id) {
    $('#' + id).addClass('hidden');
}

/* ═══════════════════════════════════════
   VISTAS — Dashboard ↔ Tabla
═══════════════════════════════════════ */
function filterByStatus(status) {
    if (!requestsDataTable) return;

    if (status === 'all') {
        requestsDataTable.search('').columns().search('').draw();
    } else if (status === 'rejected') {
        requestsDataTable.column(3).search('Denegado|Rechazado', true, false).draw();
    } else {
        requestsDataTable.column(3).search(status).draw();
    }

    $('#dashboardView').removeClass('nx-view--active').addClass('nx-view--hidden');
    $('#tableView').removeClass('nx-view--hidden').addClass('nx-view--active');
}

function showDashboard() {
    $('#tableView').removeClass('nx-view--active').addClass('nx-view--hidden');
    $('#dashboardView').removeClass('nx-view--hidden').addClass('nx-view--active');
    updateSelectionStatus();
}

/* ═══════════════════════════════════════
   ACCIONES — Aprobar / Denegar
═══════════════════════════════════════ */
function quickAction(id, action) {
    processRequests([id], action);
}

function processSelected(action) {
    if (selectedRequests.length === 0) return;
    const msg = action === 'approve'
        ? `¿Aprobar ${selectedRequests.length} solicitudes seleccionadas?`
        : `¿Denegar ${selectedRequests.length} solicitudes seleccionadas?`;
    if (!confirm(msg)) return;
    processRequests(selectedRequests, action);
}

async function processRequests(ids, action) {
    if (typeof showToast === 'function') showToast('Procesando solicitudes…', 'info');

    try {
        const res = await fetch('/admin/requests/process', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ ids, action })
        });
        const result = await res.json();
        if (result.status === 'success') {
            if (typeof showToast === 'function') showToast(result.message, 'success');
            setTimeout(() => location.reload(), 800);
        } else {
            if (typeof showToast === 'function') showToast(result.message || 'Error al procesar', 'error');
        }
    } catch {
        if (typeof showToast === 'function') showToast('Error de conexión con el servidor', 'error');
    }
}

/* ═══════════════════════════════════════
   GRÁFICAS — ApexCharts
═══════════════════════════════════════ */
function initCharts() {
    initStatusChart();
    initPlatformChart();
}

function initStatusChart() {
    const el = document.getElementById('statusChart');
    if (!el) return;

    const { pending, approved, rejected } = COUNTS_DATA;
    const total = pending + approved + rejected;

    if (total === 0) {
        renderEmpty(el,
            `<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.3"/><path d="M9 9l4.5-2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M9 9l-1.5 4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>`,
            'Sin solicitudes',
            'El motor de auditoría está en espera de registros'
        );
        return;
    }

    el.innerHTML = '';
    new ApexCharts(el, {
        series:  [pending, approved, rejected],
        chart: {
            type:       'donut',
            height:     '100%',
            width:      '100%',
            fontFamily: 'Inter, system-ui, sans-serif',
            background: 'transparent',
            toolbar: { show: false }
        },
        labels:  ['Pendientes', 'Aprobadas', 'Denegadas'],
        colors:  ['#f59e0b', '#059669', '#e11d48'],
        plotOptions: {
            pie: {
                donut: {
                    size: '70%',
                    labels: {
                        show:  true,
                        total: {
                            show:     true,
                            label:    'Total',
                            fontSize: '12px',
                            fontWeight: 600,
                            color:    'var(--color-body-text, #0f172a)',
                            formatter: () => total
                        },
                        value: { fontSize: '18px', fontWeight: 700 }
                    }
                },
                expandOnClick: false
            }
        },
        dataLabels: { enabled: false },
        stroke:     { width: 2, colors: ['transparent'] },
        legend: {
            position:    'bottom',
            fontSize:    '10px',
            fontWeight:  600,
            itemMargin:  { horizontal: 8 },
            labels:      { colors: '#64748b' },
            markers:     { width: 8, height: 8, radius: 2 }
        },
        tooltip: {
            y: {
                formatter: (val) => `${val} solicitudes (${Math.round(val / total * 100)}%)`
            }
        }
    }).render();
}

function initPlatformChart() {
    const el = document.getElementById('platformChart');
    if (!el) return;

    /* Contar solicitudes por plataforma */
    const counts = {};
    REQUESTS_DATA.forEach(r => {
        counts[r.platform_name] = (counts[r.platform_name] || 0) + 1;
    });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6);

    if (sorted.length === 0) {
        renderEmpty(el,
            `<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="7" r="3.5" stroke="currentColor" stroke-width="1.3"/><path d="M2 16c0-3.3 3.1-6 7-6s7 2.7 7 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>`,
            'Sin distribución',
            'No hay usuarios vinculados a plataformas'
        );
        return;
    }

    /* Badge con total plataformas */
    const badge = document.getElementById('platformBadge');
    if (badge) {
        badge.textContent = `${sorted.length} plataformas`;
        badge.style.display = 'block';
    }

    el.innerHTML = '';
    new ApexCharts(el, {
        series: [{ name: 'Solicitudes', data: sorted.map(p => p[1]) }],
        chart: {
            type:       'bar',
            height:     '100%',
            width:      '100%',
            toolbar:    { show: false },
            fontFamily: 'Inter, system-ui, sans-serif',
            background: 'transparent',
            animations: { enabled: true, speed: 400 }
        },
        colors: ['#2563eb'],
        plotOptions: {
            bar: {
                borderRadius:     4,
                borderRadiusApplication: 'end',
                columnWidth:      '44%',
                dataLabels: { position: 'top' }
            }
        },
        dataLabels: {
            enabled:   true,
            offsetY:   -18,
            style:     { fontSize: '10px', fontWeight: 600, colors: ['#64748b'] }
        },
        xaxis: {
            categories: sorted.map(p => p[0]),
            labels: {
                style:    { colors: '#64748b', fontSize: '10px', fontWeight: 600 },
                trim:     true,
                maxHeight: 60
            },
            axisBorder: { show: false },
            axisTicks:  { show: false }
        },
        yaxis: {
            labels: { style: { colors: '#64748b', fontSize: '10px', fontWeight: 600 } },
            min:    0
        },
        grid: {
            borderColor:     'rgba(148,163,184,0.12)',
            strokeDashArray: 4,
            xaxis: { lines: { show: false } }
        },
        tooltip: {
            y: { formatter: (v) => `${v} solicitudes` }
        }
    }).render();
}

/* ─── Estado vacío para gráficas ─── */
function renderEmpty(el, iconSvg, title, desc) {
    el.innerHTML = `
        <div class="nx-chart-empty">
            <div class="nx-chart-empty__icon">${iconSvg}</div>
            <div class="nx-chart-empty__rule"></div>
            <span class="nx-chart-empty__title">${escHtml(title)}</span>
            <span class="nx-chart-empty__desc">${escHtml(desc)}</span>
        </div>`;
}

/* ═══════════════════════════════════════
   UTILIDADES
═══════════════════════════════════════ */
function statusMeta(status) {
    const s = String(status).toLowerCase();
    if (s.includes('aprobado'))  return { cls: 'nx-badge--approved', label: 'Aprobada' };
    if (s.includes('pendiente')) return { cls: 'nx-badge--pending',  label: 'Pendiente' };
    return                              { cls: 'nx-badge--rejected', label: 'Denegada' };
}

function escHtml(str) {
    return String(str ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function iconCheck() {
    return `<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}
function iconX() {
    return `<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`;
}
function iconEye() {
    return `<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M1 6s2-4 5-4 5 4 5 4-2 4-5 4-5-4-5-4z" stroke="currentColor" stroke-width="1.3"/><circle cx="6" cy="6" r="1.5" stroke="currentColor" stroke-width="1.3"/></svg>`;
}
