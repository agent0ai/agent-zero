import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const POLL_INTERVAL_MS = 2000;

const model = {
  active: false,
  leftContextId: "",
  rightContextId: "",
  forkPoint: null, // log no where the fork happened

  leftMessages: [],
  rightMessages: [],
  leftForkInfo: null,
  rightForkInfo: null,

  loading: false,
  error: "",

  _initialized: false,
  _pollTimer: null,
  _leftLogVersion: 0,
  _rightLogVersion: 0,
  _leftLogGuid: "",
  _rightLogGuid: "",

  init() {
    if (this._initialized) return;
    this._initialized = true;
  },

  async openSplit(leftId, rightId, forkPoint = null) {
    this.leftContextId = leftId;
    this.rightContextId = rightId;
    this.forkPoint = forkPoint;
    this.leftMessages = [];
    this.rightMessages = [];
    this.leftForkInfo = null;
    this.rightForkInfo = null;
    this.error = "";
    this._leftLogVersion = 0;
    this._rightLogVersion = 0;
    this._leftLogGuid = "";
    this._rightLogGuid = "";
    this.active = true;
    this.loading = true;

    await this._fetchBoth();
    this.loading = false;
    this._startPolling();
  },

  closeSplit() {
    this._stopPolling();
    this.active = false;
    this.leftContextId = "";
    this.rightContextId = "";
    this.forkPoint = null;
    this.leftMessages = [];
    this.rightMessages = [];
    this.leftForkInfo = null;
    this.rightForkInfo = null;
    this.error = "";
  },

  cleanup() {
    this.closeSplit();
  },

  async _fetchBoth() {
    try {
      const [leftResult, rightResult] = await Promise.all([
        this._fetchLogs(this.leftContextId, this._leftLogVersion),
        this._fetchLogs(this.rightContextId, this._rightLogVersion),
      ]);

      if (leftResult) {
        // Reset on guid change
        if (this._leftLogGuid && this._leftLogGuid !== leftResult.log_guid) {
          this.leftMessages = [];
          this._leftLogVersion = 0;
        }
        this._leftLogGuid = leftResult.log_guid;
        this._leftLogVersion = leftResult.log_version;
        if (leftResult.fork_info) this.leftForkInfo = leftResult.fork_info;
        this._appendMessages("left", leftResult.logs);
      }

      if (rightResult) {
        if (this._rightLogGuid && this._rightLogGuid !== rightResult.log_guid) {
          this.rightMessages = [];
          this._rightLogVersion = 0;
        }
        this._rightLogGuid = rightResult.log_guid;
        this._rightLogVersion = rightResult.log_version;
        if (rightResult.fork_info) this.rightForkInfo = rightResult.fork_info;
        this._appendMessages("right", rightResult.logs);
      }

      // Auto-detect fork point from fork_info if not explicitly set
      if (this.forkPoint === null) {
        this._detectForkPoint();
      }
    } catch (e) {
      this.error = e.message || "Failed to fetch logs";
    }
  },

  async _fetchLogs(contextId, logFrom) {
    if (!contextId) return null;
    try {
      const result = await callJsonApi("/chat_logs", {
        context_id: contextId,
        log_from: logFrom,
      });
      if (!result.success) {
        console.warn("chat_logs failed:", result.error);
        return null;
      }
      return result;
    } catch (e) {
      console.warn("chat_logs error:", e);
      return null;
    }
  },

  _appendMessages(side, logs) {
    if (!logs || !logs.length) return;
    const existing = side === "left" ? this.leftMessages : this.rightMessages;
    const existingMap = new Map(existing.map((m) => [m.no, m]));

    for (const log of logs) {
      existingMap.set(log.no, log);
    }

    const sorted = Array.from(existingMap.values()).sort(
      (a, b) => a.no - b.no,
    );
    if (side === "left") {
      this.leftMessages = sorted;
    } else {
      this.rightMessages = sorted;
    }
  },

  _detectForkPoint() {
    // Check right context's fork_info — it should have forked_from pointing to left
    const info = this.rightForkInfo || this.leftForkInfo;
    if (info && info.fork_point != null) {
      this.forkPoint = info.fork_point;
      return;
    }

    // Fallback: find the last matching user message by content
    const leftUsers = this.leftMessages.filter((m) => m.type === "user");
    const rightUsers = this.rightMessages.filter((m) => m.type === "user");
    let lastMatch = 0;
    for (
      let i = 0;
      i < Math.min(leftUsers.length, rightUsers.length);
      i++
    ) {
      if (leftUsers[i].content === rightUsers[i].content) {
        lastMatch = leftUsers[i].no;
      } else {
        break;
      }
    }
    if (lastMatch > 0) {
      this.forkPoint = lastMatch;
    }
  },

  /**
   * Classify a message as "shared" (before fork) or "divergent" (after fork).
   */
  getMessageClass(msg) {
    if (this.forkPoint === null) return "divergent";
    return msg.no <= this.forkPoint ? "shared" : "divergent";
  },

  /**
   * Get only the main displayable message types (user + response).
   * Process types (agent, tool, etc.) are collapsed in split view.
   */
  getDisplayMessages(side) {
    const msgs = side === "left" ? this.leftMessages : this.rightMessages;
    return msgs.filter(
      (m) =>
        m.type === "user" ||
        (m.type === "response" && (m.agentno === 0 || m.agentno == null)),
    );
  },

  _startPolling() {
    this._stopPolling();
    this._pollTimer = setInterval(() => {
      if (this.active) {
        this._fetchBoth();
      }
    }, POLL_INTERVAL_MS);
  },

  _stopPolling() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  },
};

export const store = createStore("splitView", model);
