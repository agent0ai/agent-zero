import { createStore } from "/js/AlpineStore.js";
import { getContext } from "/index.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as memoryStore } from "/components/settings/memory/memory-dashboard-store.js";
import { store as projectsStore } from "/components/projects/projects-store.js";

const model = {
  // State
  isVisible: true,

  init() {
    // Initialize visibility based on current context
    this.updateVisibility();

    // Watch for context changes with faster polling for immediate response
    setInterval(() => {
      this.updateVisibility();
    }, 50); // 50ms for very responsive updates
  },

  // Update visibility based on current context
  updateVisibility() {
    const hasContext = !!getContext();
    this.isVisible = !hasContext;
  },

  // Hide welcome screen
  hide() {
    this.isVisible = false;
  },

  // Show welcome screen
  show() {
    this.isVisible = true;
  },

  // Execute an action by ID
  executeAction(actionId) {
    switch (actionId) {
      case "new-chat":
        chatsStore.newChat();
        break;
      case "settings":
        // Open settings modal
        const settingsButton = document.getElementById("settings");
        if (settingsButton) {
          settingsButton.click();
        }
        break;
      case "projects":
        projectsStore.openProjectsModal();
        break;
      case "memory":
        memoryStore.openModal();
        break;
      case "website":
        window.open("https://agent-zero.ai", "_blank");
        break;
      case "github":
        window.open("https://github.com/agent0ai/agent-zero", "_blank");
        break;
    }
  },
};

// Create and export the store
const store = createStore("welcomeStore", model);
export { store };
