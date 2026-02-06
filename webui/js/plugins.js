// Plugin system for Agent Zero
// Loads x-extension tags by resolving plugin manifests and reusing component infrastructure

import { importComponent, getParentAttributes } from './components.js';
import { getCsrfToken } from './api.js';

// Cache for plugin manifests
const extensionCache = {};

// Batch fetch plugin manifests from API
async function fetchPluginManifests(pluginIds) {
  try {
    const response = await fetch("/plugins_resolve", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": await getCsrfToken(),
      },
      body: JSON.stringify({ ids: pluginIds }),
    });

    if (!response.ok) {
      throw new Error(`Failed to resolve plugins: ${response.statusText}`);
    }

    const result = await response.json();
    if (!result.ok || !result.data) {
      throw new Error("Invalid plugins response");
    }

    return result.data;
  } catch (error) {
    console.error("Error batch-fetching plugin manifests:", error);
    return [];
  }
}

// Merge manifest props with element attributes (element attributes override manifest)
function mergePropsWithAttributes(manifestProps, element) {
  const elementAttrs = {};
  for (let attr of element.attributes) {
    if (attr.name !== "id") {
      try {
        elementAttrs[attr.name] = JSON.parse(attr.value);
      } catch (_e) {
        elementAttrs[attr.name] = attr.value;
      }
    }
  }
  return { ...manifestProps, ...elementAttrs };
}

// Set merged props as data attributes on element
function setAttributesOnElement(props, element) {
  for (const [key, value] of Object.entries(props)) {
    if (typeof value === "object") {
      element.setAttribute(key, JSON.stringify(value));
    } else {
      element.setAttribute(key, value);
    }
  }
}

// Load a single plugin by calling importComponent with manifest URLs
async function loadPlugin(pluginId, targetElement) {
  // Get manifest from cache
  let manifest = extensionCache[pluginId];
  
  if (!manifest || manifest.error) {
    throw new Error(manifest?.error || `Plugin '${pluginId}' not found`);
  }

  // Extract UI configuration from provides.ui
  // The API already resolves component_url and module_url from provides.ui
  const componentUrl = manifest.component_url;
  const moduleUrl = manifest.module_url;
  const props = manifest.props || {};

  // Merge props and set as attributes
  const mergedProps = mergePropsWithAttributes(props, targetElement);
  setAttributesOnElement(mergedProps, targetElement);

  // Call importComponent with plugin URLs
  // We prepend "components/../" to bypass the check in importComponent
  if (componentUrl) {
    const adjustedUrl = "components/.." + componentUrl;
    await importComponent(adjustedUrl, targetElement);
  }

  // Load module if specified
  // Browser's native module cache handles deduplication
  if (moduleUrl) {
    await import(moduleUrl);
  }
}

// Find all x-extension tags in root elements
function findAllExtensionTags(roots) {
  const rootElements = Array.isArray(roots) ? roots : [roots];
  return rootElements.flatMap((root) =>
    Array.from(root.querySelectorAll("x-extension"))
  );
}

// Collect unique plugin IDs that need to be fetched (not in cache)
function collectUniqueUncachedPluginIds(extensions) {
  const pluginIds = [];
  const seen = new Set();
  
  for (const extension of extensions) {
    const pluginId = extension.getAttribute("id");
    if (!pluginId) {
      console.error("x-extension missing id attribute:", extension);
      continue;
    }
    
    // Only add if not seen and not cached
    if (!seen.has(pluginId) && !extensionCache[pluginId]) {
      pluginIds.push(pluginId);
      seen.add(pluginId);
    }
  }
  
  return pluginIds;
}

// Main loader: scan DOM, batch fetch manifests, load all plugins
export async function loadExtensions(roots = [document.documentElement]) {
  try {
    // Find all x-extension tags
    const extensions = findAllExtensionTags(roots);
    
    if (extensions.length === 0) return;

    // Collect plugin IDs that need fetching
    const pluginIds = collectUniqueUncachedPluginIds(extensions);
    
    // Batch fetch all uncached manifests in one API call
    if (pluginIds.length > 0) {
      const manifests = await fetchPluginManifests(pluginIds);
      
      // Update cache with fetched manifests
      for (const manifest of manifests) {
        if (!manifest.error) {
          extensionCache[manifest.id] = manifest;
        } else {
          console.error(`Plugin '${manifest.id}' failed to load:`, manifest.error);
        }
      }
    }

    // Map plugin IDs to extension elements for parallel loading
    const extensionMap = new Map();
    for (const extension of extensions) {
      const pluginId = extension.getAttribute("id");
      if (!pluginId) continue;
      
      if (!extensionMap.has(pluginId)) {
        extensionMap.set(pluginId, []);
      }
      extensionMap.get(pluginId).push(extension);
    }

    // Load all plugins in parallel using cached manifests
    await Promise.all(
      Array.from(extensionMap.entries()).flatMap(([pluginId, extensionElements]) =>
        extensionElements.map(async (extension) => {
          try {
            await loadPlugin(pluginId, extension);
          } catch (error) {
            console.error(`Error loading extension '${pluginId}':`, error);
            extension.innerHTML = `<div class="error">Failed to load plugin: ${pluginId}</div>`;
          }
        })
      )
    );
  } catch (error) {
    console.error("Error loading extensions:", error);
  }
}

// Extend global xAttrs to check both x-component and x-extension tags
// This allows plugins to use globalThis.xAttrs() and get both component and extension attrs
globalThis.xAttrs = function(el) {
  return getParentAttributes(el, ['x-component', 'x-extension']);
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => loadExtensions());
} else {
  loadExtensions();
}

// Watch for DOM changes to dynamically load x-extension tags
const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType === 1) {
        // ELEMENT_NODE
        // Check if this node is an x-extension tag
        if (node.matches?.("x-extension")) {
          loadExtensions([node.parentElement || document.documentElement]);
        } else if (node.querySelectorAll) {
          // Check if descendants contain x-extension tags
          const extensions = node.querySelectorAll("x-extension");
          if (extensions.length > 0) {
            loadExtensions([node]);
          }
        }
      }
    }
  }
});
observer.observe(document.body, { childList: true, subtree: true });
