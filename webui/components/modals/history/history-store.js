import { createStore } from "/js/AlpineStore.js";

const model = {
  // State
  isLoading: false,
  historyData: null,
  tokenCount: 0,
  error: null,
  editor: null,
  closePromise: null,

  // Open History modal
  async open() {
    if (this.isLoading) return; // Prevent double-open
    
    this.isLoading = true;
    this.error = null;
    this.historyData = null;
    this.tokenCount = 0;

    try {
      // Open modal FIRST (immediate UI feedback, but DON'T await)
      this.closePromise = window.openModal('modals/history/history.html');
      
      // Setup cleanup on modal close
      if (this.closePromise && typeof this.closePromise.then === 'function') {
        this.closePromise.then(() => {
          this.destroy();
        });
      }
      
      this.updateModalTitle(); // Set initial "loading" title
      
      // Fetch data from backend
      const contextId = window.getContext();
      const response = await window.sendJsonData('/history_get', {
        context: contextId,
      });
      
      // Update state with data
      this.historyData = response.history;
      this.tokenCount = response.tokens || 0;
      this.isLoading = false;
      this.updateModalTitle(); // Update with token count
      
      // Initialize ACE editor
      this.scheduleEditorInit();
      
    } catch (error) {
      console.error("History fetch error:", error);
      this.error = error?.message || "Failed to load history";
      this.isLoading = false;
      this.updateModalTitle(); // Show error in title
    }
  },

  scheduleEditorInit() {
    // Use double requestAnimationFrame to ensure DOM is ready
    window.requestAnimationFrame(() => {
      if (this.isLoading || this.error) return;
      window.requestAnimationFrame(() => this.initEditor());
    });
  },

  initEditor() {
    const container = document.getElementById("history-viewer-container");
    if (!container) {
      console.warn("History container not found, deferring editor init");
      return;
    }

    // Destroy old instance if exists
    if (this.editor?.destroy) {
      this.editor.destroy();
    }

    // Check if ACE is available
    if (!window.ace?.edit) {
      console.error("ACE editor not available");
      this.error = "Editor library not loaded";
      return;
    }

    const editorInstance = window.ace.edit("history-viewer-container");
    if (!editorInstance) {
      console.error("Failed to create ACE editor instance");
      return;
    }

    this.editor = editorInstance;

    // Configure theme based on dark mode (legacy parity: != "false")
    const darkMode = window.localStorage?.getItem("darkMode");
    const theme = darkMode !== "false" ? "ace/theme/github_dark" : "ace/theme/tomorrow";

    this.editor.setTheme(theme);
    this.editor.session.setMode("ace/mode/markdown");
    this.editor.setValue(this.historyData, -1); // -1 moves cursor to start
    this.editor.setReadOnly(true);
    this.editor.clearSelection();
  },

  updateModalTitle() {
    window.requestAnimationFrame(() => {
      const modalTitles = document.querySelectorAll(".modal.show .modal-title");
      if (!modalTitles.length) return;
      
      // Get the last (topmost) modal title
      const title = modalTitles[modalTitles.length - 1];
      if (!title) return;

      if (this.error) {
        title.textContent = "History – Error";
      } else if (this.isLoading) {
        title.textContent = "History (loading…)";
      } else {
        title.textContent = `History ~${this.tokenCount} tokens`;
      }
    });
  },

  // Optional: cleanup method for lifecycle management
  destroy() {
    if (this.editor?.destroy) {
      this.editor.destroy();
    }
    this.editor = null;
  },
};

export const store = createStore("history", model);

