"""
Qdrant MCP Server Configuration
Environment-based configuration with sensible defaults
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QdrantConfig:
    """Qdrant connection configuration"""
    url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://qdrant-unity:6333"))
    grpc_url: str = field(default_factory=lambda: os.getenv("QDRANT_GRPC_URL", "http://qdrant-unity:6334"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("QDRANT_API_KEY") or None)
    timeout: int = field(default_factory=lambda: int(os.getenv("QDRANT_TIMEOUT", "30")))
    prefer_grpc: bool = field(default_factory=lambda: os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true")


@dataclass
class MCPConfig:
    """MCP server configuration"""
    name: str = field(default_factory=lambda: os.getenv("MCP_SERVER_NAME", "qdrant-admin"))
    port: int = field(default_factory=lambda: int(os.getenv("MCP_SERVER_PORT", "8080")))
    host: str = field(default_factory=lambda: os.getenv("MCP_SERVER_HOST", "0.0.0.0"))
    log_level: str = field(default_factory=lambda: os.getenv("MCP_LOG_LEVEL", "info"))


@dataclass
class RedisConfig:
    """Redis cache configuration (optional)"""
    url: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_URL"))
    enabled: bool = field(default_factory=lambda: bool(os.getenv("REDIS_URL")))
    ttl: int = field(default_factory=lambda: int(os.getenv("REDIS_TTL", "3600")))


@dataclass
class AppConfig:
    """Main application configuration"""
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    default_collection: str = field(default_factory=lambda: os.getenv("DEFAULT_COLLECTION", "unity_project_kb"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")


# Global config instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance"""
    return config
