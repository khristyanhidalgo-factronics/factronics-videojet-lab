/* Service worker — Factronics Videojet Lab (offline)
   Estrategia: precache del shell de la app + cache-first con actualización en
   segundo plano. Sube la versión del cache al publicar cambios. */
const VERSION = 'fvl-v0.2.0-alpha-2';
const SHELL = [
  './',
  './index.html',
  './datos.js',
  './manifest.webmanifest',
  '../assets/logo.svg'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((claves) => Promise.all(
      claves.filter((k) => k !== VERSION).map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then((hit) => {
      if (hit) return hit;
      return fetch(e.request).then((resp) => {
        const copia = resp.clone();
        caches.open(VERSION).then((c) => c.put(e.request, copia)).catch(() => {});
        return resp;
      }).catch(() => caches.match('./index.html'));
    })
  );
});
