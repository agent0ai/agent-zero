import { createStore } from "/js/AlpineStore.js";
import * as shortcuts from "/js/shortcuts.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";
import { store as messageQueueStore } from "/components/chat/message-queue/message-queue-store.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";

const model = {
  paused: false,
  message: "",
  _history: [],
  _historyIndex: null,
  _draft: "",
  _historyCtxid: null,
  /** Composer + menu (bottom actions moved into dropdown) */
  chatMoreMenuOpen: false,
  progressText: "",
  progressActive: false,

  toggleChatMoreMenu() {
    this.chatMoreMenuOpen = !this.chatMoreMenuOpen;
  },

  closeChatMoreMenu() {
    this.chatMoreMenuOpen = false;
  },

  _getSendState() {
    const hasInput = this.message.trim() || attachmentsStore?.attachments?.length > 0;
    const hasQueue = !!messageQueueStore?.hasQueue;
    const running = !!chatsStore.selectedContext?.running;

    if (hasQueue && !hasInput) return "all";
    if ((running || hasQueue) && hasInput) return "queue";
    return "normal";
  },

  get inputPlaceholder() {
    const state = this._getSendState();
    if (state === "all") return "Press Enter to send queued messages";
    // Show progress as ghost text when agent is working and input is empty
    if (this.progressText && !this.message) {
      return "|>  " + this.progressText;
    }
    return "Type your message here...";
  },

  // Computed: send button icon type
  get sendButtonIcon() {
    const state = this._getSendState();
    if (state === "all") return "send_and_archive";
    if (state === "queue") return "schedule_send";
    return "send";
  },

  // Computed: send button CSS class
  get sendButtonClass() {
    const state = this._getSendState();
    if (state === "all") return "send-queue send-all";
    if (state === "queue") return "send-queue queue";
    return "";
  },

  // Computed: send button title
  get sendButtonTitle() {
    const state = this._getSendState();
    if (state === "all") return "Send all queued messages";
    if (state === "queue") return "Add to queue";
    return "Send message";
  },

  init() {
    console.log("Input store initialized");
    // Event listeners are now handled via Alpine directives in the component
  },

  async sendMessage() {
    // Capture sent prompt to per-chat history (bash-style)
    try { this._pushHistory(this.message); } catch (_e) { /* ignore */ }
    // Delegate to the global function
    if (globalThis.sendMessage) {
      await globalThis.sendMessage();
    }
  },

  adjustTextareaHeight() {
    const chatInput = document.getElementById("chat-input");
    if (chatInput) {
      if (!this.message) chatInput.value = "";
      chatInput.style.height = "auto";
      chatInput.style.height = chatInput.scrollHeight + "px";
      // pick up any layout shift triggered by the height assignment
      chatInput.style.height = Math.max(chatInput.scrollHeight, parseInt(chatInput.style.height)) + "px";
    }
  },

  async pauseAgent(paused) {
    const prev = this.paused;
    this.paused = paused;
    try {
      const context = globalThis.getContext?.();
      if (!globalThis.sendJsonData)
        throw new Error("sendJsonData not available");
      await globalThis.sendJsonData("/pause", { paused, context });
    } catch (e) {
      this.paused = prev;
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error pausing agent", e);
      }
    }
  },

  async nudge() {
    try {
      const context = globalThis.getContext();
      await globalThis.sendJsonData("/nudge", { ctxid: context });
    } catch (e) {
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error nudging agent", e);
      }
    }
  },

  async loadKnowledge() {
    try {
      const resp = await shortcuts.callJsonApi(
        "/plugins/_memory/knowledge_path_get",
        { ctxid: shortcuts.getCurrentContextId() }
      );
      if (!resp.ok) throw new Error("Error getting knowledge path");
      const path = resp.path;

      // open file browser and wait for it to close
      await fileBrowserStore.open(path);

      // progress notification
      shortcuts.frontendNotification({
        type: shortcuts.NotificationType.PROGRESS,
        message: "Loading knowledge...",
        priority: shortcuts.NotificationPriority.NORMAL,
        displayTime: 999,
        group: "knowledge_load",
        frontendOnly: true,
      });

      // then reindex knowledge
      await globalThis.sendJsonData("/plugins/_memory/knowledge_reindex", {
        ctxid: shortcuts.getCurrentContextId(),
      });

      // finished notification
      shortcuts.frontendNotification({
        type: shortcuts.NotificationType.SUCCESS,
        message: "Knowledge loaded successfully",
        priority: shortcuts.NotificationPriority.NORMAL,
        displayTime: 2,
        group: "knowledge_load",
        frontendOnly: true,
      });
    } catch (e) {
      // error notification
      shortcuts.frontendNotification({
        type: shortcuts.NotificationType.ERROR,
        message: "Error loading knowledge",
        priority: shortcuts.NotificationPriority.NORMAL,
        displayTime: 5,
        group: "knowledge_load",
        frontendOnly: true,
      });
    }
  },

  // previous implementation without projects
  async _loadKnowledge() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".txt,.pdf,.csv,.html,.json,.md";
    input.multiple = true;

    input.onchange = async () => {
      try {
        const formData = new FormData();
        for (let file of input.files) {
          formData.append("files[]", file);
        }

        formData.append("ctxid", globalThis.getContext());

        const response = await globalThis.fetchApi("/import_knowledge", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          if (globalThis.toast)
            globalThis.toast(await response.text(), "error");
        } else {
          const data = await response.json();
          if (globalThis.toast) {
            globalThis.toast(
              "Knowledge files imported: " + data.filenames.join(", "),
              "success"
            );
          }
        }
      } catch (e) {
        if (globalThis.toastFetchError) {
          globalThis.toastFetchError("Error loading knowledge", e);
        }
      }
    };

    input.click();
  },

  async browseFiles(path) {
    if (!path) {
      const ctxid = shortcuts.getCurrentContextId();

      if (ctxid) {
        try {
          const resp = await shortcuts.callJsonApi("/chat_files_path_get", {
            ctxid,
          });
          if (resp.ok) path = resp.path;
        } catch (_e) {
          console.error("Error getting chat files path", _e);
        }
      }
    }
    await fileBrowserStore.open(path);
  },

  focus() {
    const chatInput = document.getElementById("chat-input");
    if (chatInput) {
      chatInput.focus();
    }
  },

  _loadHistory() {
    let ctxid = null;
    try { ctxid = shortcuts.getCurrentContextId(); } catch (_e) { ctxid = null; }
    this._historyCtxid = ctxid;
    this._history = [];
    this._historyIndex = null;
    this._draft = "";
    if (!ctxid) return;
    let raw = null;
    try { raw = localStorage.getItem("a0:chat-history:" + ctxid); } catch (_e) { raw = null; }
    if (raw !== null) {
      try {
        const arr = JSON.parse(raw);
        if (Array.isArray(arr)) {
          this._history = arr.filter((s) => typeof s === "string");
        }
      } catch (_e) { /* ignore */ }
      return;
    }
    // No entry yet for this chat: seed from rendered chat DOM (one-time bootstrap)
    try {
      const seeded = this._seedFromChatDom();
      if (seeded.length > 0) {
        this._history = seeded;
        this._saveHistory();
      } else {
        // Persist an empty array so we don't re-seed on every nav; respects user clearing
        this._saveHistory();
      }
    } catch (_e) { /* ignore */ }
  },

  _seedFromChatDom() {
    const out = [];
    let nodes;
    try {
      nodes = document.querySelectorAll(".user-container .message-user .message-text pre");
    } catch (_e) {
      return out;
    }
    for (const pre of nodes) {
      const text = (pre.textContent || "").trim();
      if (!text) continue;
      if (out.length > 0 && out[out.length - 1] === text) continue; // ignoredups
      out.push(text);
    }
    if (out.length > 50) return out.slice(-50);
    return out;
  },

  _saveHistory() {
    if (!this._historyCtxid) return;
    try {
      localStorage.setItem(
        "a0:chat-history:" + this._historyCtxid,
        JSON.stringify(this._history)
      );
    } catch (_e) { /* ignore quota / disabled */ }
  },

  _ensureHistoryLoaded() {
    let ctxid = null;
    try { ctxid = shortcuts.getCurrentContextId(); } catch (_e) { ctxid = null; }
    if (ctxid !== this._historyCtxid) {
      this._loadHistory();
    }
  },

  _pushHistory(text) {
    if (typeof text !== "string") return;
    const trimmed = text.trim();
    if (!trimmed) return;
    this._ensureHistoryLoaded();
    if (this._history.length > 0 && this._history[this._history.length - 1] === trimmed) {
      this._historyIndex = null;
      this._draft = "";
      return;
    }
    this._history.push(trimmed);
    if (this._history.length > 50) {
      this._history = this._history.slice(-50);
    }
    this._saveHistory();
    this._historyIndex = null;
    this._draft = "";
  },

  _setCaretStart() {
    queueMicrotask(() => {
      const ta = document.getElementById("chat-input");
      if (ta) {
        try { ta.setSelectionRange(0, 0); } catch (_e) { /* ignore */ }
        try { ta.scrollTop = 0; } catch (_e) { /* ignore */ }
      }
      this.adjustTextareaHeight();
    });
  },

  _setCaretEnd() {
    queueMicrotask(() => {
      const ta = document.getElementById("chat-input");
      if (ta) {
        const end = ta.value.length;
        try { ta.setSelectionRange(end, end); } catch (_e) { /* ignore */ }
        try { ta.scrollTop = ta.scrollHeight; } catch (_e) { /* ignore */ }
      }
      this.adjustTextareaHeight();
    });
  },

  historyPrev($event) {
    if ($event && ($event.isComposing || $event.keyCode === 229)) return;
    const ta = ($event && $event.target) ? $event.target : document.getElementById("chat-input");
    if (!ta) return;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    if (start !== 0 || end !== 0) return;
    $event.preventDefault();
    this._ensureHistoryLoaded();
    if (this._history.length === 0) return;
    if (this._historyIndex === null) {
      this._draft = this.message || "";
      this._historyIndex = this._history.length - 1;
    } else if (this._historyIndex > 0) {
      this._historyIndex -= 1;
    } else {
      return;
    }
    this.message = this._history[this._historyIndex];
    this._setCaretStart();
  },

  historyNext($event) {
    if ($event && ($event.isComposing || $event.keyCode === 229)) return;
    const ta = ($event && $event.target) ? $event.target : document.getElementById("chat-input");
    if (!ta) return;
    const value = ta.value;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    if (start !== value.length || end !== value.length) return;
    $event.preventDefault();
    if (this._historyIndex === null) return;
    if (this._historyIndex < this._history.length - 1) {
      this._historyIndex += 1;
      this.message = this._history[this._historyIndex];
    } else {
      this._historyIndex = null;
      this.message = this._draft || "";
      this._draft = "";
    }
    this._setCaretEnd();
  },

  reset() {
    this.message = "";
    attachmentsStore.clearAttachments();
    this.chatMoreMenuOpen = false;
    this._historyIndex = null;
    this._draft = "";
    this.adjustTextareaHeight();
  }
};

const store = createStore("chatInput", model);

export { store };
