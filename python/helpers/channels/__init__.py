"""Channel adapter package.

Importing this package auto-registers every adapter with ChannelFactory.
"""

from python.helpers.channels.discord_adapter import DiscordAdapter
from python.helpers.channels.email_adapter import EmailAdapter
from python.helpers.channels.google_chat_adapter import GoogleChatAdapter
from python.helpers.channels.irc_adapter import IrcAdapter
from python.helpers.channels.line_adapter import LineAdapter
from python.helpers.channels.mastodon_adapter import MastodonAdapter
from python.helpers.channels.matrix_adapter import MatrixAdapter
from python.helpers.channels.mattermost_adapter import MattermostAdapter
from python.helpers.channels.rocketchat_adapter import RocketChatAdapter
from python.helpers.channels.signal_adapter import SignalAdapter
from python.helpers.channels.slack_adapter import SlackAdapter
from python.helpers.channels.teams_adapter import TeamsAdapter
from python.helpers.channels.telegram_adapter import TelegramAdapter
from python.helpers.channels.twilio_sms_adapter import TwilioSmsAdapter
from python.helpers.channels.viber_adapter import ViberAdapter
from python.helpers.channels.whatsapp_adapter import WhatsAppAdapter

__all__ = [
    "DiscordAdapter",
    "EmailAdapter",
    "GoogleChatAdapter",
    "IrcAdapter",
    "LineAdapter",
    "MastodonAdapter",
    "MatrixAdapter",
    "MattermostAdapter",
    "RocketChatAdapter",
    "SignalAdapter",
    "SlackAdapter",
    "TeamsAdapter",
    "TelegramAdapter",
    "TwilioSmsAdapter",
    "ViberAdapter",
    "WhatsAppAdapter",
]
