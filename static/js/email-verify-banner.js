/**
 * Banner persistente de "verifica tu correo" si el usuario no ha verificado.
 */
(function () {
    'use strict';

    function escHtml(s) {
        return String(s || '').replace(/[&<>"']/g, function (c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function getCookie(name) {
        var v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
    }

    function buildBanner() {
        var div = document.createElement('div');
        div.className = 'verify-email-banner';
        div.id = 'verifyEmailBanner';
        div.innerHTML =
            '<span class="ve-icon">📧</span>' +
            '<span class="ve-text">Verifica tu correo electrónico para asegurar tu cuenta.</span>' +
            '<form method="post" action="/accounts/verify/resend/" class="ve-form">' +
                '<input type="hidden" name="csrfmiddlewaretoken" value="' + getCookie('csrftoken') + '">' +
                '<button type="submit" class="ve-btn">Reenviar</button>' +
            '</form>' +
            '<button class="ve-close" aria-label="Cerrar">✕</button>';
        return div;
    }

    function initBanner() {
        // Ya cerrada en esta sesion
        if (sessionStorage.getItem('ve_banner_closed') === '1') return;

        fetch('/accounts/verification-status/', {
            credentials: 'same-origin',
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(function (r) {
            if (!r.ok) throw new Error('no-auth');
            return r.json();
        })
        .then(function (data) {
            if (data.verified || !data.has_email) return;
            if (document.getElementById('verifyEmailBanner')) return;

            var header = document.querySelector('header');
            if (!header) return;

            var banner = buildBanner();
            header.parentNode.insertBefore(banner, header.nextSibling);

            banner.querySelector('.ve-close').addEventListener('click', function () {
                banner.remove();
                sessionStorage.setItem('ve_banner_closed', '1');
            });
        })
        .catch(function () { /* no logueado, no mostrar */ });
    }

    document.addEventListener('DOMContentLoaded', initBanner);
})();
