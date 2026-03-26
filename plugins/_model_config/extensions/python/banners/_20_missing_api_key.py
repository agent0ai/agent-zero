from helpers.extension import Extension
from helpers import plugins
from plugins._model_config.helpers import model_config


class MissingApiKeyCheck(Extension):
    """Check if API keys are configured for selected model providers."""

    LOCAL_PROVIDERS = {"ollama", "lm_studio"}
    LOCAL_EMBEDDING = {"huggingface"}
    CONFIGURE_MODEL_SETTINGS_LINK = (
        """<a href="#" onclick="(async()=>{"""
        """const { store: s } = await import('/components/plugins/plugin-settings-store.js');"""
        """if(s&&s.openConfig){await s.openConfig('_model_config');}"""
        """})();return false;">"""
        """Configure model settings</a>"""
    )

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        cfg = plugins.get_plugin_config("_model_config") or {}
        missing_providers = []
        checks = [
            ("Chat Model", cfg.get("chat_model", {})),
            ("Utility Model", cfg.get("utility_model", {})),
            ("Embedding Model", cfg.get("embedding_model", {})),
        ]

        for label, model_cfg in checks:
            provider = model_cfg.get("provider", "")
            if not provider:
                continue
            provider_lower = provider.lower()
            if provider_lower in self.LOCAL_PROVIDERS:
                continue
            if label == "Embedding Model" and provider_lower in self.LOCAL_EMBEDDING:
                continue

            if not model_config.has_provider_api_key(
                provider_lower,
                model_cfg.get("api_key", ""),
            ):
                missing_providers.append({
                    "model_type": label,
                    "provider": provider,
                })
        
        if missing_providers:
            model_list = ", ".join(
                f"{p['model_type']} ({p['provider']})" for p in missing_providers
            )
            
            banners.append({
                "id": "missing-api-key",
                "type": "error",
                "priority": 100,
                "title": "Missing LLM API Key for current settings",
                "html": f"""No API key configured for: {model_list}.<br>
                         Agent Zero will not be able to function properly unless you provide an API key or change your settings.<br>
                         {self.CONFIGURE_MODEL_SETTINGS_LINK}""",
                "dismissible": False,
                "source": "backend"
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
