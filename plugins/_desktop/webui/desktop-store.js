import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

let frame, activeHost, canvasHost, modalHost, pending;
let keyboardDocument, keyboardTarget;
let needsReload = false, handingOff = false;

function isKeyboardTarget(target, documentRef) {
  return target?.tagName === "CANVAS" && target.ownerDocument === documentRef;
}

function trackKeyboardTarget(event) {
  const documentRef = keyboardDocument;
  if (isKeyboardTarget(event.target, documentRef)) keyboardTarget = event.target;
}

function attachKeyboardTarget() {
  getKeyboardTarget();
}

function getKeyboardTarget() {
  try {
    const documentRef = frame?.contentDocument || null;
    if (!documentRef) return null;
    if (keyboardDocument !== documentRef) {
      keyboardDocument?.removeEventListener("focusin", trackKeyboardTarget, true);
      keyboardDocument = documentRef;
      keyboardTarget = null;
      keyboardDocument.addEventListener("focusin", trackKeyboardTarget, true);
    }
    if (isKeyboardTarget(keyboardDocument.activeElement, keyboardDocument)) {
      keyboardTarget = keyboardDocument.activeElement;
    }
    if (!isKeyboardTarget(keyboardTarget, keyboardDocument) || !keyboardTarget.isConnected) {
      keyboardTarget = keyboardDocument.querySelector?.("canvas") || null;
    }
    return isKeyboardTarget(keyboardTarget, keyboardDocument) && keyboardTarget.isConnected ? keyboardTarget : null;
  } catch (error) {
    globalThis.console?.warn?.("Desktop keyboard target is unavailable", error);
    return null;
  }
}

function keyboardCode(key) {
  if (/^[a-z]$/i.test(key)) return `Key${key.toUpperCase()}`;
  if (/^[0-9]$/.test(key)) return `Digit${key}`;
  return ({
    " ": "Space",
    Alt: "AltLeft",
    ArrowDown: "ArrowDown",
    ArrowLeft: "ArrowLeft",
    ArrowRight: "ArrowRight",
    ArrowUp: "ArrowUp",
    Backspace: "Backspace",
    CapsLock: "CapsLock",
    Control: "ControlLeft",
    Delete: "Delete",
    End: "End",
    Enter: "Enter",
    Escape: "Escape",
    Home: "Home",
    Insert: "Insert",
    Meta: "MetaLeft",
    PageDown: "PageDown",
    PageUp: "PageUp",
    Shift: "ShiftLeft",
    Tab: "Tab",
  })[key] || "Unidentified";
}

function dispatchKeyboardEvent(target, type, key) {
  const KeyboardEventConstructor = target.ownerDocument?.defaultView?.KeyboardEvent || globalThis.KeyboardEvent;
  if (!KeyboardEventConstructor) return;
  target.dispatchEvent(new KeyboardEventConstructor(type, {
    key,
    code: keyboardCode(key),
    bubbles: true,
    cancelable: true,
  }));
}

function dispatchKeyboardText(target, text) {
  if (target.matches?.("input, textarea")) {
    try {
      const start = target.selectionStart ?? target.value.length;
      const end = target.selectionEnd ?? start;
      target.setRangeText(text, start, end, "end");
    } catch {
      target.value = `${target.value || ""}${text}`;
    }
    const InputEventConstructor = target.ownerDocument?.defaultView?.InputEvent || globalThis.InputEvent;
    if (InputEventConstructor) target.dispatchEvent(new InputEventConstructor("input", { data: text, inputType: "insertText", bubbles: true }));
    return;
  }
  for (const character of text.replace(/\r\n?/g, "\n")) {
    const key = character === "\n" ? "Enter" : character;
    dispatchKeyboardEvent(target, "keydown", key);
    dispatchKeyboardEvent(target, "keyup", key);
  }
}

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
    if (frame) {
      if (needsReload) {
        this.loading = true;
        frame.style.visibility = "hidden";
        frame.src = frame.src;
      }
      needsReload = false;
      move(activeHost);
      return;
    }
    if (pending) return pending;
    needsReload = false;
    this.loading = true;
    pending = (async () => {
      try {
        const result = await callJsonApi("/api/plugins/_desktop/desktop_session", { action: "desktop" });
        if (!result.ok) throw new Error(result.error || "Desktop could not start");
        frame = document.createElement("iframe");
        frame.setAttribute("aria-label", "Tuxee Desktop");
        frame.src = result.url + "?a0_open=1";
        frame.allow = "clipboard-read; clipboard-write; fullscreen";
        frame.style.cssText = "width:100%;height:100%;border:0;display:block";
        frame.style.visibility = "hidden";
        frame.onload = () => {
          this.loading = false;
          frame.style.visibility = "";
          attachKeyboardTarget();
        };
        move(activeHost?.isConnected ? activeHost : park());
        this.ready = true;
      } catch (error) {
        globalThis.toastFrontendError?.(error.message || "Desktop could not start", "Desktop");
      } finally {
        if (!frame) this.loading = false;
        pending = null;
      }
    })();
    return pending;
  },
  blurKeyboardTarget() {
    const target = getKeyboardTarget();
    if (keyboardDocument?.activeElement === target) target.blur?.();
  },
  sendKeyboardInput({ key = "", text = "" } = {}) {
    const target = getKeyboardTarget();
    if (!target) return false;
    if (text) dispatchKeyboardText(target, String(text));
    else if (key) {
      dispatchKeyboardEvent(target, "keydown", String(key));
      dispatchKeyboardEvent(target, "keyup", String(key));
    }
    return Boolean(text || key);
  },
  cleanup(panel) {
    const host = panel.querySelector("[data-tuxee-host]");
    if (host === modalHost) modalHost = null;
    if (host === canvasHost) canvasHost = null;
    if (host === activeHost) { this.beforeHostHidden(); activeHost = null; }
  },
  setDesktopHostVisible(visible) {
    if (visible && !modalHost?.isConnected && canvasHost?.isConnected) {
      activeHost = canvasHost;
      move(activeHost);
    } else if (!visible && activeHost === canvasHost && !modalHost?.isConnected) {
      this.beforeHostHidden();
    }
  },
  beforeDesktopHostHandoff() { handingOff = true; move(park()); },
  afterDesktopHostShown() { handingOff = false; move(activeHost); },
  cancelDesktopHostHandoff() { handingOff = false; move(activeHost); },
  beforeHostHidden() {
    if (!handingOff) needsReload = true;
    move(park());
  },
});
