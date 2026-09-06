"""POST /api/plugins/_a0_connector/v1/browser_companion_release."""

from __future__ import annotations

import json

from helpers.api import ApiHandler, Request, Response
from plugins._a0_connector.helpers.browser_companion_release import (
    browser_companion_release_status,
)


class BrowserCompanionRelease(ApiHandler):
    """Return configured public presentation metadata, not release proof."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        if not isinstance(input, dict) or input or _has_unsupported_body(request):
            return Response(
                response=(
                    '{"error":"request_body_not_supported",'
                    '"message":"Release metadata is configured by the Agent Zero server."}'
                ),
                status=400,
                mimetype="application/json",
            )
        return browser_companion_release_status()


def _has_unsupported_body(request: Request | None) -> bool:
    if request is None:
        return False
    raw_data = bytes(getattr(request, "data", b"") or b"")
    content_length = getattr(request, "content_length", None)
    if isinstance(content_length, int) and content_length > 1024:
        return True
    if not raw_data:
        return False
    if len(raw_data) > 1024 or not bool(getattr(request, "is_json", False)):
        return True
    try:
        document = json.loads(raw_data)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return True
    return not isinstance(document, dict) or bool(document)
