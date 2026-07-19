import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import {
  toastFrontendError,
  toastFrontendSuccess,
} from "/components/notifications/notification-store.js";

const GOAL_API_PATH = "/plugins/_goal/goal";

const model = {
  goal: null,
  loading: false,
  saving: false,
  editing: false,
  draft: "",
  lastContextId: "",
  intervalId: null,
  clockIntervalId: null,
  goalChangedHandler: null,
  now: Date.now(),

  get visible() {
    return Boolean(this.goal?.objective && this.goal.status !== "complete");
  },

  get contextId() {
    return chatsStore?.getSelectedChatId?.() || globalThis.getContext?.() || "";
  },

  get statusLabel() {
    const status = this.goal?.status || "active";
    if (status === "paused") return "Goal paused";
    if (status === "complete") return "Goal complete";
    if (status === "blocked") return "Goal blocked";
    return "Pursuing goal";
  },

  get statusIcon() {
    const status = this.goal?.status || "active";
    if (status === "paused") return "pause_circle";
    if (status === "complete") return "check_circle";
    if (status === "blocked") return "error";
    return "track_changes";
  },

  get elapsedSeconds() {
    if (!this.goal) return 0;
    const status = this.goal.status || "active";
    const storedSeconds = Number.parseInt(this.goal.elapsed_seconds, 10);
    let seconds = Number.isNaN(storedSeconds) ? 0 : storedSeconds;
    if (Number.isNaN(storedSeconds) && status !== "active") {
      seconds = this.secondsBetween(this.goal.created_at, this.goal.updated_at);
    }
    if (status === "active") {
      seconds += this.secondsBetween(
        this.goal.active_since || this.goal.created_at || this.goal.updated_at,
        this.now,
      );
    }
    return Math.max(0, seconds);
  },

  secondsBetween(start, end) {
    const startMs = Date.parse(start || "");
    const endMs = typeof end === "number" ? end : Date.parse(end || "");
    if (Number.isNaN(startMs) || Number.isNaN(endMs)) return 0;
    return Math.max(0, Math.floor((endMs - startMs) / 1000));
  },

  get elapsedLabel() {
    const seconds = this.elapsedSeconds;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    if (hours) return `${hours}h ${minutes}m`;
    if (minutes) return `${minutes}m ${remainingSeconds}s`;
    return `${remainingSeconds}s`;
  },

  onMount() {
    document.getElementById("progress-bar-box")?.classList.add("has-goal-bar");
    this.goalChangedHandler = (event) => {
      const detail = event?.detail || {};
      if (detail.goal === null) {
        this.goal = null;
      }
      void this.refresh(true);
    };
    window.addEventListener("goal:changed", this.goalChangedHandler);
    this.clockIntervalId = window.setInterval(() => {
      this.now = Date.now();
    }, 1000);
    this.intervalId = window.setInterval(() => this.refresh(), 3000);
    void this.refresh(true);
  },

  cleanup() {
    document.getElementById("progress-bar-box")?.classList.remove("has-goal-bar");
    if (this.goalChangedHandler) {
      window.removeEventListener("goal:changed", this.goalChangedHandler);
    }
    if (this.intervalId) {
      window.clearInterval(this.intervalId);
    }
    if (this.clockIntervalId) {
      window.clearInterval(this.clockIntervalId);
    }
    this.goalChangedHandler = null;
    this.intervalId = null;
    this.clockIntervalId = null;
  },

  async refresh(force = false) {
    const contextId = this.contextId;
    if (!contextId) {
      this.goal = null;
      this.lastContextId = "";
      return;
    }
    if (!force && this.loading) return;

    this.loading = true;
    try {
      const response = await callJsonApi(GOAL_API_PATH, {
        action: "get",
        context_id: contextId,
      });
      this.goal = response?.goal || null;
      this.now = Date.now();
      this.lastContextId = contextId;
      if (!this.goal) this.editing = false;
    } catch (error) {
      console.error("Failed to load goal:", error);
      this.goal = null;
      this.lastContextId = contextId;
    } finally {
      this.loading = false;
    }
  },

  startEdit() {
    if (!this.goal) return;
    this.draft = this.goal.objective || "";
    this.editing = true;
    requestAnimationFrame(() => {
      document.querySelector(".goal-strip-input")?.focus?.();
      document.querySelector(".goal-strip-input")?.select?.();
    });
  },

  cancelEdit() {
    this.editing = false;
    this.draft = "";
  },

  async saveEdit() {
    const objective = (this.draft || "").trim();
    if (!objective) {
      void toastFrontendError("Goal objective is required.", "Goal");
      return;
    }
    const response = await this.update(
      { action: "update", objective, status: "active" },
      "Goal updated.",
    );
    this.editing = false;
    if (response?.reactivated) {
      await globalThis.sendMessage?.({
        message: response.goal?.objective || objective,
        context: response.goal?.context_id || this.contextId,
      });
    }
  },

  async pauseOrResume() {
    if (!this.goal) return;
    const action = this.goal.status === "active" ? "pause" : "resume";
    await this.update(
      { action },
      action === "pause" ? "Goal paused." : "Goal resumed.",
    );
  },

  async deleteGoal() {
    await this.update({ action: "delete" }, "Goal deleted.");
  },

  async update(payload, successMessage) {
    const contextId = this.contextId;
    if (!contextId || this.saving) return;

    this.saving = true;
    try {
      const response = await callJsonApi(GOAL_API_PATH, {
        ...payload,
        context_id: contextId,
      });
      this.goal = response?.goal || null;
      this.now = Date.now();
      this.lastContextId = contextId;
      window.dispatchEvent(new CustomEvent("goal:changed", {
        detail: { goal: this.goal, context_id: contextId },
      }));
      void toastFrontendSuccess(successMessage, "Goal");
      return response;
    } catch (error) {
      console.error("Failed to update goal:", error);
      void toastFrontendError(error?.message || "Failed to update goal.", "Goal");
      return null;
    } finally {
      this.saving = false;
    }
  },
};

export const store = createStore("goalBar", model);
