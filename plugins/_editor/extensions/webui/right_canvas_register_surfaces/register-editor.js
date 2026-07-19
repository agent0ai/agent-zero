import { store as editorStore } from "/plugins/_editor/webui/editor-store.js";

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

export default async function registerEditorSurface(surfaces) {
  surfaces.registerSurface({
    id: "editor",
    title: "Editor",
    icon: "article",
    order: 30,
    modalPath: "/plugins/_editor/webui/main.html",
    beginDockHandoff() {
      editorStore.beginSurfaceHandoff?.();
    },
    async open(payload = {}) {
      const panel = await waitForElement('[data-surface-id="editor"] .editor-panel');
      if (!panel) throw new Error("Editor surface panel did not mount.");
      await editorStore.onMount?.(panel, { mode: "canvas" });
      await editorStore.onOpen?.(payload);
    },
    async close() {
      await editorStore.cleanup?.();
    },
  });
}
