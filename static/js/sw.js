// ===== CONFIGURATION =====
const CACHE_VERSION = 'v5'; // Incrémenté pour forcer la mise à jour
const CACHE_NAME = `destock-${CACHE_VERSION}`;
const OFFLINE_URL = '/offline';
const ASSETS = [
    '/',
    OFFLINE_URL,
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/img/logo.webp',
    '/static/img/hero-banner.webp',
    'https://fonts.googleapis.com/css2?family=Inter:wght@700;900&display=swap'
];

// ===== INSTALLATION =====
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Cache initialisé :', CACHE_NAME);
                return cache.addAll(ASSETS).catch(err => {
                    console.error('[SW] Erreur de cache :', err);
                });
            })
    );
    // Force l'activation immédiate
    self.skipWaiting();
});

// ===== STRATÉGIE DE CACHE =====
self.addEventListener('fetch', (event) => {
    const request = event.request;
    
    // 1. Ignore les requêtes non-GET
    if (request.method !== 'GET') return;

    // 2. Gestion des pages (HTML)
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => cacheNetworkResponse(request, response))
                .catch(() => caches.match(OFFLINE_URL))
        );
        return;
    }

    // 3. Stratégie Cache First pour les assets
    if (request.url.match(/\.(css|js|webp|woff2|json)$/)) {
        event.respondWith(
            caches.match(request)
                .then(cached => cached || fetchAndCache(request))
        );
        return;
    }

    // 4. Pour le reste : Network First
    event.respondWith(
        fetch(request)
            .then(response => cacheNetworkResponse(request, response))
            .catch(() => caches.match(request))
    );
});

// ===== FONCTIONS UTILITAIRES =====
async function fetchAndCache(request) {
    const response = await fetch(request);
    return cacheNetworkResponse(request, response);
}

async function cacheNetworkResponse(request, response) {
    if (!response || response.status !== 200) return response;
    
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, response.clone());
    return response;
}

// ===== NETTOYAGE =====
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(
                keys.map(key => key !== CACHE_NAME && caches.delete(key))
            )
            .then(() => {
                console.log('[SW] Anciens caches nettoyés');
                return self.clients.claim();
            })
    );
});