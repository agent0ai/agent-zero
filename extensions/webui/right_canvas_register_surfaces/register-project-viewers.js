import { store } from "/components/team/project-surface-store.js";

export default function registerProjectViewers(surfaces) {
  if (globalThis.runtimeInfo?.teamRole !== "member") return;
  for (const [id, title, icon, order] of [
    ["browser", "Browser", "language", 10],
    ["desktop", "Desktop", "desktop_windows", 20],
  ]) {
    surfaces.registerSurface({
      id, title, icon, order,
      modalPath: `team/project-${id}.html`,
      open: (payload = {}) => store.open(id, payload.path || payload.filePath || ""),
    });
  }
}
