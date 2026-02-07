import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import {
  sendJsonData,
  getContext,
  setContext,
  toastFetchError,
  toast,
  justToast,
  getConnectionStatus,
} from "/index.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";
import { store as tasksStore } from "/components/sidebar/tasks/tasks-store.js";
import { store as syncStore } from "/components/sync/sync-store.js";

const model = {
  contexts: [],
  selected: "",
  selectedContext: null,
  loggedIn: false,

  // for convenience
  getSelectedChatId() {
    return this.selected;
  },

  getSelectedContext(){
    return this.selectedContext;
  },

  init() {
    this.loggedIn = Boolean(window.runtimeInfo && window.runtimeInfo.loggedIn);
    // Initialize from sessionStorage
    const lastSelectedChat = sessionStorage.getItem("lastSelectedChat");
    if (lastSelectedChat) {
      this.selectChat(lastSelectedChat);
    }
  },

  // Update contexts from polling
  applyContexts(contextsList) {
    // Sort by created_at time (newer first)
    this.contexts = contextsList.sort(
      (a, b) => (b.created_at || 0) - (a.created_at || 0)
    );

    // Keep selectedContext in sync when the currently selected context's
    // metadata changes (e.g. project activation/deactivation).
    if (this.selected) {
      const selectedId = this.selected;
      const updated = this.contexts.find((ctx) => ctx.id === selectedId);
      if (updated) {
        this.selectedContext = updated;
      }
    }
  },

  // Select a chat
  async selectChat(id) {
    const currentContext = getContext();
    if (id === currentContext) return; // already selected

    // Proceed with context selection
    setContext(id);

    // Update selection state (will also persist to localStorage)
    this.setSelected(id);

    // In push mode, context switching triggers a new `state_request` via setContext().
    // Keep polling only as a degraded-mode fallback.
    try {
      const mode = typeof syncStore.mode === "string" ? syncStore.mode : null;
      const shouldFallbackPoll = mode === "DEGRADED";
      if (shouldFallbackPoll && typeof globalThis.poll === "function") {
        globalThis.poll();
      }
    } catch (_e) {
      // no-op
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
      justToast("Chat deleted successfully", "success", 1000, "chat-removal");
    } catch (e) {
      console.error("Error deleting chat:", e);
      toastFetchError("Error deleting chat", e);
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
      this.deselectChat();
      //await this.newChat();
    }
  },

  // Reset current chat
  async resetChat(ctxid = null) {
    try {
      const context = ctxid || this.selected || getContext();
      await sendJsonData("/chat_reset", {
        context
      });

      // Increment reset counter
      if (typeof globalThis.resetCounter === 'number') {
        globalThis.resetCounter = globalThis.resetCounter + 1;
      }      
    } catch (e) {
      toastFetchError("Error resetting chat", e);
    }
  },

  // Create new chat
  async newChat() {
    try {

      // first create a new chat on the backend
      const response = await sendJsonData("/chat_create", {
        current_context: this.selected
      });

      if (response.ok) {
        this.selectChat(response.ctxid);
        return;
      }

    } catch (e) {
      toastFetchError("Error creating new chat", e);
    }
  },

  deselectChat(){
    globalThis.deselectChat(); //TODO move here
  },

  // Smoothly scroll the chats list to top if present
  _scrollChatsToTop() {
    const listEl = document.querySelector('#chats-section .chats-config-list');
    if (!listEl) return; // no-op if not in DOM
    listEl.scrollTo({ top: 0, behavior: 'smooth' });
  },

  // Load chats from files
  async loadChats() {
    try {
      const fileContents = await this.readJsonFiles();
      const response = await sendJsonData("/chat_load", { chats: fileContents });

      if (!response) {
        toast("No response returned.", "error");
      } else {
        // Set context to first loaded chat
        if (response.ctxids?.[0]) {
          setContext(response.ctxids[0]);
        }
        toast("Chats loaded.", "success");
      }
    } catch (e) {
      toastFetchError("Error loading chats", e);
    }
  },

  // Save current chat
  async saveChat() {
    try {
      const context = this.selected || getContext();
      const response = await sendJsonData("/chat_export", { ctxid: context });

      if (!response) {
        toast("No response returned.", "error");
      } else {
        this.downloadFile(response.ctxid + ".json", response.content);
        toast("Chat file downloaded.", "success");
      }
    } catch (e) {
      toastFetchError("Error saving chat", e);
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
    this.selected = contextId || "";
    this.selectedContext = this.contexts.find((ctx) => ctx.id === this.selected);
    // if not found in contexts, try to find in tasks < not nice, will need refactor later
    if(!this.selectedContext) this.selectedContext = tasksStore.tasks.find((ctx) => ctx.id === this.selected);
    if (this.selected) {
      sessionStorage.setItem("lastSelectedChat", this.selected);
    } else {
      sessionStorage.removeItem("lastSelectedChat");
    }
  },

  // Restart the backend
  async restart() {
    // Check connection status (avoid spamming requests when already disconnected)
    const connectionStatus = getConnectionStatus();
    if (connectionStatus === false) {
      await notificationStore.frontendError(
        "Backend disconnected, cannot restart.",
        "Restart Error",
      );
      return;
    }

    // Create a backend notification first so other tabs have a chance to show it
    // before the process is replaced.
    const notificationId = await notificationStore.info(
      "Restarting...",
      "System Restart",
      "",
      9999,
      "restart",
    );

    // Best-effort: wait briefly for the notification to arrive via state sync so
    // the initiating tab (and typically other tabs) renders the toast before restart.
    if (notificationId) {
      const deadline = Date.now() + 800;
      while (Date.now() < deadline) {
        try {
          
          const stack = Array.isArray(notificationStore.toastStack) ? notificationStore.toastStack : null;
          if (stack && stack.some((toast) => toast && toast.id === notificationId)) {
            break;
          }
        } catch (_err) {
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 25));
      }
    }

    // The restart endpoint usually drops the connection as the process is replaced.
    // Do not wait on /health - recovery is driven by WebSocket CSRF preflight + reconnect.
    try {
      await sendJsonData("/restart", {});
    } catch (_e) {
      // ignore
    }
  },

  async logout() {
    try {
      await callJsonApi("/logout", {});
    } catch (_e) {
      // ignore
    }

    try {
      sessionStorage.removeItem("lastSelectedChat");
      sessionStorage.removeItem("lastSelectedTask");
    } catch (_e) {
      // ignore
    }

    try {
      window.location.reload();
    } catch (_e) {
      // ignore
    }
  }
};

const store = createStore("chats", model);

export { store };
