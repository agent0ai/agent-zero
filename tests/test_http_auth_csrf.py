from __future__ import annotations

from flask import Flask, Response

import pytest

from helpers import runtime


def _make_app() -> Flask:
    app = Flask("test_http_auth_csrf")
    app.secret_key = "test-secret"

    @app.get("/login")
    def login_handler():
        return Response("login", status=200)

    return app


def _set_session(client, **values) -> None:
    with client.session_transaction() as sess:
        for key, value in values.items():
            sess[key] = value


def _set_csrf_cookie(client, token: str) -> None:
    cookie_name = f"csrf_token_{runtime.get_runtime_id()}"
    client.set_cookie(cookie_name, token)


def test_http_auth_enforced_when_configured(monkeypatch) -> None:
    from run_ui import csrf_protect, requires_auth

    monkeypatch.setattr("helpers.login.get_credentials_hash", lambda: "hash")

    app = _make_app()

    @app.get("/secure")
    @requires_auth
    @csrf_protect
    async def secure():
        return Response("ok", status=200)

    client = app.test_client()
    response = client.get("/secure")
    assert response.status_code == 302


def test_http_csrf_required_even_when_auth_not_configured(monkeypatch) -> None:
    from run_ui import csrf_protect, requires_auth

    monkeypatch.setattr("helpers.login.get_credentials_hash", lambda: None)

    app = _make_app()

    @app.get("/secure")
    @requires_auth
    @csrf_protect
    async def secure():
        return Response("ok", status=200)

    client = app.test_client()
    _set_session(client, csrf_token="csrf-1")
    response = client.get("/secure")
    assert response.status_code == 403


def test_http_csrf_rejects_missing_token(monkeypatch) -> None:
    from run_ui import csrf_protect, requires_auth

    monkeypatch.setattr("helpers.login.get_credentials_hash", lambda: "hash")

    app = _make_app()

    @app.get("/secure")
    @requires_auth
    @csrf_protect
    async def secure():
        return Response("ok", status=200)

    client = app.test_client()
    _set_session(client, authentication="hash", csrf_token="csrf-2")
    response = client.get("/secure")
    assert response.status_code == 403


def test_http_csrf_accepts_valid_header_without_cookie(monkeypatch) -> None:
    from run_ui import csrf_protect, requires_auth

    monkeypatch.setattr("helpers.login.get_credentials_hash", lambda: "hash")

    app = _make_app()

    @app.get("/secure")
    @requires_auth
    @csrf_protect
    async def secure():
        return Response("ok", status=200)

    client = app.test_client()
    _set_session(client, authentication="hash", csrf_token="csrf-3")
    response = client.get("/secure", headers={"X-CSRF-Token": "csrf-3"})
    assert response.status_code == 200


def test_http_csrf_accepts_valid_cookie(monkeypatch) -> None:
    from run_ui import csrf_protect, requires_auth

    monkeypatch.setattr("helpers.login.get_credentials_hash", lambda: "hash")

    app = _make_app()

    @app.get("/secure")
    @requires_auth
    @csrf_protect
    async def secure():
        return Response("ok", status=200)

    client = app.test_client()
    _set_session(client, authentication="hash", csrf_token="csrf-4")
    _set_csrf_cookie(client, "csrf-4")
    response = client.get("/secure")
    assert response.status_code == 200


def test_safe_next_url_accepts_plugin_page_path() -> None:
    from helpers.api import get_safe_next_url, is_safe_next_url

    target = "/plugins/a0_voqualizer/webui/voqualizer.html"
    assert is_safe_next_url(target)
    assert get_safe_next_url(target, "/") == target


def test_safe_next_url_preserves_query_string() -> None:
    from helpers.api import get_safe_next_url

    target = "/plugins/a0_voqualizer/webui/voqualizer.html?context=rlO1iMV7"
    assert get_safe_next_url(target, "/") == target


def test_safe_next_url_rejects_external_and_protocol_relative_urls() -> None:
    from helpers.api import get_safe_next_url, is_safe_next_url

    fallback = "/"
    for value in [
        "https://evil.example/plugins/a0_voqualizer/webui/voqualizer.html",
        "//evil.example/plugins/a0_voqualizer/webui/voqualizer.html",
        "javascript:alert(1)",
        "/safe\nLocation: https://evil.example",
    ]:
        assert not is_safe_next_url(value)
        assert get_safe_next_url(value, fallback) == fallback


def test_auth_redirect_includes_original_path_and_query(monkeypatch) -> None:
    from run_ui import requires_auth

    monkeypatch.setattr("helpers.login.get_credentials_hash", lambda: "hash")

    app = _make_app()

    @app.get("/plugins/a0_voqualizer/webui/voqualizer.html")
    @requires_auth
    async def voqualizer_page():
        return Response("ok", status=200)

    client = app.test_client()
    response = client.get("/plugins/a0_voqualizer/webui/voqualizer.html?context=rlO1iMV7")
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith("/login?next=")
    assert "%2Fplugins%2Fa0_voqualizer%2Fwebui%2Fvoqualizer.html%3Fcontext%3DrlO1iMV7" in location


def test_is_safe_next_url_rejects_backslash_open_redirects() -> None:
    from helpers.api import is_safe_next_url

    # Raw backslash forms
    assert is_safe_next_url("/\\evil.example") is False
    assert is_safe_next_url("\\/evil.example") is False
    assert is_safe_next_url("/path\\evil") is False

    # Percent-encoded backslash forms
    assert is_safe_next_url("/%5Cevil.example") is False
    assert is_safe_next_url("%5C/evil.example") is False
    assert is_safe_next_url("/%5cevil.example") is False  # lowercase hex

    # Mixed / double-encoded edge
    assert is_safe_next_url("/path/%5Cevil") is False

    # Sanity: a legitimate relative path still passes
    assert is_safe_next_url("/plugins/a0_voqualizer/webui/voqualizer.html") is True
