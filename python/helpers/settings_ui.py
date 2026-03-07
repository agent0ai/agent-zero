"""
settings_ui.py — UI field descriptors for frontend rendering.

This module was extracted from settings.py as part of OPA-5 (Settings Architecture Refactor).
It contains the ``convert_out`` function which transforms a Settings dict into the
SettingsOutput structure consumed by the frontend.
"""

from __future__ import annotations

from typing import cast

import models
from python.helpers import runtime
from python.helpers.providers import get_providers
from python.helpers.secrets import get_default_secrets_manager

from . import dotenv, files
from .settings_core import (
    API_KEY_PLACEHOLDER,
    PASSWORD_PLACEHOLDER,
    FieldOption,
    Settings,
    SettingsField,
    SettingsOutput,
    SettingsSection,
    _dict_to_env,
    get_default_settings,
)


def _get_api_key_field(settings: Settings, provider: str, title: str) -> SettingsField:
    key = settings["api_keys"].get(provider, models.get_api_key(provider))
    # For API keys, use simple asterisk placeholder for existing keys
    return {
        "id": f"api_key_{provider}",
        "title": title,
        "type": "text",
        "value": (API_KEY_PLACEHOLDER if key and key != "None" else ""),
    }


def convert_out(settings: Settings) -> SettingsOutput:
    default_settings = get_default_settings()

    # main model section
    chat_model_fields: list[SettingsField] = []
    chat_model_fields.append(
        {
            "id": "chat_model_provider",
            "title": "Chat model provider",
            "description": "Select provider for main chat model used by Agent Zero",
            "type": "select",
            "value": settings["chat_model_provider"],
            "options": cast("list[FieldOption]", get_providers("chat")),
        }
    )
    chat_model_fields.append(
        {
            "id": "chat_model_name",
            "title": "Chat model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["chat_model_name"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_api_base",
            "title": "Chat model API base URL",
            "description": "API base URL for main chat model. Leave empty for default. Only relevant for Azure, local and custom (other) providers.",
            "type": "text",
            "value": settings["chat_model_api_base"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_ctx_length",
            "title": "Chat model context length",
            "description": "Maximum number of tokens in the context window for LLM. System prompt, chat history, RAG and response all count towards this limit.",
            "type": "number",
            "value": settings["chat_model_ctx_length"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_ctx_history",
            "title": "Context window space for chat history",
            "description": "Portion of context window dedicated to chat history visible to the agent. Chat history will automatically be optimized to fit. Smaller size will result in shorter and more summarized history. The remaining space will be used for system prompt, RAG and response.",
            "type": "range",
            "min": 0.01,
            "max": 1,
            "step": 0.01,
            "value": settings["chat_model_ctx_history"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_vision",
            "title": "Supports Vision",
            "description": "Models capable of Vision can for example natively see the content of image attachments.",
            "type": "switch",
            "value": settings["chat_model_vision"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_rl_requests",
            "title": "Requests per minute limit",
            "description": "Limits the number of requests per minute to the chat model. Waits if the limit is exceeded. Set to 0 to disable rate limiting.",
            "type": "number",
            "value": settings["chat_model_rl_requests"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_rl_input",
            "title": "Input tokens per minute limit",
            "description": "Limits the number of input tokens per minute to the chat model. Waits if the limit is exceeded. Set to 0 to disable rate limiting.",
            "type": "number",
            "value": settings["chat_model_rl_input"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_rl_output",
            "title": "Output tokens per minute limit",
            "description": "Limits the number of output tokens per minute to the chat model. Waits if the limit is exceeded. Set to 0 to disable rate limiting.",
            "type": "number",
            "value": settings["chat_model_rl_output"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_kwargs",
            "title": "Chat model additional parameters",
            "description": "Any other parameters supported by <a href='https://docs.litellm.ai/docs/set_keys' target='_blank'>LiteLLM</a>. Format is KEY=VALUE on individual lines, like .env file. Value can also contain JSON objects - when unquoted, it is treated as object, number etc., when quoted, it is treated as string.",
            "type": "textarea",
            "value": _dict_to_env(settings["chat_model_kwargs"]),
        }
    )

    chat_model_section: SettingsSection = {
        "id": "chat_model",
        "title": "Chat Model",
        "description": "Selection and settings for main chat model used by Agent Zero",
        "fields": chat_model_fields,
        "tab": "agent",
    }

    # main model section
    util_model_fields: list[SettingsField] = []
    util_model_fields.append(
        {
            "id": "util_model_provider",
            "title": "Utility model provider",
            "description": "Select provider for utility model used by the framework",
            "type": "select",
            "value": settings["util_model_provider"],
            "options": cast("list[FieldOption]", get_providers("chat")),
        }
    )
    util_model_fields.append(
        {
            "id": "util_model_name",
            "title": "Utility model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["util_model_name"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_api_base",
            "title": "Utility model API base URL",
            "description": "API base URL for utility model. Leave empty for default. Only relevant for Azure, local and custom (other) providers.",
            "type": "text",
            "value": settings["util_model_api_base"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_rl_requests",
            "title": "Requests per minute limit",
            "description": "Limits the number of requests per minute to the utility model. Waits if the limit is exceeded. Set to 0 to disable rate limiting.",
            "type": "number",
            "value": settings["util_model_rl_requests"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_rl_input",
            "title": "Input tokens per minute limit",
            "description": "Limits the number of input tokens per minute to the utility model. Waits if the limit is exceeded. Set to 0 to disable rate limiting.",
            "type": "number",
            "value": settings["util_model_rl_input"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_rl_output",
            "title": "Output tokens per minute limit",
            "description": "Limits the number of output tokens per minute to the utility model. Waits if the limit is exceeded. Set to 0 to disable rate limiting.",
            "type": "number",
            "value": settings["util_model_rl_output"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_kwargs",
            "title": "Utility model additional parameters",
            "description": "Any other parameters supported by <a href='https://docs.litellm.ai/docs/set_keys' target='_blank'>LiteLLM</a>. Format is KEY=VALUE on individual lines, like .env file. Value can also contain JSON objects - when unquoted, it is treated as object, number etc., when quoted, it is treated as string.",
            "type": "textarea",
            "value": _dict_to_env(settings["util_model_kwargs"]),
        }
    )

    util_model_section: SettingsSection = {
        "id": "util_model",
        "title": "Utility model",
        "description": "Smaller, cheaper, faster model for handling utility tasks like organizing memory, preparing prompts, summarizing.",
        "fields": util_model_fields,
        "tab": "agent",
    }

    # embedding model section
    embed_model_fields: list[SettingsField] = []
    embed_model_fields.append(
        {
            "id": "embed_model_provider",
            "title": "Embedding model provider",
            "description": "Select provider for embedding model used by the framework",
            "type": "select",
            "value": settings["embed_model_provider"],
            "options": cast("list[FieldOption]", get_providers("embedding")),
        }
    )
    embed_model_fields.append(
        {
            "id": "embed_model_name",
            "title": "Embedding model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["embed_model_name"],
        }
    )

    embed_model_fields.append(
        {
            "id": "embed_model_api_base",
            "title": "Embedding model API base URL",
            "description": "API base URL for embedding model. Leave empty for default. Only relevant for Azure, local and custom (other) providers.",
            "type": "text",
            "value": settings["embed_model_api_base"],
        }
    )

    embed_model_fields.append(
        {
            "id": "embed_model_rl_requests",
            "title": "Requests per minute limit",
            "description": "Limits the number of requests per minute to the embedding model. Waits if the limit is exceeded. Set to 0 to disable rate limiting.",
            "type": "number",
            "value": settings["embed_model_rl_requests"],
        }
    )

    embed_model_fields.append(
        {
            "id": "embed_model_rl_input",
            "title": "Input tokens per minute limit",
            "description": "Limits the number of input tokens per minute to the embedding model. Waits if the limit is exceeded. Set to 0 to disable rate limiting.",
            "type": "number",
            "value": settings["embed_model_rl_input"],
        }
    )

    embed_model_fields.append(
        {
            "id": "embed_model_kwargs",
            "title": "Embedding model additional parameters",
            "description": "Any other parameters supported by <a href='https://docs.litellm.ai/docs/set_keys' target='_blank'>LiteLLM</a>. Format is KEY=VALUE on individual lines, like .env file. Value can also contain JSON objects - when unquoted, it is treated as object, number etc., when quoted, it is treated as string.",
            "type": "textarea",
            "value": _dict_to_env(settings["embed_model_kwargs"]),
        }
    )

    embed_model_section: SettingsSection = {
        "id": "embed_model",
        "title": "Embedding Model",
        "description": f"Settings for the embedding model used by Agent Zero.<br><h4>Warning: No need to change</h4>The default HuggingFace model {default_settings['embed_model_name']} is preloaded and runs locally within the docker container and there's no need to change it unless you have a specific requirements for embedding.",
        "fields": embed_model_fields,
        "tab": "agent",
    }

    # embedding model section
    browser_model_fields: list[SettingsField] = []
    browser_model_fields.append(
        {
            "id": "browser_model_provider",
            "title": "Web Browser model provider",
            "description": "Select provider for web browser model used by <a href='https://github.com/browser-use/browser-use' target='_blank'>browser-use</a> framework",
            "type": "select",
            "value": settings["browser_model_provider"],
            "options": cast("list[FieldOption]", get_providers("chat")),
        }
    )
    browser_model_fields.append(
        {
            "id": "browser_model_name",
            "title": "Web Browser model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["browser_model_name"],
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_model_api_base",
            "title": "Web Browser model API base URL",
            "description": "API base URL for web browser model. Leave empty for default. Only relevant for Azure, local and custom (other) providers.",
            "type": "text",
            "value": settings["browser_model_api_base"],
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_model_vision",
            "title": "Use Vision",
            "description": "Models capable of Vision can use it to analyze web pages from screenshots. Increases quality but also token usage.",
            "type": "switch",
            "value": settings["browser_model_vision"],
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_model_rl_requests",
            "title": "Web Browser model rate limit requests",
            "description": "Rate limit requests for web browser model.",
            "type": "number",
            "value": settings["browser_model_rl_requests"],
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_model_rl_input",
            "title": "Web Browser model rate limit input",
            "description": "Rate limit input for web browser model.",
            "type": "number",
            "value": settings["browser_model_rl_input"],
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_model_rl_output",
            "title": "Web Browser model rate limit output",
            "description": "Rate limit output for web browser model.",
            "type": "number",
            "value": settings["browser_model_rl_output"],
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_model_kwargs",
            "title": "Web Browser model additional parameters",
            "description": "Any other parameters supported by <a href='https://docs.litellm.ai/docs/set_keys' target='_blank'>LiteLLM</a>. Format is KEY=VALUE on individual lines, like .env file. Value can also contain JSON objects - when unquoted, it is treated as object, number etc., when quoted, it is treated as string.",
            "type": "textarea",
            "value": _dict_to_env(settings["browser_model_kwargs"]),
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_http_headers",
            "title": "HTTP Headers",
            "description": "HTTP headers to include with all browser requests. Format is KEY=VALUE on individual lines, like .env file. Value can also contain JSON objects - when unquoted, it is treated as object, number etc., when quoted, it is treated as string. Example: Authorization=Bearer token123",
            "type": "textarea",
            "value": _dict_to_env(settings.get("browser_http_headers", {})),
        }
    )

    browser_model_section: SettingsSection = {
        "id": "browser_model",
        "title": "Web Browser Model",
        "description": "Settings for the web browser model. Agent Zero uses <a href='https://github.com/browser-use/browser-use' target='_blank'>browser-use</a> agentic framework to handle web interactions.",
        "fields": browser_model_fields,
        "tab": "agent",
    }

    # basic auth section
    auth_fields: list[SettingsField] = []

    auth_fields.append(
        {
            "id": "auth_login",
            "title": "UI Login",
            "description": "Set user name for web UI",
            "type": "text",
            "value": dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN) or "",
        }
    )

    auth_fields.append(
        {
            "id": "auth_password",
            "title": "UI Password",
            "description": "Set user password for web UI",
            "type": "password",
            "value": (PASSWORD_PLACEHOLDER if dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD) else ""),
        }
    )

    if runtime.is_dockerized():
        auth_fields.append(
            {
                "id": "root_password",
                "title": "root Password",
                "description": "Change linux root password in docker container. This password can be used for SSH access. Original password was randomly generated during setup.",
                "type": "password",
                "value": "",
            }
        )

    auth_section: SettingsSection = {
        "id": "auth",
        "title": "Authentication",
        "description": "Settings for authentication to use Agent Zero Web UI.",
        "fields": auth_fields,
        "tab": "external",
    }

    # Passkey Security section
    passkey_fields: list[SettingsField] = []
    passkey_fields.append(
        {
            "id": "passkey_manager",
            "title": "Passkey (WebAuthn) Manager",
            "description": "Register your phone or hardware security key to enable passwordless auth and tool authorization.",
            "type": "html",
            "value": "<x-component path='/settings/external/passkey-manager.html' />",
        }
    )

    passkey_section: SettingsSection = {
        "id": "passkey_security",
        "title": "Hardware Security (Passkeys)",
        "description": "Manage FIDO2/WebAuthn credentials for secure hardware-bound access.",
        "fields": passkey_fields,
        "tab": "external",
    }

    # api keys model section
    api_keys_fields: list[SettingsField] = []

    # Collect unique providers from both chat and embedding sections
    providers_seen: set[str] = set()
    for p_type in ("chat", "embedding"):
        for provider in get_providers(p_type):
            pid_lower = provider["value"].lower()
            if pid_lower in providers_seen:
                continue
            providers_seen.add(pid_lower)
            api_keys_fields.append(_get_api_key_field(settings, pid_lower, provider["label"]))

    api_keys_section: SettingsSection = {
        "id": "api_keys",
        "title": "API Keys",
        "description": "API keys for model providers and services used by Agent Zero. You can set multiple API keys separated by a comma (,). They will be used in round-robin fashion.<br>For more information abou Agent Zero Venice provider, see <a href='http://agent-zero.ai/?community/api-dashboard/about' target='_blank'>Agent Zero Venice</a>.",
        "fields": api_keys_fields,
        "tab": "external",
    }

    # LiteLLM global config section
    litellm_fields: list[SettingsField] = []

    litellm_fields.append(
        {
            "id": "litellm_global_kwargs",
            "title": "LiteLLM global parameters",
            "description": "Global LiteLLM params (e.g. timeout, stream_timeout) in .env format: one KEY=VALUE per line. Example: <code>stream_timeout=30</code>. Applied to all LiteLLM calls unless overridden. See <a href='https://docs.litellm.ai/docs/set_keys' target='_blank'>LiteLLM</a> and <a href='https://docs.litellm.ai/docs/proxy/timeout' target='_blank'>timeouts</a>.",
            "type": "textarea",
            "value": _dict_to_env(settings["litellm_global_kwargs"]),
            "style": "height: 12em",
        }
    )

    litellm_section: SettingsSection = {
        "id": "litellm",
        "title": "LiteLLM Global Settings",
        "description": "Configure global parameters passed to LiteLLM for all providers.",
        "fields": litellm_fields,
        "tab": "external",
    }

    # Agent config section
    agent_fields: list[SettingsField] = []

    agent_fields.append(
        {
            "id": "agent_profile",
            "title": "Default agent profile",
            "description": "Subdirectory of /agents folder to be used by default agent no. 0. Subordinate agents can be spawned with other profiles, that is on their superior agent to decide. This setting affects the behaviour of the top level agent you communicate with.",
            "type": "select",
            "value": settings["agent_profile"],
            "options": [
                {"value": subdir, "label": subdir}
                for subdir in files.get_subdirectories("agents")
                if subdir != "_example"
            ],
        }
    )

    agent_fields.append(
        {
            "id": "agent_knowledge_subdir",
            "title": "Knowledge subdirectory",
            "description": "Subdirectory of /knowledge folder to use for agent knowledge import. 'default' subfolder is always imported and contains framework knowledge.",
            "type": "select",
            "value": settings["agent_knowledge_subdir"],
            "options": [
                {"value": subdir, "label": subdir}
                for subdir in files.get_subdirectories("knowledge", exclude="default")
            ],
        }
    )

    agent_section: SettingsSection = {
        "id": "agent",
        "title": "Agent Config",
        "description": "Agent parameters.",
        "fields": agent_fields,
        "tab": "agent",
    }

    cowork_fields: list[SettingsField] = []

    cowork_fields.append(
        {
            "id": "cowork_enabled",
            "title": "Enable Cowork mode",
            "description": "Enable folder scoping and approval checks for agent actions.",
            "type": "switch",
            "value": settings["cowork_enabled"],
        }
    )

    cowork_fields.append(
        {
            "id": "cowork_require_approvals",
            "title": "Require approvals for impactful actions",
            "description": "Prompt for approval before actions like shell execution, email, or other impactful tools.",
            "type": "switch",
            "value": settings["cowork_require_approvals"],
        }
    )

    cowork_fields.append(
        {
            "id": "cowork_impactful_tools",
            "title": "Impactful tools list",
            "description": "Comma or newline separated tool names that always require approval.",
            "type": "textarea",
            "value": settings["cowork_impactful_tools"],
            "style": "height: 8em",
        }
    )

    cowork_fields.append(
        {
            "id": "cowork_manage",
            "title": "Cowork folders & approvals",
            "description": "Manage folder allowlist and review approvals per thread.",
            "type": "button",
            "value": "Open Cowork Manager",
        }
    )

    cowork_section: SettingsSection = {
        "id": "cowork",
        "title": "Cowork Mode",
        "description": "Folder scoping and approval workflow for agent actions.",
        "fields": cowork_fields,
        "tab": "agent",
    }

    memory_fields: list[SettingsField] = []

    memory_fields.append(
        {
            "id": "agent_memory_subdir",
            "title": "Memory Subdirectory",
            "description": "Subdirectory of /memory folder to use for agent memory storage. Used to separate memory storage between different instances.",
            "type": "text",
            "value": settings["agent_memory_subdir"],
            # "options": [
            #     {"value": subdir, "label": subdir}
            #     for subdir in files.get_subdirectories("memory", exclude="embeddings")
            # ],
        }
    )

    memory_fields.append(
        {
            "id": "memory_dashboard",
            "title": "Memory Dashboard",
            "description": "View and explore all stored memories in a table format with filtering and search capabilities.",
            "type": "button",
            "value": "Open Dashboard",
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_enabled",
            "title": "Memory auto-recall enabled",
            "description": "Agent Zero will automatically recall memories based on convesation context.",
            "type": "switch",
            "value": settings["memory_recall_enabled"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_delayed",
            "title": "Memory auto-recall delayed",
            "description": "The agent will not wait for auto memory recall. Memories will be delivered one message later. This speeds up agent's response time but may result in less relevant first step.",
            "type": "switch",
            "value": settings["memory_recall_delayed"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_query_prep",
            "title": "Auto-recall AI query preparation",
            "description": "Enables vector DB query preparation from conversation context by utility LLM for auto-recall. Improves search quality, adds 1 utility LLM call per auto-recall.",
            "type": "switch",
            "value": settings["memory_recall_query_prep"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_post_filter",
            "title": "Auto-recall AI post-filtering",
            "description": "Enables memory relevance filtering by utility LLM for auto-recall. Improves search quality, adds 1 utility LLM call per auto-recall.",
            "type": "switch",
            "value": settings["memory_recall_post_filter"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_interval",
            "title": "Memory auto-recall interval",
            "description": "Memories are recalled after every user or superior agent message. During agent's monologue, memories are recalled every X turns based on this parameter.",
            "type": "range",
            "min": 1,
            "max": 10,
            "step": 1,
            "value": settings["memory_recall_interval"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_history_len",
            "title": "Memory auto-recall history length",
            "description": "The length of conversation history passed to memory recall LLM for context (in characters).",
            "type": "number",
            "value": settings["memory_recall_history_len"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_similarity_threshold",
            "title": "Memory auto-recall similarity threshold",
            "description": "The threshold for similarity search in memory recall (0 = no similarity, 1 = exact match).",
            "type": "range",
            "min": 0,
            "max": 1,
            "step": 0.01,
            "value": settings["memory_recall_similarity_threshold"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_memories_max_search",
            "title": "Memory auto-recall max memories to search",
            "description": "The maximum number of memories returned by vector DB for further processing.",
            "type": "number",
            "value": settings["memory_recall_memories_max_search"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_memories_max_result",
            "title": "Memory auto-recall max memories to use",
            "description": "The maximum number of memories to inject into A0's context window.",
            "type": "number",
            "value": settings["memory_recall_memories_max_result"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_solutions_max_search",
            "title": "Memory auto-recall max solutions to search",
            "description": "The maximum number of solutions returned by vector DB for further processing.",
            "type": "number",
            "value": settings["memory_recall_solutions_max_search"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_recall_solutions_max_result",
            "title": "Memory auto-recall max solutions to use",
            "description": "The maximum number of solutions to inject into A0's context window.",
            "type": "number",
            "value": settings["memory_recall_solutions_max_result"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_memorize_enabled",
            "title": "Auto-memorize enabled",
            "description": "A0 will automatically memorize facts and solutions from conversation history.",
            "type": "switch",
            "value": settings["memory_memorize_enabled"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_memorize_consolidation",
            "title": "Auto-memorize AI consolidation",
            "description": "A0 will automatically consolidate similar memories using utility LLM. Improves memory quality over time, adds 2 utility LLM calls per memory.",
            "type": "switch",
            "value": settings["memory_memorize_consolidation"],
        }
    )

    memory_fields.append(
        {
            "id": "memory_memorize_replace_threshold",
            "title": "Auto-memorize replacement threshold",
            "description": "Only applies when AI consolidation is disabled. Replaces previous similar memories with new ones based on this threshold. 0 = replace even if not similar at all, 1 = replace only if exact match.",
            "type": "range",
            "min": 0,
            "max": 1,
            "step": 0.01,
            "value": settings["memory_memorize_replace_threshold"],
        }
    )

    memory_section: SettingsSection = {
        "id": "memory",
        "title": "Memory",
        "description": "Configuration of A0's memory system. A0 memorizes and recalls memories automatically to help it's context awareness.",
        "fields": memory_fields,
        "tab": "agent",
    }

    prompt_enhance_fields: list[SettingsField] = []
    prompt_enhance_fields.append(
        {
            "id": "prompt_enhance_enabled",
            "title": "Prompt enhancement enabled",
            "description": "Use the utility model to rewrite user requests into clearer instructions.",
            "type": "switch",
            "value": settings["prompt_enhance_enabled"],
        }
    )
    prompt_enhance_fields.append(
        {
            "id": "prompt_enhance_max_chars",
            "title": "Prompt enhancement max chars",
            "description": "Maximum characters from the user message sent for enhancement. 0 disables trimming.",
            "type": "number",
            "value": settings["prompt_enhance_max_chars"],
        }
    )
    prompt_enhance_fields.append(
        {
            "id": "prompt_enhance_view",
            "title": "Prompt enhancement audit",
            "description": "View the latest enhanced prompt details.",
            "type": "button",
            "value": "View Details",
        }
    )
    prompt_enhance_section: SettingsSection = {
        "id": "prompt_enhancement",
        "title": "Prompt Enhancement",
        "description": "Improve prompt clarity before the main model responds.",
        "fields": prompt_enhance_fields,
        "tab": "agent",
    }

    # LLM Router settings section
    llm_router_fields: list[SettingsField] = []
    llm_router_fields.append(
        {
            "id": "llm_router_enabled",
            "title": "LLM Router enabled",
            "description": "Enable intelligent model routing for optimal model selection based on task type and priority.",
            "type": "switch",
            "value": settings["llm_router_enabled"],
        }
    )
    llm_router_fields.append(
        {
            "id": "llm_router_auto_configure",
            "title": "Auto-configure models",
            "description": "Automatically discover and configure available models from all providers on startup.",
            "type": "switch",
            "value": settings["llm_router_auto_configure"],
        }
    )
    llm_router_fields.append(
        {
            "id": "llm_router_discover",
            "title": "Discover models",
            "description": "Scan all providers for available models and update the router registry.",
            "type": "button",
            "value": "Discover Now",
        }
    )
    llm_router_fields.append(
        {
            "id": "llm_router_dashboard",
            "title": "Router dashboard",
            "description": "View models, defaults, and usage statistics.",
            "type": "button",
            "value": "Open Dashboard",
        }
    )
    llm_router_section: SettingsSection = {
        "id": "llm_router",
        "title": "LLM Router",
        "description": "Intelligent model routing and auto-configuration for optimal performance and cost.",
        "fields": llm_router_fields,
        "tab": "agent",
    }

    dev_fields: list[SettingsField] = []

    dev_fields.append(
        {
            "id": "shell_interface",
            "title": "Shell Interface",
            "description": "Terminal interface used for Code Execution Tool. Local Python TTY works locally in both dockerized and development environments. SSH always connects to dockerized environment (automatically at localhost or RFC host address).",
            "type": "select",
            "value": settings["shell_interface"],
            "options": [{"value": "local", "label": "Local Python TTY"}, {"value": "ssh", "label": "SSH"}],
        }
    )

    if runtime.is_development():
        # dev_fields.append(
        #     {
        #         "id": "rfc_auto_docker",
        #         "title": "RFC Auto Docker Management",
        #         "description": "Automatically create dockerized instance of A0 for RFCs using this instance's code base and, settings and .env.",
        #         "type": "text",
        #         "value": settings["rfc_auto_docker"],
        #     }
        # )

        dev_fields.append(
            {
                "id": "rfc_url",
                "title": "RFC Destination URL",
                "description": "URL of dockerized A0 instance for remote function calls. Do not specify port here.",
                "type": "text",
                "value": settings["rfc_url"],
            }
        )

    dev_fields.append(
        {
            "id": "rfc_password",
            "title": "RFC Password",
            "description": "Password for remote function calls. Passwords must match on both instances. RFCs can not be used with empty password.",
            "type": "password",
            "value": (PASSWORD_PLACEHOLDER if dotenv.get_dotenv_value(dotenv.KEY_RFC_PASSWORD) else ""),
        }
    )

    if runtime.is_development():
        dev_fields.append(
            {
                "id": "rfc_port_http",
                "title": "RFC HTTP port",
                "description": "HTTP port for dockerized instance of A0.",
                "type": "text",
                "value": settings["rfc_port_http"],
            }
        )

        dev_fields.append(
            {
                "id": "rfc_port_ssh",
                "title": "RFC SSH port",
                "description": "SSH port for dockerized instance of A0.",
                "type": "text",
                "value": settings["rfc_port_ssh"],
            }
        )

    dev_section: SettingsSection = {
        "id": "dev",
        "title": "Development",
        "description": "Parameters for A0 framework development. RFCs (remote function calls) are used to call functions on another A0 instance. You can develop and debug A0 natively on your local system while redirecting some functions to A0 instance in docker. This is crucial for development as A0 needs to run in standardized environment to support all features.",
        "fields": dev_fields,
        "tab": "developer",
    }

    # code_exec_fields: list[SettingsField] = []

    # code_exec_fields.append(
    #     {
    #         "id": "code_exec_ssh_enabled",
    #         "title": "Use SSH for code execution",
    #         "description": "Code execution will use SSH to connect to the terminal. When disabled, a local python terminal interface is used instead. SSH should only be used in development environment or when encountering issues with the local python terminal interface.",
    #         "type": "switch",
    #         "value": settings["code_exec_ssh_enabled"],
    #     }
    # )

    # code_exec_fields.append(
    #     {
    #         "id": "code_exec_ssh_addr",
    #         "title": "Code execution SSH address",
    #         "description": "Address of the SSH server for code execution. Only applies when SSH is enabled.",
    #         "type": "text",
    #         "value": settings["code_exec_ssh_addr"],
    #     }
    # )

    # code_exec_fields.append(
    #     {
    #         "id": "code_exec_ssh_port",
    #         "title": "Code execution SSH port",
    #         "description": "Port of the SSH server for code execution. Only applies when SSH is enabled.",
    #         "type": "text",
    #         "value": settings["code_exec_ssh_port"],
    #     }
    # )

    # code_exec_section: SettingsSection = {
    #     "id": "code_exec",
    #     "title": "Code execution",
    #     "description": "Configuration of code execution by the agent.",
    #     "fields": code_exec_fields,
    #     "tab": "developer",
    # }

    # Speech to text section
    stt_fields: list[SettingsField] = []

    stt_fields.append(
        {
            "id": "stt_microphone_section",
            "title": "Microphone device",
            "description": "Select the microphone device to use for speech-to-text.",
            "value": "<x-component path='/settings/speech/microphone.html' />",
            "type": "html",
        }
    )

    stt_fields.append(
        {
            "id": "stt_model_size",
            "title": "Speech-to-text model size",
            "description": "Select the speech-to-text model size",
            "type": "select",
            "value": settings["stt_model_size"],
            "options": [
                {"value": "tiny", "label": "Tiny (39M, English)"},
                {"value": "base", "label": "Base (74M, English)"},
                {"value": "small", "label": "Small (244M, English)"},
                {"value": "medium", "label": "Medium (769M, English)"},
                {"value": "large", "label": "Large (1.5B, Multilingual)"},
                {"value": "turbo", "label": "Turbo (Multilingual)"},
            ],
        }
    )

    stt_fields.append(
        {
            "id": "stt_language",
            "title": "Speech-to-text language code",
            "description": "Language code (e.g. en, fr, it)",
            "type": "text",
            "value": settings["stt_language"],
        }
    )

    stt_fields.append(
        {
            "id": "stt_silence_threshold",
            "title": "Microphone silence threshold",
            "description": "Silence detection threshold. Lower values are more sensitive to noise.",
            "type": "range",
            "min": 0,
            "max": 1,
            "step": 0.01,
            "value": settings["stt_silence_threshold"],
        }
    )

    stt_fields.append(
        {
            "id": "stt_silence_duration",
            "title": "Microphone silence duration (ms)",
            "description": "Duration of silence before the system considers speaking to have ended.",
            "type": "text",
            "value": settings["stt_silence_duration"],
        }
    )

    stt_fields.append(
        {
            "id": "stt_waiting_timeout",
            "title": "Microphone waiting timeout (ms)",
            "description": "Duration of silence before the system closes the microphone.",
            "type": "text",
            "value": settings["stt_waiting_timeout"],
        }
    )

    # TTS fields
    tts_fields: list[SettingsField] = []

    tts_fields.append(
        {
            "id": "tts_kokoro",
            "title": "Enable Kokoro TTS",
            "description": "Enable higher quality server-side AI (Kokoro) instead of browser-based text-to-speech.",
            "type": "switch",
            "value": settings["tts_kokoro"],
        }
    )

    speech_section: SettingsSection = {
        "id": "speech",
        "title": "Speech",
        "description": "Voice transcription and speech synthesis settings.",
        "fields": stt_fields + tts_fields,
        "tab": "agent",
    }

    # MCP section
    mcp_client_fields: list[SettingsField] = []

    mcp_client_fields.append(
        {
            "id": "mcp_servers_config",
            "title": "MCP Servers Configuration",
            "description": "External MCP servers can be configured here.",
            "type": "button",
            "value": "Open",
        }
    )

    mcp_client_fields.append(
        {
            "id": "mcp_servers",
            "title": "MCP Servers",
            "description": "(JSON list of) >> RemoteServer <<: [name, url, headers, timeout (opt), sse_read_timeout (opt), disabled (opt)] / >> Local Server <<: [name, command, args, env, encoding (opt), encoding_error_handler (opt), disabled (opt)]",
            "type": "textarea",
            "value": settings["mcp_servers"],
            "hidden": True,
        }
    )

    mcp_client_fields.append(
        {
            "id": "mcp_client_init_timeout",
            "title": "MCP Client Init Timeout",
            "description": "Timeout for MCP client initialization (in seconds). Higher values might be required for complex MCPs, but might also slowdown system startup.",
            "type": "number",
            "value": settings["mcp_client_init_timeout"],
        }
    )

    mcp_client_fields.append(
        {
            "id": "mcp_client_tool_timeout",
            "title": "MCP Client Tool Timeout",
            "description": "Timeout for MCP client tool execution. Higher values might be required for complex tools, but might also result in long responses with failing tools.",
            "type": "number",
            "value": settings["mcp_client_tool_timeout"],
        }
    )

    mcp_client_section: SettingsSection = {
        "id": "mcp_client",
        "title": "External MCP Servers",
        "description": "Agent Zero can use external MCP servers, local or remote as tools.",
        "fields": mcp_client_fields,
        "tab": "mcp",
    }

    # Secrets section
    secrets_fields: list[SettingsField] = []

    secrets_manager = get_default_secrets_manager()
    try:
        secrets = secrets_manager.get_masked_secrets()
    except Exception:
        secrets = ""

    secrets_fields.append(
        {
            "id": "variables",
            "title": "Variables Store",
            "description": 'Store non-sensitive variables in .env format e.g. EMAIL_IMAP_SERVER="imap.gmail.com", one item per line. You can use comments starting with # to add descriptions for the agent. See <a href="javascript:openModal(\'settings/secrets/example-vars.html\')">example</a>.<br>These variables are visible to LLMs and in chat history, they are not being masked.',
            "type": "textarea",
            "value": settings["variables"].strip(),
            "style": "height: 20em",
        }
    )

    secrets_fields.append(
        {
            "id": "secrets",
            "title": "Secrets Store",
            "description": 'Store secrets and credentials in .env format e.g. EMAIL_PASSWORD="s3cret-p4$$w0rd", one item per line. You can use comments starting with # to add descriptions for the agent. See <a href="javascript:openModal(\'settings/secrets/example-secrets.html\')">example</a>.<br>These variables are not visile to LLMs and in chat history, they are being masked. ⚠️ only values with length >= 4 are being masked to prevent false positives. ',
            "type": "textarea",
            "value": secrets,
            "style": "height: 20em",
        }
    )

    secrets_section: SettingsSection = {
        "id": "secrets",
        "title": "Secrets Management",
        "description": "Manage secrets and credentials that agents can use without exposing values to LLMs, chat history or logs. Placeholders are automatically replaced with values just before tool calls. If bare passwords occur in tool results, they are masked back to placeholders.",
        "fields": secrets_fields,
        "tab": "external",
    }

    mcp_server_fields: list[SettingsField] = []

    mcp_server_fields.append(
        {
            "id": "mcp_server_enabled",
            "title": "Enable A0 MCP Server",
            "description": "Expose Agent Zero as an SSE/HTTP MCP server. This will make this A0 instance available to MCP clients.",
            "type": "switch",
            "value": settings["mcp_server_enabled"],
        }
    )

    mcp_server_fields.append(
        {
            "id": "mcp_server_token",
            "title": "MCP Server Token",
            "description": "Token for MCP server authentication.",
            "type": "text",
            "hidden": True,
            "value": settings["mcp_server_token"],
        }
    )

    mcp_server_section: SettingsSection = {
        "id": "mcp_server",
        "title": "A0 MCP Server",
        "description": "Agent Zero can be exposed as an SSE MCP server. See <a href=\"javascript:openModal('settings/mcp/server/example.html')\">connection example</a>.",
        "fields": mcp_server_fields,
        "tab": "mcp",
    }

    # -------- A2A Section --------
    a2a_fields: list[SettingsField] = []

    a2a_fields.append(
        {
            "id": "a2a_server_enabled",
            "title": "Enable A2A server",
            "description": "Expose Agent Zero as A2A server. This allows other agents to connect to A0 via A2A protocol.",
            "type": "switch",
            "value": settings["a2a_server_enabled"],
        }
    )

    a2a_section: SettingsSection = {
        "id": "a2a_server",
        "title": "A0 A2A Server",
        "description": "Agent Zero can be exposed as an A2A server. See <a href=\"javascript:openModal('settings/a2a/a2a-connection.html')\">connection example</a>.",
        "fields": a2a_fields,
        "tab": "mcp",
    }

    # Gmail Accounts section
    gmail_accounts_fields: list[SettingsField] = []

    # Get current Gmail accounts status
    gmail_accounts = settings.get("gmail_accounts", {})
    account_count = len(gmail_accounts)

    # Build account list HTML
    account_list_html = "<div style='padding: 10px; background: #f5f5f5; border-radius: 4px;'>"
    account_list_html += f"<div><strong>Configured accounts: {account_count}</strong></div>"

    if account_count > 0:
        account_list_html += (
            "<div style='margin-top: 10px; font-size: 0.9em;'><ul style='margin: 5px 0; padding-left: 20px;'>"
        )
        for account_name, account_info in gmail_accounts.items():
            email = account_info.get("email", "Unknown")
            authenticated = account_info.get("authenticated", False)
            status_icon = "✅" if authenticated else "❌"
            account_list_html += f"<li><strong>{account_name}</strong>: {email} {status_icon}</li>"
        account_list_html += "</ul></div>"

    account_list_html += "</div>"

    gmail_accounts_fields.append(
        {
            "id": "gmail_accounts_info",
            "title": "Gmail Accounts",
            "description": f"Currently configured accounts: {account_count}. Click 'Manage Accounts' to add or remove Gmail accounts.",
            "type": "html",
            "value": account_list_html,
        }
    )

    gmail_accounts_fields.append(
        {
            "id": "gmail_manage_accounts",
            "title": "Manage Accounts",
            "description": "Open the Gmail account manager to add, remove, or re-authenticate accounts.",
            "type": "button",
            "value": "Manage Accounts",
        }
    )

    gmail_accounts_fields.append(
        {
            "id": "gmail_test_utility",
            "title": "Test & Setup Utility",
            "description": "Guide through OAuth setup, account validation, and sending a test email.",
            "type": "button",
            "value": "Open Test Utility",
        }
    )

    gmail_accounts_fields.append(
        {
            "id": "gmail_setup_guide",
            "title": "Setup Guide",
            "description": "View instructions for setting up Gmail API credentials and OAuth2 authentication.",
            "type": "button",
            "value": "View Setup Guide",
        }
    )

    gmail_accounts_section: SettingsSection = {
        "id": "gmail_accounts",
        "title": "Gmail Accounts",
        "description": "Manage Gmail accounts for automated email operations. Each account requires OAuth2 authentication through Google Cloud Console.",
        "fields": gmail_accounts_fields,
        "tab": "external",
    }

    google_voice_fields: list[SettingsField] = []
    google_voice_fields.append(
        {
            "id": "google_voice_manager",
            "title": "Google Voice SMS",
            "description": "Queue and approve Google Voice SMS drafts using a visible browser session.",
            "type": "html",
            "value": "<x-component path='/settings/external/google-voice-manager.html' />",
        }
    )
    google_voice_fields.append(
        {
            "id": "google_voice_auto_send",
            "title": "Auto-send approved drafts",
            "description": "When enabled, drafts will send immediately without manual approval.",
            "type": "switch",
            "value": settings.get("google_voice_auto_send", False),
            "hidden": True,
        }
    )
    google_voice_fields.append(
        {
            "id": "google_voice_shortcuts",
            "title": "Enable shortcuts",
            "description": "Enable keyboard shortcuts in Google Voice manager.",
            "type": "switch",
            "value": settings.get("google_voice_shortcuts", True),
            "hidden": True,
        }
    )
    google_voice_fields.append(
        {
            "id": "google_voice_contact_rules",
            "title": "Google Voice contact rules",
            "description": "Internal per-contact auto-send rules.",
            "type": "textarea",
            "value": settings.get("google_voice_contact_rules", "{}"),
            "hidden": True,
        }
    )
    google_voice_fields.append(
        {
            "id": "google_voice_tag_filters",
            "title": "Google Voice tag filters",
            "description": "Saved inbound tag filters.",
            "type": "textarea",
            "value": settings.get("google_voice_tag_filters", "[]"),
            "hidden": True,
        }
    )

    google_voice_section: SettingsSection = {
        "id": "google_voice",
        "title": "Google Voice",
        "description": "Manage Google Voice SMS automation and approvals.",
        "fields": google_voice_fields,
        "tab": "external",
    }

    twilio_fields: list[SettingsField] = []
    twilio_fields.append(
        {
            "id": "twilio_manager",
            "title": "Twilio Voice",
            "description": "Configure Twilio voice credentials and place outbound calls.",
            "type": "html",
            "value": "<x-component path='/settings/external/twilio-voice-manager.html' />",
        }
    )
    twilio_fields.extend(
        [
            {
                "id": "twilio_account_sid",
                "title": "Twilio Account SID",
                "type": "text",
                "value": settings.get("twilio_account_sid", ""),
                "hidden": True,
            },
            {
                "id": "twilio_auth_token",
                "title": "Twilio Auth Token",
                "type": "password",
                "value": PASSWORD_PLACEHOLDER if settings.get("twilio_auth_token") else "",
                "hidden": True,
            },
            {
                "id": "twilio_from_number",
                "title": "Twilio From Number",
                "type": "text",
                "value": settings.get("twilio_from_number", ""),
                "hidden": True,
            },
        ]
    )

    twilio_section: SettingsSection = {
        "id": "twilio_voice",
        "title": "Twilio Voice",
        "description": "Manage Twilio outbound voice calls.",
        "fields": twilio_fields,
        "tab": "external",
    }

    # External API section
    external_api_fields: list[SettingsField] = []

    external_api_fields.append(
        {
            "id": "external_api_examples",
            "title": "API Examples",
            "description": "View examples for using Agent Zero's external API endpoints with API key authentication.",
            "type": "button",
            "value": "Show API Examples",
        }
    )

    external_api_section: SettingsSection = {
        "id": "external_api",
        "title": "External API",
        "description": "Agent Zero provides external API endpoints for integration with other applications. "
        "These endpoints use API key authentication and support text messages and file attachments.",
        "fields": external_api_fields,
        "tab": "external",
    }

    # update checker section
    update_checker_fields: list[SettingsField] = []

    update_checker_fields.append(
        {
            "id": "update_check_enabled",
            "title": "Enable Update Checker",
            "description": "Enable update checker to notify about newer versions of Agent Zero.",
            "type": "switch",
            "value": settings["update_check_enabled"],
        }
    )

    update_checker_section: SettingsSection = {
        "id": "update_checker",
        "title": "Update Checker",
        "description": "Update checker periodically checks for new releases of Agent Zero and will notify when an update is recommended.<br>No personal data is sent to the update server, only randomized+anonymized unique ID and current version number, which help us evaluate the importance of the update in case of critical bug fixes etc.",
        "fields": update_checker_fields,
        "tab": "external",
    }

    # Backup & Restore section
    backup_fields: list[SettingsField] = []

    backup_fields.append(
        {
            "id": "backup_create",
            "title": "Create Backup",
            "description": "Create a backup archive of selected files and configurations "
            "using customizable patterns.",
            "type": "button",
            "value": "Create Backup",
        }
    )

    backup_fields.append(
        {
            "id": "backup_restore",
            "title": "Restore from Backup",
            "description": "Restore files and configurations from a backup archive " "with pattern-based selection.",
            "type": "button",
            "value": "Restore Backup",
        }
    )

    backup_section: SettingsSection = {
        "id": "backup_restore",
        "title": "Backup & Restore",
        "description": "Backup and restore Agent Zero data and configurations "
        "using glob pattern-based file selection.",
        "fields": backup_fields,
        "tab": "backup",
    }

    observability_fields: list[SettingsField] = []

    observability_fields.append(
        {
            "id": "telemetry_enabled",
            "title": "Enable telemetry",
            "description": "Collect tool execution telemetry for observability and evaluation.",
            "type": "switch",
            "value": settings["telemetry_enabled"],
        }
    )

    observability_fields.append(
        {
            "id": "telemetry_max_events",
            "title": "Max telemetry events",
            "description": "Number of recent telemetry events stored per thread.",
            "type": "number",
            "value": settings["telemetry_max_events"],
        }
    )

    observability_fields.append(
        {
            "id": "observability_provider",
            "title": "External observability provider",
            "description": "Select external provider(s) to receive telemetry events.",
            "type": "select",
            "value": settings.get("observability_provider", "local"),
            "options": [
                {"value": "local", "label": "Local only"},
                {"value": "langsmith", "label": "LangSmith"},
                {"value": "langfuse", "label": "Langfuse"},
                {"value": "langsmith+langfuse", "label": "LangSmith + Langfuse"},
            ],
        }
    )

    observability_fields.append(
        {
            "id": "observability_auto_store",
            "title": "Auto-store workflow runs",
            "description": "Automatically capture workflow runs from tool activity.",
            "type": "switch",
            "value": settings.get("observability_auto_store", True),
        }
    )

    langsmith_api_key = dotenv.get_dotenv_value("LANGSMITH_API_KEY", "")
    langsmith_project = dotenv.get_dotenv_value("LANGSMITH_PROJECT", settings.get("langsmith_project", ""))
    langsmith_endpoint = dotenv.get_dotenv_value("LANGSMITH_ENDPOINT", settings.get("langsmith_endpoint", ""))
    langfuse_public_key = dotenv.get_dotenv_value("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key = dotenv.get_dotenv_value("LANGFUSE_SECRET_KEY", "")
    langfuse_host = dotenv.get_dotenv_value("LANGFUSE_HOST", settings.get("langfuse_host", ""))

    observability_fields.append(
        {
            "id": "langsmith_project",
            "title": "LangSmith project",
            "description": "Project name used for LangSmith traces.",
            "type": "text",
            "value": langsmith_project,
        }
    )

    observability_fields.append(
        {
            "id": "langsmith_endpoint",
            "title": "LangSmith endpoint",
            "description": "Custom LangSmith API endpoint (optional).",
            "type": "text",
            "value": langsmith_endpoint,
        }
    )

    observability_fields.append(
        {
            "id": "langsmith_api_key",
            "title": "LangSmith API key",
            "description": "API key for LangSmith.",
            "type": "password",
            "value": PASSWORD_PLACEHOLDER if langsmith_api_key else "",
        }
    )

    observability_fields.append(
        {
            "id": "langfuse_host",
            "title": "Langfuse host",
            "description": "Langfuse host URL.",
            "type": "text",
            "value": langfuse_host,
        }
    )

    observability_fields.append(
        {
            "id": "langfuse_public_key",
            "title": "Langfuse public key",
            "description": "Public key for Langfuse.",
            "type": "password",
            "value": PASSWORD_PLACEHOLDER if langfuse_public_key else "",
        }
    )

    observability_fields.append(
        {
            "id": "langfuse_secret_key",
            "title": "Langfuse secret key",
            "description": "Secret key for Langfuse.",
            "type": "password",
            "value": PASSWORD_PLACEHOLDER if langfuse_secret_key else "",
        }
    )

    observability_fields.append(
        {
            "id": "observability_open",
            "title": "Observability dashboard",
            "description": "Inspect tool telemetry events and stats for the current thread.",
            "type": "button",
            "value": "Open Observability",
        }
    )

    observability_section: SettingsSection = {
        "id": "observability",
        "title": "Observability",
        "description": "Telemetry and evaluation settings.",
        "fields": observability_fields,
        "tab": "developer",
    }

    # Add the section to the result
    result: SettingsOutput = {
        "sections": [
            agent_section,
            cowork_section,
            chat_model_section,
            util_model_section,
            browser_model_section,
            embed_model_section,
            memory_section,
            prompt_enhance_section,
            llm_router_section,
            speech_section,
            api_keys_section,
            litellm_section,
            secrets_section,
            auth_section,
            passkey_section,
            mcp_client_section,
            mcp_server_section,
            a2a_section,
            gmail_accounts_section,
            google_voice_section,
            twilio_section,
            external_api_section,
            update_checker_section,
            backup_section,
            dev_section,
            observability_section,
            # code_exec_section,
        ]
    }
    return result
