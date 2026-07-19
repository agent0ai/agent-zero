import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getContext } from "/index.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";

const REFRESH_DEBOUNCE_MS = 180;

function lineType(text) {
  if (text.startsWith("@@")) return "hunk";
  if (text.startsWith("+++") || text.startsWith("---") || text.startsWith("diff --git") || text.startsWith("index ")) {
    return "meta";
  }
  if (text.startsWith("+")) return "add";
  if (text.startsWith("-")) return "del";
  if (text.startsWith("\\ No newline")) return "note";
  return "context";
}

function dirname(path) {
  const clean = String(path || "").replace(/\/+$/, "");
  const index = clean.lastIndexOf("/");
  return index > 0 ? clean.slice(0, index) : "";
}

function apiPath(name) {
  return `/plugins/_time_travel/${name}`;
}

const model = {
  loading: false,
  busy: false,
  error: "",
  payload: null,
  contextId: "",
  workspacePath: "",
  fileFilter: "",
  selectedHash: "",
  selectedPath: "",
  selectedDiff: null,
  diffLoading: false,
  diffError: "",
  previewOpen: false,
  previewLoading: false,
  previewError: "",
  previewTechnicalDetails: "",
  previewDetailsOpen: false,
  preview: null,
  _root: null,
  _mode: "canvas",
  _refreshTimer: null,
  _filterTimer: null,
  _requestSeq: 0,
  _diffSeq: 0,

  async init(element = null) {
    await this.onMount(element, { mode: "canvas" });
  },

  async onMount(element = null, options = {}) {
    if (element) this._root = element;
    this._mode = options?.mode === "modal" ? "modal" : "canvas";
    if (this._mode !== "modal") {
      this.setupCanvasSurface(element);
    }
    this.contextId = this.resolveContextId();
    if (!this.payload && !this.loading) {
      await this.refresh({ contextId: this.contextId });
    }
  },

  async onOpen(payload = {}) {
    const nextContextId = String(payload.contextId || payload.context_id || this.resolveContextId() || "");
    await this.refresh({ contextId: nextContextId });
  },

  cleanup() {
    if (this._refreshTimer) {
      clearTimeout(this._refreshTimer);
      this._refreshTimer = null;
    }
    if (this._filterTimer) {
      clearTimeout(this._filterTimer);
      this._filterTimer = null;
    }
  },

  setupCanvasSurface(element = null) {
    if (element) this._root = element;
  },

  resolveContextId() {
    const urlContext = new URLSearchParams(globalThis.location?.search || "").get("ctxid");
    return getContext?.() || urlContext || globalThis.Alpine?.store?.("chats")?.selected || "";
  },

  scheduleRefresh(options = {}) {
    if (this._refreshTimer) clearTimeout(this._refreshTimer);
    this._refreshTimer = setTimeout(() => {
      this._refreshTimer = null;
      this.refresh(options).catch((error) => console.error("Time Travel refresh failed", error));
    }, REFRESH_DEBOUNCE_MS);
  },

  scheduleFilterRefresh() {
    if (this._filterTimer) clearTimeout(this._filterTimer);
    this._filterTimer = setTimeout(() => {
      this._filterTimer = null;
      this.refresh({ keepSelection: false });
    }, 240);
  },

  async refresh(options = {}) {
    const contextId = String(options.contextId || options.context_id || this.resolveContextId() || "");
    const seq = ++this._requestSeq;
    this.loading = true;
    this.error = "";
    try {
      const response = await callJsonApi(apiPath("history_list"), {
        context_id: contextId,
        limit: 100,
        offset: 0,
        file_filter: this.fileFilter,
      });
      if (seq !== this._requestSeq) return;
      if (!response?.ok) throw new Error(response?.error || "Could not load history.");
      this.payload = response;
      this.contextId = String(response.context_id || contextId || "");
      this.workspacePath = String(response.workspace?.display_path || response.workspace?.path || "");
      this.reconcileSelection(Boolean(options.keepSelection));
    } catch (error) {
      if (seq !== this._requestSeq) return;
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      if (seq === this._requestSeq) this.loading = false;
    }
  },

  async loadMore() {
    if (this.loading || !this.payload?.has_more || this.isLocked()) return;
    const seq = ++this._requestSeq;
    this.loading = true;
    try {
      const response = await callJsonApi(apiPath("history_list"), {
        context_id: this.contextId,
        limit: 100,
        offset: this.commits().length,
        file_filter: this.fileFilter,
      });
      if (seq !== this._requestSeq) return;
      if (!response?.ok) throw new Error(response?.error || "Could not load history.");
      this.payload.commits = [...this.commits(), ...(response.commits || [])];
      this.payload.has_more = Boolean(response.has_more);
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      if (seq === this._requestSeq) this.loading = false;
    }
  },

  reconcileSelection(keepSelection = false) {
    if (this.isLocked()) {
      this.selectedHash = "";
      this.selectedPath = "";
      this.selectedDiff = null;
      return;
    }

    const rows = this.timelineRows();
    let selected = keepSelection ? rows.find((row) => row.key === this.selectedHash) : null;
    if (!selected) selected = rows[0] || null;
    this.selectedHash = selected?.key || "";

    const files = this.selectedFiles();
    if (!files.some((file) => this.fileKey(file) === this.selectedPath)) {
      this.selectedPath = files[0] ? this.fileKey(files[0]) : "";
    }
    void this.loadSelectedDiff();
  },

  commits() {
    return Array.isArray(this.payload?.commits) ? this.payload.commits : [];
  },

  present() {
    return this.payload?.present || {};
  },

  isLocked() {
    return Boolean(this.payload?.workspace?.locked || this.payload?.workspace?.available === false);
  },

  hasHistory() {
    return this.commits().length > 0;
  },

  hasPresentChanges() {
    return Boolean(this.present()?.dirty);
  },

  timelineRows() {
    const rows = [];
    rows.push({
      key: "present",
      kind: "present",
      hash: this.payload?.current_hash || "",
      short_hash: "present",
      message: this.hasPresentChanges() ? "Present changes" : "Present clean",
      timestamp: "",
      files: this.present()?.files || [],
      is_current: false,
      dirty: this.hasPresentChanges(),
    });
    for (const commit of this.commits()) {
      rows.push({ key: commit.hash, kind: "commit", ...commit });
    }
    return rows;
  },

  selectedRow() {
    return this.timelineRows().find((row) => row.key === this.selectedHash) || null;
  },

  selectedCommit() {
    const row = this.selectedRow();
    return row?.kind === "commit" ? row : null;
  },

  selectedFiles() {
    const row = this.selectedRow();
    return Array.isArray(row?.files) ? row.files : [];
  },

  selectedFile() {
    return this.selectedFiles().find((file) => this.fileKey(file) === this.selectedPath) || null;
  },

  selectRow(row) {
    this.selectedHash = row?.key || "";
    const files = this.selectedFiles();
    this.selectedPath = files[0] ? this.fileKey(files[0]) : "";
    void this.loadSelectedDiff();
  },

  selectFile(file) {
    this.selectedPath = this.fileKey(file);
    void this.loadSelectedDiff();
  },

  fileKey(file) {
    return `${file?.old_path || ""}:${file?.path || ""}`;
  },

  async loadSelectedDiff() {
    const file = this.selectedFile();
    const row = this.selectedRow();
    this.selectedDiff = null;
    this.diffError = "";
    if (!file || !row || this.isLocked()) return;
    const seq = ++this._diffSeq;
    this.diffLoading = true;
    try {
      const response = await callJsonApi(apiPath("history_diff"), {
        context_id: this.contextId,
        commit_hash: row.kind === "present" ? this.payload?.current_hash || "" : row.hash,
        path: file.path || file.old_path,
        mode: row.kind === "present" ? "present" : "commit",
      });
      if (seq !== this._diffSeq) return;
      if (!response?.ok) throw new Error(response?.error || "Could not load diff.");
      this.selectedDiff = response;
    } catch (error) {
      if (seq !== this._diffSeq) return;
      this.diffError = error instanceof Error ? error.message : String(error);
    } finally {
      if (seq === this._diffSeq) this.diffLoading = false;
    }
  },

  async manualSnapshot() {
    if (this.busy || this.isLocked()) return;
    this.busy = true;
    this.error = "";
    try {
      const response = await callJsonApi(apiPath("history_snapshot"), {
        context_id: this.contextId,
        trigger: "manual",
      });
      if (!response?.ok) throw new Error(response?.error || "Snapshot failed.");
      globalThis.justToast?.(response.snapshot?.created ? "Snapshot captured" : "No changes to snapshot", "success", 1400, "time-travel-snapshot");
      await this.refresh({ keepSelection: true });
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      this.busy = false;
    }
  },

  async openPreview(operation, commit = null) {
    const target = commit || this.selectedCommit();
    if (!target || this.busy || this.isLocked()) return;
    if (operation === "travel" && target.is_current) return;
    this.previewOpen = true;
    this.previewLoading = true;
    this.previewError = "";
    this.previewTechnicalDetails = "";
    this.previewDetailsOpen = false;
    this.preview = { operation, commit_hash: target.hash, short_hash: target.short_hash, files: [], previews: [] };
    try {
      const response = await callJsonApi(apiPath("history_preview"), {
        context_id: this.contextId,
        operation,
        commit_hash: target.hash,
      });
      if (!response?.ok) throw new Error(response?.error || "Preview failed.");
      this.preview = response;
    } catch (error) {
      this.previewError = error instanceof Error ? error.message : String(error);
    } finally {
      this.previewLoading = false;
    }
  },

  closePreview() {
    if (this.busy) return;
    this.previewOpen = false;
    this.preview = null;
    this.previewError = "";
    this.previewTechnicalDetails = "";
    this.previewDetailsOpen = false;
  },

  async confirmPreview() {
    if (!this.preview || this.busy || this.previewLoading) return;
    const operation = this.preview.operation;
    const endpoint = operation === "travel" ? "history_travel" : "history_revert";
    this.busy = true;
    this.previewError = "";
    this.previewDetailsOpen = false;
    try {
      const response = await callJsonApi(apiPath(endpoint), {
        context_id: this.contextId,
        commit_hash: this.preview.commit_hash,
        metadata: { source: "time_travel_ui" },
      });
      if (!response?.ok) {
        const error = new Error(response?.error || `${operation} failed.`);
        error.technicalDetails = response?.technical_details || "";
        throw error;
      }
      globalThis.justToast?.(operation === "travel" ? "Workspace traveled" : "Revert applied", "success", 1500, "time-travel-apply");
      this.previewOpen = false;
      this.preview = null;
      await this.refresh({ keepSelection: false });
    } catch (error) {
      this.previewError = error instanceof Error ? error.message : String(error);
      this.previewTechnicalDetails = error?.technicalDetails || "";
    } finally {
      this.busy = false;
    }
  },

  patchLines(diff = null) {
    const patch = String((diff || this.selectedDiff)?.patch || "");
    if (!patch) return [];
    const textLines = patch.endsWith("\n") ? patch.slice(0, -1).split("\n") : patch.split("\n");
    return textLines.map((text, index) => ({
      id: `${index}-${text.slice(0, 20)}`,
      text,
      type: lineType(text),
    }));
  },

  fileTitle(file) {
    if (file?.old_path && file.old_path !== file.path) {
      return `${file.old_path} -> ${file.path}`;
    }
    return file?.path || file?.old_path || "";
  },

  statusLabel(file) {
    return String(file?.action || file?.status || "changed").replaceAll("_", " ");
  },

  rowMeta(row) {
    if (!row) return "";
    const files = Array.isArray(row.files) ? row.files.length : 0;
    if (row.kind === "present") return files ? `${files} file${files === 1 ? "" : "s"}` : "clean";
    return `${row.short_hash || ""} · ${this.formatTime(row.timestamp)}`;
  },

  formatTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  },

  formatSigned(value, sign) {
    const number = Number(value) || 0;
    return `${sign}${number.toLocaleString()}`;
  },

  fullPath(file) {
    const relativePath = String(file?.path || file?.old_path || "").replace(/^\/+/, "");
    const base = String(this.workspacePath || "").replace(/\/+$/, "");
    return relativePath ? `${base}/${relativePath}` : base;
  },

  async openContainingFolder(file) {
    const parent = dirname(this.fullPath(file));
    await fileBrowserStore.open(parent || this.workspacePath || "$WORK_DIR");
  },

  async copyPath(file) {
    const path = this.fullPath(file);
    try {
      await navigator.clipboard.writeText(path);
      globalThis.justToast?.("Path copied", "success", 1200, "time-travel-copy");
    } catch (_error) {
      globalThis.prompt?.("Copy path", path);
    }
  },
};

export const store = createStore("timeTravel", model);
