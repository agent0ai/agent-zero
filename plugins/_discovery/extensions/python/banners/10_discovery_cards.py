from helpers.extension import Extension
from helpers import plugins


class DiscoveryCardsExtension(Extension):
    """Injects discovery cards into the banners list."""

    def _oauth_summary(self) -> dict:
        try:
            from plugins._oauth.helpers.providers import provider_registry
            from plugins._oauth.helpers.route_bootstrap import is_installed
            from plugins._oauth.helpers.summary import build_oauth_status_summary

            return build_oauth_status_summary(
                provider_registry=provider_registry,
                routes_installed=is_installed,
            )
        except Exception:
            return {}

    def _oauth_usage_windows(self, summary: dict) -> list[dict]:
        windows: list[dict] = []
        accounts = summary.get("oauth_accounts") if isinstance(summary, dict) else {}
        connected = accounts.get("connected", []) if isinstance(accounts, dict) else []
        for account in connected:
            if not isinstance(account, dict):
                continue
            provider_name = account.get("short_name") or account.get("display_name") or "Account"
            for window in account.get("usage_windows") or []:
                if not isinstance(window, dict):
                    continue
                windows.append({
                    **window,
                    "key": f'{account.get("provider_id", "oauth")}-{window.get("key", "usage")}',
                    "title": f'{provider_name} {window.get("title") or "Usage"}',
                })
        return windows[:4]

    def _oauth_account_chips(self, summary: dict) -> list[dict]:
        accounts = summary.get("oauth_accounts") if isinstance(summary, dict) else {}
        if not isinstance(accounts, dict):
            return []
        connected = accounts.get("connected") or []
        available = accounts.get("available") or []
        source = connected if connected else available
        chips = []
        for account in source[:4]:
            if not isinstance(account, dict):
                continue
            chips.append({
                "provider_id": account.get("provider_id") or "",
                "label": account.get("short_name") or account.get("display_name") or account.get("provider_id"),
                "detail": account.get("account_label") if account.get("connected") else "Available",
                "connected": bool(account.get("connected")),
            })
        return chips

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        # Optional logic: only show specific cards if plugins aren't already configured.
        # Telegram, Email, Whatsapp are built-in, so we only need to check if they've been configured.

        telegram_config = plugins.get_plugin_config("_telegram_integration") or {}
        email_config = plugins.get_plugin_config("_email_integration") or {}
        whatsapp_config = plugins.get_plugin_config("_whatsapp_integration") or {}
        oauth_summary = self._oauth_summary()
        oauth_accounts = oauth_summary.get("oauth_accounts") if isinstance(oauth_summary, dict) else {}
        connected_count = int(oauth_accounts.get("connected_count") or 0) if isinstance(oauth_accounts, dict) else 0
        total_count = int(oauth_accounts.get("total_count") or 0) if isinstance(oauth_accounts, dict) else 0

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
                "title": "Telegram",
                "description": "Chat on Telegram wherever you are.",
                "thumbnail": "/plugins/_discovery/webui/assets/thumb-telegram.png",
                "icon": "send",
                "cta_text": "Connect",
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
                "title": "Email",
                "description": "Let Agent Zero read and send emails on your behalf.",
                "thumbnail": "/plugins/_discovery/webui/assets/thumb-email.png",
                "icon": "mail",
                "cta_text": "Connect",
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
                "title": "WhatsApp",
                "description": "Send and receive WhatsApp messages through A0.",
                "thumbnail": "/plugins/_discovery/webui/assets/thumb-whatsapp.png",
                "icon": "chat",
                "cta_text": "Connect",
                "cta_action": "open-plugin-config:_whatsapp_integration",
                "dismissible": True,
                "priority": 50,
                "show_in_onboarding": True
            })

        # 5. OAuth account providers
        oauth_card = {
            "id": "discovery-oauth-accounts",
            "type": "hero",
            "placement": "after-features",
            "title": "Your AI accounts",
            "description": "Use your subscription-backed logins for model access."
            if not connected_count
            else "",
            "cta_text": "Connect accounts" if not connected_count else "Manage accounts",
            "cta_action": "open-plugin-config:_oauth",
            "dismissible": True,
            "priority": 40,
            "show_in_onboarding": True,
            "account_chips": self._oauth_account_chips(oauth_summary),
        }
        usage_windows = self._oauth_usage_windows(oauth_summary)
        if usage_windows:
            oauth_card["usage_windows"] = usage_windows
        banners.append(oauth_card)
