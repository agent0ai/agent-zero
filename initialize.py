import os

import models
from agent import AgentConfig
from python.helpers import defer, runtime, settings, startup_selector
from python.helpers.print_style import PrintStyle

_llm_router_bootstrap_started = False


def _is_laptop_mode() -> bool:
    return os.getenv("AGENT_ZERO_LAPTOP_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


def _apply_laptop_runtime_overrides(current_settings: settings.Settings) -> settings.Settings:
    if not _is_laptop_mode():
        return current_settings

    updated = dict(current_settings)
    updated.update(
        {
            "deployment_tier": "free",
            "perf_slo_profile": "free",
            "enable_persona_systems": False,
            "max_concurrent_sessions": min(int(updated.get("max_concurrent_sessions", 25)), 2),
            "llm_router_enabled": False,
            "llm_router_auto_configure": False,
            "llm_local_only_mode": True,
            "llm_cloud_fallback_enabled": False,
            "memory_recall_enabled": False,
            "memory_memorize_enabled": False,
            "update_check_enabled": False,
            "telemetry_enabled": False,
            "mcp_server_enabled": False,
            "a2a_server_enabled": False,
        }
    )
    return updated


def initialize_agent(override_settings: dict | None = None):
    current_settings = settings.get_settings()
    if override_settings:
        current_settings = settings.merge_settings(current_settings, override_settings)
    current_settings = _apply_laptop_runtime_overrides(current_settings)
    current_settings = startup_selector.apply_startup_selection(current_settings)

    def _normalize_model_kwargs(kwargs: dict) -> dict:
        # convert string values that represent valid Python numbers to numeric types
        result = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                # try to convert string to number if it's a valid Python number
                try:
                    # try int first, then float
                    result[key] = int(value)
                except ValueError:
                    try:
                        result[key] = float(value)
                    except ValueError:
                        result[key] = value
            else:
                result[key] = value
        return result

    # chat model from user settings
    chat_llm = models.ModelConfig(
        type=models.ModelType.CHAT,
        provider=current_settings["chat_model_provider"],
        name=current_settings["chat_model_name"],
        api_base=current_settings["chat_model_api_base"],
        ctx_length=current_settings["chat_model_ctx_length"],
        vision=current_settings["chat_model_vision"],
        limit_requests=current_settings["chat_model_rl_requests"],
        limit_input=current_settings["chat_model_rl_input"],
        limit_output=current_settings["chat_model_rl_output"],
        kwargs=_normalize_model_kwargs(current_settings["chat_model_kwargs"]),
    )

    # utility model from user settings
    utility_llm = models.ModelConfig(
        type=models.ModelType.CHAT,
        provider=current_settings["util_model_provider"],
        name=current_settings["util_model_name"],
        api_base=current_settings["util_model_api_base"],
        ctx_length=current_settings["util_model_ctx_length"],
        limit_requests=current_settings["util_model_rl_requests"],
        limit_input=current_settings["util_model_rl_input"],
        limit_output=current_settings["util_model_rl_output"],
        kwargs=_normalize_model_kwargs(current_settings["util_model_kwargs"]),
    )
    # embedding model from user settings
    embedding_llm = models.ModelConfig(
        type=models.ModelType.EMBEDDING,
        provider=current_settings["embed_model_provider"],
        name=current_settings["embed_model_name"],
        api_base=current_settings["embed_model_api_base"],
        limit_requests=current_settings["embed_model_rl_requests"],
        kwargs=_normalize_model_kwargs(current_settings["embed_model_kwargs"]),
    )
    # browser model from user settings
    browser_llm = models.ModelConfig(
        type=models.ModelType.CHAT,
        provider=current_settings["browser_model_provider"],
        name=current_settings["browser_model_name"],
        api_base=current_settings["browser_model_api_base"],
        vision=current_settings["browser_model_vision"],
        kwargs=_normalize_model_kwargs(current_settings["browser_model_kwargs"]),
    )
    # agent configuration
    config = AgentConfig(
        chat_model=chat_llm,
        utility_model=utility_llm,
        embeddings_model=embedding_llm,
        browser_model=browser_llm,
        profile=current_settings["agent_profile"],
        memory_subdir=current_settings["agent_memory_subdir"],
        knowledge_subdirs=[current_settings["agent_knowledge_subdir"], "default"],
        mcp_servers=current_settings["mcp_servers"],
        browser_http_headers=current_settings["browser_http_headers"],
        # code_exec params get initialized in _set_runtime_config
        # additional = {},
    )

    # update SSH and docker settings
    _set_runtime_config(config, current_settings)

    # update config with runtime args
    _args_override(config)

    # Initialize local-first LLM router once per process (non-blocking)
    _initialize_llm_router_once(current_settings)

    # Initialize Security Vault & Passkey/VAPID keys
    try:
        from python.helpers.security import SecurityVaultManager

        SecurityVaultManager.initialize_keys()
    except Exception as e:
        PrintStyle(font_color="red").print(f"Failed to initialize security vault: {e}")

    # Initialize MOS schedules (Linear/Motion/Notion sync cron jobs)
    try:
        from python.helpers.mos_scheduler_init import register_mos_schedules

        result = register_mos_schedules()
        if result["count"] > 0:
            PrintStyle(font_color="green").print(f"MOS schedules registered: {', '.join(result['registered'])}")
    except Exception as e:
        PrintStyle(font_color="yellow").print(f"[!] MOS schedule init skipped: {e}")

    # initialize MCP in deferred task to prevent blocking the main thread
    # async def initialize_mcp_async(mcp_servers_config: str):
    #     return initialize_mcp(mcp_servers_config)
    # defer.DeferredTask(thread_name="mcp-initializer").start_task(initialize_mcp_async, config.mcp_servers)
    # initialize_mcp(config.mcp_servers)

    # import python.helpers.mcp_handler as mcp_helper
    # import agent as agent_helper
    # import python.helpers.print_style as print_style_helper
    # if not mcp_helper.MCPConfig.get_instance().is_initialized():
    #     try:
    #         mcp_helper.MCPConfig.update(config.mcp_servers)
    #     except Exception as e:
    #         first_context = agent_helper.AgentContext.first()
    #         if first_context:
    #             (
    #                 first_context.log
    #                 .log(type="warning", content=f"Failed to update MCP settings: {e}", temp=False)
    #             )
    #         (
    #             print_style_helper.PrintStyle(background_color="black", font_color="red", padding=True)
    #             .print(f"Failed to update MCP settings: {e}")
    #         )

    # return config object
    return config


def _initialize_llm_router_once(current_settings: settings.Settings):
    global _llm_router_bootstrap_started
    if _llm_router_bootstrap_started:
        return

    if _is_laptop_mode() or not current_settings.get("llm_router_enabled", False):
        return

    if not current_settings.get("llm_router_auto_configure", False):
        return

    async def _bootstrap():
        from python.helpers.llm_router import auto_configure_models

        await auto_configure_models()

    _llm_router_bootstrap_started = True
    defer.DeferredTask(thread_name="llm-router-bootstrap").start_task(_bootstrap)


def initialize_chats():
    from python.helpers import persist_chat

    async def initialize_chats_async():
        persist_chat.load_tmp_chats()

    return defer.DeferredTask().start_task(initialize_chats_async)


def initialize_mcp():
    if _is_laptop_mode():
        PrintStyle(font_color="yellow").print("[!] MCP client init skipped (laptop mode)")
        return None

    set = settings.get_settings()

    async def initialize_mcp_async():
        from python.helpers.mcp_handler import initialize_mcp as _initialize_mcp

        return _initialize_mcp(set["mcp_servers"])

    return defer.DeferredTask().start_task(initialize_mcp_async)


def initialize_job_loop():
    if _is_laptop_mode():
        PrintStyle(font_color="yellow").print("[!] Job loop skipped (laptop mode)")
        return None

    try:
        from python.helpers.job_loop import run_loop

        return defer.DeferredTask("JobLoop").start_task(run_loop)
    except ImportError as e:
        # crontab module may not be installed - scheduler is optional
        PrintStyle(font_color="yellow").print(f"[!] Job loop disabled: {e}")
        return None


def initialize_preload():
    if _is_laptop_mode():
        PrintStyle(font_color="yellow").print("[!] Preload skipped (laptop mode)")
        return None

    try:
        import preload

        return defer.DeferredTask().start_task(preload.preload)
    except ImportError as e:
        # Optional dependencies like soundfile, kokoro_tts may not be installed
        PrintStyle(font_color="yellow").print(f"[!] Preload disabled: {e}")
        return None


def _args_override(config):
    # update config with runtime args
    for key, value in runtime.args.items():
        if hasattr(config, key):
            # conversion based on type of config[key]
            if isinstance(getattr(config, key), bool):
                value = value.lower().strip() == "true"
            elif isinstance(getattr(config, key), int):
                value = int(value)
            elif isinstance(getattr(config, key), float):
                value = float(value)
            elif isinstance(getattr(config, key), str):
                value = str(value)
            else:
                raise Exception(f"Unsupported argument type of '{key}': {type(getattr(config, key))}")

            setattr(config, key, value)


def _set_runtime_config(config: AgentConfig, set: settings.Settings):
    ssh_conf = settings.get_runtime_config(set)
    for key, value in ssh_conf.items():
        if hasattr(config, key):
            setattr(config, key, value)
