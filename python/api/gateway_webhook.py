"""Generic gateway webhook endpoint using adapter registry + async queue."""

from __future__ import annotations

from flask import Request, Response

from python.helpers import gateway
from python.helpers.api import ApiHandler
from python.helpers.channel_factory import ChannelFactory
from python.helpers.print_style import PrintStyle


class GatewayWebhook(ApiHandler):
    """Receives webhooks from any registered messaging platform."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False  # External platforms can't authenticate

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST", "GET"]  # GET needed for WhatsApp verification

    async def process(self, input: dict, request: Request):
        # --- Determine target channel from query param or header ----------
        channel = (request.args.get("channel") or request.headers.get("X-Gateway-Channel", "")).lower()

        if not channel:
            return Response(
                response="Missing ?channel= parameter",
                status=400,
                mimetype="text/plain",
            )

        adapter_cls = ChannelFactory.get_adapter_class(channel)
        if adapter_cls is None:
            return Response(
                response=f"Unknown channel: {channel}",
                status=404,
                mimetype="text/plain",
            )
        adapter = adapter_cls({})

        # --- WhatsApp subscription verification (GET) ---------------------
        if request.method == "GET" and channel == "whatsapp":
            mode = request.args.get("hub.mode", "")
            token = request.args.get("hub.verify_token", "")
            challenge = request.args.get("hub.challenge", "")
            # Match Meta verification semantics when no dedicated client exists.
            if mode == "subscribe" and challenge:
                if not token or token == (adapter.config.get("verify_token", "") or ""):
                    return Response(response=challenge, status=200, mimetype="text/plain")
            return Response(response="Forbidden", status=403, mimetype="text/plain")

        # --- Webhook signature verification --------------------------------
        raw_body = request.get_data()
        headers = dict(request.headers.items())
        sig_verified = await adapter.verify_webhook(headers, raw_body)
        if not sig_verified:
            PrintStyle(font_color="red", padding=True).print(
                f"[Gateway] Webhook signature verification FAILED for {channel}"
            )
            return Response(response="Forbidden", status=403, mimetype="text/plain")

        # --- Parse payload into NormalizedMessage via adapter --------------
        data = request.get_json(silent=True) or {}
        try:
            msg = await adapter.normalize(data)
        except Exception as exc:
            PrintStyle(font_color="yellow", padding=False).print(f"[Gateway] normalize skipped for {channel}: {exc}")
            msg = None
        if msg is None or not getattr(msg, "text", "").strip():
            return {"status": "ignored"}

        # --- Route through gateway queue -----------------------------------
        await gateway.route_message(msg)
        return {"status": "queued", "channel": channel, "message_id": getattr(msg, "id", "")}
