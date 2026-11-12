"""Canonical Browser-tool adapter for an explicitly selected extension route.

Construction requires server-owned authority and lifecycle services. This
module never discovers a legacy socket, interprets a CDP endpoint, enables the
rollout, or turns client-supplied policy IDs into permission.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
import re
import threading
from typing import Any, Callable, ContextManager
from urllib.parse import urlsplit, urlunsplit
import uuid

from plugins._a0_connector.helpers.browser_bridge_operations import (
    BrowserBridgeBrokerError,
    BrowserBridgeOperationBroker,
    OperationBinding,
)
from plugins._a0_connector.helpers.browser_bridge_policy import (
    BrowserBridgePolicyRepository,
    normalize_site_origin,
)


_SUPPORTED = frozenset({"open", "list", "state", "content", "navigate", "scroll", "hover", "click", "type", "ensure", "status", "screenshot_file"})
_TARGETED = frozenset({"state", "content", "navigate", "scroll", "hover", "click", "type", "screenshot_file"})
_FOREGROUND_ACTIONS = frozenset({"open", "hover", "click", "type", "scroll", "upload_file"})
_OPAQUE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_factory_lock = threading.RLock()
_runtime_factory: Callable[[Any, str], "ExtensionBrowserRuntime | None"] | None = None
_runtime_factory_owner: object | None = None
_legacy_runtime_factory_owner = object()


def install_extension_runtime_factory(
    *,
    owner: object,
    factory: Callable[[Any, str], "ExtensionBrowserRuntime | None"],
) -> bool:
    """Install one exact process owner without replacing another owner."""

    if owner is None:
        raise TypeError("Extension runtime factory owner is required")
    if not callable(factory):
        raise TypeError("Extension runtime factory must be callable")
    global _runtime_factory, _runtime_factory_owner
    with _factory_lock:
        if _runtime_factory_owner is owner:
            _runtime_factory = factory
            return False
        if _runtime_factory_owner is not None:
            raise RuntimeError("Extension runtime factory is already installed")
        _runtime_factory = factory
        _runtime_factory_owner = owner
        return True


def uninstall_extension_runtime_factory(*, owner: object) -> bool:
    """Withdraw only ``owner``'s factory; never clear a competing owner."""

    global _runtime_factory, _runtime_factory_owner
    with _factory_lock:
        if _runtime_factory_owner is not owner:
            return False
        _runtime_factory = None
        _runtime_factory_owner = None
        return True


def extension_runtime_factory_owned_by(owner: object) -> bool:
    with _factory_lock:
        return _runtime_factory_owner is owner and _runtime_factory is not None


def configure_extension_runtime_factory(
    factory: Callable[[Any, str], "ExtensionBrowserRuntime | None"] | None,
) -> None:
    """Legacy/test bootstrap seam, isolated as its own exact owner.

    Production composition uses :func:`install_extension_runtime_factory`.
    Clearing this seam cannot withdraw a separately installed server owner.
    """
    if factory is None:
        uninstall_extension_runtime_factory(owner=_legacy_runtime_factory_owner)
        return
    install_extension_runtime_factory(
        owner=_legacy_runtime_factory_owner,
        factory=factory,
    )


def selected_extension_runtime(agent: Any, bridge_id: str) -> "ExtensionBrowserRuntime | None":
    from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate

    if get_browser_bridge_gate().state != "available":
        return None
    with _factory_lock:
        factory = _runtime_factory
    if factory is None:
        return None
    try:
        runtime = factory(agent, bridge_id)
        if (
            isinstance(runtime, ExtensionBrowserRuntime)
            and runtime.context_id == str(agent.context.id)
            and runtime.bridge_id == bridge_id
        ):
            return runtime
    except Exception:
        pass
    return None


async def wait_selected_extension_runtime(agent: Any, bridge_id: str) -> "ExtensionBrowserRuntime | None":
    """Wait only for a selected owner's pre-operation reconnect, never replay work."""
    from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate
    from plugins._browser.helpers.config import get_browser_config, parse_extension_browser_selection

    with _factory_lock:
        factory, owner = _runtime_factory, _runtime_factory_owner
    if factory is None:
        return None
    # Native's first exact repeated hello begins reconciliation after 15s.
    # Bound this presentation/selection wait; no operation or grant exists yet.
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 25.0
    def still_selected() -> bool:
        with _factory_lock:
            if _runtime_factory is not factory or _runtime_factory_owner is not owner:
                return False
        if get_browser_bridge_gate().state != "available":
            return False
        try:
            config = get_browser_config(agent=agent)
            selection = parse_extension_browser_selection(config.get("host_browser_selection"))
            return config.get("runtime_backend") == "host_required" and selection is not None and selection.bridge_id == bridge_id
        except Exception:
            return False
    while True:
        if not still_selected():
            return None
        runtime = selected_extension_runtime(agent, bridge_id)
        if runtime is not None:
            return runtime if still_selected() else None
        remaining = deadline - loop.time()
        if remaining <= 0:
            return None
        await asyncio.sleep(min(0.25, remaining))


class ExtensionBrowserError(RuntimeError):
    def __init__(self, code: str, *, outcome: str = "not_applied") -> None:
        # Deliberately never include provider exceptions, URLs, or arguments in
        # errors consumed by the Browser tool's history/log path.
        super().__init__(f"Chrome extension browser: {code}; outcome={outcome}. No fallback was attempted.")
        self.code = code
        self.outcome = outcome


@dataclass(frozen=True, slots=True)
class ExtensionCall:
    action: str
    target: dict[str, str] | None
    args: dict[str, Any] = field(repr=False)
    origin: str | None
    required_capabilities: tuple[str, ...]
    upload_source: Any = field(default=None, repr=False)


class ExtensionBrowserRuntime:
    """One call facade; injected services, not this object, own session state."""

    def __init__(
        self,
        context_id: str,
        bridge_id: str,
        *,
        broker: BrowserBridgeOperationBroker,
        binding_factory: Callable[[], OperationBinding],
        policy_repository: BrowserBridgePolicyRepository,
        server_instance_id: str,
        target_origin_resolver: Callable[[OperationBinding, str], str | None],
        timeout_ms: int = 30_000,
        call_scope: Callable[[], ContextManager[OperationBinding]] | None = None,
        binding_current: Callable[[OperationBinding], bool] | None = None,
        result_observer: Callable[[OperationBinding, ExtensionCall, dict[str, Any]], None] | None = None,
        site_challenge_ready: Callable[[OperationBinding], bool] | None = None,
        turn_origin_grant: Callable[[OperationBinding, str], Any] | None = None,
        artifact_materializer: Callable | None = None,
        action_challenge_ready: Callable[[OperationBinding], bool] | None = None,
        prepare_upload: Callable | None = None,
        upload_sender: Callable | None = None,
        first_open_authority=None,
        foreground_preference: Callable[[], bool] | None = None,
    ) -> None:
        self.context_id = _opaque(context_id)
        self.bridge_id = _opaque(bridge_id)
        self._server_instance_id = _opaque(server_instance_id)
        if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or not 1 <= timeout_ms <= 120_000:
            raise ExtensionBrowserError("INVALID_STATE")
        self._broker = broker
        self._binding_factory = binding_factory
        self._policy = policy_repository
        self._target_origin_resolver = target_origin_resolver
        self._timeout_ms = timeout_ms
        self._call_scope = call_scope
        self._binding_current = binding_current
        self._result_observer = result_observer
        self._site_challenge_ready = site_challenge_ready
        self._turn_origin_grant = turn_origin_grant
        self._artifact_materializer = artifact_materializer
        self._action_challenge_ready = action_challenge_ready
        self._prepare_upload = prepare_upload
        self._upload_sender = upload_sender
        self._first_open_authority = first_open_authority
        self._foreground_preference = foreground_preference

    def _operation_display(self, action: str) -> dict[str, bool]:
        foreground = False
        if action in _FOREGROUND_ACTIONS and self._foreground_preference is not None:
            try:
                foreground = self._foreground_preference() is True
            except Exception:
                # Unavailable settings must not unexpectedly switch host tabs.
                pass
        return {
            "cursor": action in {"scroll", "hover", "click", "type", "upload_file"},
            "foreground": foreground,
        }

    async def call(self, method: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        if method == "upload_file":
            from plugins._browser.helpers.extension_uploads import PreparedUpload, UploadSourceDenied
            if (len(args) != 2 or not set(kwargs) <= {"path", "paths"}
                or self._prepare_upload is None or self._upload_sender is None):
                raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY")
            try:
                source = self._prepare_upload(**kwargs)
            except UploadSourceDenied:
                raise ExtensionBrowserError("UPLOAD_SOURCE_UNAVAILABLE") from None
            if not isinstance(source, PreparedUpload) or source.context_id != self.context_id:
                raise ExtensionBrowserError("SCOPE_DENIED")
            proposed = ExtensionCall("upload_file", {"tab_handle": _opaque(args[0])},
                {"ref": _opaque(args[1], limit=128), "artifact_id": source.artifact_id,
                 "mime_type": source.mime_type, "byte_count": source.byte_count, "sha256": source.sha256,
                 "expected_action_class": "external_side_effect"}, None,
                ("upload_file", "semantic_dom_v1", "artifacts_v1", "trusted_input_v1", "cursor_v1"), source)
        else:
            proposed = encode_extension_call(method, args, kwargs)
        if self._call_scope is not None:
            with self._call_scope() as binding:
                return await self._call_bound(proposed, binding)
        try:
            binding = self._binding_factory()
        except Exception:
            raise ExtensionBrowserError("SCOPE_DENIED") from None
        return await self._call_bound(proposed, binding)

    async def _call_bound(self, proposed: ExtensionCall, binding: OperationBinding) -> dict[str, Any]:
        if (
            not isinstance(binding, OperationBinding)
            or binding.context_id != self.context_id
            or binding.bridge_id != self.bridge_id
        ):
            raise ExtensionBrowserError("SCOPE_DENIED")
        if proposed.action == "screenshot" and self._artifact_materializer is None:
            raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY")
        if proposed.action in {"click", "type", "upload_file"} and (
                self._action_challenge_ready is None or self._action_challenge_ready(binding) is not True):
            raise ExtensionBrowserError("APPROVAL_REQUIRED")

        target_origin = self._target_origin(binding, proposed)
        cross_origin = proposed.action == "navigate" and proposed.origin != target_origin
        if cross_origin and (self._site_challenge_ready is None or self._site_challenge_ready(binding) is not True):
            raise ExtensionBrowserError("APPROVAL_REQUIRED")
        # Starting a cross-origin request authorizes only work on the current
        # owned source. The extension must suspend before navigation until the
        # server resolves its exact destination/document-bound challenge.
        origin = target_origin if cross_origin else proposed.origin or target_origin
        target_handle = proposed.target.get("tab_handle") if proposed.target else None
        grant = self._origin_grant(binding, origin, target_handle)
        if (origin is not None and grant is None and proposed.action == "open"
                and self._first_open_authority is not None and self._binding_current is not None):
            from plugins._browser.helpers.extension_first_open import FirstOpenDenied
            try:
                grant = await self._first_open_authority.request(binding, origin, current=self._binding_current)
            except TimeoutError:
                raise ExtensionBrowserError("APPROVAL_EXPIRED") from None
            except FirstOpenDenied:
                raise ExtensionBrowserError("APPROVAL_DENIED") from None
        if origin is not None and grant is None:
            raise ExtensionBrowserError("ORIGIN_BLOCKED")

        def policy_still_current() -> bool:
            if self._binding_current is not None and self._binding_current(binding) is not True:
                return False
            if cross_origin and self._site_challenge_ready(binding) is not True:
                return False
            if proposed.action in {"click", "type", "upload_file"} and self._action_challenge_ready(binding) is not True:
                return False
            if self._target_origin(binding, proposed) != target_origin:
                return False
            latest = self._origin_grant(binding, origin, target_handle)
            return latest == grant

        try:
            ticket = await self._broker.begin_operation(
                binding, action=proposed.action, target=proposed.target,
                args=proposed.args, timeout_ms=self._timeout_ms,
                required_capabilities=proposed.required_capabilities,
                policy={"origin_grant_id": grant, "action_grant_id": None},
                display=self._operation_display(proposed.action),
                dispatch_preflight=policy_still_current,
            )
            try:
                if proposed.action == "upload_file":
                    try:
                        await self._upload_sender(binding, ticket, proposed.upload_source)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        try:
                            await self._broker.begin_cancel(ticket, control_id=str(uuid.uuid4()),
                                reason="request_canceled", timeout_ms=min(self._timeout_ms, 10_000))
                        except Exception:
                            pass
                        raise ExtensionBrowserError("ARTIFACT_VERIFICATION_FAILED", outcome="unknown") from None
                result = await self._broker.wait_operation(ticket)
            except asyncio.CancelledError:
                # begin_cancel has no suspending work before its bounded,
                # process-owned send is installed. The requester's canceled
                # wait is not evidence that the remote operation was undone.
                try:
                    await self._broker.begin_cancel(
                        ticket, control_id=str(uuid.uuid4()), reason="request_canceled",
                        timeout_ms=min(self._timeout_ms, 10_000),
                    )
                except Exception:
                    pass
                raise
        except BrowserBridgeBrokerError as exc:
            raise ExtensionBrowserError(exc.code, outcome=exc.outcome) from None
        if not result.ok:
            raise ExtensionBrowserError(result.code or "INTERNAL_ERROR", outcome=result.outcome or "unknown")
        if proposed.action == "screenshot":
            if self._artifact_materializer is None:
                raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY", outcome="unknown")
            try:
                return await asyncio.to_thread(self._artifact_materializer, binding, proposed, result)
            except Exception:
                raise ExtensionBrowserError("ARTIFACT_VERIFICATION_FAILED", outcome="unknown") from None
        # Artifact and receipt verifiers are a separate boundary. Do not expose
        # an unverified path/descriptor or treat it as approval authority.
        if result.artifacts or result.receipts or not isinstance(result.result, dict):
            raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY", outcome="unknown")
        if self._binding_current is not None and self._binding_current(binding) is not True:
            raise ExtensionBrowserError("SCOPE_DENIED", outcome="unknown")
        if self._result_observer is not None:
            try:
                self._result_observer(binding, proposed, result.result)
            except Exception:
                raise ExtensionBrowserError("LEASE_CONFLICT", outcome="unknown") from None
        return result.result

    def _target_origin(self, binding: OperationBinding, call: ExtensionCall) -> str | None:
        if call.target is None:
            return None
        try:
            value = self._target_origin_resolver(binding, call.target["tab_handle"])
            return normalize_site_origin(value)
        except Exception:
            raise ExtensionBrowserError("TAB_NOT_OWNED") from None

    def _origin_grant(self, binding: OperationBinding, origin: str | None, target_handle=None) -> str | None:
        if origin is None:
            return None
        try:
            grant = self._policy.active_grant(
                server_instance_id=self._server_instance_id, bridge_id=self.bridge_id,
                subject_id=binding.principal.subject_id, origin=origin,
            )
        except Exception:
            raise ExtensionBrowserError("ORIGIN_BLOCKED") from None
        if grant is not None:
            return grant.grant_id
        if self._turn_origin_grant is not None:
            try:
                turn_grant = self._turn_origin_grant(binding, origin)
                if turn_grant is not None:
                    return _opaque(turn_grant.origin_grant_id)
            except Exception:
                raise ExtensionBrowserError("ORIGIN_BLOCKED") from None
        if self._first_open_authority is not None:
            return self._first_open_authority.grant_for(binding, origin, target_handle)
        return None


def encode_extension_call(method: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> ExtensionCall:
    """Translate only supported Browser-tool forms; never silently drop fields."""
    if not isinstance(method, str) or method not in _SUPPORTED:
        raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY")
    if method == "hover" and len(args) == 1:
        if (not set(kwargs) <= {"ref", "x", "y", "offset_x", "offset_y"}
                or any(type(kwargs.get(key, 0)) not in {int, float} or kwargs.get(key, 0) != 0
                       for key in ("x", "y", "offset_x", "offset_y"))):
            raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY")
        args = (args[0], kwargs.get("ref"))
        kwargs = {}
    expected = {"open": 1, "list": 0, "state": 1, "content": 2, "navigate": 2, "scroll": 2, "hover": 2, "click": 2, "type": 3, "ensure": 0, "status": 0, "screenshot_file": 1}[method]
    if len(args) != expected:
        raise ExtensionBrowserError("INVALID_STATE")
    allowed_kwargs = {"include_content"} if method == "list" else {"quality", "full_page", "path"} if method == "screenshot_file" else set()
    if not set(kwargs) <= allowed_kwargs:
        raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY")
    target = {"tab_handle": _opaque(args[0])} if method in _TARGETED else None
    payload: dict[str, Any] = {}
    origin = None
    capabilities = [method]
    if method in {"open", "navigate"}:
        payload["url"], origin = _url(args[0] if method == "open" else args[1])
        if method == "open":
            payload["disposition"] = "ephemeral"
            capabilities.extend(("tab_leases_v1", "tab_groups_v1"))
    elif method == "content":
        options = args[1]
        if options is not None and options != {}:
            # CSS selectors/scripts and old integer refs are deliberately not
            # interpreted by this semantic document-bound runtime.
            raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY")
        capabilities.append("semantic_dom_v1")
    elif method in {"scroll", "hover", "click", "type"}:
        payload["ref"] = _opaque(args[1], limit=128)
        capabilities.extend(("semantic_dom_v1", "cursor_v1"))
        if method in {"hover", "click", "type"}:
            capabilities.append("trusted_input_v1")
        if method == "click":
            # The existing Browser tool provides no independently verified
            # risk classification. Never infer approval from model intent.
            payload["expected_action_class"] = "unknown"
        elif method == "type":
            text = args[2]
            if not isinstance(text, str) or "\x00" in text or "\r" in text:
                raise ExtensionBrowserError("INVALID_STATE")
            try:
                encoded = text.encode("utf-8", errors="strict")
            except UnicodeError:
                raise ExtensionBrowserError("INVALID_STATE") from None
            if not 1 <= len(encoded) <= 32768:
                raise ExtensionBrowserError("INVALID_STATE")
            payload.update(text=text, text_sha256=hashlib.sha256(encoded).hexdigest(),
                           expected_action_class="sensitive_input")
    elif method == "list":
        include = kwargs.get("include_content", False)
        if not isinstance(include, bool):
            raise ExtensionBrowserError("INVALID_STATE")
        if include:
            raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY")
    elif method == "screenshot_file":
        quality = kwargs.get("quality", 80)
        if (type(quality) is not int or not 20 <= quality <= 95
                or kwargs.get("full_page", False) is not False or kwargs.get("path", "") != ""):
            raise ExtensionBrowserError("UNSUPPORTED_CAPABILITY")
        payload = {"format": "jpeg", "quality": quality}
        capabilities = ["screenshot", "screenshots_v1", "artifacts_v1"]
        method = "screenshot"
    return ExtensionCall(method, target, payload, origin, tuple(capabilities))


def _opaque(value: Any, *, limit: int = 256) -> str:
    if not isinstance(value, str) or len(value) > limit or _OPAQUE.fullmatch(value) is None:
        raise ExtensionBrowserError("INVALID_STATE")
    return value


def _url(value: Any) -> tuple[str, str]:
    if (
        not isinstance(value, str) or not value or len(value.encode("utf-8")) > 8192
        or value != value.strip() or "\\" in value
        or any(ord(character) <= 0x20 or ord(character) == 0x7f for character in value)
    ):
        raise ExtensionBrowserError("INVALID_STATE")
    try:
        parsed = urlsplit(value)
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("credentials are not a browser URL")
        origin = normalize_site_origin(urlunsplit((parsed.scheme, parsed.netloc, "", "", "")))
        canonical = urlsplit(origin)
        return urlunsplit((canonical.scheme, canonical.netloc, parsed.path or "/", parsed.query, parsed.fragment)), origin
    except Exception:
        raise ExtensionBrowserError("INVALID_STATE") from None
