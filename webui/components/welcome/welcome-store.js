import { createStore } from "/js/AlpineStore.js";

const model = {
  init() {
    this.initialize();
  },

  initialize() {
    // Nothing special needed for initialization yet
  },

  // Check if dark mode is active
  get isDarkMode() {
    return document.body.classList.contains('dark-mode');
  },

  // Execute an action by ID
  executeAction(actionId) {
    switch(actionId) {
      case 'new-chat':
        if (globalThis.newChat) {
          globalThis.newChat();
        }
        break;
      case 'settings':
        // Open settings modal
        const settingsButton = document.getElementById('settings');
        if (settingsButton) {
          settingsButton.click();
        }
        break;
      case 'website':
        window.open('https://agent-zero.ai', '_blank');
        break;
      case 'github':
        window.open('https://github.com/agent0ai/agent-zero', '_blank');
        break;
    }
  }
};

// Create and export the store
const store = createStore("welcomeStore", model);
export { store };