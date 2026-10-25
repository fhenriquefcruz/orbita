/* ORBITA Aurora 3.13 | Cache only public assets inside the application scope.
 * HTML fallback is navigation-only: never return index.html for CSS/JS/data.
 * No API responses, user records or authentication material are cached.
 */
const CACHE = 'orbita-pages-v3.13.0-offline-scope.1';
const STATIC = [
  './', './index.html', './manifest.webmanifest', './assets/orbita-icon.svg',
  './cloud-config.js', './local-integrity.js', './auth.js', './cloud-core.js',
  './cloud-sync.js', './theme.js', './design-aurora.css'
];
const SCOPE = new URL(self.registration.scope);
const STATIC_URLS = new Set(STATIC.map(path => new URL(path, SCOPE).href));
const OFFLINE_INDEX = new URL('./index.html', SCOPE).href;

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE)
    .then(cache => cache.addAll(STATIC))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys()
    .then(keys => Promise.all(keys
      .filter(key => key.startsWith('orbita-pages-') && key !== CACHE)
      .map(key => caches.delete(key))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== SCOPE.origin || !url.pathname.startsWith(SCOPE.pathname)) return;
  if (url.pathname.includes('/api/')) return;

  // Ignore query parameters for known static assets; never cache unknown paths.
  const canonical = url.origin + url.pathname;
  const isStatic = STATIC_URLS.has(canonical);
  const isNavigation = req.mode === 'navigate';
  if (!isStatic && !isNavigation) return;

  event.respondWith((async () => {
    try {
      const response = await fetch(req);
      if (isStatic && response.ok && response.type === 'basic') {
        const copy = response.clone();
        event.waitUntil(caches.open(CACHE).then(cache => cache.put(canonical, copy)));
      }
      return response;
    } catch (_) {
      const cache = await caches.open(CACHE);
      const cached = await cache.match(isNavigation ? OFFLINE_INDEX : canonical);
      if (cached) return cached;
      // A missing JS/CSS resource must never receive HTML as fallback.
      return new Response('Recurso indisponível offline.', {
        status: 503,
        headers: {'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store'}
      });
    }
  })());
});
