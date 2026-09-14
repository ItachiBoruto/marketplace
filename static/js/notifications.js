/**
 * Sistema de notificaciones in-app.
 * Inyecta la campana en el header y maneja el dropdown.
 */
(function () {
    'use strict';

    function escapeHtml(str) {
        return String(str || '').replace(/[&<>"']/g, function (c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function buildBell() {
        var wrapper = document.createElement('div');
        wrapper.className = 'notif-wrapper';
        wrapper.innerHTML =
            '<button class="notif-bell" id="notifBell" aria-label="Notificaciones">' +
                '&#128276;' +
                '<span class="notif-badge" id="notifBadge" style="display:none;">0</span>' +
            '</button>' +
            '<div class="notif-dropdown" id="notifDropdown">' +
                '<div class="notif-loading">Cargando...</div>' +
            '</div>';
        return wrapper;
    }

    function initBell() {
        // Solo si el usuario esta logueado (buscamos un header)
        var header = document.querySelector('header .container');
        if (!header) return;

        // No inyectar si ya existe
        if (document.getElementById('notifBell')) return;

        // Preferir header-top (arriba a la derecha, junto al logo)
        // Fallback: nav
        var target = header.querySelector('.header-top')
                  || header.querySelector('nav')
                  || header;

        var bell = buildBell();

        // Si hay boton toggle (movil), insertar antes
        // Si no, agregar al final (queda a la derecha del area)
        var toggle = target.querySelector('.header-menu-toggle');
        if (toggle && target.classList.contains('header-top')) {
            target.insertBefore(bell, toggle);
        } else {
            target.appendChild(bell);
        }

        // Eventos
        var bellBtn = document.getElementById('notifBell');
        var dropdown = document.getElementById('notifDropdown');
        var badge = document.getElementById('notifBadge');

        bellBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            dropdown.classList.toggle('show');
            if (dropdown.classList.contains('show')) {
                loadDropdown();
            }
        });

        document.addEventListener('click', function (e) {
            if (!e.target.closest('.notif-wrapper')) {
                dropdown.classList.remove('show');
            }
        });

        // Cargar contador inicial
        refreshBadge();
    }

    function loadDropdown() {
        var dropdown = document.getElementById('notifDropdown');
        dropdown.innerHTML = '<div class="notif-loading">Cargando...</div>';

        fetch('/notifications/dropdown/', {
            headers: {'X-Requested-With': 'XMLHttpRequest'},
            credentials: 'same-origin'
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            dropdown.innerHTML = data.html;
            updateBadge(data.unread_count);
        })
        .catch(function () {
            dropdown.innerHTML = '<div class="notif-loading">Error de conexion</div>';
        });
    }

    function refreshBadge() {
        fetch('/notifications/unread-count/', {
            headers: {'X-Requested-With': 'XMLHttpRequest'},
            credentials: 'same-origin'
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            updateBadge(data.unread_count);
        })
        .catch(function () {});
    }

    function updateBadge(count) {
        var badge = document.getElementById('notifBadge');
        if (!badge) return;
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline-block';
            badge.classList.add('bump');
            setTimeout(function () { badge.classList.remove('bump'); }, 400);
        } else {
            badge.style.display = 'none';
        }
    }

    // Refrescar badge cada 60 segundos
    setInterval(refreshBadge, 60000);

    document.addEventListener('DOMContentLoaded', initBell);

    // Exponer para uso externo (cuando se crea una notificacion desde otra parte)
    window.refreshNotifBadge = refreshBadge;
})();
