/**
 * schedule.js - Logica del panel de horarios
 * Extraido de apps/stores/templates/stores/dashboard/schedule.html
 * Fecha: 2026-09-24 10:01
 */

(function() {
    'use strict';

/* ============================================================
       TOGGLE 24/7 - cambia el estilo visual y atenua la tabla
       ============================================================ */
    (function () {
        var toggle = document.getElementById('has_24_7_schedule');
        var box = document.getElementById('toggle-247-box');
        var info = document.getElementById('toggle-247-info');
        var table = document.getElementById('schedule-table');
        if (!toggle) return;

        toggle.addEventListener('change', function () {
            if (toggle.checked) {
                box.classList.add('active');
                table.classList.add('dimmed');
                info.textContent = '✅ Los horarios individuales están desactivados';
            } else {
                box.classList.remove('active');
                table.classList.remove('dimmed');
                info.textContent = 'Actívalo si abres siempre. Se ignora la tabla de abajo.';
            }
        });
    })();

    /* ============================================================
       CERRAR DIA (individual)
       ============================================================ */
    function toggleDay(dayNum) {
        var row = document.getElementById('row-' + dayNum);
        var isClosed = document.getElementById('closed_' + dayNum).checked;
        row.classList.toggle('closed', isClosed);
    }

    /* ============================================================
       APLICAR RAPIDO (tipo alarma)
       ============================================================ */
    (function () {
        var days = document.querySelectorAll('.qa-day');
        var btnApply = document.getElementById('btn-apply');
        var feedback = document.getElementById('qa-feedback');

        // Toggle de dias
        days.forEach(function (d) {
            d.addEventListener('click', function () {
                d.classList.toggle('active');
            });
        });

        // Atajos
        document.querySelectorAll('.qa-shortcut').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var preset = btn.dataset.preset;
                days.forEach(function (d) {
                    var day = parseInt(d.dataset.day);
                    var on = false;
                    if (preset === 'weekdays') on = day >= 0 && day <= 4;
                    else if (preset === 'weekend') on = day >= 5;
                    else if (preset === 'all') on = true;
                    else if (preset === 'none') on = false;
                    d.classList.toggle('active', on);
                });
            });
        });

        // Aplicar
        btnApply.addEventListener('click', function () {
            var selected = [];
            days.forEach(function (d) {
                if (d.classList.contains('active')) selected.push(parseInt(d.dataset.day));
            });

            if (selected.length === 0) {
                feedback.textContent = '⚠️ Marca al menos un día';
                feedback.style.color = '#e74c3c';
                feedback.classList.add('show');
                setTimeout(function () { feedback.classList.remove('show'); }, 2000);
                return;
            }

            var pOpen = document.getElementById('qa-pickup-open').value;
            var pClose = document.getElementById('qa-pickup-close').value;
            var dOpen = document.getElementById('qa-delivery-open').value;
            var dClose = document.getElementById('qa-delivery-close').value;

            selected.forEach(function (day) {
                var pO = document.querySelector('[name="day_' + day + '_pickup_open"]');
                var pC = document.querySelector('[name="day_' + day + '_pickup_close"]');
                var dO = document.querySelector('[name="day_' + day + '_delivery_open"]');
                var dC = document.querySelector('[name="day_' + day + '_delivery_close"]');
                var closedCb = document.getElementById('closed_' + day);

                if (pO) pO.value = pOpen;
                if (pC) pC.value = pClose;
                if (dO) dO.value = dOpen;
                if (dC) dC.value = dClose;

                // Desmarcar "Cerrado" y actualizar estilo
                if (closedCb && closedCb.checked) {
                    closedCb.checked = false;
                    toggleDay(day);
                }
            });

            // Feedback visual
            feedback.textContent = '✅ Aplicado a ' + selected.length + ' día(s)';
            feedback.style.color = '#27ae60';
            feedback.classList.add('show');
            setTimeout(function () { feedback.classList.remove('show'); }, 2500);
        });
    })();
})();
