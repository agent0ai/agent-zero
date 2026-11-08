import { store as desktopStore } from "/plugins/_desktop/webui/desktop-store.js";

function waitForElement(selector, timeoutMs = 10000) {
  const found = document.querySelector(selector);
  if (found) return Promise.resolve(found);
  return new Promise((resolve) => {
    const timeout = globalThis.setTimeout(() => {
      observer.disconnect();
      resolve(document.querySelector(selector));
    }, timeoutMs);
    const observer = new MutationObserver(() => {
      const element = document.querySelector(selector);
      if (!element) return;
      globalThis.clearTimeout(timeout);
      observer.disconnect();
      resolve(element);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });
}

export default async function registerDesktopSurface(surfaces) {
  surfaces.registerSurface({
    id: "desktop",
    title: "Desktop",
    icon: "desktop_windows",
    order: 20,
    modalPath: "/plugins/_desktop/webui/main.html",
    async beginDockHandoff() {
      desktopStore.beforeDesktopHostHandoff?.();
    },
    async finishDockHandoff(payload = {}) {
      if (payload.opened !== false) desktopStore.afterDesktopHostShown?.({ source: "dock" });
    },
    async cancelDockHandoff() {
      desktopStore.cancelDesktopHostHandoff?.();
    },
    async open(payload = {}) {
      const panel = await waitForElement('[data-surface-id="desktop"] .desktop-panel');
      if (!panel) throw new Error("Desktop surface panel did not mount.");
      await desktopStore.onMount?.(panel, { mode: "canvas" });
      await desktopStore.onOpen?.(payload);
      desktopStore.afterDesktopHostShown?.({ source: payload?.source || "canvas" });
    },
    async close(payload = {}) {
      desktopStore.beforeHostHidden?.({ unloadDesktop: payload?.reason === "mobile" });
    },
  });
}
