import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";

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

    try {
      // Open modal FIRST (immediate UI feedback)
      this.closePromise = window.openModal(
        "modals/file-browser/file-browser.html"
      );

      // // Setup cleanup on modal close
      // if (this.closePromise && typeof this.closePromise.then === "function") {
      //   this.closePromise.then(() => {
      //     this.destroy();
      //   });
      // }

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
  },

  // --- Helpers -------------------------------------------------------------
  isArchive(filename) {
    const archiveExts = ["zip", "tar", "gz", "rar", "7z"];
    const ext = filename.split(".").pop().toLowerCase();
    return archiveExts.includes(ext);
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

  // --- Navigation ----------------------------------------------------------
  async fetchFiles(path = "") {
    this.isLoading = true;
    try {
      const response = await fetchApi(
        `/get_work_dir_files?path=${encodeURIComponent(path)}`
      );
      if (response.ok) {
        const data = await response.json();
        this.browser.entries = data.data.entries;
        this.browser.currentPath = data.data.current_path;
        this.browser.parentPath = data.data.parent_path;
      } else {
        console.error("Error fetching files:", await response.text());
        this.browser.entries = [];
      }
    } catch (e) {
      window.toastFrontendError(
        "Error fetching files: " + e.message,
        "File Browser Error"
      );
      this.browser.entries = [];
    } finally {
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
      if (resp.ok) {
        this.browser.entries = this.browser.entries.filter(
          (e) => e.path !== file.path
        );
        window.toastFrontendSuccess("File deleted successfully", "File Deleted");
      } else {
        window.toastFrontendError(`Error deleting file: ${await resp.text()}`, "Delete Error");
      }
    } catch (e) {
      window.toastFrontendError(
        "Error deleting file: " + e.message,
        "File Delete Error"
      );
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
      if (resp.ok) {
        const data = await resp.json();
        this.browser.entries = data.data.entries;
        this.browser.currentPath = data.data.current_path;
        this.browser.parentPath = data.data.parent_path;
        if (data.failed && data.failed.length) {
          const msg = data.failed
            .map((f) => `${f.name}: ${f.error}`)
            .join("\n");
          alert(`Some files failed to upload:\n${msg}`);
        }
      } else {
        alert(await resp.text());
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

  downloadFile(file) {
    const link = document.createElement("a");
    link.href = `/download_work_dir_file?path=${encodeURIComponent(file.path)}`;
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
