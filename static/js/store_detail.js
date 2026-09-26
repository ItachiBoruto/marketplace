(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        const container = document.querySelector('.container[data-store-id]');
        if (!container) return;
        const storeId = container.dataset.storeId;
        if (!storeId) return;

        // === ELEMENTOS DEL DOM ===
        const productGrid = document.getElementById('storeProductGrid');
        const loading = document.getElementById('storeLoading');
        const searchInput = document.getElementById('storeSearchInput');
        const searchBtn = document.getElementById('storeSearchBtn');
        const detailContainer = document.getElementById('product-detail-container');
        // Modal de pasillos
        const pasillosBtn = document.getElementById('storePasillosBtn');
        const pasillosClear = document.getElementById('storePasillosClear');
        const pasillosModal = document.getElementById('storePasillosModal');
        const pasillosClose = document.getElementById('storePasillosClose');
        const pasillosBody = document.getElementById('storePasillosBody');
        const pasillosSearch = document.getElementById('storePasillosSearch');
        const pasillosReset = document.getElementById('storePasillosReset');

        if (!productGrid || !loading) return;

        // === ESTADO ===
        let currentPage = 1;
        let isLoading = false;
        let hasMore = true;
        let currentSearch = '';
        let currentCategory = '';

        // === DETALLE DE PRODUCTO ===
        function showProductDetail(productId) {
            if (!productId) return;
            const url = '/product-detail/' + productId + '/';
            fetch(url)
                .then(function(r) {
                    if (!r.ok) throw new Error('Error ' + r.status);
                    return r.text();
                })
                .then(function(html) {
                    detailContainer.innerHTML = html;
                    detailContainer.style.display = 'block';
                    detailContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                })
                .catch(function(err) {
                    console.error('Error al cargar detalle:', err);
                    detailContainer.innerHTML = '<p>Error al cargar el detalle.</p>';
                    detailContainer.style.display = 'block';
                });
        }

        // === CARGAR PRODUCTOS ===
        async function loadStoreProducts(page, search, category) {
            if (page === undefined) page = 1;
            if (search === undefined) search = '';
            if (category === undefined) category = '';
            if (isLoading || !hasMore) return;

            isLoading = true;
            loading.style.display = 'block';
            loading.textContent = 'Cargando más productos...';

            try {
                let url = '/api/store-products/?store=' + storeId +
                          '&page=' + page +
                          '&search=' + encodeURIComponent(search) +
                          '&sort=name';
                if (category) {
                    url += '&category=' + encodeURIComponent(category);
                }

                const response = await fetch(url);
                if (!response.ok) throw new Error('Error ' + response.status);
                const data = await response.json();

                if (data.results.length === 0 && page === 1) {
                    productGrid.innerHTML = '<p style="text-align:center; padding:40px;">No hay productos en este pasillo.</p>';
                    hasMore = false;
                    loading.style.display = 'none';
                    return;
                }

                if (data.results.length === 0) {
                    hasMore = false;
                    loading.textContent = '✅ Todos los productos cargados';
                    loading.style.display = 'block';
                    return;
                }

                if (page === 1) productGrid.innerHTML = '';

                data.results.forEach(function(item) {
                    const card = document.createElement('div');
                    card.className = 'variant-card';
                    card.dataset.productId = item.id;
                    card.innerHTML =
                        '<div class="variant-image">' +
                            (item.image
                                ? '<img src="' + item.image + '" alt="' + item.name + '">'
                                : '<div class="no-image">Sin imagen</div>') +
                        '</div>' +
                        '<div class="variant-info">' +
                            '<h4>' + item.name + '</h4>' +
                            '<p class="price">$' + item.price + '</p>' +
                            '<p class="stock">Stock: ' + item.stock + '</p>' +
                        '</div>';
                    productGrid.appendChild(card);
                });

                currentPage = page;
                hasMore = data.next !== null;

                if (!hasMore) {
                    loading.textContent = '✅ Todos los productos cargados';
                } else {
                    loading.textContent = 'Cargando más productos...';
                }
                loading.style.display = 'block';
            } catch (error) {
                console.error('Error:', error);
                loading.textContent = 'Error al cargar. Intenta de nuevo.';
            } finally {
                isLoading = false;
            }
        }

        // === SCROLL INFINITO ===
        const observer = new IntersectionObserver(function(entries) {
            if (entries[0].isIntersecting && hasMore && !isLoading) {
                loadStoreProducts(currentPage + 1, currentSearch, currentCategory);
            }
        }, { threshold: 0.5 });
        observer.observe(loading);

        // === BUSQUEDA ===
        function performSearch() {
            productGrid.innerHTML = '';
            currentPage = 1;
            hasMore = true;
            currentSearch = searchInput.value.trim();
            loading.textContent = 'Cargando más productos...';
            loading.style.display = 'block';
            loadStoreProducts(1, currentSearch, currentCategory);
        }

        if (searchBtn) searchBtn.addEventListener('click', performSearch);
        if (searchInput) {
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') { e.preventDefault(); performSearch(); }
            });
        }

        // === CLICK EN TARJETA -> DETALLE ===
        if (productGrid) {
            productGrid.addEventListener('click', function(e) {
                const card = e.target.closest('.variant-card');
                if (card && card.dataset.productId) {
                    showProductDetail(card.dataset.productId);
                }
            });
        }

        // === MODAL DE PASILLOS ===
        function openPasillosModal() {
            if (!pasillosModal) return;
            pasillosModal.classList.add('open');
            pasillosModal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            if (pasillosSearch) {
                pasillosSearch.value = '';
                document.querySelectorAll('#storePasillosBody .cat-card').forEach(function(c) {
                    c.classList.remove('hidden');
                });
                setTimeout(function() { pasillosSearch.focus(); }, 200);
            }
            // Marcar la categoria actual
            document.querySelectorAll('#storePasillosBody .cat-card').forEach(function(c) {
                c.classList.toggle('selected', c.dataset.slug === currentCategory);
            });
        }

        function closePasillosModal() {
            if (!pasillosModal) return;
            pasillosModal.classList.remove('open');
            pasillosModal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }
            // Buscar la tarjeta de la categoria para leer sus datos

        function applyCategory(slug) {
            currentCategory = slug || '';
            productGrid.innerHTML = '';
            currentPage = 1;
            hasMore = true;
            loading.textContent = 'Cargando más productos...';
            loading.style.display = 'block';
            loadStoreProducts(1, currentSearch, currentCategory);

            // Actualizar boton de quitar filtro
            if (pasillosClear) {
                pasillosClear.style.display = currentCategory ? 'inline-flex' : 'none';
            }
            closePasillosModal();
        }

        if (pasillosBtn) pasillosBtn.addEventListener('click', openPasillosModal);
        if (pasillosClose) pasillosClose.addEventListener('click', closePasillosModal);
        if (pasillosModal) {
            pasillosModal.addEventListener('click', function(e) {
                if (e.target === pasillosModal) closePasillosModal();
            });
        }
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && pasillosModal && pasillosModal.classList.contains('open')) {
                closePasillosModal();
            }
        });
        if (pasillosBody) {
            pasillosBody.addEventListener('click', function(e) {
                const card = e.target.closest('.cat-card');
                if (!card) return;
                applyCategory(card.dataset.slug);
            });
        }
        if (pasillosReset) {
            pasillosReset.addEventListener('click', function() {
                applyCategory('');
            });
        }
        if (pasillosClear) {
            pasillosClear.addEventListener('click', function() {
                applyCategory('');
            });
        }
        if (pasillosSearch) {
            pasillosSearch.addEventListener('input', function() {
                const q = pasillosSearch.value.trim().toLowerCase();
                let visible = 0;
                document.querySelectorAll('#storePasillosBody .cat-card').forEach(function(c) {
                    const match = !q || (c.dataset.name || '').indexOf(q) !== -1;
                    c.classList.toggle('hidden', !match);
                    if (match) visible++;
                });
                const old = pasillosBody.querySelector('.cat-no-results');
                if (old) old.remove();
                if (visible === 0) {
                    const msg = document.createElement('div');
                    msg.className = 'cat-no-results';
                    msg.textContent = 'No hay pasillos con ese nombre';
                    pasillosBody.appendChild(msg);
                }
            });
        }

        // === CARGA INICIAL ===
        loadStoreProducts(1, '', '');
    });
})();
