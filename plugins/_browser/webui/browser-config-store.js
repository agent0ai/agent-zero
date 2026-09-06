import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { showConfirmDialog } from "/js/confirmDialog.js";
import { store as notifications } from "/components/notifications/notification-store.js";

const BROWSER_EXTENSIONS_API = "/plugins/_browser/extensions";
const BROWSER_SETUP_API = "/plugins/_browser/host_browser_setup";
const BROWSER_STATUS_API = "/plugins/_browser/status";
const BROWSER_BRIDGE_PAIRING_API = "/plugins/_a0_connector/browser_bridge_pairing";
const RUNTIME_BACKENDS = new Set(["container", "host_required"]);
const BROWSER_TAB_SCOPES = new Set(["per_context", "shared"]);
const HOST_PRIVACY_POLICIES = new Set(["enforce_local", "warn", "allow"]);
const HOST_PROFILE_MODES = new Set(["existing", "agent"]);
const DEFAULT_MAX_OPEN_TABS = 32;
const MIN_MAX_OPEN_TABS = 1;
const HARD_MAX_OPEN_TABS = 50;
const HOST_BROWSER_STATUS_REFRESH_MS = 1000;
const BROWSER_BRIDGE_PAIRING_REFRESH_MS = 3000;
const PAIRING_TTL_MS = 5 * 60 * 1000;
const PAIRING_DISPLAY_NAME_MAX_BYTES = 192;
const CUSTOM_HOST_BROWSER_SELECTION = "__custom_endpoint__";
const RESERVED_EXTENSION_SELECTION = /^extension(?:[^A-Za-z0-9._/-]*:|$)/i;
const RESERVED_DEVELOPMENT_SELECTION = /^development-extension(?:[^A-Za-z0-9._/-]*:|$)/i;
const BROWSER_BRIDGE_TRUST_CONTRACT = "a0.browser-bridge.trust.v1";
const PAIRING_CODE_PATTERN = /^A0B1-[0-9A-F]{8}-[0-9A-HJKMNP-TV-Z]{32}$/i;
const EXTENSION_ID_PATTERN = /^[a-p]{32}$/;
const INSTANCE_FINGERPRINT_PATTERN = /^sha256:[0-9a-f]{20}$/;
const PAIRING_STATES = new Set([
  "unpaired",
  "pairing_pending",
  "paired",
  "repair_required",
]);

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
  config.proxy_server = String(config.proxy_server || "").trim();
  config.proxy_bypass = String(config.proxy_bypass || "").trim();
  config.proxy_username = String(config.proxy_username || "");
  config.proxy_password = String(config.proxy_password || "");
  config.keyboard_layout = normalizeXkbToken(config.keyboard_layout);
  config.keyboard_variant = normalizeXkbToken(config.keyboard_variant);
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

function normalizeXkbToken(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, "")
    .slice(0, 32);
}

function normalizeRuntimeBackend(value) {
  const normalized = String(value || "").trim().toLowerCase().replace(/-/g, "_");
  if (normalized === "host_when_available") return "host_required";
  return RUNTIME_BACKENDS.has(normalized) ? normalized : "container";
}

function normalizeHostBrowserSelection(value) {
  const raw = String(value || "").trim();
  if (/^development-extension:[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?$/.test(raw)) return raw;
  if (RESERVED_DEVELOPMENT_SELECTION.test(raw)) return "development-extension:";
  if (/^extension:[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?$/.test(raw)) {
    return raw;
  }
  if (RESERVED_EXTENSION_SELECTION.test(raw)) {
    return "extension:";
  }
  if (raw.includes("://") || /^(?:\[[^\]]+\]|[^/:\s]+):\d+$/.test(raw)) {
    return raw.replace(/\s+/g, "").slice(0, 2048);
  }
  return raw.toLowerCase().replace(/\s+/g, "_").slice(0, 200);
}

function normalizeCustomHostBrowserEndpoint(value) {
  const raw = String(value || "").trim();
  if (!raw || RESERVED_EXTENSION_SELECTION.test(raw) || RESERVED_DEVELOPMENT_SELECTION.test(raw)) return "";
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

function stableHostBrowserSelection(value, status) {
  const selection = normalizeHostBrowserSelection(value);
  if (!selection) return "";
  const connectors = Array.isArray(status?.connectors) ? status.connectors : [];
  for (const connector of connectors) {
    const candidates = [
      ...(Array.isArray(connector?.available_browsers) ? connector.available_browsers : []),
      connector,
    ];
    for (const candidate of candidates) {
      const endpoint = normalizeCustomHostBrowserEndpoint(candidate?.cdp_endpoint);
      const browserId = normalizeHostBrowserSelection(candidate?.id || candidate?.browser_id);
      if (endpoint && endpoint === selection && browserId) return browserId;
    }
  }
  return selection;
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

function boundedPairingString(value, maximumBytes) {
  if (typeof value !== "string" || value !== value.trim() || !value) return "";
  if (/\p{C}/u.test(value)) return "";
  try {
    return new TextEncoder().encode(value).length <= maximumBytes ? value : "";
  } catch (_error) {
    return "";
  }
}

function normalizePairingStatus(value) {
  if (
    !value
    || typeof value !== "object"
    || value.contract !== BROWSER_BRIDGE_TRUST_CONTRACT
    || value.trust_version !== 1
    || !PAIRING_STATES.has(value.state)
    || value.pairing_code_present !== false
    || Object.prototype.hasOwnProperty.call(value, "pairing_code")
    || Object.prototype.hasOwnProperty.call(value, "public_key")
    || value.native_runtime_location !== "user_browser_host"
    || value.docker_install_target !== false
    || value.connector_session_ready !== false
    || value.browser_control_ready !== false
  ) {
    return null;
  }
  const pending = value.state === "pairing_pending";
  const pairingId = pending ? boundedPairingString(value.pairing_id, 512) : "";
  const expiresAtMs = pending && Number.isSafeInteger(value.expires_at_ms)
    ? value.expires_at_ms
    : 0;
  if (pending && (!pairingId || expiresAtMs <= 0)) return null;
  return {
    state: value.state,
    reasonCode: boundedPairingString(value.reason_code, 128) || "status_unavailable",
    pairingId,
    expiresAtMs,
    serverPairingEnabled: value.server_pairing_enabled === true,
  };
}

function normalizePairingCreation(value) {
  if (
    !value
    || typeof value !== "object"
    || value.contract !== BROWSER_BRIDGE_TRUST_CONTRACT
    || value.trust_version !== 1
    || value.state !== "pairing_pending"
  ) {
    return null;
  }
  const pairingId = boundedPairingString(value.pairing_id, 512);
  const pairingCode = typeof value.pairing_code === "string"
    && PAIRING_CODE_PATTERN.test(value.pairing_code)
    ? value.pairing_code.toUpperCase()
    : "";
  const createdAtMs = Number.isSafeInteger(value.created_at_ms) ? value.created_at_ms : 0;
  const expiresAtMs = Number.isSafeInteger(value.expires_at_ms) ? value.expires_at_ms : 0;
  const serverBaseUrl = boundedPairingString(value.server?.base_url, 2048);
  const instanceFingerprint = boundedPairingString(
    value.server?.instance_fingerprint,
    64,
  );
  const displayName = boundedPairingString(
    value.display_name,
    PAIRING_DISPLAY_NAME_MAX_BYTES,
  );
  if (
    !pairingId
    || !pairingCode
    || !serverBaseUrl
    || !INSTANCE_FINGERPRINT_PATTERN.test(instanceFingerprint)
    || !EXTENSION_ID_PATTERN.test(value.extension_id)
    || !displayName
    || createdAtMs <= 0
    || expiresAtMs - createdAtMs !== PAIRING_TTL_MS
    || value.expires_in_seconds !== PAIRING_TTL_MS / 1000
    || pairingId.replace(/-/g, "").slice(0, 8).toUpperCase() !== pairingCode.slice(5, 13)
    || value.native_runtime_location !== "user_browser_host"
    || value.docker_install_target !== false
    || value.connector_session_ready !== false
    || value.browser_control_ready !== false
  ) {
    return null;
  }
  return {
    pairingId,
    pairingCode,
    createdAtMs,
    expiresAtMs,
    serverBaseUrl,
    displayName,
  };
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
    safari: "Safari",
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
  hostBrowserSetupOpening: "",
  hostBrowserCustomEndpoint: "",
  hostBrowserCustomMode: false,
  pairingStatus: {
    state: "not_checked",
    reasonCode: "not_checked",
    pairingId: "",
    expiresAtMs: 0,
    serverPairingEnabled: false,
  },
  pairingStatusLoading: false,
  pairingActionLoading: false,
  pairingStatusRefreshTimer: null,
  pairingClockTimer: null,
  pairingPanelActive: false,
  pairingPanelGeneration: 0,
  pairingNowMs: Date.now(),
  pairingDisplayName: "My browser",
  pairingCode: "",
  pairingCodePairingId: "",
  pairingServerBaseUrl: "",
  pairingMessage: "",
  pairingError: "",

  async init(config) {
    // Alpine calls init on store registration before a settings panel owns a
    // config. Do not start a request that can strand a later mount's loading flag.
    if (!config || typeof config !== "object") return;
    this.pairingPanelGeneration += 1;
    this.pairingPanelActive = true;
    const generation = this.pairingPanelGeneration;
    this.bindConfig(config);
    await Promise.all([
      this.loadExtensionsList(),
      this.loadHostBrowserStatus(),
      this.loadBrowserBridgePairingStatus(),
    ]);
    if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
    this.startHostBrowserStatusRefresh();
    this.startBrowserBridgePairingRefresh();
  },

  cleanup() {
    this.pairingPanelActive = false;
    this.pairingPanelGeneration += 1;
    this.stopHostBrowserStatusRefresh();
    this.stopBrowserBridgePairingRefresh();
    this.clearPairingCode();
    this.config = null;
    this.extensionsList = [];
    this.extensionsError = "";
    this.extensionsMessage = "";
    this.extensionDeleteLoadingPath = "";
    this.hostBrowserStatus = null;
    this.hostBrowserStatusLoading = false;
    this.hostBrowserSetupOpening = "";
    this.hostBrowserCustomEndpoint = "";
    this.hostBrowserCustomMode = false;
    this.pairingStatus = {
      state: "not_checked",
      reasonCode: "not_checked",
      pairingId: "",
      expiresAtMs: 0,
      serverPairingEnabled: false,
    };
    this.pairingStatusLoading = false;
    this.pairingActionLoading = false;
    this.pairingDisplayName = "My browser";
    this.pairingMessage = "";
    this.pairingError = "";
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

  startBrowserBridgePairingRefresh() {
    this.stopBrowserBridgePairingRefresh();
    this.pairingClockTimer = window.setInterval(() => {
      this.tickPairingClock();
    }, 1000);
    this.pairingStatusRefreshTimer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      this.loadBrowserBridgePairingStatus();
      this.refreshProductionBrowserStatus(true);
    }, BROWSER_BRIDGE_PAIRING_REFRESH_MS);
  },

  async refreshProductionBrowserStatus(background = false) {
    if (!this.pairingPanelActive) return;
    await Promise.all([
      ...(!background ? [globalThis.Alpine?.store("browserBridgeSetup")?.refresh(), this.loadBrowserBridgePairingStatus()] : []),
      globalThis.Alpine?.store("browserBridgeAccess")?.refresh({ background }),
      globalThis.Alpine?.store("browserBridgeSelection")?.refresh(),
    ]);
  },

  stopBrowserBridgePairingRefresh() {
    if (this.pairingClockTimer) window.clearInterval(this.pairingClockTimer);
    if (this.pairingStatusRefreshTimer) window.clearInterval(this.pairingStatusRefreshTimer);
    this.pairingClockTimer = null;
    this.pairingStatusRefreshTimer = null;
  },

  tickPairingClock() {
    if (!this.pairingPanelActive) return;
    this.pairingNowMs = Date.now();
    if (
      this.pairingCode
      && this.pairingStatus.expiresAtMs > 0
      && this.pairingStatus.expiresAtMs <= this.pairingNowMs
    ) {
      this.clearPairingCode();
      this.pairingMessage = "";
      this.loadBrowserBridgePairingStatus();
    }
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
    const options = [{ value: "", label: "Automatic (first available)" }];
    const seen = new Set([""]);
    for (const connector of connectors) {
      const advertised = Array.isArray(connector?.available_browsers)
        ? connector.available_browsers
        : [];
      for (const browser of advertised) {
        const endpoint = normalizeCustomHostBrowserEndpoint(browser?.cdp_endpoint);
        const browserId = normalizeHostBrowserSelection(browser?.id || browser?.browser_id);
        const family = normalizeHostBrowserSelection(browser?.family || browser?.browser_family);
        const value = endpoint
          ? browserId || endpoint
          : family === "safari" ? browserId : "";
        if (!value || seen.has(value)) continue;
        seen.add(value);
        const label = browser?.label || hostBrowserFamilyLabel(browser?.family || value);
        const status = browser?.status ? ` - ${hostBrowserStatusLabel(browser.status)}` : "";
        options.push({ value, label: `${label}${status}` });
      }
      const fallbackEndpoint = normalizeCustomHostBrowserEndpoint(connector?.cdp_endpoint);
      const fallbackValue = fallbackEndpoint
        ? normalizeHostBrowserSelection(connector?.browser_id) || fallbackEndpoint
        : "";
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

  isDevelopmentBrowserSelected() {
    return this.config?.runtime_backend === "host_required"
      && String(this.config?.host_browser_selection || "").startsWith("development-extension:");
  },

  isProductionBrowserSelected() {
    return this.config?.runtime_backend === "host_required"
      && String(this.config?.host_browser_selection || "").startsWith("extension:");
  },

  isCompanionSelected() {
    return this.isProductionBrowserSelected() || this.isDevelopmentBrowserSelected();
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
      const safeConfig = ensureConfig(this.config);
      if (safeConfig) {
        const stable = stableHostBrowserSelection(
          safeConfig.host_browser_selection,
          this.hostBrowserStatus,
        );
        if (stable !== safeConfig.host_browser_selection) {
          safeConfig.host_browser_selection = stable;
          this.hostBrowserCustomEndpoint = "";
          this.hostBrowserCustomMode = false;
        }
      }
    } catch (_error) {
      this.hostBrowserStatus = { connectors: [] };
    } finally {
      this.hostBrowserStatusLoading = false;
    }
  },

  async loadBrowserBridgePairingStatus() {
    if (
      !this.pairingPanelActive
      || this.pairingStatusLoading
      || this.pairingActionLoading
    ) return;
    const generation = this.pairingPanelGeneration;
    this.pairingStatusLoading = true;
    try {
      const response = await callJsonApi(BROWSER_BRIDGE_PAIRING_API, {
        action: "status",
      });
      const status = normalizePairingStatus(response);
      if (!status) throw new Error("invalid pairing status");
      if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
      const codeStillCurrent = Boolean(
        this.pairingCode
        && this.pairingCodePairingId
        && this.pairingCodePairingId === status.pairingId
        && status.serverPairingEnabled
        && status.expiresAtMs > Date.now(),
      );
      if (!codeStillCurrent) this.clearPairingCode();
      this.pairingStatus = status;
      this.pairingNowMs = Date.now();
      this.pairingError = "";
    } catch (_error) {
      if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
      if (!this.pairingCodeAvailable()) {
        this.pairingStatus = {
          state: "not_checked",
          reasonCode: "status_unavailable",
          pairingId: "",
          expiresAtMs: 0,
          serverPairingEnabled: false,
        };
      }
      this.pairingNotice("error", "Pairing status could not be checked. No browser control was enabled.");
    } finally {
      if (generation === this.pairingPanelGeneration) {
        this.pairingStatusLoading = false;
      }
    }
  },

  pairingNotice(type, message) {
    const field = type === "error" ? "pairingError" : "pairingMessage";
    if (this[field] === message) return;
    this[field] = message;
    void notifications.frontendNotification({type, message, title: "Browser setup", frontendOnly: true}).catch(() => {});
  },

  pairingDisplayNameValid() {
    return Boolean(
      boundedPairingString(
        String(this.pairingDisplayName || "").trim(),
        PAIRING_DISPLAY_NAME_MAX_BYTES,
      ),
    );
  },

  canCreateBrowserBridgePairing() {
    return Boolean(
      this.pairingStatus.serverPairingEnabled
      && this.pairingDisplayNameValid()
      && this.pairingPanelActive
      && !this.pairingActionLoading,
    );
  },

  pairingPrimaryActionLabel() {
    if (this.pairingActionLoading) return "Working…";
    if (this.pairingStatus.state === "pairing_pending") return "Regenerate code";
    if (this.pairingStatus.state === "paired") return "Pair another host";
    return "Create pairing code";
  },

  async createBrowserBridgePairing() {
    this.pairingMessage = "";
    this.pairingError = "";
    if (!this.pairingDisplayNameValid()) {
      this.pairingNotice("error", "Enter a browser host name no longer than 192 bytes.");
      return;
    }
    if (!this.canCreateBrowserBridgePairing()) {
      this.pairingNotice("error", "Pairing is not enabled for this Agent Zero instance.");
      return;
    }
    const generation = this.pairingPanelGeneration;
    this.pairingActionLoading = true;
    this.clearPairingCode();
    try {
      const response = await callJsonApi(BROWSER_BRIDGE_PAIRING_API, {
        action: "create",
        display_name: String(this.pairingDisplayName).trim(),
      });
      const creation = normalizePairingCreation(response);
      if (
        !creation
        || creation.displayName !== String(this.pairingDisplayName).trim()
      ) throw new Error("invalid pairing creation response");
      if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
      this.pairingCode = creation.pairingCode;
      this.pairingCodePairingId = creation.pairingId;
      this.pairingServerBaseUrl = creation.serverBaseUrl;
      this.pairingNowMs = Date.now();
      this.pairingStatus = {
        state: "pairing_pending",
        reasonCode: "pairing_intent_active",
        pairingId: creation.pairingId,
        expiresAtMs: creation.expiresAtMs,
        serverPairingEnabled: true,
      };
      this.pairingNotice("success", "A new single-use pairing code is ready.");
    } catch (_error) {
      if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
      this.pairingNotice("error", "A pairing code could not be created. No browser control was enabled.");
    } finally {
      if (generation === this.pairingPanelGeneration) {
        this.pairingActionLoading = false;
      }
    }
  },

  async cancelBrowserBridgePairing() {
    const pairingId = boundedPairingString(this.pairingStatus.pairingId, 512);
    if (!pairingId || this.pairingActionLoading) return;
    const generation = this.pairingPanelGeneration;
    this.pairingActionLoading = true;
    this.pairingMessage = "";
    this.pairingError = "";
    this.clearPairingCode();
    try {
      const response = await callJsonApi(BROWSER_BRIDGE_PAIRING_API, {
        action: "cancel",
        pairing_id: pairingId,
      });
      const status = normalizePairingStatus(response);
      if (!status) throw new Error("invalid pairing cancel response");
      if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
      this.pairingStatus = status;
      this.pairingNotice("success", response.canceled === true
        ? "The pairing code was canceled."
        : "No active pairing code remained.");
    } catch (_error) {
      if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
      this.pairingNotice("error", "The pairing code could not be canceled. Its status is unknown; do not reuse it.");
    } finally {
      if (generation === this.pairingPanelGeneration) {
        this.pairingActionLoading = false;
      }
    }
  },

  async copyBrowserBridgePairingCode() {
    const pairingCode = this.pairingCodeAvailable() ? this.pairingCode : "";
    if (!pairingCode) return;
    const generation = this.pairingPanelGeneration;
    this.pairingMessage = "";
    this.pairingError = "";
    try {
      if (!navigator.clipboard?.writeText) throw new Error("clipboard unavailable");
      await navigator.clipboard.writeText(pairingCode);
      if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
      this.pairingNotice("success", "Pairing code copied. Paste it only into the Agent Zero browser companion.");
    } catch (_error) {
      if (!this.pairingPanelActive || generation !== this.pairingPanelGeneration) return;
      this.pairingNotice("error", "The code could not be copied. Select it and copy it manually.");
    }
  },

  clearPairingCode() {
    this.pairingCode = "";
    this.pairingCodePairingId = "";
    this.pairingServerBaseUrl = "";
  },

  pairingCodeAvailable() {
    return Boolean(
      this.pairingCode
      && this.pairingCodePairingId
      && this.pairingCodePairingId === this.pairingStatus.pairingId
      && this.pairingStatus.expiresAtMs > Math.max(this.pairingNowMs, Date.now())
      && PAIRING_CODE_PATTERN.test(this.pairingCode),
    );
  },

  pairingExpiryLabel() {
    const remainingMs = this.pairingStatus.expiresAtMs - this.pairingNowMs;
    if (remainingMs <= 0) return "Expired — regenerate the code";
    const remainingSeconds = Math.ceil(remainingMs / 1000);
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = String(remainingSeconds % 60).padStart(2, "0");
    return `Expires in ${minutes}:${seconds}`;
  },

  pairingStatusLabel() {
    if (this.pairingStatusLoading && this.pairingStatus.state === "not_checked") {
      return "Checking server pairing availability…";
    }
    if (this.pairingStatus.state === "not_checked") {
      return "Pairing status has not been checked. No browser control is enabled.";
    }
    if (this.pairingStatus.state === "repair_required") {
      return "Pairing status needs repair. No browser control is enabled.";
    }
    if (this.pairingStatus.state === "paired") {
      return "Browser pairing is saved. You do not need a new code when Chrome or Agent Zero restarts.";
    }
    if (!this.pairingStatus.serverPairingEnabled && this.pairingStatus.state !== "paired") {
      if (this.pairingStatus.reasonCode === "expected_extension_id_not_configured") {
        return "Pairing is waiting for the server's pinned Chrome extension ID.";
      }
      return "Pairing is disabled for this Agent Zero instance.";
    }
    if (this.pairingStatus.state === "pairing_pending") {
      return this.pairingCodeAvailable()
        ? "Waiting for the browser companion to use this code."
        : "A pairing is already waiting in this WebUI session. Regenerate it to display a new code.";
    }
    return "No browser companion is paired.";
  },

  async openHostBrowserSetup(browserFamily) {
    if (this.hostBrowserSetupOpening) return;
    const family = String(browserFamily || "").trim().toLowerCase();
    if (!["chrome", "opera", "edge"].includes(family)) return;
    this.hostBrowserSetupOpening = family;
    try {
      await callJsonApi(BROWSER_SETUP_API, { browser_family: family });
      const label = family === "edge" ? "Edge" : `${family[0].toUpperCase()}${family.slice(1)}`;
      notifications.addFrontendToastOnly(
        "success",
        `${label} remote-debugging setup opened on the connected host.`,
        "",
        4,
      );
    } catch (error) {
      console.error("Failed to open host browser setup:", error);
      notifications.addFrontendToastOnly(
        "error",
        "Connect or update Launcher or A0 CLI, enable host Browser access, and try again.",
        "Could not open browser setup",
        7,
      );
    } finally {
      this.hostBrowserSetupOpening = "";
    }
  },

  hostBrowserSetupAvailable(browserFamily) {
    const family = String(browserFamily || "").trim().toLowerCase();
    const connectors = Array.isArray(this.hostBrowserStatus?.connectors)
      ? this.hostBrowserStatus.connectors
      : [];
    return connectors.some((connector) => {
      if (!Array.isArray(connector?.features) || !connector.features.includes("open_remote_debugging")) {
        return false;
      }
      const browsers = Array.isArray(connector?.available_browsers)
        ? connector.available_browsers
        : [];
      return browsers.some((browser) => {
        const available = String(browser?.family || browser?.browser_family || "")
          .trim()
          .toLowerCase()
          .replace(/-(?:a0|cdp)$/, "");
        return available === family || (family === "edge" && available === "edge-dev");
      });
    });
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
    if (preparable) return "Host connected - browser will open on first use";
    if (connectors.length) return "Host connected - host browser unavailable";
    return "Connect through Launcher or A0 CLI to use a host browser";
  },

  browserRuntimeStatusLabel() {
    if (this.config?.runtime_backend !== "host_required") {
      return "Docker browser runs inside Agent Zero; host-browser connection status does not affect it.";
    }
    if (this.isDevelopmentBrowserSelected()) {
      return "This development connection is retired. Pair and select the production Chrome extension in Browser settings.";
    }
    if (this.isProductionBrowserSelected()) {
      return "Chrome extension selected. Connection status is shown above; A0 CLI and remote debugging are not required.";
    }
    const label = this.hostBrowserConnectorLabel();
    if (label.startsWith("Connect through Launcher") || label.includes("unavailable")) {
      return `${label}. Switch Browser location to Internal Docker browser to browse without a host connection.`;
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
    const safeName = name.replace(/[&<>"']/g, (character) => `&#${character.charCodeAt(0)};`);
    const confirmed = await showConfirmDialog({
      title: "Delete extension",
      message: `Delete ${safeName}? This removes the extension folder from Browser.`,
      confirmText: "Delete",
      type: "danger",
    });
    if (!confirmed) return;

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
