import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as chatInputStore } from "/components/chat/input/input-store.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import {
  toastFrontendError,
  toastFrontendInfo,
  toastFrontendSuccess,
} from "/components/notifications/notification-store.js";
import { store as commandsManagerStore } from "/plugins/_commands/webui/commands-store.js";

const COMMANDS_API_PATH = "/plugins/_commands/commands";

function sanitizeCommandName(rawName) {
  return (rawName || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^[-_]+|[-_]+$/g, "");
}

function parseSlashInput(message) {
  const text = String(message || "");
  const prefixMatch = text.match(/^\s*\/([^\s]*)(?:\s+([\s\S]*))?$/);
  const postfixMatch = prefixMatch
    ? null
    : text.match(/^([\s\S]*\S)\s+\/([^\s]*)\s*$/);
  if (!prefixMatch && !postfixMatch) {
    return {
      active: false,
      query: "",
      rawArguments: "",
      rawMessage: text,
    };
  }

  return {
    active: true,
    query: (prefixMatch?.[1] || postfixMatch?.[2] || "").trim().toLowerCase(),
    rawArguments: prefixMatch?.[2] || postfixMatch?.[1]?.trim() || "",
    rawMessage: text,
  };
}

function notifyError(message) {
  void toastFrontendError(message, "Commands");
}

function notifySuccess(message) {
  void toastFrontendSuccess(message, "Commands");
}

const HTML_ESCAPE = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (char) => HTML_ESCAPE[char]);
}

function notifyInfo(title, message) {
  const formatted = escapeHtml(message).replace(/\n/g, "<br>");
  void toastFrontendInfo(formatted, title || "Commands", 3, "", undefined, true);
}

const model = {
  loading: false,
  applying: false,
  commands: [],
  contextScope: { project_name: "" },
  lastContextId: "",
  active: false,
  dismissed: false,
  query: "",
  rawArguments: "",
  rawMessage: "",
  selectedIndex: 0,
  boundInput: null,
  keydownHandler: null,
  inputHandler: null,
  focusHandler: null,
  commandsUpdatedHandler: null,

  get menuVisible() {
    return this.active && !this.dismissed;
  },

  get filteredCommands() {
    const needle = (this.query || "").trim().toLowerCase();
    const commands = Array.isArray(this.commands) ? this.commands : [];

    if (!needle) return commands;

    return commands.filter((command) => {
      const haystack = `${command?.name || ""} ${command?.description || ""}`.toLowerCase();
      return haystack.includes(needle);
    });
  },

  get selectedCommand() {
    const commands = this.filteredCommands;
    if (!commands.length) return null;
    return commands[this.selectedIndex] || commands[0] || null;
  },

  get emptyStateLabel() {
    const name = sanitizeCommandName(this.query || "");
    return name ? `Create /${name}` : "Create slash command";
  },

  onMount() {
    this.ensureBindings();

    this.keydownHandler = (event) => this.handleKeydown(event);
    this.commandsUpdatedHandler = () => {
      this.commands = [];
      if (this.menuVisible) {
        void this.loadCommands(true);
      }
    };

    document.addEventListener("keydown", this.keydownHandler, true);
    window.addEventListener("commands:updated", this.commandsUpdatedHandler);
    this.handleInput();
  },

  cleanup() {
    this.removeBindings();
    if (this.keydownHandler) {
      document.removeEventListener("keydown", this.keydownHandler, true);
    }
    if (this.commandsUpdatedHandler) {
      window.removeEventListener("commands:updated", this.commandsUpdatedHandler);
    }
    this.keydownHandler = null;
    this.commandsUpdatedHandler = null;
    this.dismissed = false;
    this.active = false;
    this.query = "";
    this.rawArguments = "";
    this.rawMessage = "";
    this.selectedIndex = 0;
    this.applying = false;
  },

  ensureBindings() {
    const input = this.getInputElement();
    if (!input || input === this.boundInput) return;

    this.removeBindings();

    this.inputHandler = (event) => this.handleInput(event);
    this.focusHandler = () => this.handleInput();
    input.addEventListener("input", this.inputHandler);
    input.addEventListener("focus", this.focusHandler);
    this.boundInput = input;
  },

  removeBindings() {
    if (this.boundInput && this.inputHandler) {
      this.boundInput.removeEventListener("input", this.inputHandler);
    }
    if (this.boundInput && this.focusHandler) {
      this.boundInput.removeEventListener("focus", this.focusHandler);
    }
    this.boundInput = null;
    this.inputHandler = null;
    this.focusHandler = null;
  },

  getInputElement() {
    return document.getElementById("chat-input");
  },

  getInputMessage(event = null) {
    const target = event?.target || null;
    const targetEditor = target?.closest?.("#chat-input");
    if (targetEditor?.isContentEditable || target?.isContentEditable) {
      return (
        chatInputStore?._editorToMarkdown?.() ||
        targetEditor?.textContent ||
        target?.textContent ||
        ""
      );
    }
    if (typeof target?.value === "string") return target.value;

    const input = this.getInputElement();
    if (input?.isContentEditable) {
      return chatInputStore?._editorToMarkdown?.() ?? input.textContent ?? "";
    }
    if (typeof input?.value === "string") return input.value;
    return chatInputStore?.message ?? "";
  },

  getContextId() {
    return chatsStore?.getSelectedChatId?.() || globalThis.getContext?.() || "";
  },

  async loadCommands(force = false) {
    const contextId = this.getContextId();

    if (!force && this.commands.length && contextId === this.lastContextId) {
      this.ensureSelection();
      return;
    }

    this.loading = true;
    try {
      const response = await callJsonApi(COMMANDS_API_PATH, {
        action: "list_effective",
        context_id: contextId,
      });
      this.commands = Array.isArray(response?.commands) ? response.commands : [];
      this.contextScope = response?.scope || {
        project_name: "",
      };
      this.lastContextId = contextId;
      this.ensureSelection();
    } catch (error) {
      console.error("Failed to load effective commands:", error);
      this.commands = [];
      this.contextScope = { project_name: "" };
    } finally {
      this.loading = false;
    }
  },

  handleInput(event = null) {
    this.ensureBindings();
    this.dismissed = false;

    const message = this.getInputMessage(event);
    const parsed = parseSlashInput(message);

    this.active = parsed.active;
    this.query = parsed.query;
    this.rawArguments = parsed.rawArguments;
    this.rawMessage = parsed.rawMessage;

    if (!this.active) {
      this.selectedIndex = 0;
      return;
    }

    this.ensureSelection();
    void this.loadCommands();
  },

  async resolveBeforeSend(sendCtx) {
    if (!sendCtx || this.applying) return;

    const parsed = parseSlashInput(sendCtx.message);
    const commandName = sanitizeCommandName(parsed.query);
    if (!parsed.active || !commandName) return;

    await this.loadCommands();
    const command = this.commands.find((item) => item.name === commandName);
    if (!command || !this.getInputElement()) return;

    this.rawMessage = parsed.rawMessage;
    this.rawArguments = parsed.rawArguments;
    sendCtx.cancel = true;
    await this.applySelection(command);
  },

  handleKeydown(event) {
    const input = this.getInputElement();
    if (!this.menuVisible || !input || document.activeElement !== input) return;
    if (event.isComposing || event.keyCode === 229) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      event.stopPropagation();
      this.moveSelection(1);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      event.stopPropagation();
      this.moveSelection(-1);
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      this.dismissed = true;
      return;
    }

    if (event.key === "Enter" && this.selectedCommand) {
      event.preventDefault();
      event.stopPropagation();
      void this.applySelection(this.selectedCommand);
    }
  },

  ensureSelection() {
    const commands = this.filteredCommands;
    if (!commands.length) {
      this.selectedIndex = 0;
      return;
    }
    if (this.selectedIndex >= commands.length) {
      this.selectedIndex = 0;
    }
  },

  moveSelection(delta) {
    const commands = this.filteredCommands;
    if (!commands.length) return;
    const nextIndex =
      (this.selectedIndex + delta + commands.length) % commands.length;
    this.selectedIndex = nextIndex;
    this.scrollSelectedIntoView();
  },

  scrollSelectedIntoView() {
    requestAnimationFrame(() => {
      document
        .querySelector(".commands-slash-results .commands-slash-item.active")
        ?.scrollIntoView({ block: "nearest" });
    });
  },

  async applySelection(command) {
    if (!command || this.applying) return;
    const input = this.getInputElement();
    if (!input) return;

    this.applying = true;
    try {
      const contextId = this.getContextId();
      const fallbackSlash = this.rawMessage?.trim()
        ? this.rawMessage
        : this.rawArguments
          ? `/${command.name} ${this.rawArguments}`
          : `/${command.name}`;

      const response = await callJsonApi(COMMANDS_API_PATH, {
        action: "resolve",
        path: command.path,
        slash_text: fallbackSlash,
        project_name: this.contextScope?.project_name || "",
        context_id: contextId,
      });

      const applied = await this.applyResolution(response?.resolution, input);
      if (!applied?.hadToast && !applied?.hadError) {
        notifySuccess(`Applied /${command.name}`);
      }
    } catch (error) {
      console.error("Failed to apply slash command:", error);
      notifyError(error?.message || "Failed to apply slash command.");
    } finally {
      this.applying = false;
    }
  },

  async applyResolution(resolution, input) {
    const result = resolution?.result || {};
    const hasText = typeof result.text === "string";
    let nextText = hasText ? result.text : this.getInputMessage();
    const effects = Array.isArray(result.effects) ? result.effects : [];
    let hadToast = false;
    let hadError = false;
    let shouldSend = false;

    for (const effect of effects) {
      if (!effect || typeof effect !== "object") continue;
      const type = String(effect.type || "").trim().toLowerCase();
      if (type === "replace_input") {
        nextText = String(effect.text || "");
        continue;
      }
      if (type === "append_input") {
        const chunk = String(effect.text || "");
        nextText = nextText ? `${nextText}\n${chunk}` : chunk;
        continue;
      }
      if (type === "send_message") {
        nextText = String(effect.text || nextText || "");
        shouldSend = true;
        continue;
      }
      if (type === "toast") {
        hadToast = true;
        const level = String(effect.level || "info").toLowerCase();
        const message = String(effect.message || "");
        if (!message) continue;
        if (level === "error") {
          hadError = true;
          notifyError(message);
        } else {
          notifySuccess(message);
        }
        continue;
      }
      if (type === "new_chat") {
        await chatsStore?.newChat?.();
        continue;
      }
      if (type === "select_chat") {
        const contextId = String(effect.context_id || "").trim();
        if (contextId) await chatsStore?.selectChat?.(contextId);
        continue;
      }
      if (type === "reset_chat") {
        await chatsStore?.resetChat?.(String(effect.context_id || "") || null);
        continue;
      }
      if (type === "pause_agent") {
        await chatInputStore?.pauseAgent?.(Boolean(effect.paused));
        continue;
      }
      if (type === "nudge_agent") {
        await chatInputStore?.nudge?.();
        continue;
      }
      if (type === "open_modal") {
        const path = String(effect.path || "").trim();
        if (path) await window.openModal?.(path);
        continue;
      }
      if (type === "show_markdown") {
        hadToast = true;
        notifyInfo(
          String(effect.title || "Slash Command"),
          String(effect.content || ""),
        );
        continue;
      }
      if (type === "computer_use") {
        hadToast = true;
        notifyInfo(
          "Computer Use",
          String(effect.fallback || "Use Host access in A0 Launcher, or run this command in A0 CLI."),
        );
        continue;
      }
      if (type === "goal_changed") {
        window.dispatchEvent(new CustomEvent("goal:changed", { detail: effect }));
        continue;
      }
      if (type === "open_plugin_config") {
        const pluginName = String(effect.plugin || "").trim();
        if (pluginName) {
          const { store } = await import("/components/plugins/plugin-settings-store.js");
          await store.openConfig(
            pluginName,
            String(effect.project_name || ""),
            String(effect.agent_profile || ""),
          );
        }
        continue;
      }
      if (type === "compact_chat") {
        const { store } = await import("/plugins/_chat_compaction/webui/compact-store.js");
        await store.fetchStats();
        continue;
      }
      if (type === "attach_files") {
        await this.openAttachmentPicker(effect);
        continue;
      }
      if (type === "copy_transcript") {
        await this.copyTranscript();
        hadToast = true;
        continue;
      }
      if (type === "clear_transcript") {
        const history = document.getElementById("chat-history");
        if (history) history.innerHTML = "";
        continue;
      }
    }

    if (typeof input.value === "string") input.value = nextText;
    chatInputStore.message = nextText;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    chatInputStore.adjustTextareaHeight();
    input.focus();
    if (typeof input.setSelectionRange === "function") {
      input.setSelectionRange(nextText.length, nextText.length);
    } else {
      chatInputStore?._setEditorCaret?.(nextText.length);
    }

    this.active = false;
    this.dismissed = false;
    this.query = "";
    this.rawArguments = "";
    this.rawMessage = nextText;
    this.selectedIndex = 0;
    if (shouldSend && nextText.trim()) {
      await chatInputStore?.sendMessage?.();
    }
    return { hadToast, hadError };
  },

  openAttachmentPicker(effect = {}) {
    return new Promise((resolve) => {
      const picker = document.createElement("input");
      let settled = false;
      const done = () => {
        if (settled) return;
        settled = true;
        picker.remove();
        resolve();
      };
      picker.type = "file";
      picker.multiple = true;
      picker.accept = String(effect.accept || "*");
      picker.style.display = "none";
      picker.addEventListener("change", () => {
        attachmentsStore?.handleFiles?.(picker.files || []);
        done();
      }, { once: true });
      window.addEventListener("focus", () => setTimeout(done, 500), { once: true });
      document.body.appendChild(picker);
      picker.click();
    });
  },

  async copyTranscript() {
    const text = document.getElementById("chat-history")?.innerText?.trim() || "";
    if (!text) {
      notifyError("No visible transcript to copy.");
      return;
    }
    await navigator.clipboard.writeText(text);
    notifySuccess("Transcript copied.");
  },

  openCreateCommand() {
    commandsManagerStore.openManager({
      projectName: this.contextScope?.project_name || "",
      prefillName: sanitizeCommandName(this.query || ""),
      openEditor: true,
    });
    this.dismissed = true;
  },
};

export const store = createStore("commandsSlash", model);
