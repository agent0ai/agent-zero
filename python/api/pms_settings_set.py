"""
PMS Settings Set API
Configure and manage PMS provider settings
"""

import sys
from pathlib import Path
from python.helpers.api import ApiHandler, Request, Response

# Add instruments path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "instruments" / "custom"))


class PMSSettingsSet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Configure PMS provider settings

        Args:
            input: Request parameters
                - action: add, update, remove, enable, disable
                - provider_id: Provider identifier
                - provider_type: Type for new providers
                - name: Display name
                - credentials: API credentials dict
                - options: Provider-specific options

        Returns:
            Response with result
        """
        try:
            from pms_hub.provider_registry import ProviderRegistry
            from pms_hub.pms_provider import ProviderType

            action = input.get("action", "").lower()

            if action == "add":
                return await self._add_provider(input)
            elif action == "update":
                return await self._update_provider(input)
            elif action == "remove":
                return await self._remove_provider(input)
            elif action == "enable":
                return await self._enable_provider(input, True)
            elif action == "disable":
                return await self._enable_provider(input, False)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "valid_actions": ["add", "update", "remove", "enable", "disable"],
                }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "code": 500,
            }

    async def _add_provider(self, input: dict) -> dict:
        """Add new provider"""
        from pms_hub.provider_registry import ProviderRegistry
        from pms_hub.pms_provider import ProviderType

        registry = ProviderRegistry()

        provider_id = input.get("provider_id", "").strip()
        provider_type = input.get("provider_type", "").lower().strip()
        name = input.get("name", provider_type)
        credentials = input.get("credentials", {})

        if not provider_id:
            return {
                "status": "error",
                "message": "provider_id is required",
            }

        if not provider_type:
            return {
                "status": "error",
                "message": "provider_type is required",
                "valid_types": [t.value for t in ProviderType],
            }

        try:
            prov_type = ProviderType(provider_type)
        except ValueError:
            return {
                "status": "error",
                "message": f"Invalid provider_type: {provider_type}",
                "valid_types": [t.value for t in ProviderType],
            }

        if not credentials or not isinstance(credentials, dict):
            return {
                "status": "error",
                "message": "credentials dict is required",
            }

        # Register provider
        success = registry.register_provider(
            provider_id=provider_id,
            provider_type=prov_type,
            name=name,
            credentials=credentials,
            enabled=True,
        )

        if success:
            return {
                "status": "success",
                "message": f"Provider '{name}' added successfully",
                "provider_id": provider_id,
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to add provider",
            }

    async def _update_provider(self, input: dict) -> dict:
        """Update provider configuration"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()

        provider_id = input.get("provider_id", "").strip()
        if not provider_id:
            return {
                "status": "error",
                "message": "provider_id is required",
            }

        credentials = input.get("credentials")
        options = input.get("options")

        success = registry.update_provider_config(
            provider_id=provider_id,
            credentials=credentials,
            options=options,
        )

        if success:
            return {
                "status": "success",
                "message": f"Provider '{provider_id}' updated successfully",
            }
        else:
            return {
                "status": "error",
                "message": f"Provider '{provider_id}' not found or update failed",
            }

    async def _remove_provider(self, input: dict) -> dict:
        """Remove provider"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()

        provider_id = input.get("provider_id", "").strip()
        if not provider_id:
            return {
                "status": "error",
                "message": "provider_id is required",
            }

        success = registry.unregister_provider(provider_id)

        if success:
            return {
                "status": "success",
                "message": f"Provider '{provider_id}' removed successfully",
            }
        else:
            return {
                "status": "error",
                "message": f"Provider '{provider_id}' not found",
            }

    async def _enable_provider(self, input: dict, enable: bool) -> dict:
        """Enable or disable provider"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()

        provider_id = input.get("provider_id", "").strip()
        if not provider_id:
            return {
                "status": "error",
                "message": "provider_id is required",
            }

        success = registry.update_provider_config(provider_id=provider_id, enabled=enable)

        action = "enabled" if enable else "disabled"
        if success:
            return {
                "status": "success",
                "message": f"Provider '{provider_id}' {action}",
            }
        else:
            return {
                "status": "error",
                "message": f"Provider '{provider_id}' not found",
            }
