import { store as contextWindowStore } from "/plugins/_context_window/webui/context-window-store.js";

const OVERRIDE_REVISION_KEY = "_model_config_override_revision";
let lastContextId = "";
let lastRevision = null;
let lastLogGuid = "";
let lastGenerationKey = "";

function latestGenerationKey(logs) {
  if (!Array.isArray(logs)) return "";
  for (let index = logs.length - 1; index >= 0; index--) {
    const item = logs[index];
    if (item?.type !== "agent" || Number(item.agentno || 0) !== 0) continue;
    return `${item.no ?? ""}:${item.id ?? ""}`;
  }
  return "";
}

export default async function refreshContextWindow(ctx) {
  const snapshot = ctx?.snapshot;
  const contextId = String(snapshot?.context || "");
  if (!contextId) {
    lastContextId = "";
    lastRevision = null;
    lastLogGuid = "";
    lastGenerationKey = "";
    return;
  }

  const contexts = Array.isArray(snapshot?.contexts) ? snapshot.contexts : [];
  const active = contexts.find(item => item?.id === contextId) || null;
  const revision = active?.[OVERRIDE_REVISION_KEY] || null;
  const logGuid = String(snapshot?.log_guid || "");
  const generationKey = latestGenerationKey(snapshot?.logs);
  if (
    contextId === lastContextId
    && revision === lastRevision
    && logGuid === lastLogGuid
    && (!generationKey || generationKey === lastGenerationKey)
  ) return;

  lastContextId = contextId;
  lastRevision = revision;
  lastLogGuid = logGuid;
  if (generationKey) lastGenerationKey = generationKey;
  await contextWindowStore.refresh(contextId);
}
