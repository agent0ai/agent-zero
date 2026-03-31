import { createStore } from "/js/AlpineStore.js";
import { getNamespacedClient } from "/js/websocket.js";

const stateSocket = getNamespacedClient("/ws");

export const store = createStore("sampling", {
  /** @type {Array<{request_id: string, server_name: string, messages: Array, system_prompt: string|null, max_tokens: number, temperature: number|null, model_preferences: object|null, stop_sequences: Array|null, include_context: string|null, status: string}>} */
  pending: [],

  initialized: false,

  async init() {
    if (this.initialized) return;
    this.initialized = true;

    await stateSocket.on("mcp_sampling_request", (envelope) => {
      const data = envelope?.data || envelope;
      this._handleRequest(data);
    });
  },

  _handleRequest(data) {
    if (!data || !data.request_id) return;

    const existing = this.pending.find((p) => p.request_id === data.request_id);
    if (existing) return;

    this.pending = [
      ...this.pending,
      {
        request_id: data.request_id,
        server_name: data.server_name || "",
        messages: data.messages || [],
        system_prompt: data.system_prompt || null,
        max_tokens: data.max_tokens || 0,
        temperature: data.temperature,
        model_preferences: data.model_preferences || null,
        stop_sequences: data.stop_sequences || null,
        include_context: data.include_context || null,
        status: "pending",
      },
    ];
  },

  async approve(requestId) {
    const item = this.pending.find((p) => p.request_id === requestId);
    if (!item) return;

    item.status = "approving";
    this.pending = [...this.pending];

    try {
      await stateSocket.emit("mcp_sampling_response", {
        request_id: requestId,
        action: "approve",
      });
      this.pending = this.pending.filter((p) => p.request_id !== requestId);
    } catch (error) {
      console.error("[sampling] approve failed:", error);
      item.status = "pending";
      this.pending = [...this.pending];
    }
  },

  async reject(requestId) {
    const item = this.pending.find((p) => p.request_id === requestId);
    if (!item) return;

    item.status = "rejecting";
    this.pending = [...this.pending];

    try {
      await stateSocket.emit("mcp_sampling_response", {
        request_id: requestId,
        action: "reject",
      });
      this.pending = this.pending.filter((p) => p.request_id !== requestId);
    } catch (error) {
      console.error("[sampling] reject failed:", error);
      item.status = "pending";
      this.pending = [...this.pending];
    }
  },

  hasPending() {
    return this.pending.length > 0;
  },
});
