"""Process-only user consent before an owned tab exists; not a native receipt."""
from __future__ import annotations

import asyncio
from concurrent.futures import Future
from dataclasses import dataclass, field
import threading
import time
import uuid

from plugins._a0_connector.helpers.browser_bridge_policy import normalize_site_origin
from plugins._a0_connector.helpers.browser_bridge_operations import OperationBinding


class FirstOpenDenied(RuntimeError):
    pass


@dataclass(repr=False)
class _Request:
    challenge_id: str
    binding: OperationBinding
    origin: str
    current: object
    expires: int
    future: Future = field(default_factory=Future)
    decision: str | None = None
    grant_id: str = field(default_factory=lambda: "open-grant-" + uuid.uuid4().hex)
    decision_id: str = field(default_factory=lambda: "open-decision-" + uuid.uuid4().hex)
    grant_expires: int = 0
    lease_handle: str | None = None


def _same_turn(a, b):
    return a.principal is b.principal and all(getattr(a, key) == getattr(b, key) for key in (
        "connector_sid", "load_generation_id", "bridge_id", "context_id", "browser_session_id", "turn_id"))


class FirstOpenSiteAuthority:
    def __init__(self, *, clock_ms=None, approval_ms=120_000, grant_ms=7_200_000, max_entries=64,
                 policy_repository=None, server_instance_id=None):
        if (any(type(value) is not int for value in (approval_ms, grant_ms, max_entries))
                or not 1 <= approval_ms <= 120_000 or not 1 <= grant_ms <= 7_200_000 or not 1 <= max_entries <= 64):
            raise ValueError("invalid first-open bounds")
        self._clock = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._approval_ms, self._grant_ms, self._max = approval_ms, grant_ms, max_entries
        self._entries = {}
        self._lock = threading.RLock()
        self._policy = policy_repository
        self._server_id = server_instance_id

    def _saved_grant(self, entry):
        if self._policy is None or self._server_id is None:
            raise FirstOpenDenied()
        return self._policy.active_grant(server_instance_id=self._server_id,
            bridge_id=entry.binding.bridge_id, subject_id=entry.binding.principal.subject_id,
            origin=entry.origin)

    def _live(self, entry):
        try:
            return entry.current(entry.binding) is True
        except Exception:
            return False

    def _prune(self):
        now = self._clock()
        for key, entry in tuple(self._entries.items()):
            deadline = entry.expires if entry.decision is None or entry.decision == "deny" else entry.grant_expires
            if now >= deadline or not self._live(entry):
                self._remove(key)

    def _remove(self, key):
        entry = self._entries.pop(key, None)
        if entry is not None and not entry.future.done():
            entry.future.set_result(False)

    async def request(self, binding, origin, *, current):
        if not isinstance(binding, OperationBinding) or not callable(current) or current(binding) is not True:
            raise FirstOpenDenied()
        origin = normalize_site_origin(origin)
        with self._lock:
            self._prune()
            existing = self.grant_for(binding, origin)
            if existing is not None:
                return existing
            if len(self._entries) >= self._max:
                raise FirstOpenDenied()
            entry = _Request("open-site-" + uuid.uuid4().hex, binding, origin, current,
                             self._clock() + self._approval_ms)
            self._entries[entry.challenge_id] = entry
        try:
            allowed = await asyncio.wait_for(asyncio.wrap_future(entry.future), self._approval_ms / 1000)
            grant = self.grant_for(binding, origin)
            if not allowed or grant is None or current(binding) is not True:
                raise FirstOpenDenied()
            return grant
        except BaseException:
            with self._lock:
                self._remove(entry.challenge_id)
            raise

    def list_pending(self, *, subject_id, context_id, bridge_id):
        with self._lock:
            self._prune()
            return tuple({"challenge_id": entry.challenge_id, "origin": entry.origin,
                "action_class": "open", "summary": "Open this site in an Agent Zero-owned tab.",
                "options": ["deny", "allow_once", "allow_turn", "allow_site"], "expires_at_ms": entry.expires}
                for entry in self._entries.values() if entry.decision is None
                and entry.binding.principal.subject_id == subject_id
                and entry.binding.context_id == context_id and entry.binding.bridge_id == bridge_id)

    def decide(self, *, subject_id, challenge_id, decision):
        if decision not in {"deny", "allow_once", "allow_turn", "allow_site"}:
            raise FirstOpenDenied()
        with self._lock:
            self._prune()
            entry = self._entries.get(challenge_id)
            if (entry is None or entry.binding.principal.subject_id != subject_id
                    or self._clock() >= entry.expires or not self._live(entry)):
                raise FirstOpenDenied()
            if entry.decision is not None and entry.decision != decision:
                raise FirstOpenDenied()
            if entry.decision is None:
                if decision == "allow_site":
                    if self._policy is None or self._server_id is None:
                        raise FirstOpenDenied()
                    # Persist only this explicit exact-origin choice, before
                    # releasing the waiter. No caller-supplied policy fields.
                    grant = self._policy.allow(server_instance_id=self._server_id,
                        bridge_id=entry.binding.bridge_id, subject_id=entry.binding.principal.subject_id,
                        origin=entry.origin)
                    saved = self._saved_grant(entry)
                    if (saved is None or saved.grant_id != grant.grant_id
                            or not self._live(entry) or self._clock() >= entry.expires):
                        self._remove(challenge_id)
                        raise FirstOpenDenied()
                    entry.grant_id = saved.grant_id
                entry.decision = decision
                entry.grant_expires = self._clock() + self._grant_ms
                if not entry.future.done():
                    entry.future.set_result(decision != "deny")
            return {"challenge_id": challenge_id, "decision": decision,
                    "control_id": entry.decision_id, "status": "accepted", "expires_at_ms": entry.expires}

    def grant_for(self, binding, origin, target_handle=None):
        with self._lock:
            self._prune()
            for entry in self._entries.values():
                if entry.origin != origin or not _same_turn(entry.binding, binding) or not self._live(entry):
                    continue
                if entry.decision == "allow_site":
                    saved = self._saved_grant(entry)
                    return saved.grant_id if saved is not None and saved.grant_id == entry.grant_id else None
                if entry.decision == "allow_turn" or (entry.decision == "allow_once" and (
                    (target_handle is None and entry.lease_handle is None
                     and entry.binding.op_id == binding.op_id and entry.binding.action_id == binding.action_id)
                    or (target_handle is not None and entry.lease_handle == target_handle))):
                    return entry.grant_id
        return None

    def observe_open(self, binding, origin, result):
        handle = result.get("tab_handle") if isinstance(result, dict) else None
        if not isinstance(handle, str) or not handle or len(handle) > 256:
            return
        with self._lock:
            self._prune()
            for entry in self._entries.values():
                if (_same_turn(entry.binding, binding) and entry.binding.op_id == binding.op_id
                        and entry.binding.action_id == binding.action_id and entry.origin == origin
                        and entry.decision == "allow_once" and self._live(entry)):
                    entry.lease_handle = handle

    def retire(self, predicate=lambda _binding: True):
        with self._lock:
            for key, entry in tuple(self._entries.items()):
                if predicate(entry.binding):
                    self._remove(key)


def current_first_open_authority():
    from plugins._a0_connector.helpers.browser_bridge_bootstrap import get_browser_bridge_application
    application = get_browser_bridge_application()
    return getattr(application.browser, "first_open_authority", None) if application is not None and application.installed else None
