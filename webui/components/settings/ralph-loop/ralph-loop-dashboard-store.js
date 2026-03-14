import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
  // State
  loading: false,
  error: null,
  activeView: "dashboard", // dashboard, history

  // Dashboard data
  stats: {
    total_loops: 0,
    active_loops: 0,
    completed_loops: 0,
    cancelled_loops: 0,
    stale_active_loops: 0,
    total_iterations: 0,
    avg_iterations_per_loop: 0,
    success_rate: 0,
  },
  activeLoops: [],
  recentLoops: [],

  // Detail view data
  selectedLoop: null,
  loopHistory: [],

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
    }, 3000); // Faster polling for active loops
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
      console.error("Ralph Loop dashboard error:", err);
      this.error = err?.message || "Failed to load Ralph Loop data";
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
    const response = await callJsonApi("/ralph_loop_dashboard", {});

    if (response.success) {
      this.stats = response.stats || this.stats;
      this.activeLoops = response.active_loops || [];
      this.recentLoops = response.recent_loops || [];
    } else {
      throw new Error(response.error || "Failed to load dashboard");
    }
  },

  // View switching
  switchView(view) {
    this.activeView = view;
  },

  // Control operations
  async pauseLoop(loopId) {
    this.loading = true;
    try {
      const response = await callJsonApi("/ralph_loop_control", {
        action: "pause",
        loop_id: loopId,
      });
      if (!response.success) {
        throw new Error(response.error || "Failed to pause loop");
      }
      await this.refresh();
    } catch (err) {
      this.error = err?.message || "Failed to pause loop";
    } finally {
      this.loading = false;
    }
  },

  async resumeLoop(loopId) {
    this.loading = true;
    try {
      const response = await callJsonApi("/ralph_loop_control", {
        action: "resume",
        loop_id: loopId,
      });
      if (!response.success) {
        throw new Error(response.error || "Failed to resume loop");
      }
      await this.refresh();
    } catch (err) {
      this.error = err?.message || "Failed to resume loop";
    } finally {
      this.loading = false;
    }
  },

  async cancelLoop(loopId) {
    if (!confirm("Are you sure you want to cancel this Ralph loop?")) {
      return;
    }
    this.loading = true;
    try {
      const response = await callJsonApi("/ralph_loop_control", {
        action: "cancel",
        loop_id: loopId,
        reason: "Cancelled via UI",
      });
      if (!response.success) {
        throw new Error(response.error || "Failed to cancel loop");
      }
      await this.refresh();
    } catch (err) {
      this.error = err?.message || "Failed to cancel loop";
    } finally {
      this.loading = false;
    }
  },

  async viewDetails(loopId) {
    this.loading = true;
    try {
      const [detailsResp, historyResp] = await Promise.all([
        callJsonApi("/ralph_loop_control", {
          action: "get_details",
          loop_id: loopId,
        }),
        callJsonApi("/ralph_loop_control", {
          action: "get_history",
          loop_id: loopId,
        }),
      ]);

      if (detailsResp.success) {
        this.selectedLoop = detailsResp.loop;
      }
      if (historyResp.success) {
        this.loopHistory = historyResp.iterations || [];
      }
      this.activeView = "details";
    } catch (err) {
      this.error = err?.message || "Failed to load loop details";
    } finally {
      this.loading = false;
    }
  },

  closeDetails() {
    this.selectedLoop = null;
    this.loopHistory = [];
    this.activeView = "dashboard";
  },

  // Helpers
  formatDate(dateStr) {
    if (!dateStr) return "-";
    try {
      const date = new Date(dateStr);
      return date.toLocaleString();
    } catch {
      return dateStr;
    }
  },

  formatRelativeTime(dateStr) {
    if (!dateStr) return "-";
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return "just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      return `${diffDays}d ago`;
    } catch {
      return dateStr;
    }
  },

  getStatusClass(status) {
    const classes = {
      active: "status-active",
      completed: "status-completed",
      cancelled: "status-cancelled",
      paused: "status-paused",
      max_iterations: "status-max-iterations",
    };
    return classes[status] || "status-active";
  },

  getStatusIcon(status) {
    const icons = {
      active: "\uD83D\uDD04", // 🔄
      completed: "\u2705", // ✅
      cancelled: "\u274C", // ❌
      paused: "\u23F8\uFE0F", // ⏸️
      max_iterations: "\uD83D\uDCCA", // 📊
    };
    return icons[status] || "\uD83D\uDD04";
  },

  calculateProgress(loop) {
    if (!loop.max_iterations || loop.max_iterations === 0) return 0;
    return Math.round((loop.current_iteration / loop.max_iterations) * 100);
  },

  truncatePrompt(prompt, maxLen = 80) {
    if (!prompt) return "";
    if (prompt.length <= maxLen) return prompt;
    return prompt.substring(0, maxLen) + "...";
  },

  formatDuration(startedAt, completedAt) {
    if (!startedAt) return "-";
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const diffMs = end - start;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return "<1m";
    if (diffMins < 60) return `${diffMins}m`;
    return `${diffHours}h ${diffMins % 60}m`;
  },
};

export const store = createStore("ralphLoopDashboardStore", model);
