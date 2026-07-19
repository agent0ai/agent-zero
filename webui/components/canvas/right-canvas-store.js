import { createStore } from "/js/AlpineStore.js";
import { callJsExtensions } from "/js/extensions.js";
import {
  SURFACE_MODE_DOCKED,
  SURFACE_MODE_FLOATING,
  closeSurfaceGroupModals,
  getRegisteredSurfaces,
  migratePersistedSurfaceState,
  normalizeSurfaceId,
  normalizeSurfaceMode,
  registerSurface as registerSurfaceDefinition,
} from "/js/surfaces.js";

const STORAGE_KEY = "a0.rightCanvas";
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

const model = {
  surfaces: [],
  activeSurfaceId: "",
  surfaceModes: {},
  mountedSurfaces: {},
  isOpen: false,
  width: DEFAULT_WIDTH,
  isOverlayMode: false,
  isMobileMode: false,
  _initialized: false,
  _registering: false,
  _rootElement: null,
  _resizeCleanup: null,
  _lastPayloadBySurface: {},

  async init(element = null) {
    if (element) this._rootElement = element;
    if (this._initialized) {
      this.applyLayoutState();
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

  async open(surfaceId = "", payload = {}) {
    const targetId = normalizeSurfaceId(surfaceId || this.activeSurfaceId || this.panelSurfaces[0]?.id || "");
    const surface = this.getSurface(targetId);
    if (!surface) {
      return false;
    }
    if (this.isMobileMode && !surface.actionOnly) {
      return false;
    }
    if (typeof surface.canOpen === "function" && surface.canOpen(payload) === false) {
      return false;
    }

    if (surface.actionOnly) {
      try {
        await surface.open?.(payload || {});
      } catch (error) {
        console.error(`Canvas action ${targetId} failed`, error);
      }
      return true;
    }

    this.activeSurfaceId = targetId;
    this.markSurfaceMounted(targetId);
    this.isOpen = true;
    this.recordSurfaceMode(targetId, SURFACE_MODE_DOCKED, { persist: false });
    this._lastPayloadBySurface[targetId] = payload || {};
    this.persist();
    this.applyLayoutState();

    try {
      await surface.open?.(payload || {});
    } catch (error) {
      console.error(`Canvas surface ${targetId} failed to open`, error);
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
    return Boolean(this.isOpen && this.isSurfaceMounted(id));
  },

  isSurfaceVisible(id) {
    const targetId = normalizeSurfaceId(id);
    return Boolean(this.isOpen && this.activeSurfaceId === targetId && this.isSurfaceMounted(targetId));
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
    const targetId = normalizeSurfaceId(surfaceId || this.activeSurfaceId || this.panelSurfaces[0]?.id || "");
    if (!targetId) return false;
    if (this.latestSurfaceMode(targetId) === SURFACE_MODE_FLOATING) {
      return await this.openModalSurface(targetId, payload);
    }
    return await this.open(targetId, payload);
  },

  async close() {
    this.isOpen = false;
    this.persist();
    this.applyLayoutState();
    return true;
  },

  async dockSurface(surfaceId, payload = {}) {
    surfaceId = normalizeSurfaceId(surfaceId);
    if (this.isMobileMode) {
      return false;
    }
    const surface = this.getSurface(surfaceId);
    if (!surface) {
      return false;
    }
    const modalPath = payload.modalPath || surface.modalPath || "";
    let handoffStarted = false;
    try {
      await surface.beginDockHandoff?.(payload);
      handoffStarted = true;

      const closed = await this.closeDockSourceModal(payload, modalPath);
      if (closed === false) {
        await surface.cancelDockHandoff?.(payload);
        return false;
      }

      const openPayload = { ...payload, source: "modal" };
      delete openPayload.closeSourceModal;
      const opened = await this.open(surfaceId, openPayload);
      await surface.finishDockHandoff?.({ ...openPayload, opened });
      return opened;
    } catch (error) {
      if (handoffStarted) {
        await surface.cancelDockHandoff?.(payload);
      }
      console.error(`Canvas surface ${surfaceId} failed to dock`, error);
      return false;
    }
  },

  async closeDockSourceModal(payload = {}, modalPath = "") {
    if (typeof payload.closeSourceModal === "function") {
      return (await payload.closeSourceModal()) !== false;
    }

    const sourceModalPath = payload.sourceModalPath || modalPath;
    if (sourceModalPath || modalPath) {
      const closed = await closeSurfaceGroupModals();
      if (closed === false) return false;
      if (!sourceModalPath || !globalThis.isModalOpen?.(sourceModalPath)) return true;
    }
    if (sourceModalPath && globalThis.isModalOpen?.(sourceModalPath)) {
      return (await globalThis.closeModal?.(sourceModalPath)) !== false;
    }
    if (modalPath && modalPath !== sourceModalPath && globalThis.isModalOpen?.(modalPath)) {
      return (await globalThis.closeModal?.(modalPath)) !== false;
    }
    return true;
  },

  async undockSurface(surfaceId = "", payload = {}) {
    const targetId = normalizeSurfaceId(surfaceId || this.activeSurfaceId);
    const surface = this.getSurface(targetId);
    const modalPath = payload.modalPath || surface?.modalPath || "";
    if (!surface || !modalPath) return false;
    const openModal = globalThis.ensureModalOpen || globalThis.openModal;
    if (!openModal) return false;
    if (this.activeSurfaceId === targetId) {
      this.isOpen = false;
      this.persist();
      this.applyLayoutState();
    }
    this.recordSurfaceMode(targetId, SURFACE_MODE_FLOATING);
    const modalPromise = openModal(modalPath);
    if (modalPromise?.catch) {
      modalPromise.catch((error) => console.error(`Canvas surface ${targetId} failed to undock`, error));
    }
    return true;
  },

  async openModalSurface(surfaceId = "", payload = {}) {
    const targetId = normalizeSurfaceId(surfaceId || this.activeSurfaceId);
    const surface = this.getSurface(targetId);
    const modalPath = payload.modalPath || surface?.modalPath || "";
    if (!surface || !modalPath) return false;
    const openModal = globalThis.ensureModalOpen || globalThis.openModal;
    if (!openModal) return false;

    if (this.isOpen && this.activeSurfaceId === targetId) {
      this.isOpen = false;
      this.persist();
      this.applyLayoutState();
    }

    this.recordSurfaceMode(targetId, SURFACE_MODE_FLOATING);
    const modalPromise = openModal(modalPath);
    if (modalPromise?.catch) {
      modalPromise.catch((error) => console.error(`Canvas surface ${targetId} failed to open as modal`, error));
    }
    return true;
  },

  async undockActiveSurface() {
    return await this.undockSurface(this.activeSurfaceId);
  },

  currentSurfaceCanUndock() {
    return Boolean(this.currentSurface()?.modalPath);
  },

  async toggle(surfaceId = "", payload = {}) {
    const targetId = normalizeSurfaceId(surfaceId || this.activeSurfaceId || this.panelSurfaces[0]?.id || "");
    if (this.isOpen && targetId === this.activeSurfaceId) {
      await this.close();
      return false;
    }
    return await this.open(targetId, payload);
  },

  async toggleCanvas() {
    if (this.isMobileMode) {
      return false;
    }
    if (this.isOpen) {
      await this.close();
      return false;
    }
    return await this.open(this.activeSurfaceId || this.panelSurfaces[0]?.id || "");
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
    if (event.button !== 0) return;
    event.preventDefault();
    this.dispatchResizeEvent("right-canvas-resize-start");

    const onPointerMove = (moveEvent) => {
      const nextWidth = viewportWidth() - moveEvent.clientX;
      this.setWidth(nextWidth);
    };
    const onPointerUp = () => {
      globalThis.removeEventListener("pointermove", onPointerMove);
      globalThis.removeEventListener("pointerup", onPointerUp);
      globalThis.removeEventListener("pointercancel", onPointerUp);
      document.body.classList.remove("right-canvas-resizing");
      this.persist();
      this.dispatchResizeEvent("right-canvas-resize-end");
    };

    document.body.classList.add("right-canvas-resizing");
    globalThis.addEventListener("pointermove", onPointerMove);
    globalThis.addEventListener("pointerup", onPointerUp);
    globalThis.addEventListener("pointercancel", onPointerUp);
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

  persist() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          isOpen: this.isOpen,
          activeSurfaceId: this.activeSurfaceId,
          surfaceModes: this.surfaceModes,
          width: this.width,
        }),
      );
    } catch (error) {
      console.warn("Could not persist right canvas state", error);
    }
  },

  restore() {
    this.width = this.defaultWidth();
    try {
      const saved = migratePersistedSurfaceState(JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"));
      this.isOpen = false;
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
    this.setWidth(this.width, { persist: false });
  },

  updateLayoutMode() {
    const width = viewportWidth();
    const wasMobileMode = this.isMobileMode;
    this.isOverlayMode = width < DESKTOP_BREAKPOINT;
    this.isMobileMode = width <= MOBILE_BREAKPOINT;
    if (this.isMobileMode) {
      const wasOpen = this.isOpen;
      const mountedIds = this.mountedSurfaceIds();
      this.isOpen = false;
      this.mountedSurfaces = {};
      if ((wasOpen || mountedIds.length > 0) && mountedIds.length > 0) {
        globalThis.setTimeout?.(() => {
          for (const surfaceId of mountedIds) {
            const surface = this.getSurface(surfaceId);
            const payload = this._lastPayloadBySurface[surfaceId] || {};
            surface?.close?.({ ...payload, reason: "mobile" });
          }
        }, 0);
      }
    } else if (wasMobileMode && this.width < MIN_WIDTH) {
      this.width = this.defaultWidth();
    }
  },

  applyLayoutState() {
    this.updateLayoutMode();
    document.documentElement.style.setProperty("--right-canvas-width", `${this.width}px`);
    document.body.classList.toggle("right-canvas-open", this.isOpen && !this.isMobileMode);
    document.body.classList.toggle("right-canvas-overlay-mode", this.isOverlayMode);
    document.body.classList.toggle("right-canvas-mobile-mode", this.isMobileMode);
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

  get railSurfaces() {
    return this.surfaces;
  },

  get panelSurfaces() {
    return this.surfaces.filter((surface) => !surface.actionOnly);
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

  shouldRender() {
    return !this.isMobileMode;
  },
};

export const store = createStore("rightCanvas", model);
