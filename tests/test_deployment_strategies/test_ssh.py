import pytest

from python.tools.deployment_strategies.ssh import SSHStrategy


def test_ssh_strategy_can_be_instantiated():
    """Test that we can create an SSH strategy"""
    strategy = SSHStrategy()
    assert strategy is not None


@pytest.mark.asyncio
async def test_ssh_validate_config_requires_host():
    """Test that config validation requires host"""
    strategy = SSHStrategy()

    with pytest.raises(ValueError, match="host"):
        await strategy.validate_config({})


@pytest.mark.asyncio
async def test_ssh_validate_config_requires_deploy_script():
    """Test that config validation requires deploy script"""
    strategy = SSHStrategy()

    with pytest.raises(ValueError, match="deploy_script"):
        await strategy.validate_config({"host": "example.com"})


@pytest.mark.asyncio
async def test_ssh_validate_config_accepts_valid_config():
    """Test that valid config passes validation"""
    strategy = SSHStrategy()

    config = {"host": "example.com", "deploy_script": "deploy.sh", "user": "deployer"}

    assert await strategy.validate_config(config)


@pytest.mark.asyncio
async def test_ssh_execute_deployment_returns_success():
    """Test that execute_deployment returns success result"""
    strategy = SSHStrategy()

    config = {"host": "test.example.com", "deploy_script": "deploy.sh", "environment": "staging"}

    result = None
    async for item in strategy.execute_deployment(config):
        result = item

    assert result["status"] == "success"
    assert result["host"] == "test.example.com"


@pytest.mark.asyncio
async def test_ssh_smoke_tests_check_service_status():
    """Test that smoke tests verify service is running"""
    strategy = SSHStrategy()

    config = {"health_checks": {"service_name": "myapp"}}

    passed, results = await strategy.run_smoke_tests(config)

    assert isinstance(passed, bool)
    assert "service_running" in results


@pytest.mark.asyncio
async def test_ssh_rollback_restarts_previous_version():
    """Test that rollback restores previous version"""
    strategy = SSHStrategy()
    strategy.last_host = "example.com"

    result = None
    async for item in strategy.rollback():
        result = item

    assert result["rollback_successful"]
