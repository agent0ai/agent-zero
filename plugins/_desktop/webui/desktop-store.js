import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

let frame, activeHost, canvasHost, modalHost, pending;
function park() {
  let node = document.getElementById("tuxee-keepalive");
  if (!node) {
    node = document.createElement("div");
    node.id = "tuxee-keepalive";
    node.hidden = true;
    document.body.append(node);
  }
  return node;
}
function move(host) {
  if (!frame || !host || frame.parentElement === host) return;
  if (host.moveBefore && frame.isConnected) host.moveBefore(frame, null);
  else host.append(frame);
}

export const store = createStore("desktop", {
  loading: false,
  ready: false,
  async onMount(panel, options = {}) {
    const host = panel.querySelector("[data-tuxee-host]");
    if (options.mode === "modal") modalHost = host;
    else canvasHost = host;
    if (options.mode === "modal" || !modalHost?.isConnected) {
      activeHost = host;
      move(host);
      if (options.mode === "modal") await this.onOpen();
    }
  },
  async onOpen() {
    if (frame) { move(activeHost); return; }
    if (pending) return pending;
    this.loading = true;
    pending = (async () => {
      try {
        const result = await callJsonApi("/api/plugins/_desktop/desktop_session", { action: "desktop" });
        if (!result.ok) throw new Error(result.error || "Desktop could not start");
        frame = document.createElement("iframe");
        frame.setAttribute("aria-label", "Tuxee Desktop");
        frame.src = result.url;
        frame.allow = "clipboard-read; clipboard-write; fullscreen";
        frame.style.cssText = "width:100%;height:100%;border:0;display:block";
        move(activeHost?.isConnected ? activeHost : park());
        this.ready = true;
      } catch (error) {
        globalThis.toastFrontendError?.(error.message || "Desktop could not start", "Desktop");
      } finally {
        this.loading = false;
        pending = null;
      }
    })();
    return pending;
  },
  cleanup(panel) {
    const host = panel.querySelector("[data-tuxee-host]");
    if (host === modalHost) modalHost = null;
    if (host === canvasHost) canvasHost = null;
    if (host === activeHost) { activeHost = null; move(park()); }
  },
  setDesktopHostVisible(visible) {
    if (visible && !modalHost?.isConnected && canvasHost?.isConnected) {
      activeHost = canvasHost;
      move(activeHost);
    }
  },
  beforeDesktopHostHandoff() { move(park()); },
  afterDesktopHostShown() { move(activeHost); },
  cancelDesktopHostHandoff() { move(activeHost); },
  beforeHostHidden() { move(park()); },
});
