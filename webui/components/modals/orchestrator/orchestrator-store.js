import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const store = createStore("orchestrator", {

  // Flow management
  flows: [],
  currentFlow: null,
  currentFlowName: "",
  currentFilename: "",
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
    await Promise.all([this.fetchAgentProfiles(), this.loadFlows()]);
  },

  // Lifecycle — called via x-destroy when modal unmounts
  onClose() {
    this.currentFlow = null;
    this.currentFlowName = "";
    this.currentFilename = "";
    this.dirty = false;
    this.running = false;
    this.flowRunId = null;
    this.nodeStates = {};
    this.inspectedNodeId = null;
    this.inspectedNodeData = null;
    this.reactReady = false;
  },

  // ─── Flow CRUD ───

  async loadFlows() {
    try {
      const resp = await callJsonApi("/flow_list", {});
      if (resp && resp.ok) {
        this.flows = resp.flows || [];
      }
    } catch (e) {
      console.warn("Failed to load flows:", e);
      this.flows = [];
    }
  },

  async loadFlow(filename) {
    try {
      const resp = await callJsonApi("/flow_load", { filename });
      if (resp && resp.ok && resp.flow) {
        this.currentFlow = resp.flow;
        this.currentFlowName = resp.flow.name || filename;
        this.currentFilename = resp.flow.filename || filename;
        this.dirty = false;
        this.showFlowList = false;
        this.showInspector = false;
        // Wait for React to be ready, then load the flow into canvas
        this._waitForReactThenLoad();
      }
    } catch (e) {
      console.warn("Failed to load flow:", e);
    }
  },

  async saveFlow() {
    if (!this.currentFlow) return;

    try {
      const resp = await callJsonApi("/flow_save", {
        flow: this.currentFlow,
        filename: this.currentFilename || "",
      });
      if (resp && resp.ok) {
        this.currentFilename = resp.filename;
        this.dirty = false;
      }
    } catch (e) {
      console.warn("Failed to save flow:", e);
    }
  },

  async deleteFlow(filename) {
    try {
      const resp = await callJsonApi("/flow_delete", { filename });
      if (resp && resp.ok) {
        this.flows = this.flows.filter((f) => f.filename !== filename);
      }
    } catch (e) {
      console.warn("Failed to delete flow:", e);
    }
  },

  // ─── Agent Profiles ───

  async fetchAgentProfiles() {
    try {
      const resp = await callJsonApi("/agents", { action: "list" });
      if (resp && resp.ok && resp.data) {
        this.agentProfiles = resp.data;
      }
    } catch (e) {
      console.warn("Failed to fetch agent profiles:", e);
      this.agentProfiles = [{ name: "default", title: "Default Agent" }];
    }
  },

  // ─── Flow creation ───

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
    this.currentFilename = "";
    this.dirty = false;
    this.showFlowList = false;
    this._waitForReactThenLoad();
  },

  // ─── React canvas bridge ───

  onFlowChanged(detail) {
    if (this.currentFlow) {
      this.currentFlow.nodes = detail.nodes;
      this.currentFlow.edges = detail.edges;
      this.dirty = true;
    }
  },

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

  updateNodeConfig(nodeId, newData) {
    this._dispatchToReact("flow:updateNode", { nodeId, data: newData });
    this.dirty = true;
  },

  // ─── Navigation ───

  backToFlowList() {
    this.currentFlow = null;
    this.currentFlowName = "";
    this.currentFilename = "";
    this.dirty = false;
    this.showFlowList = true;
    this.showInspector = false;
    this.inspectedNodeId = null;
    this._dispatchToReact("flow:reset", {});
    this.loadFlows();
  },

  setReactReady() {
    this.reactReady = true;
  },

  // ─── Helpers ───

  _dispatchToReact(eventName, detail) {
    const root = document.getElementById("react-flow-root");
    if (root) {
      root.dispatchEvent(new CustomEvent(eventName, { detail }));
    }
  },

  _waitForReactThenLoad() {
    const load = () => {
      if (!this.currentFlow) return;
      this._dispatchToReact("flow:load", {
        nodes: this.currentFlow.nodes,
        edges: this.currentFlow.edges,
        viewport: this.currentFlow.viewport,
      });
    };

    if (this.reactReady) {
      load();
    } else {
      // Poll until React is ready (CDN modules loading)
      const interval = setInterval(() => {
        if (this.reactReady) {
          clearInterval(interval);
          load();
        }
      }, 200);
      // Safety timeout: give up after 15s
      setTimeout(() => clearInterval(interval), 15000);
    }
  },
});

export { store };
