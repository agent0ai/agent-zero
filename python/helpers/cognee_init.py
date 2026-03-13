import os
from typing import Any, TypeVar

from . import dotenv, files
from .settings import get_settings

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
}

_PROVIDER_MAP: dict[str, str] = {
    "openrouter": "openrouter",
    "huggingface": "huggingface",
    "openai": "openai",
    "anthropic": "anthropic",
}

_EMBED_DIMENSIONS: dict[str, int] = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-large-en-v1.5": 1024,
}


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
    dotenv.load_dotenv()
    settings = get_settings()

    llm_provider = _map_provider(settings["util_model_provider"])
    embed_provider = _map_provider(settings["embed_model_provider"])

    api_keys = settings.get("api_keys", {})

    os.environ["LLM_PROVIDER"] = llm_provider
    os.environ["LLM_MODEL"] = settings["util_model_name"]
    os.environ["LLM_API_KEY"] = _get_api_key(settings["util_model_provider"], api_keys)

    if settings.get("util_model_api_base"):
        os.environ["LLM_API_BASE"] = settings["util_model_api_base"]

    embed_model = settings["embed_model_name"]
    if embed_provider == "huggingface":
        os.environ["EMBEDDING_PROVIDER"] = "fastembed"
        os.environ["EMBEDDING_MODEL"] = embed_model
        os.environ["EMBEDDING_DIMENSIONS"] = str(_EMBED_DIMENSIONS.get(embed_model, 384))
    else:
        os.environ["EMBEDDING_PROVIDER"] = embed_provider
        if "/" not in embed_model or not embed_model.startswith(embed_provider):
            embed_model = f"{embed_provider}/{embed_model}"
        os.environ["EMBEDDING_MODEL"] = embed_model
    os.environ["EMBEDDING_API_KEY"] = _get_api_key(settings["embed_model_provider"], api_keys)

    if settings.get("embed_model_api_base"):
        os.environ["EMBEDDING_API_BASE"] = settings["embed_model_api_base"]

    os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
    os.environ["CACHING"] = "true"
    os.environ["CACHE_ADAPTER"] = get_cognee_setting("cognee_session_cache", "filesystem")

    data_dir = files.get_abs_path(get_cognee_setting("cognee_data_dir", "usr/cognee"))
    os.makedirs(data_dir, exist_ok=True)
    os.environ["DATA_ROOT_DIRECTORY"] = os.path.join(data_dir, "data_storage")
    os.environ["SYSTEM_ROOT_DIRECTORY"] = os.path.join(data_dir, "cognee_system")
    os.environ["CACHE_ROOT_DIRECTORY"] = os.path.join(data_dir, "cognee_cache")
