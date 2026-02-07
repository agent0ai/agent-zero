import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";

const model = {
  // --- State ---------------------------------------------------------------
  editor: null,
  editTarget: null,
  editFileName: "",
  editOriginalName: "",
  editContent: "",
  editOriginalContent: "",
  editMimeType: "text/plain",
  editIsNew: false,
  isEditLoading: false,
  isSaving: false,
  editError: null,
  editSaveError: null,
  editClosePromise: null,

  // Context
  currentPath: "", // Required for new file creation
  existingNames: [],
  onSaveSuccess: null, // Callback to refresh parent list

  // --- Public API ----------------------------------------------------------
  
  /**
   * Open the editor for an existing file
   * @param {object} file - The file object { name, path, ... }
   * @param {function} onSaveSuccess - Callback when save completes
   */
  async openFile(file, onSaveSuccess) {
    if (this.isEditLoading) return;
    this.resetEditState();
    
    this.editTarget = file;
    this.editFileName = file?.name || "";
    this.editOriginalName = this.editFileName;
    this.editIsNew = false;
    this.isEditLoading = true;
    this.editError = null;
    this.editSaveError = null;
    this.onSaveSuccess = onSaveSuccess;

    this.editClosePromise = window.openModal(
      "modals/file-editor/file-edit-modal.html",
      () => this.beforeCloseFileEditor()
    );

    if (this.editClosePromise && typeof this.editClosePromise.then === "function") {
      this.editClosePromise.then(() => this.resetEditState());
    }

    try {
      const resp = await fetchApi(
        `/edit_work_dir_file?path=${encodeURIComponent(file.path)}`
      );
      const data = await resp.json().catch(() => ({}));

      if (!resp.ok || data.error) {
        throw new Error(data.error || "Failed to load file");
      }

      const payload = data.data || {};

      this.editContent = payload.content || "";
      this.editFileName = payload.name || this.editFileName;
      this.editOriginalName = this.editFileName;
      this.editOriginalContent = this.editContent;
      this.editMimeType = payload.mime_type || "text/plain";
      this.isEditLoading = false;
      this.scheduleEditorInit();
    } catch (error) {
      let message = error?.message || "Failed to load file";
      message = this._extractErrorMessage(message);
      this.editError = message;
      this.isEditLoading = false;
      window.toastFrontendError(message, "File Edit Error");
    }
  },

  /**
   * Open the editor for a new file
   * @param {string} currentPath - The directory where the file will be created
   * @param {string[]} existingNames - Names that already exist in the directory (for UX duplicate checks)
   * @param {function} onSaveSuccess - Callback when save completes
   */
  async openNewFile(currentPath, existingNames, onSaveSuccess) {
    this.resetEditState();
    
    this.currentPath = currentPath;
    this.existingNames = Array.isArray(existingNames) ? existingNames : [];
    this.editIsNew = true;
    this.editFileName = "";
    this.editOriginalName = "";
    this.editContent = "";
    this.editOriginalContent = "";
    this.editMimeType = "text/plain";
    this.isEditLoading = false;
    this.editError = null;
    this.editSaveError = null;
    this.onSaveSuccess = onSaveSuccess;

    this.editClosePromise = window.openModal(
      "modals/file-editor/file-edit-modal.html",
      () => this.beforeCloseFileEditor()
    );

    if (this.editClosePromise && typeof this.editClosePromise.then === "function") {
      this.editClosePromise.then(() => this.resetEditState());
    }

    this.scheduleEditorInit();
  },

  // --- Actions -------------------------------------------------------------

  async saveFileEdits() {
    if (this.isSaving || this.isEditLoading || this.editError) return;
    this.editSaveError = null;

    const fileName = this.editFileName.trim();
    if (!fileName) {
      this.editSaveError = "File name is required.";
      return;
    }
    if (fileName === "." || fileName === "..") {
      this.editSaveError = "File name cannot be '.' or '..'.";
      return;
    }
    if (fileName.includes("/") || fileName.includes("\\")) {
      this.editSaveError = "File name cannot include path separators.";
      return;
    }
    if (this.editIsNew && (this.existingNames || []).includes(fileName)) {
      this.editSaveError = `An item named "${fileName}" already exists.`;
      return;
    }

    const content = this.editor ? this.editor.getValue() : this.editContent;
    const targetPath = this.editIsNew
      ? this.buildChildPath(fileName)
      : this.editTarget?.path || ""; // Note: was normalizePath(this.editTarget?.path) but path should be absolute from API

    if (!targetPath) {
      window.toastFrontendError("File path is missing.", "Save File");
      return;
    }

    this.isSaving = true;

    try {
      const resp = await fetchApi("/edit_work_dir_file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: targetPath, content }),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok || data.error) {
        throw new Error(data.error || "Failed to save file");
      }

      this.editOriginalContent = content;
      this.editOriginalName = fileName;
      this.editIsNew = false;
      if (this.editTarget) {
        this.editTarget.name = fileName;
        this.editTarget.path = targetPath;
      }

      // Trigger success callback
      if (typeof this.onSaveSuccess === 'function') {
        await this.onSaveSuccess();
      }

      // Reset isSaving before closing so beforeCloseFileEditor() allows it
      this.isSaving = false;
      this.closeFileEditor();
    } catch (error) {
      const message = error?.message || "Failed to save file";
      this.editSaveError = message;
      window.toastFrontendError(message, "Save File Error");
      this.isSaving = false;
    }
  },

  closeFileEditor() {
    window.closeModal("modals/file-editor/file-edit-modal.html");
  },

  beforeCloseFileEditor() {
    if (this.isSaving) return false;
    if (!this.editor) return true;
    if (!this.hasEditChanges()) return true;
    return confirm("You have unsaved changes. Close without saving?");
  },

  // --- Helpers -------------------------------------------------------------

  _extractErrorMessage(msg) {
    if (typeof msg !== 'string') return msg;
    // Extract clean error from traceback strings
    const lines = msg.split('\n');
    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i].trim();
      if (line.includes(': ') && /Exception|Error/.test(line)) {
        return line.split(': ').slice(1).join(': ').trim();
      }
    }
    return msg;
  },

  resetEditState() {
    if (this.editor?.destroy) {
      this.editor.destroy();
    }
    this.editor = null;
    this.editTarget = null;
    this.editFileName = "";
    this.editOriginalName = "";
    this.editContent = "";
    this.editOriginalContent = "";
    this.editMimeType = "text/plain";
    this.editIsNew = false;
    this.isEditLoading = false;
    this.isSaving = false;
    this.editError = null;
    this.editSaveError = null;
    this.editClosePromise = null;
    this.existingNames = [];
    this.onSaveSuccess = null;
  },

  normalizePath(path) {
    if (!path) return "";
    return path.startsWith("/") ? path : `/${path}`;
  },

  buildChildPath(name) {
    const base = this.normalizePath(this.currentPath || "");
    const trimmedBase = base.replace(/\/$/, "");
    if (!trimmedBase) return `/${name}`;
    return `${trimmedBase}/${name}`;
  },

  hasEditChanges() {
    const currentValue = this.editor ? this.editor.getValue() : this.editContent;
    const nameChanged = (this.editFileName || "") !== (this.editOriginalName || "");
    if (this.editIsNew) {
      return Boolean((this.editFileName || "").trim() || currentValue);
    }
    return currentValue !== this.editOriginalContent || nameChanged;
  },

  editPathLabel() {
    if (this.editIsNew) {
      const name = this.editFileName?.trim();
      return name ? this.buildChildPath(name) : this.normalizePath(this.currentPath || "");
    }
    return this.editTarget?.path ? this.normalizePath(this.editTarget.path) : "";
  },

  // --- Editor (ACE) integration --------------------------------------------

  scheduleEditorInit() {
    window.requestAnimationFrame(() => {
      if (this.isEditLoading || this.editError) return;
      window.requestAnimationFrame(() => this.initEditor());
    });
  },

  initEditor() {
    const container = document.getElementById("file-editor-container");
    if (!container) {
      // It's possible the modal hasn't fully rendered yet
      console.warn("File editor container not found, deferring editor init");
      return;
    }

    if (this.editor?.destroy) {
      this.editor.destroy();
    }

    if (!window.ace?.edit) {
      console.error("ACE editor not available");
      this.editError = "Editor library not loaded";
      return;
    }

    const editorInstance = window.ace.edit("file-editor-container");
    if (!editorInstance) {
      console.error("Failed to create ACE editor instance");
      return;
    }

    this.editor = editorInstance;

    const darkMode = window.localStorage?.getItem("darkMode");
    const theme = darkMode !== "false" ? "ace/theme/github_dark" : "ace/theme/tomorrow";
    this.editor.setTheme(theme);
    this.applyEditorMode();
    this.editor.setValue(this.editContent || "", -1);
    this.editor.clearSelection();
  },

  updateEditorMode() {
    this.applyEditorMode();
  },

  applyEditorMode() {
    if (!this.editor?.session) return;
    const mode = this.resolveAceMode(this.editMimeType, this.editFileName);
    this.editor.session.setMode(mode);
  },

  resolveAceMode(mimeType, fileName) {
    const mime = (mimeType || "").toLowerCase();
    const ext = (fileName || "").split(".").pop()?.toLowerCase();
    const mimeMap = {
      "application/json": "json",
      "application/xml": "xml",
      "application/javascript": "javascript",
      "application/typescript": "typescript",
      "application/x-yaml": "yaml",
      "text/plain": "text",
      "text/markdown": "markdown",
      "text/html": "html",
      "text/css": "css",
      "text/javascript": "javascript",
      "text/typescript": "typescript",
      "text/x-python": "python",
      "text/x-shellscript": "sh",
      "text/x-yaml": "yaml",
      "text/xml": "xml",
      "text/x-toml": "toml",
    };
    const extMap = {
      js: "javascript",
      jsx: "javascript",
      ts: "typescript",
      tsx: "typescript",
      json: "json",
      md: "markdown",
      markdown: "markdown",
      html: "html",
      htm: "html",
      css: "css",
      py: "python",
      sh: "sh",
      bash: "sh",
      zsh: "sh",
      yaml: "yaml",
      yml: "yaml",
      toml: "toml",
      xml: "xml",
      txt: "text",
      csv: "text",
      ini: "ini",
    };
    const mimeMode = mimeMap[mime];
    const extMode = extMap[ext];
    const mode = (mime && mime !== "text/plain" ? mimeMode : null) || extMode || mimeMode || "text";
    return `ace/mode/${mode}`;
  },
};

export const store = createStore("fileEditor", model);
