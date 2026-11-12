"""Durable browsing policy with exact-origin grants for paired Browser bridges.

This module persists site decisions only.  It does not mint operation approval
receipts, advertise Browser runtime readiness, or dispatch connector events.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import ipaddress
import re
import threading
import time
from typing import Any, Callable, ContextManager, Mapping
from urllib.parse import urlsplit
import uuid

from plugins._a0_connector.helpers.browser_bridge_pairing import validate_identifier
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
)


BROWSER_BRIDGE_POLICY_CONTRACT = "a0.browser-bridge.site-policy.v1"
BROWSER_BRIDGE_POLICY_VERSION = 1
BROWSER_BRIDGE_POLICY_STORE_KEY = "a0_browser_bridge_site_policy_v1"
DEFAULT_SITE_MODE = "ask_per_site"
ALL_WEBSITES_MODE = "allow_all_websites"
MAX_POLICY_REQUEST_BYTES = 8 * 1024
MAX_POLICY_GRANTS = 512
MAX_ORIGIN_BYTES = 2_048

_ASCII_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
_persistent_policy_lock = threading.RLock()


class BrowserBridgePolicyError(ValueError):
    """A caller supplied an invalid policy identity or origin."""


class BrowserBridgePolicyUnavailable(BrowserBridgePolicyError):
    """The durable policy cannot be read or updated safely."""


@dataclass(frozen=True, slots=True)
class BrowserBridgeOriginGrant:
    grant_id: str
    server_instance_id: str
    bridge_id: str
    subject_id: str
    origin: str
    created_at_ms: int
    updated_at_ms: int

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "grant_id": self.grant_id,
            "origin": self.origin,
            "created_at_ms": self.created_at_ms,
            "updated_at_ms": self.updated_at_ms,
        }


def normalize_site_origin(value: Any) -> str:
    """Return the exact canonical HTTP(S) origin or reject it."""

    if not isinstance(value, str) or not value or value != value.strip():
        raise BrowserBridgePolicyError("invalid site origin")
    try:
        encoded_size = len(value.encode("utf-8"))
    except UnicodeError:
        raise BrowserBridgePolicyError("invalid site origin") from None
    if (
        encoded_size > MAX_ORIGIN_BYTES
        or "\\" in value
        or "*" in value
        or "?" in value
        or "#" in value
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    ):
        raise BrowserBridgePolicyError("invalid site origin")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except (TypeError, ValueError):
        raise BrowserBridgePolicyError("invalid site origin") from None
    scheme = parsed.scheme.lower()
    if (
        scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or parsed.netloc.endswith(":")
    ):
        raise BrowserBridgePolicyError("invalid site origin")
    hostname = parsed.hostname
    if not hostname or any(character.isspace() for character in hostname):
        raise BrowserBridgePolicyError("invalid site origin")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            ascii_host = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError:
            raise BrowserBridgePolicyError("invalid site origin") from None
        labels = ascii_host.split(".")
        if (
            len(ascii_host) > 253
            or any(not _ASCII_LABEL.fullmatch(label) for label in labels)
            or _is_browser_ipv4_number(labels[-1])
        ):
            raise BrowserBridgePolicyError("invalid site origin")
        canonical_host = ascii_host
    else:
        if getattr(address, "scope_id", None) is not None:
            raise BrowserBridgePolicyError("invalid site origin")
        canonical_host = f"[{address.compressed}]" if address.version == 6 else address.compressed

    if port is not None and not 1 <= port <= 65_535:
        raise BrowserBridgePolicyError("invalid site origin")
    canonical_port = None if (scheme, port) in {("http", 80), ("https", 443)} else port
    return f"{scheme}://{canonical_host}{f':{canonical_port}' if canonical_port else ''}"


def _is_browser_ipv4_number(label: str) -> bool:
    """Reject DNS spellings browsers would reinterpret as legacy IPv4."""

    if label.startswith("0x"):
        return len(label) > 2 and all(character in "0123456789abcdef" for character in label[2:])
    if len(label) > 1 and label.startswith("0"):
        return all(character in "01234567" for character in label[1:])
    return label.isdecimal()


class BrowserBridgePolicyRepository:
    """Bounded saved sites and explicit production all-websites preference."""

    def __init__(
        self,
        *,
        load: Callable[[], Any] | None = None,
        save: Callable[[dict[str, Any]], None] | None = None,
        clock_ms: Callable[[], int] | None = None,
        id_factory: Callable[[], str] | None = None,
        lock: ContextManager[Any] | None = None,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self._load = load or _load_default_policy
        self._save = save or _save_default_policy
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))
        self._lock = lock or _persistent_policy_lock

    @property
    def transport_profile(self) -> BrowserBridgeTransportProfile:
        return self._transport_profile

    def list_grants(
        self,
        *,
        server_instance_id: Any,
        bridge_id: Any,
        subject_id: Any,
    ) -> tuple[BrowserBridgeOriginGrant, ...]:
        key = _policy_key(server_instance_id, bridge_id, subject_id)
        with self._lock:
            grants = self._validated_grants_locked()
            return tuple(
                grant
                for grant in grants
                if _grant_key(grant) == key
            )

    def active_grant(
        self,
        *,
        server_instance_id: Any,
        bridge_id: Any,
        subject_id: Any,
        origin: Any,
    ) -> BrowserBridgeOriginGrant | None:
        canonical_origin = normalize_site_origin(origin)
        exact = next(
            (
                grant
                for grant in self.list_grants(
                    server_instance_id=server_instance_id,
                    bridge_id=bridge_id,
                    subject_id=subject_id,
                )
                if grant.origin == canonical_origin
            ),
            None,
        )
        if exact is not None:
            return exact
        key = _policy_key(server_instance_id, bridge_id, subject_id)
        with self._lock:
            self._validated_grants_locked()
            mode = next((item for item in self._modes_locked() if _mode_key(item) == key), None)
            if mode is None:
                return None
            # A bounded exact-origin projection, not a wildcard wire grant or
            # a permanent grant surviving withdrawal of this saved preference.
            digest = hashlib.sha256((mode["grant_id"] + "\0" + canonical_origin).encode()).hexdigest()
            return BrowserBridgeOriginGrant("all-sites-" + digest, *key, canonical_origin,
                                            mode["created_at_ms"], mode["updated_at_ms"])

    def site_mode(self, *, server_instance_id, bridge_id, subject_id) -> str:
        key = _policy_key(server_instance_id, bridge_id, subject_id)
        with self._lock:
            self._validated_grants_locked()
            return ALL_WEBSITES_MODE if any(_mode_key(item) == key for item in self._modes_locked()) else DEFAULT_SITE_MODE

    def set_site_mode(self, *, server_instance_id, bridge_id, subject_id, site_mode) -> None:
        if self._transport_profile is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT or not isinstance(site_mode, str) or site_mode not in {DEFAULT_SITE_MODE, ALL_WEBSITES_MODE}:
            raise BrowserBridgePolicyError("invalid site mode")
        key = _policy_key(server_instance_id, bridge_id, subject_id)
        with self._lock:
            grants = self._validated_grants_locked()
            modes = self._modes_locked()
            existing = next((item for item in modes if _mode_key(item) == key), None)
            if (existing is not None) == (site_mode == ALL_WEBSITES_MODE):
                return
            modes = [item for item in modes if _mode_key(item) != key]
            if site_mode == ALL_WEBSITES_MODE:
                if len(modes) >= 128:
                    raise BrowserBridgePolicyUnavailable("site mode capacity")
                now = self._now()
                mode = dict(zip(("server_instance_id", "bridge_id", "subject_id"), key))
                try:
                    grant_id = validate_identifier(self._id_factory(), field_name="grant_id")
                except Exception as error:
                    raise BrowserBridgePolicyUnavailable("site mode identity unavailable") from error
                mode.update(grant_id=grant_id, created_at_ms=now, updated_at_ms=now)
                if any(item["grant_id"] == mode["grant_id"] for item in modes):
                    raise BrowserBridgePolicyUnavailable("site mode identity collision")
                modes.append(mode)
            self._save_grants_locked(grants, modes=modes)
            if self.site_mode(server_instance_id=key[0], bridge_id=key[1], subject_id=key[2]) != site_mode:
                raise BrowserBridgePolicyUnavailable("site mode readback failed")

    def allow(
        self,
        *,
        server_instance_id: Any,
        bridge_id: Any,
        subject_id: Any,
        origin: Any,
    ) -> BrowserBridgeOriginGrant:
        server_id, safe_bridge_id, safe_subject_id = _policy_key(
            server_instance_id, bridge_id, subject_id
        )
        canonical_origin = normalize_site_origin(origin)
        with self._lock:
            grants = self._validated_grants_locked()
            for grant in grants:
                if (
                    _grant_key(grant) == (server_id, safe_bridge_id, safe_subject_id)
                    and grant.origin == canonical_origin
                ):
                    return grant
            if len(grants) >= MAX_POLICY_GRANTS:
                raise BrowserBridgePolicyUnavailable("site policy grant limit reached")
            now = self._now()
            try:
                grant_id = validate_identifier(self._id_factory(), field_name="grant_id")
            except Exception as error:
                raise BrowserBridgePolicyUnavailable("site policy identity unavailable") from error
            if any(grant.grant_id == grant_id for grant in grants):
                raise BrowserBridgePolicyUnavailable("site policy identity collision")
            grant = BrowserBridgeOriginGrant(
                grant_id=grant_id,
                server_instance_id=server_id,
                bridge_id=safe_bridge_id,
                subject_id=safe_subject_id,
                origin=canonical_origin,
                created_at_ms=now,
                updated_at_ms=now,
            )
            grants.append(grant)
            self._save_grants_locked(grants)
            return grant

    def revoke(
        self,
        *,
        server_instance_id: Any,
        bridge_id: Any,
        subject_id: Any,
        origin: Any,
    ) -> bool:
        key = _policy_key(server_instance_id, bridge_id, subject_id)
        canonical_origin = normalize_site_origin(origin)
        with self._lock:
            grants = self._validated_grants_locked()
            retained = [
                grant
                for grant in grants
                if not (_grant_key(grant) == key and grant.origin == canonical_origin)
            ]
            if len(retained) == len(grants):
                return False
            self._save_grants_locked(retained)
            return True

    def _validated_grants_locked(self) -> list[BrowserBridgeOriginGrant]:
        try:
            document = self._load()
        except Exception as error:
            raise BrowserBridgePolicyUnavailable("site policy store unavailable") from error
        if document in (None, {}):
            return []
        if (
            not isinstance(document, Mapping)
            or type(document.get("schema_version")) is not int
            or (document.get("schema_version"), frozenset(document)) not in {
                (1, frozenset({"schema_version", "grants"})),
                (2, frozenset({"schema_version", "grants", "all_websites"})),
            }
            or not isinstance(document.get("grants"), list)
            or len(document["grants"]) > MAX_POLICY_GRANTS
        ):
            raise BrowserBridgePolicyUnavailable("invalid site policy store")
        try:
            grants = [_validated_grant(value) for value in document["grants"]]
        except BrowserBridgePolicyError as error:
            raise BrowserBridgePolicyUnavailable("invalid site policy store") from error
        keys = [(*_grant_key(grant), grant.origin) for grant in grants]
        grant_ids = [grant.grant_id for grant in grants]
        if len(set(keys)) != len(keys) or len(set(grant_ids)) != len(grant_ids):
            raise BrowserBridgePolicyUnavailable("invalid site policy store")
        try:
            self._validate_modes(document.get("all_websites", []))
        except Exception as error:
            raise BrowserBridgePolicyUnavailable("invalid site mode store") from error
        return grants

    def _modes_locked(self):
        try:
            document = self._load()
            return self._validate_modes(document.get("all_websites", []) if document else [])
        except Exception as error:
            raise BrowserBridgePolicyUnavailable("invalid site mode store") from error

    def _validate_modes(self, values):
        if not isinstance(values, list) or len(values) > 128 or (values and self._transport_profile is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT):
            raise BrowserBridgePolicyUnavailable("invalid site mode store")
        keys, ids = set(), set()
        for item in values:
            if not isinstance(item, dict) or set(item) != {"server_instance_id", "bridge_id", "subject_id", "grant_id", "created_at_ms", "updated_at_ms"}:
                raise BrowserBridgePolicyUnavailable("invalid site mode store")
            key = _policy_key(item["server_instance_id"], item["bridge_id"], item["subject_id"])
            token = validate_identifier(item["grant_id"], field_name="grant_id")
            if (key in keys or token in ids or type(item["created_at_ms"]) is not int
                or type(item["updated_at_ms"]) is not int or not 0 <= item["created_at_ms"] <= item["updated_at_ms"]):
                raise BrowserBridgePolicyUnavailable("invalid site mode store")
            keys.add(key); ids.add(token)
        return [dict(item) for item in values]

    def _save_grants_locked(self, grants: list[BrowserBridgeOriginGrant], *, modes=None) -> None:
        modes = self._modes_locked() if modes is None else self._validate_modes(modes)
        document = {
            "schema_version": 2 if modes else BROWSER_BRIDGE_POLICY_VERSION,
            "grants": [_grant_as_stored_dict(grant) for grant in grants],
            **({"all_websites": modes} if modes else {}),
        }
        try:
            self._save(document)
        except Exception as error:
            raise BrowserBridgePolicyUnavailable("site policy store unavailable") from error

    def _now(self) -> int:
        now = self._clock_ms()
        if isinstance(now, bool) or not isinstance(now, int) or now < 0:
            raise BrowserBridgePolicyUnavailable("site policy clock unavailable")
        return now


def _policy_key(
    server_instance_id: Any,
    bridge_id: Any,
    subject_id: Any,
) -> tuple[str, str, str]:
    try:
        return (
            validate_identifier(server_instance_id, field_name="server_instance_id"),
            validate_identifier(bridge_id, field_name="bridge_id"),
            validate_identifier(subject_id, field_name="subject_id"),
        )
    except Exception as error:
        raise BrowserBridgePolicyError("invalid site policy identity") from error


def _grant_key(grant: BrowserBridgeOriginGrant) -> tuple[str, str, str]:
    return grant.server_instance_id, grant.bridge_id, grant.subject_id


def _mode_key(value):
    return value["server_instance_id"], value["bridge_id"], value["subject_id"]


def _validated_grant(value: Any) -> BrowserBridgeOriginGrant:
    required = {
        "grant_id", "server_instance_id", "bridge_id", "subject_id", "origin",
        "created_at_ms", "updated_at_ms",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise BrowserBridgePolicyError("invalid site policy grant")
    created = value.get("created_at_ms")
    updated = value.get("updated_at_ms")
    if (
        isinstance(created, bool)
        or not isinstance(created, int)
        or created < 0
        or isinstance(updated, bool)
        or not isinstance(updated, int)
        or updated < created
    ):
        raise BrowserBridgePolicyError("invalid site policy grant")
    server_id, bridge_id, subject_id = _policy_key(
        value.get("server_instance_id"), value.get("bridge_id"), value.get("subject_id")
    )
    try:
        grant_id = validate_identifier(value.get("grant_id"), field_name="grant_id")
    except Exception as error:
        raise BrowserBridgePolicyError("invalid site policy grant") from error
    return BrowserBridgeOriginGrant(
        grant_id=grant_id,
        server_instance_id=server_id,
        bridge_id=bridge_id,
        subject_id=subject_id,
        origin=normalize_site_origin(value.get("origin")),
        created_at_ms=created,
        updated_at_ms=updated,
    )


def _grant_as_stored_dict(grant: BrowserBridgeOriginGrant) -> dict[str, Any]:
    return {
        "grant_id": grant.grant_id,
        "server_instance_id": grant.server_instance_id,
        "bridge_id": grant.bridge_id,
        "subject_id": grant.subject_id,
        "origin": grant.origin,
        "created_at_ms": grant.created_at_ms,
        "updated_at_ms": grant.updated_at_ms,
    }


def _load_default_policy() -> Any:
    from helpers import kvp

    return kvp.get_persistent(BROWSER_BRIDGE_POLICY_STORE_KEY, None)


def _save_default_policy(value: dict[str, Any]) -> None:
    from helpers import kvp

    kvp.set_persistent(BROWSER_BRIDGE_POLICY_STORE_KEY, value)


_repository: BrowserBridgePolicyRepository | None = None
_repository_lock = threading.Lock()


def get_browser_bridge_policy_repository() -> BrowserBridgePolicyRepository:
    global _repository
    if _repository is None:
        with _repository_lock:
            if _repository is None:
                _repository = BrowserBridgePolicyRepository()
    return _repository
