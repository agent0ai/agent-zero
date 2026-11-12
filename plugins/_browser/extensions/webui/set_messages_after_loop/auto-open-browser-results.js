import { store as browserStore } from "/plugins/_browser/webui/browser-store.js";
import { open as openSurface } from "/js/surfaces.js";

const AUTO_OPEN_WINDOW_MS = 10 * 60 * 1000;
const syncedBrowserCanvases = new Set();

export default async function syncBrowserResultsIntoOpenCanvas(context) {
  if (!context?.results?.length || context.historyEmpty) return;
  if (!isBrowserCanvasAlreadyOpen()) return;

  for (const { args } of context.results) {
    const payload = getToolResultPayload(args);
    if (getToolName(payload) !== "browser") continue;

    const result = parseMaybeJson(payload.tool_result) || {};
    if (!shouldSyncOpenBrowserCanvas(args, payload, result)) continue;

    const browserId = getBrowserId(payload, result);
    const contextId = getBrowserContextId(payload, result);
    const key = [
      args?.id || "",
      contextId || "",
      browserId || "",
      result.currentUrl || result.state?.currentUrl || payload.url || "",
    ].join(":");
    const persistedKey = `a0.browser.synced.${key}`;
    if (hasOpened(key, persistedKey)) continue;

    requestAnimationFrame(async () => {
      if (!isBrowserCanvasAlreadyOpen()) return;
      if (!(await browserAllowsToolAutofocus())) return;
      void syncOpenBrowserCanvas({ browserId, contextId, source: "tool-result-sync" });
    });
  }
}

function getToolResultPayload(args = {}) {
  const topLevelPayload = pickPayloadFields(args);
  const contentPayload = parseMaybeJson(args.content);
  const kvpsPayload = parseMaybeJson(args.kvps);
  return {
    ...topLevelPayload,
    ...(contentPayload || {}),
    ...(kvpsPayload || {}),
  };
}

function pickPayloadFields(args = {}) {
  const payload = {};
  for (const key of [
    "_tool_name",
    "tool_name",
    "tool_result",
    "action",
    "browser_id",
    "browserId",
    "context_id",
    "contextId",
    "url",
    "last_modified",
  ]) {
    if (args[key] != null && args[key] !== "") payload[key] = args[key];
  }
  return payload;
}

function getToolName(payload = {}) {
  return String(payload._tool_name || payload.tool_name || "").trim();
}

function parseMaybeJson(value) {
  if (!value) return null;
  if (typeof value === "object") return value;
  if (typeof value !== "string") return null;

  const trimmed = value.trim();
  if (!trimmed.startsWith("{")) return null;
  try {
    const parsed = JSON.parse(trimmed);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

// Actions that should sync an already-open viewer to the targeted tab.
// Everything else (read, click, type, evaluate, key_chord, mouse, multi, ...)
// leaves the viewer where it is so cross-tab work doesn't steal user focus.
const FOCUS_ACTIONS = new Set([
  "open",
  "navigate",
  "set_active",
  "setactive",
  "activate",
  "focus",
]);

function shouldSyncOpenBrowserCanvas(args = {}, payload = {}, result = {}) {
  if (payload._browser_backend === "chrome_extension") return false;
  const browserId = getBrowserId(payload, result);
  if (typeof browserId === "string" && (browserId.startsWith("a0t1.") || browserId.startsWith("extension:"))) return false;
  if (!isBrowserCanvasAlreadyOpen()) return false;
  if (!isFresh(args.timestamp, payload.last_modified || result.last_modified)) return false;
  const action = String(payload.action || "").trim().toLowerCase().replace("-", "_");
  if (!FOCUS_ACTIONS.has(action)) return false;
  return Boolean(getBrowserId(payload, result) || result.currentUrl || result.state?.currentUrl);
}

function getBrowserId(payload = {}, result = {}) {
  return (
    result.id
    || result.browser_id
    || result.state?.id
    || result.last_interacted_browser_id
    || payload.browser_id
    || payload.browserId
    || null
  );
}

function getBrowserContextId(payload = {}, result = {}) {
  return (
    result.context_id
    || result.state?.context_id
    || payload.context_id
    || payload.contextId
    || null
  );
}

function isFresh(timestamp, fallbackTimestamp) {
  const messageMs = toMs(timestamp) || toMs(fallbackTimestamp);
  if (!messageMs) return true;
  return Math.abs(Date.now() - messageMs) <= AUTO_OPEN_WINDOW_MS;
}

function toMs(value) {
  if (value == null || value === "") return 0;

  const numeric = Number(value);
  if (Number.isFinite(numeric) && numeric > 0) {
    return numeric > 10_000_000_000 ? numeric : numeric * 1000;
  }

  const parsed = Date.parse(String(value));
  return Number.isFinite(parsed) ? parsed : 0;
}

function hasOpened(key, persistedKey) {
  if (syncedBrowserCanvases.has(key)) return true;
  syncedBrowserCanvases.add(key);

  try {
    if (sessionStorage.getItem(persistedKey)) return true;
    sessionStorage.setItem(persistedKey, "1");
  } catch {
    // Best-effort persistence; the in-memory guard still prevents repeat syncs.
  }

  return false;
}

async function syncOpenBrowserCanvas(payload = {}) {
  if (!isBrowserCanvasAlreadyOpen()) return;
  await openSurface("browser", payload);
}

function isBrowserCanvasAlreadyOpen() {
  return Boolean(document.querySelector('[data-surface-id="browser"].is-active .browser-panel'));
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
