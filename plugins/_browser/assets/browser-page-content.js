(() => {
  const GLOBAL_KEY = "__spaceBrowserPageContent__";
  const DOM_HELPER_KEY = "__spaceBrowserDomHelper__";
  const VERSION = "12";
  const REQUIRED_API_NAMES = Object.freeze([
    "annotate",
    "boundingBoxFor",
    "capture",
    "click",
    "detail",
    "fileInputElementFor",
    "fileInputFor",
    "pointFor",
    "scroll",
    "select",
    "setChecked",
    "submit",
    "type",
    "typeSubmit"
  ]);

  function patchOpenShadowDom() {
    const original = Element.prototype.attachShadow;
    if (!original || original.__a0BrowserOpenShadowPatch) {
      return;
    }
    const patched = function attachShadow(options) {
      return original.call(this, { ...(options || {}), mode: "open" });
    };
    patched.__a0BrowserOpenShadowPatch = true;
    Element.prototype.attachShadow = patched;
  }

  patchOpenShadowDom();

  const BLOCK_TAGS = new Set([
    "ADDRESS",
    "ARTICLE",
    "ASIDE",
    "BLOCKQUOTE",
    "BODY",
    "DETAILS",
    "DIV",
    "DL",
    "FIELDSET",
    "FIGCAPTION",
    "FIGURE",
    "FOOTER",
    "FORM",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "HEADER",
    "HR",
    "HTML",
    "LI",
    "MAIN",
    "NAV",
    "OL",
    "P",
    "PRE",
    "SECTION",
    "TABLE",
    "TBODY",
    "TD",
    "TFOOT",
    "TH",
    "THEAD",
    "TR",
    "UL"
  ]);
  const SKIP_TAGS = new Set([
    "HEAD",
    "LINK",
    "META",
    "NOSCRIPT",
    "SCRIPT",
    "STYLE",
    "TEMPLATE"
  ]);
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

  if (globalThis[GLOBAL_KEY]?.version === VERSION) {
    return;
  }

  const state = {
    backend: "live",
    captureId: 0,
    capturedAt: 0,
    captureOptions: {
      includeLabelQuotes: false,
      includeLinkUrls: false,
      includeSemanticTags: true,
      includeStateTags: true,
      includeListIndentation: true,
      includeListMarkers: false
    },
    entries: new Map()
  };

  function isElementNode(value) {
    return Boolean(value && value.nodeType === 1);
  }

  function isTextNode(value) {
    return Boolean(value && value.nodeType === 3);
  }

  function normalizeText(value) {
    return String(value ?? "")
      .replace(/\s+/gu, " ")
      .trim();
  }

  function looksLikeSerializedHtmlText(value) {
    const normalizedValue = normalizeText(value);
    if (!normalizedValue || !normalizedValue.includes("<") || !normalizedValue.includes(">")) {
      return false;
    }

    if (/<!(?:doctype|--)\b/iu.test(normalizedValue)) {
      return true;
    }

    if (/<\/?(?:style|script)\b[\s\S]*?>/iu.test(normalizedValue)) {
      return true;
    }

    const tagMatches = normalizedValue.match(/<\/?[a-z][^>]*>/giu) || [];
    return tagMatches.length >= 3 && normalizedValue.length >= 80;
  }

  function looksLikeBrowserHelperMarkupText(value) {
    const normalizedValue = normalizeText(value);
    if (!normalizedValue) {
      return false;
    }

    return /space-browser-(?:frame-document|shadow-root)/iu.test(normalizedValue)
      || /data-space-browser-(?:frame|node|status|frame-url|frame-title|frame-src)/iu.test(normalizedValue);
  }

  function looksLikeMinifiedScriptText(value) {
    const normalizedValue = normalizeText(value);
    if (!normalizedValue || normalizedValue.length < 400) {
      return false;
    }

    const jsSignals = [
      /\bfunction\b/u,
      /\breturn\b/u,
      /\bvar\b/u,
      /\bnew\b/u,
      /\bcase\b/u,
      /\bswitch\b/u,
      /\bwhile\b/u,
      /\bfor\b/u,
      /\b(?:localStorage|postMessage|document\.|window\.|parent\.)/u,
      /\bthis\./u,
      /(?:&&|\|\||>>>|!==|===)/u
    ].reduce((count, pattern) => count + (pattern.test(normalizedValue) ? 1 : 0), 0);

    if (jsSignals < 4) {
      return false;
    }

    const punctuationCount = (normalizedValue.match(/[{}[\]();=<>\\]/gu) || []).length;
    return punctuationCount / normalizedValue.length >= 0.12;
  }

  function shouldDropReadableText(value) {
    const normalizedValue = normalizeText(value);
    if (!normalizedValue) {
      return true;
    }

    return looksLikeBrowserHelperMarkupText(normalizedValue)
      || looksLikeSerializedHtmlText(normalizedValue)
      || looksLikeMinifiedScriptText(normalizedValue);
  }

  function normalizeAttributeText(value) {
    return normalizeText(value).slice(0, 160);
  }

  function escapeMarkdownText(value) {
    return String(value ?? "").replace(/([\\`*_{}\[\]()#+\-!|>])/gu, "\\$1");
  }

  function quoteText(value) {
    return JSON.stringify(String(value ?? ""));
  }

  function truncateText(value, maxLength = 120) {
    const normalizedValue = normalizeText(value);
    if (normalizedValue.length <= maxLength) {
      return normalizedValue;
    }

    return `${normalizedValue.slice(0, Math.max(0, maxLength - 1)).trimEnd()}...`;
  }

  function delayMs(timeoutMs) {
    return new Promise((resolve) => {
      globalThis.setTimeout(resolve, Math.max(0, Number(timeoutMs) || 0));
    });
  }

  function parseCssColor(value) {
    const normalizedValue = normalizeText(value);
    if (!normalizedValue || normalizedValue === "transparent") {
      return null;
    }

    const rgbMatch = normalizedValue.match(/^rgba?\(([^)]+)\)$/iu);
    if (rgbMatch) {
      const parts = rgbMatch[1]
        .split(",")
        .map((part) => Number.parseFloat(String(part || "").trim()))
        .filter((part) => Number.isFinite(part));
      if (parts.length >= 3) {
        return {
          r: Math.max(0, Math.min(255, parts[0])),
          g: Math.max(0, Math.min(255, parts[1])),
          b: Math.max(0, Math.min(255, parts[2])),
          a: parts.length >= 4 ? Math.max(0, Math.min(1, parts[3])) : 1
        };
      }
    }

    const hexMatch = normalizedValue.match(/^#([\da-f]{3,8})$/iu);
    if (!hexMatch) {
      return null;
    }

    const hex = hexMatch[1];
    if (hex.length === 3 || hex.length === 4) {
      const [r, g, b, a = "f"] = hex.split("");
      return {
        r: Number.parseInt(`${r}${r}`, 16),
        g: Number.parseInt(`${g}${g}`, 16),
        b: Number.parseInt(`${b}${b}`, 16),
        a: Number.parseInt(`${a}${a}`, 16) / 255
      };
    }

    if (hex.length === 6 || hex.length === 8) {
      return {
        r: Number.parseInt(hex.slice(0, 2), 16),
        g: Number.parseInt(hex.slice(2, 4), 16),
        b: Number.parseInt(hex.slice(4, 6), 16),
        a: hex.length === 8 ? Number.parseInt(hex.slice(6, 8), 16) / 255 : 1
      };
    }

    return null;
  }

  function rgbToHsl(color) {
    if (!color) {
      return null;
    }

    const r = color.r / 255;
    const g = color.g / 255;
    const b = color.b / 255;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const delta = max - min;
    const lightness = (max + min) / 2;
    let hue = 0;
    let saturation = 0;

    if (delta > 0) {
      saturation = delta / (1 - Math.abs(2 * lightness - 1));
      if (max === r) {
        hue = 60 * (((g - b) / delta) % 6);
      } else if (max === g) {
        hue = 60 * (((b - r) / delta) + 2);
      } else {
        hue = 60 * (((r - g) / delta) + 4);
      }
    }

    if (hue < 0) {
      hue += 360;
    }

    return {
      hue,
      lightness,
      saturation
    };
  }

  function isTrustedHtmlRequirementError(error) {
    return /TrustedHTML/iu.test(String(error?.message || error || ""));
  }

  function joinBlocks(blocks) {
    return blocks
      .map((block) => String(block || "").trim())
      .filter(Boolean)
      .join("\n\n")
      .trim();
  }

  function cleanReadableMarkdown(value) {
    const lines = String(value || "")
      .replace(/<style\\?>[\s\S]*?<\/style\\?>/giu, "")
      .replace(/<script\\?>[\s\S]*?<\/script\\?>/giu, "")
      .replace(/<space\\-browser\\-(?:frame\\-document|shadow\\-root)\b[\s\S]*?<\/space\\-browser\\-(?:frame\\-document|shadow\\-root)>/giu, "")
      .split("\n");

    const filteredLines = [];
    let insideCodeFence = false;

    lines.forEach((line) => {
      const trimmedLine = String(line || "").trim();
      if (trimmedLine.startsWith("```")) {
        insideCodeFence = !insideCodeFence;
        filteredLines.push(line);
        return;
      }

      if (!trimmedLine || insideCodeFence) {
        filteredLines.push(line);
        return;
      }

      if (shouldDropReadableText(trimmedLine)) {
        return;
      }

      filteredLines.push(line);
    });

    return filteredLines
      .join("\n")
      .replace(/\n{3,}/gu, "\n\n")
      .trim();
  }

  function joinInlineParts(parts) {
    return String(parts
      .map((part) => String(part || "").trim())
      .filter(Boolean)
      .join(" "))
      .replace(/\s+([,.;!?])/gu, "$1")
      .replace(/([([{\u201c])\s+/gu, "$1")
      .replace(/\s+([\])}\u201d])/gu, "$1")
      .replace(/\s*\n\s*/gu, "\n")
      .replace(/[ \t]+\n/gu, "\n")
      .replace(/\n{3,}/gu, "\n\n")
      .trim();
  }

  function indentBlock(text, level = 1) {
    const prefix = "  ".repeat(Math.max(0, level));
    return String(text || "")
      .split("\n")
      .map((line) => `${prefix}${line}`)
      .join("\n");
  }

  function createNamedError(name, message, details = {}) {
    const error = new Error(message);
    error.name = name;
    Object.assign(error, details);
    return error;
  }

  function coerceSelectorList(payload) {
    if (typeof payload === "string") {
      return [payload];
    }

    if (Array.isArray(payload?.selectors)) {
      return payload.selectors;
    }

    if (typeof payload?.selectors === "string") {
      return [payload.selectors];
    }

    if (Array.isArray(payload?.selector)) {
      return payload.selector;
    }

    if (typeof payload?.selector === "string") {
      return [payload.selector];
    }

    if (Array.isArray(payload)) {
      return payload;
    }

    return [];
  }

  function normalizeSelectorList(payload) {
    return coerceSelectorList(payload)
      .map((selector) => String(selector || "").trim())
      .filter(Boolean);
  }

  function normalizeIncludeLinkUrls(payload) {
    return payload?.includeLinkUrls === true;
  }

  function normalizeIncludeLabelQuotes(payload) {
    return payload?.includeLabelQuotes === true;
  }

  function normalizeIncludeListIndentation(payload) {
    return payload?.includeListIndentation !== false;
  }

  function normalizeIncludeListMarkers(payload) {
    return payload?.includeListMarkers === true;
  }

  function normalizeIncludeStateTags(payload) {
    return payload?.includeStateTags !== false;
  }

  function normalizeIncludeSemanticTags(payload) {
    return payload?.includeSemanticTags !== false;
  }

  function formatSummaryValue(value, options = {}) {
    const normalizedValue = normalizeText(value);
    if (!normalizedValue) {
      return "";
    }

    if (options.includeLabelQuotes === true) {
      return quoteText(normalizedValue);
    }

    return escapeMarkdownText(normalizedValue);
  }

  function normalizeFrameChain(value) {
    const rawFrameChain = Array.isArray(value)
      ? value
      : typeof value === "string"
        ? value.split(">")
        : [];

    return rawFrameChain
      .map((entry) => String(entry || "").trim())
      .filter(Boolean);
  }

  function getDomHelper() {
    const helper = globalThis[DOM_HELPER_KEY];
    if (
      helper
      && typeof helper.captureDocument === "function"
      && typeof helper.detailNode === "function"
      && typeof helper.clickNode === "function"
      && typeof helper.typeNode === "function"
      && typeof helper.submitNode === "function"
      && typeof helper.typeSubmitNode === "function"
      && typeof helper.scrollNode === "function"
    ) {
      return helper;
    }

    return null;
  }

  function requireDomHelper(actionLabel) {
    const helper = getDomHelper();
    if (helper) {
      return helper;
    }

    throw createNamedError(
      "BrowserPageContentHelperUnavailableError",
      `Browser page content cannot ${actionLabel} without the desktop DOM helper.`,
      {
        code: "browser_page_content_dom_helper_unavailable",
        details: {
          action: String(actionLabel || "resolve")
        }
      }
    );
  }

  function normalizeReferenceId(value) {
    if (typeof value === "number" && Number.isFinite(value)) {
      return String(Math.trunc(value));
    }

    if (typeof value === "string") {
      return value.trim();
    }

    if (value && typeof value === "object") {
      return normalizeReferenceId(value.referenceId ?? value.ref ?? value.id);
    }

    return "";
  }

  function getTagName(element) {
    return String(element?.tagName || "").toUpperCase();
  }

  function expandSlotNodes(node) {
    if (!isElementNode(node) || getTagName(node) !== "SLOT" || typeof node.assignedNodes !== "function") {
      return [node];
    }

    try {
      const assignedNodes = [...(node.assignedNodes({ flatten: true }) || [])].filter(Boolean);
      if (assignedNodes.length) {
        return assignedNodes.flatMap((assignedNode) => expandSlotNodes(assignedNode));
      }
    } catch {
      // Fall through to the slot's fallback children.
    }

    return [...(node.childNodes || [])].flatMap((childNode) => expandSlotNodes(childNode));
  }

  function getReadableChildNodes(element) {
    const shadowRoot = element?.shadowRoot;
    if (shadowRoot) {
      const shadowNodes = [...(shadowRoot.childNodes || [])].flatMap((childNode) => expandSlotNodes(childNode));
      if (shadowNodes.length) {
        return shadowNodes;
      }
    }

    return [...(element?.childNodes || [])].flatMap((childNode) => expandSlotNodes(childNode));
  }

  function getReadableElementChildren(element) {
    return getReadableChildNodes(element).filter((childNode) => isElementNode(childNode));
  }

  function getReadableNodeText(node) {
    if (isTextNode(node)) {
      return node.textContent || "";
    }

    if (!isElementNode(node) || isHiddenElement(node)) {
      return "";
    }

    return getReadableChildNodes(node)
      .map((childNode) => getReadableNodeText(childNode))
      .filter(Boolean)
      .join(" ");
  }

  function querySelectorAllDeep(selector, root = globalThis.document) {
    const results = [];
    const seen = new Set();

    const addResult = (element) => {
      if (element && !seen.has(element)) {
        seen.add(element);
        results.push(element);
      }
    };

    const visitRoot = (scope) => {
      if (!scope || typeof scope.querySelectorAll !== "function") {
        return;
      }

      [...(scope.querySelectorAll(selector) || [])].forEach(addResult);
      [...(scope.querySelectorAll("*") || [])].forEach((element) => {
        if (element.shadowRoot) {
          visitRoot(element.shadowRoot);
        }
      });
    };

    visitRoot(root);
    return results;
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
      if (isGlobalOrDelegatedEventBinding(normalizedName.slice(1))) {
        return false;
      }
      return isInteractiveEventName(normalizedName.slice(1));
    }

    if (normalizedName.startsWith("x-on:") || normalizedName.startsWith("v-on:")) {
      if (isGlobalOrDelegatedEventBinding(normalizedName.slice(5))) {
        return false;
      }
      return isInteractiveEventName(normalizedName.slice(5));
    }

    if (normalizedName.startsWith("ng-")) {
      return isInteractiveEventName(normalizedName.slice(3));
    }

    if (normalizedName.startsWith("on") && normalizedName.length > 2) {
      return isInteractiveEventName(normalizedName.slice(2));
    }

    return false;
  }

  function hasHelperManagedNodeReference(element) {
    return Boolean(normalizeAttributeText(element?.getAttribute?.("data-space-browser-node-id")));
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

    const computedStyle = getComputedStyleSafe(element);
    if (isComputedStyleHidden(computedStyle)) {
      return true;
    }

    return isEffectivelyHiddenByAncestor(element.parentElement);
  }

  function isBlockElement(element) {
    return BLOCK_TAGS.has(getTagName(element));
  }

  function isInteractiveElement(element) {
    if (!isElementNode(element) || isHiddenElement(element)) {
      return false;
    }

    if (hasHelperManagedNodeReference(element)) {
      return true;
    }

    const tagName = getTagName(element);
    if (tagName === "A" && element.hasAttribute?.("href")) {
      return true;
    }

    if (tagName === "BUTTON" || tagName === "INPUT" || tagName === "SELECT" || tagName === "TEXTAREA" || tagName === "SUMMARY") {
      return true;
    }

    if (String(element.getAttribute?.("contenteditable") || "").toLowerCase() === "true") {
      return true;
    }

    const role = String(element.getAttribute?.("role") || "").trim().toLowerCase();
    return INTERACTIVE_ROLES.has(role) || hasInteractiveEventHandler(element);
  }

  function isFileInputElement(element) {
    return getTagName(element) === "INPUT"
      && String(element.getAttribute?.("type") || element.type || "").toLowerCase() === "file";
  }

  function getAssociatedLabelFileInput(labelElement) {
    if (getTagName(labelElement) !== "LABEL") {
      return null;
    }

    if (isFileInputElement(labelElement.control)) {
      return labelElement.control;
    }

    const descendantInput = labelElement.querySelector?.("input[type='file']");
    if (isFileInputElement(descendantInput)) {
      return descendantInput;
    }

    const forId = normalizeAttributeText(labelElement.getAttribute?.("for"));
    if (!forId) {
      return null;
    }

    return isFileInputElement(labelElement.ownerDocument?.getElementById?.(forId))
      ? labelElement.ownerDocument.getElementById(forId)
      : null;
  }

  function isFileInputLabel(element) {
    if (getTagName(element) !== "LABEL" || isHiddenElement(element)) {
      return false;
    }

    const input = getAssociatedLabelFileInput(element);
    return Boolean(input && isHiddenElement(input));
  }

  function getComputedStyleSafe(element) {
    try {
      return globalThis.getComputedStyle?.(element) || null;
    } catch {
      return null;
    }
  }

  function getElementRectSafe(element) {
    try {
      const rect = element?.getBoundingClientRect?.();
      if (!rect) {
        return null;
      }

      return {
        height: Number(rect.height) || 0,
        width: Number(rect.width) || 0,
        x: Number(rect.x) || 0,
        y: Number(rect.y) || 0
      };
    } catch {
      return null;
    }
  }

  function readSerializedTagList(element, attributeName) {
    const rawValue = normalizeText(element?.getAttribute?.(attributeName));
    if (!rawValue) {
      return [];
    }

    return rawValue
      .split(/\s+/u)
      .map((part) => normalizeText(part))
      .filter(Boolean);
  }

  function detectSemanticTone(element, computedStyle, metadata = {}) {
    const opacity = Number(computedStyle?.opacity || 1);
    const backgroundColor = parseCssColor(computedStyle?.backgroundColor || "");
    const borderColor = parseCssColor(computedStyle?.borderTopColor || "");
    const foregroundColor = parseCssColor(computedStyle?.color || "");
    const isButtonLike = ["BUTTON", "INPUT", "SUMMARY"].includes(getTagName(element))
      || ["button", "tab", "menuitem"].includes(String(element?.getAttribute?.("role") || "").trim().toLowerCase());

    if (metadata.disabled || metadata.blocked || opacity <= 0.58) {
      return "muted";
    }

    const preferredColor = [backgroundColor, borderColor, foregroundColor]
      .filter((color) => color && color.a > 0.15)
      .map((color) => ({
        color,
        hsl: rgbToHsl(color)
      }))
      .find((entry) => entry.hsl && entry.hsl.saturation >= 0.2);

    if (!preferredColor) {
      return "";
    }

    const {
      hue,
      lightness,
      saturation
    } = preferredColor.hsl;
    if (saturation < 0.2) {
      return "";
    }

    if ((hue >= 345 || hue < 20) && lightness >= 0.18 && lightness <= 0.82) {
      return "error";
    }

    if (hue >= 20 && hue < 65 && lightness >= 0.2 && lightness <= 0.9) {
      return "warning";
    }

    if (hue >= 65 && hue < 170 && lightness >= 0.16 && lightness <= 0.84) {
      return "success";
    }

    if (hue >= 170 && hue < 280 && lightness >= 0.14 && lightness <= 0.82) {
      if (isButtonLike && backgroundColor?.a > 0.2) {
        return "primary";
      }
      return "";
    }

    return "";
  }

  function collectElementStateMetadata(element, options = {}) {
    if (!isElementNode(element)) {
      return {
        descriptorTags: [],
        semanticTags: [],
        stateTags: []
      };
    }

    const computedStyle = getComputedStyleSafe(element);
    const rect = getElementRectSafe(element);
    const tagName = getTagName(element);
    const ariaDisabled = String(element.getAttribute?.("aria-disabled") || "").trim().toLowerCase() === "true";
    const ariaBusy = String(element.getAttribute?.("aria-busy") || "").trim().toLowerCase() === "true";
    const ariaChecked = String(element.getAttribute?.("aria-checked") || "").trim().toLowerCase() === "true";
    const ariaCurrent = normalizeText(element.getAttribute?.("aria-current"));
    const ariaInvalid = String(element.getAttribute?.("aria-invalid") || "").trim().toLowerCase() === "true";
    const ariaPressed = String(element.getAttribute?.("aria-pressed") || "").trim().toLowerCase() === "true";
    const ariaReadonly = String(element.getAttribute?.("aria-readonly") || "").trim().toLowerCase() === "true";
    const ariaRequired = String(element.getAttribute?.("aria-required") || "").trim().toLowerCase() === "true";
    const ariaSelected = String(element.getAttribute?.("aria-selected") || "").trim().toLowerCase() === "true";
    const helperStateTags = readSerializedTagList(element, "data-space-browser-state-tags");
    const helperSemanticTags = readSerializedTagList(element, "data-space-browser-semantic-tags");
    const closestInert = typeof element.closest === "function" ? element.closest("[inert]") : null;
    const pointerEventsNone = normalizeText(computedStyle?.pointerEvents || "").toLowerCase() === "none";
    const disabled = Boolean(element.disabled || ariaDisabled || closestInert || helperStateTags.includes("disabled"));
    const blocked = !disabled && (pointerEventsNone || helperStateTags.includes("blocked"));
    const checked = Boolean(element.checked || ariaChecked || helperStateTags.includes("checked"));
    const selected = tagName === "OPTION"
      ? Boolean(element.selected)
      : Boolean(ariaSelected || helperStateTags.includes("selected"));
    const invalid = Boolean(ariaInvalid || helperStateTags.includes("invalid") || element.matches?.(":invalid"));
    const readonly = Boolean(element.readOnly || ariaReadonly);
    const required = Boolean(element.required || ariaRequired);
    const expanded = String(element.getAttribute?.("aria-expanded") || "").trim().toLowerCase() === "true" || helperStateTags.includes("expanded");
    const pressed = ariaPressed || helperStateTags.includes("pressed");
    const busy = ariaBusy || helperStateTags.includes("busy");
    const current = Boolean((ariaCurrent && ariaCurrent !== "false") || helperStateTags.includes("current"));
    const zeroRect = Boolean(
      rect
      && element.ownerDocument === globalThis.document
      && rect.width <= 1
      && rect.height <= 1
    );
    const opacity = Number(computedStyle?.opacity || 1);
    const semanticTone = helperSemanticTags[0] || detectSemanticTone(element, computedStyle, {
      blocked,
      disabled
    });
    const stateTags = helperStateTags.length
      ? helperStateTags.slice()
      : [
        disabled ? "disabled" : "",
        !disabled && (blocked || zeroRect) ? "blocked" : "",
        checked ? "checked" : "",
        selected && tagName !== "SELECT" ? "selected" : "",
        invalid ? "invalid" : "",
        expanded ? "expanded" : "",
        pressed ? "pressed" : ""
      ].filter(Boolean);

    const semanticTags = helperSemanticTags.length
      ? helperSemanticTags.slice(0, 1)
      : (semanticTone ? [semanticTone] : []);
    const descriptorTags = [
      ...(options.includeStateTags !== false ? stateTags : []),
      ...(options.includeSemanticTags !== false ? semanticTags : [])
    ];

    return {
      blocked,
      busy,
      checked,
      current,
      cursor: normalizeText(computedStyle?.cursor || "").toLowerCase(),
      descriptorTags,
      disabled,
      expanded,
      invalid,
      opacity,
      pointerEventsNone,
      pressed,
      readonly,
      required,
      selected,
      semanticTags,
      semanticTone,
      stateTags,
      visible: !isHiddenElement(element),
      zeroRect
    };
  }

  function getReferenceValueMetadata(element) {
    const tagName = getTagName(element);
    const helperLiveValue = normalizeText(element?.getAttribute?.("data-space-browser-live-value"));
    const helperSelectedValue = normalizeText(element?.getAttribute?.("data-space-browser-selected-text"));
    if (tagName === "INPUT") {
      const inputType = String(element.getAttribute?.("type") || element.type || "text").toLowerCase();
      if (inputType === "password") {
        return "";
      }
      return truncateText(helperLiveValue || element.value || element.getAttribute?.("value") || "", 96);
    }

    if (tagName === "TEXTAREA") {
      return truncateText(helperLiveValue || element.value || "", 96);
    }

    if (tagName === "SELECT") {
      if (helperSelectedValue) {
        return helperSelectedValue;
      }
      const selectedOptions = [...(element.selectedOptions || [])]
        .map((option) => truncateText(option.textContent || option.label || option.value || "", 48))
        .filter(Boolean);
      return selectedOptions.join(" | ");
    }

    if (String(element.getAttribute?.("contenteditable") || "").toLowerCase() === "true") {
      return truncateText(element.textContent || "", 96);
    }

    return "";
  }

  function collectMetaLines(doc = globalThis.document) {
    const lines = [];
    const title = normalizeAttributeText(doc?.title || "");
    const description = normalizeAttributeText(
      doc?.querySelector?.('meta[name="description"]')?.getAttribute?.("content") || ""
    );
    const url = String(globalThis.location?.href || "");

    if (!title && !description && !url) {
      return "";
    }

    lines.push("---");
    if (title) {
      lines.push(`title: ${quoteText(title)}`);
    }
    if (description) {
      lines.push(`description: ${quoteText(description)}`);
    }
    if (url) {
      lines.push(`url: ${quoteText(url)}`);
    }
    lines.push("---");
    return lines.join("\n");
  }

  function summarizeUrl(value) {
    const normalizedValue = String(value || "").trim();
    if (!normalizedValue) {
      return "";
    }

    try {
      const url = new URL(normalizedValue, globalThis.location?.href || "http://localhost/");
      if (url.origin === globalThis.location?.origin) {
        const relative = `${url.pathname || "/"}${url.search || ""}${url.hash || ""}`;
        return truncateText(relative || "/", 96);
      }

      return truncateText(`${url.hostname}${url.pathname || "/"}`, 96);
    } catch {
      return truncateText(normalizedValue, 96);
    }
  }

  function getElementText(element) {
    const readableText = normalizeText(getReadableNodeText(element));
    return readableText || normalizeText(element?.textContent || "");
  }

  function isLabelableControlForText(element) {
    return ["BUTTON", "INPUT", "METER", "OUTPUT", "PROGRESS", "SELECT", "TEXTAREA"].includes(getTagName(element));
  }

  function getLabelElementText(labelElement, controlElement = null) {
    const collect = (node) => {
      if (isTextNode(node)) {
        return node.textContent || "";
      }

      if (!isElementNode(node) || isHiddenElement(node)) {
        return "";
      }

      if (node !== labelElement && (node === controlElement || isLabelableControlForText(node))) {
        return "";
      }

      return getReadableChildNodes(node)
        .map((childNode) => collect(childNode))
        .filter(Boolean)
        .join(" ");
    };

    return normalizeText(collect(labelElement)) || getElementText(labelElement);
  }

  function collectLabelCandidates(element, options = {}) {
    const includeAlt = options.includeAlt !== false;
    const includeDescendantImageAlt = options.includeDescendantImageAlt !== false;
    const includePlaceholder = options.includePlaceholder === true;
    const includeText = options.includeText !== false;
    const collectedLabels = [];

    try {
      if (Array.isArray(element?.labels) || typeof element?.labels?.forEach === "function") {
        element.labels.forEach((labelElement) => {
          const text = getLabelElementText(labelElement, element);
          if (text) {
            collectedLabels.push(text);
          }
        });
      }
    } catch {
      // Ignore labels lookup failures from non-form elements.
    }

    [
      element?.getAttribute?.("aria-label"),
      element?.getAttribute?.("title")
    ].forEach((candidate) => {
      const text = normalizeAttributeText(candidate);
      if (text) {
        collectedLabels.push(text);
      }
    });

    if (includeAlt) {
      const altText = normalizeAttributeText(element?.getAttribute?.("alt"));
      if (altText) {
        collectedLabels.push(altText);
      }
    }

    if (includePlaceholder) {
      const placeholderText = normalizeAttributeText(element?.getAttribute?.("placeholder"));
      if (placeholderText) {
        collectedLabels.push(placeholderText);
      }
    }

    if (includeDescendantImageAlt) {
      try {
        [...(element?.querySelectorAll?.("img[alt], img[title]") || [])]
          .slice(0, 3)
          .forEach((mediaElement) => {
            const text = normalizeAttributeText(
              mediaElement.getAttribute?.("alt")
              || mediaElement.getAttribute?.("title")
            );
            if (text) {
              collectedLabels.push(text);
            }
          });
      } catch {
        // Ignore descendant-media lookup failures.
      }
    }

    if (includeText) {
      const textContent = getElementText(element);
      if (textContent) {
        collectedLabels.push(textContent);
      }
    }

    return [...new Set(collectedLabels.filter(Boolean))];
  }

  function getLabelText(element, options = {}) {
    return collectLabelCandidates(element, options)[0] || "";
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
      // Fall through to XMLSerializer.
    }

    try {
      if (typeof globalThis.XMLSerializer === "function") {
        return new globalThis.XMLSerializer().serializeToString(element);
      }
    } catch {
      // Ignore serialization errors.
    }

    return "";
  }

  function getReferenceKind(element) {
    const tagName = getTagName(element);
    const role = String(element.getAttribute?.("role") || "").trim().toLowerCase();
    const inputType = String(element.getAttribute?.("type") || element.type || "text").toLowerCase();

    if (tagName === "A" || role === "link") {
      return "link";
    }

    if (tagName === "IMG") {
      return "image";
    }

    if (tagName === "BUTTON" || ["button", "menuitem", "tab"].includes(role)) {
      return "button";
    }

    if (tagName === "TEXTAREA") {
      return "textarea";
    }

    if (tagName === "SELECT" || role === "combobox") {
      return "select";
    }

    if (tagName === "SUMMARY") {
      return "summary";
    }

    if (tagName === "INPUT") {
      if (["button", "submit", "reset"].includes(inputType)) {
        return "button";
      }

      if (inputType === "checkbox") {
        return "checkbox";
      }

      if (inputType === "radio") {
        return "radio";
      }

      return `input ${inputType || "text"}`;
    }

    if (tagName === "LABEL" && isFileInputLabel(element)) {
      return "file input label";
    }

    if (String(element.getAttribute?.("contenteditable") || "").toLowerCase() === "true") {
      return "editable";
    }

    if (role === "searchbox") {
      return "input search";
    }

    if (role === "textbox") {
      return "input text";
    }

    if (hasHelperManagedNodeReference(element) || hasInteractiveEventHandler(element)) {
      return "button";
    }

    return role || tagName.toLowerCase();
  }

  function collectReferenceSummaryData(element, options = {}) {
    const tagName = getTagName(element);
    const role = String(element.getAttribute?.("role") || "").trim().toLowerCase();
    const id = normalizeAttributeText(element.getAttribute?.("id"));
    const name = normalizeAttributeText(element.getAttribute?.("name"));
    const kind = getReferenceKind(element);
    const stateMetadata = collectElementStateMetadata(element, options);
    const formatValue = (value) => formatSummaryValue(value, options);
    const includeLinkUrls = options.includeLinkUrls === true;
    const parts = [];
    const appendFallbackIdOrName = () => {
      if (id) {
        parts.push(`#${id}`);
        return;
      }

      if (name) {
        parts.push(`name=${formatValue(name)}`);
      }
    };

    if (tagName === "A" || role === "link") {
      const hrefSummary = summarizeUrl(element.getAttribute?.("href") || element.href || "");
      const label = truncateText(getLabelText(element, {
        includeAlt: false,
        includeDescendantImageAlt: true,
        includePlaceholder: false,
        includeText: true
      }), 120);
      const displayLabel = label || hrefSummary;

      if (displayLabel) {
        parts.push(formatValue(displayLabel));
      } else {
        appendFallbackIdOrName();
      }

      if (includeLinkUrls) {
        if (hrefSummary && hrefSummary !== displayLabel) {
          parts.push(`-> ${hrefSummary}`);
        }
      }
    } else if (tagName === "BUTTON" || ["button", "menuitem", "tab"].includes(role)) {
      const label = truncateText(getLabelText(element, {
        includeAlt: false,
        includeDescendantImageAlt: true,
        includePlaceholder: false,
        includeText: true
      }), 120);
      if (label) {
        parts.push(formatValue(label));
      } else {
        appendFallbackIdOrName();
      }
    } else if (tagName === "TEXTAREA" || role === "textbox" || role === "searchbox") {
      const label = truncateText(getLabelText(element, {
        includeAlt: false,
        includeDescendantImageAlt: false,
        includePlaceholder: false,
        includeText: true
      }), 120);
      if (label) {
        parts.push(formatValue(label));
      }
      const placeholder = normalizeAttributeText(element.getAttribute?.("placeholder"));
      if (placeholder) {
        parts.push(`placeholder=${formatValue(placeholder)}`);
      } else if (!label) {
        appendFallbackIdOrName();
      }
    } else if (tagName === "SELECT" || role === "combobox") {
      const label = truncateText(getLabelText(element, {
        includeAlt: false,
        includeDescendantImageAlt: false,
        includePlaceholder: false,
        includeText: true
      }), 120);
      if (label) {
        parts.push(formatValue(label));
      } else {
        appendFallbackIdOrName();
      }

      const selectedValue = getReferenceValueMetadata(element);
      const selectedOptions = selectedValue
        ? [selectedValue]
        : [...(element.selectedOptions || [])]
          .map((option) => truncateText(option.textContent || "", 48))
          .filter(Boolean);
      if (selectedOptions.length) {
        parts.push(`selected=${formatValue(selectedOptions.join(" | "))}`);
      }
    } else if (tagName === "SUMMARY") {
      const label = truncateText(getLabelText(element, {
        includeAlt: false,
        includeDescendantImageAlt: true,
        includePlaceholder: false,
        includeText: true
      }), 120);
      if (label) {
        parts.push(formatValue(label));
      } else {
        appendFallbackIdOrName();
      }
    } else if (tagName === "INPUT") {
      const inputType = String(element.getAttribute?.("type") || element.type || "text").toLowerCase();
      if (["button", "submit", "reset"].includes(inputType)) {
        const label = truncateText(getLabelText(element, {
          includeAlt: false,
          includeDescendantImageAlt: false,
          includePlaceholder: false,
          includeText: false
        }) || element.value || "", 120);
        if (label) {
          parts.push(formatValue(label));
        } else {
          appendFallbackIdOrName();
        }
      } else if (["checkbox", "radio"].includes(inputType)) {
        const label = truncateText(getLabelText(element, {
          includeAlt: false,
          includeDescendantImageAlt: false,
          includePlaceholder: false,
          includeText: false
        }), 120);
        if (label) {
          parts.push(formatValue(label));
        } else {
          appendFallbackIdOrName();
        }
      } else if (inputType === "file") {
        const label = truncateText(getLabelText(element, {
          includeAlt: false,
          includeDescendantImageAlt: false,
          includePlaceholder: false,
          includeText: false
        }), 120);
        if (label) {
          parts.push(formatValue(label));
        } else {
          appendFallbackIdOrName();
        }
      } else {
        const label = truncateText(getLabelText(element, {
          includeAlt: false,
          includeDescendantImageAlt: false,
          includePlaceholder: false,
          includeText: false
        }), 120);
        if (label) {
          parts.push(formatValue(label));
        }

        const placeholder = normalizeAttributeText(element.getAttribute?.("placeholder"));
        const value = inputType === "password"
          ? ""
          : getReferenceValueMetadata(element);

        if (placeholder) {
          parts.push(`placeholder=${formatValue(placeholder)}`);
        }
        if (value) {
          parts.push(`value=${formatValue(value)}`);
        }
        if (!label && !placeholder && !value) {
          appendFallbackIdOrName();
        }
      }
    } else if (String(element.getAttribute?.("contenteditable") || "").toLowerCase() === "true") {
      const label = truncateText(getLabelText(element, {
        includeAlt: false,
        includeDescendantImageAlt: false,
        includePlaceholder: false,
        includeText: true
      }), 120);
      if (label) {
        parts.push(formatValue(label));
      } else {
        appendFallbackIdOrName();
      }
    } else if (tagName === "IMG") {
      const srcSummary = summarizeUrl(element.currentSrc || element.getAttribute?.("src") || element.src || "");
      const label = truncateText(getLabelText(element, {
        includeAlt: true,
        includeDescendantImageAlt: false,
        includePlaceholder: false,
        includeText: false
      }), 120);
      const displayLabel = label || srcSummary;
      if (displayLabel) {
        parts.push(formatValue(displayLabel));
      } else {
        appendFallbackIdOrName();
      }
    } else if (role) {
      const label = truncateText(getLabelText(element, {
        includeAlt: false,
        includeDescendantImageAlt: true,
        includePlaceholder: false,
        includeText: true
      }), 120);
      if (label) {
        parts.push(formatValue(label));
      } else {
        appendFallbackIdOrName();
      }
    } else {
      const label = truncateText(getLabelText(element, {
        includeAlt: false,
        includeDescendantImageAlt: true,
        includePlaceholder: false,
        includeText: true
      }), 120);
      if (label) {
        parts.push(formatValue(label));
      } else {
        appendFallbackIdOrName();
      }
    }

    return {
      descriptorTags: stateMetadata.descriptorTags.slice(),
      kind,
      semanticTags: stateMetadata.semanticTags.slice(),
      state: stateMetadata,
      summary: parts.filter(Boolean).join(" ")
    };
  }

  function createReferenceEntry(element, referenceId, options = {}) {
    const nodeId = normalizeAttributeText(element.getAttribute?.("data-space-browser-node-id"));
    const frameId = normalizeAttributeText(element.getAttribute?.("data-space-browser-frame-id"));
    const frameChain = normalizeFrameChain(element.getAttribute?.("data-space-browser-frame-chain"));
    const helperBacked = Boolean(nodeId && frameChain.length);
    const summaryData = collectReferenceSummaryData(element, options);

    return {
      connected: helperBacked ? true : element.isConnected !== false,
      dom: serializeElementSnapshot(element),
      descriptorTags: summaryData.descriptorTags,
      element: helperBacked ? null : element,
      frameChain,
      frameId,
      helperBacked,
      id: normalizeAttributeText(element.getAttribute?.("id")),
      name: normalizeAttributeText(element.getAttribute?.("name")),
      nodeId,
      referenceId,
      kind: summaryData.kind,
      semanticTags: summaryData.semanticTags,
      state: summaryData.state,
      summary: summaryData.summary,
      tagName: getTagName(element)
    };
  }

  function ensureReference(element, context) {
    if (context.referenceIdsByElement.has(element)) {
      return context.referenceIdsByElement.get(element);
    }

    const referenceId = String(context.nextReferenceId++);
    const entry = createReferenceEntry(element, referenceId, context.options);
    context.referenceIdsByElement.set(element, referenceId);
    context.entries.set(referenceId, entry);
    return referenceId;
  }

  function renderReference(element, context) {
    const referenceId = ensureReference(element, context);
    const entry = context.entries.get(referenceId);
    const kind = normalizeText(entry?.kind || getTagName(element).toLowerCase());
    const descriptorTags = Array.isArray(entry?.descriptorTags)
      ? entry.descriptorTags.map((tag) => normalizeText(tag)).filter(Boolean)
      : [];
    const summary = normalizeText(entry?.summary || "");
    const descriptor = [...descriptorTags, kind, referenceId].filter(Boolean).join(" ");
    return summary ? `[${descriptor}] ${summary}` : `[${descriptor}]`;
  }

  function isReferenceableElement(element) {
    return isInteractiveElement(element) || getTagName(element) === "IMG" || isFileInputLabel(element);
  }

  function collectLabelControlElements(labelElement) {
    const controls = [];
    const seen = new Set();
    const addControl = (element) => {
      if (!isElementNode(element) || seen.has(element) || !isReferenceableElement(element)) {
        return;
      }

      seen.add(element);
      controls.push(element);
    };

    [
      "input",
      "textarea",
      "select",
      "button",
      "summary",
      "a[href]",
      "[role]",
      "[contenteditable='true']",
      "[contenteditable='']"
    ].forEach((selector) => {
      try {
        [...(labelElement.querySelectorAll?.(selector) || [])].forEach(addControl);
      } catch {
        // Ignore unsupported selectors in unusual DOMs.
      }
    });

    return controls;
  }

  function renderControlLabelReferences(labelElement, context) {
    return collectLabelControlElements(labelElement)
      .map((controlElement) => renderReference(controlElement, context))
      .filter(Boolean)
      .join("\n");
  }

  function renderInlineNode(node, context) {
    if (isTextNode(node)) {
      const textContent = normalizeText(node.textContent || "");
      if (shouldDropReadableText(textContent)) {
        return "";
      }

      return escapeMarkdownText(textContent);
    }

    if (!isElementNode(node) || isHiddenElement(node)) {
      return "";
    }

    if (isReferenceableElement(node)) {
      return renderReference(node, context);
    }

    const tagName = getTagName(node);

    if (tagName === "LABEL" && (node.getAttribute?.("for") || node.querySelector?.("input, textarea, select, button"))) {
      return renderControlLabelReferences(node, context);
    }

    if (tagName === "BR") {
      return "\n";
    }

    if (tagName === "STRONG" || tagName === "B") {
      const content = renderInlineChildren(node, context);
      return content ? `**${content}**` : "";
    }

    if (tagName === "EM" || tagName === "I") {
      const content = renderInlineChildren(node, context);
      return content ? `*${content}*` : "";
    }

    if (tagName === "S" || tagName === "STRIKE" || tagName === "DEL") {
      const content = renderInlineChildren(node, context);
      return content ? `~~${content}~~` : "";
    }

    if (tagName === "CODE") {
      const content = normalizeText(node.textContent || "");
      return content ? `\`${content.replace(/`/gu, "\\`")}\`` : "";
    }

    return renderInlineChildren(node, context);
  }

  function renderInlineChildren(element, context) {
    const parts = [];

    getReadableChildNodes(element).forEach((childNode) => {
      const renderedChild = renderInlineNode(childNode, context);
      if (renderedChild) {
        parts.push(renderedChild);
      }
    });

    return joinInlineParts(parts);
  }

  function renderParagraph(element, context) {
    return renderInlineChildren(element, context);
  }

  function renderHeading(element, context) {
    const level = Math.min(6, Math.max(1, Number.parseInt(getTagName(element).slice(1), 10) || 1));
    const content = renderInlineChildren(element, context);
    return content ? `${"#".repeat(level)} ${content}` : "";
  }

  function renderCodeBlock(element) {
    const content = String(element.textContent || "").trimEnd();
    if (!content) {
      return "";
    }

    return `\`\`\`\n${content.replace(/```/gu, "\\`\\`\\`")}\n\`\`\``;
  }

  function renderBlockquote(element, context) {
    const content = renderBlockChildren(element, context);
    if (!content) {
      return "";
    }

    return content
      .split("\n")
      .map((line) => `> ${line}`)
      .join("\n");
  }

  function renderListItem(element, context, depth, index, ordered) {
    const includeListMarkers = context.options.includeListMarkers === true;
    const includeListIndentation = context.options.includeListIndentation !== false;
    const marker = includeListMarkers ? (ordered ? `${index + 1}.` : "-") : "";
    const indentation = includeListIndentation ? "  ".repeat(Math.max(0, depth)) : "";
    const inlineParts = [];
    const nestedBlocks = [];

    getReadableChildNodes(element).forEach((childNode) => {
      if (isElementNode(childNode) && (getTagName(childNode) === "UL" || getTagName(childNode) === "OL")) {
        const nestedList = renderList(childNode, context, depth + 1);
        if (nestedList) {
          nestedBlocks.push(nestedList);
        }
        return;
      }

      const renderedChild = renderInlineNode(childNode, context);
      if (renderedChild) {
        inlineParts.push(renderedChild);
      }
    });

    const head = joinInlineParts(inlineParts);
    const linePrefix = marker ? `${indentation}${marker} ` : indentation;
    const lines = [`${linePrefix}${head || "(empty)"}`];
    nestedBlocks.forEach((nestedBlock) => {
      lines.push(indentBlock(nestedBlock, includeListIndentation ? 1 : 0));
    });
    return lines.join("\n");
  }

  function renderList(element, context, depth = 0) {
    const ordered = getTagName(element) === "OL";
    return getReadableElementChildren(element)
      .filter((child) => getTagName(child) === "LI" && !isHiddenElement(child))
      .map((item, index) => renderListItem(item, context, depth, index, ordered))
      .filter(Boolean)
      .join("\n");
  }

  function renderTableCell(element, context) {
    return renderInlineChildren(element, context);
  }

  function renderTable(element, context) {
    const rows = [...element.querySelectorAll?.(":scope > thead > tr, :scope > tbody > tr, :scope > tr, :scope > tfoot > tr") || []]
      .filter((row) => getTagName(row) === "TR");

    if (!rows.length) {
      return "";
    }

    const renderedRows = rows.map((row) => {
      return [...row.children]
        .filter((cell) => ["TD", "TH"].includes(getTagName(cell)) && !isHiddenElement(cell))
        .map((cell) => renderTableCell(cell, context));
    }).filter((cells) => cells.length);

    if (!renderedRows.length) {
      return "";
    }

    const columnCount = Math.max(...renderedRows.map((cells) => cells.length));
    const normalizedRows = renderedRows.map((cells) => {
      const nextCells = cells.slice();
      while (nextCells.length < columnCount) {
        nextCells.push("");
      }
      return nextCells;
    });

    const headerRow = normalizedRows[0];
    const separatorRow = headerRow.map(() => "---");
    const tableLines = [
      `| ${headerRow.join(" | ")} |`,
      `| ${separatorRow.join(" | ")} |`
    ];

    normalizedRows.slice(1).forEach((row) => {
      tableLines.push(`| ${row.join(" | ")} |`);
    });

    return tableLines.join("\n");
  }

  function renderGenericContainer(element, context) {
    return renderBlockChildren(element, context);
  }

  function renderElementAsBlock(element, context) {
    if (!isElementNode(element) || isHiddenElement(element)) {
      return "";
    }

    if (isReferenceableElement(element)) {
      return renderReference(element, context);
    }

    const tagName = getTagName(element);

    if (tagName === "LABEL" && (element.getAttribute?.("for") || element.querySelector?.("input, textarea, select, button"))) {
      return renderControlLabelReferences(element, context);
    }

    if (/^H[1-6]$/u.test(tagName)) {
      return renderHeading(element, context);
    }

    if (tagName === "P") {
      return renderParagraph(element, context);
    }

    if (tagName === "PRE") {
      return renderCodeBlock(element);
    }

    if (tagName === "BLOCKQUOTE") {
      return renderBlockquote(element, context);
    }

    if (tagName === "UL" || tagName === "OL") {
      return renderList(element, context);
    }

    if (tagName === "TABLE") {
      return renderTable(element, context);
    }

    if (tagName === "HR") {
      return "---";
    }

    return renderGenericContainer(element, context);
  }

  function renderBlockChildren(element, context) {
    const blocks = [];
    const inlineParts = [];

    const flushInlineParts = () => {
      const inlineText = joinInlineParts(inlineParts.splice(0, inlineParts.length));
      if (inlineText) {
        blocks.push(inlineText);
      }
    };

    getReadableChildNodes(element).forEach((childNode) => {
      if (isTextNode(childNode)) {
        const rawTextContent = normalizeText(childNode.textContent || "");
        if (shouldDropReadableText(rawTextContent)) {
          return;
        }

        const textContent = escapeMarkdownText(rawTextContent);
        if (textContent) {
          inlineParts.push(textContent);
        }
        return;
      }

      if (!isElementNode(childNode) || isHiddenElement(childNode)) {
        return;
      }

      const renderedChild = renderElementAsBlock(childNode, context);
      if (!renderedChild) {
        return;
      }

      if (isBlockElement(childNode) || isReferenceableElement(childNode)) {
        flushInlineParts();
        blocks.push(renderedChild);
        return;
      }

      inlineParts.push(renderedChild);
    });

    flushInlineParts();
    return joinBlocks(blocks);
  }

  function createCaptureContext(payload = null) {
    return {
      entries: new Map(),
      nextReferenceId: 1,
      options: {
        includeLabelQuotes: normalizeIncludeLabelQuotes(payload),
        includeLinkUrls: normalizeIncludeLinkUrls(payload),
        includeSemanticTags: normalizeIncludeSemanticTags(payload),
        includeStateTags: normalizeIncludeStateTags(payload),
        includeListIndentation: normalizeIncludeListIndentation(payload),
        includeListMarkers: normalizeIncludeListMarkers(payload)
      },
      referenceIdsByElement: new WeakMap()
    };
  }

  function resolveSelectorTargets(payload, doc = globalThis.document) {
    const selectors = normalizeSelectorList(payload);
    if (!selectors.length) {
      return {
        includeMetaData: true,
        items: [
          {
            key: "document",
            targets: [doc?.body || doc?.documentElement].filter(Boolean)
          }
        ]
      };
    }

    return {
      includeMetaData: false,
      items: selectors.map((selector) => {
        let targets = [];
        try {
          targets = doc === globalThis.document
            ? querySelectorAllDeep(selector, doc)
            : [...(doc?.querySelectorAll?.(selector) || [])];
        } catch (error) {
          throw createNamedError(
            "BrowserPageContentSelectorError",
            `Browser page content could not resolve selector "${selector}".`,
            {
              code: "browser_page_content_selector_error",
              details: {
                selector
              },
              cause: error
            }
          );
        }

        return {
          key: selector,
          targets
        };
      })
    };
  }

  function parseSnapshotFragment(html, parser) {
    return parser.parseFromString(
      `<!DOCTYPE html><html><body>${String(html || "")}</body></html>`,
      "text/html"
    );
  }

  function renderSnapshotFragment(html, captureContext, parser) {
    const parsedDocument = parseSnapshotFragment(html, parser);
    const blocks = [];
    const inlineParts = [];

    const flushInlineParts = () => {
      const inlineText = joinInlineParts(inlineParts.splice(0, inlineParts.length));
      if (inlineText) {
        blocks.push(inlineText);
      }
    };

    parsedDocument.body.childNodes.forEach((childNode) => {
      if (isTextNode(childNode)) {
        const rawTextContent = normalizeText(childNode.textContent || "");
        if (shouldDropReadableText(rawTextContent)) {
          return;
        }

        const textContent = escapeMarkdownText(rawTextContent);
        if (textContent) {
          inlineParts.push(textContent);
        }
        return;
      }

      if (!isElementNode(childNode) || isHiddenElement(childNode)) {
        return;
      }

      const renderedChild = renderElementAsBlock(childNode, captureContext);
      if (!renderedChild) {
        return;
      }

      if (isBlockElement(childNode) || isReferenceableElement(childNode)) {
        flushInlineParts();
        blocks.push(renderedChild);
        return;
      }

      inlineParts.push(renderedChild);
    });

    flushInlineParts();
    return cleanReadableMarkdown(joinBlocks(blocks));
  }

  function captureLive(payload = null) {
    const captureContext = createCaptureContext(payload);
    const resolvedTargets = resolveSelectorTargets(payload);
    const snapshot = {};

    resolvedTargets.items.forEach((item) => {
      const blocks = [];
      if (resolvedTargets.includeMetaData && item.key === "document") {
        const meta = collectMetaLines(globalThis.document);
        if (meta) {
          blocks.push(meta);
        }
      }

      item.targets.forEach((target) => {
        const renderedTarget = renderElementAsBlock(target, captureContext);
        if (renderedTarget) {
          blocks.push(renderedTarget);
        }
      });

      snapshot[item.key] = cleanReadableMarkdown(joinBlocks(blocks));
    });

    state.captureId += 1;
    state.capturedAt = Date.now();
    state.backend = "live";
    state.captureOptions = { ...captureContext.options };
    state.entries = captureContext.entries;
    return snapshot;
  }

  async function captureWithDomHelper(payload = null) {
    const helper = requireDomHelper("capture content");
    const selectors = normalizeSelectorList(payload);
    const helperPayload = {
      snapshotMode: "content"
    };
    if (selectors.length) {
      helperPayload.selectors = selectors;
    }
    const documentSnapshot = await helper.captureDocument({
      ...helperPayload
    });
    const snapshot = {};
    const parser = new globalThis.DOMParser();
    const captureContext = createCaptureContext(payload);
    try {
      if (selectors.length && documentSnapshot?.targets && typeof documentSnapshot.targets === "object") {
        selectors.forEach((selector) => {
          snapshot[selector] = renderSnapshotFragment(documentSnapshot.targets?.[selector] || "", captureContext, parser);
        });

        state.captureId += 1;
        state.capturedAt = Date.now();
        state.backend = "dom_helper";
        state.captureOptions = { ...captureContext.options };
        state.entries = captureContext.entries;
        return snapshot;
      }

      const parsedDocument = parser.parseFromString(String(documentSnapshot?.html || ""), "text/html");
      const resolvedTargets = resolveSelectorTargets(payload, parsedDocument);

      resolvedTargets.items.forEach((item) => {
        const blocks = [];
        if (resolvedTargets.includeMetaData && item.key === "document") {
          const meta = collectMetaLines(parsedDocument);
          if (meta) {
            blocks.push(meta);
          }
        }

        item.targets.forEach((target) => {
          const renderedTarget = renderElementAsBlock(target, captureContext);
          if (renderedTarget) {
            blocks.push(renderedTarget);
          }
        });

        snapshot[item.key] = cleanReadableMarkdown(joinBlocks(blocks));
      });

      state.captureId += 1;
      state.capturedAt = Date.now();
      state.backend = "dom_helper";
      state.captureOptions = { ...captureContext.options };
      state.entries = captureContext.entries;
      return snapshot;
    } catch (error) {
      if (!isTrustedHtmlRequirementError(error)) {
        throw error;
      }

      return captureLive(payload);
    }
  }

  async function capture(payload = null) {
    if (getDomHelper()) {
      return captureWithDomHelper(payload);
    }

    return captureLive(payload);
  }

  function detailLive(entry) {
    const liveState = entry.connected && entry.element
      ? collectElementStateMetadata(entry.element, state.captureOptions)
      : entry.state || collectElementStateMetadata(null);
    return {
      captureId: state.captureId,
      capturedAt: state.capturedAt,
      connected: entry.connected,
      descriptorTags: liveState.descriptorTags,
      dom: entry.connected ? serializeElementSnapshot(entry.element) || entry.dom : entry.dom,
      referenceId: entry.referenceId,
      semanticTags: liveState.semanticTags,
      state: liveState,
      summary: entry.summary,
      tagName: entry.tagName
    };
  }

  async function detail(referenceId) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "detail",
      requireConnected: false
    });

    if (entry.helperBacked) {
      const helper = requireDomHelper("resolve detail");
      const resolvedDetail = await helper.detailNode(entry.frameChain, entry.nodeId);
      return {
        captureId: state.captureId,
        capturedAt: state.capturedAt,
        connected: resolvedDetail?.connected !== false,
        descriptorTags: Array.isArray(resolvedDetail?.descriptorTags) ? resolvedDetail.descriptorTags : (entry.descriptorTags || []),
        dom: String(resolvedDetail?.dom || entry.dom || ""),
        frameChain: entry.frameChain.slice(),
        frameId: entry.frameId,
        nodeId: entry.nodeId,
        referenceId: entry.referenceId,
        semanticTags: Array.isArray(resolvedDetail?.semanticTags) ? resolvedDetail.semanticTags : (entry.semanticTags || []),
        state: resolvedDetail?.state || entry.state || collectElementStateMetadata(null),
        summary: entry.summary,
        tagName: String(resolvedDetail?.tagName || entry.tagName || "")
      };
    }

    return detailLive(entry);
  }

  function requireReferenceEntry(referenceId, options = {}) {
    const normalizedReferenceId = normalizeReferenceId(referenceId);
    if (!normalizedReferenceId) {
      throw createNamedError(
        "BrowserPageContentReferenceError",
        "Browser page content requests require a reference id.",
        {
          code: "browser_page_content_reference_required",
          details: {
            action: String(options.actionLabel || "resolve")
          }
        }
      );
    }

    if (!state.entries.size) {
      throw createNamedError(
        "BrowserPageContentReferenceError",
        `Browser page content has no reference capture for "${normalizedReferenceId}".`,
        {
          code: "browser_page_content_reference_missing_capture",
          details: {
            action: String(options.actionLabel || "resolve"),
            referenceId: normalizedReferenceId
          }
        }
      );
    }

    const entry = state.entries.get(normalizedReferenceId);
    if (!entry) {
      throw createNamedError(
        "BrowserPageContentReferenceError",
        `Browser page content could not find reference "${normalizedReferenceId}".`,
        {
          code: "browser_page_content_reference_not_found",
          details: {
            action: String(options.actionLabel || "resolve"),
            referenceId: normalizedReferenceId
          }
        }
      );
    }

    refreshReferenceEntry(entry);

    if (options.requireConnected !== false && !entry.connected) {
      throw createNamedError(
        "BrowserPageContentReferenceError",
        `Browser page content reference "${normalizedReferenceId}" is no longer connected.`,
        {
          code: "browser_page_content_reference_disconnected",
          details: {
            action: String(options.actionLabel || "resolve"),
            referenceId: normalizedReferenceId
          }
        }
      );
    }

    return entry;
  }

  function computeStableSelector(el) {
    if (!el || el.nodeType !== 1) return null;
    const doc = el.ownerDocument || document;
    if (el.id && /^[A-Za-z_][\w-]*$/.test(el.id)) {
      const sel = "#" + (typeof CSS !== "undefined" && CSS.escape ? CSS.escape(el.id) : el.id);
      try {
        if (doc.querySelectorAll(sel).length === 1) return sel;
      } catch (_) {}
    }
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && node !== doc.documentElement) {
      let part = node.tagName.toLowerCase();
      if (node.id && /^[A-Za-z_][\w-]*$/.test(node.id)) {
        const idSel = "#" + (typeof CSS !== "undefined" && CSS.escape ? CSS.escape(node.id) : node.id);
        try {
          if (doc.querySelectorAll(idSel).length === 1) {
            parts.unshift(idSel);
            break;
          }
        } catch (_) {}
      }
      const parent = node.parentElement;
      if (parent) {
        const sibs = parent.children;
        let idx = 0;
        let sameTag = 0;
        for (let i = 0; i < sibs.length; i++) {
          if (sibs[i].tagName === node.tagName) {
            sameTag++;
            if (sibs[i] === node) idx = sameTag;
          }
        }
        if (sameTag > 1) part += ":nth-of-type(" + idx + ")";
      }
      parts.unshift(part);
      node = parent;
    }
    const sel = parts.join(" > ");
    if (!sel) return null;
    try {
      if (doc.querySelectorAll(sel).length === 1) return sel;
    } catch (_) {}
    return null;
  }

  function boundingBoxFor(referenceId) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "boundingBox",
      requireConnected: false
    });
    if (entry.helperBacked || !entry.element) return null;
    const el = entry.element;
    if (typeof el.getBoundingClientRect !== "function") return null;
    try {
      el.scrollIntoView({ block: "center", inline: "center", behavior: "instant" });
    } catch (_) {}
    const r = el.getBoundingClientRect();
    const selector = computeStableSelector(el);
    const hasBox = r && r.width > 0 && r.height > 0;
    if (!hasBox && !selector) return null;
    return {
      x: hasBox ? r.left : 0,
      y: hasBox ? r.top : 0,
      width: hasBox ? r.width : 0,
      height: hasBox ? r.height : 0,
      selector: selector || null
    };
  }

  function pointFor(referenceId, offsets = {}) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "point",
      requireConnected: true
    });
    if (entry.helperBacked || !entry.element) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content cannot resolve point for helper-backed reference "${entry.referenceId}".`,
        {
          code: "browser_page_content_point_helper_backed"
        }
      );
    }

    const element = entry.element;
    scrollElementIntoView(element);
    const rect = getElementRectSafe(element);
    if (!rect || rect.width <= 0 || rect.height <= 0) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content reference "${entry.referenceId}" has no visible viewport box.`,
        {
          code: "browser_page_content_point_no_box"
        }
      );
    }

    const offsetX = Number(offsets?.offset_x ?? offsets?.offsetX ?? 0) || 0;
    const offsetY = Number(offsets?.offset_y ?? offsets?.offsetY ?? 0) || 0;
    const useOffsets = offsets?.useOffsets === true || offsetX !== 0 || offsetY !== 0;
    return {
      rect,
      selector: computeStableSelector(element),
      x: rect.x + (useOffsets ? offsetX : rect.width / 2),
      y: rect.y + (useOffsets ? offsetY : rect.height / 2)
    };
  }

  function normalizeActionValues(valueOrValues) {
    if (Array.isArray(valueOrValues)) {
      return valueOrValues.map((value) => String(value ?? ""));
    }

    if (valueOrValues === null || valueOrValues === undefined) {
      return [];
    }

    return [String(valueOrValues)];
  }

  function optionMatchesValue(option, value) {
    const normalizedValue = normalizeText(value);
    const candidates = [
      option?.value,
      option?.label,
      option?.textContent,
      option?.getAttribute?.("aria-label"),
      option?.getAttribute?.("data-value"),
      option?.getAttribute?.("id")
    ].map((candidate) => normalizeText(candidate));
    return candidates.some((candidate) => candidate === normalizedValue);
  }

  function findNativeSelectOption(selectElement, value) {
    const options = [...(selectElement.options || [])];
    return options.find((option) => optionMatchesValue(option, value)) || null;
  }

  function setNativeChecked(element, checked) {
    const descriptor = Object.getOwnPropertyDescriptor(globalThis.HTMLInputElement?.prototype || {}, "checked");
    if (typeof descriptor?.set === "function") {
      descriptor.set.call(element, Boolean(checked));
    } else {
      element.checked = Boolean(checked);
    }
  }

  async function selectNativeElement(entry, values) {
    const element = entry.element;
    const beforeSnapshot = captureActionEffectSnapshot(element);
    const requestedValues = values.length ? values : [""];
    const appliedValues = [];

    const {
      observedMutations
    } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);

      if (element.multiple) {
        const matchedOptions = requestedValues.map((requestedValue) => {
          const option = findNativeSelectOption(element, requestedValue);
          if (!option) {
            throw createNamedError(
              "BrowserPageContentActionError",
              `Browser page content could not find select option "${requestedValue}".`,
              {
                code: "browser_page_content_select_option_not_found"
              }
            );
          }
          return option;
        });
        const matchedSet = new Set(matchedOptions);
        [...(element.options || [])].forEach((option) => {
          option.selected = matchedSet.has(option);
        });
        matchedOptions.forEach((option) => appliedValues.push(option.value));
      } else {
        const option = findNativeSelectOption(element, requestedValues[0]);
        if (!option) {
          throw createNamedError(
            "BrowserPageContentActionError",
            `Browser page content could not find select option "${requestedValues[0]}".`,
            {
              code: "browser_page_content_select_option_not_found"
            }
          );
        }
        appliedValues.push(setNativeValue(element, option.value));
      }

      dispatchDomEvent(element, "input", "InputEvent", {
        inputType: "insertReplacementText"
      });
      dispatchDomEvent(element, "change");
      return appliedValues.slice();
    });

    refreshReferenceEntry(entry);
    return buildActionResult(entry, {
      ...buildActionEffectResult(entry, beforeSnapshot, captureActionEffectSnapshot(element), observedMutations),
      values: appliedValues.slice()
    });
  }

  function ariaOptionMatchesValue(option, value) {
    const normalizedValue = normalizeText(value);
    const candidates = [
      option?.getAttribute?.("aria-label"),
      option?.getAttribute?.("data-value"),
      option?.getAttribute?.("value"),
      option?.getAttribute?.("id"),
      getElementText(option)
    ].map((candidate) => normalizeText(candidate));
    return candidates.some((candidate) => candidate === normalizedValue);
  }

  function visibleAriaOptions(root) {
    const scope = isElementNode(root) && String(root.getAttribute?.("role") || "").trim().toLowerCase() === "listbox"
      ? root
      : globalThis.document;
    try {
      return [...(scope.querySelectorAll?.("[role='option']") || [])]
        .filter((option) => isElementNode(option) && !isHiddenElement(option));
    } catch {
      return [];
    }
  }

  function findAriaOption(root, value) {
    const matches = visibleAriaOptions(root).filter((option) => ariaOptionMatchesValue(option, value));
    return matches.length === 1 ? matches[0] : null;
  }

  async function selectAriaElement(entry, values) {
    const element = entry.element;
    const role = String(element.getAttribute?.("role") || "").trim().toLowerCase();
    if (!["combobox", "listbox"].includes(role)) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content cannot select options on <${getTagName(element).toLowerCase()}>.`,
        {
          code: "browser_page_content_select_unsupported"
        }
      );
    }

    const beforeSnapshot = captureActionEffectSnapshot(element);
    const requestedValues = values.length ? values : [""];
    const appliedValues = [];
    const {
      observedMutations
    } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);
      if (role === "combobox") {
        dispatchDomEvent(element, "mousedown", "MouseEvent", { button: 0 });
        if (typeof element.click === "function") {
          element.click();
        } else {
          dispatchDomEvent(element, "click", "MouseEvent", { button: 0 });
        }
        await delayMs(80);
      }

      for (const requestedValue of requestedValues) {
        const option = findAriaOption(element, requestedValue);
        if (!option) {
          throw createNamedError(
            "BrowserPageContentActionError",
            `Browser page content could not safely find one ARIA option "${requestedValue}".`,
            {
              code: "browser_page_content_aria_option_not_found"
            }
          );
        }
        scrollElementIntoView(option);
        dispatchDomEvent(option, "mousedown", "MouseEvent", { button: 0 });
        if (typeof option.click === "function") {
          option.click();
        } else {
          dispatchDomEvent(option, "click", "MouseEvent", { button: 0 });
        }
        appliedValues.push(requestedValue);
        await delayMs(40);
      }
    });

    refreshReferenceEntry(entry);
    return buildActionResult(entry, {
      ...buildActionEffectResult(entry, beforeSnapshot, captureActionEffectSnapshot(element), observedMutations),
      values: appliedValues.slice()
    });
  }

  async function selectReference(referenceId, valueOrValues) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "select"
    });
    if (entry.helperBacked) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content cannot select helper-backed reference "${entry.referenceId}".`,
        {
          code: "browser_page_content_select_helper_backed"
        }
      );
    }

    const element = entry.element;
    const values = normalizeActionValues(valueOrValues);
    if (getTagName(element) === "SELECT") {
      return selectNativeElement(entry, values);
    }

    return selectAriaElement(entry, values);
  }

  function checkedStateForElement(element) {
    const tagName = getTagName(element);
    const role = String(element.getAttribute?.("role") || "").trim().toLowerCase();
    if (tagName === "INPUT") {
      const inputType = String(element.getAttribute?.("type") || element.type || "").toLowerCase();
      if (["checkbox", "radio"].includes(inputType)) {
        return Boolean(element.checked);
      }
    }
    if (["checkbox", "radio", "switch", "menuitemcheckbox", "menuitemradio"].includes(role)) {
      return String(element.getAttribute?.("aria-checked") || "").trim().toLowerCase() === "true";
    }
    if (role === "button" && element.hasAttribute?.("aria-pressed")) {
      return String(element.getAttribute?.("aria-pressed") || "").trim().toLowerCase() === "true";
    }
    return null;
  }

  async function setCheckedReference(referenceId, checked = true) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "setChecked"
    });
    if (entry.helperBacked) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content cannot set helper-backed reference "${entry.referenceId}".`,
        {
          code: "browser_page_content_checked_helper_backed"
        }
      );
    }

    const element = entry.element;
    const beforeSnapshot = captureActionEffectSnapshot(element);
    const desiredChecked = Boolean(checked);
    const tagName = getTagName(element);
    const role = String(element.getAttribute?.("role") || "").trim().toLowerCase();
    const currentChecked = checkedStateForElement(element);
    if (currentChecked === null) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content cannot set checked state on <${tagName.toLowerCase()}>.`,
        {
          code: "browser_page_content_checked_unsupported"
        }
      );
    }

    const {
      observedMutations
    } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);

      if (tagName === "INPUT") {
        setNativeChecked(element, desiredChecked);
        dispatchDomEvent(element, "input", "InputEvent", {
          inputType: "insertReplacementText"
        });
        dispatchDomEvent(element, "change");
      } else if (["checkbox", "radio", "switch", "menuitemcheckbox", "menuitemradio"].includes(role)) {
        if (currentChecked !== desiredChecked) {
          if (typeof element.click === "function") {
            element.click();
          } else {
            dispatchDomEvent(element, "click", "MouseEvent", {
              button: 0
            });
          }
          await delayMs(40);
        }
        if (checkedStateForElement(element) !== desiredChecked) {
          element.setAttribute("aria-checked", desiredChecked ? "true" : "false");
          dispatchDomEvent(element, "input", "InputEvent", {
            inputType: "insertReplacementText"
          });
          dispatchDomEvent(element, "change");
        }
      } else if (role === "button" && element.hasAttribute?.("aria-pressed")) {
        if (currentChecked !== desiredChecked) {
          if (typeof element.click === "function") {
            element.click();
          } else {
            dispatchDomEvent(element, "click", "MouseEvent", {
              button: 0
            });
          }
          await delayMs(40);
        }
        if (checkedStateForElement(element) !== desiredChecked) {
          element.setAttribute("aria-pressed", desiredChecked ? "true" : "false");
        }
      }
    });

    refreshReferenceEntry(entry);
    return buildActionResult(entry, {
      ...buildActionEffectResult(entry, beforeSnapshot, captureActionEffectSnapshot(element), observedMutations),
      checked: desiredChecked
    });
  }

  function resolveFileInputElement(referenceId) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "fileInput"
    });
    if (entry.helperBacked) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content cannot upload files through helper-backed reference "${entry.referenceId}".`,
        {
          code: "browser_page_content_file_input_helper_backed"
        }
      );
    }

    const element = entry.element;
    const isFileInput = (candidate) => {
      return getTagName(candidate) === "INPUT"
        && String(candidate.getAttribute?.("type") || candidate.type || "").toLowerCase() === "file";
    };

    if (isFileInput(element)) {
      return element;
    }

    if (getTagName(element) === "LABEL") {
      if (isFileInput(element.control)) {
        return element.control;
      }
      const labelledInput = element.querySelector?.("input[type='file']");
      if (isFileInput(labelledInput)) {
        return labelledInput;
      }
      const forId = normalizeAttributeText(element.getAttribute?.("for"));
      if (forId) {
        const byId = element.ownerDocument?.getElementById?.(forId);
        if (isFileInput(byId)) {
          return byId;
        }
      }
    }

    const descendantInput = element.querySelector?.("input[type='file']");
    if (isFileInput(descendantInput)) {
      return descendantInput;
    }

    const closestLabel = element.closest?.("label");
    if (closestLabel) {
      if (isFileInput(closestLabel.control)) {
        return closestLabel.control;
      }
      const labelledInput = closestLabel.querySelector?.("input[type='file']");
      if (isFileInput(labelledInput)) {
        return labelledInput;
      }
    }

    return null;
  }

  function fileInputFor(referenceId) {
    const input = resolveFileInputElement(referenceId);
    if (!input) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content reference "${normalizeReferenceId(referenceId)}" is not a file input or associated label.`,
        {
          code: "browser_page_content_file_input_not_found"
        }
      );
    }
    return {
      accept: normalizeAttributeText(input.getAttribute?.("accept")),
      multiple: Boolean(input.multiple),
      name: normalizeAttributeText(input.getAttribute?.("name")),
      selector: computeStableSelector(input),
      tagName: getTagName(input),
      type: String(input.getAttribute?.("type") || input.type || "").toLowerCase()
    };
  }

  function fileInputElementFor(referenceId) {
    return resolveFileInputElement(referenceId);
  }

  function refreshReferenceEntry(entry) {
    if (!entry || entry.helperBacked || !entry.element) {
      return entry;
    }

    entry.connected = entry.element.isConnected !== false;
    if (entry.connected) {
      entry.dom = serializeElementSnapshot(entry.element) || entry.dom;
      entry.id = normalizeAttributeText(entry.element.getAttribute?.("id"));
      entry.name = normalizeAttributeText(entry.element.getAttribute?.("name"));
      const summaryData = collectReferenceSummaryData(entry.element, state.captureOptions);
      entry.descriptorTags = summaryData.descriptorTags;
      entry.kind = summaryData.kind;
      entry.semanticTags = summaryData.semanticTags;
      entry.state = summaryData.state;
      entry.summary = summaryData.summary;
      entry.tagName = getTagName(entry.element);
    }

    return entry;
  }

  function scrollElementIntoView(element) {
    try {
      element.scrollIntoView?.({
        behavior: "auto",
        block: "center",
        inline: "center"
      });
      return true;
    } catch {
      return false;
    }
  }

  function focusElement(element) {
    try {
      element.focus?.({
        preventScroll: true
      });
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

  function describeActiveElement(element) {
    if (!isElementNode(element)) {
      return "";
    }

    const tagName = getTagName(element).toLowerCase();
    const id = normalizeAttributeText(element.getAttribute?.("id"));
    const name = normalizeAttributeText(element.getAttribute?.("name"));
    const label = truncateText(getLabelText(element, {
      includeAlt: false,
      includeDescendantImageAlt: true,
      includePlaceholder: false,
      includeText: false
    }), 48);
    return [tagName, id ? `#${id}` : "", name ? `name=${name}` : "", label].filter(Boolean).join(" ");
  }

  function getActionObservationRoot(element) {
    if (!isElementNode(element)) {
      return globalThis.document?.body || globalThis.document?.documentElement || null;
    }

    return element.closest?.("form, fieldset, dialog, [role='dialog'], [role='alert'], [role='status'], [aria-live], article, section, main, li, tr, td, th")
      || element.parentElement
      || element;
  }

  function getElementDirectText(element) {
    if (!isElementNode(element)) {
      return "";
    }

    return normalizeText(
      [...(element.childNodes || [])]
        .filter((node) => isTextNode(node))
        .map((node) => node.textContent || "")
        .join(" ")
    );
  }

  function collectNearbyTextEntries(root, limit = 24) {
    if (!isElementNode(root)) {
      return [];
    }

    const entries = [];
    const seen = new Set();
    const acceptElement = (element) => {
      if (!isElementNode(element) || isHiddenElement(element) || entries.length >= limit) {
        return;
      }

      const role = normalizeText(element.getAttribute?.("role")).toLowerCase();
      const directText = getElementDirectText(element);
      const fallbackText = ["alert", "status"].includes(role) || element.hasAttribute?.("aria-live")
        ? getElementText(element)
        : "";
      const text = truncateText(directText || fallbackText, 220);
      if (!text) {
        return;
      }

      const key = `${role}|${text}`;
      if (seen.has(key)) {
        return;
      }
      seen.add(key);
      const state = collectElementStateMetadata(element, {
        includeSemanticTags: true,
        includeStateTags: true
      });
      entries.push({
        invalid: state.invalid === true,
        role,
        semanticTone: state.semanticTone || "",
        text
      });
    };

    acceptElement(root);
    const walker = globalThis.document?.createTreeWalker?.(root, globalThis.NodeFilter?.SHOW_ELEMENT ?? 1);
    if (!walker) {
      return entries;
    }

    let currentNode = walker.nextNode();
    while (currentNode && entries.length < limit) {
      acceptElement(currentNode);
      currentNode = walker.nextNode();
    }

    return entries;
  }

  function captureActionEffectSnapshot(element) {
    const observationRoot = getActionObservationRoot(element);
    return {
      activeElement: describeActiveElement(globalThis.document?.activeElement),
      observationRoot,
      observationText: truncateText(getElementText(observationRoot), 2000),
      targetDom: truncateText(serializeElementSnapshot(element), 2000),
      targetState: collectElementStateMetadata(element, {
        includeSemanticTags: true,
        includeStateTags: true
      }),
      textEntries: collectNearbyTextEntries(observationRoot),
      value: getReferenceValueMetadata(element)
    };
  }

  async function waitForObservedActionWindow(observationRoot, {
    quietMs = 40,
    timeoutMs = 180
  } = {}) {
    const target = observationRoot?.ownerDocument?.body
      || observationRoot?.ownerDocument?.documentElement
      || globalThis.document?.body
      || globalThis.document?.documentElement;
    if (!target || typeof globalThis.MutationObserver !== "function") {
      await delayMs(timeoutMs);
      return {
        attributeNames: [],
        mutationCount: 0
      };
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
      const startedAt = Date.now();
      while (Date.now() - startedAt < timeoutMs) {
        await delayMs(20);
        if (mutationCount > 0 && Date.now() - lastMutationAt >= quietMs) {
          break;
        }
      }
    } finally {
      observer.disconnect();
    }

    return {
      attributeNames: [...attributeNames],
      mutationCount
    };
  }

  async function withObservedActionWindow(observationRoot, action, options = {}) {
    const target = observationRoot?.ownerDocument?.body
      || observationRoot?.ownerDocument?.documentElement
      || globalThis.document?.body
      || globalThis.document?.documentElement;
    if (!target || typeof globalThis.MutationObserver !== "function") {
      const result = await action();
      const observedMutations = await waitForObservedActionWindow(observationRoot, options);
      return {
        observedMutations,
        result
      };
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
      const quietMs = Math.max(0, Number(options.quietMs) || 40);
      const timeoutMs = Math.max(0, Number(options.timeoutMs) || 180);
      const startedAt = Date.now();
      while (Date.now() - startedAt < timeoutMs) {
        await delayMs(20);
        if (mutationCount > 0 && Date.now() - lastMutationAt >= quietMs) {
          break;
        }
      }
      return {
        observedMutations: {
          attributeNames: [...attributeNames],
          mutationCount
        },
        result
      };
    } finally {
      observer.disconnect();
    }
  }

  function compareDescriptorTags(beforeTags = [], afterTags = []) {
    const beforeValue = beforeTags.filter(Boolean).join("|");
    const afterValue = afterTags.filter(Boolean).join("|");
    return beforeValue !== afterValue;
  }

  function buildActionEffectResult(entry, beforeSnapshot, afterSnapshot, observedMutations, extra = {}) {
    const newTextEntries = afterSnapshot.textEntries.filter((entryData) => {
      return !beforeSnapshot.textEntries.some((beforeEntry) => beforeEntry.text === entryData.text);
    });
    const validationEntries = newTextEntries.filter((entryData) => {
      return entryData.invalid
        || ["alert", "status"].includes(entryData.role)
        || ["error", "warning"].includes(entryData.semanticTone);
    });
    const focusChanged = beforeSnapshot.activeElement !== afterSnapshot.activeElement;
    const nearbyTextChanged = beforeSnapshot.observationText !== afterSnapshot.observationText;
    const valueChanged = beforeSnapshot.value !== afterSnapshot.value;
    const checkedChanged = beforeSnapshot.targetState.checked !== afterSnapshot.targetState.checked;
    const selectedChanged = beforeSnapshot.targetState.selected !== afterSnapshot.targetState.selected;
    const expandedChanged = beforeSnapshot.targetState.expanded !== afterSnapshot.targetState.expanded;
    const pressedChanged = beforeSnapshot.targetState.pressed !== afterSnapshot.targetState.pressed;
    const descriptorChanged = compareDescriptorTags(beforeSnapshot.targetState.descriptorTags, afterSnapshot.targetState.descriptorTags);
    const targetDomChanged = beforeSnapshot.targetDom !== afterSnapshot.targetDom;
    const domChanged = Boolean(observedMutations.mutationCount) || targetDomChanged || nearbyTextChanged;
    const status = {
      alertTextAdded: newTextEntries.some((entryData) => ["alert", "status"].includes(entryData.role)),
      checkedChanged,
      descriptorChanged,
      domChanged,
      expandedChanged,
      focusChanged,
      nearbyTextChanged,
      pressedChanged,
      reacted: false,
      selectedChanged,
      targetChanged: descriptorChanged || targetDomChanged || valueChanged || checkedChanged || selectedChanged || expandedChanged || pressedChanged,
      targetDomChanged,
      valueChanged,
      validationTextAdded: validationEntries.length > 0
    };
    status.reacted = Object.entries(status).some(([key, value]) => key !== "reacted" && value === true);
    status.noObservedEffect = !status.reacted;

    return {
      ...extra,
      descriptorTags: afterSnapshot.targetState.descriptorTags.slice(),
      effect: {
        mutationAttributes: observedMutations.attributeNames.slice(0, 8),
        mutationCount: observedMutations.mutationCount,
        newText: newTextEntries.map((entryData) => entryData.text).slice(0, 3),
        semanticHints: [...new Set(newTextEntries.map((entryData) => entryData.semanticTone).filter(Boolean))].slice(0, 3),
        validationText: validationEntries.map((entryData) => entryData.text).slice(0, 3)
      },
      semanticTags: afterSnapshot.targetState.semanticTags.slice(),
      state: afterSnapshot.targetState,
      status
    };
  }

  function buildActionResult(entry, extra = {}) {
    return {
      captureId: state.captureId,
      descriptorTags: Array.isArray(entry?.descriptorTags) ? entry.descriptorTags.slice() : [],
      referenceId: entry.referenceId,
      semanticTags: Array.isArray(entry?.semanticTags) ? entry.semanticTags.slice() : [],
      state: entry.state || collectElementStateMetadata(entry.element, state.captureOptions),
      summary: entry.summary,
      tagName: entry.tagName,
      ...extra
    };
  }

  function buildHelperBackedActionResult(entry, helperResult, extra = {}) {
    return {
      captureId: state.captureId,
      descriptorTags: Array.isArray(helperResult?.descriptorTags) ? helperResult.descriptorTags : (entry.descriptorTags || []),
      frameChain: entry.frameChain.slice(),
      frameId: entry.frameId,
      nodeId: entry.nodeId,
      referenceId: entry.referenceId,
      semanticTags: Array.isArray(helperResult?.semanticTags) ? helperResult.semanticTags : (entry.semanticTags || []),
      state: helperResult?.state || entry.state || collectElementStateMetadata(null),
      summary: entry.summary,
      tagName: String(helperResult?.tagName || entry.tagName || ""),
      ...extra
    };
  }

  function mergeActionOutcomeResults(...results) {
    const normalizedResults = results.filter(Boolean);
    const mergedStatus = {};
    const mergedEffect = {
      mutationAttributes: [],
      mutationCount: 0,
      newText: [],
      semanticHints: [],
      validationText: []
    };

    normalizedResults.forEach((result) => {
      Object.entries(result?.status || {}).forEach(([key, value]) => {
        if (typeof value === "boolean") {
          mergedStatus[key] = mergedStatus[key] === true || value === true;
        }
      });
      if (Number.isFinite(result?.effect?.mutationCount)) {
        mergedEffect.mutationCount += Number(result.effect.mutationCount);
      }
      ["mutationAttributes", "newText", "semanticHints", "validationText"].forEach((key) => {
        const values = Array.isArray(result?.effect?.[key]) ? result.effect[key] : [];
        values.forEach((value) => {
          if (value && !mergedEffect[key].includes(value)) {
            mergedEffect[key].push(value);
          }
        });
      });
    });

    mergedStatus.reacted = Object.entries(mergedStatus).some(([key, value]) => key !== "reacted" && key !== "noObservedEffect" && value === true);
    mergedStatus.noObservedEffect = !mergedStatus.reacted;
    return {
      effect: mergedEffect,
      status: mergedStatus
    };
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
      ...options
    });

    [
      ["charCode", Number(options.charCode ?? 0)],
      ["keyCode", Number(options.keyCode ?? 13)],
      ["which", Number(options.which ?? 13)]
    ].forEach(([propertyName, propertyValue]) => {
      try {
        if (typeof event[propertyName] !== "number") {
          Object.defineProperty(event, propertyName, {
            configurable: true,
            enumerable: true,
            value: propertyValue
          });
        }
      } catch {
        // Ignore read-only KeyboardEvent properties.
      }
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
      const matchedOption = [...(element.options || [])].find((option) => {
        return option.value === normalizedValue
          || normalizeText(option.textContent || "") === normalizeText(normalizedValue)
          || normalizeText(option.label || "") === normalizeText(normalizedValue);
      });

      const resolvedValue = matchedOption ? matchedOption.value : normalizedValue;
      const descriptor = Object.getOwnPropertyDescriptor(globalThis.HTMLSelectElement?.prototype || {}, "value");
      if (typeof descriptor?.set === "function") {
        descriptor.set.call(element, resolvedValue);
      } else {
        element.value = resolvedValue;
      }
      return resolvedValue;
    }

    if (String(element.getAttribute?.("contenteditable") || "").toLowerCase() === "true") {
      element.textContent = normalizedValue;
      return normalizedValue;
    }

    throw createNamedError(
      "BrowserPageContentActionError",
      `Browser page content cannot type into <${getTagName(element).toLowerCase()}>.`,
      {
        code: "browser_page_content_type_unsupported"
      }
    );
  }

  async function updateElementValue(referenceId, value) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "type"
    });

    if (entry.helperBacked) {
      const helper = requireDomHelper("type into reference");
      const typedResult = await helper.typeNode(entry.frameChain, entry.nodeId, value);
      return buildHelperBackedActionResult(entry, typedResult, {
        effect: typedResult?.effect || {},
        status: typedResult?.status || {},
        value: typedResult?.value ?? String(value ?? "")
      });
    }

    const element = entry.element;
    const beforeSnapshot = captureActionEffectSnapshot(element);

    const {
      result: appliedValue,
      observedMutations
    } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);
      const nextValue = setNativeValue(element, value);

      if (typeof element.setSelectionRange === "function") {
        try {
          element.setSelectionRange(String(nextValue).length, String(nextValue).length);
        } catch {
          // Ignore selection errors for unsupported input types.
        }
      }

      dispatchDomEvent(element, "beforeinput", "InputEvent", {
        data: String(value ?? ""),
        inputType: "insertText"
      });
      dispatchDomEvent(element, "input", "InputEvent", {
        data: String(value ?? ""),
        inputType: "insertText"
      });
      dispatchDomEvent(element, "change");
      return nextValue;
    });

    refreshReferenceEntry(entry);
    return buildActionResult(entry, {
      ...buildActionEffectResult(entry, beforeSnapshot, captureActionEffectSnapshot(element), observedMutations),
      value: appliedValue
    });
  }

  async function activateElement(referenceId) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "click"
    });

    if (entry.helperBacked) {
      const helper = requireDomHelper("click reference");
      const clickedResult = await helper.clickNode(entry.frameChain, entry.nodeId);
      return buildHelperBackedActionResult(entry, clickedResult, {
        effect: clickedResult?.effect || {},
        status: clickedResult?.status || {}
      });
    }

    const element = entry.element;
    const beforeSnapshot = captureActionEffectSnapshot(element);

    scrollElementIntoView(element);
    focusElement(element);

    if (beforeSnapshot.targetState.disabled) {
      throw createNamedError(
        "BrowserPageContentActionError",
        `Browser page content reference "${entry.referenceId}" is disabled.`,
        {
          code: "browser_page_content_click_disabled"
        }
      );
    }

    const {
      observedMutations
    } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      if (typeof element.click === "function") {
        element.click();
      } else {
        dispatchDomEvent(element, "click", "MouseEvent", {
          button: 0
        });
      }
    });

    refreshReferenceEntry(entry);
    return buildActionResult(entry, buildActionEffectResult(
      entry,
      beforeSnapshot,
      captureActionEffectSnapshot(element),
      observedMutations
    ));
  }

  async function submitElement(referenceId) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "submit"
    });

    if (entry.helperBacked) {
      const helper = requireDomHelper("submit reference");
      const submittedResult = await helper.submitNode(entry.frameChain, entry.nodeId);
      return buildHelperBackedActionResult(entry, submittedResult, {
        effect: submittedResult?.effect || {},
        status: submittedResult?.status || {}
      });
    }

    const element = entry.element;
    const tagName = getTagName(element);
    const beforeSnapshot = captureActionEffectSnapshot(element);

    const {
      observedMutations
    } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);

      if (tagName === "FORM") {
        if (typeof element.requestSubmit === "function") {
          element.requestSubmit();
        } else {
          const submitEvent = dispatchDomEvent(element, "submit");
          if (!submitEvent.defaultPrevented) {
            element.submit?.();
          }
        }
      } else if (typeof element.form?.requestSubmit === "function") {
        if (tagName === "BUTTON" || tagName === "INPUT") {
          element.form.requestSubmit(element);
        } else {
          element.form.requestSubmit();
        }
      } else if (element.form) {
        const submitEvent = dispatchDomEvent(element.form, "submit");
        if (!submitEvent.defaultPrevented) {
          element.form.submit?.();
        }
      } else if (typeof element.click === "function") {
        element.click();
      } else {
        throw createNamedError(
          "BrowserPageContentActionError",
          `Browser page content cannot submit reference "${entry.referenceId}".`,
          {
            code: "browser_page_content_submit_unsupported"
          }
        );
      }
    });

    refreshReferenceEntry(entry);
    return buildActionResult(entry, buildActionEffectResult(
      entry,
      beforeSnapshot,
      captureActionEffectSnapshot(element),
      observedMutations
    ));
  }

  function shouldEnterSubmitForm(element) {
    const tagName = getTagName(element);
    if (tagName !== "INPUT") {
      return false;
    }

    const inputType = String(element.getAttribute?.("type") || element.type || "text").toLowerCase();
    return ![
      "button",
      "checkbox",
      "color",
      "file",
      "hidden",
      "image",
      "radio",
      "range",
      "reset",
      "submit"
    ].includes(inputType);
  }

  async function pressEnterElement(referenceId, actionLabel = "type_submit") {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel
    });

    if (entry.helperBacked) {
      const helper = requireDomHelper("press enter on reference");
      const submittedResult = await helper.typeSubmitNode(entry.frameChain, entry.nodeId, "");
      return buildHelperBackedActionResult(entry, submittedResult, {
        effect: submittedResult?.effect || {},
        status: submittedResult?.status || {}
      });
    }

    const element = entry.element;
    const beforeSnapshot = captureActionEffectSnapshot(element);

    const {
      observedMutations
    } = await withObservedActionWindow(beforeSnapshot.observationRoot, async () => {
      scrollElementIntoView(element);
      focusElement(element);

      const keydownEvent = dispatchKeyboardEvent(element, "keydown", {
        charCode: 0,
        keyCode: 13,
        which: 13
      });
      const keypressEvent = dispatchKeyboardEvent(element, "keypress", {
        charCode: 13,
        keyCode: 13,
        which: 13
      });
      const keyupEvent = dispatchKeyboardEvent(element, "keyup", {
        charCode: 0,
        keyCode: 13,
        which: 13
      });

      if (
        !keydownEvent.defaultPrevented
        && !keypressEvent.defaultPrevented
        && !keyupEvent.defaultPrevented
        && shouldEnterSubmitForm(element)
      ) {
        if (typeof element.form?.requestSubmit === "function") {
          element.form.requestSubmit();
        } else if (element.form) {
          const submitEvent = dispatchDomEvent(element.form, "submit");
          if (!submitEvent.defaultPrevented) {
            element.form.submit?.();
          }
        }
      }
    });

    refreshReferenceEntry(entry);
    return buildActionResult(entry, buildActionEffectResult(
      entry,
      beforeSnapshot,
      captureActionEffectSnapshot(element),
      observedMutations
    ));
  }

  async function typeAndSubmit(referenceId, value) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "type_submit"
    });

    if (entry.helperBacked) {
      const helper = requireDomHelper("type and submit reference");
      const submittedResult = await helper.typeSubmitNode(entry.frameChain, entry.nodeId, value);
      return buildHelperBackedActionResult(entry, submittedResult, {
        effect: submittedResult?.effect || {},
        status: submittedResult?.status || {},
        value: submittedResult?.value ?? String(value ?? "")
      });
    }

    const typed = await updateElementValue(referenceId, value);
    const submitted = await pressEnterElement(referenceId);
    const mergedOutcome = mergeActionOutcomeResults(typed, submitted);

    return {
      ...submitted,
      ...mergedOutcome,
      value: typed.value
    };
  }

  async function scrollToReference(referenceId) {
    const entry = requireReferenceEntry(referenceId, {
      actionLabel: "scroll"
    });

    if (entry.helperBacked) {
      const helper = requireDomHelper("scroll to reference");
      const scrollResult = await helper.scrollNode(entry.frameChain, entry.nodeId);
      return buildHelperBackedActionResult(entry, scrollResult, {
        effect: scrollResult?.effect || {},
        status: scrollResult?.status || {}
      });
    }

    const beforeSnapshot = captureActionEffectSnapshot(entry.element);
    scrollElementIntoView(entry.element);
    focusElement(entry.element);
    refreshReferenceEntry(entry);
    const afterSnapshot = captureActionEffectSnapshot(entry.element);
    const scrollEffect = buildActionEffectResult(entry, beforeSnapshot, afterSnapshot, {
      attributeNames: [],
      mutationCount: 0
    });
    return buildActionResult(entry, {
      ...scrollEffect,
      status: {
        ...scrollEffect.status,
        reacted: true,
        noObservedEffect: false
      }
    });
  }

  function cssEscape(value) {
    const rawValue = String(value || "");
    if (!rawValue) {
      return "";
    }

    if (typeof globalThis.CSS?.escape === "function") {
      return globalThis.CSS.escape(rawValue);
    }

    return rawValue.replace(/[^a-zA-Z0-9_-]/gu, (character) => `\\${character}`);
  }

  function getClassSummary(element) {
    try {
      return [...(element?.classList || [])]
        .map((className) => normalizeAttributeText(className))
        .filter(Boolean)
        .slice(0, 4)
        .join(" ");
    } catch {
      return "";
    }
  }

  function buildCssSelector(element) {
    if (!isElementNode(element)) {
      return "";
    }

    const id = normalizeAttributeText(element.getAttribute?.("id"));
    if (id) {
      return `#${cssEscape(id)}`;
    }

    const parts = [];
    let current = element;
    while (isElementNode(current) && current !== globalThis.document?.documentElement && parts.length < 6) {
      const tagName = getTagName(current).toLowerCase();
      if (!tagName) {
        break;
      }

      let part = tagName;
      const classes = getClassSummary(current)
        .split(/\s+/u)
        .filter(Boolean)
        .slice(0, 2);
      if (classes.length && !["body", "html"].includes(tagName)) {
        part += classes.map((className) => `.${cssEscape(className)}`).join("");
      }

      const parent = current.parentElement;
      if (parent) {
        const siblings = [...parent.children].filter((sibling) => getTagName(sibling) === getTagName(current));
        if (siblings.length > 1) {
          part += `:nth-of-type(${siblings.indexOf(current) + 1})`;
        }
      }

      parts.unshift(part);
      if (tagName === "body") {
        break;
      }
      current = parent;
    }

    return parts.join(" > ");
  }

  function sanitizeAnnotationDom(value) {
    return truncateText(
      String(value || "")
        .replace(/(<input\b(?=[^>]*\btype\s*=\s*(["'])?password\2?)[^>]*?)\s+value\s*=\s*(["'])[\s\S]*?\3/giu, "$1 value=\"[redacted]\"")
        .replace(/\svalue\s*=\s*(["'])[\s\S]{0,600}?\1/giu, " value=\"[redacted]\"")
        .replace(/\sdata-space-browser-live-value\s*=\s*(["'])[\s\S]{0,600}?\1/giu, "")
        .replace(/\sdata-space-browser-selected-text\s*=\s*(["'])[\s\S]{0,600}?\1/giu, ""),
      1200
    );
  }

  function summarizeAnnotationElement(element) {
    if (!isElementNode(element)) {
      return null;
    }

    const summaryData = collectReferenceSummaryData(element, {
      includeLabelQuotes: false,
      includeLinkUrls: true,
      includeSemanticTags: true,
      includeStateTags: true
    });
    const rawDom = serializeElementSnapshot(element);
    return {
      classes: getClassSummary(element),
      dom: sanitizeAnnotationDom(rawDom),
      id: normalizeAttributeText(element.getAttribute?.("id")),
      kind: summaryData.kind,
      name: normalizeAttributeText(element.getAttribute?.("name")),
      rect: getElementRectSafe(element),
      role: normalizeAttributeText(element.getAttribute?.("role")).toLowerCase(),
      selector: buildCssSelector(element),
      semanticTags: Array.isArray(summaryData.semanticTags) ? summaryData.semanticTags.slice(0, 4) : [],
      stateTags: Array.isArray(summaryData.state?.stateTags) ? summaryData.state.stateTags.slice(0, 8) : [],
      summary: truncateText(summaryData.summary || getLabelText(element, {
        includeAlt: true,
        includeDescendantImageAlt: true,
        includePlaceholder: true,
        includeText: true
      }), 240),
      tagName: getTagName(element)
    };
  }

  function annotationViewport() {
    return {
      height: Math.max(0, Number(globalThis.innerHeight || globalThis.document?.documentElement?.clientHeight || 0)),
      scrollX: Number(globalThis.scrollX || globalThis.pageXOffset || 0),
      scrollY: Number(globalThis.scrollY || globalThis.pageYOffset || 0),
      width: Math.max(0, Number(globalThis.innerWidth || globalThis.document?.documentElement?.clientWidth || 0))
    };
  }

  function normalizeAnnotationPoint(payload = {}, viewport = annotationViewport()) {
    const source = payload?.point && typeof payload.point === "object" ? payload.point : payload;
    const width = Math.max(1, Number(viewport.width || 1));
    const height = Math.max(1, Number(viewport.height || 1));
    return {
      x: Math.max(0, Math.min(width, Number(source?.x || 0))),
      y: Math.max(0, Math.min(height, Number(source?.y || 0)))
    };
  }

  function normalizeAnnotationRectPayload(payload = {}, viewport = annotationViewport()) {
    const source = payload?.rect && typeof payload.rect === "object" ? payload.rect : payload;
    const width = Math.max(1, Number(viewport.width || 1));
    const height = Math.max(1, Number(viewport.height || 1));
    const x = Math.max(0, Math.min(width, Number(source?.x || 0)));
    const y = Math.max(0, Math.min(height, Number(source?.y || 0)));
    return {
      height: Math.max(1, Math.min(height - y, Number(source?.height || source?.h || 1))),
      width: Math.max(1, Math.min(width - x, Number(source?.width || source?.w || 1))),
      x,
      y
    };
  }

  function intersectRects(leftRect, rightRect) {
    if (!leftRect || !rightRect) {
      return null;
    }

    const x = Math.max(Number(leftRect.x || 0), Number(rightRect.x || 0));
    const y = Math.max(Number(leftRect.y || 0), Number(rightRect.y || 0));
    const right = Math.min(
      Number(leftRect.x || 0) + Number(leftRect.width || 0),
      Number(rightRect.x || 0) + Number(rightRect.width || 0)
    );
    const bottom = Math.min(
      Number(leftRect.y || 0) + Number(leftRect.height || 0),
      Number(rightRect.y || 0) + Number(rightRect.height || 0)
    );
    const width = right - x;
    const height = bottom - y;
    if (width <= 0 || height <= 0) {
      return null;
    }
    return {
      area: width * height,
      height,
      width,
      x,
      y
    };
  }

  function deepElementFromPoint(x, y) {
    let element = null;
    try {
      element = globalThis.document?.elementFromPoint?.(x, y) || null;
    } catch {
      return null;
    }

    let guard = 0;
    while (isElementNode(element) && element.shadowRoot && guard < 8) {
      guard += 1;
      try {
        const nestedElement = element.shadowRoot.elementFromPoint?.(x, y);
        if (!nestedElement || nestedElement === element) {
          break;
        }
        element = nestedElement;
      } catch {
        break;
      }
    }

    return element;
  }

  function findAnnotationTarget(element) {
    if (!isElementNode(element)) {
      return null;
    }

    const selector = [
      "a[href]",
      "button",
      "input",
      "textarea",
      "select",
      "summary",
      "[role]",
      "img",
      "label",
      "form",
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "p",
      "li",
      "td",
      "th",
      "article",
      "section",
      "nav",
      "header",
      "main",
      "footer"
    ].join(",");
    const target = element.closest?.(selector) || element;
    return isElementNode(target) && !isHiddenElement(target) ? target : element;
  }

  function isMeaningfulAnnotationElement(element) {
    if (!isElementNode(element) || isHiddenElement(element)) {
      return false;
    }

    if (isInteractiveElement(element) || getTagName(element) === "IMG") {
      return true;
    }

    const tagName = getTagName(element);
    const role = normalizeAttributeText(element.getAttribute?.("role")).toLowerCase();
    return Boolean(
      role
      || /^H[1-6]$/u.test(tagName)
      || ["ARTICLE", "SECTION", "MAIN", "NAV", "HEADER", "FOOTER", "FORM", "LABEL", "P", "LI", "TD", "TH"].includes(tagName)
    );
  }

  function collectIntersectingAnnotationElements(rect) {
    const selector = [
      "a[href]",
      "button",
      "input",
      "textarea",
      "select",
      "summary",
      "[role]",
      "img",
      "label",
      "form",
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "p",
      "li",
      "td",
      "th",
      "article",
      "section",
      "main",
      "nav",
      "header",
      "footer"
    ].join(",");
    let candidates = [];
    try {
      candidates = [...(globalThis.document?.querySelectorAll?.(selector) || [])];
    } catch {
      candidates = [];
    }

    const seen = new Set();
    return candidates
      .map((element) => {
        if (!isMeaningfulAnnotationElement(element) || seen.has(element)) {
          return null;
        }
        seen.add(element);
        const elementRect = getElementRectSafe(element);
        const intersection = intersectRects(rect, elementRect);
        if (!intersection || intersection.area < 48) {
          return null;
        }
        return {
          element,
          elementArea: Math.max(1, Number(elementRect.width || 0) * Number(elementRect.height || 0)),
          intersection
        };
      })
      .filter(Boolean)
      .sort((left, right) => {
        if (right.intersection.area !== left.intersection.area) {
          return right.intersection.area - left.intersection.area;
        }
        return left.elementArea - right.elementArea;
      })
      .slice(0, 12)
      .map((entry) => summarizeAnnotationElement(entry.element))
      .filter(Boolean);
  }

  function annotate(payload = null) {
    const request = payload && typeof payload === "object" ? payload : {};
    const viewport = annotationViewport();
    const kind = request.kind === "area" || request.rect ? "area" : "element";

    if (kind === "area") {
      const rect = normalizeAnnotationRectPayload(request, viewport);
      const point = {
        x: rect.x + rect.width / 2,
        y: rect.y + rect.height / 2
      };
      const elements = collectIntersectingAnnotationElements(rect);
      const fallbackElement = findAnnotationTarget(deepElementFromPoint(point.x, point.y));
      const fallbackTarget = fallbackElement ? summarizeAnnotationElement(fallbackElement) : null;
      return {
        elements,
        kind,
        point,
        rect,
        status: elements.length || fallbackTarget ? "ok" : "empty",
        target: elements[0] || fallbackTarget,
        viewport
      };
    }

    const point = normalizeAnnotationPoint(request, viewport);
    const rawElement = deepElementFromPoint(point.x, point.y);
    const targetElement = findAnnotationTarget(rawElement);
    const target = targetElement ? summarizeAnnotationElement(targetElement) : null;
    return {
      kind,
      point,
      rect: target?.rect || {
        height: 1,
        width: 1,
        x: point.x,
        y: point.y
      },
      status: target ? "ok" : "empty",
      target,
      viewport
    };
  }

  globalThis[GLOBAL_KEY] = {
    click(referenceId) {
      return activateElement(referenceId);
    },
    annotate,
    capture,
    clear() {
      state.captureId = 0;
      state.capturedAt = 0;
      state.captureOptions = {
        includeLabelQuotes: false,
        includeLinkUrls: false,
        includeSemanticTags: true,
        includeStateTags: true,
        includeListIndentation: true,
        includeListMarkers: false
      };
      state.entries = new Map();
    },
    detail,
    getState() {
      return {
        captureId: state.captureId,
        capturedAt: state.capturedAt,
        includeLabelQuotes: state.captureOptions.includeLabelQuotes === true,
        includeLinkUrls: state.captureOptions.includeLinkUrls === true,
        includeSemanticTags: state.captureOptions.includeSemanticTags !== false,
        includeStateTags: state.captureOptions.includeStateTags !== false,
        includeListIndentation: state.captureOptions.includeListIndentation !== false,
        includeListMarkers: state.captureOptions.includeListMarkers === true,
        referenceCount: state.entries.size
      };
    },
    scroll(referenceId) {
      return scrollToReference(referenceId);
    },
    submit(referenceId) {
      return submitElement(referenceId);
    },
    type(referenceId, value) {
      return updateElementValue(referenceId, value);
    },
    typeSubmit(referenceId, value) {
      return typeAndSubmit(referenceId, value);
    },
    boundingBoxFor,
    fileInputElementFor,
    fileInputFor,
    pointFor,
    select(referenceId, valueOrValues) {
      return selectReference(referenceId, valueOrValues);
    },
    setChecked(referenceId, checked) {
      return setCheckedReference(referenceId, checked);
    },
    ready() {
      const api = globalThis[GLOBAL_KEY];
      return Boolean(api && REQUIRED_API_NAMES.every((name) => typeof api[name] === "function"));
    },
    requiredApis: REQUIRED_API_NAMES.slice(),
    version: VERSION
  };
})();
