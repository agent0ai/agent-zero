import copy
import yaml
from python.helpers import files


DEFAULT_CONFIG = {
    "backend": "faiss",
    "fallback_to_faiss": True,
    "mirror_to_faiss": False,
    "qdrant": {
        "url": "http://localhost:6333",
        "api_key": "",
        "collection": "agent-zero",
        "prefer_hybrid": True,
        "score_threshold": 0.6,
        "limit": 20,
        "timeout": 10,
        "searchable_payload_keys": [
            "area",
            "source",
            "project",
            "tags",
            "consolidation_action",
        ],
    },
}


_cache: dict | None = None


def get_memory_config() -> dict:
    """Load memory configuration from conf/memory.yaml with sane defaults."""
    global _cache
    if _cache is not None:
        return copy.deepcopy(_cache)

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    try:
        path = files.get_abs_path("conf/memory.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                cfg = _merge(cfg, data)
    except FileNotFoundError:
        # keep defaults
        pass
    except Exception:
        # if the file is malformed, stick to defaults to avoid breaking runtime
        pass

    _cache = cfg
    return copy.deepcopy(_cache)


def _merge(base: dict, override: dict) -> dict:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged
