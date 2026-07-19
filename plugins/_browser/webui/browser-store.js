import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getNamespacedClient } from "/js/websocket.js";
import { getContext, setContext } from "/index.js";
import { copyToClipboard } from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as chatInputStore } from "/components/chat/input/input-store.js";
import { store as pluginSettingsStore } from "/components/plugins/plugin-settings-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as rightCanvasStore } from "/components/canvas/right-canvas-store.js";
import { openLatest as openLatestSurface, registerUrlHandler } from "/js/surfaces.js";

const websocket = getNamespacedClient("/ws");
websocket.addHandlers(["ws_webui"]);

const EXTENSIONS_ROOT = "/a0/usr/_browser/extensions";
const BROWSER_SUBSCRIBE_TIMEOUT_MS = 60000;
const BROWSER_FIRST_INSTALL_TIMEOUT_MS = 300000;
const BROWSER_CONFIG_REFRESH_MS = 15000;
const VIEWPORT_SYNC_DEBOUNCE_MS = 220;
const VIEWPORT_SYNC_SIZE_TOLERANCE = 4;
const CANVAS_VIEWPORT_SETTLE_MS = 520;
const SURFACE_VIEWPORT_STABLE_FRAMES = 4;
const SURFACE_VIEWPORT_MAX_WAIT_MS = 1200;
const FRAME_REJECT_SYNC_COOLDOWN_MS = 600;
const ANNOTATION_DRAG_THRESHOLD = 6;
const ANNOTATION_MAX_COMMENTS = 24;
const ANNOTATION_DOM_LIMIT = 1200;
const ANNOTATION_TRAY_MARGIN = 10;
const BROWSER_VISUAL_SHORTCUT_KEYS = new Set(["a", "c", "insert", "v", "x", "y", "z"]);
const LOCAL_EDITABLE_SELECTOR = "input, textarea, select, [contenteditable]";

function makeViewerToken() {
  return globalThis.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

function firstOk(response) {
  const result = response?.results?.find((item) => item?.ok);
  if (result) {
    const data = result.data || {};
    if (data.browser_error) {
      throw new Error(data.browser_error.error || data.browser_error.code || "Browser request failed");
    }
    return data;
  }
  const error = response?.results?.find((item) => !item?.ok)?.error;
  if (error) throw new Error(error.error || error.code || "Browser request failed");
  return {};
}

function normalizeBool(value, fallback = true) {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return Boolean(value);
  const normalized = String(value).trim().toLowerCase();
  if (["1", "true", "yes", "on", "enabled"].includes(normalized)) return true;
  if (["0", "false", "no", "off", "disabled"].includes(normalized)) return false;
  return fallback;
}

function elementFromTarget(target) {
  if (!target) return null;
  if (target.nodeType === 1) return target;
  return target.parentElement || null;
}

function isLocalEditableTarget(target) {
  const element = elementFromTarget(target);
  const editable = element?.closest?.(LOCAL_EDITABLE_SELECTOR);
  if (!editable) return false;
  if (editable.matches?.("input, textarea, select")) return true;
  const value = String(editable.getAttribute?.("contenteditable") || "").trim().toLowerCase();
  return ["", "true", "plaintext-only"].includes(value);
}

function nextAnimationFrame() {
  return new Promise((resolve) => {
    const schedule = globalThis.requestAnimationFrame || ((callback) => globalThis.setTimeout(callback, 16));
    schedule(() => resolve());
  });
}

function loadFrameDimensions(src) {
  return new Promise((resolve) => {
    if (!src) {
      resolve(null);
      return;
    }

    const image = new Image();
    let settled = false;
    const finish = (dimensions) => {
      if (settled) return;
      settled = true;
      resolve(dimensions);
    };

    image.onload = () => finish({
      width: image.naturalWidth || 0,
      height: image.naturalHeight || 0,
    });
    image.onerror = () => finish(null);
    image.src = src;

    if (image.complete) {
      image.onload();
    }
  });
}

const model = {
  loading: true,
  error: "",
  status: null,
  contextId: "",
  browsers: [],
  activeBrowserId: null,
  activeBrowserContextId: "",
  address: "",
  frameSrc: "",
  frameState: null,
  annotating: false,
  annotationComments: [],
  annotationDraft: null,
  annotationDraftText: "",
  annotationDragRect: null,
  annotationBusy: false,
  annotationError: "",
  annotationTrayPosition: null,
  annotationTrayDragging: false,
  connected: false,
  switchingBrowserId: null,
  commandInFlight: false,
  addressFocused: false,
  _frameOff: null,
  _stateOff: null,
  _lastFrameAt: 0,
  _lastFrameDimensions: null,
  _pendingFrameSrc: "",
  _pendingFrameOptions: null,
  _frameRenderHandle: null,
  _frameRenderCancel: null,
  _frameRenderSequence: 0,
  _floatingCleanup: null,
  _stageElement: null,
  _stageResizeObserver: null,
  _viewportSyncTimer: null,
  _lastFrameRejectSyncAt: 0,
  _lastViewportKey: "",
  _lastViewport: null,
  _annotationPointer: null,
  _annotationTrayDrag: null,
  _annotationSequence: 0,
  _mode: "",
  _surfaceMounted: false,
  _surfaceSwitching: false,
  _surfaceHandoff: false,
  _surfaceHandoffTimer: null,
  _surfaceOpenedAt: 0,
  _surfaceOpenSequence: 0,
  _canvasSurfaceReadySequence: 0,
  _canvasFirstFrameAcceptedSequence: 0,
  _canvasFirstFrameNudgeSequence: 0,
  _openPromise: null,
  _openSignature: "",
  _connectSequence: 0,
  _viewerToken: "",
  _contextCreatePromise: null,
  _lastSelectedContextId: "",
  _sessionRefreshPromise: null,
  _sessionRefreshContextId: "",
  extensionMenuOpen: false,
  extensionInstallUrl: "",
  extensionActionLoading: false,
  extensionActionMessage: "",
  extensionActionError: "",
  extensionsRoot: "",
  extensionsList: [],
  extensionsListLoading: false,
  extensionToggleLoadingPath: "",
  modelPreset: "",
  modelPresetOptions: [],
  mainModelSummary: "",
  modelPresetSaving: false,
  browserInstallExpected: false,
  defaultHomepage: "about:blank",
  autofocusActivePage: true,
  _commandInFlightCount: 0,
  _closingBrowserIds: {},
  _configLoadedAt: 0,
  _configRefreshPromise: null,
  _clipboardFallbackText: "",

  async refreshStatus() {
    this.status = await callJsonApi("/plugins/_browser/status", {});
    this.browserInstallExpected = Boolean(this.status?.playwright?.install_required);
  },

  async refreshExtensionsList() {
    this.extensionsListLoading = true;
    try {
      const response = await callJsonApi("/plugins/_browser/extensions", {
        action: "list",
        context_id: this.resolveContextId() || this.contextId,
      });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not load browser extensions.");
      }
      this.applyExtensionPayload(response);
    } catch (error) {
      this.extensionActionError = error instanceof Error ? error.message : String(error);
    } finally {
      this.extensionsListLoading = false;
    }
  },

  applyExtensionPayload(response = {}) {
    this.extensionsRoot = response.root || EXTENSIONS_ROOT;
    this.extensionsList = Array.isArray(response.extensions) ? response.extensions : [];
    this.defaultHomepage = String(response.default_homepage || "about:blank").trim() || "about:blank";
    this.autofocusActivePage = normalizeBool(response.autofocus_active_page, true);
    this.modelPreset = String(response.model_preset || "");
    this.mainModelSummary = String(response.main_model_summary || "");
    this.modelPresetOptions = Array.isArray(response.model_preset_options)
      ? response.model_preset_options
      : [];
    this._configLoadedAt = Date.now();
  },

  async ensureBrowserConfigLoaded(force = false) {
    if (!force && this._configLoadedAt && Date.now() - this._configLoadedAt < BROWSER_CONFIG_REFRESH_MS) {
      return;
    }
    if (this._configRefreshPromise) {
      await this._configRefreshPromise;
      return;
    }
    this._configRefreshPromise = (async () => {
      const response = await callJsonApi("/plugins/_browser/extensions", {
        action: "list",
        context_id: this.resolveContextId() || this.contextId,
      });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not load browser settings.");
      }
      this.applyExtensionPayload(response);
    })();
    try {
      await this._configRefreshPromise;
    } finally {
      this._configRefreshPromise = null;
    }
  },

  async allowsToolAutofocus() {
    try {
      await this.ensureBrowserConfigLoaded();
    } catch (error) {
      console.warn("Browser autofocus setting could not be loaded", error);
    }
    return this.autofocusActivePage !== false;
  },

  handleSelectedContextChange(contextId = "") {
    const selectedContextId = this.normalizeContextId(contextId || this.resolveContextId());
    if (selectedContextId === this._lastSelectedContextId) return;
    this._lastSelectedContextId = selectedContextId;
    if (!this._surfaceMounted) return;
    void this.syncViewerToSelectedContext(selectedContextId);
  },

  async refreshBrowserSessions(contextId = "") {
    const requestedContextId = this.normalizeContextId(contextId || this.resolveContextId());
    if (this._sessionRefreshPromise) {
      const inFlightContextId = this._sessionRefreshContextId;
      await this._sessionRefreshPromise;
      if (requestedContextId && requestedContextId !== inFlightContextId) {
        return await this.refreshBrowserSessions(requestedContextId);
      }
      return;
    }
    this._sessionRefreshContextId = requestedContextId;
    this._sessionRefreshPromise = (async () => {
      const response = await websocket.request(
        "browser_viewer_sessions",
        { context_id: requestedContextId },
        { timeoutMs: 10000 },
      );
      const data = firstOk(response);
      this.applyBrowserListing(data.browsers || [], data.context_id || "", {
        replaceAll: Boolean(data.all_browsers),
      });
    })();
    try {
      await this._sessionRefreshPromise;
    } catch (error) {
      console.warn("Browser session refresh failed", error);
    } finally {
      this._sessionRefreshPromise = null;
      this._sessionRefreshContextId = "";
    }
  },

  async syncViewerToSelectedContext(contextId = "") {
    const selectedContextId = this.normalizeContextId(contextId || this.resolveContextId());
    if (!selectedContextId) return;
    await this.refreshBrowserSessions(selectedContextId);
    if (!this._surfaceMounted || !this.isVisibleBrowserSurface()) return;

    const targetBrowserId = this.firstBrowserInContext(selectedContextId)?.id || null;
    if (
      this.normalizeContextId(this.contextId) === selectedContextId
      && (
        !targetBrowserId
        || this.sameBrowserTab(targetBrowserId, selectedContextId, this.activeBrowserId, this.activeBrowserContextId)
      )
    ) {
      return;
    }

    this.loading = true;
    this.error = "";
    this.resetRenderedFrame();
    this.resetViewportTracking();
    this._surfaceSwitching = Boolean(targetBrowserId);
    this.switchingBrowserId = targetBrowserId;
    try {
      await this.connectViewer({
        browserId: targetBrowserId,
        contextId: selectedContextId,
        initialViewport: this.currentViewportSize(),
      });
      await this.syncViewportAfterSurfaceOpen(this._surfaceOpenSequence);
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
      this._surfaceSwitching = false;
    }
  },

  toggleExtensionsMenu() {
    this.extensionMenuOpen = !this.extensionMenuOpen;
    if (this.extensionMenuOpen) {
      this.extensionActionMessage = "";
      this.extensionActionError = "";
      void this.refreshExtensionsList();
    }
  },

  closeExtensionsMenu() {
    this.extensionMenuOpen = false;
  },

  resolveContextId() {
    const urlContext = new URLSearchParams(globalThis.location?.search || "").get("ctxid");
    return getContext() || urlContext || chatsStore.selected || "";
  },

  normalizeContextId(contextId = "") {
    return String(contextId || "").trim();
  },

  async ensureContextId() {
    const existingContextId = String(this.resolveContextId() || "").trim();
    if (existingContextId) {
      this.contextId = existingContextId;
      return existingContextId;
    }

    if (!this._contextCreatePromise) {
      this._contextCreatePromise = this.createChatContextForBrowser();
    }

    try {
      const contextId = await this._contextCreatePromise;
      this.contextId = contextId;
      return contextId;
    } finally {
      this._contextCreatePromise = null;
    }
  },

  async contextIdForNewBrowser() {
    return await this.ensureContextId();
  },

  async contextIdForActiveBrowser() {
    const activeContextId = this.normalizeContextId(this.activeBrowserContextId || this.contextId);
    if (activeContextId) return activeContextId;
    return await this.ensureContextId();
  },

  async createChatContextForBrowser() {
    const response = await callJsonApi("/chat_create", {
      current_context: this.resolveContextId() || "",
    });
    const selectedContextId = String(this.resolveContextId() || "").trim();
    if (selectedContextId) return selectedContextId;

    const contextId = String(response?.ctxid || "").trim();
    if (!response?.ok || !contextId) {
      throw new Error(response?.error || "Could not create a chat for Browser.");
    }

    setContext(contextId);
    chatsStore.setSelected?.(contextId);

    return contextId;
  },

  async openExtensionsSettings() {
    if (!pluginSettingsStore?.openConfig) {
      this.error = "Browser settings are unavailable.";
      return;
    }
    try {
      this.closeExtensionsMenu();
      await pluginSettingsStore.openConfig("_browser");
      await this.refreshAfterSettingsClose();
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    }
  },

  async refreshAfterSettingsClose() {
    this.loading = true;
    this.error = "";
    try {
      await this.refreshStatus();
      await this.refreshExtensionsList();
      this.connected = false;
      this.browsers = [];
      this.setActiveBrowserId(null);
      this.address = "";
      this.frameState = null;
      this.frameSrc = "";
      if (this.contextId) {
        await this.connectViewer();
      }
    } finally {
      this.loading = false;
    }
  },

  createExtensionWithAgent() {
    this._prefillAgentPrompt(
      [
        "Use the browser-extension-control skill to create a new Chrome extension for Agent Zero's Browser.",
        "Start by asking me for the extension name, purpose, target websites, and required permissions.",
        `Create it under ${this.extensionsRoot || EXTENSIONS_ROOT}/<extension-slug> and keep permissions minimal.`,
      ].join("\n")
    );
  },

  askAgentInstallExtension() {
    const url = String(this.extensionInstallUrl || "").trim();
    const prompt = url
      ? [
          "Use the browser-extension-control skill to review and optionally install this Chrome Web Store extension for Agent Zero's Browser.",
          `Chrome Web Store URL or id: ${url}`,
          "Explain the permissions and any sandbox risk before enabling it.",
        ].join("\n")
      : [
          "Use the browser-extension-control skill to help me install and review a Chrome Web Store extension for Agent Zero's Browser.",
          "Ask me for the Chrome Web Store URL or extension id first.",
          "Explain the permissions and any sandbox risk before enabling it.",
        ].join("\n");
    this._prefillAgentPrompt(prompt);
  },

  async installExtensionFromUrl() {
    const url = String(this.extensionInstallUrl || "").trim();
    this.extensionActionMessage = "";
    this.extensionActionError = "";
    if (!url) {
      this.extensionActionError = "Paste a Chrome Web Store URL or extension id first.";
      return;
    }

    this.extensionActionLoading = true;
    try {
      const response = await callJsonApi("/plugins/_browser/extensions", {
        action: "install_web_store",
        context_id: this.resolveContextId() || this.contextId,
        url,
      });
      if (!response?.ok) {
        throw new Error(response?.error || "Install failed.");
      }
      this.applyExtensionPayload(response);
      this.extensionInstallUrl = "";
      this.extensionActionMessage = `Installed ${response.name || response.id}.`;
      await this.refreshAfterSettingsClose();
    } catch (error) {
      this.extensionActionError = error instanceof Error ? error.message : String(error);
    } finally {
      this.extensionActionLoading = false;
    }
  },

  async setExtensionEnabled(extension, enabled, input = null) {
    const path = String(extension?.path || "");
    if (!path) return;
    const previous = Boolean(extension?.enabled);
    this.extensionActionMessage = "";
    this.extensionActionError = "";
    this.extensionToggleLoadingPath = path;
    try {
      const response = await callJsonApi("/plugins/_browser/extensions", {
        action: "set_extension_enabled",
        context_id: this.resolveContextId() || this.contextId,
        path,
        enabled: Boolean(enabled),
      });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not update extension.");
      }
      this.applyExtensionPayload(response);
      this.extensionActionMessage = `${enabled ? "Enabled" : "Disabled"} ${extension.name || "extension"}.`;
      await this.refreshAfterSettingsClose();
    } catch (error) {
      if (input) input.checked = previous;
      this.extensionActionError = error instanceof Error ? error.message : String(error);
    } finally {
      this.extensionToggleLoadingPath = "";
    }
  },

  async setBrowserModelPreset(value) {
    const presetName = String(value || "");
    this.modelPreset = presetName;
    this.extensionActionMessage = "";
    this.extensionActionError = "";
    this.modelPresetSaving = true;
    try {
      const response = await callJsonApi("/plugins/_browser/extensions", {
        action: "set_model_preset",
        context_id: this.resolveContextId() || this.contextId,
        model_preset: presetName,
      });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not update browser model preset.");
      }
      this.applyExtensionPayload(response);
      this.extensionActionMessage = "Browser model preset updated.";
    } catch (error) {
      this.extensionActionError = error instanceof Error ? error.message : String(error);
      await this.refreshExtensionsList();
    } finally {
      this.modelPresetSaving = false;
    }
  },

  modelPresetSummary() {
    if (!this.modelPreset) {
      return this.mainModelSummary ? `Using ${this.mainModelSummary}` : "Using Main Model";
    }
    const option = this.modelPresetOptions.find((preset) => preset?.name === this.modelPreset);
    return option?.summary || option?.label || this.modelPreset;
  },

  hasExtensionInstallUrl() {
    return Boolean(String(this.extensionInstallUrl || "").trim());
  },

  extensionAssistantActionLabel() {
    return "Scan with A0";
  },

  extensionVersionLabel(extension) {
    const version = String(extension?.version || "").trim();
    return version ? `v${version}` : "Unpacked extension";
  },

  extensionOpenUrl(extension) {
    return String(extension?.open_url || extension?.ui?.open_url || "").trim();
  },

  extensionHasOpenUi(extension) {
    return Boolean(this.extensionOpenUrl(extension));
  },

  extensionOpenTitle(extension) {
    const label = String(extension?.open_label || extension?.ui?.open_label || "Extension UI").trim();
    const name = String(extension?.name || "extension").trim();
    if (!extension?.enabled) {
      return `Enable ${name} before opening ${label}.`;
    }
    return `Open ${label} for ${name}`;
  },

  async openExtensionUi(extension) {
    const url = this.extensionOpenUrl(extension);
    if (!url) return;
    this.extensionActionMessage = "";
    this.extensionActionError = "";
    if (!extension?.enabled) {
      this.extensionActionError = `Enable ${extension?.name || "this extension"} before opening it.`;
      return;
    }
    this.closeExtensionsMenu();
    await this.command("open", { url });
  },

  _prefillAgentPrompt(prompt) {
    chatInputStore.message = prompt;
    chatInputStore.adjustTextareaHeight?.();
    chatInputStore.focus?.();
    this.closeExtensionsMenu();
  },

  async onOpen(element = null, options = {}) {
    const requestedBrowserId = this.normalizeBrowserId(
      options.requestedBrowserId ?? options.browserId ?? options.browser_id,
    );
    const requestedContextId = this.normalizeContextId(
      options.requestedContextId ?? options.contextId ?? options.context_id,
    );
    const nextMode = options?.mode === "modal" ? "modal" : "canvas";
    if (nextMode === "canvas" && !this.isCanvasSurfaceVisible(element)) {
      return;
    }
    const openSignature = this.surfaceOpenSignature(element, nextMode, requestedBrowserId, requestedContextId);
    if (this._openPromise && this._openSignature === openSignature) {
      return await this._openPromise;
    }
    const promise = this.openSurface(element, {
      ...options,
      requestedBrowserId,
      requestedContextId,
      nextMode,
    });
    this._openPromise = promise;
    this._openSignature = openSignature;
    try {
      return await promise;
    } finally {
      if (this._openPromise === promise) {
        this._openPromise = null;
        this._openSignature = "";
      }
    }
  },

  async openSurface(element = null, options = {}) {
    this.loading = true;
    this.error = "";
    const requestedBrowserId = this.normalizeBrowserId(
      options.requestedBrowserId ?? options.browserId ?? options.browser_id,
    );
    const requestedContextId = this.normalizeContextId(
      options.requestedContextId ?? options.contextId ?? options.context_id,
    );
    let targetContextId = requestedContextId
      || this.contextIdForBrowserId(requestedBrowserId)
      || this.resolveContextId();
    const nextMode = options?.nextMode || (options?.mode === "modal" ? "modal" : "canvas");
    if (nextMode === "canvas" && !this.isCanvasSurfaceVisible(element)) {
      this.loading = false;
      return;
    }
    const surfaceSequence = this._surfaceOpenSequence + 1;
    this._surfaceOpenSequence = surfaceSequence;
    this.prepareSurfaceOpen(nextMode, requestedBrowserId, requestedContextId);
    if (nextMode === "modal") {
      this.setupFloatingModal(element);
    } else {
      this.setupCanvasSurface(element);
    }
    try {
      if (!targetContextId && !this.activeBrowserContextId && !this.contextId) {
        targetContextId = await this.ensureContextId();
      }
      if (!this.isCurrentSurfaceOpen(surfaceSequence)) return;
      await this.refreshStatus();
      if (!this.isCurrentSurfaceOpen(surfaceSequence)) return;
      const viewport = await this.waitForSurfaceViewport({ sequence: surfaceSequence });
      if (!this.isCurrentSurfaceOpen(surfaceSequence)) return;
      if (nextMode === "canvas" && !viewport) return;
      this.resetRenderedFrameIfViewportChanged(viewport, requestedBrowserId, targetContextId);
      await this.connectViewer({
        browserId: requestedBrowserId,
        contextId: targetContextId,
        initialViewport: viewport,
      });
      if (!this.isCurrentSurfaceOpen(surfaceSequence)) return;
      await this.syncViewportAfterSurfaceOpen(surfaceSequence);
    } catch (error) {
      if (this.isCurrentSurfaceOpen(surfaceSequence)) {
        this.error = error instanceof Error ? error.message : String(error);
      }
    } finally {
      if (this.isCurrentSurfaceOpen(surfaceSequence)) {
        this.loading = false;
        if (this._mode === "canvas") {
          this._canvasSurfaceReadySequence = surfaceSequence;
          this.scheduleCanvasWidthNudgeAfterFirstFrame();
        }
      }
    }
  },

  surfaceOpenSignature(element = null, mode = "", browserId = null, contextId = "") {
    const root = element || globalThis.document?.querySelector(".browser-panel");
    if (root && !root.__browserSurfaceOpenId) {
      root.__browserSurfaceOpenId = makeViewerToken();
    }
    return [
      mode || "",
      this.normalizeContextId(contextId) || "",
      this.normalizeBrowserId(browserId) || "",
      root?.__browserSurfaceOpenId || "",
    ].join(":");
  },

  isCurrentSurfaceOpen(sequence) {
    return this._surfaceMounted && sequence === this._surfaceOpenSequence;
  },

  beginSurfaceHandoff() {
    if (this._surfaceHandoffTimer) {
      globalThis.clearTimeout(this._surfaceHandoffTimer);
    }
    this._surfaceHandoff = true;
    this._surfaceHandoffTimer = globalThis.setTimeout(() => {
      this._surfaceHandoff = false;
      this._surfaceHandoffTimer = null;
    }, 3000);
  },

  finishSurfaceHandoff() {
    if (this._surfaceHandoffTimer) {
      globalThis.clearTimeout(this._surfaceHandoffTimer);
      this._surfaceHandoffTimer = null;
    }
    this._surfaceHandoff = false;
  },

  cancelSurfaceHandoff() {
    if (this._surfaceHandoffTimer) {
      globalThis.clearTimeout(this._surfaceHandoffTimer);
      this._surfaceHandoffTimer = null;
    }
    this._surfaceHandoff = false;
  },

  releaseSurfaceBindings() {
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    this._stageResizeObserver?.disconnect?.();
    this._stageResizeObserver = null;
    this._stageElement = null;
  },

  isCanvasSurfaceVisible(element = null) {
    const root = element
      || globalThis.document?.querySelector?.(".browser-canvas-surface .browser-panel")
      || globalThis.document?.querySelector?.(".browser-panel");
    if (!root?.isConnected) return false;
    const surface = root.closest?.(".browser-canvas-surface");
    const stage = root.querySelector?.(".browser-stage") || root;
    const surfaceStyle = surface ? globalThis.getComputedStyle?.(surface) : null;
    const rootStyle = globalThis.getComputedStyle?.(root);
    if (surfaceStyle?.display === "none" || surfaceStyle?.visibility === "hidden") return false;
    if (rootStyle?.display === "none" || rootStyle?.visibility === "hidden") return false;
    const rect = stage.getBoundingClientRect?.();
    return Boolean(rect && Math.round(rect.width || 0) >= 80 && Math.round(rect.height || 0) >= 80);
  },

  isVisibleBrowserSurface() {
    if (!this._surfaceMounted) return false;
    if (this._mode === "canvas") {
      return Boolean(rightCanvasStore?.isSurfaceVisible?.("browser"))
        && this.isCanvasSurfaceVisible(globalThis.document?.querySelector?.(".browser-canvas-surface .browser-panel"));
    }

    const panel = globalThis.document?.querySelector?.(".modal .browser-panel");
    const modal = panel?.closest?.(".modal");
    if (!panel || !modal) return false;
    if (modal.classList.contains("modal-surface-parked") || modal.classList.contains("surface-modal-parked")) {
      return false;
    }
    const panelStyle = globalThis.getComputedStyle?.(panel);
    if (panelStyle?.display === "none" || panelStyle?.visibility === "hidden") return false;
    const rect = panel.getBoundingClientRect?.();
    return Boolean(rect && Math.round(rect.width || 0) >= 80 && Math.round(rect.height || 0) >= 80);
  },

  prepareSurfaceOpen(nextMode, requestedBrowserId = null, requestedContextId = "") {
    const targetBrowserId = requestedBrowserId || this.activeBrowserId || this.firstBrowserId(requestedContextId);
    const targetContextId = this.normalizeContextId(
      requestedContextId
      || this.contextIdForBrowserId(targetBrowserId)
      || this.resolveContextId()
      || this.activeBrowserContextId
      || this.contextId,
    );
    const targetChanged = Boolean(
      targetBrowserId
      && this.activeBrowserId
      && !this.sameBrowserTab(targetBrowserId, targetContextId, this.activeBrowserId, this.activeBrowserContextId),
    );
    this._mode = nextMode;
    this._surfaceMounted = true;
    this._surfaceOpenedAt = Date.now();
    this._lastViewportKey = "";
    if (this.frameSrc && !targetChanged) {
      this._surfaceSwitching = false;
      this.switchingBrowserId = null;
      return;
    }
    if (!targetBrowserId) return;

    this.resetRenderedFrame();
    this.resetViewportTracking();
    this._surfaceSwitching = Boolean(targetBrowserId);
    this.switchingBrowserId = targetBrowserId;
  },

  resetViewportTracking() {
    this._lastViewportKey = "";
    this._lastViewport = null;
  },

  resetRenderedFrame() {
    this.cancelFrameRender();
    this.frameSrc = "";
    this._lastFrameDimensions = null;
    this._lastFrameAt = 0;
  },

  resetRenderedFrameIfViewportChanged(viewport = null, requestedBrowserId = null, requestedContextId = "") {
    if (!viewport || !this.frameSrc || !this._lastViewport) return;
    const targetBrowserId = requestedBrowserId || this.activeBrowserId || this.firstBrowserId();
    const targetContextId = this.normalizeContextId(requestedContextId || this.contextIdForBrowserId(targetBrowserId) || this.activeBrowserContextId);
    if (!this.sameBrowserTab(this._lastViewport.browserId, this._lastViewport.contextId, targetBrowserId, targetContextId)) return;
    const changed = Math.abs(this._lastViewport.width - viewport.width) > VIEWPORT_SYNC_SIZE_TOLERANCE
      || Math.abs(this._lastViewport.height - viewport.height) > VIEWPORT_SYNC_SIZE_TOLERANCE;
    if (!changed) return;

    this.cancelFrameRender();
    this.resetViewportTracking();
    this._surfaceSwitching = true;
    this.switchingBrowserId = targetBrowserId;
  },

  async waitForSurfaceViewport(options = {}) {
    const sequence = Number(options.sequence || 0);
    const startedAt = Date.now();
    let lastKey = "";
    let stableCount = 0;
    while (Date.now() - startedAt <= SURFACE_VIEWPORT_MAX_WAIT_MS) {
      await nextAnimationFrame();
      if (sequence && !this.isCurrentSurfaceOpen(sequence)) {
        return null;
      }
      const viewport = this.surfaceViewportMeasurement();
      if (!viewport) continue;
      const key = `${viewport.rawWidth}x${viewport.rawHeight}`;
      if (key === lastKey) {
        stableCount += 1;
        const canvasSettled = this._mode !== "canvas"
          || !this._surfaceOpenedAt
          || Date.now() - this._surfaceOpenedAt >= CANVAS_VIEWPORT_SETTLE_MS;
        if (canvasSettled && stableCount >= SURFACE_VIEWPORT_STABLE_FRAMES) {
          return { width: viewport.width, height: viewport.height };
        }
      } else {
        stableCount = 0;
        lastKey = key;
      }
    }
    const fallbackViewport = this.currentViewportSize();
    return fallbackViewport;
  },

  async syncViewportAfterSurfaceOpen(sequence = this._surfaceOpenSequence) {
    if (!this.connected || !this.activeBrowserId) return;
    await this.waitForSurfaceViewport({ sequence });
    if (!this.isCurrentSurfaceOpen(sequence)) {
      return;
    }
    await this.syncViewport(true, { restartStream: this._mode === "canvas" });
    if (this._mode !== "canvas") return;
    this.scheduleViewportSyncForSurface(sequence, 240);
    this.scheduleViewportSyncForSurface(sequence, 520);
  },

  scheduleViewportSyncForSurface(sequence, delayMs = 0) {
    globalThis.setTimeout?.(() => {
      if (!this.isCurrentSurfaceOpen(sequence) || this._mode !== "canvas") {
        return;
      }
      this.queueViewportSync(true);
    }, delayMs);
  },

  async connectViewer(options = {}) {
    let contextId = "";
    const requestedBrowserId = this.normalizeBrowserId(options.browserId ?? this.activeBrowserId);
    const requestedContextId = this.normalizeContextId(
      options.contextId
      ?? options.context_id
      ?? this.contextIdForBrowserId(requestedBrowserId)
      ?? this.activeBrowserContextId
      ?? this.contextId
    );
    try {
      contextId = requestedContextId || await this.ensureContextId();
    } catch (error) {
      this.connected = false;
      this.switchingBrowserId = null;
      this._surfaceSwitching = false;
      throw error;
    }
    if (!contextId) {
      this.connected = false;
      this.error = "Could not create a chat for Browser.";
      this.switchingBrowserId = null;
      this._surfaceSwitching = false;
      return;
    }
    const previousContextId = this.normalizeContextId(this.contextId);
    if (previousContextId && previousContextId !== contextId) {
      try {
        await websocket.emit("browser_viewer_unsubscribe", { context_id: previousContextId });
      } catch {}
    }
    this.contextId = contextId;
    const sequence = this._connectSequence + 1;
    const viewerToken = makeViewerToken();
    this._connectSequence = sequence;
    this._viewerToken = viewerToken;
    this.error = "";
    await this._bindSocketEvents();
    if (sequence !== this._connectSequence || viewerToken !== this._viewerToken) {
      return;
    }
    const initialViewport = options.initialViewport || this.currentViewportSize();
    let response;
    try {
      response = await websocket.request(
        "browser_viewer_subscribe",
        {
          context_id: contextId,
          browser_id: requestedBrowserId,
          viewer_id: viewerToken,
          create_browser: Boolean(options.createBrowser || options.create_browser),
          viewport_width: initialViewport?.width,
          viewport_height: initialViewport?.height,
        },
        {
          timeoutMs: this.browserInstallExpected
            ? BROWSER_FIRST_INSTALL_TIMEOUT_MS
            : BROWSER_SUBSCRIBE_TIMEOUT_MS,
        },
      );
    } catch (error) {
      if (sequence === this._connectSequence && viewerToken === this._viewerToken) {
        this.switchingBrowserId = null;
        this._surfaceSwitching = false;
        throw error;
      }
      return;
    }
    if (sequence !== this._connectSequence || viewerToken !== this._viewerToken) {
      return;
    }
    const data = firstOk(response);
    this.applyBrowserListing(data.browsers || [], contextId, { replaceAll: Boolean(data.all_browsers) });
    this.setActiveBrowserId(
      data.active_browser_id || requestedBrowserId || this.activeBrowserId || null,
      data.active_browser_context_id || contextId,
    );
    this.applySnapshot(data.snapshot);
	    this.connected = true;
	    this.browserInstallExpected = false;
	  },

  async _bindSocketEvents() {
    if (!this._frameOff) {
      const frameHandler = ({ data }) => {
        if (data?.context_id !== this.contextId) return;
        if (data?.viewer_id && data.viewer_id !== this._viewerToken) return;
        const incomingContextId = this.normalizeContextId(data.context_id || this.contextId);
        const incomingBrowserId = this.normalizeBrowserId(data.browser_id || data.state?.id);
        this.applyBrowserListing(data.browsers || [], incomingContextId, { replaceContext: true });
        if (incomingBrowserId && !this.activeBrowserId) {
          this.setActiveBrowserId(incomingBrowserId, incomingContextId);
        }
        if (
          incomingBrowserId
          && this.activeBrowserId
          && !this.sameBrowserTab(incomingBrowserId, incomingContextId, this.activeBrowserId, this.activeBrowserContextId)
        ) {
          return;
        }
        if (data.state) {
          this.frameState = data.state;
        }
        if (!this.addressFocused && data.state?.currentUrl) {
          this.address = data.state.currentUrl;
        }
        if (data.image) {
          const frameBrowserId = incomingBrowserId || this.activeBrowserId;
          this.queueFrameRender(`data:${data.mime || "image/jpeg"};base64,${data.image}`, {
            browserId: frameBrowserId,
            contextId: incomingContextId,
            onAccepted: () => {
              if (
                this.sameBrowserId(this.switchingBrowserId, frameBrowserId)
                && this.normalizeContextId(this.activeBrowserContextId) === incomingContextId
              ) {
                this.switchingBrowserId = null;
              }
              this._surfaceSwitching = false;
            },
          });
        } else if (!data.state) {
          this.cancelFrameRender();
          this.frameSrc = "";
        }
        if (!data.image && !data.state) {
          if (!this.activeBrowserId) {
            this.setActiveBrowserId(null, "");
            this.frameState = null;
            this.frameSrc = "";
          }
        }
        this._lastFrameAt = Date.now();
      };
      await websocket.on("browser_viewer_frame", frameHandler);
      this._frameOff = () => websocket.off("browser_viewer_frame", frameHandler);
    }
	    if (!this._stateOff) {
	      const stateHandler = ({ data }) => {
	        if (data?.context_id !== this.contextId) return;
	        if (data?.viewer_id && data.viewer_id !== this._viewerToken) return;
        const commandContextId = this.normalizeContextId(data.active_browser_context_id || data.context_id || this.contextId);
        this.applyBrowserListing(data.browsers || [], commandContextId, { replaceAll: Boolean(data.all_browsers) });
        const command = String(data.command || "").toLowerCase();
        const commandBrowserId = this.normalizeBrowserId(data.browser_id);
        const result = data.result || {};
        const resultState = this.stateFromCommandResult(result);
        const resultContextId = this.normalizeContextId(
          result.context_id
          || result.state?.context_id
          || commandContextId
        );
        const preferredBrowserId = this.normalizeBrowserId(
          result.id
          || result.state?.id
          || data.last_interacted_browser_id
          || this.activeBrowserId
          || this.firstBrowserId(resultContextId)
        );
	        if (
	          !this.activeBrowserId
	          || command === "open"
	          || command === "close"
	          || this.sameBrowserTab(commandBrowserId, commandContextId, this.activeBrowserId, this.activeBrowserContextId)
	        ) {
	          this.setActiveBrowserId(preferredBrowserId, resultContextId);
	        }
	        this.applyActiveFrameState(resultState || this.browserById(this.activeBrowserId, this.activeBrowserContextId));
	        this.applySnapshot(data.snapshot);
	      };
      await websocket.on("browser_viewer_state", stateHandler);
      this._stateOff = () => websocket.off("browser_viewer_state", stateHandler);
    }
  },

  queueFrameRender(frameSrc, options = {}) {
    this._pendingFrameSrc = frameSrc;
    this._pendingFrameOptions = options || null;
    if (this._frameRenderHandle) return;
    const schedule = globalThis.requestAnimationFrame?.bind(globalThis);
    if (schedule) {
      this._frameRenderCancel = globalThis.cancelAnimationFrame?.bind(globalThis) || null;
      this._frameRenderHandle = schedule(() => this.flushFrameRender());
      return;
    }
    this._frameRenderCancel = globalThis.clearTimeout?.bind(globalThis) || null;
    this._frameRenderHandle = globalThis.setTimeout(() => this.flushFrameRender(), 16);
  },

  flushFrameRender() {
    this._frameRenderHandle = null;
    this._frameRenderCancel = null;
    const frameSrc = this._pendingFrameSrc || "";
    const options = this._pendingFrameOptions || {};
    this._pendingFrameSrc = "";
    this._pendingFrameOptions = null;
    const sequence = this._frameRenderSequence + 1;
    const surfaceSequence = this._surfaceOpenSequence;
    this._frameRenderSequence = sequence;
    void this.renderDecodedFrame(frameSrc, options, sequence, surfaceSequence);
  },

  async renderDecodedFrame(frameSrc, options = {}, sequence = 0, surfaceSequence = this._surfaceOpenSequence) {
    if (!frameSrc) {
      if (sequence === this._frameRenderSequence) {
        this.frameSrc = "";
      }
      return;
    }
    const dimensions = await loadFrameDimensions(frameSrc);
    if (sequence !== this._frameRenderSequence || surfaceSequence !== this._surfaceOpenSequence) {
      return;
    }
    const viewport = this.currentViewportSize() || this._lastViewport;
    if (!this.frameMatchesViewport(dimensions, viewport)) {
      this.requestViewportSyncAfterRejectedFrame();
      if (!this.shouldAcceptMismatchedFrame(dimensions)) {
        return;
      }
    }
    this.frameSrc = frameSrc;
    this._lastFrameDimensions = dimensions;
    this._lastFrameAt = Date.now();
    options?.onAccepted?.();
    this._canvasFirstFrameAcceptedSequence = surfaceSequence;
    this.scheduleCanvasWidthNudgeAfterFirstFrame();
  },

  shouldAcceptMismatchedFrame(dimensions = null) {
    return Boolean(
      dimensions?.width
      && dimensions?.height
      && (!this.frameSrc || this._surfaceSwitching || this.isSwitchingBrowser())
    );
  },

  scheduleCanvasWidthNudgeAfterFirstFrame() {
    const surfaceSequence = this._surfaceOpenSequence;
    if (this._mode !== "canvas" || !this.isCurrentSurfaceOpen(surfaceSequence) || !this.activeBrowserId) {
      return;
    }
    if (this._canvasFirstFrameNudgeSequence === surfaceSequence) {
      return;
    }
    if (
      this._canvasSurfaceReadySequence !== surfaceSequence
      || this._canvasFirstFrameAcceptedSequence !== surfaceSequence
    ) {
      return;
    }
    this._canvasFirstFrameNudgeSequence = surfaceSequence;

    void (async () => {
      await nextAnimationFrame();
      await nextAnimationFrame();
      if (!this.isCurrentSurfaceOpen(surfaceSequence) || this._mode !== "canvas") {
        return;
      }
      this.forceRightCanvasWidthNudge();
    })();
  },

  forceRightCanvasWidthNudge() {
    const canvas = rightCanvasStore;
    if (!canvas || canvas.isMobileMode || !canvas.isOpen || canvas.activeSurfaceId !== "browser") {
      return;
    }

    const currentWidth = Number(canvas.width || 0);
    if (!Number.isFinite(currentWidth) || currentWidth <= 0) {
      return;
    }
    const maxWidth = Number(canvas.maxWidth?.() || currentWidth);
    const minWidth = Number(canvas.minWidth || 420);
    const direction = currentWidth < maxWidth ? 1 : -1;
    const nudgedWidth = currentWidth + direction;
    if (nudgedWidth < minWidth || nudgedWidth > maxWidth || nudgedWidth === currentWidth) {
      return;
    }

    canvas.setWidth?.(nudgedWidth, { persist: false });
    this.queueViewportSync(true);
  },

  frameMatchesViewport(dimensions = null, viewport = null) {
    if (!dimensions?.width || !dimensions?.height || !viewport?.width || !viewport?.height) {
      return false;
    }
    return Math.abs(Number(dimensions.width) - Number(viewport.width)) <= VIEWPORT_SYNC_SIZE_TOLERANCE
      && Math.abs(Number(dimensions.height) - Number(viewport.height)) <= VIEWPORT_SYNC_SIZE_TOLERANCE;
  },

  requestViewportSyncAfterRejectedFrame() {
    const now = Date.now();
    if (now - this._lastFrameRejectSyncAt < FRAME_REJECT_SYNC_COOLDOWN_MS) {
      return;
    }
    this._lastFrameRejectSyncAt = now;
    this.queueViewportSync(true);
  },

  clearRenderedFrameIfViewportChanged() {
    const viewport = this.currentViewportSize();
    if (!this.frameSrc || !this._lastFrameDimensions || !viewport) return;
    if (this.frameMatchesViewport(this._lastFrameDimensions, viewport)) return;
    this.cancelFrameRender();
    this.resetViewportTracking();
    if (this.activeBrowserId) {
      this._surfaceSwitching = true;
      this.switchingBrowserId = this.activeBrowserId;
    }
  },

  cancelFrameRender() {
    if (this._frameRenderHandle && this._frameRenderCancel) {
      this._frameRenderCancel(this._frameRenderHandle);
    }
    this._frameRenderHandle = null;
    this._frameRenderCancel = null;
    this._pendingFrameSrc = "";
    this._pendingFrameOptions = null;
    this._frameRenderSequence += 1;
  },

  beginCommand() {
    this._commandInFlightCount += 1;
    this.commandInFlight = true;
  },

  finishCommand() {
    this._commandInFlightCount = Math.max(0, this._commandInFlightCount - 1);
    this.commandInFlight = this._commandInFlightCount > 0;
  },

  async command(command, extra = {}) {
    this.error = "";
    this.annotationError = "";
    this.beginCommand();
    const previousActiveBrowserId = this.activeBrowserId;
    const previousActiveContextId = this.activeBrowserContextId;
    const commandName = String(command || "").toLowerCase();
    try {
      const targetContextId = commandName === "open"
        ? await this.contextIdForNewBrowser()
        : this.normalizeContextId(extra.context_id || extra.contextId) || await this.contextIdForActiveBrowser();
      const targetBrowserId = this.normalizeBrowserId(extra.browser_id ?? this.activeBrowserId);
      this.contextId = targetContextId;
      const response = await websocket.request(
        "browser_viewer_command",
        {
          ...extra,
          context_id: targetContextId,
          browser_id: targetBrowserId,
          viewer_id: this._viewerToken,
          command,
        },
        { timeoutMs: 20000 },
      );
      const data = firstOk(response);
      this.applyBrowserListing(data.browsers || [], targetContextId, { replaceAll: Boolean(data.all_browsers) });
      const result = data.result || {};
      const resultContextId = this.normalizeContextId(
        result.context_id
        || result.state?.context_id
        || data.active_browser_context_id
        || targetContextId
      );
      const preferredBrowser = this.browserById(
        result.id
        || result.state?.id
        || result.last_interacted_browser_id
        || data.last_interacted_browser_id,
        resultContextId,
      )
        || this.browserById(this.activeBrowserId, this.activeBrowserContextId)
        || this.firstBrowser(resultContextId)
        || this.firstBrowser();
      this.setActiveBrowserId(preferredBrowser?.id || null, preferredBrowser?.context_id || resultContextId);
      this.applyActiveFrameState(
        this.stateFromCommandResult(result)
        || this.browserById(this.activeBrowserId, this.activeBrowserContextId)
      );
      if (!this.activeBrowserId) {
        this.frameState = null;
        this.frameSrc = "";
      }
      if (result.state?.currentUrl || result.currentUrl) {
        this.address = result.state?.currentUrl || result.currentUrl;
      }
      this.applySnapshot(data.snapshot);
      if (["navigate", "back", "forward", "reload", "close"].includes(commandName)) {
        this.clearAnnotationsForBrowser(previousActiveBrowserId, null, previousActiveContextId);
        this.cancelAnnotationDraft();
      }
      const activeChanged = this.activeBrowserId
        && !this.sameBrowserTab(
          this.activeBrowserId,
          this.activeBrowserContextId,
          previousActiveBrowserId,
          previousActiveContextId,
        );
      if ((commandName === "open" || commandName === "close" || activeChanged) && this.contextId && this.activeBrowserId) {
        await this.connectViewer({
          browserId: this.activeBrowserId,
          contextId: this.activeBrowserContextId,
        });
      } else if (["navigate", "back", "forward", "reload"].includes(commandName)) {
        await this.restartCanvasStreamAfterPageChange();
      }
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      this.finishCommand();
    }
  },

  async restartCanvasStreamAfterPageChange() {
    const surfaceSequence = this._surfaceOpenSequence;
    if (this._mode !== "canvas" || !this.isCurrentSurfaceOpen(surfaceSequence) || !this.activeBrowserId) {
      return;
    }
    await this.waitForSurfaceViewport({ sequence: surfaceSequence });
    if (this._mode !== "canvas" || !this.isCurrentSurfaceOpen(surfaceSequence) || !this.activeBrowserId) {
      return;
    }
    await this.syncViewport(true, { restartStream: true });
  },

  async go() {
    const url = String(this.address || "").trim();
    if (!url) return;
    this.addressFocused = false;
    globalThis.document?.activeElement?.blur?.();
    if (this.activeBrowserId) {
      await this.command("navigate", { url });
    } else {
      await this.command("open", { url });
    }
  },

  async openUrlIntent(url = "", options = {}) {
    if (this._openPromise) {
      try {
        await this._openPromise;
      } catch {}
    }
    if (!this._surfaceMounted) return false;
    const targetUrl = String(url || "").trim();
    if (targetUrl) {
      await this.command("open", {
        url: targetUrl,
        source: options?.source || "desktop-url",
      });
      return true;
    }
    if (!this.activeBrowserId) {
      await this.command("open");
    }
    return true;
  },

  onAddressFocus() {
    this.addressFocused = true;
  },

  onAddressBlur() {
    this.addressFocused = false;
    if (this.frameState?.currentUrl && !String(this.address || "").trim()) {
      this.address = this.frameState.currentUrl;
    }
  },

  async selectBrowser(id, contextId = "") {
    const targetId = this.normalizeBrowserId(id);
    const targetContextId = this.normalizeContextId(contextId || this.contextIdForBrowserId(targetId));
    if (!targetId) {
      await this.openNewBrowser();
      return;
    }
    if (
      this.sameBrowserTab(targetId, targetContextId, this.activeBrowserId, this.activeBrowserContextId)
      && this.connected
      && !this.isSwitchingBrowser()
    ) {
      return;
    }
    const browser = this.browserById(targetId, targetContextId);
    this.error = "";
    this.switchingBrowserId = targetId;
    this.cancelFrameRender();
    this.frameSrc = "";
    this.frameState = browser || null;
    if (!this.addressFocused && browser?.currentUrl) {
      this.address = browser.currentUrl;
    }
    this.setActiveBrowserId(targetId, targetContextId);
    if (this.activeBrowserContextId) {
      try {
        await this.connectViewer({ browserId: targetId, contextId: targetContextId });
      } catch (error) {
        if (
          this.sameBrowserId(this.switchingBrowserId, targetId)
          && this.normalizeContextId(this.activeBrowserContextId) === targetContextId
        ) {
          this.switchingBrowserId = null;
        }
        this.error = error instanceof Error ? error.message : String(error);
      }
    }
  },

  async openNewBrowser() {
    await this.command("open");
  },

  isClosingBrowser(id, contextId = "") {
    const browserId = this.normalizeBrowserId(id);
    const key = this.browserTabKey({
      id: browserId,
      context_id: contextId || this.contextIdForBrowserId(browserId),
    });
    return Boolean(key && this._closingBrowserIds[key]);
  },

  markBrowserClosing(id, contextId = "", closing = true) {
    const browserId = this.normalizeBrowserId(id);
    if (!browserId) return;
    const key = this.browserTabKey({
      id: browserId,
      context_id: contextId || this.contextIdForBrowserId(browserId),
    });
    if (!key) return;
    const nextClosing = { ...this._closingBrowserIds };
    if (closing) {
      nextClosing[key] = true;
    } else {
      delete nextClosing[key];
    }
    this._closingBrowserIds = nextClosing;
  },

  async closeBrowser(id, contextId = "") {
    const browserId = this.normalizeBrowserId(id);
    const browserContextId = this.normalizeContextId(contextId || this.contextIdForBrowserId(browserId));
    if (!browserId || !browserContextId || this.isClosingBrowser(browserId, browserContextId)) return;
    this.markBrowserClosing(browserId, browserContextId, true);
    try {
      await this.command("close", { browser_id: browserId, context_id: browserContextId });
    } finally {
      this.markBrowserClosing(browserId, browserContextId, false);
    }
  },

  isActiveBrowser(browser) {
    return this.sameBrowserTab(browser?.id, browser?.context_id, this.activeBrowserId, this.activeBrowserContextId);
  },

  browserTabTitle(browser) {
    const title = String(browser?.title || "").trim();
    const url = String(browser?.currentUrl || "").trim();
    return title || url || "about:blank";
  },

  browserTabLabel(browser) {
    const id = browser?.id ? `#${browser.id}` : "Browser";
    return [id, this.browserTabTitle(browser)].filter(Boolean).join(" ");
  },

  browserTabTooltip(browser) {
    const chatTitle = this.browserChatTitle(browser);
    return [this.browserTabLabel(browser), chatTitle ? `Chat: ${chatTitle}` : ""]
      .filter(Boolean)
      .join("\n");
  },

  browserTabKey(browser = {}) {
    const id = this.normalizeBrowserId(browser?.id ?? browser);
    const contextId = this.normalizeContextId(browser?.context_id || browser?.contextId || this.activeBrowserContextId || this.contextId);
    return id && contextId ? `${contextId}:${id}` : "";
  },

  browserChatTitle(browser = {}) {
    const contextId = this.normalizeContextId(browser?.context_id || browser?.contextId);
    if (!contextId) return "";
    const context = chatsStore.contexts?.find?.((item) => item?.id === contextId);
    return String(context?.name || context?.title || "").trim();
  },

  firstBrowser(contextId = "") {
    const normalizedContextId = this.normalizeContextId(contextId);
    const browsers = Array.isArray(this.browsers) ? this.browsers : [];
    if (normalizedContextId) {
      const scoped = browsers.find((browser) => this.normalizeContextId(browser?.context_id) === normalizedContextId);
      if (scoped) return scoped;
    }
    return browsers[0] || null;
  },

  firstBrowserInContext(contextId = "") {
    const normalizedContextId = this.normalizeContextId(contextId);
    if (!normalizedContextId || !Array.isArray(this.browsers)) return null;
    return this.browsers.find((browser) => this.normalizeContextId(browser?.context_id) === normalizedContextId) || null;
  },

  firstBrowserId(contextId = "") {
    return this.firstBrowser(contextId)?.id || null;
  },

  normalizeBrowserId(id) {
    return Number(id) || null;
  },

  sameBrowserId(left, right) {
    const leftId = this.normalizeBrowserId(left);
    const rightId = this.normalizeBrowserId(right);
    return Boolean(leftId && rightId && leftId === rightId);
  },

  sameBrowserTab(leftId, leftContextId, rightId, rightContextId) {
    return this.sameBrowserId(leftId, rightId)
      && this.normalizeContextId(leftContextId) === this.normalizeContextId(rightContextId);
  },

  browserById(id, contextId = "") {
    const numeric = this.normalizeBrowserId(id);
    if (!numeric || !Array.isArray(this.browsers)) return null;
    const normalizedContextId = this.normalizeContextId(contextId);
    return this.browsers.find((browser) => (
      Number(browser?.id) === numeric
      && (!normalizedContextId || this.normalizeContextId(browser?.context_id) === normalizedContextId)
    )) || null;
  },

  contextIdForBrowserId(id) {
    const numeric = this.normalizeBrowserId(id);
    if (!numeric) return "";
    if (this.sameBrowserId(numeric, this.activeBrowserId) && this.activeBrowserContextId) {
      return this.activeBrowserContextId;
    }
    return this.normalizeContextId(this.browserById(numeric)?.context_id);
  },

  applyBrowserListing(browsers = [], fallbackContextId = "", options = {}) {
    const incoming = Array.isArray(browsers)
      ? browsers.map((browser) => ({
          ...browser,
          context_id: this.normalizeContextId(browser?.context_id || fallbackContextId),
        })).filter((browser) => browser.id && browser.context_id)
      : [];
    const incomingKeys = new Set(incoming.map((browser) => this.browserTabKey(browser)));
    const fallback = this.normalizeContextId(fallbackContextId);
    const existing = Array.isArray(this.browsers) ? this.browsers : [];
    const retained = options.replaceAll
      ? []
      : existing.filter((browser) => {
          const key = this.browserTabKey(browser);
          if (incomingKeys.has(key)) return false;
          if (options.replaceContext && fallback && this.normalizeContextId(browser?.context_id) === fallback) return false;
          return true;
        });
    this.browsers = [...retained, ...incoming];
  },

  stateFromCommandResult(result = {}) {
    if (result?.state?.id || result?.state?.currentUrl || result?.state?.title) {
      return result.state;
    }
    if (result?.id || result?.currentUrl || result?.title) {
      return result;
    }
    return null;
  },

  applyActiveFrameState(nextState = null) {
    if (!nextState) return;
    const stateId = this.normalizeBrowserId(nextState.id);
    const stateContextId = this.normalizeContextId(nextState.context_id || this.activeBrowserContextId);
    if (
      stateId
      && this.activeBrowserId
      && !this.sameBrowserTab(stateId, stateContextId, this.activeBrowserId, this.activeBrowserContextId)
    ) {
      return;
    }
    const previousUrl = String(this.frameState?.currentUrl || "");
    const nextUrl = String(nextState.currentUrl || "");
    this.frameState = nextState;
    if (previousUrl && nextUrl && previousUrl !== nextUrl) {
      this.cancelAnnotationDraft();
    }
    if (!this.addressFocused && nextState.currentUrl) {
      this.address = nextState.currentUrl;
    }
  },

	  applySnapshot(snapshot = null) {
	    if (!snapshot?.image) return;
	    const snapshotId = this.normalizeBrowserId(snapshot.browser_id || snapshot.state?.id);
    const snapshotContextId = this.normalizeContextId(snapshot.context_id || snapshot.state?.context_id || this.activeBrowserContextId);
	    if (
      snapshotId
      && this.activeBrowserId
      && !this.sameBrowserTab(snapshotId, snapshotContextId, this.activeBrowserId, this.activeBrowserContextId)
    ) {
	      return;
	    }
	    if (snapshot.state) {
	      this.applyActiveFrameState(snapshot.state);
	    }
	    const frameBrowserId = snapshotId || this.activeBrowserId;
	    this.queueFrameRender(`data:${snapshot.mime || "image/jpeg"};base64,${snapshot.image}`, {
	      browserId: frameBrowserId,
      contextId: snapshotContextId,
	      onAccepted: () => {
	        if (
          this.sameBrowserId(this.switchingBrowserId, frameBrowserId)
          && this.normalizeContextId(this.activeBrowserContextId) === snapshotContextId
        ) {
	          this.switchingBrowserId = null;
	        }
	        this._surfaceSwitching = false;
	      },
	    });
	  },

  isSwitchingBrowser() {
    return Boolean(
      this.switchingBrowserId
      && this.sameBrowserId(this.switchingBrowserId, this.activeBrowserId)
      && this.normalizeContextId(this.contextId) === this.normalizeContextId(this.activeBrowserContextId)
    );
  },

  isBusy() {
    return Boolean(this.loading || this.commandInFlight || this._surfaceSwitching || this.isSwitchingBrowser());
  },

  setActiveBrowserId(id, contextId = "") {
    const previous = this.activeBrowserId;
    const previousContextId = this.activeBrowserContextId;
    const numeric = this.normalizeBrowserId(id);
    const normalizedContextId = this.normalizeContextId(contextId || this.contextIdForBrowserId(numeric));
    const exists = !numeric
      || !Array.isArray(this.browsers)
      || this.browsers.some((browser) => (
        Number(browser.id) === numeric
        && (!normalizedContextId || this.normalizeContextId(browser.context_id) === normalizedContextId)
      ));
    this.activeBrowserId = exists ? numeric : null;
    this.activeBrowserContextId = this.activeBrowserId ? normalizedContextId : "";
    this.contextId = this.activeBrowserContextId || this.contextId;
    if (this.activeBrowserId !== previous || this.activeBrowserContextId !== previousContextId) {
      this._lastViewportKey = "";
      this._lastViewport = null;
      this.cancelAnnotationDraft();
    }
  },

  pointerCoordinatesFor(event, element = null) {
    const target = element || event?.currentTarget;
    if (!target) return null;
    const rect = target.getBoundingClientRect();
    const naturalWidth = target.naturalWidth || rect.width;
    const naturalHeight = target.naturalHeight || rect.height;
    let contentLeft = rect.left;
    let contentTop = rect.top;
    let contentWidth = rect.width;
    let contentHeight = rect.height;

    const objectFit = globalThis.getComputedStyle?.(target)?.objectFit || "";
    if (
      target.matches?.(".browser-frame")
      && ["contain", "scale-down"].includes(objectFit)
      && naturalWidth > 0
      && naturalHeight > 0
      && rect.width > 0
      && rect.height > 0
    ) {
      const naturalRatio = naturalWidth / naturalHeight;
      const rectRatio = rect.width / rect.height;
      if (naturalRatio > rectRatio) {
        contentWidth = rect.width;
        contentHeight = rect.width / naturalRatio;
        contentTop = rect.top + (rect.height - contentHeight) / 2;
      } else {
        contentHeight = rect.height;
        contentWidth = rect.height * naturalRatio;
        contentLeft = rect.left + (rect.width - contentWidth) / 2;
      }
    }

    const relativeX = (event.clientX - contentLeft) / Math.max(1, contentWidth);
    const relativeY = (event.clientY - contentTop) / Math.max(1, contentHeight);
    return {
      x: Math.max(0, Math.min(naturalWidth, relativeX * naturalWidth)),
      y: Math.max(0, Math.min(naturalHeight, relativeY * naturalHeight)),
    };
  },

  handleKeydown(event) {
    const annotateShortcut = event?.key === "." && (event.metaKey || event.ctrlKey) && !event.altKey;
    if (annotateShortcut && this._surfaceMounted) {
      event.preventDefault();
      event.stopPropagation?.();
      this.toggleAnnotationMode();
      return;
    }

    if (this.annotating) {
      if (event?.key === "Escape") {
        event.preventDefault();
        if (this.annotationDraft || this.annotationDragRect) {
          this.cancelAnnotationDraft();
        } else {
          this.toggleAnnotationMode(false);
        }
      }
      return;
    }

    if (this.handleVisualBrowserShortcut(event)) {
      return;
    }

    void this.sendKey(event);
  },

  handleVisualBrowserShortcut(event) {
    const shortcut = this.visualBrowserShortcut(event);
    if (!shortcut) return false;
    event.preventDefault();
    event.stopPropagation?.();

    if (shortcut.action === "paste") {
      void this.pasteHostClipboardToBrowser();
      return true;
    }
    if (shortcut.action === "copy" || shortcut.action === "cut") {
      void this.copyBrowserClipboardToHost(shortcut.action);
      return true;
    }
    if (shortcut.key) {
      void this.sendShortcut(shortcut.key);
      return true;
    }
    return false;
  },

  visualBrowserShortcut(event) {
    if (!this.shouldHandleVisualBrowserShortcut(event)) return null;
    const key = String(event?.key || "").toLowerCase();
    const primary = Boolean(event?.ctrlKey || event?.metaKey);
    const shift = Boolean(event?.shiftKey);

    if (!primary && shift && key === "insert") {
      return { action: "paste" };
    }
    if (!primary || event?.altKey) return null;

    if (key === "v") return { action: "paste" };
    if (!shift && (key === "c" || key === "insert")) return { action: "copy" };
    if (!shift && key === "x") return { action: "cut" };
    if (!shift && key === "a") return { key: "Control+A" };
    if (key === "z") return { key: shift ? "Control+Shift+Z" : "Control+Z" };
    if (!shift && key === "y") return { key: "Control+Y" };
    return null;
  },

  shouldHandleVisualBrowserShortcut(event) {
    if (!this._surfaceMounted || !this.activeBrowserId || this.annotating) return false;
    if (isLocalEditableTarget(event?.target)) return false;
    const key = String(event?.key || "").toLowerCase();
    if (!BROWSER_VISUAL_SHORTCUT_KEYS.has(key)) return false;
    return Boolean(this.visualBrowserStageForEvent(event));
  },

  visualBrowserStageForEvent(event) {
    const element = elementFromTarget(event?.target);
    const blockingUi = element?.closest?.(
      ".browser-toolbar, .browser-meta, .browser-extension-dropdown, .browser-annotation-popover, .browser-annotation-tray, button, a",
    );
    if (blockingUi) return null;

    const stage = element?.closest?.(".browser-stage");
    if (stage?.closest?.(".browser-panel")) return stage;

    const activeElement = globalThis.document?.activeElement;
    const activeStage = activeElement?.closest?.(".browser-stage");
    if (activeStage?.closest?.(".browser-panel")) return activeStage;
    return null;
  },

  handleStageWheel(event) {
    if (this.annotating) return;
    void this.sendWheel(event);
  },

  toggleAnnotationMode(force = null) {
    const nextValue = force === null ? !this.annotating : Boolean(force);
    if (nextValue && !this.canAnnotate()) return;

    this.annotating = nextValue;
    this.annotationError = "";
    this.closeExtensionsMenu();
    if (!nextValue) {
      this.cancelAnnotationDraft();
      this.annotationDragRect = null;
      this._annotationPointer = null;
    } else {
      this._stageElement?.focus?.({ preventScroll: true });
    }
  },

  canAnnotate() {
    return Boolean(this.activeBrowserId && this.frameSrc && !this.isBusy());
  },

  activeAnnotationUrl() {
    return String(this.frameState?.currentUrl || this.address || "about:blank");
  },

  visibleAnnotations() {
    const browserId = this.normalizeBrowserId(this.activeBrowserId);
    const contextId = this.normalizeContextId(this.activeBrowserContextId);
    const url = this.activeAnnotationUrl();
    return this.annotationComments.filter((annotation) => (
      this.sameBrowserTab(annotation.browserId, annotation.contextId, browserId, contextId)
      && String(annotation.url || "") === url
    ));
  },

  nextAnnotationIndex() {
    return this.visibleAnnotations().length + 1;
  },

  annotationTrayStyle() {
    if (!this.annotationTrayPosition) return {};
    const position = this.clampAnnotationTrayPosition(this.annotationTrayPosition);
    return {
      left: `${position.x}px`,
      top: `${position.y}px`,
      right: "auto",
      bottom: "auto",
    };
  },

  clampAnnotationTrayPosition(position = {}) {
    const stageRect = this._stageElement?.getBoundingClientRect?.();
    const stageWidth = Math.max(1, Number(stageRect?.width || 0));
    const stageHeight = Math.max(1, Number(stageRect?.height || 0));
    const width = Math.max(180, Number(position.width || 0));
    const height = Math.max(90, Number(position.height || 0));
    const maxX = Math.max(ANNOTATION_TRAY_MARGIN, stageWidth - width - ANNOTATION_TRAY_MARGIN);
    const maxY = Math.max(ANNOTATION_TRAY_MARGIN, stageHeight - height - ANNOTATION_TRAY_MARGIN);
    return {
      x: Math.min(Math.max(ANNOTATION_TRAY_MARGIN, Number(position.x || 0)), maxX),
      y: Math.min(Math.max(ANNOTATION_TRAY_MARGIN, Number(position.y || 0)), maxY),
      width,
      height,
    };
  },

  startAnnotationTrayDrag(event) {
    if (event.button !== 0) return;
    if (event.target?.closest?.("button, input, select, textarea, a")) return;
    const tray = event.currentTarget?.closest?.(".browser-annotation-tray");
    const stageRect = this._stageElement?.getBoundingClientRect?.();
    const trayRect = tray?.getBoundingClientRect?.();
    if (!tray || !stageRect || !trayRect) return;

    const position = this.clampAnnotationTrayPosition({
      x: trayRect.left - stageRect.left,
      y: trayRect.top - stageRect.top,
      width: trayRect.width,
      height: trayRect.height,
    });
    this.annotationTrayPosition = position;
    this.annotationTrayDragging = true;
    this._annotationTrayDrag = {
      id: event.pointerId,
      target: event.currentTarget,
      x: event.clientX,
      y: event.clientY,
      startX: position.x,
      startY: position.y,
      width: position.width,
      height: position.height,
    };
    event.currentTarget?.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  },

  moveAnnotationTrayDrag(event) {
    const drag = this._annotationTrayDrag;
    if (!drag || event.pointerId !== drag.id) return;
    this.annotationTrayPosition = this.clampAnnotationTrayPosition({
      x: drag.startX + event.clientX - drag.x,
      y: drag.startY + event.clientY - drag.y,
      width: drag.width,
      height: drag.height,
    });
    event.preventDefault();
  },

  finishAnnotationTrayDrag(event = null) {
    const drag = this._annotationTrayDrag;
    if (!drag || (event?.pointerId && event.pointerId !== drag.id)) return;
    try {
      drag.target?.releasePointerCapture?.(drag.id);
    } catch {}
    this._annotationTrayDrag = null;
    this.annotationTrayDragging = false;
  },

  resetAnnotationTrayPosition() {
    this.finishAnnotationTrayDrag();
    this.annotationTrayPosition = null;
  },

  clearVisibleAnnotations() {
    this.clearAnnotationsForBrowser(this.activeBrowserId, this.activeAnnotationUrl(), this.activeBrowserContextId);
    this.resetAnnotationTrayPosition();
  },

  clearAnnotationsForBrowser(browserId, url = null, contextId = "") {
    const numericBrowserId = this.normalizeBrowserId(browserId);
    const normalizedContextId = this.normalizeContextId(contextId || this.activeBrowserContextId);
    if (!numericBrowserId) return;
    this.annotationComments = this.annotationComments.filter((annotation) => {
      if (!this.sameBrowserTab(annotation.browserId, annotation.contextId, numericBrowserId, normalizedContextId)) return true;
      return url ? String(annotation.url || "") !== String(url) : false;
    });
  },

  annotationBoxStyle(rect = {}) {
    const viewport = this.currentViewportSize() || this._lastViewport || {};
    const width = Math.max(1, Number(viewport.width || rect.width || 1));
    const height = Math.max(1, Number(viewport.height || rect.height || 1));
    const normalized = this.clampAnnotationRect(rect);
    return [
      `left: ${(normalized.x / width) * 100}%`,
      `top: ${(normalized.y / height) * 100}%`,
      `width: ${(Math.max(1, normalized.width) / width) * 100}%`,
      `height: ${(Math.max(1, normalized.height) / height) * 100}%`,
    ].join("; ");
  },

  annotationPopoverStyle() {
    const rect = this.annotationDraft?.rect || this.annotationDragRect || {};
    const viewport = this.currentViewportSize() || this._lastViewport || {};
    const width = Math.max(1, Number(viewport.width || 1));
    const height = Math.max(1, Number(viewport.height || 1));
    const popoverWidth = Math.min(320, Math.max(240, width - 20));
    const popoverHeight = 190;
    const nextLeft = Math.min(
      Math.max(10, Number(rect.x || 0) + Number(rect.width || 0) + 10),
      Math.max(10, width - popoverWidth - 10),
    );
    const nextTop = Math.min(
      Math.max(10, Number(rect.y || 0) + Number(rect.height || 0) + 10),
      Math.max(10, height - popoverHeight - 10),
    );
    return [
      `left: ${(nextLeft / width) * 100}%`,
      `top: ${(nextTop / height) * 100}%`,
      `width: min(${popoverWidth}px, calc(100% - 20px))`,
    ].join("; ");
  },

  annotationDraftTitle() {
    if (!this.annotationDraft) return "Annotation";
    return this.annotationDraft.kind === "area" ? "Area annotation" : "Element annotation";
  },

  stagePointForEvent(event) {
    const image = this._stageElement?.querySelector?.(".browser-frame") || null;
    return this.pointerCoordinatesFor(event, image);
  },

  normalizeAnnotationRect(start = {}, end = {}) {
    const x1 = Number(start.x || 0);
    const y1 = Number(start.y || 0);
    const x2 = Number(end.x || x1);
    const y2 = Number(end.y || y1);
    return this.clampAnnotationRect({
      x: Math.min(x1, x2),
      y: Math.min(y1, y2),
      width: Math.abs(x2 - x1),
      height: Math.abs(y2 - y1),
    });
  },

  clampAnnotationRect(rect = {}) {
    const viewport = this.currentViewportSize() || this._lastViewport || {};
    const viewportWidth = Math.max(1, Number(viewport.width || rect.x + rect.width || 1));
    const viewportHeight = Math.max(1, Number(viewport.height || rect.y + rect.height || 1));
    const x = Math.max(0, Math.min(viewportWidth, Number(rect.x || 0)));
    const y = Math.max(0, Math.min(viewportHeight, Number(rect.y || 0)));
    const width = Math.max(1, Math.min(viewportWidth - x, Number(rect.width || 1)));
    const height = Math.max(1, Math.min(viewportHeight - y, Number(rect.height || 1)));
    return {
      x: Math.round(x),
      y: Math.round(y),
      width: Math.round(width),
      height: Math.round(height),
    };
  },

  startAnnotationSelection(event) {
    if (!this.annotating || this.annotationBusy || !this.canAnnotate()) return;
    const point = this.stagePointForEvent(event);
    if (!point) return;
    this.cancelAnnotationDraft();
    this.annotationError = "";
    this._annotationPointer = {
      id: event.pointerId,
      start: point,
      last: point,
    };
    this.annotationDragRect = this.clampAnnotationRect({
      x: point.x,
      y: point.y,
      width: 1,
      height: 1,
    });
    event.currentTarget?.setPointerCapture?.(event.pointerId);
  },

  moveAnnotationSelection(event) {
    if (!this.annotating || !this._annotationPointer) return;
    if (event.pointerId !== this._annotationPointer.id) return;
    const point = this.stagePointForEvent(event);
    if (!point) return;
    this._annotationPointer.last = point;
    this.annotationDragRect = this.normalizeAnnotationRect(this._annotationPointer.start, point);
  },

  async finishAnnotationSelection(event) {
    if (!this.annotating || !this._annotationPointer) return;
    if (event.pointerId !== this._annotationPointer.id) return;
    const pointer = this._annotationPointer;
    this._annotationPointer = null;
    event.currentTarget?.releasePointerCapture?.(event.pointerId);
    const endPoint = this.stagePointForEvent(event) || pointer.last || pointer.start;
    const rect = this.normalizeAnnotationRect(pointer.start, endPoint);
    this.annotationDragRect = null;
    const isDrag = rect.width >= ANNOTATION_DRAG_THRESHOLD || rect.height >= ANNOTATION_DRAG_THRESHOLD;
    const point = {
      x: Math.round(endPoint.x),
      y: Math.round(endPoint.y),
    };
    const payload = {
      kind: isDrag ? "area" : "element",
      point,
      rect: isDrag ? rect : null,
      viewport: this.currentViewportSize(),
      url: this.activeAnnotationUrl(),
      title: this.activeTitle,
    };
    await this.createAnnotationDraft(payload, isDrag ? rect : {
      x: point.x - 10,
      y: point.y - 10,
      width: 20,
      height: 20,
    });
  },

  cancelAnnotationSelection(event = null) {
    if (event && this._annotationPointer?.id === event.pointerId) {
      event.currentTarget?.releasePointerCapture?.(event.pointerId);
    }
    this._annotationPointer = null;
    this.annotationDragRect = null;
  },

  cancelAnnotationDraft() {
    this.annotationDraft = null;
    this.annotationDraftText = "";
    this.annotationDragRect = null;
  },

  async createAnnotationDraft(payload, fallbackRect) {
    const contextId = this.normalizeContextId(this.activeBrowserContextId || this.contextId);
    if (!this.activeBrowserId || !contextId) return;
    const sequence = this._annotationSequence + 1;
    const browserId = this.activeBrowserId;
    const url = this.activeAnnotationUrl();
    const title = this.activeTitle;
    this._annotationSequence = sequence;
    this.annotationBusy = true;
    this.annotationError = "";
    try {
      const response = await websocket.request(
        "browser_viewer_annotation",
        {
          context_id: contextId,
          browser_id: browserId,
          viewer_id: this._viewerToken,
          payload,
        },
        { timeoutMs: 10000 },
      );
      if (sequence !== this._annotationSequence) return;
      const data = firstOk(response);
      const metadata = data.annotation || {};
      this.annotationDraft = {
        id: makeViewerToken(),
        browserId,
        contextId,
        url,
        title,
        kind: metadata.kind || payload.kind,
        rect: this.annotationRectFromMetadata(metadata, fallbackRect),
        metadata,
        createdAt: Date.now(),
      };
      this.annotationDraftText = "";
    } catch (error) {
      this.annotationError = error instanceof Error ? error.message : String(error);
      this.error = this.annotationError;
    } finally {
      if (sequence === this._annotationSequence) {
        this.annotationBusy = false;
      }
    }
  },

  annotationRectFromMetadata(metadata = {}, fallbackRect = {}) {
    const targetRect = metadata?.target?.rect || metadata?.rect || null;
    return this.clampAnnotationRect(targetRect || fallbackRect);
  },

  addAnnotationComment() {
    const comment = String(this.annotationDraftText || "").trim();
    if (!this.annotationDraft || !comment) return;
    if (this.visibleAnnotations().length >= ANNOTATION_MAX_COMMENTS) {
      this.annotationError = `Keep each batch to ${ANNOTATION_MAX_COMMENTS} annotations or fewer.`;
      this.error = this.annotationError;
      return;
    }
    this.annotationComments = [
      ...this.annotationComments,
      {
        ...this.annotationDraft,
        comment,
        index: this.nextAnnotationIndex(),
      },
    ];
    this.cancelAnnotationDraft();
  },

  removeAnnotationComment(annotationId) {
    this.annotationComments = this.annotationComments.filter((annotation) => annotation.id !== annotationId);
    if (!this.visibleAnnotations().length) {
      this.resetAnnotationTrayPosition();
    }
  },

  annotationChipLabel(annotation) {
    const prefix = annotation?.kind === "area" ? "Area" : "Element";
    return `${prefix} ${annotation?.index || ""}`.trim();
  },

  formatAnnotationRect(rect = {}) {
    const normalized = this.clampAnnotationRect(rect);
    return `x=${normalized.x}, y=${normalized.y}, width=${normalized.width}, height=${normalized.height}`;
  },

  redactAnnotationText(value) {
    return String(value || "")
      .replace(/(<input\b(?=[^>]*\btype=(["'])?password\2?)[^>]*?)\svalue=(["'])[\s\S]*?\3/giu, "$1 value=\"[redacted]\"")
      .replace(/\b(password|passcode|token|secret|value)=((["'])[\s\S]{1,240}?\3)/giu, "$1=\"[redacted]\"");
  },

  formatAnnotationMetadata(metadata = {}) {
    const lines = [];
    const target = metadata.target || {};
    const selector = target.selector || metadata.selector || "";
    const summary = target.summary || metadata.summary || "";
    const dom = this.redactAnnotationText(target.dom || metadata.dom || "").slice(0, ANNOTATION_DOM_LIMIT);

    if (selector) {
      lines.push(`Selector: ${selector}`);
    }
    if (target.tagName || target.role || target.id || target.name || target.classes) {
      lines.push([
        "Element:",
        target.tagName ? `<${String(target.tagName).toLowerCase()}>` : "",
        target.role ? `role=${target.role}` : "",
        target.id ? `id=${target.id}` : "",
        target.name ? `name=${target.name}` : "",
        target.classes ? `class=${target.classes}` : "",
      ].filter(Boolean).join(" "));
    }
    if (summary) {
      lines.push(`Summary: ${summary}`);
    }
    if (Array.isArray(metadata.elements) && metadata.elements.length) {
      lines.push("Intersecting elements:");
      metadata.elements.slice(0, 8).forEach((element, index) => {
        const elementLabel = [
          `${index + 1}.`,
          element.tagName ? `<${String(element.tagName).toLowerCase()}>` : "",
          element.selector || "",
          element.summary || "",
        ].filter(Boolean).join(" ");
        lines.push(elementLabel);
      });
    }
    if (dom) {
      lines.push(`DOM: ${dom}`);
    }
    return lines.join("\n");
  },

  buildAnnotationsPrompt() {
    const annotations = this.visibleAnnotations();
    if (!annotations.length) return "";
    const lines = [
      "Browser annotations",
      `Page title: ${this.activeTitle}`,
      `Page URL: ${this.activeAnnotationUrl()}`,
      `Browser id: ${this.activeBrowserId}`,
      "",
    ];
    annotations.forEach((annotation, index) => {
      lines.push(
        `Annotation ${index + 1}`,
        `Comment: ${annotation.comment}`,
        `Selection kind: ${annotation.kind}`,
        `Coordinates: ${this.formatAnnotationRect(annotation.rect)}`,
      );
      const metadata = this.formatAnnotationMetadata(annotation.metadata);
      if (metadata) {
        lines.push(metadata);
      }
      lines.push("");
    });
    return lines.join("\n").trim();
  },

  draftAnnotationsToChat() {
    const prompt = this.buildAnnotationsPrompt();
    if (!prompt) return;
    const existingMessage = String(chatInputStore.message || "").trim();
    chatInputStore.message = existingMessage ? `${existingMessage}\n\n${prompt}` : prompt;
    chatInputStore.adjustTextareaHeight?.();
    chatInputStore.focus?.();
    this.clearVisibleAnnotations();
    this.toggleAnnotationMode(false);
  },

  async sendAnnotationsToChat() {
    const prompt = this.buildAnnotationsPrompt();
    if (!prompt) return;
    chatInputStore.message = prompt;
    chatInputStore.adjustTextareaHeight?.();
    try {
      if (typeof chatInputStore.sendMessage === "function") {
        await chatInputStore.sendMessage();
      } else if (typeof globalThis.sendMessage === "function") {
        await globalThis.sendMessage();
      } else {
        chatInputStore.focus?.();
        return;
      }
      this.clearVisibleAnnotations();
      this.toggleAnnotationMode(false);
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    }
  },

  currentViewportSize() {
    const measurement = this.surfaceViewportMeasurement();
    if (!measurement) return null;
    return {
      width: measurement.width,
      height: measurement.height,
    };
  },

  surfaceViewportMeasurement() {
    const stage = this._stageElement;
    if (!stage) return null;
    const rect = stage.getBoundingClientRect?.();
    const rawWidth = Math.round(rect?.width || stage.clientWidth || 0);
    const rawHeight = Math.round(rect?.height || stage.clientHeight || 0);
    if (rawWidth < 80 || rawHeight < 80) return null;
    return {
      rawWidth,
      rawHeight,
      width: Math.max(320, rawWidth),
      height: Math.max(200, rawHeight),
    };
  },

  queueViewportSync(force = false) {
    this.clearRenderedFrameIfViewportChanged();
    if (this._viewportSyncTimer) {
      globalThis.clearTimeout(this._viewportSyncTimer);
    }
    this._viewportSyncTimer = globalThis.setTimeout(() => {
      this._viewportSyncTimer = null;
      void this.syncViewport(force);
    }, force ? 0 : VIEWPORT_SYNC_DEBOUNCE_MS);
  },

  async syncViewport(force = false, options = {}) {
    const restartStream = Boolean(options.restartStream);
    const contextId = this.normalizeContextId(this.activeBrowserContextId || this.contextId);
    if (!contextId || !this.activeBrowserId) {
      return;
    }
    const viewport = this.currentViewportSize();
    if (!viewport) {
      return;
    }
    const key = `${contextId}:${this.activeBrowserId}:${viewport.width}x${viewport.height}`;
    if (
      (!restartStream && this._lastViewportKey === key)
      || (
        !force
        && !restartStream
        && this._lastViewport
        && this.sameBrowserTab(this._lastViewport.browserId, this._lastViewport.contextId, this.activeBrowserId, contextId)
        && Math.abs(this._lastViewport.width - viewport.width) <= VIEWPORT_SYNC_SIZE_TOLERANCE
        && Math.abs(this._lastViewport.height - viewport.height) <= VIEWPORT_SYNC_SIZE_TOLERANCE
      )
    ) {
      return;
    }
    try {
      await websocket.emit("browser_viewer_input", {
        context_id: contextId,
        browser_id: this.activeBrowserId,
        viewer_id: this._viewerToken,
        input_type: "viewport",
        width: viewport.width,
        height: viewport.height,
        restart_stream: restartStream,
      });
      this._lastViewportKey = key;
      this._lastViewport = {
        browserId: this.activeBrowserId,
        contextId,
        width: viewport.width,
        height: viewport.height,
      };
    } catch (error) {
      this._lastViewportKey = "";
      this._lastViewport = null;
      console.warn("Browser viewport sync failed", error);
    }
  },

  async sendMouse(eventType, event) {
    if (this.annotating) return;
    const contextId = this.normalizeContextId(this.activeBrowserContextId || this.contextId);
    if (!contextId || !this.activeBrowserId || !event?.currentTarget) return;
    const pointer = this.pointerCoordinatesFor(event);
    if (!pointer) return;
    const payload = {
      context_id: contextId,
      browser_id: this.activeBrowserId,
      viewer_id: this._viewerToken,
      input_type: "mouse",
      event_type: eventType,
      x: pointer.x,
      y: pointer.y,
      button: "left",
    };
    if (eventType === "click") {
      try {
	        const response = await websocket.request("browser_viewer_input", payload, { timeoutMs: 10000 });
	        const data = firstOk(response);
	        this.applyActiveFrameState(data.state);
	        this.applySnapshot(data.snapshot);
	      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error);
      }
      return;
    }
    await websocket.emit("browser_viewer_input", payload);
  },

  async sendWheel(event) {
    const contextId = this.normalizeContextId(this.activeBrowserContextId || this.contextId);
    if (!contextId || !this.activeBrowserId || !event) return;
    const image = event.currentTarget?.querySelector?.(".browser-frame") || event.target?.closest?.(".browser-frame");
    const pointer = this.pointerCoordinatesFor(event, image);
    if (!pointer) return;
    const payload = {
      context_id: contextId,
      browser_id: this.activeBrowserId,
      viewer_id: this._viewerToken,
      input_type: "wheel",
      x: pointer.x,
      y: pointer.y,
      delta_x: Number(event.deltaX || 0),
      delta_y: Number(event.deltaY || 0),
    };
    try {
      await websocket.emit("browser_viewer_input", payload);
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    }
  },

  async sendKey(event) {
    if (this.annotating) return;
    const contextId = this.normalizeContextId(this.activeBrowserContextId || this.contextId);
    if (!contextId || !this.activeBrowserId) return;
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    const editable = ["INPUT", "TEXTAREA", "SELECT"].includes(event.target?.tagName);
    if (editable) return;
    event.preventDefault();
    const printable = event.key && event.key.length === 1;
    await websocket.emit("browser_viewer_input", {
      context_id: contextId,
      browser_id: this.activeBrowserId,
      input_type: "keyboard",
      key: printable ? "" : event.key,
      text: printable ? event.key : "",
    });
  },

  async sendShortcut(key) {
    const contextId = this.normalizeContextId(this.activeBrowserContextId || this.contextId);
    if (!contextId || !this.activeBrowserId || !key) return;
    await websocket.emit("browser_viewer_input", {
      context_id: contextId,
      browser_id: this.activeBrowserId,
      viewer_id: this._viewerToken,
      input_type: "keyboard",
      key,
      text: "",
    });
  },

  async pasteHostClipboardToBrowser() {
    try {
      const text = await this.readHostClipboardText();
      if (!text) return;
      await this.sendClipboard("paste", text);
    } catch (error) {
      this.error = "Browser paste needs clipboard permission in this tab.";
      globalThis.justToast?.(this.error, "warning", 2200, "browser-clipboard");
      console.warn("Browser clipboard paste failed", error);
    }
  },

  async copyBrowserClipboardToHost(action = "copy") {
    try {
      const clipboard = await this.sendClipboard(action);
      const text = String(clipboard?.text || clipboard?.clipboard_text || "");
      if (!text) return;
      await copyToClipboard(text);
      this._clipboardFallbackText = text;
      const message = action === "cut" ? "Cut from Browser" : "Copied from Browser";
      globalThis.justToast?.(message, "success", 1200, "browser-clipboard");
    } catch (error) {
      this.error = action === "cut"
        ? "Browser cut failed."
        : "Browser copy failed.";
      globalThis.justToast?.(this.error, "warning", 1800, "browser-clipboard");
      console.warn("Browser clipboard copy failed", error);
    }
  },

  async readHostClipboardText() {
    const clipboard = globalThis.navigator?.clipboard;
    if (clipboard?.readText && globalThis.isSecureContext) {
      try {
        return await clipboard.readText();
      } catch (error) {
        if (this._clipboardFallbackText) return this._clipboardFallbackText;
        throw error;
      }
    }
    return this._clipboardFallbackText || "";
  },

  async sendClipboard(action = "copy", text = "") {
    const contextId = this.normalizeContextId(this.activeBrowserContextId || this.contextId);
    if (!contextId || !this.activeBrowserId) return {};
    const response = await websocket.request(
      "browser_viewer_input",
      {
        context_id: contextId,
        browser_id: this.activeBrowserId,
        viewer_id: this._viewerToken,
        input_type: "clipboard",
        action,
        text,
      },
      { timeoutMs: 10000 },
    );
    const data = firstOk(response);
    this.applyActiveFrameState(data.state);
    this.applySnapshot(data.snapshot);
    return data.clipboard || {};
  },

  async cleanup() {
    if (this._surfaceHandoff) {
      this.releaseSurfaceBindings();
      this.extensionMenuOpen = false;
      return;
    }
    this._surfaceOpenSequence += 1;
    this._openPromise = null;
    this._openSignature = "";
    this._connectSequence += 1;
    this._viewerToken = "";
    this.switchingBrowserId = null;
    this._surfaceMounted = false;
    this._surfaceSwitching = false;
    this.commandInFlight = false;
    this._commandInFlightCount = 0;
    this._closingBrowserIds = {};
    this.annotating = false;
    this.annotationBusy = false;
    this.annotationError = "";
    this.cancelAnnotationDraft();
    this.cancelAnnotationSelection();
    this.resetAnnotationTrayPosition();
    if (this.contextId) {
      try {
        await websocket.emit("browser_viewer_unsubscribe", { context_id: this.contextId });
      } catch {}
    }
    this._frameOff?.();
    this._stateOff?.();
    this._frameOff = null;
    this._stateOff = null;
    this.resetRenderedFrame();
    this.releaseSurfaceBindings();
    if (this._viewportSyncTimer) {
      globalThis.clearTimeout(this._viewportSyncTimer);
      this._viewportSyncTimer = null;
    }
    this.resetViewportTracking();
    this.extensionMenuOpen = false;
    this.extensionActionLoading = false;
    this.extensionsListLoading = false;
    this.extensionToggleLoadingPath = "";
    this.modelPresetSaving = false;
    this.connected = false;
  },

  setupFloatingModal(element = null) {
    this._floatingCleanup?.();
    const root = element || globalThis.document?.querySelector(".browser-panel");
    const modal = root?.closest?.(".modal");
    const inner = modal?.querySelector?.(".modal-inner");
    const body = modal?.querySelector?.(".modal-bd");
    const header = modal?.querySelector?.(".modal-header");
    const stage = root?.querySelector?.(".browser-stage");
    if (!modal || !inner || !header) return;
    modal.classList.add("surface-floating", "modal-floating");
    inner.classList.add("surface-modal", "browser-modal");
    body?.classList?.add("browser-modal-body");
    this._stageElement = stage || null;

    const rect = inner.getBoundingClientRect();
    inner.style.left = `${Math.max(8, rect.left)}px`;
    inner.style.top = `${Math.max(8, rect.top)}px`;
    inner.style.transform = "none";

    let drag = null;
    let resizeObserver = null;
    let beforeFocusBounds = null;
    const viewportGap = 8;
    const currentBounds = () => {
      const bounds = inner.getBoundingClientRect();
      return {
        left: bounds.left,
        top: bounds.top,
        width: bounds.width,
        height: bounds.height,
      };
    };
    const normalizedBounds = (bounds = {}) => {
      const maxWidth = Math.max(320, globalThis.innerWidth - viewportGap * 2);
      const maxHeight = Math.max(300, globalThis.innerHeight - viewportGap * 2);
      const width = Math.min(Math.max(320, Number(bounds.width || 320)), maxWidth);
      const height = Math.min(Math.max(300, Number(bounds.height || 300)), maxHeight);
      return {
        left: Math.min(
          Math.max(viewportGap, Number(bounds.left || viewportGap)),
          Math.max(viewportGap, globalThis.innerWidth - width - viewportGap),
        ),
        top: Math.min(
          Math.max(viewportGap, Number(bounds.top || viewportGap)),
          Math.max(viewportGap, globalThis.innerHeight - height - viewportGap),
        ),
        width,
        height,
      };
    };
    const setBounds = (bounds = {}) => {
      const next = normalizedBounds(bounds);
      inner.style.position = "fixed";
      inner.style.transform = "none";
      inner.style.left = `${Math.round(next.left)}px`;
      inner.style.top = `${Math.round(next.top)}px`;
      inner.style.width = `${Math.round(next.width)}px`;
      inner.style.height = `${Math.round(next.height)}px`;
      inner.style.maxWidth = `${Math.max(320, globalThis.innerWidth - viewportGap * 2)}px`;
      inner.style.maxHeight = `${Math.max(300, globalThis.innerHeight - viewportGap * 2)}px`;
      this.queueViewportSync();
      return next;
    };
    const focusBounds = () => ({
      left: viewportGap,
      top: viewportGap,
      width: globalThis.innerWidth - viewportGap * 2,
      height: globalThis.innerHeight - viewportGap * 2,
    });
    const clampPosition = (left, top) => {
      const bounds = inner.getBoundingClientRect();
      const maxLeft = Math.max(viewportGap, globalThis.innerWidth - bounds.width - viewportGap);
      const maxTop = Math.max(viewportGap, globalThis.innerHeight - bounds.height - viewportGap);
      return {
        left: Math.min(Math.max(viewportGap, left), maxLeft),
        top: Math.min(Math.max(viewportGap, top), maxTop),
      };
    };
    const clampGeometry = () => {
      if (inner.classList.contains("is-focus-mode")) {
        setBounds(focusBounds());
        return;
      }
      setBounds(currentBounds());
    };
    clampGeometry();

    const focusButton = globalThis.document.createElement("button");
    focusButton.type = "button";
    focusButton.className = "surface-button browser-modal-focus-button";
    focusButton.innerHTML = '<span class="material-symbols-outlined" aria-hidden="true">fullscreen</span>';
    const updateFocusButton = (active) => {
      const label = active ? "Restore size" : "Focus mode";
      focusButton.setAttribute("aria-label", label);
      focusButton.setAttribute("title", label);
      focusButton.querySelector(".material-symbols-outlined").textContent = active ? "fullscreen_exit" : "fullscreen";
    };
    const setFocusMode = (enabled) => {
      if (enabled) {
        beforeFocusBounds = currentBounds();
        inner.classList.add("is-focus-mode");
        setBounds(focusBounds());
        updateFocusButton(true);
        return;
      }
      inner.classList.remove("is-focus-mode");
      setBounds(beforeFocusBounds || currentBounds());
      beforeFocusBounds = null;
      updateFocusButton(false);
    };
    updateFocusButton(false);
    const closeButton = inner.querySelector(".modal-close");
    if (closeButton) {
      closeButton.insertAdjacentElement("beforebegin", focusButton);
    } else {
      header.appendChild(focusButton);
    }
    const onFocusClick = () => setFocusMode(!inner.classList.contains("is-focus-mode"));
    focusButton.addEventListener("click", onFocusClick);

    globalThis.addEventListener("resize", clampGeometry);
    if (globalThis.ResizeObserver) {
      resizeObserver = new ResizeObserver(clampGeometry);
      resizeObserver.observe(inner);
      if (stage) {
        this._stageResizeObserver?.disconnect?.();
        this._stageResizeObserver = new ResizeObserver(() => {
          this.queueViewportSync();
        });
        this._stageResizeObserver.observe(stage);
      }
    }
    const surfaceSequence = this._surfaceOpenSequence;
    globalThis.requestAnimationFrame(() => {
      if (!this.isCurrentSurfaceOpen(surfaceSequence)) return;
      this.queueViewportSync(true);
    });

    const onPointerMove = (event) => {
      if (!drag) return;
      const next = clampPosition(
        drag.left + event.clientX - drag.x,
        drag.top + event.clientY - drag.y,
      );
      inner.style.left = `${next.left}px`;
      inner.style.top = `${next.top}px`;
      clampGeometry();
    };
    const onPointerUp = () => {
      drag = null;
      globalThis.removeEventListener("pointermove", onPointerMove);
      globalThis.removeEventListener("pointerup", onPointerUp);
      try {
        header.releasePointerCapture?.(header.__browserPanelPointerId || 0);
      } catch {}
    };
    const onPointerDown = (event) => {
      if (event.button !== 0) return;
      if (event.target?.closest?.("button, input, select, textarea, a")) return;
      if (inner.classList.contains("is-focus-mode")) return;
      const current = inner.getBoundingClientRect();
      drag = {
        x: event.clientX,
        y: event.clientY,
        left: current.left,
        top: current.top,
      };
      header.__browserPanelPointerId = event.pointerId;
      header.setPointerCapture?.(event.pointerId);
      globalThis.addEventListener("pointermove", onPointerMove);
      globalThis.addEventListener("pointerup", onPointerUp);
      event.preventDefault();
    };
    header.addEventListener("pointerdown", onPointerDown);

    this._floatingCleanup = () => {
      focusButton.removeEventListener("click", onFocusClick);
      focusButton.remove();
      header.removeEventListener("pointerdown", onPointerDown);
      globalThis.removeEventListener("pointermove", onPointerMove);
      globalThis.removeEventListener("pointerup", onPointerUp);
      globalThis.removeEventListener("resize", clampGeometry);
      resizeObserver?.disconnect?.();
      this._stageResizeObserver?.disconnect?.();
      this._stageResizeObserver = null;
      inner.classList.remove("is-focus-mode");
    };
  },

  setupCanvasSurface(element = null) {
    const surfaceSequence = this._surfaceOpenSequence;
    this._floatingCleanup?.();
    this._floatingCleanup = null;
    this._stageResizeObserver?.disconnect?.();
    const root = element || globalThis.document?.querySelector(".browser-panel");
    const stage = root?.querySelector?.(".browser-stage");
    this._stageElement = stage || null;
    if (stage && globalThis.ResizeObserver) {
      this._stageResizeObserver = new ResizeObserver(() => {
        this.queueViewportSync();
      });
      this._stageResizeObserver.observe(stage);
    }
    globalThis.requestAnimationFrame?.(() => {
      if (!this.isCurrentSurfaceOpen(surfaceSequence) || this._mode !== "canvas") return;
      this.queueViewportSync(true);
    });
  },

  get activeTitle() {
    return this.frameState?.title || "Browser";
  },

  get activeUrl() {
    return this.frameState?.currentUrl || this.address || "about:blank";
  },

  loadingMessage() {
    if (this.browserInstallExpected) {
      const cacheDir = this.status?.playwright?.cache_dir || "/a0/tmp/playwright";
      return `Installing Chromium for the first Browser run. This can take a few minutes; future starts reuse ${cacheDir}.`;
    }
    return "Loading";
  },
};

export const store = createStore("browserPage", model);

registerUrlHandler(async (intent = {}) => {
  const url = String(intent.url || "").trim();
  const payload = { url, source: intent.source || "surface-url-intent" };
  await openLatestSurface("browser", payload);
  return await store.openUrlIntent(url, { source: payload.source });
});
