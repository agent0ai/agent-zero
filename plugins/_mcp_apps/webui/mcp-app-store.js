/**
 * MCP Apps Alpine.js store — manages active app instances and their iframe bridges.
 */
import { createStore } from "/js/AlpineStore.js";
import { getNamespacedClient } from "/js/websocket.js";
import { McpAppBridge } from "/usr/plugins/mcp_apps/webui/mcp-app-bridge.js";

const stateSocket = getNamespacedClient("/ws");

export const store = createStore("mcpApps", {
  /** @type {Map<string, McpAppBridge>} */
  _bridges: new Map(),

  initialized: false,

  async init() {
    if (this.initialized) return;
    this.initialized = true;
  },

  /**
   * Initialize an app iframe with its bridge.
   * Called from the mcp_app message renderer when the DOM element is ready.
   *
   * @param {string} appId
   * @param {HTMLIFrameElement} sandboxIframe - The outer sandbox iframe
   * @param {object} appData - App data from the backend
   */
  async setupApp(appId, sandboxIframe, appData) {
    if (this._bridges.has(appId)) return;

    const bridge = new McpAppBridge(sandboxIframe, {
      appId: appData.app_id,
      serverName: appData.server_name,
      toolName: appData.tool_name,
      toolArgs: appData.tool_args || {},
      toolResult: appData.tool_result || null,
      toolDescription: appData.tool_description || "",
      toolInputSchema: appData.tool_input_schema || { type: "object" },
      uiMeta: appData.ui_meta || {},
      onMessage: (params) => {
        console.log("[mcp-apps] ui/message from app:", params);
      },
      onSizeChanged: (params) => {
        // Only auto-size height; width is controlled by the layout container.
        // Applying the app's reported width causes an infinite resize loop.
        // Add buffer (+24px) and hysteresis (ignore deltas ≤20px) to prevent
        // resize feedback loops between the app's ResizeObserver and the iframe.
        if (params.height != null) {
          const target = Math.min(params.height + 24, 800);
          const current = parseFloat(sandboxIframe.style.height) || 400;
          if (Math.abs(target - current) > 20) {
            sandboxIframe.style.height = `${target}px`;
          }
        }
      },
      onTeardownRequest: () => {
        this.teardownApp(appId);
      },
      wsRequest: (event, data) => stateSocket.request(event, data),
    });

    this._bridges.set(appId, bridge);

    // Wait for sandbox proxy ready, then send the HTML resource
    const onSandboxReady = (event) => {
      if (event.source !== sandboxIframe.contentWindow) return;
      const data = event.data;
      if (!data || data.method !== "ui/notifications/sandbox-proxy-ready") return;

      window.removeEventListener("message", onSandboxReady);

      sandboxIframe.contentWindow.postMessage({
        jsonrpc: "2.0",
        method: "ui/notifications/sandbox-resource-ready",
        params: {
          html: appData.html_content,
          csp: appData.ui_meta?.csp || null,
          permissions: appData.ui_meta?.permissions || null,
        },
      }, "*");
    };

    window.addEventListener("message", onSandboxReady);
  },

  /**
   * Fetch app data from the backend for a given app_id.
   * @param {string} appId
   * @returns {Promise<object|null>}
   */
  async fetchAppData(appId) {
    try {
      const response = await stateSocket.request("mcp_app_get_data", { app_id: appId });
      const first = response && Array.isArray(response.results) ? response.results[0] : null;
      if (!first || first.ok !== true || !first.data) {
        const errMsg = first?.data?.error || first?.error?.message || "No data returned";
        console.error("[mcp-apps] fetchAppData error:", errMsg);
        return { error: errMsg };
      }
      return first.data;
    } catch (e) {
      console.error("[mcp-apps] fetchAppData failed:", e);
      return null;
    }
  },

  /**
   * Tear down an app and clean up its bridge.
   * @param {string} appId
   */
  async teardownApp(appId) {
    const bridge = this._bridges.get(appId);
    if (bridge) {
      bridge.destroy();
      this._bridges.delete(appId);
    }

    try {
      await stateSocket.request("mcp_app_teardown", { app_id: appId });
    } catch (e) {
      console.warn("[mcp-apps] teardown notify failed:", e);
    }
  },

  /**
   * Check if an app bridge exists.
   * @param {string} appId
   * @returns {boolean}
   */
  hasApp(appId) {
    return this._bridges.has(appId);
  },
});
