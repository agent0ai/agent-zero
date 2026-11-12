from __future__ import annotations

import asyncio
import importlib
import json
import sys
from contextlib import contextmanager
from types import ModuleType

import pytest

from plugins._a0_connector.helpers.browser_companion_release import (
    CATALOG_KEY_FINGERPRINT_ENV,
    CATALOG_URL_ENV,
    INSTALL_CONTRACT,
    RELEASE_METADATA_CONTRACT,
    RELEASE_METADATA_ENV,
    SERVER_MINIMUM_SECURE_COMPANION,
    browser_companion_release_status,
)


def _artifact(platform: str, arch: str, kind: str) -> dict[str, object]:
    suffix = {
        ("macos", "installer"): ".dmg",
        ("windows", "installer"): ".exe",
        ("linux", "bootstrap"): ".sh",
    }.get((platform, kind), ".tar.gz")
    name = f"a0-browser-bridge-{platform}-{arch}-{kind}{suffix}"
    return {
        "name": name,
        "platform": platform,
        "arch": arch,
        "kind": kind,
        "download_url": f"https://releases.example.test/v2.12.0/{name}",
        "sha256": "ab" * 32,
        "size": 1_234_567,
    }


def _document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "release": "2.12.0",
        "channel": "stable",
        "published_at": "2026-09-04T00:00:00Z",
        "protocol": {"min": 1, "max": 1},
        "trust": {"min": 1, "max": 1},
        "minimum_secure_companion": "2.12.0",
        "catalog_signature_url": "https://releases.example.test/v2.12.0/catalog.sig",
        "release_key_id": "release-root-2026",
        "artifacts": [
            _artifact("macos", "universal2", "installer"),
            _artifact("macos", "universal2", "payload"),
            _artifact("windows", "x86_64", "installer"),
            _artifact("windows", "x86_64", "payload"),
            _artifact("windows", "arm64", "installer"),
            _artifact("windows", "arm64", "payload"),
            _artifact("linux", "any", "bootstrap"),
            _artifact("linux", "x86_64", "payload"),
            _artifact("linux", "aarch64", "payload"),
        ],
    }


def _environment(document: dict[str, object] | None = None) -> dict[str, str]:
    return {
        CATALOG_URL_ENV: "https://releases.example.test/v2.12.0/catalog.json",
        CATALOG_KEY_FINGERPRINT_ENV: f"sha256:{'cd' * 32}",
        RELEASE_METADATA_ENV: json.dumps(document or _document()),
    }


def test_release_metadata_is_unavailable_and_host_targeted_by_default() -> None:
    status = browser_companion_release_status(environ={})

    assert status["ok"] is False
    assert status["contract"] == RELEASE_METADATA_CONTRACT
    assert status["install_contract"] == INSTALL_CONTRACT
    assert status["install_ready"] is False
    assert status["state"] == "unavailable"
    assert status["catalog"] is None
    assert status["release"] is None
    assert status["artifacts"] == []
    assert status["delivery"]["target"] == "browser_host"
    assert status["delivery"]["docker_container_install"] is False
    assert status["verification"] == {
        "server_validation": "metadata_shape_and_compatibility_only",
        "catalog_signature_verified": False,
        "artifact_verified": False,
        "host_verification_required": True,
    }


def test_scoped_v2_metadata_requires_exact_complete_declared_platform_groups() -> None:
    document = _document()
    document.update(schema_version=2, platforms=["macos"])
    document["artifacts"] = document["artifacts"][:2]
    status = browser_companion_release_status(environ=_environment(document))
    assert status["state"] == "available"
    assert len(status["artifacts"]) == 2
    assert status["install_ready"] is False
    assert status["verification"]["catalog_signature_verified"] is False
    for platforms in ([], ["macos", "macos"], ["windows", "macos"], ["android"], ["macos", "windows"], [True]):
        invalid = {**document, "platforms": platforms}
        assert browser_companion_release_status(environ=_environment(invalid))["state"] == "unavailable"


def test_setup_projection_requires_enabled_server_and_keeps_os_links_exact():
    from plugins._a0_connector.helpers.browser_bridge_setup import browser_bridge_setup_status
    document = _document()
    document.update(schema_version=2, platforms=["macos"])
    document["artifacts"] = document["artifacts"][:2]
    environment = _environment(document)
    environment["A0_BROWSER_BRIDGE_EXTENSION_ID"] = "a" * 32
    assert browser_bridge_setup_status(environ=environment)["installers"] == []
    environment["A0_BROWSER_BRIDGE_ROLLOUT"] = "available"
    setup = browser_bridge_setup_status(environ=environment)
    assert setup["browser_control_ready"] is False
    assert setup["host_verification_required"] is True
    assert setup["install_target"] == "browser_host"
    assert setup["extension_url"] == "https://chromewebstore.google.com/detail/" + "a" * 32
    assert setup["installers"] == [{"platform": "macos", "arch": "universal2", "url": document["artifacts"][0]["download_url"]}]
    for invalid in (
        {**document, "schema_version": 1},
        {**document, "artifacts": document["artifacts"][:1]},
        {**document, "artifacts": document["artifacts"] + [_artifact("linux", "any", "bootstrap")]},
    ):
        assert browser_companion_release_status(environ=_environment(invalid))["state"] == "unavailable"


def test_complete_compatible_metadata_projects_only_public_release_fields() -> None:
    status = browser_companion_release_status(environ=_environment())

    assert status["ok"] is True
    assert status["state"] == "available"
    assert status["contract"] == RELEASE_METADATA_CONTRACT
    assert status["install_contract"] == INSTALL_CONTRACT
    assert status["install_ready"] is False
    assert status["compatibility"]["compatible"] is True
    assert (
        status["compatibility"]["server_minimum_secure_companion"]
        == SERVER_MINIMUM_SECURE_COMPANION
    )
    assert "verified release" not in status["message"].lower()
    assert status["verification"]["host_verification_required"] is True
    assert status["verification"]["catalog_signature_verified"] is False
    assert status["release"] == {
        "version": "2.12.0",
        "channel": "stable",
        "published_at": "2026-09-04T00:00:00Z",
        "minimum_secure_companion": "2.12.0",
        "effective_minimum_secure_companion": SERVER_MINIMUM_SECURE_COMPANION,
    }
    assert len(status["artifacts"]) == 9
    assert all(item["download_url"].startswith("https://") for item in status["artifacts"])


@pytest.mark.parametrize(
    "mutate",
    [
        lambda document: document.update({"extension_origins": ["chrome-extension://secret/"]}),
        lambda document: document.update({"native_host_path": "/Users/private/bridge"}),
        lambda document: document["artifacts"][0].update(
            {"download_url": "https://token@example.test/file.bin"}
        ),
        lambda document: document.update({"protocol": {"min": 2, "max": 2}}),
        lambda document: document.update({"minimum_secure_companion": "2.13.0"}),
        lambda document: document["artifacts"].pop(),
    ],
)
def test_untrusted_or_incompatible_metadata_fails_closed_without_echo(
    mutate,
) -> None:
    document = _document()
    mutate(document)
    secret = "sentinel-server-credential"
    private_key = "sentinel-release-signing-private-key"
    environment = _environment(document)
    environment["UNRELATED_SECRET"] = secret
    environment["A0_BROWSER_COMPANION_SIGNING_PRIVATE_KEY"] = private_key

    status = browser_companion_release_status(environ=environment)
    serialized = json.dumps(status, sort_keys=True)

    assert status["state"] == "unavailable"
    assert status["catalog"] is None
    assert status["release"] is None
    assert status["artifacts"] == []
    assert secret not in serialized
    assert private_key not in serialized
    assert "chrome-extension://" not in serialized
    assert "/Users/private" not in serialized
    assert "token@" not in serialized


@pytest.mark.parametrize(
    "environment_update",
    [
        {CATALOG_URL_ENV: "https://latest.example.test/catalog.json?token=secret"},
        {CATALOG_URL_ENV: "https://releases.example.test/catalog.json?"},
        {CATALOG_URL_ENV: "https://releases.example.test/catalog.json#"},
        {CATALOG_URL_ENV: "https://releases.example.test\\ambiguous/catalog.json"},
        {CATALOG_URL_ENV: "https://releases.example.test/%0a/catalog.json"},
        {CATALOG_URL_ENV: "https://releases.example.test/%2f/catalog.json"},
        {CATALOG_URL_ENV: "https://releases.example.test/%2e%2e/catalog.json"},
        {CATALOG_URL_ENV: "https://releases.example.test//ambiguous/catalog.json"},
        {CATALOG_URL_ENV: "https://.example.test/catalog.json"},
        {CATALOG_URL_ENV: "https://releases.example.test:/catalog.json"},
        {CATALOG_URL_ENV: "https://127.1/catalog.json"},
        {CATALOG_URL_ENV: " https://releases.example.test/catalog.json"},
        {CATALOG_URL_ENV: "https://releases.exämple/catalog.json"},
        {CATALOG_KEY_FINGERPRINT_ENV: "sha256:not-a-release-root"},
        {RELEASE_METADATA_ENV: "{"},
    ],
)
def test_invalid_pinned_configuration_fails_closed(
    environment_update: dict[str, str],
) -> None:
    environment = _environment()
    environment.update(environment_update)

    status = browser_companion_release_status(environ=environment)

    assert status["ok"] is False
    assert status["state"] == "unavailable"
    assert status["reason_code"] == "browser_companion_release_invalid"
    assert status["catalog"] is None
    assert status["artifacts"] == []
    assert "token=secret" not in json.dumps(status, sort_keys=True)


def test_duplicate_json_fields_fail_closed() -> None:
    raw_metadata = json.dumps(_document()).replace(
        '"schema_version": 1,',
        '"schema_version": 2, "schema_version": 1,',
        1,
    )
    environment = _environment()
    environment[RELEASE_METADATA_ENV] = raw_metadata

    status = browser_companion_release_status(environ=environment)

    assert status["state"] == "unavailable"
    assert status["reason_code"] == "browser_companion_release_invalid"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda document: document.update({"schema_version": True}),
        lambda document: document.update({"release": 212}),
        lambda document: document.update({"release_key_id": 2026}),
        lambda document: document["artifacts"][0].update({"name": 123}),
    ],
)
def test_metadata_rejects_json_values_with_the_wrong_scalar_type(mutate) -> None:
    document = _document()
    mutate(document)

    status = browser_companion_release_status(environ=_environment(document))

    assert status["ok"] is False
    assert status["state"] == "unavailable"
    assert status["reason_code"] == "browser_companion_release_invalid"


def test_release_below_server_security_floor_is_incompatible() -> None:
    document = _document()
    document["release"] = "2.11.0"
    document["minimum_secure_companion"] = "2.11.0"

    status = browser_companion_release_status(environ=_environment(document))

    assert status["state"] == "unavailable"
    assert status["reason_code"] == "browser_companion_release_incompatible"
    assert status["compatibility"]["server_minimum_secure_companion"] == "2.12.0"
    assert status["release"] is None


def test_server_security_floor_cannot_be_lowered_by_metadata() -> None:
    document = _document()
    document["minimum_secure_companion"] = "2.11.0"

    status = browser_companion_release_status(environ=_environment(document))

    assert status["state"] == "available"
    assert status["release"]["minimum_secure_companion"] == "2.11.0"
    assert status["release"]["effective_minimum_secure_companion"] == "2.12.0"


@contextmanager
def _load_endpoint_module(monkeypatch: pytest.MonkeyPatch):
    class FakeApiHandler:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        @classmethod
        def requires_auth(cls) -> bool:
            return True

        @classmethod
        def requires_csrf(cls) -> bool:
            return cls.requires_auth()

    class FakeResponse:
        def __init__(self, *, response: str, status: int, mimetype: str) -> None:
            self.response = response
            self.status = status
            self.mimetype = mimetype

    api_stub = ModuleType("helpers.api")
    api_stub.ApiHandler = FakeApiHandler
    api_stub.Request = object
    api_stub.Response = FakeResponse
    module_name = "plugins._a0_connector.api.v1.browser_companion_release"
    previous = sys.modules.pop(module_name, None)
    try:
        with monkeypatch.context() as context:
            context.setitem(sys.modules, "helpers.api", api_stub)
            yield importlib.import_module(module_name)
    finally:
        sys.modules.pop(module_name, None)
        if previous is not None:
            sys.modules[module_name] = previous


def test_endpoint_is_authenticated_csrf_protected_and_rejects_request_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _load_endpoint_module(monkeypatch) as endpoint:
        handler = endpoint.BrowserCompanionRelease(None, None)
        assert handler.requires_auth() is True
        assert handler.requires_csrf() is True

        response = asyncio.run(
            handler.process(
                {"download_url": "https://page.example.test/untrusted.bin"},
                request=None,
            )
        )

    assert response.status == 400
    assert "request_body_not_supported" in response.response
    assert "page.example.test" not in response.response


def test_endpoint_returns_server_projection_without_request_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _load_endpoint_module(monkeypatch) as endpoint:
        expected = {"state": "unavailable", "source": "server"}
        monkeypatch.setattr(
            endpoint,
            "browser_companion_release_status",
            lambda: expected,
        )
        response = asyncio.run(handler_process(endpoint, {}))

    assert response is expected


def test_endpoint_rejects_non_json_request_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = type(
        "Request",
        (),
        {
            "is_json": False,
            "content_length": 22,
            "data": b"download_url=untrusted",
        },
    )()
    with _load_endpoint_module(monkeypatch) as endpoint:
        response = asyncio.run(handler_process(endpoint, {}, request=request))

    assert response.status == 400
    assert "request_body_not_supported" in response.response


def test_endpoint_rejects_malformed_application_json_request_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = type(
        "Request",
        (),
        {
            "is_json": True,
            "content_length": 1,
            "data": b"{",
        },
    )()
    with _load_endpoint_module(monkeypatch) as endpoint:
        response = asyncio.run(handler_process(endpoint, {}, request=request))

    assert response.status == 400
    assert "request_body_not_supported" in response.response


def test_endpoint_accepts_only_a_parsed_empty_json_object_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = type(
        "Request",
        (),
        {
            "is_json": True,
            "content_length": 5,
            "data": b" {} \n",
        },
    )()
    with _load_endpoint_module(monkeypatch) as endpoint:
        expected = {"state": "unavailable", "source": "server"}
        monkeypatch.setattr(endpoint, "browser_companion_release_status", lambda: expected)
        response = asyncio.run(handler_process(endpoint, {}, request=request))

    assert response is expected




async def handler_process(endpoint, payload: dict[str, object], *, request=None):
    handler = endpoint.BrowserCompanionRelease(None, None)
    return await handler.process(payload, request=request)
