import { createStore } from "/js/AlpineStore.js";

const model = {
  activeTab: (localStorage.getItem("activeTab") || "chats"),

  init() {
    try {
      // Attach click handlers once Alpine is ready
      this.setupTabs();
    } catch (e) {
      console.error("tabs-store.init failed", e);
    }
  },

  setupTabs() {
    const chatsTab = document.getElementById("chats-tab");
    const tasksTab = document.getElementById("tasks-tab");

    if (chatsTab && tasksTab) {
      // Remove existing listeners by cloning (prevents duplicate bindings on hot reload)
      const chatsClone = chatsTab.cloneNode(true);
      const tasksClone = tasksTab.cloneNode(true);
      chatsTab.parentNode.replaceChild(chatsClone, chatsTab);
      tasksTab.parentNode.replaceChild(tasksClone, tasksTab);

      chatsClone.addEventListener("click", () => {
        this.setActiveTab("chats");
        if (globalThis.activateTab) globalThis.activateTab("chats");
      });

      tasksClone.addEventListener("click", () => {
        this.setActiveTab("tasks");
        if (globalThis.activateTab) globalThis.activateTab("tasks");
      });
    } else {
      console.error("Tab elements not found");
      setTimeout(() => this.setupTabs(), 100);
    }
  },

  initializeActiveTab() {
    if (!localStorage.getItem("lastSelectedChat")) localStorage.setItem("lastSelectedChat", "");
    if (!localStorage.getItem("lastSelectedTask")) localStorage.setItem("lastSelectedTask", "");

    const active = localStorage.getItem("activeTab") || this.activeTab || "chats";
    this.setActiveTab(active);
    if (globalThis.activateTab) globalThis.activateTab(active);
  },

  setActiveTab(tabName) {
    this.activeTab = tabName;
    try { localStorage.setItem("activeTab", tabName); } catch {}
  },
};

export const store = createStore("tabs", model);


