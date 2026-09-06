"""Strict, production-only credential controls for the proven current bridge."""
import asyncio

from plugins._a0_connector.helpers.browser_bridge_context_controller import _request_document, _exact_keys, _contract, _identifier
from plugins._a0_connector.helpers.browser_bridge_credentials import get_browser_bridge_credential_store
from plugins._a0_connector.helpers.browser_bridge_runtime import BrowserBridgeRuntimeDenied
from plugins._a0_connector.helpers.browser_bridge_transport import PRODUCTION_BROWSER_BRIDGE_TRANSPORT


class BrowserBridgeCredentialController:
    def __init__(self, *, manager, current, server_instance_id, retire_bridge, credentials=None):
        self.manager, self.current = manager, current
        self.server_instance_id, self.retire_bridge = server_instance_id, retire_bridge
        self.credentials = credentials or get_browser_bridge_credential_store()
        self._tasks = set()

    async def dispatch(self, route, document):
        request = _request_document(document)
        action = request.get("action")
        extra = {"rotation_id", "public_key"} if action == "rotate" else {"rotation_id"} if action == "status" else set()
        _exact_keys(request, required={"contract_version", "action"} | extra)
        _contract(request)
        principal = route.principal
        if (action not in {"rotate", "status", "revoke"}
            or route.transport_profile is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT
            or principal.principal_type != "browser_bridge"
            or "bridge.connect" not in principal.scopes or not self.current(route)):
            raise BrowserBridgeRuntimeDenied("SCOPE_DENIED")
        identity = dict(bridge_id=principal.principal_id, server_id=self.server_instance_id(),
                        subject_id=principal.subject_id, key_generation=principal.key_generation)
        if action in {"rotate", "status"}:
            rotation_id = _identifier(request["rotation_id"], "rotation_id")
            if action == "rotate":
                result = self.credentials.begin(**identity, rotation_id=rotation_id, public_key=request["public_key"])
            else:
                result = self.credentials.status(**identity, rotation_id=rotation_id)
            if not self.current(route):
                raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
            return {"action": action, **result}
        # Durable denial precedes all network awaits. Cancellation may not undo
        # revocation or cancel process-owned negative session cleanup.
        revoked = self.credentials.self_revoke(**identity)
        if revoked is None:
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
        from plugins._a0_connector.helpers.browser_bridge_auth import get_browser_bridge_challenge_store
        get_browser_bridge_challenge_store().invalidate_bridge(identity["bridge_id"], identity["server_id"])
        self.retire_bridge(identity["bridge_id"])
        result = {"contract_version": 1, "action": "revoke", "rotation_id": None,
                  "key_generation": principal.key_generation, "status": "revoked", "expires_at_ms": None}
        task = asyncio.create_task(self._notify_and_disconnect(route, result))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        await asyncio.shield(task)
        return result

    async def _notify_and_disconnect(self, route, result):
        profile = PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        try:
            await asyncio.wait_for(self.manager.emit_to(profile.namespace, route.connector_sid,
                "connector_bridge_credential_status", result, handler_id=profile.handler_id,
                expected_principal=route.principal), timeout=5)
        except Exception:
            pass  # Durable denial already exists; notification is not a success prerequisite.
        with self.manager.lock:
            targets = [(namespace, sid, info.principal) for (namespace, sid), info in self.manager.connections.items()
                       if info.principal is not None and info.principal.principal_type == "browser_bridge"
                       and info.principal.principal_id == route.principal.principal_id
                       and info.principal.subject_id == route.principal.subject_id]
        for namespace, sid, principal in targets:
            with self.manager.lock:
                current = self.manager.connections.get((namespace, sid))
                if current is None or current.principal is not principal:
                    continue
            try:
                await asyncio.wait_for(self.manager.socketio.disconnect(sid, namespace=namespace), timeout=5)
            except Exception:
                pass

    async def close(self):
        if self._tasks:
            await asyncio.gather(*tuple(self._tasks), return_exceptions=True)
