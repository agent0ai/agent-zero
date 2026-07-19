export const SURFACE_MODE_DOCKED = "canvas";
export const SURFACE_MODE_FLOATING = "modal";
export const SURFACE_MODAL_GROUP = "surfaces";

const LEGACY_SURFACE_IDS = new Map([
  ["office", "desktop"],
]);

const registeredSurfaces = new Map();
const urlHandlers = new Set();

export const CORE_SURFACES = [
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

function markSurfaceModal(modal, metadata) {
  const element = modal?.element;
  const inner = modal?.inner || element?.querySelector?.(".modal-inner");
  if (!element || !inner) return;
  element.dataset.surfaceId = metadata.surfaceId;
  element.classList.add("surface-floating", "modal-floating", "modal-no-backdrop", "modal-explicit-close");
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

  modal.close?.insertAdjacentElement("beforebegin", switcher);
}

function configureModalDockButton(modal, metadata) {
  if (!metadata || !modal?.header || modal.header.querySelector(".surface-dock-button, .modal-dock-button")) {
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

  modal.close?.insertAdjacentElement("beforebegin", button);
}

async function configureSurfaceModal(event) {
  const { modal, doc } = event?.detail || {};
  const metadata = modalSurfaceMetadata(doc, modal?.path || "");
  if (!metadata) return;
  markSurfaceModal(modal, metadata);
  configureModalSurfaceSwitcher(modal, metadata);
  configureModalDockButton(modal, metadata);
  const { refreshModalStack } = await modalApi();
  refreshModalStack();
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
