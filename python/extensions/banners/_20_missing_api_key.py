from python.helpers.extension import Extension
from python.helpers import settings as settings_helper
import models


class MissingApiKeyCheck(Extension):
    """Check if API keys are configured for selected model providers."""

    LOCAL_PROVIDERS = ["ollama", "lm_studio"]
    LOCAL_EMBEDDING = ["huggingface"]
    MODEL_TYPE_NAMES = {
        "chat": "Chat Model",
        "utility": "Utility Model", 
        "browser": "Web Browser Model",
        "embedding": "Embedding Model",
    }

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        current_settings = settings_helper.get_settings()
        model_providers = {
            "chat": current_settings.get("chat_model_provider", ""),
            "utility": current_settings.get("util_model_provider", ""),
            "browser": current_settings.get("browser_model_provider", ""),
            "embedding": current_settings.get("embed_model_provider", ""),
        }
        
        missing_providers = []
        
        for model_type, provider in model_providers.items():
            if not provider:
                continue
            
            provider_lower = provider.lower()
            if provider_lower in self.LOCAL_PROVIDERS:
                continue
            if model_type == "embedding" and provider_lower in self.LOCAL_EMBEDDING:
                continue
            
            api_key = models.get_api_key(provider_lower)
            if not (api_key and api_key.strip() and api_key != "None"):
                missing_providers.append({
                    "model_type": self.MODEL_TYPE_NAMES.get(model_type, model_type),
                    "provider": provider,
                })
        
        if not missing_providers:
            return
        
        model_list = ", ".join(
            f"{p['model_type']} ({p['provider']})" for p in missing_providers
        )
        
        banners.append({
            "id": "missing-api-key",
            "type": "error",
            "priority": 100,
            "title": "Missing API Key",
            "html": f"""No API key configured for: {model_list}. 
                     Agent Zero will not be able to function properly. 
                     <a href="#" onclick="document.getElementById('settings').click(); return false;">
                     Add your API key</a> in Settings → External Services → API Keys.""",
            "dismissible": False,
            "source": "backend"
        })
