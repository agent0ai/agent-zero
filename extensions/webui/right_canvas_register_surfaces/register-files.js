import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";

function waitForElement(selector, timeoutMs = 3000) {
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

export default async function registerFilesSurface(surfaces) {
  surfaces.registerSurface({
    id: "files",
    title: "Files",
    icon: "folder",
    order: 5,
    modalPath: "modals/file-browser/file-browser.html",
    beginDockHandoff() {
      fileBrowserStore.beginSurfaceHandoff?.();
    },
    finishDockHandoff(payload = {}) {
      fileBrowserStore.finishSurfaceHandoff?.(payload);
    },
    cancelDockHandoff() {
      fileBrowserStore.cancelSurfaceHandoff?.();
    },
    async open(payload = {}) {
      const panel = await waitForElement('[data-surface-id="files"] .file-browser-root');
      if (!panel) throw new Error("Files surface panel did not mount.");
      await fileBrowserStore.openSurface(payload.path || payload.filePath || payload.directory || "");
    },
  });
}
