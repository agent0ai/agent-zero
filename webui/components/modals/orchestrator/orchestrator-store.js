import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const store = createStore("orchestrator", {

  // Flow management
  flows: [],
  templates: [],
  currentFlow: null,
  currentFlowName: "",
  currentFilename: "",
  dirty: false,

  // Execution state
  flowRunId: null,
  nodeStates: {},
  nodeOutputs: {},
  finalOutput: null,
  executionError: null,
  running: false,

  // UI state
  inspectedNodeId: null,
  inspectedNodeData: null,
  agentProfiles: [{ key: "default", label: "Default Agent" }],
  showFlowList: true,
  showInspector: false,
  showOutputPanel: true,
  reactReady: false,

  get hasExecutionState() {
    return this.running || this.finalOutput !== null || this.executionError;
  },

  _resetExecutionState() {
    this.running = false;
    this.flowRunId = null;
    this.nodeStates = {};
    this.nodeOutputs = {};
    this.finalOutput = null;
    this.executionError = null;
  },

  // Lifecycle — called via x-init when modal mounts
  async onOpen() {
    this.reactReady = false;
    this.showFlowList = true;
    this.showInspector = false;
    this.inspectedNodeId = null;
    this.inspectedNodeData = null;
    this.dirty = false;
    this._resetExecutionState();
    await Promise.all([this.fetchAgentProfiles(), this.loadFlows(), this.loadTemplates()]);
  },

  // Lifecycle — called via x-destroy when modal unmounts
  onClose() {
    this._stopStatusPolling();
    this.currentFlow = null;
    this.currentFlowName = "";
    this.currentFilename = "";
    this.dirty = false;
    this._resetExecutionState();
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

  async loadTemplates() {
    try {
      const resp = await callJsonApi("/flow_template_list", {});
      if (resp && resp.ok) {
        this.templates = resp.templates || [];
      }
    } catch (e) {
      console.warn("Failed to load templates:", e);
      this.templates = [];
    }
  },

  useTemplate(template) {
    const flow = JSON.parse(JSON.stringify(template.flow));
    this.currentFlow = flow;
    this.currentFlowName = flow.name || template.name;
    this.currentFilename = "";
    this.dirty = false;
    this.showFlowList = false;
    this.showInspector = false;
    this._resetExecutionState();
    this._waitForReactThenLoad();
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
      this.agentProfiles = [{ key: "default", label: "Default Agent" }];
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
      // Strip React Flow internal metadata — keep only serializable essentials
      this.currentFlow.nodes = (detail.nodes || []).map((n) => ({
        id: n.id,
        type: n.type,
        position: { x: n.position.x, y: n.position.y },
        data: { ...n.data, _status: undefined, _progress: undefined },
      }));
      this.currentFlow.edges = (detail.edges || []).map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        ...(e.sourceHandle ? { sourceHandle: e.sourceHandle } : {}),
        ...(e.targetHandle ? { targetHandle: e.targetHandle } : {}),
      }));
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

  // ─── Execution ───

  _statusPollInterval: null,

  async executeFlow(userPrompt) {
    if (!this.currentFlow || this.running) return;

    this._resetExecutionState();
    this.running = true;

    try {
      const resp = await callJsonApi("/flow_execute", {
        flow: this.currentFlow,
        user_prompt: userPrompt || "",
      });
      if (resp && resp.ok && resp.run_id) {
        this.flowRunId = resp.run_id;
        this._startStatusPolling();
      } else {
        this.running = false;
        console.warn("Failed to start flow:", resp?.error);
      }
    } catch (e) {
      this.running = false;
      console.warn("Failed to execute flow:", e);
    }
  },

  async stopFlow() {
    if (!this.flowRunId) return;

    try {
      await callJsonApi("/flow_stop", { run_id: this.flowRunId });
    } catch (e) {
      console.warn("Failed to stop flow:", e);
    }
  },

  _startStatusPolling() {
    this._stopStatusPolling();
    this._statusPollInterval = setInterval(() => this._pollStatus(), 1000);
  },

  _stopStatusPolling() {
    if (this._statusPollInterval) {
      clearInterval(this._statusPollInterval);
      this._statusPollInterval = null;
    }
  },

  async _pollStatus() {
    if (!this.flowRunId) {
      this._stopStatusPolling();
      return;
    }

    try {
      const resp = await callJsonApi("/flow_status", {
        run_id: this.flowRunId,
      });
      if (resp && resp.ok) {
        this.nodeStates = resp.node_states || {};
        this.nodeOutputs = resp.node_outputs || {};
        this._dispatchToReact("flow:nodeStates", {
          nodeStates: this.nodeStates,
          nodeProgress: resp.node_progress || {},
        });

        if (!resp.running) {
          this.running = false;
          this.finalOutput = resp.final_output || null;
          this.executionError = resp.error || null;
          this._stopStatusPolling();
        }
      }
    } catch (e) {
      console.warn("Status poll failed:", e);
    }
  },

  dismissResults() {
    this._resetExecutionState();
    this.showOutputPanel = true;
    this._dispatchToReact("flow:nodeStates", { nodeStates: {} });
  },

  async sendResultToChat() {
    if (!this.finalOutput) return;

    const contextId = globalThis.getContext?.();
    if (!contextId) {
      console.warn("No active chat context to send results to");
      return;
    }

    try {
      const resp = await callJsonApi("/flow_result", {
        context_id: contextId,
        content: this.finalOutput,
        heading: `Flow: ${this.currentFlowName || "Orchestration"}`,
      });
      if (resp && resp.ok) {
        console.log("Flow result sent to chat");
      }
    } catch (e) {
      console.warn("Failed to send flow result to chat:", e);
    }
  },

  // ─── Navigation ───

  backToFlowList() {
    this._stopStatusPolling();
    this.currentFlow = null;
    this.currentFlowName = "";
    this.currentFilename = "";
    this.dirty = false;
    this._resetExecutionState();
    this.showFlowList = true;
    this.showInspector = false;
    this.inspectedNodeId = null;
    this.reactReady = false;
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
