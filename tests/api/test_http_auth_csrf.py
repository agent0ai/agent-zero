from __future__ import annotations

from flask import Flask, Response

import pytest

from python.helpers import runtime


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

    monkeypatch.setattr("python.helpers.login.get_credentials_hash", lambda: "hash")

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

    monkeypatch.setattr("python.helpers.login.get_credentials_hash", lambda: None)

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

    monkeypatch.setattr("python.helpers.login.get_credentials_hash", lambda: "hash")

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

    monkeypatch.setattr("python.helpers.login.get_credentials_hash", lambda: "hash")

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

    monkeypatch.setattr("python.helpers.login.get_credentials_hash", lambda: "hash")

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
