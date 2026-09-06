import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const API = "/plugins/_a0_connector/browser_bridge_approval";
const CONTRACT = "a0.browser-bridge.approval.v1";
const choices = ["decline", "approve_once"];
const classes = ["sensitive_input", "external_side_effect", "unknown"];
const identifier = (value) => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/.test(value);

function envelope(value) {
  if (value?.contract !== CONTRACT || value.approval_version !== 1 || value.browser_control_ready !== false) throw new Error("Invalid action authority");
  return value;
}

function parseRequests(value, contextId) {
  const response = envelope(value);
  if (!Array.isArray(response.challenges) || response.challenges.length > 128) throw new Error("Invalid action requests");
  const requests = response.challenges.map((request) => {
    if (!identifier(request?.challenge_id) || !["click", "type", "upload_file"].includes(request.action) || !classes.includes(request.action_class)
      || (request.action === "type" && request.action_class !== "sensitive_input")
      || (request.action === "upload_file" && request.action_class !== "external_side_effect")
      || JSON.stringify(request.options) !== JSON.stringify(choices)
      || !Number.isSafeInteger(request.expires_at_ms) || request.expires_at_ms < 1
      || typeof request.origin !== "string" || request.origin.length > 2048) throw new Error("Invalid action request");
    const url = new URL(request.origin);
    if (!["https:", "http:"].includes(url.protocol) || url.origin !== request.origin) throw new Error("Invalid action origin");
    // Page descriptions, DOM, input data and authority bindings are not UI copy.
    return { id: request.challenge_id, action: request.action, origin: request.origin, expires: request.expires_at_ms,
      contextId };
  });
  if (new Set(requests.map((request) => request.id)).size !== requests.length) throw new Error("Duplicate action request");
  return requests;
}

export function createActionRequestsModel({ api, selection = () => null, now = Date.now, schedule = setTimeout, unschedule = clearTimeout }) {
  // Session-local uncertainty survives component close/reopen. A failed HTTP
  // reply cannot prove that Core did not record the decision.
  const unresolved = new Map();
  const prune = (time = now()) => { for (const [id, request] of unresolved) if (request.expires <= time) unresolved.delete(id); };
  const uncertainNotice = "This decision could not be confirmed. Refresh to check the request; do not repeat the action.";
  return {
    active: false, generation: 0, listSequence: 0, timer: null, loading: false, busyId: "",
    requests: [], state: "not_checked", stateContextId: "", notice: "", noticeContextId: "", noticeExpires: 0, decisionUnconfirmed: false, clock: 0,
    async mount() { this.cleanup(); this.active = true; await this.refresh(); },
    cleanup() {
      this.active = false; this.generation += 1; this.listSequence += 1;
      if (this.timer !== null) unschedule(this.timer);
      this.timer = null; this.requests = []; this.loading = false; this.busyId = "";
      this.state = "not_checked"; this.stateContextId = ""; this.notice = ""; this.noticeContextId = ""; this.noticeExpires = 0; this.decisionUnconfirmed = false;
    },
    current(generation) { return this.active && this.generation === generation; },
    hasUnconfirmedDecision() {
      prune(Math.max(this.clock, now()));
      return this.active && [...unresolved.values()].some((request) => request.id !== this.busyId && this.matchesSelection(request));
    },
    visibleNotice() {
      if (this.hasUnconfirmedDecision()) return uncertainNotice;
      if (this.noticeExpires && Math.max(this.clock, now()) >= this.noticeExpires) return "";
      return this.active && !this.decisionUnconfirmed && this.noticeContextId === selection()?.contextId ? this.notice : "";
    },
    unavailableHere() { return this.state === "unavailable" && this.stateContextId === selection()?.contextId; },
    matchesSelection(request) {
      const selected = selection();
      return Boolean(selected && request.contextId === selected.contextId);
    },
    visibleRequests() { prune(); return this.requests.filter((request) => this.matchesSelection(request)
      && request.expires > Math.max(this.clock, now()) && !unresolved.has(request.id)); },
    canDecide(request) {
      prune();
      return this.active && !this.busyId && this.state === "loaded"
        && unresolved.size < 128 && !unresolved.has(request.id)
        && this.matchesSelection(request) && this.requests.some((item) => item.id === request.id) && request.expires > now();
    },
    async refresh() {
      if (!this.active || this.loading) return;
      if (this.timer !== null) unschedule(this.timer);
      this.timer = null;
      const generation = this.generation, sequence = ++this.listSequence;
      const contextId = selection()?.contextId || "";
      this.loading = true; this.clock = now();
      try {
        const requests = identifier(contextId) ? parseRequests(await api(API, { action: "list", context_id: contextId }), contextId) : [];
        if (!this.current(generation) || sequence !== this.listSequence || contextId !== (selection()?.contextId || "")) return;
        this.requests = requests.filter((request) => request.expires > now()); this.state = "loaded"; this.stateContextId = contextId;
        prune();
        if ([...unresolved.values()].some((request) => this.matchesSelection(request))) {
          this.decisionUnconfirmed = true; this.notice = uncertainNotice;
        }
      } catch {
        if (!this.current(generation) || sequence !== this.listSequence || contextId !== (selection()?.contextId || "")) return;
        // Preserve known prompts through a transport failure without retaining
        // decision authority: canDecide requires a successful current list.
        this.requests = this.requests.filter((request) => this.matchesSelection(request) && request.expires > now());
        this.state = "unavailable"; this.stateContextId = contextId;
      } finally {
        if (this.current(generation)) {
          this.loading = false; this.clock = now();
          this.timer = schedule(() => { void this.refresh(); }, this.state === "unavailable" ? 10_000 : 2_000);
        }
      }
    },
    async decide(request, choice) {
      if (!choices.includes(choice) || !this.canDecide(request)) return;
      const generation = this.generation;
      unresolved.set(request.id, { ...request });
      this.noticeExpires = 0;
      this.listSequence += 1; this.busyId = request.id; this.notice = "Recording your decision…"; this.noticeContextId = request.contextId; this.decisionUnconfirmed = false;
      try {
        const response = envelope(await api(API, { challenge_id: request.id, choice }));
        if (response.challenge_id !== request.id || response.decision !== (choice === "approve_once" ? "approved" : "declined")
          || !identifier(response.control_id) || response.status !== "accepted") throw new Error("Invalid action acknowledgement");
        unresolved.delete(request.id);
        if (!this.current(generation)) return;
        this.listSequence += 1; this.requests = this.requests.filter((item) => item.id !== request.id);
        this.notice = choice === "decline" ? "Decline recorded. Waiting for the browser to confirm cancellation."
          : "Approval recorded for this action only. The browser will recheck the target before continuing.";
        this.noticeExpires = now() + 3_000;
      } catch {
        if (this.current(generation)) {
          this.listSequence += 1; this.requests = this.requests.filter((item) => item.id !== request.id);
          this.decisionUnconfirmed = true;
          this.notice = uncertainNotice;
        }
      } finally { if (this.current(generation)) this.busyId = ""; }
    },
  };
}

export const store = createStore("browserActionRequests", createActionRequestsModel({
  api: callJsonApi,
  selection: () => ({ contextId: globalThis.Alpine?.store("chats")?.selected || "" }),
}));
