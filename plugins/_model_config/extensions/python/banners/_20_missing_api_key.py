from helpers.extension import Extension
from helpers import plugins
from plugins._model_config.helpers import model_config


class MissingApiKeyCheck(Extension):
    """Check if API keys are configured for selected model providers."""

    LOCAL_PROVIDERS = {"ollama", "lm_studio"}
    CONFIGURE_MODEL_SETTINGS_LINK = (
        """<div class="onboarding-banner-btn-container" style="margin-top: 12px;">"""
        """<button class="btn btn-ok" onclick="window.openModal('/plugins/_onboarding/webui/onboarding.html');return false;">"""
        """Start Onboarding</button>"""
        """</div>"""
    )

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        cfg = plugins.get_plugin_config("_model_config") or {}
        missing_providers = model_config.get_missing_api_key_providers()

        if missing_providers:
            banners.append({
                "id": "missing-api-key",
                "type": "warning",
                "priority": 100,
                "title": "Welcome to Agent Zero!",
                "html": f"""You're almost ready to chat. Please configure your models to continue.<br>
                         Insert your API key in the onboarding wizard.
                         {self.CONFIGURE_MODEL_SETTINGS_LINK}""",
                "dismissible": False,
                "source": "backend",
                "auto_modal_path": "/plugins/_onboarding/webui/onboarding.html",
                "auto_modal_reason": "missing-api-key",
                "auto_modal_priority": 100,
                "auto_modal_surfaces": ["welcome", "chat-created"],
                # For programmatic clients (e.g. chat composer) reusing this banner pipeline
                "missing_providers": missing_providers,
            })

        # Check preset providers for missing API keys (warning level)
        if cfg.get("allow_chat_override"):
            preset_missing = []
            seen = set()
            for preset in cfg.get("model_presets", []):
                preset_name = preset.get("name", "Unnamed")
                for slot_key, slot_label in [("chat", "Main"), ("utility", "Utility")]:
                    slot = preset.get(slot_key, {})
                    provider = slot.get("provider", "")
                    if not provider:
                        continue
                    provider_lower = provider.lower()
                    if provider_lower in self.LOCAL_PROVIDERS:
                        continue
                    # Skip if already covered by default checks
                    if provider_lower in seen:
                        continue
                    # Skip if preset has its own api_key
                    if slot.get("api_key", "").strip():
                        continue
                    if not model_config.has_provider_api_key(provider_lower):
                        seen.add(provider_lower)
                        preset_missing.append(f"{preset_name}/{slot_label} ({provider})")

            if preset_missing:
                preset_list = ", ".join(preset_missing)
                banners.append({
                    "id": "missing-preset-api-key",
                    "type": "warning",
                    "priority": 90,
                    "title": "Missing API Key for model presets",
                    "html": f"""No API key configured for preset models: {preset_list}.<br>
                             These presets will not work until you provide the required API keys.<br>
                             {self.CONFIGURE_MODEL_SETTINGS_LINK}""",
                    "dismissible": True,
                    "source": "backend"
                })
