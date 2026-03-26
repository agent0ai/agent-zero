import { clear, clear_all } from "/js/cache.js";

export default async function clearCache(eventType, envelope) {
  try {
    // clear frontend cache areas when backend caches are cleared via API
    if (eventType == "clear_cache") {
      const areas = envelope?.data?.areas || [];
      console.log("Clearing caches", areas);
      if (areas.length > 0) {
        for (const area of areas) {
          clear(area);
        }
      } else {
        // clear all caches
        clear_all();
      }
    }
  } catch (e) {
    console.error(e);
  }
}
