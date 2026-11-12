"""Offline verification of the server-owned signed Browser release allowlist."""

from __future__ import annotations

import base64
import json
import os
import re
import stat
import time
from types import MappingProxyType


POLICY_ENV = "A0_BROWSER_BRIDGE_RELEASE_POLICY_FILE"
POLICY_CONTRACT = "a0.browser-bridge.server-release-policy.v1"
MAX_POLICY_BYTES = 64 * 1024
MAX_POLICY_LIFETIME_MS = 90 * 24 * 60 * 60 * 1000
# Release engineering pins reviewed public roots here. Never load a root from
# the policy being verified, an HTTP request, the extension, or a pairing code.
TRUSTED_RELEASE_KEYS = MappingProxyType({
    "publisher-2026": "GEOygP0rBYlVYZEx+bgDhUZ3sVpfVyedoI9Jo+bcYII=",
})
_VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
_ENTRY_FIELDS = frozenset({
    "extension_id", "extension_version", "companion_version", "companion_platform", "companion_arch",
})


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate policy key")
        result[key] = value
    return result


def _base64(value, size):
    if not isinstance(value, str):
        raise ValueError("invalid policy signature")
    decoded = base64.b64decode(value, validate=True)
    if len(decoded) != size or base64.b64encode(decoded).decode("ascii") != value:
        raise ValueError("invalid policy signature")
    return decoded


def verify_policy_document(raw: bytes, *, now_ms: int) -> tuple[dict, ...]:
    """Verify exact bounded bytes against pinned keys; no network or effects."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_POLICY_BYTES:
        raise ValueError("invalid release policy")
    document = json.loads(raw, object_pairs_hook=_unique)
    if not isinstance(document, dict) or set(document) != {"key_id", "policy", "signature"}:
        raise ValueError("invalid release policy")
    key_id = document["key_id"]
    if not isinstance(key_id, str) or key_id not in TRUSTED_RELEASE_KEYS:
        raise ValueError("untrusted release policy")
    policy = document["policy"]
    if not isinstance(policy, dict) or set(policy) != {"contract", "issued_at_ms", "expires_at_ms", "releases"}:
        raise ValueError("invalid release policy")
    issued, expires = policy["issued_at_ms"], policy["expires_at_ms"]
    if (
        policy["contract"] != POLICY_CONTRACT
        or type(issued) is not int or type(expires) is not int
        or type(now_ms) is not int
        or not 0 < issued <= now_ms < expires <= 2**53 - 1
        or expires - issued > MAX_POLICY_LIFETIME_MS
        or not isinstance(policy["releases"], list)
        or not 1 <= len(policy["releases"]) <= 64
    ):
        raise ValueError("invalid release policy")
    releases = []
    for entry in policy["releases"]:
        if not isinstance(entry, dict) or set(entry) != _ENTRY_FIELDS:
            raise ValueError("invalid release policy")
        if (
            not all(isinstance(value, str) and len(value) <= 64 for value in entry.values())
            or re.fullmatch(r"[a-p]{32}", entry["extension_id"]) is None
            or _VERSION.fullmatch(entry["extension_version"]) is None
            or _VERSION.fullmatch(entry["companion_version"]) is None
            or tuple(map(int, entry["companion_version"].split("."))) < (2, 12, 0)
            or entry["companion_platform"] not in {"darwin", "linux", "windows"}
            or entry["companion_arch"] not in {"aarch64", "arm64", "universal2", "x86_64"}
            or entry in releases
        ):
            raise ValueError("invalid release policy")
        releases.append(entry)
    canonical = json.dumps(policy, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    public_key = _base64(TRUSTED_RELEASE_KEYS[key_id], 32)
    Ed25519PublicKey.from_public_bytes(public_key).verify(_base64(document["signature"], 64), canonical)
    return tuple(releases)


def _read_owned_policy() -> bytes:
    path = os.environ.get(POLICY_ENV)
    if not path or not os.path.isabs(path):
        raise ValueError("release policy is not configured")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_POLICY_BYTES:
            raise ValueError("invalid release policy file")
        raw = os.read(descriptor, MAX_POLICY_BYTES + 1)
        after = os.fstat(descriptor)
        if len(raw) != before.st_size or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("release policy changed while reading")
        return raw
    finally:
        os.close(descriptor)


def verify_configured_browser_release(active, sid, hello):
    """Reverify policy signature/time and exact admitted version tuple per call."""
    from plugins._a0_connector.helpers.browser_bridge_runtime_owner import VerifiedBrowserRelease

    try:
        releases = verify_policy_document(_read_owned_policy(), now_ms=time.time_ns() // 1_000_000)
        expected = {field: getattr(hello, field) for field in _ENTRY_FIELDS}
        if expected not in releases or hello.extension_id != active.extension_id:
            return None
        return VerifiedBrowserRelease(
            principal=active.principal, server_instance_id=active.server_instance_id,
            connector_sid=sid, load_generation_id=hello.load_generation_id,
            install_instance_id=hello.install_instance_id, **expected,
        )
    except Exception:
        return None
