import { createStore } from "/js/AlpineStore.js";

// Tasks sidebar store: tasks list and selected task id
const model = {
  tasks: [],
  selected: "",

  init() {
    // No-op: data is driven by poll() in index.js; this store provides a stable target
  },

  // Apply tasks coming from poll() and keep them sorted (newest first)
  applyTasks(tasksList) {
    try {
      const tasks = Array.isArray(tasksList) ? tasksList : [];
      const sorted = [...tasks].sort((a, b) => (b?.created_at || 0) - (a?.created_at || 0));
      this.tasks = sorted;
    } catch (e) {
      console.error("tasks-store.applyTasks failed", e);
      this.tasks = [];
    }
  },

  // Update selected task and persist for tab restore
  setSelected(taskId) {
    this.selected = taskId || "";
    try { localStorage.setItem("lastSelectedTask", this.selected); } catch {}
  },

  // Returns true if a task with the given id exists in the current list
  contains(taskId) {
    return Array.isArray(this.tasks) && this.tasks.some((t) => t?.id === taskId);
  },

  // Convenience: id of the first task in the current list (or empty string)
  firstId() {
    return (Array.isArray(this.tasks) && this.tasks[0]?.id) || "";
  },
};

export const store = createStore("tasks", model);


