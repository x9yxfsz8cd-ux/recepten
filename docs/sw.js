const CACHE = 'recepten-v1';
const STATISCH = [
  './index.html',
  './recept.html',
  './css/style.css',
  './manifest.json'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATISCH))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = e.request.url;

  // Recepten JSON: netwerk eerst, val terug op cache
  if (url.includes('recepten.json')) {
    e.respondWith(
      fetch(e.request)
        .then(res => {
          const kopie = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, kopie));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Externe bronnen (Google Fonts, afbeeldingen): netwerk, cache bijwerken
  if (!url.startsWith(self.location.origin)) {
    e.respondWith(
      caches.match(e.request).then(cached => {
        const netwerk = fetch(e.request).then(res => {
          caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          return res;
        });
        return cached || netwerk;
      })
    );
    return;
  }

  // Alles overig: cache eerst
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
