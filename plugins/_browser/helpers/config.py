from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent import Agent


PLUGIN_NAME = "_browser"
MODEL_PRESET_KEY = "model_preset"
BROWSER_MODEL_ACTIVE_KEY = "_browser_model_active"
DEFAULT_HOMEPAGE_KEY = "default_homepage"
AUTOFOCUS_ACTIVE_PAGE_KEY = "autofocus_active_page"
TAB_SCOPE_KEY = "browser_tab_scope"
MAX_OPEN_TABS_KEY = "max_open_tabs"
RUNTIME_BACKEND_KEY = "runtime_backend"
HOST_BROWSER_PRIVACY_POLICY_KEY = "host_browser_privacy_policy"
HOST_BROWSER_PROFILE_MODE_KEY = "host_browser_profile_mode"
HOST_BROWSER_SELECTION_KEY = "host_browser_selection"
PROXY_SERVER_KEY = "proxy_server"
PROXY_BYPASS_KEY = "proxy_bypass"
PROXY_USERNAME_KEY = "proxy_username"
PROXY_PASSWORD_KEY = "proxy_password"
KEYBOARD_LAYOUT_KEY = "keyboard_layout"
KEYBOARD_VARIANT_KEY = "keyboard_variant"
RUNTIME_BACKENDS = {"container", "host_required"}
BROWSER_TAB_SCOPES = {"per_context", "shared"}
HOST_BROWSER_PRIVACY_POLICIES = {"enforce_local", "warn", "allow"}
HOST_BROWSER_PROFILE_MODES = {"existing", "agent"}
DEFAULT_BROWSER_TAB_SCOPE = "per_context"
DEFAULT_MAX_OPEN_TABS = 32
MIN_MAX_OPEN_TABS = 1
HARD_MAX_OPEN_TABS = 50
DEFAULT_HOST_BROWSER_PRIVACY_POLICY = "allow"
EXTENSION_BROWSER_SELECTION_PREFIX = "extension:"
INVALID_EXTENSION_BROWSER_SELECTION = EXTENSION_BROWSER_SELECTION_PREFIX
DEVELOPMENT_EXTENSION_BROWSER_SELECTION_PREFIX = "development-extension:"
INVALID_DEVELOPMENT_EXTENSION_BROWSER_SELECTION = (
    DEVELOPMENT_EXTENSION_BROWSER_SELECTION_PREFIX
)
_EXTENSION_NAMESPACE_RE = re.compile(
    r"^extension(?:[^A-Za-z0-9._/-]*:|$)",
    re.IGNORECASE | re.ASCII,
)
_EXTENSION_BRIDGE_ID_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?$"
)
_DEVELOPMENT_EXTENSION_NAMESPACE_RE = re.compile(
    r"^development-extension(?:[^A-Za-z0-9._/-]*:|$)",
    re.IGNORECASE | re.ASCII,
)
_production_selection_write = ContextVar("browser_production_selection_write", default=False)


@dataclass(frozen=True, slots=True)
class ExtensionBrowserSelection:
    value: str
    bridge_id: str


@dataclass(frozen=True, slots=True)
class DevelopmentExtensionBrowserSelection:
    value: str
    bridge_id: str


def parse_development_extension_browser_selection(
    value: Any,
) -> DevelopmentExtensionBrowserSelection | None:
    """Parse the separate development namespace without legacy fallback."""

    selection = str(value or "").strip()
    if not _DEVELOPMENT_EXTENSION_NAMESPACE_RE.match(selection):
        return None
    if not selection.startswith(DEVELOPMENT_EXTENSION_BROWSER_SELECTION_PREFIX):
        raise ValueError(
            "the reserved development extension prefix must be exactly "
            "'development-extension:'"
        )
    bridge_id = selection.removeprefix(
        DEVELOPMENT_EXTENSION_BROWSER_SELECTION_PREFIX
    )
    if not _EXTENSION_BRIDGE_ID_RE.fullmatch(bridge_id):
        raise ValueError("the development extension bridge ID is invalid")
    return DevelopmentExtensionBrowserSelection(selection, bridge_id)


def parse_extension_browser_selection(value: Any) -> ExtensionBrowserSelection | None:
    """Parse the reserved extension selection without accepting a legacy fallback."""
    selection = str(value or "").strip()
    if not _EXTENSION_NAMESPACE_RE.match(selection):
        return None
    if not selection.startswith(EXTENSION_BROWSER_SELECTION_PREFIX):
        raise ValueError(
            "the reserved extension browser prefix must be exactly 'extension:'"
        )

    bridge_id = selection.removeprefix(EXTENSION_BROWSER_SELECTION_PREFIX)
    if not _EXTENSION_BRIDGE_ID_RE.fullmatch(bridge_id):
        raise ValueError(
            "the extension browser bridge ID must be 1-128 ASCII letters, digits, dots, "
            "underscores, or hyphens"
        )
    return ExtensionBrowserSelection(value=selection, bridge_id=bridge_id)


def _normalize_extension_paths(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    elif isinstance(value, (list, tuple, set)):
        candidates = list(value)
    else:
        candidates = []

    normalized_paths: list[str] = []
    seen: set[str] = set()
    for entry in candidates:
        raw_path = str(entry or "").strip()
        if not raw_path:
            continue
        normalized = str(Path(raw_path).expanduser())
        if normalized in seen:
            continue
        seen.add(normalized)
        normalized_paths.append(normalized)
    return normalized_paths


def _normalize_model_preset(value: Any) -> str:
    return str(value or "").strip()


def _normalize_host_browser_selection(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        development_selection = parse_development_extension_browser_selection(raw)
    except ValueError:
        return INVALID_DEVELOPMENT_EXTENSION_BROWSER_SELECTION
    if development_selection is not None:
        return development_selection.value
    try:
        extension_selection = parse_extension_browser_selection(raw)
    except ValueError:
        # Keep malformed values in the reserved namespace so runtime selection
        # rejects them instead of routing them through the legacy connector.
        return INVALID_EXTENSION_BROWSER_SELECTION
    if extension_selection is not None:
        return extension_selection.value
    endpoint_like = "://" in raw or (
        raw.rpartition(":")[0] and raw.rpartition(":")[2].isdigit()
    )
    if endpoint_like:
        return "".join(ch for ch in raw if ch.isprintable() and not ch.isspace())[:2048]
    normalized = raw.lower().replace(" ", "_")
    return "".join(
        ch for ch in normalized if ch.isalnum() or ch in {"_", "-", ":", ".", "/"}
    )[:200]


def normalize_host_browser_selection(value: Any) -> str:
    """Normalize legacy selections while reserving extension values fail-closed."""

    return _normalize_host_browser_selection(value)


def validate_extension_browser_selection_change(
    *,
    proposed_value: Any,
    current_value: Any,
    proposed_runtime_backend: Any,
    current_runtime_backend: Any,
) -> None:
    """Block new extension selections until the atomic activation flow exists."""

    proposed = _normalize_host_browser_selection(proposed_value)
    current = _normalize_host_browser_selection(current_value)
    try:
        development_selection = parse_development_extension_browser_selection(
            proposed
        )
    except ValueError as exc:
        raise ValueError(
            "The reserved development extension browser selection is invalid."
        ) from exc
    if development_selection is not None:
        proposed_backend = _normalize_runtime_backend(proposed_runtime_backend)
        current_backend = _normalize_runtime_backend(current_runtime_backend)
        if proposed == current and not (
            proposed_backend == "host_required" and current_backend != "host_required"
        ):
            return
        raise ValueError(
            "Development Chrome extension selection is retired. Use the production "
            "browser pairing flow."
        )
    try:
        extension_selection = parse_extension_browser_selection(proposed)
    except ValueError as exc:
        raise ValueError("The reserved extension browser selection is invalid.") from exc
    if extension_selection is not None:
        proposed_backend = _normalize_runtime_backend(proposed_runtime_backend)
        current_backend = _normalize_runtime_backend(current_runtime_backend)
        if proposed == current and not (
            proposed_backend == "host_required" and current_backend != "host_required"
        ):
            return
        if _production_selection_write.get() is True:
            return
        raise ValueError(
            "Choose this paired browser using the protected browser selection flow."
        )


@contextmanager
def protected_production_selection_write():
    """Lexical capability held only by the protected paired-browser selector."""
    token = _production_selection_write.set(True)
    try:
        yield
    finally:
        _production_selection_write.reset(token)


def _normalize_default_homepage(value: Any) -> str:
    homepage = str(value or "").strip()
    return homepage or "about:blank"


def _normalize_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _normalize_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _normalize_xkb_token(value: Any) -> str:
    return "".join(
        ch for ch in str(value or "").strip().lower() if ch.isalnum() or ch in {"_", "-"}
    )[:32]


def _normalize_choice(value: Any, *, allowed: set[str], default: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in allowed:
        return normalized
    return default


def _normalize_runtime_backend(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized == "host_when_available":
        return "host_required"
    return _normalize_choice(normalized, allowed=RUNTIME_BACKENDS, default="container")


def _model_config_summary(config: dict[str, Any] | None) -> str:
    if not isinstance(config, dict):
        return ""
    provider = str(config.get("provider", "") or "").strip()
    model_name = str(config.get("name", "") or "").strip()
    return " / ".join(part for part in (provider, model_name) if part)


def normalize_browser_config(settings: dict[str, Any] | None) -> dict[str, Any]:
    raw = settings if isinstance(settings, dict) else {}
    extension_paths = _normalize_extension_paths(raw.get("extension_paths", []))
    keyboard_layout = _normalize_xkb_token(raw.get(KEYBOARD_LAYOUT_KEY, ""))
    keyboard_variant = (
        _normalize_xkb_token(raw.get(KEYBOARD_VARIANT_KEY, "")) if keyboard_layout else ""
    )
    return {
        "extension_paths": extension_paths,
        DEFAULT_HOMEPAGE_KEY: _normalize_default_homepage(
            raw.get(DEFAULT_HOMEPAGE_KEY, raw.get("starting_page", "about:blank"))
        ),
        AUTOFOCUS_ACTIVE_PAGE_KEY: _normalize_bool(
            raw.get(AUTOFOCUS_ACTIVE_PAGE_KEY, True),
            default=True,
        ),
        TAB_SCOPE_KEY: _normalize_choice(
            raw.get(TAB_SCOPE_KEY, DEFAULT_BROWSER_TAB_SCOPE),
            allowed=BROWSER_TAB_SCOPES,
            default=DEFAULT_BROWSER_TAB_SCOPE,
        ),
        MAX_OPEN_TABS_KEY: _normalize_int(
            raw.get(MAX_OPEN_TABS_KEY, DEFAULT_MAX_OPEN_TABS),
            default=DEFAULT_MAX_OPEN_TABS,
            minimum=MIN_MAX_OPEN_TABS,
            maximum=HARD_MAX_OPEN_TABS,
        ),
        RUNTIME_BACKEND_KEY: _normalize_runtime_backend(
            raw.get(RUNTIME_BACKEND_KEY, "container")
        ),
        HOST_BROWSER_PRIVACY_POLICY_KEY: _normalize_choice(
            raw.get(HOST_BROWSER_PRIVACY_POLICY_KEY, DEFAULT_HOST_BROWSER_PRIVACY_POLICY),
            allowed=HOST_BROWSER_PRIVACY_POLICIES,
            default=DEFAULT_HOST_BROWSER_PRIVACY_POLICY,
        ),
        HOST_BROWSER_PROFILE_MODE_KEY: _normalize_choice(
            raw.get(HOST_BROWSER_PROFILE_MODE_KEY, "existing"),
            allowed=HOST_BROWSER_PROFILE_MODES,
            default="existing",
        ),
        HOST_BROWSER_SELECTION_KEY: _normalize_host_browser_selection(
            raw.get(HOST_BROWSER_SELECTION_KEY, raw.get("host_browser_choice", ""))
        ),
        PROXY_SERVER_KEY: str(raw.get(PROXY_SERVER_KEY, "") or "").strip()[:2048],
        PROXY_BYPASS_KEY: str(raw.get(PROXY_BYPASS_KEY, "") or "").strip()[:4096],
        PROXY_USERNAME_KEY: str(raw.get(PROXY_USERNAME_KEY, "") or "")[:1024],
        PROXY_PASSWORD_KEY: str(raw.get(PROXY_PASSWORD_KEY, "") or "")[:4096],
        KEYBOARD_LAYOUT_KEY: keyboard_layout,
        KEYBOARD_VARIANT_KEY: keyboard_variant,
        MODEL_PRESET_KEY: _normalize_model_preset(raw.get(MODEL_PRESET_KEY, "")),
    }


def browser_runtime_config(settings: dict[str, Any] | None) -> dict[str, Any]:
    config = normalize_browser_config(settings)
    return {
        "extension_paths": config["extension_paths"],
        PROXY_SERVER_KEY: config[PROXY_SERVER_KEY],
        PROXY_BYPASS_KEY: config[PROXY_BYPASS_KEY],
        PROXY_USERNAME_KEY: config[PROXY_USERNAME_KEY],
        PROXY_PASSWORD_KEY: config[PROXY_PASSWORD_KEY],
        KEYBOARD_LAYOUT_KEY: config[KEYBOARD_LAYOUT_KEY],
        KEYBOARD_VARIANT_KEY: config[KEYBOARD_VARIANT_KEY],
    }


def get_browser_config(agent: "Agent | None" = None) -> dict[str, Any]:
    from helpers import plugins

    return normalize_browser_config(plugins.get_plugin_config(PLUGIN_NAME, agent=agent) or {})


def get_browser_model_preset_name(
    agent: "Agent | None" = None,
    settings: dict[str, Any] | None = None,
) -> str:
    config = (
        normalize_browser_config(settings)
        if settings is not None
        else get_browser_config(agent=agent)
    )
    return str(config.get(MODEL_PRESET_KEY, "") or "").strip()


def get_browser_model_preset_options(
    agent: "Agent | None" = None,
    settings: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    from plugins._model_config.helpers import model_config

    selected_name = get_browser_model_preset_name(agent=agent, settings=settings)
    options: list[dict[str, Any]] = []
    found_selected = False

    for preset in model_config.get_presets():
        name = str(preset.get("name", "") or "").strip()
        if not name:
            continue
        if name == selected_name:
            found_selected = True
        chat_cfg = preset.get("chat", {}) if isinstance(preset, dict) else {}
        if not isinstance(chat_cfg, dict):
            chat_cfg = {}
        summary = _model_config_summary(chat_cfg)
        options.append(
            {
                "name": name,
                "label": name,
                "missing": False,
                "summary": summary,
            }
        )

    if selected_name and not found_selected:
        options.append(
            {
                "name": selected_name,
                "label": f"{selected_name} (missing)",
                "missing": True,
                "summary": "",
            }
        )

    return options


def get_browser_main_model_summary(agent: "Agent | None" = None) -> str:
    from plugins._model_config.helpers import model_config

    return _model_config_summary(model_config.get_chat_model_config(agent))


def resolve_browser_model_selection(
    agent: "Agent | None" = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from plugins._model_config.helpers import model_config

    preset_name = get_browser_model_preset_name(agent=agent, settings=settings)
    if preset_name:
        preset = model_config.get_preset_by_name(preset_name)
        if isinstance(preset, dict):
            if hasattr(model_config, "build_config_from_preset"):
                default_preset = model_config.get_preset_by_name(
                    model_config.DEFAULT_PRESET_NAME
                ) or {}
                base_config = (
                    model_config.preset_to_config(default_preset)
                    if hasattr(model_config, "preset_to_config")
                    else {}
                )
                preset_config = model_config.build_config_from_preset(
                    preset,
                    base_config,
                    strip_api_key=False,
                    slots=("chat",),
                )
                chat_cfg = preset_config.get("chat_model", {})
            else:
                chat_cfg = preset.get("chat", {})
            if isinstance(chat_cfg, dict) and (
                str(chat_cfg.get("provider", "") or "").strip()
                or str(chat_cfg.get("name", "") or "").strip()
            ):
                return {
                    "config": chat_cfg,
                    "source_kind": "preset",
                    "source_label": f"Preset '{preset_name}' via _model_config",
                    "selected_preset_name": preset_name,
                    "preset_status": "active",
                    "warning": "",
                }
            return {
                "config": model_config.get_chat_model_config(agent),
                "source_kind": "main",
                "source_label": "Main Model via _model_config",
                "selected_preset_name": preset_name,
                "preset_status": "invalid",
                "warning": (
                    f"Configured browser preset '{preset_name}' does not define a chat model. "
                    "Falling back to the Main Model."
                ),
            }

        return {
            "config": model_config.get_chat_model_config(agent),
            "source_kind": "main",
            "source_label": "Main Model via _model_config",
            "selected_preset_name": preset_name,
            "preset_status": "missing",
            "warning": (
                f"Configured browser preset '{preset_name}' was not found. "
                "Falling back to the Main Model."
            ),
        }

    return {
        "config": model_config.get_chat_model_config(agent),
        "source_kind": "main",
        "source_label": "Main Model via _model_config",
        "selected_preset_name": "",
        "preset_status": "none",
        "warning": "",
    }


def activate_browser_model(agent: "Agent") -> dict[str, Any]:
    selection = resolve_browser_model_selection(agent=agent)
    agent.set_data(
        BROWSER_MODEL_ACTIVE_KEY,
        selection["selected_preset_name"]
        if selection["source_kind"] == "preset"
        else "",
    )
    return selection


def clear_browser_model(agent: "Agent") -> None:
    agent.set_data(BROWSER_MODEL_ACTIVE_KEY, "")


def browser_model_is_active(agent: "Agent") -> bool:
    return bool(agent.get_data(BROWSER_MODEL_ACTIVE_KEY))


def resolve_browser_model(
    agent: "Agent",
    settings: dict[str, Any] | None = None,
    fallback: Any = None,
):
    selection = resolve_browser_model_selection(agent=agent, settings=settings)
    if selection["source_kind"] == "main":
        clear_browser_model(agent)
        return fallback if fallback is not None else agent.get_chat_model()

    import models
    from plugins._model_config.helpers import model_config

    model_config_object = model_config.build_model_config(
        selection["config"],
        models.ModelType.CHAT,
    )
    return models.get_chat_model(
        model_config_object.provider,
        model_config_object.name,
        model_config=model_config_object,
        **model_config_object.build_kwargs(),
    )


def describe_browser_extensions(settings: dict[str, Any] | None) -> dict[str, Any]:
    config = normalize_browser_config(settings)
    path_details: list[dict[str, Any]] = []
    for extension_path in config["extension_paths"]:
        path = Path(extension_path)
        exists = path.exists()
        is_dir = path.is_dir() if exists else False
        path_details.append(
            {
                "path": extension_path,
                "exists": exists,
                "is_dir": is_dir,
                "loadable": exists and is_dir,
            }
        )

    active_paths = [item["path"] for item in path_details if item["loadable"]]
    invalid_paths = [item["path"] for item in path_details if not item["loadable"]]
    active = bool(active_paths)

    warnings: list[str] = []
    if config["extension_paths"] and not active_paths:
        warnings.append(
            "None of the enabled extension directories are readable unpacked folders."
        )
    elif invalid_paths:
        warnings.append(
            "Some configured extension directories are missing or not directories, so they will be skipped."
        )

    return {
        "active": active,
        "configured_paths": config["extension_paths"],
        "active_paths": active_paths,
        "invalid_paths": invalid_paths,
        "path_details": path_details,
        "active_path_count": len(active_paths),
        "warnings": warnings,
    }


def build_browser_launch_config(settings: dict[str, Any] | None) -> dict[str, Any]:
    config = normalize_browser_config(settings)
    extensions = describe_browser_extensions(config)
    args = ["--hide-crash-restore-bubble"]
    channel: str | None = None
    browser_mode = "chromium"
    proxy = None

    if extensions["active"]:
        joined_paths = ",".join(extensions["active_paths"])
        args.extend(
            [
                f"--disable-extensions-except={joined_paths}",
                f"--load-extension={joined_paths}",
            ]
        )

    if config[PROXY_SERVER_KEY]:
        proxy = {"server": config[PROXY_SERVER_KEY]}
        for config_key, proxy_key in (
            (PROXY_BYPASS_KEY, "bypass"),
            (PROXY_USERNAME_KEY, "username"),
            (PROXY_PASSWORD_KEY, "password"),
        ):
            if config[config_key]:
                proxy[proxy_key] = config[config_key]

    return {
        "args": args,
        "proxy": proxy,
        "browser_mode": browser_mode,
        "channel": channel,
        "extensions": extensions,
        "requires_full_browser": True,
    }
