# tests/test_deployment_strategies/test_aws.py
import pytest

from python.tools.deployment_strategies.aws import AWSStrategy


def test_aws_strategy_can_be_instantiated():
    """Test that we can create an AWS strategy"""
    strategy = AWSStrategy()
    assert strategy is not None


@pytest.mark.asyncio
async def test_aws_validate_config_requires_service():
    """Test that config validation requires AWS service"""
    strategy = AWSStrategy()

    with pytest.raises(ValueError, match="service"):
        await strategy.validate_config({})


@pytest.mark.asyncio
async def test_aws_validate_config_accepts_valid_services():
    """Test that valid AWS services pass validation"""
    strategy = AWSStrategy()

    for service in ["ecs", "lambda", "codedeploy"]:
        config = {"service": service, "region": "us-east-1"}
        assert await strategy.validate_config(config)


@pytest.mark.asyncio
async def test_aws_execute_deployment_returns_success():
    """Test that execute_deployment works for ECS"""
    strategy = AWSStrategy()

    config = {"service": "ecs", "cluster": "prod-cluster", "task_definition": "api-server"}

    result = None
    async for item in strategy.execute_deployment(config):
        result = item

    assert result["status"] == "success"
    assert "deployment_id" in result
