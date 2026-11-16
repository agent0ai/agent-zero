import { getRegisteredSurfaces, sameModalPath, open } from "/js/surfaces.js";
import { store } from "/components/canvas/right-canvas-store.js";

export default async function routeSurfaceModal(context) {
  const surface = getRegisteredSurfaces().find(surface => surface.modalPath && sameModalPath(surface.modalPath, context.modalPath));
  if (!surface || surface.actionOnly) return;
  context.cancel = true;
  if (await open(surface.id)) await store.whenClosed();
}
