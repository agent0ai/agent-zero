"""Read-only, allowlisted Browser companion release metadata projection."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from urllib.parse import urlsplit


INSTALL_CONTRACT = "a0.browser-bridge.install.v1"
RELEASE_METADATA_CONTRACT = "a0.browser-bridge.release-metadata.v1"
RELEASE_METADATA_SCHEMA_VERSION = 1
SERVER_MINIMUM_SECURE_COMPANION = "2.12.0"
CATALOG_URL_ENV = "A0_BROWSER_COMPANION_CATALOG_URL"
CATALOG_KEY_FINGERPRINT_ENV = "A0_BROWSER_COMPANION_CATALOG_KEY_FINGERPRINT"
RELEASE_METADATA_ENV = "A0_BROWSER_COMPANION_RELEASE_METADATA"
MAX_RELEASE_METADATA_BYTES = 128 * 1024
MAX_ARTIFACTS = 32
MAX_ARTIFACT_BYTES = 2 * 1024 * 1024 * 1024
MAX_PUBLIC_URL_BYTES = 4096
SUPPORTED_PROTOCOL = 1
SUPPORTED_TRUST = 1

_HEX_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_KEY_FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_RELEASE_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_ARTIFACT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")
_PUBLISHED_AT_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

_ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "release",
        "channel",
        "published_at",
        "protocol",
        "trust",
        "minimum_secure_companion",
        "catalog_signature_url",
        "release_key_id",
        "artifacts",
    }
)
_REQUIRED_TOP_LEVEL_KEYS = _ALLOWED_TOP_LEVEL_KEYS
_ALLOWED_ARTIFACT_KEYS = frozenset(
    {"name", "platform", "arch", "kind", "download_url", "sha256", "size"}
)
_PLATFORM_ARCHES = {
    "macos": frozenset({"universal2", "x86_64", "arm64"}),
    "windows": frozenset({"x86_64", "arm64"}),
    "linux": frozenset({"any", "x86_64", "aarch64"}),
}
_ARTIFACT_KINDS = frozenset({"installer", "bootstrap", "payload"})
_REQUIRED_ARTIFACTS = frozenset(
    {
        ("macos", "universal2", "installer"),
        ("macos", "universal2", "payload"),
        ("windows", "x86_64", "installer"),
        ("windows", "x86_64", "payload"),
        ("windows", "arm64", "installer"),
        ("windows", "arm64", "payload"),
        ("linux", "any", "bootstrap"),
        ("linux", "x86_64", "payload"),
        ("linux", "aarch64", "payload"),
    }
)


class _MetadataError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BrowserCompanionArtifact:
    name: str
    platform: str
    arch: str
    kind: str
    download_url: str
    sha256: str
    size: int

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "platform": self.platform,
            "arch": self.arch,
            "kind": self.kind,
            "download_url": self.download_url,
            "sha256": self.sha256,
            "size": self.size,
        }


def browser_companion_release_status(
    *, environ: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Return public release metadata without fetching or installing anything."""

    source = os.environ if environ is None else environ
    catalog_url = str(source.get(CATALOG_URL_ENV, "") or "")
    key_fingerprint = str(
        source.get(CATALOG_KEY_FINGERPRINT_ENV, "") or ""
    ).strip()
    raw_metadata = str(source.get(RELEASE_METADATA_ENV, "") or "").strip()
    configured = {
        "catalog_url": bool(catalog_url),
        "catalog_key_fingerprint": bool(key_fingerprint),
        "release_metadata": bool(raw_metadata),
    }

    if not all(configured.values()):
        return _unavailable(
            reason_code="browser_companion_release_not_configured",
            message="Signed Browser companion release metadata is not configured.",
            configured=configured,
        )

    try:
        if len(raw_metadata.encode("utf-8")) > MAX_RELEASE_METADATA_BYTES:
            raise _MetadataError("metadata too large")
        if not _is_safe_https_url(catalog_url):
            raise _MetadataError("invalid catalog URL")
        if not _KEY_FINGERPRINT_RE.fullmatch(key_fingerprint):
            raise _MetadataError("invalid key fingerprint")
        document = json.loads(
            raw_metadata,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_number,
        )
        release = _parse_release_document(document)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return _unavailable(
            reason_code="browser_companion_release_invalid",
            message="Signed Browser companion release metadata is invalid.",
            configured=configured,
        )

    if (
        not _range_contains(release["protocol"], SUPPORTED_PROTOCOL)
        or not _range_contains(release["trust"], SUPPORTED_TRUST)
        or _semantic_version_tuple(release["release"])
        < _semantic_version_tuple(SERVER_MINIMUM_SECURE_COMPANION)
    ):
        return _unavailable(
            reason_code="browser_companion_release_incompatible",
            message="No configured Browser companion release is compatible with this server.",
            configured=configured,
        )

    artifacts: tuple[BrowserCompanionArtifact, ...] = release["artifacts"]
    return {
        "ok": True,
        "contract": RELEASE_METADATA_CONTRACT,
        "schema_version": RELEASE_METADATA_SCHEMA_VERSION,
        "install_contract": INSTALL_CONTRACT,
        "install_ready": False,
        "state": "available",
        "reason_code": "browser_companion_release_available",
        "message": (
            "Pinned presentation metadata is available for browser-host delivery; "
            "installation is not verified."
        ),
        "delivery": _delivery_projection(),
        "verification": _verification_projection(),
        "configuration": configured,
        "catalog": {
            "url": catalog_url,
            "signature_url": release["catalog_signature_url"],
            "key_fingerprint": key_fingerprint.lower(),
            "release_key_id": release["release_key_id"],
        },
        "compatibility": {
            "protocol": release["protocol"],
            "trust": release["trust"],
            "server_protocol": SUPPORTED_PROTOCOL,
            "server_trust": SUPPORTED_TRUST,
            "server_minimum_secure_companion": SERVER_MINIMUM_SECURE_COMPANION,
            "compatible": True,
        },
        "release": {
            "version": release["release"],
            "channel": release["channel"],
            "published_at": release["published_at"],
            "minimum_secure_companion": release["minimum_secure_companion"],
            "effective_minimum_secure_companion": _maximum_semantic_version(
                release["minimum_secure_companion"],
                SERVER_MINIMUM_SECURE_COMPANION,
            ),
        },
        "artifacts": [artifact.to_public_dict() for artifact in artifacts],
    }


def _unavailable(
    *, reason_code: str, message: str, configured: dict[str, bool]
) -> dict[str, Any]:
    return {
        "ok": False,
        "contract": RELEASE_METADATA_CONTRACT,
        "schema_version": RELEASE_METADATA_SCHEMA_VERSION,
        "install_contract": INSTALL_CONTRACT,
        "install_ready": False,
        "state": "unavailable",
        "reason_code": reason_code,
        "message": message,
        "delivery": _delivery_projection(),
        "verification": _verification_projection(),
        "configuration": configured,
        "catalog": None,
        "compatibility": {
            "server_protocol": SUPPORTED_PROTOCOL,
            "server_trust": SUPPORTED_TRUST,
            "server_minimum_secure_companion": SERVER_MINIMUM_SECURE_COMPANION,
            "compatible": False,
        },
        "release": None,
        "artifacts": [],
    }


def _delivery_projection() -> dict[str, Any]:
    return {
        "target": "browser_host",
        "docker_container_install": False,
        "message": (
            "Download and run the installer on the computer that runs your browser. "
            "Agent Zero does not install the native companion inside its Docker container."
        ),
    }


def _verification_projection() -> dict[str, Any]:
    return {
        "server_validation": "metadata_shape_and_compatibility_only",
        "catalog_signature_verified": False,
        "artifact_verified": False,
        "host_verification_required": True,
    }


def _parse_release_document(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _MetadataError("unexpected release metadata fields")
    schema_version = value.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version not in (1, 2)
    ):
        raise _MetadataError("unsupported release metadata schema")
    expected_keys = _REQUIRED_TOP_LEVEL_KEYS | ({"platforms"} if schema_version == 2 else set())
    if set(value) != expected_keys:
        raise _MetadataError("unexpected release metadata fields")
    platforms = value.get("platforms") if schema_version == 2 else sorted(_PLATFORM_ARCHES)
    if (not isinstance(platforms, list) or not platforms
        or any(not isinstance(item, str) or item not in _PLATFORM_ARCHES for item in platforms)
        or platforms != sorted(set(platforms))):
        raise _MetadataError("invalid release platforms")
    required_artifacts = frozenset(item for item in _REQUIRED_ARTIFACTS if item[0] in platforms)

    release = _required_match(value.get("release"), _RELEASE_RE)
    minimum_secure = _required_match(
        value.get("minimum_secure_companion"), _RELEASE_RE
    )
    if value.get("channel") != "stable":
        raise _MetadataError("unsupported release channel")
    published_at = _required_match(value.get("published_at"), _PUBLISHED_AT_RE)
    datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
    if _semantic_version_tuple(minimum_secure) > _semantic_version_tuple(release):
        raise _MetadataError("release is below the minimum secure companion")
    release_key_id = _required_match(value.get("release_key_id"), _SAFE_TOKEN_RE)
    signature_url = str(value.get("catalog_signature_url") or "")
    if not _is_safe_https_url(signature_url):
        raise _MetadataError("invalid catalog signature URL")

    protocol = _parse_compatibility_range(value.get("protocol"))
    trust = _parse_compatibility_range(value.get("trust"))
    artifacts_value = value.get("artifacts")
    if not isinstance(artifacts_value, list) or not (
        1 <= len(artifacts_value) <= MAX_ARTIFACTS
    ):
        raise _MetadataError("invalid artifacts")
    artifacts = tuple(_parse_artifact(item) for item in artifacts_value)
    identities = {(item.platform, item.arch, item.kind) for item in artifacts}
    names = {item.name for item in artifacts}
    urls = {item.download_url for item in artifacts}
    if len(identities) != len(artifacts) or identities != required_artifacts:
        raise _MetadataError("incomplete or duplicate artifact matrix")
    if len(names) != len(artifacts) or len(urls) != len(artifacts):
        raise _MetadataError("duplicate artifact name or URL")

    return {
        "release": release,
        "channel": "stable",
        "published_at": published_at,
        "protocol": protocol,
        "trust": trust,
        "minimum_secure_companion": minimum_secure,
        "catalog_signature_url": signature_url,
        "release_key_id": release_key_id,
        "artifacts": artifacts,
    }


def _parse_artifact(value: Any) -> BrowserCompanionArtifact:
    if not isinstance(value, dict) or set(value) != _ALLOWED_ARTIFACT_KEYS:
        raise _MetadataError("unexpected artifact fields")
    name = _required_match(value.get("name"), _ARTIFACT_NAME_RE)
    platform = str(value.get("platform") or "").strip()
    arch = str(value.get("arch") or "").strip()
    kind = str(value.get("kind") or "").strip()
    download_url = str(value.get("download_url") or "")
    sha256 = str(value.get("sha256") or "").strip().lower()
    size = value.get("size")

    if platform not in _PLATFORM_ARCHES or arch not in _PLATFORM_ARCHES[platform]:
        raise _MetadataError("unsupported artifact target")
    if kind not in _ARTIFACT_KINDS:
        raise _MetadataError("unsupported artifact kind")
    if not _is_safe_https_url(download_url, expected_name=name):
        raise _MetadataError("invalid artifact URL")
    if not _HEX_SHA256_RE.fullmatch(sha256):
        raise _MetadataError("invalid artifact digest")
    if isinstance(size, bool) or not isinstance(size, int) or not (
        1 <= size <= MAX_ARTIFACT_BYTES
    ):
        raise _MetadataError("invalid artifact size")
    return BrowserCompanionArtifact(
        name=name,
        platform=platform,
        arch=arch,
        kind=kind,
        download_url=download_url,
        sha256=sha256,
        size=size,
    )


def _parse_compatibility_range(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"min", "max"}:
        raise _MetadataError("invalid compatibility range")
    minimum = value.get("min")
    maximum = value.get("max")
    if (
        isinstance(minimum, bool)
        or isinstance(maximum, bool)
        or not isinstance(minimum, int)
        or not isinstance(maximum, int)
        or minimum < 1
        or maximum < minimum
        or maximum > 65535
    ):
        raise _MetadataError("invalid compatibility range")
    return {"min": minimum, "max": maximum}


def _range_contains(value: dict[str, int], current: int) -> bool:
    return value["min"] <= current <= value["max"]


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise _MetadataError("duplicate metadata field")
        document[key] = value
    return document


def _reject_non_finite_number(_value: str) -> None:
    raise _MetadataError("non-finite metadata number")


def _semantic_version_tuple(value: str) -> tuple[int, int, int]:
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


def _maximum_semantic_version(first: str, second: str) -> str:
    if _semantic_version_tuple(first) >= _semantic_version_tuple(second):
        return first
    return second


def _required_match(value: Any, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str):
        raise _MetadataError("invalid public metadata value")
    normalized = value.strip()
    if not pattern.fullmatch(normalized):
        raise _MetadataError("invalid public metadata value")
    return normalized


def _is_safe_https_url(value: str, *, expected_name: str | None = None) -> bool:
    if (
        not value
        or len(value.encode("utf-8")) > MAX_PUBLIC_URL_BYTES
        or not value.isascii()
        or not value.startswith("https://")
        or "\\" in value
        or "?" in value
        or "#" in value
        or "%" in value
        or _contains_control_character(value)
    ):
        return False
    try:
        parsed = urlsplit(value)
        parsed_port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.netloc.endswith(":")
        or (parsed_port is not None and not (1 <= parsed_port <= 65535))
        or not parsed.path.startswith("/")
        or parsed.path.startswith("//")
        or not _is_unambiguous_hostname(parsed.hostname)
        or any(part in {".", ".."} for part in parsed.path.split("/"))
    ):
        return False
    if expected_name is not None:
        path_name = parsed.path.rsplit("/", 1)[-1]
        if path_name != expected_name:
            return False
    return True


def _contains_control_character(value: str) -> bool:
    return any(
        character.isspace() or unicodedata.category(character) == "Cc"
        for character in value
    )


def _is_unambiguous_hostname(hostname: str) -> bool:
    if (
        not hostname
        or hostname.startswith(".")
        or hostname.endswith(".")
        or ".." in hostname
    ):
        return False
    if ":" in hostname:
        try:
            return str(ipaddress.ip_address(hostname)) == hostname
        except ValueError:
            return False
    if hostname != hostname.lower():
        return False
    if all(character.isdigit() or character == "." for character in hostname):
        try:
            return str(ipaddress.ip_address(hostname)) == hostname
        except ValueError:
            return False
    return len(hostname) <= 253 and all(
        1 <= len(label) <= 63
        and not label.startswith("-")
        and not label.endswith("-")
        and all(character.isalnum() or character == "-" for character in label)
        for label in hostname.split(".")
    )
