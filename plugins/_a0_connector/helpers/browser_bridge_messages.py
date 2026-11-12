"""Once-only, authorized text delivery to an existing Agent Zero context.

The durable reservation precedes any log/model effect. A crash in that window
is uncertain, never permission to replay a message. No attachment paths, model
configuration, project creation, or legacy connector authority cross this lane.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from typing import Any, Callable

from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextAccess, BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_journal import BrowserBridgeJournal
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
)


_STORE_KEY = "a0_browser_bridge_messages_v1"
_MAX_TEXT_BYTES = 32768
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_HASH = re.compile(r"[a-f0-9]{64}")
_persistent_lock = threading.RLock()


class BrowserBridgeMessageError(RuntimeError):
    def __init__(self, code: str, *, outcome: str = "not_applied") -> None:
        super().__init__(code)
        self.code = code
        self.outcome = outcome


class BrowserBridgeMessageDispatcher:
    def __init__(
        self,
        *,
        access: BrowserBridgeContextAccess,
        server_instance_id: Callable[[], str],
        load: Callable[[str, Any], Any] | None = None,
        save: Callable[[str, dict[str, Any]], None] | None = None,
        deliver: Callable[[str, str, str], None] | None = None,
        clock_ms: Callable[[], int] | None = None,
        lock=None,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        self._access = access
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        access_profile = getattr(access, "transport_profile", None)
        if (
            access_profile is not None
            and access_profile is not self._transport_profile
        ):
            raise BrowserBridgeMessageError("INVALID_STATE")
        self._server_instance_id = server_instance_id
        self._journal = BrowserBridgeJournal(
            _STORE_KEY, _validate_record,
            lambda: BrowserBridgeMessageError("MESSAGE_STORE_UNAVAILABLE"),
            load=load, save=save,
        )
        self._deliver = deliver or _deliver_existing_context
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._lock = lock or _persistent_lock

    @property
    def transport_profile(self) -> BrowserBridgeTransportProfile:
        return self._transport_profile

    def send(self, route: BrowserBridgeContextRoute, document: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(document, dict) or set(document) != {"contract_version", "context_id", "client_message_id", "text"} or type(document.get("contract_version")) is not int or document["contract_version"] != 1:
            raise BrowserBridgeMessageError("INVALID_STATE")
        context_id = _identifier(document["context_id"])
        message_id = _identifier(document["client_message_id"])
        text = document["text"]
        if not isinstance(text, str) or not text.strip():
            raise BrowserBridgeMessageError("INVALID_STATE")
        try:
            if len(text.encode("utf-8")) > _MAX_TEXT_BYTES:
                raise BrowserBridgeMessageError("INVALID_STATE")
        except UnicodeError:
            raise BrowserBridgeMessageError("INVALID_STATE") from None
        self._authorize(route, context_id)
        try:
            server_id = _identifier(self._server_instance_id())
        except Exception:
            raise BrowserBridgeMessageError("SCOPE_DENIED") from None
        binding = {
            "server_instance_id": server_id,
            "bridge_id": route.principal.principal_id,
            "subject_id": route.principal.subject_id,
            "context_id": context_id,
            "client_message_id": message_id,
        }
        key = _digest(binding)
        content_hash = _digest({"binding": binding, "text": text})
        with self._lock:
            prior = self._journal.get(key)
            if prior is not None:
                if prior["content_hash"] != content_hash:
                    raise BrowserBridgeMessageError("IDEMPOTENCY_CONFLICT")
                if prior["state"] != "accepted":
                    raise BrowserBridgeMessageError("OUTCOME_UNKNOWN", outcome="unknown")
                self._authorize(route, context_id)
                return _accepted(context_id, message_id)
            now = self._clock_ms()
            if type(now) is not int or now < 0:
                raise BrowserBridgeMessageError("INVALID_STATE")
            record = {"content_hash": content_hash, "state": "reserved", "created_at_ms": now}
            self._journal.put(key, record)
            # No await or queued closure separates this final current-route
            # check from the actual model/log effect.
            self._authorize(route, context_id)
            try:
                still_same_server = self._server_instance_id() == server_id
            except Exception:
                still_same_server = False
            if not still_same_server:
                raise BrowserBridgeMessageError("SCOPE_DENIED")
            try:
                self._deliver(context_id, text, message_id)
            except Exception:
                # Keep the reservation even if only the log effect happened.
                raise BrowserBridgeMessageError("OUTCOME_UNKNOWN", outcome="unknown") from None
            record["state"] = "accepted"
            try:
                self._journal.put(key, record)
            except BrowserBridgeMessageError:
                raise BrowserBridgeMessageError("OUTCOME_UNKNOWN", outcome="unknown") from None
        return _accepted(context_id, message_id)

    def _authorize(self, route: BrowserBridgeContextRoute, context_id: str) -> None:
        if route.transport_profile is not self._transport_profile:
            raise BrowserBridgeMessageError("SCOPE_DENIED")
        try:
            self._access.authorize_message_target(route, context_id=context_id)
        except Exception:
            raise BrowserBridgeMessageError("SCOPE_DENIED") from None


def _validate_record(record):
    if not isinstance(record, dict) or set(record) != {"content_hash", "state", "created_at_ms"} or not isinstance(record["content_hash"], str) or not _HASH.fullmatch(record["content_hash"]) or record["state"] not in {"reserved", "accepted"} or type(record["created_at_ms"]) is not int or record["created_at_ms"] < 0:
        raise ValueError()


def _identifier(value: Any) -> str:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise BrowserBridgeMessageError("INVALID_STATE")
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _accepted(context_id: str, message_id: str) -> dict[str, Any]:
    return {"contract_version": 1, "context_id": context_id, "client_message_id": message_id, "status": "accepted"}


def _deliver_existing_context(context_id: str, text: str, message_id: str) -> None:
    from agent import AgentContext, AgentContextType, UserMessage

    context = AgentContext.get(context_id)
    if context is None or context.type == AgentContextType.BACKGROUND:
        raise BrowserBridgeMessageError("CONTEXT_NOT_FOUND")
    context.log.log(type="user", heading="", content=text, kvps={}, id=message_id)
    # AgentContext owns this task independently of the WebSocket/side panel.
    # Do not switch global current context or inherit caller paths/profiles.
    context.communicate(UserMessage(message=text, attachments=[]))
