// Mi Marketplace - Service Worker
// v1 - Cache-first para estaticos, network-first para HTML

const CACHE_NAME = 'mi-marketplace-v1';
const OFFLINE_URL = '/offline/';

// Assets que se cachean al instalar
const PRECACHE = [
    '/',
    '/offline/',
    '/static/css/style.css',
    '/static/js/cart-toast.js',
    '/static/js/notifications.js',
    '/static/js/email-verify-banner.js',
    '/static/img/icons/icon-192x192.png',
    '/static/img/icons/icon-512x512.png',
    '/static/img/apple-touch-icon.png',
];

// INSTALL: precachear assets estaticos
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(PRECACHE))
            .then(() => self.skipWaiting())
    );
});

// ACTIVATE: limpiar caches viejos
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((k) => k !== CACHE_NAME)
                    .map((k) => caches.delete(k))
            );
        }).then(() => self.clients.claim())
    );
});

// FETCH: estrategia segun tipo de recurso
self.addEventListener('fetch', (event) => {
    const req = event.request;

    // Solo GET
    if (req.method !== 'GET') return;

    // Ignorar requests a otros dominios (Cloudinary, Sentry, etc.)
    const url = new URL(req.url);
    if (url.origin !== self.location.origin) return;

    // Ignorar admin, accounts, cart, orders (dinamicos)
    const skipPrefixes = ['/admin/', '/accounts/', '/cart/', '/orders/', '/notifications/'];
    if (skipPrefixes.some((p) => url.pathname.startsWith(p))) return;

    // HTML / navegacion: network-first con fallback a offline
    if (req.mode === 'navigate') {
        event.respondWith(
            fetch(req)
                .then((response) => {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
                    return response;
                })
                .catch(() => caches.match(OFFLINE_URL))
        );
        return;
    }

    // Estaticos: cache-first
    event.respondWith(
        caches.match(req).then((cached) => {
            if (cached) return cached;
            return fetch(req).then((response) => {
                // Solo cachear respuestas validas
                if (response && response.status === 200) {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
                }
                return response;
            });
        })
    );
});
