const MAX_CONCURRENT_WEBUI_LOADS = 4;
let activeLoads = 0;
const waitingLoads = [];

/**
 * Run a web UI load operation within the shared request budget.
 *
 * @template T
 * @param {() => T | Promise<T>} load
 * @returns {Promise<T>}
 */
export function withWebuiLoadSlot(load) {
  return new Promise((resolve, reject) => {
    const start = async () => {
      activeLoads += 1;
      try {
        resolve(await load());
      } catch (error) {
        reject(error);
      } finally {
        activeLoads -= 1;
        waitingLoads.shift()?.();
      }
    };

    if (activeLoads < MAX_CONCURRENT_WEBUI_LOADS) {
      start();
    } else {
      waitingLoads.push(start);
    }
  });
}

/**
 * Run a list of load operations without exceeding the shared request budget.
 * Results retain input order even when individual operations finish out of order.
 *
 * @template T, R
 * @param {T[]} items
 * @param {(item: T, index: number) => R | Promise<R>} load
 * @returns {Promise<R[]>}
 */
export function mapWithConcurrency(items, load) {
  return Promise.all(items.map((item, index) =>
    withWebuiLoadSlot(() => load(item, index))
  ));
}
