# python/helpers/checkpoint.py
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid
import hashlib
import json


class AgentCheckpoint(BaseModel):
    """Complete checkpoint of an agent's state at a point in time"""
    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_id: str
    context_type: str  # USER, TASK, or BACKGROUND
    created_at: datetime
    checkpoint_type: str  # manual, auto, scheduled, pre_tool, post_tool
    agent_state: Dict[str, Any]  # Serialized agent hierarchy and history
    execution_state: Dict[str, Any]  # Current task state for scheduler integration
    structure_hash: str  # SHA256 hash for validation
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CheckpointMetadata(BaseModel):
    """Lightweight checkpoint metadata for listing without full deserialization"""
    checkpoint_id: str
    context_id: str
    created_at: datetime
    checkpoint_type: str
    message_count: int = 0
    tool_execution_count: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CheckpointConfig(BaseModel):
    """Configuration for checkpoint behavior"""
    auto_save: bool = True
    save_interval_messages: int = 10
    save_interval_tools: int = 5
    pre_tool_checkpoint: bool = False
    keep_last_n: int = 5
    storage_path: str = "tmp/checkpoints"
    storage_backend: str = "file"  # "file" or "memory"


def calculate_structure_hash(config: Any, tools: List[str], extensions: List[str]) -> str:
    """
    Calculate a SHA256 hash of the agent structure.

    This hash is used to validate that a checkpoint can be safely restored
    by checking if the agent configuration, tools, and extensions match.
    """
    # Extract model names from ModelConfig objects if present
    chat_model = getattr(config, "chat_model", "unknown")
    if hasattr(chat_model, "name"):
        chat_model = chat_model.name

    utility_model = getattr(config, "utility_model", "unknown")
    if hasattr(utility_model, "name"):
        utility_model = utility_model.name

    structure_data = {
        "chat_model": str(chat_model),
        "utility_model": str(utility_model),
        "profile": getattr(config, "profile", "default"),
        "tools": sorted(tools),
        "extensions": sorted(extensions),
    }

    # Serialize to JSON and hash
    json_str = json.dumps(structure_data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


class CheckpointValidationResult(BaseModel):
    """Result of checkpoint validation"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
