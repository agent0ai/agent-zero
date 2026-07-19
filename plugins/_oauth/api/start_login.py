from __future__ import annotations

import webbrowser

from helpers.api import ApiHandler, Request
from plugins._oauth.helpers import codex
from plugins._oauth.helpers.config import codex_config
from plugins._oauth.helpers.state import put_attempt


class StartLogin(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        cfg = codex_config()
        if not cfg["enabled"]:
            return {"ok": False, "error": "Codex/ChatGPT account connection is disabled."}

        redirect_uri = _redirect_uri(request, cfg["callback_path"])
        pkce = codex.generate_pkce()
        state = codex.generate_state()
        attempt = put_attempt(state, pkce.verifier, redirect_uri)
        auth_url = codex.build_authorize_url(redirect_uri, state, pkce)

        if cfg["open_browser_from_server"]:
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass

        return {
            "ok": True,
            "auth_url": auth_url,
            "redirect_uri": redirect_uri,
            "expires_at": attempt.expires_at,
        }


def _redirect_uri(request: Request, callback_path: str) -> str:
    origin = (request.headers.get("Origin") or "").rstrip("/")
    if not _is_local_origin(origin):
        origin = request.url_root.rstrip("/")
    return f"{origin}{callback_path}"


def _is_local_origin(origin: str) -> bool:
    if not origin:
        return False
    return (
        origin.startswith("http://localhost:")
        or origin == "http://localhost"
        or origin.startswith("http://127.0.0.1:")
        or origin == "http://127.0.0.1"
        or origin.startswith("http://[::1]:")
        or origin == "http://[::1]"
    )
