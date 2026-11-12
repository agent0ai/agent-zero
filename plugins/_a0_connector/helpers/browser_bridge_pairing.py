"""Bounded, fail-closed Browser bridge pairing foundation.

Pending pairing secrets and source-rate state are process memory only. Durable
state contains only the companion public-key record required by trust v1.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from plugins._browser.helpers.bridge_foundation import BrowserBridgeGate


BROWSER_BRIDGE_TRUST_CONTRACT = "a0.browser-bridge.trust.v1"
BROWSER_BRIDGE_TRUST_VERSION = 1
BROWSER_BRIDGE_PAIRING_FEATURE = "browser_bridge_pairing_v1"
BROWSER_BRIDGE_EXTENSION_ID_ENV = "A0_BROWSER_BRIDGE_EXTENSION_ID"
BROWSER_BRIDGE_SERVER_BASE_URL_ENV = "A0_BROWSER_BRIDGE_SERVER_BASE_URL"
BROWSER_BRIDGE_RECORD_STORE_KEY = "a0_browser_bridge_credentials_v1"
BROWSER_BRIDGE_RECORD_SCHEMA_VERSION = 1
BROWSER_BRIDGE_INVENTORY_CONTRACT = "a0.browser-bridge.bridges.v1"

PAIRING_TTL_MS = 5 * 60 * 1000
PAIRING_MAX_FAILED_EXCHANGES = 5
PAIRING_SECRET_BYTES = 20
MAX_PENDING_PAIRINGS = 128
MAX_BRIDGE_RECORDS = 64
MAX_REQUEST_BYTES = 8 * 1024
MAX_DISPLAY_NAME_BYTES = 192
MAX_IDENTIFIER_BYTES = 512
SOURCE_RATE_WINDOW_MS = 60 * 1000
SOURCE_RATE_MAX_EXCHANGES = 20
MAX_SOURCE_BUCKETS = 256

SUBJECT_ID = "single_user"
CONNECTOR_PROTOCOL = "a0-connector.v1"
BROWSER_PROTOCOL = "a0.browser-bridge.v1"
CORE_ADAPTER_CONTRACT = "a0.browser-bridge.adapter.v1"
MV3_RUNTIME_CONTRACT = "a0.browser-bridge.mv3-runtime.v1"

FIXED_BROWSER_BRIDGE_SCOPES = (
    "bridge.connect",
    "context.list",
    "context.read",
    "context.message",
    "browser.operate",
    "browser.control",
    "browser.artifact",
    "browser.approval",
)

_CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_PAIRING_CODE_RE = re.compile(
    r"^A0B1-([0-9A-F]{8})-([0-9A-HJKMNP-TV-Z]{32})$"
)
_EXTENSION_ID_RE = re.compile(r"^[a-p]{32}$")
_PUBLIC_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_SAFE_PATH_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._~-]+$")
_DNS_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class BrowserBridgePairingError(ValueError):
    """Internal typed pairing error; callers must return allowlisted messages."""


class BrowserBridgePairingUnavailable(BrowserBridgePairingError):
    pass


class BrowserBridgePairingExchangeFailed(BrowserBridgePairingError):
    pass


class _DuplicateJsonKey(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PairingCreation:
    pairing_id: str
    pairing_code: str = field(repr=False)
    server_base_url: str = ""
    server_instance_fingerprint: str = ""
    extension_id: str = ""
    display_name: str = ""
    created_at_ms: int = 0
    expires_at_ms: int = 0

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "contract": BROWSER_BRIDGE_TRUST_CONTRACT,
            "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
            "state": "pairing_pending",
            "pairing_id": self.pairing_id,
            "pairing_code": self.pairing_code,
            "server": {
                "base_url": self.server_base_url,
                "instance_fingerprint": self.server_instance_fingerprint,
            },
            "extension_id": self.extension_id,
            "display_name": self.display_name,
            "created_at_ms": self.created_at_ms,
            "expires_at_ms": self.expires_at_ms,
            "expires_in_seconds": PAIRING_TTL_MS // 1000,
            "native_runtime_location": "user_browser_host",
            "docker_install_target": False,
            "connector_session_ready": False,
            "browser_control_ready": False,
        }


@dataclass(frozen=True, slots=True)
class PairingExchangeSuccess:
    bridge_id: str
    server_instance_id: str
    server_base_url: str
    extension_id: str
    display_name: str
    created_at_ms: int

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "contract": BROWSER_BRIDGE_TRUST_CONTRACT,
            "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
            "state": "paired",
            "bridge_id": self.bridge_id,
            "server_instance_id": self.server_instance_id,
            "server_base_url": self.server_base_url,
            "subject_id": SUBJECT_ID,
            "extension_id": self.extension_id,
            "display_name": self.display_name,
            "key_generation": 1,
            "scopes": list(FIXED_BROWSER_BRIDGE_SCOPES),
            "protocols": {
                "connector": CONNECTOR_PROTOCOL,
                "browser": BROWSER_PROTOCOL,
                "adapter": CORE_ADAPTER_CONTRACT,
                "mv3_runtime": MV3_RUNTIME_CONTRACT,
            },
            "policy": {"site_mode": "ask_per_site"},
            "created_at_ms": self.created_at_ms,
            "native_runtime_location": "user_browser_host",
            "docker_install_target": False,
            "connector_session_ready": False,
            "browser_control_ready": False,
        }


@dataclass(frozen=True, slots=True)
class BrowserBridgePublicRecord:
    """Allowlisted WebUI projection of one durable bridge record."""

    bridge_id: str
    display_name: str
    state: str
    key_generation: int
    created_at_ms: int
    last_authenticated_at_ms: int | None
    revoked_at_ms: int | None

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "bridge_id": self.bridge_id,
            "display_name": self.display_name,
            "state": self.state,
            "key_generation": self.key_generation,
            "created_at_ms": self.created_at_ms,
            "last_authenticated_at_ms": self.last_authenticated_at_ms,
            "revoked_at_ms": self.revoked_at_ms,
        }


@dataclass(frozen=True, slots=True)
class BrowserBridgeRevocation:
    bridge: BrowserBridgePublicRecord
    already_revoked: bool


@dataclass(slots=True)
class _PendingPairing:
    pairing_id: str
    pairing_prefix: str
    owner_id: str
    secret_digest: bytes = field(repr=False)
    server_instance_id: str = field(repr=False)
    server_base_url: str
    extension_id: str
    display_name: str
    created_at_ms: int
    expires_at_ms: int
    failed_exchanges: int = 0


@dataclass(slots=True)
class _SourceRate:
    window_started_at_ms: int
    attempts: int


def _now_ms() -> int:
    return int(time.time() * 1000)


def _random_uuid() -> str:
    return str(uuid.uuid4())


def _bounded_string(value: Any, *, field_name: str, max_bytes: int) -> str:
    if not isinstance(value, str) or not value:
        raise BrowserBridgePairingError(f"invalid {field_name}")
    if value != value.strip() or not value.isprintable():
        raise BrowserBridgePairingError(f"invalid {field_name}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as error:
        raise BrowserBridgePairingError(f"invalid {field_name}") from error
    if size > max_bytes:
        raise BrowserBridgePairingError(f"invalid {field_name}")
    return value


def validate_identifier(value: Any, *, field_name: str) -> str:
    return _bounded_string(
        value,
        field_name=field_name,
        max_bytes=MAX_IDENTIFIER_BYTES,
    )


def validate_display_name(value: Any) -> str:
    return _bounded_string(
        value,
        field_name="display_name",
        max_bytes=MAX_DISPLAY_NAME_BYTES,
    )


def parse_unique_json_object(raw_data: bytes) -> dict[str, Any] | None:
    """Decode one JSON object while rejecting duplicate keys at every depth."""

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise _DuplicateJsonKey("duplicate JSON object key")
            result[key] = value
        return result

    try:
        document = json.loads(raw_data, object_pairs_hook=unique_object)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return None
    return document if isinstance(document, dict) else None


def validate_extension_id(value: Any) -> str:
    if not isinstance(value, str) or not _EXTENSION_ID_RE.fullmatch(value):
        raise BrowserBridgePairingError("invalid extension_id")
    return value


def configured_extension_id(
    *, environ: Mapping[str, str] | None = None
) -> str | None:
    source = os.environ if environ is None else environ
    try:
        return validate_extension_id(source.get(BROWSER_BRIDGE_EXTENSION_ID_ENV))
    except BrowserBridgePairingError:
        return None


def normalize_server_base_url(value: Any) -> str:
    raw = _bounded_string(value, field_name="server_base_url", max_bytes=2048)
    if any(character in raw for character in ("\\", "\r", "\n", "\t")):
        raise BrowserBridgePairingError("invalid server_base_url")
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as error:
        raise BrowserBridgePairingError("invalid server_base_url") from error
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise BrowserBridgePairingError("invalid server_base_url")

    hostname = parsed.hostname.rstrip(".").lower()
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise BrowserBridgePairingError("invalid server_base_url") from error
    try:
        parsed_address = ipaddress.ip_address(ascii_hostname)
    except ValueError:
        parsed_address = None
    if not ascii_hostname or (
        parsed_address is None
        and any(
            not _DNS_LABEL_RE.fullmatch(label)
            for label in ascii_hostname.split(".")
        )
    ):
        raise BrowserBridgePairingError("invalid server_base_url")

    path = parsed.path or ""
    if "%" in path or "//" in path:
        raise BrowserBridgePairingError("invalid server_base_url")
    segments = [segment for segment in path.split("/") if segment]
    if any(
        segment in {".", ".."} or not _SAFE_PATH_SEGMENT_RE.fullmatch(segment)
        for segment in segments
    ):
        raise BrowserBridgePairingError("invalid server_base_url")
    normalized_path = "/" + "/".join(segments) if segments else ""

    is_loopback = _is_loopback_hostname(ascii_hostname)
    if parsed.scheme == "http" and not is_loopback:
        raise BrowserBridgePairingError("invalid server_base_url")
    if port is not None and port < 1:
        raise BrowserBridgePairingError("invalid server_base_url")

    host = f"[{ascii_hostname}]" if ":" in ascii_hostname else ascii_hostname
    default_port = 80 if parsed.scheme == "http" else 443
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{parsed.scheme}://{host}{port_suffix}{normalized_path}"


def _is_loopback_hostname(hostname: str) -> bool:
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def server_base_url_for_request(
    request: Any,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    source = os.environ if environ is None else environ
    configured = source.get(BROWSER_BRIDGE_SERVER_BASE_URL_ENV)
    if configured:
        return normalize_server_base_url(configured)

    headers = getattr(request, "headers", {}) or {}
    origin = headers.get("Origin") if hasattr(headers, "get") else None
    if origin:
        script_root = str(getattr(request, "script_root", "") or "")
        origin_url = normalize_server_base_url(f"{origin.rstrip('/')}{script_root}")
        request_root = getattr(request, "url_root", None)
        if request_root and normalize_server_base_url(request_root) != origin_url:
            raise BrowserBridgePairingUnavailable("request origin does not match host")
        return origin_url
    request_root = getattr(request, "url_root", None)
    if request_root:
        return normalize_server_base_url(request_root)
    raise BrowserBridgePairingUnavailable("server base URL is unavailable")


def server_instance_fingerprint(server_instance_id: str) -> str:
    digest = hashlib.sha256(server_instance_id.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:20]}"


def _encode_crockford(data: bytes) -> str:
    if len(data) != PAIRING_SECRET_BYTES:
        raise BrowserBridgePairingError("invalid pairing entropy")
    number = int.from_bytes(data, "big")
    characters = ["0"] * 32
    for index in range(31, -1, -1):
        number, remainder = divmod(number, 32)
        characters[index] = _CROCKFORD_ALPHABET[remainder]
    return "".join(characters)


def _normalize_pairing_code(value: Any) -> tuple[str, str]:
    if not isinstance(value, str) or len(value) != 46:
        raise BrowserBridgePairingExchangeFailed("pairing exchange failed")
    normalized = value.upper()
    match = _PAIRING_CODE_RE.fullmatch(normalized)
    if match is None:
        raise BrowserBridgePairingExchangeFailed("pairing exchange failed")
    return normalized, match.group(1)


def _public_key(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {
        "algorithm",
        "encoding",
        "value",
    }:
        raise BrowserBridgePairingExchangeFailed("pairing exchange failed")
    if value.get("algorithm") != "Ed25519" or value.get("encoding") != "raw-base64url":
        raise BrowserBridgePairingExchangeFailed("pairing exchange failed")
    encoded = value.get("value")
    if not isinstance(encoded, str) or not _PUBLIC_KEY_RE.fullmatch(encoded):
        raise BrowserBridgePairingExchangeFailed("pairing exchange failed")
    try:
        decoded = base64.b64decode(encoded + "=", altchars=b"-_", validate=True)
    except (binascii.Error, ValueError) as error:
        raise BrowserBridgePairingExchangeFailed("pairing exchange failed") from error
    if len(decoded) != 32:
        raise BrowserBridgePairingExchangeFailed("pairing exchange failed")
    return {
        "algorithm": "Ed25519",
        "encoding": "raw-base64url",
        "value": encoded,
    }


def coarse_source_key(remote_address: Any) -> str:
    raw = str(remote_address or "").strip()
    try:
        address = ipaddress.ip_address(raw)
    except ValueError:
        source_class = "unknown"
    else:
        if address.is_loopback:
            source_class = "loopback"
        else:
            prefix = 24 if address.version == 4 else 64
            source_class = str(ipaddress.ip_network(f"{address}/{prefix}", strict=False))
    return hashlib.sha256(source_class.encode("ascii")).hexdigest()


class BrowserBridgeRecordRepository:
    """Atomic, bounded repository for public bridge credential records."""

    def __init__(
        self,
        *,
        load: Callable[[], Any] | None = None,
        save: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self._load = load or _load_default_records
        self._save = save or _save_default_records

    def active_record_present(self, *, server_instance_id: str | None = None) -> bool:
        records = self._validated_records()
        safe_server_id = (
            validate_identifier(server_instance_id, field_name="server_instance_id")
            if server_instance_id is not None
            else None
        )
        return any(
            record["state"] == "active"
            and (
                safe_server_id is None
                or record["server_instance_id"] == safe_server_id
            )
            for record in records
        )

    def active_record(
        self,
        *,
        bridge_id: Any,
        server_instance_id: Any,
    ) -> dict[str, Any] | None:
        safe_bridge_id = validate_identifier(bridge_id, field_name="bridge_id")
        safe_server_id = validate_identifier(
            server_instance_id,
            field_name="server_instance_id",
        )
        for record in self._validated_records():
            if (
                record["bridge_id"] == safe_bridge_id
                and record["server_instance_id"] == safe_server_id
                and record["state"] == "active"
            ):
                return record
        return None

    def list_public_records(
        self,
        *,
        server_instance_id: Any,
        subject_id: Any,
    ) -> list[BrowserBridgePublicRecord]:
        safe_server_id = validate_identifier(
            server_instance_id,
            field_name="server_instance_id",
        )
        safe_subject_id = validate_identifier(subject_id, field_name="subject_id")
        return sorted(
            (
                _public_bridge_record(record)
                for record in self._validated_records()
                if record["server_instance_id"] == safe_server_id
                and record["subject_id"] == safe_subject_id
            ),
            key=lambda record: (-record.created_at_ms, record.bridge_id),
        )

    def public_record(
        self,
        *,
        bridge_id: Any,
        server_instance_id: Any,
        subject_id: Any,
    ) -> BrowserBridgePublicRecord | None:
        safe_bridge_id = validate_identifier(bridge_id, field_name="bridge_id")
        for record in self.list_public_records(
            server_instance_id=server_instance_id,
            subject_id=subject_id,
        ):
            if record.bridge_id == safe_bridge_id:
                return record
        return None

    def revoke(
        self,
        *,
        bridge_id: Any,
        server_instance_id: Any,
        subject_id: Any,
        revoked_at_ms: Any,
    ) -> BrowserBridgeRevocation | None:
        safe_bridge_id = validate_identifier(bridge_id, field_name="bridge_id")
        safe_server_id = validate_identifier(
            server_instance_id,
            field_name="server_instance_id",
        )
        safe_subject_id = validate_identifier(subject_id, field_name="subject_id")
        if type(revoked_at_ms) is not int or revoked_at_ms < 0:
            raise BrowserBridgePairingUnavailable("invalid revocation time")

        records = self._validated_records()
        matched: dict[str, Any] | None = None
        already_revoked = False
        updated: list[dict[str, Any]] = []
        for record in records:
            candidate = dict(record)
            if (
                candidate["bridge_id"] == safe_bridge_id
                and candidate["server_instance_id"] == safe_server_id
                and candidate["subject_id"] == safe_subject_id
            ):
                already_revoked = candidate["state"] == "revoked"
                if not already_revoked:
                    candidate["state"] = "revoked"
                    candidate["revoked_at_ms"] = revoked_at_ms
                    candidate.pop("rotation", None)
                matched = candidate
            updated.append(candidate)
        if matched is None:
            return None
        if not already_revoked:
            self._save(
                {
                    "schema_version": BROWSER_BRIDGE_RECORD_SCHEMA_VERSION,
                    "bridges": updated,
                }
            )
        return BrowserBridgeRevocation(
            bridge=_public_bridge_record(matched),
            already_revoked=already_revoked,
        )

    def mark_authenticated(
        self,
        *,
        bridge_id: Any,
        key_generation: Any,
        authenticated_at_ms: Any,
    ) -> None:
        safe_bridge_id = validate_identifier(bridge_id, field_name="bridge_id")
        if type(key_generation) is not int or key_generation < 1:
            raise BrowserBridgePairingUnavailable("invalid key generation")
        if type(authenticated_at_ms) is not int or authenticated_at_ms < 0:
            raise BrowserBridgePairingUnavailable("invalid authentication time")

        records = self._validated_records()
        matched = False
        updated: list[dict[str, Any]] = []
        for record in records:
            candidate = dict(record)
            if (
                candidate["bridge_id"] == safe_bridge_id
                and candidate["key_generation"] == key_generation
                and candidate["state"] == "active"
            ):
                candidate["last_authenticated_at_ms"] = authenticated_at_ms
                matched = True
            updated.append(candidate)
        if not matched:
            raise BrowserBridgePairingUnavailable("active bridge record unavailable")
        self._save(
            {
                "schema_version": BROWSER_BRIDGE_RECORD_SCHEMA_VERSION,
                "bridges": updated,
            }
        )

    def add(self, record: dict[str, Any]) -> None:
        records = self._validated_records()
        if len(records) >= MAX_BRIDGE_RECORDS:
            raise BrowserBridgePairingUnavailable("bridge record limit reached")
        validated = _validated_bridge_record(record)
        if any(
            existing["bridge_id"] == validated["bridge_id"]
            for existing in records
        ):
            raise BrowserBridgePairingUnavailable("bridge identity collision")
        records.append(validated)
        self._save(
            {
                "schema_version": BROWSER_BRIDGE_RECORD_SCHEMA_VERSION,
                "bridges": records,
            }
        )

    def _validated_records(self) -> list[dict[str, Any]]:
        document = self._load()
        if document in (None, {}):
            return []
        if (
            not isinstance(document, Mapping)
            or set(document) != {"schema_version", "bridges"}
            or document.get("schema_version") != BROWSER_BRIDGE_RECORD_SCHEMA_VERSION
            or not isinstance(document.get("bridges"), list)
            or len(document["bridges"]) > MAX_BRIDGE_RECORDS
        ):
            raise BrowserBridgePairingUnavailable("invalid bridge record store")
        records = [_validated_bridge_record(record) for record in document["bridges"]]
        bridge_ids = [record["bridge_id"] for record in records]
        if len(set(bridge_ids)) != len(bridge_ids):
            raise BrowserBridgePairingUnavailable("invalid bridge record store")
        return records


def _validated_bridge_record(value: Any) -> dict[str, Any]:
    required = {
        "trust_version",
        "bridge_id",
        "server_instance_id",
        "subject_id",
        "display_name",
        "companion_instance_id",
        "extension_id",
        "public_key",
        "key_generation",
        "scopes",
        "state",
        "created_at_ms",
        "last_authenticated_at_ms",
        "revoked_at_ms",
    }
    if not isinstance(value, Mapping) or set(value) not in (required, required | {"rotation"}):
        raise BrowserBridgePairingUnavailable("invalid bridge record")
    if (
        value.get("trust_version") != BROWSER_BRIDGE_TRUST_VERSION
        or value.get("subject_id") != SUBJECT_ID
        or type(value.get("key_generation")) is not int
        or not 1 <= value["key_generation"] <= 2_147_483_647
        or value.get("state") not in {"active", "revoked"}
        or value.get("scopes") != list(FIXED_BROWSER_BRIDGE_SCOPES)
        or type(value.get("created_at_ms")) is not int
        or value.get("created_at_ms", -1) < 0
        or (
            value.get("last_authenticated_at_ms") is not None
            and (
                type(value.get("last_authenticated_at_ms")) is not int
                or value.get("last_authenticated_at_ms") < 0
            )
        )
        or (
            value.get("revoked_at_ms") is not None
            and (
                type(value.get("revoked_at_ms")) is not int
                or value.get("revoked_at_ms") < 0
            )
        )
        or (value.get("state") == "active" and value.get("revoked_at_ms") is not None)
        or (value.get("state") == "revoked" and value.get("revoked_at_ms") is None)
    ):
        raise BrowserBridgePairingUnavailable("invalid bridge record")
    try:
        result = {
            "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
            "bridge_id": validate_identifier(value.get("bridge_id"), field_name="bridge_id"),
            "server_instance_id": validate_identifier(
                value.get("server_instance_id"),
                field_name="server_instance_id",
            ),
            "subject_id": SUBJECT_ID,
            "display_name": validate_display_name(value.get("display_name")),
            "companion_instance_id": validate_identifier(
                value.get("companion_instance_id"),
                field_name="companion_instance_id",
            ),
            "extension_id": validate_extension_id(value.get("extension_id")),
            "public_key": _public_key(value.get("public_key")),
            "key_generation": value["key_generation"],
            "scopes": list(FIXED_BROWSER_BRIDGE_SCOPES),
            "state": value["state"],
            "created_at_ms": value["created_at_ms"],
            "last_authenticated_at_ms": value["last_authenticated_at_ms"],
            "revoked_at_ms": value["revoked_at_ms"],
        }
    except BrowserBridgePairingError as error:
        raise BrowserBridgePairingUnavailable("invalid bridge record") from error
    if "rotation" in value:
        from plugins._a0_connector.helpers.browser_bridge_credentials import validate_rotation
        result["rotation"] = validate_rotation(value["rotation"], result)
    return result


def _public_bridge_record(record: Mapping[str, Any]) -> BrowserBridgePublicRecord:
    """Project only already-validated, non-authorizing presentation fields."""
    return BrowserBridgePublicRecord(
        bridge_id=record["bridge_id"],
        display_name=record["display_name"],
        state=record["state"],
        key_generation=record["key_generation"],
        created_at_ms=record["created_at_ms"],
        last_authenticated_at_ms=record["last_authenticated_at_ms"],
        revoked_at_ms=record["revoked_at_ms"],
    )


def _load_default_records() -> Any:
    from helpers import kvp

    return kvp.get_persistent(BROWSER_BRIDGE_RECORD_STORE_KEY, None)


def _save_default_records(value: dict[str, Any]) -> None:
    from helpers import kvp

    kvp.set_persistent(BROWSER_BRIDGE_RECORD_STORE_KEY, value)


class BrowserBridgePairingStore:
    """Thread-safe pending-pairing and single-use exchange store."""

    def __init__(
        self,
        *,
        repository: BrowserBridgeRecordRepository | None = None,
        clock_ms: Callable[[], int] = _now_ms,
        random_bytes: Callable[[int], bytes] = secrets.token_bytes,
        id_factory: Callable[[], str] = _random_uuid,
    ) -> None:
        self._repository = repository or BrowserBridgeRecordRepository()
        self._clock_ms = clock_ms
        self._random_bytes = random_bytes
        self._id_factory = id_factory
        self._pending: dict[str, _PendingPairing] = {}
        self._owner_pairing: dict[str, str] = {}
        self._source_rates: dict[str, _SourceRate] = {}
        self._lock = threading.RLock()

    def create(
        self,
        *,
        owner_id: str,
        server_instance_id: str,
        server_base_url: str,
        extension_id: str,
        display_name: str,
    ) -> PairingCreation:
        safe_owner = validate_identifier(owner_id, field_name="owner_id")
        safe_server_id = validate_identifier(
            server_instance_id,
            field_name="server_instance_id",
        )
        safe_base_url = normalize_server_base_url(server_base_url)
        safe_extension_id = validate_extension_id(extension_id)
        safe_display_name = validate_display_name(display_name)
        now = self._clock_ms()
        with self._lock:
            self._expire_locked(now)
            previous = self._owner_pairing.pop(safe_owner, None)
            if previous:
                self._pending.pop(previous, None)
            while len(self._pending) >= MAX_PENDING_PAIRINGS:
                oldest = min(
                    self._pending.values(),
                    key=lambda pending: (pending.created_at_ms, pending.pairing_id),
                )
                self._remove_pending_locked(oldest)

            pairing_id = self._new_unique_pairing_id_locked()
            prefix = pairing_id.replace("-", "")[:8].upper()
            entropy = self._random_bytes(PAIRING_SECRET_BYTES)
            if not isinstance(entropy, bytes) or len(entropy) != PAIRING_SECRET_BYTES:
                raise BrowserBridgePairingUnavailable("secure entropy unavailable")
            code = f"A0B1-{prefix}-{_encode_crockford(entropy)}"
            pending = _PendingPairing(
                pairing_id=pairing_id,
                pairing_prefix=prefix,
                owner_id=safe_owner,
                secret_digest=hashlib.sha256(code.encode("ascii")).digest(),
                server_instance_id=safe_server_id,
                server_base_url=safe_base_url,
                extension_id=safe_extension_id,
                display_name=safe_display_name,
                created_at_ms=now,
                expires_at_ms=now + PAIRING_TTL_MS,
            )
            self._pending[pairing_id] = pending
            self._owner_pairing[safe_owner] = pairing_id

        return PairingCreation(
            pairing_id=pairing_id,
            pairing_code=code,
            server_base_url=safe_base_url,
            server_instance_fingerprint=server_instance_fingerprint(safe_server_id),
            extension_id=safe_extension_id,
            display_name=safe_display_name,
            created_at_ms=now,
            expires_at_ms=now + PAIRING_TTL_MS,
        )

    def status(
        self,
        *,
        owner_id: str | None,
        server_instance_id: str | None = None,
    ) -> dict[str, Any]:
        now = self._clock_ms()
        with self._lock:
            self._expire_locked(now)
            pending = self._pending_for_owner_locked(owner_id)
            try:
                paired = self._repository.active_record_present(
                    server_instance_id=server_instance_id
                )
            except BrowserBridgePairingUnavailable:
                return _pairing_status(
                    state="repair_required",
                    reason_code="bridge_record_store_invalid",
                )
            if pending is not None:
                return _pairing_status(
                    state="pairing_pending",
                    reason_code="pairing_intent_active",
                    pairing_id=pending.pairing_id,
                    expires_at_ms=pending.expires_at_ms,
                    server_base_url=pending.server_base_url,
                    extension_id=pending.extension_id,
                    display_name=pending.display_name,
                )
            return _pairing_status(
                state="paired" if paired else "unpaired",
                reason_code=(
                    "active_bridge_record_present"
                    if paired
                    else "no_active_bridge_record"
                ),
            )

    def cancel(self, *, owner_id: str | None, pairing_id: Any) -> bool:
        if owner_id is None:
            return False
        try:
            safe_owner = validate_identifier(owner_id, field_name="owner_id")
            safe_pairing_id = validate_identifier(
                pairing_id,
                field_name="pairing_id",
            )
        except BrowserBridgePairingError:
            return False
        now = self._clock_ms()
        with self._lock:
            self._expire_locked(now)
            pending = self._pending.get(safe_pairing_id)
            if pending is None or pending.owner_id != safe_owner:
                return False
            self._remove_pending_locked(pending)
            return True

    def active_bridge_record(
        self,
        *,
        bridge_id: Any,
        server_instance_id: Any,
    ) -> dict[str, Any] | None:
        with self._lock:
            return self._repository.active_record(
                bridge_id=bridge_id,
                server_instance_id=server_instance_id,
            )

    def list_bridge_records(
        self,
        *,
        server_instance_id: Any,
        subject_id: Any,
    ) -> list[BrowserBridgePublicRecord]:
        with self._lock:
            return self._repository.list_public_records(
                server_instance_id=server_instance_id,
                subject_id=subject_id,
            )

    def bridge_record(
        self,
        *,
        bridge_id: Any,
        server_instance_id: Any,
        subject_id: Any,
    ) -> BrowserBridgePublicRecord | None:
        with self._lock:
            return self._repository.public_record(
                bridge_id=bridge_id,
                server_instance_id=server_instance_id,
                subject_id=subject_id,
            )

    def revoke_bridge(
        self,
        *,
        bridge_id: Any,
        server_instance_id: Any,
        subject_id: Any,
    ) -> BrowserBridgeRevocation | None:
        # This is intentionally the same lock used by exchange and
        # mark_bridge_authenticated. Once this call returns, neither a stale
        # proof nor an overlapping record write can restore active state.
        with self._lock:
            return self._repository.revoke(
                bridge_id=bridge_id,
                server_instance_id=server_instance_id,
                subject_id=subject_id,
                revoked_at_ms=self._clock_ms(),
            )

    def mark_bridge_authenticated(
        self,
        *,
        bridge_id: Any,
        key_generation: Any,
        authenticated_at_ms: Any,
    ) -> None:
        with self._lock:
            self._repository.mark_authenticated(
                bridge_id=bridge_id,
                key_generation=key_generation,
                authenticated_at_ms=authenticated_at_ms,
            )

    def exchange(
        self,
        request: Any,
        *,
        source_key: str,
    ) -> PairingExchangeSuccess:
        now = self._clock_ms()
        with self._lock:
            self._expire_locked(now)
            if not self._allow_source_locked(source_key, now):
                raise BrowserBridgePairingExchangeFailed("pairing exchange failed")
            try:
                data = request if isinstance(request, Mapping) else {}
                code, prefix = _normalize_pairing_code(data.get("pairing_code"))
            except BrowserBridgePairingExchangeFailed:
                raise

            pending = next(
                (
                    candidate
                    for candidate in self._pending.values()
                    if candidate.pairing_prefix == prefix
                ),
                None,
            )
            if pending is None:
                raise BrowserBridgePairingExchangeFailed("pairing exchange failed")

            try:
                success = self._matches_exchange_locked(pending, data, code)
            except BrowserBridgePairingError:
                success = False
            if not success:
                pending.failed_exchanges += 1
                if pending.failed_exchanges >= PAIRING_MAX_FAILED_EXCHANGES:
                    self._remove_pending_locked(pending)
                raise BrowserBridgePairingExchangeFailed("pairing exchange failed")

            public_key = _public_key(data.get("public_key"))
            companion_instance_id = validate_identifier(
                data.get("companion_instance_id"),
                field_name="companion_instance_id",
            )
            bridge_id = validate_identifier(
                self._id_factory(),
                field_name="bridge_id",
            )
            record = {
                "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
                "bridge_id": bridge_id,
                "server_instance_id": pending.server_instance_id,
                "subject_id": SUBJECT_ID,
                "display_name": pending.display_name,
                "companion_instance_id": companion_instance_id,
                "extension_id": pending.extension_id,
                "public_key": public_key,
                "key_generation": 1,
                "scopes": list(FIXED_BROWSER_BRIDGE_SCOPES),
                "state": "active",
                "created_at_ms": now,
                "last_authenticated_at_ms": None,
                "revoked_at_ms": None,
            }
            self._repository.add(record)
            self._remove_pending_locked(pending)
            return PairingExchangeSuccess(
                bridge_id=bridge_id,
                server_instance_id=pending.server_instance_id,
                server_base_url=pending.server_base_url,
                extension_id=pending.extension_id,
                display_name=pending.display_name,
                created_at_ms=now,
            )

    def _matches_exchange_locked(
        self,
        pending: _PendingPairing,
        data: Mapping[str, Any],
        code: str,
    ) -> bool:
        if set(data) != {
            "trust_version",
            "pairing_code",
            "server_base_url",
            "extension_id",
            "companion_instance_id",
            "public_key",
        }:
            return False
        if type(data.get("trust_version")) is not int or data.get("trust_version") != 1:
            return False
        supplied_digest = hashlib.sha256(code.encode("ascii")).digest()
        if not hmac.compare_digest(supplied_digest, pending.secret_digest):
            return False
        if normalize_server_base_url(data.get("server_base_url")) != pending.server_base_url:
            return False
        if validate_extension_id(data.get("extension_id")) != pending.extension_id:
            return False
        validate_identifier(
            data.get("companion_instance_id"),
            field_name="companion_instance_id",
        )
        _public_key(data.get("public_key"))
        return True

    def _new_unique_pairing_id_locked(self) -> str:
        for _ in range(16):
            pairing_id = validate_identifier(
                self._id_factory(),
                field_name="pairing_id",
            )
            prefix = pairing_id.replace("-", "")[:8].upper()
            if len(prefix) == 8 and re.fullmatch(r"[0-9A-F]{8}", prefix) and all(
                candidate.pairing_prefix != prefix
                for candidate in self._pending.values()
            ):
                return pairing_id
        raise BrowserBridgePairingUnavailable("pairing identity unavailable")

    def _pending_for_owner_locked(
        self,
        owner_id: str | None,
    ) -> _PendingPairing | None:
        if not owner_id:
            return None
        pairing_id = self._owner_pairing.get(owner_id)
        return self._pending.get(pairing_id) if pairing_id else None

    def _remove_pending_locked(self, pending: _PendingPairing) -> None:
        self._pending.pop(pending.pairing_id, None)
        if self._owner_pairing.get(pending.owner_id) == pending.pairing_id:
            self._owner_pairing.pop(pending.owner_id, None)

    def _expire_locked(self, now: int) -> None:
        for pending in tuple(self._pending.values()):
            if pending.expires_at_ms <= now:
                self._remove_pending_locked(pending)
        for key, rate in tuple(self._source_rates.items()):
            if rate.window_started_at_ms + SOURCE_RATE_WINDOW_MS <= now:
                self._source_rates.pop(key, None)

    def _allow_source_locked(self, source_key: str, now: int) -> bool:
        safe_key = validate_identifier(source_key, field_name="source_key")
        rate = self._source_rates.get(safe_key)
        if rate is None or rate.window_started_at_ms + SOURCE_RATE_WINDOW_MS <= now:
            if len(self._source_rates) >= MAX_SOURCE_BUCKETS:
                oldest_key = min(
                    self._source_rates,
                    key=lambda key: self._source_rates[key].window_started_at_ms,
                )
                self._source_rates.pop(oldest_key, None)
            self._source_rates[safe_key] = _SourceRate(now, 1)
            return True
        rate.attempts += 1
        return rate.attempts <= SOURCE_RATE_MAX_EXCHANGES


def _pairing_status(
    *,
    state: str,
    reason_code: str,
    pairing_id: str | None = None,
    expires_at_ms: int | None = None,
    server_base_url: str | None = None,
    extension_id: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    pending = state == "pairing_pending"
    return {
        "contract": BROWSER_BRIDGE_TRUST_CONTRACT,
        "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
        "state": state,
        "reason_code": reason_code,
        "pairing_id": pairing_id if pending else None,
        "server_base_url": server_base_url if pending else None,
        "extension_id": extension_id if pending else None,
        "display_name": display_name if pending else None,
        "expires_at_ms": expires_at_ms if pending else None,
        "pairing_code_present": False,
        "native_runtime_location": "user_browser_host",
        "docker_install_target": False,
        "connector_session_ready": False,
        "browser_control_ready": False,
    }


def build_browser_bridge_pairing_foundation_status(
    gate: BrowserBridgeGate,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    extension_configured = configured_extension_id(environ=environ) is not None
    create_enabled = gate.state in {"preview", "available"} and extension_configured
    if gate.state == "disabled":
        reason_code = "rollout_disabled"
    elif not extension_configured:
        reason_code = "expected_extension_id_not_configured"
    else:
        reason_code = "pairing_endpoint_available"
    return {
        "contract": BROWSER_BRIDGE_TRUST_CONTRACT,
        "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
        "state": "available" if create_enabled else "disabled",
        "reason_code": reason_code,
        "pairing_create_enabled": create_enabled,
        "pairing_exchange_enabled": create_enabled,
        "connector_session_ready": False,
        "browser_control_ready": False,
        "native_runtime_location": "user_browser_host",
        "docker_install_target": False,
    }


_store: BrowserBridgePairingStore | None = None
_store_lock = threading.Lock()


def get_browser_bridge_pairing_store() -> BrowserBridgePairingStore:
    global _store
    with _store_lock:
        if _store is None:
            _store = BrowserBridgePairingStore()
        return _store


PAIRING_OWNER_SESSION_KEY = "browser_bridge_pairing_owner_v1"


def pairing_owner_id(
    session_state: MutableMapping[str, Any],
    *,
    create: bool,
) -> str | None:
    current = session_state.get(PAIRING_OWNER_SESSION_KEY)
    try:
        if current is not None:
            return validate_identifier(current, field_name="pairing owner")
    except BrowserBridgePairingError:
        session_state.pop(PAIRING_OWNER_SESSION_KEY, None)
    if not create:
        return None
    owner = secrets.token_urlsafe(24)
    session_state[PAIRING_OWNER_SESSION_KEY] = owner
    return owner
