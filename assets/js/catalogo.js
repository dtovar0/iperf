/**
 * NEXUS PORTAL ENGINE
 * Managed Service Catalog Logic with Pagination
 */

let currentPage = 1;
let itemsPerPage = 8;
let filteredPlatforms = [];

/**
 * Calculate items per page based on screen width to avoid scroll
 */
function calculateItemsPerPage() {
    const width = window.innerWidth;
    if (width < 640) return 2; // Mobile (2 rows of 1)
    if (width < 1024) return 4; // Tablet (2 rows of 2)
    return 8; // Desktop (2 rows of 4)
}

document.addEventListener('DOMContentLoaded', () => {
    itemsPerPage = calculateItemsPerPage();
    initPortalFilters();
    initPagination();
    const platforms = Array.from(document.querySelectorAll('.platform-card'));
    filteredPlatforms = platforms;
    updatePagination();
    updateStats();

    // Handle resize to adjust pagination dynamically
    window.addEventListener('resize', () => {
        const newItemsPerPage = calculateItemsPerPage();
        if (newItemsPerPage !== itemsPerPage) {
            itemsPerPage = newItemsPerPage;
            currentPage = 1; // Reset to page 1 on layout change
            updatePagination();
        }
    });
});

/**
 * Filter platforms by area or favorite status
 */
function initPortalFilters() {
    const filterButtons = document.querySelectorAll('.area-filter-btn');
    const platforms = Array.from(document.querySelectorAll('.platform-card'));
    const searchInput = document.getElementById('platformSearch');

    function applyFilters() {
        const activeTabBtn = document.querySelector('.area-filter-btn.bg-primary');
        const activeTab = activeTabBtn ? activeTabBtn.getAttribute('data-area') : 'all';
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';

        filteredPlatforms = platforms.filter(card => {
            const name = card.querySelector('h3').textContent.toLowerCase();
            const desc = card.querySelector('p').textContent.toLowerCase();
            const matchesSearch = name.includes(searchTerm) || desc.includes(searchTerm);
            
            let matchesTab = true;
            if (activeTab === 'favorites') {
                matchesTab = card.getAttribute('data-is-fav') === 'true';
            } else if (activeTab !== 'all') {
                matchesTab = card.getAttribute('data-area') === activeTab;
            }

            return matchesSearch && matchesTab;
        });

        currentPage = 1;
        updatePagination();
    }

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => {
                b.classList.remove('bg-primary', 'text-white', 'shadow-lg', 'shadow-primary/20');
                b.classList.add('bg-surface-container/50', 'text-label/40', 'border-panel-border');
            });
            btn.classList.add('bg-primary', 'text-white', 'shadow-lg', 'shadow-primary/20');
            btn.classList.remove('bg-surface-container/50', 'text-label/40', 'border-panel-border');
            applyFilters();
        });
    });

    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }
}

/**
 * Pagination Controls
 */
function initPagination() {
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                updatePagination();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredPlatforms.length / itemsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                updatePagination();
            }
        });
    }
}

/**
 * Update stat chips in header
 */
function updateStats() {
    const platforms = Array.from(document.querySelectorAll('.platform-card'));
    const favCount = platforms.filter(p => p.getAttribute('data-is-fav') === 'true').length;
    const totalEl = document.getElementById('totalCount');
    const favEl = document.getElementById('favCount');
    if (totalEl) totalEl.textContent = platforms.length;
    if (favEl) favEl.textContent = favCount;
}

/**
 * Update UI based on current page and filters
 */
function updatePagination() {
    const allPlatforms = document.querySelectorAll('.platform-card');
    const totalItems = filteredPlatforms.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
    
    // Hide all first
    allPlatforms.forEach(p => p.classList.add('hidden'));

    // Show only the slice
    const start = (currentPage - 1) * itemsPerPage;
    const end = Math.min(start + itemsPerPage, totalItems);
    const pageItems = filteredPlatforms.slice(start, end);

    pageItems.forEach(card => {
        card.classList.remove('hidden');
        // Trigger a fresh animation
        card.style.animation = 'none';
        card.offsetHeight; // trigger reflow
        card.style.animation = '';
        card.classList.add('animate-in', 'fade-in', 'zoom-in-95', 'duration-300');
    });

    // Update Footer Metrics (e.g. "Mostrando 1 - 8 de 15")
    const itemsShownSpan = document.getElementById('itemsShown');
    const totalItemsSpan = document.getElementById('totalItems');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (itemsShownSpan) {
        if (totalItems === 0) {
            itemsShownSpan.textContent = '0';
        } else {
            itemsShownSpan.textContent = `${start + 1} - ${end}`;
        }
    }
    
    if (totalItemsSpan) {
        totalItemsSpan.textContent = totalItems;
    }
    
    if (prevBtn) prevBtn.disabled = (currentPage === 1);
    if (nextBtn) nextBtn.disabled = (currentPage === totalPages || totalItems === 0);

    // Update page number indicator
    const currentPageNum = document.getElementById('currentPageNum');
    const totalPagesNum = document.getElementById('totalPagesNum');
    if (currentPageNum) currentPageNum.textContent = currentPage;
    if (totalPagesNum) totalPagesNum.textContent = totalPages;

    // Empty state toggle
    const emptyState = document.getElementById('emptyState');
    const grid = document.getElementById('platformsGrid');
    if (emptyState && grid) {
        if (totalItems === 0) {
            emptyState.classList.remove('hidden');
            emptyState.classList.add('flex');
            grid.style.visibility = 'hidden';
        } else {
            emptyState.classList.add('hidden');
            emptyState.classList.remove('flex');
            grid.style.visibility = 'visible';
        }
    }
}

/**
 * Toggle Favorite Status
 */
async function toggleFav(event, platformId) {
    if (event) event.stopPropagation();
    
    const btn = event.currentTarget;
    const icon = btn.querySelector('i');
    const card = btn.closest('.platform-card');
    const activeTabBtn = document.querySelector('.area-filter-btn.bg-primary');
    const activeTab = activeTabBtn ? activeTabBtn.getAttribute('data-area') : 'all';

    try {
        const res = await fetch('/catalogo/favorite/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify({ platform_id: platformId })
        });
        const data = await res.json();

        if (data.status === 'success') {
            const newFavState = data.is_favorite;
            card.setAttribute('data-is-fav', newFavState ? 'true' : 'false');
            
            if (newFavState) {
                icon.classList.remove('text-label/20');
                icon.classList.add('text-amber-400', 'drop-shadow-[0_0_8px_rgba(251,191,36,0.6)]');
            } else {
                icon.classList.add('text-label/20');
                icon.classList.remove('text-amber-400', 'drop-shadow-[0_0_8px_rgba(251,191,36,0.6)]');
            }

            updateStats();

            // Re-apply filters to handle visibility if in favorites tab
            if (activeTab === 'favorites') {
                const platforms = Array.from(document.querySelectorAll('.platform-card'));
                const searchInput = document.getElementById('platformSearch');
                const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
                
                filteredPlatforms = platforms.filter(p => {
                    const matchesTab = p.getAttribute('data-is-fav') === 'true';
                    const name = p.querySelector('h3').textContent.toLowerCase();
                    return matchesTab && name.includes(searchTerm);
                });

                const totalPages = Math.ceil(filteredPlatforms.length / itemsPerPage) || 1;
                if (currentPage > totalPages) currentPage = totalPages;
                
                updatePagination();
            }
        }
    } catch (e) {
        console.error(e);
    }
}

/**
 * Request Access to a platform
 */
async function requestAccess(platformId, platformName) {
    const modal = document.getElementById('requestAccessModal');
    const nameSpan = document.getElementById('targetPlatformName');
    const confirmBtn = document.getElementById('confirmRequestBtn');

    if (!modal || !nameSpan || !confirmBtn) return;

    nameSpan.textContent = platformName;
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    confirmBtn.onclick = async () => {
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Procesando...';
        
        try {
            const res = await fetch('/admin/requests/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                body: JSON.stringify({ platform_id: platformId })
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                // Actualizar botón en la UI
                const card = document.querySelector(`.platform-card[data-platform-id="${platformId}"]`);
                if (card) {
                    const actionZone = card.querySelector('.mt-auto');
                    actionZone.innerHTML = `
                        <div class="w-full h-12 bg-surface-container/80 text-primary border border-panel-border rounded-xl text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 shadow-inner opacity-80">
                            <span>En Revisión</span>
                            <div class="flex gap-1 ml-2">
                                <div class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"></div>
                                <div class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]"></div>
                                <div class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]"></div>
                            </div>
                        </div>
                    `;
                }
                closeModal('requestAccessModal');
            }
        } catch (e) {
            console.error(e);
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = 'Confirmar';
        }
    };
}

/**
 * Close Modal Helper
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}
