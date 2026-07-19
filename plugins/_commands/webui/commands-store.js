import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import {
  toastFrontendError,
  toastFrontendSuccess,
} from "/components/notifications/notification-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";

const COMMANDS_API_PATH = "/plugins/_commands/commands";
const MAIN_MODAL_PATH = "/plugins/_commands/webui/main.html";
const EDITOR_MODAL_PATH = "/plugins/_commands/webui/editor.html";

function createEmptyEditor() {
  return {
    mode: "create",
    existingPath: "",
    path: "",
    name: "",
    description: "",
    argumentHint: "",
    commandType: "text",
    includeHistory: false,
    body: "",
    extraFrontmatter: {},
  };
}

function safeStringify(value) {
  try {
    return JSON.stringify(value ?? {});
  } catch {
    return "";
  }
}

function sanitizeCommandName(rawName) {
  return (rawName || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^[-_]+|[-_]+$/g, "");
}

function buildDefaultBody(commandType = "text") {
  if (commandType === "script") {
    return [
      "def run(payload):",
      "    args = payload.get('arguments', {})",
      "    flags = args.get('flags', {})",
      "    positional = args.get('positional', [])",
      "    return {",
      "        'text': f\"Script command received args: {positional} flags: {flags}\",",
      "        'effects': [],",
      "    }",
      "",
    ].join("\n");
  }
  return "Describe the work to perform here.\n\n{raw}";
}

function notifyError(message) {
  void toastFrontendError(message, "Commands");
}

function notifySuccess(message) {
  void toastFrontendSuccess(message, "Commands");
}

function emitCommandsUpdated() {
  window.dispatchEvent(new CustomEvent("commands:updated"));
}

const model = {
  loading: false,
  saving: false,
  projects: [],
  projectName: "",
  scope: null,
  contextScope: { project_name: "" },
  commands: [],
  builtinCommands: [],
  pendingScope: null,
  pendingCreate: null,
  editor: createEmptyEditor(),
  editorSnapshot: "",

  get selectedScopeLabel() {
    return this.scope?.scope_label || "Global";
  },

  get hasCommands() {
    return (this.commands || []).length > 0;
  },

  get editorTitle() {
    return this.editor.mode === "edit" ? "Edit Slash Command" : "Create Slash Command";
  },

  get editorDirty() {
    return this._serializeEditor() !== this.editorSnapshot;
  },

  get editorBodyLabel() {
    return this.editor.commandType === "script" ? "Python hook" : "Text template";
  },

  openManager(options = {}) {
    const hasExplicitScope = Object.prototype.hasOwnProperty.call(options, "projectName");

    this.pendingScope = hasExplicitScope
      ? {
          projectName: options.projectName || "",
        }
      : null;

    this.pendingCreate =
      options.openEditor || options.prefillName
        ? {
            name: options.prefillName || "",
          }
        : null;

    return window.openModal?.(MAIN_MODAL_PATH);
  },

  async onOpen() {
    await this.loadProjects();

    try {
      await this.resolveInitialScope();
      await this.loadCommands();
    } catch (error) {
      console.error("Failed to initialize commands manager:", error);
      this.scope = null;
      this.commands = [];
      this.builtinCommands = [];
      notifyError(error?.message || "Failed to open the commands manager.");
    }

    if (this.pendingCreate) {
      const pendingCreate = { ...this.pendingCreate };
      this.pendingCreate = null;
      await this.openCreateCommand({ name: pendingCreate.name });
    }
  },

  cleanup() {
    this.loading = false;
    this.saving = false;
    this.projects = [];
    this.projectName = "";
    this.scope = null;
    this.contextScope = { project_name: "" };
    this.commands = [];
    this.builtinCommands = [];
    this.pendingScope = null;
    this.pendingCreate = null;
    this.resetEditor();
  },

  async loadProjects() {
    try {
      const response = await callJsonApi("projects", { action: "list_options" });
      this.projects = Array.isArray(response?.data) ? response.data : [];
    } catch {
      this.projects = [];
    }
  },

  normalizeProject(projectName) {
    if (!projectName) return "";
    return (this.projects || []).some((project) => project?.key === projectName)
      ? projectName
      : "";
  },

  async resolveInitialScope() {
    const contextId =
      chatsStore?.getSelectedChatId?.() || globalThis.getContext?.() || "";
    const scopeInfo = await callJsonApi(COMMANDS_API_PATH, {
      action: "scope_info",
      context_id: contextId,
    });

    this.contextScope = scopeInfo?.context_scope || {
      project_name: "",
    };

    const preferredScope = this.pendingScope || scopeInfo?.scope || {};
    this.projectName = this.normalizeProject(preferredScope.project_name || "");
    this.pendingScope = null;
  },

  async loadCommands() {
    this.loading = true;

    try {
      const response = await callJsonApi(COMMANDS_API_PATH, {
        action: "list_scope",
        project_name: this.projectName || "",
      });

      this.commands = Array.isArray(response?.commands) ? response.commands : [];
      this.builtinCommands = Array.isArray(response?.builtin_commands)
        ? response.builtin_commands
        : [];
      this.scope = response?.scope || null;
    } catch (error) {
      console.error("Failed to load commands:", error);
      this.commands = [];
      this.builtinCommands = [];
      this.scope = null;
      notifyError(error?.message || "Failed to load commands.");
    } finally {
      this.loading = false;
    }
  },

  async refresh() {
    await this.loadCommands();
  },

  async onScopeChanged() {
    this.projectName = this.normalizeProject(this.projectName);
    await this.loadCommands();
  },

  scopedOverride(command) {
    return (this.commands || []).find((item) => item.name === command?.name);
  },

  async editBuiltinCommand(command) {
    const existing = this.scopedOverride(command);
    if (existing) {
      await this.openEditCommand(existing);
      return;
    }

    try {
      const response = await callJsonApi(COMMANDS_API_PATH, {
        action: "duplicate",
        path: command.path,
        project_name: this.projectName || "",
      });
      await this.loadCommands();
      emitCommandsUpdated();
      notifySuccess(`Created ${this.selectedScopeLabel} override for /${command.name}`);
      if (response?.command) await this.openEditCommand(response.command);
    } catch (error) {
      console.error("Failed to create command override:", error);
      notifyError(error?.message || "Failed to create command override.");
    }
  },

  async browseScopeFolder() {
    try {
      const response = await callJsonApi(COMMANDS_API_PATH, {
        action: "scope_info",
        project_name: this.projectName || "",
        ensure_directory: true,
      });
      if (response?.scope?.directory_path) {
        await fileBrowserStore.open(response.scope.directory_path);
      }
    } catch (error) {
      console.error("Failed to open scope folder:", error);
      notifyError(error?.message || "Failed to open scope folder.");
    }
  },

  async openCreateCommand(options = {}) {
    if (Object.prototype.hasOwnProperty.call(options, "projectName")) {
      this.projectName = this.normalizeProject(options.projectName || "");
      await this.loadCommands();
    }

    const suggestedName = sanitizeCommandName(options.name || "");
    this.editor = {
      ...createEmptyEditor(),
      mode: "create",
      name: suggestedName,
      commandType: "text",
      body: buildDefaultBody("text"),
    };
    this.editorSnapshot = this._serializeEditor();
    await this.openEditorModal();
  },

  async openEditCommand(command) {
    if (!command?.path) return;

    try {
      const response = await callJsonApi(COMMANDS_API_PATH, {
        action: "get",
        path: command.path,
        project_name: this.projectName || "",
      });
      const loaded = response?.command || command;
      this.editor = {
        mode: "edit",
        existingPath: loaded.path || "",
        path: loaded.path || "",
        name: loaded.name || "",
        description: loaded.description || "",
        argumentHint: loaded.argument_hint || "",
        commandType: loaded.command_type || "text",
        includeHistory: Boolean(loaded.include_history),
        body: loaded.body || "",
        extraFrontmatter: loaded.frontmatter_extra || {},
      };
      this.editorSnapshot = this._serializeEditor();
      await this.openEditorModal();
    } catch (error) {
      console.error("Failed to load command:", error);
      notifyError(error?.message || "Failed to load command.");
    }
  },

  async duplicateCommand(command) {
    if (!command?.path) return;

    try {
      const response = await callJsonApi(COMMANDS_API_PATH, {
        action: "duplicate",
        path: command.path,
        project_name: this.projectName || "",
      });
      await this.loadCommands();
      emitCommandsUpdated();
      notifySuccess(`Duplicated /${response?.command?.name || command.name}`);
      if (response?.command) {
        await this.openEditCommand(response.command);
      }
    } catch (error) {
      console.error("Failed to duplicate command:", error);
      notifyError(error?.message || "Failed to duplicate command.");
    }
  },

  async deleteCommand(command) {
    if (!command?.path) return;

    try {
      await callJsonApi(COMMANDS_API_PATH, {
        action: "delete",
        path: command.path,
        project_name: this.projectName || "",
      });
      await this.loadCommands();
      emitCommandsUpdated();
      notifySuccess(`Deleted /${command.name}`);
    } catch (error) {
      console.error("Failed to delete command:", error);
      notifyError(error?.message || "Failed to delete command.");
    }
  },

  async openEditorModal() {
    await window.openModal?.(EDITOR_MODAL_PATH, () => this.confirmCloseEditor());
    this.resetEditor();
  },

  confirmCloseEditor() {
    if (!this.editorDirty) return true;
    return window.confirm("Discard unsaved slash command changes?");
  },

  async closeEditor() {
    await window.closeModal?.(EDITOR_MODAL_PATH);
  },

  setEditorType(nextType) {
    const normalizedType = nextType === "script" ? "script" : "text";
    if (this.editor.commandType === normalizedType) return;
    this.editor.commandType = normalizedType;
    this.editor.includeHistory =
      normalizedType === "script" ? this.editor.includeHistory : false;
    this.editor.body = buildDefaultBody(normalizedType);
  },

  async saveEditor() {
    this.saving = true;

    try {
      const response = await callJsonApi(COMMANDS_API_PATH, {
        action: "save",
        project_name: this.projectName || "",
        existing_path: this.editor.existingPath || "",
        name: this.editor.name || "",
        description: this.editor.description || "",
        argument_hint: this.editor.argumentHint || "",
        command_type: this.editor.commandType || "text",
        include_history:
          this.editor.commandType === "script" ? Boolean(this.editor.includeHistory) : false,
        body: this.editor.body || "",
        extra_frontmatter: this.editor.extraFrontmatter || {},
      });

      this.editor.path = response?.command?.path || "";
      this.editor.existingPath = response?.command?.path || "";
      this.editorSnapshot = this._serializeEditor();
      await this.loadCommands();
      emitCommandsUpdated();
      notifySuccess(
        `${this.editor.mode === "edit" ? "Updated" : "Saved"} /${response?.command?.name || this.editor.name}`,
      );
      await window.closeModal?.(EDITOR_MODAL_PATH);
    } catch (error) {
      console.error("Failed to save command:", error);
      notifyError(error?.message || "Failed to save command.");
    } finally {
      this.saving = false;
    }
  },

  resetEditor() {
    this.editor = createEmptyEditor();
    this.editorSnapshot = this._serializeEditor();
  },

  _serializeEditor() {
    return safeStringify({
      existingPath: this.editor.existingPath || "",
      name: this.editor.name || "",
      description: this.editor.description || "",
      argumentHint: this.editor.argumentHint || "",
      commandType: this.editor.commandType || "text",
      includeHistory: Boolean(this.editor.includeHistory),
      body: this.editor.body || "",
      extraFrontmatter: this.editor.extraFrontmatter || {},
    });
  },
};

export const store = createStore("commandsManager", model);
