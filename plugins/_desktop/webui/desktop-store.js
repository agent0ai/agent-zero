import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getNamespacedClient } from "/js/websocket.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";
import { handleUrlIntent } from "/js/surfaces.js";

const officeSocket = getNamespacedClient("/ws");
officeSocket.addHandlers(["ws_webui"]);

const SAVE_MESSAGE_MS = 1800;
const INPUT_PUSH_DELAY_MS = 650;
const DESKTOP_HEARTBEAT_MS = 3500;
const DESKTOP_RESIZE_DELAY_MS = 80;
const DESKTOP_START_MESSAGE = "Starting Agent Zero Desktop environment";
const DESKTOP_RUNTIME_INSTALL_MESSAGE = "Installing Agent Zero Desktop runtime dependencies. This can take a few minutes after an update.";
const DESKTOP_RUNTIME_INSTALL_POLL_MS = 4000;
const DESKTOP_RUNTIME_INSTALL_TIMEOUT_MS = 10 * 60 * 1000;
const XPRA_DESKTOP_PRIME_INTERVAL_MS = 220;
const XPRA_DESKTOP_PRIME_ATTEMPTS = 120;
const SYSTEM_DESKTOP_FILE_ID = "system-desktop";
const URL_INTENT_PANEL_TIMEOUT_MS = 5000;
const DESKTOP_SHUTDOWN_STORAGE_KEY = "a0.desktop.shutdown";
const MAX_HISTORY = 80;

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

function isOfficialExtension(extension = "") {
  return ["odt", "ods", "odp", "docx", "xlsx", "pptx"].includes(String(extension || "").toLowerCase());
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

function isEditableInputTarget(target) {
  const element = target?.nodeType === 1 ? target : target?.parentElement;
  const editable = element?.closest?.("input, textarea, select, [contenteditable='true'], [contenteditable=''], [role='textbox']");
  if (!editable) return false;
  if (editable.tagName !== "INPUT") return true;
  const type = String(editable.getAttribute("type") || "text").toLowerCase();
  return !["button", "checkbox", "color", "file", "image", "radio", "range", "reset", "submit"].includes(type);
}

function normalizeModalPath(path = "") {
  return String(path || "").replace(/^\/+/, "");
}

function isModalPathOpen(path = "") {
  const normalized = normalizeModalPath(path);
  return Boolean(
    globalThis.isModalOpen?.(path)
    || globalThis.isModalOpen?.(`/${normalized}`)
    || globalThis.isModalOpen?.(normalized)
  );
}

function waitForElementByPredicate(predicate, timeoutMs = URL_INTENT_PANEL_TIMEOUT_MS) {
  const found = predicate();
  if (found) return Promise.resolve(found);
  return new Promise((resolve) => {
    const timeout = globalThis.setTimeout(() => {
      observer.disconnect();
      resolve(predicate());
    }, timeoutMs);
    const observer = new MutationObserver(() => {
      const element = predicate();
      if (!element) return;
      globalThis.clearTimeout(timeout);
      observer.disconnect();
      resolve(element);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });
}

function browserPanelForMode(mode = "modal") {
  const panels = Array.from(document.querySelectorAll(".browser-panel"));
  if (mode === "canvas") {
    return panels.find((panel) => panel.closest?.('[data-surface-id="browser"]')) || null;
  }
  return panels.find((panel) => panel.closest?.(".modal")) || null;
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

function sleep(ms) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms));
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
  const extension = String(payload.extension || document.extension || "").toLowerCase();
  return {
    ...payload,
    document,
    extension,
    file_id: payload.file_id || document.file_id || "",
    path: document.path || payload.path || "",
    title: payload.title || document.title || document.basename || basename(document.path),
    tab_id: uniqueTabId(payload),
    text: String(payload.text || ""),
    desktop: payload.desktop || null,
    desktop_session_id: payload.desktop_session_id || payload.desktop?.session_id || "",
    dirty: false,
  };
}

async function callOffice(action, payload = {}) {
  return await callJsonApi("/plugins/_office/office_session", {
    action,
    ctxid: currentContextId(),
    ...payload,
  });
}

async function callDesktop(action, payload = {}) {
  return await callJsonApi("/plugins/_desktop/desktop_session", {
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
    || Object.prototype.hasOwnProperty.call(data, "desktop")
    || Object.prototype.hasOwnProperty.call(data, "closed")
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
  _mode: "canvas",
  _saveMessageTimer: null,
  _inputTimer: null,
  _history: [],
  _historyIndex: -1,
  _pendingFocus: false,
  _pendingFocusEnd: true,
  _focusAttempts: 0,
  _floatingCleanup: null,
  _desktopHeartbeatTimer: null,
  _desktopHeartbeatSessionId: "",
  _desktopHeartbeatTabId: "",
  _desktopHeartbeatMisses: 0,
  _desktopResizeCleanup: null,
  _desktopResizeTarget: null,
  _desktopResizeTimer: null,
  _desktopResizeKey: "",
  _desktopResizePendingKey: "",
  _desktopResizeSuspended: false,
  _desktopResizePending: false,
  _desktopViewportSyncTimers: [],
  _desktopHostVisible: false,
  _desktopPrimeTimer: null,
  _desktopPrimeAttempts: 0,
  _desktopKeyboardActive: false,
  _desktopFocusInProgress: false,
  _desktopBridgeReady: false,
  _desktopKeyboardCaptureState: { ready: false, active: false, capture: false, focused: false },
  _desktopLastState: null,
  _desktopKeyboardCleanup: null,
  _desktopClipboardCleanup: null,
  _desktopStarting: null,
  _desktopUrlIntentBusy: false,
  _desktopUrlIntentQueue: [],
  _desktopFrame: null,
  _desktopFrameHost: null,
  _desktopFrameLoadHandler: null,
  _desktopKeepaliveHost: null,
  _desktopIntentionalShutdown: false,

  async init(element = null) {
    this.restoreDesktopShutdownState();
    return await this.onMount(element, { mode: "canvas" });
  },

  async onMount(element = null, options = {}) {
    if (element) this._root = element;
    this._mode = options?.mode === "modal" ? "modal" : "canvas";
    if (this._mode === "modal") {
      this._desktopHostVisible = true;
      this.setupFloatingModal(element);
      await this.onOpen({ source: "modal" });
      return;
    }
    this.queueRender();
  },

  async onOpen(payload = {}) {
    this.restoreDesktopShutdownState();
    await this.refresh();
    if (payload?.path || payload?.file_id) {
      await this.openSession({
        path: payload.path || "",
        file_id: payload.file_id || "",
        refresh: payload.refresh === true,
        source: payload.source || "",
      });
    } else if (this._desktopIntentionalShutdown) {
      this.session = null;
      this.activeTabId = "";
      this.editorText = "";
      this.dirty = false;
    } else {
      await this.ensureDesktopSession({ select: !this.session });
    }
    this.restoreDesktopFrames();
    this.requestDesktopViewportSync({ force: true });
  },

  beforeHostHidden(options = {}) {
    this._desktopHostVisible = false;
    this.flushInput();
    this.clearDesktopViewportSyncTimers();
    this.stopDesktopMonitor();
    this.stopDesktopKeyboardBridge();
    this.stopDesktopClipboardBridge();
    this.unloadDesktopFrames();
  },

  cleanup() {
    this.flushInput();
    this.stopDesktopMonitor();
    this.stopDesktopResizeObserver();
    this.clearDesktopViewportSyncTimers();
    this.stopXpraDesktopPrime();
    this.stopDesktopKeyboardBridge();
    this.stopDesktopClipboardBridge();
    if (!this._desktopIntentionalShutdown) this.moveDesktopFrameToKeepalive();
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    if (this._mode === "modal") this._root = null;
  },

  async refresh() {
    try {
      const status = await callDesktop("status");
      this.status = status || {};
      this.error = "";
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    }
  },

  restoreDesktopShutdownState() {
    try {
      this._desktopIntentionalShutdown = localStorage.getItem(DESKTOP_SHUTDOWN_STORAGE_KEY) === "1";
    } catch {
      this._desktopIntentionalShutdown = Boolean(this._desktopIntentionalShutdown);
    }
  },

  persistDesktopShutdownState() {
    try {
      if (this._desktopIntentionalShutdown) {
        localStorage.setItem(DESKTOP_SHUTDOWN_STORAGE_KEY, "1");
      } else {
        localStorage.removeItem(DESKTOP_SHUTDOWN_STORAGE_KEY);
      }
    } catch {
      // Shutdown state is still correct for this page even without storage.
    }
  },

  setDesktopIntentionalShutdown(value) {
    this._desktopIntentionalShutdown = Boolean(value);
    this.persistDesktopShutdownState();
  },

  isDesktopShutdown() {
    return Boolean(this._desktopIntentionalShutdown);
  },

  shouldShowDesktopEmptyState() {
    return Boolean(this._desktopIntentionalShutdown && !this.session);
  },

  async restartDesktopSession() {
    this.error = "";
    const session = await this.ensureDesktopSession({
      force: true,
      restart: true,
      select: true,
      message: "Restarting Agent Zero Desktop environment",
    });
    if (!session) {
      this.setDesktopIntentionalShutdown(true);
      return null;
    }
    this.restoreDesktopFrames();
    this.requestDesktopViewportSync({ force: true });
    return session;
  },

  async shutdownDesktop(options = {}) {
    this.loading = options.progress !== false;
    this.message = this.loading ? "Shutting down Desktop" : this.message;
    this.error = "";
    try {
      const response = await callDesktop("shutdown", {
        save_first: options.saveFirst !== false,
        source: options.source || "ui",
      });
      await this.handleIntentionalDesktopShutdown(response);
      return response;
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      return null;
    } finally {
      if (options.progress !== false) {
        this.loading = false;
        if (this.message === "Shutting down Desktop") this.message = "";
      }
    }
  },

  async handleIntentionalDesktopShutdown(response = {}) {
    this.setDesktopIntentionalShutdown(true);
    this.stopDesktopMonitor();
    this.stopDesktopResizeObserver();
    this.clearDesktopViewportSyncTimers();
    this.stopXpraDesktopPrime();
    this.stopDesktopKeyboardBridge();
    this.stopDesktopClipboardBridge();
    this.destroyDesktopFrame();
    const activeTabId = this.activeTabId;
    this.tabs = this.tabs.filter((tab) => !this.isDesktopSession(tab) && !this.hasOfficialOffice(tab));
    if (!this.tabs.some((tab) => tab.tab_id === activeTabId)) {
      this.session = null;
      this.activeTabId = "";
      this.editorText = "";
      this.dirty = false;
      this.resetHistory("");
    }
    this._desktopStarting = null;
    this._desktopHeartbeatMisses = 0;
    this.message = response?.source === "tray" ? "Desktop shut down from system tray" : "Desktop is shut down";
    await this.refresh();
  },

  async ensureDesktopSession(options = {}) {
    if (this._desktopIntentionalShutdown && options.restart !== true) {
      return null;
    }
    if (options.restart === true) {
      this.setDesktopIntentionalShutdown(false);
      this.destroyDesktopFrame();
    }
    const existing = this.tabs.find((tab) => this.isDesktopSession(tab));
    if (existing && !options.force) {
      if (options.select) this.selectTab(existing.tab_id, { focus: false });
      this.updateDesktopMonitor();
      return existing;
    }
    const showProgress = options.progress !== false;
    const progressMessage = String(options.message || DESKTOP_START_MESSAGE);
    if (this._desktopStarting) {
      if (showProgress) {
        this.loading = true;
        this.message = progressMessage;
      }
      return await this._desktopStarting;
    }

    this._desktopStarting = (async () => {
      try {
        if (showProgress) {
          this.loading = true;
          this.message = progressMessage;
          this.error = "";
        }
        const response = await this.openDesktopWhenRuntimeReady(showProgress);
        if (response?.ok === false) throw new Error(response.error || "Desktop session could not be opened.");
        this.setDesktopIntentionalShutdown(false);
        const session = normalizeSession(response);
        const existingIndex = this.tabs.findIndex((tab) => this.isDesktopSession(tab));
        let desktopTabId = session.tab_id;
        if (existingIndex >= 0) {
          desktopTabId = this.tabs[existingIndex].tab_id;
          this.tabs.splice(existingIndex, 1, { ...this.tabs[existingIndex], ...session, tab_id: desktopTabId });
        } else {
          this.tabs.unshift(session);
        }
        this.tabs = this.tabs.map((tab) => (
          this.hasOfficialOffice(tab)
            ? {
              ...tab,
              desktop: session.desktop,
              desktop_session_id: session.desktop_session_id,
              session_id: this.isDesktopSession(tab) ? session.session_id : tab.session_id,
            }
            : tab
        ));
        if (options.select || !this.session) {
          this.selectTab(desktopTabId, { focus: false });
        } else {
          this.updateDesktopMonitor();
        }
        this.restoreDesktopFrames();
        return { ...session, tab_id: desktopTabId };
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error);
        return null;
      } finally {
        if (showProgress) {
          this.loading = false;
          if (this.message === progressMessage || this.message === DESKTOP_RUNTIME_INSTALL_MESSAGE) this.message = "";
        }
        this._desktopStarting = null;
      }
    })();
    return await this._desktopStarting;
  },

  async openDesktopWhenRuntimeReady(showProgress = true) {
    const startedAt = Date.now();
    let response = await callDesktop("desktop");
    while (response?.ok === false && this.isDesktopRuntimeInstalling(response)) {
      if (showProgress) {
        this.loading = true;
        this.error = "";
        this.message = this.desktopRuntimeInstallMessage(response);
      }
      if (Date.now() - startedAt > DESKTOP_RUNTIME_INSTALL_TIMEOUT_MS) {
        return {
          ...response,
          error: "Agent Zero Desktop runtime installation is still running. Please try again in a moment.",
        };
      }
      await sleep(DESKTOP_RUNTIME_INSTALL_POLL_MS);
      response = await callDesktop("desktop");
    }
    return response;
  },

  isDesktopRuntimeInstalling(response = {}) {
    const status = response?.status || response?.desktop?.status || response?.libreoffice?.desktop || {};
    return Boolean(status.installing || status.state === "installing" || status.preparation?.preparing);
  },

  desktopRuntimeInstallMessage(response = {}) {
    const status = response?.status || response?.desktop?.status || response?.libreoffice?.desktop || {};
    return String(status.message || DESKTOP_RUNTIME_INSTALL_MESSAGE);
  },

  async create(kind = "document", format = "") {
    const fmt = String(format || (kind === "spreadsheet" ? "ods" : kind === "presentation" ? "odp" : "md")).toLowerCase();
    const title = this.defaultTitle(kind, fmt);
    this.loading = true;
    this.error = "";
    try {
      const response = await callOffice("create", {
        kind,
        format: fmt,
        title,
        open_in_desktop: isOfficialExtension(fmt),
      });
      if (response?.ok === false) {
        this.error = response.error || "Document could not be created.";
        return null;
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
      const response = await callDesktop("open_document", payload);
      if (response?.ok === false) {
        this.error = response.error || "Document could not be opened.";
        return null;
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
    if (this.isDesktopOfficeDocument(session)) {
      this.installDesktopDocumentSession(session);
      return;
    }
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

  installDesktopDocumentSession(session) {
    this.setDesktopIntentionalShutdown(false);
    this.tabs = this.tabs.filter((tab) => !this.isDesktopOfficeDocument(tab));
    let desktopTab = this.tabs.find((tab) => this.isDesktopSession(tab));
    if (!desktopTab) {
      desktopTab = {
        ...session,
        tab_id: SYSTEM_DESKTOP_FILE_ID,
        file_id: SYSTEM_DESKTOP_FILE_ID,
        extension: "desktop",
        title: "Desktop",
        path: session.desktop?.desktop_path || "/desktop/session",
        mode: "desktop",
        document: {
          file_id: SYSTEM_DESKTOP_FILE_ID,
          path: session.desktop?.desktop_path || "/desktop/session",
          basename: "Desktop",
          title: "Desktop",
          extension: "desktop",
        },
        dirty: false,
      };
      this.tabs.unshift(desktopTab);
    }
    const documentSession = { ...session, tab_id: session.tab_id || uniqueTabId(session) };
    const existingIndex = this.tabs.findIndex((tab) => (
      (documentSession.file_id && tab.file_id === documentSession.file_id)
      || (documentSession.path && tab.path === documentSession.path)
    ));
    if (existingIndex >= 0) {
      this.tabs.splice(existingIndex, 1, documentSession);
    } else {
      this.tabs.push(documentSession);
    }
    this.session = documentSession;
    this.activeTabId = documentSession.tab_id;
    this.editorText = "";
    this.dirty = false;
    this.resetHistory("");
    this.queueRender({ focus: true });
    this.restoreDesktopFrames();
    this.requestDesktopViewportSync({ force: true });
    this.updateDesktopMonitor();
  },

  selectTab(tabId, options = {}) {
    const tab = this.tabs.find((item) => item.tab_id === tabId) || this.tabs[0] || null;
    if (this.hasOfficialOffice(this.session) && !this.hasOfficialOffice(tab)) {
      this.moveDesktopFrameToKeepalive();
    }
    this.session = tab;
    this.activeTabId = tab?.tab_id || "";
    this.editorText = String(tab?.text || "");
    this.dirty = Boolean(tab?.dirty);
    this.resetHistory(this.editorText);
    this.queueRender({ focus: Boolean(tab) && options.focus !== false });
    if (this.hasOfficialOffice(tab)) {
      this.restoreDesktopFrames();
      this.requestDesktopViewportSync({ force: true });
    }
    this.updateDesktopMonitor();
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
    if (this.isDesktopSession(tab)) {
      this.selectTab(tab.tab_id, { focus: false });
      return;
    }
    if (!this.hasOfficialOffice(tab) && (tab.dirty || (this.isActiveTab(tab) && this.dirty))) {
      const shouldSave = globalThis.confirm?.("Save changes?") ?? true;
      if (shouldSave) await this.save();
    }
    try {
      if (this.hasOfficialOffice(tab)) {
        await callDesktop("save", {
          desktop_session_id: tab.desktop_session_id || tab.session_id,
          file_id: tab.file_id || "",
        }).catch(() => null);
      } else if (tab.session_id) {
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
    this.updateDesktopMonitor();
    this.ensureActiveTab();
    await this.refresh();
  },

  async closeActiveFile() {
    if (!this.session || this.isDesktopSession() || this.loading) return;
    await this.closeTab(this.session.tab_id);
  },

  async save() {
    if (!this.session || this.saving) return;
    if (this.isDesktopSession()) return;
    if (this.hasOfficialOffice()) {
      this.saving = true;
      this.error = "";
      try {
        const response = await callDesktop("save", {
          desktop_session_id: this.session.desktop_session_id || this.session.session_id,
          file_id: this.session.file_id || "",
        });
        if (response?.ok === false) throw new Error(response.error || "Save failed.");
        const document = normalizeDocument(response.document || this.session.document || {});
        const updated = {
          ...this.session,
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
      return;
    }
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
    if (!this.session || this.isDesktopSession() || this.saving) return;

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
      desktop: response.desktop?.desktop || session.desktop,
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
    this.updateDesktopMonitor();
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
    if (this.hasOfficialOffice()) return;
    this.session.text = this.editorText;
  },

  scheduleInputPush() {
    if (!this.session?.session_id) return;
    if (this._inputTimer) globalThis.clearTimeout(this._inputTimer);
    this._inputTimer = globalThis.setTimeout(() => {
      this._inputTimer = null;
      this.flushInput();
    }, INPUT_PUSH_DELAY_MS);
  },

  flushInput() {
    if (!this.session?.session_id) return;
    if (this.hasOfficialOffice()) return;
    this.syncEditorText();
    requestOffice("office_input", {
      session_id: this.session.session_id,
      text: this.editorText,
    }, 3000).catch(() => {});
  },

  format(command) {
    if (!this.session) return;
    if (!this.isMarkdown()) return;
    this.applySourceFormat(command);
  },

  applySourceFormat(command) {
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
    const force = Boolean(options.force);
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
    if (!this.session) return false;
    if (this.hasOfficialOffice()) {
      return this.focusDesktopFrame(this.desktopFrame(), { arm: true });
    }
    const source = this._root?.querySelector?.("[data-office-source]");
    if (!this.isMarkdown() || !source) return false;
    source.focus?.({ preventScroll: true });
    if (!editorContainsFocus(source)) return false;
    if (options.end !== false) placeCaretAtEnd(source);
    return true;
  },

  isMarkdown(tab = this.session) {
    const ext = String(tab?.extension || tab?.document?.extension || "").toLowerCase();
    return ext === "md";
  },

  isBinaryOffice(tab = this.session) {
    const ext = String(tab?.extension || tab?.document?.extension || "").toLowerCase();
    return ["odt", "ods", "odp", "docx", "xlsx", "pptx"].includes(ext);
  },

  hasOfficialOffice(tab = this.session) {
    return Boolean(tab?.desktop?.available && tab.desktop.url);
  },

  isDesktopSession(tab = this.session) {
    return Boolean(
      tab
      && (
        tab.file_id === SYSTEM_DESKTOP_FILE_ID
        || tab.extension === "desktop"
        || tab.mode === "desktop"
      )
    );
  },

  isDesktopOfficeDocument(tab = this.session) {
    return Boolean(tab && this.hasOfficialOffice(tab) && !this.isDesktopSession(tab) && this.isBinaryOffice(tab));
  },

  hasActiveFile(tab = this.session) {
    return Boolean(tab && !this.isDesktopSession(tab) && (this.isMarkdown(tab) || this.isDesktopOfficeDocument(tab)));
  },

  isVisibleOfficeTab(tab = {}) {
    return Boolean(this.hasActiveFile(tab));
  },

  visibleTabs() {
    return this.tabs.filter((tab) => this.isVisibleOfficeTab(tab));
  },

  officialOfficeUrl(tab = this.session) {
    const url = tab?.desktop?.url || "";
    if (!url) return "";
    try {
      const parsed = new URL(url, window.location.href);
      const secureContext = globalThis.isSecureContext === true;
      parsed.searchParams.set("offscreen", secureContext ? "true" : "false");
      parsed.searchParams.set("clipboard_poll", secureContext ? "true" : "false");
      if (parsed.origin === window.location.origin) return `${parsed.pathname}${parsed.search}${parsed.hash}`;
      return parsed.href;
    } catch {
      return url;
    }
  },

  isDesktopHostVisible() {
    if (this._mode === "modal") return true;
    const surface = this._root?.closest?.('[data-surface-id="desktop"]');
    return Boolean(surface?.classList?.contains("is-mounted") || surface?.classList?.contains("is-active"));
  },

  setDesktopHostVisible(visible) {
    const next = Boolean(visible);
    if (!next && this._mode === "modal") return;
    if (this._desktopHostVisible === next) return;
    this._desktopHostVisible = next;
    if (next) {
      this.afterDesktopHostShown({ source: "canvas-visibility" });
    } else {
      this.beforeHostHidden({ reason: "hidden" });
    }
  },

  desktopFrames() {
    const frames = [];
    if (this._desktopFrame) frames.push(this._desktopFrame);
    for (const frame of Array.from(document.querySelectorAll("[data-office-desktop-frame]"))) {
      if (!frames.includes(frame)) frames.push(frame);
    }
    return frames;
  },

  isUsableDesktopFrame(frame) {
    if (!frame?.contentWindow) return false;
    const rect = frame.getBoundingClientRect?.();
    return Boolean(rect && rect.width >= 120 && rect.height >= 80);
  },

  desktopFrame(preferred = null) {
    if (this.isUsableDesktopFrame(preferred)) return preferred;
    const rootFrame = this._root?.querySelector?.("[data-office-desktop-frame]");
    if (this.isUsableDesktopFrame(rootFrame)) return rootFrame;
    const frames = this.desktopFrames();
    return frames
      .filter((frame) => this.isUsableDesktopFrame(frame))
      .sort((left, right) => {
        const leftRect = left.getBoundingClientRect();
        const rightRect = right.getBoundingClientRect();
        return (rightRect.width * rightRect.height) - (leftRect.width * leftRect.height);
      })[0] || null;
  },

  isUsableDesktopHost(host) {
    if (!host?.appendChild) return false;
    const rect = host.getBoundingClientRect?.();
    return Boolean(rect && rect.width >= 120 && rect.height >= 80);
  },

  desktopHost(preferred = null) {
    if (preferred?.matches?.("[data-office-desktop-host]")) return preferred;
    const rootHost = this._root?.querySelector?.("[data-office-desktop-host]");
    if (this.isUsableDesktopHost(rootHost)) return rootHost;
    const hosts = Array.from(document.querySelectorAll("[data-office-desktop-host]"));
    return hosts
      .filter((host) => this.isUsableDesktopHost(host))
      .sort((left, right) => {
        const leftRect = left.getBoundingClientRect();
        const rightRect = right.getBoundingClientRect();
        return (rightRect.width * rightRect.height) - (leftRect.width * leftRect.height);
      })[0] || rootHost || hosts[0] || null;
  },

  ensureDesktopKeepaliveHost() {
    if (this._desktopKeepaliveHost?.isConnected) return this._desktopKeepaliveHost;
    const host = document.createElement("div");
    host.className = "office-desktop-keepalive";
    host.dataset.officeDesktopKeepalive = "true";
    Object.assign(host.style, {
      position: "fixed",
      left: "-10000px",
      top: "-10000px",
      width: "720px",
      height: "480px",
      overflow: "hidden",
      pointerEvents: "none",
      visibility: "hidden",
    });
    document.body?.appendChild(host);
    this._desktopKeepaliveHost = host;
    return host;
  },

  rememberDesktopFrameSize() {
    const frame = this._desktopFrame;
    const rect = frame?.getBoundingClientRect?.();
    const hostRect = this._desktopFrameHost?.getBoundingClientRect?.();
    const width = Math.round(rect?.width || hostRect?.width || 720);
    const height = Math.round(rect?.height || hostRect?.height || 480);
    const keepalive = this.ensureDesktopKeepaliveHost();
    keepalive.style.width = `${Math.max(320, width)}px`;
    keepalive.style.height = `${Math.max(220, height)}px`;
    return keepalive;
  },

  ensureDesktopFrame() {
    if (this._desktopFrame) return this._desktopFrame;
    const frame = document.createElement("iframe");
    frame.className = "office-desktop-frame";
    frame.dataset.officeDesktopFrame = "true";
    frame.dataset.officePersistentDesktopFrame = "true";
    frame.setAttribute("tabindex", "0");
    frame.setAttribute("aria-label", "Desktop");
    frame.setAttribute("allow", "clipboard-read; clipboard-write; autoplay");
    this._desktopFrameLoadHandler = (event) => this.onDesktopFrameLoaded(event);
    frame.addEventListener("load", this._desktopFrameLoadHandler);
    this._desktopFrame = frame;
    return frame;
  },

  desktopFrameSrcMatches(frame, url) {
    const current = frame?.getAttribute?.("src") || frame?.src || "";
    if (!current && !url) return true;
    try {
      return new URL(current, window.location.href).href === new URL(url, window.location.href).href;
    } catch {
      return current === url;
    }
  },

  attachDesktopFrame(host = null) {
    if (!this.hasOfficialOffice()) return false;
    const target = this.desktopHost(host);
    if (!target) return false;
    const frame = this.ensureDesktopFrame();
    if (frame.parentElement !== target) {
      frame.parentElement?.removeAttribute?.("data-office-desktop-attached");
      target.appendChild(frame);
    }
    target.dataset.officeDesktopAttached = "true";
    if (this._desktopFrameHost !== target) this._desktopFrameHost = target;
    const url = this.officialOfficeUrl();
    if (url && !this.desktopFrameSrcMatches(frame, url)) {
      frame.setAttribute("src", url);
    }
    return true;
  },

  mountDesktopFrameHost(host = null) {
    const attached = this.attachDesktopFrame(host);
    if (attached && this.isDesktopHostVisible()) {
      this.requestDesktopViewportSync({ force: true, frame: this._desktopFrame, followup: true });
    }
    return attached;
  },

  moveDesktopFrameToKeepalive() {
    const frame = this._desktopFrame;
    if (!frame) return false;
    const keepalive = this.rememberDesktopFrameSize();
    if (frame.parentElement !== keepalive) {
      frame.parentElement?.removeAttribute?.("data-office-desktop-attached");
      keepalive.appendChild(frame);
    }
    this._desktopFrameHost = keepalive;
    this._desktopKeyboardActive = false;
    this.updateDesktopKeyboardCaptureState(frame);
    return true;
  },

  destroyDesktopFrame() {
    const frame = this._desktopFrame;
    if (!frame) return;
    if (this._desktopFrameLoadHandler) {
      frame.removeEventListener("load", this._desktopFrameLoadHandler);
    }
    frame.setAttribute("src", "about:blank");
    frame.remove();
    this._desktopFrame = null;
    this._desktopFrameHost = null;
    this._desktopFrameLoadHandler = null;
    this._desktopBridgeReady = false;
    this.updateDesktopKeyboardCaptureState();
    this._desktopKeepaliveHost?.remove?.();
    this._desktopKeepaliveHost = null;
  },

  unloadDesktopFrames() {
    this.stopDesktopResizeObserver();
    this.stopXpraDesktopPrime();
    this.moveDesktopFrameToKeepalive();
  },

  restoreDesktopFrames() {
    if (!this.isDesktopHostVisible()) return;
    this.attachDesktopFrame();
  },

  afterDesktopHostShown() {
    if (!this.hasOfficialOffice()) return;
    this._desktopHostVisible = true;
    this._desktopResizeKey = "";
    this._desktopResizePendingKey = "";
    this._desktopResizeSuspended = false;
    this._desktopResizePending = false;
    this.restoreDesktopFrames();
    this.requestDesktopViewportSync({ force: true, frame: this.desktopFrame() });
  },

  beforeDesktopHostHandoff() {
    this.stopDesktopResizeObserver();
    this.clearDesktopViewportSyncTimers();
    this.stopXpraDesktopPrime();
    this._desktopResizeKey = "";
    this._desktopResizePendingKey = "";
    this._desktopResizeSuspended = true;
    this._desktopResizePending = true;
  },

  cancelDesktopHostHandoff() {
    this._desktopResizeSuspended = false;
    this._desktopResizePending = false;
    this.requestDesktopViewportSync({ force: true, frame: this.desktopFrame() });
  },

  onDesktopFrameLoaded(event = null) {
    if (event?.target?.getAttribute?.("src") === "about:blank") return;
    if (!this.isDesktopHostVisible()) return;
    this.error = "";
    this.queueDesktopFrameFocus(event?.target || null);
    this.requestDesktopViewportSync({ force: true, frame: event?.target || null });
  },

  queueDesktopFrameFocus(frame = null) {
    for (const delay of [0, 80, 260]) {
      globalThis.setTimeout(() => {
        if (!this.hasOfficialOffice()) return;
        if (isEditableInputTarget(document.activeElement)) return;
        this.focusDesktopFrame(frame || this.desktopFrame(), { arm: true });
      }, delay);
    }
  },

  focusDesktopFrame(frame = null, options = {}) {
    if (this._desktopFocusInProgress) return false;
    const target = this.desktopFrame(frame);
    if (!target) return false;
    if (options.arm !== false) this._desktopKeyboardActive = true;
    this._desktopFocusInProgress = true;
    try {
      target.setAttribute("tabindex", "0");
      target.focus?.({ preventScroll: true });
      target.contentWindow?.focus?.();
      if (target.contentDocument?.body && !target.contentDocument.body.hasAttribute("tabindex")) {
        target.contentDocument.body.tabIndex = -1;
      }
      target.contentDocument?.body?.focus?.({ preventScroll: true });
      if (target.contentWindow?.client) target.contentWindow.client.capture_keyboard = true;
    } catch {
      target.focus?.({ preventScroll: true });
    } finally {
      this._desktopFocusInProgress = false;
    }
    const focused = Boolean(document.activeElement === target || target.contentDocument?.hasFocus?.());
    this.updateDesktopKeyboardCaptureState(target);
    return focused;
  },

  updateDesktopMonitor() {
    if (!this.hasOfficialOffice() || !this.isDesktopHostVisible()) {
      this.stopDesktopMonitor();
      this.stopDesktopResizeObserver();
      this._desktopKeyboardActive = false;
      this._desktopBridgeReady = false;
      this.updateDesktopKeyboardCaptureState();
      return;
    }
    const sessionId = this.session?.desktop_session_id || this.session?.session_id || "";
    const tabId = this.session?.tab_id || "";
    if (
      sessionId
      && tabId
      && this._desktopHeartbeatTimer
      && this._desktopHeartbeatSessionId === sessionId
      && this._desktopHeartbeatTabId === tabId
    ) return;
    this.startDesktopMonitor();
    this.startDesktopResizeObserver();
  },

  startDesktopResizeObserver() {
    if (!this.hasOfficialOffice() || !this.isDesktopHostVisible()) {
      this.stopDesktopResizeObserver();
      return;
    }
    const frame = this.desktopFrame();
    const target = frame?.parentElement || frame;
    if (!target) {
      this.stopDesktopResizeObserver();
      return;
    }
    if (this._desktopResizeCleanup && this._desktopResizeTarget === target) return;
    this.stopDesktopResizeObserver();

    const resize = () => this.queueDesktopResize();
    const resizeStart = () => this.suspendDesktopResize();
    const resizeEnd = () => this.resumeDesktopResize();
    const cleanup = [];
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(resize);
      observer.observe(target);
      cleanup.push(() => observer.disconnect());
    }
    globalThis.addEventListener?.("resize", resize);
    cleanup.push(() => globalThis.removeEventListener?.("resize", resize));
    globalThis.addEventListener?.("right-canvas-resize-start", resizeStart);
    cleanup.push(() => globalThis.removeEventListener?.("right-canvas-resize-start", resizeStart));
    globalThis.addEventListener?.("right-canvas-resize-end", resizeEnd);
    cleanup.push(() => globalThis.removeEventListener?.("right-canvas-resize-end", resizeEnd));
    this._desktopResizeTarget = target;
    this._desktopResizeCleanup = () => cleanup.splice(0).reverse().forEach((entry) => entry());
    resize();
  },

  stopDesktopResizeObserver() {
    if (this._desktopResizeTimer) {
      globalThis.clearTimeout(this._desktopResizeTimer);
    }
    this._desktopResizeTimer = null;
    this._desktopResizeCleanup?.();
    this._desktopResizeCleanup = null;
    this._desktopResizeTarget = null;
    this._desktopResizeKey = "";
    this._desktopResizePendingKey = "";
    this._desktopResizeSuspended = false;
    this._desktopResizePending = false;
  },

  suspendDesktopResize() {
    this._desktopResizeSuspended = true;
    if (this._desktopResizeTimer) {
      globalThis.clearTimeout(this._desktopResizeTimer);
      this._desktopResizeTimer = null;
    }
    this._desktopResizePendingKey = "";
  },

  resumeDesktopResize() {
    const hadPendingResize = this._desktopResizePending;
    this._desktopResizeSuspended = false;
    this._desktopResizePending = false;
    if (hadPendingResize || this.hasOfficialOffice()) {
      this.queueDesktopResize({ force: true });
    }
  },

  shouldDeferDesktopResize() {
    return Boolean(
      this._desktopResizeSuspended
      || document.body?.classList?.contains("right-canvas-resizing")
      || document.querySelector?.(".modal-inner.office-modal.is-resizing")
    );
  },

  clearDesktopViewportSyncTimers() {
    for (const timer of this._desktopViewportSyncTimers.splice(0)) {
      globalThis.clearTimeout(timer);
    }
  },

  requestDesktopViewportSync(options = {}) {
    if (!this.hasOfficialOffice() || !this.isDesktopHostVisible()) return;
    if (options.force) this.clearDesktopViewportSyncTimers();
    const run = (force = false) => {
      this.syncDesktopViewport({ ...options, force });
    };
    if (globalThis.requestAnimationFrame) {
      globalThis.requestAnimationFrame(() => run(Boolean(options.force)));
    } else {
      globalThis.setTimeout(() => run(Boolean(options.force)), 0);
    }
    if (options.followup === false) return;
    const timer = globalThis.setTimeout(() => {
      this._desktopViewportSyncTimers = this._desktopViewportSyncTimers.filter((item) => item !== timer);
      run(false);
    }, options.force ? 260 : 180);
    this._desktopViewportSyncTimers.push(timer);
  },

  syncDesktopViewport(options = {}) {
    if (!this.hasOfficialOffice() || !this.isDesktopHostVisible()) return false;
    const frame = this.desktopFrame(options.frame || null);
    if (!frame) return false;
    this.startDesktopResizeObserver();
    this.primeXpraDesktopFrame({ reset: true, frame });
    this.queueDesktopResize({
      force: Boolean(options.force),
      serverResize: options.serverResize !== false,
      frame,
    });
    this.updateDesktopMonitor();
    return true;
  },

  primeXpraDesktopFrame(options = {}) {
    if (options.reset) {
      this.stopXpraDesktopPrime();
      this._desktopPrimeAttempts = 0;
    }
    if (this.applyXpraDesktopFrameMode(options.frame || null)) return;
    if (this._desktopPrimeAttempts >= XPRA_DESKTOP_PRIME_ATTEMPTS) return;
    this._desktopPrimeAttempts += 1;
    if (this._desktopPrimeTimer) globalThis.clearTimeout(this._desktopPrimeTimer);
    this._desktopPrimeTimer = globalThis.setTimeout(() => {
      this._desktopPrimeTimer = null;
      this.primeXpraDesktopFrame();
    }, XPRA_DESKTOP_PRIME_INTERVAL_MS);
  },

  stopXpraDesktopPrime() {
    if (this._desktopPrimeTimer) globalThis.clearTimeout(this._desktopPrimeTimer);
    this._desktopPrimeTimer = null;
  },

  applyXpraDesktopFrameMode(preferredFrame = null, options = {}) {
    const frame = this.desktopFrame(preferredFrame);
    const remoteWindow = frame?.contentWindow;
    if (!remoteWindow) return false;
    const requestServerResize = options.requestServerResize === true;
    const requestRefresh = options.requestRefresh !== false;
    try {
      const remoteDocument = frame.contentDocument || remoteWindow.document;
      this.installXpraDesktopFrameCss(remoteDocument);
      this.installXpraDesktopFramePatches(remoteWindow, remoteDocument);
      const client = remoteWindow.client;
      if (!client) return false;
      this.installXpraDesktopClientPatches(remoteWindow, client);
      this.installXpraDesktopCursorPatches(remoteWindow, remoteDocument, client);
      this.installXpraDesktopKeyboardBridge(frame, remoteWindow, remoteDocument, client);
      this.installXpraDesktopClipboardBridge(frame, remoteWindow, remoteDocument, client);
      const container = client.container || remoteDocument?.querySelector?.("#screen");
      if (!container) return false;

      client.server_is_desktop = true;
      client.server_resize_exact = true;
      remoteDocument?.body?.classList?.add("desktop");

      const windows = Object.values(client.id_to_window || {});
      if (!client.connected || !windows.length) return false;

      const width = Math.round(container.clientWidth || remoteWindow.innerWidth || 0);
      const height = Math.round(container.clientHeight || remoteWindow.innerHeight || 0);
      if (width > 0 && height > 0) {
        client.desktop_width = width;
        client.desktop_height = height;
      }
      if (requestServerResize && width > 0 && height > 0 && typeof client._screen_resized === "function") {
        client.desktop_width = 0;
        client.desktop_height = 0;
        client.__a0AllowScreenResize = true;
        try {
          client._screen_resized(new remoteWindow.Event("resize"));
        } finally {
          client.__a0AllowScreenResize = false;
        }
      }

      for (const xpraWindow of windows) {
        this.normalizeXpraDesktopWindow(xpraWindow, width, height);
        xpraWindow.screen_resized?.();
        this.normalizeXpraDesktopWindow(xpraWindow, width, height);
        xpraWindow.updateCSSGeometry?.();
        this.fitXpraDesktopWindowElement(xpraWindow, width, height);
        this.installXpraDesktopWheelBridge(remoteWindow, xpraWindow);
        if (requestRefresh && xpraWindow.wid != null) client.request_refresh?.(xpraWindow.wid);
      }
      this.installXpraDesktopAgentBridge(frame, remoteWindow, remoteDocument, client, container);
      return true;
    } catch (error) {
      console.warn("Xpra desktop viewport prime skipped", error);
      return false;
    }
  },

  installXpraDesktopAgentBridge(frame, remoteWindow, remoteDocument, client, container) {
    if (!frame || !remoteWindow || !remoteDocument || !client) return null;
    const store = this;
    const finite = (value, fallback = 0) => {
      const number = Number(value);
      return Number.isFinite(number) ? number : fallback;
    };
    const metrics = () => {
      const desktopWidth = Math.max(1, finite(client.desktop_width || container?.clientWidth || remoteWindow.innerWidth, 1));
      const desktopHeight = Math.max(1, finite(client.desktop_height || container?.clientHeight || remoteWindow.innerHeight, 1));
      const clientWidth = Math.max(1, finite(container?.clientWidth || remoteWindow.innerWidth, desktopWidth));
      const clientHeight = Math.max(1, finite(container?.clientHeight || remoteWindow.innerHeight, desktopHeight));
      return {
        desktopWidth,
        desktopHeight,
        clientWidth,
        clientHeight,
        scaleX: clientWidth / desktopWidth,
        scaleY: clientHeight / desktopHeight,
      };
    };
    const bridge = frame.__agentZeroDesktopBridge || {};
    Object.assign(bridge, {
      ready: true,
      state: async (options = {}) => {
        const result = await callDesktop("state", {
          include_screenshot: options.includeScreenshot === true || options.include_screenshot === true,
        });
        store._desktopLastState = result;
        return result;
      },
      focus: (options = {}) => store.focusDesktopFrame(frame, { ...options, arm: options.arm !== false }),
      requestRefresh: () => {
        for (const xpraWindow of Object.values(client.id_to_window || {})) {
          if (xpraWindow?.wid != null) client.request_refresh?.(xpraWindow.wid);
        }
        return true;
      },
      desktopToClient: (x, y) => {
        const value = metrics();
        return {
          x: Math.round(finite(x) * value.scaleX),
          y: Math.round(finite(y) * value.scaleY),
          scale_x: value.scaleX,
          scale_y: value.scaleY,
        };
      },
      clientToDesktop: (x, y) => {
        const value = metrics();
        return {
          x: Math.round(finite(x) / value.scaleX),
          y: Math.round(finite(y) / value.scaleY),
          scale_x: value.scaleX,
          scale_y: value.scaleY,
        };
      },
      diagnostics: () => store.desktopBridgeDiagnostics(frame),
    });
    frame.agentZeroDesktop = bridge;
    frame.__agentZeroDesktopBridge = bridge;
    remoteWindow.agentZeroDesktop = bridge;
    remoteWindow.__agentZeroDesktopBridge = bridge;
    this._desktopBridgeReady = true;
    this.updateDesktopKeyboardCaptureState(frame);
    return bridge;
  },

  desktopBridgeDiagnostics(frame = null) {
    return {
      ready: this._desktopBridgeReady,
      keyboard: this.updateDesktopKeyboardCaptureState(frame),
      lastStateOk: this._desktopLastState?.ok ?? null,
    };
  },

  updateDesktopKeyboardCaptureState(frame = null) {
    const target = this.desktopFrame(frame);
    const client = target?.contentWindow?.client;
    const state = {
      ready: Boolean(target?.__agentZeroDesktopBridge || target?.contentWindow?.__agentZeroDesktopBridge),
      active: Boolean(this._desktopKeyboardActive),
      capture: Boolean(client?.capture_keyboard),
      focused: Boolean(target && (document.activeElement === target || target.contentDocument?.hasFocus?.())),
    };
    this._desktopKeyboardCaptureState = state;
    return state;
  },

  normalizeXpraDesktopWindow(xpraWindow, width, height) {
    if (!xpraWindow) return;
    const normalizedWidth = Math.max(1, Math.round(Number(width || 0)));
    const normalizedHeight = Math.max(1, Math.round(Number(height || 0)));
    xpraWindow.x = 0;
    xpraWindow.y = 0;
    xpraWindow.w = normalizedWidth;
    xpraWindow.h = normalizedHeight;
    xpraWindow.resizable = false;
    xpraWindow.decorations = false;
    xpraWindow.decorated = false;
    xpraWindow.metadata = { ...(xpraWindow.metadata || {}), decorations: false };
    xpraWindow._set_decorated?.(false);
    xpraWindow.configure_border_class?.();
    xpraWindow.leftoffset = 0;
    xpraWindow.rightoffset = 0;
    xpraWindow.topoffset = 0;
    xpraWindow.bottomoffset = 0;
  },

  fitXpraDesktopWindowElement(xpraWindow, width, height) {
    const cssWidth = `${Math.max(1, Number(width || 0))}px`;
    const cssHeight = `${Math.max(1, Number(height || 0))}px`;
    const windowElement = xpraWindow?.div;
    const canvas = xpraWindow?.canvas;
    windowElement?.style?.setProperty("left", "0px", "important");
    windowElement?.style?.setProperty("top", "0px", "important");
    windowElement?.style?.setProperty("position", "absolute", "important");
    windowElement?.style?.setProperty("width", cssWidth, "important");
    windowElement?.style?.setProperty("height", cssHeight, "important");
    windowElement?.style?.setProperty("transform", "none", "important");
    windowElement?.style?.setProperty("margin", "0", "important");
    canvas?.style?.setProperty("width", cssWidth, "important");
    canvas?.style?.setProperty("height", cssHeight, "important");
    canvas?.style?.setProperty("display", "block", "important");
    canvas?.style?.setProperty("margin", "0", "important");
  },

  installXpraDesktopWheelBridge(remoteWindow, xpraWindow) {
    const canvas = xpraWindow?.canvas;
    if (!remoteWindow || !canvas || canvas.__a0XpraWheelBridgeInstalled) return;
    if (typeof xpraWindow.mouse_scroll_cb !== "function") return;
    canvas.__a0XpraWheelBridgeInstalled = true;
    canvas.addEventListener("wheel", (event) => {
      event.stopImmediatePropagation?.();
      event.stopPropagation?.();
      event.preventDefault?.();
      const normalizedEvent = this.xpraDesktopWheelEvent(remoteWindow, canvas, event);
      xpraWindow.mouse_scroll_cb(normalizedEvent, xpraWindow);
    }, { passive: false, capture: true });
  },

  xpraDesktopWheelEvent(remoteWindow, canvas, event) {
    const finite = (value, fallback = 0) => {
      const number = Number(value);
      return Number.isFinite(number) ? number : fallback;
    };
    const deltaMode = finite(event.deltaMode, 0);
    const lineHeight = 16;
    const pageHeight = Math.max(1, remoteWindow.innerHeight || canvas.clientHeight || 800);
    const deltaScale = deltaMode === 1 ? lineHeight : deltaMode === 2 ? pageHeight : 1;
    const deltaX = finite(event.deltaX) * deltaScale;
    const deltaY = finite(event.deltaY) * deltaScale;
    const deltaZ = finite(event.deltaZ) * deltaScale;
    const wheelDeltaX = finite(event.wheelDeltaX, -deltaX);
    const wheelDeltaY = finite(event.wheelDeltaY, -deltaY);
    const wheelDelta = finite(event.wheelDelta, wheelDeltaY || wheelDeltaX);
    const getModifierState = (key) => {
      if (typeof event.getModifierState === "function") return event.getModifierState(key);
      const normalizedKey = String(key || "").toLowerCase();
      if (normalizedKey === "alt") return Boolean(event.altKey);
      if (normalizedKey === "control") return Boolean(event.ctrlKey);
      if (normalizedKey === "meta") return Boolean(event.metaKey);
      if (normalizedKey === "shift") return Boolean(event.shiftKey);
      return false;
    };
    const normalizedEvent = Object.create(event);
    Object.defineProperties(normalizedEvent, {
      target: { value: event.target || canvas },
      currentTarget: { value: canvas },
      clientX: { value: finite(event.clientX) },
      clientY: { value: finite(event.clientY) },
      pageX: { value: finite(event.pageX, finite(event.clientX)) },
      pageY: { value: finite(event.pageY, finite(event.clientY)) },
      screenX: { value: finite(event.screenX) },
      screenY: { value: finite(event.screenY) },
      offsetX: { value: finite(event.offsetX) },
      offsetY: { value: finite(event.offsetY) },
      movementX: { value: finite(event.movementX) },
      movementY: { value: finite(event.movementY) },
      button: { value: finite(event.button) },
      buttons: { value: finite(event.buttons) },
      which: { value: finite(event.which) },
      detail: { value: finite(event.detail) },
      deltaX: { value: deltaX },
      deltaY: { value: deltaY },
      deltaZ: { value: deltaZ },
      deltaMode: { value: 0 },
      wheelDeltaX: { value: wheelDeltaX },
      wheelDeltaY: { value: wheelDeltaY },
      wheelDelta: { value: wheelDelta },
      altKey: { value: Boolean(event.altKey) },
      ctrlKey: { value: Boolean(event.ctrlKey) },
      metaKey: { value: Boolean(event.metaKey) },
      shiftKey: { value: Boolean(event.shiftKey) },
      getModifierState: { value: getModifierState },
      preventDefault: { value: () => event.preventDefault?.() },
      stopPropagation: { value: () => event.stopPropagation?.() },
      stopImmediatePropagation: { value: () => event.stopImmediatePropagation?.() },
    });
    return normalizedEvent;
  },

  installXpraDesktopFrameCss(remoteDocument) {
    if (!remoteDocument || remoteDocument.getElementById("a0-xpra-desktop-frame-css")) return;
    const style = remoteDocument.createElement("style");
    style.id = "a0-xpra-desktop-frame-css";
    style.textContent = `
      html, body, #screen {
        width: 100% !important;
        height: 100% !important;
        overflow: hidden !important;
      }
      #float_menu,
      .windowhead,
      .windowbuttons {
        display: none !important;
      }
      #shadow_pointer {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
      }
      .window,
      .window.border,
      .window.desktop,
      .undecorated,
      .undecorated.border,
      .undecorated.desktop {
        left: 0 !important;
        top: 0 !important;
        position: absolute !important;
        width: 100% !important;
        height: 100% !important;
        transform: none !important;
        margin: 0 !important;
        border: 0 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
      }
      .window canvas,
      .undecorated canvas {
        display: block !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        border: 0 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
      }
    `;
    remoteDocument.head?.appendChild(style);
  },

  installXpraDesktopCursorPatches(remoteWindow, remoteDocument, client) {
    if (!remoteWindow || !remoteDocument || !client) return;
    const hideShadowPointer = () => {
      const pointer = remoteDocument.getElementById?.("shadow_pointer");
      pointer?.style?.setProperty("display", "none", "important");
      pointer?.style?.setProperty("visibility", "hidden", "important");
      pointer?.style?.setProperty("opacity", "0", "important");
    };
    hideShadowPointer();

    const pointerPacket = remoteWindow.PACKET_TYPES?.pointer_position || "pointer-position";
    if (!client.__a0XpraDesktopCursorPatched) {
      if (typeof client._process_pointer_position === "function") {
        client.__a0OriginalProcessPointerPosition = client._process_pointer_position;
      }
      client._process_pointer_position = function patchedProcessPointerPosition(packet) {
        hideShadowPointer();
        this.__a0LastPointerPosition = packet;
        return false;
      };
      client.__a0XpraDesktopCursorPatched = true;
    }
    if (client.packet_handlers && pointerPacket) {
      client.packet_handlers[pointerPacket] = client._process_pointer_position;
    }
  },

  installXpraDesktopFramePatches(remoteWindow, remoteDocument) {
    if (!remoteWindow || !remoteDocument) return;
    remoteWindow.__a0XpraDesktopFramePatches ||= {};
    const patches = remoteWindow.__a0XpraDesktopFramePatches;
    const isBenignXpraWarning = (args = []) => {
      const text = Array.from(args || []).map((value) => String(value || "")).join(" ");
      return text.includes("window does not fit in canvas, offsets")
        || (text.includes("decode error packet") && text.includes("not found"));
    };
    if (!patches.consoleWarn && typeof remoteWindow.console?.warn === "function") {
      const originalConsoleWarn = remoteWindow.console.warn.bind(remoteWindow.console);
      remoteWindow.console.warn = function patchedConsoleWarn(...args) {
        if (isBenignXpraWarning(args)) return undefined;
        return originalConsoleWarn(...args);
      };
      patches.consoleWarn = true;
    }
    if (!patches.noWindowList && typeof remoteWindow.noWindowList === "function") {
      const originalNoWindowList = remoteWindow.noWindowList;
      remoteWindow.noWindowList = function patchedNoWindowList(...args) {
        if (!remoteDocument.querySelector("#open_windows")) return undefined;
        return originalNoWindowList.apply(this, args);
      };
      patches.noWindowList = true;
    }
    if (!patches.addWindowListItem && typeof remoteWindow.addWindowListItem === "function") {
      const originalAddWindowListItem = remoteWindow.addWindowListItem;
      remoteWindow.addWindowListItem = function patchedAddWindowListItem(...args) {
        if (!remoteDocument.querySelector("#open_windows_list")) return undefined;
        return originalAddWindowListItem.apply(this, args);
      };
      patches.addWindowListItem = true;
    }
  },

  installXpraDesktopClientPatches(remoteWindow, client) {
    if (!remoteWindow || !client) return;
    if (!client.__a0XpraOffsetWarnPatched && typeof client.warn === "function") {
      const originalClientWarn = client.warn.bind(client);
      client.warn = function patchedClientWarn(...args) {
        const text = Array.from(args || []).map((value) => String(value || "")).join(" ");
        if (
          text.includes("window does not fit in canvas, offsets")
          || (text.includes("decode error packet") && text.includes("not found"))
        ) {
          return undefined;
        }
        return originalClientWarn(...args);
      };
      client.__a0XpraOffsetWarnPatched = true;
    }
    if (client.__a0XpraDesktopClientPatched) return;
    if (typeof client._screen_resized === "function") {
      const originalScreenResized = client._screen_resized.bind(client);
      client.__a0OriginalScreenResized = originalScreenResized;
      client._screen_resized = function patchedScreenResized(event) {
        if (client.__a0AllowScreenResize === true) return originalScreenResized(event);
        return false;
      };
    }
    client.__a0XpraDesktopClientPatched = true;
  },

  installXpraDesktopClipboardBridge(frame, remoteWindow, remoteDocument, client) {
    if (!frame || !remoteWindow || !remoteDocument || !client) return;
    this.ensureDesktopClipboardBridge();
    if (remoteWindow.__a0XpraDesktopClipboardBridgeInstalled) return;

    const onPaste = (event) => {
      this.handleDesktopPasteEvent(event, frame, remoteWindow, client);
    };
    const onKeydown = (event) => {
      if (this.isDesktopPasteShortcut(event)) {
        void this.syncHostClipboardToDesktop(frame);
      }
    };
    remoteWindow.addEventListener("paste", onPaste, true);
    remoteDocument.addEventListener("paste", onPaste, true);
    remoteWindow.addEventListener("keydown", onKeydown, true);
    remoteDocument.addEventListener("keydown", onKeydown, true);
    remoteWindow.__a0XpraDesktopClipboardBridgeInstalled = true;
    remoteWindow.__a0XpraDesktopClipboardBridgeCleanup = () => {
      remoteWindow.removeEventListener("paste", onPaste, true);
      remoteDocument.removeEventListener("paste", onPaste, true);
      remoteWindow.removeEventListener("keydown", onKeydown, true);
      remoteDocument.removeEventListener("keydown", onKeydown, true);
      remoteWindow.__a0XpraDesktopClipboardBridgeInstalled = false;
    };
  },

  ensureDesktopClipboardBridge() {
    if (this._desktopClipboardCleanup) return;

    const onPaste = (event) => {
      if (!this._desktopKeyboardActive || !this.hasOfficialOffice()) return;
      if (isEditableInputTarget(event.target)) return;
      const frame = this.desktopFrame();
      const remoteWindow = frame?.contentWindow;
      const client = remoteWindow?.client;
      if (!frame || !remoteWindow || !client) return;
      this.handleDesktopPasteEvent(event, frame, remoteWindow, client);
    };

    document.addEventListener("paste", onPaste, true);
    this._desktopClipboardCleanup = () => {
      document.removeEventListener("paste", onPaste, true);
      this._desktopClipboardCleanup = null;
    };
  },

  stopDesktopClipboardBridge() {
    this._desktopClipboardCleanup?.();
  },

  handleDesktopPasteEvent(event, frame, remoteWindow, client) {
    const text = this.desktopClipboardTextFromEvent(event);
    if (!text) return false;
    if (!this.syncXpraClipboardText(client, text, remoteWindow)) return false;
    event.preventDefault?.();
    event.stopImmediatePropagation?.();
    event.stopPropagation?.();
    this.focusDesktopFrame(frame, { arm: true });
    return true;
  },

  desktopClipboardTextFromEvent(event) {
    const data = (event?.originalEvent || event)?.clipboardData;
    if (!data?.getData) return "";
    for (const type of ["text/plain", "text", "Text", "STRING", "UTF8_STRING"]) {
      const value = data.getData(type);
      if (value) return value;
    }
    return "";
  },

  syncXpraClipboardText(client, text, remoteWindow = null) {
    const value = String(text ?? "");
    if (!client || !value || typeof client.send_clipboard_token !== "function") return false;
    const textPlain = remoteWindow?.TEXT_PLAIN || "text/plain";
    const utf8String = remoteWindow?.UTF8_STRING || "UTF8_STRING";
    const utilities = remoteWindow?.Utilities;
    const payload = utilities?.StringToUint8 ? utilities.StringToUint8(value) : value;
    client.clipboard_enabled = true;
    client.clipboard_direction = "both";
    client.clipboard_buffer = value;
    client.clipboard_pending = false;
    client.send_clipboard_token(payload, [textPlain, utf8String, "TEXT", "STRING"]);
    return true;
  },

  async syncHostClipboardToDesktop(frame = null) {
    const target = this.desktopFrame(frame);
    const remoteWindow = target?.contentWindow;
    const client = remoteWindow?.client;
    if (!client || !navigator.clipboard?.readText) return false;
    try {
      const text = await navigator.clipboard.readText();
      return this.syncXpraClipboardText(client, text, remoteWindow);
    } catch {
      return false;
    }
  },

  isDesktopPasteShortcut(event) {
    const key = String(event?.key || "").toLowerCase();
    return key === "v" && (event?.ctrlKey || event?.metaKey) && !event?.altKey;
  },

  installXpraDesktopKeyboardBridge(frame, remoteWindow, remoteDocument, client) {
    if (!frame || !remoteWindow || !remoteDocument || !client) return;
    this.ensureDesktopKeyboardBridge();
    frame.setAttribute("tabindex", "0");
    if (remoteWindow.__a0XpraDesktopKeyboardBridgeInstalled) return;

    const activate = () => {
      if (this._desktopFocusInProgress) return;
      this.focusDesktopFrame(frame, { arm: true });
    };
    const events = ["pointerdown", "mousedown", "touchstart", "focusin"];
    for (const eventName of events) {
      remoteDocument.addEventListener(eventName, activate, true);
    }
    remoteWindow.addEventListener("focus", activate, true);
    remoteWindow.__a0XpraDesktopKeyboardBridgeInstalled = true;
    remoteWindow.__a0XpraDesktopKeyboardBridgeCleanup = () => {
      for (const eventName of events) {
        remoteDocument.removeEventListener(eventName, activate, true);
      }
      remoteWindow.removeEventListener("focus", activate, true);
      remoteWindow.__a0XpraDesktopKeyboardBridgeInstalled = false;
    };
  },

  ensureDesktopKeyboardBridge() {
    if (this._desktopKeyboardCleanup) return;

    const deactivateWhenOutsideDesktop = (event) => {
      const target = event.target;
      if (target?.closest?.(".office-desktop-wrap") || target?.matches?.("[data-office-desktop-frame]")) return;
      this._desktopKeyboardActive = false;
    };
    const forwardKeyboardEvent = (event, pressed) => {
      if (!this._desktopKeyboardActive || !this.hasOfficialOffice()) return;
      if (event.defaultPrevented || isEditableInputTarget(event.target)) return;

      const frame = this.desktopFrame();
      if (!frame || document.activeElement === frame) return;
      const client = frame.contentWindow?.client;
      const handler = pressed ? client?._keyb_onkeydown : client?._keyb_onkeyup;
      if (!client?.capture_keyboard || typeof handler !== "function") return;
      if (pressed && this.isDesktopPasteShortcut(event)) {
        void this.syncHostClipboardToDesktop(frame);
      }

      const allowDefault = handler.call(client, event);
      if (!allowDefault) {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    const onKeydown = (event) => forwardKeyboardEvent(event, true);
    const onKeyup = (event) => forwardKeyboardEvent(event, false);

    document.addEventListener("pointerdown", deactivateWhenOutsideDesktop, true);
    document.addEventListener("keydown", onKeydown, true);
    document.addEventListener("keyup", onKeyup, true);
    this._desktopKeyboardCleanup = () => {
      document.removeEventListener("pointerdown", deactivateWhenOutsideDesktop, true);
      document.removeEventListener("keydown", onKeydown, true);
      document.removeEventListener("keyup", onKeyup, true);
      this._desktopKeyboardActive = false;
      this._desktopKeyboardCleanup = null;
    };
  },

  stopDesktopKeyboardBridge() {
    this._desktopKeyboardCleanup?.();
  },

  queueDesktopResize(options = {}) {
    if (!this.hasOfficialOffice() || !this.isDesktopHostVisible()) return;
    const token = this.session?.desktop?.token || "";
    const frame = this.desktopFrame(options.frame || null);
    const target = frame?.parentElement || frame;
    if (!token || !target) return;
    const force = Boolean(options.force);
    const serverResize = options.serverResize !== false;
    const rect = target.getBoundingClientRect();
    const width = Math.round(rect.width);
    const height = Math.round(rect.height);
    if (width < 320 || height < 220) return;
    const key = `${token}:${width}x${height}`;
    const refreshFrameOnly = () => {
      this.applyXpraDesktopFrameMode(frame, { requestServerResize: false, requestRefresh: false });
    };
    if (!serverResize) {
      refreshFrameOnly();
      return;
    }
    if (key === this._desktopResizeKey || key === this._desktopResizePendingKey) {
      refreshFrameOnly();
      return;
    }
    refreshFrameOnly();
    if (!force && this.shouldDeferDesktopResize()) {
      this._desktopResizePending = true;
      return;
    }
    if (this._desktopResizeTimer) globalThis.clearTimeout(this._desktopResizeTimer);
    this._desktopResizePendingKey = key;
    this._desktopResizeTimer = globalThis.setTimeout(async () => {
      this._desktopResizeTimer = null;
      if (!this.hasOfficialOffice() || !this.isDesktopHostVisible()) {
        if (this._desktopResizePendingKey === key) this._desktopResizePendingKey = "";
        return;
      }
      if (!force && this.shouldDeferDesktopResize()) {
        if (this._desktopResizePendingKey === key) this._desktopResizePendingKey = "";
        this._desktopResizePending = true;
        return;
      }
      try {
        const params = new URLSearchParams({ token, width: String(width), height: String(height) });
        const response = await fetch(`/desktop/resize?${params.toString()}`, { credentials: "same-origin" });
        if (response.ok) {
          const result = await response.json().catch(() => ({}));
          this._desktopResizeKey = key;
          const activeFrame = this.desktopFrame(frame);
          const activeTarget = activeFrame?.parentElement || activeFrame;
          const activeRect = activeTarget?.getBoundingClientRect?.();
          const activeWidth = Math.round(activeRect?.width || 0);
          const activeHeight = Math.round(activeRect?.height || 0);
          if (activeWidth >= 320 && activeHeight >= 220) {
            const activeKey = `${token}:${activeWidth}x${activeHeight}`;
            if (activeKey !== key) {
              this.queueDesktopResize({ force: true, serverResize: true, frame: activeFrame });
              return;
            }
          }
          if (result?.reload) this.reloadDesktopFrame(activeFrame || frame);
          this.primeXpraDesktopFrame({ reset: true, frame: activeFrame || frame });
        }
      } catch (error) {
        console.warn("Desktop resize skipped", error);
      } finally {
        if (this._desktopResizePendingKey === key) this._desktopResizePendingKey = "";
      }
    }, DESKTOP_RESIZE_DELAY_MS);
  },

  reloadDesktopFrame(frame = null) {
    const target = this.desktopFrame(frame);
    if (!target) return;
    const current = target.getAttribute("src") || target.src || this.officialOfficeUrl();
    if (!current) return;
    try {
      const url = new URL(current, window.location.href);
      url.searchParams.set("a0_reload", String(Date.now()));
      target.setAttribute("src", `${url.pathname}${url.search}`);
    } catch {
      target.setAttribute("src", current);
    }
  },

  async handleDesktopUrlIntents(intents = []) {
    const incoming = Array.isArray(intents)
      ? intents.filter((intent) => intent && typeof intent === "object")
      : [];
    if (!incoming.length) return;
    this._desktopUrlIntentQueue.push(...incoming);
    if (this._desktopUrlIntentBusy) return;

    this._desktopUrlIntentBusy = true;
    try {
      while (this._desktopUrlIntentQueue.length) {
        const intent = this._desktopUrlIntentQueue.shift();
        await this.openDesktopUrlIntent(intent);
      }
    } finally {
      this._desktopUrlIntentBusy = false;
    }
  },

  async openDesktopUrlIntent(intent = {}) {
    const url = String(intent?.url || "").trim();
    const handled = await handleUrlIntent({ url, source: "desktop-url" });
    this.setMessage(handled ? "Opened link in Browser" : "Browser is not available");
  },

  browserDestinationForDesktopUrl() {
    if (this.isDesktopInModal()) return "canvas";
    return "modal";
  },

  isDesktopInModal() {
    const modalDesktop = Array.from(document.querySelectorAll(".office-panel"))
      .some((panel) => panel.closest?.(".modal") && panel.querySelector?.("[data-office-desktop-frame]"));
    if (modalDesktop) return true;
    return this._mode === "modal";
  },

  startDesktopMonitor() {
    this.stopDesktopMonitor();
    if (!this.hasOfficialOffice() || !this.isDesktopHostVisible()) return;
    const tabId = this.session?.tab_id || "";
    const sessionId = this.session?.desktop_session_id || this.session?.session_id || "";
    if (!tabId || !sessionId) return;
    this._desktopHeartbeatSessionId = sessionId;
    this._desktopHeartbeatTabId = tabId;
    this._desktopHeartbeatMisses = 0;

    const tick = async () => {
      if (!this.session || this.session.tab_id !== tabId || !this.hasOfficialOffice() || !this.isDesktopHostVisible()) return;
      try {
        const response = await callDesktop("sync", {
          desktop_session_id: sessionId,
          file_id: this.session.file_id || "",
        });
        if (response?.intentional_shutdown || response?.shutdown) {
          await this.handleIntentionalDesktopShutdown(response);
          return;
        }
        if (response?.ok === false) throw new Error(response.error || "Desktop session closed.");
        this._desktopHeartbeatMisses = 0;
        await this.handleDesktopUrlIntents(response?.url_intents);
        if (response?.document) {
          const document = normalizeDocument(response.document);
          this.replaceActiveSession({
            ...this.session,
            document,
            path: document.path || this.session.path,
            file_id: document.file_id || this.session.file_id,
            version: document.version || this.session.version,
          });
        }
      } catch {
        if (!this.session || this.session.tab_id !== tabId) return;
        this._desktopHeartbeatMisses += 1;
        if (this._desktopHeartbeatMisses >= 2) {
          await this.handleOfficialOfficeClosed(tabId);
        }
      }
    };

    this._desktopHeartbeatTimer = globalThis.setInterval(tick, DESKTOP_HEARTBEAT_MS);
    globalThis.setTimeout(tick, Math.min(1200, DESKTOP_HEARTBEAT_MS));
  },

  stopDesktopMonitor() {
    if (this._desktopHeartbeatTimer) {
      globalThis.clearInterval(this._desktopHeartbeatTimer);
    }
    this._desktopHeartbeatTimer = null;
    this._desktopHeartbeatSessionId = "";
    this._desktopHeartbeatTabId = "";
    this._desktopHeartbeatMisses = 0;
  },

  async handleOfficialOfficeClosed(tabId) {
    if (this._desktopIntentionalShutdown) return;
    const tab = this.tabs.find((item) => item.tab_id === tabId);
    const hiddenDesktopDocument = !tab && this.session?.tab_id === tabId && this.isDesktopOfficeDocument(this.session)
      ? this.session
      : null;
    const target = tab || hiddenDesktopDocument;
    if (!target || target._desktopClosed) return;
    target._desktopClosed = true;
    this.stopDesktopMonitor();
    this.stopDesktopResizeObserver();
    this.stopXpraDesktopPrime();
    this.message = "Desktop is restarting";
    await this.ensureDesktopSession({
      force: true,
      select: this.activeTabId === tabId || Boolean(hiddenDesktopDocument),
      message: "Desktop is restarting",
    });
    target._desktopClosed = false;
    await this.refresh();
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
    if (this.isDesktopSession(tab)) return "desktop_windows";
    if (ext === "md") return "article";
    if (ext === "odt" || ext === "docx") return "description";
    if (ext === "ods" || ext === "xlsx") return "table_chart";
    if (ext === "odp" || ext === "pptx") return "co_present";
    return "draft";
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

    const root = globalThis.document.createElement("div");
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
    globalThis.document.addEventListener("click", onDocumentClick);
    globalThis.document.addEventListener("keydown", onDocumentKeydown);

    const firstHeaderAction = header.querySelector(
      ".modal-surface-switcher, .modal-dock-button, .office-modal-focus-button, .modal-close",
    );
    if (firstHeaderAction) {
      firstHeaderAction.insertAdjacentElement("beforebegin", root);
    } else {
      header.appendChild(root);
    }

    setOpen(false);
    return () => {
      button?.removeEventListener("click", onButtonClick);
      globalThis.document.removeEventListener("click", onDocumentClick);
      globalThis.document.removeEventListener("keydown", onDocumentKeydown);
      root.remove();
    };
  },

  setupFloatingModal(element = null) {
    const root = element || globalThis.document?.querySelector(".office-panel");
    const modal = root?.closest?.(".modal");
    const inner = root?.closest?.(".modal-inner");
    const body = root?.closest?.(".modal-bd");
    const header = inner?.querySelector?.(".modal-header");
    if (!inner || !body || !header || inner.dataset.officeModalReady === "1") return;

    inner.dataset.officeModalReady = "1";
    modal?.classList?.add("surface-floating", "modal-floating", "modal-no-backdrop");
    inner.classList.add("surface-modal", "office-modal", "modal-no-backdrop");
    body.classList.add("office-modal-body");
    header.style.cursor = "move";

    const inset = 8;
    const minWidth = 720;
    const minHeight = 520;
    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
    const cleanup = [];
    let beforeFocusBounds = null;
    let dragging = false;
    let resizing = false;
    let pointerId = 0;
    let startX = 0;
    let startY = 0;
    let startLeft = 0;
    let startTop = 0;
    let startWidth = 0;
    let startHeight = 0;
    let resizeMode = "";

    const newMenuCleanup = this.installHeaderNewMenu(header);

    const currentBounds = () => {
      const rect = inner.getBoundingClientRect();
      return {
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
      };
    };

    const normalizedBounds = (bounds) => {
      const maxWidth = Math.max(320, globalThis.innerWidth - inset * 2);
      const maxHeight = Math.max(320, globalThis.innerHeight - inset * 2);
      const safeMinWidth = Math.min(minWidth, maxWidth);
      const safeMinHeight = Math.min(minHeight, maxHeight);
      const width = clamp(bounds.width, safeMinWidth, maxWidth);
      const height = clamp(bounds.height, safeMinHeight, maxHeight);
      return {
        width,
        height,
        left: clamp(bounds.left, inset, Math.max(inset, globalThis.innerWidth - width - inset)),
        top: clamp(bounds.top, inset, Math.max(inset, globalThis.innerHeight - height - inset)),
      };
    };

    const setBounds = (bounds) => {
      const next = normalizedBounds(bounds);
      inner.style.position = "fixed";
      inner.style.transform = "none";
      inner.style.left = `${Math.round(next.left)}px`;
      inner.style.top = `${Math.round(next.top)}px`;
      inner.style.width = `${Math.round(next.width)}px`;
      inner.style.height = `${Math.round(next.height)}px`;
      inner.style.right = "auto";
      inner.style.bottom = "auto";
      inner.style.margin = "0";
    };

    const ensurePosition = () => {
      setBounds(currentBounds());
    };

    const shield = globalThis.document.createElement("div");
    shield.className = "office-modal-input-shield";
    inner.appendChild(shield);
    cleanup.push(() => shield.remove());

    const setShield = (visible, cursor = "") => {
      shield.style.display = visible ? "block" : "none";
      shield.style.cursor = cursor;
    };

    const focusButton = globalThis.document.createElement("button");
    focusButton.type = "button";
    focusButton.className = "modal-dock-button office-modal-focus-button";
    focusButton.innerHTML = '<span class="material-symbols-outlined" aria-hidden="true">fullscreen</span>';
    const updateFocusButton = (active) => {
      const label = active ? "Restore size" : "Focus mode";
      focusButton.setAttribute("aria-label", label);
      focusButton.querySelector(".material-symbols-outlined").textContent = active ? "fullscreen_exit" : "fullscreen";
    };
    updateFocusButton(false);
    const closeButton = inner.querySelector(".modal-close");
    if (closeButton) {
      closeButton.insertAdjacentElement("beforebegin", focusButton);
    } else {
      header.appendChild(focusButton);
    }
    cleanup.push(() => focusButton.remove());

    const setFocusMode = (enabled) => {
      ensurePosition();
      if (enabled) {
        beforeFocusBounds = currentBounds();
        inner.classList.add("is-focus-mode");
        setBounds({
          left: inset,
          top: inset,
          width: globalThis.innerWidth - inset * 2,
          height: globalThis.innerHeight - inset * 2,
        });
        updateFocusButton(true);
        return;
      }
      inner.classList.remove("is-focus-mode");
      setBounds(beforeFocusBounds || currentBounds());
      beforeFocusBounds = null;
      updateFocusButton(false);
    };

    const onFocusClick = () => setFocusMode(!inner.classList.contains("is-focus-mode"));
    focusButton.addEventListener("click", onFocusClick);
    cleanup.push(() => focusButton.removeEventListener("click", onFocusClick));

    const onPointerDown = (event) => {
      if (event.button !== 0) return;
      if (event.target?.closest?.("button,a,input,textarea,select")) return;
      if (inner.classList.contains("is-focus-mode")) return;
      ensurePosition();
      const rect = inner.getBoundingClientRect();
      dragging = true;
      pointerId = event.pointerId;
      startX = event.clientX;
      startY = event.clientY;
      startLeft = rect.left;
      startTop = rect.top;
      startWidth = rect.width;
      startHeight = rect.height;
      inner.classList.add("is-dragging");
      setShield(true, "move");
      header.setPointerCapture?.(pointerId);
      event.preventDefault();
    };

    const onPointerMove = (event) => {
      if (!dragging || event.pointerId !== pointerId) return;
      setBounds({
        left: startLeft + event.clientX - startX,
        top: startTop + event.clientY - startY,
        width: startWidth,
        height: startHeight,
      });
    };

    const onPointerUp = (event) => {
      if (!dragging || event.pointerId !== pointerId) return;
      dragging = false;
      inner.classList.remove("is-dragging");
      setShield(false);
      header.releasePointerCapture?.(pointerId);
    };

    const createResizeHandle = (mode) => {
      const handle = globalThis.document.createElement("div");
      handle.className = `office-modal-resizer is-${mode}`;
      handle.dataset.officeResize = mode;
      inner.appendChild(handle);
      cleanup.push(() => handle.remove());
      return handle;
    };

    const onResizeDown = (event) => {
      if (event.button !== 0 || inner.classList.contains("is-focus-mode")) return;
      ensurePosition();
      const rect = inner.getBoundingClientRect();
      resizing = true;
      resizeMode = event.currentTarget.dataset.officeResize || "";
      pointerId = event.pointerId;
      startX = event.clientX;
      startY = event.clientY;
      startLeft = rect.left;
      startTop = rect.top;
      startWidth = rect.width;
      startHeight = rect.height;
      inner.classList.add("is-resizing");
      this.suspendDesktopResize();
      setShield(true, resizeMode === "right" ? "ew-resize" : resizeMode === "bottom" ? "ns-resize" : "nwse-resize");
      event.currentTarget.setPointerCapture?.(pointerId);
      event.preventDefault();
      event.stopPropagation();
    };

    const onResizeMove = (event) => {
      if (!resizing || event.pointerId !== pointerId) return;
      const dx = event.clientX - startX;
      const dy = event.clientY - startY;
      setBounds({
        left: startLeft,
        top: startTop,
        width: resizeMode === "bottom" ? startWidth : startWidth + dx,
        height: resizeMode === "right" ? startHeight : startHeight + dy,
      });
    };

    const onResizeUp = (event) => {
      if (!resizing || event.pointerId !== pointerId) return;
      resizing = false;
      resizeMode = "";
      inner.classList.remove("is-resizing");
      setShield(false);
      event.currentTarget.releasePointerCapture?.(pointerId);
      this.resumeDesktopResize();
    };

    header.addEventListener("pointerdown", onPointerDown);
    header.addEventListener("pointermove", onPointerMove);
    header.addEventListener("pointerup", onPointerUp);
    header.addEventListener("pointercancel", onPointerUp);
    cleanup.push(() => header.removeEventListener("pointerdown", onPointerDown));
    cleanup.push(() => header.removeEventListener("pointermove", onPointerMove));
    cleanup.push(() => header.removeEventListener("pointerup", onPointerUp));
    cleanup.push(() => header.removeEventListener("pointercancel", onPointerUp));

    for (const mode of ["right", "bottom", "corner"]) {
      const handle = createResizeHandle(mode);
      handle.addEventListener("pointerdown", onResizeDown);
      handle.addEventListener("pointermove", onResizeMove);
      handle.addEventListener("pointerup", onResizeUp);
      handle.addEventListener("pointercancel", onResizeUp);
      cleanup.push(() => handle.removeEventListener("pointerdown", onResizeDown));
      cleanup.push(() => handle.removeEventListener("pointermove", onResizeMove));
      cleanup.push(() => handle.removeEventListener("pointerup", onResizeUp));
      cleanup.push(() => handle.removeEventListener("pointercancel", onResizeUp));
    }

    const onWindowResize = () => {
      if (inner.classList.contains("is-focus-mode")) {
        setBounds({
          left: inset,
          top: inset,
          width: globalThis.innerWidth - inset * 2,
          height: globalThis.innerHeight - inset * 2,
        });
        return;
      }
      ensurePosition();
    };
    globalThis.addEventListener("resize", onWindowResize);
    cleanup.push(() => globalThis.removeEventListener("resize", onWindowResize));

    if (globalThis.requestAnimationFrame) {
      globalThis.requestAnimationFrame(ensurePosition);
    } else {
      globalThis.setTimeout(ensurePosition, 0);
    }
    this._floatingCleanup = () => {
      newMenuCleanup?.();
      cleanup.splice(0).reverse().forEach((entry) => entry());
      modal?.classList?.remove("surface-floating", "modal-floating", "modal-no-backdrop");
      inner.classList.remove("is-dragging", "is-resizing", "is-focus-mode");
      this._desktopResizeSuspended = false;
      this._desktopResizePending = false;
      delete inner.dataset.officeModalReady;
    };
  },
};

export const store = createStore("desktop", model);
