"""Helper for per-chat model configuration overrides."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent import AgentContext

OVERRIDE_KEY = "_chat_model_override"


def get_override(context: "AgentContext") -> dict | None:
    return context.data.get(OVERRIDE_KEY)


def set_override(context: "AgentContext", override: dict | None):
    if override is None:
        context.data.pop(OVERRIDE_KEY, None)
    else:
        context.data[OVERRIDE_KEY] = override


def apply_override(context: "AgentContext"):
    """Apply stored per-chat model override to context.config.chat_model."""
    override = get_override(context)
    if not override:
        return

    import models
    from helpers.settings import _env_to_dict

    current = context.config.chat_model
    kwargs = override.get("chat_model_kwargs", current.kwargs)
    if isinstance(kwargs, str):
        kwargs = _env_to_dict(kwargs)
    if not isinstance(kwargs, dict):
        kwargs = current.kwargs

    # Normalize kwargs values (string numbers -> actual numbers)
    normalized: dict = {}
    for key, value in kwargs.items():
        if isinstance(value, str):
            try:
                normalized[key] = int(value)
            except ValueError:
                try:
                    normalized[key] = float(value)
                except ValueError:
                    normalized[key] = value
        else:
            normalized[key] = value

    context.config.chat_model = models.ModelConfig(
        type=models.ModelType.CHAT,
        provider=override.get("chat_model_provider") or current.provider,
        name=override.get("chat_model_name") or current.name,
        api_base=override.get("chat_model_api_base", current.api_base),
        ctx_length=override.get("chat_model_ctx_length", current.ctx_length),
        vision=override.get("chat_model_vision", current.vision),
        limit_requests=override.get("chat_model_rl_requests", current.limit_requests),
        limit_input=override.get("chat_model_rl_input", current.limit_input),
        limit_output=override.get("chat_model_rl_output", current.limit_output),
        kwargs=normalized,
    )
