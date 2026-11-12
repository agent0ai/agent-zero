import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const API = "/plugins/_a0_connector/browser_bridge_site_authority";
const CONTRACT = "a0.browser-bridge.site-authority.v1";
const PRODUCTION_PROFILE = Object.freeze({ api: API, contract: CONTRACT });
const decisions = ["deny", "allow_once", "allow_turn"];
const firstOpenDecisions = [...decisions, "allow_site"];
const identifier = (value) => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/.test(value);

function envelope(value, profile) {
  if (value?.contract !== profile.contract || value.authority_version !== 1
    || value.browser_control_ready !== false) throw new Error("Invalid site authority");
  return value;
}

function parseRequests(value, contextId, profile) {
  const response = envelope(value, profile);
  if (!Array.isArray(response.challenges) || response.challenges.length > 128) throw new Error("Invalid site requests");
  const requests = response.challenges.map((request) => {
    if (!identifier(request?.challenge_id) || !["navigate", "open"].includes(request.action_class)
      || JSON.stringify(request.options) !== JSON.stringify(request.action_class === "open" ? firstOpenDecisions : decisions)
      || !Number.isSafeInteger(request.expires_at_ms) || request.expires_at_ms < 1
      || typeof request.origin !== "string" || request.origin.length > 2048) throw new Error("Invalid site request");
    const url = new URL(request.origin);
    if (!["https:", "http:"].includes(url.protocol) || url.origin !== request.origin) throw new Error("Invalid site origin");
    // Never render a page-supplied action description or HTML as permission UI.
    return { id: request.challenge_id, origin: request.origin, expires: request.expires_at_ms, contextId,
      canRemember: request.action_class === "open" };
  });
  if (new Set(requests.map((request) => request.id)).size !== requests.length) throw new Error("Duplicate site request");
  return requests;
}

function createRequestsModel({ api, selection = () => "", now = Date.now, schedule = setTimeout, unschedule = clearTimeout }, profile) {
  return {
    active: false, generation: 0, listSequence: 0, timer: null, loading: false, busyId: "",
    requests: [], state: "not_checked", stateContextId: "", notice: "", noticeContextId: "", noticeExpires: 0, decisionUnconfirmed: false, clock: 0,

    async mount() {
      this.cleanup();
      this.active = true;
      await this.refresh();
    },

    cleanup() {
      this.active = false; this.generation += 1; this.listSequence += 1;
      if (this.timer !== null) unschedule(this.timer);
      this.timer = null; this.requests = []; this.loading = false; this.busyId = "";
      this.state = "not_checked"; this.stateContextId = ""; this.notice = ""; this.noticeContextId = ""; this.noticeExpires = 0; this.decisionUnconfirmed = false;
    },

    current(generation) { return this.active && this.generation === generation; },
    visibleNotice() {
      const time = Math.max(this.clock, now());
      return this.active && this.noticeContextId === selection() && this.noticeExpires > time ? this.notice : "";
    },
    hasUnconfirmedDecision() { return this.decisionUnconfirmed && Boolean(this.visibleNotice()); },
    unavailableHere() { return this.state === "unavailable" && this.stateContextId === selection(); },
    visibleRequests() { return this.requests.filter((request) => request.contextId === selection() && request.expires > Math.max(this.clock, now())); },
    canDecide(request) {
      return this.active && !this.busyId && this.state === "loaded"
        && request.contextId === selection() && this.requests.some((item) => item.id === request.id) && request.expires > now();
    },

    async refresh() {
      if (!this.active || this.loading) return;
      if (this.timer !== null) unschedule(this.timer);
      this.timer = null;
      const generation = this.generation;
      const sequence = ++this.listSequence;
      const contextId = selection();
      this.loading = true; this.clock = now();
      try {
        const requests = identifier(contextId) ? parseRequests(await api(profile.api, { action: "list", context_id: contextId }), contextId, profile) : [];
        if (!this.current(generation) || sequence !== this.listSequence || contextId !== selection()) return;
        this.requests = requests.filter((request) => request.expires > now());
        this.state = "loaded"; this.stateContextId = contextId;
      } catch {
        if (!this.current(generation) || sequence !== this.listSequence || contextId !== selection()) return;
        // A failed poll is not evidence that a previously listed request was
        // withdrawn. Keep its safe projection visible, but canDecide fails shut.
        this.requests = this.requests.filter((request) => request.contextId === contextId && request.expires > now());
        this.state = "unavailable"; this.stateContextId = contextId;
      } finally {
        if (this.current(generation)) {
          this.loading = false; this.clock = now();
          this.timer = schedule(() => { void this.refresh(); }, this.state === "unavailable" ? 10_000 : 2_000);
        }
      }
    },

    async decide(request, decision) {
      if (!(request.canRemember ? firstOpenDecisions : decisions).includes(decision) || !this.canDecide(request)) return;
      const generation = this.generation;
      this.listSequence += 1;
      this.busyId = request.id; this.notice = ""; this.decisionUnconfirmed = false;
      this.noticeContextId = request.contextId; this.noticeExpires = request.expires;
      try {
        const response = envelope(await api(profile.api, { action: "decide", challenge_id: request.id, decision }), profile);
        if (!this.current(generation)) return;
        if (response.challenge_id !== request.id || response.decision !== decision
          || !identifier(response.control_id) || response.status !== "accepted"
          || !Number.isSafeInteger(response.expires_at_ms)) throw new Error("Invalid decision acknowledgement");
        this.listSequence += 1;
        this.requests = this.requests.filter((item) => item.id !== request.id);
        this.notice = "Decision recorded. The browser will recheck access before continuing.";
        this.noticeExpires = Math.min(request.expires, now() + 3_000);
      } catch {
        if (this.current(generation)) {
          this.listSequence += 1;
          this.requests = this.requests.filter((item) => item.id !== request.id);
          this.decisionUnconfirmed = true;
          this.notice = "This request could not be confirmed. Refresh to check whether it is still available.";
        }
      } finally {
        if (this.current(generation)) this.busyId = "";
      }
    },
  };
}

export function createSiteRequestsModel(dependencies) { return createRequestsModel(dependencies, PRODUCTION_PROFILE); }

export const store = createStore("browserSiteRequests", createSiteRequestsModel({
  api: callJsonApi,
  selection: () => globalThis.Alpine?.store("chats")?.selected || "",
}));
