"""Server-owned composition of the implemented bridge controllers.

This is not an activation switch. Typed transport admission and all release/
cutover prerequisites are required for a provisional route. Exact reconciliation
must promote it before context or browser-operation authority exists. No legacy
registry is used.
"""

import asyncio
import logging
import threading
import uuid
from typing import Any, Callable

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_context import BrowserBridgeContextAccess, BrowserBridgeContextRoute
from plugins._a0_connector.helpers.browser_bridge_context_controller import BrowserBridgeContextController
from plugins._a0_connector.helpers.browser_bridge_events import BrowserBridgeCriticalEventReceiver
from plugins._a0_connector.helpers.browser_bridge_artifacts import ArtifactBinding, BrowserBridgeArtifactReceiver
from plugins._a0_connector.helpers.browser_bridge_artifact_controller import BrowserBridgeArtifactController
from plugins._a0_connector.helpers.browser_bridge_artifact_sender import BrowserBridgeArtifactSender
from plugins._a0_connector.helpers.browser_bridge_site_authority import BrowserBridgeSiteAuthorityRepository
from plugins._a0_connector.helpers.browser_bridge_action_authority import BrowserBridgeActionAuthority
from plugins._a0_connector.helpers.browser_bridge_messages import BrowserBridgeMessageDispatcher
from plugins._a0_connector.helpers.browser_bridge_queue import BrowserBridgeQueueController, QUEUE_EVENTS
from plugins._a0_connector.helpers.browser_bridge_local_approval import BrowserBridgeLocalApprovalController
from plugins._a0_connector.helpers.browser_bridge_credential_control import BrowserBridgeCredentialController
from plugins._a0_connector.helpers.browser_bridge_policy import BrowserBridgePolicyRepository
from plugins._a0_connector.helpers.browser_bridge_operations import ReconciliationBinding
from plugins._a0_connector.helpers.browser_bridge_reconciliation import (
    BrowserBridgeReconciliationController, ReconciliationSnapshot, ExpectedReconciliationContext,
)
from plugins._a0_connector.helpers.browser_bridge_runtime import (
    BrowserBridgeRuntimeRegistry, BrowserBridgeRuntimeDenied, restricted_browser_sender,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
)
from plugins._browser.helpers.extension_services import ExtensionBrowserServices
from plugins._browser.helpers.extension_artifacts import ExtensionScreenshotMaterializer
from plugins._browser.helpers.extension_sessions import ExtensionSessionLifecycle, TURN_ACTIVE


_CONTEXT_EVENTS = frozenset({
    "connector_context_list", "connector_subscribe_context",
    "connector_unsubscribe_context", "connector_send_message",
})

_STAGE_CODES = frozenset({
    "INITIAL_HELLO_ADMITTED", "RENEWED_HELLO_OBSERVED", "HELLO_REJECTED",
    "RECONCILIATION_STARTED", "RECONCILIATION_SUCCEEDED", "RECONCILIATION_RESULT_RECEIVED",
    "RECONCILIATION_RESULT_REJECTED", "RECONCILIATION_TIMEOUT", "RECONCILIATION_CONNECTION_LOST",
    "RECONCILIATION_SCOPE_DENIED", "RECONCILIATION_INVALID_SNAPSHOT", "RECONCILIATION_INVALID_REQUEST",
    "RECONCILIATION_CAPACITY", "RECONCILIATION_OTHER_FAILURE",
    "RECONCILIATION_INVALID_STATE", "RECONCILIATION_UNSUPPORTED_CAPABILITY",
    "RECONCILIATION_INTERNAL_ERROR", "RECONCILIATION_OUTCOME_UNKNOWN",
    "ADMISSION_OWNER_UNAVAILABLE", "ADMISSION_SOCKET_MISMATCH", "ADMISSION_PRINCIPAL_REJECTED",
    "ADMISSION_EXTENSION_MISMATCH", "ADMISSION_ROLLOUT_DISABLED", "ADMISSION_SELECTION_MISSING",
    "ADMISSION_HEARTBEAT_REJECTED", "ADMISSION_LEGACY_PRESENT", "ADMISSION_BOUNDARY_MISSING",
    "ADMISSION_RELEASE_UNVERIFIED", "ADMISSION_RELEASE_MISMATCH", "ADMISSION_CHECK_EXCEPTION",
    "RECONCILIATION_START_SCOPE_LOST", "RECONCILIATION_SNAPSHOT_SCOPE_LOST",
    "RECONCILIATION_BROKER_SCOPE_LOST", "RECONCILIATION_PENDING_SCOPE_LOST",
    "RECONCILIATION_SETTLEMENT_SCOPE_LOST",
})
_stage_counts = {}
_stage_lock = threading.Lock()


def record_production_browser_stage(code):
    """Private bounded diagnostics: fixed symbols only, never peer data."""
    if not isinstance(code, str) or code not in _STAGE_CODES:
        return
    with _stage_lock:
        count = _stage_counts.get(code, 0)
        if count >= 5:
            return
        _stage_counts[code] = count + 1
    logging.getLogger(__name__).warning("Browser bridge stage: %s", code)


def _record_reconciliation_failure(error):
    categories = {
        "TIMEOUT": "RECONCILIATION_TIMEOUT", "DEADLINE_EXCEEDED": "RECONCILIATION_TIMEOUT",
        "CONNECTION_LOST": "RECONCILIATION_CONNECTION_LOST", "SCOPE_DENIED": "RECONCILIATION_SCOPE_DENIED",
        "RECONCILE_RESULT_INVALID": "RECONCILIATION_INVALID_SNAPSHOT",
        "RECONCILE_REQUEST_INVALID": "RECONCILIATION_INVALID_REQUEST",
        "RECONCILIATION_CAPACITY": "RECONCILIATION_CAPACITY",
        "INVALID_STATE": "RECONCILIATION_INVALID_STATE",
        "UNSUPPORTED_CAPABILITY": "RECONCILIATION_UNSUPPORTED_CAPABILITY",
        "INTERNAL_ERROR": "RECONCILIATION_INTERNAL_ERROR",
        "OUTCOME_UNKNOWN": "RECONCILIATION_OUTCOME_UNKNOWN",
    }
    candidate = getattr(error, "code", None)
    record_production_browser_stage(categories.get(candidate, "RECONCILIATION_OTHER_FAILURE")
                                    if isinstance(candidate, str) else "RECONCILIATION_OTHER_FAILURE")


class BrowserBridgeApplication:
    """One owner for route, context, operation, event and cleanup state.

    Dependencies are supplied by authenticated server bootstrap, never an API
    request. Construction does not install Browser selection, broaden principal
    events, advertise readiness, or mutate the live Docker instance.
    """

    def __init__(self, *, manager: Any, server_instance_id: Callable[[], str],
                 lifecycle: ExtensionSessionLifecycle, active_principal_verifier,
                 admission_evaluator, context_authorizer,
                 context_data_source=None, policy_repository=None,
                 message_load=None, message_save=None, message_deliver=None,
                 event_load=None, event_save=None, artifact_spool_parent=None,
                 approval_record_loader=None, selection_current=None,
                 queue_context_get=None, queue_service=None, queue_load=None,
                 queue_save=None, queue_mark_dirty=None,
                 transport_profile: BrowserBridgeTransportProfile =
                 PRODUCTION_BROWSER_BRIDGE_TRANSPORT) -> None:
        self.transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self.registry = BrowserBridgeRuntimeRegistry(
            sender=restricted_browser_sender(
                manager, transport_profile=self.transport_profile
            ),
            active_principal_verifier=active_principal_verifier,
            admission_evaluator=admission_evaluator,
            context_authorizer=context_authorizer,
            cleanup_callbacks=(self._retire_projection,),
            transport_profile=self.transport_profile,
        )
        self.access = BrowserBridgeContextAccess(
            data_source=context_data_source,
            route_authorizer=self.registry.authorize_context_route,
            transport_profile=self.transport_profile,
        )
        policy_repository = policy_repository or BrowserBridgePolicyRepository(
            transport_profile=self.transport_profile
        )
        if policy_repository.transport_profile is not self.transport_profile:
            raise RuntimeError("Browser bridge policy transport mismatch")
        self.browser = ExtensionBrowserServices(
            lifecycle=lifecycle, broker=self.registry.broker,
            route_resolver=self.registry.resolve_extension_route,
            policy_repository=policy_repository,
            server_instance_id=server_instance_id(),
            transport_profile=self.transport_profile,
        )
        self.messages = BrowserBridgeMessageDispatcher(
            access=self.access, server_instance_id=server_instance_id,
            load=message_load, save=message_save, deliver=message_deliver,
            transport_profile=self.transport_profile,
        )
        self.sites = BrowserBridgeSiteAuthorityRepository(
            current_operation=self.registry.broker.current_operation,
            remaining_operation_ms=self.registry.broker.remaining_operation_ms,
            lease_for=self.browser.leases.lease_for,
            route_verifier=self.registry.authorize_context_route,
            begin_resolution=self.registry.broker.begin_site_resolution,
            wait_control=self.registry.broker.wait_control,
            server_instance_id=server_instance_id, turn_current=self._turn_current,
            selection_current=selection_current,
            saved_origin_grant=lambda binding, origin: self._saved_site_grant(
                policy_repository, server_instance_id(), binding, origin),
            transport_profile=self.transport_profile,
        )
        self.browser.site_authority = self.sites
        self.actions = BrowserBridgeActionAuthority(
            current_operation=self.registry.broker.current_operation,
            remaining_operation_ms=self.registry.broker.remaining_operation_ms,
            lease_for=self.browser.leases.lease_for, document_for=self.browser.leases.document_for,
            route_verifier=self.registry.authorize_context_route, turn_current=self._turn_current,
            begin_resolution=self.registry.broker.begin_action_resolution,
            wait_control=self.registry.broker.wait_control, server_instance_id=server_instance_id,
            approval_record_loader=approval_record_loader,
            selection_current=selection_current,
            transport_profile=self.transport_profile,
        )
        self.browser.action_authority = self.actions
        self.local_approvals = BrowserBridgeLocalApprovalController(
            actions=self.actions, sites=self.sites,
            current=self.registry.authorize_context_route,
        )
        self.queues = BrowserBridgeQueueController(
            access=self.access, messages=self.messages, manager=manager,
            server_instance_id=server_instance_id, context_get=queue_context_get,
            queue_service=queue_service, load=queue_load, save=queue_save,
            mark_dirty=queue_mark_dirty,
        )
        self.contexts = BrowserBridgeContextController(
            access=self.access, messages=self.messages, manager=manager,
            route_authorizer=self.registry.authorize_context_route,
            transport_profile=self.transport_profile,
            queue_projection=self.queues.project,
        )
        self.credentials = BrowserBridgeCredentialController(
            manager=manager, current=self.registry.authorize_context_route,
            server_instance_id=server_instance_id, retire_bridge=self.registry.retire_bridge,
        )
        self.artifact_receiver = BrowserBridgeArtifactReceiver(
            spool_parent=artifact_spool_parent, authorizer=self._artifact_current,
            transport_profile=self.transport_profile,
        )
        self.artifacts = BrowserBridgeArtifactController(
            receiver=self.artifact_receiver, binding_resolver=self._artifact_binding,
            manager=manager,
            transport_profile=self.transport_profile,
        )
        self.input_artifacts = BrowserBridgeArtifactSender(
            manager=manager, authorizer=self._input_artifact_current,
        )
        self.browser.input_artifact_sender = self.input_artifacts
        self.browser.artifact_materializer = ExtensionScreenshotMaterializer(
            receiver=self.artifact_receiver, lease_for=self.browser.leases.lease_for,
            current=self._artifact_current,
        )
        self.events = BrowserBridgeCriticalEventReceiver(
            manager=manager, server_instance_id=server_instance_id,
            current_route_verifier=self.registry.authorize_context_route,
            invalidate_lease=self.browser.invalidate_lease_event,
            register_site_challenge=self.sites.register_event,
            register_action_challenge=self.actions.register_event,
            # Informational only. Cleanup settles exclusively via control result.
            observe_finalization=lambda _notice: None,
            load=event_load, save=event_save,
            transport_profile=self.transport_profile,
        )
        self._state_lock = threading.RLock()
        self._closed = False
        self._reconciliation_tasks = {}
        self.reconciliation = BrowserBridgeReconciliationController(
            broker=self.registry.broker, snapshot_source=self._reconciliation_snapshot,
            route_current=self.registry.route_current_for_reconciliation,
            promote=self.registry.promote_reconciled, transport_profile=self.transport_profile,
        )
        self._bootstrap_bound = False

    def _saved_site_grant(self, policy, server_id, binding, origin):
        if not self._turn_current(binding):
            return None
        grant = policy.active_grant(server_instance_id=server_id,
            bridge_id=binding.bridge_id, subject_id=binding.principal.subject_id, origin=origin)
        return grant.grant_id if grant is not None else None

    @property
    def installed(self) -> bool:
        with self._state_lock:
            return not self._closed and self.browser.installed

    def runtime_boundaries(self) -> frozenset[str]:
        """Report implemented owned boundaries, never an activation attestation.

        Input/output transfer, source selection and one-use upload consent are
        composed independently of release and cutover. Those remain the
        startup owner's responsibility, never a claim from a transport peer.
        """
        if not self.installed:
            return frozenset()
        return frozenset({"operation", "control", "context", "event", "artifact", "approval", "lifecycle", "policy"})

    def install(self, *, submitter=None) -> tuple[str, ...]:
        """Explicitly acquire the Browser lifecycle/factory process seams."""

        with self._state_lock:
            if self._closed:
                raise RuntimeError("Browser bridge application is closed")
            return self.browser.install(submitter=submitter)

    def claim_bootstrap_binding(self) -> bool:
        """Claim this installed instance for the one optional process owner."""

        with self._state_lock:
            if self._closed or not self.browser.installed:
                raise RuntimeError("Browser bridge application is not installed")
            if self._bootstrap_bound:
                return False
            self._bootstrap_bound = True
            return True

    def register_hello(self, *, principal: WsPrincipal, connector_sid: str,
                       data: object):
        """Admit one exact route and replay only durable pending cleanup."""

        if not self.installed:
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_INSTALLED")
        previous = self.registry.current_sid_route(principal, connector_sid)
        route = self.registry.register_hello(
            principal=principal,
            connector_sid=connector_sid,
            data=data,
        )
        current = self.registry.current_sid_route(principal, connector_sid)
        if current is not route:
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
        record_production_browser_stage("RENEWED_HELLO_OBSERVED" if previous is not None and previous.hello == route.hello
                                        else "INITIAL_HELLO_ADMITTED")
        # Native sends a repeated hello only after consuming its initial ACK.
        # Initial admission publishes no controls: production native cannot
        # receive a control while it is still waiting for that first ACK.
        if (previous is not None and previous.hello == route.hello
                and not self.registry.current_bridge_ready(route.bridge_id)):
            self._start_reconciliation(route)
        return route

    def _start_reconciliation(self, route):
        binding = ReconciliationBinding(route.principal, route.connector_sid,
                                        route.load_generation_id, uuid.uuid4().hex,
                                        self.transport_profile)
        key = (id(route.principal), route.connector_sid, route.load_generation_id)
        with self._state_lock:
            if self._closed or key in self._reconciliation_tasks:
                return
            if not self.registry.begin_reconciliation(binding):
                return
            try:
                task = self.reconciliation.start(binding, expected_install_instance_id=route.hello.install_instance_id)
            except Exception as error:
                _record_reconciliation_failure(error)
                self.registry.retire_sid(route.principal, route.connector_sid)
                raise
            self._reconciliation_tasks[key] = task
            record_production_browser_stage("RECONCILIATION_STARTED")
            task.add_done_callback(lambda done: self._reconciliation_finished(key, binding, done))

    def _reconciliation_snapshot(self, binding):
        if not self.registry.route_current_for_reconciliation(binding):
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
        contexts = tuple(
            ExpectedReconciliationContext(session.context_id, session.browser_session_id,
                tuple(turn.turn_id for turn in session.turns if turn.state == TURN_ACTIVE))
            for session in self.browser.lifecycle.registry.sessions()
            if session.bridge_id == binding.bridge_id and any(turn.state == TURN_ACTIVE for turn in session.turns)
        )
        controls = tuple(intent.control_id for intent in self.browser.lifecycle.registry.pending_finalizations()
                         if intent.bridge_id == binding.bridge_id)
        return ReconciliationSnapshot(expected_contexts=contexts, known_control_ids=controls)

    def _reconciliation_finished(self, key, binding, task):
        with self._state_lock:
            if self._reconciliation_tasks.get(key) is task:
                self._reconciliation_tasks.pop(key, None)
        try:
            task.result()
        except BaseException as error:
            _record_reconciliation_failure(error)
            current = self.registry.current_sid_route(binding.principal, binding.connector_sid)
            if current is not None and current.load_generation_id == binding.load_generation_id:
                self.registry.retire_sid(binding.principal, binding.connector_sid)
        else:
            if self.registry.route_current_for_reconciliation(binding):
                record_production_browser_stage("RECONCILIATION_SUCCEEDED")
                self.browser.lifecycle.replay_pending()

    def _retire_projection(self, principal, sid, generation) -> None:
        if self.browser.first_open_authority is not None:
            self.browser.first_open_authority.retire(lambda binding: (
                binding.principal is principal and binding.connector_sid == sid
                and binding.load_generation_id == generation))
        self.input_artifacts.retire(principal=principal, connector_sid=sid, load_generation_id=generation)
        self.access.disconnect(principal=principal, connector_sid=sid, load_generation_id=generation)
        self.browser.leases.invalidate(principal=principal, connector_sid=sid, load_generation_id=generation)
        self.sites.disconnect(principal=principal, connector_sid=sid, load_generation_id=generation)
        self.actions.disconnect(principal=principal, connector_sid=sid, load_generation_id=generation)
        self.artifact_receiver.disconnect(principal=principal, connector_sid=sid, load_generation_id=generation)
        # Existing presentation pollers see the absent route on their next
        # bounded tick. Explicit disconnect below additionally awaits teardown.

    def _artifact_current(self, binding: ArtifactBinding) -> bool:
        if not self.registry.authorize_artifact_binding(binding):
            return False
        return self._turn_current(binding)

    def _input_artifact_current(self, binding: ArtifactBinding) -> bool:
        if binding.direction != "input" or binding.purpose != "upload_file" or not self._artifact_current(binding):
            return False
        operation = self.registry.broker.current_operation(
            principal=binding.principal, connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id, op_id=binding.op_id,
        )
        if operation is None or operation.action != "upload_file":
            return False
        if any(getattr(operation.binding, key) != getattr(binding, key) for key in (
            "context_id", "browser_session_id", "turn_id", "action_id", "op_id",
        )):
            return False
        # This exact source permit permits host staging only; the extension's
        # later one-use upload challenge is still required before a site effect.
        consent = getattr(self.browser, "authorize_input_artifact", None)
        return callable(consent) and consent(binding) is True

    def _turn_current(self, binding) -> bool:
        active = self.browser.lifecycle.registry.active_turn_binding(
            context_id=binding.context_id, turn_id=binding.turn_id,
        )
        return bool(active is not None and active.bridge_id == binding.bridge_id
                    and active.browser_session_id == binding.browser_session_id)

    def _artifact_binding(self, lookup) -> ArtifactBinding | None:
        operation = self.registry.broker.current_operation(
            principal=lookup.route.principal, connector_sid=lookup.route.connector_sid,
            load_generation_id=lookup.route.load_generation_id, op_id=lookup.op_id,
        )
        if operation is None or lookup.direction != "output" or operation.action != lookup.purpose:
            return None
        source = operation.binding
        if any(getattr(source, name) != getattr(lookup, name) for name in (
            "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id", "action_id", "op_id",
        )):
            return None
        binding = ArtifactBinding(
            source.principal, source.connector_sid, source.load_generation_id, source.bridge_id,
            source.context_id, source.browser_session_id, source.turn_id, source.action_id, source.op_id,
            lookup.artifact_id, lookup.direction, lookup.purpose,
            transport_profile=self.transport_profile,
        )
        return binding if self._artifact_current(binding) else None

    async def dispatch(self, principal: WsPrincipal, sid: str, event: str, document: Any) -> dict[str, Any]:
        if not isinstance(principal, WsPrincipal) or not principal.permits_inbound(event, principal.handler_id):
            raise BrowserBridgeRuntimeDenied("EVENT_NOT_ALLOWED")
        if not isinstance(document, dict):
            raise BrowserBridgeRuntimeDenied("INVALID_STATE")
        route = self.registry.current_sid_route(principal, sid)
        if route is None:
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
        context_route = BrowserBridgeContextRoute(
            principal,
            sid,
            route.load_generation_id,
            self.transport_profile,
        )
        if event in _CONTEXT_EVENTS:
            return await self.contexts.dispatch(event, context_route, document)
        if event in QUEUE_EVENTS:
            return await self.queues.dispatch(event, context_route, document)
        if event == "connector_bridge_credential_control":
            return await self.credentials.dispatch(context_route, document)
        if event == "connector_browser_approval_decision":
            return await self.local_approvals.dispatch(context_route, document)
        if event == "connector_browser_event":
            return await self.events.receive(context_route, document)
        if event == "connector_browser_artifact_chunk":
            return await self.artifacts.receive(context_route, document)
        if event == "connector_browser_artifact_ack":
            return await self.input_artifacts.receive_ack(context_route, document)
        if event in {"connector_browser_op_result", "connector_browser_control_result"}:
            reconciling = event == "connector_browser_control_result" and document.get("method") == "browser.reconcile"
            if reconciling:
                record_production_browser_stage("RECONCILIATION_RESULT_RECEIVED")
            settle = self.registry.settle_operation if event == "connector_browser_op_result" else self.registry.settle_control
            status = settle(principal=principal, connector_sid=sid,
                            load_generation_id=route.load_generation_id, payload=document)
            if reconciling and status != "settled":
                record_production_browser_stage("RECONCILIATION_RESULT_REJECTED")
            return {"contract_version": 1, "status": status}
        # Unsupported controls never enter a broad callback or legacy handler.
        raise BrowserBridgeRuntimeDenied("EVENT_NOT_IMPLEMENTED")

    async def disconnect(self, principal: WsPrincipal, sid: str) -> bool:
        route = self.registry.retire_sid(principal, sid)
        if route is None:
            return False
        await self.contexts.disconnect(principal=principal, connector_sid=sid,
                                       load_generation_id=route.load_generation_id)
        await self.artifacts.disconnect(principal=principal, connector_sid=sid,
                                        load_generation_id=route.load_generation_id)
        return True

    async def close(self, *, _bootstrap_retirement: bool = False) -> None:
        with self._state_lock:
            if self._bootstrap_bound and not _bootstrap_retirement:
                raise RuntimeError(
                    "retire the bound Browser bridge application explicitly"
                )
            self._closed = True
        # First make Browser hooks/factory inert and durably stage tracked turn
        # cleanup while this application's exact admitted routes still exist.
        try:
            self.browser.uninstall()
        except Exception:
            # A competing owner is never cleared to make shutdown look clean.
            # Route withdrawal below still makes this application unusable.
            pass
        for route in self.registry.retire_all():
            await self.contexts.disconnect(principal=route.principal, connector_sid=route.connector_sid,
                                           load_generation_id=route.load_generation_id)
        # Retirement disconnects retained broker tickets; their process-owned
        # tasks settle without cancellation or replay of uncertain controls.
        with self._state_lock:
            tasks = tuple(self._reconciliation_tasks.values())
        for task in tasks:
            async def join(owned=task):
                await asyncio.gather(owned, return_exceptions=True)
            if task.get_loop() is asyncio.get_running_loop():
                await join()
            elif task.get_loop().is_running():
                await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(join(), task.get_loop()))
        await self.sites.close()
        await self.actions.close()
        await self.artifacts.close()
        await self.input_artifacts.close()
        await self.credentials.close()
