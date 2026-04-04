import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";
import { renderSafeMarkdown } from "/js/safe-markdown.js";

const IMAGE_EXTS = new Set([
  "jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "svgz",
]);
const PDF_EXTS = new Set(["pdf"]);
const VIDEO_EXTS = new Set(["mp4", "webm", "ogg", "mov"]);
const AUDIO_EXTS = new Set(["mp3", "wav", "flac", "aac", "m4a"]);
const MARKDOWN_EXTS = new Set(["md"]);
const HTML_EXTS = new Set(["html", "htm"]);
const TEXT_EXTS = new Set([
  "txt", "json", "yaml", "yml", "xml", "csv", "log", "ini", "cfg", "conf",
  "py", "js", "ts", "css", "sh", "bash", "zsh",
  "c", "cpp", "h", "java", "go", "rs", "rb",
  "php", "sql", "r", "lua", "pl", "swift", "kt",
  "toml", "env", "gitignore", "dockerfile",
]);

const ALL_PREVIEWABLE = new Set([
  ...IMAGE_EXTS, ...PDF_EXTS, ...VIDEO_EXTS, ...AUDIO_EXTS,
  ...MARKDOWN_EXTS, ...HTML_EXTS, ...TEXT_EXTS,
]);

function getExt(filename) {
  const dot = filename.lastIndexOf(".");
  return dot >= 0 ? filename.slice(dot + 1).toLowerCase() : "";
}

function detectType(ext) {
  if (IMAGE_EXTS.has(ext)) return "image";
  if (PDF_EXTS.has(ext)) return "pdf";
  if (VIDEO_EXTS.has(ext)) return "video";
  if (AUDIO_EXTS.has(ext)) return "audio";
  if (MARKDOWN_EXTS.has(ext)) return "markdown";
  if (HTML_EXTS.has(ext)) return "html";
  if (TEXT_EXTS.has(ext)) return "text";
  return "unsupported";
}

const PLUGIN_API_PREFIX = "/plugins/_attachment_preview";

const model = {
  isOpen: false,
  filePath: "",
  fileName: "",
  fileExt: "",
  fileType: "",
  content: "",
  previewUrl: "",
  isLoading: false,
  error: /** @type {string|null} */ (null),
  isResizing: false,
  isMaximized: false,

  // Intercept openFileLink + download_work_dir_file links
  init() {
    this._interceptOpenFileLink();
    this._interceptDownloadLinks();
  },

  _interceptOpenFileLink() {
    const w = /** @type {any} */ (window);
    const origFn = w.openFileLink;
    if (!origFn) return;
    const self = this;
    w.openFileLink = function (path) {
      const filename = path.split("/").pop() || "";
      if (ALL_PREVIEWABLE.has(getExt(filename))) {
        self.open(path, filename);
        return;
      }
      return origFn.call(this, path);
    };
  },

  _interceptDownloadLinks() {
    const chatHistory = document.getElementById("chat-history");
    if (!chatHistory) return;

    chatHistory.addEventListener("click", (e) => {
      const anchor = /** @type {HTMLElement} */ (e.target).closest("a[href]");
      if (!anchor) return;

      const href = anchor.getAttribute("href") || "";
      if (!href.includes("/api/download_work_dir_file?")) return;

      const url = new URL(href, location.origin);
      const filePath = url.searchParams.get("path") || "";
      if (!filePath) return;

      const filename = filePath.split("/").pop()?.split("?")[0] || "";
      if (!ALL_PREVIEWABLE.has(getExt(filename))) return;

      e.preventDefault();
      e.stopPropagation();
      this.open(filePath, filename);
    });
  },

  isPreviewable(filename) {
    return ALL_PREVIEWABLE.has(getExt(filename));
  },

  async open(filePath, fileName) {
    filePath = decodeURIComponent(filePath);
    const ext = getExt(fileName || filePath);
    const type = detectType(ext);

    this.filePath = filePath;
    this.fileName = fileName || filePath.split("/").pop() || "";
    this.fileExt = ext;
    this.fileType = type;
    this.content = "";
    this.previewUrl = "";
    this.error = null;
    this.isLoading = true;
    this.isOpen = true;

    try {
      switch (type) {
        case "image":
          this.previewUrl = `/api/image_get?path=${encodeURIComponent(filePath)}`;
          break;

        case "markdown": {
          const resp = await fetchApi(
            `/edit_work_dir_file?path=${encodeURIComponent(filePath)}`
          );
          const data = await resp.json();
          if (data.error) throw new Error(data.error);
          this.content = renderSafeMarkdown(data.data.content);
          break;
        }

        case "text": {
          const resp = await fetchApi(
            `/edit_work_dir_file?path=${encodeURIComponent(filePath)}`
          );
          const data = await resp.json();
          if (data.error) throw new Error(data.error);
          this.content = data.data.content;
          break;
        }

        case "html":
        case "pdf":
        case "video":
        case "audio":
          this.previewUrl =
            `/api${PLUGIN_API_PREFIX}/preview_work_dir_file?path=${encodeURIComponent(filePath)}`;
          break;

        default:
          this.error = "This file type cannot be previewed.";
      }
    } catch (e) {
      console.error("Preview error:", e);
      this.error = e instanceof Error ? e.message : "Failed to load preview";
    } finally {
      this.isLoading = false;
    }
  },

  close() {
    this.isOpen = false;
    this.isMaximized = false;
    this.filePath = "";
    this.fileName = "";
    this.fileExt = "";
    this.fileType = "";
    this.content = "";
    this.previewUrl = "";
    this.isLoading = false;
    this.error = null;
  },

  downloadFile() {
    if (!this.filePath) return;
    const link = document.createElement("a");
    link.href = `/api/download_work_dir_file?path=${encodeURIComponent(this.filePath)}`;
    link.download = this.fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  // Resize
  startResize(e) {
    e.preventDefault();
    if (this.isMaximized) return;
    this.isResizing = true;

    const panel = document.getElementById("preview-panel");
    const rightPanel = document.getElementById("right-panel");
    if (!panel || !rightPanel) return;

    const onMove = (ev) => {
      const clientY = ev.touches ? ev.touches[0].clientY : ev.clientY;
      const rect = rightPanel.getBoundingClientRect();
      const newHeight = rect.bottom - clientY;
      const clamped = Math.max(120, Math.min(newHeight, rect.height * 0.75));
      panel.style.height = clamped + "px";
    };

    const onUp = () => {
      this.isResizing = false;
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      document.removeEventListener("touchmove", onMove);
      document.removeEventListener("touchend", onUp);
    };

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    document.addEventListener("touchmove", onMove, { passive: false });
    document.addEventListener("touchend", onUp);
  },

  toggleMaximize() {
    const panel = document.getElementById("preview-panel");
    if (!panel) {
      this.isMaximized = !this.isMaximized;
      return;
    }

    if (this.isMaximized) {
      panel.style.transition = "none";
      panel.style.height = "";
      this.isMaximized = false;
      requestAnimationFrame(() => {
        panel.style.transition = "";
      });
    } else {
      panel.style.height = "";
      this.isMaximized = true;
    }
  },
};

export const store = createStore("attachmentPreview", model);
