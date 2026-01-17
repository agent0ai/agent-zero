"""
PMS Hub Tool
Main interface for property management system integration
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from python.helpers.tool import Response, Tool

# Add instruments path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "instruments" / "custom"))


class PMSHub(Tool):
    """
    PMS Hub Tool - Multi-provider vacation rental management
    Integrates with AirBnb, Hostaway, Lodgify, Hostify, and other platforms
    """

    async def execute(self, **kwargs):
        """
        Execute PMS Hub operations

        Args:
            action (str): Action to perform
            Various action-specific parameters
        """

        from pms_hub.provider_registry import ProviderRegistry
        from pms_hub.sync_service import PMSSyncService
        from pms_hub.pms_provider import ProviderType

        action = kwargs.get("action", "status")

        try:
            if action == "status":
                return await self._get_status()

            elif action == "list_providers":
                return await self._list_providers()

            elif action == "register_provider":
                return await self._register_provider(kwargs)

            elif action == "unregister_provider":
                return await self._unregister_provider(kwargs)

            elif action == "get_reservations":
                return await self._get_reservations(kwargs)

            elif action == "get_properties":
                return await self._get_properties(kwargs)

            elif action == "get_calendar":
                return await self._get_calendar(kwargs)

            elif action == "send_message":
                return await self._send_message(kwargs)

            elif action == "sync_reservations":
                return await self._sync_reservations(kwargs)

            elif action == "sync_status":
                return await self._get_sync_status()

            else:
                return Response(
                    status="error",
                    data={"message": f"Unknown action: {action}"},
                )

        except Exception as e:
            return Response(status="error", data={"error": str(e)})

    async def _get_status(self) -> Response:
        """Get PMS Hub status"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()
        providers = registry.list_providers()

        return Response(
            status="success",
            data={
                "message": "PMS Hub is operational",
                "providers_registered": len(providers),
                "providers_enabled": len(registry.list_providers(enabled_only=True)),
                "providers": providers,
            },
        )

    async def _list_providers(self) -> Response:
        """List all registered providers"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()

        provider_list = []
        for provider_id in registry.list_providers():
            config = registry.get_provider_config(provider_id)
            provider_list.append(
                {
                    "id": provider_id,
                    "type": config.provider_type.value,
                    "name": config.name,
                    "enabled": config.enabled,
                }
            )

        return Response(status="success", data={"providers": provider_list})

    async def _register_provider(self, kwargs) -> Response:
        """Register a new PMS provider"""
        from pms_hub.provider_registry import ProviderRegistry
        from pms_hub.pms_provider import ProviderType

        registry = ProviderRegistry()

        provider_type_str = kwargs.get("provider_type", "").lower()
        provider_id = kwargs.get("provider_id", "")
        name = kwargs.get("name", provider_type_str)
        credentials = kwargs.get("credentials", {})

        try:
            provider_type = ProviderType(provider_type_str)
        except ValueError:
            return Response(
                status="error",
                data={
                    "message": f"Invalid provider type: {provider_type_str}",
                    "valid_types": [t.value for t in ProviderType],
                },
            )

        if not provider_id:
            return Response(status="error", data={"message": "provider_id is required"})

        if not credentials:
            return Response(status="error", data={"message": "credentials are required"})

        # Register provider
        success = registry.register_provider(
            provider_id=provider_id,
            provider_type=provider_type,
            name=name,
            credentials=credentials,
            enabled=True,
        )

        if success:
            return Response(
                status="success",
                data={
                    "message": f"Provider {provider_id} registered successfully",
                    "provider_id": provider_id,
                },
            )
        else:
            return Response(
                status="error",
                data={"message": f"Failed to register provider {provider_id}"},
            )

    async def _unregister_provider(self, kwargs) -> Response:
        """Unregister a PMS provider"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()
        provider_id = kwargs.get("provider_id", "")

        if not provider_id:
            return Response(status="error", data={"message": "provider_id is required"})

        success = registry.unregister_provider(provider_id)

        if success:
            return Response(
                status="success",
                data={"message": f"Provider {provider_id} unregistered"},
            )
        else:
            return Response(
                status="error",
                data={"message": f"Provider {provider_id} not found"},
            )

    async def _get_reservations(self, kwargs) -> Response:
        """Get reservations from a provider"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()
        provider_id = kwargs.get("provider_id", "")
        property_id = kwargs.get("property_id")
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")

        if not provider_id:
            return Response(status="error", data={"message": "provider_id is required"})

        try:
            provider = await registry.get_provider_async(provider_id)
            if not provider:
                return Response(
                    status="error",
                    data={"message": f"Provider not found: {provider_id}"},
                )

            # Parse dates if provided
            from datetime import datetime

            check_in = None
            check_out = None
            if start_date:
                check_in = datetime.fromisoformat(start_date).date()
            if end_date:
                check_out = datetime.fromisoformat(end_date).date()

            # Fetch reservations
            reservations = await provider.get_reservations(
                property_id=property_id,
                start_date=check_in,
                end_date=check_out,
            )

            reservation_list = [
                {
                    "id": r.provider_id,
                    "property_id": r.property_provider_id,
                    "guest": r.guest_name,
                    "email": r.guest_email,
                    "check_in": r.check_in_date.isoformat(),
                    "check_out": r.check_out_date.isoformat(),
                    "nights": r.nights,
                    "total_price": str(r.total_price),
                    "status": r.status.value,
                }
                for r in reservations
            ]

            return Response(
                status="success",
                data={
                    "message": f"Retrieved {len(reservation_list)} reservations",
                    "reservations": reservation_list,
                },
            )

        except Exception as e:
            return Response(status="error", data={"error": str(e)})

    async def _get_properties(self, kwargs) -> Response:
        """Get properties from a provider"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()
        provider_id = kwargs.get("provider_id", "")

        if not provider_id:
            return Response(status="error", data={"message": "provider_id is required"})

        try:
            provider = await registry.get_provider_async(provider_id)
            if not provider:
                return Response(
                    status="error",
                    data={"message": f"Provider not found: {provider_id}"},
                )

            properties = await provider.get_properties()

            property_list = [
                {
                    "id": p.provider_id,
                    "name": p.name,
                    "city": p.city,
                    "state": p.state,
                    "bedrooms": p.bedrooms,
                    "bathrooms": p.bathrooms,
                    "max_guests": p.max_guests,
                    "base_price": str(p.base_price),
                }
                for p in properties
            ]

            return Response(
                status="success",
                data={
                    "message": f"Retrieved {len(property_list)} properties",
                    "properties": property_list,
                },
            )

        except Exception as e:
            return Response(status="error", data={"error": str(e)})

    async def _get_calendar(self, kwargs) -> Response:
        """Get calendar/availability from a provider"""
        from pms_hub.provider_registry import ProviderRegistry
        from datetime import datetime

        registry = ProviderRegistry()
        provider_id = kwargs.get("provider_id", "")
        property_id = kwargs.get("property_id", "")
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")

        if not provider_id or not property_id:
            return Response(
                status="error",
                data={"message": "provider_id and property_id are required"},
            )

        try:
            provider = await registry.get_provider_async(provider_id)
            if not provider:
                return Response(
                    status="error",
                    data={"message": f"Provider not found: {provider_id}"},
                )

            check_in = None
            check_out = None
            if start_date:
                check_in = datetime.fromisoformat(start_date).date()
            if end_date:
                check_out = datetime.fromisoformat(end_date).date()

            calendar = await provider.get_calendar(
                property_id=property_id,
                start_date=check_in,
                end_date=check_out,
            )

            calendar_list = [
                {
                    "date": c.date.isoformat(),
                    "status": c.status,
                    "price": str(c.price) if c.price else None,
                    "min_nights": c.min_nights,
                }
                for c in calendar
            ]

            return Response(
                status="success",
                data={
                    "message": f"Retrieved {len(calendar_list)} calendar days",
                    "calendar": calendar_list,
                },
            )

        except Exception as e:
            return Response(status="error", data={"error": str(e)})

    async def _send_message(self, kwargs) -> Response:
        """Send message to guest through PMS"""
        from pms_hub.provider_registry import ProviderRegistry

        registry = ProviderRegistry()
        provider_id = kwargs.get("provider_id", "")
        reservation_id = kwargs.get("reservation_id", "")
        subject = kwargs.get("subject", "Message from Host")
        body = kwargs.get("body", "")

        if not provider_id or not reservation_id or not body:
            return Response(
                status="error",
                data={
                    "message": "provider_id, reservation_id, and body are required"
                },
            )

        try:
            provider = await registry.get_provider_async(provider_id)
            if not provider:
                return Response(
                    status="error",
                    data={"message": f"Provider not found: {provider_id}"},
                )

            success = await provider.send_message(reservation_id, subject, body)

            if success:
                return Response(
                    status="success",
                    data={"message": "Message sent successfully"},
                )
            else:
                return Response(
                    status="error",
                    data={"message": "Failed to send message"},
                )

        except Exception as e:
            return Response(status="error", data={"error": str(e)})

    async def _sync_reservations(self, kwargs) -> Response:
        """Sync reservations from PMS to property_manager"""
        from pms_hub.sync_service import PMSSyncService

        provider_id = kwargs.get("provider_id", "")

        if not provider_id:
            return Response(status="error", data={"message": "provider_id is required"})

        try:
            sync = PMSSyncService()
            synced, errors = await sync.sync_all_reservations(provider_id)

            return Response(
                status="success",
                data={
                    "message": f"Sync completed: {synced} synced, {errors} errors",
                    "synced": synced,
                    "errors": errors,
                },
            )

        except Exception as e:
            return Response(status="error", data={"error": str(e)})

    async def _get_sync_status(self) -> Response:
        """Get sync status"""
        from pms_hub.sync_service import PMSSyncService

        try:
            sync = PMSSyncService()
            status = await sync.get_sync_status()

            return Response(status="success", data={"sync_status": status})

        except Exception as e:
            return Response(status="error", data={"error": str(e)})
