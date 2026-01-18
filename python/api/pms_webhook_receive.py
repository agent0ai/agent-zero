"""
PMS Webhook Receiver API
Handles incoming webhooks from PMS providers (Hostaway, Lodgify, Hostify)
Routes webhooks to appropriate handlers and emits events to EventBus
"""

import json
from typing import Any

from instruments.custom.pms_hub.provider_registry import ProviderRegistry
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.event_bus import EventBus, EventStore


class PMSWebhookReceive(ApiHandler):
    """
    Webhook receiver for PMS providers

    Endpoint: POST /api/pms/webhook/{provider}/{provider_id}
    Headers: signature (for verification where applicable)
    Body: JSON webhook payload
    """

    def __init__(self, app, thread_lock):
        """Initialize webhook receiver"""
        super().__init__(app, thread_lock)
        self.registry = ProviderRegistry()
        # Initialize event bus
        import os

        db_path = os.path.join(os.path.expanduser("~"), ".pms_hub", "events.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.event_store = EventStore(db_path)
        self.event_bus = EventBus(self.event_store)

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Process incoming webhook

        Args:
            input: Request input containing:
                - provider: PMS provider type (hostaway, lodgify, hostify)
                - provider_id: Registered provider ID
                - event: Event type/name
                - payload: Webhook payload
            request: HTTP request object

        Returns:
            Response dict with status
        """
        try:
            # Extract webhook parameters
            provider = input.get("provider", "").lower()
            provider_id = input.get("provider_id", "")
            signature = input.get("signature", "")
            payload = input.get("payload", {})

            # Validate required parameters
            if not provider or not provider_id:
                return {
                    "status": "error",
                    "message": "Missing provider or provider_id",
                    "code": 400,
                }

            # Get provider configuration
            config = self.registry.get_provider_config(provider_id)
            if not config or not config.enabled:
                return {
                    "status": "error",
                    "message": "Provider not found or disabled",
                    "code": 404,
                }

            # Verify webhook signature if provider supports it
            if not await self._verify_webhook(provider_id, payload, signature):
                return {
                    "status": "error",
                    "message": "Invalid webhook signature",
                    "code": 401,
                }

            # Emit event to event bus
            event_type = f"pms.webhook.{provider}.{input.get('event', 'unknown')}"
            event = await self.event_bus.emit(
                event_type,
                {
                    "provider": provider,
                    "provider_id": provider_id,
                    "payload": payload,
                    "webhook_timestamp": input.get("timestamp"),
                },
            )

            return {
                "status": "success",
                "message": "Webhook received and queued for processing",
                "event_id": event["id"],
            }

        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON payload",
                "code": 400,
            }
        except Exception as e:
            print(f"Error processing PMS webhook: {e}")
            return {
                "status": "error",
                "message": str(e),
                "code": 500,
            }

    async def _verify_webhook(self, provider_id: str, payload: dict[str, Any], signature: str) -> bool:
        """
        Verify webhook signature

        Args:
            provider_id: Provider ID
            payload: Webhook payload
            signature: Signature to verify

        Returns:
            True if signature is valid
        """
        if not signature:
            # No signature provided - some providers don't require it
            return True

        try:
            provider = await self.registry.get_provider_async(provider_id)
            if not provider:
                return False

            # Use provider's verify_webhook method
            return provider.verify_webhook(payload, signature)
        except Exception as e:
            print(f"Webhook verification error: {e}")
            return False
