const MOBILE_USER_AGENT = /android|iphone|ipad|ipod|mobile|tablet|windows phone|iemobile|opera mini|blackberry|webos|silk|kindle/i;
const MODIFIER_KEYS = new Set(["Shift", "Control", "Alt", "Meta", "CapsLock"]);

export function isMobileUserAgent(
  userAgent = globalThis.navigator?.userAgent || "",
  platform = globalThis.navigator?.platform || "",
  maxTouchPoints = globalThis.navigator?.maxTouchPoints || 0,
) {
  return MOBILE_USER_AGENT.test(String(userAgent)) || (platform === "MacIntel" && maxTouchPoints > 1);
}

export function createSurfaceKeyboard(button, { onText, onKey, onFocusTarget, onBlurTarget, onError } = {}) {
  const documentRef = globalThis.document;
  if (!button || !documentRef?.createElement) return null;

  const input = documentRef.createElement("textarea");
  input.setAttribute("aria-label", "Keyboard input");
  input.autocapitalize = "off";
  input.autocomplete = "off";
  input.autocorrect = "off";
  input.spellcheck = false;
  input.tabIndex = -1;
  input.style.cssText = "position:fixed;left:0;bottom:0;width:1px;height:1px;padding:0;border:0;opacity:.01;font-size:16px;z-index:1;pointer-events:none";
  documentRef.body.append(input);

  let composing = false;
  let destroyed = false;
  let open = false;
  let blurTimer;
  let targetFocused = false;
  let targetPrepared = false;
  const reportError = (error) => {
    if (onError) onError(error);
    else globalThis.console?.warn?.("Surface keyboard input failed", error);
  };
  const dispatch = (handler, value) => {
    try {
      Promise.resolve(handler?.(value)).catch(reportError);
    } catch (error) {
      reportError(error);
    }
  };
  const updateOpen = (isOpen) => {
    open = isOpen;
    button.setAttribute("aria-pressed", String(isOpen));
    button.classList?.toggle("is-active", isOpen);
  };
  const sendText = () => {
    const text = input.value;
    if (!text) return;
    input.value = "";
    dispatch(onText, text);
  };
  const clearTarget = () => {
    if (targetPrepared) {
      try {
        onBlurTarget?.();
      } catch (error) {
        reportError(error);
      }
      targetPrepared = false;
    }
    targetFocused = false;
  };
  const close = () => {
    clearTimeout(blurTimer);
    blurTimer = undefined;
    updateOpen(false);
    clearTarget();
    input.blur();
  };
  const toggle = () => {
    if (open) {
      close();
      return;
    }
    try {
      targetPrepared = Boolean(onFocusTarget);
      targetFocused = Boolean(onFocusTarget?.());
    } catch (error) {
      reportError(error);
    }
    if (!targetFocused) input.focus({ preventScroll: true });
    updateOpen(true);
  };
  const onInput = (event) => {
    if (composing || event.isComposing) return;
    sendText();
  };
  const onKeyDown = (event) => {
    if (event.isComposing || event.key === "Dead" || event.key === "Process" || MODIFIER_KEYS.has(event.key)) return;
    if (event.key.length === 1) return;
    event.preventDefault();
    dispatch(onKey, event.key);
  };
  const onFocus = () => updateOpen(true);
  const onBlur = () => {
    clearTarget();
    if (!open) return;
    clearTimeout(blurTimer);
    blurTimer = setTimeout(() => {
      blurTimer = undefined;
      updateOpen(false);
    }, 100);
  };
  const onCompositionStart = () => {
    composing = true;
  };
  const onCompositionEnd = () => {
    composing = false;
    sendText();
  };

  input.addEventListener("input", onInput);
  input.addEventListener("keydown", onKeyDown);
  input.addEventListener("focus", onFocus);
  input.addEventListener("blur", onBlur);
  input.addEventListener("compositionstart", onCompositionStart);
  input.addEventListener("compositionend", onCompositionEnd);
  button.addEventListener("click", toggle);

  return {
    close,
    toggle,
    destroy() {
      if (destroyed) return;
      destroyed = true;
      close();
      button.removeEventListener("click", toggle);
      input.removeEventListener("input", onInput);
      input.removeEventListener("keydown", onKeyDown);
      input.removeEventListener("focus", onFocus);
      input.removeEventListener("blur", onBlur);
      input.removeEventListener("compositionstart", onCompositionStart);
      input.removeEventListener("compositionend", onCompositionEnd);
      input.remove();
    },
  };
}
