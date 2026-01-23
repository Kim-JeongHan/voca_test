// Voca Trainer Service Worker
// Provides offline caching for PWA functionality

const CACHE_NAME = 'voca-trainer-v9';
const STATIC_ASSETS = [
    './',
    './index.html',
    './css/style.css',
    './js/storage.js',
    './js/tts.js',
    './js/image_association.js',
    './js/app.js',
    './manifest.json'
];

const WASM_ASSETS = [
    './wasm/voca_core.js',
    './wasm/voca_core.wasm'
];

// Install: cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                // Try to cache WASM assets, but don't fail if they don't exist yet
                return caches.open(CACHE_NAME)
                    .then((cache) => {
                        return Promise.all(
                            WASM_ASSETS.map((asset) =>
                                cache.add(asset).catch(() => {
                                    console.log(`WASM asset not available yet: ${asset}`);
                                })
                            )
                        );
                    });
            })
            .then(() => self.skipWaiting())
    );
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch: serve from cache, falling back to network
self.addEventListener('fetch', (event) => {
    const { request } = event;

    // Skip non-GET requests (POST for TTS worker, etc.)
    if (request.method !== 'GET') {
        return;
    }

    // Allow cross-origin requests for TTS (Dictionary API, Cloudflare Worker)
    // These should not be intercepted - let them go directly to network
    const url = new URL(request.url);
    if (url.hostname.includes('dictionaryapi.dev') ||
        url.hostname.includes('workers.dev')) {
        return;
    }

    // Skip other cross-origin requests
    if (!request.url.startsWith(self.location.origin)) {
        return;
    }

    // CSV files: Network first strategy (always get latest data)
    if (request.url.endsWith('.csv')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    if (response.ok) {
                        // Clone BEFORE using the response
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => caches.match(request))
        );
        return;
    }

    event.respondWith(
        caches.match(request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    // Return cached version, but also update cache in background
                    fetchAndCache(request);
                    return cachedResponse;
                }

                // Not in cache, fetch from network
                return fetchAndCache(request);
            })
            .catch(() => {
                // Network failed and no cache, return fallback
                if (request.mode === 'navigate') {
                    return caches.match('./index.html');
                }
                return new Response('Offline', { status: 503 });
            })
    );
});

async function fetchAndCache(request) {
    try {
        const response = await fetch(request);

        // Only cache successful responses
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        throw error;
    }
}
