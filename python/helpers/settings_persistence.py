"""
settings_persistence.py — Load/save/merge logic and file I/O for settings.

This module was extracted from settings.py as part of OPA-5 (Settings Architecture Refactor).
It contains:
  - _read_settings_file / _write_settings_file
  - _remove_sensitive_settings / _write_sensitive_settings
  - normalize_settings / _adjust_to_version (migration)
  - get_settings / set_settings / set_settings_delta / merge_settings
  - convert_in / convert_out (frontend <-> backend transforms)
  - _apply_settings (live-reload side effects)
  - SettingsWatcher for hot-reload via file mtime polling
"""

from __future__ import annotations

import json
import os
import threading

from python.helpers import defer, whisper
from python.helpers.print_style import PrintStyle
from python.helpers.secrets import get_default_secrets_manager

from . import dotenv, files
from .settings_core import (
    API_KEY_PLACEHOLDER,
    PASSWORD_PLACEHOLDER,
    SETTINGS_FILE,
    Settings,
    _env_to_dict,
    create_auth_token,
    get_default_settings,
    set_root_password,
)

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_settings: Settings | None = None


# ---------------------------------------------------------------------------
# Public API — get / set / merge
# ---------------------------------------------------------------------------


def get_settings() -> Settings:
    global _settings
    if not _settings:
        _settings = _read_settings_file()
    if not _settings:
        _settings = get_default_settings()
    norm = normalize_settings(_settings)
    return norm


def set_settings(settings: Settings, apply: bool = True):
    global _settings
    previous = _settings
    _settings = normalize_settings(settings)
    _write_settings_file(_settings)
    if apply:
        _apply_settings(previous)


def set_settings_delta(delta: dict, apply: bool = True):
    current = get_settings()
    new = {**current, **delta}
    set_settings(new, apply)  # type: ignore


def merge_settings(original: Settings, delta: dict) -> Settings:
    merged = original.copy()
    merged.update(delta)
    return merged


# ---------------------------------------------------------------------------
# Normalize / migrate
# ---------------------------------------------------------------------------


def normalize_settings(settings: Settings) -> Settings:
    copy = settings.copy()
    default = get_default_settings()

    # adjust settings values to match current version if needed
    if "version" not in copy or copy["version"] != default["version"]:
        _adjust_to_version(copy, default)
        copy["version"] = default["version"]  # sync version

    # remove keys that are not in default
    keys_to_remove = [key for key in copy if key not in default]
    for key in keys_to_remove:
        del copy[key]

    # add missing keys and normalize types
    for key, value in default.items():
        if key not in copy:
            copy[key] = value
        else:
            try:
                copy[key] = type(value)(copy[key])  # type: ignore
                if isinstance(copy[key], str):
                    copy[key] = copy[key].strip()  # strip strings
            except (ValueError, TypeError):
                copy[key] = value  # make default instead

    # mcp server token is set automatically
    copy["mcp_server_token"] = create_auth_token()

    return copy


def _adjust_to_version(settings: Settings, default: Settings):
    # starting with 0.9, the default prompt subfolder for agent no. 0 is agent0
    # switch to agent0 if the old default is used from v0.8
    if "version" not in settings or settings["version"].startswith("v0.8"):
        if "agent_profile" not in settings or settings["agent_profile"] == "default":
            settings["agent_profile"] = "agent0"


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def _read_settings_file() -> Settings | None:
    if os.path.exists(SETTINGS_FILE):
        content = files.read_file(SETTINGS_FILE)
        parsed = json.loads(content)
        return normalize_settings(parsed)


def _write_settings_file(settings: Settings):
    settings = settings.copy()
    _write_sensitive_settings(settings)
    _remove_sensitive_settings(settings)

    # write settings
    content = json.dumps(settings, indent=4)
    files.write_file(SETTINGS_FILE, content)


def _remove_sensitive_settings(settings: Settings):
    settings["api_keys"] = {}
    settings["auth_login"] = ""
    settings["auth_password"] = ""
    settings["rfc_password"] = ""
    settings["root_password"] = ""
    settings["mcp_server_token"] = ""
    settings["secrets"] = ""
    settings["langsmith_api_key"] = ""
    settings["langfuse_public_key"] = ""
    settings["langfuse_secret_key"] = ""
    settings["twilio_auth_token"] = ""


def _write_sensitive_settings(settings: Settings):
    for key, val in settings["api_keys"].items():
        dotenv.save_dotenv_value(key.upper(), val)

    dotenv.save_dotenv_value(dotenv.KEY_AUTH_LOGIN, settings["auth_login"])
    if settings["auth_password"]:
        dotenv.save_dotenv_value(dotenv.KEY_AUTH_PASSWORD, settings["auth_password"])
    if settings["rfc_password"]:
        dotenv.save_dotenv_value(dotenv.KEY_RFC_PASSWORD, settings["rfc_password"])

    if settings["root_password"]:
        dotenv.save_dotenv_value(dotenv.KEY_ROOT_PASSWORD, settings["root_password"])
    if settings["root_password"]:
        set_root_password(settings["root_password"])

    if settings.get("langsmith_api_key") is not None:
        dotenv.save_dotenv_value("LANGSMITH_API_KEY", settings.get("langsmith_api_key", ""))
    if settings.get("langsmith_project") is not None:
        dotenv.save_dotenv_value("LANGSMITH_PROJECT", settings.get("langsmith_project", ""))
    if settings.get("langsmith_endpoint") is not None:
        dotenv.save_dotenv_value("LANGSMITH_ENDPOINT", settings.get("langsmith_endpoint", ""))
    if settings.get("langfuse_public_key") is not None:
        dotenv.save_dotenv_value("LANGFUSE_PUBLIC_KEY", settings.get("langfuse_public_key", ""))
    if settings.get("langfuse_secret_key") is not None:
        dotenv.save_dotenv_value("LANGFUSE_SECRET_KEY", settings.get("langfuse_secret_key", ""))
    if settings.get("langfuse_host") is not None:
        dotenv.save_dotenv_value("LANGFUSE_HOST", settings.get("langfuse_host", ""))

    if settings.get("twilio_account_sid") is not None:
        dotenv.save_dotenv_value("TWILIO_ACCOUNT_SID", settings.get("twilio_account_sid", ""))
    if settings.get("twilio_auth_token") is not None:
        dotenv.save_dotenv_value("TWILIO_AUTH_TOKEN", settings.get("twilio_auth_token", ""))
    if settings.get("twilio_from_number") is not None:
        dotenv.save_dotenv_value("TWILIO_FROM_NUMBER", settings.get("twilio_from_number", ""))

    # Handle secrets separately - merge with existing preserving comments/order and support deletions
    secrets_manager = get_default_secrets_manager()
    submitted_content = settings["secrets"]
    secrets_manager.save_secrets_with_merge(submitted_content)


# ---------------------------------------------------------------------------
# Frontend conversion helpers
# ---------------------------------------------------------------------------


def convert_in(settings: dict) -> Settings:
    current = get_settings()
    for section in settings["sections"]:
        if "fields" in section:
            for field in section["fields"]:
                # Skip saving if value is a placeholder
                should_skip = field["value"] == PASSWORD_PLACEHOLDER or field["value"] == API_KEY_PLACEHOLDER

                if not should_skip:
                    # Special handling for browser_http_headers
                    if field["id"] == "browser_http_headers" or field["id"].endswith("_kwargs"):
                        current[field["id"]] = _env_to_dict(field["value"])
                    elif field["id"].startswith("api_key_"):
                        current["api_keys"][field["id"]] = field["value"]
                    else:
                        current[field["id"]] = field["value"]
    return current


# NOTE: convert_out lives in settings_ui.py because it builds UI field descriptors.
# It is re-exported via settings.py for backward compatibility.


# ---------------------------------------------------------------------------
# Apply settings (live-reload side effects)
# ---------------------------------------------------------------------------


def _apply_settings(previous: Settings | None):
    global _settings
    if _settings:
        from agent import AgentContext
        from initialize import initialize_agent

        config = initialize_agent()
        for ctx in AgentContext._contexts.values():
            ctx.config = config  # reinitialize context config with new settings
            # apply config to agents
            agent = ctx.agent0
            while agent:
                agent.config = ctx.config
                agent = agent.get_data(agent.DATA_NAME_SUBORDINATE)

        # reload whisper model if necessary
        if not previous or _settings["stt_model_size"] != previous["stt_model_size"]:
            defer.DeferredTask().start_task(
                whisper.preload, _settings["stt_model_size"]
            )  # TODO overkill, replace with background task

        # force memory reload on embedding model change
        if not previous or (
            _settings["embed_model_name"] != previous["embed_model_name"]
            or _settings["embed_model_provider"] != previous["embed_model_provider"]
            or _settings["embed_model_kwargs"] != previous["embed_model_kwargs"]
        ):
            from python.helpers.memory import reload as memory_reload

            memory_reload()

        # update mcp settings if necessary
        if not previous or _settings["mcp_servers"] != previous["mcp_servers"]:
            from python.helpers.mcp_handler import MCPConfig

            async def update_mcp_settings(mcp_servers: str):
                PrintStyle(background_color="black", font_color="white", padding=True).print("Updating MCP config...")
                AgentContext.log_to_all(type="info", content="Updating MCP settings...", temp=True)

                mcp_config = MCPConfig.get_instance()
                try:
                    MCPConfig.update(mcp_servers)
                except Exception as e:
                    AgentContext.log_to_all(
                        type="error",
                        content=f"Failed to update MCP settings: {e}",
                        temp=False,
                    )
                    (
                        PrintStyle(background_color="red", font_color="black", padding=True).print(
                            "Failed to update MCP settings"
                        )
                    )
                    (PrintStyle(background_color="black", font_color="red", padding=True).print(f"{e}"))

                PrintStyle(background_color="#6734C3", font_color="white", padding=True).print("Parsed MCP config:")
                (
                    PrintStyle(background_color="#334455", font_color="white", padding=False).print(
                        mcp_config.model_dump_json()
                    )
                )
                AgentContext.log_to_all(type="info", content="Finished updating MCP settings.", temp=True)

            defer.DeferredTask().start_task(
                update_mcp_settings, config.mcp_servers
            )  # TODO overkill, replace with background task

        # update token in mcp server
        current_token = (
            create_auth_token()
        )  # TODO - ugly, token in settings is generated from dotenv and does not always correspond
        if not previous or current_token != previous["mcp_server_token"]:

            async def update_mcp_token(token: str):
                from python.helpers.mcp_server import DynamicMcpProxy

                DynamicMcpProxy.get_instance().reconfigure(token=token)

            defer.DeferredTask().start_task(
                update_mcp_token, current_token
            )  # TODO overkill, replace with background task

        # update token in a2a server
        if not previous or current_token != previous["mcp_server_token"]:

            async def update_a2a_token(token: str):
                from python.helpers.fasta2a_server import DynamicA2AProxy

                DynamicA2AProxy.get_instance().reconfigure(token=token)

            defer.DeferredTask().start_task(
                update_a2a_token, current_token
            )  # TODO overkill, replace with background task


# ---------------------------------------------------------------------------
# SettingsWatcher — hot-reload via file mtime polling
# ---------------------------------------------------------------------------


class SettingsWatcher:
    """
    Watches the settings JSON file for changes and triggers a reload callback.

    Usage::

        def on_change(new_settings):
            print("Settings changed!")

        watcher = SettingsWatcher(on_change, interval=2.0)
        watcher.start()
        # ... later ...
        watcher.stop()
    """

    def __init__(self, callback, interval: float = 2.0):
        """
        Args:
            callback: Callable receiving the new Settings dict when the file changes.
            interval: Seconds between mtime checks.
        """
        self._callback = callback
        self._interval = interval
        self._last_mtime: float | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        """Start the watcher thread (daemon)."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        # Seed the mtime so we don't fire on first check
        self._last_mtime = self._get_mtime()
        self._thread = threading.Thread(target=self._run, daemon=True, name="SettingsWatcher")
        self._thread.start()

    def stop(self):
        """Signal the watcher to stop and wait for the thread to exit."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._interval + 1)
            self._thread = None

    # -- internal --

    def _get_mtime(self) -> float | None:
        try:
            return os.path.getmtime(SETTINGS_FILE)
        except OSError:
            return None

    def _run(self):
        while not self._stop_event.is_set():
            mtime = self._get_mtime()
            if mtime is not None and mtime != self._last_mtime:
                self._last_mtime = mtime
                try:
                    new_settings = get_settings()
                    self._callback(new_settings)
                except Exception:
                    pass  # swallow — watcher should never crash
            self._stop_event.wait(self._interval)
