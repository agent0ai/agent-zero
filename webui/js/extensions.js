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
 * @property {{ default: (...data: any[]) => (void|Promise<void>) }} module
 */

const JS_CACHE_AREA = "frontend_extensions_js(extensions)(plugins)";
const HTML_CACHE_AREA = "frontend_extensions_html(extensions)(plugins)";

export const API_EXTENSION_EXCLUDED_ENDPOINTS = new Set([
  "/api/load_webui_extensions",
]);

export function clearCache() {
  cache.clear(JS_CACHE_AREA);
  cache.clear(HTML_CACHE_AREA);
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
 * @returns {Promise<JsExtensionImport[]>}
 */
export async function loadJsExtensions(extensionPoint) {
  try {
    const cached = cache.get(JS_CACHE_AREA, extensionPoint, null);
    if (cached != null) return cached;

    /** @type {LoadWebuiExtensionsResponse} */
    const response = await api.callJsonApi(`/api/load_webui_extensions`, {
      extension_point: extensionPoint,
      filters: ["*.js", "*.mjs"],
    });
    /** @type {JsExtensionImport[]} */
    const imports = await Promise.all(
      response.extensions.map(async (path) => ({
        path,
        module: await import(normalizePath(path))
      }))
    );
    cache.add(JS_CACHE_AREA, extensionPoint, imports);
    return imports;
  } catch (error) {
    console.error("Error loading JS extensions:", error);
    return [];
  }
}

// Load all x-component tags starting from root elements
/**
 * Load and render all HTML extensions in the given DOM roots.
 *
 * @param {Element | Document | Array<Element | Document>} [roots]
 * @returns {Promise<void>}
 */
export async function loadHtmlExtensions(roots = [document.documentElement]) {
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
        await importHtmlExtensions(path, /** @type {HTMLElement} */ (extension));
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
export async function reloadHtmlExtensions(roots = [document.documentElement]) {
  try {
    /** @type {Array<Element | Document>} */
    const rootElements = Array.isArray(roots) ? roots : [roots];

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

        extension.innerHTML = "";
        await importHtmlExtensions(path, /** @type {HTMLElement} */ (extension));
      }),
    );
  } catch (error) {
    console.error("Error reloading HTML extensions:", error);
  }
}

// import all extensions for extension point via backend api
/**
 * Import all HTML extensions for an extension point and inject them as `<x-component>` tags.
 *
 * @param {string} extensionPoint
 * @param {HTMLElement} targetElement
 * @returns {Promise<void>}
 */
export async function importHtmlExtensions(extensionPoint, targetElement) {
  try {
    const cachedHtml = cache.get(HTML_CACHE_AREA, extensionPoint, null);
    if (cachedHtml != null) {
      targetElement.innerHTML = cachedHtml;
      return;
    }

    /** @type {LoadWebuiExtensionsResponse} */
    const response = await api.callJsonApi(`/api/load_webui_extensions`, {
      extension_point: extensionPoint,
      filters: ["*.html", "*.htm", "*.xhtml"],
    });
    let combinedHTML = "";
    for (const extension of response.extensions) {
      const path = normalizePath(extension);
      combinedHTML += `<x-component path="${path}"></x-component>`;
    }
    cache.add(HTML_CACHE_AREA, extensionPoint, combinedHTML);
    targetElement.innerHTML = combinedHTML;
  } catch (error) {
    console.error("Error importing HTML extensions:", error);
    return;
  }
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
          if (id) importHtmlExtensions(id, /** @type {HTMLElement} */ (el));
        } else if (/** @type {any} */ (el)["querySelectorAll"]) {
          loadHtmlExtensions([el]);
        }
      }
    }
  }
};

/** @type {MutationObserver} */
const extensionObserver = new MutationObserver(extensionObserverCallback);
extensionObserver.observe(document.body, { childList: true, subtree: true });

// Do an initial scan for static x-extension tags
// that already exist in the DOM (index.html), then rely on
// the observer for dynamically inserted nodes coming from components.
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => loadHtmlExtensions());
} else {
  loadHtmlExtensions();
}
