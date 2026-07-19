"""POST /api/plugins/_a0_connector/v1/model_switcher."""
from __future__ import annotations

import time
from typing import Callable

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base

_MODEL_OVERRIDE_REVISION_KEY = "_model_config_override_revision"


def _model_payload(config: dict | None, *, has_api_key: bool = False) -> dict[str, object]:
    config = config or {}
    provider = str(config.get("provider") or "").strip()
    name = str(config.get("name") or "").strip()
    return {
        "provider": provider,
        "name": name,
        "label": f"{provider}/{name}" if provider and name else (name or provider or "—"),
        "has_api_key": bool(has_api_key),
    }


def _coerce_override_model(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}

    payload: dict[str, str] = {}
    provider = str(value.get("provider") or "").strip()
    name = str(value.get("name") or "").strip()
    api_key = str(value.get("api_key") or "").strip()
    api_base = str(value.get("api_base") or value.get("base_url") or "").strip()

    if provider:
        payload["provider"] = provider
    if name:
        payload["name"] = name
    if api_key:
        payload["api_key"] = api_key
    if api_base:
        payload["api_base"] = api_base

    return payload


def _provider_payload(
    value: object,
    *,
    has_api_key_lookup: Callable[[str], bool] | None = None,
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []

    options: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, dict):
            provider = str(item.get("value") or item.get("id") or "").strip().lower()
            label = str(item.get("label") or item.get("name") or provider).strip()
        else:
            provider = str(item or "").strip().lower()
            label = provider.replace("_", " ").title()

        if not provider or provider in seen:
            continue
        seen.add(provider)
        has_api_key = False
        if callable(has_api_key_lookup):
            try:
                has_api_key = bool(has_api_key_lookup(provider))
            except Exception:
                has_api_key = False
        elif isinstance(item, dict):
            has_api_key = bool(item.get("has_api_key"))

        options.append({"value": provider, "label": label or provider, "has_api_key": has_api_key})

    return options


def _notify_model_override_changed(context: object, context_id: str) -> None:
    if hasattr(context, "set_output_data"):
        context.set_output_data(_MODEL_OVERRIDE_REVISION_KEY, time.time())

    try:
        from helpers.state_monitor_integration import mark_dirty_for_context

        mark_dirty_for_context(context_id, reason="a0_connector.model_switcher")
    except Exception:
        pass


class ModelSwitcher(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import AgentContext
        from helpers.persist_chat import save_tmp_chat
        from plugins._model_config.helpers import model_config

        action = str(input.get("action", "get")).strip() or "get"
        context_id = str(input.get("context_id", "")).strip()
        context = AgentContext.get(context_id) if context_id else None
        agent = getattr(context, "agent0", None) if context is not None else None

        def build_state() -> dict[str, object]:
            override = context.get_data("chat_model_override") if context is not None else None
            try:
                chat_providers = _provider_payload(
                    model_config.get_chat_providers(),
                    has_api_key_lookup=lambda provider: model_config.has_provider_api_key(provider, ""),
                )
            except Exception:
                chat_providers = []
            chat_model = model_config.get_chat_model_config(agent)
            utility_model = model_config.get_utility_model_config(agent)

            def _has_api_key(config: object) -> bool:
                if not isinstance(config, dict):
                    return False
                provider = str(config.get("provider") or "").strip().lower()
                api_key = str(config.get("api_key") or "").strip()
                if not provider:
                    return bool(api_key)
                try:
                    return bool(model_config.has_provider_api_key(provider, api_key))
                except Exception:
                    return bool(api_key)

            return {
                "ok": True,
                "allowed": bool(model_config.is_chat_override_allowed(agent)),
                "override": override,
                "presets": model_config.get_presets(),
                "chat_providers": chat_providers,
                "main_model": _model_payload(chat_model, has_api_key=_has_api_key(chat_model)),
                "utility_model": _model_payload(utility_model, has_api_key=_has_api_key(utility_model)),
            }

        if action == "get":
            return build_state()

        if not context_id:
            return Response(status=400, response="Missing context_id")

        if context is None:
            return Response(status=404, response="Context not found")

        if not model_config.is_chat_override_allowed(agent):
            return Response(status=403, response="Per-chat override is disabled")

        if action == "set_preset":
            preset_name = str(input.get("preset_name", "")).strip()
            if not preset_name:
                return Response(status=400, response="Missing preset_name")
            preset = model_config.get_preset_by_name(preset_name)
            if not preset:
                return Response(status=404, response=f"Preset '{preset_name}' not found")
            context.set_data("chat_model_override", {"preset_name": preset_name})
            save_tmp_chat(context)
            _notify_model_override_changed(context, context_id)
            return build_state()

        if action == "clear":
            context.set_data("chat_model_override", None)
            save_tmp_chat(context)
            _notify_model_override_changed(context, context_id)
            return build_state()

        if action == "set_override":
            main_model = _coerce_override_model(input.get("main_model"))
            utility_model = _coerce_override_model(input.get("utility_model"))
            if not main_model and not utility_model:
                return Response(status=400, response="Missing model override payload")

            override: dict[str, dict[str, str]] = {}
            if main_model:
                override["chat"] = main_model
            if utility_model:
                override["utility"] = utility_model
            context.set_data("chat_model_override", override)
            save_tmp_chat(context)
            _notify_model_override_changed(context, context_id)
            return build_state()

        return Response(status=400, response=f"Unknown action: {action}")
