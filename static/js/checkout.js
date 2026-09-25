/**
 * checkout.js - Logica del checkout
 * Extraido de apps/orders/templates/orders/checkout.html
 *
 * Los datos que vienen del servidor se leen desde elementos
 * <script type="application/json"> con id "data-*".
 */
(function() {
    'use strict';

    // ============================================================
    // DATOS DEL SERVIDOR
    // ============================================================
    function readJson(id, fallback) {
        var el = document.getElementById(id);
        if (!el) return fallback;
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            console.error('Error parseando #' + id, e);
            return fallback;
        }
    }

    var SUBTOTAL_USD = parseFloat(readJson('data-subtotal', 0)) || 0;
    var SHIPPING_FEE = parseFloat(readJson('data-shipping', 0)) || 0;
    var BCV_RATE_RAW = readJson('data-rate', '');
    var BCV_RATE = BCV_RATE_RAW ? parseFloat(BCV_RATE_RAW) : null;
    var DELIVERY_AVAILABLE = readJson('data-delivery-available', false);
    var BANK_TRANSFER = readJson('data-bank-transfer', {});
    var BANK_MOBILE = readJson('data-bank-mobile', {});

    // ============================================================
    // UTILIDADES DE FORMATEO
    // ============================================================
    function formatUsd(v) { return '$' + v.toFixed(2); }
    function formatBs(v) {
        return 'Bs. ' + v.toLocaleString('es-VE', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    // ============================================================
    // TOTALES DINAMICOS (retiro vs delivery)
    // ============================================================
    function updateTotals() {
        var checked = document.querySelector('input[name="shipping_method"]:checked');
        var method = checked ? checked.value : 'pickup';
        var isDelivery = method === 'delivery' && DELIVERY_AVAILABLE;
        var fee = isDelivery ? SHIPPING_FEE : 0;
        var totalUsd = SUBTOTAL_USD + fee;

        var shippingLine = document.getElementById('shippingLine');
        if (shippingLine) shippingLine.style.display = isDelivery ? 'flex' : 'none';

        var shippingFee = document.getElementById('shippingFee');
        if (shippingFee) shippingFee.textContent = formatUsd(fee);

        var totalUsdEl = document.getElementById('totalUsd');
        if (totalUsdEl) totalUsdEl.textContent = formatUsd(totalUsd);

        if (BCV_RATE) {
            var totalBsEl = document.getElementById('totalBs');
            if (totalBsEl) totalBsEl.textContent = formatBs(totalUsd * BCV_RATE);
        }

        var addrBlock = document.getElementById('deliveryAddressBlock');
        if (addrBlock) addrBlock.classList.toggle('show', isDelivery);
    }

    document.querySelectorAll('input[name="shipping_method"]').forEach(function(r) {
        r.addEventListener('change', updateTotals);
    });
    updateTotals();

    // ============================================================
    // COPIAR AL PORTAPAPELES
    // ============================================================
    function fallbackCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(ta);
    }

    function copyToClipboard(text, btn) {
        var done = function() {
            if (btn) {
                var orig = btn.textContent;
                btn.textContent = 'OK';
                setTimeout(function() { btn.textContent = orig; }, 1500);
            }
        };
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(done).catch(function() {
                fallbackCopy(text);
                done();
            });
        } else {
            fallbackCopy(text);
            done();
        }
    }

    // Exponer al scope global (los onclick="" en el HTML lo necesitan)
    window.copyToClipboard = copyToClipboard;

    // ============================================================
    // COPIAR DATOS DE TRANSFERENCIA / PAGO MOVIL
    // ============================================================
    window.copyAllTransferData = function() {
        var data = [
            'Banco: ' + (BANK_TRANSFER.bank_name || ''),
            'Titular: ' + (BANK_TRANSFER.account_holder || ''),
            'Cedula/RIF: ' + (BANK_TRANSFER.document || ''),
            'Cuenta: ' + (BANK_TRANSFER.account_number || '')
        ].join('\n');
        copyToClipboard(data, null);
        alert('Datos de transferencia copiados');
    };

    window.copyAllMobileData = function() {
        var data = [
            'Banco receptor: ' + (BANK_MOBILE.bank_name || ''),
            'Telefono: ' + (BANK_MOBILE.phone || ''),
            'Cedula/RIF: ' + (BANK_MOBILE.document || '')
        ].join('\n');
        copyToClipboard(data, null);
        alert('Datos de pago movil copiados');
    };

    // ============================================================
    // TOGGLE DE METODOS DE PAGO (transferencia / pago movil)
    // ============================================================
    (function() {
        var btns = document.querySelectorAll('.pm-btn');
        var panels = document.querySelectorAll('.pm-panel');
        var hiddenInput = document.getElementById('paymentMethodInput');

        function selectMethod(method) {
            btns.forEach(function(b) {
                b.classList.toggle('selected', b.dataset.method === method);
            });
            panels.forEach(function(p) {
                p.classList.toggle('show', p.dataset.method === method);
            });
            if (hiddenInput) hiddenInput.value = method;
        }

        btns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                selectMethod(btn.dataset.method);
            });
        });

        if (hiddenInput && hiddenInput.value) {
            selectMethod(hiddenInput.value);
        }
    })();



    // ============================================================
    // MEJORAS DE UX - Estado de carga, validacion en vivo
    // ============================================================

    // 1) Estado "Procesando" al enviar el form
    (function() {
        var form = document.getElementById('checkoutForm');
        var btn = document.getElementById('btnConfirmOrder');
        if (!form || !btn) return;

        form.addEventListener('submit', function() {
            var textEl = btn.querySelector('.btn-text');
            var loadingEl = btn.querySelector('.btn-loading');
            if (textEl) textEl.style.display = 'none';
            if (loadingEl) loadingEl.style.display = 'inline-flex';
            btn.disabled = true;
        });
    })();

    // 2) Validacion en vivo del campo de referencia
    (function() {
        // El input de referencia tiene name="payment_reference"
        var refInput = document.querySelector('input[name="payment_reference"]');
        if (!refInput) return;

        function validate() {
            var val = refInput.value.trim();
            if (val.length === 0) {
                refInput.classList.remove('input-valid', 'input-invalid');
                return;
            }
            if (val.length >= 4) {
                refInput.classList.add('input-valid');
                refInput.classList.remove('input-invalid');
            } else {
                refInput.classList.add('input-invalid');
                refInput.classList.remove('input-valid');
            }
        }

        refInput.addEventListener('input', validate);
        validate();
    })();

    // 3) Feedback mejorado del boton copiar
    (function() {
        // Sobrescribimos copyToClipboard para mejor feedback
        var originalCopy = window.copyToClipboard;
        window.copyToClipboard = function(text, btn) {
            if (originalCopy) {
                originalCopy(text, btn);
            }
            // Vibracion en mobile (si esta disponible)
            if (navigator.vibrate) {
                navigator.vibrate(30);
            }
        };
    })();

    // 4) Descarga de QR (agregar boton si hay QR visible)
    (function() {
        var qrImages = document.querySelectorAll('.qr-image');
        qrImages.forEach(function(qr) {
            var container = qr.parentNode;
            if (!container || container.querySelector('.qr-actions')) return;

            var actions = document.createElement('div');
            actions.className = 'qr-actions';
            actions.innerHTML =
                '<button type="button" class="qr-action-btn" data-qr-download>⬇️ Descargar</button>' +
                '<button type="button" class="qr-action-btn" data-qr-share>📤 Compartir</button>';

            // Insertar despues del QR
            qr.parentNode.insertBefore(actions, qr.nextSibling);

            // Handlers
            var dlBtn = actions.querySelector('[data-qr-download]');
            if (dlBtn) {
                dlBtn.addEventListener('click', function() {
                    var link = document.createElement('a');
                    link.href = qr.src;
                    link.download = 'qr-pago.png';
                    link.click();
                });
            }

            var shBtn = actions.querySelector('[data-qr-share]');
            if (shBtn) {
                if (!navigator.share) {
                    shBtn.style.display = 'none';
                } else {
                    shBtn.addEventListener('click', function() {
                        fetch(qr.src)
                            .then(function(r) { return r.blob(); })
                            .then(function(blob) {
                                var file = new File([blob], 'qr-pago.png', { type: 'image/png' });
                                return navigator.share({
                                    files: [file],
                                    title: 'QR de pago',
                                });
                            })
                            .catch(function() {});
                    });
                }
            }
        });
    })();

    // 5) Animacion al cambiar de metodo de pago
    (function() {
        var btns = document.querySelectorAll('.pm-btn');
        var panels = document.querySelectorAll('.pm-panel');

        function selectWithAnim(method) {
            btns.forEach(function(b) {
                b.classList.toggle('selected', b.dataset.method === method);
            });
            panels.forEach(function(p) {
                if (p.dataset.method === method) {
                    p.classList.remove('show');
                    // Forzar reflow para reiniciar animacion
                    void p.offsetWidth;
                    p.classList.add('show');
                } else {
                    p.classList.remove('show');
                }
            });
        }

        // Reemplazar el handler del toggle original
        // (que ya estaba definido en el codigo)
        btns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                selectWithAnim(btn.dataset.method);
                var hidden = document.getElementById('paymentMethodInput');
                if (hidden) hidden.value = btn.dataset.method;
            });
        });
    })();

})();
