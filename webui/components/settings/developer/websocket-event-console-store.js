import { createStore } from "/js/AlpineStore.js";
import { websocket } from "/js/websocket.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

const DIAGNOSTIC_EVENT = "ws_dev_console_event";
const SUBSCRIBE_EVENT = "ws_event_console_subscribe";
const UNSUBSCRIBE_EVENT = "ws_event_console_unsubscribe";
const MAX_ENTRIES = 200;
const CAPTURE_ENABLED_KEY = "a0.websocket_event_console.capture_enabled";

const model = {
  entries: [],
  isEnabled: false,
  captureEnabled: false,
  subscriptionActive: false,
  showHandledOnly: false,
  lastError: null,
  _consoleCallback: null,
  _lifecycleBound: false,
  _entrySeq: 0,

  init() {
    const rootStore = window.Alpine?.store ? window.Alpine.store("root") : undefined;
    this.isEnabled = Boolean(window.runtimeInfo?.isDevelopment || rootStore?.isDevelopment);
    if (!this.isEnabled) {
      this.captureEnabled = false;
      return;
    }

    this._bindLifecycle();
    this.captureEnabled = this._loadCaptureEnabled();
    if (this.captureEnabled) {
      this.attach({ notify: false }).catch(() => {});
    }
  },

  _bindLifecycle() {
    if (this._lifecycleBound) return;
    this._lifecycleBound = true;

    websocket.onDisconnect(() => {
      // Watcher subscriptions are per-sid and cleared server-side on disconnect.
      this.subscriptionActive = false;
    });

    websocket.onConnect(() => {
      if (!this.captureEnabled) return;
      // Re-subscribe after reconnect (server watcher set is per-sid).
      this._subscribe({ notify: false }).catch(() => {});
    });
  },

  _loadCaptureEnabled() {
    try {
      const raw = window.localStorage?.getItem(CAPTURE_ENABLED_KEY);
      return raw === "1" || raw === "true";
    } catch (error) {
      return false;
    }
  },

  _persistCaptureEnabled(enabled) {
    try {
      window.localStorage?.setItem(CAPTURE_ENABLED_KEY, enabled ? "1" : "0");
    } catch (error) {
      // Ignore storage failures (private mode, etc).
    }
  },

  async startCapture() {
    await this.setCaptureEnabled(true, { notify: true });
  },

  async stopCapture() {
    await this.setCaptureEnabled(false, { notify: true });
  },

  async setCaptureEnabled(enabled, { notify = true } = {}) {
    if (!this.isEnabled) return;

    const desired = Boolean(enabled);
    if (this.captureEnabled === desired) {
      if (desired) {
        await this.attach({ notify: false });
      }
      return;
    }

    this.captureEnabled = desired;
    this._persistCaptureEnabled(desired);

    if (desired) {
      await this.attach({ notify });
      return;
    }

    await this.detach({ notify });
  },

  async _subscribe({ notify = true } = {}) {
    if (!this.isEnabled) return;
    if (this.subscriptionActive) return;

    try {
      await websocket.request(SUBSCRIBE_EVENT, {
        requestedAt: new Date().toISOString(),
      });
      this.subscriptionActive = true;
      this.lastError = null;

      if (notify) {
        notificationStore.frontendInfo(
          "WebSocket diagnostics capture enabled",
          "Event Console",
          4,
        );
      }
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  },

  async attach({ notify = true } = {}) {
    if (!this.isEnabled) return;
    if (this.subscriptionActive && this._consoleCallback) return;

    try {
      await websocket.connect();

      if (!this._consoleCallback) {
        this._consoleCallback = (envelope) => {
          try {
            this.addEntry(envelope);
          } catch (error) {
            this.handleError(error);
          }
        };

        await websocket.on(DIAGNOSTIC_EVENT, this._consoleCallback);
      }

      await this._subscribe({ notify });
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  },

  async detach({ notify = false } = {}) {
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

    if (notify) {
      notificationStore.frontendInfo(
        "WebSocket diagnostics capture disabled",
        "Event Console",
        3,
      );
    }
  },

  async reconnect() {
    if (!this.isEnabled) return;
    if (!this.captureEnabled) {
      await this.startCapture();
      return;
    }

    await this.detach({ notify: false });
    await this.attach({ notify: true });
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
      eventId: envelope?.eventId || null,
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
    if (!entry.eventId) {
      this._entrySeq += 1;
      entry.eventId = `evt_${this._entrySeq}`;
    }
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
