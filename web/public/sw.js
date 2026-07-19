const VERSION = 'datarg-pwa-v2';
const APP_CACHE = `${VERSION}-app`;
const DATA_CACHE = `${VERSION}-data`;
const APP_SHELL = [
  '/',
  '/offline.html',
  '/manifest.webmanifest',
  '/datarg-logo.png',
  '/icons/app-icon-192.png',
  '/icons/app-icon-512.png',
  '/icons/apple-touch-icon.png',
  '/icons/favicon-32.png'
];

async function installAppShell() {
  const cache = await caches.open(APP_CACHE);
  await cache.addAll(APP_SHELL);

  const page = await cache.match('/');
  const html = await page.text();
  const builtAssets = [...html.matchAll(/(?:src|href)="(\/assets\/[^"?]+)"/g)].map(match => match[1]);
  await cache.addAll([...new Set(builtAssets)]);
  await self.skipWaiting();
}

self.addEventListener('install', event => {
  event.waitUntil(installAppShell());
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key.startsWith('datarg-pwa-') && !key.startsWith(VERSION)).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request, cacheName, fallback) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response.ok) await cache.put(request, response.clone());
    return response;
  } catch {
    return (await cache.match(request)) || (fallback ? await caches.match(fallback) : undefined) || new Response('Sin conexión', { status: 503 });
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) (await caches.open(APP_CACHE)).put(request, response.clone());
  return response;
}

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request, APP_CACHE, '/offline.html'));
    return;
  }
  if (url.pathname.startsWith('/data/')) {
    event.respondWith(networkFirst(request, DATA_CACHE));
    return;
  }
  if (url.pathname.startsWith('/assets/') || url.pathname.startsWith('/icons/') || url.pathname === '/datarg-logo.png') {
    event.respondWith(cacheFirst(request));
  }
});
