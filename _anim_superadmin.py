from pathlib import Path
from datetime import datetime
import shutil

tp = Path("templates/superadmin/order_detail.html")
backup = tp.parent / f"order_detail.html.bak-anim-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(tp, backup)
print(f"[OK] Backup: {backup.name}")

content = tp.read_text(encoding="utf-8")

# ============================================================
# 1) Agregar CSS al <style> existente
# ============================================================
css_animacion = """
    /* ============================================================
       ANIMACION DE ACCION - Overlay con feedback visual
       ============================================================ */
    .action-overlay {
        position: fixed;
        inset: 0;
        background: rgba(26, 26, 46, 0.8);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        z-index: 99999;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 20px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .action-overlay.show {
        display: flex;
        opacity: 1;
    }
    .action-modal {
        background: white;
        border-radius: 20px;
        padding: 32px 40px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        min-width: 280px;
        animation: actionModalPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    @keyframes actionModalPop {
        0% { transform: scale(0.85); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
    .action-icon {
        font-size: 3.5rem;
        line-height: 1;
        margin-bottom: 14px;
        display: inline-block;
    }
    .action-icon.icon-package {
        animation: packageShake 0.9s ease-in-out infinite;
    }
    @keyframes packageShake {
        0%, 100% { transform: rotate(0) scale(1); }
        50% { transform: rotate(-6deg) scale(1.08); }
    }
    .action-icon.icon-money {
        animation: moneyPulse 0.9s ease-in-out infinite;
    }
    @keyframes moneyPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.15); }
    }
    .action-text {
        font-size: 1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 18px;
    }
    .action-progress {
        width: 220px;
        height: 6px;
        background: #e9ecef;
        border-radius: 3px;
        overflow: hidden;
        margin: 0 auto;
    }
    .action-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #6c3483, #9b59b6);
        border-radius: 3px;
        width: 0%;
    }
    .action-modal.success .action-progress-bar {
        background: linear-gradient(90deg, #27ae60, #2ecc71);
    }
    .action-success {
        animation: successAppear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    @keyframes successAppear {
        0% { transform: scale(0.5); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
    .action-check {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 68px;
        height: 68px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2ecc71, #27ae60);
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px rgba(46, 204, 113, 0.45);
        animation: checkBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    @keyframes checkBounce {
        0% { transform: scale(0) rotate(-180deg); }
        60% { transform: scale(1.15) rotate(10deg); }
        100% { transform: scale(1) rotate(0); }
    }
    .action-success-text {
        font-size: 1.15rem;
        font-weight: 700;
        color: #27ae60;
    }
    @media (max-width: 480px) {
        .action-modal {
            padding: 26px 30px;
            min-width: 260px;
        }
        .action-icon {
            font-size: 3rem;
        }
        .action-text {
            font-size: 0.92rem;
        }
        .action-progress {
            width: 190px;
        }
    }
</style>"""

if "ANIMACION DE ACCION - Overlay" in content:
    print("[SKIP] El CSS ya estaba")
elif "</style>" in content:
    content = content.replace("</style>", css_animacion, 1)
    print("[OK] CSS de la animacion agregado")

# ============================================================
# 2) Quitar el confirm() nativo de mark_delivered
# ============================================================
old_confirm_delivered = 'onsubmit="return confirm(\'¿Marcar este pedido como entregado?\');"'
new_confirm_delivered = ""

# Buscar variantes del confirm
import re
# Variante 1
if "onsubmit=\"return confirm('¿Marcar este pedido como entregado?');\"" in content:
    content = content.replace("onsubmit=\"return confirm('¿Marcar este pedido como entregado?');\"", "", 1)
    print("[OK] Confirm nativo quitado de mark_delivered")

# Variante 2 (busqueda por regex si no matcheo arriba)
if "confirm" in content:
    # Buscar el form de mark_delivered y quitarle el onsubmit
    patron_delivered = re.compile(
        r'(<form method="post" action="\{%.*?superuser_mark_delivered.*?%\}")[^>]*onsubmit="[^"]*"([^>]*>)',
        re.DOTALL
    )
    content, n = patron_delivered.subn(r'\1\2', content)
    if n:
        print("[OK] Confirm nativo quitado de mark_delivered (regex)")

# ============================================================
# 3) Agregar el JS antes de </body>
# ============================================================
js_animacion = """
<script>
(function() {
    'use strict';

    var overlay = document.createElement('div');
    overlay.id = 'actionOverlay';
    overlay.className = 'action-overlay';
    overlay.innerHTML =
        '<div class="action-modal" id="actionModal">' +
            '<div class="action-icon" id="actionIcon"></div>' +
            '<div class="action-text" id="actionText"></div>' +
            '<div class="action-progress" id="actionProgress">' +
                '<div class="action-progress-bar" id="actionProgressBar"></div>' +
            '</div>' +
            '<div class="action-success" id="actionSuccess" style="display:none;">' +
                '<div class="action-check">\\u2713</div>' +
                '<div class="action-success-text" id="actionSuccessText"></div>' +
            '</div>' +
        '</div>';
    document.body.appendChild(overlay);

    var PACKAGE_EMOJI = '\\uD83D\\uDCE6'; // caja
    var MONEY_EMOJI = '\\uD83D\\uDCB0'; // dinero

    function showAnimation(type, onComplete) {
        var icon = document.getElementById('actionIcon');
        var text = document.getElementById('actionText');
        var progress = document.getElementById('actionProgress');
        var progressBar = document.getElementById('actionProgressBar');
        var success = document.getElementById('actionSuccess');
        var successText = document.getElementById('actionSuccessText');
        var modal = document.getElementById('actionModal');

        success.style.display = 'none';
        progress.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.style.transition = 'none';
        modal.classList.remove('success');
        icon.className = 'action-icon';
        overlay.classList.add('show');

        if (type === 'delivered') {
            icon.textContent = PACKAGE_EMOJI;
            icon.classList.add('icon-package');
            text.textContent = 'Marcando como entregado...';
            successText.textContent = '\\u00A1Entregado!';
        } else if (type === 'payment') {
            icon.textContent = MONEY_EMOJI;
            icon.classList.add('icon-money');
            text.textContent = 'Confirmando pago...';
            successText.textContent = '\\u00A1Pago confirmado!';
        }

        // Reiniciar transicion
        void progressBar.offsetWidth;
        progressBar.style.transition = 'width 1.8s cubic-bezier(0.4, 0, 0.2, 1)';
        progressBar.style.width = '100%';

        setTimeout(function() {
            progress.style.display = 'none';
            success.style.display = 'block';
            modal.classList.add('success');

            setTimeout(function() {
                onComplete();
            }, 900);
        }, 1800);
    }

    document.addEventListener('submit', function(e) {
        var form = e.target;
        var action = form.getAttribute('action') || '';

        var type = null;
        if (action.indexOf('superuser_mark_delivered') !== -1) {
            type = 'delivered';
        } else if (action.indexOf('superuser_confirm_payment') !== -1) {
            type = 'payment';
        }

        if (!type) return;

        e.preventDefault();

        showAnimation(type, function() {
            form.submit();
        });
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('show')) {
            e.stopPropagation();
            e.preventDefault();
        }
    }, true);
})();
</script>
</body>"""

if "actionOverlay" in content:
    print("[SKIP] El JS ya estaba")
elif "</body>" in content:
    content = content.replace("</body>", js_animacion, 1)
    print("[OK] JS de la animacion agregado")
else:
    print("[!] No se encontro </body>")

tp.write_bytes(content.encode("utf-8", errors="ignore"))

# Verificacion
after = tp.read_text(encoding="utf-8")
print()
print("[VERIFICACION]")
print(f"  CSS con action-overlay: {'.action-overlay' in after}")
print(f"  JS con actionOverlay: {'actionOverlay' in after}")
print(f"  Interceptor de delivered: {'superuser_mark_delivered' in after}")
print(f"  Interceptor de payment: {'superuser_confirm_payment' in after}")
print(f"  Confirm nativo removido: {'¿Marcar este pedido como entregado?' not in after}")
print(f"  Tamano: {len(content):,} chars")
