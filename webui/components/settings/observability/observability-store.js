import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getCurrentContextId } from "/js/shortcuts.js";

const model = {
  contextId: "",
  events: [],
  stats: {},
  workflowRuns: [],
  savedRuns: [],
  activeRunId: "",
  loading: false,
  workflowLoading: false,
  error: null,
  workflowError: null,

  async onOpen() {
    this.contextId = getCurrentContextId() || "";
    await this.refresh();
  },

  async refresh() {
    this.error = null;
    this.workflowError = null;
    this.loading = true;
    try {
      const [telemetryResp, workflowResp] = await Promise.all([
        callJsonApi("/telemetry_get", { context: this.contextId }),
        callJsonApi("/workflow_get", { context: this.contextId }),
      ]);
      this.events = telemetryResp.events || [];
      this.stats = telemetryResp.stats || {};
      this.workflowRuns = workflowResp.runs || [];
      this.savedRuns = workflowResp.saved_runs || [];
      this.activeRunId = workflowResp.active_run_id || "";
    } catch (err) {
      console.error(err);
      this.error = err?.message || "Failed to load telemetry.";
    } finally {
      this.loading = false;
    }
  },

  async refreshWorkflows() {
    this.workflowError = null;
    this.workflowLoading = true;
    try {
      const resp = await callJsonApi("/workflow_get", {
        context: this.contextId,
      });
      this.workflowRuns = resp.runs || [];
      this.savedRuns = resp.saved_runs || [];
      this.activeRunId = resp.active_run_id || "";
    } catch (err) {
      console.error(err);
      this.workflowError = err?.message || "Failed to load workflows.";
    } finally {
      this.workflowLoading = false;
    }
  },

  async clear() {
    if (!this.contextId) return;
    await callJsonApi("/telemetry_clear", { context: this.contextId });
    this.events = [];
    this.stats = {};
  },

  async saveWorkflow() {
    if (!this.contextId) return;
    const label = window.prompt("Optional label for this workflow run:", "");
    await callJsonApi("/workflow_save", {
      context: this.contextId,
      label: label || "",
    });
    await this.refreshWorkflows();
  },

  async clearWorkflows() {
    if (!this.contextId) return;
    await callJsonApi("/workflow_clear", { context: this.contextId });
    this.workflowRuns = [];
    this.savedRuns = [];
    this.activeRunId = "";
  },

  get statEntries() {
    return Object.entries(this.stats || {}).map(([tool, data]) => ({
      tool,
      ...data,
    }));
  },

  get activeRun() {
    if (!this.workflowRuns.length) return null;
    const active = this.workflowRuns.find((run) => run.run_id === this.activeRunId);
    return active || this.workflowRuns[0];
  },

  hasDeploymentTelemetry(step) {
    return !!step?.deployment_telemetry || !!step?.deployment_status;
  },

  deploymentStages(step) {
    const stages = step?.deployment_telemetry?.stages;
    return Array.isArray(stages) ? stages : [];
  },

  deploymentFailedStage(step) {
    return step?.deployment_telemetry?.failed_stage || "";
  },

  deploymentStatus(step) {
    return step?.deployment_status || step?.deployment_telemetry?.status || "";
  },

  formatMs(value) {
    if (value === null || value === undefined || value === "") return "";
    const parsed = Number(value);
    if (Number.isNaN(parsed)) return "";
    return `${Math.round(parsed)}ms`;
  },
};

export const store = createStore("observabilityStore", model);
