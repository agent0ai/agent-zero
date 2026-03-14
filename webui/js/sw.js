const CACHE_NAME = 'agent-jumbo-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/index.css',
  '/js/manifest.json',
  '/public/icon.svg',
  '/vendor/alpine/alpine.min.js'
];

// Install Event - Caching assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate Event - Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
});

// Fetch Event - Cache First Strategy
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).then((fetchRes) => {
        // Don't cache API calls
        if (event.request.url.includes('/api/')) return fetchRes;

        return caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request.url, fetchRes.clone());
          return fetchRes;
        });
      });
    }).catch(() => {
      // Offline fallback can be added here
    })
  );
});

// PUSH Event - Handle incoming push notifications
self.addEventListener('push', (event) => {
  let data = { title: 'Agent Jumbo', body: 'New update available', icon: '/public/icon.svg' };
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/public/icon.svg',
    badge: '/public/icon.svg',
    vibrate: [100, 50, 100],
    actions: data.actions || [],
    data: {
      url: data.url || '/',
      requestId: data.requestId || null
    }
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification Click Event
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  // If the user clicked an action button (Approve/Deny)
  if (event.action && event.notification.data.requestId) {
    const action = event.action; // 'approve' or 'deny'
    const requestId = event.notification.data.requestId;

    event.waitUntil(
      fetch('/security_tool_action', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: action,
          requestId: requestId
        })
      }).then(response => {
        console.log('Action recorded:', action);
      }).catch(err => {
        console.error('Failed to report action:', err);
      })
    );
    return;
  }

  // Default behavior: focus or open window
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === '/' && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(event.notification.data.url || '/');
    })
  );
});
