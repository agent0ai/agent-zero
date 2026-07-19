import { store as modelConfigStore } from "/plugins/_model_config/webui/model-config-store.js";

const OVERRIDE_REVISION_KEY = "_model_config_override_revision";

let lastContextId = "";
let lastRevision = null;

export default async function refreshSwitcherOnOverrideRevision(ctx) {
  const snapshot = ctx?.snapshot;
  const contextId = String(snapshot?.context || "");

  if (!contextId) {
    lastContextId = "";
    lastRevision = null;
    return;
  }

  const contexts = Array.isArray(snapshot?.contexts) ? snapshot.contexts : [];
  const activeContext = contexts.find(item => item?.id === contextId) || null;
  const revision = activeContext?.[OVERRIDE_REVISION_KEY] || null;

  if (contextId === lastContextId && revision === lastRevision) return;

  lastContextId = contextId;
  lastRevision = revision;
  await modelConfigStore.refreshSwitcher(contextId);
}
