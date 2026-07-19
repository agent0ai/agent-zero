export const SURFACE_MODE_DOCKED = "canvas";
export const SURFACE_MODE_FLOATING = "modal";
export const SURFACE_MODAL_GROUP = "surfaces";

const LEGACY_SURFACE_IDS = new Map([
  ["office", "desktop"],
]);

const registeredSurfaces = new Map();
const urlHandlers = new Set();
const SURFACE_MODAL_ACTION_GROUPS = ["surfaces", "window", "new"];

export const CORE_SURFACES = [
  {
    id: "files",
    title: "Files",
    icon: "folder",
    order: 5,
    modalPath: "modals/file-browser/file-browser.html",
    async beginDockHandoff() {
      const { store } = await import("/components/modals/file-browser/file-browser-store.js");
      store.beginSurfaceHandoff?.();
    },
    async finishDockHandoff(payload = {}) {
      const { store } = await import("/components/modals/file-browser/file-browser-store.js");
      store.finishSurfaceHandoff?.(payload);
    },
    async cancelDockHandoff() {
      const { store } = await import("/components/modals/file-browser/file-browser-store.js");
      store.cancelSurfaceHandoff?.();
    },
    async open(payload = {}) {
      const { store } = await import("/components/modals/file-browser/file-browser-store.js");
      await store.openSurface(payload.path || payload.filePath || payload.directory || "");
    },
  },
  {
    id: "browser",
    title: "Browser",
    icon: "language",
    order: 10,
    modalPath: "/plugins/_browser/webui/main.html",
  },
  {
    id: "desktop",
    title: "Desktop",
    icon: "desktop_windows",
    order: 20,
    modalPath: "/plugins/_desktop/webui/main.html",
  },
  {
    id: "editor",
    title: "Editor",
    icon: "article",
    order: 30,
    modalPath: "/plugins/_editor/webui/main.html",
  },
];

export function normalizeSurfaceId(surfaceId = "") {
  const normalized = String(surfaceId || "").trim();
  return LEGACY_SURFACE_IDS.get(normalized) || normalized;
}

export function normalizeSurfaceMode(mode = "") {
  return mode === SURFACE_MODE_FLOATING ? SURFACE_MODE_FLOATING : SURFACE_MODE_DOCKED;
}

export function normalizeModalPath(modalPath = "") {
  return String(modalPath || "").replace(/^\/+/, "");
}

export function sameModalPath(left = "", right = "") {
  return normalizeModalPath(left) === normalizeModalPath(right);
}

export function migratePersistedSurfaceState(saved = {}) {
  const result = { ...(saved || {}) };
  result.activeSurfaceId = normalizeSurfaceId(result.activeSurfaceId || "");
  result.surfaceModes = migrateSurfaceModeMap(result.surfaceModes || {});
  return result;
}

function migrateSurfaceModeMap(surfaceModes = {}) {
  const result = {};
  for (const [surfaceId, mode] of Object.entries(surfaceModes || {})) {
    const normalizedId = normalizeSurfaceId(surfaceId);
    if (!normalizedId) continue;
    if (result[normalizedId] && normalizedId !== surfaceId) continue;
    result[normalizedId] = normalizeSurfaceMode(mode);
  }
  return result;
}

export function registerSurface(surface = {}) {
  const id = normalizeSurfaceId(surface.id || "");
  if (!id) return null;
  const normalized = {
    title: id,
    icon: "web_asset",
    image: "",
    order: 100,
    canOpen: () => true,
    open: () => {},
    close: () => {},
    modalPath: "",
    actionOnly: false,
    ...surface,
    id,
  };
  registeredSurfaces.set(id, normalized);
  return normalized;
}

export function getRegisteredSurfaces() {
  const surfacesById = new Map(CORE_SURFACES.map((surface) => [surface.id, surface]));
  for (const surface of registeredSurfaces.values()) {
    surfacesById.set(surface.id, surface);
  }
  return Array.from(surfacesById.values())
    .filter((surface) => surface?.id)
    .sort((left, right) => (left.order ?? 100) - (right.order ?? 100));
}

export function getSurface(surfaceId = "") {
  const targetId = normalizeSurfaceId(surfaceId);
  return getRegisteredSurfaces().find((surface) => surface.id === targetId) || null;
}

export function modalSurfaceMetadata(doc, modalPath = "") {
  const htmlDataset = doc?.documentElement?.dataset || {};
  const bodyDataset = doc?.body?.dataset || {};
  const surfaceId = normalizeSurfaceId(
    htmlDataset.surfaceId
      || bodyDataset.surfaceId
      || htmlDataset.canvasSurface
      || bodyDataset.canvasSurface
      || "",
  );
  if (!surfaceId) return null;
  return {
    surfaceId,
    modalPath: (
      htmlDataset.surfaceModalPath
      || bodyDataset.surfaceModalPath
      || htmlDataset.canvasModalPath
      || bodyDataset.canvasModalPath
      || modalPath
    ),
    title: (
      htmlDataset.surfaceDockTitle
      || bodyDataset.surfaceDockTitle
      || htmlDataset.canvasDockTitle
      || bodyDataset.canvasDockTitle
      || "Open in surface"
    ),
    icon: (
      htmlDataset.surfaceDockIcon
      || bodyDataset.surfaceDockIcon
      || htmlDataset.canvasDockIcon
      || bodyDataset.canvasDockIcon
      || "dock_to_right"
    ),
  };
}

export function modalHasSurfaceMetadata(modalOrElement) {
  const element = modalOrElement?.element || modalOrElement;
  return Boolean(
    element?.dataset?.surfaceId
      || element?.dataset?.canvasSurface
      || element?.querySelector?.(".modal-inner")?.dataset?.surfaceId
      || element?.querySelector?.(".modal-inner")?.dataset?.canvasSurface
      || modalPathMatchesSurface(modalOrElement?.path || element?.path || ""),
  );
}

export function modalPathMatchesSurface(path = "") {
  return getRegisteredSurfaces().some((surface) => sameModalPath(surface.modalPath || "", path));
}

function modalSurfaceDefinition(modalOrElement) {
  const element = modalOrElement?.element || modalOrElement;
  const path = typeof modalOrElement === "string"
    ? modalOrElement
    : modalOrElement?.path || element?.path || element?.dataset?.modalPath || "";
  return getRegisteredSurfaces().find((surface) => sameModalPath(surface.modalPath || "", path)) || null;
}

function modalSurfaceGroup(modalOrElement) {
  return modalSurfaceDefinition(modalOrElement) ? SURFACE_MODAL_GROUP : "";
}

export function shouldSuppressBackdrop(modal) {
  return Boolean(
    modalHasSurfaceMetadata(modal)
      || modal?.element?.classList?.contains("surface-floating")
      || modal?.element?.classList?.contains("modal-floating")
      || modal?.element?.classList?.contains("modal-no-backdrop")
      || modal?.inner?.classList?.contains("surface-modal")
      || modal?.inner?.classList?.contains("modal-no-backdrop")
  );
}

function setModalParked(modal, parked = false) {
  const element = modal?.element;
  if (!element) return;
  element.classList.toggle("modal-surface-parked", parked);
  element.classList.toggle("surface-modal-parked", parked);
  if (parked) {
    element.classList.remove("show");
    element.setAttribute("aria-hidden", "true");
  } else {
    element.classList.add("show");
    element.removeAttribute("aria-hidden");
  }
}

async function modalApi() {
  return await import("/js/modals.js");
}

async function parkSiblingSurfaceModals(activeModal) {
  const group = modalSurfaceGroup(activeModal);
  if (!group) {
    setModalParked(activeModal, false);
    return;
  }

  const { getModalStack } = await modalApi();
  for (const modal of getModalStack()) {
    setModalParked(modal, modal !== activeModal && modalSurfaceGroup(modal) === group);
  }
}

export async function closeSurfaceGroupModals(options = {}) {
  const { closeModal, getModalStack, isModalOpen } = await modalApi();
  const exceptPath = normalizeModalPath(options?.exceptPath || "");
  const targets = getModalStack()
    .filter((modal) => modalSurfaceGroup(modal) === SURFACE_MODAL_GROUP)
    .map((modal) => ({
      path: modal.path,
      surface: modalSurfaceDefinition(modal),
    }))
    .filter((target) => !exceptPath || normalizeModalPath(target.path) !== exceptPath)
    .reverse();
  const handoffPayload = { source: "modal-group-close" };
  const handoffs = [];
  let closedAll = false;

  try {
    for (const target of targets) {
      if (!target.surface?.beginDockHandoff) continue;
      await target.surface.beginDockHandoff({ ...handoffPayload, modalPath: target.path });
      handoffs.push(target.surface);
    }

    for (const target of targets) {
      if (!isModalOpen(target.path)) continue;
      const closed = await closeModal(target.path);
      if (closed === false) return false;
    }
    closedAll = true;
    return true;
  } finally {
    for (const surface of handoffs) {
      try {
        if (closedAll) {
          await surface.finishDockHandoff?.({ ...handoffPayload, opened: false });
        } else {
          await surface.cancelDockHandoff?.(handoffPayload);
        }
      } catch (error) {
        console.error("Surface modal group handoff cleanup failed", error);
      }
    }
  }
}

function getModalSwitchSurfaces(metadata) {
  const surfacesById = new Map(CORE_SURFACES.map((surface) => [surface.id, surface]));
  for (const surface of getRegisteredSurfaces()) {
    if (!surface?.id || !surface.modalPath || surface.actionOnly) continue;
    surfacesById.set(surface.id, {
      ...surface,
      modalPath: surface.modalPath,
    });
  }

  if (metadata?.surfaceId && !surfacesById.has(metadata.surfaceId)) {
    surfacesById.set(metadata.surfaceId, {
      id: metadata.surfaceId,
      title: metadata.title,
      icon: metadata.icon,
      modalPath: metadata.modalPath,
    });
  }

  return Array.from(surfacesById.values())
    .filter((surface) => surface?.id && surface.modalPath && !surface.actionOnly)
    .sort((left, right) => (left.order ?? 100) - (right.order ?? 100));
}

function directChildByClass(parent, className) {
  return Array.from(parent?.children || []).find((child) => child.classList?.contains(className)) || null;
}

function ensureSurfaceModalActionRail(header) {
  if (!header) return null;
  let rail = directChildByClass(header, "surface-modal-actions");
  if (!rail) {
    rail = document.createElement("div");
    rail.className = "surface-modal-actions";
    rail.setAttribute("aria-label", "Surface modal actions");

    const closeButton = directChildByClass(header, "modal-close") || header.querySelector?.(".modal-close");
    if (closeButton) {
      closeButton.insertAdjacentElement("beforebegin", rail);
    } else {
      header.appendChild(rail);
    }
  }

  for (const [index, groupName] of SURFACE_MODAL_ACTION_GROUPS.entries()) {
    if (!rail.querySelector(`[data-surface-modal-action-group="${groupName}"]`)) {
      if (index > 0 && !rail.querySelector(`[data-surface-modal-separator-before="${groupName}"]`)) {
        const separator = document.createElement("span");
        separator.className = "surface-modal-action-separator";
        separator.dataset.surfaceModalSeparatorBefore = groupName;
        separator.setAttribute("aria-hidden", "true");
        rail.appendChild(separator);
      }

      const group = document.createElement("div");
      group.className = `surface-modal-action-group surface-modal-action-group-${groupName}`;
      group.dataset.surfaceModalActionGroup = groupName;
      rail.appendChild(group);
    }
  }

  refreshSurfaceModalActionRail(header);
  return rail;
}

function surfaceModalActionGroup(header, groupName) {
  const rail = ensureSurfaceModalActionRail(header);
  return rail?.querySelector?.(`[data-surface-modal-action-group="${groupName}"]`) || null;
}

export function refreshSurfaceModalActionRail(header) {
  const rail = directChildByClass(header, "surface-modal-actions");
  if (!rail) return;

  const groups = Object.fromEntries(
    SURFACE_MODAL_ACTION_GROUPS.map((groupName) => [
      groupName,
      rail.querySelector(`[data-surface-modal-action-group="${groupName}"]`),
    ]),
  );
  const hasActions = Object.fromEntries(
    Object.entries(groups).map(([groupName, group]) => [
      groupName,
      Boolean(group?.children?.length),
    ]),
  );

  for (const [groupName, group] of Object.entries(groups)) {
    if (group) group.hidden = !hasActions[groupName];
  }

  const beforeWindow = rail.querySelector('[data-surface-modal-separator-before="window"]');
  if (beforeWindow) beforeWindow.hidden = !(hasActions.surfaces && (hasActions.window || hasActions.new));

  const beforeNew = rail.querySelector('[data-surface-modal-separator-before="new"]');
  if (beforeNew) beforeNew.hidden = !(hasActions.window && hasActions.new);
}

export function placeSurfaceModalHeaderAction(header, element, groupName = "window", options = {}) {
  if (!header || !element) return;
  const normalizedGroup = SURFACE_MODAL_ACTION_GROUPS.includes(groupName) ? groupName : "window";
  const group = surfaceModalActionGroup(header, normalizedGroup);
  if (!group) return;

  if (options.prepend) {
    if (element.parentElement !== group || group.firstElementChild !== element) {
      group.insertBefore(element, group.firstElementChild);
    }
  } else if (element.parentElement !== group) {
    group.appendChild(element);
  }

  refreshSurfaceModalActionRail(header);
}

export function setupFloatingSurfaceModalChrome(options = {}) {
  const root = options.root || null;
  const modal = options.modal || root?.closest?.(".modal") || null;
  const inner = options.inner || modal?.querySelector?.(".modal-inner") || root?.closest?.(".modal-inner") || null;
  const header = options.header || inner?.querySelector?.(".modal-header") || null;
  if (!modal || !inner || !header) return () => {};

  const viewportGap = Number.isFinite(Number(options.viewportGap)) ? Number(options.viewportGap) : 8;
  const minWidth = Number.isFinite(Number(options.minWidth)) ? Number(options.minWidth) : 320;
  const minHeight = Number.isFinite(Number(options.minHeight)) ? Number(options.minHeight) : 300;
  const modalClass = String(options.modalClass || "").trim();
  const focusButtonClass = String(options.focusButtonClass || "").trim();
  const focusEnabled = options.focus !== false;
  const focusLabel = options.focusLabel || "Focus mode";
  const restoreLabel = options.restoreLabel || "Restore size";
  const onBoundsChange = typeof options.onBoundsChange === "function" ? options.onBoundsChange : null;
  const onFocusChange = typeof options.onFocusChange === "function" ? options.onFocusChange : null;

  modal.classList.add("surface-floating", "modal-floating");
  inner.classList.add("surface-modal", "is-draggable-surface-modal");
  if (modalClass) inner.classList.add(modalClass);

  const viewportWidth = () => Math.max(document.documentElement.clientWidth || 0, globalThis.innerWidth || 0);
  const viewportHeight = () => Math.max(document.documentElement.clientHeight || 0, globalThis.innerHeight || 0);
  const availableWidth = () => Math.max(1, viewportWidth() - viewportGap * 2);
  const availableHeight = () => Math.max(1, viewportHeight() - viewportGap * 2);
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
    const maxWidth = availableWidth();
    const maxHeight = availableHeight();
    const safeMinWidth = Math.min(minWidth, maxWidth);
    const safeMinHeight = Math.min(minHeight, maxHeight);
    const width = Math.min(Math.max(safeMinWidth, Number(bounds.width || safeMinWidth)), maxWidth);
    const height = Math.min(Math.max(safeMinHeight, Number(bounds.height || safeMinHeight)), maxHeight);
    return {
      left: Math.min(
        Math.max(viewportGap, Number(bounds.left || viewportGap)),
        Math.max(viewportGap, viewportWidth() - width - viewportGap),
      ),
      top: Math.min(
        Math.max(viewportGap, Number(bounds.top || viewportGap)),
        Math.max(viewportGap, viewportHeight() - height - viewportGap),
      ),
      width,
      height,
    };
  };
  const notifyBoundsChange = () => {
    try {
      onBoundsChange?.({
        ...currentBounds(),
        focus: inner.classList.contains("is-focus-mode"),
      });
    } catch (error) {
      console.error("Surface modal bounds callback failed", error);
    }
  };
  const setBounds = (bounds = {}) => {
    const next = normalizedBounds(bounds);
    inner.style.position = "fixed";
    inner.style.transform = "none";
    inner.style.left = `${Math.round(next.left)}px`;
    inner.style.top = `${Math.round(next.top)}px`;
    inner.style.width = `${Math.round(next.width)}px`;
    inner.style.height = `${Math.round(next.height)}px`;
    inner.style.maxWidth = `${availableWidth()}px`;
    inner.style.maxHeight = `${availableHeight()}px`;
    notifyBoundsChange();
    return next;
  };
  const focusBounds = () => ({
    left: viewportGap,
    top: viewportGap,
    width: availableWidth(),
    height: availableHeight(),
  });
  const clampGeometry = () => {
    if (inner.classList.contains("is-focus-mode")) {
      setBounds(focusBounds());
      return;
    }
    setBounds(currentBounds());
  };

  const initialBounds = currentBounds();
  inner.style.left = `${Math.max(viewportGap, initialBounds.left)}px`;
  inner.style.top = `${Math.max(viewportGap, initialBounds.top)}px`;
  inner.style.transform = "none";
  clampGeometry();

  let drag = null;
  let resizeObserver = null;
  let beforeFocusBounds = null;
  let focusButton = null;

  const updateFocusButton = (active) => {
    if (!focusButton) return;
    const label = active ? restoreLabel : focusLabel;
    focusButton.setAttribute("aria-label", label);
    focusButton.setAttribute("title", label);
    focusButton.classList.toggle("is-active", active);
    const icon = focusButton.querySelector(".material-symbols-outlined");
    if (icon) icon.textContent = active ? "fullscreen_exit" : "fullscreen";
  };
  const setFocusMode = (enabled) => {
    const active = Boolean(enabled);
    if (active === inner.classList.contains("is-focus-mode")) return;
    if (active) {
      beforeFocusBounds = currentBounds();
      inner.classList.add("is-focus-mode");
      setBounds(focusBounds());
    } else {
      inner.classList.remove("is-focus-mode");
      setBounds(beforeFocusBounds || currentBounds());
      beforeFocusBounds = null;
    }
    updateFocusButton(active);
    try {
      onFocusChange?.(active);
    } catch (error) {
      console.error("Surface modal focus callback failed", error);
    }
  };

  const onPointerMove = (event) => {
    if (!drag) return;
    setBounds({
      ...currentBounds(),
      left: drag.left + event.clientX - drag.x,
      top: drag.top + event.clientY - drag.y,
    });
  };
  const onPointerUp = () => {
    drag = null;
    globalThis.removeEventListener("pointermove", onPointerMove);
    globalThis.removeEventListener("pointerup", onPointerUp);
    try {
      header.releasePointerCapture?.(header.__surfaceModalPointerId || 0);
    } catch {}
  };
  const onPointerDown = (event) => {
    if (event.button !== 0) return;
    if (event.target?.closest?.("button, input, select, textarea, a, [data-no-modal-drag], .surface-modal-actions")) return;
    if (inner.classList.contains("is-focus-mode")) return;
    const bounds = currentBounds();
    drag = {
      x: event.clientX,
      y: event.clientY,
      left: bounds.left,
      top: bounds.top,
    };
    header.__surfaceModalPointerId = event.pointerId;
    header.setPointerCapture?.(event.pointerId);
    globalThis.addEventListener("pointermove", onPointerMove);
    globalThis.addEventListener("pointerup", onPointerUp);
    event.preventDefault();
  };
  header.addEventListener("pointerdown", onPointerDown);

  if (focusEnabled) {
    focusButton = globalThis.document.createElement("button");
    focusButton.type = "button";
    focusButton.className = ["surface-button", "surface-modal-focus-button", focusButtonClass]
      .filter(Boolean)
      .join(" ");
    focusButton.innerHTML = '<span class="material-symbols-outlined" aria-hidden="true">fullscreen</span>';
    const onFocusClick = () => setFocusMode(!inner.classList.contains("is-focus-mode"));
    updateFocusButton(false);
    focusButton.addEventListener("click", onFocusClick);
    focusButton.__surfaceModalFocusCleanup = () => focusButton.removeEventListener("click", onFocusClick);
    placeSurfaceModalHeaderAction(header, focusButton, "window");
  }

  globalThis.addEventListener("resize", clampGeometry);
  if (globalThis.ResizeObserver) {
    resizeObserver = new ResizeObserver(clampGeometry);
    resizeObserver.observe(inner);
  }

  return () => {
    focusButton?.__surfaceModalFocusCleanup?.();
    focusButton?.remove();
    refreshSurfaceModalActionRail(header);
    header.removeEventListener("pointerdown", onPointerDown);
    globalThis.removeEventListener("pointermove", onPointerMove);
    globalThis.removeEventListener("pointerup", onPointerUp);
    globalThis.removeEventListener("resize", clampGeometry);
    resizeObserver?.disconnect?.();
    inner.classList.remove("is-focus-mode", "is-draggable-surface-modal");
  };
}

function markSurfaceModal(modal, metadata) {
  const element = modal?.element;
  const inner = modal?.inner || element?.querySelector?.(".modal-inner");
  if (!element || !inner) return;
  element.dataset.surfaceId = metadata.surfaceId;
  element.dataset.modalRestore = "surface";
  element.classList.add("surface-floating", "modal-floating", "modal-no-backdrop", "modal-explicit-close");
  inner.dataset.modalRestore = "surface";
  inner.classList.add("surface-modal", "modal-no-backdrop", "modal-explicit-close");
}

function createModalSurfaceButton(surface, metadata, modal) {
  const title = surface.title || surface.id;
  const targetModalPath = surface.modalPath || "";
  const normalizedId = normalizeSurfaceId(surface.id);
  const isActive = normalizedId === metadata.surfaceId || sameModalPath(targetModalPath, modal.path);
  const button = document.createElement("button");
  button.type = "button";
  button.className = "surface-button modal-surface-button";
  button.dataset.surfaceId = normalizedId;
  button.dataset.canvasSurface = normalizedId;
  button.setAttribute("aria-label", title);
  button.setAttribute("aria-pressed", isActive.toString());
  if (isActive) button.classList.add("is-active");

  if (surface.image) {
    const image = document.createElement("img");
    image.className = "modal-surface-image";
    image.src = surface.image;
    image.alt = "";
    image.setAttribute("aria-hidden", "true");
    button.appendChild(image);
  } else {
    const icon = document.createElement("span");
    icon.className = "material-symbols-outlined";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = surface.icon || "web_asset";
    button.appendChild(icon);
  }

  button.addEventListener("click", async () => {
    if (button.disabled || isActive || !targetModalPath) return;
    button.disabled = true;
    try {
      await recordMode(normalizedId, SURFACE_MODE_FLOATING);
      const { ensureModalOpen } = await modalApi();
      const openPromise = ensureModalOpen(targetModalPath);
      if (openPromise?.catch) {
        openPromise.catch((error) => console.error(`Modal surface ${surface.id} failed to open`, error));
      }
    } finally {
      if (document.contains(button)) button.disabled = false;
    }
  });

  return button;
}

function configureModalSurfaceSwitcher(modal, metadata) {
  if (!metadata || !modal?.header || modal.header.querySelector(".surface-switcher, .modal-surface-switcher")) {
    return;
  }

  const surfaces = getModalSwitchSurfaces(metadata);
  if (surfaces.length <= 1) return;

  const switcher = document.createElement("div");
  switcher.className = "surface-switcher modal-surface-switcher";
  switcher.setAttribute("role", "group");
  switcher.setAttribute("aria-label", "Modal surfaces");

  for (const surface of surfaces) {
    switcher.appendChild(createModalSurfaceButton(surface, metadata, modal));
  }

  placeSurfaceModalHeaderAction(modal.header, switcher, "surfaces");
}

function configureModalDockButton(modal, metadata) {
  if (!metadata || !modal?.header || modal.header.querySelector(".surface-dock-button")) {
    return;
  }

  void recordMode(metadata.surfaceId, SURFACE_MODE_FLOATING);

  const button = document.createElement("button");
  button.type = "button";
  button.className = "surface-dock-button modal-dock-button";
  button.setAttribute("aria-label", metadata.title);
  button.innerHTML = `<span class="material-symbols-outlined" aria-hidden="true">${metadata.icon}</span>`;
  button.addEventListener("click", async () => {
    if (button.disabled) return;
    button.disabled = true;
    try {
      await dock(metadata.surfaceId, {
        modalPath: metadata.modalPath,
        sourceModalPath: modal.path,
        source: "modal",
        closeSourceModal: async () => {
          const closed = await closeSurfaceGroupModals();
          if (closed === false) return false;
          return !document.contains(modal.element);
        },
      });
    } finally {
      if (document.contains(button)) button.disabled = false;
    }
  });

  placeSurfaceModalHeaderAction(modal.header, button, "window", { prepend: true });
}

async function configureSurfaceModal(event) {
  const { modal, doc } = event?.detail || {};
  const metadata = modalSurfaceMetadata(doc, modal?.path || "");
  if (!metadata) return;
  markSurfaceModal(modal, metadata);
  configureModalSurfaceSwitcher(modal, metadata);
  configureModalDockButton(modal, metadata);
  const { persistRestorableModalStack, refreshModalStack } = await modalApi();
  refreshModalStack();
  persistRestorableModalStack?.({ force: true });
}

export async function open(surfaceId = "", payload = {}) {
  const { store } = await import("/components/canvas/right-canvas-store.js");
  return await store.open(normalizeSurfaceId(surfaceId), payload);
}

export async function openLatest(surfaceId = "", payload = {}) {
  const { store } = await import("/components/canvas/right-canvas-store.js");
  return await store.openLatest(normalizeSurfaceId(surfaceId), payload);
}

export async function dock(surfaceId = "", payload = {}) {
  const { store } = await import("/components/canvas/right-canvas-store.js");
  return await store.dockSurface(normalizeSurfaceId(surfaceId), payload);
}

export async function recordMode(surfaceId = "", mode = SURFACE_MODE_DOCKED, options = {}) {
  const { store } = await import("/components/canvas/right-canvas-store.js");
  return store.recordSurfaceMode?.(normalizeSurfaceId(surfaceId), normalizeSurfaceMode(mode), options);
}

export function registerUrlHandler(handler) {
  if (typeof handler !== "function") return () => {};
  urlHandlers.add(handler);
  return () => urlHandlers.delete(handler);
}

export async function handleUrlIntent(intent = {}) {
  for (const handler of Array.from(urlHandlers)) {
    const handled = await handler(intent);
    if (handled) return true;
  }
  globalThis.dispatchEvent?.(new CustomEvent("surface-url-intent", { detail: intent }));
  return false;
}

document.addEventListener("modal-content-loaded", (event) => {
  void configureSurfaceModal(event);
});

document.addEventListener("modal-activated", (event) => {
  void parkSiblingSurfaceModals(event?.detail?.modal);
});

document.addEventListener("modal-closed", async () => {
  const { getModalStack, refreshModalStack } = await modalApi();
  const stack = getModalStack();
  if (stack.length > 0) {
    refreshModalStack();
  }
});

globalThis.closeSurfaceGroupModals = closeSurfaceGroupModals;
