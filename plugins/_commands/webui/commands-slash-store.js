import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";
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
const SKILLS_API_PATH = "/plugins/_skills/skills_catalog";
const AGENT_EDITOR_API_PATH = "/plugins/_agent_editor/agent_editor";

function sanitizeCommandName(rawName) {
  return (rawName || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^[-_]+|[-_]+$/g, "");
}

function parseSlashInput(message, allowPostfix = true) {
  const text = String(message || "");
  const prefixMatch = text.match(/^\s*\/([^\s]*)(?:\s+([\s\S]*))?$/);
  const postfixMatch = prefixMatch || !allowPostfix
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

function parseReferenceInput(message, caretOffset = undefined) {
  const text = String(message || "");
  if (caretOffset === null) return { active: false, query: "", start: 0, end: 0 };
  const caret = Math.max(0, Math.min(text.length, caretOffset ?? text.length));
  const match = text.slice(0, caret).match(/(?:^|\s)@([^\s@]*)$/);
  if (!match) return { active: false, query: "", start: caret, end: caret };
  if (match[1].startsWith("[") && match[1].endsWith("]")) {
    return { active: false, query: "", start: caret, end: caret };
  }

  const token = `@${match[1]}`;
  return {
    active: true,
    query: match[1].toLowerCase(),
    start: caret - token.length,
    end: caret,
  };
}

function normalizePath(value) {
  return String(value || "").replace(/\\/g, "/").replace(/\/{2,}/g, "/").replace(/\/$/, "");
}

function fileQueryDirectory(query) {
  const value = String(query || "").replace(/^\.\//, "");
  if (value.startsWith("agent/") || value.startsWith("skill/") || value.startsWith("mcp/") || value.split("/").includes("..")) {
    return null;
  }
  const slash = value.lastIndexOf("/");
  return slash < 0 ? "" : value.slice(0, slash);
}

function mcpPolicyAllows(policy, id) {
  if (!policy || policy.mode !== "custom") return true;
  if (policy.blocked?.includes(id)) return false;
  if (policy.allowed?.includes(id)) return true;
  return policy.mcp_default === "allow";
}

function getMcpReferences(state) {
  const servers = new Map();
  const policy = state?.tools?.effective_policy;
  for (const tool of state?.tools?.catalog || []) {
    const id = String(tool?.id || "");
    const match = id.match(/^mcp:([^:]+):/);
    if (!match || tool?.available === false || !mcpPolicyAllows(policy, id)) continue;
    const name = match[1];
    servers.set(name, (servers.get(name) || 0) + 1);
  }
  return [...servers].map(([name, toolCount]) => ({ name, toolCount }));
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
  references: [],
  referenceContextId: null,
  referenceDirectoryKey: "",
  referenceRoot: "",
  referenceCatalog: [],
  referenceFiles: [],
  referenceLoadGeneration: 0,
  contextScope: { project_name: "" },
  lastContextId: "",
  active: false,
  dismissed: false,
  query: "",
  rawArguments: "",
  rawMessage: "",
  mode: "",
  referenceStart: 0,
  referenceEnd: 0,
  referenceRange: null,
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

  get filteredReferences() {
    const needle = (this.query || "").trim().toLowerCase().replace(/^\.\//, "");
    const references = Array.isArray(this.references) ? this.references : [];
    if (!needle) return references;
    return references.filter((reference) => reference.search.includes(needle));
  },

  get filteredItems() {
    return this.mode === "reference" ? this.filteredReferences : this.filteredCommands;
  },

  get selectedCommand() {
    const commands = this.filteredCommands;
    if (!commands.length) return null;
    return commands[this.selectedIndex] || commands[0] || null;
  },

  get selectedItem() {
    const items = this.filteredItems;
    if (!items.length) return null;
    return items[this.selectedIndex] || items[0] || null;
  },

  get loadingLabel() {
    return this.mode === "reference" ? "Loading references..." : "Loading slash commands...";
  },

  get emptyLabel() {
    return this.mode === "reference" ? "No matching references." : "No matching slash commands.";
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
    this.mode = "";
    this.referenceRange = null;
    this.references = [];
    this.referenceContextId = null;
    this.referenceDirectoryKey = "";
    this.referenceRoot = "";
    this.referenceCatalog = [];
    this.referenceFiles = [];
    this.referenceLoadGeneration += 1;
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

  getCaretOffset() {
    const input = this.getInputElement();
    const selection = document.getSelection?.();
    const range = selection?.rangeCount ? selection.getRangeAt(0) : null;
    if (range && chatInputStore?._isInCodeBlock?.(range.startContainer?.parentElement)) return null;
    const offsets = chatInputStore?._selectionOffsets?.(input);
    return offsets && offsets.start === offsets.end ? offsets.end : null;
  },

  captureReferenceRange(length) {
    const input = this.getInputElement();
    const selection = document.getSelection?.();
    if (!input || !selection || selection.rangeCount === 0) return null;
    const range = selection.getRangeAt(0);
    if (
      !range.collapsed ||
      range.startContainer?.nodeType !== Node.TEXT_NODE ||
      range.startOffset < length ||
      !input.contains(range.startContainer)
    ) return null;
    const triggerRange = range.cloneRange();
    triggerRange.setStart(range.startContainer, range.startOffset - length);
    return triggerRange;
  },

  async loadReferences(force = false) {
    const contextId = this.getContextId();
    const directory = fileQueryDirectory(this.query);
    const generation = ++this.referenceLoadGeneration;
    this.loading = true;

    try {
      if (force || contextId !== this.referenceContextId) {
        const [rootResult, settingsResult, skillsResult, profilesResult] = await Promise.allSettled([
          contextId ? callJsonApi("/chat_files_path_get", { ctxid: contextId }) : Promise.resolve(null),
          callJsonApi("settings_get", null),
          callJsonApi(SKILLS_API_PATH, { action: "list", context_id: contextId }),
          callJsonApi(AGENT_EDITOR_API_PATH, { action: "list", context_id: contextId }),
        ]);
        if (generation !== this.referenceLoadGeneration) return;

        this.referenceRoot = normalizePath(
          rootResult.value?.path || settingsResult.value?.settings?.workdir_path || "",
        );
        const skills = skillsResult.value?.ok && Array.isArray(skillsResult.value.skills)
          ? skillsResult.value.skills
          : [];
        const profiles = profilesResult.value?.ok && Array.isArray(profilesResult.value.profiles)
          ? profilesResult.value.profiles
          : [];
        const activeProfile = String(
          chatsStore.selectedContext?.agent_profile
          || settingsResult.value?.settings?.agent_profile
          || "",
        ).trim();
        const activeProfileAvailable = profiles.some((profile) => (
          profile?.id === activeProfile && profile?.enabled && profile?.available
        ));
        const mcpResult = activeProfileAvailable
          ? await callJsonApi(AGENT_EDITOR_API_PATH, {
            action: "load",
            profile_id: activeProfile,
            context_id: contextId,
          }).catch((error) => {
            console.error("Failed to load scoped MCP references:", error);
            return null;
          })
          : null;
        if (generation !== this.referenceLoadGeneration) return;
        const mcpServers = getMcpReferences(mcpResult?.state);
        this.referenceCatalog = [
          ...profiles.filter((profile) => (
            profile?.id !== "default" && profile?.enabled && profile?.available
          )).map((profile) => {
            const key = String(profile?.id || "").trim();
            const label = String(profile?.title || key).trim();
            return {
              id: `agent:${key}`,
              kind: "Agent",
              icon: "person",
              tone: "agent",
              label,
              value: `@[agent/${key}]`,
              description: key === label ? "Agent profile" : `Agent profile · ${key}`,
              search: `agent/${key} ${label}`.toLowerCase(),
            };
          }).filter((item) => item.id !== "agent:"),
          ...skills.filter((skill) => !skill?.hidden).map((skill) => {
            const name = String(skill?.name || "").trim();
            return {
              id: `skill:${String(skill?.path || name)}`,
              kind: "Skill",
              icon: "auto_awesome",
              tone: "skill",
              label: name,
              value: `@[skill/${name}]`,
              description: String(skill?.description || "Skill").trim(),
              search: `skill/${name} ${skill?.description || ""} ${skill?.path || ""}`.toLowerCase(),
            };
          }).filter((item) => item.label),
          ...mcpServers.map((server) => {
            const name = String(server?.name || "").trim();
            const description = `${Number(server?.toolCount || 0)} available MCP tools`;
            return {
              id: `mcp:${name}`,
              kind: "MCP",
              icon: "hub",
              tone: "mcp",
              label: name,
              value: `@[mcp/${name}]`,
              description,
              search: `mcp/${name} ${name} ${description}`.toLowerCase(),
            };
          }).filter((item) => item.label),
        ];
        this.referenceFiles = [];
        this.referenceContextId = contextId;
        this.referenceDirectoryKey = "";
      }

      const directoryKey = directory === null || !this.referenceRoot
        ? ""
        : `${this.referenceRoot}/${directory}`.replace(/\/$/, "");
      if (directory !== null && directoryKey && directoryKey !== this.referenceDirectoryKey) {
        const response = await fetchApi(`/get_work_dir_files?path=${encodeURIComponent(directoryKey)}`);
        const payload = await response.json().catch(() => ({}));
        if (generation !== this.referenceLoadGeneration) return;
        const entries = response.ok && Array.isArray(payload?.data?.entries) ? payload.data.entries : [];
        const root = this.referenceRoot.replace(/^\//, "");
        this.referenceFiles = entries.flatMap((entry) => {
          const path = normalizePath(entry?.path).replace(/^\//, "");
          if (!path || (path !== root && !path.startsWith(`${root}/`))) return [];
          const relative = path === root ? "" : path.slice(root.length + 1);
          if (!relative) return [];
          const isDirectory = Boolean(entry?.is_dir);
          const displayPath = `./${relative}${isDirectory ? "/" : ""}`;
          return [{
            id: `${isDirectory ? "folder" : "file"}:${path}`,
            kind: isDirectory ? "Folder" : "File",
            icon: isDirectory ? "folder" : "draft",
            tone: isDirectory ? "folder" : "file",
            label: displayPath,
            value: `@[${displayPath}]`,
            description: isDirectory ? "Folder in active workspace" : "File in active workspace",
            search: displayPath.toLowerCase(),
          }];
        });
        this.referenceDirectoryKey = directoryKey;
      } else if (directory === null) {
        this.referenceFiles = [];
        this.referenceDirectoryKey = "";
      }

      if (generation === this.referenceLoadGeneration) {
        this.references = [...this.referenceFiles, ...this.referenceCatalog];
        this.ensureSelection();
      }
    } catch (error) {
      console.error("Failed to load composer references:", error);
      if (generation === this.referenceLoadGeneration) {
        this.references = [...this.referenceCatalog];
      }
    } finally {
      if (generation === this.referenceLoadGeneration) this.loading = false;
    }
  },

  handleInput(event = null) {
    this.ensureBindings();
    this.dismissed = false;

    const message = this.getInputMessage(event);
    const reference = parseReferenceInput(message, this.getCaretOffset());
    if (reference.active) {
      const newReferenceSession = this.mode !== "reference";
      this.mode = "reference";
      this.active = true;
      this.query = reference.query;
      this.rawMessage = message;
      this.referenceStart = reference.start;
      this.referenceEnd = reference.end;
      this.referenceRange = this.captureReferenceRange(reference.end - reference.start);
      this.ensureSelection();
      void this.loadReferences(newReferenceSession);
      return;
    }

    const parsed = parseSlashInput(message, false);

    this.referenceRange = null;
    this.mode = parsed.active ? "slash" : "";
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

    if (event.key === "Enter" && this.selectedItem) {
      event.preventDefault();
      event.stopPropagation();
      void this.applySelectedItem(this.selectedItem);
    }
  },

  ensureSelection() {
    const items = this.filteredItems;
    if (!items.length) {
      this.selectedIndex = 0;
      return;
    }
    if (this.selectedIndex >= items.length) {
      this.selectedIndex = 0;
    }
  },

  moveSelection(delta) {
    const items = this.filteredItems;
    if (!items.length) return;
    const nextIndex =
      (this.selectedIndex + delta + items.length) % items.length;
    this.selectedIndex = nextIndex;
    this.scrollSelectedIntoView();
  },

  applySelectedItem(item) {
    return this.mode === "reference" ? this.applyReference(item) : this.applySelection(item);
  },

  applyReference(reference) {
    const input = this.getInputElement();
    if (!reference?.value || !input) return;

    const current = this.getInputMessage();
    const suffix = current.slice(this.referenceEnd);
    const separator = suffix && /^\s/.test(suffix) ? "" : " ";
    const nextText = `${current.slice(0, this.referenceStart)}${reference.value}${separator}${suffix}`;
    const caret = this.referenceStart + reference.value.length + separator.length;
    const range = this.referenceRange;
    this.referenceRange = null;
    if (range && input.contains(range.startContainer)) {
      range.deleteContents();
      const node = document.createElement("span");
      node.className = `composer-reference is-${reference.tone}`;
      node.dataset.reference = reference.value;
      node.dataset.label = reference.label;
      node.contentEditable = "false";
      node.textContent = reference.value;
      node.setAttribute("aria-label", `${reference.kind}: ${reference.label}`);
      range.insertNode(node);
      const space = separator ? document.createTextNode(separator) : null;
      if (space) node.after(space);
      range.setStartAfter(space || node);
      range.collapse(true);
      const selection = document.getSelection?.();
      selection?.removeAllRanges();
      selection?.addRange(range);
      chatInputStore?._syncMessageFromEditor?.();
    } else {
      chatInputStore.message = nextText;
      chatInputStore?._setEditorCaret?.(caret);
    }
    input.dispatchEvent(new Event("input", { bubbles: true }));
    chatInputStore.adjustTextareaHeight();
    this.active = false;
    this.dismissed = false;
    this.mode = "";
    this.query = "";
    this.selectedIndex = 0;
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
      if (type === "open_agent_editor") {
        await globalThis.openAgentEditor?.({
          view: String(effect.view || "manage"),
          profileId: String(effect.profile_id || ""),
        });
        continue;
      }
      if (type === "test_agent_profile") {
        const profileId = String(effect.profile_id || "").trim();
        if (profileId) {
          await globalThis.testAgentProfile?.(
            profileId,
            String(effect.project_name || ""),
          );
        }
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
