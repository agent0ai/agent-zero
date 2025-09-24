import { createStore } from "/js/AlpineStore.js";

const model = {
  activeTab: (localStorage.getItem("activeTab") || "chats"),

  init() {
    try {
      // Click handlers are now managed via Alpine @click directives
      // Initialize active tab on startup
      this.initializeActiveTab();
    } catch (e) {
      console.error("tabs-store.init failed", e);
    }
  },

  initializeActiveTab() {
    if (!localStorage.getItem("lastSelectedChat")) localStorage.setItem("lastSelectedChat", "");
    if (!localStorage.getItem("lastSelectedTask")) localStorage.setItem("lastSelectedTask", "");

    const active = localStorage.getItem("activeTab") || this.activeTab || "chats";
    this.activateTab(active);
  },

  activateTab(tabName) {
    // Get current context to preserve before switching
    const currentContext = globalThis.getContext ? globalThis.getContext() : "";

    // Store the current selection for the active tab before switching
    const previousTab = localStorage.getItem("activeTab");
    if (previousTab === "chats") {
      localStorage.setItem("lastSelectedChat", currentContext);
    } else if (previousTab === "tasks") {
      localStorage.setItem("lastSelectedTask", currentContext);
    }

    // Update active tab (Alpine will handle CSS classes and display via :class and x-show)
    this.setActiveTab(tabName);

    // Restore context selection based on tab
    if (tabName === "chats") {
      // Get the available contexts from store
      const chatsStore = globalThis.Alpine ? Alpine.store('chats') : null;
      const availableContexts = chatsStore?.contexts || [];

      // Restore previous chat selection
      const lastSelectedChat = localStorage.getItem("lastSelectedChat");

      // Only switch if:
      // 1. lastSelectedChat exists AND
      // 2. It's different from current context AND
      // 3. The context actually exists in our contexts list OR there are no contexts yet
      if (
        lastSelectedChat &&
        lastSelectedChat !== currentContext &&
        (availableContexts.some((ctx) => ctx.id === lastSelectedChat) ||
          availableContexts.length === 0)
      ) {
        if (globalThis.setContext) globalThis.setContext(lastSelectedChat);
      }
    } else if (tabName === "tasks") {
      // Get the available tasks from store
      const tasksStore = globalThis.Alpine ? Alpine.store('tasks') : null;
      const availableTasks = tasksStore?.tasks || [];

      // Restore previous task selection
      const lastSelectedTask = localStorage.getItem("lastSelectedTask");

      // Only switch if:
      // 1. lastSelectedTask exists AND
      // 2. It's different from current context AND
      // 3. The task actually exists in our tasks list
      if (
        lastSelectedTask &&
        lastSelectedTask !== currentContext &&
        availableTasks.some((task) => task.id === lastSelectedTask)
      ) {
        if (globalThis.setContext) globalThis.setContext(lastSelectedTask);
      }
    }

    // Request a poll update
    if (globalThis.poll) globalThis.poll();
  },

  setActiveTab(tabName) {
    this.activeTab = tabName;
    try { localStorage.setItem("activeTab", tabName); } catch {}
  },

  ensureProperTabSelection(contextId) {
    const tasksStore = globalThis.Alpine?.store('tasks');
    let isTask = false;
    
    if (tasksStore) {
      isTask = tasksStore.contains(contextId);
    }
    
    // If selecting a task but in chats tab, switch to tasks
    if (isTask && this.activeTab === "chats") {
      localStorage.setItem("lastSelectedTask", contextId);
      this.activateTab("tasks");
      return true;
    }
    
    // If selecting a chat but in tasks tab, switch to chats
    if (!isTask && this.activeTab === "tasks") {
      localStorage.setItem("lastSelectedChat", contextId);
      this.activateTab("chats");
      return true;
    }
    
    return false;
  },
};

export const store = createStore("tabs", model);


