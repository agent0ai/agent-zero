import { createStore } from "/js/AlpineStore.js";

let bootstrapTooltipObserver = null;

function ensureBootstrapTooltip(element) {
  if (!element || !(element instanceof Element)) return;
  
  const bs = globalThis.bootstrap;
  if (!bs?.Tooltip) return;

  const existing = bs.Tooltip.getInstance(element);
  const title = element.getAttribute("title") || element.getAttribute("data-bs-original-title");

  if (!title) return;

  if (existing) {
    if (element.getAttribute("title")) {
      element.setAttribute("data-bs-original-title", title);
      element.removeAttribute("title");
    }
    existing.setContent({ ".tooltip-inner": title });
    return;
  }

  if (element.getAttribute("title")) {
    element.setAttribute("data-bs-original-title", title);
    element.removeAttribute("title");
  }

  element.setAttribute("data-bs-toggle", "tooltip");
  element.setAttribute("data-bs-trigger", "hover");
  element.setAttribute("data-bs-tooltip-initialized", "true");
  new bs.Tooltip(element, {
    delay: { show: 0, hide: 0 },
    trigger: "hover",
  });
}

function initBootstrapTooltips(root = document) {
  if (!globalThis.bootstrap?.Tooltip) return;
  const tooltipTargets = root.querySelectorAll(
    "[title]:not([data-bs-tooltip-initialized]), [data-bs-original-title]:not([data-bs-tooltip-initialized])"
  );
  tooltipTargets.forEach((element) => ensureBootstrapTooltip(element));
}

function observeBootstrapTooltips() {
  if (!globalThis.bootstrap?.Tooltip) return;
  
  // Prevent multiple observers
  if (bootstrapTooltipObserver) return;
  
  bootstrapTooltipObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === "attributes" && mutation.attributeName === "title") {
        ensureBootstrapTooltip(mutation.target);
        return;
      }

      if (mutation.type === "childList") {
        // Check removed nodes for tooltip cleanup
        mutation.removedNodes.forEach((node) => {
          if (!(node instanceof Element)) return;
          const tooltipElements = node.matches?.('[data-bs-tooltip-initialized]') ? [node] : Array.from(node.querySelectorAll?.('[data-bs-tooltip-initialized]') || []);
          tooltipElements.forEach((el) => {
            const instance = globalThis.bootstrap?.Tooltip?.getInstance(el);
            if (instance) {
              instance.dispose();
            }
          });
        });
        
        mutation.addedNodes.forEach((node) => {
          if (!(node instanceof Element)) return;
          if (node.matches("[title]") || node.querySelector("[title]")) {
            initBootstrapTooltips(node);
          }
        });
      }
    });
  });

  bootstrapTooltipObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["title"],
  });
}

function cleanupTooltipObserver() {
  if (bootstrapTooltipObserver) {
    bootstrapTooltipObserver.disconnect();
    bootstrapTooltipObserver = null;
  }
}

export const store = createStore("tooltips", {
  init() {
    initBootstrapTooltips();
    observeBootstrapTooltips();
  },
  
  cleanup: cleanupTooltipObserver,
});
