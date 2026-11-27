from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask


@pytest.mark.asyncio
async def test_csrf_token_allows_normalized_active_tailscale_origin(monkeypatch):
    import api.csrf_token as csrf_module
    from plugins._tunnel.helpers import runtime as tunnel_runtime

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

    def fake_tunnel_process():
        return {
            "success": True,
            "tunnel_url": "https://agent-zero.tailabc.ts.net/funnel-ready/",
            "is_running": True,
        }

    monkeypatch.setattr(tunnel_runtime, "status", fake_tunnel_process)

    origin_check = await handler.check_allowed_origin(request)

    assert origin_check["ok"] is True
    assert "https://agent-zero.tailabc.ts.net" in origin_check["allowed_origins"]


@pytest.mark.asyncio
async def test_csrf_token_rejects_unrelated_origin_with_active_tunnel(monkeypatch):
    import api.csrf_token as csrf_module
    from plugins._tunnel.helpers import runtime as tunnel_runtime

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

    def fake_tunnel_process():
        return {
            "success": True,
            "tunnel_url": "https://agent-zero.tailabc.ts.net/funnel-ready/",
            "is_running": True,
        }

    monkeypatch.setattr(tunnel_runtime, "status", fake_tunnel_process)

    origin_check = await handler.check_allowed_origin(request)

    assert origin_check["ok"] is False


def test_active_tunnel_origin_comes_from_plugin_without_network_control_service(monkeypatch):
    import helpers.tunnel_origins as tunnel_origins
    from plugins._tunnel.helpers import runtime
    monkeypatch.setattr(runtime, "status", lambda: {
        "is_running": True, "tunnel_url": "https://agent-zero.tailabc.ts.net/funnel-ready/"
    })
    assert tunnel_origins.get_active_tunnel_origins() == ["https://agent-zero.tailabc.ts.net"]


def test_stopped_plugin_never_adds_stale_origin(monkeypatch):
    from helpers.tunnel_origins import get_active_tunnel_origins
    from plugins._tunnel.helpers import runtime
    monkeypatch.setattr(runtime, "status", lambda: {
        "is_running": False, "tunnel_url": "https://old.example"
    })
    assert get_active_tunnel_origins() == []
