import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const BROWSER_EXTENSIONS_API = "/plugins/_browser/extensions";
const BROWSER_STATUS_API = "/plugins/_browser/status";
const RUNTIME_BACKENDS = new Set(["container", "host_required"]);
const HOST_PRIVACY_POLICIES = new Set(["enforce_local", "warn", "allow"]);
const HOST_PROFILE_MODES = new Set(["existing", "agent"]);

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
  config.model_preset = String(config.model_preset || "").trim();
  delete config.model;
  return config;
}

function normalizeChoice(value, allowed, fallback) {
  const normalized = String(value || "").trim().toLowerCase().replace(/-/g, "_");
  return allowed.has(normalized) ? normalized : fallback;
}

function normalizeRuntimeBackend(value) {
  const normalized = String(value || "").trim().toLowerCase().replace(/-/g, "_");
  if (normalized === "host_when_available") return "host_required";
  return RUNTIME_BACKENDS.has(normalized) ? normalized : "container";
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

  async init(config) {
    this.bindConfig(config);
    await Promise.all([this.loadExtensionsList(), this.loadHostBrowserStatus()]);
  },

  cleanup() {
    this.config = null;
    this.extensionsList = [];
    this.extensionsError = "";
    this.extensionsMessage = "";
    this.extensionDeleteLoadingPath = "";
    this.hostBrowserStatus = null;
    this.hostBrowserStatusLoading = false;
  },

  bindConfig(config) {
    const safeConfig = ensureConfig(config);
    if (!safeConfig) return;
    if (this.config === safeConfig) return;
    this.config = safeConfig;
  },

  setAutofocusActivePage(enabled) {
    const safeConfig = ensureConfig(this.config);
    if (!safeConfig) return;
    safeConfig.autofocus_active_page = Boolean(enabled);
  },

  autofocusLabel() {
    return this.config?.autofocus_active_page === false ? "Off" : "On";
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
