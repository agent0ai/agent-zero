"""Generic gateway webhook endpoint.

Routes incoming platform webhooks to the correct channel adapter
via the Gateway registry. Each channel's signature is verified
before the message is processed.
"""

from __future__ import annotations

from flask import Request, Response

from python.helpers.api import ApiHandler
from python.helpers.channel_bridge import NormalizedMessage
from python.helpers.gateway import Gateway
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
        gateway = Gateway.get()

        # --- Determine target channel from query param or header ----------
        channel = (request.args.get("channel") or request.headers.get("X-Gateway-Channel", "")).lower()

        if not channel:
            return Response(
                response="Missing ?channel= parameter",
                status=400,
                mimetype="text/plain",
            )

        pair = gateway.get_channel(channel)
        if pair is None:
            return Response(
                response=f"Unknown channel: {channel}",
                status=404,
                mimetype="text/plain",
            )

        bridge, client = pair

        # --- WhatsApp subscription verification (GET) ---------------------
        if request.method == "GET" and channel == "whatsapp":
            mode = request.args.get("hub.mode", "")
            token = request.args.get("hub.verify_token", "")
            challenge = request.args.get("hub.challenge", "")
            if hasattr(client, "verify_subscription"):
                result = client.verify_subscription(mode, token, challenge)  # type: ignore[attr-defined]
                if result is not None:
                    return Response(response=result, status=200, mimetype="text/plain")
            return Response(response="Forbidden", status=403, mimetype="text/plain")

        # --- Webhook signature verification --------------------------------
        raw_body = request.get_data()
        sig_verified = await self._verify_signature(channel, client, raw_body, request)
        if not sig_verified:
            PrintStyle(font_color="red", padding=True).print(
                f"[Gateway] Webhook signature verification FAILED for {channel}"
            )
            return Response(response="Forbidden", status=403, mimetype="text/plain")

        # --- Parse platform-specific payload into NormalizedMessage ---------
        data = request.get_json(silent=True) or {}
        msg = self._parse_payload(channel, data)
        if msg is None:
            return {"status": "ignored"}

        # --- Route through gateway -----------------------------------------
        result = await gateway.receive_message(msg, use_context_fn=self.use_context)
        return result

    async def _verify_signature(
        self,
        channel: str,
        client: object,
        raw_body: bytes,
        request: Request,
    ) -> bool:
        """Dispatch signature verification to the correct adapter."""
        from python.helpers.channel_bridge import ChannelClient

        if not isinstance(client, ChannelClient):
            return False

        if channel == "telegram":
            sig = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            return await client.verify_webhook_signature(raw_body, sig)

        elif channel == "slack":
            sig = request.headers.get("X-Slack-Signature", "")
            ts = request.headers.get("X-Slack-Request-Timestamp", "")
            return await client.verify_webhook_signature(raw_body, sig, timestamp=ts)

        elif channel == "discord":
            sig = request.headers.get("X-Signature-Ed25519", "")
            ts = request.headers.get("X-Signature-Timestamp", "")
            return await client.verify_webhook_signature(raw_body, sig, timestamp=ts)

        elif channel == "whatsapp":
            sig = request.headers.get("X-Hub-Signature-256", "")
            return await client.verify_webhook_signature(raw_body, sig)

        return False

    def _parse_payload(self, channel: str, data: dict) -> NormalizedMessage | None:
        """Convert platform-specific JSON into a NormalizedMessage."""

        if channel == "telegram":
            return self._parse_telegram(data)
        elif channel == "slack":
            return self._parse_slack(data)
        elif channel == "discord":
            return self._parse_discord(data)
        elif channel == "whatsapp":
            return self._parse_whatsapp(data)
        return None

    # -- Platform parsers ---------------------------------------------------

    def _parse_telegram(self, data: dict) -> NormalizedMessage | None:
        message = data.get("message") or data.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = message.get("text") or message.get("caption")
        sender = message.get("from", {})

        if not chat_id or not text:
            return None

        return NormalizedMessage(
            channel="telegram",
            conversation_id=str(chat_id),
            sender_id=str(sender.get("id", chat_id)),
            text=text,
            metadata={"update_id": data.get("update_id")},
        )

    def _parse_slack(self, data: dict) -> NormalizedMessage | None:
        # Slack Events API sends a challenge on subscription
        if data.get("type") == "url_verification":
            return None  # Handled separately or return challenge

        event = data.get("event", {})
        if event.get("type") != "message" or event.get("subtype"):
            return None  # Ignore non-message events and bot messages

        channel_id = event.get("channel", "")
        user_id = event.get("user", "")
        text = event.get("text", "")

        if not channel_id or not user_id or not text:
            return None

        return NormalizedMessage(
            channel="slack",
            conversation_id=channel_id,
            sender_id=user_id,
            text=text,
            metadata={
                "update_id": event.get("client_msg_id", event.get("ts")),
                "thread_ts": event.get("thread_ts"),
                "team_id": data.get("team_id"),
            },
        )

    def _parse_discord(self, data: dict) -> NormalizedMessage | None:
        # Discord interaction type 1 = PING
        if data.get("type") == 1:
            return None  # Handled by PING/PONG at a higher level

        # Message from gateway bot event
        if data.get("t") == "MESSAGE_CREATE":
            d = data.get("d", {})
        else:
            d = data

        channel_id = d.get("channel_id", "")
        author = d.get("author", {})
        user_id = author.get("id", "")
        text = d.get("content", "")

        # Ignore bot messages
        if author.get("bot"):
            return None

        if not channel_id or not user_id or not text:
            return None

        return NormalizedMessage(
            channel="discord",
            conversation_id=channel_id,
            sender_id=user_id,
            text=text,
            metadata={"update_id": d.get("id")},
        )

    def _parse_whatsapp(self, data: dict) -> NormalizedMessage | None:
        entry = data.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        if msg.get("type") != "text":
            return None

        wa_id = msg.get("from", "")
        text = msg.get("text", {}).get("body", "")

        if not wa_id or not text:
            return None

        return NormalizedMessage(
            channel="whatsapp",
            conversation_id=wa_id,
            sender_id=wa_id,
            text=text,
            metadata={
                "update_id": msg.get("id"),
                "timestamp": msg.get("timestamp"),
            },
        )
