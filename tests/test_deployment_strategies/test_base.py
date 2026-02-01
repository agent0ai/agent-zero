import pytest

from python.helpers.deployment_progress import StreamingProgressReporter
from python.tools.deployment_strategies.base import DeploymentStrategy


class ConcreteStrategy(DeploymentStrategy):
    """Minimal concrete implementation for testing"""

    async def validate_config(self, config):
        return True

    async def execute_deployment(self, config, deployment_mode="rolling"):
        await self._report_progress("Starting deployment", 0)
        yield {"status": "success", "mode": deployment_mode}

    async def run_smoke_tests(self, config):
        return True, {"test": "passed"}

    async def rollback(self):
        await self._report_progress("Rolling back", 0)
        yield {"rollback_successful": True}


def test_deployment_strategy_can_be_instantiated():
    """Test that we can create a concrete strategy instance"""
    strategy = ConcreteStrategy()
    assert strategy is not None


def test_deployment_strategy_requires_abstract_methods():
    """Test that base class enforces required methods"""
    with pytest.raises(TypeError):
        DeploymentStrategy()


def test_base_class_has_progress_reporter_support():
    """Test base class supports progress reporter"""
    strategy = ConcreteStrategy()
    assert hasattr(strategy, "progress_reporter")
    assert hasattr(strategy, "set_progress_reporter")
    assert hasattr(strategy, "last_deployment_metadata")
    assert strategy.progress_reporter is None
    assert strategy.last_deployment_metadata is None


@pytest.mark.asyncio
async def test_base_class_report_progress_helper():
    """Test _report_progress helper method"""
    strategy = ConcreteStrategy()
    reporter = StreamingProgressReporter()
    strategy.set_progress_reporter(reporter)

    # Execute deployment should report progress
    result = None
    async for update in strategy.execute_deployment({"test": True}):
        result = update

    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_execute_deployment_returns_async_generator():
    """Test execute_deployment returns async generator"""
    strategy = ConcreteStrategy()
    config = {"test": True}

    result = strategy.execute_deployment(config)
    # Should be an async generator
    assert hasattr(result, "__anext__")

    # Should yield results
    final_result = None
    async for update in result:
        final_result = update

    assert final_result["status"] == "success"
    assert final_result["mode"] == "rolling"


@pytest.mark.asyncio
async def test_execute_deployment_with_deployment_mode():
    """Test execute_deployment respects deployment_mode parameter"""
    strategy = ConcreteStrategy()
    config = {"test": True}

    final_result = None
    async for update in strategy.execute_deployment(config, deployment_mode="blue-green"):
        final_result = update

    assert final_result["mode"] == "blue-green"


@pytest.mark.asyncio
async def test_rollback_returns_async_generator():
    """Test rollback returns async generator"""
    strategy = ConcreteStrategy()

    result = strategy.rollback()
    # Should be an async generator
    assert hasattr(result, "__anext__")

    # Should yield results
    final_result = None
    async for update in result:
        final_result = update

    assert final_result["rollback_successful"] is True
