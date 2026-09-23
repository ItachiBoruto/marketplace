/**
 * Modal de categorias reutilizable.
 * Autodetecta #categoryOpenBtn / #catModalOverlay / #categoryFilter.
 * Al seleccionar una tarjeta, actualiza el <select> oculto y dispara
 * un evento 'change' con bubbles=true (para que el listado lo escuche).
 */
(function () {
    'use strict';

    function initCategoryModal() {
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
                var emptyTxt = sel.options[0] ? sel.options[0].textContent.trim() : '📂 Categorías';
                btnLabel.textContent = emptyTxt;
                openBtn.classList.remove('has-filter');
                return;
            }
            var opt = sel.options[sel.selectedIndex];
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
            // Buscar el slug de la opcion actual
            var currentSlug = '';
            if (sel.selectedIndex >= 0) {
                var opt = sel.options[sel.selectedIndex];
                currentSlug = opt.dataset.slug || '';
            }
            markSelected(currentSlug);
            if (searchInp) {
                searchInp.value = '';
                document.querySelectorAll('.cat-card').forEach(function (c) {
                    c.classList.remove('hidden');
                });
                var old = body.querySelector('.cat-no-results');
                if (old) old.remove();
            }
            setTimeout(function () { if (searchInp) searchInp.focus(); }, 200);
        }

        function closeModal() {
            overlay.classList.remove('open');
            overlay.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }

        function applyCategoryFromCard(card) {
            var slug = card.dataset.slug || '';
            var idVal = card.dataset.id || '';
            // Buscar la opcion que corresponda (por slug)
            var chosen = null;
            for (var i = 0; i < sel.options.length; i++) {
                if (slug === '') {
                    if (sel.options[i].value === '') { chosen = sel.options[i]; break; }
                } else if (sel.options[i].dataset.slug === slug) {
                    chosen = sel.options[i];
                    break;
                }
            }
            if (chosen) sel.value = chosen.value;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            syncLabel();
            closeModal();
        }

        openBtn.addEventListener('click', function (e) {
            e.preventDefault();
            openModal();
        });
        closeBtn.addEventListener('click', closeModal);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeModal();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && overlay.classList.contains('open')) closeModal();
        });

        body.addEventListener('click', function (e) {
            var card = e.target.closest('.cat-card');
            if (!card) return;
            applyCategoryFromCard(card);
        });

        clearBtn.addEventListener('click', function () {
            sel.value = '';
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            syncLabel();
            closeModal();
        });

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

        syncLabel();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCategoryModal);
    } else {
        initCategoryModal();
    }
})();
