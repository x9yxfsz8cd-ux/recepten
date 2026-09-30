/* Service worker.
   De productfoto's moeten offline beschikbaar zijn: juist in de kelder van een
   supermarkt heb je geen bereik, en daar is het winkelscherm voor bedoeld. */

const CACHE = 'recepten-v787396';

const STATISCH = [
  './',
  './index.html',
  './recept.html',
  './winkel.html',
  './import.html',
  './css/style.css?v=787396',
  './js/gedeeld.js?v=787396',
  './js/ingredient-icoon.js?v=787396',
  './js/opslag.js?v=787396',
  './manifest.json',
];

// Data en afbeeldingen halen we bij installatie binnen, maar een mislukte
// afbeelding mag de hele installatie niet laten klappen.
async function vulCache() {
  const cache = await caches.open(CACHE);
  await cache.addAll(STATISCH);

  try {
    const [recepten, producten] = await Promise.all([
      fetch('./data/recepten.json', { cache: 'no-cache' }).then(r => r.json()),
      fetch('./data/ah-producten.json', { cache: 'no-cache' }).then(r => r.json()).catch(() => ({})),
    ]);
    await cache.put('./data/recepten.json',
      new Response(JSON.stringify({ recepten: recepten.recepten }),
        { headers: { 'Content-Type': 'application/json' } }));

    const paden = new Set();
    recepten.recepten.forEach(r => {
      if (r.afbeelding && !r.afbeelding.startsWith('http')) paden.add('./' + r.afbeelding);
    });
    Object.values(producten).forEach(p => {
      if (p && p.afbeelding && !String(p.afbeelding).startsWith('http')) {
        paden.add('./' + p.afbeelding);
      }
    });
    await Promise.all([...paden].map(pad =>
      cache.add(pad).catch(() => {})       // één kapotte foto mag niets breken
    ));
  } catch {}
}

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(vulCache());
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);

  // Data: netwerk eerst, zodat nieuwe recepten meteen doorkomen
  if (url.pathname.endsWith('.json')) {
    e.respondWith(
      // no-cache dwingt hercontrole af; anders serveert de HTTP-cache van de
      // browser oude receptdata en zie je wijzigingen niet terug
      fetch(new Request(e.request, { cache: 'no-cache' }))
        .then(res => {
          const kopie = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, kopie));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Al het andere: cache eerst. Dat maakt de app snel en offline bruikbaar.
  e.respondWith(
    caches.match(e.request).then(gevonden => gevonden || fetch(e.request)
      .then(res => {
        if (res.ok && url.origin === location.origin) {
          const kopie = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, kopie));
        }
        return res;
      })
      .catch(() => gevonden)
    )
  );
});
