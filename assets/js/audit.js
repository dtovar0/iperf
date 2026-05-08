/**
 * Returns optimal pageLength based on viewport height.
 *   < 900px → 9 rows   >= 900px → 10 rows
 */
function getPageLength() {
    const h = window.innerHeight;
    if (h < 900) return 9;
    return 10;
}

/**
 * MODULE: Centralized Nexus Table Engine (DataTables Powered)
 * Logic for rendering Audit tables with DataTables integration.
 */

let auditDataTable;

/**
 * INITIALIZATION
 */
$(document).ready(function() {
    initAuditDataTable();

    // Universal Search Integration
    $('#auditSearch').on('input', function() {
        if (auditDataTable) {
            auditDataTable.search(this.value).draw();
        }
    });

    // Refresh Action
    $('#refreshAudit').on('click', function() {
        if (auditDataTable) {
            auditDataTable.ajax.reload();
        }
    });
});

/**
 * Initializes DataTables for Audit
 */
function initAuditDataTable() {
    const tableEl = $('table');
    if (!tableEl.length) return;

    auditDataTable = tableEl.DataTable({
        ajax: {
            url: '/audit/api/list',
            dataSrc: 'logs'
        },
        columns: [
            { data: 'id', width: '80px', render: (data) => `<div class="flex items-center h-full text-primary/60 font-black text-left">#${String(data).padStart(5, '0')}</div>` },
            { data: 'user', width: '130px', render: (data) => `<div class="flex items-center h-full font-bold text-label/80 truncate">${data || 'SYSTEM'}</div>` },
            { 
                data: 'action', 
                width: '170px',
                render: (data) => {
                    const action = String(data).toLowerCase();
                    let cls = 'nx-badge-primary';
                    let icon = 'fa-info-circle';
                    let label = String(data).toUpperCase();

                    if (action.includes('login') || action.includes('auth')) {
                        cls = 'nx-badge-cyan';
                        icon = 'fa-key';
                    } else if (action.includes('logout')) {
                        cls = 'nx-badge-slate';
                        icon = 'fa-sign-out-alt';
                    } else if (action.includes('creada') || action.includes('nueva') || action.includes('registro')) {
                        cls = 'nx-badge-success';
                        icon = 'fa-plus-circle';
                    } else if (action.includes('eliminada') || action.includes('borrada') || action.includes('baja')) {
                        cls = 'nx-badge-error';
                        icon = 'fa-trash-alt';
                    } else if (action.includes('actualizada') || action.includes('modificada') || action.includes('cambio') || action.includes('edición')) {
                        cls = 'nx-badge-primary';
                        icon = 'fa-edit';
                    } else if (action.includes('terminada') || action.includes('completada')) {
                        cls = 'nx-badge-violet';
                        icon = 'fa-check-double';
                    } else if (action.includes('iniciada')) {
                        cls = 'nx-badge-primary';
                        icon = 'fa-play-circle';
                    } else if (action.includes('identity') || action.includes('acceso') || action.includes('petición')) {
                        cls = 'nx-badge-warning';
                        icon = 'fa-shield-alt';
                    }

                    return `
                        <div class="flex items-center justify-center h-full">
                            <span class="nx-badge ${cls} flex items-center gap-2 px-3 py-1 rounded-full text-[9px] font-black tracking-widest border border-current/10 shadow-sm">
                                <i class="fas ${icon} text-[8px] opacity-70"></i>
                                ${label}
                            </span>
                        </div>`;
                }
            },
            { 
                data: 'status', 
                width: '100px',
                render: (data) => {
                    const status = String(data).toLowerCase();
                    let cls = 'nx-badge-primary';
                    if (status.includes('success')) cls = 'nx-badge-success';
                    else if (status.includes('error')) cls = 'nx-badge-error';
                    else if (status.includes('warning')) cls = 'nx-badge-warning';
                    
                    return `<div class="flex items-center justify-center h-full"><span class="nx-badge ${cls}">${data.toUpperCase()}</span></div>`;
                }
            },
            { data: 'description', width: 'auto', render: (data) => `<div class="flex items-center h-full text-[12px] font-bold text-label/60 line-clamp-1 min-w-0 overflow-hidden text-ellipsis text-left" title="${data || ''}">${data || '-'}</div>` },
            { data: 'time', width: '180px', render: (data) => `<div class="flex items-center h-full font-mono text-[12px] font-bold text-label/60 justify-center">${data}</div>` }
        ],
        autoWidth: false,
        pageLength: getPageLength(),
        pagingType: 'simple',
        order: [[0, 'desc']],
        layout: {
            topStart: null,
            topEnd: null,
            bottomStart: 'info',
            bottomEnd: 'paging'
        },
        language: {
            zeroRecords: "No se encontraron registros",
            info: "Mostrando _START_-_END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0-0 de 0 registros",
            infoFiltered: "(filtrado de _MAX_ registros totales)",
            paginate: {
                previous: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>',
                next: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>'
            }
        },
        drawCallback: function(settings) {
            renderGhostRows(settings, 6);
        },
        initComplete: function() {
            const cell = $(this.api().table().container()).find('.dt-layout-row.dt-layout-table .dt-layout-cell');
            const tbl  = cell.children('table');
            if (tbl.length && !cell.children('.nx-table-scroll').length) {
                tbl.wrap('<div class="nx-table-scroll"></div>');
            }
            const api = this.api();
            let resizeTimer;
            $(window).on('resize.dtPageLen', function() {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(function() {
                    const newLen = getPageLength();
                    if (api.page.len() !== newLen) api.page.len(newLen).draw();
                    else api.draw(false);
                }, 200);
            });
        }
    });

    // Register globally for top bar search
    window.activeNexusTable = auditDataTable;
}

/**
 * Sizes all rows equally to fill the table wrapper, then adds ghost rows.
 * rowH = floor( (wrapperHeight - borderGaps) / (pageLen + 1) )
 */
function renderGhostRows(settings, columns) {
    const api     = new $.fn.dataTable.Api(settings);
    const info    = api.page.info();
    const tbody   = $(settings.nTBody);
    const pageLen = api.page.len();

    // 1. Cleanup
    tbody.find('.ghost-row').remove();
    tbody.find('.dataTables_empty').closest('tr').remove();

    // 2. Calculate row height based on the GRID SCOPE
    const container = api.table().container();
    const gridH = $(container).height(); 
    let rowH = 50;
    
    if (gridH > 0) {
        const totalRows  = pageLen;
        // Restamos el footer y aplicamos un offset de -1px para compensar bordes
        rowH = Math.max(40, Math.floor((gridH - 52) / (totalRows + 1)) - 1);
    }
    
    // Set the variable for CSS (Matches Header, Body and Pagination)
    $(container).css('--row-h', rowH + 'px');

    // 3. Ghost Row injection (simplified)
    const realRows   = info.end - info.start;
    const ghostCount = pageLen - realRows;
    if (ghostCount <= 0) return;

    let ghostHtml = '';
    for (let i = 0; i < ghostCount; i++) {
        ghostHtml += `
            <tr class="ghost-row pointer-events-none select-none">
                <td class="text-left"><div></div></td>
                <td class="text-left"><div></div></td>
                <td class="text-center"><div></div></td>
                <td class="text-center"><div></div></td>
                <td class="text-left"><div></div></td>
                <td class="text-center"><div></div></td>
            </tr>`;
    }
    tbody.append(ghostHtml);
}


// Adaptive Redraw on Resize
$(window).on('resize', () => {
    if (auditDataTable) auditDataTable.draw(false);
});
