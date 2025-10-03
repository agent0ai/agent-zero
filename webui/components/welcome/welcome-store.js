import { createStore } from "/js/AlpineStore.js";
import { store as contextStore } from "/components/chat/context/context-store.js";

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
    const hasContext = !!(globalThis.getContext && globalThis.getContext());
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
        if (globalThis.newChat) {
          globalThis.newChat();
        }
        break;
      case "settings":
        // Open settings modal
        const settingsButton = document.getElementById("settings");
        if (settingsButton) {
          settingsButton.click();
        }
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
