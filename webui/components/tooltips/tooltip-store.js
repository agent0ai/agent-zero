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
  element.setAttribute("data-bs-tooltip-initialized", "true");
  new bs.Tooltip(element, {
    delay: { show: 0, hide: 0 },
    trigger: "hover focus",
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

function hideAllTooltips() {
  const Tooltip = globalThis.bootstrap?.Tooltip;
  if (!Tooltip) return;

  document
    .querySelectorAll('[data-bs-tooltip-initialized="true"]')
    .forEach((element) => {
      try {
        const instance = Tooltip.getInstance(element);
        if (instance) {
          instance.hide();
        }
      } catch (error) {
        console.warn("Error hiding tooltip:", error);
      }
    });
}

export const store = createStore("tooltips", {
  hideAll: hideAllTooltips,
  
  init() {
    initBootstrapTooltips();
    observeBootstrapTooltips();
  },
  
  cleanup: cleanupTooltipObserver,
});
