// Plugin frontend auto-injection.
// Imported once in initFw.js. The backend resolves plugin components and their
// injection targets (parsed from <meta name="plugin-target"> server-side).
// This module simply creates <x-component> elements at the declared targets;
// the standard components.js MutationObserver handles loading automatically.
import { callJsonApi } from "/js/api.js";

const injected = new Set();

function tryInject(entry) {
  const key = `${entry.component_url}|${entry.target}`;
  if (injected.has(key)) return true;
  const host = document.querySelector(entry.target);
  if (!host) return false;
  injected.add(key);
  const el = document.createElement("x-component");
  el.setAttribute("path", `../${entry.component_url.replace(/^\/+/, "")}`);
  el.className = "plugin-slot-entry";
  host.appendChild(el);
  return true;
}

(async () => {
  let res;
  try {
    res = await callJsonApi("/plugins_resolve", {});
  } catch (e) {
    console.warn("Plugin resolve failed:", e);
    return;
  }
  if (!res.ok || !Array.isArray(res.data)) return;

  // Only auto-inject entries that declare a target; others are standalone (modals etc.)
  const pending = res.data.filter(e => e?.component_url && e?.target);
  const remaining = pending.filter(e => !tryInject(e));

  // Retry for targets that load after initial render (e.g. sidebar components)
  if (remaining.length > 0) {
    const obs = new MutationObserver(() => {
      for (let i = remaining.length - 1; i >= 0; i--) {
        if (tryInject(remaining[i])) remaining.splice(i, 1);
      }
      if (remaining.length === 0) obs.disconnect();
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }
})();
