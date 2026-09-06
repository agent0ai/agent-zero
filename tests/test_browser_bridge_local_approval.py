import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest

from plugins._a0_connector.helpers.browser_bridge_local_approval import BrowserBridgeLocalApprovalController
from plugins._a0_connector.helpers.browser_bridge_action_authority import BrowserBridgeActionAuthorityUnavailable
from test_browser_bridge_action_authority import _Harness, _operation, _notice, _principal


def test_local_action_decision_requires_exact_retained_route_not_only_same_subject():
    async def scenario():
        h = _Harness(_operation(asyncio.get_running_loop(), _principal()))
        h.authority.register_challenge(_notice(h.operation))
        controller = BrowserBridgeLocalApprovalController(actions=h.authority, sites=None, current=lambda route: True)
        fixture = json.loads((Path(__file__).parent / "fixtures/context-queue-approval-v1.json").read_text())
        body = fixture["action_approval"]["params"]
        route = h.current_route
        for forged in (
            replace(route, connector_sid="sid-other"),
            replace(route, load_generation_id="generation-other"),
            replace(route, principal=replace(route.principal)),
        ):
            with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
                await controller.dispatch(forged, body)
        assert not h.resolutions
        result = await controller.dispatch(route, body)
        assert result["status"] == "accepted"
        assert result["challenge_id"] == "challenge-A"
        assert result == fixture["action_approval"]["result"]
        assert (await controller.dispatch(route, body)) == result
        await h.authority.close()
    asyncio.run(scenario())


def test_local_site_decision_cannot_cross_same_subject_bridge_socket():
    from test_browser_bridge_site_authority import _Harness, _operation, _notice, _principal
    from plugins._a0_connector.helpers.browser_bridge_site_authority import BrowserBridgeSiteAuthorityUnavailable

    async def scenario():
        principal = _principal()
        h = _Harness(_operation(asyncio.get_running_loop(), principal))
        sites = h.repository()
        sites.register_event(_notice(principal))
        controller = BrowserBridgeLocalApprovalController(actions=None, sites=sites, current=lambda route: True)
        body = {"contract_version": 1, "challenge_id": "challenge-A", "kind": "site", "decision": "allow_once"}
        with pytest.raises(BrowserBridgeSiteAuthorityUnavailable):
            await controller.dispatch(replace(h.current_route, connector_sid="another-socket"), body)
        assert not h.resolutions
        assert (await controller.dispatch(h.current_route, body))["status"] == "accepted"
        await sites.close()
    asyncio.run(scenario())
