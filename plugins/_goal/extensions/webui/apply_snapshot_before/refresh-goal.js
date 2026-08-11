import { store as goalStore } from "/plugins/_goal/webui/goal-store.js";

let lastContextId = "";
let lastRevision = null;

export default async function refreshGoalOnRevision(ctx) {
  const snapshot = ctx?.snapshot;
  const contextId = String(snapshot?.context || "");
  const activeContext = (snapshot?.contexts || []).find(item => item?.id === contextId);
  const revision = activeContext?._goal_revision ?? null;

  if (contextId === lastContextId && revision === lastRevision) return;
  lastContextId = contextId;
  lastRevision = revision;
  await goalStore.refresh(true);
}
