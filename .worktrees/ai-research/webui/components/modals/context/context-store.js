import { createStore } from "/js/AlpineStore.js";

const model = {
  // State
  isLoading: false,
  contextData: null,
  tokenCount: 0,
  error: null,
  editor: null,
  closePromise: null,

  // Open Context Window modal
  async open() {
    if (this.isLoading) return; // Prevent double-open
    
    this.isLoading = true;
    this.error = null;
    this.contextData = null;
    this.tokenCount = 0;

    try {
      // Open modal FIRST (immediate UI feedback, but DON'T await)
      this.closePromise = window.openModal('modals/context/context.html');
      
      // Setup cleanup on modal close
      if (this.closePromise && typeof this.closePromise.then === 'function') {
        this.closePromise.then(() => {
          this.destroy();
        });
      }
      
      this.updateModalTitle(); // Set initial "loading" title
      
      // Fetch data from backend
      const contextId = window.getContext();
      const response = await window.sendJsonData('/ctx_window_get', {
        context: contextId,
      });
      
      // Update state with data
      this.contextData = response.content;
      this.tokenCount = response.tokens || 0;
      this.isLoading = false;
      this.updateModalTitle(); // Update with token count
      
      // Initialize ACE editor
      this.scheduleEditorInit();
      
    } catch (error) {
      console.error("Context fetch error:", error);
      this.error = error?.message || "Failed to load context window";
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
    const container = document.getElementById("context-viewer-container");
    if (!container) {
      console.warn("Context container not found, deferring editor init");
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

    const editorInstance = window.ace.edit("context-viewer-container");
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
    this.editor.setValue(this.contextData, -1); // -1 moves cursor to start
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
        title.textContent = "Context Window – Error";
      } else if (this.isLoading) {
        title.textContent = "Context Window (loading…)";
      } else {
        title.textContent = `Context Window ~${this.tokenCount} tokens`;
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

export const store = createStore("context", model);

