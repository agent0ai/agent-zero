import { store as modelConfigStore } from "/plugins/_model_config/webui/model-config-store.js";

const OVERRIDE_REVISION_KEY = "_model_config_override_revision";

let lastContextId = "";
let lastRevision = null;
let lastScopeKey = "";

export default async function refreshSwitcherOnOverrideRevision(ctx) {
  const snapshot = ctx?.snapshot;
  const contextId = String(snapshot?.context || "");

  if (!contextId) {
    lastContextId = "";
    lastRevision = null;
    lastScopeKey = "";
    return;
  }

  const contexts = Array.isArray(snapshot?.contexts) ? snapshot.contexts : [];
  const activeContext = contexts.find(item => item?.id === contextId) || null;
  const revision = activeContext?.[OVERRIDE_REVISION_KEY] || null;
  const project = activeContext?.project;
  const projectName = typeof project === "object" ? project?.name || "" : project || "";
  const scopeKey = JSON.stringify([
    String(projectName),
    String(activeContext?.agent_profile || ""),
  ]);

  if (
    contextId === lastContextId
    && revision === lastRevision
    && scopeKey === lastScopeKey
  ) return;

  lastContextId = contextId;
  lastRevision = revision;
  lastScopeKey = scopeKey;
  await modelConfigStore.refreshSwitcher(contextId);
}
