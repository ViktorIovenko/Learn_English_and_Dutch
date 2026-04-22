const VERSION = "v1";
const PAGE_CACHE = `pages-${VERSION}`;
const ASSET_CACHE = `assets-${VERSION}`;
const AUDIO_CACHE = `audio-${VERSION}`;

const AUDIO_EXT_RE = /\.(mp3|wav|ogg)$/i;

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.map((key) => {
        if (key !== PAGE_CACHE && key !== ASSET_CACHE && key !== AUDIO_CACHE) {
          return caches.delete(key);
        }
        return undefined;
      })
    );
    await self.clients.claim();
  })());
});

function isAudioRequest(request, url) {
  if (request.destination === "audio") return true;
  if (AUDIO_EXT_RE.test(url.pathname)) return true;
  return url.pathname.startsWith("/audio") || url.pathname.includes("/audio/");
}

function isRangeRequest(request) {
  try {
    return request.headers && request.headers.has("range");
  } catch (_) {
    return false;
  }
}

function isAssetRequest(request) {
  return ["style", "script", "image", "font"].includes(request.destination);
}

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response && response.ok && response.status === 200) {
    await cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      await cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw err;
  }
}

async function staleWhileRevalidate(request, cacheName, event) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const networkPromise = (async () => {
    try {
      const response = await fetch(request);
      if (response && response.ok) {
        await cache.put(request, response.clone());
      }
      return response;
    } catch (err) {
      return null;
    }
  })();

  if (event) {
    event.waitUntil(networkPromise);
  }

  if (cached) return cached;
  const networkResponse = await networkPromise;
  if (networkResponse) return networkResponse;
  return new Response("Offline", { status: 504, statusText: "Gateway Timeout" });
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/api/")) return;

  if (isAudioRequest(request, url)) {
    if (isRangeRequest(request)) {
      event.respondWith(fetch(request));
      return;
    }
    event.respondWith(cacheFirst(request, AUDIO_CACHE));
    return;
  }

  if (request.mode === "navigate" || request.destination === "document") {
    event.respondWith(networkFirst(request, PAGE_CACHE));
    return;
  }

  if (isAssetRequest(request)) {
    event.respondWith(staleWhileRevalidate(request, ASSET_CACHE, event));
  }
});
