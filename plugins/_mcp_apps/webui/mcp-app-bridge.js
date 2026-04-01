/**
 * MCP App Bridge — PostMessage JSON-RPC bridge between sandboxed iframes and the host.
 *
 * Implements the host side of the MCP Apps communication protocol (SEP-1865).
 * Handles ui/initialize, tools/call, resources/read, notifications/message,
 * and sends tool-input/tool-result notifications to the iframe.
 */

const PROTOCOL_VERSION = "2025-06-18";

export class McpAppBridge {
  /**
   * @param {HTMLIFrameElement} iframe - The sandbox iframe element
   * @param {object} options
   * @param {string} options.appId - Unique app instance ID
   * @param {string} options.serverName - MCP server name
   * @param {string} options.toolName - Tool name (without server prefix)
   * @param {object} options.toolArgs - Tool call arguments
   * @param {object|null} options.toolResult - Tool call result
   * @param {object} options.uiMeta - UI metadata from tool definition
   * @param {Function} options.onMessage - Callback for ui/message requests
   * @param {Function} options.onSizeChanged - Callback for size change notifications
   * @param {Function} options.onTeardownRequest - Callback for teardown request
   * @param {Function} options.wsEmit - WebSocket emit function for proxying
   */
  constructor(iframe, options) {
    this.iframe = iframe;
    this.appId = options.appId;
    this.serverName = options.serverName;
    this.toolName = options.toolName;
    this.toolArgs = options.toolArgs || {};
    this.toolResult = options.toolResult || null;
    this.toolDescription = options.toolDescription || "";
    this.toolInputSchema = options.toolInputSchema || { type: "object" };
    this.uiMeta = options.uiMeta || {};
    this.onMessage = options.onMessage || (() => {});
    this.onSizeChanged = options.onSizeChanged || (() => {});
    this.onTeardownRequest = options.onTeardownRequest || (() => {});
    this.wsRequest = options.wsRequest;

    this._initialized = false;
    this._pendingRequests = new Map();
    this._requestDebounce = new Map();
    this._nextHostId = 1;
    this._messageHandler = this._handleMessage.bind(this);

    window.addEventListener("message", this._messageHandler);
  }

  destroy() {
    window.removeEventListener("message", this._messageHandler);
    this._pendingRequests.clear();
    for (const entry of this._requestDebounce.values()) clearTimeout(entry.timer);
    this._requestDebounce.clear();
  }

  /**
   * Send a JSON-RPC notification to the iframe.
   */
  _sendNotification(method, params) {
    if (!this.iframe?.contentWindow) return;
    this.iframe.contentWindow.postMessage(
      { jsonrpc: "2.0", method, params },
      "*"
    );
  }

  /**
   * Send a JSON-RPC response to the iframe.
   */
  _sendResponse(id, result) {
    if (!this.iframe?.contentWindow) return;
    this.iframe.contentWindow.postMessage(
      { jsonrpc: "2.0", id, result },
      "*"
    );
  }

  /**
   * Send a JSON-RPC error response to the iframe.
   */
  _sendError(id, code, message) {
    if (!this.iframe?.contentWindow) return;
    this.iframe.contentWindow.postMessage(
      { jsonrpc: "2.0", id, error: { code, message } },
      "*"
    );
  }

  /**
   * Send tool input notification after initialization.
   */
  _sendToolInput() {
    this._sendNotification("ui/notifications/tool-input", {
      arguments: this.toolArgs,
    });
  }

  /**
   * Send tool result notification.
   */
  _sendToolResult() {
    if (this.toolResult) {
      this._sendNotification("ui/notifications/tool-result", this.toolResult);
    }
  }

  /**
   * Handle incoming postMessage events from the iframe.
   */
  _handleMessage(event) {
    if (event.source !== this.iframe?.contentWindow) return;

    const data = event.data;
    if (!data || data.jsonrpc !== "2.0") return;

    // It's a request (has id and method)
    if (data.id !== undefined && data.method) {
      this._handleRequest(data);
      return;
    }

    // It's a notification (has method but no id)
    if (data.method && data.id === undefined) {
      this._handleNotification(data);
      return;
    }

    // It's a response to a host-initiated request (has id but no method)
    if (data.id !== undefined && !data.method) {
      const pending = this._pendingRequests.get(data.id);
      if (pending) {
        this._pendingRequests.delete(data.id);
        if (data.error) {
          pending.reject(new Error(data.error.message || "Unknown error"));
        } else {
          pending.resolve(data.result);
        }
      }
    }
  }

  /**
   * Handle JSON-RPC requests from the iframe.
   *
   * Uses a short debounce (per method) so that duplicate requests fired in
   * rapid succession (e.g. from the MCP Apps SDK re-connecting) are coalesced
   * into a single bridge operation (last-write-wins).
   */
  _handleRequest(msg) {
    const { method } = msg;

    const DEBOUNCE_METHODS = new Set([
      "ui/initialize", "tools/call", "resources/read",
    ]);

    if (DEBOUNCE_METHODS.has(method)) {
      const existing = this._requestDebounce.get(method);
      if (existing) {
        clearTimeout(existing.timer);
      }

      this._requestDebounce.set(method, {
        msg,
        timer: setTimeout(() => {
          this._requestDebounce.delete(method);
          this._dispatchRequest(msg);
        }, 15),
      });
      return;
    }

    this._dispatchRequest(msg);
  }

  /**
   * Dispatch a (possibly debounced) JSON-RPC request to its handler.
   */
  async _dispatchRequest(msg) {
    const { id, method, params } = msg;

    switch (method) {
      case "ui/initialize":
        this._handleInitialize(id, params);
        break;

      case "tools/call":
        await this._handleToolsCall(id, params);
        break;

      case "resources/read":
        await this._handleResourcesRead(id, params);
        break;

      case "ui/open-link":
        this._handleOpenLink(id, params);
        break;

      case "ui/message":
        this._handleUiMessage(id, params);
        break;

      case "ui/update-model-context":
        this._sendResponse(id, {});
        break;

      case "ui/request-display-mode":
        this._sendResponse(id, { mode: "inline" });
        break;

      case "ping":
        this._sendResponse(id, {});
        break;

      default:
        this._sendError(id, -32601, `Method not found: ${method}`);
    }
  }

  /**
   * Handle JSON-RPC notifications from the iframe.
   */
  _handleNotification(msg) {
    const { method, params } = msg;

    switch (method) {
      case "ui/notifications/initialized":
        if (!this._initialized) {
          this._initialized = true;
          this._sendToolInput();
          this._sendToolResult();
        }
        break;

      case "ui/notifications/size-changed":
        if (params) {
          this.onSizeChanged(params);
        }
        break;

      case "ui/notifications/request-teardown":
        this.onTeardownRequest();
        break;

      case "notifications/cancelled":
        // Advisory per MCP spec — acknowledged but no action needed.
        break;

      case "notifications/message":
        // Log message from app — just consume silently
        break;
    }
  }

  /**
   * Handle ui/initialize request.
   */
  _handleInitialize(id, params) {
    // Each ui/initialize starts a fresh session — reset so that
    // tool-input / tool-result are re-sent after the next initialized notification.
    this._initialized = false;

    const toolInfo = {
      tool: {
        name: this.toolName,
        description: this.toolDescription || "",
        inputSchema: this.toolInputSchema || { type: "object" },
      },
    };

    const hostCapabilities = {
      serverTools: { listChanged: false },
      serverResources: { listChanged: false },
      logging: {},
    };

    const hostContext = {
      toolInfo,
      theme: document.documentElement.classList.contains("dark") ? "dark" : "light",
      displayMode: "inline",
      availableDisplayModes: ["inline"],
      platform: "web",
    };

    this._sendResponse(id, {
      protocolVersion: PROTOCOL_VERSION,
      hostCapabilities,
      hostInfo: { name: "agent-zero", version: "1.0.0" },
      hostContext,
    });
  }

  /**
   * Proxy tools/call to the backend via WebSocket.
   */
  async _handleToolsCall(id, params) {
    if (!params?.name) {
      this._sendError(id, -32602, "Missing tool name");
      return;
    }

    try {
      const response = await this.wsRequest("mcp_app_tool_call", {
        app_id: this.appId,
        tool_name: params.name,
        arguments: params.arguments || {},
      });

      const first = response && Array.isArray(response.results) ? response.results[0] : null;
      const result = first?.data;

      if (result?.error) {
        this._sendError(id, result.error.code || -32000, result.error.message);
      } else {
        this._sendResponse(id, result || {});
      }
    } catch (e) {
      this._sendError(id, -32000, e.message || "Tool call failed");
    }
  }

  /**
   * Proxy resources/read to the backend via WebSocket.
   */
  async _handleResourcesRead(id, params) {
    if (!params?.uri) {
      this._sendError(id, -32602, "Missing resource URI");
      return;
    }

    try {
      const response = await this.wsRequest("mcp_app_resource_read", {
        app_id: this.appId,
        uri: params.uri,
      });

      const first = response && Array.isArray(response.results) ? response.results[0] : null;
      const result = first?.data;

      if (result?.error) {
        this._sendError(id, result.error.code || -32000, result.error.message);
      } else {
        this._sendResponse(id, result || {});
      }
    } catch (e) {
      this._sendError(id, -32000, e.message || "Resource read failed");
    }
  }

  /**
   * Handle ui/open-link — open URL in new tab.
   */
  _handleOpenLink(id, params) {
    if (params?.url) {
      window.open(params.url, "_blank", "noopener,noreferrer");
      this._sendResponse(id, {});
    } else {
      this._sendError(id, -32602, "Missing URL");
    }
  }

  /**
   * Handle ui/message — forward to host chat.
   */
  _handleUiMessage(id, params) {
    this.onMessage(params);
    this._sendResponse(id, {});
  }

  /**
   * Send host context change notification to the iframe.
   */
  sendHostContextChanged(context) {
    this._sendNotification("ui/notifications/host-context-changed", context);
  }

  /**
   * Initiate graceful teardown of the app.
   */
  async teardown(reason = "host") {
    const id = this._nextHostId++;
    return new Promise((resolve) => {
      this._pendingRequests.set(id, {
        resolve: () => resolve(true),
        reject: () => resolve(false),
      });
      if (this.iframe?.contentWindow) {
        this.iframe.contentWindow.postMessage(
          { jsonrpc: "2.0", id, method: "ui/resource-teardown", params: { reason } },
          "*"
        );
      }
      // Timeout: don't wait forever
      setTimeout(() => {
        if (this._pendingRequests.has(id)) {
          this._pendingRequests.delete(id);
          resolve(false);
        }
      }, 3000);
    });
  }
}
