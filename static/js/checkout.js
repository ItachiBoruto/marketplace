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

})();
