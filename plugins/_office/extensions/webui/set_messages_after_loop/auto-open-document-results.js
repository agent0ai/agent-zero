import { store as officeStore } from "/plugins/_office/webui/office-store.js";
import { store as desktopStore } from "/plugins/_desktop/webui/desktop-store.js";
import { open as openSurface } from "/js/surfaces.js";

const SYNC_WINDOW_MS = 10 * 60 * 1000;
const syncedDocumentResults = new Set();

export default async function syncDocumentResultsIntoOpenOfficeModal(context) {
  if (!context?.results?.length || context.historyEmpty) return;

  for (const { args } of context.results) {
    const payload = getDocumentPayload(args);
    if (getToolName(payload) !== "document_artifact") continue;
    if (!shouldSyncOpenOfficeModal(args, payload)) continue;

    const document = payload.document && typeof payload.document === "object" ? payload.document : {};
    const path = payload.path || document.path || "";
    const fileId = payload.file_id || document.file_id || "";
    if (!path && !fileId) continue;

    const key = [
      args?.id || "",
      payload.action || "",
      fileId || "",
      path || "",
      payload.version || document.version || "",
    ].join(":");
    if (syncedDocumentResults.has(key)) continue;
    syncedDocumentResults.add(key);

    if (shouldOpenDocumentUiFromResult(payload, document)) {
      globalThis.setTimeout(() => {
        void openDocumentUiFromResult({ path, file_id: fileId }, payload, document);
      }, 0);
      continue;
    }

    globalThis.setTimeout(() => {
      void syncOpenDocumentSurfaces({ path, file_id: fileId });
    }, 0);
  }
}

function getDocumentPayload(args = {}) {
  const contentPayload = parseMaybeJson(args.content);
  const kvpsPayload = args.kvps && typeof args.kvps === "object"
    ? args.kvps
    : parseMaybeJson(args.kvps);
  return {
    ...pickPayloadFields(args),
    ...(contentPayload || {}),
    ...(kvpsPayload || {}),
  };
}

function pickPayloadFields(args = {}) {
  const payload = {};
  for (const key of [
    "_tool_name",
    "tool_name",
    "action",
    "canvas_surface",
    "extension",
    "file_id",
    "format",
    "open_canvas",
    "open_document",
    "open_desktop",
    "open_in_canvas",
    "open_in_desktop",
    "path",
    "version",
    "last_modified",
  ]) {
    if (args[key] != null && args[key] !== "") payload[key] = args[key];
  }
  return payload;
}

function getToolName(payload = {}) {
  return String(payload._tool_name || payload.tool_name || "").trim();
}

function shouldSyncOpenOfficeModal(args = {}, payload = {}) {
  if (!isFresh(args.timestamp, payload.last_modified || payload.document?.last_modified)) return false;
  const action = String(payload.action || "").trim().toLowerCase().replace("-", "_");
  return ["create", "open", "edit", "restore_version"].includes(action);
}

function shouldOpenDocumentUiFromResult(payload = {}, document = {}) {
  if (!isExplicitDocumentUiRequest(payload)) return false;
  return Boolean(documentExtension(payload, document));
}

function isExplicitDocumentUiRequest(payload = {}) {
  const action = String(payload.action || "").trim().toLowerCase().replace("-", "_");
  return action === "open"
    || truthy(payload.open_in_canvas)
    || truthy(payload.open_canvas)
    || truthy(payload.open_document)
    || truthy(payload.open_in_desktop)
    || truthy(payload.open_desktop);
}

async function openDocumentUiFromResult(target = {}, payload = {}, document = {}) {
  await openSurface("desktop", {
    path: target.path || "",
    file_id: target.file_id || "",
    refresh: true,
    source: "tool-result-open",
  });
}

function documentExtension(payload = {}, document = {}) {
  return String(
    payload.format
      || payload.extension
      || document.extension
      || document.format
      || "",
  ).toLowerCase();
}

function isOfficeModalOpen() {
  if (
    globalThis.isModalOpen?.("/plugins/_office/webui/main.html")
      || globalThis.isModalOpen?.("plugins/_office/webui/main.html")
  ) {
    return true;
  }

  const panels = Array.from(globalThis.document?.querySelectorAll?.(".modal-inner.office-modal .office-panel") || []);
  return panels.some((panel) => !isDesktopPanel(panel));
}

function isDesktopSurfaceOpen() {
  return Boolean(
    globalThis.document?.querySelector?.(
      '[data-surface-id="desktop"] .office-panel, .modal-inner[data-surface-id="desktop"] .office-panel, .modal-inner[data-canvas-surface="desktop"] .office-panel',
    ),
  );
}

async function syncOpenDocumentSurfaces(document = {}) {
  await syncOpenDesktopCanvas(document);
  await syncOpenOfficeModal(document);
}

async function syncOpenDesktopCanvas(document = {}) {
  const desktop = desktopStore;
  if (!desktop || !isDesktopSurfaceOpen()) return false;
  if (!hasSameDocument(desktop, document)) return false;
  if (isDirtySameDocument(desktop, document)) return false;
  await desktop.openSession?.({
    path: document.path || "",
    file_id: document.file_id || "",
    refresh: true,
    source: "tool-result-sync",
  });
  return true;
}

async function syncOpenOfficeModal(document = {}) {
  const office = officeStore;
  if (!office || !isOfficeModalOpen()) return false;
  if (!hasSameDocument(office, document)) return false;
  if (isDirtySameDocument(office, document)) return false;
  await office.openSession?.({
    path: document.path || "",
    file_id: document.file_id || "",
    refresh: true,
    source: "tool-result-sync",
  });
  return true;
}

function isDesktopPanel(panel = null) {
  return Boolean(
    panel?.closest?.('[data-surface-id="desktop"], [data-canvas-surface="desktop"]'),
  );
}

function hasSameDocument(store, document = {}) {
  return documentEntries(store).some((entry) => documentsMatch(entry, document));
}

function isDirtySameDocument(store, document = {}) {
  return documentEntries(store).some((entry) => {
    if (!documentsMatch(entry, document)) return false;
    const isActive = entry === store?.session || (entry.tab_id && entry.tab_id === store?.activeTabId);
    return Boolean(entry.dirty || (isActive && store?.dirty));
  });
}

function documentEntries(store) {
  const entries = [];
  if (store?.session) entries.push(store.session);
  if (Array.isArray(store?.tabs)) entries.push(...store.tabs);
  return entries;
}

function documentsMatch(entry = {}, document = {}) {
  const path = String(document.path || "").trim();
  const fileId = String(document.file_id || "").trim();
  const entryPath = String(entry.path || entry.document?.path || "").trim();
  const entryFileId = String(entry.file_id || entry.document?.file_id || "").trim();
  return Boolean(
    (fileId && entryFileId === fileId)
      || (path && entryPath === path),
  );
}

function truthy(value) {
  if (value === true) return true;
  if (value === false || value == null) return false;
  if (typeof value === "number") return value !== 0;
  return ["1", "true", "yes", "y", "on"].includes(String(value).trim().toLowerCase());
}

function isFresh(...timestamps) {
  const now = Date.now();
  for (const value of timestamps) {
    const time = parseTimestamp(value);
    if (time && now - time < SYNC_WINDOW_MS) return true;
  }
  return false;
}

function parseTimestamp(value) {
  if (!value) return 0;
  if (typeof value === "number") return value > 1e12 ? value : value * 1000;
  const parsed = Date.parse(String(value));
  return Number.isFinite(parsed) ? parsed : 0;
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
