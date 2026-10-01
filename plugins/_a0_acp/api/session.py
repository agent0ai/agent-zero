"""Authenticated ACP session metadata API for the host-side A0 CLI."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from helpers.api import Request, Response
from plugins._a0_connector.api.v1.base import ProtectedConnectorApiHandler


PLUGIN_NAME = "_a0_acp"
CTX_IS_ACP = "acp_session"
CTX_CWD = "acp_cwd"
CTX_ADDITIONAL_DIRECTORIES = "acp_additional_directories"
CTX_MODE = "acp_mode"
CTX_MODEL_ID = "acp_model_id"
CTX_CONFIG_OPTIONS = "acp_config_options"
CTX_TRANSPORT = "acp_transport"
CTX_WORKDIR = "workdir_path"
_VALID_MODES = {"default", "plan", "act"}
_MAX_PATHS = 32
_MAX_PATH_LENGTH = 4096


def _config() -> dict[str, Any]:
    from helpers.plugins import get_plugin_config

    return dict(get_plugin_config(PLUGIN_NAME) or {})


def _paths(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        str(path).strip()
        for path in value[:_MAX_PATHS]
        if str(path).strip() and len(str(path).strip()) <= _MAX_PATH_LENGTH
    ]


def _mode(value: object) -> str:
    mode = str(value or "default").strip().lower()
    return mode if mode in _VALID_MODES else "default"


def _timestamp(value: object) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value or "")


def _session_payload(context) -> dict[str, Any]:
    return {
        "session_id": context.id,
        "title": context.name or "Agent Zero ACP",
        "cwd": str(context.get_data(CTX_CWD) or ""),
        "additional_directories": _paths(context.get_data(CTX_ADDITIONAL_DIRECTORIES)),
        "updated_at": _timestamp(context.last_message or context.created_at),
        "mode": _mode(context.get_data(CTX_MODE)),
        "model_id": str(context.get_data(CTX_MODEL_ID) or ""),
    }


def _mark_dirty(context_id: str, reason: str) -> None:
    try:
        from helpers.state_monitor_integration import mark_dirty_for_context

        mark_dirty_for_context(context_id, reason=reason)
    except Exception:
        return


class Session(ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        del request
        action = str(input.get("action") or "config").strip().lower()
        if action == "config":
            return {"ok": True, "config": _config()}

        if action == "list":
            return self._list_sessions(input)
        if action == "configure":
            return self._configure(input)
        if action == "fork":
            return self._fork(input)
        if action == "close":
            return self._close(input)
        if action == "set_mode":
            return self._set_value(input, CTX_MODE, _mode(input.get("mode")))
        if action == "set_model":
            return self._set_value(input, CTX_MODEL_ID, str(input.get("model_id") or "").strip())
        if action == "set_config_option":
            return self._set_config_option(input)
        return Response(status=400, response=f"Unknown ACP action: {action}")

    def _context(self, input: dict):
        from agent import AgentContext

        context_id = str(input.get("context_id") or input.get("session_id") or "").strip()
        if not context_id:
            return None, Response(status=400, response="context_id is required")
        context = AgentContext.get(context_id)
        if context is None:
            return None, Response(status=404, response="ACP session not found")
        return context, None

    def _list_sessions(self, input: dict) -> dict:
        from agent import AgentContext
        from helpers import persist_chat

        persist_chat.load_tmp_chats()
        cwd = str(input.get("cwd") or "").strip()
        sessions = [
            _session_payload(context)
            for context in AgentContext.all()
            if context.get_data(CTX_IS_ACP)
            and (not cwd or str(context.get_data(CTX_CWD) or "") == cwd)
        ]
        sessions.sort(key=lambda session: str(session["updated_at"]), reverse=True)
        return {"ok": True, "sessions": sessions}

    def _configure(self, input: dict) -> dict | Response:
        from helpers import persist_chat

        config = _config()
        if not bool(config.get("enabled", True)):
            return Response(status=403, response="ACP is disabled in Agent Zero settings")
        context, error = self._context(input)
        if error:
            return error

        cwd = str(input.get("cwd") or "").strip()
        if not cwd or len(cwd) > _MAX_PATH_LENGTH:
            return Response(status=400, response="A valid ACP workspace path is required")
        transport = str(config.get("transport") or "connector").strip().lower()
        if transport not in {"connector", "container"}:
            transport = "connector"

        context.set_data(CTX_IS_ACP, True)
        context.set_data(CTX_CWD, cwd)
        context.set_data(CTX_ADDITIONAL_DIRECTORIES, _paths(input.get("additional_directories")))
        context.set_data(CTX_MODE, _mode(input.get("mode")))
        context.set_data(CTX_TRANSPORT, transport)
        if transport == "container":
            container_workspace = str(config.get("container_workspace_root") or "").strip()
            if container_workspace:
                context.set_data(CTX_WORKDIR, container_workspace)
        if not context.name:
            context.name = Path(cwd).name or "Agent Zero ACP"
        persist_chat.save_tmp_chat(context)
        _mark_dirty(context.id, "a0_acp.configure")
        return {"ok": True, "session": _session_payload(context), "config": config}

    def _fork(self, input: dict) -> dict | Response:
        from agent import AgentContext
        from helpers import persist_chat

        context, error = self._context(input)
        if error:
            return error
        if not context.get_data(CTX_IS_ACP):
            return Response(status=400, response="Only ACP sessions can be forked through ACP")

        new_ids = persist_chat.load_json_chats([persist_chat.export_json_chat(context)])
        if not new_ids:
            return Response(status=500, response="Could not fork ACP session")
        fork = AgentContext.get(new_ids[0])
        if fork is None:
            return Response(status=500, response="Forked ACP session could not be loaded")

        fork.name = f"{context.name or 'Agent Zero ACP'} (fork)"
        fork.set_data(CTX_IS_ACP, True)
        fork.set_data(CTX_CWD, str(input.get("cwd") or context.get_data(CTX_CWD) or ""))
        fork.set_data(
            CTX_ADDITIONAL_DIRECTORIES,
            _paths(input.get("additional_directories"))
            or _paths(context.get_data(CTX_ADDITIONAL_DIRECTORIES)),
        )
        fork.set_data(CTX_MODE, _mode(context.get_data(CTX_MODE)))
        fork.set_data(CTX_TRANSPORT, context.get_data(CTX_TRANSPORT) or "connector")
        persist_chat.save_tmp_chat(fork)
        _mark_dirty(fork.id, "a0_acp.fork")
        return {"ok": True, "session": _session_payload(fork)}

    def _close(self, input: dict) -> dict | Response:
        from agent import AgentContext
        from helpers import persist_chat

        context, error = self._context(input)
        if error:
            return error
        context.kill_process()
        AgentContext.remove(context.id)
        persist_chat.remove_chat(context.id)
        return {"ok": True}

    def _set_value(self, input: dict, key: str, value: object) -> dict | Response:
        from helpers import persist_chat

        context, error = self._context(input)
        if error:
            return error
        context.set_data(key, value)
        persist_chat.save_tmp_chat(context)
        _mark_dirty(context.id, f"a0_acp.{key}")
        return {"ok": True, "session": _session_payload(context)}

    def _set_config_option(self, input: dict) -> dict | Response:
        from helpers import persist_chat

        context, error = self._context(input)
        if error:
            return error
        config_id = str(input.get("config_id") or "").strip()
        if not config_id:
            return Response(status=400, response="config_id is required")
        options = context.get_data(CTX_CONFIG_OPTIONS)
        options = dict(options) if isinstance(options, dict) else {}
        options[config_id] = input.get("value")
        context.set_data(CTX_CONFIG_OPTIONS, options)
        persist_chat.save_tmp_chat(context)
        _mark_dirty(context.id, "a0_acp.config_option")
        return {"ok": True, "config_options": options}
