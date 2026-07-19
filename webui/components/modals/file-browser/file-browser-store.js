import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";
import { formatDateTime } from "/js/time-utils.js";
import { store as fileEditorStore } from "/components/modals/file-editor/file-editor-store.js";
import {
  openLatest as openLatestSurface,
  setupFloatingSurfaceModalChrome,
} from "/js/surfaces.js";

const FILE_BROWSER_MODAL_PATH = "modals/file-browser/file-browser.html";
const FILE_BROWSER_LAST_DIRECTORY_STORAGE_KEY = "fileBrowser.lastDirectory";
const DEFAULT_REMEMBER_LAST_DIRECTORY = true;
const PICKER_MODE_NONE = "";
const PICKER_MODE_TEXT_OPEN = "text-open";
const PICKER_MODE_SAVE_AS = "save-as";
const EDITOR_TEXT_EXTENSIONS = new Set(["md", "txt"]);
const DESKTOP_EXTENSIONS = new Set(["odt", "ods", "odp", "docx", "xlsx", "pptx"]);
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

const SURFACE_ACTIONS = {
  editor: {
    label: "Open in Editor",
    icon: "article",
    title: "Open text in Editor",
  },
  desktop: {
    label: "Open in Desktop",
    icon: "desktop_windows",
    title: "Open document in Desktop",
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

// Model migrated from legacy file_browser.js (lift-and-shift)
const model = {
  // Reactive state
  isLoading: false,
  browser: {
    title: "File Browser",
    currentPath: "",
    entries: [],
    parentPath: "",
    sortBy: "name",
    sortDirection: "asc",
  },
  history: [], // navigation stack
  initialPath: "", // Store path for open() call
  closePromise: null,
  isSurfaceHandoff: false,
  surfaceHandoffPath: "",
  error: null,
  pathInput: "",
  pathError: "",
  isPathSubmitting: false,
  rememberLastDirectory: DEFAULT_REMEMBER_LAST_DIRECTORY,
  settingsLoadPromise: null,
  settingsUpdatedHandler: null,
  _floatingCleanup: null,
  _mountedDefaultLoadTimer: null,
  renameTarget: null,
  renameName: "",
  renameMode: "rename",
  isRenaming: false,
  renameError: null,
  renameAfterConfirm: null,
  renamePerformAction: null,
  renameValidateName: null,
  openDropdownPath: null, // Track which dropdown is currently open
  dropdownStyle: {},
  searchQuery: "",
  isBulkBusy: false,
  pickerMode: PICKER_MODE_NONE,
  pickerConfirmLabel: "",
  pickerFilename: "",
  pickerDefaultExtension: "md",
  pickerFilenameError: "",
  pickerOnConfirm: null,

  // --- Lifecycle -----------------------------------------------------------
  init() {
    if (this.settingsUpdatedHandler) return;
    this.settingsUpdatedHandler = (event) => {
      const value = event?.detail?.file_browser_remember_last_directory;
      if (typeof value !== "boolean") return;
      this.rememberLastDirectory = value;
      if (!value) this.clearRememberedDirectory();
    };
    document.addEventListener("settings-updated", this.settingsUpdatedHandler);
  },

  onMount(element = null, options = {}) {
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    const mode = options?.mode === "canvas" ? "canvas" : "modal";
    if (mode === "modal") {
      this.setupFloatingModal(element);
    } else {
      this.scheduleMountedDefaultLoad();
    }
  },

  onUnmount() {
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    this.cancelMountedDefaultLoad();
  },

  // --- Public API (called from button/link) --------------------------------
  async open(path = "", options = {}) {
    if (this.isLoading) return; // Prevent double-open
    this.resetOpenState(options);

    try {
      // Open modal FIRST (immediate UI feedback)
      this.closePromise = window.openModal(FILE_BROWSER_MODAL_PATH);
      await this.loadOpeningPath(path);

      // await modal close
      await this.closePromise;
      if (!this.isSurfaceHandoff) this.destroy();

    } catch (error) {
      console.error("File browser error:", error);
      this.error = error?.message || "Failed to load files";
      this.isLoading = false;
    }
  },

  async openSurface(path = "") {
    if (this.isLoading) return false;
    this.resetOpenState();

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

  handleClose() {
    // Close the modal manually
    this.disposeScopedTooltips();
    window.closeModal(FILE_BROWSER_MODAL_PATH);
  },

  async openTextPicker(path = "", onConfirm = null) {
    return await this.open(path, {
      pickerMode: PICKER_MODE_TEXT_OPEN,
      confirmLabel: "Open Selected",
      onConfirm,
    });
  },

  async openSaveAsPicker(path = "", options = {}) {
    return await this.open(path, {
      pickerMode: PICKER_MODE_SAVE_AS,
      confirmLabel: "Save Here",
      filename: options.filename || "Untitled.md",
      defaultExtension: options.defaultExtension || "",
      onConfirm: options.onConfirm,
    });
  },

  destroy() {
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    this.cancelMountedDefaultLoad();
    // Reset state when modal closes
    this.isLoading = false;
    this.history = [];
    this.initialPath = "";
    this.closePromise = null;
    this.isSurfaceHandoff = false;
    this.surfaceHandoffPath = "";
    this.browser.currentPath = "";
    this.browser.parentPath = "";
    this.browser.entries = [];
    this.openDropdownPath = null;
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
    this.cancelMountedDefaultLoad();
    this.isLoading = true;
    this.error = null;
    this.history = [];
    this.searchQuery = "";
    this.isBulkBusy = false;
    this.pathError = "";
    this.isPathSubmitting = false;
    this.configurePicker(options);
  },

  configurePicker(options = {}) {
    const mode = String(options?.pickerMode || PICKER_MODE_NONE).trim();
    this.pickerMode = [PICKER_MODE_TEXT_OPEN, PICKER_MODE_SAVE_AS].includes(mode)
      ? mode
      : PICKER_MODE_NONE;
    this.pickerConfirmLabel = String(options?.confirmLabel || "").trim()
      || (this.pickerMode === PICKER_MODE_SAVE_AS ? "Save Here" : "Open Selected");
    this.pickerFilename = String(options?.filename || "").trim();
    this.pickerDefaultExtension = this.normalizedEditorTextExtension(
      options?.defaultExtension || this.fileExtension({ name: this.pickerFilename }) || "md",
    );
    this.pickerFilenameError = "";
    this.pickerOnConfirm = typeof options?.onConfirm === "function" ? options.onConfirm : null;
    if (this.pickerMode) this.clearSelection();
  },

  resetPickerState() {
    this.pickerMode = PICKER_MODE_NONE;
    this.pickerConfirmLabel = "";
    this.pickerFilename = "";
    this.pickerDefaultExtension = "md";
    this.pickerFilenameError = "";
    this.pickerOnConfirm = null;
  },

  async loadOpeningPath(path = "") {
    await this.loadDirectoryPreference();
    const explicitPath = this.normalizeOpeningPath(path || this.initialPath);
    const rememberedPath = !explicitPath ? this.getRememberedDirectory() : "";
    const targetPath = explicitPath || rememberedPath || "$WORK_DIR";
    this.browser.currentPath = targetPath;
    this.syncPathInput();

    const loaded = await this.fetchFiles(this.browser.currentPath, {
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

  saveScrollPosition() {
    // Find the file browser modal's scrollable container
    // We look for the modal containing .file-browser-root to target the correct modal
    const fileBrowserRoot = document.querySelector('.file-browser-root');
    if (fileBrowserRoot) {
      const modalScroll = fileBrowserRoot.closest('.modal-scroll');
      if (modalScroll) {
        return {
          scrollTop: modalScroll.scrollTop,
          scrollLeft: modalScroll.scrollLeft
        };
      }
    }
    return null;
  },

  restoreScrollPosition(scrollPos) {
    if (!scrollPos) return;

    const restore = () => {
      const fileBrowserRoot = document.querySelector('.file-browser-root');
      if (fileBrowserRoot) {
        const modalScroll = fileBrowserRoot.closest('.modal-scroll');
        if (modalScroll) {
          modalScroll.scrollTop = scrollPos.scrollTop;
          modalScroll.scrollLeft = scrollPos.scrollLeft;
        }
      }
    };

    requestAnimationFrame(() => requestAnimationFrame(restore));
  },

  formatFileSize(size) {
    if (size === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(size) / Math.log(k));
    return parseFloat((size / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
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
    const query = this.searchQuery.trim().toLowerCase();
    return this.browser.entries.filter((file) => {
      if (!this.pickerAllowsEntry(file)) return false;
      if (!query) return true;
      const searchable = [
        file.name,
        file.path,
        file.type,
        file.symlink_target,
        file.is_dir ? "folder directory" : "file",
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return searchable.includes(query);
    });
  },

  get visibleEntries() {
    return this.sortFiles(this.filteredEntries);
  },

  clearSearch() {
    this.searchQuery = "";
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
    this.browser.entries.forEach((file) => {
      file.selected = false;
    });
  },

  isPickerMode() {
    return this.pickerMode !== PICKER_MODE_NONE;
  },

  isTextOpenPicker() {
    return this.pickerMode === PICKER_MODE_TEXT_OPEN;
  },

  isSaveAsPicker() {
    return this.pickerMode === PICKER_MODE_SAVE_AS;
  },

  isSelectableEntry(file = {}) {
    if (this.isSaveAsPicker()) return false;
    if (this.isTextOpenPicker()) return !file?.is_dir && this.fileSurfaceTarget(file) === "editor";
    return true;
  },

  normalizeOpeningPath(path) {
    return String(path || "").trim();
  },

  normalizeSubmittedPath(path) {
    const trimmed = String(path || "").trim();
    if (!trimmed || trimmed === "$WORK_DIR") return trimmed;
    return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  },

  syncPathInput() {
    this.pathInput = this.browser.currentPath || "";
  },

  resetPathInput() {
    this.syncPathInput();
    this.pathError = "";
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
      return localStorage.getItem(FILE_BROWSER_LAST_DIRECTORY_STORAGE_KEY) || "";
    } catch {
      return "";
    }
  },

  rememberCurrentDirectory(path = this.browser.currentPath) {
    if (!this.rememberLastDirectory) return;
    const directory = this.normalizeOpeningPath(path);
    if (!directory || directory === "$WORK_DIR") return;
    try {
      localStorage.setItem(FILE_BROWSER_LAST_DIRECTORY_STORAGE_KEY, directory);
    } catch {}
  },

  clearRememberedDirectory() {
    try {
      localStorage.removeItem(FILE_BROWSER_LAST_DIRECTORY_STORAGE_KEY);
    } catch {}
  },

  disposeScopedTooltips() {
    const root = document.querySelector(".file-browser-root");
    const tooltipApi = globalThis.bootstrap?.Tooltip;
    if (!root || !tooltipApi) return;

    root.querySelectorAll("[data-bs-tooltip-initialized]").forEach((element) => {
      const instance = tooltipApi.getInstance(element);
      try {
        instance?.dispose();
      } catch {}
    });
    document.querySelectorAll(".tooltip").forEach((tooltip) => tooltip.remove());
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
    if (EDITOR_TEXT_EXTENSIONS.has(ext)) return "editor";
    if (BROWSER_EXTENSIONS.has(ext)) return "browser";
    if (DESKTOP_EXTENSIONS.has(ext)) return "desktop";
    return "";
  },

  pickerAllowsEntry(file = {}) {
    if (!this.isTextOpenPicker()) return true;
    return Boolean(file?.is_dir || this.fileSurfaceTarget(file) === "editor");
  },

  pickerSelectedFiles() {
    if (!this.isTextOpenPicker()) return [];
    return this.selectedFiles.filter((file) => !file.is_dir && this.fileSurfaceTarget(file) === "editor");
  },

  pickerSelectionLabel() {
    if (!this.isTextOpenPicker()) return "";
    const count = this.pickerSelectedFiles().length;
    if (!count) return "No text files selected";
    return `${count} text ${count === 1 ? "file" : "files"} selected`;
  },

  normalizedEditorTextExtension(value = "") {
    const ext = String(value || "").toLowerCase().trim().replace(/^\./, "");
    return EDITOR_TEXT_EXTENSIONS.has(ext) ? ext : "md";
  },

  pickerFilenameValue() {
    const raw = String(this.pickerFilename || "").trim();
    if (!raw) return "";
    const ext = this.fileExtension({ name: raw });
    return ext ? raw : `${raw}.${this.pickerDefaultExtension || "md"}`;
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
    } else if (!EDITOR_TEXT_EXTENSIONS.has(this.fileExtension({ name: filename }))) {
      error = "Use a .md or .txt file name.";
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
    if (this.isTextOpenPicker()) return this.pickerSelectedFiles().length > 0;
    if (this.isSaveAsPicker()) return Boolean(this.pickerFilenameValue()) && !this.pickerFilenameError;
    return false;
  },

  pickerTargetPath() {
    if (!this.isSaveAsPicker()) return "";
    return this.buildChildPath(this.pickerFilenameValue());
  },

  togglePickerFile(file = {}) {
    if (!this.isTextOpenPicker() || file?.is_dir || this.fileSurfaceTarget(file) !== "editor") return;
    file.selected = !file.selected;
  },

  async confirmPicker() {
    if (!this.isPickerMode() || this.isBulkBusy) return;
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
      window.closeModal(FILE_BROWSER_MODAL_PATH);
    } catch (error) {
      const message = error?.message || "File selection failed";
      if (this.isSaveAsPicker()) this.pickerFilenameError = message;
      window.toastFrontendError?.(message, "File Browser");
    } finally {
      this.isBulkBusy = false;
    }
  },

  cancelPicker() {
    this.disposeScopedTooltips();
    window.closeModal(FILE_BROWSER_MODAL_PATH);
  },

  handleFileNameClick(file = {}) {
    if (file?.is_dir) {
      return this.navigateToFolder(file.path);
    }
    if (this.isTextOpenPicker()) {
      this.togglePickerFile(file);
    }
  },

  canOpenInSurface(file = {}) {
    return Boolean(this.fileSurfaceTarget(file));
  },

  isEditorSurface(file = {}) {
    return this.fileSurfaceTarget(file) === "editor";
  },

  canOpenInActionMenu(file = {}) {
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
    this.isRenaming = false;
    this.renameError = null;
    this.renameAfterConfirm = null;
    this.renamePerformAction = null;
    this.renameValidateName = null;
  },

  // --- Sorting -------------------------------------------------------------
  toggleSort(column) {
    if (this.browser.sortBy === column) {
      this.browser.sortDirection =
        this.browser.sortDirection === "asc" ? "desc" : "asc";
    } else {
      this.browser.sortBy = column;
      this.browser.sortDirection = "asc";
    }
  },

  sortFiles(entries) {
    return [...entries].sort((a, b) => {
      // Folders first
      if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
      const dir = this.browser.sortDirection === "asc" ? 1 : -1;
      switch (this.browser.sortBy) {
        case "name":
          return dir * a.name.localeCompare(b.name);
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
  toggleDropdown(filePath, triggerElement = null) {
    // Toggle: if already open, close it; otherwise open this one (closing any other)
    if (this.openDropdownPath === filePath) {
      this.closeDropdown();
      return;
    }
    this.openDropdownPath = filePath;
    this.dropdownStyle = this.getDropdownStyle(triggerElement);
  },

  isDropdownOpen(filePath) {
    return this.openDropdownPath === filePath;
  },

  closeDropdown() {
    this.openDropdownPath = null;
    this.dropdownStyle = {};
  },

  getDropdownStyle(triggerElement) {
    if (!triggerElement) return {};

    const rect = triggerElement.getBoundingClientRect();
    const gap = 6;
    const padding = 8;
    const minWidth = 180;
    const spaceBelow = window.innerHeight - rect.bottom - gap - padding;
    const spaceAbove = rect.top - gap - padding;
    const openUp = spaceBelow < 160 && spaceAbove > spaceBelow;
    const maxHeight = Math.max(96, openUp ? spaceAbove : spaceBelow);
    const maxLeft = Math.max(padding, window.innerWidth - minWidth - padding);
    const left = Math.min(Math.max(rect.right - minWidth, padding), maxLeft);

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
    const preserveOnError = options?.preserveOnError === true;
    const suppressErrorToast = options?.suppressErrorToast === true;
    const requestedPath = this.normalizeOpeningPath(path) || "$WORK_DIR";
    this.isLoading = true;
    
    // Preserve scroll position if refreshing the same path
    const isSamePath =
      this.browser.currentPath === requestedPath ||
      (requestedPath === "$WORK_DIR" && ["/a0", "$WORK_DIR", ""].includes(this.browser.currentPath));
    const scrollPos = isSamePath ? this.saveScrollPosition() : null;
    const selectedPaths = isSamePath
      ? new Set(this.selectedFiles.map((file) => file.path))
      : new Set();
    
    try {
      const response = await fetchApi(
        `/get_work_dir_files?path=${encodeURIComponent(requestedPath)}`
      );
      const data = await response.json().catch(() => ({}));

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
        if (!isSamePath) this.searchQuery = "";
        this.browser.entries = this.decorateEntries(
          entries,
          selectedPaths
        );
        this.browser.currentPath = resolvedCurrentPath;
        this.browser.parentPath = result.parent_path;
        this.syncPathInput();
        this.pathError = "";
        this.rememberCurrentDirectory(this.browser.currentPath);
        
        // Set isLoading to false BEFORE restoring scroll to avoid reactivity issues
        this.isLoading = false;
        
        // Restore scroll position if on same path
        if (scrollPos) {
          this.restoreScrollPosition(scrollPos);
        }
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
      const message = "Error fetching files: " + e.message;
      if (!suppressErrorToast) {
        window.toastFrontendError(message, "File Browser Error");
      }
      if (!preserveOnError) this.browser.entries = [];
      this.isLoading = false;
      return false;
    }
  },

  async navigateToFolder(path) {
    if(!path.startsWith("/")) path = "/" + path;
    if (this.browser.currentPath !== path)
      this.history.push(this.browser.currentPath);
    await this.fetchFiles(path);
  },

  async submitPath() {
    if (this.isPathSubmitting || this.isLoading) return;

    const path = this.normalizeSubmittedPath(this.pathInput);
    if (!path) {
      this.pathError = "Enter a directory path.";
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
          this.history.push(previousPath);
        }
        return;
      }

      this.pathError = "Directory not found or not accessible.";
    } finally {
      this.isPathSubmitting = false;
    }
  },

  async navigateUp() {
    if (this.browser.parentPath) {
      this.history.push(this.browser.currentPath);
      await this.fetchFiles(this.browser.parentPath);
    }
  },

  // --- Rename / Create -----------------------------------------------------
  async openRenameModal(file, options = {}) {
    this.resetRenameState();
    this.renameTarget = file;
    this.renameName = file?.name || "";
    this.renameMode = "rename";
    this.renameError = null;
    this.renameAfterConfirm = typeof options.onRenamed === "function" ? options.onRenamed : null;
    this.renamePerformAction = typeof options.performRename === "function" ? options.performRename : null;
    this.renameValidateName = typeof options.validateName === "function" ? options.validateName : null;
    if (typeof options.currentPath === "string" && options.currentPath) {
      this.browser.currentPath = options.currentPath;
    }
    if (Array.isArray(options.entries)) {
      this.browser.entries = options.entries;
    }
    window.openModal("modals/file-browser/rename-modal.html");
  },

  async openNewFolderModal() {
    this.resetRenameState();
    this.renameMode = "create-folder";
    this.renameName = "";
    this.renameError = null;
    window.openModal("modals/file-browser/rename-modal.html");
  },

  closeRenameModal() {
    window.closeModal("modals/file-browser/rename-modal.html");
  },

  async confirmRename() {
    if (this.isRenaming) return;

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
    const duplicate = (this.browser.entries || []).some((entry) => {
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
          ? this.buildChildPath(newName)
          : this.siblingPath(previousPath, newName);
      const payload =
        this.renameMode === "create-folder"
          ? {
              action: "create-folder",
              parentPath: this.browser.currentPath,
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

  // --- File Editor (Delegated to FileEditorStore) --------------------------
  async openFileEditor(file) {
    await fileEditorStore.openFile(file, async () => {
      // Callback on successful save to refresh file list
      await this.fetchFiles(this.browser.currentPath);
    });
  },

  async openNewFile() {
    const existingNames = (this.browser.entries || [])
      .map((e) => e?.name)
      .filter(Boolean);
    await fileEditorStore.openNewFile(this.browser.currentPath, existingNames, async () => {
      // Callback on successful save to refresh file list
      await this.fetchFiles(this.browser.currentPath);
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

  async deleteFile(file) {
    try {
      const resp = await fetchApi("/delete_work_dir_file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: file.path,
          currentPath: this.browser.currentPath,
        }),
      });
      const data = await resp.json().catch(() => ({}));
      if (resp.ok && !data.error) {
        this.browser.entries = this.browser.entries.filter(
          (e) => e.path !== file.path
        );
        window.toastFrontendSuccess("File deleted successfully", "File Deleted");
      } else {
        window.toastFrontendError(data.error || "Error deleting file", "Delete Error");
      }
    } catch (e) {
      window.toastFrontendError(
        "Error deleting file: " + e.message,
        "File Delete Error"
      );
    }
  },

  copySelectedPaths() {
    const selectedFiles = this.selectedFiles;
    if (!selectedFiles.length) return;

    const paths = selectedFiles.map((file) => file.path).join("\n");
    this.copyToClipboard(paths, () => {
      window.toastFrontendSuccess(
        `Copied ${selectedFiles.length} ${selectedFiles.length === 1 ? "path" : "paths"}`,
        "File Browser"
      );
    });
  },

  copyToClipboard(text, onSuccess) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard
        .writeText(text)
        .then(() => onSuccess?.())
        .catch(() => this.fallbackCopyToClipboard(text, onSuccess));
    } else {
      this.fallbackCopyToClipboard(text, onSuccess);
    }
  },

  fallbackCopyToClipboard(text, onSuccess) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand("copy");
      onSuccess?.();
    } catch (error) {
      console.error("Clipboard copy failed:", error);
      window.toastFrontendError("Failed to copy selected paths", "File Browser");
    } finally {
      document.body.removeChild(textArea);
    }
  },

  getDownloadFilename(response, fallback) {
    const disposition = response.headers.get("Content-Disposition") || "";
    const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf8Match?.[1]) {
      try {
        return decodeURIComponent(utf8Match[1].replace(/^"|"$/g, ""));
      } catch {
        return utf8Match[1].replace(/^"|"$/g, "");
      }
    }

    const asciiMatch = disposition.match(/filename="([^"]+)"/i);
    return asciiMatch?.[1] || fallback;
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
    if (!selectedFiles.length || this.isBulkBusy) return;

    this.isBulkBusy = true;
    this.closeDropdown();
    const downloadToastGroup = this.createDownloadToastGroup("file-browser-bulk-download");

    try {
      this.showDownloadPreparingToast(downloadToastGroup);
      const resp = await fetchApi("/download_work_dir_files", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paths: selectedFiles.map((file) => file.path),
          currentPath: this.browser.currentPath,
        }),
      });

      if (!resp.ok) {
        const message = await resp.text();
        throw new Error(message || "Download failed");
      }

      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const fallback = `agent-zero-files-${selectedFiles.length}.zip`;
      const link = document.createElement("a");
      link.href = url;
      link.download = this.getDownloadFilename(resp, fallback);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 0);

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

  async bulkDeleteFiles() {
    const selectedFiles = this.selectedFiles;
    if (!selectedFiles.length || this.isBulkBusy) return;

    this.isBulkBusy = true;
    this.closeDropdown();

    try {
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
    return store._handleFileUpload(event); // bind to model to ensure correct context
  },

  async openInSurface(file = {}) {
    const target = this.fileSurfaceTarget(file);
    const path = this.normalizePath(String(file?.path || ""));
    if (!target || !path) return;

    this.closeDropdown();

    try {
      if (target === "browser") {
        const url = this.fileUrl(file);
        const { store: browserStore } = await import("/plugins/_browser/webui/browser-store.js");
        await openLatestSurface("browser", { url, source: "file-browser" });

        let opened = false;
        for (let attempt = 0; attempt < 40 && !opened; attempt += 1) {
          opened = await browserStore.openUrlIntent(url, { source: "file-browser" });
          if (!opened) await delay(75);
        }
        if (!opened) {
          throw new Error("Browser surface is unavailable.");
        }
      } else {
        await openLatestSurface(target, { path, source: "file-browser" });
        if (target === "editor") {
          const { store: editorStore } = await import("/plugins/_editor/webui/editor-store.js");
          if (!this.storeHasPath(editorStore, path)) {
            const session = await editorStore.openPath(path, { source: "file-browser" });
            if (!session || session.ok === false) {
              throw new Error(editorStore.error || "Text document could not be opened.");
            }
          }
        }
        if (target === "desktop") {
          const { store: desktopStore } = await import("/plugins/_desktop/webui/desktop-store.js");
          if (!this.storeHasPath(desktopStore, path)) {
            const session = await desktopStore.openPath(path);
            if (!session || session.ok === false) {
              throw new Error(desktopStore.error || "Document could not be opened.");
            }
          }
        }
      }

      this.disposeScopedTooltips();
      await window.closeModal?.(FILE_BROWSER_MODAL_PATH);
    } catch (error) {
      window.toastFrontendError?.(
        error?.message || "Could not open file",
        "File Browser"
      );
    }
  },

  async _handleFileUpload(event) {
    try {
      const files = event.target.files;
      if (!files.length) return;
      const formData = new FormData();
      formData.append("path", this.browser.currentPath);
      for (let f of files) {
        const ext = f.name.split(".").pop().toLowerCase();
        if (
          !["zip", "tar", "gz", "rar", "7z"].includes(ext) &&
          f.size > 100 * 1024 * 1024
        ) {
          alert(`File ${f.name} exceeds 100MB limit.`);
          continue;
        }
        formData.append("files[]", f);
      }
      const resp = await fetchApi("/upload_work_dir_files", {
        method: "POST",
        body: formData,
      });
      const data = await resp.json().catch(() => ({}));
      if (resp.ok && !data.error) {
        this.browser.entries = this.decorateEntries(data.data.entries || []);
        this.browser.currentPath = data.data.current_path;
        this.browser.parentPath = data.data.parent_path;
        if (data.failed && data.failed.length) {
          const msg = data.failed
            .map((f) => `${f.name}: ${f.error}`)
            .join("\n");
          alert(`Some files failed to upload:\n${msg}`);
        }
      } else {
        alert(data.error || "Error uploading files");
      }
    } catch (e) {
      window.toastFrontendError(
        "Error uploading files: " + e.message,
        "File Upload Error"
      );
    } finally {
      event.target.value = ""; // reset input so same file can be reselected
    }
  },

  async downloadDirectory(file) {
    const downloadToastGroup = this.createDownloadToastGroup("file-browser-directory-download");

    try {
      this.showDownloadPreparingToast(downloadToastGroup);
      const resp = await fetchApi(`/download_work_dir_file?path=${encodeURIComponent(file.path)}`, {
        method: "GET",
      });

      if (!resp.ok) {
        const message = await resp.text();
        throw new Error(message || "Download failed");
      }

      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const fallback = `${file.name}.zip`;
      const link = document.createElement("a");
      link.href = url;
      link.download = this.getDownloadFilename(resp, fallback);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 0);
      this.showDownloadStartedToast(downloadToastGroup);
    } catch (error) {
      this.showDownloadErrorToast(
        downloadToastGroup,
        error?.message || "Failed to download directory"
      );
    }
  },

  downloadFile(file) {
    if (file.is_dir) {
      return this.downloadDirectory(file);
    }

    const link = document.createElement("a");
    link.href = `/api/download_work_dir_file?path=${encodeURIComponent(file.path)}`;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
};

export const store = createStore("fileBrowser", model);

window.openFileLink = async function (path) {
  try {
    const resp = await window.sendJsonData("/file_info", { path });
    if (!resp.exists) {
      window.toastFrontendError("File does not exist.", "File Error");
      return;
    }
    if (resp.is_dir) {
      // Set initial path and open via store
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
