import * as api from "./api.js";
import * as cache from "./cache.js";

/**
 * @typedef {string} WebuiExtension
 */



/**
 * @typedef {Object} LoadWebuiExtensionsResponse
 * @property {WebuiExtension[]} extensions
 */

/**
 * @typedef {Object} JsExtensionImport
 * @property {string} path
 * @property {{ default: (...data: any[]) => unknown }} module
 */

const JS_CACHE_AREA = "frontend_extensions_js(extensions)(plugins)";
const HTML_CACHE_AREA = "frontend_extensions_html(extensions)(plugins)";
const htmlExtensionLoads = new WeakMap();
let alpineInitialized = false;
const LOADING_SELECTOR = "x-component > .loading:empty, x-extension.loading";

export let initialHtmlExtensionsLoaded = false;

function checkInitialLoadComplete() {
  if (initialHtmlExtensionsLoaded || !alpineInitialized || document.querySelector(LOADING_SELECTOR)) return;
  globalThis.Alpine.nextTick(() => {
    if (initialHtmlExtensionsLoaded || document.querySelector(LOADING_SELECTOR)) return;
    initialHtmlExtensionsLoaded = true;
    document.dispatchEvent(new Event("webui-extensions-loaded"));
  });
}

export const API_EXTENSION_EXCLUDED_ENDPOINTS = new Set([
  "/api/load_webui_extensions",
]);

export function clearCache() {
  cache.clear(JS_CACHE_AREA);
  cache.clear(HTML_CACHE_AREA);
}

function manifestExtensionPaths(assetType, extensionPoint) {
  const manifest = globalThis.runtimeInfo?.webuiExtensions;
  if (!manifest || typeof manifest !== "object") return null;
  const extensionsByPoint = manifest[assetType];
  if (!extensionsByPoint || typeof extensionsByPoint !== "object") return null;
  const extensions = extensionsByPoint[extensionPoint];
  return Array.isArray(extensions) ? extensions : [];
}

/**
 * Call all JS extensions for a given extension point.
 *
 * @param {string} extensionPoint
 * @param {...any} data
 * @returns {Promise<void>}
 */
export async function callJsExtensions(extensionPoint, ...data){
  const extensions = cache.get(JS_CACHE_AREA, extensionPoint, null) || await loadJsExtensions(extensionPoint);
  for(const extension of extensions){
    try{
      await extension.module.default(...data);
    }catch(error){
      console.error(`Error calling extension: ${extension.path}`, error);
    }
  }
}

/**
 * Load JS extension modules for an extension point.
 *
 * @param {string} extensionPoint
 * @param {{ fresh?: boolean }} [options] Query current activation even if a page manifest exists.
 * @returns {Promise<JsExtensionImport[]>}
 */
export async function loadJsExtensions(extensionPoint, { fresh = false } = {}) {
  try {
    const cached = cache.get(JS_CACHE_AREA, extensionPoint, null);
    if (!fresh && cached != null) return cached;

    const manifestExtensions = fresh ? null : manifestExtensionPaths("js", extensionPoint);
    /** @type {WebuiExtension[]} */
    let extensionPaths = manifestExtensions;
    if (extensionPaths == null) {
      /** @type {LoadWebuiExtensionsResponse} */
      const response = await api.callJsonApi(`/api/load_webui_extensions`, {
        extension_point: extensionPoint,
        filters: ["*.js", "*.mjs"],
      });
      extensionPaths = response.extensions;
    }
    /** @type {JsExtensionImport[]} */
    const imports = await Promise.all(
      extensionPaths.map(async (path) => ({
        path,
        module: await import(normalizePath(path))
      }))
    );
    cache.add(JS_CACHE_AREA, extensionPoint, imports);
    return imports;
  } catch (error) {
    if (fresh) throw error;
    console.error("Error loading JS extensions:", error);
    return [];
  }
}

/**
 * Load and render all HTML extensions in the given DOM roots.
 *
 * @param {Element | Document | Array<Element | Document>} [roots]
 * @param {{ reload?: boolean }} [options]
 * @returns {Promise<void>}
 */
export async function loadHtmlExtensions(roots = [document.documentElement], { reload = false } = {}) {
  try {
    // Convert single root to array if needed
    /** @type {Array<Element | Document>} */
    const rootElements = Array.isArray(roots) ? roots : [roots];

    // Find all top-level components and load them in parallel
    /** @type {Element[]} */
    const extensions = rootElements.flatMap((root) =>
      Array.from(root.querySelectorAll("x-extension")),
    );

    if (extensions.length === 0) return;

    await Promise.all(
      extensions.map(async (extension) => {
        const path = extension.getAttribute("id");
        if (!path) {
          console.error("x-extension missing id attribute:", extension);
          return;
        }
        if (reload) extension.innerHTML = "";
        await importHtmlExtensions(path, /** @type {HTMLElement} */ (extension), { reload });
      }),
    );
  } catch (error) {
    console.error("Error loading HTML extensions:", error);
  }
}

/**
 * Reload and re-render all HTML extensions in the given DOM roots.
 *
 * @param {Element | Document | Array<Element | Document>} [roots]
 * @returns {Promise<void>}
 */
export function reloadHtmlExtensions(roots = [document.documentElement]) {
  return loadHtmlExtensions(roots, { reload: true });
}

// import all extensions for extension point via backend api
/**
 * Import all HTML extensions for an extension point and inject them as `<x-component>` tags.
 *
 * @param {string} extensionPoint
 * @param {HTMLElement} targetElement
 * @param {{ reload?: boolean }} [options]
 * @returns {Promise<void>}
 */
export function importHtmlExtensions(extensionPoint, targetElement, { reload = true } = {}) {
  const previous = htmlExtensionLoads.get(targetElement);
  if (!reload && previous?.point === extensionPoint) return previous.ready;

  targetElement.classList.add("loading");
  const isCurrent = () => htmlExtensionLoads.get(targetElement)?.ready === ready;
  const ready = getHtmlExtensionMarkup(extensionPoint)
    .then(html => {
      if (isCurrent()) targetElement.innerHTML = html;
    })
    .finally(() => {
      if (isCurrent()) {
        targetElement.classList.remove("loading");
        checkInitialLoadComplete();
      }
    })
    .catch(error => {
      if (isCurrent()) htmlExtensionLoads.delete(targetElement);
      console.error("Error importing HTML extensions:", error);
    });
  htmlExtensionLoads.set(targetElement, { point: extensionPoint, ready });
  return ready;
}

async function getHtmlExtensionMarkup(extensionPoint) {
  const cachedHtml = cache.get(HTML_CACHE_AREA, extensionPoint, null);
  if (cachedHtml != null) return cachedHtml;

  const manifestExtensions = manifestExtensionPaths("html", extensionPoint);
  /** @type {WebuiExtension[]} */
  let extensionPaths = manifestExtensions;
  if (extensionPaths == null) {
    /** @type {LoadWebuiExtensionsResponse} */
    const response = await api.callJsonApi(`/api/load_webui_extensions`, {
      extension_point: extensionPoint,
      filters: ["*.html", "*.htm", "*.xhtml"],
    });
    extensionPaths = response.extensions;
  }
  let combinedHTML = "";
  for (const extension of extensionPaths) {
    const path = normalizePath(extension);
    combinedHTML += `<x-component path="${path}"></x-component>`;
  }
  cache.add(HTML_CACHE_AREA, extensionPoint, combinedHTML);
  return combinedHTML;
}

/**
 * @param {string} path
 * @returns {string}
 */
function normalizePath(path) {
  return path.startsWith("/") ? path : "/" + path;
}

// Watch for DOM changes to dynamically load x-extensions
/** @type {MutationCallback} */
const extensionObserverCallback = (mutations) => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType === 1) {
        // ELEMENT_NODE
        // Check if this node or its descendants contain x-extension(s)
        const el = /** @type {Element} */ (node);
        if (el.matches?.("x-extension")) {
          const id = el.getAttribute("id");
          if (id) importHtmlExtensions(id, /** @type {HTMLElement} */ (el), { reload: false });
        } else if (/** @type {any} */ (el)["querySelectorAll"]) {
          loadHtmlExtensions([el]);
        }
      }
    }
  }
  checkInitialLoadComplete();
};

/** @type {MutationObserver} */
const extensionObserver = new MutationObserver(extensionObserverCallback);
extensionObserver.observe(document.body, { childList: true, subtree: true });

document.addEventListener("alpine:initialized", () => {
  alpineInitialized = true;
  checkInitialLoadComplete();
}, { once: true });

// Do an initial scan for static x-extension tags
// that already exist in the DOM (index.html), then rely on
// the observer for dynamically inserted nodes coming from components.
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => loadHtmlExtensions());
} else {
  loadHtmlExtensions();
}
