"""Initialize the messaging gateway with all available channel adapters.

Called once at application startup. Channels that lack required env vars
are still registered but will report ``connected=False`` in status.
"""

from __future__ import annotations

from python.helpers.gateway import Gateway
from python.helpers.print_style import PrintStyle


def initialize_gateway() -> Gateway:
    """Register all channel adapters and return the gateway singleton."""
    gateway = Gateway.get()

    # -- Telegram -----------------------------------------------------------
    try:
        from python.helpers.channels.telegram_adapter import (
            TelegramBridge,
            TelegramClient,
        )

        gateway.register_channel("telegram", TelegramBridge(), TelegramClient())
    except Exception as exc:
        PrintStyle.error(f"[Gateway] Failed to register telegram: {exc}")

    # -- Slack --------------------------------------------------------------
    try:
        from python.helpers.channels.slack_adapter import SlackBridge, SlackClient

        gateway.register_channel("slack", SlackBridge(), SlackClient())
    except Exception as exc:
        PrintStyle.error(f"[Gateway] Failed to register slack: {exc}")

    # -- Discord ------------------------------------------------------------
    try:
        from python.helpers.channels.discord_adapter import (
            DiscordBridge,
            DiscordClient,
        )

        gateway.register_channel("discord", DiscordBridge(), DiscordClient())
    except Exception as exc:
        PrintStyle.error(f"[Gateway] Failed to register discord: {exc}")

    # -- WhatsApp -----------------------------------------------------------
    try:
        from python.helpers.channels.whatsapp_adapter import (
            WhatsAppBridge,
            WhatsAppClient,
        )

        gateway.register_channel("whatsapp", WhatsAppBridge(), WhatsAppClient())
    except Exception as exc:
        PrintStyle.error(f"[Gateway] Failed to register whatsapp: {exc}")

    configured = [
        name for name in gateway.channel_names() if (pair := gateway.get_channel(name)) and pair[0].is_configured()
    ]
    PrintStyle(font_color="green").print(
        f"[✓] Gateway initialized — "
        f"{len(gateway.channel_names())} channels registered, "
        f"{len(configured)} configured: {configured or 'none'}"
    )
    return gateway
