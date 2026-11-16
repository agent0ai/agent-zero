import { createStore } from "/js/AlpineStore.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";
import { callJsExtensions } from "/js/extensions.js";
import {
  SURFACE_MODE_DOCKED,
  SURFACE_MODE_FLOATING,
  getRegisteredSurfaces,
  migratePersistedSurfaceState,
  normalizeSurfaceId,
  normalizeSurfaceMode,
  registerSurface as registerSurfaceDefinition,
} from "/js/surfaces.js";

const MODAL_PATH = "canvas/canvas-modal.html";
const STORAGE_KEY = "a0.rightCanvas";
const SESSION_STORAGE_KEY = "a0.rightCanvas.session";
const DEFAULT_WIDTH = 720;
const MIN_WIDTH = 0;
const DESKTOP_BREAKPOINT = 1200;
const MOBILE_BREAKPOINT = 768;

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function viewportWidth() {
  return Math.max(document.documentElement.clientWidth || 0, globalThis.innerWidth || 0);
}

function normalizeWidth(value, fallback = DEFAULT_WIDTH) {
  if (value === null || value === undefined || value === "") return fallback;
  const width = Number(value);
  return Number.isFinite(width) ? Math.max(MIN_WIDTH, Math.round(width)) : fallback;
}

function isReloadNavigation() {
  const navigation = performance.getEntriesByType?.("navigation")?.[0];
  if (navigation?.type) return navigation.type === "reload";
  if (!performance.navigation) return false;
  return performance.navigation?.type === performance.navigation?.TYPE_RELOAD;
}

const model = {
  surfaces: [],
  activeSurfaceId: "",
  surfaceModes: {},
  mountedSurfaces: {},
  isOpen: false,
  isDetached: false,
  _shellElement: null,
  _shellParent: null,
  _modalOpening: null,
  _resolveModalMount: null,
  _reattaching: false,
  _closedPromise: null,
  _resolveClosed: null,
  width: DEFAULT_WIDTH,
  railPosition: null,
  railHeight: 0,
  _railObserver: null,
  _railDragCleanup: null,
  isOverlayMode: false,
  isMobileMode: false,
  _initialized: false,
  _registering: false,
  _rootElement: null,
  _resizeCleanup: null,
  _lastPayloadBySurface: {},
  _restoreOpenRequested: false,
  _restoreOpenTimer: null,
  _restoringSurface: false,
  _restoreMode: null,

  async init(element = null) {
    if (element) this._rootElement = element;
    if (this._initialized) {
      this.applyLayoutState();
      this.scheduleRestoreOpenSurface();
      return;
    }

    this._initialized = true;
    this.restore();
    this.updateLayoutMode();
    this.applyLayoutState();
    globalThis.addEventListener("resize", () => {
      this.updateLayoutMode();
      this.setWidth(this.width, { persist: false });
      this.applyLayoutState();
    });

    if (!this._registering) {
      this._registering = true;
      await callJsExtensions("surfaces_register", this);
      await callJsExtensions("right_canvas_register_surfaces", this);
      this._registering = false;
      this.ensureActiveSurface();
      this.scheduleRestoreOpenSurface();
    }
  },

  registerSurface(surface) {
    if (!surface?.id) return;
    const surfaceId = normalizeSurfaceId(surface.id);
    const normalized = {
      title: surface.id,
      icon: "web_asset",
      image: "",
      order: 100,
      canOpen: () => true,
      open: () => {},
      close: () => {},
      modalPath: "",
      actionOnly: false,
      ...surface,
      id: surfaceId,
    };

    const index = this.surfaces.findIndex((item) => item.id === normalized.id);
    if (index >= 0) {
      this.surfaces.splice(index, 1, normalized);
    } else {
      this.surfaces.push(normalized);
    }
    if (!this.surfaceModes[normalized.id]) {
      this.surfaceModes[normalized.id] = SURFACE_MODE_DOCKED;
    }
    registerSurfaceDefinition(normalized);
    preferencesStore.registerUiControlVisibility(`canvas:${normalized.id}`);
    this.surfaces.sort((a, b) => (a.order ?? 100) - (b.order ?? 100));
    if (!this._registering) {
      this.ensureActiveSurface();
    }
  },

  ensureActiveSurface() {
    const panelSurfaces = this.panelSurfaces;
    if (!panelSurfaces.length) {
      this.activeSurfaceId = "";
      return;
    }
    if (!panelSurfaces.some((surface) => surface.id === this.activeSurfaceId)) {
      this.activeSurfaceId = panelSurfaces[0].id;
    }
  },

  async open(surfaceId = "", payload = {}, mode = null) {
    const targetId = normalizeSurfaceId(surfaceId || this.activeSurfaceId || this.panelSurfaces[0]?.id || "");
    const surface = this.getSurface(targetId);
    if (!surface) {
      return false;
    }
    if (typeof surface.canOpen === "function" && surface.canOpen(payload) === false) {
      return false;
    }

    this._restoreOpenRequested = false;
    this.cancelRestoreOpenSurface();

    if (surface.actionOnly) {
      try {
        await surface.open?.(payload || {});
      } catch (error) {
        console.error(`Canvas action ${targetId} failed`, error);
      }
      return true;
    }

    const wasOpen = this.isOpen || this.isDetached || Boolean(this._modalOpening);
    let detached = this.isDetached || Boolean(this._modalOpening);
    if (!this.isOpen && !detached) detached = true;
    if (mode) detached = mode === SURFACE_MODE_FLOATING;
    if (this.isMobileMode || !this.shouldRender() || !this.isSurfaceEnabled(targetId)) detached = true;
    if (detached) {
      if (!await this.showModal()) return false;
    } else if (this.isDetached) {
      this._reattaching = true;
      try {
        if (await globalThis.closeModal(MODAL_PATH) === false) return false;
      } finally {
        this._reattaching = false;
      }
    }

    const mounted = this.isSurfaceMounted(targetId);
    this.activeSurfaceId = targetId;
    this.markSurfaceMounted(targetId);
    this.isOpen = !detached;
    this.recordSurfaceMode(targetId, detached ? SURFACE_MODE_FLOATING : SURFACE_MODE_DOCKED, { persist: false });
    this._lastPayloadBySurface[targetId] = payload || {};
    this.persist();
    this.applyLayoutState();

    // Plain tab switches reuse the live panel; explicit payloads still navigate it.
    if (mounted && wasOpen && Object.keys(payload).length === 0) return true;
    try {
      await surface.open?.(payload || {});
    } catch (error) {
      this.markSurfaceUnmounted(targetId);
      console.error(`Canvas surface ${targetId} failed to open`, error);
      return false;
    }
    return true;
  },

  markSurfaceMounted(surfaceId) {
    const targetId = normalizeSurfaceId(surfaceId);
    if (!targetId) return;
    this.mountedSurfaces = {
      ...this.mountedSurfaces,
      [targetId]: true,
    };
  },

  markSurfaceUnmounted(surfaceId) {
    const targetId = normalizeSurfaceId(surfaceId);
    if (!targetId || !this.mountedSurfaces[targetId]) return;
    const next = { ...this.mountedSurfaces };
    delete next[targetId];
    this.mountedSurfaces = next;
  },

  mountedSurfaceIds() {
    return Object.entries(this.mountedSurfaces)
      .filter(([, mounted]) => mounted)
      .map(([surfaceId]) => surfaceId);
  },

  isSurfaceMounted(id) {
    return Boolean(this.mountedSurfaces[normalizeSurfaceId(id)]);
  },

  isSurfaceRendered(id) {
    return Boolean((this.isOpen || this.isDetached) && this.isSurfaceMounted(id));
  },

  isSurfaceVisible(id) {
    const targetId = normalizeSurfaceId(id);
    return Boolean((this.isOpen || this.isDetached) && this.activeSurfaceId === targetId && this.isSurfaceMounted(targetId));
  },

  recordSurfaceMode(surfaceId, mode = SURFACE_MODE_DOCKED, options = {}) {
    const targetId = normalizeSurfaceId(surfaceId);
    if (!targetId) return;
    this.surfaceModes = {
      ...this.surfaceModes,
      [targetId]: normalizeSurfaceMode(mode),
    };
    if (options.persist !== false) this.persist();
  },

  latestSurfaceMode(surfaceId) {
    const targetId = normalizeSurfaceId(surfaceId);
    return normalizeSurfaceMode(this.surfaceModes[targetId]);
  },

  async openLatest(surfaceId = "", payload = {}) {
    return await this.openModalSurface(surfaceId, payload);
  },

  async openFromRail(surfaceId) {
    const mode = surfaceId === "desktop" && !this.isOpen ? SURFACE_MODE_FLOATING : SURFACE_MODE_DOCKED;
    return await this.open(surfaceId, {}, mode);
  },

  whenClosed() {
    if (!this.isOpen && !this.isDetached && !this._modalOpening) return Promise.resolve();
    if (!this._closedPromise) {
      this._closedPromise = new Promise(resolve => { this._resolveClosed = resolve; });
    }
    return this._closedPromise;
  },

  finishClose() {
    this._resolveClosed?.();
    this._resolveClosed = null;
    this._closedPromise = null;
  },

  canClose() {
    return this.mountedSurfaceIds().every(id => this.getSurface(id)?.canClose?.() !== false);
  },

  mountShell(element) {
    this._shellElement = element;
    this._shellParent = element.parentElement;
  },

  moveShell(parent) {
    const shell = this._shellElement;
    if (!parent || !shell || shell.parentElement === parent) return;
    // Suppress Alpine teardown; moveBefore also preserves iframe browsing contexts.
    Alpine.mutateDom(() => {
      if (parent.moveBefore) parent.moveBefore(shell, null);
      // shortcut: legacy browsers may reload iframes; retire this fallback when moveBefore is universal.
      else parent.appendChild(shell);
    });
  },

  mountModal(host) {
    this.moveShell(host);
    this.isDetached = true;
    this.isOpen = false;
    this._resizeCleanup?.();
    this.applyLayoutState();
    this._resolveModalMount?.(true);
    this._resolveModalMount = null;
  },

  async showModal() {
    if (this.isDetached) {
      void globalThis.ensureModalOpen?.(MODAL_PATH);
      return true;
    }
    if (this._modalOpening) return await this._modalOpening;
    if (!this._shellElement) return false;
    let resolveMounted;
    this._modalOpening = new Promise(resolve => { resolveMounted = resolve; });
    this._resolveModalMount = resolveMounted;
    void globalThis.openModal(MODAL_PATH, () => {
      if (!this._reattaching && !this.canClose()) return false;
      this.moveShell(this._shellParent);
      this.isDetached = false;
      this.isOpen = this._reattaching;
      this.persist();
      this.applyLayoutState();
      if (!this._reattaching) this.finishClose();
      return true;
    }).finally(() => {
      resolveMounted(false);
      if (this._resolveModalMount === resolveMounted) this._resolveModalMount = null;
    });
    try {
      return await this._modalOpening;
    } finally {
      this._modalOpening = null;
    }
  },

  async close() {
    if (!this.canClose()) return false;
    this._resizeCleanup?.();
    this._restoreOpenRequested = false;
    this.cancelRestoreOpenSurface();
    if (this.isDetached || this._modalOpening) {
      return await globalThis.closeModal(MODAL_PATH);
    }
    this.isOpen = false;
    this.persist();
    this.applyLayoutState();
    this.finishClose();
    return true;
  },

  async dockSurface(surfaceId = "", payload = {}) {
    if (this.isMobileMode || !this.shouldRender()) return false;
    if (payload.closeSourceModal && await payload.closeSourceModal() === false) return false;
    return await this.open(surfaceId || this.activeSurfaceId, payload, SURFACE_MODE_DOCKED);
  },

  async undockSurface(surfaceId = "", payload = {}) {
    return await this.open(surfaceId || this.activeSurfaceId, payload, SURFACE_MODE_FLOATING);
  },

  async openModalSurface(surfaceId = "", payload = {}) {
    return await this.undockSurface(surfaceId, payload);
  },

  async toggleMode() {
    return this.isDetached ? await this.dockSurface() : await this.undockActiveSurface();
  },

  async undockActiveSurface() {
    return await this.undockSurface(this.activeSurfaceId);
  },

  currentSurfaceCanUndock() {
    return Boolean(this.currentSurface()?.modalPath);
  },

  async toggle(surfaceId = "", payload = {}) {
    const targetId = normalizeSurfaceId(surfaceId || this.activeSurfaceId || this.panelSurfaces[0]?.id || "");
    if ((this.isOpen || this.isDetached) && targetId === this.activeSurfaceId) {
      await this.close();
      return false;
    }
    return await this.open(targetId, payload);
  },

  async toggleCanvas() {
    if (!this.shouldRender()) return false;
    this.ensureActiveSurface();
    if (this.isMobileMode) {
      return await this.open(this.activeSurfaceId || this.panelSurfaces[0]?.id || "", { source: "mobile-toggle" });
    }
    if (this.isOpen || this.isDetached) {
      await this.close();
      return false;
    }
    return await this.open(this.activeSurfaceId || this.panelSurfaces[0]?.id || "");
  },

  mountRail(element) {
    this._railObserver?.disconnect();
    this._railObserver = new ResizeObserver(() => {
      this.railHeight = element.offsetHeight;
    });
    this._railObserver.observe(element);
  },

  unmountRail() {
    this._railDragCleanup?.();
    this._railObserver?.disconnect();
    this._railObserver = null;
  },

  railStyle() {
    const inset = this.railHeight / 2 + 8;
    const position = this.railPosition ?? (this.isMobileMode ? 0.5 : 0.33);
    return `top: clamp(${inset}px, ${position * 100}%, calc(100% - ${inset}px));`;
  },

  startRailDrag(event) {
    if (event.button !== 0 || event.isPrimary === false) return;
    this._railDragCleanup?.();
    event.preventDefault();
    const handle = event.currentTarget;
    const rail = handle.closest(".right-canvas-rail");
    const bounds = this._rootElement.getBoundingClientRect();
    const rect = rail.getBoundingClientRect();
    const offset = event.clientY - (rect.top + rect.height / 2);
    const listeners = new AbortController();
    const options = { signal: listeners.signal, capture: true };
    const move = (e) => {
      if (e.pointerId !== event.pointerId) return;
      if (e.buttons === 0) { end(); return; }
      const inset = this.railHeight / 2 + 8;
      const center = clamp(e.clientY - offset - bounds.top, inset, bounds.height - inset);
      this.railPosition = clamp(center / bounds.height, 0, 1);
    };
    const end = (e) => {
      if (e?.pointerId !== undefined && e.pointerId !== event.pointerId) return;
      listeners.abort();
      this._railDragCleanup = null;
      if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId);
      this.persist();
    };
    this._railDragCleanup = end;
    globalThis.addEventListener("pointermove", move, options);
    globalThis.addEventListener("pointerup", end, options);
    globalThis.addEventListener("pointercancel", end, options);
    globalThis.addEventListener("blur", end, options);
    handle.addEventListener("lostpointercapture", end, options);
    try { handle.setPointerCapture(event.pointerId); } catch { /* Window listeners also handle drags without capture. */ }
  },

  moveRail(event) {
    if (!["ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const position = this.railPosition ?? (this.isMobileMode ? 0.5 : 0.33);
    this.railPosition = event.key === "Home" ? 0 : event.key === "End" ? 1
      : clamp(position + (event.key === "ArrowUp" ? -0.02 : 0.02), 0, 1);
    this.persist();
  },

  async customize() {
    const { store: settingsStore } = await import("/components/settings/settings-store.js");
    await settingsStore.open("agent", "section-interface");
  },

  setWidth(px, options = {}) {
    const { persist = true } = options;
    const next = clamp(normalizeWidth(px), MIN_WIDTH, this.maxWidth());
    this.width = next;
    this.applyLayoutState();
    if (persist) this.persist();
  },

  maxWidth() {
    if (this.isOverlayMode) {
      return Math.max(MIN_WIDTH, viewportWidth() - 44);
    }

    const container = this._rootElement?.closest(".container");
    const rightPanel = document.getElementById("right-panel");
    const containerRight = container?.getBoundingClientRect().right ?? viewportWidth();
    const panelLeft = rightPanel?.getBoundingClientRect().left ?? 0;
    return Math.max(MIN_WIDTH, Math.floor(containerRight - panelLeft));
  },

  defaultWidth() {
    return Math.min(DEFAULT_WIDTH, Math.floor(viewportWidth() * 0.45));
  },

  startResize(event) {
    if (this.isOverlayMode || this.isMobileMode || !this.isOpen) return;
    if (event.button !== 0 || event.isPrimary === false) return;
    this._resizeCleanup?.();
    event.preventDefault();
    const handle = event.currentTarget;
    const bounds = this._rootElement.getBoundingClientRect();
    const startWidth = this.width;
    const maxWidth = this.maxWidth();
    let nextWidth = startWidth;
    // Cover embedded documents even when pointer capture is unavailable.
    const preview = document.createElement("div");
    preview.className = "right-canvas-resize-preview";
    preview.setAttribute("aria-hidden", "true");
    preview.style.setProperty("--resize-top", `${bounds.top}px`);
    preview.style.setProperty("--resize-height", `${bounds.height}px`);
    const update = (x) => {
      nextWidth = clamp(normalizeWidth(startWidth + event.clientX - x), MIN_WIDTH, maxWidth);
      preview.style.setProperty("--resize-left", `${bounds.right - nextWidth}px`);
    };
    update(event.clientX);
    document.body.appendChild(preview);
    const listeners = new AbortController();
    const options = { signal: listeners.signal, capture: true };
    const end = (e) => {
      if (e?.pointerId !== undefined && e.pointerId !== event.pointerId) return;
      if (e?.type === "pointerup") update(e.clientX);
      listeners.abort();
      this._resizeCleanup = null;
      if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId);
      preview.remove();
      document.body.classList.remove("right-canvas-resizing");
      if ((e?.type === "pointerup" || e?.type === "pointermove") && nextWidth !== this.width) {
        this.setWidth(nextWidth);
      }
      this.dispatchResizeEvent("right-canvas-resize-end");
    };
    const move = (e) => {
      if (e.pointerId !== event.pointerId) return;
      if (e.buttons === 0) { end(e); return; }
      update(e.clientX);
    };
    this._resizeCleanup = end;
    document.body.classList.add("right-canvas-resizing");
    globalThis.addEventListener("pointermove", move, options);
    globalThis.addEventListener("pointerup", end, options);
    globalThis.addEventListener("pointercancel", end, options);
    globalThis.addEventListener("blur", end, options);
    globalThis.addEventListener("resize", end, options);
    globalThis.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { e.preventDefault(); end(); }
    }, options);
    handle.addEventListener("lostpointercapture", end, options);
    try { handle.setPointerCapture(event.pointerId); } catch { /* The preview also shields iframe input. */ }
    this.dispatchResizeEvent("right-canvas-resize-start");
  },

  dispatchResizeEvent(name) {
    try {
      globalThis.dispatchEvent(new CustomEvent(name, {
        detail: {
          width: this.width,
          activeSurfaceId: this.activeSurfaceId,
        },
      }));
    } catch {
      // Resize events are an optimization hook for embedded surfaces.
    }
  },

  cancelRestoreOpenSurface() {
    if (!this._restoreOpenTimer) return;
    globalThis.clearTimeout?.(this._restoreOpenTimer);
    this._restoreOpenTimer = null;
  },

  scheduleRestoreOpenSurface() {
    if (!this._restoreOpenRequested || this._restoreOpenTimer) return;
    if (!this.shouldRender() && this._restoreMode !== SURFACE_MODE_FLOATING) return;
    this._restoreOpenTimer = globalThis.setTimeout?.(() => {
      this._restoreOpenTimer = null;
      this.restoreOpenSurface();
    }, 0) || null;
  },

  async restoreOpenSurface() {
    if (!this._restoreOpenRequested || this._restoringSurface) return false;
    if (!this.shouldRender() && this._restoreMode !== SURFACE_MODE_FLOATING) return false;

    const targetId = normalizeSurfaceId(this.activeSurfaceId || this.panelSurfaces[0]?.id || "");
    if (!targetId || !this.getSurface(targetId)) {
      return false;
    }

    this._restoreOpenRequested = false;
    this._restoringSurface = true;
    try {
      return await this.open(targetId, { source: "reload-restore" }, this._restoreMode);
    } finally {
      this._restoringSurface = false;
    }
  },

  persist() {
    const state = {
      isOpen: this.isOpen || this.isDetached,
      mode: this.isDetached ? SURFACE_MODE_FLOATING : SURFACE_MODE_DOCKED,
      activeSurfaceId: this.activeSurfaceId,
      surfaceModes: this.surfaceModes,
      width: this.width,
      railPosition: this.railPosition,
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.warn("Could not persist right canvas state", error);
    }
    try {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.warn("Could not persist right canvas session state", error);
    }
  },

  restore() {
    this.width = this.defaultWidth();
    try {
      const saved = migratePersistedSurfaceState(JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"));
      this.isOpen = false;
      if (typeof saved.railPosition === "number" && Number.isFinite(saved.railPosition)) {
        this.railPosition = clamp(saved.railPosition, 0, 1);
      }
      this.activeSurfaceId = String(saved.activeSurfaceId || "");
      this.surfaceModes = Object.fromEntries(
        Object.entries(saved.surfaceModes || {}).map(([surfaceId, mode]) => [
          surfaceId,
          normalizeSurfaceMode(mode),
        ]),
      );
      if (Number.isFinite(Number(saved.width))) this.width = Number(saved.width);
    } catch (error) {
      console.warn("Could not restore right canvas state", error);
    }

    if (isReloadNavigation()) {
      try {
        const savedSession = migratePersistedSurfaceState(
          JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEY) || "{}"),
        );
        if (savedSession?.activeSurfaceId) this.activeSurfaceId = String(savedSession.activeSurfaceId);
        if (savedSession?.surfaceModes) {
          this.surfaceModes = Object.fromEntries(
            Object.entries(savedSession.surfaceModes || {}).map(([surfaceId, mode]) => [
              surfaceId,
              normalizeSurfaceMode(mode),
            ]),
          );
        }
        if (Number.isFinite(Number(savedSession?.width))) this.width = Number(savedSession.width);
        this._restoreMode = normalizeSurfaceMode(savedSession?.mode);
        this._restoreOpenRequested = Boolean(savedSession?.isOpen && savedSession?.activeSurfaceId);
      } catch (error) {
        console.warn("Could not restore right canvas session state", error);
        sessionStorage.removeItem(SESSION_STORAGE_KEY);
      }
    } else {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }

    this.setWidth(this.width, { persist: false });
  },

  updateLayoutMode() {
    const width = viewportWidth();
    const wasMobileMode = this.isMobileMode;
    this.isOverlayMode = width < DESKTOP_BREAKPOINT;
    this.isMobileMode = width <= MOBILE_BREAKPOINT;
    if (this.isMobileMode && !wasMobileMode && this.isOpen) {
      void this.undockActiveSurface();
    }
  },

  applyLayoutState() {
    this.updateLayoutMode();
    if (this.isOpen && !this.isSurfaceEnabled(this.activeSurfaceId)) {
      this.isOpen = false;
      this.ensureActiveSurface();
      this.persist();
    }
    document.documentElement.style.setProperty("--right-canvas-width", `${this.width}px`);
    document.body.classList.toggle("right-canvas-open", this.isOpen && !this.isMobileMode && this.shouldRender());
    document.body.classList.toggle("right-canvas-overlay-mode", this.isOverlayMode);
    document.body.classList.toggle("right-canvas-mobile-mode", this.isMobileMode);
    this.scheduleRestoreOpenSurface();
  },

  widthStyle() {
    if (this.isMobileMode) return "";
    if (!this.isOpen) return "width: 0;";
    if (this.isOverlayMode) {
      return `width: min(${this.width}px, calc(100vw - 44px));`;
    }
    return `width: ${this.width}px;`;
  },

  getSurface(id) {
    const targetId = normalizeSurfaceId(id);
    return this.surfaces.find((surface) => surface.id === targetId)
      || getRegisteredSurfaces().find((surface) => surface.id === targetId)
      || null;
  },

  isSurfaceEnabled(id) {
    return preferencesStore.isUiControlVisible(`canvas:${normalizeSurfaceId(id)}`);
  },

  get railSurfaces() {
    return this.surfaces.filter((surface) => this.isSurfaceEnabled(surface.id));
  },

  get panelSurfaces() {
    return this.railSurfaces.filter((surface) => !surface.actionOnly);
  },

  currentSurface() {
    return this.getSurface(this.activeSurfaceId);
  },

  isSurfaceActive(id) {
    return this.activeSurfaceId === normalizeSurfaceId(id);
  },

  activeTitle() {
    return this.currentSurface()?.title || "Canvas";
  },

  isWelcomeVisible() {
    return !chatsStore.selected;
  },

  shouldRender() {
    return !this.isWelcomeVisible();
  },
};

export const store = createStore("rightCanvas", model);
