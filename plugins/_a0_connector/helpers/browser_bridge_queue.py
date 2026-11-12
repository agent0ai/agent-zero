"""Restricted text-only access to bridge-owned Core message queue items.

Queue data stays in the existing AgentContext. The separate durable journal
contains hashes only and prevents replay from enqueueing or sending twice.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import threading

from helpers.ws_principal import restricted_correlation_id
from plugins._a0_connector.helpers.browser_bridge_journal import BrowserBridgeJournal

QUEUE_EVENTS = frozenset({"connector_message_queue_add", "connector_message_queue_remove", "connector_message_queue_send"})
_STORE_KEY = "a0_browser_bridge_queue_v1"
_LOCK = threading.RLock()
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_HASH = re.compile(r"[a-f0-9]{64}")
_MAX_ITEMS = 32


class BrowserBridgeQueueError(RuntimeError):
    def __init__(self, code: str, *, outcome: str = "not_applied") -> None:
        super().__init__(code)
        self.code = code
        self.outcome = outcome


class BrowserBridgeQueueController:
    def __init__(self, *, access, messages, manager, server_instance_id,
                 context_get=None, queue_service=None, load=None, save=None,
                 mark_dirty=None):
        self.access, self.messages, self.manager = access, messages, manager
        self.profile = access.transport_profile
        self.server_instance_id = server_instance_id
        self.context_get = context_get or _context_get
        self.queue_service = queue_service
        self.journal = BrowserBridgeJournal(
            _STORE_KEY, _validate_record,
            lambda: BrowserBridgeQueueError("QUEUE_STORE_UNAVAILABLE"),
            load=load, save=save,
        )
        self.mark_dirty = mark_dirty or _mark_dirty

    async def dispatch(self, event, route, document):
        if not isinstance(document, dict):
            raise BrowserBridgeQueueError("INVALID_STATE")
        request = dict(document)
        request.pop("correlationId", None)
        required = {"contract_version", "context_id"}
        if event == "connector_message_queue_add":
            required |= {"client_message_id", "text"}
        elif event in QUEUE_EVENTS:
            required |= {"item_id"}
        else:
            raise BrowserBridgeQueueError("EVENT_NOT_ALLOWED")
        if set(request) != required or type(request.get("contract_version")) is not int or request["contract_version"] != 1:
            raise BrowserBridgeQueueError("INVALID_STATE")
        context_id = _identifier(request["context_id"])
        self._authorize(route, context_id, event)
        context = self.context_get(context_id)
        if context is None:
            raise BrowserBridgeQueueError("CONTEXT_NOT_FOUND")
        scope = _digest([self.server_instance_id(), route.principal.principal_id, route.principal.subject_id, context_id])
        queue = self.queue_service
        if queue is None:
            from helpers import message_queue as queue
        with _LOCK:
            self._authorize(route, context_id, event)
            if event == "connector_message_queue_add":
                message_id = _identifier(request["client_message_id"])
                text = request["text"]
                try:
                    valid_text = isinstance(text, str) and bool(text.strip()) and len(text.encode("utf-8")) <= 32768
                except UnicodeError:
                    valid_text = False
                if not valid_text:
                    raise BrowserBridgeQueueError("INVALID_STATE")
                item_id = _digest([scope, message_id])
                content_hash = _digest(text)
                prior = self.journal.get(item_id)
                if prior is not None:
                    if prior["content_hash"] != content_hash:
                        raise BrowserBridgeQueueError("IDEMPOTENCY_CONFLICT")
                    if prior["state"] == "reserved":
                        raise BrowserBridgeQueueError("OUTCOME_UNKNOWN", outcome="unknown")
                    # A consumed/deleted item is not recreated by an old add.
                    status = prior["state"]
                else:
                    if len(queue.get_queue(context)) >= _MAX_ITEMS:
                        raise BrowserBridgeQueueError("QUEUE_LIMIT")
                    record = {"scope": scope, "content_hash": content_hash, "state": "reserved"}
                    self.journal.put(item_id, record)
                    self._authorize(route, context_id, event)
                    try:
                        queue.add(context, text, [], item_id=item_id)
                        record["state"] = "queued"
                        self.journal.put(item_id, record)
                    except Exception:
                        raise BrowserBridgeQueueError("OUTCOME_UNKNOWN", outcome="unknown") from None
                    status = "queued"
            else:
                item_id = _identifier(request["item_id"])
                prior = self.journal.get(item_id)
                if prior is None or prior["scope"] != scope:
                    raise BrowserBridgeQueueError("QUEUE_ITEM_NOT_FOUND")
                target_state = "removed" if event.endswith("_remove") else "sent"
                if prior["state"] == target_state:
                    status = target_state
                elif prior["state"] != "queued":
                    raise BrowserBridgeQueueError("OUTCOME_UNKNOWN" if prior["state"] == "reserved" else "QUEUE_ITEM_NOT_FOUND",
                                                 outcome="unknown" if prior["state"] == "reserved" else "not_applied")
                else:
                    found = next((item for item in queue.get_queue(context) if item.get("id") == item_id), None)
                    if found is None:
                        # Core may already have consumed the ordinary queue.
                        prior["state"] = "removed"
                        self.journal.put(item_id, prior)
                        status = "removed"
                    else:
                        if found.get("attachments") or _digest(found.get("text")) != prior["content_hash"]:
                            raise BrowserBridgeQueueError("QUEUE_ITEM_CHANGED")
                        prior["state"] = "reserved"
                        self.journal.put(item_id, prior)
                        self._authorize(route, context_id, event)
                        try:
                            if target_state == "sent":
                                # Pop before the effect so Core's normal queue
                                # consumer cannot subsequently send this item.
                                item = queue.pop_item(context, item_id)
                                if item is None or item.get("attachments") or _digest(item.get("text")) != prior["content_hash"]:
                                    raise BrowserBridgeQueueError("QUEUE_ITEM_CHANGED")
                                self.messages.send(route, {"contract_version": 1, "context_id": context_id,
                                                          "client_message_id": "queue:" + item_id, "text": item["text"]})
                            else:
                                queue.remove(context, item_id)
                            prior["state"] = target_state
                            self.journal.put(item_id, prior)
                        except Exception:
                            # Never retry an uncertain model/log or queue effect.
                            raise BrowserBridgeQueueError("OUTCOME_UNKNOWN", outcome="unknown") from None
                        status = target_state
            self.mark_dirty(context_id)
            self._authorize(route, context_id, event)
            try:
                items = self._items(queue, context, scope)
            except BrowserBridgeQueueError:
                # A projection read failure cannot undo the persisted effect.
                raise BrowserBridgeQueueError("OUTCOME_UNKNOWN", outcome="unknown") from None
        payload = {"contract_version": 1, "context_id": context_id, "message_queue": items}
        try:
            await asyncio.wait_for(self.manager.emit_to(
                self.profile.namespace, route.connector_sid, "connector_message_queue_updated", payload,
                handler_id=self.profile.handler_id, correlation_id=restricted_correlation_id(None),
                expected_principal=route.principal), timeout=5)
        except Exception:
            # A presentation failure cannot convert a persisted effect to a
            # not-applied response that encourages an unsafe retry.
            raise BrowserBridgeQueueError("OUTCOME_UNKNOWN", outcome="unknown") from None
        self._authorize(route, context_id, event)
        return {**payload, "item_id": item_id, "status": status}

    def _authorize(self, route, context_id, event):
        if route.transport_profile is not self.profile or not route.principal.permits_inbound(event, self.profile.handler_id):
            raise BrowserBridgeQueueError("SCOPE_DENIED")
        try:
            self.access.authorize_message_target(route, context_id=context_id)
        except Exception:
            raise BrowserBridgeQueueError("SCOPE_DENIED") from None

    def project(self, route, context_id):
        """Current owned queue for the existing subscribed-context poller."""
        self._authorize(route, context_id, "connector_message_queue_add")
        context = self.context_get(context_id)
        if context is None:
            raise BrowserBridgeQueueError("CONTEXT_NOT_FOUND")
        queue = self.queue_service
        if queue is None:
            from helpers import message_queue as queue
        scope = _digest([self.server_instance_id(), route.principal.principal_id, route.principal.subject_id, context_id])
        with _LOCK:
            items = self._items(queue, context, scope)
        self._authorize(route, context_id, "connector_message_queue_add")
        return {"contract_version": 1, "context_id": context_id, "message_queue": items}

    def _items(self, queue, context, scope):
        items = []
        for item in queue.get_queue(context):
            record = self.journal.get(item.get("id"))
            if record is None or record["scope"] != scope or record["state"] != "queued":
                continue
            if item.get("attachments") or _digest(item.get("text")) != record["content_hash"]:
                continue
            items.append({"id": item["id"], "text": item["text"][:100], "attachments": [], "attachment_count": 0})
            if len(items) == _MAX_ITEMS:
                break
        return items

def _validate_record(record):
    if not isinstance(record, dict) or set(record) != {"scope", "content_hash", "state"}:
        raise ValueError()
    if any(not isinstance(record[name], str) or not _HASH.fullmatch(record[name]) for name in ("scope", "content_hash")) or record["state"] not in {"reserved", "queued", "removed", "sent"}:
        raise ValueError()


def _identifier(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise BrowserBridgeQueueError("INVALID_STATE")
    return value


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _context_get(context_id):
    from agent import AgentContext
    return AgentContext.get(context_id)


def _mark_dirty(context_id):
    from helpers.state_monitor_integration import mark_dirty_for_context
    mark_dirty_for_context(context_id, reason="browser_bridge_queue")
