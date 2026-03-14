from __future__ import annotations

from typing import Any

from python.helpers import dotenv
from python.helpers.settings import get_settings

_adapter_cache: dict[str, Any] = {}


def _resolve_setting(settings: dict[str, Any], key: str, env_key: str) -> str:
    value = settings.get(key) if settings else ""
    if not value:
        value = dotenv.get_dotenv_value(env_key, "") or ""
    return value


def _selected_providers(settings: dict[str, Any]) -> list[str]:
    selection = settings.get("observability_provider", "local") if settings else "local"
    if selection in ("local", "", None):
        return []
    if selection == "langsmith+langfuse":
        return ["langsmith", "langfuse"]
    return [selection]


class LangSmithAdapter:
    def __init__(self, api_key: str, project: str, endpoint: str | None):
        self.api_key = api_key
        self.project = project or "agent-jumbo"
        self.endpoint = endpoint or None
        self.client = None
        try:
            from langsmith import Client
        except Exception:
            Client = None
        if Client and api_key:
            try:
                self.client = Client(api_key=api_key, api_url=self.endpoint)
            except Exception:
                self.client = None

    def ready(self) -> bool:
        return self.client is not None

    def record_event(self, event: dict[str, Any]) -> None:
        if not self.client:
            return
        try:
            self.client.create_run(
                name=event.get("tool_name") or "tool",
                run_type="tool",
                inputs={"tool_args": event.get("tool_args", {})},
                outputs={"status": event.get("status")},
                error=event.get("error"),
                tags=[event.get("stage", "tool")],
                metadata={
                    "trace_id": event.get("trace_id"),
                    "agent_name": event.get("agent_name"),
                    "agent_number": event.get("agent_number"),
                },
                project_name=self.project,
            )
        except Exception:
            return

    def record_workflow_snapshot(self, workflow: dict[str, Any]) -> None:
        if not self.client:
            return
        try:
            self.client.create_run(
                name=workflow.get("name", "workflow"),
                run_type="chain",
                inputs={"steps": workflow.get("steps", [])},
                outputs={"status": workflow.get("status")},
                tags=["workflow", "snapshot"],
                metadata={
                    "run_id": workflow.get("run_id"),
                    "label": workflow.get("label"),
                },
                project_name=self.project,
            )
        except Exception:
            return


class LangfuseAdapter:
    def __init__(self, public_key: str, secret_key: str, host: str | None):
        self.public_key = public_key
        self.secret_key = secret_key
        self.host = host or None
        self.client = None
        try:
            from langfuse import Langfuse
        except Exception:
            Langfuse = None
        if Langfuse and public_key and secret_key:
            try:
                self.client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=self.host,
                )
            except Exception:
                self.client = None

    def ready(self) -> bool:
        return self.client is not None

    def record_event(self, event: dict[str, Any]) -> None:
        if not self.client:
            return
        try:
            trace = self.client.trace(
                id=event.get("trace_id"),
                name=event.get("tool_name") or "tool",
                metadata={
                    "agent_name": event.get("agent_name"),
                    "agent_number": event.get("agent_number"),
                    "stage": event.get("stage"),
                    "status": event.get("status"),
                },
            )
            if hasattr(trace, "event"):
                trace.event(
                    name=event.get("stage") or "tool_event",
                    input=event.get("tool_args", {}),
                    output={"status": event.get("status")},
                    metadata={"error": event.get("error")},
                )
            if hasattr(self.client, "flush"):
                self.client.flush()
        except Exception:
            return

    def record_workflow_snapshot(self, workflow: dict[str, Any]) -> None:
        if not self.client:
            return
        try:
            trace = self.client.trace(
                id=workflow.get("run_id"),
                name=workflow.get("name", "workflow"),
                metadata={"label": workflow.get("label"), "status": workflow.get("status")},
            )
            if hasattr(trace, "event"):
                trace.event(
                    name="workflow_snapshot",
                    input={"steps": workflow.get("steps", [])},
                    output={"status": workflow.get("status")},
                )
            if hasattr(self.client, "flush"):
                self.client.flush()
        except Exception:
            return


def _get_langsmith_adapter(settings: dict[str, Any]) -> LangSmithAdapter | None:
    api_key = _resolve_setting(settings, "langsmith_api_key", "LANGSMITH_API_KEY")
    project = _resolve_setting(settings, "langsmith_project", "LANGSMITH_PROJECT")
    endpoint = _resolve_setting(settings, "langsmith_endpoint", "LANGSMITH_ENDPOINT")
    if not api_key:
        return None
    cache_key = f"langsmith::{api_key}::{project}::{endpoint}"
    cached = _adapter_cache.get(cache_key)
    if cached:
        return cached
    adapter = LangSmithAdapter(api_key=api_key, project=project, endpoint=endpoint or None)
    if adapter.ready():
        _adapter_cache[cache_key] = adapter
        return adapter
    return None


def _get_langfuse_adapter(settings: dict[str, Any]) -> LangfuseAdapter | None:
    public_key = _resolve_setting(settings, "langfuse_public_key", "LANGFUSE_PUBLIC_KEY")
    secret_key = _resolve_setting(settings, "langfuse_secret_key", "LANGFUSE_SECRET_KEY")
    host = _resolve_setting(settings, "langfuse_host", "LANGFUSE_HOST")
    if not public_key or not secret_key:
        return None
    cache_key = f"langfuse::{public_key}::{secret_key}::{host}"
    cached = _adapter_cache.get(cache_key)
    if cached:
        return cached
    adapter = LangfuseAdapter(public_key=public_key, secret_key=secret_key, host=host or None)
    if adapter.ready():
        _adapter_cache[cache_key] = adapter
        return adapter
    return None


def dispatch_event(context, event: dict[str, Any]) -> None:
    settings = get_settings()
    providers = _selected_providers(settings)
    if not providers:
        return
    for provider in providers:
        if provider == "langsmith":
            adapter = _get_langsmith_adapter(settings)
        elif provider == "langfuse":
            adapter = _get_langfuse_adapter(settings)
        else:
            adapter = None
        if adapter:
            adapter.record_event(event)


def dispatch_workflow_snapshot(context, workflow: dict[str, Any]) -> None:
    settings = get_settings()
    providers = _selected_providers(settings)
    if not providers:
        return
    for provider in providers:
        if provider == "langsmith":
            adapter = _get_langsmith_adapter(settings)
        elif provider == "langfuse":
            adapter = _get_langfuse_adapter(settings)
        else:
            adapter = None
        if adapter:
            adapter.record_workflow_snapshot(workflow)
