// Nexus Premium - Platforms Module (Modernized Legacy 1:1)
(function() {
    'use strict';

    // Global Data State
    let currentArea = null;
    let currentAreaId = null;
    let currentStep = 1;
    let selectedUserIds = [];
    let areaPage = 1;
    const areasPerPage = 8;

    const iconsMap = {
        'server': '<i class="fas fa-server"></i>',
        'cloud': '<i class="fas fa-cloud"></i>',
        'cpu': '<i class="fas fa-microchip"></i>',
        'database': '<i class="fas fa-database"></i>',
        'lock': '<i class="fas fa-lock"></i>',
        'code': '<i class="fas fa-code"></i>',
        'terminal': '<i class="fas fa-terminal"></i>',
        'monitor': '<i class="fas fa-desktop"></i>',
        'shield': '<i class="fas fa-shield-alt"></i>',
        'globe': '<i class="fas fa-globe"></i>',
        'box': '<i class="fas fa-box"></i>',
        'layers': '<i class="fas fa-layer-group"></i>',
        'users': '<i class="fas fa-users"></i>',
        'settings': '<i class="fas fa-cog"></i>',
        'tool': '<i class="fas fa-tools"></i>',
        'key': '<i class="fas fa-key"></i>',
        'hard-drive': '<i class="fas fa-hdd"></i>',
        'network': '<i class="fas fa-network-wired"></i>',
        'wifi': '<i class="fas fa-wifi"></i>',
        'bolt': '<i class="fas fa-bolt"></i>',
        'fire': '<i class="fas fa-fire"></i>',
        'rocket': '<i class="fas fa-rocket"></i>',
        'plug': '<i class="fas fa-plug"></i>',
        'sync': '<i class="fas fa-sync"></i>',
        'save': '<i class="fas fa-save"></i>',
        'print': '<i class="fas fa-print"></i>',
        'share': '<i class="fas fa-share-alt"></i>',
        'sitemap': '<i class="fas fa-sitemap"></i>',
        'project': '<i class="fas fa-project-diagram"></i>',
        'chart': '<i class="fas fa-chart-bar"></i>',
        'pie': '<i class="fas fa-chart-pie"></i>',
        'line': '<i class="fas fa-chart-line"></i>',
        'at': '<i class="fas fa-at"></i>',
        'envelope': '<i class="fas fa-envelope"></i>',
        'phone': '<i class="fas fa-phone"></i>',
        'video': '<i class="fas fa-video"></i>',
        'camera': '<i class="fas fa-camera"></i>',
        'image': '<i class="fas fa-image"></i>',
        'folder': '<i class="fas fa-folder"></i>',
        'briefcase': '<i class="fas fa-briefcase"></i>',
        'bookmark': '<i class="fas fa-bookmark"></i>',
        'tag': '<i class="fas fa-tag"></i>',
        'heart': '<i class="fas fa-heart"></i>',
        'star': '<i class="fas fa-star"></i>',
        'bell': '<i class="fas fa-bell"></i>',
        'calendar': '<i class="fas fa-calendar-alt"></i>',
        'clock': '<i class="fas fa-clock"></i>',
        'mobile': '<i class="fas fa-mobile-alt"></i>',
        'tablet': '<i class="fas fa-tablet-alt"></i>',
        'laptop': '<i class="fas fa-laptop"></i>'
    };

    let currentFilterArea = 'all';
    let searchQuery = '';

    window.initHeader = function() {
        const totalCountEl = document.getElementById('totalPlatformsCount');
        const totalItemsCountEl = document.getElementById('totalItemsCount');
        if (totalCountEl && window.__areaData) {
            totalCountEl.textContent = window.__areaData.length;
        }
        if (totalItemsCountEl && window.__areaData) {
            totalItemsCountEl.textContent = window.__areaData.length;
        }

        const searchInp = document.getElementById('platformSearch');
        if (searchInp) {
            searchInp.oninput = (e) => {
                searchQuery = e.target.value.toLowerCase();
                areaPage = 1; // Reset to first page on search
                renderPlatformGrid();
            };
        }

        // Pagination Listeners
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        if (prevBtn) prevBtn.onclick = () => { if (areaPage > 1) { areaPage--; renderPlatformGrid(); } };
        if (nextBtn) nextBtn.onclick = () => { 
            const areas = window.__areaData || [];
            const totalPages = Math.ceil(areas.length / areasPerPage);
            if (areaPage < totalPages) { areaPage++; renderPlatformGrid(); } 
        };

        const areaSelect = document.getElementById('modalAreaSelect');
        if (areaSelect && window.__areaData) {
            const currentVal = areaSelect.value;
            areaSelect.innerHTML = '<option value="" disabled selected>Seleccione un área...</option>';
            window.__areaData.forEach(area => {
                areaSelect.innerHTML += `<option value="${area.id}">${area.name.toUpperCase()}</option>`;
            });
            if (currentVal) areaSelect.value = currentVal;
        }
    }

    window.renderPlatformGrid = function() {
        const grid = document.getElementById('platformGrid');
        const emptyState = document.getElementById('emptyState');
        if (!grid) return;
        grid.innerHTML = '';

        // Data Source
        const areas = window.__areaData || [];
        
        // Filter Areas by search
        let filtered = areas.filter(a => {
            return !searchQuery || 
                   a.name.toLowerCase().includes(searchQuery) || 
                   (a.description && a.description.toLowerCase().includes(searchQuery));
        });

        // Pagination Logic
        const totalItems = filtered.length;
        const totalPages = Math.max(1, Math.ceil(totalItems / areasPerPage));
        if (areaPage > totalPages) areaPage = totalPages;

        const start = (areaPage - 1) * areasPerPage;
        const end = start + areasPerPage;
        const paginatedAreas = filtered.slice(start, end);

        // Update Footer
        const itemsShownEl = document.getElementById('itemsShown');
        const totalItemsCountEl = document.getElementById('totalItemsCount');
        const currentPageNumEl = document.getElementById('currentPageNum');
        const totalPagesNumEl = document.getElementById('totalPagesNum');
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');

        if (itemsShownEl) itemsShownEl.textContent = paginatedAreas.length;
        if (totalItemsCountEl) totalItemsCountEl.textContent = totalItems;
        if (currentPageNumEl) currentPageNumEl.textContent = areaPage;
        if (totalPagesNumEl) totalPagesNumEl.textContent = totalPages;
        
        if (prevBtn) prevBtn.disabled = (areaPage === 1);
        if (nextBtn) nextBtn.disabled = (areaPage === totalPages);

        if (totalItems === 0) {
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }
        if (emptyState) emptyState.classList.add('hidden');
        paginatedAreas.forEach((area, idx) => {
            const card = document.createElement('div');
            const areaColor = area.color || '#6366f1';
            const areaPlatforms = window.__platformData[area.id] || [];
            const platCount = areaPlatforms.length;
            const userCount = areaPlatforms.reduce((acc, p) => acc + (p.users_count || 0), 0);
            const status = area.status || 'Activo';
            const statusColor = status === 'Activo' ? 'emerald' : 'rose';
            const areaIcon = iconsMap[area.icon] || '<i class="fas fa-folder"></i>';
            
            card.className = "group relative flex flex-col h-full bg-panel-fill border border-panel-border rounded-2xl overflow-hidden transition-all duration-300 hover:border-primary/40 hover:shadow-xl hover:shadow-primary/5 p-8";
            
            card.innerHTML = `
                <!-- Sobrio Top Border -->
                <div class="absolute top-0 left-0 w-full h-0.5 bg-panel-border/30">
                    <div class="h-full bg-primary/40 opacity-0 group-hover:opacity-100 transition-all duration-500" style="width: 100%"></div>
                </div>

                <div class="relative z-10 flex items-center gap-6 mb-8">
                    <!-- Icon with Subtle Area Accent -->
                    <div class="w-16 h-16 rounded-2xl flex-shrink-0 flex items-center justify-center text-3xl transition-all duration-500 group-hover:scale-110 shadow-sm" 
                         style="background: ${areaColor}10; color: ${areaColor}; border: 1px solid ${areaColor}20">
                        ${areaIcon}
                    </div>
                    <div class="flex-1 min-w-0">
                        <h3 class="text-xl font-black text-label uppercase tracking-tighter group-hover:text-primary transition-colors leading-tight truncate">
                            ${area.name}
                        </h3>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="w-2.5 h-2.5 rounded-full bg-${statusColor}-500"></span>
                            <span class="text-[11px] font-black uppercase tracking-widest text-label/70">${status}</span>
                        </div>
                    </div>
                </div>

                <div class="relative z-10 flex-1 space-y-6">
                    <!-- Metrics Badges -->
                    <div class="flex items-center gap-4">
                        <div class="px-4 py-2 rounded-xl bg-surface-container/50 border border-panel-border flex items-center gap-2.5">
                            <i class="fas fa-layer-group text-xs text-primary/60"></i>
                            <span class="text-[13px] font-bold uppercase tracking-widest text-label/80">${platCount} <span class="opacity-60">Plataformas</span></span>
                        </div>
                        <div class="px-4 py-2 rounded-xl bg-surface-container/50 border border-panel-border flex items-center gap-2.5">
                            <i class="fas fa-users text-xs text-primary/60"></i>
                            <span class="text-[13px] font-bold uppercase tracking-widest text-label/80">${userCount} <span class="opacity-60">Usuarios</span></span>
                        </div>
                    </div>
                    
                    <p class="text-base text-label/80 leading-relaxed font-bold line-clamp-2 italic border-l-4 border-panel-border/50 pl-5">
                        ${area.description || 'Gestión centralizada de servicios digitales.'}
                    </p>
                </div>

                <div class="relative z-10 mt-8 pt-6 border-t border-panel-border/30">
                    <button class="w-full h-14 rounded-xl flex items-center justify-center gap-4 text-xs font-black uppercase tracking-[0.2em] bg-surface-container/40 border border-panel-border text-label/60 hover:bg-primary hover:text-white hover:border-primary hover:shadow-lg hover:shadow-primary/20 transition-all duration-300" 
                            onclick="drillDown('${area.name}', ${area.id})">
                        <span>Gestionar Área</span>
                        <i class="fas fa-chevron-right text-xs opacity-50 group-hover:translate-x-1 transition-transform"></i>
                    </button>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    function hexToRGB(hex) {
        hex = hex.replace('#', '');
        if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        return `${r}, ${g}, ${b}`;
    }

    window.drillDown = function(areaName, areaId) {
        currentArea = areaName;
        currentAreaId = areaId;

        const platforms = (window.__platformData && (window.__platformData[areaId] || window.__platformData[String(areaId)])) || [];

        const gridView = document.getElementById('gridView');
        const drillDownView = document.getElementById('drillDownView');
        
        if (gridView) gridView.classList.add('hidden');
        if (drillDownView) {
            drillDownView.classList.remove('hidden');
            drillDownView.style.display = 'flex';
        }
        
        const breadcrumb = document.getElementById('breadcrumbDrilldown');
        const breadcrumbArea = document.getElementById('breadcrumbArea');
        if (breadcrumb) breadcrumb.classList.remove('hidden');
        if (breadcrumbArea) breadcrumbArea.textContent = areaName;

        renderPlatformsTable(platforms);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    window.showCatalog = function() {
        document.getElementById('gridView').classList.remove('hidden');
        document.getElementById('drillDownView').classList.add('hidden');
        document.getElementById('breadcrumbDrilldown').classList.add('hidden');
        initHeader();
        renderPlatformGrid();
    };



    let platformsDataTable;

    function initPlatformsDataTable() {
        const tableEl = $('#modern-table');
        if (!tableEl.length || $.fn.dataTable.isDataTable('#modern-table')) return;

        platformsDataTable = tableEl.DataTable({
            data: [],
            columns: [
                { 
                    data: 'id', 
                    width: '50px', 
                    orderable: false,
                    className: 'text-center',
                    render: (data) => `
                        <div class="flex items-center justify-center">
                            <input type="checkbox" class="platform-checkbox w-4 h-4 rounded border-panel-border text-primary focus:ring-primary/20 cursor-pointer" data-id="${data}" onchange="updateActionButtons()">
                        </div>` 
                },
                { 
                    data: null, 
                    width: '80px',
                    orderable: false,
                    className: 'text-center',
                    render: (data) => {
                        const style = `background: ${data.bg_color || '#6366f1'}; color: ${data.text_color || '#ffffff'}`;
                        return `
                            <div class="flex items-center justify-center h-full">
                                <div class="w-8 h-8 min-w-[32px] min-h-[32px] aspect-square flex-shrink-0 rounded-[8px] flex items-center justify-center transition-all group-hover:scale-110 shadow-sm border border-white/5" style="${style}">
                                    <div class="text-[14px] flex items-center justify-center leading-none">
                                        ${data.logo_url ? `<img src="${data.logo_url}" class="w-full h-full object-cover rounded-[8px]">` : (iconsMap[data.icon] || iconsMap['box'])}
                                    </div>
                                </div>
                            </div>`;
                    }
                },
                { 
                    data: 'name', 
                    width: '20%',
                    className: 'text-left',
                    render: (data) => `
                        <div class="flex flex-col">
                            <span class="text-sm font-black text-primary uppercase italic leading-none">${data}</span>
                        </div>` 
                },
                { 
                    data: 'direct_link', 
                    width: '230px',
                    render: (data) => `
                        <div class="flex items-center gap-2">
                            <i class="fas fa-link text-[10px] text-label/20"></i>
                            <span class="text-[10px] text-label/40 font-bold truncate max-w-[200px]">${data || 'SIN ENLACE'}</span>
                        </div>` 
                },
                { 
                    data: 'description', 
                    width: '35%',
                    className: 'text-left',
                    render: (data) => `<div class="text-[12px] text-label/60 font-bold line-clamp-2 pr-8">${data || '-'}</div>` 
                },
                { 
                    data: 'users_count', 
                    width: '100px',
                    className: 'text-center',
                    render: (data) => `
                        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-surface-container text-label/60 font-black text-[10px] uppercase">
                            <i class="fas fa-users opacity-40"></i> ${data || 0}
                        </div>` 
                },
                { 
                    data: 'status', 
                    width: '110px',
                    className: 'text-center',
                    render: (data) => {
                        const cls = data === 'Activo' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500';
                        return `<span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${cls}">${data}</span>`;
                    }
                },
                { 
                    data: null, 
                    width: '100px',
                    className: 'text-center',
                    render: () => `<span class="font-mono text-[10px] font-bold text-label/40">0 VISITAS</span>` 
                }
            ],
            autoWidth: false,
            pageLength: getPageLength(),
            pagingType: 'simple',
            order: [[2, 'asc']],
            layout: {
                topStart: null,
                topEnd: null,
                bottomStart: 'info',
                bottomEnd: 'paging'
            },
            language: {
                zeroRecords: "No se encontraron registros",
                info: "Mostrando _START_-_END_ de _TOTAL_",
                infoEmpty: "Mostrando 0-0 de 0",
                paginate: {
                    previous: '<i class="fas fa-chevron-left text-[10px]"></i>',
                    next: '<i class="fas fa-chevron-right text-[10px]"></i>'
                }
            },
            drawCallback: function(settings) {
                renderGhostRows(settings, 8);
            }
        });

        // Row Click Edit Integration
        $('#modern-table tbody').on('click', 'tr', function(e) {
            // Ignore if clicking on checkbox or its container
            if ($(e.target).closest('.platform-checkbox').length || $(e.target).is('input[type="checkbox"]')) {
                return;
            }
            
            // Ignore ghost rows
            if ($(this).hasClass('ghost-row')) return;

            const cb = $(this).find('.platform-checkbox');
            if (cb.length) {
                // Clear other selections for single-edit clarity
                $('.platform-checkbox').prop('checked', false);
                cb.prop('checked', true);
                window.updateActionButtons();
                
                // Trigger the edit modal
                $('[data-action="platforms-edit-selected"]').trigger('click');
            }
        });

        // Add visual cue for interactivity
        $('#modern-table').addClass('cursor-pointer');

        window.activeNexusTable = platformsDataTable;
    }

    function renderPlatformsTable(data) {
        if (!platformsDataTable) initPlatformsDataTable();
        
        platformsDataTable.clear();
        platformsDataTable.rows.add(data);
        platformsDataTable.draw();
        
        updateActionButtons();
    }

    function getPageLength() {
        const h = window.innerHeight;
        return h < 900 ? 9 : 10;
    }

    function renderGhostRows(settings, columns) {
        const api = new $.fn.dataTable.Api(settings);
        const info = api.page.info();
        const tbody = $(settings.nTBody);
        const pageLen = api.page.len();

        tbody.find('.ghost-row').remove();
        
        const realRows = info.end - info.start;
        const ghostCount = pageLen - realRows;
        if (ghostCount <= 0) return;

        let ghostHtml = '';
        for (let i = 0; i < ghostCount; i++) {
            // Apply zebra striping to ghost rows based on their index
            const isEven = (realRows + i) % 2 === 0;
            const bgClass = isEven ? 'bg-white' : 'bg-slate-50/50';
            
            ghostHtml += `
                <tr class="ghost-row pointer-events-none select-none ${bgClass}">
                    <td class="py-5 text-center"><div></div></td>
                    <td class="py-5 text-center"><div></div></td>
                    <td class="py-5 text-left"><div></div></td>
                    <td class="py-5 text-left"><div></div></td>
                    <td class="py-5 text-left"><div></div></td>
                    <td class="py-5 text-center"><div></div></td>
                    <td class="py-5 text-center"><div></div></td>
                    <td class="py-5 text-center"><div></div></td>
                </tr>`;
        }
        tbody.append(ghostHtml);
    }

    window.updateActionButtons = function() {
        const selected = document.querySelectorAll('.platform-checkbox:checked');
        const btnEdit = document.getElementById('btnEditPlatform');
        const btnDelete = document.getElementById('btnDeletePlatform');
        const selectAll = document.getElementById('selectAllPlatforms');
        
        if (btnEdit) {
            const isDisabled = selected.length !== 1;
            btnEdit.disabled = isDisabled;
            btnEdit.classList.toggle('text-slate-400', isDisabled);
            btnEdit.classList.toggle('text-slate-700', !isDisabled);
            btnEdit.classList.toggle('opacity-40', isDisabled);
            btnEdit.classList.toggle('opacity-100', !isDisabled);
        }

        if (btnDelete) {
            const isDisabled = selected.length === 0;
            btnDelete.disabled = isDisabled;
            btnDelete.classList.toggle('text-rose-300', isDisabled);
            btnDelete.classList.toggle('text-rose-600', !isDisabled);
            btnDelete.classList.toggle('opacity-40', isDisabled);
            btnDelete.classList.toggle('opacity-100', !isDisabled);
        }

        if (selectAll) {
            const allCheckboxes = document.querySelectorAll('.platform-checkbox');
            selectAll.checked = allCheckboxes.length > 0 && selected.length === allCheckboxes.length;
            selectAll.indeterminate = selected.length > 0 && selected.length < allCheckboxes.length;
        }
    };

    // Modal Wizard Logic
    function changeStep(step) {
        currentStep = step;
        const progress = document.getElementById('stepProgress');
        const btnNext = document.getElementById('btnNext');
        const btnSubmit = document.getElementById('btnSubmit');
        const btnBack = document.getElementById('btnBack');
        const btnCancel = document.getElementById('btnCancel');

        document.querySelectorAll('.modal-step').forEach(s => s.classList.add('hidden'));
        const targetStep = document.getElementById(`step${step}`);
        if (targetStep) targetStep.classList.remove('hidden');

        if (step === 1) {
            if (progress) progress.style.width = '0%';
            if (btnNext) { btnNext.style.display = 'flex'; btnNext.classList.remove('hidden'); }
            if (btnSubmit) { btnSubmit.style.display = 'none'; btnSubmit.classList.add('hidden'); }
            if (btnBack) { btnBack.style.display = 'none'; btnBack.classList.add('hidden'); }
        } else if (step === 2) {
            if (progress) progress.style.width = '50%';
            if (btnNext) { btnNext.style.display = 'flex'; btnNext.classList.remove('hidden'); }
            if (btnSubmit) { btnSubmit.style.display = 'none'; btnSubmit.classList.add('hidden'); }
            if (btnBack) { btnBack.style.display = 'flex'; btnBack.classList.remove('hidden'); }
        } else {
            if (progress) progress.style.width = '100%';
            if (btnNext) { btnNext.style.display = 'none'; btnNext.classList.add('hidden'); }
            if (btnSubmit) { btnSubmit.style.display = 'flex'; btnSubmit.classList.remove('hidden'); }
            if (btnBack) { btnBack.style.display = 'flex'; btnBack.classList.remove('hidden'); }
        }
        
        updateLivePreview();
        
        // Cancel button visibility
        if (btnCancel) {
            if (step === 1) {
                btnCancel.style.display = 'flex';
                btnCancel.classList.remove('hidden');
            } else {
                btnCancel.style.display = 'none';
                btnCancel.classList.add('hidden');
            }
        }
    }

    // URL Premium Validation
    const urlInput = document.getElementById('directLinkInput');
    urlInput?.addEventListener('input', function() {
        const url = this.value;
        const isValid = /^(https?:\/\/)/.test(url);
        if (url.length > 0 && !isValid) {
            this.classList.add('border-rose-500', 'bg-rose-50');
            this.classList.remove('border-panel-border', 'bg-input-bg');
        } else {
            this.classList.remove('border-rose-500', 'bg-rose-50');
            this.classList.add('border-panel-border', 'bg-input-bg');
        }
    });

    window.handleStepNext = function() {
        const Toast = Swal.mixin({
            toast: true,
            position: 'bottom-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });

        const nameInp = document.querySelector('input[name="name"]');
        const descInp = document.querySelector('textarea[name="description"]');
        const linkInp = document.getElementById('directLinkInput');
        const form = document.getElementById('createPlatformForm');
        const isEdit = form.dataset.mode === 'edit';
        const editId = form.dataset.editId;

        if (currentStep === 1) {
            let hasError = false;
            
            // Basic required validation
            [nameInp, descInp, linkInp].forEach(inp => {
                if (!inp || !inp.value.trim()) {
                    if (inp) inp.classList.add('border-rose-500', 'bg-rose-50', 'animate-shake');
                    hasError = true;
                } else {
                    inp.classList.remove('border-rose-500', 'bg-rose-50', 'animate-shake');
                }
            });

            // Premium URL Validation
            const urlPattern = /^(https?:\/\/)/;
            if (linkInp && linkInp.value.trim() && !urlPattern.test(linkInp.value.trim())) {
                linkInp.classList.add('border-rose-500', 'bg-rose-50', 'animate-shake');
                Toast.fire({ icon: 'warning', title: 'URL inválida', text: 'Debe iniciar con http:// o https://' });
                hasError = true;
            }

            // DUPLICATE NAME VALIDATION (Within same Area)
            if (nameInp && nameInp.value.trim()) {
                const newName = nameInp.value.trim().toLowerCase();
                const existingPlatforms = window.__platformData[currentAreaId] || window.__platformData[String(currentAreaId)] || [];
                
                const isDuplicate = existingPlatforms.some(p => {
                    // If editing, skip the current record by ID
                    if (isEdit && p.id == editId) return false;
                    return p.name.toLowerCase() === newName;
                });

                if (isDuplicate) {
                    nameInp.classList.add('border-rose-500', 'bg-rose-50', 'animate-shake');
                    Toast.fire({ 
                        icon: 'error', 
                        title: 'Nombre Duplicado', 
                        text: `El servicio "${nameInp.value}" ya existe en esta área.` 
                    });
                    hasError = true;
                }
            }

            if (hasError) return;
        }

        if (currentStep === 2) {
            const mode = document.getElementById('logoUploadZone')?.classList.contains('hidden') ? 'icon' : 'image';
            if (mode === 'image') {
                const logoInput = document.getElementById('logoInput');
                const hasPreview = document.querySelector('#logoUploadZone img');
                if (!logoInput?.files[0] && !hasPreview) {
                    Toast.fire({ icon: 'warning', title: 'Identidad Requerida', text: 'Debe subir un logo o elegir un icono' });
                    return;
                }
            }
        }

        if (currentStep < 3) changeStep(currentStep + 1);
    };

    window.handleStepBack = function() {
        if (currentStep > 1) changeStep(currentStep - 1);
    };

    function populateIconGrid() {
        const grid = document.getElementById('iconSelectorZone');
        if (!grid) return;
        grid.innerHTML = '';
        Object.entries(iconsMap).forEach(([key, svg]) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = "w-full aspect-square flex items-center justify-center text-base text-label/40 hover:bg-primary/10 hover:text-primary transition-all border-b border-r border-panel-border/50";
            btn.innerHTML = svg;
            btn.onclick = () => {
                document.querySelectorAll('#iconSelectorZone button').forEach(b => b.classList.remove('bg-primary', 'text-white'));
                btn.classList.add('bg-primary', 'text-white');
                document.getElementById('selectedIconInput').value = key;
                updateLivePreview();
            };
            grid.appendChild(btn);
        });
    }

    window.setVisualMode = function(mode) {
        const logoZone = document.getElementById('logoUploadZone');
        const iconZone = document.getElementById('iconSelectorZone');
        const btnImage = document.getElementById('btnModeImage');
        const btnIcon = document.getElementById('btnModeIcon');
        const textColorCtrl = document.getElementById('textColorControl');
        const bgColorCtrl = document.getElementById('bgColorControl');

        if (logoZone) logoZone.classList.toggle('hidden', mode !== 'image');
        if (iconZone) iconZone.classList.toggle('hidden', mode !== 'icon');
        
        const isIconMode = mode === 'icon';
        [textColorCtrl, bgColorCtrl].forEach(ctrl => {
            if (ctrl) {
                ctrl.style.opacity = isIconMode ? '1' : '0.4';
                ctrl.querySelectorAll('input').forEach(i => i.disabled = !isIconMode);
            }
        });

        if (btnImage) {
            btnImage.classList.toggle('bg-white', mode === 'image');
            btnImage.classList.toggle('text-label/40', mode !== 'image');
        }
        if (btnIcon) {
            btnIcon.classList.toggle('bg-white', mode === 'icon');
            btnIcon.classList.toggle('text-label/40', mode !== 'icon');
        }
        
        if (mode === 'icon') populateIconGrid();
        updateLivePreview();
    };

    function updateLivePreview() {
        const colorInp = document.getElementById('bgColorInput');
        const iconInp = document.getElementById('selectedIconInput');
        const textColorInp = document.getElementById('textColorInput');
        
        // Forced Defaults if values are missing or suspicious
        let color = colorInp ? colorInp.value : '#000000';
        let textColor = textColorInp ? textColorInp.value : '#ffffff';
        const iconKey = iconInp ? iconInp.value : 'box';
        
        // If it's a new form and values are both black (browser reset bug), force Nexus defaults
        if (color === '#000000' && textColor === '#000000') {
            textColor = '#ffffff';
            if (textColorInp) textColorInp.value = '#ffffff';
        }

        const bgColorText = document.getElementById('bgColorText');
        const textColorText = document.getElementById('textColorText');
        
        if (bgColorText) bgColorText.value = color.toUpperCase();
        if (textColorText) textColorText.value = textColor.toUpperCase();

        const logoUploadZone = document.getElementById('logoUploadZone');
        const logoInput = document.getElementById('logoInput');

        if (logoUploadZone && logoInput && logoInput.files && logoInput.files[0]) {
            const reader = new FileReader();
            reader.onload = (e) => {
                logoUploadZone.innerHTML = `
                    <div class="relative w-full h-full flex flex-col items-center justify-center p-4 group">
                        <img src="${e.target.result}" class="max-w-full max-h-[140px] object-contain rounded-xl shadow-lg">
                        <button type="button" onclick="document.getElementById('logoInput').click()" 
                                class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-[10px] font-black uppercase tracking-widest transition-all">
                            Cambiar Logo
                        </button>
                    </div>
                `;
            };
            reader.readAsDataURL(logoInput.files[0]);
        }

        const selectedBtn = document.querySelector('#iconSelectorZone button.bg-primary');
        if (selectedBtn) {
            selectedBtn.style.backgroundColor = color;
            selectedBtn.style.color = textColor;
        }
    }

    // Hex sync listeners
    ['bgColor', 'textColor'].forEach(prefix => {
        const picker = document.getElementById(`${prefix}Input`);
        const text = document.getElementById(`${prefix}Text`);
        if (picker && text) {
            picker.addEventListener('input', () => {
                text.value = picker.value.toUpperCase();
                updateLivePreview();
            });
            text.addEventListener('change', () => {
                if (/^#[0-9A-F]{6}$/i.test(text.value)) {
                    picker.value = text.value;
                    updateLivePreview();
                }
            });
        }
    });

    // Picklist logic
    function updatePicklist() {
        const availableList = document.getElementById('availableList');
        const assignedList = document.getElementById('assignedList');
        availableList.innerHTML = '';
        assignedList.innerHTML = '';
        
        window.__allUsers.forEach(u => {
            const isActive = selectedUserIds.includes(u.id);
            const item = document.createElement('div');
            item.className = `p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between group ${isActive ? 'bg-primary/10 border-primary/20 hover:bg-primary/20' : 'bg-panel-fill border-panel-border hover:border-primary/40'}`;
            item.innerHTML = `
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg ${isActive ? 'bg-primary text-white' : 'bg-surface-container text-label/40'} flex items-center justify-center text-[10px] font-black uppercase">
                        ${u.name.substring(0, 2)}
                    </div>
                    <div class="flex flex-col">
                        <span class="text-xs font-bold text-text">${u.name}</span>
                        <span class="text-[10px] text-label/40 font-bold uppercase">${u.email}</span>
                    </div>
                </div>
                <i class="fas ${isActive ? 'fa-minus-circle text-rose-500' : 'fa-plus-circle text-primary opacity-20 group-hover:opacity-100'} transition-opacity"></i>
            `;
            item.onclick = () => {
                if (isActive) selectedUserIds = selectedUserIds.filter(id => id !== u.id);
                else selectedUserIds.push(u.id);
                updatePicklist();
            };
            
            if (isActive) assignedList.appendChild(item);
            else availableList.appendChild(item);
        });
        document.getElementById('selectedUsersInput').value = JSON.stringify(selectedUserIds);
    }

    // Init
    document.addEventListener('DOMContentLoaded', () => {
        initHeader();
        renderPlatformGrid();

        // Search Integration
        $('#platformSearchSub').on('input', function() {
            if (platformsDataTable) {
                platformsDataTable.search(this.value).draw();
            }
        });

        // Bindings
        document.querySelectorAll('[data-action="platforms-step-next"]').forEach(b => b.onclick = handleStepNext);
        document.querySelectorAll('[data-action="platforms-step-back"]').forEach(b => b.onclick = handleStepBack);
        document.querySelectorAll('[data-action="platforms-close-modal"]').forEach(b => b.onclick = () => window.closeModal('platformModal'));
        function resetIdentity() {
            const bgI = document.getElementById('bgColorInput');
            const txI = document.getElementById('textColorInput');
            const bgT = document.getElementById('bgColorText');
            const txT = document.getElementById('textColorText');
            if (bgI) bgI.value = '#000000';
            if (txI) txI.value = '#ffffff';
            if (bgT) bgT.value = '#000000';
            if (txT) txT.value = '#FFFFFF';
            setVisualMode('image');
        }

        // Global Delegation for Modal Creation (fixes lost bindings)
        $(document).on('click', '[data-action="platforms-open-create-modal"]', function() {
            const form = document.getElementById('createPlatformForm');
            if (!form) return;
            form.reset();
            resetIdentity();
            form.dataset.mode = 'create';
            document.getElementById('platformModalTitle').textContent = "Registrar Nueva Plataforma";
            
            const areaSelect = document.getElementById('modalAreaSelect');
            if (areaSelect) {
                areaSelect.value = currentAreaId || "";
            }
            
            selectedUserIds = [];
            changeStep(1);
            updatePicklist();
            window.openModal('platformModal');
        });

        // Global Delegation for Edit
        $(document).on('click', '[data-action="platforms-edit-selected"]', function() {
            const selected = document.querySelector('.platform-checkbox:checked');
            if (!selected) return;
            
            const platId = selected.dataset.id;
            let palt = null;

            if (platformsDataTable) {
                palt = platformsDataTable.row($(selected).closest('tr')).data();
            }

            if (!palt) {
                const areaPlats = window.__platformData[currentAreaId] || window.__platformData[String(currentAreaId)] || [];
                palt = areaPlats.find(p => p.id == platId);
            }
            
            if (!palt) {
                Swal.fire('Error', 'No se pudieron recuperar los datos.', 'error');
                return;
            }

            const form = document.getElementById('createPlatformForm');
            if (!form) return;
            
            // TITULO INMEDIATO
            document.getElementById('platformModalTitle').textContent = "Modificar Plataforma";
            
            form.reset();
            resetIdentity();
            form.dataset.mode = 'edit';
            form.dataset.editId = palt.id;
            
            // FILL DATA WITH MICRO-DELAY TO OVERRIDE ANY MODAL RESET
            setTimeout(() => {
                console.log("Nexus Population - Data:", palt);
                
                $('#createPlatformForm [name="name"]').val(palt.name || '');
                $('#createPlatformForm [name="description"]').val(palt.description || '');
                $('#createPlatformForm [name="direct_link"]').val(palt.direct_link || '');
                $('#createPlatformForm [name="area_id"]').val(palt.area_id || currentAreaId);

                const statusToggle = document.getElementById('platformStatusToggle');
                if (statusToggle) {
                    statusToggle.checked = (palt.status === 'Activo');
                    statusToggle.dispatchEvent(new Event('change'));
                }

                // Identity Sync
                $('#bgColorInput').val(palt.bg_color || '#000000');
                $('#textColorInput').val(palt.text_color || '#ffffff');
                $('#selectedIconInput').val(palt.icon || 'box');
                
                if (palt.logo_url) setVisualMode('image');
                else setVisualMode('icon');

                selectedUserIds = palt.user_ids || [];
                updatePicklist();
                updateLivePreview();
                console.log("Nexus Population - Complete");
            }, 50);

            changeStep(1);
            window.openModal('platformModal');
        });

        // Global Delegation for Delete with Block Validation
        $(document).on('click', '[data-action="platforms-delete-selected"]', async function() {
            const selected = document.querySelectorAll('.platform-checkbox:checked');
            if (selected.length === 0) return;

            let totalUsersAffected = 0;
            selected.forEach(cb => {
                const row = platformsDataTable.row($(cb).closest('tr')).data();
                if (row) totalUsersAffected += (row.users_count || 0);
            });

            // BLOCK LOGIC: Cannot delete if has users
            if (totalUsersAffected > 0) {
                return Swal.fire({
                    title: '<span class="text-rose-500 uppercase italic font-black tracking-tighter">Acción Bloqueada</span>',
                    html: `<div class="text-xs font-bold text-slate-300 leading-relaxed uppercase tracking-widest">
                            No es posible eliminar plataformas con usuarios activos.<br><br>
                            Se detectaron <span class="text-rose-500 font-black">${totalUsersAffected} accesos vinculados</span>.<br>
                            Por favor, remueva los accesos de los usuarios antes de intentar dar de baja el servicio.
                           </div>`,
                    icon: 'error',
                    confirmButtonText: 'Entendido',
                    confirmButtonColor: '#6366f1',
                    background: '#1e293b',
                    color: '#ffffff',
                    backdrop: 'rgba(15, 23, 42, 0.75)'
                });
            }

            // Standard Confirmation for empty platforms
            const confirm = await Swal.fire({
                title: '<span class="text-white uppercase italic font-black tracking-tighter">¿Confirmar Baja?</span>',
                html: `<div class="text-xs font-bold text-slate-300 uppercase tracking-widest">Se eliminarán ${selected.length} servicios de forma permanente.</div>`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#f43f5e',
                confirmButtonText: 'Sí, Ejecutar Baja',
                cancelButtonText: 'Cancelar',
                background: '#1e293b',
                color: '#ffffff',
                backdrop: 'rgba(15, 23, 42, 0.75)'
            });

            if (confirm.isConfirmed) {
                const procModal = document.getElementById('processingModal');
                if (procModal) {
                    procModal.classList.remove('hidden');
                    procModal.classList.add('flex');
                    setTimeout(() => procModal.classList.add('show'), 50);
                }

                try {
                    await Promise.all(Array.from(selected).map(cb => fetch(`/admin/platforms/delete/${cb.dataset.id}`, { method: 'GET' })));
                    startSuccessCountdown("Los servicios han sido purgados permanentemente del catálogo.");
                } catch (e) {
                    if (procModal) procModal.classList.add('hidden');
                    Swal.fire('Error', 'Fallo técnico al procesar la baja.', 'error');
                }
            }
        });

        // Select All Handler
        document.getElementById('selectAllPlatforms')?.addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.platform-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
            updateActionButtons();
        });

        // Visual Mode Switcher (Icon vs Image)
        $(document).on('click', '[data-action="platforms-visual-mode"]', function() {
            window.setVisualMode(this.dataset.mode);
        });

        document.getElementById('logoInput').addEventListener('change', updateLivePreview);
        document.querySelector('input[name="name"]').addEventListener('input', updateLivePreview);
        document.querySelectorAll('.js-sync-color').forEach(p => p.addEventListener('input', (e) => {
            document.getElementById(e.target.dataset.textInputId).value = e.target.value.toUpperCase();
            document.getElementById(e.target.dataset.swatchId).style.background = e.target.value;
            updateLivePreview();
        }));

        // Status Toggle Handler
        document.getElementById('platformStatusToggle')?.addEventListener('change', function() {
            const label = document.getElementById('platformStatusLabel');
            if (this.checked) {
                label.textContent = "Activo / Disponible";
                label.className = "text-xs font-black text-emerald-500 uppercase";
            } else {
                label.textContent = "Inactivo / Deshabilitado";
                label.className = "text-xs font-black text-slate-400 uppercase";
            }
        });

        document.getElementById('createPlatformForm').onsubmit = async (e) => {
            e.preventDefault();
            const form = e.target;
            const isEdit = form.dataset.mode === 'edit';
            const url = isEdit ? `/admin/platforms/edit-platform/${form.dataset.editId}` : '/admin/platforms/add-platform';
            
            const formData = new FormData(form);
            
            // Critical Fail-safe for area_id
            if (!formData.get('area_id') || formData.get('area_id') === '') {
                formData.set('area_id', currentAreaId);
            }

            if (!formData.get('area_id')) {
                Swal.fire('Error de Contexto', 'No se ha detectado el Área de origen. Por favor, reintente.', 'error');
                return;
            }

            formData.append('users', JSON.stringify(selectedUserIds));
            
            const isChecked = document.getElementById('platformStatusToggle').checked;
            formData.append('status', isChecked ? 'Activo' : 'Inactivo');

            const procModal = document.getElementById('processingModal');
            if (procModal) {
                procModal.classList.remove('hidden');
                procModal.classList.add('flex');
                setTimeout(() => procModal.classList.add('show'), 50);
            }

            try {
                const res = await fetch(url, { method: 'POST', body: formData });
                const result = await res.json();
                
                const Toast = Swal.mixin({
                    toast: true,
                    position: 'bottom-end',
                    showConfirmButton: false,
                    timer: 4000,
                    timerProgressBar: true
                });

                if (result.success) {
                    startSuccessCountdown("La plataforma y sus parámetros de acceso han sido actualizados correctamente.");
                } else {
                    console.error("Backend Error:", result.error);
                    Toast.fire({ 
                        icon: 'error', 
                        title: 'Error de Procesamiento',
                        text: 'No pudimos guardar los cambios. Verifique los datos e intente de nuevo.'
                    });
                }
            } catch (err) {
                console.error("Connection Error:", err);
                Swal.fire({
                    toast: true,
                    position: 'bottom-end',
                    icon: 'error',
                    title: 'Error de Red',
                    text: 'Fallo técnico en la conexión con el servidor.',
                    showConfirmButton: false,
                    timer: 4000
                });
            }
        };

        async function refreshPlatforms() {
            if (!currentAreaId) return;
            try {
                const res = await fetch(`/admin/platforms/api/list/${currentAreaId}`);
                const result = await res.json();
                if (result.success) {
                    // Update Global State
                    if (!window.__platformData) window.__platformData = {};
                    window.__platformData[currentAreaId] = result.platforms;
                    
                    // Force Table Refresh
                    renderPlatformsTable(result.platforms);
                }
            } catch (e) {
                console.error("Error refreshing platforms:", e);
            }
        }

        // Picklist Search Logic
        $(document).on('input', '.js-picklist-filter', function() {
            const query = this.value.toLowerCase();
            const targetListId = this.dataset.listId;
            const items = document.querySelectorAll(`#${targetListId} > div`);
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.classList.toggle('hidden', !text.includes(query));
            });
        });

        // Force Identity Reset to Nexus Standards
        const bgI = document.getElementById('bgColorInput');
        const txI = document.getElementById('textColorInput');
        const bgT = document.getElementById('bgColorText');
        const txT = document.getElementById('textColorText');

        if (bgI) bgI.value = '#000000';
        if (txI) txI.value = '#ffffff';
        if (bgT) bgT.value = '#000000';
        if (txT) txT.value = '#FFFFFF';

        // Initial state
        setVisualMode('image');
        updateLivePreview();
    });

})();
