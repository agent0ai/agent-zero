import { createStore } from "/js/AlpineStore.js";
import { websocket } from "/js/websocket.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

const DIAGNOSTIC_EVENT = "ws_dev_console_event";
const SUBSCRIBE_EVENT = "ws_event_console_subscribe";
const UNSUBSCRIBE_EVENT = "ws_event_console_unsubscribe";
const MAX_ENTRIES = 200;

const model = {
  entries: [],
  isEnabled: false,
  subscriptionActive: false,
  showHandledOnly: false,
  lastError: null,
  _consoleCallback: null,

  init() {
    const rootStore = window.Alpine?.store ? window.Alpine.store("root") : undefined;
    this.isEnabled = Boolean(window.runtimeInfo?.isDevelopment || rootStore?.isDevelopment);
  },

  async attach() {
    if (!this.isEnabled || this.subscriptionActive) return;
    try {
      await websocket.connect();
      await websocket.request(SUBSCRIBE_EVENT, {
        requestedAt: new Date().toISOString(),
      });
      this.subscriptionActive = true;
      this.lastError = null;

      this._consoleCallback = (envelope) => {
        try {
          this.addEntry(envelope);
        } catch (error) {
          this.handleError(error);
        }
      };

      await websocket.on(DIAGNOSTIC_EVENT, this._consoleCallback);
      notificationStore.frontendInfo(
        "Streaming WebSocket diagnostics",
        "Event Console",
        4,
      );
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  },

  async detach() {
    if (this._consoleCallback) {
      websocket.off(DIAGNOSTIC_EVENT, this._consoleCallback);
      this._consoleCallback = null;
    }
    if (this.subscriptionActive) {
      try {
        await websocket.request(UNSUBSCRIBE_EVENT, {});
      } catch (error) {
        this.handleError(error);
      }
    }
    this.subscriptionActive = false;
  },

  async reconnect() {
    await this.detach();
    await this.attach();
  },

  handleError(error) {
    const message = error?.message || String(error || "Unknown error");
    this.lastError = message;
    notificationStore.frontendError(message, "WebSocket Event Console", 6);
  },

  addEntry(envelope) {
    const payload = envelope?.data || {};
    const entry = {
      kind: payload.kind || "unknown",
      eventType: payload.eventType || payload.event || "unknown",
      sid: payload.sid || null,
      correlationId: payload.correlationId || envelope?.correlationId || null,
      timestamp: payload.timestamp || envelope?.ts || new Date().toISOString(),
      handlerId: payload.handlerId || envelope?.handlerId || "WebSocketManager",
      resultSummary: payload.resultSummary || {},
      payloadSummary: payload.payloadSummary || {},
      delivered: payload.delivered ?? null,
      buffered: payload.buffered ?? null,
      targets: Array.isArray(payload.targets) ? payload.targets : [],
      targetCount: payload.targetCount ?? null,
    };
    entry.hasHandlers =
      (entry.resultSummary?.handlerCount ?? entry.resultSummary?.ok ?? 0) > 0;

    this.entries.push(entry);
    if (this.entries.length > MAX_ENTRIES) {
      this.entries.shift();
    }
  },

  filteredEntries() {
    if (!this.showHandledOnly) {
      return this.entries;
    }
    return this.entries.filter(
      (entry) =>
        entry.kind !== "inbound" ||
        entry.hasHandlers ||
        entry.resultSummary?.error > 0,
    );
  },

  clear() {
    this.entries = [];
  },
};

const store = createStore("websocketEventConsoleStore", model);
export { store };
