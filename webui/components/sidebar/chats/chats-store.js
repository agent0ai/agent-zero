import { createStore } from "/js/AlpineStore.js";
import { sendJsonData } from "/index.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

const model = {
  contexts: [],
  selected: "",

  init() {
    // Initialize from localStorage
    const lastSelectedChat = localStorage.getItem("lastSelectedChat");
    if (lastSelectedChat) {
      this.selected = lastSelectedChat;
    }
  },

  // Update contexts from polling
  applyContexts(contextsList) {
    // Sort by created_at time (newer first)
    this.contexts = contextsList.sort(
      (a, b) => (b.created_at || 0) - (a.created_at || 0)
    );
  },

  // Select a chat
  async selectChat(id) {
    const currentContext = globalThis.getContext?.();
    if (id === currentContext) return; // already selected
    
    // Proceed with context selection
    if (globalThis.setContext) {
      globalThis.setContext(id);
    }
    
    // Update selection state (will also persist to localStorage)
    this.setSelected(id);
    
    // Trigger immediate poll
    if (globalThis.poll) {
      globalThis.poll();
    }
    
    // Update scroll
    if (globalThis.updateAfterScroll) {
      globalThis.updateAfterScroll();
    }
  },

  // Delete a chat
  async killChat(id) {
    if (!id) {
      console.error("No chat ID provided for deletion");
      return;
    }

    console.log("Deleting chat with ID:", id);

    try {
      // Switch to another context if deleting current
      if (this.selected === id) {
        await this.switchFromContext(id);
      }

      // Delete the chat on the server
      await sendJsonData("/chat_remove", { context: id });

      // Update the UI - remove from contexts
      const updatedContexts = this.contexts.filter((ctx) => ctx.id !== id);
      console.log(
        "Updated contexts after deletion:",
        JSON.stringify(updatedContexts.map((c) => ({ id: c.id, name: c.name })))
      );

      // Force UI update by creating a new array
      this.contexts = [...updatedContexts];

      // Show success notification
      if (globalThis.justToast) {
        globalThis.justToast("Chat deleted successfully", "success", 1000, "chat-removal");
      }
    } catch (e) {
      console.error("Error deleting chat:", e);
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error deleting chat", e);
      }
    }
  },

  // Switch from a context that's being deleted
  async switchFromContext(id) {
    // Find an alternate chat to switch to
    let alternateChat = null;
    for (let i = 0; i < this.contexts.length; i++) {
      if (this.contexts[i].id !== id) {
        alternateChat = this.contexts[i];
        break;
      }
    }

    if (alternateChat) {
      await this.selectChat(alternateChat.id);
    } else {
      // If no other chats, create a new empty context
      if (globalThis.newChat) {
        await globalThis.newChat();
      }
    }
  },

  // Reset current chat
  async resetChat(ctxid = null) {
    try {
      const context = ctxid || this.selected || globalThis.getContext?.();
      await sendJsonData("/chat_reset", {
        context
      });
      
      // Increment reset counter
      if (typeof globalThis.resetCounter === 'number') {
        globalThis.resetCounter = globalThis.resetCounter + 1;
      }
      
      if (globalThis.updateAfterScroll) {
        globalThis.updateAfterScroll();
      }
    } catch (e) {
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error resetting chat", e);
      }
    }
  },

  // Create new chat
  async newChat() {
    try {
      if (globalThis.newContext) {
        globalThis.newContext();
      }
      if (globalThis.updateAfterScroll) {
        globalThis.updateAfterScroll();
      }
    } catch (e) {
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error creating new chat", e);
      }
    }
  },

  // Load chats from files
  async loadChats() {
    try {
      const fileContents = await this.readJsonFiles();
      const response = await sendJsonData("/chat_load", { chats: fileContents });

      if (!response) {
        if (globalThis.toast) globalThis.toast("No response returned.", "error");
      } else {
        // Set context to first loaded chat
        if (globalThis.setContext && response.ctxids?.[0]) {
          globalThis.setContext(response.ctxids[0]);
        }
        if (globalThis.toast) globalThis.toast("Chats loaded.", "success");
      }
    } catch (e) {
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error loading chats", e);
      }
    }
  },

  // Save current chat
  async saveChat() {
    try {
      const context = this.selected || globalThis.getContext?.();
      const response = await sendJsonData("/chat_export", { ctxid: context });

      if (!response) {
        if (globalThis.toast) globalThis.toast("No response returned.", "error");
      } else {
        this.downloadFile(response.ctxid + ".json", response.content);
        if (globalThis.toast) globalThis.toast("Chat file downloaded.", "success");
      }
    } catch (e) {
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error saving chat", e);
      }
    }
  },

  // Helper: read JSON files
  readJsonFiles() {
    return new Promise((resolve, reject) => {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".json";
      input.multiple = true;

      input.click();

      input.onchange = async () => {
        const files = input.files;
        if (!files.length) {
          resolve([]);
          return;
        }

        const filePromises = Array.from(files).map((file) => {
          return new Promise((fileResolve, fileReject) => {
            const reader = new FileReader();
            reader.onload = () => fileResolve(reader.result);
            reader.onerror = fileReject;
            reader.readAsText(file);
          });
        });

        try {
          const fileContents = await Promise.all(filePromises);
          resolve(fileContents);
        } catch (error) {
          reject(error);
        }
      };
    });
  },

  // Helper: download file
  downloadFile(filename, content) {
    const blob = new Blob([content], { type: "application/json" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = filename;
    link.click();

    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 0);
  },

  // Check if context exists
  contains(contextId) {
    return this.contexts.some((ctx) => ctx.id === contextId);
  },

  // Get first context ID
  firstId() {
    return this.contexts.length > 0 ? this.contexts[0].id : null;
  },

  // Set selected context
  setSelected(contextId) {
    this.selected = contextId;
    localStorage.setItem("lastSelectedChat", contextId);
  },

  // Restart the backend
  async restart() {
    try {
      // Check connection status
      const connectionStatus = globalThis.getConnectionStatus?.();
      if (connectionStatus === false) {
        await notificationStore.frontendError(
          "Backend disconnected, cannot restart.",
          "Restart Error"
        );
        return;
      }
      
      // Try to initiate restart
      const resp = await sendJsonData("/restart", {});
    } catch (e) {
      // Show restarting message
      await notificationStore.frontendInfo("Restarting...", "System Restart", 9999, "restart");

      let retries = 0;
      const maxRetries = 240; // 60 seconds with 250ms interval

      while (retries < maxRetries) {
        try {
          const resp = await sendJsonData("/health", {});
          // Server is back up
          await new Promise((resolve) => setTimeout(resolve, 250));
          await notificationStore.frontendSuccess("Restarted", "System Restart", 5, "restart");
          return;
        } catch (e) {
          // Server still down, keep waiting
          retries++;
          await new Promise((resolve) => setTimeout(resolve, 250));
        }
      }

      // Restart failed or timed out
      await notificationStore.frontendError(
        "Restart timed out or failed",
        "Restart Error",
        8,
        "restart"
      );
    }
  }
};

const store = createStore("chats", model);

export { store };
