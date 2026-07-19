import {
  createActionButton,
  copyToClipboard,
} from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as stepDetailStore } from "/components/modals/process-step-detail/step-detail-store.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";
import { store as browserStore } from "/plugins/_browser/webui/browser-store.js";
import { getNamespacedClient } from "/js/websocket.js";
import { open as openSurface } from "/js/surfaces.js";
import {
  buildDetailPayload,
  cleanStepTitle,
  drawProcessStep,
} from "/js/messages.js";

const BROWSER_SCREENSHOT_KVP_KEY = "Screenshot";
const BROWSER_SNAPSHOT_META_KEY = "browser_snapshot";
const BROWSER_SCREENSHOT_STYLE_ID = "a0-browser-screenshot-kvp-style";
const AUTO_OPEN_WINDOW_MS = 10 * 60 * 1000;
const PREVIEW_REFRESH_MS = 2500;
const PREVIEW_RETRY_MS = 5000;
const PREVIEW_SNAPSHOT_TIMEOUT_MS = 10000;
const PREVIEW_QUALITY = 62;
const PREVIEW_FRAME_LIMIT = 16;
const NO_SCREENSHOT_ACTIONS = new Set(["close", "close_all"]);
const syncedBrowserCanvases = new Set();
const liveScreenshotFrames = new Map();
const websocket = getNamespacedClient("/ws");
websocket.addHandlers(["ws_webui"]);

export default async function registerBrowserToolHandler(extData) {
  if (extData?.tool_name === "browser") {
    extData.handler = drawBrowserTool;
  }
}

async function openBrowserSurface(payload = {}) {
  await openSurface("browser", payload);
}

async function browserAllowsToolAutofocus() {
  try {
    if (browserStore.allowsToolAutofocus) {
      return await browserStore.allowsToolAutofocus();
    }
  } catch (error) {
    console.warn("Browser autofocus setting could not be checked", error);
  }
  return true;
}

function parseBrowserResult(content) {
  if (!content || typeof content !== "string") return {};
  try {
    const parsed = JSON.parse(content);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function normalizeBrowserAction(kvps = {}) {
  return String(kvps.action || "").trim().toLowerCase().replace("-", "_");
}

function browserSnapshotMeta(kvps = {}) {
  return kvps?.[BROWSER_SNAPSHOT_META_KEY] && typeof kvps[BROWSER_SNAPSHOT_META_KEY] === "object"
    ? kvps[BROWSER_SNAPSHOT_META_KEY]
    : {};
}

function browserIdFromResult(result = {}, kvps = {}) {
  const snapshotMeta = browserSnapshotMeta(kvps);
  const browsers = Array.isArray(result.browsers) ? result.browsers : [];
  const lastInteractedId = result.last_interacted_browser_id;
  const listedBrowser = lastInteractedId
    ? browsers.find((browser) => String(browser?.id) === String(lastInteractedId))
    : browsers[0];
  return (
    result.id
    || result.browser_id
    || result.state?.id
    || result.last_interacted_browser_id
    || listedBrowser?.id
    || snapshotMeta.browser_id
    || kvps.browser_id
    || null
  );
}

function browserContextIdFromResult(result = {}, kvps = {}) {
  const snapshotMeta = browserSnapshotMeta(kvps);
  const browserId = browserIdFromResult(result, kvps);
  const browsers = Array.isArray(result.browsers) ? result.browsers : [];
  const listedBrowser = browserId
    ? browsers.find((browser) => String(browser?.id) === String(browserId))
    : browsers[0];
  return (
    result.context_id
    || result.state?.context_id
    || listedBrowser?.context_id
    || snapshotMeta.context_id
    || kvps.context_id
    || kvps.contextId
    || null
  );
}

function isFreshToolMessage(timestamp) {
  const value = Number(timestamp);
  if (!Number.isFinite(value) || value <= 0) return true;
  const messageMs = value > 10_000_000_000 ? value : value * 1000;
  return Math.abs(Date.now() - messageMs) <= AUTO_OPEN_WINDOW_MS;
}

function isBrowserCanvasAlreadyOpen() {
  return Boolean(document.querySelector('[data-surface-id="browser"].is-active .browser-panel'));
}

// Allowlist: only these actions sync an already-open viewer to the target tab.
// Background work (evaluate, click, type, key_chord, mouse, multi, ...) does
// not steal focus.
const FOCUS_ACTIONS = new Set([
  "open",
  "navigate",
  "set_active",
  "setactive",
  "activate",
  "focus",
]);

function shouldSyncOpenBrowserCanvas(args, result) {
  if (!isBrowserCanvasAlreadyOpen()) return false;
  if (!isFreshToolMessage(args?.timestamp)) return false;
  const action = String(args?.kvps?.action || "").trim().toLowerCase().replace("-", "_");
  if (!FOCUS_ACTIONS.has(action)) return false;
  return Boolean(browserIdFromResult(result, args?.kvps || {}));
}

function syncOpenBrowserCanvas(args, result) {
  if (!shouldSyncOpenBrowserCanvas(args, result)) return;
  const kvps = args?.kvps || {};
  const browserId = browserIdFromResult(result, kvps);
  const contextId = browserContextIdFromResult(result, kvps);
  const key = `${args.id || ""}:${contextId || ""}:${kvps.action || ""}:${browserId || ""}:${result.currentUrl || result.state?.currentUrl || kvps.url || ""}`;
  if (syncedBrowserCanvases.has(key)) return;
  syncedBrowserCanvases.add(key);
  requestAnimationFrame(async () => {
    if (!isBrowserCanvasAlreadyOpen()) return;
    if (!(await browserAllowsToolAutofocus())) return;
    void openSurface("browser", {
      browserId,
      contextId,
      source: "tool-sync",
    });
  });
}

function currentBrowserContextId(result = {}, kvps = {}) {
  return (
    browserContextIdFromResult(result, kvps)
    || browserStore?.resolveContextId?.()
    || ""
  );
}

function buildBrowserCanvasPayload(result = {}, kvps = {}, source = "tool-kvp") {
  const browserId = browserIdFromResult(result, kvps);
  const contextId = currentBrowserContextId(result, kvps);
  if (!browserId && !contextId) return null;
  return {
    browserId: browserId || null,
    contextId,
    source,
  };
}

function makeViewerToken() {
  return globalThis.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

function snapshotToObjectUrl(snapshot) {
  if (!snapshot?.image) return null;
  const binary = globalThis.atob(snapshot.image);
  const chunks = [];
  const chunkSize = 8192;
  for (let offset = 0; offset < binary.length; offset += chunkSize) {
    const slice = binary.slice(offset, offset + chunkSize);
    const bytes = new Uint8Array(slice.length);
    for (let index = 0; index < slice.length; index += 1) {
      bytes[index] = slice.charCodeAt(index);
    }
    chunks.push(bytes);
  }
  return URL.createObjectURL(new Blob(chunks, { type: snapshot.mime || "image/jpeg" }));
}

function staticScreenshotUri(kvps = {}) {
  const metaUri = browserSnapshotMeta(kvps).uri;
  const value = kvps?.[BROWSER_SCREENSHOT_KVP_KEY] || metaUri || "";
  return typeof value === "string" && value.startsWith("img://") ? value : "";
}

function staticScreenshotSrc(uri = "") {
  return uri ? uri.replace("img://", "/api/image_get?path=") : "";
}

function releaseLiveScreenshotFrame(viewerId) {
  const release = liveScreenshotFrames.get(viewerId);
  if (!release) return;
  liveScreenshotFrames.delete(viewerId);
  release();
}

function rememberLiveScreenshotFrame(viewerId, release) {
  liveScreenshotFrames.delete(viewerId);
  liveScreenshotFrames.set(viewerId, release);

  while (liveScreenshotFrames.size > PREVIEW_FRAME_LIMIT) {
    releaseLiveScreenshotFrame(liveScreenshotFrames.keys().next().value);
  }
}

function firstOk(response) {
  const result = response?.results?.find((item) => item?.ok);
  if (result) return result.data || {};
  const error = response?.results?.find((item) => !item?.ok)?.error;
  if (error) throw new Error(error.error || error.code || "Browser request failed");
  return {};
}

function browserResultFromRenderedStep(step) {
  if (!step) return {};
  const contentText = step.querySelector(".process-step-detail-content")?.textContent || "";
  return parseBrowserResult(contentText);
}

function shouldRenderBrowserScreenshotKvp(result = {}, kvps = {}) {
  if (buildBrowserCanvasPayload(result, kvps)) return true;
  const action = normalizeBrowserAction(kvps);
  return Boolean(action && !NO_SCREENSHOT_ACTIONS.has(action));
}

function ensureBrowserScreenshotStyles() {
  if (document.getElementById(BROWSER_SCREENSHOT_STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = BROWSER_SCREENSHOT_STYLE_ID;
  style.textContent = `
    .browser-screenshot-kvp-button {
      padding: 0;
      width: min(12rem, 100%);
      aspect-ratio: 16 / 10;
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid color-mix(in srgb, var(--color-border) 74%, transparent);
      border-radius: 7px;
      background: color-mix(in srgb, var(--color-panel) 88%, var(--color-chat-background));
      color: var(--color-message-text);
      cursor: pointer;
      overflow: hidden;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
      transition: border-color 0.16s ease, color 0.16s ease, transform 0.16s ease, background 0.16s ease;
    }

    .browser-screenshot-kvp-button:hover {
      border-color: color-mix(in srgb, var(--color-primary) 68%, var(--color-border));
      color: var(--color-text);
      transform: translateY(-1px);
    }

    .browser-screenshot-kvp-button:focus-visible {
      outline: 2px solid color-mix(in srgb, var(--color-primary) 72%, white);
      outline-offset: 2px;
    }

    .browser-screenshot-kvp-image {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: cover;
      object-position: top left;
      background: var(--color-chat-background);
    }

    .browser-screenshot-kvp-button:not(.has-frame) .browser-screenshot-kvp-image {
      display: none;
    }

    .browser-screenshot-kvp-placeholder {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background:
        linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.06), transparent),
        color-mix(in srgb, var(--color-panel) 84%, black 16%);
      background-size: 200% 100%, auto;
      animation: browser-screenshot-kvp-pulse 1.6s ease-in-out infinite;
    }

    .browser-screenshot-kvp-button.has-frame .browser-screenshot-kvp-placeholder {
      display: none;
    }

    .browser-screenshot-kvp-button .material-symbols-outlined {
      font-size: 1.15rem;
      line-height: 1;
      font-variation-settings: 'FILL' 0, 'wght' 420, 'GRAD' 0, 'opsz' 20;
    }

    @keyframes browser-screenshot-kvp-pulse {
      0% { background-position: 160% 0, 0 0; }
      100% { background-position: -160% 0, 0 0; }
    }
  `;
  document.head.appendChild(style);
}

function renderBrowserScreenshotKvp(kvpsTable, resolveBrowserPayload, label, staticUri = "") {
  if (!kvpsTable || typeof resolveBrowserPayload !== "function") return;
  ensureBrowserScreenshotStyles();

  const rows = Array.from(kvpsTable.querySelectorAll(".kvps-row"));
  const row = rows.find((candidate) => {
    const keyText = candidate.querySelector(".kvps-key")?.textContent || "";
    return keyText.trim().toLowerCase() === BROWSER_SCREENSHOT_KVP_KEY.toLowerCase();
  });
  const cell = row?.querySelector(".kvps-val") || row?.cells?.[1];
  if (!cell) return;

  cell.__browserScreenshotCleanup?.();

  const button = document.createElement("button");
  button.type = "button";
  button.className = "browser-screenshot-kvp-button";
  button.title = label;
  button.setAttribute("aria-label", label);
  button.innerHTML = `
    <img class="browser-screenshot-kvp-image" alt="" draggable="false">
    <span class="browser-screenshot-kvp-placeholder" aria-hidden="true">
      <span class="material-symbols-outlined">image_search</span>
    </span>
  `;
  button.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();
    const canvasPayload = resolveBrowserPayload();
    if (!canvasPayload) return;
    await openBrowserSurface(canvasPayload);
  });

  cell.textContent = "";
  cell.appendChild(button);
  const image = button.querySelector(".browser-screenshot-kvp-image");
  if (staticUri) {
    image.src = staticScreenshotSrc(staticUri);
    button.classList.add("has-frame");
    cell.__browserScreenshotCleanup = () => {
      image.removeAttribute("src");
      button.classList.remove("has-frame");
    };
    return;
  }
  cell.__browserScreenshotCleanup = startBrowserScreenshotPreview(button, image, resolveBrowserPayload);
}

function startBrowserScreenshotPreview(button, image, resolveBrowserPayload) {
  const viewerId = makeViewerToken();
  let stopped = false;
  let timerId = null;
  let refreshInFlight = false;
  let frameUrl = null;

  const releaseFrame = () => {
    liveScreenshotFrames.delete(viewerId);
    if (frameUrl) {
      URL.revokeObjectURL(frameUrl);
      frameUrl = null;
    }
    image.removeAttribute("src");
    button.classList.remove("has-frame");
  };

  const setFrame = (snapshot) => {
    const nextUrl = snapshotToObjectUrl(snapshot);
    if (!nextUrl) {
      releaseFrame();
      return false;
    }
    if (frameUrl) {
      URL.revokeObjectURL(frameUrl);
    }
    frameUrl = nextUrl;
    image.src = frameUrl;
    button.classList.add("has-frame");
    rememberLiveScreenshotFrame(viewerId, releaseFrame);
    return true;
  };

  const cleanup = () => {
    stopped = true;
    if (timerId) {
      globalThis.clearTimeout(timerId);
      timerId = null;
    }
    releaseFrame();
  };

  const schedule = (delay = PREVIEW_REFRESH_MS) => {
    if (stopped || timerId) return;
    timerId = globalThis.setTimeout(refresh, delay);
  };

  const refresh = async () => {
    timerId = null;
    if (stopped || refreshInFlight) return;
    if (!button.isConnected) {
      cleanup();
      return;
    }

    const payload = resolveBrowserPayload();
    if (!payload?.contextId) {
      schedule(PREVIEW_RETRY_MS);
      return;
    }

    refreshInFlight = true;
    try {
      const response = await websocket.request(
        "browser_viewer_snapshot",
        {
          context_id: payload.contextId,
          browser_id: payload.browserId,
          viewer_id: viewerId,
          quality: PREVIEW_QUALITY,
        },
        { timeoutMs: PREVIEW_SNAPSHOT_TIMEOUT_MS },
      );
      const data = firstOk(response);
      const hasFrame = setFrame(data.snapshot);
      schedule(hasFrame ? PREVIEW_REFRESH_MS : PREVIEW_RETRY_MS);
    } catch (_error) {
      schedule(PREVIEW_RETRY_MS);
    } finally {
      refreshInFlight = false;
    }
  };

  schedule(0);

  return cleanup;
}

function drawBrowserTool({
  id,
  type,
  heading,
  content,
  kvps,
  timestamp,
  agentno = 0,
  ...additional
}) {
  const args = arguments[0];
  const title = cleanStepTitle(heading);
  const displayKvps = { ...kvps };
  const headerLabels = [
    kvps?._tool_name && { label: kvps._tool_name, class: "tool-name-badge" },
  ].filter(Boolean);
  const contentText = String(content ?? "");
  const browserResult = parseBrowserResult(contentText);
  const screenshotUri = staticScreenshotUri(kvps);
  const browserId = browserIdFromResult(browserResult, kvps);
  const browserCanvasPayload = buildBrowserCanvasPayload(browserResult, kvps);
  const browserPreviewLabel = browserId
    ? `Open Browser surface for Browser ${browserId}`
    : "Open Browser surface from screenshot";
  if (shouldRenderBrowserScreenshotKvp(browserResult, kvps)) {
    displayKvps[BROWSER_SCREENSHOT_KVP_KEY] = "";
  }
  if (screenshotUri) {
    displayKvps[BROWSER_SCREENSHOT_KVP_KEY] = screenshotUri;
  }
  delete displayKvps[BROWSER_SNAPSHOT_META_KEY];
  const browserButton = createActionButton(
    "visibility",
    "Browser",
    () => openBrowserSurface(
      buildBrowserCanvasPayload(browserResult, kvps, "tool")
      || {
        browserId,
        contextId: browserContextIdFromResult(browserResult, kvps),
        source: "tool",
      },
    ),
  );
  browserButton.setAttribute("title", "Open Browser");
  browserButton.setAttribute("aria-label", "Open Browser");
  browserButton.setAttribute("data-bs-placement", "top");
  browserButton.setAttribute("data-bs-trigger", "hover");
  const actionButtons = [browserButton];

  if (contentText.trim()) {
    actionButtons.push(
      createActionButton("detail", "", () =>
        stepDetailStore.showStepDetail(
          buildDetailPayload(args, { headerLabels }),
        ),
      ),
      createActionButton("speak", "", () => speechStore.speak(contentText)),
      createActionButton("copy", "", () => copyToClipboard(contentText)),
    );
  }

  const result = drawProcessStep({
    id,
    title,
    code: "WWW",
    classes: undefined,
    kvps: displayKvps,
    content,
    actionButtons: actionButtons.filter(Boolean),
    log: args,
  });
  renderBrowserScreenshotKvp(
    result.kvpsTable,
    () => (
      buildBrowserCanvasPayload(browserResultFromRenderedStep(result.step), kvps)
      || browserCanvasPayload
      || buildBrowserCanvasPayload({}, kvps)
    ),
    browserPreviewLabel,
    screenshotUri,
  );
  syncOpenBrowserCanvas(args, browserResult);
  return result;
}
