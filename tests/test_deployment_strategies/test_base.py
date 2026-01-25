import pytest

from python.helpers.deployment_progress import StreamingProgressReporter
from python.tools.deployment_strategies.base import DeploymentStrategy


class ConcreteStrategy(DeploymentStrategy):
    """Minimal concrete implementation for testing"""

    async def validate_config(self, config):
        return True

    async def execute_deployment(self, config, deployment_mode="rolling"):
        yield {"status": "success"}

    async def run_smoke_tests(self, config):
        return True, {"test": "passed"}

    async def rollback(self):
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

    class TestStrategy(DeploymentStrategy):
        async def validate_config(self, config):
            return True

        async def execute_deployment(self, config, deployment_mode="rolling"):
            yield {"status": "success"}

        async def run_smoke_tests(self, config):
            return True, {}

        async def rollback(self):
            yield {"rollback_successful": True}

    strategy = TestStrategy()
    assert hasattr(strategy, "progress_reporter")
    assert hasattr(strategy, "set_progress_reporter")
    assert hasattr(strategy, "last_deployment_metadata")


@pytest.mark.asyncio
async def test_base_class_report_progress_helper():
    """Test _report_progress helper method"""

    class TestStrategy(DeploymentStrategy):
        async def validate_config(self, config):
            return True

        async def execute_deployment(self, config, deployment_mode="rolling"):
            await self._report_progress("Deploying...", 50)
            yield {"status": "success"}

        async def run_smoke_tests(self, config):
            return True, {}

        async def rollback(self):
            yield {"rollback_successful": True}

    strategy = TestStrategy()
    reporter = StreamingProgressReporter()
    strategy.set_progress_reporter(reporter)

    # Execute deployment should report progress
    async for result in strategy.execute_deployment({}):
        assert result["status"] == "success"
