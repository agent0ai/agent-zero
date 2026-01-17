"""Minimal Telegram API helper."""

from __future__ import annotations

import json
import urllib.request
from typing import Any


def send_message(token: str, chat_id: str, text: str, parse_mode: str = "Markdown") -> dict[str, Any]:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    return {"raw": raw}
