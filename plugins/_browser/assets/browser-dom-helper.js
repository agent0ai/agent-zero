(() => {
  const DOM_HELPER_CHANNEL = "a0.browser.dom_helper";
  const DOM_HELPER_KEY = "__spaceBrowserDomHelper__";
  const VERSION = "1";
  const REQUEST_TIMEOUT_MS = 800;

  if (globalThis[DOM_HELPER_KEY]?.version === VERSION) {
    return;
  }

  const INTERACTIVE_ROLES = new Set([
    "button",
    "checkbox",
    "combobox",
    "link",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "option",
    "radio",
    "searchbox",
    "slider",
    "spinbutton",
    "switch",
    "tab",
    "textbox"
  ]);
  const STRUCTURAL_ROLES = new Set([
    "alertdialog",
    "article",
    "banner",
    "complementary",
    "contentinfo",
    "dialog",
    "document",
    "form",
    "group",
    "main",
    "navigation",
    "none",
    "presentation",
    "region"
  ]);
  const INTERACTIVE_EVENT_NAMES = new Set([
    "auxclick",
    "change",
    "click",
    "contextmenu",
    "dblclick",
    "input",
    "keydown",
    "keypress",
    "keyup",
    "mousedown",
    "mouseup",
    "pointerdown",
    "pointerup",
    "submit",
    "touchend",
    "touchstart"
  ]);
  const INTERACTIVE_EVENT_PROPERTIES = [...INTERACTIVE_EVENT_NAMES]
    .map((eventName) => `on${eventName}`);
  const SKIP_TAGS = new Set([
    "HEAD",
    "LINK",
    "META",
    "NOSCRIPT",
    "SCRIPT",
    "STYLE",
    "TEMPLATE"
  ]);
  const VOID_TAGS = new Set([
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr"
  ]);

  const childFramesById = new Map();
  const elementsByNodeId = new Map();
  const nodeIdsByElement = new WeakMap();
  const pendingRequests = new Map();
  const helperFrameId = typeof globalThis.crypto?.randomUUID === "function"
    ? globalThis.crypto.randomUUID()
    : `a0-browser-frame-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  let nextNodeId = 1;
  let nextRequestId = 1;

  function patchOpenShadowDom() {
    const original = globalThis.Element?.prototype?.attachShadow;
    if (!original || original.__a0BrowserDomHelperOpenShadowPatch) {
      return;
    }
    const patched = function attachShadow(options) {
      return original.call(this, { ...(options || {}), mode: "open" });
    };
    patched.__a0BrowserDomHelperOpenShadowPatch = true;
    globalThis.Element.prototype.attachShadow = patched;
  }

  patchOpenShadowDom();

  function createNamedError(name, message, details = {}) {
    const error = new Error(message);
    error.name = name;
    Object.assign(error, details);
    return error;
  }

  function normalizeText(value) {
    return String(value ?? "").replace(/\s+/gu, " ").trim();
  }

  function normalizeAttributeText(value) {
    return normalizeText(value).slice(0, 160);
  }

  function truncateText(value, maxLength = 120) {
    const normalizedValue = normalizeText(value);
    if (normalizedValue.length <= maxLength) {
      return normalizedValue;
    }
    return `${normalizedValue.slice(0, Math.max(0, maxLength - 1)).trimEnd()}...`;
  }

  function escapeHtmlText(value) {
    return String(value ?? "")
      .replace(/&/gu, "&amp;")
      .replace(/</gu, "&lt;")
      .replace(/>/gu, "&gt;");
  }

  function escapeHtmlAttribute(value) {
    return escapeHtmlText(value)
      .replace(/"/gu, "&quot;")
      .replace(/'/gu, "&#39;");
  }

  function isElementNode(value) {
    return Boolean(value && value.nodeType === 1);
  }

  function isTextNode(value) {
    return Boolean(value && value.nodeType === 3);
  }

  function getTagName(element) {
    return String(element?.tagName || "").toUpperCase();
  }

  function getAttributeNamesSafe(element) {
    try {
      if (typeof element?.getAttributeNames === "function") {
        return element.getAttributeNames();
      }
      return [...(element?.attributes || [])]
        .map((attribute) => String(attribute?.name || "").trim())
        .filter(Boolean);
    } catch {
      return [];
    }
  }

  function getComputedStyleSafe(element) {
    try {
      return globalThis.getComputedStyle?.(element) || null;
    } catch {
      return null;
    }
  }

  function isStyleDeclarationHidden(styleValue) {
    const normalizedStyleValue = String(styleValue || "")
      .toLowerCase()
      .replace(/\s+/gu, "");
    if (!normalizedStyleValue) {
      return false;
    }
    return /(?:^|;)display:none(?:;|$)/u.test(normalizedStyleValue)
      || /(?:^|;)visibility:hidden(?:;|$)/u.test(normalizedStyleValue)
      || /(?:^|;)visibility:collapse(?:;|$)/u.test(normalizedStyleValue)
      || /(?:^|;)content-visibility:hidden(?:;|$)/u.test(normalizedStyleValue)
      || /(?:^|;)opacity:0(?:\.0+)?(?:;|$)/u.test(normalizedStyleValue);
  }

  function isComputedStyleHidden(computedStyle) {
    if (!computedStyle) {
      return false;
    }
    const display = normalizeText(computedStyle.display).toLowerCase();
    const visibility = normalizeText(computedStyle.visibility).toLowerCase();
    const contentVisibility = normalizeText(computedStyle.contentVisibility).toLowerCase();
    const opacity = Number(computedStyle.opacity || 1);
    return display === "none"
      || visibility === "hidden"
      || visibility === "collapse"
      || contentVisibility === "hidden"
      || opacity <= 0;
  }

  function isEffectivelyHiddenByAncestor(element) {
    let current = element;
    while (isElementNode(current)) {
      if (current.hidden || current.getAttribute?.("aria-hidden") === "true") {
        return true;
      }
      if (isStyleDeclarationHidden(current.getAttribute?.("style"))) {
        return true;
      }
      if (isComputedStyleHidden(getComputedStyleSafe(current))) {
        return true;
      }
      current = current.parentElement;
    }
    return false;
  }

  function isHiddenElement(element) {
    if (!isElementNode(element)) {
      return true;
    }
    const tagName = getTagName(element);
    if (SKIP_TAGS.has(tagName)) {
      return true;
    }
    if (element.hidden || element.getAttribute?.("aria-hidden") === "true") {
      return true;
    }
    if (tagName === "INPUT" && String(element.getAttribute?.("type") || "").toLowerCase() === "hidden") {
      return true;
    }
    if (isStyleDeclarationHidden(element.getAttribute?.("style"))) {
      return true;
    }
    if (isComputedStyleHidden(getComputedStyleSafe(element))) {
      return true;
    }
    return isEffectivelyHiddenByAncestor(element.parentElement);
  }

  function normalizeInteractiveEventName(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .split(/[.:]/u, 1)[0];
  }

  function isGlobalOrDelegatedEventBinding(value) {
    const parts = String(value || "")
      .trim()
      .toLowerCase()
      .split(/[.:]/u)
      .map((part) => part.trim())
      .filter(Boolean);
    return parts.includes("window")
      || parts.includes("document")
      || parts.includes("outside")
      || parts.includes("away");
  }

  function isInteractiveEventName(value) {
    return INTERACTIVE_EVENT_NAMES.has(normalizeInteractiveEventName(value));
  }

  function isInteractiveEventAttributeName(attributeName) {
    const normalizedName = String(attributeName || "").trim().toLowerCase();
    if (!normalizedName) {
      return false;
    }
    if (normalizedName.startsWith("@")) {
      return !isGlobalOrDelegatedEventBinding(normalizedName.slice(1))
        && isInteractiveEventName(normalizedName.slice(1));
    }
    if (normalizedName.startsWith("x-on:") || normalizedName.startsWith("v-on:")) {
      return !isGlobalOrDelegatedEventBinding(normalizedName.slice(5))
        && isInteractiveEventName(normalizedName.slice(5));
    }
    if (normalizedName.startsWith("ng-")) {
      return isInteractiveEventName(normalizedName.slice(3));
    }
    if (normalizedName.startsWith("on") && normalizedName.length > 2) {
      return isInteractiveEventName(normalizedName.slice(2));
    }
    return false;
  }

  function hasInteractiveEventHandlerAttribute(element) {
    return getAttributeNamesSafe(element).some((attributeName) => {
      return isInteractiveEventAttributeName(attributeName);
    });
  }

  function hasInteractiveEventHandlerProperty(element) {
    return INTERACTIVE_EVENT_PROPERTIES.some((propertyName) => {
      return typeof element?.[propertyName] === "function";
    });
  }

  function hasInteractiveEventHandler(element) {
    return hasInteractiveEventHandlerAttribute(element) || hasInteractiveEventHandlerProperty(element);
  }

  function isActionableElement(element) {
    if (!isElementNode(element) || isHiddenElement(element)) {
      return false;
    }
    const tagName = getTagName(element);
    if (tagName === "A" && element.hasAttribute?.("href")) {
      return true;
    }
    if (tagName === "IMG") {
      return true;
    }
    if (["BUTTON", "INPUT", "SELECT", "TEXTAREA", "SUMMARY"].includes(tagName)) {
      return true;
    }
    if (String(element.getAttribute?.("contenteditable") || "").toLowerCase() === "true") {
      return true;
    }
    const role = String(element.getAttribute?.("role") || "").trim().toLowerCase();
    if (INTERACTIVE_ROLES.has(role)) {
      return true;
    }
    if (STRUCTURAL_ROLES.has(role)) {
      return false;
    }
    if (hasInteractiveEventHandlerAttribute(element)) {
      return true;
    }
    return hasInteractiveEventHandlerProperty(element) && Boolean(normalizeText(element.textContent || ""));
  }

  function normalizeFrameChain(frameChain) {
    const rawFrameChain = Array.isArray(frameChain)
      ? frameChain
      : typeof frameChain === "string"
        ? frameChain.split(">")
        : [];
    return rawFrameChain
      .map((entry) => String(entry || "").trim())
      .filter(Boolean);
  }

  function encodeFrameChain(frameChain) {
    return normalizeFrameChain(frameChain).join(">");
  }

  function ensureNodeId(element) {
    if (nodeIdsByElement.has(element)) {
      return nodeIdsByElement.get(element);
    }
    const nodeId = String(nextNodeId++);
    nodeIdsByElement.set(element, nodeId);
    elementsByNodeId.set(nodeId, element);
    return nodeId;
  }

  function normalizeSnapshotMode(value) {
    return String(value || "").trim().toLowerCase() || "dom";
  }

  function isContentSnapshotMode(payload = {}) {
    return normalizeSnapshotMode(payload?.snapshotMode) === "content";
  }

  function normalizeSelectorList(payload = {}) {
    const rawSelectors = typeof payload === "string"
      ? [payload]
      : Array.isArray(payload?.selectors)
        ? payload.selectors
        : typeof payload?.selectors === "string"
          ? [payload.selectors]
          : Array.isArray(payload?.selector)
            ? payload.selector
            : typeof payload?.selector === "string"
              ? [payload.selector]
              : [];
    return rawSelectors.map((selector) => String(selector || "").trim()).filter(Boolean);
  }

  function getReferenceValueMetadata(element) {
    const tagName = getTagName(element);
    if (tagName === "INPUT") {
      const inputType = String(element.getAttribute?.("type") || element.type || "text").toLowerCase();
      if (inputType === "password") {
        return "";
      }
      if (["checkbox", "radio"].includes(inputType)) {
        return element.checked ? "checked" : "unchecked";
      }
      return truncateText(element.value || element.getAttribute?.("value") || "", 96);
    }
    if (tagName === "TEXTAREA") {
      return truncateText(element.value || "", 96);
    }
    if (tagName === "SELECT") {
      return [...(element.selectedOptions || [])]
        .map((option) => truncateText(option.textContent || option.label || option.value || "", 48))
        .filter(Boolean)
        .join(" | ");
    }
    if (String(element.getAttribute?.("contenteditable") || "").toLowerCase() === "true") {
      return truncateText(element.textContent || "", 96);
    }
    return "";
  }

  function collectElementStateMetadata(element) {
    if (!isElementNode(element)) {
      return {
        descriptorTags: [],
        semanticTags: [],
        stateTags: []
      };
    }
    const tagName = getTagName(element);
    const computedStyle = getComputedStyleSafe(element);
    const ariaDisabled = String(element.getAttribute?.("aria-disabled") || "").trim().toLowerCase() === "true";
    const ariaChecked = String(element.getAttribute?.("aria-checked") || "").trim().toLowerCase() === "true";
    const ariaExpanded = String(element.getAttribute?.("aria-expanded") || "").trim().toLowerCase() === "true";
    const ariaInvalid = String(element.getAttribute?.("aria-invalid") || "").trim().toLowerCase() === "true";
    const ariaPressed = String(element.getAttribute?.("aria-pressed") || "").trim().toLowerCase() === "true";
    const ariaReadonly = String(element.getAttribute?.("aria-readonly") || "").trim().toLowerCase() === "true";
    const ariaRequired = String(element.getAttribute?.("aria-required") || "").trim().toLowerCase() === "true";
    const ariaSelected = String(element.getAttribute?.("aria-selected") || "").trim().toLowerCase() === "true";
    const disabled = Boolean(element.disabled || ariaDisabled || element.closest?.("[inert]"));
    const checked = Boolean(element.checked || ariaChecked);
    const selected = tagName === "OPTION" ? Boolean(element.selected) : ariaSelected;
    const invalid = Boolean(ariaInvalid || element.matches?.(":invalid"));
    const readonly = Boolean(element.readOnly || ariaReadonly);
    const required = Boolean(element.required || ariaRequired);
    const blocked = !disabled && normalizeText(computedStyle?.pointerEvents || "").toLowerCase() === "none";
    const stateTags = [
      disabled ? "disabled" : "",
      blocked ? "blocked" : "",
      checked ? "checked" : "",
      selected && tagName !== "SELECT" ? "selected" : "",
      invalid ? "invalid" : "",
      ariaExpanded ? "expanded" : "",
      ariaPressed ? "pressed" : ""
    ].filter(Boolean);
    return {
      blocked,
      checked,
      descriptorTags: stateTags.slice(),
      disabled,
      expanded: ariaExpanded,
      invalid,
      pointerEventsNone: blocked,
      pressed: ariaPressed,
      readonly,
      required,
      selected,
      semanticTags: [],
      stateTags,
      visible: !isHiddenElement(element)
    };
  }

  function serializeAttributes(element, frameChain) {
    const serializedAttributes = [];
    const helperManagedAttributes = new Set([
      "data-space-browser-node-id",
      "data-space-browser-frame-id",
      "data-space-browser-frame-chain",
      "data-space-browser-state-tags",
      "data-space-browser-semantic-tags",
      "data-space-browser-descriptor-tags",
      "data-space-browser-live-value",
      "data-space-browser-selected-text"
    ]);
    try {
      [...(element?.attributes || [])].forEach((attribute) => {
        const name = String(attribute?.name || "").trim();
        if (!name || helperManagedAttributes.has(name)) {
          return;
        }
        serializedAttributes.push(` ${name}="${escapeHtmlAttribute(attribute?.value || "")}"`);
      });
    } catch {
      // Attribute reads are best effort across unusual DOM nodes.
    }

    if (isActionableElement(element)) {
      const stateMetadata = collectElementStateMetadata(element);
      const liveValue = getReferenceValueMetadata(element);
      serializedAttributes.push(` data-space-browser-node-id="${escapeHtmlAttribute(ensureNodeId(element))}"`);
      serializedAttributes.push(` data-space-browser-frame-id="${escapeHtmlAttribute(helperFrameId)}"`);
      serializedAttributes.push(` data-space-browser-frame-chain="${escapeHtmlAttribute(encodeFrameChain(frameChain))}"`);
      if (stateMetadata.stateTags.length) {
        serializedAttributes.push(` data-space-browser-state-tags="${escapeHtmlAttribute(stateMetadata.stateTags.join(" "))}"`);
      }
      if (stateMetadata.semanticTags.length) {
        serializedAttributes.push(` data-space-browser-semantic-tags="${escapeHtmlAttribute(stateMetadata.semanticTags.join(" "))}"`);
      }
      if (stateMetadata.descriptorTags.length) {
        serializedAttributes.push(` data-space-browser-descriptor-tags="${escapeHtmlAttribute(stateMetadata.descriptorTags.join(" "))}"`);
      }
      if (liveValue) {
        serializedAttributes.push(` data-space-browser-live-value="${escapeHtmlAttribute(liveValue)}"`);
        if (getTagName(element) === "SELECT") {
          serializedAttributes.push(` data-space-browser-selected-text="${escapeHtmlAttribute(liveValue)}"`);
        }
      }
    }
    return serializedAttributes.join("");
  }

  function isFrameLikeElement(element) {
    return ["IFRAME", "FRAME", "OBJECT", "EMBED"].includes(getTagName(element));
  }

  function createRequestId() {
    nextRequestId += 1;
    return `a0-browser-dom-${Date.now()}-${nextRequestId}-${Math.random().toString(16).slice(2)}`;
  }

  function resolveElementWindow(element) {
    try {
      return element?.contentWindow || null;
    } catch {
      return null;
    }
  }

  function requestChildFrameOperation(targetWindow, type, payload = {}, frameElement = null) {
    if (!targetWindow || typeof targetWindow.postMessage !== "function") {
      throw createNamedError(
        "BrowserDomHelperFrameUnavailableError",
        "Embedded frame window is unavailable.",
        {
          code: "browser_dom_helper_frame_window_unavailable",
          details: { frameElementTag: getTagName(frameElement).toLowerCase() }
        }
      );
    }
    return new Promise((resolve, reject) => {
      const requestId = createRequestId();
      const timer = globalThis.setTimeout(() => {
        pendingRequests.delete(requestId);
        reject(createNamedError(
          "BrowserDomHelperFrameTimeoutError",
          `Embedded frame request "${type}" timed out.`,
          { code: "browser_dom_helper_frame_timeout", details: { type } }
        ));
      }, REQUEST_TIMEOUT_MS);
      pendingRequests.set(requestId, { reject, resolve, timer, type });
      try {
        targetWindow.postMessage({
          channel: DOM_HELPER_CHANNEL,
          payload,
          requestId,
          type
        }, "*");
      } catch (error) {
        globalThis.clearTimeout(timer);
        pendingRequests.delete(requestId);
        reject(createNamedError(
          "BrowserDomHelperFrameRequestError",
          `Embedded frame request "${type}" could not be posted.`,
          { cause: error, code: "browser_dom_helper_frame_postmessage_failed", details: { type } }
        ));
      }
    });
  }

  function registerChildFrame(frameId, targetWindow) {
    const normalizedFrameId = String(frameId || "").trim();
    if (normalizedFrameId && targetWindow && typeof targetWindow.postMessage === "function") {
      childFramesById.set(normalizedFrameId, targetWindow);
    }
  }

  function extractDocumentBodyHtml(html) {
    const normalizedHtml = String(html || "").trim();
    if (!normalizedHtml) {
      return "";
    }
    try {
      if (typeof DOMParser === "function") {
        const parsedDocument = new DOMParser().parseFromString(normalizedHtml, "text/html");
        return String(parsedDocument.body?.innerHTML || normalizedHtml).trim();
      }
    } catch {
      // Fall through to the raw snapshot.
    }
    return normalizedHtml.replace(/<!doctype[\s\S]*?>/iu, "").trim();
  }

  async function captureFrameElement(frameElement, frameChain, payload = {}) {
    const childWindow = resolveElementWindow(frameElement);
    const childPayload = {
      snapshotMode: normalizeSnapshotMode(payload?.snapshotMode),
      parentFrameChain: frameChain
    };
    if (!childWindow) {
      return {
        frameChain: [],
        frameId: "",
        html: escapeHtmlText("Embedded frame snapshot unavailable."),
        message: "Embedded frame snapshot unavailable.",
        ok: false,
        status: "window_unavailable",
        title: "",
        url: String(frameElement?.getAttribute?.("src") || "").trim()
      };
    }

    try {
      const snapshot = await requestChildFrameOperation(childWindow, "capture_document", childPayload, frameElement);
      registerChildFrame(snapshot?.frameId, childWindow);
      return snapshot;
    } catch (error) {
      try {
        const frameDocument = frameElement?.contentDocument;
        if (frameDocument) {
          const currentFrameChain = normalizeFrameChain(frameChain);
          return {
            frameChain: currentFrameChain,
            frameId: helperFrameId,
            html: await serializeDocumentNode(frameDocument, currentFrameChain, childPayload),
            ok: true,
            title: String(frameDocument.title || "").trim(),
            url: String(childWindow.location?.href || frameElement?.src || "").trim()
          };
        }
      } catch {
        // Cross-origin frames stay best effort and report the postMessage failure below.
      }
      return {
        frameChain: normalizeFrameChain(frameChain),
        frameId: "",
        html: escapeHtmlText(String(error?.message || "Embedded frame snapshot unavailable.")),
        message: String(error?.message || "Embedded frame snapshot unavailable."),
        ok: false,
        status: String(error?.code || "capture_failed"),
        title: String(frameElement?.getAttribute?.("title") || "").trim(),
        url: String(frameElement?.getAttribute?.("src") || frameElement?.src || "").trim()
      };
    }
  }

  function renderFrameDocument(snapshot, frameElement, payload = {}) {
    const normalizedSnapshot = snapshot && typeof snapshot === "object" ? snapshot : {};
    const content = String(
      normalizedSnapshot.html
      || escapeHtmlText(normalizedSnapshot.message || "Embedded frame snapshot unavailable.")
    );
    if (isContentSnapshotMode(payload)) {
      return normalizedSnapshot.ok === false ? "" : extractDocumentBodyHtml(content);
    }
    return `<space-browser-frame-document`
      + ` data-space-browser-frame-id="${escapeHtmlAttribute(normalizedSnapshot.frameId || "")}"`
      + ` data-space-browser-frame-chain="${escapeHtmlAttribute(encodeFrameChain(normalizedSnapshot.frameChain))}"`
      + ` data-space-browser-status="${escapeHtmlAttribute(normalizedSnapshot.ok === false ? normalizedSnapshot.status || "error" : "ok")}"`
      + ` data-space-browser-frame-url="${escapeHtmlAttribute(normalizedSnapshot.url || frameElement?.src || "")}"`
      + ` data-space-browser-frame-title="${escapeHtmlAttribute(normalizedSnapshot.title || frameElement?.getAttribute?.("title") || "")}">`
      + content
      + `</space-browser-frame-document>`;
  }

  async function serializeChildNodes(parentNode, frameChain, payload = {}) {
    const parts = [];
    for (const childNode of Array.from(parentNode?.childNodes || [])) {
      parts.push(await serializeNode(childNode, frameChain, payload));
    }
    return parts.join("");
  }

  async function serializeElementNode(element, frameChain, payload = {}) {
    const tagName = String(element?.tagName || "").toLowerCase();
    if (!tagName) {
      return "";
    }
    if (isContentSnapshotMode(payload) && isHiddenElement(element)) {
      return "";
    }
    const openTag = `<${tagName}${serializeAttributes(element, frameChain)}>`;
    const lightDom = await serializeChildNodes(element, frameChain, payload);
    let shadowDom = "";
    try {
      const shadowRoot = element?.shadowRoot;
      if (shadowRoot) {
        const shadowInnerHtml = await serializeChildNodes(shadowRoot, frameChain, payload);
        shadowDom = isContentSnapshotMode(payload)
          ? shadowInnerHtml
          : `<space-browser-shadow-root>${shadowInnerHtml}</space-browser-shadow-root>`;
      }
    } catch {
      shadowDom = "";
    }
    let frameDom = "";
    if (isFrameLikeElement(element)) {
      frameDom = renderFrameDocument(
        await captureFrameElement(element, frameChain, payload),
        element,
        payload
      );
      if (isContentSnapshotMode(payload)) {
        return frameDom;
      }
    }
    if (VOID_TAGS.has(tagName)) {
      return `${openTag}${shadowDom}${frameDom}`;
    }
    return `${openTag}${lightDom}${shadowDom}${frameDom}</${tagName}>`;
  }

  async function serializeNode(node, frameChain, payload = {}) {
    if (!node || typeof node.nodeType !== "number") {
      return "";
    }
    if (node.nodeType === 9) {
      return serializeDocumentNode(node, frameChain, payload);
    }
    if (node.nodeType === 11) {
      return serializeChildNodes(node, frameChain, payload);
    }
    if (node.nodeType === 1) {
      return serializeElementNode(node, frameChain, payload);
    }
    if (node.nodeType === 3) {
      return escapeHtmlText(node.textContent || "");
    }
    if (node.nodeType === 8 && !isContentSnapshotMode(payload)) {
      return `<!--${escapeHtmlText(node.data || "")}-->`;
    }
    return "";
  }

  async function serializeDocumentNode(doc, frameChain, payload = {}) {
    return serializeChildNodes(doc, frameChain, payload);
  }

  async function serializeSelectorTargets(doc, selectors, frameChain, payload = {}) {
    const targets = {};
    for (const selector of selectors) {
      let elements = [];
      try {
        elements = [...(doc?.querySelectorAll?.(selector) || [])];
      } catch (error) {
        throw createNamedError(
          "BrowserDomHelperSelectorError",
          `Browser DOM helper could not resolve selector "${selector}".`,
          { cause: error, code: "browser_dom_helper_selector_error", details: { selector } }
        );
      }
      const parts = [];
      for (const element of elements) {
        parts.push(await serializeNode(element, frameChain, payload));
      }
      targets[selector] = parts.join("");
    }
    return targets;
  }

  async function captureDocument(payload = {}) {
    childFramesById.clear();
    const currentFrameChain = normalizeFrameChain(payload?.parentFrameChain).concat(helperFrameId);
    const selectors = normalizeSelectorList(payload);
    const documentSnapshot = {
      frameChain: currentFrameChain,
      frameId: helperFrameId,
      ok: true,
      title: String(globalThis.document?.title || "").trim(),
      url: String(globalThis.location?.href || "").trim()
    };
    if (selectors.length) {
      return {
        ...documentSnapshot,
        targets: await serializeSelectorTargets(globalThis.document, selectors, currentFrameChain, payload)
      };
    }
    return {
      ...documentSnapshot,
      html: await serializeDocumentNode(globalThis.document, currentFrameChain, payload)
    };
  }

  function getElementByNodeId(nodeId, actionLabel) {
    const normalizedNodeId = String(nodeId || "").trim();
    if (!normalizedNodeId) {
      throw createNamedError(
        "BrowserDomHelperReferenceError",
        `Browser DOM helper ${actionLabel} requires a node id.`,
        { code: "browser_dom_helper_node_required", details: { action: actionLabel } }
      );
    }
    const element = elementsByNodeId.get(normalizedNodeId);
    if (!element) {
      throw createNamedError(
        "BrowserDomHelperReferenceError",
        `Browser DOM helper could not find node "${normalizedNodeId}".`,
        { code: "browser_dom_helper_node_not_found", details: { action: actionLabel, nodeId: normalizedNodeId } }
      );
    }
    if (element.isConnected === false) {
      throw createNamedError(
        "BrowserDomHelperReferenceError",
        `Browser DOM helper node "${normalizedNodeId}" is no longer connected.`,
        { code: "browser_dom_helper_node_disconnected", details: { action: actionLabel, nodeId: normalizedNodeId } }
      );
    }
    return element;
  }

  function serializeElementSnapshot(element) {
    if (!isElementNode(element)) {
      return "";
    }
    try {
      if (typeof element.outerHTML === "string" && element.outerHTML) {
        return element.outerHTML;
      }
    } catch {
      // Fall through.
    }
    return "";
  }

  function scrollElementIntoView(element) {
    try {
      element.scrollIntoView?.({ behavior: "auto", block: "center", inline: "center" });
      return true;
    } catch {
      return false;
    }
  }

  function focusElement(element) {
    try {
      element.focus?.({ preventScroll: true });
      return true;
    } catch {
      try {
        element.focus?.();
        return true;
      } catch {
        return false;
      }
    }
  }

  function dispatchDomEvent(target, eventName, EventType = "Event", options = {}) {
    const EventConstructor = typeof globalThis[EventType] === "function"
      ? globalThis[EventType]
      : globalThis.Event;
    const event = new EventConstructor(eventName, {
      bubbles: true,
      cancelable: true,
      composed: true,
      ...options
    });
    target.dispatchEvent(event);
    return event;
  }

  function dispatchKeyboardEvent(target, eventName, options = {}) {
    const KeyboardEventConstructor = typeof globalThis.KeyboardEvent === "function"
      ? globalThis.KeyboardEvent
      : globalThis.Event;
    const event = new KeyboardEventConstructor(eventName, {
      bubbles: true,
      cancelable: true,
      composed: true,
      code: "Enter",
      key: "Enter",
      keyCode: 13,
      which: 13,
      ...options
    });
    target.dispatchEvent(event);
    return event;
  }

  function setNativeValue(element, nextValue) {
    const tagName = getTagName(element);
    const normalizedValue = String(nextValue ?? "");
    if (tagName === "INPUT") {
      const descriptor = Object.getOwnPropertyDescriptor(globalThis.HTMLInputElement?.prototype || {}, "value");
      if (typeof descriptor?.set === "function") {
        descriptor.set.call(element, normalizedValue);
      } else {
        element.value = normalizedValue;
      }
      return normalizedValue;
    }
    if (tagName === "TEXTAREA") {
      const descriptor = Object.getOwnPropertyDescriptor(globalThis.HTMLTextAreaElement?.prototype || {}, "value");
      if (typeof descriptor?.set === "function") {
        descriptor.set.call(element, normalizedValue);
      } else {
        element.value = normalizedValue;
      }
      return normalizedValue;
    }
    if (tagName === "SELECT") {
      element.value = normalizedValue;
      return element.value;
    }
    if (String(element.getAttribute?.("contenteditable") || "").toLowerCase() === "true") {
      element.textContent = normalizedValue;
      return normalizedValue;
    }
    throw createNamedError(
      "BrowserDomHelperActionError",
      `Browser DOM helper cannot type into <${getTagName(element).toLowerCase()}>.`,
      { code: "browser_dom_helper_type_unsupported" }
    );
  }

  function delayMs(timeoutMs) {
    return new Promise((resolve) => {
      globalThis.setTimeout(resolve, Math.max(0, Number(timeoutMs) || 0));
    });
  }

  function describeActiveElement(element) {
    if (!isElementNode(element)) {
      return "";
    }
    return [
      getTagName(element).toLowerCase(),
      normalizeAttributeText(element.getAttribute?.("id")) ? `#${normalizeAttributeText(element.getAttribute?.("id"))}` : "",
      normalizeAttributeText(element.getAttribute?.("name")) ? `name=${normalizeAttributeText(element.getAttribute?.("name"))}` : ""
    ].filter(Boolean).join(" ");
  }

  function getActionObservationRoot(element) {
    return element?.closest?.("form, fieldset, dialog, [role='dialog'], [role='alert'], [role='status'], [aria-live], article, section, main, li, tr, td, th")
      || element?.parentElement
      || element
      || globalThis.document?.body
      || globalThis.document?.documentElement
      || null;
  }

  function captureActionEffectSnapshot(element) {
    const observationRoot = getActionObservationRoot(element);
    return {
      activeElement: describeActiveElement(globalThis.document?.activeElement),
      observationRoot,
      observationText: truncateText(normalizeText(observationRoot?.textContent || ""), 2000),
      targetDom: truncateText(serializeElementSnapshot(element), 2000),
      targetState: collectElementStateMetadata(element),
      value: getReferenceValueMetadata(element)
    };
  }

  async function withObservedActionWindow(observationRoot, action, { quietMs = 40, timeoutMs = 180 } = {}) {
    const target = observationRoot?.ownerDocument?.body
      || observationRoot?.ownerDocument?.documentElement
      || globalThis.document?.body
      || globalThis.document?.documentElement;
    if (!target || typeof globalThis.MutationObserver !== "function") {
      const result = await action();
      await delayMs(timeoutMs);
      return { observedMutations: { attributeNames: [], mutationCount: 0 }, result };
    }
    const attributeNames = new Set();
    let lastMutationAt = 0;
    let mutationCount = 0;
    const observer = new globalThis.MutationObserver((mutations) => {
      mutationCount += mutations.length;
      lastMutationAt = Date.now();
      mutations.forEach((mutation) => {
        if (mutation.type === "attributes" && mutation.attributeName) {
          attributeNames.add(String(mutation.attributeName));
        }
      });
    });
    try {
      observer.observe(target, {
        attributes: true,
        characterData: true,
        childList: true,
        subtree: true
      });
      const result = await action();
      const startedAt = Date.now();
      while (Date.now() - startedAt < timeoutMs) {
        await delayMs(20);
        if (mutationCount > 0 && Date.now() - lastMutationAt >= quietMs) {
          break;
        }
      }
      return { observedMutations: { attributeNames: [...attributeNames], mutationCount }, result };
    } finally {
      observer.disconnect();
    }
  }

  function buildActionEffectResult(beforeSnapshot, afterSnapshot, observedMutations, extra = {}) {
    const focusChanged = beforeSnapshot.activeElement !== afterSnapshot.activeElement;
    const nearbyTextChanged = beforeSnapshot.observationText !== afterSnapshot.observationText;
    const valueChanged = beforeSnapshot.value !== afterSnapshot.value;
    const checkedChanged = beforeSnapshot.targetState.checked !== afterSnapshot.targetState.checked;
    const selectedChanged = beforeSnapshot.targetState.selected !== afterSnapshot.targetState.selected;
    const expandedChanged = beforeSnapshot.targetState.expanded !== afterSnapshot.targetState.expanded;
    const pressedChanged = beforeSnapshot.targetState.pressed !== afterSnapshot.targetState.pressed;
    const targetDomChanged = beforeSnapshot.targetDom !== afterSnapshot.targetDom;
    const domChanged = Boolean(observedMutations.mutationCount) || targetDomChanged || nearbyTextChanged;
    const status = {
      checkedChanged,
      domChanged,
      expandedChanged,
      focusChanged,
      nearbyTextChanged,
      pressedChanged,
      reacted: false,
      selectedChanged,
      targetChanged: targetDomChanged || valueChanged || checkedChanged || selectedChanged || expandedChanged || pressedChanged,
      targetDomChanged,
      valueChanged
    };
    status.reacted = Object.entries(status).some(([key, value]) => key !== "reacted" && value === true);
    status.noObservedEffect = !status.reacted;
    return {
      ...extra,
      effect: {
        mutationAttributes: observedMutations.attributeNames.slice(0, 8),
        mutationCount: observedMutations.mutationCount
      },
      status
    };
  }

  function collectActionResult(element) {
    const state = collectElementStateMetadata(element);
    return {
      connected: element.isConnected !== false,
      descriptorTags: state.descriptorTags.slice(),
      dom: serializeElementSnapshot(element),
      frameId: helperFrameId,
      nodeId: ensureNodeId(element),
      semanticTags: state.semanticTags.slice(),
      state,
      tagName: getTagName(element)
    };
  }

  function detailLocalNode(payload = {}) {
    return collectActionResult(getElementByNodeId(payload?.nodeId, "detail"));
  }

  async function clickLocalNode(payload = {}) {
    const element = getElementByNodeId(payload?.nodeId, "click");
    const beforeSnapshot = captureActionEffectSnapshot(element);
    scrollElementIntoView(element);
    focusElement(element);
    if (beforeSnapshot.targetState.disabled) {
      throw createNamedError(
        "BrowserDomHelperActionError",
        `Browser DOM helper node "${payload?.nodeId}" is disabled.`,
        { code: "browser_dom_helper_click_disabled" }
      );
    }
    const { observedMutations } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      if (typeof element.click === "function") {
        element.click();
      } else {
        dispatchDomEvent(element, "click", "MouseEvent", { button: 0 });
      }
    });
    return {
      ...collectActionResult(element),
      ...buildActionEffectResult(beforeSnapshot, captureActionEffectSnapshot(element), observedMutations)
    };
  }

  async function typeLocalNode(payload = {}) {
    const element = getElementByNodeId(payload?.nodeId, "type");
    const beforeSnapshot = captureActionEffectSnapshot(element);
    const { observedMutations, result } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);
      const appliedValue = setNativeValue(element, payload?.value ?? "");
      dispatchDomEvent(element, "beforeinput", "InputEvent", {
        data: String(payload?.value ?? ""),
        inputType: "insertText"
      });
      dispatchDomEvent(element, "input", "InputEvent", {
        data: String(payload?.value ?? ""),
        inputType: "insertText"
      });
      dispatchDomEvent(element, "change");
      return appliedValue;
    });
    return {
      ...collectActionResult(element),
      ...buildActionEffectResult(beforeSnapshot, captureActionEffectSnapshot(element), observedMutations),
      value: result
    };
  }

  async function submitLocalNode(payload = {}) {
    const element = getElementByNodeId(payload?.nodeId, "submit");
    const tagName = getTagName(element);
    const beforeSnapshot = captureActionEffectSnapshot(element);
    const { observedMutations } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);
      if (tagName === "FORM" && typeof element.requestSubmit === "function") {
        element.requestSubmit();
      } else if (element.form && typeof element.form.requestSubmit === "function") {
        element.form.requestSubmit(["BUTTON", "INPUT"].includes(tagName) ? element : undefined);
      } else if (element.form) {
        const submitEvent = dispatchDomEvent(element.form, "submit");
        if (!submitEvent.defaultPrevented) {
          element.form.submit?.();
        }
      } else if (typeof element.click === "function") {
        element.click();
      } else {
        throw createNamedError(
          "BrowserDomHelperActionError",
          `Browser DOM helper cannot submit node "${payload?.nodeId}".`,
          { code: "browser_dom_helper_submit_unsupported" }
        );
      }
    });
    return {
      ...collectActionResult(element),
      ...buildActionEffectResult(beforeSnapshot, captureActionEffectSnapshot(element), observedMutations)
    };
  }

  async function pressEnterLocalNode(payload = {}) {
    const element = getElementByNodeId(payload?.nodeId, "type_submit");
    const beforeSnapshot = captureActionEffectSnapshot(element);
    const { observedMutations } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);
      dispatchKeyboardEvent(element, "keydown");
      dispatchKeyboardEvent(element, "keypress");
      dispatchKeyboardEvent(element, "keyup");
      if (getTagName(element) === "INPUT" && element.form && typeof element.form.requestSubmit === "function") {
        element.form.requestSubmit();
      }
    });
    return {
      ...collectActionResult(element),
      ...buildActionEffectResult(beforeSnapshot, captureActionEffectSnapshot(element), observedMutations)
    };
  }

  async function typeSubmitLocalNode(payload = {}) {
    const typed = await typeLocalNode(payload);
    const submitted = await pressEnterLocalNode(payload);
    return {
      ...submitted,
      effect: {
        mutationAttributes: [...new Set([...(typed?.effect?.mutationAttributes || []), ...(submitted?.effect?.mutationAttributes || [])])],
        mutationCount: Number(typed?.effect?.mutationCount || 0) + Number(submitted?.effect?.mutationCount || 0)
      },
      status: {
        ...(typed?.status || {}),
        ...(submitted?.status || {}),
        reacted: Boolean(typed?.status?.reacted || submitted?.status?.reacted),
        noObservedEffect: !Boolean(typed?.status?.reacted || submitted?.status?.reacted)
      },
      value: typed.value
    };
  }

  function scrollLocalNode(payload = {}) {
    const element = getElementByNodeId(payload?.nodeId, "scroll");
    const beforeSnapshot = captureActionEffectSnapshot(element);
    scrollElementIntoView(element);
    focusElement(element);
    const scrollEffect = buildActionEffectResult(beforeSnapshot, captureActionEffectSnapshot(element), {
      attributeNames: [],
      mutationCount: 0
    });
    return {
      ...collectActionResult(element),
      ...scrollEffect,
      status: {
        ...scrollEffect.status,
        reacted: true,
        noObservedEffect: false
      }
    };
  }

  async function invokeLocalOperation(type, payload = {}) {
    if (type === "capture_document") {
      return captureDocument(payload);
    }
    if (type === "detail_node") {
      return detailLocalNode(payload);
    }
    if (type === "click_node") {
      return clickLocalNode(payload);
    }
    if (type === "type_node") {
      return typeLocalNode(payload);
    }
    if (type === "submit_node") {
      return submitLocalNode(payload);
    }
    if (type === "type_submit_node") {
      return typeSubmitLocalNode(payload);
    }
    if (type === "scroll_node") {
      return scrollLocalNode(payload);
    }
    throw createNamedError(
      "BrowserDomHelperActionError",
      `Browser DOM helper does not support "${type}".`,
      { code: "browser_dom_helper_action_unsupported", details: { type } }
    );
  }

  async function routeOperation(type, payload = {}) {
    const frameChain = normalizeFrameChain(payload?.frameChain);
    if (!frameChain.length) {
      return invokeLocalOperation(type, payload);
    }
    if (frameChain[0] !== helperFrameId) {
      throw createNamedError(
        "BrowserDomHelperFrameRouteError",
        `Browser DOM helper cannot route frame chain "${encodeFrameChain(frameChain)}" from "${helperFrameId}".`,
        { code: "browser_dom_helper_frame_chain_mismatch", details: { frameChain } }
      );
    }
    if (frameChain.length === 1) {
      return invokeLocalOperation(type, payload);
    }
    const nextFrameId = frameChain[1];
    const childWindow = childFramesById.get(nextFrameId);
    if (!childWindow) {
      throw createNamedError(
        "BrowserDomHelperFrameRouteError",
        `Browser DOM helper does not know child frame "${nextFrameId}".`,
        { code: "browser_dom_helper_child_frame_missing", details: { frameChain } }
      );
    }
    return requestChildFrameOperation(childWindow, type, {
      ...payload,
      frameChain: frameChain.slice(1)
    });
  }

  globalThis.addEventListener("message", (event) => {
    const rawMessage = event?.data;
    if (!rawMessage || rawMessage.channel !== DOM_HELPER_CHANNEL || typeof rawMessage.type !== "string") {
      return;
    }
    const requestId = typeof rawMessage.requestId === "string" ? rawMessage.requestId : "";
    if (!requestId) {
      return;
    }
    if (rawMessage.type.endsWith("_result")) {
      const pendingRequest = pendingRequests.get(requestId);
      if (!pendingRequest) {
        return;
      }
      pendingRequests.delete(requestId);
      if (pendingRequest.timer != null) {
        globalThis.clearTimeout(pendingRequest.timer);
      }
      if (rawMessage.ok === false) {
        pendingRequest.reject(createNamedError(
          "BrowserDomHelperRemoteError",
          String(rawMessage?.payload?.message || `Embedded frame request "${pendingRequest.type}" failed.`),
          {
            code: rawMessage?.payload?.code ?? "browser_dom_helper_remote_error",
            details: rawMessage?.payload?.details || {},
            payload: rawMessage.payload
          }
        ));
        return;
      }
      pendingRequest.resolve(rawMessage.payload);
      return;
    }
    if (typeof event?.source?.postMessage !== "function") {
      return;
    }
    Promise.resolve(routeOperation(rawMessage.type, rawMessage.payload || {}))
      .then((payload) => {
        event.source.postMessage({
          channel: DOM_HELPER_CHANNEL,
          ok: true,
          payload,
          requestId,
          type: `${rawMessage.type}_result`
        }, "*");
      })
      .catch((error) => {
        console.error(`[a0-browser/dom-helper] Request "${rawMessage.type}" failed.`, error);
        event.source.postMessage({
          channel: DOM_HELPER_CHANNEL,
          ok: false,
          payload: {
            code: error?.code ?? "browser_dom_helper_error",
            details: error?.details || {},
            message: String(error?.message || `Embedded frame request "${rawMessage.type}" failed.`)
          },
          requestId,
          type: `${rawMessage.type}_result`
        }, "*");
      });
  });

  globalThis[DOM_HELPER_KEY] = {
    captureDocument(payload) {
      return captureDocument(payload);
    },
    clickNode(frameChain, nodeId) {
      return routeOperation("click_node", { frameChain, nodeId });
    },
    detailNode(frameChain, nodeId) {
      return routeOperation("detail_node", { frameChain, nodeId });
    },
    frameId: helperFrameId,
    scrollNode(frameChain, nodeId) {
      return routeOperation("scroll_node", { frameChain, nodeId });
    },
    submitNode(frameChain, nodeId) {
      return routeOperation("submit_node", { frameChain, nodeId });
    },
    typeNode(frameChain, nodeId, value) {
      return routeOperation("type_node", { frameChain, nodeId, value });
    },
    typeSubmitNode(frameChain, nodeId, value) {
      return routeOperation("type_submit_node", { frameChain, nodeId, value });
    },
    version: VERSION
  };
})();
