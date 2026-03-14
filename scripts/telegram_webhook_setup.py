#!/usr/bin/env python3
"""Configure Telegram webhook for Agent Jumbo."""

from __future__ import annotations

import json
import os
import urllib.request


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

    if not token or not webhook_url:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_URL in the environment.")

    payload = {"url": webhook_url}
    if secret:
        payload["secret_token"] = secret

    data = json.dumps(payload).encode("utf-8")
    endpoint = f"https://api.telegram.org/bot{token}/setWebhook"
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    print(raw)


if __name__ == "__main__":
    main()
