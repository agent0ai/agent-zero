"""Bounded current-route ownership learned only from correlated Browser results.

This index is not Chrome authority and is never persisted. The extension still
checks its exact live lease/document before every effect. URLs, titles, page
content and provider tab IDs do not belong in this index.
"""

from dataclasses import dataclass, replace
import hashlib
import re
import threading
from typing import Any, Callable

from plugins._a0_connector.helpers.browser_bridge_operations import OperationBinding, TurnBinding
from plugins._a0_connector.helpers.browser_bridge_policy import normalize_site_origin


_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")


class ExtensionLeaseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExtensionDocument:
    document_id: str
    document_epoch: int
    refs: frozenset[str]


@dataclass(frozen=True, slots=True)
class ExtensionLease:
    binding: OperationBinding
    lease_id: str
    tab_handle: str
    origin: str
    disposition: str
    document: ExtensionDocument | None = None


class ExtensionLeaseIndex:
    def __init__(self, *, authorizer: Callable[[OperationBinding], bool], max_leases: int = 1024):
        if type(max_leases) is not int or not 1 <= max_leases <= 4096:
            raise ValueError("invalid lease bound")
        self._authorizer = authorizer
        self._max_leases = max_leases
        self._leases: dict[tuple[int, str, str, str], ExtensionLease] = {}
        self._lock = threading.RLock()

    def _current(self, binding: OperationBinding) -> bool:
        try:
            return self._authorizer(binding) is True
        except Exception:
            return False

    @staticmethod
    def _key(binding: OperationBinding, handle: str) -> tuple[int, str, str, str]:
        return (id(binding.principal), binding.connector_sid, binding.load_generation_id, handle)

    def origin_for(self, binding: OperationBinding, handle: str) -> str | None:
        lease = self.lease_for(binding, handle)
        return lease.origin if lease is not None else None

    def document_for(self, binding: OperationBinding, handle: str) -> ExtensionDocument | None:
        lease = self.lease_for(binding, handle)
        return lease.document if lease is not None else None

    def clear_document(self, binding: OperationBinding, handle: str) -> None:
        with self._lock:
            lease = self._leases.get(self._key(binding, handle))
            if lease is not None and _same_session(lease.binding, binding):
                self._leases[self._key(binding, handle)] = replace(lease, document=None)

    def observe_content(self, binding: OperationBinding, handle: str, result: dict[str, Any]) -> None:
        """Remember only document/ref provenance from correlated inspection.

        Labels, DOM and text remain tool output, not approval authority. A
        challenge cannot populate this record or introduce an unseen ref.
        """
        with self._lock:
            lease = self.lease_for(binding, handle)
            if (lease is None or not isinstance(result, dict)
                    or set(result) != {"lease_id", "browser_id", "tab_handle", "document_id", "document_epoch", "title", "text", "nodes", "truncated"}
                    or result["lease_id"] != lease.lease_id or result["browser_id"] != handle or result["tab_handle"] != handle):
                raise ExtensionLeaseError("LEASE_CONFLICT")
            document_id = _identifier(result["document_id"])
            epoch = result["document_epoch"]
            if (not isinstance(epoch, str) or re.fullmatch(r"0|[1-9][0-9]{0,15}", epoch) is None
                    or int(epoch) > 2**53 - 1 or not isinstance(result["nodes"], list) or len(result["nodes"]) > 128):
                raise ExtensionLeaseError("DOCUMENT_CONFLICT")
            refs = []
            for node in result["nodes"]:
                if not isinstance(node, dict) or set(node) != {"ref", "role", "name"}:
                    raise ExtensionLeaseError("DOCUMENT_CONFLICT")
                ref = _identifier(node["ref"])
                if len(ref) > 128:
                    raise ExtensionLeaseError("DOCUMENT_CONFLICT")
                refs.append(ref)
            if len(set(refs)) != len(refs) or not self._current(binding):
                raise ExtensionLeaseError("DOCUMENT_CONFLICT")
            document = ExtensionDocument(document_id, int(epoch), frozenset(refs))
            if lease.document is not None:
                previous = lease.document
                if (document.document_epoch < previous.document_epoch or
                        (document.document_epoch == previous.document_epoch and document.document_id != previous.document_id)):
                    raise ExtensionLeaseError("DOCUMENT_CONFLICT")
            self._leases[self._key(binding, handle)] = replace(lease, document=document)

    def lease_for(self, binding: OperationBinding, handle: str) -> ExtensionLease | None:
        if not self._current(binding):
            return None
        with self._lock:
            lease = self._leases.get(self._key(binding, handle))
            if lease is None or not _same_session(lease.binding, binding):
                return None
            return lease if self._current(binding) else None

    def observe_open(self, binding: OperationBinding, result: dict[str, Any], expected_origin: str) -> ExtensionLease:
        """Call only after exact broker settlement of a successful open."""
        if not isinstance(result, dict) or not self._current(binding):
            raise ExtensionLeaseError("SCOPE_DENIED")
        lease_id, handle = _identifier(result.get("lease_id")), _identifier(result.get("tab_handle"))
        if lease_id == handle or result.get("browser_id") != handle:
            raise ExtensionLeaseError("LEASE_CONFLICT")
        try:
            origin = normalize_site_origin(result.get("origin"))
        except Exception:
            raise ExtensionLeaseError("ORIGIN_BLOCKED") from None
        disposition = result.get("disposition")
        if origin != expected_origin or disposition != "ephemeral":
            raise ExtensionLeaseError("LEASE_CONFLICT")
        lease = ExtensionLease(binding, lease_id, handle, origin, disposition)
        with self._lock:
            key = self._key(binding, handle)
            old = self._leases.get(key)
            if old is not None and old != lease:
                raise ExtensionLeaseError("LEASE_CONFLICT")
            if any(
                other.lease_id == lease_id and other_key != key
                and other.binding.principal is binding.principal
                and other.binding.load_generation_id == binding.load_generation_id
                for other_key, other in self._leases.items()
            ):
                raise ExtensionLeaseError("LEASE_CONFLICT")
            if old is None and len(self._leases) >= self._max_leases:
                raise ExtensionLeaseError("LEASE_REGISTRY_FULL")
            if not self._current(binding):
                raise ExtensionLeaseError("SCOPE_DENIED")
            self._leases[key] = lease
        return lease

    def invalidate(self, *, principal, connector_sid: str, load_generation_id: str, tab_handle: str | None = None) -> None:
        with self._lock:
            self._leases = {
                key: lease for key, lease in self._leases.items()
                if not (
                    lease.binding.principal is principal
                    and lease.binding.connector_sid == connector_sid
                    and lease.binding.load_generation_id == load_generation_id
                    and (tab_handle is None or lease.tab_handle == tab_handle)
                )
            }

    def observe_navigation(self, binding: OperationBinding, handle: str, result: dict[str, Any], expected_origin: str) -> None:
        """Advance only the exact retained lease after correlated success."""
        with self._lock:
            lease = self.lease_for(binding, handle)
            if lease is None or not isinstance(result, dict) or set(result) != {"lease_id", "browser_id", "tab_handle", "origin"}:
                raise ExtensionLeaseError("LEASE_CONFLICT")
            if (result["lease_id"] != lease.lease_id or result["browser_id"] != handle
                    or result["tab_handle"] != handle or result["origin"] != expected_origin
                    or normalize_site_origin(expected_origin) != expected_origin):
                raise ExtensionLeaseError("LEASE_CONFLICT")
            if not self._current(binding):
                raise ExtensionLeaseError("SCOPE_DENIED")
            self._leases[self._key(binding, handle)] = replace(lease, origin=expected_origin, document=None)

    def retire_turn(self, turn: TurnBinding) -> None:
        # Even a retained tab does not silently acquire permission in a future
        # turn. Explicit reconciliation/claim is a separate authority boundary.
        with self._lock:
            self._leases = {
                key: lease for key, lease in self._leases.items()
                if not (_same_session(lease.binding, turn) and lease.binding.turn_id == turn.turn_id)
            }

    def invalidate_digests(self, *, principal, connector_sid: str, load_generation_id: str,
                          context_id: str, browser_session_id: str, turn_id: str,
                          lease_id_digest: str, browser_id_digest: str) -> None:
        """Idempotent negative authority for a redacted, authenticated event."""
        with self._lock:
            self._leases = {
                key: lease for key, lease in self._leases.items()
                if not (
                    lease.binding.principal is principal
                    and lease.binding.connector_sid == connector_sid
                    and lease.binding.load_generation_id == load_generation_id
                    and lease.binding.context_id == context_id
                    and lease.binding.browser_session_id == browser_session_id
                    and lease.binding.turn_id == turn_id
                    and hashlib.sha256(lease.lease_id.encode()).hexdigest() == lease_id_digest
                    and hashlib.sha256(lease.tab_handle.encode()).hexdigest() == browser_id_digest
                )
            }


def _identifier(value: Any) -> str:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise ExtensionLeaseError("LEASE_CONFLICT")
    return value


def _same_session(left: OperationBinding, right: OperationBinding | TurnBinding) -> bool:
    return bool(
        left.principal is right.principal
        and left.connector_sid == right.connector_sid
        and left.load_generation_id == right.load_generation_id
        and left.context_id == right.context_id
        and left.browser_session_id == right.browser_session_id
        and left.turn_id == right.turn_id
    )
