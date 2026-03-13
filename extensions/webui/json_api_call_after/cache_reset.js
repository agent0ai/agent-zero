import { clear } from "/js/cache.js";

export default async function resetCache(ctx) {
  try {
    // clear frontend cache areas when backend caches are cleared via API
    if (ctx.endpoint == "cache_reset") {
      for (const area of ctx.data.areas) {
        clear(area);
      }
    }
  } catch (e) {
    console.error(e);
  }
}
