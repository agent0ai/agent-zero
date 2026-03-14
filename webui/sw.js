const CACHE_VERSION = "agent-zero-v1";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGE_CACHE = `${CACHE_VERSION}-pages`;

const PRECACHE_URLS = [
    "/js/manifest.json",
    "/public/apple-touch-icon.png",
    "/public/favicon.svg",
    "/public/icon-192.png",
    "/public/icon-512.png",
    "/public/icon-maskable.svg",
    "/public/icon.svg",
];

function isSameOrigin(url) {
    return url.origin === self.location.origin;
}

function isStaticAsset(pathname) {
    return (
        pathname === "/index.css" ||
        pathname === "/index.js" ||
        pathname === "/login.css" ||
        pathname.startsWith("/components/") ||
        pathname.startsWith("/css/") ||
        pathname.startsWith("/js/") ||
        pathname.startsWith("/public/") ||
        pathname.startsWith("/vendor/")
    );
}

function isBypassedRequest(pathname) {
    return (
        pathname.startsWith("/api/") ||
        pathname.startsWith("/socket.io/") ||
        pathname.startsWith("/ws")
    );
}

async function cacheResponse(cacheName, request, response) {
    if (!response || !response.ok) {
        return response;
    }

    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
    return response;
}

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS)).then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((key) => ![STATIC_CACHE, PAGE_CACHE].includes(key))
                    .map((key) => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (request.method !== "GET" || !isSameOrigin(url) || isBypassedRequest(url.pathname)) {
        return;
    }

    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request)
                .then((response) => cacheResponse(PAGE_CACHE, request, response))
                .catch(async () => {
                    const cachedResponse = await caches.match(request);
                    if (cachedResponse) {
                        return cachedResponse;
                    }

                    return new Response(
                        `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Offline</title></head><body><h1>Agent Zero is offline</h1><p>Reconnect to load the latest session data.</p></body></html>`,
                        {
                            headers: { "Content-Type": "text/html; charset=utf-8" },
                            status: 503,
                            statusText: "Service Unavailable",
                        }
                    );
                })
        );
        return;
    }

    if (!isStaticAsset(url.pathname)) {
        return;
    }

    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            const networkResponse = fetch(request)
                .then((response) => cacheResponse(STATIC_CACHE, request, response))
                .catch(() => cachedResponse);

            return cachedResponse || networkResponse;
        })
    );
});
