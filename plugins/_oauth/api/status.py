from __future__ import annotations

from helpers.api import ApiHandler, Request
from plugins._oauth.helpers.route_bootstrap import is_installed
from plugins._oauth.helpers.providers import provider_registry
from plugins._oauth.helpers.summary import build_oauth_status_summary


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        del input, request
        return build_oauth_status_summary(
            provider_registry=provider_registry,
            routes_installed=is_installed,
        )
