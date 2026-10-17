/* Ricoweer serviceworker: netwerk-eerst voor appbestanden, offline fallback. */
const VERSION='rico-app-20261017-modelstatus-v16';
const FILES=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',event=>{event.waitUntil((async()=>{const c=await caches.open(VERSION);await Promise.allSettled(FILES.map(f=>c.add(new Request(f,{cache:'reload'}))));await self.skipWaiting()})())});
self.addEventListener('activate',event=>{event.waitUntil((async()=>{for(const key of await caches.keys()){if((key.startsWith('regioweer-')||key.startsWith('rico-app-'))&&key!==VERSION)await caches.delete(key)}await self.clients.claim()})())});
self.addEventListener('fetch',event=>{
 const req=event.request;if(req.method!=='GET')return;
 const u=new URL(req.url);if(u.origin!==self.location.origin)return;
 if(!FILES.some(f=>new URL(f,self.registration.scope).pathname===u.pathname))return;
 event.respondWith((async()=>{const cache=await caches.open(VERSION);try{const response=await fetch(new Request(req,{cache:'no-store'}));if(response.ok)await cache.put(req,response.clone());return response}catch(e){const cached=await cache.match(req,{ignoreSearch:true});if(cached)return cached;throw e}})());
});

// API guard update 2026-10-17
