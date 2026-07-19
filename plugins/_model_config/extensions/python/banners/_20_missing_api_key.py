from helpers.extension import Extension
from plugins._model_config.helpers import model_config


class MissingApiKeyCheck(Extension):
    """Check if API keys are configured for selected model providers."""

    LOCAL_PROVIDERS = {"ollama", "lm_studio", "llama_cpp", "omlx", "vllm"}
    ONBOARDING_MODAL_PATH = "/plugins/_onboarding/webui/onboarding.html"
    ONBOARDING_CTA_TEXT = "Start Onboarding"

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        missing_providers = model_config.get_missing_api_key_providers()

        if missing_providers:
            banners.append({
                "id": "missing-api-key",
                "type": "warning",
                "priority": 100,
                "title": "Welcome to Agent Zero!",
                "html": f"""You're almost ready to chat. Please configure your models to continue.<br>
                         Insert your API key in the onboarding wizard.""",
                "cta_text": self.ONBOARDING_CTA_TEXT,
                "cta_action": f"open-modal:{self.ONBOARDING_MODAL_PATH}",
                "dismissible": False,
                "source": "backend",
                # For programmatic clients (e.g. chat composer) reusing this banner pipeline
                "missing_providers": missing_providers,
            })

        # Check preset providers for missing API keys (warning level)
        preset_missing = []
        seen = set()
        for preset in model_config.get_presets():
            preset_name = preset.get("name", "Unnamed")
            for slot_key, slot_label, model_type in [
                ("chat", "Main", "chat"),
                ("utility", "Utility", "chat"),
                ("embedding", "Embedding", "embedding"),
            ]:
                slot = preset.get(slot_key, {})
                provider = slot.get("provider", "")
                if not provider:
                    continue
                provider_lower = provider.lower()
                identity = (provider_lower, model_type)
                if (
                    provider_lower in self.LOCAL_PROVIDERS
                    or model_type == "embedding"
                    and provider_lower in model_config.LOCAL_EMBEDDING
                    or identity in seen
                ):
                    continue
                if slot.get("api_key", "").strip():
                    continue
                if not model_config.has_provider_api_key(
                    provider_lower,
                    model_type=model_type,
                ):
                    seen.add(identity)
                    preset_missing.append(f"{preset_name}/{slot_label} ({provider})")

        if preset_missing:
            preset_list = ", ".join(preset_missing)
            banners.append({
                "id": "missing-preset-api-key",
                "type": "warning",
                "priority": 90,
                "title": "Missing API Key for model presets",
                "html": f"""No API key configured for preset models: {preset_list}.<br>
                         These presets will not work until you provide the required API keys.""",
                "cta_text": self.ONBOARDING_CTA_TEXT,
                "cta_action": f"open-modal:{self.ONBOARDING_MODAL_PATH}",
                "dismissible": True,
                "source": "backend"
            })
