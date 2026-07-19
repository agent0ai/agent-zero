import { store as editorStore } from "/plugins/_editor/webui/editor-store.js";
import { open as openSurface } from "/js/surfaces.js";

const SYNC_WINDOW_MS = 10 * 60 * 1000;
const syncedTextEditorResults = new Set();

export default async function syncTextEditorResultsIntoOpenEditor(context) {
  if (!context?.results?.length) return;

  for (const { args } of context.results) {
    const payload = getTextEditorPayload(args);
    if (toolName(payload) !== "text_editor") continue;
    if (!shouldSyncTextEditorResult(args, payload)) continue;

    const target = textEditorTarget(payload);
    if (!target.path || target.extension !== "md") continue;
    const explicitOpen = shouldOpenEditorUiFromResult(payload, target);
    if (context.historyEmpty && !explicitOpen) continue;

    const key = [
      args?.id || "",
      payload.action || "",
      target.path || "",
      payload.version || "",
      payload.last_modified || "",
    ].join(":");
    if (syncedTextEditorResults.has(key)) continue;
    syncedTextEditorResults.add(key);

    globalThis.setTimeout(() => {
      if (explicitOpen) {
        void openSurface("editor", {
          path: target.path || "",
          file_id: target.file_id || "",
          ctxid: target.ctxid || target.context_id || "",
          context_id: target.context_id || target.ctxid || "",
          refresh: true,
          source: "tool-result-open",
        });
        return;
      }
      void syncOpenEditorSurface(target);
    }, 0);
  }
}

function getTextEditorPayload(args = {}) {
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
    "extension",
    "format",
    "context_id",
    "ctxid",
    "last_modified",
    "open_canvas",
    "open_document",
    "open_in_canvas",
    "path",
    "version",
  ]) {
    if (args[key] != null && args[key] !== "") payload[key] = args[key];
  }
  return payload;
}

function toolName(payload = {}) {
  return String(payload._tool_name || payload.tool_name || "").trim();
}

function shouldSyncTextEditorResult(args = {}, payload = {}) {
  if (!isFresh(args.timestamp, payload.last_modified)) return false;
  const action = String(payload.action || "").trim().toLowerCase().replace("-", "_");
  return ["write", "patch"].includes(action);
}

function shouldOpenEditorUiFromResult(payload = {}, document = {}) {
  return isExplicitEditorUiRequest(payload) && documentExtension(payload, document) === "md";
}

function isExplicitEditorUiRequest(payload = {}) {
  const action = String(payload.action || "").trim().toLowerCase().replace("-", "_");
  return action === "open"
    || truthy(payload.open_in_canvas)
    || truthy(payload.open_canvas)
    || truthy(payload.open_document);
}

function textEditorTarget(payload = {}) {
  const path = String(payload.path || "").trim();
  const extension = documentExtension(payload, { path });
  const contextId = contextIdFromPayload(payload);
  return {
    path,
    file_id: "",
    context_id: contextId,
    ctxid: contextId,
    extension,
    format: extension,
    version: payload.version || "",
    last_modified: payload.last_modified || "",
  };
}

function documentExtension(payload = {}, document = {}) {
  return String(
    payload.format
      || payload.extension
      || extensionFromPath(document.path)
      || "",
  ).toLowerCase().replace(/^\./, "");
}

function extensionFromPath(path = "") {
  const clean = String(path || "").split("?")[0].split("#")[0];
  const name = clean.split("/").filter(Boolean).pop() || "";
  const index = name.lastIndexOf(".");
  return index > 0 ? name.slice(index + 1).toLowerCase() : "";
}

function isEditorSurfaceOpen() {
  return Boolean(
    globalThis.document?.querySelector?.(
      '[data-surface-id="editor"] .editor-panel, .modal-inner[data-surface-id="editor"] .editor-panel, .modal-inner[data-canvas-surface="editor"] .editor-panel',
    ),
  );
}

async function syncOpenEditorSurface(document = {}) {
  const editor = editorStore;
  if (!editor || !isEditorSurfaceOpen()) return false;
  if (!hasSameDocument(editor, document)) return false;
  if (isDirtySameDocument(editor, document)) return false;
  await editor.openSession?.({
    path: document.path || "",
    file_id: document.file_id || "",
    ctxid: document.ctxid || document.context_id || "",
    context_id: document.context_id || document.ctxid || "",
    refresh: true,
    source: "tool-result-sync",
  });
  return true;
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

function contextIdFromPayload(payload = {}) {
  return String(payload.context_id || payload.ctxid || "").trim();
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
