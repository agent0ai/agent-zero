"""One-time Ed25519 proof foundation for Browser bridge connector sessions.

Challenge material is bounded process memory only. Successful verification
returns a scoped principal projection; it does not activate a WebSocket handler.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from plugins._a0_connector.helpers.browser_bridge_pairing import (
    BROWSER_BRIDGE_TRUST_VERSION,
    CONNECTOR_PROTOCOL,
    BrowserBridgePairingError,
    BrowserBridgePairingUnavailable,
    get_browser_bridge_pairing_store,
    normalize_server_base_url,
    validate_identifier,
)


BRIDGE_CONNECTOR_HANDLER = "plugins/_a0_connector/ws_connector"
CHALLENGE_TTL_MS = 60 * 1000
CHALLENGE_NONCE_BYTES = 32
CHALLENGE_SIGNATURE_BYTES = 64
MAX_PENDING_CHALLENGES = 256
CHALLENGE_SOURCE_RATE_WINDOW_MS = 60 * 1000
CHALLENGE_SOURCE_RATE_MAX = 20
MAX_CHALLENGE_SOURCE_BUCKETS = 256

_BASE64URL_32_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_BASE64URL_64_RE = re.compile(r"^[A-Za-z0-9_-]{86}$")
_PROOF_KEYS = {
    "aud",
    "bridge_id",
    "challenge_id",
    "client_nonce",
    "handler",
    "protocol",
    "server_base_url",
    "server_nonce",
    "trust_version",
}


class BrowserBridgeAuthError(ValueError):
    """Internal proof error; public callers must return a generic failure."""


class BrowserBridgeChallengeFailed(BrowserBridgeAuthError):
    pass


class BrowserBridgeChallengeUnavailable(BrowserBridgeAuthError):
    pass


@dataclass(frozen=True, slots=True)
class BrowserBridgeChallenge:
    challenge_id: str
    server_nonce: str = field(repr=False)
    server_instance_id: str = field(repr=False)
    server_base_url: str
    expires_at_ms: int

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
            "challenge_id": self.challenge_id,
            "server_nonce": self.server_nonce,
            "server_instance_id": self.server_instance_id,
            "server_base_url": self.server_base_url,
            "expires_at_ms": self.expires_at_ms,
        }


@dataclass(frozen=True, slots=True)
class BrowserBridgePrincipal:
    principal_type: str
    bridge_id: str
    server_instance_id: str
    subject_id: str
    extension_id: str
    companion_instance_id: str
    key_generation: int
    scopes: tuple[str, ...]
    authenticated_at_ms: int

    def as_security_context_dict(self) -> dict[str, Any]:
        return {
            "principal_type": self.principal_type,
            "bridge_id": self.bridge_id,
            "server_instance_id": self.server_instance_id,
            "subject_id": self.subject_id,
            "extension_id": self.extension_id,
            "companion_instance_id": self.companion_instance_id,
            "key_generation": self.key_generation,
            "scopes": list(self.scopes),
            "authenticated_at_ms": self.authenticated_at_ms,
        }


@dataclass(slots=True)
class _PendingChallenge:
    challenge_id: str
    bridge_id: str
    client_nonce: str = field(repr=False)
    server_nonce: str = field(repr=False)
    server_instance_id: str = field(repr=False)
    server_base_url: str
    created_at_ms: int
    expires_at_ms: int


@dataclass(slots=True)
class _SourceRate:
    window_started_at_ms: int
    attempts: int


def _now_ms() -> int:
    return int(time.time() * 1000)


def _random_uuid() -> str:
    return str(uuid.uuid4())


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode_base64url(value: Any, *, size: int) -> bytes:
    pattern = _BASE64URL_32_RE if size == 32 else _BASE64URL_64_RE
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise BrowserBridgeChallengeFailed("bridge authentication failed")
    try:
        decoded = base64.b64decode(
            value + ("=" if size == 32 else "=="),
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError) as error:
        raise BrowserBridgeChallengeFailed("bridge authentication failed") from error
    if len(decoded) != size:
        raise BrowserBridgeChallengeFailed("bridge authentication failed")
    return decoded


def canonical_proof_bytes(proof: Any) -> bytes:
    """Return RFC 8785-equivalent bytes for the fixed scalar-only v1 proof."""

    if not isinstance(proof, Mapping) or set(proof) != _PROOF_KEYS:
        raise BrowserBridgeChallengeFailed("bridge authentication failed")
    if (
        type(proof.get("trust_version")) is not int
        or proof.get("trust_version") != BROWSER_BRIDGE_TRUST_VERSION
    ):
        raise BrowserBridgeChallengeFailed("bridge authentication failed")
    try:
        for key in {
            "aud",
            "bridge_id",
            "challenge_id",
            "handler",
            "protocol",
        }:
            validate_identifier(proof.get(key), field_name=key)
        normalize_server_base_url(proof.get("server_base_url"))
        _decode_base64url(proof.get("client_nonce"), size=CHALLENGE_NONCE_BYTES)
        _decode_base64url(proof.get("server_nonce"), size=CHALLENGE_NONCE_BYTES)
    except BrowserBridgePairingError as error:
        raise BrowserBridgeChallengeFailed("bridge authentication failed") from error
    try:
        return json.dumps(
            dict(proof),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise BrowserBridgeChallengeFailed("bridge authentication failed") from error


class BrowserBridgeChallengeStore:
    """Issue and atomically consume bounded one-time connector challenges."""

    def __init__(
        self,
        *,
        record_lookup: Callable[[str, str], dict[str, Any] | None] | None = None,
        record_authenticated: Callable[[str, int, int], None] | None = None,
        record_candidates: Callable[[str, str], tuple[dict[str, Any], ...]] | None = None,
        record_verified: Callable[[dict[str, Any], int], None] | None = None,
        clock_ms: Callable[[], int] = _now_ms,
        random_bytes: Callable[[int], bytes] = secrets.token_bytes,
        id_factory: Callable[[], str] = _random_uuid,
    ) -> None:
        self._record_lookup = record_lookup or _active_record
        self._record_authenticated = record_authenticated or _mark_authenticated
        if (record_candidates is None) != (record_verified is None):
            raise TypeError("candidate lookup and verified-key commit must be paired")
        default_owner = record_lookup is None and record_authenticated is None
        self._record_candidates = record_candidates or (_authentication_records if default_owner else None)
        self._record_verified = record_verified or (_accept_verified_key if default_owner else None)
        self._clock_ms = clock_ms
        self._random_bytes = random_bytes
        self._id_factory = id_factory
        self._pending: dict[str, _PendingChallenge] = {}
        self._source_rates: dict[str, _SourceRate] = {}
        self._lock = threading.RLock()

    def issue(
        self,
        request: Any,
        *,
        source_key: str,
        server_instance_id: Any,
        server_base_url: Any,
    ) -> BrowserBridgeChallenge:
        now = self._clock_ms()
        with self._lock:
            self._expire_locked(now)
            if not self._allow_source_locked(source_key, now):
                raise BrowserBridgeChallengeFailed("bridge challenge failed")
            if not isinstance(request, Mapping) or set(request) != {
                "trust_version",
                "bridge_id",
                "client_nonce",
            }:
                raise BrowserBridgeChallengeFailed("bridge challenge failed")
            if (
                type(request.get("trust_version")) is not int
                or request.get("trust_version") != BROWSER_BRIDGE_TRUST_VERSION
            ):
                raise BrowserBridgeChallengeFailed("bridge challenge failed")
            try:
                bridge_id = validate_identifier(
                    request.get("bridge_id"),
                    field_name="bridge_id",
                )
                safe_server_id = validate_identifier(
                    server_instance_id,
                    field_name="server_instance_id",
                )
                safe_base_url = normalize_server_base_url(server_base_url)
                client_nonce = request.get("client_nonce")
                _decode_base64url(client_nonce, size=CHALLENGE_NONCE_BYTES)
                record = self._record_lookup(bridge_id, safe_server_id)
            except (BrowserBridgePairingError, BrowserBridgePairingUnavailable):
                raise BrowserBridgeChallengeFailed("bridge challenge failed")
            except BrowserBridgeChallengeFailed:
                raise
            except Exception as error:
                raise BrowserBridgeChallengeUnavailable(
                    "bridge challenge unavailable"
                ) from error
            if record is None:
                raise BrowserBridgeChallengeFailed("bridge challenge failed")
            if len(self._pending) >= MAX_PENDING_CHALLENGES:
                raise BrowserBridgeChallengeUnavailable("bridge challenge unavailable")

            challenge_id = validate_identifier(
                self._id_factory(),
                field_name="challenge_id",
            )
            if challenge_id in self._pending:
                raise BrowserBridgeChallengeUnavailable("challenge identity collision")
            entropy = self._random_bytes(CHALLENGE_NONCE_BYTES)
            if not isinstance(entropy, bytes) or len(entropy) != CHALLENGE_NONCE_BYTES:
                raise BrowserBridgeChallengeUnavailable("secure entropy unavailable")
            server_nonce = _base64url(entropy)
            pending = _PendingChallenge(
                challenge_id=challenge_id,
                bridge_id=bridge_id,
                client_nonce=client_nonce,
                server_nonce=server_nonce,
                server_instance_id=safe_server_id,
                server_base_url=safe_base_url,
                created_at_ms=now,
                expires_at_ms=now + CHALLENGE_TTL_MS,
            )
            self._pending[challenge_id] = pending
            return BrowserBridgeChallenge(
                challenge_id=challenge_id,
                server_nonce=server_nonce,
                server_instance_id=safe_server_id,
                server_base_url=safe_base_url,
                expires_at_ms=pending.expires_at_ms,
            )

    def verify(self, *, proof: Any, signature: Any) -> BrowserBridgePrincipal:
        now = self._clock_ms()
        with self._lock:
            self._expire_locked(now)
            if not isinstance(proof, Mapping):
                raise BrowserBridgeChallengeFailed("bridge authentication failed")
            raw_challenge_id = proof.get("challenge_id")
            try:
                challenge_id = validate_identifier(
                    raw_challenge_id,
                    field_name="challenge_id",
                )
            except BrowserBridgePairingError as error:
                raise BrowserBridgeChallengeFailed(
                    "bridge authentication failed"
                ) from error
            pending = self._pending.pop(challenge_id, None)
            if pending is None:
                raise BrowserBridgeChallengeFailed("bridge authentication failed")

            try:
                record = self._record_lookup(
                    pending.bridge_id,
                    pending.server_instance_id,
                )
                if record is None or not self._matches_pending(proof, pending):
                    raise BrowserBridgeChallengeFailed("bridge authentication failed")
                signature_bytes = _decode_base64url(
                    signature,
                    size=CHALLENGE_SIGNATURE_BYTES,
                )
                candidates = self._record_candidates(pending.bridge_id, pending.server_instance_id) if self._record_candidates else (record,)
                if not isinstance(candidates, tuple) or not 1 <= len(candidates) <= 2:
                    raise BrowserBridgeChallengeFailed("bridge authentication failed")
                message = canonical_proof_bytes(proof)
                verified = None
                for candidate in candidates:
                    if any(candidate.get(k) != record.get(k) for k in ("bridge_id", "server_instance_id", "subject_id", "extension_id", "companion_instance_id", "scopes")):
                        raise BrowserBridgeChallengeFailed("bridge authentication failed")
                    try:
                        _verify_ed25519(_decode_public_key(candidate.get("public_key")), signature_bytes, message)
                    except BrowserBridgeChallengeFailed:
                        continue
                    verified = candidate
                    break
                if verified is None:
                    raise BrowserBridgeChallengeFailed("bridge authentication failed")
                record = verified
                authenticated_at_ms = self._clock_ms()
                if self._record_verified:
                    self._record_verified(record, authenticated_at_ms)
                else:
                    self._record_authenticated(pending.bridge_id, record["key_generation"], authenticated_at_ms)
            except BrowserBridgeChallengeFailed:
                raise
            except Exception as error:
                raise BrowserBridgeChallengeFailed(
                    "bridge authentication failed"
                ) from error

            return BrowserBridgePrincipal(
                principal_type="browser_bridge",
                bridge_id=record["bridge_id"],
                server_instance_id=record["server_instance_id"],
                subject_id=record["subject_id"],
                extension_id=record["extension_id"],
                companion_instance_id=record["companion_instance_id"],
                key_generation=record["key_generation"],
                scopes=tuple(record["scopes"]),
                authenticated_at_ms=authenticated_at_ms,
            )

    def invalidate_bridge(self, bridge_id: str, server_instance_id: str) -> None:
        with self._lock:
            for challenge_id, pending in tuple(self._pending.items()):
                if pending.bridge_id == bridge_id and pending.server_instance_id == server_instance_id:
                    self._pending.pop(challenge_id, None)

    @staticmethod
    def _matches_pending(proof: Mapping[str, Any], pending: _PendingChallenge) -> bool:
        if set(proof) != _PROOF_KEYS:
            return False
        if type(proof.get("trust_version")) is not int:
            return False
        try:
            normalized_base_url = normalize_server_base_url(
                proof.get("server_base_url")
            )
        except BrowserBridgePairingError:
            return False
        return (
            proof.get("trust_version") == BROWSER_BRIDGE_TRUST_VERSION
            and proof.get("aud") == pending.server_instance_id
            and proof.get("bridge_id") == pending.bridge_id
            and proof.get("challenge_id") == pending.challenge_id
            and proof.get("client_nonce") == pending.client_nonce
            and proof.get("handler") == BRIDGE_CONNECTOR_HANDLER
            and proof.get("protocol") == CONNECTOR_PROTOCOL
            and normalized_base_url == pending.server_base_url
            and proof.get("server_nonce") == pending.server_nonce
        )

    def _expire_locked(self, now: int) -> None:
        for challenge_id, pending in tuple(self._pending.items()):
            if pending.expires_at_ms <= now:
                self._pending.pop(challenge_id, None)
        for source_key, rate in tuple(self._source_rates.items()):
            if rate.window_started_at_ms + CHALLENGE_SOURCE_RATE_WINDOW_MS <= now:
                self._source_rates.pop(source_key, None)

    def _allow_source_locked(self, source_key: Any, now: int) -> bool:
        try:
            safe_source = validate_identifier(source_key, field_name="source_key")
        except BrowserBridgePairingError as error:
            raise BrowserBridgeChallengeFailed("bridge challenge failed") from error
        rate = self._source_rates.get(safe_source)
        if (
            rate is None
            or rate.window_started_at_ms + CHALLENGE_SOURCE_RATE_WINDOW_MS <= now
        ):
            if len(self._source_rates) >= MAX_CHALLENGE_SOURCE_BUCKETS:
                oldest = min(
                    self._source_rates,
                    key=lambda key: self._source_rates[key].window_started_at_ms,
                )
                self._source_rates.pop(oldest, None)
            self._source_rates[safe_source] = _SourceRate(now, 1)
            return True
        rate.attempts += 1
        return rate.attempts <= CHALLENGE_SOURCE_RATE_MAX


def _decode_public_key(value: Any) -> bytes:
    if not isinstance(value, Mapping) or set(value) != {
        "algorithm",
        "encoding",
        "value",
    }:
        raise BrowserBridgeChallengeFailed("bridge authentication failed")
    if value.get("algorithm") != "Ed25519" or value.get("encoding") != "raw-base64url":
        raise BrowserBridgeChallengeFailed("bridge authentication failed")
    return _decode_base64url(value.get("value"), size=CHALLENGE_NONCE_BYTES)


def _verify_ed25519(public_key: bytes, signature: bytes, message: bytes) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
    except Exception as error:
        raise BrowserBridgeChallengeUnavailable(
            "bridge authentication unavailable"
        ) from error
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except InvalidSignature as error:
        raise BrowserBridgeChallengeFailed("bridge authentication failed") from error
    except Exception as error:
        raise BrowserBridgeChallengeUnavailable(
            "bridge authentication unavailable"
        ) from error


def _active_record(bridge_id: str, server_instance_id: str) -> dict[str, Any] | None:
    return get_browser_bridge_pairing_store().active_bridge_record(
        bridge_id=bridge_id,
        server_instance_id=server_instance_id,
    )


def _authentication_records(bridge_id: str, server_instance_id: str) -> tuple[dict[str, Any], ...]:
    from plugins._a0_connector.helpers.browser_bridge_credentials import get_browser_bridge_credential_store
    return get_browser_bridge_credential_store().authentication_records(bridge_id, server_instance_id)


def _accept_verified_key(record: dict[str, Any], authenticated_at_ms: int) -> None:
    from plugins._a0_connector.helpers.browser_bridge_credentials import get_browser_bridge_credential_store
    get_browser_bridge_credential_store().accept_verified_key(record, authenticated_at_ms)


def _mark_authenticated(
    bridge_id: str,
    key_generation: int,
    authenticated_at_ms: int,
) -> None:
    get_browser_bridge_pairing_store().mark_bridge_authenticated(
        bridge_id=bridge_id,
        key_generation=key_generation,
        authenticated_at_ms=authenticated_at_ms,
    )


_challenge_store: BrowserBridgeChallengeStore | None = None
_challenge_store_lock = threading.Lock()


def get_browser_bridge_challenge_store() -> BrowserBridgeChallengeStore:
    global _challenge_store
    with _challenge_store_lock:
        if _challenge_store is None:
            _challenge_store = BrowserBridgeChallengeStore()
        return _challenge_store
