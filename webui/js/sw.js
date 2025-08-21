// Import the Workbox library
importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js');

// Check if Workbox is available
if (workbox) {
    console.log('Workbox is loaded! 🎉');

    // Set the cache name prefix and suffix (version number)
    // Increment the suffix version number whenever you make significant changes to the Service Worker logic
    workbox.core.setCacheNameDetails({
        prefix: 'agent-zero',
        suffix: 'v11' // New version number to trigger update
    });

    // Precache core static assets (Cache First strategy)
    // These files will be downloaded and cached during the Service Worker installation phase.
    const CORE_STATIC_URLS = [
        '/',
        '/index.html',
        '/index.css',
        '/css/messages.css',
        '/css/toast.css',
        '/css/settings.css',
        '/css/notification.css',
        '/js/manifest.json',
        '/js/sw.js'
    ];

    // workbox.precaching.precacheAndRoute automatically handles install and activate events,
    // and applies a Cache First strategy for these precached resources.
    workbox.precaching.precacheAndRoute(CORE_STATIC_URLS);

    // Cache all image formats under the /public/ directory (Cache First strategy)
    // Suitable for images that don't change frequently and need fast loading.
    workbox.routing.registerRoute(
        ({ request, url }) =>
            request.destination === 'image' && url.pathname.startsWith('/public/'),
        new workbox.strategies.CacheFirst({
            cacheName: 'public-images-cache',
            plugins: [
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 50, // Maximum 50 images in cache
                    maxAgeSeconds: 30 * 24 * 60 * 60, // Cache for 30 days
                }),
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200], // Ensure successful responses are cached
                }),
            ],
        })
    );

    // Cache JS and CSS files (Stale-While-Revalidate strategy)
    // Suitable for scripts and styles that need fast loading but also occasional updates.
    workbox.routing.registerRoute(
        ({ request, url }) =>
            (request.destination === 'script' || request.destination === 'style') &&
            (url.pathname.endsWith('.js') || url.pathname.endsWith('.css')),
        new workbox.strategies.StaleWhileRevalidate({
            cacheName: 'js-css-cache',
            plugins: [
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 100, // Maximum 100 JS/CSS files in cache
                }),
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200],
                }),
            ],
        })
    );

    // Cache all files under the /vendor/ directory (Cache First strategy)
    // which typically do not change frequently.
    workbox.routing.registerRoute(
        ({ url }) => url.pathname.startsWith('/vendor/'),
        new workbox.strategies.CacheFirst({
            cacheName: 'vendor-cache',
            plugins: [
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 60, // Maximum 60 vendor files in cache
                    maxAgeSeconds: 30 * 24 * 60 * 60, // Cache for 30 days
                }),
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200],
                }),
            ],
        })
    );

    // Handle other dynamic requests (Network First strategy)
    // For all other GET requests not matched by the above routes, prioritize network.
    workbox.routing.registerRoute(
        ({ url, request }) => {
            // Exclude WebSocket and EventSource requests
            if (request.url.includes('/ws') ||
                request.url.includes('/events') ||
                request.headers.get('accept') === 'text/event-stream') {
                return false;
            }
            // Exclude Service Worker itself and precached URLs (handled by precacheAndRoute)
            // Exclude files under /public/, /js/, /css/, /vendor/ (handled by specific routes)
            return request.method === 'GET' &&
                   !CORE_STATIC_URLS.includes(url.pathname) &&
                   !url.pathname.startsWith('/public/') &&
                   !url.pathname.startsWith('/js/') &&
                   !url.pathname.startsWith('/css/') &&
                   !url.pathname.startsWith('/vendor/');
        },
        new workbox.strategies.NetworkFirst({
            cacheName: 'dynamic-api-cache',
            plugins: [
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 20, // Limit dynamic API cache entries
                    maxAgeSeconds: 24 * 60 * 60, // Cache for 1 day
                }),
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200],
                }),
            ],
        })
    );

    // Fallback handler for requests that fail
    // This will result in the browser's default offline page if network and cache fail.
    workbox.routing.setCatchHandler(async ({ event }) => {
        console.warn('Service Worker: Network and cache failed for request:', event.request.url);
        return new Response('Offline Content Not Available', { status: 503 });
    });

    // Claim clients immediately after new Service Worker activation
    workbox.core.clientsClaim();
    // Skip waiting, allowing the new Service Worker to activate immediately
    workbox.core.skipWaiting();

} else {
    console.log('Workbox failed to load. 😬');
}