import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
  // State
  loading: false,
  error: null,
  activeView: "dashboard", // dashboard, workflows, training, skills, history

  // Dashboard data
  stats: {
    total_workflows: 0,
    total_executions: 0,
    total_skills: 0,
    total_learning_paths: 0,
    executions_by_status: {},
  },
  recentExecutions: [],
  topSkills: [],
  auditLogs: [],

  // Workflows data
  workflows: [],
  selectedWorkflow: null,
  workflowHistory: [],
  workflowVisualization: "",

  // Executions data
  executions: [],
  selectedExecution: null,
  executionStatus: null,

  // Training data
  learningPaths: [],
  selectedPath: null,
  pathProgress: null,

  // Skills data
  skills: [],
  skillsByCategory: {},
  agentProficiency: [],

  // Polling
  pollingInterval: null,

  // Lifecycle
  async onOpen() {
    await this.refresh();
    this.startPolling();
  },

  cleanup() {
    this.stopPolling();
  },

  startPolling() {
    if (this.pollingInterval) return;
    this.pollingInterval = setInterval(() => {
      this.refreshSilent();
    }, 5000);
  },

  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  },

  // API calls
  async refresh() {
    this.loading = true;
    this.error = null;
    try {
      await this.loadDashboard();
    } catch (err) {
      console.error("Workflow dashboard error:", err);
      this.error = err?.message || "Failed to load workflow data";
    } finally {
      this.loading = false;
    }
  },

  async refreshSilent() {
    try {
      await this.loadDashboard();
    } catch (err) {
      console.error("Silent refresh error:", err);
    }
  },

  async loadDashboard() {
    const response = await callJsonApi("/workflow_dashboard", {});

    if (response.success) {
      this.stats = response.stats || this.stats;
      this.recentExecutions = response.recent_executions || [];
      this.topSkills = response.top_skills || [];
      this.workflows = response.workflows || [];
      this.learningPaths = response.learning_paths || [];
      this.auditLogs = response.audit_logs || [];
    } else {
      throw new Error(response.error || "Failed to load dashboard");
    }
  },

  // View switching
  switchView(view) {
    this.activeView = view;
    if (view === "workflows") {
      this.loadWorkflows();
    } else if (view === "training") {
      this.loadTraining();
    } else if (view === "skills") {
      this.loadSkills();
    } else if (view === "history") {
      this.loadAuditLogs();
    }
  },

  // Workflow operations
  async loadWorkflows() {
    this.loading = true;
    try {
      const response = await callJsonApi("/workflow_engine_api", {
        action: "list_workflows",
      });
      if (response.success) {
        this.workflows = response.workflows || [];
      }
    } catch (err) {
      this.error = err?.message || "Failed to load workflows";
    } finally {
      this.loading = false;
    }
  },

  async selectWorkflow(workflowId) {
    this.loading = true;
    try {
      const [workflowResp, visualResp, historyResp] = await Promise.all([
        callJsonApi("/workflow_engine_api", {
          action: "get_workflow",
          workflow_id: workflowId,
        }),
        callJsonApi("/workflow_engine_api", {
          action: "visualize_workflow",
          workflow_id: workflowId,
        }),
        callJsonApi("/workflow_engine_api", {
          action: "get_version_history",
          name: this.workflows.find((w) => w.workflow_id === workflowId)?.name,
        }),
      ]);

      if (workflowResp.success) {
        this.selectedWorkflow = workflowResp.workflow;
      }
      if (visualResp.success) {
        this.workflowVisualization = visualResp.diagram || "";
        this.$nextTick(() => this.renderMermaid());
      }
      if (historyResp && historyResp.success) {
        this.workflowHistory = historyResp.history || [];
      }
    } catch (err) {
      console.error("Workflow detail error:", err);
      this.error = err?.message || "Failed to load workflow detail";
    } finally {
      this.loading = false;
    }
  },

  async rollback(version) {
    if (!this.selectedWorkflow) return;
    this.loading = true;
    try {
      const response = await callJsonApi("/workflow_engine_api", {
        action: "rollback_workflow",
        name: this.selectedWorkflow.name,
        version: version,
      });
      if (response.success) {
        await this.selectWorkflow(this.selectedWorkflow.workflow_id);
      } else {
        throw new Error(response.error);
      }
    } catch (err) {
      this.error = "Rollback failed: " + err.message;
    } finally {
      this.loading = false;
    }
  },

  async loadExecutions(workflowId) {
    const response = await callJsonApi("/workflow_engine_api", {
      action: "list_executions",
      workflow_id: workflowId,
    });
    if (response.success) {
      this.executions = response.executions || [];
    }
  },

  async selectExecution(executionId) {
    this.loading = true;
    try {
      const response = await callJsonApi("/workflow_engine_api", {
        action: "get_status",
        execution_id: executionId,
      });
      if (response.success) {
        this.selectedExecution = response.execution;
        this.executionStatus = response.status;
      }
    } catch (err) {
      this.error = err?.message || "Failed to load execution";
    } finally {
      this.loading = false;
    }
  },

  // Training operations
  async loadTraining() {
    this.loading = true;
    try {
      const response = await callJsonApi("/workflow_training_api", {
        action: "list_paths",
      });
      if (response.success) {
        this.learningPaths = response.paths || [];
      }
    } catch (err) {
      this.error = err?.message || "Failed to load training data";
    } finally {
      this.loading = false;
    }
  },

  async selectPath(pathId) {
    this.loading = true;
    try {
      const [pathResp, progressResp] = await Promise.all([
        callJsonApi("/workflow_training_api", {
          action: "get_path",
          path_id: pathId,
        }),
        callJsonApi("/workflow_training_api", {
          action: "get_progress",
          path_id: pathId,
        }),
      ]);

      if (pathResp.success) {
        this.selectedPath = pathResp.path;
      }
      if (progressResp.success) {
        this.pathProgress = progressResp.progress;
      }
    } catch (err) {
      this.error = err?.message || "Failed to load path";
    } finally {
      this.loading = false;
    }
  },

  // Skills operations
  async loadSkills() {
    this.loading = true;
    try {
      const [skillsResp, profResp] = await Promise.all([
        callJsonApi("/workflow_training_api", {
          action: "list_skills",
        }),
        callJsonApi("/workflow_training_api", {
          action: "get_proficiency",
        }),
      ]);

      if (skillsResp.success) {
        this.skills = skillsResp.skills || [];
        // Group by category
        this.skillsByCategory = {};
        for (const skill of this.skills) {
          const cat = skill.category || "other";
          if (!this.skillsByCategory[cat]) {
            this.skillsByCategory[cat] = [];
          }
          this.skillsByCategory[cat].push(skill);
        }
      }
      if (profResp.success) {
        this.agentProficiency = profResp.proficiency || [];
      }
    } catch (err) {
      this.error = err?.message || "Failed to load skills";
    } finally {
      this.loading = false;
    }
  },

  // Helpers
  renderMermaid() {
    const container = document.getElementById("workflow-mermaid-container");
    if (container && this.workflowVisualization && window.mermaid) {
      // Extract just the mermaid code (remove ```mermaid and ``` markers)
      let code = this.workflowVisualization;
      if (code.startsWith("```mermaid")) {
        code = code.replace(/^```mermaid\n?/, "").replace(/\n?```$/, "");
      }

      // Clear container safely
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
      const id = "mermaid-" + Date.now();

      try {
        window.mermaid.render(id, code).then((result) => {
          // Use DOM methods to insert SVG safely
          const wrapper = document.createElement("div");
          wrapper.insertAdjacentHTML("afterbegin", result.svg);
          container.appendChild(wrapper.firstChild);
        });
      } catch (err) {
        console.error("Mermaid render error:", err);
        const pre = document.createElement("pre");
        pre.textContent = code;
        container.appendChild(pre);
      }
    }
  },

  formatDate(dateStr) {
    if (!dateStr) return "";
    try {
      const date = new Date(dateStr);
      return date.toLocaleString();
    } catch {
      return dateStr;
    }
  },

  getStatusClass(status) {
    const classes = {
      completed: "status-completed",
      running: "status-running",
      in_progress: "status-running",
      pending: "status-pending",
      failed: "status-failed",
      error: "status-failed",
    };
    return classes[status] || "status-pending";
  },

  getStatusIcon(status) {
    const icons = {
      completed: "\u2713",
      running: "\u25B6",
      in_progress: "\u25B6",
      pending: "\u25CB",
      failed: "\u2717",
      error: "\u2717",
    };
    return icons[status] || "\u25CB";
  },

  getSkillStars(level) {
    const filled = "\u2605";
    const empty = "\u2606";
    return filled.repeat(level) + empty.repeat(5 - level);
  },

  getProgressPercent(completed, total) {
    if (!total) return 0;
    return Math.round((completed / total) * 100);
  },
};

export const store = createStore("workflowDashboardStore", model);
