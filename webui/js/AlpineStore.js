// Track all created stores
const stores = new Map();

/**
 * Creates a store that can be used to share state between components.
 * Uses initial state object and returns a proxy to it that uses Alpine when initialized
 * @template T
 * @param {string} name
 * @param {T} initialState
 * @returns {T}
 */
export function createStore(name, initialState) {
  const proxy = new Proxy(initialState, {
    set(target, prop, value) {
      const store = globalThis.Alpine?.store(name);
      if (store) store[prop] = value;
      else target[prop] = value;
      return true;
    },
    get(target, prop) {
      const store = globalThis.Alpine?.store(name);
      if (store) return store[prop];
      return target[prop];
    }
  });

  if (globalThis.Alpine) {
    globalThis.Alpine.store(name, initialState);
  } else {
    document.addEventListener("alpine:init", () => Alpine.store(name, initialState));
  }

  // Store the proxy
  stores.set(name, proxy);

  return /** @type {T} */ (proxy); // explicitly cast for linter support
}

/**
 * Get an existing store by name
 * @template T
 * @param {string} name
 * @returns {T | undefined}
 */
export function getStore(name) {
  return /** @type {T | undefined} */ (stores.get(name));
}

/**
 * Save current state of a store into a plain object, with optional include/exclude filters.
 * If exclude (blacklist) is provided and non-empty, everything except excluded keys is saved.
 * Otherwise, if include (whitelist) is provided and non-empty, only included keys are saved.
 * If both are empty, all own enumerable properties are saved.
 * @param {object} store
 * @param {string[]} [include]
 * @param {string[]} [exclude]
 * @returns {object}
 */
export function saveState(store, include = [], exclude = []) {
  const hasExclude = Array.isArray(exclude) && exclude.length > 0;
  const hasInclude = !hasExclude && Array.isArray(include) && include.length > 0;

  /** @type {Record<string, any>} */
  const snapshot = {};

  for (const key of Object.keys(store)) {
    if (hasExclude) {
      if (exclude.includes(key)) continue;
    } else if (hasInclude) {
      if (!include.includes(key)) continue;
    }

    const value = store[key];
    if (typeof value === "function") continue;

    if (Array.isArray(value)) {
      snapshot[key] = value.map((item) =>
        typeof item === "object" && item !== null ? { ...item } : item
      );
    } else if (typeof value === "object" && value !== null) {
      snapshot[key] = { ...value };
    } else {
      snapshot[key] = value;
    }
  }

  return snapshot;
}

/**
 * Load a previously saved state object back into a store, honoring include/exclude filters.
 * Filtering rules are the same as in saveState.
 * @param {object} store
 * @param {object} state
 * @param {string[]} [include]
 * @param {string[]} [exclude]
 */
export function loadState(store, state, include = [], exclude = []) {
  if (!state) return;

  const hasExclude = Array.isArray(exclude) && exclude.length > 0;
  const hasInclude = !hasExclude && Array.isArray(include) && include.length > 0;

  for (const key of Object.keys(state)) {
    if (hasExclude) {
      if (exclude.includes(key)) continue;
    } else if (hasInclude) {
      if (!include.includes(key)) continue;
    }

    const value = state[key];

    if (Array.isArray(value)) {
      store[key] = value.map((item) =>
        typeof item === "object" && item !== null ? { ...item } : item
      );
    } else if (typeof value === "object" && value !== null) {
      store[key] = { ...value };
    } else {
      store[key] = value;
    }
  }
}