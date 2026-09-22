/**
 * Agrega productos al carrito via AJAX y actualiza el badge del header.
 */
(function () {
    'use strict';

    function updateBadge(count) {
        var badges = document.querySelectorAll('.cart-count-badge');
        if (badges.length === 0) return;
        badges.forEach(function (b) {
            b.textContent = count;
            if (count > 0) {
                b.style.display = 'inline-block';
                b.classList.add('bump');
                setTimeout(function () { b.classList.remove('bump'); }, 500);
            } else {
                b.style.display = 'none';
            }
        });
    }

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-add-cart]');
        if (!btn || btn.disabled) return;

        e.preventDefault();

        var productId = btn.dataset.productId;
        var originalText = btn.textContent;
        var originalDisabled = btn.disabled;

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
        .then(function (r) {
            // Si el servidor redirige a login (no autenticado)
            if (r.redirected && r.url.indexOf('/accounts/login') !== -1) {
                window.location.href = r.url;
                return null;
            }
            // Si no es JSON, probablemente es un redirect
            var contentType = r.headers.get('content-type') || '';
            if (contentType.indexOf('application/json') === -1) {
                window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                return null;
            }
            return r.json().then(function (d) { return { ok: r.ok, data: d }; });
        })
        .then(function (res) {
            if (res === null) return;  // Fue redirigido a login
            var data = res.data;
            if (data.success) {
                btn.textContent = '\u2705 Agregado';
                updateBadge(data.cart_count);
            } else {
                btn.textContent = '\u26a0 ' + (data.message || 'No disponible');
            }
        })
        .catch(function () {
            btn.textContent = '\u26a0 Error';
        })
        .then(function () {
            setTimeout(function () {
                btn.textContent = originalText;
                btn.disabled = originalDisabled;
            }, 1600);
        });
    });
})();
