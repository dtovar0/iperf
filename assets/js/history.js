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
 * Logic for rendering Iperf History tables with DataTables integration.
 */

let historyDataTable;

/**
 * INITIALIZATION
 */
$(document).ready(function() {
    initHistoryDataTable();

    // Universal Search Integration
    $('#historySearch').on('input', function() {
        if (historyDataTable) {
            historyDataTable.search(this.value).draw();
        }
    });

    // Refresh Action
    $('#refreshHistory').on('click', function() {
        if (historyDataTable) {
            historyDataTable.ajax.reload();
        }
    });
});

/**
 * Initializes DataTables for History
 */
function initHistoryDataTable() {
    const tableEl = $('table');
    if (!tableEl.length) return;

    historyDataTable = tableEl.DataTable({
        ajax: {
            url: '/iperf/api/history-list',
            dataSrc: 'tests'
        },
        columns: [
            { 
                data: 'id', 
                width: '80px', 
                render: (data) => `<div class="flex items-center h-full text-primary/60 font-black text-left">#${String(data).padStart(5, '0')}</div>` 
            },
            { 
                data: 'status', 
                width: '120px',
                render: (data) => {
                    const status = String(data).toLowerCase();
                    let cls = 'nx-badge-primary';
                    if (status.includes('completed') || status.includes('success') || status.includes('terminada')) cls = 'nx-badge-success';
                    else if (status.includes('failed') || status.includes('error') || status.includes('fallida')) cls = 'nx-badge-error';
                    else if (status.includes('running') || status.includes('iniciada')) cls = 'nx-badge-primary';
                    
                    return `<div class="flex items-center justify-center h-full"><span class="nx-badge ${cls}">${data.toUpperCase()}</span></div>`;
                }
            },
            { 
                data: 'protocol', 
                width: '100px',
                render: (data) => {
                    const proto = String(data).toLowerCase();
                    let cls = 'nx-badge-cyan';
                    if (proto === 'udp') cls = 'nx-badge-warning';
                    
                    return `<div class="flex items-center justify-center h-full"><span class="nx-badge ${cls} text-[9px] font-black">${data.toUpperCase()}</span></div>`;
                }
            },
            { 
                data: null, 
                width: 'auto', 
                render: (data) => `
                    <div class="flex flex-col h-full justify-center text-left">
                        <span class="text-xs font-bold text-label/80 truncate">${data.target_host}</span>
                        <span class="text-[10px] text-label/30 font-bold uppercase tracking-widest">Puerto: ${data.port}</span>
                    </div>` 
            },
            { 
                data: 'bandwidth', 
                width: '120px', 
                render: (data) => `
                    <div class="flex flex-col items-center justify-center h-full">
                        <span class="text-sm font-black text-primary italic leading-none">${data}</span>
                        <span class="text-[9px] font-black text-label/20 uppercase tracking-widest mt-1">Gbps</span>
                    </div>` 
            },
            { 
                data: 'date', 
                width: '180px', 
                render: (data) => {
                    const parts = data.split(' ');
                    return `
                    <div class="flex flex-col items-center justify-center h-full">
                        <span class="text-[11px] font-bold text-label/60 leading-none">${parts[0]}</span>
                        <span class="text-[10px] text-label/20 font-medium mt-1 font-mono uppercase">${parts[1] || ''}</span>
                    </div>`;
                }
            },
            { 
                data: 'id', 
                width: '80px', 
                render: (data) => `
                    <div class="flex items-center justify-center h-full">
                        <a href="/iperf/report/${data}" target="_blank" class="w-8 h-8 flex items-center justify-center rounded-lg bg-surface-container hover:bg-primary hover:text-white text-label/40 transition-all shadow-sm">
                            <i class="fas fa-file-pdf"></i>
                        </a>
                    </div>` 
            }
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
            zeroRecords: "No se encontraron sesiones de red",
            info: "Mostrando _START_-_END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0-0 de 0 registros",
            infoFiltered: "(filtrado de _MAX_ registros totales)",
            paginate: {
                previous: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>',
                next: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>'
            }
        },
        drawCallback: function(settings) {
            renderGhostRows(settings, 7);
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
    window.activeNexusTable = historyDataTable;
}

/**
 * Sizes all rows equally to fill the table wrapper, then adds ghost rows.
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
                <td class="text-center"><div></div></td>
                <td class="text-center"><div></div></td>
                <td class="text-left"><div></div></td>
                <td class="text-center"><div></div></td>
                <td class="text-center"><div></div></td>
                <td class="text-center"><div></div></td>
            </tr>`;
    }
    tbody.append(ghostHtml);
}


// Adaptive Redraw on Resize
$(window).on('resize', () => {
    if (historyDataTable) historyDataTable.draw(false);
});
