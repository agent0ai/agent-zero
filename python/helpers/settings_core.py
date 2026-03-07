"""
settings_core.py — TypedDict definitions, default values, and version constants.

This module was extracted from settings.py as part of OPA-5 (Settings Architecture Refactor).
It contains:
  - All TypedDict definitions (Settings, PartialSettings, FieldOption, SettingsField, etc.)
  - Default settings factory (get_default_settings)
  - Version helpers
  - Constants (PASSWORD_PLACEHOLDER, API_KEY_PLACEHOLDER, SETTINGS_FILE)
  - Utility functions (_env_to_dict, _dict_to_env, create_auth_token, set_root_password, get_runtime_config)
"""

import base64
import hashlib
import json
import os
import subprocess
from typing import Any, Literal, TypedDict

from . import dotenv, files

# ---------------------------------------------------------------------------
# TypedDict definitions
# ---------------------------------------------------------------------------


class GmailAccountInfo(TypedDict):
    """Gmail account metadata stored in settings"""

    email: str
    authenticated: bool
    scopes: list[str]
    added_date: str  # ISO format datetime


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
    prompt_enhance_enabled: bool
    prompt_enhance_max_chars: int

    llm_router_enabled: bool
    llm_router_auto_configure: bool

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

    # Gmail API accounts - dict mapping account_name -> GmailAccountInfo
    gmail_accounts: dict[str, GmailAccountInfo]

    google_voice_auto_send: bool
    google_voice_shortcuts: bool
    google_voice_contact_rules: str
    google_voice_tag_filters: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str

    cowork_enabled: bool
    cowork_require_approvals: bool
    cowork_allowed_paths: list[str]
    cowork_impactful_tools: str

    telemetry_enabled: bool
    telemetry_max_events: int

    observability_provider: str
    observability_auto_store: bool
    langsmith_api_key: str
    langsmith_project: str
    langsmith_endpoint: str
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str

    # Tier / performance profile controls
    deployment_tier: str
    enable_persona_systems: bool
    max_concurrent_sessions: int
    perf_slo_profile: str


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


class SettingsOutput(TypedDict):
    sections: list[SettingsSection]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PASSWORD_PLACEHOLDER = "****PSWD****"
API_KEY_PLACEHOLDER = "************"

SETTINGS_FILE = files.get_abs_path("tmp/settings.json")


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------


def _get_version():
    from python.helpers import git

    return git.get_version()


# ---------------------------------------------------------------------------
# Auth token
# ---------------------------------------------------------------------------


def create_auth_token() -> str:
    from python.helpers import runtime

    runtime_id = runtime.get_persistent_id()
    username = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN) or ""
    password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD) or ""
    # use base64 encoding for a more compact token with alphanumeric chars
    hash_bytes = hashlib.sha256(f"{runtime_id}:{username}:{password}".encode()).digest()
    # encode as base64 and remove any non-alphanumeric chars (like +, /, =)
    b64_token = base64.urlsafe_b64encode(hash_bytes).decode().replace("=", "")
    return b64_token[:16]


# ---------------------------------------------------------------------------
# Env <-> dict helpers
# ---------------------------------------------------------------------------


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
        elif isinstance(value, dict | list | bool) or value is None:
            # Serialize as unquoted JSON
            lines.append(f"{key}={json.dumps(value, separators=(',', ':'))}")
        else:
            # Numbers and other types as unquoted strings
            lines.append(f"{key}={value}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Root password
# ---------------------------------------------------------------------------


def set_root_password(password: str):
    from python.helpers import runtime

    if not runtime.is_dockerized():
        raise Exception("root password can only be set in dockerized environments")
    _result = subprocess.run(
        ["chpasswd"],
        input=f"root:{password}".encode(),
        capture_output=True,
        check=True,
    )
    dotenv.save_dotenv_value(dotenv.KEY_ROOT_PASSWORD, password)


# ---------------------------------------------------------------------------
# Runtime config
# ---------------------------------------------------------------------------


def get_runtime_config(set: Settings):
    from python.helpers import runtime

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
            host, _port = host.split(":")
        if host.endswith("/"):
            host = host[:-1]
        return {
            "code_exec_ssh_enabled": set["shell_interface"] == "ssh",
            "code_exec_ssh_addr": host,
            "code_exec_ssh_port": set["rfc_port_ssh"],
            "code_exec_ssh_user": "root",
        }


# ---------------------------------------------------------------------------
# Default settings
# ---------------------------------------------------------------------------


def get_default_settings() -> Settings:
    from python.helpers import runtime

    # Use Ollama URL from environment or default to localhost
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    env_tier = os.getenv("TIER", "free").strip().lower()
    tier = env_tier if env_tier in {"free", "pro"} else "free"
    env_profile = os.getenv("PERF_SLO_PROFILE", "").strip().lower()
    perf_profile = env_profile if env_profile in {"free", "pro"} else tier
    persona_default = "true" if tier == "pro" else "false"
    enable_persona = os.getenv("ENABLE_PERSONA_SYSTEMS", persona_default).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    max_sessions_default = 100 if tier == "pro" else 25
    try:
        max_concurrent_sessions = int(os.getenv("MAX_CONCURRENT_SESSIONS", str(max_sessions_default)))
    except ValueError:
        max_concurrent_sessions = max_sessions_default

    return Settings(
        version=_get_version(),
        chat_model_provider="ollama",
        chat_model_name="qwen2.5-coder:3b",
        chat_model_api_base=ollama_base_url,
        chat_model_kwargs={"temperature": "0"},
        chat_model_ctx_length=32768,
        chat_model_ctx_history=0.7,
        chat_model_vision=False,
        chat_model_rl_requests=0,
        chat_model_rl_input=0,
        chat_model_rl_output=0,
        util_model_provider="ollama",
        util_model_name="qwen2.5-coder:3b",
        util_model_api_base=ollama_base_url,
        util_model_ctx_length=32768,
        util_model_ctx_input=0.7,
        util_model_kwargs={"temperature": "0"},
        util_model_rl_requests=0,
        util_model_rl_input=0,
        util_model_rl_output=0,
        embed_model_provider="huggingface",
        embed_model_name="sentence-transformers/all-MiniLM-L6-v2",
        embed_model_api_base="",
        embed_model_kwargs={},
        embed_model_rl_requests=0,
        embed_model_rl_input=0,
        browser_model_provider="ollama",
        browser_model_name="qwen2.5-coder:3b",
        browser_model_api_base=ollama_base_url,
        browser_model_vision=False,
        browser_model_rl_requests=0,
        browser_model_rl_input=0,
        browser_model_rl_output=0,
        browser_model_kwargs={"temperature": "0"},
        browser_http_headers={},
        memory_recall_enabled=True,
        memory_recall_delayed=False,
        memory_recall_interval=3,
        memory_recall_history_len=10000,
        memory_recall_memories_max_search=12,
        memory_recall_solutions_max_search=8,
        memory_recall_memories_max_result=5,
        memory_recall_solutions_max_result=3,
        memory_recall_similarity_threshold=0.7,
        memory_recall_query_prep=True,
        memory_recall_post_filter=True,
        memory_memorize_enabled=True,
        memory_memorize_consolidation=True,
        memory_memorize_replace_threshold=0.9,
        prompt_enhance_enabled=False,
        prompt_enhance_max_chars=4000,
        llm_router_enabled=False,
        llm_router_auto_configure=False,
        api_keys={},
        auth_login="",
        auth_password="",
        root_password="",
        agent_profile="agent0",
        agent_memory_subdir="default",
        agent_knowledge_subdir="custom",
        rfc_auto_docker=True,
        rfc_url="localhost",
        rfc_password="",
        rfc_port_http=55080,
        rfc_port_ssh=55022,
        shell_interface="local" if runtime.is_dockerized() else "ssh",
        stt_model_size="base",
        stt_language="en",
        stt_silence_threshold=0.3,
        stt_silence_duration=1000,
        stt_waiting_timeout=2000,
        tts_kokoro=True,
        mcp_servers='{\n    "mcpServers": {}\n}',
        mcp_client_init_timeout=10,
        mcp_client_tool_timeout=120,
        mcp_server_enabled=False,
        mcp_server_token=create_auth_token(),
        a2a_server_enabled=False,
        variables="",
        secrets="",
        litellm_global_kwargs={},
        update_check_enabled=True,
        gmail_accounts={},
        google_voice_auto_send=False,
        google_voice_shortcuts=True,
        google_voice_contact_rules="{}",
        google_voice_tag_filters="[]",
        twilio_account_sid=dotenv.get_dotenv_value("TWILIO_ACCOUNT_SID", ""),
        twilio_auth_token=dotenv.get_dotenv_value("TWILIO_AUTH_TOKEN", ""),
        twilio_from_number=dotenv.get_dotenv_value("TWILIO_FROM_NUMBER", ""),
        cowork_enabled=False,
        cowork_require_approvals=True,
        cowork_allowed_paths=["/a0"],
        cowork_impactful_tools="code_execution_tool,email,email_advanced,memory_delete,memory_forget,memory_save,scheduler,browser_agent",
        telemetry_enabled=False,
        telemetry_max_events=200,
        observability_provider="local",
        observability_auto_store=True,
        langsmith_api_key=dotenv.get_dotenv_value("LANGSMITH_API_KEY", ""),
        langsmith_project=dotenv.get_dotenv_value("LANGSMITH_PROJECT", ""),
        langsmith_endpoint=dotenv.get_dotenv_value("LANGSMITH_ENDPOINT", ""),
        langfuse_public_key=dotenv.get_dotenv_value("LANGFUSE_PUBLIC_KEY", ""),
        langfuse_secret_key=dotenv.get_dotenv_value("LANGFUSE_SECRET_KEY", ""),
        langfuse_host=dotenv.get_dotenv_value("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        deployment_tier=tier,
        enable_persona_systems=enable_persona,
        max_concurrent_sessions=max_concurrent_sessions,
        perf_slo_profile=perf_profile,
    )
