"""
PMS Settings Get API
Retrieve PMS provider configurations and settings
"""

import sys
from pathlib import Path
from python.helpers.api import ApiHandler, Request, Response

# Add instruments path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "instruments" / "custom"))


class PMSSettingsGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Get PMS settings and provider configurations

        Args:
            input: Request parameters
                - provider_id: Optional specific provider ID

        Returns:
            Response with settings
        """
        try:
            from pms_hub.provider_registry import ProviderRegistry

            registry = ProviderRegistry()
            provider_id = input.get("provider_id")

            if provider_id:
                # Get specific provider config
                config = registry.get_provider_config(provider_id)
                if not config:
                    return {
                        "status": "error",
                        "message": f"Provider not found: {provider_id}",
                        "code": 404,
                    }

                return {
                    "status": "success",
                    "provider": {
                        "id": provider_id,
                        "type": config.provider_type.value,
                        "name": config.name,
                        "enabled": config.enabled,
                        # Don't expose credentials in response
                        "has_credentials": bool(config.credentials),
                    },
                }
            else:
                # Get all providers
                providers = []
                for pid in registry.list_providers():
                    config = registry.get_provider_config(pid)
                    providers.append(
                        {
                            "id": pid,
                            "type": config.provider_type.value,
                            "name": config.name,
                            "enabled": config.enabled,
                            "has_credentials": bool(config.credentials),
                        }
                    )

                return {
                    "status": "success",
                    "providers": providers,
                    "total": len(providers),
                    "enabled_count": sum(1 for p in providers if p["enabled"]),
                }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "code": 500,
            }
