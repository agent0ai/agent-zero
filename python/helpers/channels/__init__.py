"""Channel adapter package.

Importing this package auto-registers every adapter with ChannelFactory.
"""

from python.helpers.channels.discord_adapter import DiscordAdapter
from python.helpers.channels.slack_adapter import SlackAdapter
from python.helpers.channels.telegram_adapter import TelegramAdapter
from python.helpers.channels.whatsapp_adapter import WhatsAppAdapter

__all__ = [
    "DiscordAdapter",
    "SlackAdapter",
    "TelegramAdapter",
    "WhatsAppAdapter",
]
