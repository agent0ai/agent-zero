import { createStore } from "/js/AlpineStore.js";
import { getNamespacedClient } from "/js/websocket.js";

const stateSocket = getNamespacedClient("/ws");

export const store = createStore("elicitation", {
  /** @type {Array<{request_id: string, message: string, requested_schema: object, server_name: string, formData: object, status: string}>} */
  pending: [],

  initialized: false,

  async init() {
    if (this.initialized) return;
    this.initialized = true;

    await stateSocket.on("mcp_elicitation_request", (envelope) => {
      const data = envelope?.data || envelope;
      this._handleRequest(data);
    });
  },

  _handleRequest(data) {
    if (!data || !data.request_id) return;

    const existing = this.pending.find((p) => p.request_id === data.request_id);
    if (existing) return;

    const formData = this._buildDefaultFormData(data.requested_schema);

    this.pending = [
      ...this.pending,
      {
        request_id: data.request_id,
        message: data.message || "",
        requested_schema: data.requested_schema || {},
        server_name: data.server_name || "",
        formData,
        status: "pending",
      },
    ];
  },

  _buildDefaultFormData(schema) {
    const formData = {};
    if (!schema || !schema.properties) return formData;

    for (const [key, prop] of Object.entries(schema.properties)) {
      if (prop.default !== undefined) {
        formData[key] = prop.default;
      } else if (prop.type === "boolean") {
        formData[key] = false;
      } else if (prop.type === "number" || prop.type === "integer") {
        formData[key] = prop.minimum ?? 0;
      } else {
        formData[key] = "";
      }
    }
    return formData;
  },

  getFields(schema) {
    if (!schema || !schema.properties) return [];
    const required = new Set(schema.required || []);
    return Object.entries(schema.properties).map(([key, prop]) => ({
      key,
      label: prop.title || key,
      description: prop.description || "",
      type: prop.type || "string",
      required: required.has(key),
      enum: prop.enum || null,
      minimum: prop.minimum,
      maximum: prop.maximum,
    }));
  },

  async submit(requestId) {
    const item = this.pending.find((p) => p.request_id === requestId);
    if (!item) return;

    item.status = "submitting";
    this.pending = [...this.pending];

    try {
      await stateSocket.emit("mcp_elicitation_response", {
        request_id: requestId,
        action: "accept",
        content: { ...item.formData },
      });
      this.pending = this.pending.filter((p) => p.request_id !== requestId);
    } catch (error) {
      console.error("[elicitation] submit failed:", error);
      item.status = "pending";
      this.pending = [...this.pending];
    }
  },

  async decline(requestId) {
    const item = this.pending.find((p) => p.request_id === requestId);
    if (!item) return;

    item.status = "declining";
    this.pending = [...this.pending];

    try {
      await stateSocket.emit("mcp_elicitation_response", {
        request_id: requestId,
        action: "decline",
        content: null,
      });
      this.pending = this.pending.filter((p) => p.request_id !== requestId);
    } catch (error) {
      console.error("[elicitation] decline failed:", error);
      item.status = "pending";
      this.pending = [...this.pending];
    }
  },

  async cancel(requestId) {
    const item = this.pending.find((p) => p.request_id === requestId);
    if (!item) return;

    item.status = "cancelling";
    this.pending = [...this.pending];

    try {
      await stateSocket.emit("mcp_elicitation_response", {
        request_id: requestId,
        action: "cancel",
        content: null,
      });
      this.pending = this.pending.filter((p) => p.request_id !== requestId);
    } catch (error) {
      console.error("[elicitation] cancel failed:", error);
      item.status = "pending";
      this.pending = [...this.pending];
    }
  },

  updateField(requestId, key, value) {
    const item = this.pending.find((p) => p.request_id === requestId);
    if (!item) return;
    item.formData = { ...item.formData, [key]: value };
    this.pending = [...this.pending];
  },

  hasPending() {
    return this.pending.length > 0;
  },
});
