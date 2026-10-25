/* KernelBase: cache dos arquivos do laboratório.
   Os arquivos do sistema têm o hash do conteúdo no nome e ficam numa versão fixa
   do repositório, então podem ser guardados para sempre no navegador. */
const CACHE = "kb-lab-v1";
const LAB = /raw\.githubusercontent\.com\/Daniel-Pereira-Linux\/kernel-docs-br\/[0-9a-f]{40}\/|\/lab\/v86\/|\/labout\//;
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k.startsWith("kb-lab-") && k !== CACHE) await caches.delete(k);
  await self.clients.claim();
})()));
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || req.headers.has("range") || !LAB.test(req.url)) return;
  e.respondWith((async () => {
    const c = await caches.open(CACHE);
    const hit = await c.match(req.url);
    if (hit) return hit;
    const r = await fetch(req.url, { mode: "cors", credentials: "omit" });
    if (r.ok) c.put(req.url, r.clone()).catch(() => {});
    return r;
  })());
});
