"""POST /api/plugins/_a0_connector/v1/capabilities."""
from __future__ import annotations

import importlib.util
import sys

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


_BASE_FEATURES = [
    "chat_create",
    "chats_list",
    "chat_get",
    "chat_reset",
    "chat_delete",
    "pause",
    "nudge",
    "message_send",
    "log_tail",
    "projects",
    "text_editor_remote",
    "code_execution_remote",
    "computer_use_remote",
    "browser_host_remote",
    "connector_browser_op",
    "remote_file_tree",
    "token_status",
]

_OPTIONAL_FEATURES: dict[str, tuple[str, ...]] = {
    "settings_get": ("helpers.settings", "helpers.subagents"),
    "settings_set": ("helpers.settings", "helpers.subagents"),
    "agent_profile_set": ("api.agent_profile_set",),
    "agents_list": ("helpers.subagents",),
    "skills_list": ("helpers.skills", "helpers.files", "helpers.projects", "helpers.runtime"),
    "skills_delete": ("helpers.skills", "helpers.files", "helpers.projects", "helpers.runtime"),
    "model_presets": ("plugins._model_config.helpers.model_config",),
    "model_switcher": ("plugins._model_config.helpers.model_config",),
    "browser_runtime_config": ("plugins._browser.helpers.config", "helpers.plugins"),
    "compact_chat": (
        "plugins._chat_compaction.helpers.compactor",
        "plugins._model_config.helpers.model_config",
    ),
}


def _module_available(module_name: str) -> bool:
    if module_name in sys.modules:
        return True

    try:
        return importlib.util.find_spec(module_name) is not None
    except (AttributeError, ModuleNotFoundError, ValueError):
        return False


def _feature_available(feature: str) -> bool:
    required = _OPTIONAL_FEATURES.get(feature, ())
    return all(_module_available(module_name) for module_name in required)


def _feature_list() -> list[str]:
    features = list(_BASE_FEATURES)
    for feature in _OPTIONAL_FEATURES:
        if _feature_available(feature):
            features.append(feature)
    return features


class Capabilities(connector_base.PublicConnectorApiHandler):
    """Return the connector discovery contract for current Agent Zero."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        from helpers import login

        return {
            "protocol": "a0-connector.v1",
            "version": "0.1.0",
            "auth": ["session"],
            "auth_required": bool(login.is_login_required()),
            "transports": ["http", "websocket"],
            "streaming": True,
            "websocket_namespace": "/ws",
            "websocket_handlers": ["plugins/_a0_connector/ws_connector"],
            "attachments": {
                "mode": "path_or_url",
                "http_upload": "base64_to_file",
                "max_files": 20,
            },
            "features": _feature_list(),
        }
