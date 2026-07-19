import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const BROWSER_EXTENSIONS_API = "/plugins/_browser/extensions";
const BROWSER_STATUS_API = "/plugins/_browser/status";
const RUNTIME_BACKENDS = new Set(["container", "host_required"]);
const BROWSER_TAB_SCOPES = new Set(["per_context", "shared"]);
const HOST_PRIVACY_POLICIES = new Set(["enforce_local", "warn", "allow"]);
const HOST_PROFILE_MODES = new Set(["existing", "agent"]);
const DEFAULT_MAX_OPEN_TABS = 32;
const MIN_MAX_OPEN_TABS = 1;
const HARD_MAX_OPEN_TABS = 50;
const HOST_BROWSER_STATUS_REFRESH_MS = 1000;
const CUSTOM_HOST_BROWSER_SELECTION = "__custom_endpoint__";

function normalizePathList(value) {
  const source = Array.isArray(value)
    ? value
    : String(value || "").split(/\r?\n/);
  const seen = new Set();
  const paths = [];
  for (const item of source) {
    const path = String(item || "").trim();
    if (!path || seen.has(path)) continue;
    seen.add(path);
    paths.push(path);
  }
  return paths;
}

function ensureConfig(config) {
  if (!config || typeof config !== "object") return null;
  config.extension_paths = normalizePathList(config.extension_paths);
  config.default_homepage = String(config.default_homepage || "about:blank").trim() || "about:blank";
  config.autofocus_active_page = normalizeBoolean(config.autofocus_active_page, true);
  config.browser_tab_scope = normalizeChoice(config.browser_tab_scope, BROWSER_TAB_SCOPES, "per_context");
  config.max_open_tabs = normalizeInt(config.max_open_tabs, DEFAULT_MAX_OPEN_TABS, MIN_MAX_OPEN_TABS, HARD_MAX_OPEN_TABS);
  config.runtime_backend = normalizeRuntimeBackend(config.runtime_backend);
  config.host_browser_privacy_policy = normalizeChoice(
    config.host_browser_privacy_policy,
    HOST_PRIVACY_POLICIES,
    "allow",
  );
  config.host_browser_profile_mode = normalizeChoice(
    config.host_browser_profile_mode,
    HOST_PROFILE_MODES,
    "existing",
  );
  config.host_browser_selection = normalizeHostBrowserSelection(config.host_browser_selection);
  config.model_preset = String(config.model_preset || "").trim();
  delete config.model;
  return config;
}

function normalizeChoice(value, allowed, fallback) {
  const normalized = String(value || "").trim().toLowerCase().replace(/-/g, "_");
  return allowed.has(normalized) ? normalized : fallback;
}

function normalizeInt(value, fallback, minimum, maximum) {
  const number = Number.parseInt(value, 10);
  if (!Number.isFinite(number)) return fallback;
  return Math.max(minimum, Math.min(maximum, number));
}

function normalizeRuntimeBackend(value) {
  const normalized = String(value || "").trim().toLowerCase().replace(/-/g, "_");
  if (normalized === "host_when_available") return "host_required";
  return RUNTIME_BACKENDS.has(normalized) ? normalized : "container";
}

function normalizeHostBrowserSelection(value) {
  const raw = String(value || "").trim();
  if (raw.includes("://") || /^(?:\[[^\]]+\]|[^/:\s]+):\d+$/.test(raw)) {
    return raw.replace(/\s+/g, "").slice(0, 2048);
  }
  return raw.toLowerCase().replace(/\s+/g, "_").slice(0, 200);
}

function normalizeCustomHostBrowserEndpoint(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const candidate = raw.includes("://") ? raw : `http://${raw}`;
  try {
    const url = new URL(candidate);
    if (!url.host) return "";
    if (["http:", "https:"].includes(url.protocol)) {
      if (!["/", "/json/version"].includes(url.pathname)) return "";
      const path = url.pathname === "/" ? "" : url.pathname;
      return normalizeHostBrowserSelection(`${url.protocol}//${url.host}${path}${url.search || ""}`);
    }
    if (!["ws:", "wss:"].includes(url.protocol)) return "";
    return normalizeHostBrowserSelection(`${url.protocol}//${url.host}${url.pathname === "/" ? "" : url.pathname}${url.search || ""}`);
  } catch (_error) {
    return "";
  }
}

function isCustomHostBrowserEndpoint(value) {
  return Boolean(normalizeCustomHostBrowserEndpoint(value));
}

function normalizeBoolean(value, fallback = true) {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return Boolean(value);
  const normalized = String(value).trim().toLowerCase();
  if (["1", "true", "yes", "on", "enabled"].includes(normalized)) return true;
  if (["0", "false", "no", "off", "disabled"].includes(normalized)) return false;
  return fallback;
}

function hostBrowserFamilyLabel(value) {
  const family = String(value || "").trim().toLowerCase();
  const a0Profile = family.endsWith("-a0");
  const remoteDebugging = family.endsWith("-cdp");
  const base = a0Profile ? family.slice(0, -3) : remoteDebugging ? family.slice(0, -4) : family;
  const labels = {
    chrome: "Chrome",
    chromium: "Chromium",
    edge: "Edge",
    "edge-dev": "Edge Dev",
    brave: "Brave",
    opera: "Opera",
    vivaldi: "Vivaldi",
  };
  const label = labels[base] || "Host browser";
  if (remoteDebugging) return `${label} (allowed)`;
  return a0Profile ? `${label} (A0 profile)` : label;
}

function hostBrowserStatusLabel(value) {
  const status = String(value || "").trim().toLowerCase();
  if (status === "active") return "open";
  if (status === "ready") return "ready";
  if (status === "disabled") return "will open on first use";
  if (status === "relaunch_required") return "close browser and retry";
  if (status === "unsupported") return "unavailable";
  return status || "ready";
}

export const store = createStore("browserConfig", {
  config: null,
  extensionsList: [],
  extensionsLoading: false,
  extensionsError: "",
  extensionsMessage: "",
  extensionDeleteLoadingPath: "",
  hostBrowserStatus: null,
  hostBrowserStatusLoading: false,
  hostBrowserStatusRefreshTimer: null,
  hostBrowserCustomEndpoint: "",
  hostBrowserCustomMode: false,

  async init(config) {
    this.bindConfig(config);
    await Promise.all([this.loadExtensionsList(), this.loadHostBrowserStatus()]);
    this.startHostBrowserStatusRefresh();
  },

  cleanup() {
    this.stopHostBrowserStatusRefresh();
    this.config = null;
    this.extensionsList = [];
    this.extensionsError = "";
    this.extensionsMessage = "";
    this.extensionDeleteLoadingPath = "";
    this.hostBrowserStatus = null;
    this.hostBrowserStatusLoading = false;
    this.hostBrowserCustomEndpoint = "";
    this.hostBrowserCustomMode = false;
  },

  startHostBrowserStatusRefresh() {
    this.stopHostBrowserStatusRefresh();
    this.hostBrowserStatusRefreshTimer = window.setInterval(
      () => this.loadHostBrowserStatus(),
      HOST_BROWSER_STATUS_REFRESH_MS,
    );
  },

  stopHostBrowserStatusRefresh() {
    if (!this.hostBrowserStatusRefreshTimer) return;
    window.clearInterval(this.hostBrowserStatusRefreshTimer);
    this.hostBrowserStatusRefreshTimer = null;
  },

  bindConfig(config) {
    const safeConfig = ensureConfig(config);
    if (!safeConfig) return;
    if (this.config === safeConfig) return;
    this.config = safeConfig;
    if (isCustomHostBrowserEndpoint(safeConfig.host_browser_selection)) {
      this.hostBrowserCustomEndpoint = safeConfig.host_browser_selection;
    }
  },

  setAutofocusActivePage(enabled) {
    const safeConfig = ensureConfig(this.config);
    if (!safeConfig) return;
    safeConfig.autofocus_active_page = Boolean(enabled);
  },

  autofocusLabel() {
    return this.config?.autofocus_active_page === false ? "Off" : "On";
  },

  setBrowserTabScope(value) {
    const safeConfig = ensureConfig(this.config);
    if (!safeConfig) return;
    safeConfig.browser_tab_scope = normalizeChoice(value, BROWSER_TAB_SCOPES, "per_context");
  },

  browserTabScopeLabel() {
    return this.config?.browser_tab_scope === "shared" ? "Shared" : "Per chat";
  },

  normalizeMaxOpenTabs() {
    const safeConfig = ensureConfig(this.config);
    if (!safeConfig) return;
    safeConfig.max_open_tabs = normalizeInt(
      safeConfig.max_open_tabs,
      DEFAULT_MAX_OPEN_TABS,
      MIN_MAX_OPEN_TABS,
      HARD_MAX_OPEN_TABS,
    );
  },

  runtimeBackendLabel() {
    const value = this.config?.runtime_backend || "container";
    if (value === "host_required") return "Bring Your Own Browser";
    return "Docker Browser";
  },

  privacyPolicyLabel() {
    const value = this.config?.host_browser_privacy_policy || "allow";
    if (value === "warn") return "Warn When Using Cloud";
    if (value === "allow") return "Allow";
    return "Local Models Only";
  },

  hostBrowserOptions() {
    const connectors = Array.isArray(this.hostBrowserStatus?.connectors)
      ? this.hostBrowserStatus.connectors
      : [];
    const options = [{ value: "", label: "Automatic (A0 CLI chooses)" }];
    const seen = new Set([""]);
    for (const connector of connectors) {
      const advertised = Array.isArray(connector?.available_browsers)
        ? connector.available_browsers
        : [];
      for (const browser of advertised) {
        const value = normalizeCustomHostBrowserEndpoint(browser?.cdp_endpoint || browser?.id);
        if (!value || seen.has(value)) continue;
        seen.add(value);
        const label = browser?.label || hostBrowserFamilyLabel(browser?.family || value);
        const status = browser?.status ? ` - ${hostBrowserStatusLabel(browser.status)}` : "";
        options.push({ value, label: `${label}${status}` });
      }
      const fallbackValue = normalizeCustomHostBrowserEndpoint(connector?.cdp_endpoint || connector?.browser_id);
      if (fallbackValue && !seen.has(fallbackValue)) {
        seen.add(fallbackValue);
        const label = connector?.browser_label || hostBrowserFamilyLabel(connector?.browser_family || fallbackValue);
        options.push({ value: fallbackValue, label });
      }
    }
    const selected = normalizeHostBrowserSelection(this.config?.host_browser_selection);
    if (selected && !seen.has(selected) && !isCustomHostBrowserEndpoint(selected)) {
      seen.add(selected);
      options.push({ value: selected, label: `Saved: ${selected}` });
    }
    options.push({ value: CUSTOM_HOST_BROWSER_SELECTION, label: "Custom endpoint" });
    return options;
  },

  hostBrowserSelectValue() {
    if (this.hostBrowserCustomMode) return CUSTOM_HOST_BROWSER_SELECTION;
    const selected = normalizeHostBrowserSelection(this.config?.host_browser_selection);
    if (!selected) return "";
    if (this.hostBrowserOptions().some((option) => option.value === selected)) return selected;
    if (isCustomHostBrowserEndpoint(selected)) return CUSTOM_HOST_BROWSER_SELECTION;
    return selected;
  },

  setHostBrowserSelection(value) {
    const safeConfig = ensureConfig(this.config);
    if (!safeConfig) return;
    if (value === CUSTOM_HOST_BROWSER_SELECTION) {
      this.hostBrowserCustomMode = true;
      if (isCustomHostBrowserEndpoint(safeConfig.host_browser_selection)) {
        this.hostBrowserCustomEndpoint = safeConfig.host_browser_selection;
      } else {
        safeConfig.host_browser_selection = "";
      }
      return;
    }
    this.hostBrowserCustomMode = false;
    safeConfig.host_browser_selection = normalizeHostBrowserSelection(value);
  },

  showCustomHostBrowserEndpoint() {
    return this.hostBrowserSelectValue() === CUSTOM_HOST_BROWSER_SELECTION;
  },

  setCustomHostBrowserEndpoint(value) {
    this.hostBrowserCustomMode = true;
    this.hostBrowserCustomEndpoint = String(value || "").trim();
    const safeConfig = ensureConfig(this.config);
    if (!safeConfig) return;
    const endpoint = normalizeCustomHostBrowserEndpoint(this.hostBrowserCustomEndpoint);
    safeConfig.host_browser_selection = endpoint
      || normalizeHostBrowserSelection(this.hostBrowserCustomEndpoint);
  },

  customHostBrowserEndpointDiagnostic() {
    if (!this.hostBrowserCustomEndpoint) {
      return "Paste a ws://.../devtools/browser/... endpoint from the browser inspect page.";
    }
    const endpoint = normalizeCustomHostBrowserEndpoint(this.hostBrowserCustomEndpoint);
    if (endpoint) return `Using ${endpoint}`;
    return "Use host:port, an http(s):// discovery address, or a ws(s):// browser endpoint.";
  },

  hostBrowserProfileModeLabel() {
    const value = this.config?.host_browser_profile_mode || "existing";
    if (value === "agent") return "Clean Agent Profile";
    return "Existing Browser Profile";
  },

  async loadHostBrowserStatus() {
    if (this.hostBrowserStatusLoading) return;
    this.hostBrowserStatusLoading = true;
    try {
      const response = await callJsonApi(BROWSER_STATUS_API, {});
      this.hostBrowserStatus = response?.host_browser || { connectors: [] };
    } catch (_error) {
      this.hostBrowserStatus = { connectors: [] };
    } finally {
      this.hostBrowserStatusLoading = false;
    }
  },

  hostBrowserConnectorLabel() {
    const connectors = Array.isArray(this.hostBrowserStatus?.connectors)
      ? this.hostBrowserStatus.connectors
      : [];
    const active = connectors.find((item) => item?.supported && item?.enabled);
    if (active) {
      const profile = active.profile_label ? ` - ${active.profile_label}` : "";
      return `${hostBrowserFamilyLabel(active.browser_family)}${profile}: ${hostBrowserStatusLabel(active.status)}`;
    }
    const preparable = connectors.find((item) => item?.can_prepare || item?.supported);
    if (preparable) return "A0 CLI connected - browser will open on first use";
    if (connectors.length) return "A0 CLI connected - host browser unavailable";
    return "Connect A0 CLI to use a host browser";
  },

  browserRuntimeStatusLabel() {
    if (this.config?.runtime_backend !== "host_required") {
      return "Docker browser runs inside Agent Zero; A0 CLI host-browser status does not affect it.";
    }
    const label = this.hostBrowserConnectorLabel();
    if (label.startsWith("Connect A0 CLI") || label.includes("unavailable")) {
      return `${label}. Switch Browser location to Internal Docker browser to browse without A0 CLI.`;
    }
    return label;
  },

  hasPaths() {
    return this.pathCount() > 0;
  },

  pathCount() {
    return normalizePathList(this.config?.extension_paths).length;
  },

  pathCountLabel() {
    const count = this.pathCount();
    if (!count) return "No extensions enabled";
    return `${count} extension${count === 1 ? "" : "s"} enabled`;
  },

  extensionModeReady() {
    return this.pathCount() > 0;
  },

  async loadExtensionsList() {
    if (this.extensionsLoading) return;
    this.extensionsLoading = true;
    this.extensionsError = "";
    try {
      const response = await callJsonApi(BROWSER_EXTENSIONS_API, { action: "list" });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not load browser extensions.");
      }
      this.applyExtensionPayload(response);
    } catch (error) {
      this.extensionsList = [];
      this.extensionsError = error instanceof Error ? error.message : String(error);
    } finally {
      this.extensionsLoading = false;
    }
  },

  applyExtensionPayload(response = {}) {
    this.extensionsList = Array.isArray(response.extensions) ? response.extensions : [];
    if (Array.isArray(response.extension_paths) && this.config) {
      this.config.extension_paths = normalizePathList(response.extension_paths);
    }
  },

  extensionEnabled(extension) {
    const path = typeof extension === "string" ? extension : extension?.path;
    return normalizePathList(this.config?.extension_paths).includes(String(path || ""));
  },

  setExtensionEnabled(extension, enabled) {
    const path = String((typeof extension === "string" ? extension : extension?.path) || "").trim();
    if (!path) return;
    const safeConfig = ensureConfig(this.config);
    if (!safeConfig) return;
    const paths = normalizePathList(safeConfig.extension_paths);
    if (enabled && !paths.includes(path)) {
      paths.push(path);
    } else if (!enabled) {
      const index = paths.indexOf(path);
      if (index >= 0) paths.splice(index, 1);
    }
    safeConfig.extension_paths = paths;
  },

  extensionCanDelete(extension) {
    return Boolean(extension?.can_delete);
  },

  extensionDeleteTitle(extension) {
    return this.extensionCanDelete(extension)
      ? "Delete extension"
      : "Only Browser-managed extensions can be deleted";
  },

  async deleteExtension(extension) {
    const path = String(extension?.path || "").trim();
    if (!path) return;
    this.extensionsError = "";
    this.extensionsMessage = "";
    if (!this.extensionCanDelete(extension)) {
      this.extensionsError = "Only Browser-managed extensions can be deleted.";
      return;
    }
    const name = String(extension?.name || "this extension").trim();
    if (globalThis.confirm && !globalThis.confirm(`Delete ${name}? This removes the extension folder from Browser.`)) {
      return;
    }

    this.extensionDeleteLoadingPath = path;
    try {
      const response = await callJsonApi(BROWSER_EXTENSIONS_API, {
        action: "uninstall_extension",
        path,
      });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not delete extension.");
      }
      this.applyExtensionPayload(response);
      this.extensionsMessage = `Deleted ${response.name || name}.`;
    } catch (error) {
      this.extensionsError = error instanceof Error ? error.message : String(error);
    } finally {
      this.extensionDeleteLoadingPath = "";
    }
  },

  extensionVersionLabel(extension) {
    const version = String(extension?.version || "").trim();
    return version ? `v${version}` : "Unpacked extension";
  },
});
