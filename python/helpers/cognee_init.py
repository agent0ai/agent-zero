import os
from typing import Any, TypeVar

from . import dotenv, files
from .settings import get_settings
from .print_style import PrintStyle

T = TypeVar("T")

_COGNEE_DEFAULTS: dict[str, Any] = {
    "cognee_search_type": "GRAPH_COMPLETION",
    "cognee_search_types": "GRAPH_COMPLETION,CHUNKS_LEXICAL",
    "cognee_multi_search_enabled": True,
    "cognee_cognify_interval": 5,
    "cognee_cognify_after_n_inserts": 10,
    "cognee_temporal_enabled": True,
    "cognee_memify_enabled": True,
    "cognee_feedback_enabled": True,
    "cognee_session_cache": "filesystem",
    "cognee_data_dir": "usr/cognee",
    "cognee_chunk_size": 512,
    "cognee_chunk_overlap": 50,
    "cognee_search_system_prompt": "",
}

_PROVIDER_MAP: dict[str, str] = {
    "openrouter": "openrouter",
    "huggingface": "huggingface",
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "gemini",
    "ollama": "ollama",
    "lmstudio": "custom",
}

_EMBED_DIMENSIONS: dict[str, int] = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-large-en-v1.5": 1024,
    "nomic-embed-text:latest": 768,
}

_configured = False


def get_cognee_setting(name: str, default: T) -> T:
    env_key = f"A0_SET_{name}"
    env_value = dotenv.get_dotenv_value(env_key, dotenv.get_dotenv_value(env_key.upper(), None))
    if env_value is None:
        return _COGNEE_DEFAULTS.get(name, default)  # type: ignore
    try:
        if isinstance(default, bool):
            return env_value.strip().lower() in ("true", "1", "yes", "on")  # type: ignore
        elif isinstance(default, int):
            return type(default)(env_value.strip())  # type: ignore
        elif isinstance(default, str):
            return str(env_value).strip()  # type: ignore
        return default
    except (ValueError, TypeError):
        return _COGNEE_DEFAULTS.get(name, default)  # type: ignore


def _map_provider(a0_provider: str) -> str:
    return _PROVIDER_MAP.get(a0_provider.lower(), a0_provider)


def _get_api_key(provider: str, api_keys: dict[str, str] | None = None) -> str:
    dotenv.load_dotenv()
    key = dotenv.get_dotenv_value(f"API_KEY_{provider.upper()}")
    if key:
        return key
    if api_keys is not None:
        return api_keys.get(provider, "") or ""
    return get_settings().get("api_keys", {}).get(provider, "") or ""


def configure_cognee() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    dotenv.load_dotenv()
    settings = get_settings()

    # --- Storage directories (MUST be set BEFORE import cognee) ---
    data_dir = files.get_abs_path(get_cognee_setting("cognee_data_dir", "usr/cognee"))
    os.makedirs(data_dir, exist_ok=True)

    data_storage = os.path.join(data_dir, "data_storage")
    system_storage = os.path.join(data_dir, "cognee_system")
    cache_storage = os.path.join(data_dir, "cognee_cache")

    os.makedirs(data_storage, exist_ok=True)
    os.makedirs(system_storage, exist_ok=True)
    os.makedirs(cache_storage, exist_ok=True)

    os.environ["DATA_ROOT_DIRECTORY"] = data_storage
    os.environ["SYSTEM_ROOT_DIRECTORY"] = system_storage
    os.environ["CACHE_ROOT_DIRECTORY"] = cache_storage
    os.environ["DB_PROVIDER"] = "sqlite"
    os.environ["DB_NAME"] = "cognee_db"
    os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
    os.environ["CACHING"] = "true"
    os.environ["CACHE_ADAPTER"] = get_cognee_setting("cognee_session_cache", "filesystem")

    PrintStyle.standard(f"Cognee env configured: system={system_storage}, data={data_storage}")

    # --- Now safe to import cognee (env vars are set) ---
    try:
        import cognee
    except ImportError:
        PrintStyle.error("Cognee is not installed — memory features will not work")
        return

    api_keys = settings.get("api_keys", {})

    # --- LLM (from Agent Zero util_model_* settings) ---
    llm_provider = _map_provider(settings["util_model_provider"])
    llm_api_key = _get_api_key(settings["util_model_provider"], api_keys)

    try:
        cognee.config.set_llm_config({
            "llm_provider": llm_provider,
            "llm_model": settings["util_model_name"],
            "llm_api_key": llm_api_key,
        })
        if settings.get("util_model_api_base"):
            cognee.config.set_llm_endpoint(settings["util_model_api_base"])
    except Exception as e:
        PrintStyle.error(f"cognee.config LLM setup failed, falling back to env vars: {e}")
        os.environ["LLM_PROVIDER"] = llm_provider
        os.environ["LLM_MODEL"] = settings["util_model_name"]
        os.environ["LLM_API_KEY"] = llm_api_key
        if settings.get("util_model_api_base"):
            os.environ["LLM_API_BASE"] = settings["util_model_api_base"]

    # --- Embedding (from Agent Zero embed_model_* settings) ---
    embed_provider = _map_provider(settings["embed_model_provider"])
    embed_model = settings["embed_model_name"]
    embed_api_key = _get_api_key(settings["embed_model_provider"], api_keys)

    if embed_provider in ("huggingface", "fastembed"):
        os.environ["EMBEDDING_PROVIDER"] = "fastembed"
        os.environ["EMBEDDING_MODEL"] = embed_model
        os.environ["EMBEDDING_DIMENSIONS"] = str(_EMBED_DIMENSIONS.get(embed_model, 384))
    else:
        os.environ["EMBEDDING_PROVIDER"] = embed_provider
        if "/" not in embed_model or not embed_model.startswith(embed_provider):
            embed_model = f"{embed_provider}/{embed_model}"
        os.environ["EMBEDDING_MODEL"] = embed_model
    os.environ["EMBEDDING_API_KEY"] = embed_api_key
    if settings.get("embed_model_api_base"):
        os.environ["EMBEDDING_API_BASE"] = settings["embed_model_api_base"]

    # --- Chunking ---
    try:
        cognee.config.set_chunk_size(get_cognee_setting("cognee_chunk_size", 512))
        cognee.config.set_chunk_overlap(get_cognee_setting("cognee_chunk_overlap", 50))
    except Exception as e:
        PrintStyle.error(f"cognee.config chunk setup failed: {e}")

    # --- Apply directory config via cognee API ---
    try:
        cognee.config.set_data_root_directory(data_storage)
        cognee.config.set_system_root_directory(system_storage)
    except Exception as e:
        PrintStyle.error(f"cognee.config directory setup failed: {e}")
