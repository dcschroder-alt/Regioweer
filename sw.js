const CACHE='regioweer-v75';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).catch(()=>{}))});
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const k of await caches.keys())if(k!==CACHE)await caches.delete(k);await self.clients.claim()})()));
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;const u=new URL(e.request.url);if(u.origin!==location.origin){e.respondWith(fetch(e.request));return}e.respondWith((async()=>{try{const r=await fetch(e.request,{cache:'no-store'});const c=await caches.open(CACHE);c.put(e.request,r.clone());return r}catch(err){return (await caches.match(e.request))||Response.error()}})())});
