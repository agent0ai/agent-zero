import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getNamespacedClient } from "/js/websocket.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";
import { open as openSurface } from "/js/surfaces.js";

const officeSocket = getNamespacedClient("/ws");
officeSocket.addHandlers(["ws_webui"]);

const SAVE_MESSAGE_MS = 1800;
const INPUT_PUSH_DELAY_MS = 650;
const MAX_HISTORY = 80;
const DESKTOP_DOCUMENT_EXTENSIONS = new Set(["odt", "ods", "odp", "docx", "xlsx", "pptx"]);

function currentContextId() {
  try {
    return globalThis.getContext?.() || "";
  } catch {
    return "";
  }
}

function basename(path = "") {
  const value = String(path || "").split("?")[0].split("#")[0];
  return value.split("/").filter(Boolean).pop() || "Untitled";
}

function extensionOf(path = "") {
  const name = basename(path).toLowerCase();
  const index = name.lastIndexOf(".");
  return index >= 0 ? name.slice(index + 1) : "";
}

function parentPath(path = "") {
  const normalized = String(path || "").split("?")[0].split("#")[0].replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  if (index <= 0) return "/";
  return normalized.slice(0, index);
}

function uniqueTabId(session = {}) {
  return String(session.file_id || session.session_id || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`);
}

function editorContainsFocus(element) {
  const active = document.activeElement;
  return Boolean(element && active && (element === active || element.contains(active)));
}

function placeCaretAtEnd(element) {
  if (!element) return;
  if (element.tagName === "TEXTAREA" || element.tagName === "INPUT") {
    const length = element.value?.length || 0;
    element.selectionStart = length;
    element.selectionEnd = length;
    return;
  }
  const selection = globalThis.getSelection?.();
  const range = document.createRange?.();
  if (!selection || !range) return;
  range.selectNodeContents(element);
  range.collapse(false);
  selection.removeAllRanges();
  selection.addRange(range);
}

function normalizeDocument(doc = {}) {
  const path = doc.path || "";
  const extension = String(doc.extension || extensionOf(path)).toLowerCase();
  return {
    ...doc,
    extension,
    title: doc.title || doc.basename || basename(path),
    basename: doc.basename || basename(path),
    path,
  };
}

function normalizeSession(payload = {}) {
  const document = normalizeDocument(payload.document || payload);
  return {
    ...payload,
    document,
    extension: String(payload.extension || document.extension || "").toLowerCase(),
    file_id: payload.file_id || document.file_id || "",
    path: document.path || payload.path || "",
    title: payload.title || document.title || document.basename || basename(document.path),
    tab_id: uniqueTabId(payload),
    text: String(payload.text || ""),
    dirty: false,
  };
}

function documentLabel(document = {}) {
  return document.title || document.basename || basename(document.path);
}

async function callOffice(action, payload = {}) {
  return await callJsonApi("/plugins/_office/office_session", {
    action,
    ctxid: currentContextId(),
    ...payload,
  });
}

async function requestOffice(eventType, payload = {}, timeoutMs = 5000) {
  const response = await officeSocket.request(eventType, {
    ctxid: currentContextId(),
    ...payload,
  }, { timeoutMs });
  const results = Array.isArray(response?.results) ? response.results : [];
  const first = results.find((item) => item?.ok === true && isOfficeSocketData(item?.data))
    || results.find((item) => item?.ok === true);
  if (!first) {
    const error = results.find((item) => item?.error)?.error;
    throw new Error(error?.error || error?.code || `${eventType} failed`);
  }
  if (first.data?.office_error) {
    const error = first.data.office_error;
    throw new Error(error.error || error.code || `${eventType} failed`);
  }
  return first.data || {};
}

function isOfficeSocketData(data) {
  if (!data || typeof data !== "object") return false;
  return (
    Object.prototype.hasOwnProperty.call(data, "office_error")
    || Object.prototype.hasOwnProperty.call(data, "ok")
    || Object.prototype.hasOwnProperty.call(data, "session_id")
    || Object.prototype.hasOwnProperty.call(data, "document")
  );
}

const model = {
  status: null,
  tabs: [],
  activeTabId: "",
  session: null,
  loading: false,
  saving: false,
  dirty: false,
  error: "",
  message: "",
  editorText: "",
  _root: null,
  _mode: "modal",
  _initialized: false,
  _saveMessageTimer: null,
  _inputTimer: null,
  _history: [],
  _historyIndex: -1,
  _pendingFocus: false,
  _pendingFocusEnd: true,
  _focusAttempts: 0,
  _headerCleanup: null,

  async init() {
    if (this._initialized) return;
    this._initialized = true;
    await this.refresh();
  },

  async onMount(element = null, options = {}) {
    await this.init();
    if (element) this._root = element;
    this._mode = options?.mode === "canvas" ? "canvas" : "modal";
    if (this._mode === "modal") this.setupDocumentModal(element);
    this.queueRender();
  },

  async onOpen(payload = {}) {
    await this.init();
    await this.refresh();
    if (payload?.path || payload?.file_id) {
      await this.openSession({
        path: payload.path || "",
        file_id: payload.file_id || "",
        refresh: payload.refresh === true,
        source: payload.source || "",
      });
    }
  },

  beforeHostHidden() {
    this.flushInput();
  },

  cleanup() {
    this.flushInput();
    this._headerCleanup?.();
    this._headerCleanup = null;
    if (this._mode === "modal") this._root = null;
  },

  async refresh() {
    try {
      const status = await callOffice("status");
      this.status = status || {};
      this.error = "";
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    }
  },

  async create(kind = "document", format = "") {
    const fmt = String(format || (kind === "spreadsheet" ? "ods" : kind === "presentation" ? "odp" : "md")).toLowerCase();
    const title = this.defaultTitle(kind, fmt);
    await this.openSession({
      action: "create",
      kind,
      format: fmt,
      title,
    });
  },

  async openFileBrowser() {
    let workdirPath = "/a0/usr/workdir";
    try {
      const response = await callJsonApi("settings_get", null);
      workdirPath = response?.settings?.workdir_path || workdirPath;
    } catch {
      try {
        const home = await callOffice("home");
        workdirPath = home?.path || workdirPath;
      } catch {
        // The file browser can still open with the static fallback.
      }
    }
    await fileBrowserStore.open(workdirPath);
  },

  async openPath(path) {
    await this.openSession({ path: String(path || "") });
  },

  async openSession(payload = {}) {
    this.loading = true;
    this.error = "";
    try {
      const response = await callOffice(payload.action || "open", payload);
      if (response?.ok === false) {
        this.error = response.error || "Document could not be opened.";
        return null;
      }
      if (response?.requires_desktop || this.isDesktopDocument(response)) {
        const document = normalizeDocument(response.document || response);
        this.setMessage(`${documentLabel(document)} is ready. Use Open in Desktop to edit it.`);
        await this.refresh();
        return response;
      }
      const session = normalizeSession(response);
      this.installSession(session);
      await this.refresh();
      return session;
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      return null;
    } finally {
      this.loading = false;
    }
  },

  installSession(session) {
    const existingIndex = this.tabs.findIndex((tab) => (
      (session.file_id && tab.file_id === session.file_id)
      || (session.path && tab.path === session.path)
    ));
    if (existingIndex >= 0) {
      this.tabs.splice(existingIndex, 1, { ...this.tabs[existingIndex], ...session, tab_id: this.tabs[existingIndex].tab_id });
      this.activeTabId = this.tabs[existingIndex].tab_id;
    } else {
      this.tabs.push(session);
      this.activeTabId = session.tab_id;
    }
    this.selectTab(this.activeTabId);
  },

  selectTab(tabId, options = {}) {
    const tab = this.tabs.find((item) => item.tab_id === tabId) || this.tabs[0] || null;
    this.session = tab;
    this.activeTabId = tab?.tab_id || "";
    this.editorText = String(tab?.text || "");
    this.dirty = Boolean(tab?.dirty);
    this.resetHistory(this.editorText);
    this.queueRender({ focus: Boolean(tab) && options.focus !== false });
  },

  ensureActiveTab() {
    if (this.session && this.tabs.some((tab) => tab.tab_id === this.session.tab_id)) return;
    if (this.tabs.length) this.selectTab(this.tabs[0].tab_id, { focus: false });
  },

  isActiveTab(tab) {
    return Boolean(tab && tab.tab_id === this.activeTabId);
  },

  async closeTab(tabId) {
    const tab = this.tabs.find((item) => item.tab_id === tabId);
    if (!tab) return;
    if (tab.dirty || (this.isActiveTab(tab) && this.dirty)) {
      const shouldSave = globalThis.confirm?.("Save changes?") ?? true;
      if (shouldSave) await this.save();
    }
    try {
      if (tab.session_id) {
        await requestOffice("office_close", { session_id: tab.session_id }, 2500).catch(() => null);
      }
      await callOffice("close", {
        session_id: tab.store_session_id || "",
        file_id: tab.file_id || "",
      });
    } catch (error) {
      console.warn("Document close skipped", error);
    }
    this.tabs = this.tabs.filter((item) => item.tab_id !== tabId);
    if (this.activeTabId === tabId) {
      this.session = null;
      this.activeTabId = "";
      this.editorText = "";
      this.dirty = false;
      this.ensureActiveTab();
    }
    this.ensureActiveTab();
    await this.refresh();
  },

  async closeActiveFile() {
    if (!this.session || this.loading) return;
    await this.closeTab(this.session.tab_id);
  },

  async save() {
    if (!this.session || this.saving || !this.isMarkdown()) return;
    this.syncEditorText();
    this.saving = true;
    this.error = "";
    try {
      let response;
      const payload = { session_id: this.session.session_id, text: this.editorText };
      try {
        response = await requestOffice("office_save", payload, 10000);
      } catch (_socketError) {
        response = await callOffice("save", payload);
      }
      if (response?.ok === false) throw new Error(response.error || "Save failed.");
      const document = normalizeDocument(response.document || this.session.document || {});
      const updated = {
        ...this.session,
        text: this.editorText,
        dirty: false,
        document,
        path: document.path || this.session.path,
        file_id: document.file_id || this.session.file_id,
        version: document.version || response.version || this.session.version,
      };
      this.replaceActiveSession(updated);
      this.dirty = false;
      this.setMessage("Saved");
      await this.refresh();
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      this.saving = false;
    }
  },

  async renameActiveFile() {
    if (!this.session || this.saving) return;
    const session = this.session;
    const path = session.path || session.document?.path || "";
    if (!path) {
      this.error = "This document does not have a file path to rename.";
      return;
    }
    const name = basename(path || session.title || "");
    const extension = extensionOf(name);
    await fileBrowserStore.openRenameModal(
      {
        name,
        path,
        is_dir: false,
        size: session.document?.size || 0,
        modified: session.document?.last_modified || "",
        type: "document",
      },
      {
        currentPath: parentPath(path),
        validateName: (newName) => {
          if (!extension) return true;
          return extensionOf(newName) === extension || `Keep the .${extension} extension for this open document.`;
        },
        performRename: async ({ path: renamedPath }) => {
          const payload = {
            file_id: session.file_id || "",
            path: renamedPath,
          };
          if (this.isMarkdown(session)) {
            this.syncEditorText();
            payload.text = this.session?.tab_id === session.tab_id ? this.editorText : session.text || "";
          }
          return await callOffice("renamed", payload);
        },
        onRenamed: async ({ path: renamedPath, response }) => {
          await this.handleActiveFileRenamed(session, renamedPath, response);
        },
      },
    );
  },

  async handleActiveFileRenamed(session, renamedPath, renameResponse = null) {
    const response = renameResponse || await callOffice("renamed", {
      file_id: session.file_id || "",
      path: renamedPath,
    });
    if (response?.ok === false) throw new Error(response.error || "Rename failed.");

    const document = normalizeDocument(response.document || session.document || {});
    const updated = {
      ...session,
      document,
      title: document.title || document.basename || basename(document.path),
      path: document.path || renamedPath,
      extension: document.extension || session.extension,
      file_id: document.file_id || session.file_id,
      version: document.version || response.version || session.version,
      text: this.session?.tab_id === session.tab_id ? this.editorText : session.text,
      dirty: false,
    };
    this.replaceSession(session, updated);
    this.dirty = false;
    this.setMessage("Renamed");
    await this.refresh();
  },

  replaceActiveSession(next) {
    if (!this.session) return;
    this.replaceSession(this.session, next);
  },

  replaceSession(previous, next) {
    this.session = next;
    const index = this.tabs.findIndex((tab) => tab.tab_id === (previous?.tab_id || next.tab_id));
    if (index >= 0) this.tabs.splice(index, 1, next);
    this.queueRender();
  },

  setMessage(value) {
    this.message = value;
    if (this._saveMessageTimer) globalThis.clearTimeout(this._saveMessageTimer);
    this._saveMessageTimer = globalThis.setTimeout(() => {
      this.message = "";
      this._saveMessageTimer = null;
    }, SAVE_MESSAGE_MS);
  },

  resetHistory(text) {
    this._history = [String(text || "")];
    this._historyIndex = 0;
  },

  pushHistory(text) {
    const value = String(text || "");
    if (this._history[this._historyIndex] === value) return;
    this._history = this._history.slice(0, this._historyIndex + 1);
    this._history.push(value);
    if (this._history.length > MAX_HISTORY) this._history.shift();
    this._historyIndex = this._history.length - 1;
  },

  undo() {
    if (this._historyIndex <= 0) return;
    this._historyIndex -= 1;
    this.applyEditorText(this._history[this._historyIndex], true);
  },

  redo() {
    if (this._historyIndex >= this._history.length - 1) return;
    this._historyIndex += 1;
    this.applyEditorText(this._history[this._historyIndex], true);
  },

  canUndo() {
    return this._historyIndex > 0;
  },

  canRedo() {
    return this._historyIndex < this._history.length - 1;
  },

  applyEditorText(text, markDirty = false) {
    this.editorText = String(text || "");
    if (this.session) {
      this.session.text = this.editorText;
      this.session.dirty = markDirty || this.session.dirty;
    }
    if (markDirty) this.markDirty();
    this.queueRender({ force: true, focus: true });
  },

  markDirty() {
    this.dirty = true;
    if (this.session) this.session.dirty = true;
  },

  onSourceInput() {
    this.markDirty();
    this.pushHistory(this.editorText);
    this.scheduleInputPush();
  },

  syncEditorText() {
    if (!this.session) return;
    this.session.text = this.editorText;
  },

  scheduleInputPush() {
    if (!this.session?.session_id || !this.isMarkdown()) return;
    if (this._inputTimer) globalThis.clearTimeout(this._inputTimer);
    this._inputTimer = globalThis.setTimeout(() => {
      this._inputTimer = null;
      this.flushInput();
    }, INPUT_PUSH_DELAY_MS);
  },

  flushInput() {
    if (!this.session?.session_id || !this.isMarkdown()) return;
    this.syncEditorText();
    requestOffice("office_input", {
      session_id: this.session.session_id,
      text: this.editorText,
    }, 3000).catch(() => {});
  },

  format(command) {
    if (!this.session || !this.isMarkdown()) return;
    const textarea = this._root?.querySelector?.("[data-office-source]");
    if (!textarea) return;
    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || start;
    const selected = this.editorText.slice(start, end);
    let replacement = selected;
    if (command === "bold") replacement = `**${selected || "text"}**`;
    if (command === "italic") replacement = `*${selected || "text"}*`;
    if (command === "list") replacement = (selected || "item").split("\n").map((line) => `- ${line.replace(/^[-*]\s+/, "")}`).join("\n");
    if (command === "numbered") replacement = (selected || "item").split("\n").map((line, index) => `${index + 1}. ${line.replace(/^\d+\.\s+/, "")}`).join("\n");
    if (command === "table") replacement = "| Column | Value |\n| --- | --- |\n|  |  |";
    if (replacement === selected) return;
    this.editorText = `${this.editorText.slice(0, start)}${replacement}${this.editorText.slice(end)}`;
    this.onSourceInput();
    globalThis.requestAnimationFrame?.(() => {
      textarea.focus();
      textarea.selectionStart = start;
      textarea.selectionEnd = start + replacement.length;
    });
  },

  queueRender(options = {}) {
    if (options.focus) {
      this._pendingFocus = true;
      this._pendingFocusEnd = options.end !== false;
      this._focusAttempts = 0;
    }
    const render = () => {
      if (this._pendingFocus && this.focusEditor({ end: this._pendingFocusEnd })) {
        this._pendingFocus = false;
        this._focusAttempts = 0;
      } else if (this._pendingFocus && this._focusAttempts < 6) {
        this._focusAttempts += 1;
        globalThis.setTimeout(render, 45);
      }
    };
    if (globalThis.requestAnimationFrame) {
      globalThis.requestAnimationFrame(render);
    } else {
      globalThis.setTimeout(render, 0);
    }
  },

  focusEditor(options = {}) {
    if (!this.session || !this.isMarkdown()) return false;
    const source = this._root?.querySelector?.("[data-office-source]");
    if (!source) return false;
    source.focus?.({ preventScroll: true });
    if (!editorContainsFocus(source)) return false;
    if (options.end !== false) placeCaretAtEnd(source);
    return true;
  },

  isMarkdown(tab = this.session) {
    const ext = String(tab?.extension || tab?.document?.extension || "").toLowerCase();
    return ext === "md";
  },

  isDesktopDocument(tab = this.session) {
    const ext = String(tab?.extension || tab?.document?.extension || "").toLowerCase();
    return DESKTOP_DOCUMENT_EXTENSIONS.has(ext);
  },

  hasActiveFile(tab = this.session) {
    return Boolean(tab && this.isMarkdown(tab));
  },

  visibleTabs() {
    return this.tabs.filter((tab) => this.hasActiveFile(tab));
  },

  defaultTitle(kind, fmt) {
    const date = new Date().toISOString().slice(0, 10);
    if (fmt === "md") return `Document ${date}`;
    if (fmt === "odt") return `Writer ${date}`;
    if (fmt === "docx") return `DOCX ${date}`;
    if (kind === "spreadsheet") return `Spreadsheet ${date}`;
    if (kind === "presentation") return `Presentation ${date}`;
    return `Document ${date}`;
  },

  tabTitle(tab = {}) {
    tab = tab || {};
    return tab.title || tab.document?.basename || basename(tab.path);
  },

  tabLabel(tab = {}) {
    tab = tab || {};
    const title = this.tabTitle(tab);
    return tab.dirty ? `${title} unsaved` : title;
  },

  tabIcon(tab = {}) {
    tab = tab || {};
    const ext = String(tab.extension || tab.document?.extension || "").toLowerCase();
    if (ext === "md") return "article";
    if (ext === "odt" || ext === "docx") return "description";
    if (ext === "ods" || ext === "xlsx") return "table_chart";
    if (ext === "odp" || ext === "pptx") return "co_present";
    return "draft";
  },

  async openActiveInDesktop() {
    const target = this.session?.document || this.session;
    if (!target?.path && !target?.file_id) return;
    await openSurface("desktop", {
      path: target.path || "",
      file_id: target.file_id || "",
      refresh: true,
      source: "office-explicit-action",
    });
  },

  async runNewMenuAction(action = "") {
    const normalized = String(action || "").trim().toLowerCase();
    if (normalized === "open") return await this.openFileBrowser();
    if (normalized === "markdown") return await this.create("document", "md");
    if (normalized === "writer") return await this.create("document", "odt");
    if (normalized === "spreadsheet") return await this.create("spreadsheet", "ods");
    if (normalized === "presentation") return await this.create("presentation", "odp");
    return null;
  },

  installHeaderNewMenu(header = null) {
    if (!header || header.querySelector(".office-header-actions")) return () => {};

    const root = document.createElement("div");
    root.className = "office-header-actions";
    root.innerHTML = `
      <button type="button" class="office-header-new-button" aria-haspopup="menu" aria-expanded="false">
        <span class="material-symbols-outlined" aria-hidden="true">add</span>
        <span>New</span>
        <span class="material-symbols-outlined office-new-chevron" aria-hidden="true">expand_more</span>
      </button>
      <div class="office-new-menu" role="menu" hidden>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="open">
          <span class="material-symbols-outlined" aria-hidden="true">folder_open</span>
          <span>Open</span>
        </button>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="markdown">
          <span class="material-symbols-outlined" aria-hidden="true">article</span>
          <span>Markdown</span>
        </button>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="writer">
          <span class="material-symbols-outlined" aria-hidden="true">description</span>
          <span>Writer</span>
        </button>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="spreadsheet">
          <span class="material-symbols-outlined" aria-hidden="true">table_chart</span>
          <span>Spreadsheet</span>
        </button>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="presentation">
          <span class="material-symbols-outlined" aria-hidden="true">co_present</span>
          <span>Presentation</span>
        </button>
      </div>
    `;

    const button = root.querySelector(".office-header-new-button");
    const menu = root.querySelector(".office-new-menu");
    const setOpen = (open) => {
      root.classList.toggle("is-open", open);
      button?.setAttribute("aria-expanded", open.toString());
      if (menu) menu.hidden = !open;
    };
    const onButtonClick = (event) => {
      event.preventDefault();
      event.stopPropagation();
      setOpen(!root.classList.contains("is-open"));
    };
    const onDocumentClick = (event) => {
      if (!root.contains(event.target)) setOpen(false);
    };
    const onDocumentKeydown = (event) => {
      if (event.key === "Escape") setOpen(false);
    };

    button?.addEventListener("click", onButtonClick);
    for (const item of root.querySelectorAll("[data-office-new-action]")) {
      item.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();
        const action = event.currentTarget?.dataset?.officeNewAction || "";
        setOpen(false);
        await this.runNewMenuAction(action);
      });
    }
    document.addEventListener("click", onDocumentClick);
    document.addEventListener("keydown", onDocumentKeydown);

    const firstHeaderAction = header.querySelector(".modal-close");
    if (firstHeaderAction) {
      firstHeaderAction.insertAdjacentElement("beforebegin", root);
    } else {
      header.appendChild(root);
    }

    setOpen(false);
    return () => {
      button?.removeEventListener("click", onButtonClick);
      document.removeEventListener("click", onDocumentClick);
      document.removeEventListener("keydown", onDocumentKeydown);
      root.remove();
    };
  },

  setupDocumentModal(element = null) {
    const root = element || document.querySelector(".office-panel");
    const inner = root?.closest?.(".modal-inner");
    const header = inner?.querySelector?.(".modal-header");
    if (!inner || !header || inner.dataset.officeModalReady === "1") return;
    inner.dataset.officeModalReady = "1";
    inner.classList.add("office-modal");
    this._headerCleanup = () => {
      delete inner.dataset.officeModalReady;
      inner.classList.remove("office-modal");
    };
    const menuCleanup = this.installHeaderNewMenu(header);
    const previousCleanup = this._headerCleanup;
    this._headerCleanup = () => {
      menuCleanup?.();
      previousCleanup?.();
    };
  },
};

export const store = createStore("office", model);
