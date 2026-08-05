import { store } from "/plugins/_agent_editor/webui/agent-editor-store.js";

let initialized = false;

export default async function initAgentEditor() {
  if (initialized) return;
  initialized = true;
  globalThis.openAgentEditor = (options = {}) => store.open(options);
  globalThis.testAgentProfile = (profileId) => store.openFreshChat(String(profileId || ""), false);
}
