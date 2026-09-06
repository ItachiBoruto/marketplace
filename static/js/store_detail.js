(function() {
    'use strict';

    // Esperar a que el DOM esté completamente cargado
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOMContentLoaded: iniciando store_detail.js');

        // === OBTENER STORE_ID ===
        const container = document.querySelector('.container[data-store-id]');
        if (!container) {
            console.error('No se encontró .container con data-store-id');
            return;
        }
        const storeId = container.dataset.storeId;
        if (!storeId) {
            console.error('data-store-id está vacío');
            return;
        }
        console.log('Store ID obtenido:', storeId);

        // === ELEMENTOS DEL DOM ===
        const productGrid = document.getElementById('storeProductGrid');
        const loading = document.getElementById('storeLoading');
        const searchInput = document.getElementById('storeSearchInput');
        const searchBtn = document.getElementById('storeSearchBtn');
        const sortFilter = document.getElementById('sortFilter');
        const detailContainer = document.getElementById('product-detail-container');

        // Verificar que todos los elementos existan
        const elements = { productGrid, loading, searchInput, searchBtn, sortFilter, detailContainer };
        let missing = false;
        for (const [key, el] of Object.entries(elements)) {
            if (!el) {
                console.error(`Elemento '${key}' no encontrado en el DOM.`);
                missing = true;
            }
        }
        if (missing) {
            console.error('Faltan elementos en el DOM. Verifica los IDs.');
            return;
        }
        console.log('Todos los elementos del DOM encontrados.');

        // === CONFIGURACIÓN ===
        let currentPage = 1;
        let isLoading = false;
        let hasMore = true;
        let currentSearch = '';
        let currentSort = 'name';

        // === FUNCIÓN PARA MOSTRAR DETALLE ===
        function showProductDetail(productId) {
            if (!productId) {
                console.error('Product ID no válido');
                return;
            }
            const url = '/stores/product-detail/' + productId + '/';
            console.log('Cargando detalle del producto:', productId);
            fetch(url)
                .then(function(response) {
                    if (!response.ok) {
                        throw new Error('Error al cargar el detalle: ' + response.status);
                    }
                    return response.text();
                })
                .then(function(html) {
                    detailContainer.innerHTML = html;
                    detailContainer.style.display = 'block';
                    detailContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    console.log('Detalle cargado correctamente para producto', productId);
                })
                .catch(function(error) {
                    console.error('Error al cargar detalle:', error);
                    detailContainer.innerHTML = '<p>Error al cargar el detalle del producto.</p>';
                    detailContainer.style.display = 'block';
                });
        }

        // === FUNCIÓN PARA CARGAR PRODUCTOS (SCROLL INFINITO) ===
        async function loadStoreProducts(page, search, sort) {
            if (page === undefined) page = 1;
            if (search === undefined) search = '';
            if (sort === undefined) sort = 'name';
            if (isLoading || !hasMore) return;

            console.log(`Cargando página ${page} con búsqueda "${search}" y orden "${sort}"`);
            isLoading = true;
            loading.style.display = 'block';
            loading.textContent = 'Cargando más productos...';

            try {
                const url = '/api/store-products/?store=' + storeId + '&page=' + page + '&search=' + encodeURIComponent(search) + '&sort=' + sort;
                console.log('URL de la API:', url);

                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor: ' + response.status);
                }
                const data = await response.json();
                console.log('Datos recibidos:', data);

                if (data.results.length === 0 && page === 1) {
                    productGrid.innerHTML = '<p style="text-align:center; padding:40px;">No hay productos en este comercio.</p>';
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

                // Limpiar el grid si es la primera página
                if (page === 1) {
                    productGrid.innerHTML = '';
                }

                // Renderizar productos
                data.results.forEach(function(item) {
                    const card = document.createElement('div');
                    card.className = 'variant-card';
                    card.dataset.productId = item.id;
                    card.innerHTML = `
                        <div class="variant-image">
                            ${item.image ? `<img src="${item.image}" alt="${item.name}">` : '<div class="no-image">Sin imagen</div>'}
                        </div>
                        <div class="variant-info">
                            <h4>${item.name}</h4>
                            <p class="price">$${item.price}</p>
                            <p class="stock">Stock: ${item.stock}</p>
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
                console.error('Error en loadStoreProducts:', error);
                loading.textContent = 'Error al cargar. Intenta de nuevo.';
            } finally {
                isLoading = false;
            }
        }

        // === OBSERVER PARA SCROLL INFINITO ===
        const observer = new IntersectionObserver(function(entries) {
            if (entries[0].isIntersecting && hasMore && !isLoading) {
                const nextPage = currentPage + 1;
                loadStoreProducts(nextPage, currentSearch, currentSort);
            }
        }, { threshold: 0.5 });

        if (loading) {
            observer.observe(loading);
        }

        // === FUNCIÓN PARA BÚSQUEDA Y ORDEN ===
        function performSearch() {
            console.log('Ejecutando búsqueda/filtro...');
            productGrid.innerHTML = '';
            currentPage = 1;
            hasMore = true;
            currentSearch = searchInput.value.trim();
            currentSort = sortFilter.value;
            console.log('Nuevos parámetros - Búsqueda:', currentSearch, 'Orden:', currentSort);
            loading.textContent = 'Cargando más productos...';
            loading.style.display = 'block';
            loadStoreProducts(1, currentSearch, currentSort);
        }

        // === EVENT LISTENERS ===
        if (searchBtn) {
            searchBtn.addEventListener('click', performSearch);
            console.log('Event listener añadido al botón de búsqueda');
        }
        if (searchInput) {
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    performSearch();
                }
            });
            console.log('Event listener añadido al input de búsqueda (Enter)');
        }
        if (sortFilter) {
            sortFilter.addEventListener('change', performSearch);
            console.log('Event listener añadido al filtro de orden');
        }

        // === DELEGACIÓN DE EVENTOS PARA CLIC EN TARJETAS ===
        if (productGrid) {
            productGrid.addEventListener('click', function(e) {
                const card = e.target.closest('.variant-card');
                if (card) {
                    const productId = card.dataset.productId;
                    if (productId) {
                        showProductDetail(productId);
                    } else {
                        console.warn('La tarjeta no tiene data-product-id');
                    }
                }
            });
            console.log('Event listener de clic añadido al grid de productos');
        }

        // === CARGA INICIAL ===
        loadStoreProducts(1, '', 'name');
        console.log('Carga inicial completada');

    }); // Fin DOMContentLoaded

    console.log('Script store_detail.js cargado y ejecutado');
})();