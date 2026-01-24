import { createStore } from "/js/AlpineStore.js";
import { getNamespacedClient } from "/js/websocket.js";
import { invalidateCsrfToken } from "/js/api.js";
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
  return Boolean(globalThis.runtimeInfo?.isDevelopment);
}

function isSyncDebugEnabled() {
  try {
    let value = globalThis.localStorage?.getItem("a0_debug_sync");
    if (isDevelopmentRuntime()) {
      globalThis.localStorage?.setItem("a0_debug_sync", "true");
      value = "true";
    }
    return value === "true";
  } catch (_error) {
    return false;
  }
}

function debug(...args) {
  if (!isSyncDebugEnabled()) return;
  // eslint-disable-next-line no-console
  console.debug(...args);
}

function isRestartToastActive() {
  return (
    Array.isArray(notificationStore.toastStack) &&
    notificationStore.toastStack.some((toast) => toast && toast.group === "restart")
  );
}

const model = {
  mode: SYNC_MODES.DISCONNECTED,
  initialized: false,
  needsHandshake: false,
  handshakePromise: null,
  _handshakeQueued: false,
  _queuedPayload: null,
  _inFlightPayload: null,
  _seenFirstConnect: false,
  _lastConnectWasFirst: true,
  _pendingReconnectToast: null,
  _wasDegraded: false,
  _degradedToastShown: false,
  _degradedToastTimer: null,
  _degradedToastDelayMs: 100,
  _handshakeRetryTimer: null,
  _handshakeRetryAttempt: 0,
  _handshakeRetryBaseMs: 500,
  _handshakeRetryCapMs: 5000,
  _handshakeFailureCount: 0,
  _forceReconnectCooldownMs: 5000,
  _lastForceReconnectAtMs: 0,
  _forceReconnectThreshold: 3,
  _suppressDisconnectToastOnce: false,

  runtimeEpoch: null,
  seqBase: 0,
  lastSeq: 0,

  _setMode(newMode, reason = "") {
    const oldMode = this.mode;
    if (oldMode === newMode) return;
    this.mode = newMode;
    debug("[syncStore] Mode transition:", oldMode, "→", newMode, reason ? `(${reason})` : "");

    if (newMode !== SYNC_MODES.DEGRADED) {
      if (this._degradedToastTimer) {
        clearTimeout(this._degradedToastTimer);
        this._degradedToastTimer = null;
      }
    }

    if (newMode === SYNC_MODES.DISCONNECTED) {
      this._wasDegraded = false;
      this._degradedToastShown = false;
    }

    if (newMode === SYNC_MODES.DEGRADED) {
      this._wasDegraded = true;
      if (this._degradedToastShown || this._degradedToastTimer) {
        return;
      }
      this._degradedToastTimer = setTimeout(() => {
        this._degradedToastTimer = null;
        this._degradedToastShown = true;
        notificationStore
          .frontendWarning(
            "WebSocket connection problems - using polling fallback",
            "Connection",
            5,
            "sync-mode",
            undefined,
            true
          )
          .catch((error) => {
            console.error("[syncStore] degraded toast failed:", error);
          });
      }, this._degradedToastDelayMs);
      return;
    }

    if (newMode === SYNC_MODES.HEALTHY) {
      if (this._degradedToastShown) {
        notificationStore
          .frontendSuccess(
            "WebSocket connection restored",
            "Connection",
            4,
            "sync-mode",
            undefined,
            true
          )
          .catch((error) => {
            console.error("[syncStore] recovery toast failed:", error);
          });
      }
      this._wasDegraded = false;
      this._degradedToastShown = false;
    }
  },

  _clearHandshakeRetry() {
    if (this._handshakeRetryTimer) {
      clearTimeout(this._handshakeRetryTimer);
      this._handshakeRetryTimer = null;
    }
  },

  _scheduleHandshakeRetry(reason, forceReconnect = false) {
    if (this._handshakeRetryTimer) return;
    if (!this.needsHandshake) return;
    if (!stateSocket.isConnected()) return;

    const attempt = Math.max(0, Number(this._handshakeRetryAttempt) || 0);
    const delayMs = Math.min(this._handshakeRetryCapMs, this._handshakeRetryBaseMs * 2 ** attempt);
    this._handshakeRetryAttempt = attempt + 1;

    debug("[syncStore] scheduling handshake retry", {
      reason,
      attempt,
      delayMs,
      forceReconnect,
    });
    this._handshakeRetryTimer = setTimeout(() => {
      this._handshakeRetryTimer = null;
      if (!stateSocket.isConnected()) return;
      if (!this.needsHandshake) return;
      if (forceReconnect) {
        this._forceReconnect(reason);
        return;
      }
      this.sendStateRequest({ forceFull: true }).catch((error) => {
        console.error("[syncStore] handshake retry failed:", error);
      });
    }, delayMs);
  },

  _handleHandshakeFailure(reason) {
    this._handshakeFailureCount += 1;
    debug("[syncStore] handshake failure tracked", {
      reason,
      count: this._handshakeFailureCount,
      threshold: this._forceReconnectThreshold,
    });
    if (this._handshakeFailureCount < this._forceReconnectThreshold) {
      this._scheduleHandshakeRetry(reason, false);
      return;
    }
    this._handshakeFailureCount = 0;
    this._scheduleHandshakeRetry(reason, true);
  },

  _forceReconnect(reason) {
    const now = Date.now();
    if (now - this._lastForceReconnectAtMs < this._forceReconnectCooldownMs) {
      return;
    }
    this._lastForceReconnectAtMs = now;
    this._suppressDisconnectToastOnce = true;
    debug("[syncStore] forcing socket reconnect", { reason });
    try {
      invalidateCsrfToken();
    } catch (_error) {
      // no-op
    }
    try {
      stateSocket.disconnect();
    } catch (error) {
      console.error("[syncStore] forced disconnect failed:", error);
    }
    this.needsHandshake = true;
    this._clearHandshakeRetry();
    this._handshakeRetryAttempt = 0;
    stateSocket.connect().catch((error) => {
      console.error("[syncStore] forced reconnect failed:", error);
    });
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
        this._lastConnectWasFirst = firstConnect;
        if (firstConnect) {
          this._seenFirstConnect = true;
        } else if (this._seenFirstConnect) {
          const runtimeChanged = Boolean(info && info.runtimeChanged);
          this._pendingReconnectToast = runtimeChanged ? "restart" : "reconnect";
        }
        this._clearHandshakeRetry();
        this._handshakeRetryAttempt = 0;

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
        const restartToastActive = isRestartToastActive();
        this._setMode(
          SYNC_MODES.DISCONNECTED,
          restartToastActive ? "ws disconnect (restart toast active)" : "ws disconnect",
        );
        this.needsHandshake = true;
        this._clearHandshakeRetry();
        debug("[syncStore] websocket disconnected");

        // Tab-local UX: brief "Disconnected" toast. This intentionally does not go through
        // the backend notification pipeline (no cross-tab intent, avoids request storms).
        // Uses the same group as "Reconnected" so the reconnect toast replaces it if still visible.
        const suppressToast = this._suppressDisconnectToastOnce;
        this._suppressDisconnectToastOnce = false;
        if (this._seenFirstConnect && !restartToastActive && !suppressToast) {
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

      await stateSocket.on("server_restart", (envelope) => {
        // Avoid showing restart toast on the initial connect; prefer reconnect flows.
        if (this._lastConnectWasFirst) return;
        const runtimeId = envelope?.data?.runtimeId || null;
        debug("[syncStore] server_restart received", { runtimeId });
        this._pendingReconnectToast = "restart";
      });
      debug("[syncStore] subscribed to server_restart");

      await this.sendStateRequest({ forceFull: true });
    } catch (error) {
      console.error("[syncStore] init failed:", error);
      // Initialization failures often mean the socket can't connect; treat as disconnected.
      this._setMode(SYNC_MODES.DISCONNECTED, "init failed");
    }
  },

  async sendStateRequest(options = {}) {
    const { forceFull = false } = options || {};
    const payload = buildStateRequestPayload({ forceFull });
    return await this._sendStateRequestPayload(payload);
  },

  async _sendStateRequestPayload(payload) {
    if (this.handshakePromise) {
      const inFlight = this._inFlightPayload;
      if (
        inFlight &&
        payload &&
        payload.context === inFlight.context &&
        typeof payload.log_from === "number" &&
        typeof payload.notifications_from === "number" &&
        typeof inFlight.log_from === "number" &&
        typeof inFlight.notifications_from === "number"
      ) {
        const stronger =
          payload.log_from <= inFlight.log_from &&
          payload.notifications_from <= inFlight.notifications_from &&
          (payload.log_from < inFlight.log_from ||
            payload.notifications_from < inFlight.notifications_from);
        if (!stronger) {
          debug("[syncStore] state_request ignored (in-flight stronger/equal)", payload);
          return await this.handshakePromise;
        }
      }

      // Coalesce repeated requests while a handshake is in-flight. This is important
      // for fast context switching and resync flows where multiple requests can happen
      // back-to-back with different contexts/offsets.
      this._handshakeQueued = true;
      const queued = this._queuedPayload;
      if (!queued || !payload || payload.context !== queued.context) {
        this._queuedPayload = payload;
      } else if (
        typeof payload.log_from === "number" &&
        typeof payload.notifications_from === "number" &&
        typeof queued.log_from === "number" &&
        typeof queued.notifications_from === "number"
      ) {
        // Keep the "strongest" request: smaller offsets (0) mean a more complete resync.
        const queuedStrongerOrEqual =
          queued.log_from <= payload.log_from && queued.notifications_from <= payload.notifications_from;
        if (!queuedStrongerOrEqual) {
          this._queuedPayload = payload;
        }
      }
      debug("[syncStore] state_request coalesced (handshake in-flight)", payload);
      return await this.handshakePromise;
    }

    this._inFlightPayload = payload;
    this.handshakePromise = (async () => {
      this._setMode(SYNC_MODES.HANDSHAKE_PENDING, "sendStateRequest");

      let response;
      try {
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
        this._handleHandshakeFailure("state_request failed");
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
        this._handleHandshakeFailure(`handshake failed: ${code}`);
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
      this._handshakeFailureCount = 0;
      this._clearHandshakeRetry();
      this._handshakeRetryAttempt = 0;
      this._setMode(SYNC_MODES.HEALTHY, "handshake ok");
    })().finally(() => {
      this.handshakePromise = null;
      this._inFlightPayload = null;

      if (this._handshakeQueued) {
        const queuedPayload = this._queuedPayload;
        this._handshakeQueued = false;
        this._queuedPayload = null;
        if (queuedPayload) {
          debug("[syncStore] sending queued state_request", queuedPayload);
          Promise.resolve().then(() => {
            this._sendStateRequestPayload(queuedPayload).catch((error) => {
              console.error("[syncStore] queued state_request failed:", error);
            });
          });
        }
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
