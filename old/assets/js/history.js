/**
 * Returns optimal pageLength based on viewport height.
 */
function getPageLength() {
    const h = window.innerHeight;
    if (h < 900) return 9;
    return 10;
}

let historyDataTable;

$(document).ready(function() {
    initHistoryDataTable();

    $('#historySearch').on('input', function() {
        if (historyDataTable) {
            historyDataTable.search(this.value).draw();
        }
    });

    $('#refreshHistory').on('click', function() {
        if (historyDataTable) {
            historyDataTable.ajax.reload();
        }
    });
});

function initHistoryDataTable() {
    const tableEl = $('#iperfHistoryTable');
    if (!tableEl.length) return;

    historyDataTable = tableEl.DataTable({
        ajax: {
            url: '/iperf/api/history-list',
            dataSrc: 'tests'
        },
        columns: [
            { 
                data: 'id', 
                width: '8%', 
                render: (data) => `<div class="flex items-center h-full text-primary/60 font-black text-left pl-6">#${data}</div>` 
            },
            { 
                data: 'status', 
                width: '12%',
                render: (data) => {
                    const status = String(data).toLowerCase();
                    let cls = 'bg-rose-500/10 text-rose-500 border-rose-500/20';
                    if (status === 'completed') cls = 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
                    return `<div class="flex items-center justify-center h-full"><span class="px-3 py-1 rounded-lg text-[9px] font-black border ${cls}">${data.toUpperCase()}</span></div>`;
                }
            },
            { 
                data: 'protocol', 
                width: '12%',
                render: (data) => {
                    const proto = String(data).toLowerCase();
                    let cls = 'bg-blue-500/10 text-blue-500 border-blue-500/20';
                    if (proto === 'udp') cls = 'bg-amber-500/10 text-amber-500 border-amber-500/20';
                    return `<div class="flex items-center justify-center h-full"><span class="px-3 py-1 rounded-lg text-[9px] font-black border ${cls}">${data.toUpperCase()}</span></div>`;
                }
            },
            { 
                data: null, 
                width: '25%', 
                render: (data) => `
                    <div class="flex flex-col h-full justify-center px-4">
                        <span class="text-xs font-bold text-body-text">${data.target_host}</span>
                        <span class="text-[10px] text-label/30 font-medium uppercase tracking-widest">Puerto: ${data.port}</span>
                    </div>` 
            },
            { 
                data: 'bandwidth', 
                width: '18%', 
                render: (data) => `
                    <div class="flex flex-col items-center justify-center h-full">
                        <span class="text-sm font-black text-primary italic leading-none">${data}</span>
                        <span class="text-[9px] font-black text-label/20 uppercase tracking-widest mt-1">Gbps</span>
                    </div>` 
            },
            { 
                data: 'date', 
                width: '15%', 
                render: (data) => {
                    const parts = data.split(' ');
                    return `
                    <div class="flex flex-col items-center justify-center h-full">
                        <span class="text-[11px] font-bold text-label/60 leading-none">${parts[0]}</span>
                        <span class="text-[10px] text-label/20 font-medium mt-1">${parts[1] || ''}</span>
                    </div>`;
                }
            },
            { 
                data: 'id', 
                width: '10%', 
                render: (data) => `
                    <div class="flex items-center justify-end h-full pr-6">
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
            zeroRecords: "No hay registros disponibles",
            info: "Mostrando _START_-_END_ de _TOTAL_",
            infoEmpty: "Mostrando 0-0 de 0",
            infoFiltered: "(filtrado de _MAX_)",
            paginate: {
                previous: '<i class="fas fa-chevron-left text-[10px]"></i>',
                next: '<i class="fas fa-chevron-right text-[10px]"></i>'
            }
        },
        drawCallback: function(settings) {
            renderGhostRows(settings, 7);
        },
        initComplete: function() {
            const container = $(this.api().table().container());
            container.find('table').wrap('<div class="nx-table-scroll"></div>');
        }
    });

    $(window).on('resize', function() {
        const newLen = getPageLength();
        if (historyDataTable.page.len() !== newLen) {
            historyDataTable.page.len(newLen).draw();
        }
    });
}

function renderGhostRows(settings, columns) {
    const api = new $.fn.dataTable.Api(settings);
    const info = api.page.info();
    const tbody = $(settings.nTBody);
    const pageLen = api.page.len();

    tbody.find('.ghost-row').remove();
    tbody.find('.dataTables_empty').closest('tr').remove();

    const container = api.table().container();
    const gridH = $(container).height(); 
    let rowH = 50;
    
    if (gridH > 0) {
        rowH = Math.max(40, Math.floor((gridH - 60) / (pageLen + 1)) - 1);
    }
    
    $(container).css('--row-h', rowH + 'px');

    const realRows = info.end - info.start;
    const ghostCount = pageLen - realRows;
    if (ghostCount <= 0) return;

    let ghostHtml = '';
    for (let i = 0; i < ghostCount; i++) {
        ghostHtml += `<tr class="ghost-row pointer-events-none select-none">`;
        for (let j = 0; j < columns; j++) {
            ghostHtml += `<td><div></div></td>`;
        }
        ghostHtml += `</tr>`;
    }
    tbody.append(ghostHtml);
}
