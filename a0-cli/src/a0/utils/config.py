"""Configuration management.

Loads config from (in priority order):
1. Environment variables
2. Project-level .a0.toml
3. User config ~/.config/a0/config.toml
4. Defaults
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

import tomli_w


class Config(BaseModel):
    """Application configuration."""

    # Agent Zero connection
    agent_url: str = Field(default="http://localhost:55080") # change from 8080
    api_key: Optional[str] = Field(default=None)

    # Display settings
    theme: str = Field(default="dark")

    # Shell settings
    shell: str = Field(default_factory=lambda: os.environ.get("SHELL", "/bin/bash"))

    # File settings
    max_file_size: int = Field(default=1_000_000)

    # ACP settings
    acp_auto_approve: bool = Field(default=False)

    @classmethod
    def load(cls) -> Config:
        """Load configuration from files and environment."""
        config_data: dict[str, Any] = {}

        # User config
        user_path = Path.home() / ".config" / "a0" / "config.toml"
        if user_path.exists():
            with open(user_path, "rb") as f:
                config_data.update(tomllib.load(f))

        # Project config
        project_path = Path.cwd() / ".a0.toml"
        if project_path.exists():
            with open(project_path, "rb") as f:
                config_data.update(tomllib.load(f))

        # Environment overrides
        env_mapping = {
            "AGENT_ZERO_URL": "agent_url",
            "AGENT_ZERO_API_KEY": "api_key",
            "A0_THEME": "theme",
        }
        for env_var, config_key in env_mapping.items():
            val = os.environ.get(env_var)
            if val is not None:
                config_data[config_key] = val

        return cls(**config_data)

    def save(self) -> None:
        """Save configuration to user config file."""
        user_path = Path.home() / ".config" / "a0" / "config.toml"
        user_path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(exclude_none=True)
        with open(user_path, "wb") as f:
            tomli_w.dump(data, f)
