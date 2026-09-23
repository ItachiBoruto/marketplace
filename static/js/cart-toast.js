/**
 * Cart toast + flying box + feedback visual al agregar productos.
 * v2 - Optimizado para mobile (fallback a esquina sup. derecha)
 */
(function () {
    'use strict';

    var IS_MOBILE = window.matchMedia('(max-width: 768px)').matches;
    var FLY_DURATION = IS_MOBILE ? 550 : 700; // ms
    var DEBUG = false; // poner true para ver logs en consola

    function escapeHtml(str) {
        return String(str || '').replace(/[&<>"']/g, function (c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function isElementVisible(el) {
        if (!el) return false;
        var rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return false;
        var style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') return false;
        if (parseFloat(style.opacity) === 0) return false;
        return true;
    }

    function getCartElement() {
        var selectors = [
            '.header-cart-link',
            '.cart-count-badge',
            'a[href="/cart/"]',
            'a[href$="/cart/"]',
            'a[href*="/cart"]'
        ];
        for (var i = 0; i < selectors.length; i++) {
            var nodes = document.querySelectorAll(selectors[i]);
            for (var j = 0; j < nodes.length; j++) {
                if (isElementVisible(nodes[j])) return nodes[j];
            }
        }
        return null;
    }

    function getCartTarget() {
        var el = getCartElement();
        if (el) {
            var r = el.getBoundingClientRect();
            return { x: r.left + r.width / 2, y: r.top + r.height / 2, element: el, source: 'visible-cart' };
        }
        // Fallback: esquina superior derecha (donde suele estar el carrito en mobile)
        return { x: window.innerWidth - 30, y: 30, element: null, source: 'fallback-corner' };
    }

    function flyBoxToCart(fromButton) {
        if (!fromButton) return;
        var btnRect = fromButton.getBoundingClientRect();
        if (btnRect.width === 0 || btnRect.height === 0) return;

        var target = getCartTarget();
        if (DEBUG) console.log('[cart-toast] target:', target.source, target);

        var startX = btnRect.left + btnRect.width / 2;
        var startY = btnRect.top + btnRect.height / 2;
        var dx = target.x - startX;
        var dy = target.y - startY;

        var box = document.createElement('div');
        box.className = 'flying-box';
        box.textContent = '\ud83d\udce6';
        box.style.left = (startX - 22) + 'px';
        box.style.top = (startY - 22) + 'px';
        document.body.appendChild(box);

        var sec = FLY_DURATION / 1000;
        box.style.transition =
            'transform ' + sec + 's cubic-bezier(0.45, 0.05, 0.55, 0.95), ' +
            'opacity ' + sec + 's ease-in';

        // Doble rAF: garantiza que el navegador registre el estado inicial
        // antes de aplicar la transform (clave en mobile).
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                box.style.transform = 'translate(' + dx + 'px, ' + dy + 'px) scale(0.3) rotate(360deg)';
                box.style.opacity = '0.4';
            });
        });

        setTimeout(function () {
            box.remove();
            if (target.element) {
                target.element.classList.add('cart-shake');
                setTimeout(function () {
                    if (target.element) target.element.classList.remove('cart-shake');
                }, 700);
            }
        }, FLY_DURATION + 60);
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
        setTimeout(function () { overlay.classList.remove('show'); }, 2400);
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

                flyBoxToCart(btn);

                // Actualizamos el badge apenas termina la animacion de la caja
                setTimeout(function () {
                    updateBadge(data.cart_count);
                }, FLY_DURATION);

                setTimeout(function () {
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
