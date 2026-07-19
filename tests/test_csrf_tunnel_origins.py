from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from flask import Flask


@pytest.mark.asyncio
async def test_csrf_token_allows_normalized_active_tailscale_origin(monkeypatch):
    import api.csrf_token as csrf_module
    import api.tunnel_proxy as tunnel_proxy

    handler = csrf_module.GetCsrfToken(Flask("test_csrf_tunnel_origins"), None)
    request = SimpleNamespace(
        headers={"Origin": "https://agent-zero.tailabc.ts.net"},
        environ={},
        referrer=None,
    )

    monkeypatch.setattr(csrf_module.login, "is_login_required", lambda: False)
    monkeypatch.setattr(
        csrf_module.dotenv,
        "get_dotenv_value",
        lambda key: "http://localhost:32080"
        if key == csrf_module.ALLOWED_ORIGINS_KEY
        else "",
    )

    async def fake_tunnel_process(input_data):
        return {
            "success": True,
            "tunnel_url": "https://agent-zero.tailabc.ts.net/funnel-ready/",
            "is_running": True,
        }

    monkeypatch.setattr(tunnel_proxy, "process", fake_tunnel_process)

    origin_check = await handler.check_allowed_origin(request)

    assert origin_check["ok"] is True
    assert "https://agent-zero.tailabc.ts.net" in origin_check["allowed_origins"]


@pytest.mark.asyncio
async def test_csrf_token_rejects_unrelated_origin_with_active_tunnel(monkeypatch):
    import api.csrf_token as csrf_module
    import api.tunnel_proxy as tunnel_proxy

    handler = csrf_module.GetCsrfToken(Flask("test_csrf_tunnel_origins"), None)
    request = SimpleNamespace(
        headers={"Origin": "https://evil.example"},
        environ={},
        referrer=None,
    )

    monkeypatch.setattr(csrf_module.login, "is_login_required", lambda: False)
    monkeypatch.setattr(
        csrf_module.dotenv,
        "get_dotenv_value",
        lambda key: "http://localhost:32080"
        if key == csrf_module.ALLOWED_ORIGINS_KEY
        else "",
    )

    async def fake_tunnel_process(input_data):
        return {
            "success": True,
            "tunnel_url": "https://agent-zero.tailabc.ts.net/funnel-ready/",
            "is_running": True,
        }

    monkeypatch.setattr(tunnel_proxy, "process", fake_tunnel_process)

    origin_check = await handler.check_allowed_origin(request)

    assert origin_check["ok"] is False


def test_active_tunnel_origins_include_docker_tunnel_service_url(monkeypatch):
    import helpers.tunnel_origins as tunnel_origins

    monkeypatch.setattr(
        tunnel_origins,
        "_get_tunnel_service_url",
        lambda: "https://agent-zero.tailabc.ts.net/funnel-ready/",
    )

    assert (
        "https://agent-zero.tailabc.ts.net"
        in tunnel_origins.get_active_tunnel_origins()
    )


def test_tunnel_service_url_uses_short_local_get_request(monkeypatch):
    from helpers import dotenv, runtime
    import helpers.tunnel_origins as tunnel_origins

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self):
            return json.dumps({
                "success": True,
                "tunnel_url": "https://agent-zero.tailabc.ts.net/funnel-ready/",
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = request.data
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        runtime,
        "is_dockerized",
        lambda: True,
    )
    monkeypatch.setattr(
        runtime,
        "get_arg",
        lambda name: None,
    )
    monkeypatch.setattr(
        runtime,
        "get_tunnel_api_port",
        lambda: 55520,
    )
    monkeypatch.setattr(
        dotenv,
        "get_dotenv_value",
        lambda key: "",
    )
    monkeypatch.setattr(tunnel_origins.urllib.request, "urlopen", fake_urlopen)

    assert (
        tunnel_origins._get_tunnel_service_url()
        == "https://agent-zero.tailabc.ts.net/funnel-ready/"
    )
    assert captured == {
        "url": "http://localhost:55520/",
        "body": b'{"action": "get"}',
        "method": "POST",
        "timeout": 0.35,
    }
