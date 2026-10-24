/* ORBITA | Cache only static application files. Never caches API responses or private messages. */
const CACHE='orbita-pages-v3.5.0-isolation.1';
const STATIC=['./','./index.html','./manifest.webmanifest','./assets/orbita-icon.svg','./cloud-config.js','./auth.js','./cloud-core.js','./cloud-sync.js','./theme.js','./design-aurora.css'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(STATIC)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('orbita-pages-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',event=>{
 const req=event.request; if(req.method!=='GET')return;
 const url=new URL(req.url); if(url.origin!==self.location.origin||url.pathname.includes('/api/'))return;
 event.respondWith(fetch(req).then(res=>{if(res.ok&&res.type==='basic'){const copy=res.clone();caches.open(CACHE).then(c=>c.put(req,copy))}return res}).catch(()=>caches.match(req).then(res=>res||caches.match('./index.html'))));
});
