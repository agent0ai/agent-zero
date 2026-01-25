import os
import tempfile

import pytest

from python.tools.deployment_config import DeploymentConfig


def test_config_loader_can_be_instantiated():
    """Test that we can create a config loader"""
    config = DeploymentConfig()
    assert config is not None


def test_load_from_file_reads_yaml():
    """Test loading config from YAML file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
platform: kubernetes
namespace: prod
health_checks:
  http_endpoint: https://example.com/health
""")
        f.flush()

        config = DeploymentConfig()
        result = config.load_from_file(f.name)

        assert result["platform"] == "kubernetes"
        assert result["namespace"] == "prod"
        assert result["health_checks"]["http_endpoint"] == "https://example.com/health"

        os.unlink(f.name)


def test_load_from_file_handles_missing_file():
    """Test that missing file raises clear error"""
    config = DeploymentConfig()
    with pytest.raises(FileNotFoundError):
        config.load_from_file("/nonexistent/config.yaml")


def test_merge_configs_prefers_explicit_params():
    """Test that explicit params override file config"""
    file_config = {"platform": "kubernetes", "namespace": "prod"}
    explicit_params = {"platform": "ssh"}

    config = DeploymentConfig()
    merged = config.merge_configs(file_config, explicit_params)

    assert merged["platform"] == "ssh"  # Explicit wins
    assert merged["namespace"] == "prod"  # File value preserved


def test_validate_platform_accepts_valid_platforms():
    """Test that valid platforms pass validation"""
    config = DeploymentConfig()

    for platform in ["github-actions", "kubernetes", "ssh", "aws", "gcp"]:
        assert config.validate_platform(platform) is True


def test_validate_platform_rejects_invalid_platforms():
    """Test that invalid platforms fail validation"""
    config = DeploymentConfig()

    with pytest.raises(ValueError, match="Invalid platform"):
        config.validate_platform("docker-compose")
