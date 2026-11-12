import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { showConfirmDialog } from "/js/confirmDialog.js";
import { store as notifications } from "/components/notifications/notification-store.js";

const BRIDGES_API = "/plugins/_a0_connector/browser_bridge_bridges";
const POLICY_API = "/plugins/_a0_connector/browser_bridge_policy";
const BRIDGES_CONTRACT = "a0.browser-bridge.bridges.v1";
const POLICY_CONTRACT = "a0.browser-bridge.site-policy.v1";
const identifier = (value) => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/.test(value);
const text = (value, limit) => typeof value === "string" && value.length > 0
  && new TextEncoder().encode(value).length <= limit && !/\p{C}/u.test(value);

export function normalizeSiteOrigin(value) {
  if (typeof value !== "string") return "";
  const raw = value.trim();
  if (!raw || raw.length > 2048 || /[\s\\%?#*]/u.test(raw)) return "";
  try {
    const url = new URL(raw);
    if (!["https:", "http:"].includes(url.protocol) || !url.hostname || url.username || url.password
      || url.pathname !== "/" || url.search || url.hash || url.hostname.endsWith(".")) return "";
    return url.origin;
  } catch { return ""; }
}

function parseBridges(response) {
  if (response?.contract !== BRIDGES_CONTRACT || response.trust_version !== 1
    || response.browser_control_ready !== false || !Array.isArray(response.bridges)
    || response.bridges.length > 128) throw new Error("Invalid browser inventory");
  const bridges = response.bridges.map((bridge) => {
    if (!identifier(bridge?.bridge_id) || !text(bridge.display_name, 192)
      || !["active", "revoked"].includes(bridge.state) || !Number.isSafeInteger(bridge.key_generation)
      || bridge.key_generation < 1) throw new Error("Invalid browser entry");
    return { id: bridge.bridge_id, name: bridge.display_name, state: bridge.state };
  });
  if (new Set(bridges.map((bridge) => bridge.id)).size !== bridges.length) throw new Error("Duplicate browser entry");
  return bridges;
}

function parseGrants(response, bridgeId) {
  if (response?.contract !== POLICY_CONTRACT || response.policy_version !== 1
    || response.bridge_id !== bridgeId || !["ask_per_site", "allow_all_websites"].includes(response.site_mode)
    || response.operation_grants_enabled !== false || response.browser_control_ready !== false
    || !Array.isArray(response.grants) || response.grants.length > 256) throw new Error("Invalid site permissions");
  const grants = response.grants.map((grant) => {
    if (!identifier(grant?.grant_id) || !grant.origin || normalizeSiteOrigin(grant.origin) !== grant.origin) throw new Error("Invalid site permission");
    return { id: grant.grant_id, origin: grant.origin };
  });
  if (new Set(grants.map((grant) => grant.origin)).size !== grants.length) throw new Error("Duplicate site permission");
  return { grants, siteMode: response.site_mode };
}

export function createBridgeAccessModel({ api, confirm, notify }) {
  return {
    active: false, generation: 0, policySequence: 0,
    bridges: [], grants: [], selectedId: "", originDraft: "", siteMode: "ask_per_site",
    inventoryState: "not_checked", policyState: "not_checked",
    loading: false, busy: false,

    async mount() {
      this.cleanup();
      this.active = true;
      await this.refresh();
    },

    cleanup() {
      this.active = false;
      this.generation += 1;
      this.policySequence += 1;
      this.bridges = []; this.grants = []; this.selectedId = ""; this.originDraft = "";
      this.siteMode = "ask_per_site";
      this.inventoryState = "not_checked"; this.policyState = "not_checked";
      this.loading = false; this.busy = false;
    },

    current(generation, bridgeId = this.selectedId) {
      return this.active && this.generation === generation && this.selectedId === bridgeId;
    },

    selectedBridge() { return this.bridges.find((bridge) => bridge.id === this.selectedId) || null; },
    canManageSites() { return this.selectedBridge()?.state === "active" && !this.busy && !this.loading; },
    canAllowSite() { return this.canManageSites() && Boolean(normalizeSiteOrigin(this.originDraft)); },

    async refresh({ background = false } = {}) {
      if (!this.active || this.loading || (background && this.busy)) return;
      const generation = this.generation;
      this.loading = true;
      try {
        const bridges = parseBridges(await api(BRIDGES_API, { action: "list" }));
        if (!this.active || this.generation !== generation) return;
        const previous = this.selectedBridge();
        this.bridges = bridges;
        this.inventoryState = "loaded";
        const selection = bridges.find((bridge) => bridge.id === this.selectedId)
          || bridges.find((bridge) => bridge.state === "active") || bridges[0];
        // Quiet inventory checks must not erase a site address being typed or
        // race a user switching the browser whose permissions are on screen.
        if (!background || previous?.id !== selection?.id || previous?.state !== selection?.state
          || this.policyState !== "loaded") await this.selectBridge(selection?.id || "");
      } catch {
        if (!this.active || this.generation !== generation) return;
        this.inventoryState = "unavailable";
        this.bridges = []; this.grants = []; this.selectedId = "";
        this.policySequence += 1;
      } finally {
        if (this.generation === generation) this.loading = false;
      }
    },

    async selectBridge(bridgeId) {
      if (!this.active || (bridgeId && !this.bridges.some((bridge) => bridge.id === bridgeId))) return;
      this.selectedId = bridgeId;
      this.originDraft = "";
      this.grants = [];
      this.siteMode = "ask_per_site";
      const sequence = ++this.policySequence;
      this.policyState = "not_checked";
      if (this.selectedBridge()?.state !== "active") return;
      const generation = this.generation;
      this.policyState = "loading";
      try {
        const grants = parseGrants(await api(POLICY_API, { action: "list", bridge_id: bridgeId }), bridgeId);
        if (!this.current(generation, bridgeId) || sequence !== this.policySequence) return;
        this.grants = grants.grants;
        this.siteMode = grants.siteMode;
        this.policyState = "loaded";
      } catch {
        if (this.current(generation, bridgeId) && sequence === this.policySequence) this.policyState = "unavailable";
      }
    },

    async allowSite() {
      if (!this.canAllowSite()) return;
      await this.changeSite("allow", normalizeSiteOrigin(this.originDraft));
    },

    async setAllWebsites(enabled) {
      if (typeof enabled !== "boolean" || !this.canManageSites() || this.policyState !== "loaded") return;
      const generation = this.generation;
      const bridgeId = this.selectedId;
      const sequence = ++this.policySequence;
      this.busy = true;
      try {
        if (enabled) {
          const approved = await confirm({ title: "Allow all websites?", message: "Remember browsing access to all supported websites for this Chrome browser across chats. Purchases, submissions, sensitive input and uploads still require their separate approvals. You can turn this off here.", confirmText: "Allow all websites", type: "warning" });
          if (!approved || !this.current(generation, bridgeId)) return;
        }
        const result = parseGrants(await api(POLICY_API, { action: "set_mode", bridge_id: bridgeId,
          site_mode: enabled ? "allow_all_websites" : "ask_per_site" }), bridgeId);
        if (!this.current(generation, bridgeId) || sequence !== this.policySequence) return;
        if (result.siteMode !== (enabled ? "allow_all_websites" : "ask_per_site")) throw new Error("Unconfirmed site mode");
        this.grants = result.grants; this.siteMode = result.siteMode;
        notify("success", enabled ? "All websites allowed for this Chrome browser." : "All-websites access turned off. Individually saved sites remain allowed.");
      } catch {
        if (this.current(generation, bridgeId)) {
          this.policyState = "unavailable";
          notify("error", "Website access could not be confirmed. Check connection before changing it again.");
        }
      } finally {
        if (this.generation === generation) this.busy = false;
      }
    },

    async revokeSite(origin) {
      if (!this.canManageSites() || !this.grants.some((grant) => grant.origin === origin)) return;
      await this.changeSite("revoke", origin);
    },

    async changeSite(action, origin) {
      if (!this.canManageSites()) return;
      const generation = this.generation;
      const bridgeId = this.selectedId;
      const sequence = ++this.policySequence;
      this.busy = true;
      try {
        const grants = parseGrants(await api(POLICY_API, { action, bridge_id: bridgeId, origin }), bridgeId);
        if (!this.current(generation, bridgeId) || sequence !== this.policySequence) return;
        this.grants = grants.grants;
        this.siteMode = grants.siteMode;
        this.policyState = "loaded";
        if (action === "allow") this.originDraft = "";
        notify("success", action === "allow" ? "Site permission saved. Browser control is still gated separately." : "Site permission removed.");
      } catch {
        if (this.current(generation, bridgeId)) notify("error", "Site permission could not be updated. Refresh and try again.");
      } finally {
        if (this.generation === generation) this.busy = false;
      }
    },

    async revokeBridge() {
      if (!this.canManageSites()) return;
      const generation = this.generation;
      const bridgeId = this.selectedId;
      this.busy = true;
      try {
        const approved = await confirm({ title: "Revoke browser access?", message: "This browser must pair again before reconnecting. Revocation does not delete the key on your computer or close browser tabs.", confirmText: "Revoke access", type: "danger" });
        if (!approved || !this.current(generation, bridgeId)) return;
        const response = await api(BRIDGES_API, { action: "revoke", bridge_id: bridgeId });
        if (!this.current(generation, bridgeId)) return;
        if (response?.contract !== BRIDGES_CONTRACT || response.trust_version !== 1
          || response.revoked !== true || response.bridge?.bridge_id !== bridgeId || response.bridge.state !== "revoked") throw new Error("Invalid revocation");
        this.grants = []; this.policySequence += 1;
        notify("success", "Browser access revoked. Your tabs and the key on your computer were not deleted.");
        await this.refresh();
      } catch {
        if (this.current(generation, bridgeId)) notify("error", "Revocation could not be confirmed. Refresh browser access before trying again.");
      } finally {
        if (this.generation === generation) this.busy = false;
      }
    },
  };
}

export const store = createStore("browserBridgeAccess", createBridgeAccessModel({
  api: callJsonApi,
  confirm: showConfirmDialog,
  notify: (type, message) => {
    void notifications.frontendNotification({ type, message, title: "Browser access", frontendOnly: true }).catch(() => {});
  },
}));
