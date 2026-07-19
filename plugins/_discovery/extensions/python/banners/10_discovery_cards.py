from helpers.extension import Extension
from helpers import plugins


class DiscoveryCardsExtension(Extension):
    """Injects discovery cards into the banners list."""

    def _codex_oauth_connected(self) -> bool:
        try:
            from plugins._oauth.helpers import codex

            return bool(codex.status().get("connected"))
        except Exception:
            return False

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        # Optional logic: only show specific cards if plugins aren't already configured.
        # Telegram, Email, Whatsapp are built-in, so we only need to check if they've been configured.

        telegram_config = plugins.get_plugin_config("_telegram_integration") or {}
        email_config = plugins.get_plugin_config("_email_integration") or {}
        whatsapp_config = plugins.get_plugin_config("_whatsapp_integration") or {}
        codex_oauth_connected = self._codex_oauth_connected()

        # 1. Plugin Hub Hero
        banners.append({
            "id": "discovery-plugin-hub",
            "type": "hero",
            "title": "Discover the Plugin Hub",
            "description": "Extend Agent Zero with integrations, tools, and automations from the community.",
            "thumbnail": "/plugins/_discovery/webui/assets/hero-plugin-hub.png",
            "icon": "extension",
            "cta_text": "Explore Plugins",
            "cta_action": "open-plugin-hub",
            "dismissible": True,
            "priority": 100,
            "show_in_onboarding": True
        })

        # 2. Telegram
        if not telegram_config.get("bot_token"):
            banners.append({
                "id": "discovery-telegram",
                "type": "feature",
                "title": "Connect Telegram",
                "description": "Chat with Agent Zero from Telegram wherever you are.",
                "thumbnail": "/plugins/_discovery/webui/assets/thumb-telegram.png",
                "icon": "send",
                "cta_text": "Setup",
                "cta_action": "open-plugin-config:_telegram_integration",
                "dismissible": True,
                "priority": 50,
                "show_in_onboarding": True
            })

        # 3. Email
        email_handlers = email_config.get("handlers") or []
        email_is_configured = any((handler or {}).get("username") for handler in email_handlers)
        if not email_is_configured:
            banners.append({
                "id": "discovery-email",
                "type": "feature",
                "title": "Setup Email",
                "description": "Let Agent Zero read and send emails on your behalf.",
                "thumbnail": "/plugins/_discovery/webui/assets/thumb-email.png",
                "icon": "mail",
                "cta_text": "Open Setup",
                "cta_action": "open-plugin-config:_email_integration",
                "dismissible": True,
                "priority": 50,
                "show_in_onboarding": True
            })

        # 4. WhatsApp
        if not whatsapp_config.get("phone_number_id"):
            banners.append({
                "id": "discovery-whatsapp",
                "type": "feature",
                "title": "Connect WhatsApp",
                "description": "Send and receive WhatsApp messages through A0.",
                "thumbnail": "/plugins/_discovery/webui/assets/thumb-whatsapp.png",
                "icon": "chat",
                "cta_text": "Setup",
                "cta_action": "open-plugin-config:_whatsapp_integration",
                "dismissible": True,
                "priority": 50,
                "show_in_onboarding": True
            })

        # 5. Codex/ChatGPT OAuth
        banners.append({
            "id": "discovery-codex-oauth",
            "type": "hero",
            "placement": "after-features",
            "title": "Connect ChatGPT/Codex" if not codex_oauth_connected else "ChatGPT/Codex Connected",
            "description": "Link your account through the OAuth plugin to unlock account-backed Codex models locally."
            if not codex_oauth_connected
            else "Manage your OAuth connection and account-backed Codex models.",
            "thumbnail": "/plugins/_discovery/webui/assets/hero-openai-oauth.png",
            "icon": "key",
            "cta_text": "Connect Account" if not codex_oauth_connected else "Manage OAuth",
            "cta_action": "open-plugin-config:_oauth",
            "dismissible": True,
            "priority": 40,
            "show_in_onboarding": True
        })
