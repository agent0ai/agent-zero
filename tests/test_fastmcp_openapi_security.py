import sys
from pathlib import Path

import httpx
import pytest
from fastmcp.server.providers.openapi import OpenAPIProvider

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "FastMCP security regression", "version": "1.0.0"},
    "paths": {
        "/api/v1/users/{id}/profile": {
            "get": {
                "operationId": "get_user_profile",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "ok"}},
            }
        }
    },
}


@pytest.mark.asyncio
async def test_openapi_provider_percent_encodes_path_parameters():
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["raw_path"] = request.url.raw_path.decode("ascii")
        captured["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="http://backend.local/",
        headers={"Authorization": "Bearer admin_secret"},
        transport=transport,
    ) as client:
        provider = OpenAPIProvider(openapi_spec=OPENAPI_SPEC, client=client)
        tool = await provider.get_tool("get_user_profile")

        assert tool is not None

        with pytest.raises(ValueError, match="dot segments"):
            await tool.run({"id": "./profile"})
        assert captured == {}
        result = await tool.run({"id": "two users"})

    assert result.structured_content == {"ok": True}
    assert captured["authorization"] == "Bearer admin_secret"
    assert captured["path"].startswith("/api/v1/users/")
    assert captured["raw_path"] == "/api/v1/users/two%20users/profile"
