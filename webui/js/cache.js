let enabledGlobal = true;

/** @type {Map<string, boolean>} */
const enabledAreas = new Map();

/** @type {Map<string, Map<string, any>>} */
const cache = new Map();

export function toggle_global(enabled) {
  enabledGlobal = !!enabled;
}

export function toggle_area(area, enabled) {
  enabledAreas.set(area, !!enabled);
}

export function has(area, key) {
  if (!isEnabled(area)) return false;
  const areaCache = cache.get(area);
  if (!areaCache) return false;
  return areaCache.has(key);
}

export function add(area, key, data) {
  if (!isEnabled(area)) return;
  let areaCache = cache.get(area);
  if (!areaCache) {
    areaCache = new Map();
    cache.set(area, areaCache);
  }
  areaCache.set(key, data);
}

export function get(area, key, defaultValue = null) {
  if (!isEnabled(area)) return defaultValue;
  const areaCache = cache.get(area);
  if (!areaCache) return defaultValue;
  return areaCache.has(key) ? areaCache.get(key) : defaultValue;
}

export function remove(area, key) {
  if (!isEnabled(area)) return;
  const areaCache = cache.get(area);
  if (!areaCache) return;
  areaCache.delete(key);
}

export function clear(area) {
  if (hasGlob(area)) {
    const re = globToRegExp(area);
    for (const k of cache.keys()) {
      if (re.test(k)) cache.delete(k);
    }
    return;
  }
  cache.delete(area);
}

export function clear_all() {
  cache.clear();
}

function isEnabled(area) {
  if (!enabledGlobal) return false;
  const v = enabledAreas.get(area);
  return v === undefined ? true : v;
}

function hasGlob(pattern) {
  return /[\*\?\[]/.test(pattern);
}

function escapeRegExpChar(ch) {
  return /[\\^$.*+?()[\]{}|]/.test(ch) ? `\\${ch}` : ch;
}

function globToRegExp(glob) {
  let out = "^";
  for (let i = 0; i < glob.length; i++) {
    const ch = glob[i];

    if (ch === "*") {
      out += ".*";
      continue;
    }

    if (ch === "?") {
      out += ".";
      continue;
    }

    if (ch === "[") {
      const end = glob.indexOf("]", i + 1);
      if (end === -1) {
        out += "\\[";
        continue;
      }

      const content = glob.slice(i + 1, end);
      let cls = "";
      let j = 0;
      if (content[0] === "!" || content[0] === "^") {
        cls += "^";
        j++;
      }
      for (; j < content.length; j++) {
        const c = content[j];
        if (c === "\\") {
          cls += "\\\\";
          continue;
        }
        if (c === "]") {
          cls += "\\]";
          continue;
        }
        if (c === "-") {
          cls += "-";
          continue;
        }
        cls += escapeRegExpChar(c);
      }

      out += `[${cls}]`;
      i = end;
      continue;
    }

    out += escapeRegExpChar(ch);
  }
  out += "$";
  return new RegExp(out);
}
