import { store as browserStore } from "/plugins/_browser/webui/browser-store.js";

function waitForElement(selector, timeoutMs = 3000) {
  const found = document.querySelector(selector);
  if (found) return Promise.resolve(found);
  return new Promise((resolve) => {
    const timeout = globalThis.setTimeout(() => {
      observer.disconnect();
      resolve(null);
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

function nextAnimationFrame() {
  return new Promise((resolve) => {
    const schedule = globalThis.requestAnimationFrame || ((callback) => globalThis.setTimeout(callback, 16));
    schedule(() => resolve());
  });
}

function isVisibleCanvasPanel(panel) {
  if (!panel?.isConnected) return false;
  const surface = panel.closest(".browser-canvas-surface");
  const stage = panel.querySelector(".browser-stage") || panel;
  const surfaceStyle = surface ? globalThis.getComputedStyle?.(surface) : null;
  const panelStyle = globalThis.getComputedStyle?.(panel);
  if (surfaceStyle?.display === "none" || surfaceStyle?.visibility === "hidden") return false;
  if (panelStyle?.display === "none" || panelStyle?.visibility === "hidden") return false;
  const rect = stage.getBoundingClientRect?.();
  return Boolean(rect && Math.round(rect.width || 0) >= 80 && Math.round(rect.height || 0) >= 80);
}

async function waitForVisibleCanvasPanel(selector, timeoutMs = 3000) {
  const deadline = Date.now() + timeoutMs;
  let stableKey = "";
  let stableCount = 0;

  while (Date.now() <= deadline) {
    const panel = document.querySelector(selector);
    const visible = isVisibleCanvasPanel(panel);
    if (visible) {
      const stage = panel.querySelector(".browser-stage") || panel;
      const rect = stage.getBoundingClientRect();
      const key = `${Math.round(rect.width || 0)}x${Math.round(rect.height || 0)}`;
      if (key === stableKey) {
        stableCount += 1;
        if (stableCount >= 2) {
          return panel;
        }
      } else {
        stableKey = key;
        stableCount = 0;
      }
    } else {
      stableKey = "";
      stableCount = 0;
    }
    await nextAnimationFrame();
  }

  return document.querySelector(selector);
}

export default async function registerBrowserSurface(canvas) {
  canvas.registerSurface({
    id: "browser",
    title: "Browser",
    icon: "language",
    order: 10,
    modalPath: "/plugins/_browser/webui/main.html",
    beginDockHandoff() {
      browserStore.beginSurfaceHandoff?.();
    },
    finishDockHandoff() {
      browserStore.finishSurfaceHandoff?.();
    },
    cancelDockHandoff() {
      browserStore.cancelSurfaceHandoff?.();
    },
    sendKeyboardInput(input) {
      return browserStore.sendSurfaceKeyboardInput?.(input);
    },
    async open(payload = {}) {
      await waitForElement('[data-surface-id="browser"] .browser-panel');
      const panel = await waitForVisibleCanvasPanel('[data-surface-id="browser"] .browser-panel');
      const browser = browserStore;
      if (panel && browser?.onOpen) {
        await browser.onOpen(panel, {
          mode: "canvas",
          browserId: payload.browserId || payload.browser_id || null,
          contextId: payload.contextId || payload.context_id || null,
        });
      }
    },
    async close() {
      await browserStore.cleanup?.();
    },
  });
}
