import { createStore } from "/js/AlpineStore.js";
import { getNamespacedClient } from "/js/websocket.js";
import { applySnapshot, buildStateRequestPayload } from "/index.js";
import { store as chatTopStore } from "/components/chat/top-section/chat-top-store.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

const stateSocket = getNamespacedClient("/state_sync");

const SYNC_MODES = {
  DISCONNECTED: "DISCONNECTED",
  HANDSHAKE_PENDING: "HANDSHAKE_PENDING",
  HEALTHY: "HEALTHY",
  DEGRADED: "DEGRADED",
};

function isDevelopmentRuntime() {
  try {
    const rootStore =
      globalThis.Alpine && typeof globalThis.Alpine.store === "function"
        ? globalThis.Alpine.store("root")
        : null;
    return Boolean(globalThis.runtimeInfo?.isDevelopment || rootStore?.isDevelopment);
  } catch (_error) {
    return false;
  }
}

function isSyncDebugEnabled() {
  if (!isDevelopmentRuntime()) return false;
  try {
    return globalThis.localStorage?.getItem("a0_debug_sync") === "true";
  } catch (_error) {
    return false;
  }
}

function debug(...args) {
  if (!isSyncDebugEnabled()) return;
  // eslint-disable-next-line no-console
  console.debug(...args);
}

const model = {
  mode: SYNC_MODES.DISCONNECTED,
  initialized: false,
  needsHandshake: false,
  handshakePromise: null,
  _handshakeQueued: false,
  _queuedForceFull: false,
  _seenFirstConnect: false,
  _pendingReconnectToast: null,

  runtimeEpoch: null,
  seqBase: 0,
  lastSeq: 0,

  _setMode(newMode, reason = "") {
    const oldMode = this.mode;
    if (oldMode === newMode) return;
    this.mode = newMode;
    debug("[syncStore] Mode transition:", oldMode, "→", newMode, reason ? `(${reason})` : "");
  },

  async _flushPendingReconnectToast() {
    const pending = this._pendingReconnectToast;
    if (!pending) return;
    this._pendingReconnectToast = null;

    try {
      if (pending === "restart") {
        await notificationStore.frontendSuccess(
          "Restarted",
          "System Restart",
          5,
          "restart",
          undefined,
          true,
        );
        return;
      }
      await notificationStore.frontendSuccess(
        "Reconnected",
        "Connection",
        3,
        "reconnect",
        undefined,
        true,
      );
    } catch (error) {
      console.error("[syncStore] reconnect toast failed:", error);
    }
  },

  async init() {
    if (this.initialized) return;
    this.initialized = true;

    try {
      stateSocket.onConnect((info) => {
        chatTopStore.connected = true;
        debug("[syncStore] websocket connected", { needsHandshake: this.needsHandshake });

        const firstConnect = Boolean(info && info.firstConnect);
        if (firstConnect) {
          this._seenFirstConnect = true;
        } else if (this._seenFirstConnect) {
          const runtimeChanged = Boolean(info && info.runtimeChanged);
          this._pendingReconnectToast = runtimeChanged ? "restart" : "reconnect";
        }

        // Always re-handshake on every Socket.IO connect.
        //
        // The backend StateMonitor tracking is per-sid and starts with seq_base=0 on a
        // newly connected sid. If a tab misses the 'disconnect' event (e.g. browser
        // suspended overnight) it can look HEALTHY locally while never sending a
        // fresh state_request, so pushes are gated and logs appear to stall.
        this.sendStateRequest({ forceFull: true }).catch((error) => {
          console.error("[syncStore] connect handshake failed:", error);
        });
      });

      stateSocket.onDisconnect(() => {
        chatTopStore.connected = false;
        this._setMode(SYNC_MODES.DISCONNECTED, "ws disconnect");
        this.needsHandshake = true;
        debug("[syncStore] websocket disconnected");

        // Tab-local UX: brief "Disconnected" toast. This intentionally does not go through
        // the backend notification pipeline (no cross-tab intent, avoids request storms).
        // Uses the same group as "Reconnected" so the reconnect toast replaces it if still visible.
        if (this._seenFirstConnect) {
          notificationStore
            .frontendWarning("Disconnected", "Connection", 5, "reconnect", undefined, true)
            .catch((error) => {
              console.error("[syncStore] disconnected toast failed:", error);
            });
        }
      });

      await stateSocket.on("state_push", (envelope) => {
        this._handlePush(envelope).catch((error) => {
          console.error("[syncStore] state_push handler failed:", error);
        });
      });
      debug("[syncStore] subscribed to state_push");

      await this.sendStateRequest({ forceFull: true });
    } catch (error) {
      console.error("[syncStore] init failed:", error);
      // Initialization failures often mean the socket can't connect; treat as disconnected.
      this._setMode(SYNC_MODES.DISCONNECTED, "init failed");
    }
  },

  async sendStateRequest(options = {}) {
    const { forceFull = false } = options || {};
    if (this.handshakePromise) {
      // Coalesce repeated requests while a handshake is in-flight. This is important
      // for fast context switching and log-guid resync flows, where multiple
      // `sendStateRequest()` calls can happen back-to-back with different contexts.
      this._handshakeQueued = true;
      this._queuedForceFull = this._queuedForceFull || forceFull;
      debug("[syncStore] state_request coalesced (handshake in-flight)", { forceFull });
      return await this.handshakePromise;
    }
    this.handshakePromise = (async () => {
      this._setMode(SYNC_MODES.HANDSHAKE_PENDING, "sendStateRequest");

      let response;
      try {
        const payload = buildStateRequestPayload({ forceFull });
        debug("[syncStore] state_request sent", payload);
        response = await stateSocket.request("state_request", payload, { timeoutMs: 2000 });
      } catch (error) {
        this.needsHandshake = true;
        // If the socket isn't connected, we are disconnected (poll may or may not work).
        // If the socket is connected but the request failed/timed out, treat as degraded (poll fallback).
        this._setMode(
          stateSocket.isConnected() ? SYNC_MODES.DEGRADED : SYNC_MODES.DISCONNECTED,
          "state_request failed",
        );
        throw error;
      }

      const first = response && Array.isArray(response.results) ? response.results[0] : null;
      if (!first || first.ok !== true || !first.data) {
        const code =
          first && first.error && typeof first.error.code === "string"
            ? first.error.code
            : "HANDSHAKE_FAILED";
        this._setMode(SYNC_MODES.DEGRADED, `handshake failed: ${code}`);
        this.needsHandshake = true;
        throw new Error(`state_request failed: ${code}`);
      }

      const data = first.data;
      if (typeof data.runtime_epoch === "string") {
        this.runtimeEpoch = data.runtime_epoch;
      }
      if (typeof data.seq_base === "number" && Number.isFinite(data.seq_base)) {
        this.seqBase = data.seq_base;
        this.lastSeq = data.seq_base;
      }

      this.needsHandshake = false;
      this._setMode(SYNC_MODES.HEALTHY, "handshake ok");
    })().finally(() => {
      this.handshakePromise = null;
      if (this._handshakeQueued) {
        const queuedForceFull = this._queuedForceFull;
        this._handshakeQueued = false;
        this._queuedForceFull = false;
        debug("[syncStore] sending queued state_request", { forceFull: queuedForceFull });
        Promise.resolve().then(() => {
          this.sendStateRequest({ forceFull: queuedForceFull }).catch((error) => {
            console.error("[syncStore] queued state_request failed:", error);
          });
        });
      }
    });

    return await this.handshakePromise;
  },

  async _handlePush(envelope) {
    if (this.mode === SYNC_MODES.DEGRADED) {
      debug("[syncStore] ignoring state_push while DEGRADED");
      return;
    }

    const data = envelope && envelope.data ? envelope.data : null;
    if (!data || typeof data !== "object") return;

    if (typeof data.runtime_epoch === "string") {
      if (this.runtimeEpoch && this.runtimeEpoch !== data.runtime_epoch) {
        debug("[syncStore] runtime_epoch mismatch -> resync", {
          current: this.runtimeEpoch,
          incoming: data.runtime_epoch,
        });
        this._setMode(SYNC_MODES.HANDSHAKE_PENDING, "runtime_epoch mismatch");
        await this.sendStateRequest({ forceFull: true });
        return;
      }
      this.runtimeEpoch = data.runtime_epoch;
    }

    if (typeof data.seq === "number" && Number.isFinite(data.seq)) {
      const expected = this.lastSeq + 1;
      if (this.lastSeq > 0 && data.seq !== expected) {
        debug("[syncStore] seq gap/out-of-order -> resync", {
          lastSeq: this.lastSeq,
          expected,
          incoming: data.seq,
        });
        this._setMode(SYNC_MODES.HANDSHAKE_PENDING, "seq gap");
        await this.sendStateRequest({ forceFull: true });
        return;
      }
      this.lastSeq = data.seq;
    }

    if (data.snapshot && typeof data.snapshot === "object") {
      await applySnapshot(data.snapshot, {
        onLogGuidReset: async () => {
          debug("[syncStore] log_guid reset -> resync (forceFull)");
          await this.sendStateRequest({ forceFull: true });
        },
      });
      this._setMode(SYNC_MODES.HEALTHY, "push applied");
      await this._flushPendingReconnectToast();
    }
  },
};

const store = createStore("sync", model);

export { store, SYNC_MODES };
