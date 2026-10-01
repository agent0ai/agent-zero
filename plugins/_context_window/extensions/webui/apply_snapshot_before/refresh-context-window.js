import { store as contextWindowStore } from "/plugins/_context_window/webui/context-window-store.js";

const OVERRIDE_REVISION_KEY = "_model_config_override_revision";
const TOOL_REFRESH_INTERVAL = 4;
const TOOL_LOG_TYPES = new Set([
  "tool", "mcp", "code_exe", "text_editor", "subagent",
]);
let lastContextId = "";
let lastRevision = null;
let lastLogGuid = "";
let lastGenerationKey = "";
let lastToolNo = -1;
let toolCallsSinceRefresh = 0;

function latestGenerationKey(logs) {
  if (!Array.isArray(logs)) return "";
  for (let index = logs.length - 1; index >= 0; index--) {
    const item = logs[index];
    if (item?.type !== "agent" || Number(item.agentno || 0) !== 0) continue;
    return `${item.no ?? ""}:${item.id ?? ""}`;
  }
  return "";
}

function rootToolNos(logs) {
  if (!Array.isArray(logs)) return [];
  return [...new Set(logs
    .filter(item => TOOL_LOG_TYPES.has(item?.type) && Number(item.agentno || 0) === 0)
    .map(item => Number(item.no))
    .filter(Number.isInteger))];
}

export default async function refreshContextWindow(ctx) {
  const snapshot = ctx?.snapshot;
  const contextId = String(snapshot?.context || "");
  if (!contextId) {
    lastContextId = "";
    lastRevision = null;
    lastLogGuid = "";
    lastGenerationKey = "";
    lastToolNo = -1;
    toolCallsSinceRefresh = 0;
    return;
  }

  const contexts = Array.isArray(snapshot?.contexts) ? snapshot.contexts : [];
  const active = contexts.find(item => item?.id === contextId) || null;
  const revision = active?.[OVERRIDE_REVISION_KEY] || null;
  const logGuid = String(snapshot?.log_guid || "");
  const generationKey = latestGenerationKey(snapshot?.logs);
  const activeLogChanged = contextId !== lastContextId || logGuid !== lastLogGuid;
  const toolNos = rootToolNos(snapshot?.logs);
  if (activeLogChanged) {
    lastToolNo = toolNos.length ? Math.max(...toolNos) : -1;
    toolCallsSinceRefresh = 0;
  } else {
    const newToolNos = toolNos.filter(no => no > lastToolNo);
    if (newToolNos.length) {
      lastToolNo = Math.max(lastToolNo, ...newToolNos);
      toolCallsSinceRefresh += newToolNos.length;
    }
  }
  if (
    !activeLogChanged
    && revision === lastRevision
    && (!generationKey || generationKey === lastGenerationKey)
    && toolCallsSinceRefresh < TOOL_REFRESH_INTERVAL
  ) return;

  lastContextId = contextId;
  lastRevision = revision;
  lastLogGuid = logGuid;
  if (generationKey) lastGenerationKey = generationKey;
  toolCallsSinceRefresh = 0;
  await contextWindowStore.refresh(contextId);
}
