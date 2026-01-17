"""Telegram delivery tool."""

import json
import os
import urllib.request

from python.helpers.tool import Response, Tool


class TelegramSend(Tool):
    """Send messages to Telegram via bot API."""

    async def execute(self, **kwargs):
        text = self.args.get("text")
        if not text:
            return Response(message="Error: text is required", break_loop=False)

        token = self.args.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = self.args.get("chat_id") or os.getenv("TELEGRAM_CHAT_ID")
        parse_mode = self.args.get("parse_mode") or "Markdown"

        if not token or not chat_id:
            return Response(
                message="Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required",
                break_loop=False,
            )

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        endpoint = f"https://api.telegram.org/bot{token}/sendMessage"

        try:
            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8", errors="ignore")
            return Response(message=f"Telegram send ok: {raw}", break_loop=False)
        except Exception as exc:
            return Response(message=f"Telegram send failed: {exc}", break_loop=False)
