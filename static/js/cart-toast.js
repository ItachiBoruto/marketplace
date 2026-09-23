/**
 * Cart toast + flying box + feedback visual al agregar productos.
 */
(function () {
    'use strict';

    function escapeHtml(str) {
        return String(str || '').replace(/[&<>"']/g, function (c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function getCartElement() {
        return document.querySelector('.header-cart-link') || document.querySelector('a[href="/cart/"]');
    }

    function flyBoxToCart(fromButton) {
        var cartEl = getCartElement();
        if (!cartEl || !fromButton) return;

        var btnRect = fromButton.getBoundingClientRect();
        var cartRect = cartEl.getBoundingClientRect();

        var box = document.createElement('div');
        box.className = 'flying-box';
        box.innerHTML = '\ud83d\udce6';
        box.style.left = (btnRect.left + btnRect.width / 2 - 20) + 'px';
        box.style.top = (btnRect.top + btnRect.height / 2 - 20) + 'px';
        document.body.appendChild(box);

        var dx = (cartRect.left + cartRect.width / 2) - (btnRect.left + btnRect.width / 2);
        var dy = (cartRect.top + cartRect.height / 2) - (btnRect.top + btnRect.height / 2);

        requestAnimationFrame(function () {
            box.classList.add('flying-box-animate');
            box.style.transform = 'translate(' + dx + 'px, ' + dy + 'px) scale(0.4) rotate(360deg)';
            box.style.opacity = '0.3';
        });

        setTimeout(function () {
            box.remove();
            var cartElNow = getCartElement();
            if (cartElNow) {
                cartElNow.classList.add('cart-shake');
                setTimeout(function () { cartElNow.classList.remove('cart-shake'); }, 700);
            }
        }, 750);
    }

    function showCartToast(productName, cartCount, isError) {
        var overlay = document.getElementById('cart-success-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'cart-success-overlay';
            overlay.className = 'cart-success-overlay';
            document.body.appendChild(overlay);
        }

        if (isError) {
            overlay.style.background = 'linear-gradient(135deg, #e74c3c, #c0392b)';
            overlay.style.boxShadow = '0 8px 24px rgba(231, 76, 60, 0.4)';
            overlay.innerHTML =
                '<div class="check-icon">\u26a0\ufe0f</div>' +
                '<div class="success-text">' +
                    '<strong>No se pudo agregar</strong>' +
                    '<small>' + escapeHtml(productName) + '</small>' +
                '</div>';
        } else {
            overlay.style.background = 'linear-gradient(135deg, #2ecc71, #27ae60)';
            overlay.style.boxShadow = '0 8px 24px rgba(46, 204, 113, 0.35)';
            overlay.innerHTML =
                '<div class="check-icon">\u2713</div>' +
                '<div class="success-text">' +
                    '<strong>\u00a1Agregado!</strong>' +
                    '<small>' + escapeHtml(productName) + '</small>' +
                '</div>' +
                '<a href="/cart/" class="success-link">Ver \u2192</a>';
        }

        overlay.classList.add('show');
        setTimeout(function() { overlay.classList.remove('show'); }, 2400);
    }

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
        var productName = btn.dataset.productName || 'Producto';
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
            if (r.redirected && r.url.indexOf('/accounts/login') !== -1) {
                window.location.href = r.url;
                return null;
            }
            var contentType = r.headers.get('content-type') || '';
            if (contentType.indexOf('application/json') === -1) {
                window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                return null;
            }
            return r.json().then(function (d) { return { ok: r.ok, data: d }; });
        })
        .then(function (res) {
            if (res === null) return;
            var data = res.data;
            if (data.success) {
                btn.textContent = '\u2705 Agregado';
                btn.classList.add('btn-added-success');

                // Volamos la caja al carrito
                flyBoxToCart(btn);

                // Mostramos el overlay + actualizamos badge
                setTimeout(function () {
                    showCartToast(data.product_name || productName, data.cart_count, false);
                    updateBadge(data.cart_count);
                }, 700);

                setTimeout(function() {
                    btn.classList.remove('btn-added-success');
                }, 700);
            } else {
                btn.textContent = '\u26a0 No disponible';
                showCartToast(data.message || 'No disponible', 0, true);
            }
        })
        .catch(function () {
            btn.textContent = '\u26a0 Error';
            showCartToast('Error de conexion', 0, true);
        })
        .then(function () {
            setTimeout(function () {
                btn.textContent = originalText;
                btn.disabled = originalDisabled;
            }, 1800);
        });
    });
})();
