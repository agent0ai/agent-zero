"""Explicit composition of the extension codec, lifecycle and control broker.

The authenticated connector runtime must install this service after validating
the complete release/capability boundary. Nothing imports or installs it by
default, and its route resolver must never draw from the legacy CLI registry.
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
import re
import threading
from typing import Any, Callable
import uuid

from plugins._a0_connector.helpers.browser_bridge_operations import (
    BrowserBridgeBrokerError, BrowserBridgeOperationBroker, OperationBinding, TurnBinding,
)
from plugins._a0_connector.helpers.browser_bridge_policy import BrowserBridgePolicyRepository
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
)
from plugins._browser.helpers.extension_leases import ExtensionLeaseIndex
from plugins._browser.helpers.extension_runtime import (
    ExtensionBrowserError,
    ExtensionBrowserRuntime,
    extension_runtime_factory_owned_by,
    install_extension_runtime_factory,
    uninstall_extension_runtime_factory,
)
from plugins._browser.helpers.extension_sessions import (
    ExtensionFinalizationIntent, ExtensionSessionLifecycle, ValidatedExtensionRoute,
    TURN_FINALIZED, TURN_OUTCOME_UNKNOWN,
)


class ExtensionBrowserServices:
    def __init__(
        self,
        *,
        lifecycle: ExtensionSessionLifecycle,
        broker: BrowserBridgeOperationBroker,
        route_resolver: Callable[[str, str], ValidatedExtensionRoute | None],
        target_origin_resolver: Callable[[OperationBinding, str], str | None] | None = None,
        policy_repository: BrowserBridgePolicyRepository,
        server_instance_id: str,
        site_authority=None,
        artifact_materializer=None,
        action_authority=None,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        if isinstance(broker, BrowserBridgeOperationBroker) and (
            broker.transport_profile is not self._transport_profile
        ):
            raise ValueError("Browser bridge broker transport mismatch")
        if policy_repository.transport_profile is not self._transport_profile:
            raise ValueError("Browser bridge policy transport mismatch")
        self.lifecycle = lifecycle
        self.broker = broker
        self._route_resolver = route_resolver
        self.leases = ExtensionLeaseIndex(authorizer=self._binding_route_current)
        self._target_origin_resolver = target_origin_resolver or self.leases.origin_for
        self._policy = policy_repository
        self._server_instance_id = server_instance_id
        self.site_authority = site_authority
        from plugins._browser.helpers.extension_first_open import FirstOpenSiteAuthority
        self.first_open_authority = (FirstOpenSiteAuthority(
            policy_repository=policy_repository, server_instance_id=server_instance_id)
            if self._transport_profile is PRODUCTION_BROWSER_BRIDGE_TRANSPORT else None)
        self.artifact_materializer = artifact_materializer
        self.action_authority = action_authority
        self.input_artifact_sender = None
        self._input_permits = {}
        self._input_lock = threading.RLock()
        self._runtime_factory = self.runtime_for_agent
        self._install_lock = threading.RLock()
        self._installed = False
        self._factory_installed = False

    @property
    def installed(self) -> bool:
        with self._install_lock:
            return bool(
                self._installed
                and self._factory_owned()
                and self.lifecycle.configured_for(self)
            )

    @property
    def policy_repository(self) -> BrowserBridgePolicyRepository:
        return self._policy

    def _factory_owned(self) -> bool:
        return extension_runtime_factory_owned_by(self)

    def _install_factory(self) -> None:
        install_extension_runtime_factory(
            owner=self,
            factory=self._runtime_factory,
        )

    def _uninstall_factory(self) -> bool:
        return uninstall_extension_runtime_factory(owner=self)

    def _binding_route_current(self, binding: OperationBinding) -> bool:
        route = self._route(binding.context_id, binding.bridge_id)
        return bool(
            route is not None and route.principal is binding.principal
            and route.connector_sid == binding.connector_sid
            and route.load_generation_id == binding.load_generation_id
        )

    def _observe_result(self, binding, call, result) -> None:
        if call.action == "open":
            self.leases.observe_open(binding, result, call.origin)
            if self.first_open_authority is not None:
                self.first_open_authority.observe_open(binding, call.origin, result)
        elif call.action == "navigate":
            self.leases.observe_navigation(binding, call.target["tab_handle"], result, call.origin)
        elif call.action == "content":
            self.leases.observe_content(binding, call.target["tab_handle"], result)
        elif call.action in {"hover", "click", "type", "upload_file"}:
            handle = call.target["tab_handle"]
            lease = self.leases.lease_for(binding, handle)
            fields = {"lease_id", "browser_id", "tab_handle", "document_epoch", "ref"}
            if call.action in {"click", "type", "upload_file"}:
                fields.add("action_class")
            if (lease is None or set(result) != fields
                    or result["lease_id"] != lease.lease_id or result["browser_id"] != handle or result["tab_handle"] != handle
                    or result["ref"] != call.args["ref"] or not isinstance(result["document_epoch"], str)
                    or re.fullmatch(r"0|[1-9][0-9]{0,15}", result["document_epoch"]) is None
                    or int(result["document_epoch"]) > 2**53 - 1):
                raise ExtensionBrowserError("LEASE_CONFLICT", outcome="unknown")
            if call.action in {"click", "type", "upload_file"}:
                document = self.leases.document_for(binding, handle)
                self.leases.clear_document(binding, handle)
                if (document is None or document.document_epoch != int(result["document_epoch"])
                        or result["ref"] not in document.refs
                        or result["action_class"] != call.args["expected_action_class"]):
                    raise ExtensionBrowserError("DOCUMENT_CONFLICT", outcome="unknown")

    def invalidate_lease_event(self, event) -> None:
        from plugins._a0_connector.helpers.browser_bridge_events import LeaseInvalidation

        if not isinstance(event, LeaseInvalidation):
            raise ValueError("invalid lease invalidation")
        self.leases.invalidate_digests(**{
            name: getattr(event, name) for name in (
                "principal", "connector_sid", "load_generation_id", "context_id",
                "browser_session_id", "turn_id", "lease_id_digest", "browser_id_digest",
            )
        })

    def install(self, *, submitter=None) -> tuple[str, ...]:
        """Server bootstrap only; a config save or hello cannot call this."""
        with self._install_lock:
            if self._installed:
                if not self.installed:
                    raise RuntimeError("Extension browser service ownership was lost")
                return self.lifecycle.replay_pending()
            self._install_factory()
            self._factory_installed = True
            try:
                replayed = self.lifecycle.configure(
                    route_resolver=self._route,
                    sender=self.finalize,
                    submitter=submitter,
                    owner=self,
                )
            except Exception:
                self._uninstall_factory()
                self._factory_installed = False
                raise
            self._installed = True
            return replayed

    def uninstall(self) -> tuple[str, ...]:
        """Withdraw only this service while preserving durable uncertainty."""

        if self.first_open_authority is not None:
            self.first_open_authority.retire()
        with self._install_lock:
            if not self._installed:
                return ()
            try:
                scheduled = self.lifecycle.unconfigure(owner=self)
            except Exception:
                # A persistence failure keeps lifecycle ownership retryable,
                # but Browser selection must still fail closed immediately.
                if self._factory_installed:
                    self._uninstall_factory()
                    self._factory_installed = False
                raise
            removed = (
                self._uninstall_factory()
                if self._factory_installed
                else True
            )
            self._factory_installed = False
            self._installed = False
            if not removed:
                # Never clear a competing factory to make teardown look clean.
                raise RuntimeError("Extension browser runtime factory owner mismatch")
            return scheduled

    def _route(self, context_id: str, bridge_id: str) -> ValidatedExtensionRoute | None:
        try:
            route = self._route_resolver(context_id, bridge_id)
        except Exception:
            return None
        if (
            not isinstance(route, ValidatedExtensionRoute)
            or route.bridge_id != bridge_id
            or route.transport_profile is not self._transport_profile
        ):
            return None
        if route.browser_id != f"extension:{bridge_id}":
            return None
        return route

    def runtime_for_agent(self, agent: Any, bridge_id: str) -> ExtensionBrowserRuntime | None:
        context_id = str(getattr(getattr(agent, "context", None), "id", ""))
        if self._route(context_id, bridge_id) is None:
            return None

        def binding_for(active) -> OperationBinding:
            route = self._route(context_id, bridge_id)
            if (
                active is None or route is None
                or active.context_id != context_id or active.bridge_id != bridge_id
                or active.browser_id != route.browser_id
            ):
                raise ExtensionBrowserError("SCOPE_DENIED")
            return OperationBinding(
                route.principal, route.connector_sid, route.load_generation_id,
                context_id, active.browser_session_id, active.turn_id,
                str(uuid.uuid4()), str(uuid.uuid4()),
            )

        @contextmanager
        def call_scope():
            active = self.lifecycle.active_agent_turn(agent)
            synthetic = None
            if active is None:
                synthetic = self.lifecycle.begin_synthetic_turn(agent)
                active = synthetic
            try:
                yield binding_for(active)
            finally:
                if synthetic is not None:
                    self.lifecycle.finalize_synthetic_turn(agent, synthetic, reason="direct")

        def binding_current(binding: OperationBinding) -> bool:
            from plugins._browser.helpers.extension_sessions import ActiveExtensionTurnBinding

            route = self._route(context_id, bridge_id)
            return bool(
                route is not None and route.principal is binding.principal
                and route.connector_sid == binding.connector_sid
                and route.load_generation_id == binding.load_generation_id
                and self.lifecycle.is_current_turn(agent, ActiveExtensionTurnBinding(
                    context_id, binding.browser_session_id, route.browser_id, bridge_id, binding.turn_id,
                ))
            )

        from plugins._browser.helpers.extension_uploads import prepare_upload
        from plugins._browser.helpers.config import get_browser_config
        return ExtensionBrowserRuntime(
            context_id, bridge_id, broker=self.broker,
            binding_factory=lambda: binding_for(self.lifecycle.active_agent_turn(agent)),
            policy_repository=self._policy, server_instance_id=self._server_instance_id,
            target_origin_resolver=self._target_origin_resolver,
            call_scope=call_scope, binding_current=binding_current,
            result_observer=self._observe_result,
            first_open_authority=self.first_open_authority,
            foreground_preference=lambda: (
                self._transport_profile is PRODUCTION_BROWSER_BRIDGE_TRANSPORT
                and get_browser_config(agent=agent).get("autofocus_active_page") is True
            ),
            site_challenge_ready=lambda binding: self.site_authority is not None and binding_current(binding),
            turn_origin_grant=lambda binding, origin: (
                self.site_authority.turn_grant_for(binding, origin=origin) if self.site_authority is not None else None
            ),
            artifact_materializer=self.artifact_materializer,
            action_challenge_ready=lambda binding: (
                self.action_authority is not None and binding_current(binding)
                and self.action_authority.ready_for(binding)
            ),
            prepare_upload=lambda **kwargs: prepare_upload(agent.context, **kwargs),
            upload_sender=self.send_input_artifact if self.input_artifact_sender is not None else None,
        )

    def authorize_input_artifact(self, binding) -> bool:
        with self._input_lock:
            permit = self._input_permits.get(binding.artifact_id)
        if permit is None or permit is not binding:
            return False
        route = self._route(binding.context_id, binding.bridge_id)
        return bool(route is not None and route.principal is binding.principal
                    and route.connector_sid == binding.connector_sid
                    and route.load_generation_id == binding.load_generation_id)

    async def send_input_artifact(self, operation, ticket, source):
        from plugins._a0_connector.helpers.browser_bridge_artifacts import ArtifactBinding
        from plugins._browser.helpers.extension_uploads import PreparedUpload
        if (self._transport_profile is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT
            or self.input_artifact_sender is None or not isinstance(source, PreparedUpload)
            or source.context_id != operation.context_id or ticket.binding is not operation
            or ticket.action != "upload_file"):
            raise ExtensionBrowserError("SCOPE_DENIED")
        binding = ArtifactBinding(operation.principal, operation.connector_sid, operation.load_generation_id,
            operation.bridge_id, operation.context_id, operation.browser_session_id, operation.turn_id,
            operation.action_id, operation.op_id, source.artifact_id, "input", "upload_file")
        with self._input_lock:
            if len(self._input_permits) >= 16 or source.artifact_id in self._input_permits:
                raise ExtensionBrowserError("CAPACITY_EXCEEDED")
            self._input_permits[source.artifact_id] = binding
        try:
            await self.broker.wait_dispatched(ticket)
            data = await asyncio.to_thread(source.read)
            if not self.authorize_input_artifact(binding):
                raise ExtensionBrowserError("SCOPE_DENIED")
            await self.input_artifact_sender.send(binding, data=data, mime_type=source.mime_type)
        finally:
            with self._input_lock:
                if self._input_permits.get(source.artifact_id) is binding:
                    self._input_permits.pop(source.artifact_id, None)

    async def finalize(self, intent: ExtensionFinalizationIntent, _scheduled_route: ValidatedExtensionRoute) -> str:
        if self.first_open_authority is not None:
            self.first_open_authority.retire(lambda binding: (
                binding.context_id == intent.context_id and binding.bridge_id == intent.bridge_id
                and binding.browser_session_id == intent.browser_session_id and binding.turn_id == intent.turn_id))
        route = self._route(intent.context_id, intent.bridge_id)
        if route is None or route.browser_id != intent.browser_id:
            return TURN_OUTCOME_UNKNOWN
        turn = TurnBinding(
            route.principal, route.connector_sid, route.load_generation_id,
            intent.context_id, intent.browser_session_id, intent.turn_id,
        )
        # Finalization starts by withdrawing local target authority regardless
        # of whether the remote cleanup can ultimately be acknowledged.
        self.leases.retire_turn(turn)
        if self.action_authority is not None:
            self.action_authority.finalize_turn(
                principal=turn.principal, connector_sid=turn.connector_sid, load_generation_id=turn.load_generation_id,
                context_id=turn.context_id, browser_session_id=turn.browser_session_id, turn_id=turn.turn_id,
            )
        if self.site_authority is not None:
            self.site_authority.finalize_turn(
                principal=turn.principal, connector_sid=turn.connector_sid, load_generation_id=turn.load_generation_id,
                context_id=turn.context_id, browser_session_id=turn.browser_session_id, turn_id=turn.turn_id,
            )

        async def cancel(operation) -> None:
            try:
                ticket = await self.broker.begin_cancel(
                    operation, control_id=str(uuid.uuid4()), reason="turn_finalizing", timeout_ms=5_000,
                )
                await self.broker.wait_control(ticket)
            except BrowserBridgeBrokerError:
                # Already-settled operations no longer need cancellation. The
                # finalizer independently checks lease/turn ownership.
                pass

        operations = self.broker.pending_operations_for_turn(turn)
        if operations:
            await asyncio.gather(*(cancel(operation) for operation in operations))
        latest = self._route(intent.context_id, intent.bridge_id)
        if (
            latest is None or latest.principal is not route.principal
            or latest.connector_sid != route.connector_sid
            or latest.load_generation_id != route.load_generation_id
        ):
            return TURN_OUTCOME_UNKNOWN
        try:
            ticket = await self.broker.begin_finalize(
                turn, control_id=intent.control_id, dispositions=intent.disposition_mapping(),
                reason=intent.reason, timeout_ms=30_000,
            )
            completion = await self.broker.wait_control(ticket)
        except BrowserBridgeBrokerError:
            return TURN_OUTCOME_UNKNOWN
        result = completion.result
        if not completion.ok or not valid_finalization_result(result, intent.control_id):
            return TURN_OUTCOME_UNKNOWN
        # This means the exact finalization was acknowledged, not that every
        # tab was closed: claimed/deliverable/orphan tabs may be retained.
        return TURN_FINALIZED


def valid_finalization_result(result: Any, control_id: str) -> bool:
    groups = ("closed", "released", "retained", "already_finalized", "errors")
    if (
        not isinstance(result, dict)
        or set(result) != {"contract_version", "control_id", *groups}
        or type(result["contract_version"]) is not int or result["contract_version"] != 1
        or result["control_id"] != control_id
        or any(not isinstance(result[key], list) or len(result[key]) > 256 for key in groups)
        or sum(len(result[key]) for key in groups) > 256 or result["errors"]
    ):
        return False
    seen = set()
    reasons = {
        "user_takeover", "claimed_tab", "non_ephemeral", "generation_mismatch",
        "handle_mismatch", "context_mismatch", "browser_session_mismatch", "turn_mismatch",
        "control_mismatch", "identity_mismatch", "tab_missing", "protected", "ambiguous",
        "unresolved_reconciliation", "not_active", "outcome_unknown",
    }
    for key in groups[:-1]:
        for entry in result[key]:
            if key == "retained":
                if (
                    not isinstance(entry, dict) or set(entry) != {"lease_id", "tab_handle", "reason"}
                    or not isinstance(entry["reason"], str) or entry["reason"] not in reasons
                    or not _valid_id(entry["tab_handle"])
                ):
                    return False
                lease_id = entry["lease_id"]
                if lease_id == entry["tab_handle"]:
                    return False
            else:
                lease_id = entry
            if not _valid_id(lease_id) or lease_id in seen:
                return False
            seen.add(lease_id)
    return True


def _valid_id(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}", value) is not None
