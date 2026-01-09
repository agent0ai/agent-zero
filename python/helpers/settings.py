import base64
import hashlib
import json
import os
import re
import subprocess
from typing import Any, Literal, TypedDict, cast, TypeVar

import models
from python.helpers import runtime, whisper, defer, git
from . import files, dotenv
from python.helpers.print_style import PrintStyle
from python.helpers.providers import get_providers, FieldOption as ProvidersFO
from python.helpers.secrets import get_default_secrets_manager
from python.helpers import dirty_json


T = TypeVar("T")


def get_default_value(name: str, value: T) -> T:
    """
    Load setting value from .env with A0_SET_ prefix, falling back to default.

    Args:
        name: Setting name (will be prefixed with A0_SET_)
        value: Default value to use if env var not set

    Returns:
        Environment variable value (type-normalized) or default value
    """
    env_value = dotenv.get_dotenv_value(
        f"A0_SET_{name}", dotenv.get_dotenv_value(f"A0_SET_{name.upper()}", None)
    )

    if env_value is None:
        return value

    # Normalize type to match value param type
    try:
        if isinstance(value, bool):
            return env_value.strip().lower() in ("true", "1", "yes", "on")  # type: ignore
        elif isinstance(value, dict):
            return json.loads(env_value.strip())  # type: ignore
        elif isinstance(value, str):
            return str(env_value).strip()  # type: ignore
        else:
            return type(value)(env_value.strip())  # type: ignore
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        PrintStyle(background_color="yellow", font_color="black").print(
            f"Warning: Invalid value for A0_SET_{name}='{env_value}': {e}. Using default: {value}"
        )
        return value


class Settings(TypedDict):
    version: str

    chat_model_provider: str
    chat_model_name: str
    chat_model_api_base: str
    chat_model_kwargs: dict[str, Any]
    chat_model_ctx_length: int
    chat_model_ctx_history: float
    chat_model_vision: bool
    chat_model_rl_requests: int
    chat_model_rl_input: int
    chat_model_rl_output: int

    util_model_provider: str
    util_model_name: str
    util_model_api_base: str
    util_model_kwargs: dict[str, Any]
    util_model_ctx_length: int
    util_model_ctx_input: float
    util_model_rl_requests: int
    util_model_rl_input: int
    util_model_rl_output: int

    embed_model_provider: str
    embed_model_name: str
    embed_model_api_base: str
    embed_model_kwargs: dict[str, Any]
    embed_model_rl_requests: int
    embed_model_rl_input: int

    browser_model_provider: str
    browser_model_name: str
    browser_model_api_base: str
    browser_model_vision: bool
    browser_model_rl_requests: int
    browser_model_rl_input: int
    browser_model_rl_output: int
    browser_model_kwargs: dict[str, Any]
    browser_http_headers: dict[str, Any]

    agent_profile: str
    agent_memory_subdir: str
    agent_knowledge_subdir: str

    memory_recall_enabled: bool
    memory_recall_delayed: bool
    memory_recall_interval: int
    memory_recall_history_len: int
    memory_recall_memories_max_search: int
    memory_recall_solutions_max_search: int
    memory_recall_memories_max_result: int
    memory_recall_solutions_max_result: int
    memory_recall_similarity_threshold: float
    memory_recall_query_prep: bool
    memory_recall_post_filter: bool
    memory_memorize_enabled: bool
    memory_memorize_consolidation: bool
    memory_memorize_replace_threshold: float

    api_keys: dict[str, str]

    auth_login: str
    auth_password: str
    root_password: str

    rfc_auto_docker: bool
    rfc_url: str
    rfc_password: str
    rfc_port_http: int
    rfc_port_ssh: int

    shell_interface: Literal["local", "ssh"]

    stt_model_size: str
    stt_language: str
    stt_silence_threshold: float
    stt_silence_duration: int
    stt_waiting_timeout: int

    tts_kokoro: bool

    mcp_servers: str
    mcp_client_init_timeout: int
    mcp_client_tool_timeout: int
    mcp_server_enabled: bool
    mcp_server_token: str

    a2a_server_enabled: bool

    variables: str
    secrets: str

    # LiteLLM global kwargs applied to all model calls
    litellm_global_kwargs: dict[str, Any]

    update_check_enabled: bool


class PartialSettings(Settings, total=False):
    pass


class FieldOption(TypedDict):
    value: str
    label: str


class SettingsField(TypedDict, total=False):
    id: str
    title: str
    description: str
    type: Literal[
        "text",
        "number",
        "select",
        "range",
        "textarea",
        "password",
        "switch",
        "button",
        "html",
    ]
    value: Any
    min: float
    max: float
    step: float
    hidden: bool
    options: list[FieldOption]
    style: str


class SettingsSection(TypedDict, total=False):
    id: str
    title: str
    description: str
    fields: list[SettingsField]
    tab: str  # Indicates which tab this section belongs to


class ModelProvider(ProvidersFO):
    pass


class SettingsOutputAdditional(TypedDict):
    chat_providers: list[ModelProvider]
    embedding_providers: list[ModelProvider]
    shell_interfaces: list[FieldOption]
    agent_subdirs: list[FieldOption]
    knowledge_subdirs: list[FieldOption]
    stt_models: list[FieldOption]
    is_dockerized: bool


class SettingsOutput(TypedDict):
    settings: Settings
    additional: SettingsOutputAdditional


PASSWORD_PLACEHOLDER = "****PSWD****"
API_KEY_PLACEHOLDER = "************"

SETTINGS_FILE = files.get_abs_path("tmp/settings.json")
_settings: Settings | None = None

OptionT = TypeVar("OptionT", bound=FieldOption)


def _ensure_option_present(
    options: list[OptionT] | None, current_value: str | None
) -> list[OptionT]:
    """
    Ensure the currently selected value exists in a dropdown options list.
    If missing, inserts it at the front as {value: current_value, label: current_value}.
    """
    opts = list(options or [])
    if not current_value:
        return opts
    for o in opts:
        if o.get("value") == current_value:
            return opts
    opts.insert(0, cast(OptionT, {"value": current_value, "label": current_value}))
    return opts


def convert_out(settings: Settings) -> SettingsOutput:
    out = SettingsOutput(
        settings=settings.copy(),
        additional=SettingsOutputAdditional(
            chat_providers=get_providers("chat"),
            embedding_providers=get_providers("embedding"),
            shell_interfaces=[
                {"value": "local", "label": "Local Python TTY"},
                {"value": "ssh", "label": "SSH"},
            ],
            is_dockerized=runtime.is_dockerized(),
            agent_subdirs=[
                {"value": subdir, "label": subdir}
                for subdir in files.get_subdirectories("agents")
                if subdir != "_example"
            ],
            knowledge_subdirs=[
                {"value": subdir, "label": subdir}
                for subdir in files.get_subdirectories("knowledge", exclude="default")
            ],
            stt_models=[
                {"value": "tiny", "label": "Tiny (39M, English)"},
                {"value": "base", "label": "Base (74M, English)"},
                {"value": "small", "label": "Small (244M, English)"},
                {"value": "medium", "label": "Medium (769M, English)"},
                {"value": "large", "label": "Large (1.5B, Multilingual)"},
                {"value": "turbo", "label": "Turbo (Multilingual)"},
            ],
        ),
    )

    # ensure dropdown options include currently selected values
    additional = out["additional"]
    current = out["settings"]

    additional["chat_providers"] = _ensure_option_present(
        additional.get("chat_providers"), current.get("chat_model_provider")
    )
    additional["chat_providers"] = _ensure_option_present(
        additional.get("chat_providers"), current.get("util_model_provider")
    )
    additional["chat_providers"] = _ensure_option_present(
        additional.get("chat_providers"), current.get("browser_model_provider")
    )
    additional["embedding_providers"] = _ensure_option_present(
        additional.get("embedding_providers"), current.get("embed_model_provider")
    )
    additional["shell_interfaces"] = _ensure_option_present(
        additional.get("shell_interfaces"), current.get("shell_interface")
    )
    additional["agent_subdirs"] = _ensure_option_present(
        additional.get("agent_subdirs"), current.get("agent_profile")
    )
    additional["knowledge_subdirs"] = _ensure_option_present(
        additional.get("knowledge_subdirs"), current.get("agent_knowledge_subdir")
    )
    additional["stt_models"] = _ensure_option_present(
        additional.get("stt_models"), current.get("stt_model_size")
    )

    # masked api keys
    providers = get_providers("chat") + get_providers("embedding")
    for provider in providers:
        provider_name = provider["value"]
        api_key = settings["api_keys"].get(
            provider_name, models.get_api_key(provider_name)
        )
        settings["api_keys"][provider_name] = (
            API_KEY_PLACEHOLDER if api_key and api_key != "None" else ""
        )

    # load auth from dotenv
    out["settings"]["auth_login"] = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN) or ""
    out["settings"]["auth_password"] = (
        PASSWORD_PLACEHOLDER
        if dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD)
        else ""
    )
    out["settings"]["rfc_password"] = (
        PASSWORD_PLACEHOLDER if dotenv.get_dotenv_value(dotenv.KEY_RFC_PASSWORD) else ""
    )
    out["settings"]["root_password"] = (
        PASSWORD_PLACEHOLDER
        if dotenv.get_dotenv_value(dotenv.KEY_ROOT_PASSWORD)
        else ""
    )

    # secrets
    secrets_manager = get_default_secrets_manager()
    try:
        out["settings"]["secrets"] = secrets_manager.get_masked_secrets()
    except Exception:
        out["settings"]["secrets"] = ""

    # mask API keys before sending to frontend
    if isinstance(out["settings"].get("api_keys"), dict):
        for provider, value in list(out["settings"]["api_keys"].items()):
            if value:
                out["settings"]["api_keys"][provider] = API_KEY_PLACEHOLDER

    # normalize certain fields
    for key, value in list(out["settings"].items()):
        # convert kwargs dicts to .env format
        if (key.endswith("_kwargs") or key == "browser_http_headers") and isinstance(
            value, dict
        ):
            out["settings"][key] = _dict_to_env(value)
    return out


def _get_api_key_field(settings: Settings, provider: str, title: str) -> SettingsField:
    key = settings["api_keys"].get(provider, models.get_api_key(provider))
    # For API keys, use simple asterisk placeholder for existing keys
    return {
        "id": f"api_key_{provider}",
        "title": title,
        "type": "text",
        "value": (API_KEY_PLACEHOLDER if key and key != "None" else ""),
    }


def convert_in(settings: Settings) -> Settings:
    current = get_settings()

    for key, value in settings.items():
        # Special handling for browser_http_headers and *_kwargs (stored as .env text)
        if (key == "browser_http_headers" or key.endswith("_kwargs")) and isinstance(
            value, str
        ):
            current[key] = _env_to_dict(value)
            continue

        current[key] = value
    return current


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
    return _settings


def set_settings_delta(delta: dict, apply: bool = True):
    current = get_settings()
    new = {**current, **delta}
    return set_settings(new, apply)  # type: ignore


def merge_settings(original: Settings, delta: dict) -> Settings:
    merged = original.copy()
    merged.update(delta)
    return merged


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


def _write_sensitive_settings(settings: Settings):
    for key, val in settings["api_keys"].items():
        if val != API_KEY_PLACEHOLDER:
            dotenv.save_dotenv_value(key.upper(), val)

    dotenv.save_dotenv_value(dotenv.KEY_AUTH_LOGIN, settings["auth_login"])
    if settings["auth_password"] != PASSWORD_PLACEHOLDER:
        dotenv.save_dotenv_value(dotenv.KEY_AUTH_PASSWORD, settings["auth_password"])
    if settings["rfc_password"] != PASSWORD_PLACEHOLDER:
        dotenv.save_dotenv_value(dotenv.KEY_RFC_PASSWORD, settings["rfc_password"])
    if settings["root_password"] != PASSWORD_PLACEHOLDER:
        if runtime.is_dockerized():
            dotenv.save_dotenv_value(
                dotenv.KEY_ROOT_PASSWORD, settings["root_password"]
            )
            set_root_password(settings["root_password"])

    # Handle secrets separately - merge with existing preserving comments/order and support deletions
    secrets_manager = get_default_secrets_manager()
    submitted_content = settings["secrets"]
    secrets_manager.save_secrets_with_merge(submitted_content)


def get_default_settings() -> Settings:
    return Settings(
        version=_get_version(),
        chat_model_provider=get_default_value("chat_model_provider", "openrouter"),
        chat_model_name=get_default_value("chat_model_name", "openai/gpt-4.1"),
        chat_model_api_base=get_default_value("chat_model_api_base", ""),
        chat_model_kwargs=get_default_value("chat_model_kwargs", {"temperature": "0"}),
        chat_model_ctx_length=get_default_value("chat_model_ctx_length", 100000),
        chat_model_ctx_history=get_default_value("chat_model_ctx_history", 0.7),
        chat_model_vision=get_default_value("chat_model_vision", True),
        chat_model_rl_requests=get_default_value("chat_model_rl_requests", 0),
        chat_model_rl_input=get_default_value("chat_model_rl_input", 0),
        chat_model_rl_output=get_default_value("chat_model_rl_output", 0),
        util_model_provider=get_default_value("util_model_provider", "openrouter"),
        util_model_name=get_default_value("util_model_name", "openai/gpt-4.1-mini"),
        util_model_api_base=get_default_value("util_model_api_base", ""),
        util_model_ctx_length=get_default_value("util_model_ctx_length", 100000),
        util_model_ctx_input=get_default_value("util_model_ctx_input", 0.7),
        util_model_kwargs=get_default_value("util_model_kwargs", {"temperature": "0"}),
        util_model_rl_requests=get_default_value("util_model_rl_requests", 0),
        util_model_rl_input=get_default_value("util_model_rl_input", 0),
        util_model_rl_output=get_default_value("util_model_rl_output", 0),
        embed_model_provider=get_default_value("embed_model_provider", "huggingface"),
        embed_model_name=get_default_value(
            "embed_model_name", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        embed_model_api_base=get_default_value("embed_model_api_base", ""),
        embed_model_kwargs=get_default_value("embed_model_kwargs", {}),
        embed_model_rl_requests=get_default_value("embed_model_rl_requests", 0),
        embed_model_rl_input=get_default_value("embed_model_rl_input", 0),
        browser_model_provider=get_default_value(
            "browser_model_provider", "openrouter"
        ),
        browser_model_name=get_default_value("browser_model_name", "openai/gpt-4.1"),
        browser_model_api_base=get_default_value("browser_model_api_base", ""),
        browser_model_vision=get_default_value("browser_model_vision", True),
        browser_model_rl_requests=get_default_value("browser_model_rl_requests", 0),
        browser_model_rl_input=get_default_value("browser_model_rl_input", 0),
        browser_model_rl_output=get_default_value("browser_model_rl_output", 0),
        browser_model_kwargs=get_default_value(
            "browser_model_kwargs", {"temperature": "0"}
        ),
        browser_http_headers=get_default_value("browser_http_headers", {}),
        memory_recall_enabled=get_default_value("memory_recall_enabled", True),
        memory_recall_delayed=get_default_value("memory_recall_delayed", False),
        memory_recall_interval=get_default_value("memory_recall_interval", 3),
        memory_recall_history_len=get_default_value("memory_recall_history_len", 10000),
        memory_recall_memories_max_search=get_default_value(
            "memory_recall_memories_max_search", 12
        ),
        memory_recall_solutions_max_search=get_default_value(
            "memory_recall_solutions_max_search", 8
        ),
        memory_recall_memories_max_result=get_default_value(
            "memory_recall_memories_max_result", 5
        ),
        memory_recall_solutions_max_result=get_default_value(
            "memory_recall_solutions_max_result", 3
        ),
        memory_recall_similarity_threshold=get_default_value(
            "memory_recall_similarity_threshold", 0.7
        ),
        memory_recall_query_prep=get_default_value("memory_recall_query_prep", True),
        memory_recall_post_filter=get_default_value("memory_recall_post_filter", True),
        memory_memorize_enabled=get_default_value("memory_memorize_enabled", True),
        memory_memorize_consolidation=get_default_value(
            "memory_memorize_consolidation", True
        ),
        memory_memorize_replace_threshold=get_default_value(
            "memory_memorize_replace_threshold", 0.9
        ),
        api_keys={},
        auth_login="",
        auth_password="",
        root_password="",
        agent_profile=get_default_value("agent_profile", "agent0"),
        agent_memory_subdir=get_default_value("agent_memory_subdir", "default"),
        agent_knowledge_subdir=get_default_value("agent_knowledge_subdir", "custom"),
        rfc_auto_docker=get_default_value("rfc_auto_docker", True),
        rfc_url=get_default_value("rfc_url", "localhost"),
        rfc_password="",
        rfc_port_http=get_default_value("rfc_port_http", 55080),
        rfc_port_ssh=get_default_value("rfc_port_ssh", 55022),
        shell_interface=get_default_value(
            "shell_interface", "local" if runtime.is_dockerized() else "ssh"
        ),
        stt_model_size=get_default_value("stt_model_size", "base"),
        stt_language=get_default_value("stt_language", "en"),
        stt_silence_threshold=get_default_value("stt_silence_threshold", 0.3),
        stt_silence_duration=get_default_value("stt_silence_duration", 1000),
        stt_waiting_timeout=get_default_value("stt_waiting_timeout", 2000),
        tts_kokoro=get_default_value("tts_kokoro", True),
        mcp_servers=get_default_value("mcp_servers", '{\n    "mcpServers": {}\n}'),
        mcp_client_init_timeout=get_default_value("mcp_client_init_timeout", 10),
        mcp_client_tool_timeout=get_default_value("mcp_client_tool_timeout", 120),
        mcp_server_enabled=get_default_value("mcp_server_enabled", False),
        mcp_server_token=create_auth_token(),
        a2a_server_enabled=get_default_value("a2a_server_enabled", False),
        variables="",
        secrets="",
        litellm_global_kwargs=get_default_value("litellm_global_kwargs", {}),
        update_check_enabled=get_default_value("update_check_enabled", True),
    )


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
            task = defer.DeferredTask().start_task(
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
                PrintStyle(
                    background_color="black", font_color="white", padding=True
                ).print("Updating MCP config...")
                AgentContext.log_to_all(
                    type="info", content="Updating MCP settings...", temp=True
                )

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
                        PrintStyle(
                            background_color="red", font_color="black", padding=True
                        ).print("Failed to update MCP settings")
                    )
                    (
                        PrintStyle(
                            background_color="black", font_color="red", padding=True
                        ).print(f"{e}")
                    )

                PrintStyle(
                    background_color="#6734C3", font_color="white", padding=True
                ).print("Parsed MCP config:")
                (
                    PrintStyle(
                        background_color="#334455", font_color="white", padding=False
                    ).print(mcp_config.model_dump_json())
                )
                AgentContext.log_to_all(
                    type="info", content="Finished updating MCP settings.", temp=True
                )

            task2 = defer.DeferredTask().start_task(
                update_mcp_settings, config.mcp_servers
            )  # TODO overkill, replace with background task

        # update token in mcp server
        current_token = create_auth_token()  # TODO - ugly, token in settings is generated from dotenv and does not always correspond
        if not previous or current_token != previous["mcp_server_token"]:

            async def update_mcp_token(token: str):
                from python.helpers.mcp_server import DynamicMcpProxy

                DynamicMcpProxy.get_instance().reconfigure(token=token)

            task3 = defer.DeferredTask().start_task(
                update_mcp_token, current_token
            )  # TODO overkill, replace with background task

        # update token in a2a server
        if not previous or current_token != previous["mcp_server_token"]:

            async def update_a2a_token(token: str):
                from python.helpers.fasta2a_server import DynamicA2AProxy

                DynamicA2AProxy.get_instance().reconfigure(token=token)

            task4 = defer.DeferredTask().start_task(
                update_a2a_token, current_token
            )  # TODO overkill, replace with background task


def _env_to_dict(data: str):
    result = {}
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # If quoted, treat as string
        if value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1].replace('\\"', '"')  # Unescape quotes
        elif value.startswith("'") and value.endswith("'"):
            result[key] = value[1:-1].replace("\\'", "'")  # Unescape quotes
        else:
            # Not quoted, try JSON parse
            try:
                result[key] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                result[key] = value

    return result


def _dict_to_env(data_dict):
    lines = []
    for key, value in data_dict.items():
        if isinstance(value, str):
            # Quote strings and escape internal quotes
            escaped_value = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped_value}"')
        elif isinstance(value, (dict, list, bool)) or value is None:
            # Serialize as unquoted JSON
            lines.append(f"{key}={json.dumps(value, separators=(',', ':'))}")
        else:
            # Numbers and other types as unquoted strings
            lines.append(f"{key}={value}")

    return "\n".join(lines)


def set_root_password(password: str):
    if not runtime.is_dockerized():
        raise Exception("root password can only be set in dockerized environments")
    _result = subprocess.run(
        ["chpasswd"],
        input=f"root:{password}".encode(),
        capture_output=True,
        check=True,
    )
    dotenv.save_dotenv_value(dotenv.KEY_ROOT_PASSWORD, password)


def get_runtime_config(set: Settings):
    if runtime.is_dockerized():
        return {
            "code_exec_ssh_enabled": set["shell_interface"] == "ssh",
            "code_exec_ssh_addr": "localhost",
            "code_exec_ssh_port": 22,
            "code_exec_ssh_user": "root",
        }
    else:
        host = set["rfc_url"]
        if "//" in host:
            host = host.split("//")[1]
        if ":" in host:
            host, port = host.split(":")
        if host.endswith("/"):
            host = host[:-1]
        return {
            "code_exec_ssh_enabled": set["shell_interface"] == "ssh",
            "code_exec_ssh_addr": host,
            "code_exec_ssh_port": set["rfc_port_ssh"],
            "code_exec_ssh_user": "root",
        }


def create_auth_token() -> str:
    runtime_id = runtime.get_persistent_id()
    username = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN) or ""
    password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD) or ""
    # use base64 encoding for a more compact token with alphanumeric chars
    hash_bytes = hashlib.sha256(f"{runtime_id}:{username}:{password}".encode()).digest()
    # encode as base64 and remove any non-alphanumeric chars (like +, /, =)
    b64_token = base64.urlsafe_b64encode(hash_bytes).decode().replace("=", "")
    return b64_token[:16]


def _get_version():
    return git.get_version()
