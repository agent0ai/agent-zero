# tests/test_deployment_strategies/test_gcp.py
import pytest

from python.tools.deployment_strategies.gcp import GCPStrategy


def test_gcp_strategy_can_be_instantiated():
    """Test that we can create a GCP strategy"""
    strategy = GCPStrategy()
    assert strategy is not None


@pytest.mark.asyncio
async def test_gcp_validate_config_requires_service():
    """Test that config validation requires GCP service"""
    strategy = GCPStrategy()

    with pytest.raises(ValueError, match="service"):
        await strategy.validate_config({})


@pytest.mark.asyncio
async def test_gcp_validate_config_accepts_valid_services():
    """Test that valid GCP services pass validation"""
    strategy = GCPStrategy()

    for service in ["cloudrun", "gke", "cloudbuild"]:
        config = {"service": service, "project": "my-project"}
        assert await strategy.validate_config(config)


@pytest.mark.asyncio
async def test_gcp_execute_deployment_returns_success():
    """Test that execute_deployment works for Cloud Run"""
    strategy = GCPStrategy()

    config = {"service": "cloudrun", "service_name": "api-server", "region": "us-central1"}

    result = None
    async for item in strategy.execute_deployment(config):
        result = item

    assert result["status"] == "success"
    assert "deployment_id" in result
