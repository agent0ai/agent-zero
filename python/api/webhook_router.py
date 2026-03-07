"""Unified webhook endpoint: ``/webhook/<channel>``.

Routes incoming webhooks to the correct adapter via ``ChannelFactory``,
verifies signatures, and hands messages to the gateway for processing.

Follows the existing ``ApiHandler`` pattern from ``python.helpers.api``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading  # noqa: TCH003

from flask import Flask, Request, Response

# Ensure all adapters are registered when this module is imported.
import python.helpers.channels  # noqa: F401
from python.helpers.api import ApiHandler
from python.helpers.channel_factory import ChannelFactory

logger = logging.getLogger(__name__)


class WebhookRouter(ApiHandler):
    """Single ``/webhook/<channel>`` endpoint for all channel adapters."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST", "GET"]

    @classmethod
    def requires_auth(cls) -> bool:
        # Webhook callers are external platforms; auth is via signature.
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        """Dispatch based on the ``<channel>`` URL segment."""
        # Flask stores URL rule arguments in request.view_args.
        channel = (request.view_args or {}).get("channel", "")
        if not channel:
            return Response(
                json.dumps({"error": "Missing channel in URL"}),
                status=400,
                mimetype="application/json",
            )

        # Check the channel is registered.
        adapter_cls = ChannelFactory.get_adapter_class(channel)
        if adapter_cls is None:
            return Response(
                json.dumps(
                    {
                        "error": f"Unknown channel: {channel}",
                        "available": ChannelFactory.available(),
                    }
                ),
                status=404,
                mimetype="application/json",
            )

        # Build adapter with config from the request (or empty).
        # In production the config would come from env / settings;
        # here we pass an empty dict so the adapter can still verify.
        adapter = ChannelFactory.create(channel)

        # --- Webhook verification challenge (GET requests) ----------------
        if request.method == "GET":
            return self._handle_verification(channel, request)

        # --- Signature verification ----------------------------------------
        body = request.get_data()
        headers = dict(request.headers)
        if not await adapter.verify_webhook(headers, body):
            logger.warning("Webhook signature verification failed for %s", channel)
            return Response(
                json.dumps({"error": "Invalid signature"}),
                status=401,
                mimetype="application/json",
            )

        # --- Normalize & route --------------------------------------------
        raw_payload = input or {}
        msg = await adapter.normalize(raw_payload)

        from python.helpers import gateway

        response_text = await gateway.process_now(msg)

        return {"ok": True, "message_id": msg.id, "response": response_text}

    # ------------------------------------------------------------------

    @staticmethod
    def _handle_verification(channel: str, request: Request) -> Response:
        """Handle platform verification challenges (e.g. WhatsApp, Slack)."""
        # WhatsApp / Meta verification
        mode = request.args.get("hub.mode")
        _token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and challenge:
            return Response(challenge, status=200, mimetype="text/plain")

        # Slack URL verification comes as POST with type=url_verification,
        # but some setups do GET.  Return 200 for simple health checks.
        return Response(
            json.dumps({"status": "ok", "channel": channel}),
            status=200,
            mimetype="application/json",
        )


def register_routes(app: Flask, thread_lock: threading.Lock) -> None:
    """Register the ``/webhook/<channel>`` route with a Flask app."""
    handler = WebhookRouter(app, thread_lock)

    async def _dispatch(channel: str):  # type: ignore[no-untyped-def]
        from flask import request

        return await handler.handle_request(request)

    # Wrap async handler for Flask (which is sync by default).
    def webhook_view(channel: str):  # type: ignore[no-untyped-def]
        from flask import request

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(handler.handle_request(request))
        finally:
            loop.close()

    app.add_url_rule(
        "/webhook/<channel>",
        endpoint="webhook_channel",
        view_func=webhook_view,
        methods=WebhookRouter.get_methods(),
    )
