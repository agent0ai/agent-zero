"""Exact authenticated route adapter for explicit companion-local decisions."""

from plugins._a0_connector.helpers.browser_bridge_context_controller import (
    _request_document, _exact_keys, _contract, _identifier,
)
from plugins._a0_connector.helpers.browser_bridge_runtime import BrowserBridgeRuntimeDenied


class BrowserBridgeLocalApprovalController:
    def __init__(self, *, actions, sites, current):
        self.actions, self.sites, self.current = actions, sites, current

    async def dispatch(self, route, document):
        request = _request_document(document)
        _exact_keys(request, required={"contract_version", "challenge_id", "kind", "decision"})
        _contract(request)
        challenge_id = _identifier(request["challenge_id"], "challenge_id")
        if not self.current(route) or "browser.approval" not in route.principal.scopes:
            raise BrowserBridgeRuntimeDenied("SCOPE_DENIED")
        kind, decision = request["kind"], request["decision"]
        if kind == "site" and decision in ("deny", "allow_once", "allow_turn"):
            receipt = await self.sites.decide(subject_id=route.principal.subject_id,
                                              challenge_id=challenge_id, decision=decision,
                                              expected_route=route)
        elif kind == "action" and decision in ("decline", "approve_once"):
            receipt = await self.actions.decide(subject_id=route.principal.subject_id,
                                                challenge_id=challenge_id, choice=decision,
                                                expected_route=route)
        else:
            raise BrowserBridgeRuntimeDenied("INVALID_STATE")
        # Public projection says accepted, never that Chrome applied the action.
        return {"contract_version": 1, **receipt.as_public_dict()}
