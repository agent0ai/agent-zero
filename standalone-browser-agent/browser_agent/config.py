"""
Configuration management for browser agent.
"""

import os
from pathlib import Path
from typing import Optional, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class BrowserConfig(BaseModel):
    """Browser configuration settings."""

    headless: bool = Field(default=True, description="Run browser in headless mode")
    width: int = Field(default=1024, description="Browser viewport width")
    height: int = Field(default=2048, description="Browser viewport height")
    disable_security: bool = Field(default=True, description="Disable browser security features")
    user_data_dir: Optional[str] = Field(default=None, description="Browser user data directory")
    downloads_path: str = Field(default="./downloads", description="Download directory")
    extra_http_headers: Dict[str, str] = Field(default_factory=dict, description="Extra HTTP headers")


class LLMConfig(BaseModel):
    """LLM configuration settings."""

    provider: str = Field(default="openai", description="LLM provider (openai, anthropic, google, etc.)")
    model: str = Field(default="gpt-4o", description="Model name")
    api_key: Optional[str] = Field(default=None, description="API key for the LLM provider")
    temperature: float = Field(default=0.7, description="LLM temperature")
    use_vision: bool = Field(default=True, description="Use vision capabilities if available")


class AgentConfig(BaseModel):
    """Agent configuration settings."""

    max_steps: int = Field(default=50, description="Maximum number of steps the agent can take")
    llm_timeout: int = Field(default=300, description="LLM timeout in seconds")
    enable_memory: bool = Field(default=False, description="Enable agent memory")


class Config(BaseModel):
    """Main configuration for browser agent."""

    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file

        Returns:
            Config instance
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        return cls(
            browser=BrowserConfig(
                headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
                width=int(os.getenv("BROWSER_WIDTH", "1024")),
                height=int(os.getenv("BROWSER_HEIGHT", "2048")),
                disable_security=os.getenv("BROWSER_DISABLE_SECURITY", "true").lower() == "true",
                user_data_dir=os.getenv("BROWSER_USER_DATA_DIR"),
                downloads_path=os.getenv("BROWSER_DOWNLOADS_PATH", "./downloads"),
            ),
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "openai"),
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                use_vision=os.getenv("LLM_USE_VISION", "true").lower() == "true",
            ),
            agent=AgentConfig(
                max_steps=int(os.getenv("AGENT_MAX_STEPS", "50")),
                llm_timeout=int(os.getenv("AGENT_LLM_TIMEOUT", "300")),
                enable_memory=os.getenv("AGENT_ENABLE_MEMORY", "false").lower() == "true",
            ),
        )

    def get_llm_model(self):
        """
        Get LiteLLM model string.

        Returns:
            Model string in format 'provider/model'
        """
        # LiteLLM format: provider/model
        provider_map = {
            "openai": "openai",
            "anthropic": "anthropic",
            "google": "google",
            "gemini": "gemini",
        }

        provider = provider_map.get(self.llm.provider.lower(), self.llm.provider)
        return f"{provider}/{self.llm.model}"
