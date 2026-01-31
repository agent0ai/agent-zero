import uuid
from datetime import datetime
from typing import Any

from python.helpers import settings
from python.helpers.settings import ModelGroupConfig


# Fields needed in model group config
MODEL_GROUP_FIELDS = [
    "chat_model_provider", "chat_model_name", "chat_model_api_base",
    "util_model_provider", "util_model_name", "util_model_api_base",
    "browser_model_provider", "browser_model_name", "browser_model_api_base",
    "embed_model_provider", "embed_model_name", "embed_model_api_base",
]


def create_model_group_from_current() -> ModelGroupConfig:
    """Create model group config from current settings"""
    current = settings.get_settings()
    return ModelGroupConfig(
        id=str(uuid.uuid4()),
        name="",
        description="",
        created_at=datetime.now().isoformat(),
        chat_model_provider=current["chat_model_provider"],
        chat_model_name=current["chat_model_name"],
        chat_model_api_base=current["chat_model_api_base"],
        util_model_provider=current["util_model_provider"],
        util_model_name=current["util_model_name"],
        util_model_api_base=current["util_model_api_base"],
        browser_model_provider=current["browser_model_provider"],
        browser_model_name=current["browser_model_name"],
        browser_model_api_base=current["browser_model_api_base"],
        embed_model_provider=current["embed_model_provider"],
        embed_model_name=current["embed_model_name"],
        embed_model_api_base=current["embed_model_api_base"],
    )


def apply_model_group_to_settings(group: ModelGroupConfig) -> None:
    """Apply model group config to current settings"""
    current = settings.get_settings()
    for field in MODEL_GROUP_FIELDS:
        if field in group:
            current[field] = group[field]
    current["active_model_group_id"] = group["id"]
    settings.set_settings(current)