import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";
import { store as fileEditorStore } from "/components/modals/file-editor/file-editor-store.js";

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
  error: null,
  renameTarget: null,
  renameName: "",
  renameMode: "rename",
  isRenaming: false,
  renameError: null,
  renameAfterConfirm: null,
  renamePerformAction: null,
  renameValidateName: null,
  openDropdownPath: null, // Track which dropdown is currently open
  searchQuery: "",
  isBulkBusy: false,

  // --- Lifecycle -----------------------------------------------------------
  init() {
    // Nothing special to do here; all methods available immediately
  },

  // --- Public API (called from button/link) --------------------------------
  async open(path = "") {
    if (this.isLoading) return; // Prevent double-open
    this.isLoading = true;
    this.error = null;
    this.history = [];
    this.searchQuery = "";
    this.isBulkBusy = false;

    try {
      // Open modal FIRST (immediate UI feedback)
      this.closePromise = window.openModal(
        "modals/file-browser/file-browser.html"
      );

      // Use stored initial path or default
      path = path || this.initialPath || this.browser.currentPath || "$WORK_DIR";
      this.browser.currentPath = path;

      // Fetch files
      await this.fetchFiles(this.browser.currentPath);

      // await modal close
      await this.closePromise;
      this.destroy();

    } catch (error) {
      console.error("File browser error:", error);
      this.error = error?.message || "Failed to load files";
      this.isLoading = false;
    }
  },

  handleClose() {
    // Close the modal manually
    window.closeModal();
  },

  destroy() {
    // Reset state when modal closes
    this.isLoading = false;
    this.history = [];
    this.initialPath = "";
    this.browser.entries = [];
    this.openDropdownPath = null;
    this.searchQuery = "";
    this.isBulkBusy = false;
    this.resetRenameState();
  },

  // --- Helpers -------------------------------------------------------------
  isArchive(filename) {
    const archiveExts = ["zip", "tar", "gz", "rar", "7z"];
    const ext = filename.split(".").pop().toLowerCase();
    return archiveExts.includes(ext);
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
    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  },

  decorateEntries(entries = [], selectedPaths = new Set()) {
    return entries.map((entry) => ({
      ...entry,
      selected: selectedPaths.has(entry.path),
    }));
  },

  get filteredEntries() {
    const query = this.searchQuery.trim().toLowerCase();
    if (!query) return this.browser.entries;

    return this.browser.entries.filter((file) => {
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
    return this.browser.entries.filter((file) => file.selected);
  },

  get selectedCount() {
    return this.selectedFiles.length;
  },

  get selectedCountLabel() {
    return `${this.selectedCount} ${this.selectedCount === 1 ? "item" : "items"} selected`;
  },

  get allVisibleSelected() {
    return (
      this.filteredEntries.length > 0 &&
      this.filteredEntries.every((file) => file.selected)
    );
  },

  get someVisibleSelected() {
    return this.filteredEntries.some((file) => file.selected);
  },

  toggleSelectAllVisible() {
    const shouldSelect = !this.allVisibleSelected;
    this.filteredEntries.forEach((file) => {
      file.selected = shouldSelect;
    });
  },

  clearSelection() {
    this.browser.entries.forEach((file) => {
      file.selected = false;
    });
  },

  // --- Modal helpers -------------------------------------------------------
  normalizePath(path) {
    if (!path) return "";
    return path.startsWith("/") ? path : `/${path}`;
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
  toggleDropdown(filePath) {
    // Toggle: if already open, close it; otherwise open this one (closing any other)
    this.openDropdownPath = this.openDropdownPath === filePath ? null : filePath;
  },

  isDropdownOpen(filePath) {
    return this.openDropdownPath === filePath;
  },

  closeDropdown() {
    this.openDropdownPath = null;
  },

  // --- Navigation ----------------------------------------------------------
  async fetchFiles(path = "") {
    this.isLoading = true;
    
    // Preserve scroll position if refreshing the same path
    const isSamePath = this.browser.currentPath === path || 
                       (!path && !this.browser.currentPath);
    const scrollPos = isSamePath ? this.saveScrollPosition() : null;
    const selectedPaths = isSamePath
      ? new Set(this.selectedFiles.map((file) => file.path))
      : new Set();
    
    try {
      const response = await fetchApi(
        `/get_work_dir_files?path=${encodeURIComponent(path)}`
      );
      const data = await response.json().catch(() => ({}));

      if (response.ok && !data.error) {
        if (!isSamePath) this.searchQuery = "";
        this.browser.entries = this.decorateEntries(
          data.data.entries || [],
          selectedPaths
        );
        this.browser.currentPath = data.data.current_path;
        this.browser.parentPath = data.data.parent_path;
        
        // Set isLoading to false BEFORE restoring scroll to avoid reactivity issues
        this.isLoading = false;
        
        // Restore scroll position if on same path
        if (scrollPos) {
          this.restoreScrollPosition(scrollPos);
        }
      } else {
        const msg = data.error || "Error fetching files";
        console.error("Error fetching files:", msg);
        this.browser.entries = [];
        this.isLoading = false;
        window.toastFrontendError(msg, "File Browser Error");
      }
    } catch (e) {
      window.toastFrontendError(
        "Error fetching files: " + e.message,
        "File Browser Error"
      );
      this.browser.entries = [];
      this.isLoading = false;
    }
  },

  async navigateToFolder(path) {
    if(!path.startsWith("/")) path = "/" + path;
    if (this.browser.currentPath !== path)
      this.history.push(this.browser.currentPath);
    await this.fetchFiles(path);
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
