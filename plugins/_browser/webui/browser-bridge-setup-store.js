import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const SETUP_API = "/plugins/_a0_connector/browser_bridge_setup";
const PLATFORMS = { macos: "macOS", windows: "Windows", linux: "Linux" };
const INSTALLER_ARCHES = { macos: ["universal2"], windows: ["x86_64", "arm64"], linux: ["any"] };

function browserHostPlatform(navigatorValue = globalThis.navigator) {
  const platform = navigatorValue?.userAgentData?.platform || navigatorValue?.platform || "";
  if (/mac/i.test(platform)) return "macos";
  if (/win/i.test(platform)) return "windows";
  if (/linux/i.test(platform) && !/android/i.test(navigatorValue?.userAgent || "")) return "linux";
  return "";
}

function canonicalHttps(value) {
  if (typeof value !== "string" || value.length > 4096 || /[\s\\]/.test(value)) return false;
  try {
    const url = new URL(value);
    return url.href === value && url.protocol === "https:" && Boolean(url.hostname)
      && !url.username && !url.password && !url.search && !url.hash;
  } catch { return false; }
}

function parseSetup(value) {
  const keys = ["contract", "setup_enabled", "browser_control_ready", "install_target",
    "host_verification_required", "extension_id", "extension_url", "companion_version", "installers"];
  if (!value || typeof value !== "object" || Array.isArray(value)
    || Object.keys(value).length !== keys.length || !keys.every(key => Object.hasOwn(value, key))
    || value.contract !== "a0.browser-bridge.setup.v1" || typeof value.setup_enabled !== "boolean"
    || value.browser_control_ready !== false || value.install_target !== "browser_host"
    || value.host_verification_required !== true || !Array.isArray(value.installers) || value.installers.length > 4
    || (value.setup_enabled ? !/^[a-p]{32}$/.test(value.extension_id || "")
      || value.extension_url !== `https://chromewebstore.google.com/detail/${value.extension_id}`
      : value.extension_id !== null || value.extension_url !== null || value.installers.length !== 0)
    || (value.companion_version !== null && !/^\d+\.\d+\.\d+$/.test(value.companion_version))) throw new Error("Invalid browser setup");
  const identities = new Set();
  for (const item of value.installers) {
    if (!item || typeof item !== "object" || Object.keys(item).sort().join() !== "arch,platform,url"
      || !INSTALLER_ARCHES[item.platform]?.includes(item.arch) || !canonicalHttps(item.url)
      || identities.has(`${item.platform}:${item.arch}`) || value.companion_version === null) throw new Error("Invalid browser installer");
    identities.add(`${item.platform}:${item.arch}`);
  }
  return value;
}

export function createBrowserSetupModel({ api, platform = browserHostPlatform() }) {
  return {
    active: false, generation: 0, loading: false, state: "not_checked", setup: null,
    platform: Object.hasOwn(PLATFORMS, platform) ? platform : "",
    async mount() { this.cleanup(); this.active = true; await this.refresh(); },
    cleanup() { this.active = false; this.generation += 1; this.loading = false; this.setup = null; this.state = "not_checked"; },
    async refresh() {
      if (!this.active || this.loading) return;
      const generation = this.generation; this.loading = true;
      try {
        const setup = parseSetup(await api(SETUP_API, {}));
        if (this.active && this.generation === generation) { this.setup = setup; this.state = "loaded"; }
      } catch {
        if (this.active && this.generation === generation) { this.setup = null; this.state = "unavailable"; }
      } finally { if (this.generation === generation) this.loading = false; }
    },
    installers() { return (this.setup?.installers || []).filter(item => item.platform === this.platform); },
    installerLabel(item) {
      const arch = { universal2: "Intel and Apple silicon", x86_64: "Intel / AMD", arm64: "ARM64", any: "all supported architectures" };
      return `${PLATFORMS[item.platform]} companion (${arch[item.arch]})`;
    },
    availabilityText() {
      if (this.state === "not_checked") return "Checking companion downloads…";
      if (this.state === "unavailable") return "Setup details could not be loaded. Check connection to retry.";
      if (!this.setup?.setup_enabled) return "Chrome setup has not been enabled on this Agent Zero server. Ask the person who manages it to finish browser setup.";
      if (!this.platform) return "Choose the operating system of the computer running Chrome, not the Docker server.";
      if (!this.installers().length) return `No ${PLATFORMS[this.platform]} companion download is configured for this release. Do not use another operating system's installer.`;
      return `Companion ${this.setup.companion_version}. Download and run it on this ${PLATFORMS[this.platform]} computer, outside Docker.`;
    },
  };
}

export const store = createStore("browserBridgeSetup", createBrowserSetupModel({ api: callJsonApi }));
