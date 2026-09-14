/**
 * Sistema de toast para "Agregado al carrito"
 * Usa event delegation: funciona con botones cargados por AJAX.
 */
(function () {
    'use strict';

    function ensureContainer() {
        var container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    function escapeHtml(str) {
        return String(str || '').replace(/[&<>"']/g, function (c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function showCartToast(productName, cartCount, isError) {
        var container = ensureContainer();
        var toast = document.createElement('div');
        toast.className = 'cart-toast' + (isError ? ' toast-error' : '');

        var safeName = escapeHtml(productName);
        var icon = isError ? '&#9888;&#65039;' : '&#128722;';
        var title = isError ? 'No disponible' : '&iexcl;Agregado al carrito!';
        var actions = isError ? '' : (
            '<div class="cart-toast-actions">' +
                '<a href="/cart/" class="cart-toast-link">Ver carrito (' +
                cartCount + ') &rarr;</a>' +
            '</div>'
        );

        toast.innerHTML =
            '<div class="cart-toast-icon">' + icon + '</div>' +
            '<div class="cart-toast-content">' +
                '<p class="cart-toast-title">' + title + '</p>' +
                '<p class="cart-toast-msg">' + safeName + '</p>' +
                actions +
            '</div>' +
            '<button class="cart-toast-close" aria-label="Cerrar">&#10005;</button>';

        container.appendChild(toast);

        requestAnimationFrame(function () {
            setTimeout(function () { toast.classList.add('show'); }, 20);
        });

        function close() {
            toast.classList.remove('show');
            setTimeout(function () {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 400);
        }
        toast.querySelector('.cart-toast-close').addEventListener('click', close);
        setTimeout(close, 4200);
    }

    window.showCartToast = showCartToast;

    // Event delegation: funciona incluso con botones que aparecen por AJAX
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-add-cart]');
        if (!btn) return;
        if (btn.disabled) return;

        e.preventDefault();

        var productId = btn.dataset.productId;
        var originalText = btn.textContent;

        btn.disabled = true;
        btn.textContent = 'Agregando...';

        fetch('/cart/add/' + productId + '/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            credentials: 'same-origin',
        })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
            var data = res.data;
            if (data.success) {
                showCartToast(data.product_name, data.cart_count, false);
                btn.textContent = 'Agregado';
                document.querySelectorAll('.cart-count-badge').forEach(function (b) {
                    b.textContent = data.cart_count;
                    b.classList.add('bump');
                    setTimeout(function () { b.classList.remove('bump'); }, 500);
                });
            } else {
                showCartToast(data.message || 'No disponible', 0, true);
                btn.textContent = originalText;
            }
        })
        .catch(function () {
            showCartToast('Error de conexion', 0, true);
            btn.textContent = originalText;
        })
        .then(function () {
            setTimeout(function () {
                btn.textContent = originalText;
                btn.disabled = false;
            }, 1500);
        });
    });
})();
