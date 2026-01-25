import pytest

from python.tools.deployment_strategies.base import DeploymentStrategy


class ConcreteStrategy(DeploymentStrategy):
    """Minimal concrete implementation for testing"""

    async def validate_config(self, config):
        return True

    async def execute_deployment(self, config):
        return {"status": "success"}

    async def run_smoke_tests(self, config):
        return True, {"test": "passed"}

    async def rollback(self):
        return {"rollback_successful": True}


def test_deployment_strategy_can_be_instantiated():
    """Test that we can create a concrete strategy instance"""
    strategy = ConcreteStrategy()
    assert strategy is not None


def test_deployment_strategy_requires_abstract_methods():
    """Test that base class enforces required methods"""
    with pytest.raises(TypeError):
        DeploymentStrategy()
