import { toastFrontendNotice } from "/components/notifications/notification-store.js";
import { createStore, getStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";
import { formatDateTime } from "/js/time-utils.js";
import { mediaKind, mediaPreview } from "/components/modals/file-browser/file-preview.js";
import { mountFileGestures } from "/components/modals/file-browser/file-gestures.js";
import { createFileTree } from "/components/modals/file-browser/file-tree.js";
import {
  open as openSurface,
  select as selectSurface,
  setupFloatingSurfaceModalChrome,
} from "/js/surfaces.js";

const SAVE_AS_MODAL_PATH = "modals/file-browser/save-as-modal.html";
const FILE_BROWSER_LAST_DIRECTORY_STORAGE_KEY = "fileBrowser.lastDirectory";
const DEFAULT_REMEMBER_LAST_DIRECTORY = true;
const PICKER_MODE_NONE = "";
const PICKER_MODE_TEXT_OPEN = "text-open";
const PICKER_MODE_SAVE_AS = "save-as";
const CONNECTION_PLUGINS = [
  ["ssh", "File Browser SSH access"],
  ["webdav", "File Browser WebDAV access"],
  ["smb", "File Browser SMB 3 for NAS"],
  ["s3", "File Browser S3 access"],
  ["ftps", "File Browser FTPS access"],
].map(([id, title]) => ({
  key: `file_browser_${id}`,
  title,
  thumbnail: `https://raw.githubusercontent.com/agent0ai/a0-plugins/main/plugins/file_browser_${id}/thumbnail.webp`,
}));
const BROWSER_EXTENSIONS = new Set([
  "html",
  "htm",
  "xhtml",
  "svg",
  "xml",
  "pdf",
  "png",
  "jpg",
  "jpeg",
  "gif",
  "webp",
  "bmp",
  "ico",
]);
const ARCHIVE_SUFFIXES = [".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst", ".tar", ".tgz", ".tbz", ".tbz2", ".txz", ".zip", ".rar", ".7z", ".gz", ".bz2", ".xz", ".zst"];
const filenameOrder = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

const SURFACE_ACTIONS = {
  editor: {
    label: "Edit",
    icon: "edit",
    title: "Edit",
  },
  browser: {
    label: "Open in Browser",
    icon: "language",
    title: "Open web-viewable file in Browser",
  },
};

function delay(ms) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms));
}

const views = new Map();
const configuration = createStore("fileBrowserConfiguration", {
  modalOwner: null, renameOwner: null, clipboard: null,
});
const sharedFields = [
  "limits", "textLimitMib", "transferLimitMib", "extractLimitMib", "archiveEntries",
  "savingTextLimit", "preferences", "rememberLastDirectory", "settingsLoadPromise",
  "settingsUpdatedHandler", "connections", "connectionProviders", "connectionDraft",
  "connectionsBusy", "installedConnectionPlugins", "openingConnectionPlugin",
];

export function createFileBrowserView(name, { embedded = false, rememberKey = FILE_BROWSER_LAST_DIRECTORY_STORAGE_KEY } = {}) {
  if (views.has(name)) return views.get(name);
  let view;
  const model = {
  embedded,
  viewName: name,
  rememberKey,
  limits: null,
  textLimitMib: null,
  transferLimitMib: null,
  extractLimitMib: null,
  archiveEntries: null,
  savingTextLimit: false,
  async ensureLimits(force = false) {
    if (this.limits && !force) return this.limits;
    const response = await fetchApi("/get_work_dir_files?limits=1");
    const data = await response.json();
    if (!response.ok || !data.limits?.max_text_bytes || !data.limits?.max_file_bytes) {
      throw new Error("File Browser limits are unavailable.");
    }
    this.limits = data.limits;
    return this.limits;
  },
  async saveSizeLimit(kind = "text") {
    if (this.savingTextLimit) return;
    this.savingTextLimit = true;
    try {
      const limit = {text: this.textLimitMib, transfer: this.transferLimitMib, extract: this.extractLimitMib, entries: this.archiveEntries}[kind];
      if (!Number.isInteger(limit) || limit < 1) throw new Error("Enter a positive whole number of MiB.");
      const result = await callJsonApi("/file_browser_settings", { [kind === "entries" ? "max_archive_entries" : `max_${kind}_size_mb`]: limit });
      if (!result.ok) throw new Error(result.error || "Could not save the size limit.");
      this.limits = result.limits;
      const settings = globalThis.Alpine?.store("settings")?.settings;
      if (settings) {
        const key = kind === "entries" ? "file_browser_max_archive_entries" : `file_browser_max_${kind}_size_mb`;
        settings[key] = limit;
      }
    } catch (error) {
      this.textLimitMib = this.limits.max_text_bytes / (1024 * 1024);
      this.transferLimitMib = this.limits.max_file_bytes / (1024 * 1024);
      this.extractLimitMib = this.limits.max_extract_bytes / (1024 * 1024);
      this.archiveEntries = this.limits.max_archive_entries;
      globalThis.toastFrontendError?.(error.message, "File Browser Settings");
    } finally { this.savingTextLimit = false; }
  },
  fileTree: createFileTree((file) => view.openTreeEntry(file), () => view.preferences.treeRoot),

  async openTreeEntry(file) {
    await this.ensureLimits();
    if (file.is_dir) return this.navigateToFolder(file.path);
    if (this.isPickerMode()) {
      if (await this.fetchFiles(this.parentPath(file.path), { preserveOnError: true })) {
        const entry = this.browser.entries.find(entry => this.normalizePath(entry.path) === file.path);
        if (entry) this.handleFileNameClick(entry);
      }
      return;
    }
    if (this.canOpenInSurface(file)) return this.openInSurface(file);
    return this.openFileEditor(file);
  },

  // Reactive state
  isLoading: false,
  browser: {
    title: "File Browser",
    currentPath: "",
    entries: [],
    parentPath: "",
    explicitSort: false,
    sortBy: "name",
    sortDirection: "asc",
  },
  history: [], // back navigation stack
  forwardHistory: [], // forward navigation stack
  initialPath: "", // Store path for open() call
  _finishPicker: null,
  isSurfaceHandoff: false,
  surfaceHandoffPath: "",
  error: null,
  pathInput: "",
  pathError: "",
  isPathSubmitting: false,
  pathEditing: false,
  pathSuggestions: [],
  pathSuggestionsStyle: {},
  pathSuggestionIndex: 0,
  _pathSuggestionsToken: 0,
  _pathSuggestionsTimer: null,
  pathSuggestionsOwner: null,
  _directoryRequest: 0,
  rememberLastDirectory: DEFAULT_REMEMBER_LAST_DIRECTORY,
  settingsLoadPromise: null,
  settingsUpdatedHandler: null,
  _floatingCleanup: null,
  _mountedElement: null,
  _canvasElement: null,
  _modalElement: null,
  _mountedDefaultLoadTimer: null,
  renameTarget: null,
  renameName: "",
  renameMode: "rename",
  renameInline: false,
  renameDirectory: "",
  renameEntries: [],
  isRenaming: false,
  renameError: null,
  renameAfterConfirm: null,
  renamePerformAction: null,
  renameValidateName: null,
  openDropdownPath: null, // Track which dropdown is currently open
  dropdownOwner: null,
  dropdownStyle: {},
  searchQuery: "",
  filterOpen: false,
  showHidden: false,
  focusedPath: "",
  selectionAnchor: "",
  lastTap: null,
  isBulkBusy: false,
  operationLabel: "",
  operationError: "",
  destinationSelection: null,
  pickerMode: PICKER_MODE_NONE,
  pickerConfirmLabel: "",
  pickerFilename: "",
  pickerDefaultExtension: "md",
  pickerFilenameError: "",
  pickerOnConfirm: null,

  connections: [],
  connectionProviders: [],
  connectionDraft: null,
  connectionsBusy: false,
  installedConnectionPlugins: [],
  openingConnectionPlugin: "",
  remotePermissions: null,

  get connectionPluginOffers() {
    return CONNECTION_PLUGINS.map(plugin => ({
      ...plugin,
      installed: this.installedConnectionPlugins.includes(plugin.key),
      provider: this.connectionProviders.find(provider => provider.plugin === plugin.key)?.id,
    }));
  },
  async openConnectionPlugin(plugin) {
    if (this.openingConnectionPlugin) return;
    try {
      if (!plugin.installed) {
        this.openingConnectionPlugin = plugin.key;
        const { store: installer } = await import("/plugins/_plugin_installer/webui/pluginInstallStore.js");
        await installer.ensureIndexLoaded();
        if (!installer.getPluginHubPluginByKey(plugin.key)) await installer.fetchIndex({ force: true });
        await installer.openPluginHubDetailByKey(plugin.key);
        return;
      }
      const provider = this.connectionProviders.find(provider => provider.plugin === plugin.key);
      if (provider) this.editConnection(null, provider.id);
    } catch (error) { globalThis.toastFrontendError?.(error.message, "File Browser Plugins"); }
    finally { this.openingConnectionPlugin = ""; }
  },
  get draftProvider() { return this.connectionProviders.find(p => p.id === this.connectionDraft?.provider); },
  isRemote(path = this.browser.currentPath) { return /^\/@(?:ssh|connections)(?:\/|$)/.test(String(path)); },
  remoteAllowed(permission, file = null) {
    return !this.isRemote(file?.path || this.browser.currentPath)
      || Boolean((file?.permissions || this.remotePermissions)?.[permission]);
  },
  async connectionRequest(action, payload = {}) {
    const response = await callJsonApi("/file_browser_connections", { action, ...payload });
    if (response?.error || response?.ok === false) throw new Error(response.error || "Connection operation failed.");
    return response;
  },
  async loadConnections() {
    const [response, installed] = await Promise.all([
      this.connectionRequest("list"),
      callJsonApi("plugins_list", { filter: { custom: true, builtin: false } }),
    ]);
    this.connections = response.connections || [];
    this.connectionProviders = response.providers || [];
    this.installedConnectionPlugins = (installed.plugins || []).map(plugin => plugin.name);
  },
  editConnection(connection = null, providerId = "") {
    const editable = this.connectionProviders.filter(p => !p.managed);
    const provider = editable.find(p => p.id === (connection?.provider || providerId)) || editable[0];
    if (!provider) return;
    this.connectionDraft = connection ? JSON.parse(JSON.stringify(connection)) : {
      provider: provider.id, name: "",
      ...Object.fromEntries(provider.fields.filter(f => !f.secret).map(f => [f.name, f.default ?? ""])),
      permissions: { browse: true, download: true, upload: false, edit: false, rename: false, delete: false },
    };
  },
  async saveConnection() {
    if (this.connectionsBusy || !this.connectionDraft) return;
    this.connectionsBusy = true;
    try {
      await this.connectionRequest("save-connection", { connection: this.connectionDraft });
      this.connectionDraft = null;
      await this.loadConnections();
    } catch (error) { globalThis.toastFrontendError?.(error.message, "File connections"); }
    finally { this.connectionsBusy = false; }
  },
  async testConnection(connection) {
    try {
      await this.connectionRequest("test", {provider: connection.provider, id: connection.id});
      globalThis.toastFrontendSuccess?.("Connected successfully.", "File connections");
    } catch (error) { globalThis.toastFrontendError?.(error.message, "File connections"); }
  },
  async removeConnection(connection) {
    try {
      await this.connectionRequest("remove-connection", {provider: connection.provider, id: connection.id});
      await this.loadConnections();
    } catch (error) { globalThis.toastFrontendError?.(error.message, "File connections"); }
  },
  async openConnection(connection) {
    await window.closeModal("settings/settings.html");
    const path = "/@connections/" + connection.provider + "/" + connection.id;
    return openSurface("files", { path, source: "file-browser-settings" });
  },
  async startDownload(files) {
    const result = await callJsonApi("/download_work_dir_files", {
      paths: files.map(file => file.path), currentPath: this.browser.currentPath,
    });
    if (!result.download_url) throw new Error(result.error || "Download failed.");
    const link = document.createElement("a");
    link.href = result.download_url;
    link.download = result.name;
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  preferences: { sortBy: "name", sortDirection: "asc", view: "list", treeShown: false, treeRoot: "/a0", pathBar: "buttons", independent: true },

  normalizeTreeRoot(value) {
    if (typeof value !== "string" || !value.trim().startsWith("/")) return "";
    const path = value.trim().replace(/\/+/g, "/").replace(/\/$/, "") || "/";
    return !/(?:^|\/)\.\.?(?:\/|$)|[\0\r\n]/.test(path) ? path : "";
  },

  async saveTreeRoot(value) {
    const path = this.normalizeTreeRoot(value);
    if (!path) {
      toastFrontendNotice("error", "Enter an absolute folder path without . or .. segments.", "File Browser Settings");
      return;
    }
    this.preferences.treeRoot = path;
    await this.savePreferences();
  },

  loadPreferences() {
    try {
      const value = JSON.parse(localStorage.getItem("fileBrowser.preferences") || "{}");
      this.preferences = {
        sortBy: ["name", "size", "date"].includes(value.sortBy) ? value.sortBy : "name",
        sortDirection: value.sortDirection === "desc" ? "desc" : "asc",
        view: value.view === "icons" ? "icons" : "list",
        treeShown: value.treeShown === true,
        treeRoot: this.normalizeTreeRoot(value.treeRoot) || "/a0",
        pathBar: value.pathBar === "raw" ? "raw" : "buttons",
        independent: value.independent !== false,
      };
    } catch { /* Storage may be unavailable. Keep the defaults. */ }
    this.browser.explicitSort = false;
    this.browser.sortBy = this.preferences.sortBy;
    this.browser.sortDirection = this.preferences.sortDirection;
    this.fileTree.shown = this.preferences.treeShown;
  },

  async savePreferences() {
    try {
      localStorage.setItem("fileBrowser.preferences", JSON.stringify(this.preferences));
    } catch {
      toastFrontendNotice("error", "Could not save file browser preferences.");
      return;
    }
    await Promise.all([...views.values()].map(async browser => {
      browser.applyPreferences();
      if (browser._mountedElement) await browser.fileTree.follow(browser.browser.currentPath);
    }));
  },

  async loadSettings() {
    try {
      // Reflect saved UI preferences (e.g. pathBar) before binding settings fields.
      this.loadPreferences();
      await this.ensureLimits(true);
      this.textLimitMib = this.limits.max_text_bytes / (1024 * 1024);
      this.transferLimitMib = this.limits.max_file_bytes / (1024 * 1024);
      this.extractLimitMib = this.limits.max_extract_bytes / (1024 * 1024);
      this.archiveEntries = this.limits.max_archive_entries;
      await this.loadConnections();
    } catch (error) { globalThis.toastFrontendError?.(error.message, "File Browser Settings"); }
  },

  async openSettings(providerId = "") {
    await this.loadSettings();
    this.connectionDraft = null;
    if (providerId) this.editConnection(null, providerId);
    const { store: settingsStore } = await import("/components/settings/settings-store.js");
    return await settingsStore.open("file-browser");
  },

  // --- Lifecycle -----------------------------------------------------------
  init() { this.applyPreferences(); },

  applyPreferences() {
    this.browser.explicitSort = false;
    this.browser.sortBy = this.preferences.sortBy;
    this.browser.sortDirection = this.preferences.sortDirection;
    this.fileTree.shown = this.preferences.treeShown;
  },

  get isPickerModal() { return configuration.modalOwner === name; },
  get isRenameModal() { return configuration.renameOwner === name; },

  onMount(element = null, options = {}) {
    const mode = this.embedded ? "embedded" : options?.mode === "canvas" ? "canvas" : "modal";
    if (mode === "canvas") this._canvasElement = element;
    if (mode === "modal") this._modalElement = element;
    if (mode === "canvas" && this._modalElement?.isConnected) return;
    if (element && element === this._mountedElement) return;
    this._mountedElement = element;
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    if (mode === "modal") this.setupFloatingModal(element);
    this.scheduleMountedDefaultLoad();
  },

  onUnmount(element = null) {
    if (element === this._canvasElement) this._canvasElement = null;
    if (element === this._modalElement) this._modalElement = null;
    if (element && element !== this._mountedElement) return;
    if (!this.isSurfaceHandoff) {
      this._directoryRequest++;
      this.isLoading = false;
      this.pathEditing = false;
      if (!this.isBulkBusy && !this.isPickerModal) this.resetPickerState();
      if (!this.isRenaming && !this.isRenameModal) this.resetRenameState();
    }
    this.clearPathSuggestions();
    this._mountedElement = null;
    this.closeDropdown();
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    this.cancelMountedDefaultLoad();
    if (this._canvasElement?.isConnected) this.onMount(this._canvasElement, { mode: "canvas" });
  },

  // --- Public API (called from button/link) --------------------------------
  async open(path = "", options = {}) {
    if (this.embedded) return store.open(path || this.browser.currentPath, options);
    if (this.isLoading || this.isRenaming || this.isBulkBusy) return;
    const { store: canvas } = await import("/components/canvas/right-canvas-store.js");
    const retainedPath = this.browser.currentPath;
    const returnSurface = options.pickerMode && (canvas.isOpen || canvas.isDetached) ? canvas.activeSurfaceId : "";
    if (options.pickerMode) configuration.modalOwner = name;
    let finishPicker;
    try {
      const opened = options.pickerMode
        ? await canvas.open("files", { path, options })
        : await canvas.openModalSurface("files", { path, options });
      if (!opened) {
        if (configuration.modalOwner === name) configuration.modalOwner = null;
        return;
      }
      if (!options.pickerMode) return await canvas.whenClosed();
      const picked = new Promise(resolve => { finishPicker = this._finishPicker = resolve; });
      await Promise.race([canvas.whenClosed(), picked]);
      // A new explicit navigation replaces the picker without restoring its old location.
      if (this._finishPicker !== finishPicker) return;
      this._finishPicker = null;
      this.resetPickerState();
      if (retainedPath) await this.openSurface(retainedPath);
      if (configuration.modalOwner === name) configuration.modalOwner = null;
      if (returnSurface && (canvas.isOpen || canvas.isDetached) && canvas.activeSurfaceId === "files") {
        await canvas.open(returnSurface);
      }
    } catch (error) {
      if (this._finishPicker === finishPicker) this._finishPicker = null;
      if (configuration.modalOwner === name) configuration.modalOwner = null;
      console.error("File browser error:", error);
      this.error = error?.message || "Failed to load files";
      this.isLoading = false;
    }
  },

  async openSurface(path = "", options = {}) {
    if (this.isLoading || this.isRenaming || this.isBulkBusy) return false;
    if (this.isSurfaceHandoff) return true;
    if (this._finishPicker) {
      this._finishPicker();
      this._finishPicker = null;
      if (configuration.modalOwner === name) configuration.modalOwner = null;
    }
    if (options.pickerMode) configuration.modalOwner = name;
    this.resetOpenState(options);

    try {
      const retainedPath = this.normalizeOpeningPath(
        path
          || this.surfaceHandoffPath
          || this.browser.currentPath
          || this.initialPath
      );
      return await this.loadOpeningPath(retainedPath);
    } catch (error) {
      console.error("File browser surface error:", error);
      this.error = error?.message || "Failed to load files";
      this.isLoading = false;
      return false;
    }
  },

  async handleClose() {
    this.disposeScopedTooltips();
    const { store: canvas } = await import("/components/canvas/right-canvas-store.js");
    return await canvas.close();
  },

  async openTextPicker(path = "", onConfirm = null) {
    return await this.open(path, {
      pickerMode: PICKER_MODE_TEXT_OPEN,
      confirmLabel: "Open Selected",
      onConfirm,
    });
  },

  async openSaveAsPicker(path = "", options = {}) {
    const picker = createFileBrowserView("fileBrowserSaveAs");
    if (picker._finishPicker) {
      void window.ensureModalOpen?.(SAVE_AS_MODAL_PATH);
      return;
    }
    picker.resetOpenState({
      pickerMode: PICKER_MODE_SAVE_AS,
      confirmLabel: "Save Here",
      filename: options.filename || "Untitled.md",
      defaultExtension: options.defaultExtension || "",
      onConfirm: options.onConfirm,
    });
    picker._finishPicker = () => window.closeModal(SAVE_AS_MODAL_PATH);
    const closed = window.openModal(SAVE_AS_MODAL_PATH, () => !picker.isBulkBusy && !picker.isRenaming);
    try {
      await picker.loadOpeningPath(path);
      await closed;
    } finally {
      picker._finishPicker = null;
      picker.destroy();
    }
  },

  destroy() {
    this._directoryRequest++;
    this.resetPathInput();
    this.pathEditing = false;
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    this.cancelMountedDefaultLoad();
    // Reset state when modal closes
    this.isLoading = false;
    this.history = [];
    this.forwardHistory = [];
    this.initialPath = "";
    this.isSurfaceHandoff = false;
    this.surfaceHandoffPath = "";
    this.browser.currentPath = "";
    this.browser.parentPath = "";
    this.browser.entries = [];
    this.closeDropdown();
    this.searchQuery = "";
    this.isBulkBusy = false;
    this.pathInput = "";
    this.pathError = "";
    this.isPathSubmitting = false;
    this.resetPickerState();
    this.resetRenameState();
  },

  setupFloatingModal(element = null) {
    this._floatingCleanup?.();
    this._floatingCleanup = setupFloatingSurfaceModalChrome({
      root: element,
      modalClass: "file-browser-modal",
      focusButtonClass: "file-browser-modal-focus-button",
      minWidth: 420,
      minHeight: 360,
    });
  },

  cancelMountedDefaultLoad() {
    if (!this._mountedDefaultLoadTimer) return;
    globalThis.clearTimeout(this._mountedDefaultLoadTimer);
    this._mountedDefaultLoadTimer = null;
  },

  scheduleMountedDefaultLoad() {
    this.cancelMountedDefaultLoad();
    this._mountedDefaultLoadTimer = globalThis.setTimeout(async () => {
      this._mountedDefaultLoadTimer = null;
      if (this.isLoading) return;
      const targetPath = this.browser.currentPath || "";
      if (targetPath && this.browser.entries.length) {
        this.syncPathInput();
        return;
      }
      try {
        await this.loadOpeningPath(targetPath);
      } catch (error) {
        console.error("File browser default path load failed:", error);
      }
    }, 120);
  },

  // --- Helpers -------------------------------------------------------------
  resetOpenState(options = {}) {
    this.loadPreferences();
    this.closeDropdown();
    this.cancelMountedDefaultLoad();
    this.resetRenameState();
    this.resetPathInput();
    this.pathEditing = false;
    this.isLoading = true;
    this.error = null;
    this.history = [];
    this.forwardHistory = [];
    this.searchQuery = "";
    this.isBulkBusy = false;
    this.pathError = "";
    this.isPathSubmitting = false;
    this.configurePicker(options);
  },

  configurePicker(options = {}) {
    this.destinationSelection = null;
    const mode = String(options?.pickerMode || PICKER_MODE_NONE).trim();
    this.pickerMode = [PICKER_MODE_TEXT_OPEN, PICKER_MODE_SAVE_AS].includes(mode)
      ? mode
      : PICKER_MODE_NONE;
    this.pickerConfirmLabel = String(options?.confirmLabel || "").trim()
      || (this.pickerMode === PICKER_MODE_SAVE_AS ? "Save Here" : "Open Selected");
    this.pickerFilename = String(options?.filename || "").trim();
    this.pickerDefaultExtension = this.normalizedEditorTextExtension(
      options?.defaultExtension ?? this.fileExtension({ name: this.pickerFilename }),
    );
    this.pickerFilenameError = "";
    this.pickerOnConfirm = typeof options?.onConfirm === "function" ? options.onConfirm : null;
    if (this.pickerMode) this.clearSelection();
  },

  resetPickerState() {
    this.destinationSelection = null;
    this.pickerMode = PICKER_MODE_NONE;
    this.pickerConfirmLabel = "";
    this.pickerFilename = "";
    this.pickerDefaultExtension = "md";
    this.pickerFilenameError = "";
    this.pickerOnConfirm = null;
  },

  async loadOpeningPath(path = "") {
    const request = this._directoryRequest;
    await this.loadDirectoryPreference();
    if (request !== this._directoryRequest) return false;
    const explicitPath = this.normalizeOpeningPath(path || this.initialPath);
    const rememberedPath = !explicitPath ? this.getRememberedDirectory() : "";
    const targetPath = explicitPath || rememberedPath || "$WORK_DIR";
    const loaded = await this.fetchFiles(targetPath, {
      preserveOnError: Boolean(rememberedPath && targetPath === rememberedPath),
      suppressErrorToast: Boolean(rememberedPath && targetPath === rememberedPath),
    });
    if (!loaded && rememberedPath && targetPath === rememberedPath) {
      this.clearRememberedDirectory();
      return await this.fetchFiles("$WORK_DIR");
    }
    return loaded;
  },

  beginSurfaceHandoff() {
    this.isSurfaceHandoff = true;
    this.surfaceHandoffPath = this.browser.currentPath || this.pathInput || "";
  },

  finishSurfaceHandoff() {
    this.isSurfaceHandoff = false;
    this.surfaceHandoffPath = "";
  },

  cancelSurfaceHandoff() {
    this.isSurfaceHandoff = false;
    this.surfaceHandoffPath = "";
  },

  isArchive(filename) {
    return ARCHIVE_SUFFIXES.some((suffix) => String(filename || "").toLowerCase().endsWith(suffix));
  },

  formatFileSize(size) {
    if (size === 0) return "0B";
    const units = ["B", "K", "M", "G", "T", "P"];
    const index = Math.min(units.length - 1, Math.floor(Math.log(size) / Math.log(1024)));
    const value = size / 1024 ** index;
    return Number(value.toFixed(value < 10 ? 1 : 0)) + units[index];
  },

  formatDate(dateString) {
    return formatDateTime(dateString, "short");
  },

  decorateEntries(entries = [], selectedPaths = new Set()) {
    return entries.map((entry) => ({
      ...entry,
      selected: selectedPaths.has(entry.path),
    }));
  },

  get filteredEntries() {
    const query = this.searchQuery.trim().toLocaleLowerCase();
    return this.browser.entries.filter(file => this.pickerAllowsEntry(file)
      && (this.showHidden || !file.name.startsWith("."))
      && file.name.toLocaleLowerCase().includes(query));
  },

  get visibleEntries() {
    return this.sortFiles(this.filteredEntries);
  },

  clearSearch() {
    this.searchQuery = "";
  },

  setFilter(query, showHidden = this.showHidden) {
    this.searchQuery = query;
    this.showHidden = showHidden;
    const visible = new Set(this.filteredEntries.map(file => file.path));
    for (const file of this.browser.entries) {
      if (file.selected && !visible.has(file.path)) file.selected = false;
    }
    if (!visible.has(this.selectionAnchor)) this.selectionAnchor = "";
    if (!visible.has(this.focusedPath)) this.focusedPath = "";
    this.lastTap = null;
  },

  get selectedFiles() {
    return this.browser.entries.filter((file) => file.selected && this.isSelectableEntry(file));
  },

  get selectableEntries() {
    return this.filteredEntries.filter((file) => this.isSelectableEntry(file));
  },

  get selectedCount() {
    return this.selectedFiles.length;
  },

  get selectedCountLabel() {
    return `${this.selectedCount} ${this.selectedCount === 1 ? "item" : "items"} selected`;
  },

  get allVisibleSelected() {
    return (
      this.selectableEntries.length > 0 &&
      this.selectableEntries.every((file) => file.selected)
    );
  },

  get someVisibleSelected() {
    return this.selectableEntries.some((file) => file.selected);
  },

  toggleSelectAllVisible() {
    const shouldSelect = !this.allVisibleSelected;
    this.selectableEntries.forEach((file) => {
      file.selected = shouldSelect;
    });
  },

  clearSelection() {
    this.selectionAnchor = "";
    this.browser.entries.forEach((file) => {
      file.selected = false;
    });
  },

  selectEntry(file, { shiftKey, ctrlKey, metaKey } = {}) {
    if (!this.isSelectableEntry(file)) return;
    const entries = this.visibleEntries;
    const start = entries.findIndex(entry => entry.path === this.selectionAnchor);
    if (shiftKey && start >= 0) {
      const end = entries.findIndex(entry => entry.path === file.path);
      const range = entries.slice(Math.min(start, end), Math.max(start, end) + 1);
      if (!ctrlKey && !metaKey) this.browser.entries.forEach(entry => { entry.selected = false; });
      range.forEach(entry => { entry.selected = this.isSelectableEntry(entry); });
    } else {
      if (ctrlKey || metaKey) file.selected = !file.selected;
      else { this.clearSelection(); file.selected = true; }
      this.selectionAnchor = file.path;
    }
  },

  clickEntry(file, event) {
    event.currentTarget.focus({ preventScroll: true });
    this.focusedPath = file.path;
    this.selectEntry(file, event);
    if (this.isSaveAsPicker() && !file.is_dir) {
      this.pickerFilename = file.name;
      this.validatePickerFilename(true);
    }
    const touch = event.pointerType === "touch";
    const open = touch ? this.lastTap?.path === file.path && event.timeStamp - this.lastTap.time < 400 : event.detail === 2;
    this.lastTap = touch && !open ? { path: file.path, time: event.timeStamp } : null;
    if (open && !event.shiftKey && !event.ctrlKey && !event.metaKey) return this.activateEntry(file);
  },

  activateEntry(file) {
    if (file.is_dir) return this.navigateToFolder(file.path);
    if (this.isTextOpenPicker() && this.isSelectableEntry(file)) {
      file.selected = true;
      return this.confirmPicker();
    }
    if (!this.isPickerMode()) {
      if (this.canPreview(file)) return this.previewFile(file);
      return this.handleFileNameClick(file);
    }
  },

  listKey(event) {
    if (event.isComposing || event.altKey || event.target.closest("input, button, textarea, [contenteditable=true]")) return;
    const list = event.currentTarget;
    const entries = this.visibleEntries;
    const index = entries.findIndex(file => file.path === this.focusedPath);
    const file = entries[index];
    const command = event.metaKey || event.ctrlKey;
    if (command && event.key.toLowerCase() === "a") {
      this.selectableEntries.forEach(entry => { entry.selected = true; });
    } else if (command) return;
    else if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      let next = event.key === "ArrowDown" ? index + 1 : index - 1;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = entries.length - 1;
      const entry = entries[Math.max(0, Math.min(next, entries.length - 1))];
      if (entry) {
        if (event.shiftKey) { this.selectionAnchor ||= file?.path || entry.path; this.selectEntry(entry, event); }
        else this.selectionAnchor = entry.path;
        list.querySelector(`[data-file-path="${CSS.escape(entry.path)}"]`)?.focus();
      }
    } else if (file && !this.isPickerMode() && (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10"))) {
      const row = list.querySelector(`[data-file-path="${CSS.escape(file.path)}"]`);
      this.openEntryMenu(file, row);
    } else if (file && (event.key === "Enter" || (event.key === "ArrowRight" && file.is_dir))) this.activateEntry(file);
    else if (file && event.key === " ") this.selectEntry(file, { ctrlKey: true });
    else if (event.key === "ArrowLeft") this.navigateUp();
    else if (event.key === "F5") this.fetchFiles(this.browser.currentPath, { preserveOnError: true });
    else if (file && event.key === "F2" && !this.isPickerMode() && this.remoteAllowed("rename", file)) this.beginRename(file);
    else if (event.key === "Escape" && this.clipboard?.move) configuration.clipboard = null;
    else if (event.key === "Escape" && (this.selectedCount || this.filterOpen)) {
      this.clearSelection(); this.clearSearch(); this.filterOpen = false;
    } else if (event.key.length === 1 && event.key !== " ") {
      this.filterOpen = true;
      this.setFilter(this.searchQuery + event.key);
      globalThis.Alpine.nextTick(() => list.closest(".file-browser-root")?.querySelector(".file-filter-input")?.focus());
    } else return;
    event.preventDefault();
    event.stopPropagation();
  },

  isPickerMode() {
    return Boolean(this.destinationSelection) || this.pickerMode !== PICKER_MODE_NONE;
  },

  isTextOpenPicker() {
    return this.pickerMode === PICKER_MODE_TEXT_OPEN;
  },

  isSaveAsPicker() {
    return this.pickerMode === PICKER_MODE_SAVE_AS;
  },

  isSelectableEntry(file = {}) {
    if (this.isSaveAsPicker() || this.destinationSelection) return false;
    if (this.isTextOpenPicker()) return !file?.is_dir && this.isEditableFile(file);
    return true;
  },

  normalizeOpeningPath(path) {
    return String(path || "");
  },

  normalizeSubmittedPath(path) {
    const trimmed = String(path || "").trim();
    if (!trimmed || trimmed === "$WORK_DIR") return trimmed;
    return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  },

  syncPathInput() {
    this.pathInput = this.browser.currentPath || "";
  },

  // Pin to the right end when unedited or caret at end; blur re-pins through pinPathInputAfterBlur.
  pinPathInput(element) {
    if (!element) return;
    if (!element._pinResizeObserver) {
      element._pinResizeObserver = new ResizeObserver(() => {
        this.scrollPathInputNextFrame(element);
      });
    }
    element._pinResizeObserver.observe(element);
    this.scrollPathInputNextFrame(element);
  },

  runNextFrame(callback) {
    requestAnimationFrame(() => requestAnimationFrame(callback));
  },

  scrollPathInputNextFrame(element) {
    this.runNextFrame(() => this.scrollPathInputToEnd(element));
  },

  scrollPathInputToEnd(element) {
    if (!element || !element.isConnected) return;
    const atEnd = document.activeElement !== element
      || (element.selectionStart === element.value.length && element.selectionEnd === element.value.length);
    if (atEnd) element.scrollLeft = element.scrollWidth;
  },

  // Chrome resets an input's scrollLeft to 0 when the input blurs, after handlers and microtasks; snap on the first frame (pre-paint, instant) and re-check on the second in case the reset lands between frames.
  pinPathInputAfterBlur(element) {
    requestAnimationFrame(() => {
      this.scrollPathInputToEnd(element);
      requestAnimationFrame(() => this.scrollPathInputToEnd(element));
    });
  },

  // The raw submit slot acts as part of the field: a real click focuses the input.
  focusPathInput(button) {
    const input = button?.closest(".path-input-shell")?.querySelector("input");
    if (input) input.focus();
  },

  resetPathInput() {
    this.syncPathInput();
    this.pathError = "";
    this.clearPathSuggestions();
  },

  // --- Path bar: crumbs, edit mode, folder autocomplete --------------------
  pathCrumbs() {
    const current = this.normalizeOpeningPath(this.browser.currentPath).replace(/\/+$/, "");
    const crumbs = [{ name: "/", path: "/" }];
    if (!current || current === "$WORK_DIR") return crumbs;
    let acc = "";
    const parts = current.split("/").filter(Boolean);
    for (const [index, part] of parts.entries()) {
      acc += `/${part}`;
      // Providers are namespace segments, not browsable directories.
      if (parts[0] === "@connections" && index === 1) continue;
      crumbs.push({ name: part, path: acc });
    }
    return crumbs;
  },

  startPathEdit() {
    if (this.isLoading) return;
    this.pathEditing = true;
    this.resetPathInput();
  },

  exitPathEdit(restoreFocus = false) {
    const input = document.activeElement;
    const toolbar = input?.closest?.(".path-navigator");
    this.pathEditing = false;
    this.resetPathInput();
    if (restoreFocus) this.runNextFrame(() => toolbar?.querySelector(".path-edit-toggle")?.focus());
  },

  // Hide crumbs that would render partially; expose an overflow parent menu.
  measurePathCrumbFit(element, overflow = 0) {
    if (!element?.isConnected || !element.clientWidth) return 0;
    const crumbs = [...element.querySelectorAll(".path-crumb")];
    if (!crumbs.length) return 0;
    const measure = (available) => {
      let used = 0;
      let hidden = 0;
      for (let i = crumbs.length - 1; i >= 0; i--) {
        const width = crumbs[i].offsetWidth;
        // Hide any leading crumb, including root; only current folder must remain.
        if (used + width > available && i < crumbs.length - 1) {
          hidden = i + 1;
          break;
        }
        used += width;
      }
      return Math.min(hidden, crumbs.length - 1);
    };
    // Reset visibility first: hidden crumbs report offsetWidth 0 and corrupt sizing.
    crumbs.forEach((crumb) => {
      crumb.style.display = "";
    });
    // Measure the full slot first so an old chevron cannot perpetuate overflow.
    const available = element.clientWidth + (overflow ? 18 : 0);
    let hidden = measure(available);
    if (hidden) hidden = measure(available - 18);
    crumbs.forEach((crumb, index) => {
      crumb.style.display = index < hidden ? "none" : "";
    });
    element.scrollLeft = 0;
    return hidden;
  },

  async updatePathSuggestions(element = null) {
    this.clearPathSuggestions();
    const token = this._pathSuggestionsToken;
    this.pathSuggestionsOwner = element;
    this.pathError = "";
    const value = String(this.pathInput || "").trim();
    if (!value || value === "$WORK_DIR") {
      this.pathSuggestions = [];
      this.pathSuggestionsStyle = {};
      return;
    }
    const endsWithSlash = /\/$/.test(value);
    const normalized = this.normalizeSubmittedPath(value).replace(/\/+$/, "") || "/";
    const connectionRoot = normalized.match(/^\/@(?:connections\/[a-z0-9_]+|ssh)\/[a-f0-9]{32}(?=\/|$)/)?.[0];
    if (/^\/@(?:connections|ssh)\//.test(normalized) && !connectionRoot) return;
    const slashIndex = normalized.lastIndexOf("/");
    // Connection roots have no browsable parent within their provider namespace.
    const listChildren = endsWithSlash || normalized === connectionRoot;
    const parent = listChildren ? normalized : (slashIndex <= 0 ? "/" : normalized.slice(0, slashIndex));
    const prefix = listChildren ? "" : normalized.slice(slashIndex + 1).toLowerCase();
    try {
      const response = await fetchApi(`/get_work_dir_files?path=${encodeURIComponent(parent)}`);
      const data = await response.json().catch(() => ({}));
      if (token !== this._pathSuggestionsToken) return;
      if (!response.ok || data.error || data.data?.error) return;
      const entries = data?.data?.entries || [];
      const matches = entries
        .filter((entry) => entry.is_dir && entry.name.toLowerCase().startsWith(prefix) && entry.path !== normalized)
        .map((entry) => ({ name: entry.name, path: entry.path }));
      this.pathSuggestions = matches;
      const style = this.pathSuggestions.length && element
        ? this.getDropdownStyle(element, Math.max(element.getBoundingClientRect().width, 220), false)
        : {};
      // Cap the dropdown at 8 rows while keeping the viewport-aware placement.
      if (style.maxHeight) {
        style.maxHeight = `${Math.min(parseInt(style.maxHeight, 10) || 0, 304)}px`;
      }
      this.pathSuggestionsStyle = style;
    } catch {
      if (token === this._pathSuggestionsToken) {
        this.pathSuggestions = [];
        this.pathSuggestionsStyle = {};
      }
    }
  },

  async pickPathSuggestion(suggestion) {
    this.pathInput = this.normalizeSubmittedPath(suggestion?.path);
    this.clearPathSuggestions();
    await this.submitPath();
  },

  get activePathSuggestion() {
    return this.pathSuggestions[this.pathSuggestionIndex] || null;
  },

  selectPathSuggestion(element = null) {
    const suggestion = this.activePathSuggestion;
    if (!suggestion) return false;
    const path = this.normalizeSubmittedPath(suggestion.path);
    this.pathInput = path.endsWith("/") ? path : `${path}/`;
    this.pathSuggestions = [];
    this.updatePathSuggestions(element);
    return true;
  },

  movePathSuggestion(delta) {
    if (!this.pathSuggestions.length) return false;
    const count = this.pathSuggestions.length;
    this.pathSuggestionIndex = (this.pathSuggestionIndex + delta + count) % count;
    this.runNextFrame(() => {
      for (const container of document.querySelectorAll(".path-suggestions")) {
        if (container._fileBrowserOwner !== name || container.getClientRects().length === 0) continue;
        const row = container.querySelectorAll(".path-suggestion")[this.pathSuggestionIndex];
        row?.scrollIntoView({ block: "nearest" });
      }
    });
    return true;
  },

  clearPathSuggestions() {
    clearTimeout(this._pathSuggestionsTimer);
    this._pathSuggestionsTimer = null;
    this._pathSuggestionsToken++;
    this.pathSuggestions = [];
    this.pathSuggestionsStyle = {};
    this.pathSuggestionsOwner = null;
    this.pathSuggestionIndex = 0;
  },

  // Keystrokes debounce the directory fetch; direct calls (Tab accept, refocus) stay immediate.
  queuePathSuggestions(element = null) {
    this.clearPathSuggestions();
    this.pathError = "";
    this._pathSuggestionsTimer = setTimeout(() => {
      this._pathSuggestionsTimer = null;
      this.updatePathSuggestions(element);
    }, 200);
  },

  hidePathSuggestions() {
    this.exitPathEdit();
  },

  showPathSuggestions(element = null) {
    if (this.pathInput) this.updatePathSuggestions(element);
  },

  async loadDirectoryPreference() {
    if (this.settingsLoadPromise) return await this.settingsLoadPromise;

    this.settingsLoadPromise = (async () => {
      try {
        const response = await callJsonApi("settings_get", null);
        const remember = response?.settings?.file_browser_remember_last_directory;
        this.rememberLastDirectory =
          typeof remember === "boolean" ? remember : DEFAULT_REMEMBER_LAST_DIRECTORY;
      } catch (error) {
        console.warn("Failed to load file browser directory preference:", error);
        this.rememberLastDirectory = DEFAULT_REMEMBER_LAST_DIRECTORY;
      } finally {
        if (!this.rememberLastDirectory) this.clearRememberedDirectory();
        this.settingsLoadPromise = null;
      }
      return this.rememberLastDirectory;
    })();

    return await this.settingsLoadPromise;
  },

  getRememberedDirectory() {
    if (!this.rememberLastDirectory) return "";
    try {
      return localStorage.getItem(this.rememberKey) || "";
    } catch {
      return "";
    }
  },

  rememberCurrentDirectory(path = this.browser.currentPath) {
    if (!this.rememberLastDirectory) return;
    const directory = this.normalizeOpeningPath(path);
    if (!directory || directory === "$WORK_DIR") return;
    try {
      localStorage.setItem(this.rememberKey, directory);
    } catch {}
  },

  clearRememberedDirectory() {
    try {
      localStorage.removeItem(this.rememberKey);
    } catch {}
  },

  disposeScopedTooltips() {
    const root = this._mountedElement;
    const tooltipApi = globalThis.bootstrap?.Tooltip;
    if (!root || !tooltipApi) return;

    root.querySelectorAll("[data-bs-tooltip-initialized]").forEach((element) => {
      const instance = tooltipApi.getInstance(element);
      try {
        instance?.dispose();
      } catch {}
    });
  },

  // --- Modal helpers -------------------------------------------------------
  normalizePath(path) {
    if (!path) return "";
    return path.startsWith("/") ? path : `/${path}`;
  },

  fileExtension(file = {}) {
    const name = String(file?.name || file?.path || "").split(/[?#]/, 1)[0].toLowerCase();
    const index = name.lastIndexOf(".");
    return index >= 0 ? name.slice(index + 1) : "";
  },

  fileSurfaceTarget(file = {}) {
    if (!file || file.is_dir) return "";
    const ext = this.fileExtension(file);
    if (BROWSER_EXTENSIONS.has(ext)) return "browser";
    return this.isEditableFile(file) ? "editor" : "";
  },

  mediaPreview() { return mediaPreview(); },

  canPreview(file) { return Boolean(mediaKind(file)) && this.remoteAllowed("download", file); },

  previewFile(file) {
    if (!this.canPreview(file) || this.isPickerMode()) return;
    this._mountedElement?.querySelector(".files-media-dialog")?.dispatchEvent(new CustomEvent("file-preview", {detail: file}));
  },

  isEditableFile(file = {}) {
    if (!this.remoteAllowed("edit", file)) return false;
    if (!file || file.is_dir || !this.limits || file.size > this.limits.max_text_bytes || this.isArchive(file.name || file.path)) return false;
    const ext = this.fileExtension(file);
    return !new Set(["odt", "ods", "odp", "docx", "xlsx", "pptx"]).has(ext)
      && !["pdf", "png", "jpg", "jpeg", "gif", "webp", "bmp", "ico", "mp3", "mp4", "wav", "webm", "ogg", "woff", "woff2", "ttf"].includes(ext);
  },

  pickerAllowsEntry(file = {}) {
    if (this.destinationSelection) return file.is_dir;
    if (!this.isTextOpenPicker()) return true;
    return Boolean(file?.is_dir || this.isEditableFile(file));
  },

  pickerSelectedFiles() {
    if (!this.isTextOpenPicker()) return [];
    return this.selectedFiles.filter((file) => !file.is_dir && this.isEditableFile(file));
  },

  normalizedEditorTextExtension(value = "") {
    const ext = String(value || "").toLowerCase().trim().replace(/^\./, "");
    return ext;
  },

  pickerFilenameValue() {
    const raw = String(this.pickerFilename || "").trim();
    if (!raw) return "";
    const ext = this.fileExtension({ name: raw });
    return ext || !this.pickerDefaultExtension ? raw : `${raw}.${this.pickerDefaultExtension}`;
  },

  validatePickerFilename(updateError = true) {
    if (!this.isSaveAsPicker()) return true;
    const raw = String(this.pickerFilename || "").trim();
    const filename = this.pickerFilenameValue();
    let error = "";
    if (!raw) {
      error = "File name is required.";
    } else if (raw === "." || raw === "..") {
      error = "File name cannot be '.' or '..'.";
    } else if (raw.includes("/") || raw.includes("\\")) {
      error = "File name cannot include path separators.";
    } else if ((this.browser.entries || []).some((entry) => entry?.name === filename)) {
      error = `An item named "${filename}" already exists.`;
    }
    if (updateError) this.pickerFilenameError = error;
    return !error;
  },

  onPickerFilenameInput() {
    if (this.pickerFilenameError) this.validatePickerFilename(true);
  },

  canConfirmPicker() {
    if (this.destinationSelection) {
      const { paths, operation } = this.destinationSelection;
      return this.canTransfer(paths, this.browser.currentPath, operation);
    }
    if (this.isTextOpenPicker()) return this.pickerSelectedFiles().length > 0;
    if (this.isSaveAsPicker()) return this.remoteAllowed("upload") && Boolean(this.pickerFilenameValue()) && !this.pickerFilenameError;
    return false;
  },

  pickerTargetPath() {
    if (!this.isSaveAsPicker()) return "";
    return this.buildChildPath(this.pickerFilenameValue());
  },

  togglePickerFile(file = {}) {
    if (!this.isTextOpenPicker() || file?.is_dir || !this.isEditableFile(file)) return;
    file.selected = !file.selected;
  },

  async confirmPicker() {
    if (!this.isPickerMode() || this.isBulkBusy || this.isLoading || this.renameInline) return;
    if (this.destinationSelection) {
      const selection = this.destinationSelection;
      if (!this.canConfirmPicker()) return;
      this.destinationSelection = null;
      if (!await this.transferFiles(selection.paths, this.browser.currentPath, selection.operation)) {
        this.destinationSelection = selection;
      }
      return;
    }
    if (this.isSaveAsPicker() && !this.validatePickerFilename(true)) return;
    const payload = this.isSaveAsPicker()
      ? {
        mode: this.pickerMode,
        directory: this.browser.currentPath,
        filename: this.pickerFilenameValue(),
        path: this.pickerTargetPath(),
      }
      : {
        mode: this.pickerMode,
        directory: this.browser.currentPath,
        selectedFiles: this.pickerSelectedFiles(),
      };
    try {
      this.isBulkBusy = true;
      const result = await this.pickerOnConfirm?.(payload);
      if (result === false) return;
      this.disposeScopedTooltips();
      this.isBulkBusy = false;
      await this.closeOrRestorePicker();
    } catch (error) {
      const message = error?.message || "File selection failed";
      if (this.isSaveAsPicker()) this.pickerFilenameError = message;
      window.toastFrontendError?.(message, "File Browser");
    } finally {
      this.isBulkBusy = false;
    }
  },

  async cancelPicker() {
    if (this.destinationSelection) {
      const { directory } = this.destinationSelection;
      this.destinationSelection = null;
      return this.navigateToFolder(directory);
    }
    this.disposeScopedTooltips();
    await this.closeOrRestorePicker();
  },

  async closeOrRestorePicker() {
    if (this.isBulkBusy || this.isRenaming) return;
    if (this._finishPicker) await this._finishPicker();
    else await this.restoreBrowserAfterInPlacePicker();
  },

  async restoreBrowserAfterInPlacePicker() {
    // Drop picker state and reload the listing so a live surface returns to normal browsing.
    this.resetPickerState();
    this.clearSelection();
    this.isLoading = false;
    await this.fetchFiles(this.browser.currentPath, { preserveOnError: true });
  },

  handleFileNameClick(file = {}) {
    if (file?.is_dir) {
      return this.navigateToFolder(file.path);
    }
    if (this.isTextOpenPicker()) {
      this.togglePickerFile(file);
    } else if (!this.isPickerMode()) {
      return this.canOpenInSurface(file) ? this.openInSurface(file) : this.downloadFile(file);
    }
  },

  canOpenInSurface(file = {}) {
    return Boolean(this.fileSurfaceTarget(file));
  },

  isEditorSurface(file = {}) {
    return this.fileSurfaceTarget(file) === "editor";
  },

  canOpenInActionMenu(file = {}) {
    if (this.isRemote(file.path)) return false;
    const target = this.fileSurfaceTarget(file);
    return Boolean(target && target !== "editor");
  },

  surfaceAction(file = {}) {
    const target = this.fileSurfaceTarget(file);
    return target ? SURFACE_ACTIONS[target] : null;
  },

  surfaceActionLabel(file = {}) {
    return this.surfaceAction(file)?.label || "Open";
  },

  surfaceActionIcon(file = {}) {
    return this.surfaceAction(file)?.icon || "open_in_new";
  },

  surfaceActionTitle(file = {}) {
    return this.surfaceAction(file)?.title || "Open file";
  },

  fileUrl(file = {}) {
    const path = this.normalizePath(String(file?.path || ""));
    const encodedPath = path
      .split("/")
      .map((part) => encodeURIComponent(part))
      .join("/");
    return `file://${encodedPath}`;
  },

  storeHasPath(surfaceStore = {}, path = "") {
    const normalizedPath = this.normalizePath(path);
    const activePath = surfaceStore?.session?.path || surfaceStore?.session?.document?.path || "";
    return this.normalizePath(activePath) === normalizedPath;
  },

  buildChildPath(name) {
    const base = this.normalizePath(this.browser.currentPath || "");
    const trimmedBase = base.replace(/\/$/, "");
    if (!trimmedBase) return `/${name}`;
    return `${trimmedBase}/${name}`;
  },

  parentPath(path) {
    const normalized = this.normalizePath(String(path || "")).replace(/\/+$/, "");
    const index = normalized.lastIndexOf("/");
    if (index <= 0) return "/";
    return normalized.slice(0, index);
  },

  siblingPath(path, name) {
    const parent = this.parentPath(path);
    return parent === "/" ? `/${name}` : `${parent}/${name}`;
  },

  resetRenameState() {
    this.renameTarget = null;
    this.renameName = "";
    this.renameMode = "rename";
    this.renameInline = false;
    this.renameDirectory = "";
    this.renameEntries = [];
    this.isRenaming = false;
    this.renameError = null;
    this.renameAfterConfirm = null;
    this.renamePerformAction = null;
    this.renameValidateName = null;
  },

  // --- Sorting -------------------------------------------------------------
  toggleSort(column) {
    if (this.browser.explicitSort && this.browser.sortBy === column) {
      if (this.browser.sortDirection === "asc") this.browser.sortDirection = "desc";
      else {
        this.browser.explicitSort = false;
        this.browser.sortBy = this.preferences.sortBy;
        this.browser.sortDirection = this.preferences.sortDirection;
      }
    } else {
      this.browser.explicitSort = true;
      this.browser.sortBy = column;
      this.browser.sortDirection = "asc";
    }
  },

  sortFiles(entries) {
    return [...entries].sort((a, b) => {
      if (!this.browser.explicitSort && a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
      const dir = this.browser.sortDirection === "asc" ? 1 : -1;
      switch (this.browser.sortBy) {
        case "name":
          return dir * filenameOrder.compare(a.name, b.name);
        case "size":
          return dir * (a.size - b.size);
        case "date":
          return dir * (new Date(a.modified) - new Date(b.modified));
        default:
          return 0;
      }
    });
  },

  // --- Dropdown Management -------------------------------------------------
  focusMenuButton(menu, delta) {
    const buttons = Array.from(menu.querySelectorAll("button")).filter(button => !button.disabled && button.checkVisibility());
    const next = (buttons.indexOf(document.activeElement) + delta + buttons.length) % buttons.length;
    buttons[next]?.focus();
  },

  contextEntry(file, event) {
    if (this.isPickerMode()) return;
    event.preventDefault();
    this.openEntryMenu(file, event.currentTarget, event);
  },

  openEntryMenu(file, row, point = null) {
    const button = row?.querySelector(".dropdown-trigger");
    if (!button) return;
    if (!file.selected) this.selectEntry(file);
    row.focus({ preventScroll: true });
    this.openDropdownPath = file.path;
    this.dropdownOwner = button.closest(".file-actions");
    this.dropdownStyle = this.getDropdownStyle(point ? {
      getBoundingClientRect: () => ({ left: point.clientX, right: point.clientX, top: point.clientY, bottom: point.clientY }),
    } : button, 180, !point);
  },

  toggleDropdown(filePath, triggerElement = null) {
    // Toggle: if already open, close it; otherwise open this one (closing any other)
    const owner = triggerElement?.closest(".file-actions") || null;
    if (this.isDropdownOpen(filePath, owner)) {
      this.closeDropdown();
      return;
    }
    const entry = this.browser.entries.find(file => file.path === filePath);
    if (entry && !entry.selected) this.selectEntry(entry);
    this.openDropdownPath = filePath;
    this.dropdownOwner = owner;
    this.dropdownStyle = this.getDropdownStyle(triggerElement);
  },

  isDropdownOpen(filePath, owner = null) {
    return this.openDropdownPath === filePath && (!owner || owner === this.dropdownOwner);
  },

  closeDropdown(restoreFocus = false) {
    if (restoreFocus) this.dropdownOwner?.closest(".file-item")?.focus({preventScroll: true});
    this.openDropdownPath = null;
    this.dropdownOwner = null;
    this.dropdownStyle = {};
  },

  getDropdownStyle(triggerElement, width = 180, alignRight = true) {
    if (!triggerElement) return {};

    const rect = triggerElement.getBoundingClientRect();
    const gap = 6;
    const padding = 8;
    const minWidth = Math.min(width, window.innerWidth - padding * 2);
    const spaceBelow = window.innerHeight - rect.bottom - gap - padding;
    const spaceAbove = rect.top - gap - padding;
    const openUp = spaceBelow < 160 && spaceAbove > spaceBelow;
    const maxHeight = Math.max(96, openUp ? spaceAbove : spaceBelow);
    const maxLeft = Math.max(padding, window.innerWidth - minWidth - padding);
    const left = Math.min(Math.max(alignRight ? rect.right - minWidth : rect.left, padding), maxLeft);

    return {
      position: "fixed",
      left: `${Math.round(left)}px`,
      right: "auto",
      top: openUp ? "auto" : `${Math.round(rect.bottom + gap)}px`,
      bottom: openUp ? `${Math.round(window.innerHeight - rect.top + gap)}px` : "auto",
      minWidth: `${minWidth}px`,
      maxHeight: `${Math.round(maxHeight)}px`,
      zIndex: "6000",
    };
  },

  // --- Navigation ----------------------------------------------------------
  async fetchFiles(path = "", options = {}) {
    const request = ++this._directoryRequest;
    this.clearPathSuggestions();
    const preserveOnError = options?.preserveOnError === true;
    const suppressErrorToast = options?.suppressErrorToast === true;
    const requestedPath = this.normalizeOpeningPath(path) || "$WORK_DIR";
    this.isLoading = true;
    
    // Preserve scroll position if refreshing the same path
    const isSamePath =
      this.browser.currentPath === requestedPath ||
      (requestedPath === "$WORK_DIR" && ["/a0", "$WORK_DIR", ""].includes(this.browser.currentPath));
    const list = this._mountedElement?.querySelector(".files-list");
    const focused = list?.contains(document.activeElement) ? document.activeElement : null;
    const scrollTop = isSamePath ? list?.scrollTop || 0 : 0;
    const selectedPaths = isSamePath
      ? new Set(this.selectedFiles.map((file) => file.path))
      : new Set();
    
    try {
      const response = await fetchApi(
        `/get_work_dir_files?path=${encodeURIComponent(requestedPath)}`
      );
      const data = await response.json().catch(() => ({}));
      if (request !== this._directoryRequest) return false;
      if (data.limits) this.limits = data.limits;

      const result = data.data || {};
      const entries = result.entries || [];
      const resolvedCurrentPath =
        result.current_path || (requestedPath === "$WORK_DIR" ? "/a0" : requestedPath);
      const resultError =
        data.error ||
        result.error ||
        (
          requestedPath &&
          requestedPath !== "$WORK_DIR" &&
          !result.current_path &&
          !entries.length
            ? "Directory not found or not accessible"
            : ""
        );

      if (response.ok && !resultError) {
        if (!isSamePath && this.renameInline && !this.isRenaming) this.resetRenameState();
        if (!isSamePath) {
          this.clearSearch();
          this.focusedPath = "";
          this.selectionAnchor = "";
        }
        this.lastTap = null;
        this.remotePermissions = result.permissions || null;
        this.browser.entries = this.decorateEntries(
          entries,
          selectedPaths
        );
        this.browser.currentPath = resolvedCurrentPath;
        this.browser.parentPath = result.parent_path;
        if (this.isSaveAsPicker() && this.pickerFilenameError) this.validatePickerFilename(true);
        this.syncPathInput();
        this.pathError = "";
        this.rememberCurrentDirectory(this.browser.currentPath);
        
        this.isLoading = false;
        if (list) this.runNextFrame(() => {
          if (this._directoryRequest !== request || !list.isConnected) return;
          list.scrollTop = scrollTop;
          if (focused && (document.activeElement === focused || document.activeElement === document.body)) {
            const row = this.focusedPath && list.querySelector(`[data-file-path="${CSS.escape(this.focusedPath)}"]`);
            (row || list).focus({preventScroll: true});
          }
        });
        return true;
      } else {
        const msg = resultError || "Error fetching files";
        console.error("Error fetching files:", msg);
        if (!preserveOnError) this.browser.entries = [];
        this.isLoading = false;
        if (!suppressErrorToast) window.toastFrontendError(msg, "File Browser Error");
        return false;
      }
    } catch (e) {
      if (request !== this._directoryRequest) return false;
      const message = "Error fetching files: " + e.message;
      if (!suppressErrorToast) {
        window.toastFrontendError(message, "File Browser Error");
      }
      if (!preserveOnError) this.browser.entries = [];
      this.isLoading = false;
      return false;
    }
  },

  pushNavHistory(path) {
    this.history.push(path);
    this.forwardHistory = [];
  },

  async navigateStack(from, to) {
    if (this.isLoading || this.isRenaming || this.isBulkBusy || !this[from].length) return;
    const targetPath = this[from].at(-1);
    const previousPath = this.browser.currentPath;
    const loaded = await this.fetchFiles(targetPath, { preserveOnError: true });
    if (loaded) {
      this[from].pop();
      this[to].push(previousPath);
    }
  },

  navigateBack() {
    return this.navigateStack("history", "forwardHistory");
  },

  navigateForward() {
    return this.navigateStack("forwardHistory", "history");
  },

  async navigateToFolder(path) {
    if (this.isLoading || this.isRenaming || this.isBulkBusy) return false;
    path = path === "$WORK_DIR" ? path : this.normalizePath(path).replace(/\/+$/, "") || "/";
    if (this.browser.currentPath === path) {
      return true;
    }
    const previousPath = this.browser.currentPath;
    const loaded = await this.fetchFiles(path, { preserveOnError: true });
    if (loaded && previousPath !== this.browser.currentPath) this.pushNavHistory(previousPath);
    return loaded;
  },

  async submitPath() {
    if (this.isPathSubmitting || this.isLoading || this.isRenaming || this.isBulkBusy) return;

    const path = this.normalizeSubmittedPath(this.pathInput);
    if (!path) {
      this.pathError = "Enter a directory path.";
      return;
    }

    // Submitting the already-current directory is a no-op, like navigateToFolder.
    const currentPath = String(this.browser.currentPath || "").replace(/\/+$/, "");
    if (currentPath && path.replace(/\/+$/, "") === currentPath) {
      this.exitPathEdit(true);
      return;
    }

    this.isPathSubmitting = true;
    this.pathError = "";

    try {
      const previousPath = this.browser.currentPath;
      const loaded = await this.fetchFiles(path, {
        preserveOnError: true,
        suppressErrorToast: true,
      });

      if (loaded) {
        if (previousPath && previousPath !== this.browser.currentPath) {
          this.pushNavHistory(previousPath);
        }
        this.exitPathEdit(true);
        return;
      }

      if (!this.isPickerMode() && !this.isRemote(path)) {
        const info = await callJsonApi("/file_info", { path });
        if (info.is_file) {
          const file = {name: info.file_name, path, size: info.size, is_dir: false};
          this.exitPathEdit();
          if (this.canPreview(file)) this.previewFile(file);
          else await this.handleFileNameClick(file);
          return;
        }
      }
      this.pathError = "Path not found or not accessible.";
    } catch (error) {
      this.pathError = error.message;
    } finally {
      this.isPathSubmitting = false;
    }
  },

  async navigateUp() {
    if (this.browser.parentPath) return this.navigateToFolder(this.browser.parentPath);
  },

  // --- Transfers ----------------------------------------------------------
  mountGestures(element, getView) { return mountFileGestures(element, getView); },

  get clipboard() { return configuration.clipboard; },

  copySelection(move, event = null) {
    const files = this.selectedFiles;
    if (this.isPickerMode() || !files.length || files.some(file => !this.remoteAllowed(move ? "rename" : "download", file))) return;
    if (!move && files.some(file => this.isRemote(file.path))) return;
    const record = {
      id: globalThis.crypto.randomUUID?.() || Math.random().toString(36).slice(2),
      paths: files.map(file => this.normalizePath(file.path)), move,
    };
    const write = clipboardEvent => {
      const data = clipboardEvent.clipboardData;
      if (!data) return;
      data.setData("text/plain", record.paths.join("\n"));
      // HTML keeps the opaque page-local token through native and toolbar paste.
      const tag = document.createElement("span");
      tag.dataset.a0FileSelection = record.id;
      tag.textContent = record.paths.join("\n");
      data.setData("text/html", tag.outerHTML);
      clipboardEvent.preventDefault();
      clipboardEvent.stopPropagation();
      configuration.clipboard = record;
    };
    if (event) write(event);
    else {
      document.addEventListener("copy", write, { capture: true, once: true });
      try {
        if (!document.execCommand("copy")) throw new Error("Use the keyboard Copy or Cut shortcut in the file list.");
      } catch (error) { window.toastFrontendError(error.message, "Clipboard"); }
      finally { document.removeEventListener("copy", write, true); }
    }
  },

  async pasteSelection(event = null) {
    if (this.isPickerMode() || this.isBulkBusy || !(this.remoteAllowed("upload") || this.remoteAllowed("rename"))) return;
    const path = this.browser.currentPath;
    try {
      let html, plain;
      if (event) {
        const data = event.clipboardData;
        if (data?.files?.length) {
          event.preventDefault(); event.stopPropagation();
          return this.uploadFiles(Array.from(data.files), path);
        }
        html = data?.getData("text/html") || "";
        plain = data?.getData("text/plain");
        if (!html.includes("data-a0-file-selection")) return;
        event.preventDefault(); event.stopPropagation();
      } else {
        if (!navigator.clipboard?.read) throw new Error("Focus the file list and use Ctrl+V or Command+V to paste.");
        const items = await navigator.clipboard.read();
        if (this.browser.currentPath !== path) return;
        const images = [];
        for (const item of items) {
          if (item.types.includes("image/png")) images.push(new File([await item.getType("image/png")], "clipboard-image.png", { type: "image/png" }));
          if (item.types.includes("text/plain")) {
            const blob = await item.getType("text/plain");
            if (blob.size < 1024 * 1024) plain = await blob.text();
          }
          if (item.types.includes("text/html")) {
            const blob = await item.getType("text/html");
            if (blob.size < 1024 * 1024) html = await blob.text();
          }
        }
        if (images.length) return this.uploadFiles(images, path);
      }
      if (this.browser.currentPath !== path || this.isPickerMode()) return;
      const record = this.clipboard;
      if (!record || plain !== record.paths.join("\n") || !html?.includes(`data-a0-file-selection="${record.id}"`)) throw new Error("No Files selection on the clipboard.");
      if (!this.canTransfer(record.paths, path, record.move ? "move" : "copy")) throw new Error("Choose a different destination folder.");
      if (record.move) configuration.clipboard = null;
      await this.transferFiles(record.paths, path, record.move ? "move" : "copy");
    } catch (error) {
      window.toastFrontendError(error.name === "NotAllowedError" ? "Focus the file list and use the keyboard Paste shortcut." : error.message, "Paste");
    }
  },

  canTransfer(paths, destinationPath, operation) {
    if (!paths.length || !destinationPath || this.isBulkBusy || this.pickerMode) return false;
    const dest = this.normalizePath(destinationPath).replace(/\/+$/, "") || "/";
    return paths.every(path => {
      const source = this.normalizePath(path);
      if (source === dest || dest.startsWith(source + "/")) return false;
      if (operation === "move" && this.parentPath(source) === dest) return false;
      if (this.isRemote(source) || this.isRemote(dest)) {
        const root = value => value.match(/^\/@(?:connections\/[^/]+|ssh)\/[^/]+(?=\/|$)/)?.[0];
        return operation === "move" && this.remoteAllowed("rename", {path: dest}) && !!root(source) && root(source) === root(dest);
      }
      return true;
    });
  },

  async transferFiles(paths, destinationPath, operation) {
    if (this.isPickerMode()) return false;
    const destination = this.normalizePath(destinationPath);
    if (!this.canTransfer(paths, destination, operation)) {
      toastFrontendNotice("error", "Choose a writable folder outside the selection. Remote moves must stay within one connection.", "Files");
      return false;
    }
    const sources = paths.map(path => this.normalizePath(path));
    const affected = new Set([destination, ...sources.map(path => this.parentPath(path))]);
    this.isBulkBusy = true;
    this.operationLabel = operation === "copy" ? "Copying…" : "Moving…";
    try {
      if (this.isRemote(destination)) {
        for (const path of sources) await this.connectionRequest("rename", { path, destination: destination.replace(/\/$/, "") + "/" + path.split("/").pop() });
      } else {
        const result = await callJsonApi("/rename_work_dir_file", { action: operation, paths: sources, destinationPath: destination, currentPath: destination });
        if (result.error) throw new Error(result.error);
      }
      const verb = operation === "copy" ? "Copied" : "Moved";
      window.toastFrontendSuccess?.(`${verb} ${sources.length} ${sources.length === 1 ? "item" : "items"} to ${destination}`, "Files");
      return true;
    } catch (error) {
      window.toastFrontendError(error.message, "File transfer");
      return false;
    } finally {
      this.isBulkBusy = false;
      this.operationLabel = "";
      await this.refreshFolders(affected);
    }
  },

  async refreshFolders(folders) {
    await Promise.all([...views.values()]
      .filter(browser => !browser.isLoading && folders.has(browser.browser.currentPath))
      .map(browser => browser.fetchFiles(browser.browser.currentPath, { preserveOnError: true })));
  },

  chooseDestination(operation) {
    if (!this.selectionAllows(operation === "move" ? "rename" : "download") || (operation === "copy" && this.isRemote())) return;
    const paths = this.selectedFiles.map(file => this.normalizePath(file.path));
    this.closeDropdown();
    this.destinationSelection = { paths, operation, directory: this.browser.currentPath };
    this.pickerConfirmLabel = operation === "copy" ? "Copy here" : "Move here";
    this.clearSelection();
    this.clearSearch();
  },

  selectionAllows(permission) {
    return !this.isPickerMode() && !this.isBulkBusy && this.selectedCount > 0
      && this.selectedFiles.every(file => this.remoteAllowed(permission, file));
  },

  async localAction(action, paths, options = {}) {
    if (this.isBulkBusy || this.isPickerMode() || this.isRemote()) return false;
    const currentPath = this.browser.currentPath;
    this.isBulkBusy = true;
    this.operationError = "";
    this.operationLabel = {trash: "Moving to Trash…", restore: "Restoring…", purge: "Deleting…", compress: "Creating ZIP…", chmod: "Applying permissions…"}[action];
    try {
      const result = await callJsonApi("/file_browser_actions", {...options, action, paths, currentPath});
      if (result.error) throw new Error(result.error);
      await this.refreshFolders(new Set((result.paths || []).map(path => this.parentPath(path))));
      if (result.failed?.length) throw new Error(result.failed.join("\n"));
      return true;
    } catch (error) {
      this.operationError = error.message;
      window.toastFrontendError(error.message, "Files");
      return false;
    } finally {
      this.isBulkBusy = false;
      this.operationLabel = "";
    }
  },

  trashSelected() {
    if (!this.selectionAllows("delete")) return;
    return this.localAction("trash", this.selectedFiles.map(file => this.normalizePath(file.path)));
  },

  async propertyData(action, entries) {
    const paths = entries.map(entry => this.normalizePath(entry.path));
    const result = await callJsonApi("/file_browser_actions", { action, paths });
    if (result.error) throw new Error(result.error);
    return result;
  },

  summarizeProperties(entries) {
    const common = get => {
      const first = get(entries[0]);
      return entries.every(entry => get(entry) === first) ? first : "Multiple";
    };
    const type = entry => entry.is_symlink ? "Symbolic link" : entry.is_dir ? "Folder" : "File";
    const path = entry => this.normalizePath(entry.path);
    const rows = {
      Name: entries.length === 1 ? entries[0].name || path(entries[0]) : entries.length + " items",
      Location: entries.length === 1 ? path(entries[0]) : common(entry => this.parentPath(path(entry))),
      Type: common(type),
    };
    const hasFolders = entries.some(entry => entry.is_dir && !entry.is_symlink);
    const size = !hasFolders && entries.every(entry => Number.isFinite(entry.size))
      ? entries.reduce((sum, entry) => sum + entry.size, 0) : null;
    for (const [label, field] of Object.entries({UID: "uid", GID: "gid", Modified: "modified", Accessed: "accessed", Changed: "changed", Target: "symlink_target"})) {
      if (!entries.some(entry => entry[field] != null)) continue;
      const value = common(entry => entry[field]);
      if (["modified", "accessed", "changed"].includes(field) && value !== "Multiple") {
        rows[label] = this.formatDate(typeof value === "number" ? new Date(value).toISOString() : value);
      } else {
        rows[label] = value;
      }
    }
    const mode = common(entry => entry.mode);
    const editable = !this.isRemote() && entries.every(entry => !entry.is_symlink && path(entry) !== "/");
    if (!editable && mode) rows.Permissions = mode;
    return {rows, size, mode, editable, canMeasure: hasFolders && !this.isRemote()};
  },

  async readTrash() {
    const result = await callJsonApi("/file_browser_actions", {action: "list-trash"});
    if (result.error) throw new Error(result.error);
    return result.entries;
  },

  // --- Rename / Create -----------------------------------------------------
  beginRename(file, options = {}) {
    if (this.isLoading || this.isRenaming || this.isBulkBusy) return false;
    this.resetRenameState();
    this.renameTarget = file;
    this.renameName = file?.name || "";
    this.renameMode = "rename";
    this.renameError = null;
    this.renameAfterConfirm = typeof options.onRenamed === "function" ? options.onRenamed : null;
    this.renamePerformAction = typeof options.performRename === "function" ? options.performRename : null;
    this.renameValidateName = typeof options.validateName === "function" ? options.validateName : null;
    this.renameDirectory = typeof options.currentPath === "string" && options.currentPath
      ? options.currentPath : this.browser.currentPath;
    this.renameEntries = Array.isArray(options.entries) ? options.entries
      : this.renameDirectory === this.browser.currentPath ? this.browser.entries : [];
    this.renameInline = true;
    return true;
  },

  beginNewFolder() {
    if (!this.beginRename(null)) return false;
    this.renameMode = "create-folder";
    return true;
  },

  openRenameModal(file, options = {}) {
    if (!this.beginRename(file, options)) return;
    if (this.embedded) return;
    configuration.renameOwner = name;
    this.renameInline = false;
    window.openModal("modals/file-browser/rename-modal.html", () => !this.isRenaming);
  },

  openNewFolderModal() {
    if (!this.beginNewFolder()) return;
    if (this.embedded) return;
    configuration.renameOwner = name;
    this.renameInline = false;
    window.openModal("modals/file-browser/rename-modal.html", () => !this.isRenaming);
  },

  releaseRenameModal() {
    if (!this.isRenaming) this.resetRenameState();
    if (configuration.renameOwner === name) configuration.renameOwner = null;
  },

  closeRenameModal() {
    if (this.isRenaming) return;
    if (this.renameInline) {
      this.resetRenameState();
      return;
    }
    window.closeModal("modals/file-browser/rename-modal.html");
  },

  async confirmRename() {
    if (this.isRenaming || this.isLoading) return;

    const newName = this.renameName.trim();
    if (!newName) {
      this.renameError = "Name is required.";
      return;
    }
    if (newName === "." || newName === "..") {
      this.renameError = "Name cannot be '.' or '..'.";
      return;
    }
    if (newName.includes("/") || newName.includes("\\")) {
      this.renameError = "Name cannot include path separators.";
      return;
    }
    if (this.renameMode !== "create-folder" && !this.renameTarget?.path) {
      this.renameError = "No item selected for rename.";
      return;
    }
    if (this.renameValidateName) {
      const validation = this.renameValidateName(newName, this.renameTarget);
      if (validation !== true) {
        this.renameError = typeof validation === "string" ? validation : "Name is not valid.";
        return;
      }
    }

    // UX: pre-validate duplicates so we can show a clean inline error (no toast spam)
    const duplicate = this.renameEntries.some((entry) => {
      if (!entry?.name) return false;
      if (entry.name !== newName) return false;
      // When renaming, allow keeping the same entry name
      if (this.renameTarget?.path && entry.path === this.renameTarget.path) return false;
      return true;
    });
    if (duplicate) {
      this.renameError = `An item named "${newName}" already exists.`;
      return;
    }

    this.isRenaming = true;
    this.renameError = null;

    try {
      const previousPath = this.renameTarget?.path || "";
      const renamedPath =
        this.renameMode === "create-folder"
          ? `${this.renameDirectory.replace(/\/$/, "")}/${newName}`
          : this.siblingPath(previousPath, newName);
      const payload =
        this.renameMode === "create-folder"
          ? {
              action: "create-folder",
              parentPath: this.renameDirectory,
              currentPath: this.browser.currentPath,
              newName: newName,
            }
          : {
              action: "rename",
              path: this.renameTarget?.path,
              currentPath: this.browser.currentPath,
              newName: newName,
            };

      let data = {};
      if (this.isRemote(renamedPath) && !this.renamePerformAction) {
        await this.connectionRequest(this.renameMode === "create-folder" ? "mkdir" : "rename", {
          path: this.renameMode === "create-folder" ? renamedPath : previousPath, destination:renamedPath,
        });
        await this.fetchFiles(this.browser.currentPath);
        this.isRenaming = false;
        this.closeRenameModal();
        return;
      }
      if (this.renamePerformAction) {
        data = await this.renamePerformAction({
          action: this.renameMode,
          previousPath,
          path: renamedPath,
          name: newName,
          target: this.renameTarget,
          payload,
        }) || {};
        if (data.error || data.ok === false) {
          throw new Error(data.error || "Rename failed");
        }
      } else {
        const resp = await fetchApi("/rename_work_dir_file", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        data = await resp.json().catch(() => ({}));
        if (!resp.ok || data.error) {
          throw new Error(data.error || "Rename failed");
        }
      }

      if (!this.renamePerformAction || data.refreshFiles !== false) {
        await this.fetchFiles(this.browser.currentPath);
      }
      if (this.renameAfterConfirm) {
        await this.renameAfterConfirm({
          action: this.renameMode,
          previousPath,
          path: renamedPath,
          name: newName,
          target: this.renameTarget,
          response: data,
        });
      }
      this.isRenaming = false;
      this.closeRenameModal();
    } catch (error) {
      const message = error?.message || "Rename failed";
      this.renameError = message;
      const title =
        this.renameMode === "create-folder" ? "Folder Error" : "Rename Error";
      window.toastFrontendError(message, title);
    } finally {
      this.isRenaming = false;
    }
  },

  // --- Shared Editor -------------------------------------------------------
  async openFileEditor(file) {
    return this.openInSurface(file, "editor");
  },

  async openNewFile() {
    if (this.isLoading || this.isRenaming || this.isBulkBusy) return;
    this.resetRenameState();
    this.configurePicker({
      pickerMode: PICKER_MODE_SAVE_AS,
      filename: "Untitled.txt",
      defaultExtension: "",
      onConfirm: async ({ path }) => {
        const { store: editorStore } = await import("/plugins/_editor/webui/editor-store.js");
        const session = await editorStore.openSession({ action: "create", path, source: "file-browser" });
        if (!session) throw new Error(editorStore.error || "Could not create file.");
        await (this.embedded ? openSurface : selectSurface)("editor", {});
        return true;
      },
    });
  },

  // --- File actions --------------------------------------------------------
  async extractArchive(file = {}) {
    if (!file?.path || !this.isArchive(file.name) || this.isBulkBusy) return;
    this.isBulkBusy = true;
    this.closeDropdown();
    try {
      const resp = await fetchApi("/extract_work_dir_archive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: file.path, currentPath: this.browser.currentPath }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || data.error) throw new Error(data.error || "Archive extraction failed");
      this.browser.entries = this.decorateEntries(data.data?.entries || []);
      this.browser.currentPath = data.data?.current_path || this.browser.currentPath;
      this.browser.parentPath = data.data?.parent_path || this.browser.parentPath;
      window.toastFrontendSuccess(`Extracted to ${data.extracted_path || "a new folder"}`, "Archive Extracted");
    } catch (error) {
      window.toastFrontendError(error?.message || "Archive extraction failed", "Archive Extract Error");
    } finally {
      this.isBulkBusy = false;
    }
  },

  createDownloadToastGroup(prefix) {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  },

  showDownloadPreparingToast(group) {
    window.toastFrontendInfo?.("Preparing download...", "Download", 0, group, undefined, true);
  },

  showDownloadStartedToast(group) {
    window.toastFrontendInfo?.("Downloading...", "Download", 3, group, undefined, true);
  },

  showDownloadErrorToast(group, message) {
    window.toastFrontendError?.(message || "Download failed", "Download Error", 8, group, undefined, true);
  },

  async bulkDownloadFiles() {
    const selectedFiles = this.selectedFiles;
    if (!this.selectionAllows("download")) return;

    this.isBulkBusy = true;
    this.closeDropdown();
    const downloadToastGroup = this.createDownloadToastGroup("file-browser-bulk-download");

    try {
      this.showDownloadPreparingToast(downloadToastGroup);
      await this.startDownload(selectedFiles);
      this.showDownloadStartedToast(downloadToastGroup);
    } catch (error) {
      this.showDownloadErrorToast(
        downloadToastGroup,
        error?.message || "Failed to download selected files"
      );
    } finally {
      this.isBulkBusy = false;
    }
  },

  async bulkDeleteFiles(selectedFiles = this.selectedFiles) {
    if (this.isPickerMode() || this.isBulkBusy || !selectedFiles.length || selectedFiles.some(file => !this.remoteAllowed("delete", file))) return;

    this.isBulkBusy = true;
    this.closeDropdown();

    try {
      if (this.isRemote()) {
        for (const file of selectedFiles) await this.connectionRequest("delete", {path:file.path});
        await this.fetchFiles(this.browser.currentPath);
        return;
      }
      const resp = await fetchApi("/delete_work_dir_files", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paths: selectedFiles.map((file) => file.path),
          currentPath: this.browser.currentPath,
        }),
      });
      const data = await resp.json().catch(() => ({}));

      if (resp.ok && !data.error) {
        this.browser.entries = this.decorateEntries(data.data?.entries || []);
        this.browser.currentPath = data.data?.current_path || this.browser.currentPath;
        this.browser.parentPath = data.data?.parent_path || this.browser.parentPath;
        const deletedCount = data.deleted?.length || selectedFiles.length;
        window.toastFrontendSuccess(
          `Deleted ${deletedCount} ${deletedCount === 1 ? "item" : "items"}`,
          "File Browser"
        );

        if (data.failed?.length) {
          window.toastFrontendError(
            `${data.failed.length} selected ${data.failed.length === 1 ? "item" : "items"} could not be deleted`,
            "File Browser"
          );
        }
      } else {
        window.toastFrontendError(
          data.error || "Error deleting selected files",
          "File Browser"
        );
      }
    } catch (error) {
      window.toastFrontendError(
        "Error deleting selected files: " + error.message,
        "File Browser"
      );
    } finally {
      this.isBulkBusy = false;
    }
  },

  async handleFileUpload(event) {
    const files = Array.from(event.target.files);
    event.target.value = "";
    return this.uploadFiles(files, this.browser.currentPath);
  },

  async openInSurface(file = {}, target = this.fileSurfaceTarget(file)) {
    if (this.isRemote(file.path)) target = "editor";
    const path = this.normalizePath(String(file?.path || ""));
    if (!target || !path) return;

    this.closeDropdown();

    try {
      if (target === "browser") {
        const url = this.fileUrl(file);
        const { store: browserStore } = await import("/plugins/_browser/webui/browser-store.js");
        await (this.embedded ? openSurface : selectSurface)("browser", { url, source: "file-browser" });

        let opened = false;
        for (let attempt = 0; attempt < 40 && !opened; attempt += 1) {
          opened = await browserStore.openUrlIntent(url, { source: "file-browser" });
          if (!opened) await delay(75);
        }
        if (!opened) {
          throw new Error("Browser surface is unavailable.");
        }
      } else {
        await (this.embedded ? openSurface : selectSurface)(target, { path, source: "file-browser" });
        if (target === "editor") {
          const { store: editorStore } = await import("/plugins/_editor/webui/editor-store.js");
          if (!this.storeHasPath(editorStore, path)) {
            const session = await editorStore.openPath(path, { source: "file-browser" });
            if (!session || session.ok === false) {
              throw new Error(editorStore.error || "Text document could not be opened.");
            }
          }
        }

      }

      this.disposeScopedTooltips();
    } catch (error) {
      window.toastFrontendError?.(
        error?.message || "Could not open file",
        "File Browser"
      );
    }
  },

  async uploadDrop(data, path) {
    const entries = Array.from(data.items || [], item => item.webkitGetAsEntry?.()).filter(Boolean);
    if (!entries.some(entry => entry.isDirectory)) return this.uploadFiles(Array.from(data.files), path);
    if (this.isRemote(path)) {
      toastFrontendNotice("error", "This connection supports dropping individual files.", "Upload");
      return;
    }
    const files = [], names = [], folders = [];
    async function collect(entry, prefix) {
      const name = prefix + entry.name;
      if (entry.isDirectory) {
        folders.push(name);
        const reader = entry.createReader();
        while (true) {
          const children = await new Promise((resolve, reject) => reader.readEntries(resolve, reject));
          if (!children.length) break;
          for (const child of children) await collect(child, name + "/");
        }
      } else {
        files.push(await new Promise((resolve, reject) => entry.file(resolve, reject)));
        names.push(name);
      }
    }
    try {
      for (const entry of entries) await collect(entry, "");
      return await this.uploadFiles(files, path, names, folders);
    } catch (error) { window.toastFrontendError(error.message, "Upload"); }
  },

  async uploadFiles(files, path, names = files.map(file => file.name), folders = []) {
    if (this.isPickerMode() || this.isBulkBusy || !this.remoteAllowed("upload") || (!files.length && !folders.length)) return;
    this.isBulkBusy = true;
    this.operationLabel = "Uploading…";
    try {
      const limits = await this.ensureLimits(true);
      const formData = new FormData();
      formData.append("path", path);
      if (!this.isRemote(path)) formData.append("manifest", JSON.stringify({ files: names, folders }));
      for (const f of files) {
        if (f.size > limits.max_file_bytes) {
          throw new Error(`File ${f.name} exceeds the ${limits.max_file_bytes / (1024 * 1024)} MiB limit.`);
        }
        formData.append("files[]", f);
      }
      const resp = await fetchApi("/upload_work_dir_files", {
        method: "POST",
        body: formData,
      });
      const data = await resp.json().catch(() => ({}));
      if (resp.ok && !data.error) {
        await this.refreshFolders(new Set([this.normalizePath(path)]));
        if (data.failed && data.failed.length) {
          const msg = data.failed
            .map((f) => typeof f === "string" ? f : `${f.name}: ${f.error}`)
            .join("\n");
          throw new Error(`Some files failed to upload:\n${msg}`);
        }
      } else {
        throw new Error(data.error || "Error uploading files");
      }
    } catch (e) {
      window.toastFrontendError(
        "Error uploading files: " + e.message,
        "File Upload Error"
      );
    } finally {
      this.isBulkBusy = false;
      this.operationLabel = "";
    }
  },

  async downloadDirectory(file) {
    const downloadToastGroup = this.createDownloadToastGroup("file-browser-directory-download");

    try {
      this.showDownloadPreparingToast(downloadToastGroup);
      await this.startDownload([file]);
      this.showDownloadStartedToast(downloadToastGroup);
    } catch (error) {
      this.showDownloadErrorToast(
        downloadToastGroup,
        error?.message || "Failed to download directory"
      );
    }
  },

  async downloadFile(file) {
    return this.downloadDirectory(file);
  },

};

  for (const key of sharedFields) {
    if (!Object.prototype.hasOwnProperty.call(configuration, key)) configuration[key] = model[key];
    Object.defineProperty(model, key, {
      enumerable: true, configurable: true,
      get: () => configuration[key],
      set: value => { configuration[key] = value; },
    });
  }
  view = createStore(name, model);
  views.set(name, view);
  return view;
}

const primary = createFileBrowserView("fileBrowserShared");
const facade = {
  get current() {
    if (configuration.modalOwner) return views.get(configuration.modalOwner);
    const context = getStore("chats")?.selected;
    return this.preferences.independent && context
      ? createFileBrowserView(`fileBrowserChat_${context}`, { rememberKey: `fileBrowser.lastDirectory.${context}` })
      : primary;
  },
  get renameView() { return views.get(configuration.renameOwner) || this.current; },
  init() {
    primary.loadPreferences();
    primary.ensureLimits().catch(() => {});
    if (configuration.settingsUpdatedHandler) return;
    configuration.settingsUpdatedHandler = event => {
      const value = event?.detail?.file_browser_remember_last_directory;
      if (typeof value !== "boolean") return;
      configuration.rememberLastDirectory = value;
      if (!value) {
        for (const browser of views.values()) browser.clearRememberedDirectory();
        // Clear saved chat locations even for views not mounted this session.
        try {
          for (const key of Object.keys(localStorage)) {
            if (key.startsWith("fileBrowser.lastDirectory.")) localStorage.removeItem(key);
          }
        } catch { /* Storage may be unavailable. Remembering remains disabled. */ }
      }
    };
    document.addEventListener("settings-updated", configuration.settingsUpdatedHandler);
  },
};
for (const key of Object.keys(primary)) {
  if (key === "init") continue;
  Object.defineProperty(facade, key, {
    enumerable: true, configurable: true,
    get() {
      if (sharedFields.includes(key)) return configuration[key];
      const browser = this.current;
      const value = browser[key];
      return typeof value === "function" ? value.bind(browser) : value;
    },
    set(value) {
      if (sharedFields.includes(key)) configuration[key] = value;
      else this.current[key] = value;
    },
  });
}
export const store = createStore("fileBrowser", facade);

window.openFileLink = async function (path) {
  try {
    const resp = await window.sendJsonData("/file_info", { path });
    if (!resp.exists) {
      toastFrontendNotice("error", "File does not exist.", "File Error");
      return;
    }
    if (resp.is_dir) {
      await store.open(resp.abs_path);
    } else {
      store.downloadFile({ path: resp.abs_path, name: resp.file_name });
    }
  } catch (e) {
    window.toastFrontendError(
      "Error opening file: " + e.message,
      "File Open Error"
    );
  }
};
