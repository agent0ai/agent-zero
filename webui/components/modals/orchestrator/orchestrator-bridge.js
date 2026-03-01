/**
 * Orchestrator Bridge
 *
 * Handles bidirectional communication between the Alpine store and the React
 * Flow canvas using custom DOM events on #react-flow-root.
 *
 * Alpine → React events:
 *   flow:load        { nodes, edges, viewport }
 *   flow:nodeStates  { nodeStates: { [nodeId]: "pending"|"running"|... } }
 *   flow:reset       {}
 *   flow:updateNode  { nodeId, data }
 *
 * React → Alpine events:
 *   flow:changed     { nodes, edges }
 *   flow:nodeSelect  { nodeId, data }
 */

let _listeners = [];

export function initBridge(store) {
  const root = document.getElementById("react-flow-root");
  if (!root) {
    console.warn("orchestrator-bridge: #react-flow-root not found");
    return;
  }

  // React → Alpine listeners
  const handlers = {
    "flow:changed": (e) => store.onFlowChanged(e.detail),
    "flow:nodeSelect": (e) => store.onNodeSelected(e.detail),
    "flow:reactReady": () => store.setReactReady(),
  };

  for (const [event, handler] of Object.entries(handlers)) {
    root.addEventListener(event, handler);
    _listeners.push({ root, event, handler });
  }
}

export function destroyBridge() {
  for (const { root, event, handler } of _listeners) {
    root.removeEventListener(event, handler);
  }
  _listeners = [];
}
