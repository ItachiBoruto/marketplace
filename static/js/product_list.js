/**
 * product_list.js - Logica del listado de productos
 * Extraido de apps/products/templates/products/list.html
 * Fecha: 2026-09-24 10:16
 *
 * Incluye:
 * - Scroll infinito de productos
 * - Busqueda y filtros
 * - Modal de categorias
 */

(function () {
    'use strict';

// ===== CONFIGURACIÓN =====
        const productGrid = document.getElementById('productGrid');
        const loading = document.getElementById('loading');
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        const storeFilter = document.getElementById('storeFilter');
        const categoryFilter = document.getElementById('categoryFilter');

        // ===== TOGGLES MÓVIL =====
        const menuToggle = document.getElementById('menuToggle');
        const headerNav = document.getElementById('headerNav');
        const filtersToggle = document.getElementById('filtersToggle');
        const headerFilters = document.getElementById('headerFilters');

        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                headerNav.classList.toggle('open');
                menuToggle.textContent = headerNav.classList.contains('open') ? '✕' : '☰';
            });
        }

        if (filtersToggle) {
            filtersToggle.addEventListener('click', () => {
                headerFilters.classList.toggle('open');
            });
        }

        let currentPage = 1;
        let isLoading = false;
        let hasMore = true;
        let currentSearch = '';
        let currentStore = '';
        let currentCategory = '';
        let currentSort = 'name';

        function escapeHtml(str) {
            return String(str || '').replace(/[&<>"']/g, c => (
                {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
            ));
        }

        async function loadProducts(page = 1, search = '', store = '', category = '', sort = 'name') {
            if (isLoading || !hasMore) return;
            isLoading = true;
            loading.style.display = 'block';

            try {
                const url = `/api/products/?page=${page}&search=${encodeURIComponent(search)}&store=${store}&category=${encodeURIComponent(category)}&sort=${sort}`;
                const response = await fetch(url);
                const data = await response.json();

                if (data.results.length === 0 && page === 1) {
                    productGrid.innerHTML = '<p style="text-align:center; padding:40px;">No hay productos disponibles.</p>';
                    hasMore = false;
                    loading.style.display = 'none';
                    return;
                }

                if (page === 1) productGrid.innerHTML = '';

                data.results.forEach(product => {
                    const stock = parseInt(product.stock) || 0;
                    const outOfStock = stock <= 0;
                    const lowStock = stock > 0 && stock <= 5;

                    const card = document.createElement('div');
                    card.className = 'product-card';
                    if (outOfStock) card.classList.add('out-of-stock');
                    if (lowStock) card.classList.add('low-stock');
                    card.dataset.store = product.store_id;

                    // Solo navega si hay stock
                    if (!outOfStock) {
                        card.onclick = () => { window.location.href = `/product/${product.id}/`; };
                    }

                    const imgHtml = product.image
                        ? `<img src="${escapeHtml(product.image)}" alt="${escapeHtml(product.name)}" loading="lazy">`
                        : '<div class="no-image">Sin imagen</div>';

                    const badge = outOfStock
                        ? '<span class="stock-badge badge-out">AGOTADO</span>'
                        : (lowStock ? `<span class="stock-badge badge-low">¡Quedan ${stock}!</span>` : '');

                    const stockClass = outOfStock ? 'stock-zero' : (lowStock ? 'stock-low' : '');
                    const stockLabel = outOfStock ? 'Sin stock' : `Stock: ${stock}`;

                    card.innerHTML = `
                        <div class="product-image">
                            ${imgHtml}
                            ${badge}
                        </div>
                        <div class="product-info">
                            <h3 class="product-name">${escapeHtml(product.name)}</h3>
                            <p class="store-name">${escapeHtml(product.store_name || 'Sin comercio')}</p>
                            <p class="price">$${escapeHtml(product.price)}</p>
                            <p class="stock-counter ${stockClass}">📦 <span>${escapeHtml(stockLabel)}</span></p>
                        </div>
                    `;
                    productGrid.appendChild(card);
                });

                currentPage = page;
                hasMore = data.next !== null;

                if (!hasMore) {
                    loading.textContent = '✅ Todos los productos cargados';
                    loading.style.display = 'block';
                } else {
                    loading.textContent = 'Cargando más productos...';
                    loading.style.display = 'block';
                }
            } catch (error) {
                console.error('Error:', error);
                loading.textContent = 'Error al cargar. Intenta de nuevo.';
            } finally {
                isLoading = false;
            }
        }

        // ===== SCROLL INFINITO =====
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && hasMore && !isLoading) {
                loadProducts(currentPage + 1, currentSearch, currentStore, currentCategory, currentSort);
            }
        }, { threshold: 0.5 });
        observer.observe(loading);

        // ===== BÚSQUEDA Y FILTROS =====
        function performSearch() {
            productGrid.innerHTML = '';
            currentPage = 1;
            hasMore = true;
            currentSearch = searchInput.value.trim();
            currentStore = storeFilter.value;
            currentCategory = categoryFilter.value;
            currentSort = 'name'; // Orden fijo: alfabetico
            loading.textContent = 'Cargando más productos...';
            loading.style.display = 'block';
            loadProducts(1, currentSearch, currentStore, currentCategory, currentSort);
        }

        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') performSearch(); });
        storeFilter.addEventListener('change', performSearch);
        categoryFilter.addEventListener('change', performSearch);

        loadProducts(1, '', '', '', 'name');

        /* ============================================================
           CAT-MODAL-JS - Modal de categorias
           ============================================================ */
        (function () {
            var openBtn = document.getElementById('categoryOpenBtn');
            var btnLabel = document.getElementById('categoryBtnLabel');
            var overlay = document.getElementById('catModalOverlay');
            var closeBtn = document.getElementById('catModalClose');
            var clearBtn = document.getElementById('catClearBtn');
            var searchInp = document.getElementById('catSearchInput');
            var body = document.getElementById('catModalBody');
            var sel = document.getElementById('categoryFilter');
            if (!openBtn || !overlay || !sel) return;

            function syncLabel() {
                var val = sel.value;
                if (!val) {
                    btnLabel.textContent = 'Categorías';
                    openBtn.classList.remove('has-filter');
                    return;
                }
                var opt = sel.querySelector('option[value="' + val + '"]');
                if (opt) {
                    btnLabel.textContent = opt.textContent.trim();
                    openBtn.classList.add('has-filter');
                }
            }

            function markSelected(slug) {
                document.querySelectorAll('.cat-card').forEach(function (c) {
                    c.classList.toggle('selected', c.dataset.slug === slug);
                });
            }

            function openModal() {
                overlay.classList.add('open');
                overlay.setAttribute('aria-hidden', 'false');
                document.body.style.overflow = 'hidden';
                markSelected(sel.value);
                if (searchInp) {
                    searchInp.value = '';
                    document.querySelectorAll('.cat-card').forEach(function (c) {
                        c.classList.remove('hidden');
                    });
                }
                setTimeout(function () { if (searchInp) searchInp.focus(); }, 200);
            }

            function closeModal() {
                overlay.classList.remove('open');
                overlay.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }

            function applyCategory(slug) {
                sel.value = slug;
                sel.dispatchEvent(new Event('change', { bubbles: true }));
                syncLabel();
                closeModal();
            }

            // Abrir
            openBtn.addEventListener('click', function (e) {
                e.preventDefault();
                openModal();
            });

            // Cerrar: X, overlay, ESC
            closeBtn.addEventListener('click', closeModal);
            overlay.addEventListener('click', function (e) {
                if (e.target === overlay) closeModal();
            });
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && overlay.classList.contains('open')) closeModal();
            });

            // Click en tarjeta
            body.addEventListener('click', function (e) {
                var card = e.target.closest('.cat-card');
                if (!card) return;
                applyCategory(card.dataset.slug);
            });

            // Limpiar filtro
            clearBtn.addEventListener('click', function () {
                applyCategory('');
            });

            // Busqueda dentro del modal
            if (searchInp) {
                searchInp.addEventListener('input', function () {
                    var q = searchInp.value.trim().toLowerCase();
                    var visible = 0;
                    document.querySelectorAll('.cat-card').forEach(function (c) {
                        var match = !q || (c.dataset.name || '').indexOf(q) !== -1;
                        c.classList.toggle('hidden', !match);
                        if (match) visible++;
                    });
                    var old = body.querySelector('.cat-no-results');
                    if (old) old.remove();
                    if (visible === 0) {
                        var msg = document.createElement('div');
                        msg.className = 'cat-no-results';
                        msg.textContent = 'No se encontraron categorias';
                        body.appendChild(msg);
                    }
                });
            }

            // Sincronizar el label al cargar (por si el select ya tiene valor)
            syncLabel();
        })();
})();
