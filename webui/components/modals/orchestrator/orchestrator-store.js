import { createStore } from "/js/AlpineStore.js";

const store = createStore("orchestrator", {

  // Flow management
  flows: [],
  currentFlow: null,
  currentFlowName: "",
  dirty: false,

  // Execution state
  flowRunId: null,
  nodeStates: {},
  running: false,

  // UI state
  inspectedNodeId: null,
  inspectedNodeData: null,
  agentProfiles: [],
  showFlowList: true,
  showInspector: false,
  reactReady: false,

  // Lifecycle — called via x-init when modal mounts
  async onOpen() {
    this.reactReady = false;
    this.showFlowList = true;
    this.showInspector = false;
    this.inspectedNodeId = null;
    this.inspectedNodeData = null;
    this.dirty = false;
    this.running = false;
    this.flowRunId = null;
    this.nodeStates = {};
    await this.fetchAgentProfiles();
  },

  // Lifecycle — called via x-destroy when modal unmounts
  onClose() {
    this.currentFlow = null;
    this.currentFlowName = "";
    this.dirty = false;
    this.running = false;
    this.flowRunId = null;
    this.nodeStates = {};
    this.inspectedNodeId = null;
    this.inspectedNodeData = null;
    this.reactReady = false;
  },

  // Fetch available agent profiles
  async fetchAgentProfiles() {
    try {
      const resp = await (globalThis.callJsonApi || globalThis.fetch)("/api/agents", {});
      if (resp && resp.agents) {
        this.agentProfiles = resp.agents;
      }
    } catch (e) {
      console.warn("Failed to fetch agent profiles:", e);
      this.agentProfiles = [{ name: "default", title: "Default Agent" }];
    }
  },

  // New flow
  newFlow() {
    this.currentFlow = {
      name: "Untitled Flow",
      description: "",
      nodes: [
        {
          id: "input-1",
          type: "inputNode",
          position: { x: 250, y: 50 },
          data: { label: "User Prompt", promptMode: "runtime", fixedPrompt: "" },
        },
        {
          id: "output-1",
          type: "outputNode",
          position: { x: 250, y: 400 },
          data: { label: "Final Response", format: "markdown" },
        },
      ],
      edges: [],
      viewport: { x: 0, y: 0, zoom: 1 },
    };
    this.currentFlowName = "Untitled Flow";
    this.dirty = false;
    this.showFlowList = false;
    this._dispatchToReact("flow:load", {
      nodes: this.currentFlow.nodes,
      edges: this.currentFlow.edges,
      viewport: this.currentFlow.viewport,
    });
  },

  // Handle flow changes from React canvas
  onFlowChanged(detail) {
    if (this.currentFlow) {
      this.currentFlow.nodes = detail.nodes;
      this.currentFlow.edges = detail.edges;
      this.dirty = true;
    }
  },

  // Handle node selection from React canvas
  onNodeSelected(detail) {
    if (detail && detail.nodeId) {
      this.inspectedNodeId = detail.nodeId;
      this.inspectedNodeData = detail.data || null;
      this.showInspector = true;
    } else {
      this.inspectedNodeId = null;
      this.inspectedNodeData = null;
      this.showInspector = false;
    }
  },

  // Update node config from inspector
  updateNodeConfig(nodeId, newData) {
    this._dispatchToReact("flow:updateNode", { nodeId, data: newData });
    this.dirty = true;
  },

  // Back to flow list
  backToFlowList() {
    this.currentFlow = null;
    this.currentFlowName = "";
    this.dirty = false;
    this.showFlowList = true;
    this.showInspector = false;
    this.inspectedNodeId = null;
    this._dispatchToReact("flow:reset", {});
  },

  // Mark React as ready
  setReactReady() {
    this.reactReady = true;
  },

  // Bridge helper
  _dispatchToReact(eventName, detail) {
    const root = document.getElementById("react-flow-root");
    if (root) {
      root.dispatchEvent(new CustomEvent(eventName, { detail }));
    }
  },
});

export { store };
