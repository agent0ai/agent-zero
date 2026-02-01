# tests/test_deployment_strategies/test_kubernetes.py
from unittest.mock import MagicMock, patch

import pytest

from python.tools.deployment_strategies.kubernetes import KubernetesStrategy


def test_kubernetes_strategy_can_be_instantiated():
    """Test that we can create a Kubernetes strategy"""
    strategy = KubernetesStrategy()
    assert strategy is not None


@pytest.mark.asyncio
async def test_kubernetes_validate_config_requires_context():
    """Test that config validation requires kubectl context"""
    strategy = KubernetesStrategy()

    with pytest.raises(ValueError, match="kubectl_context"):
        await strategy.validate_config({})


@pytest.mark.asyncio
async def test_kubernetes_validate_config_requires_manifest_path():
    """Test that config validation requires manifest path"""
    strategy = KubernetesStrategy()

    with pytest.raises(ValueError, match="manifest_path"):
        await strategy.validate_config({"kubectl_context": "prod-cluster"})


@pytest.mark.asyncio
async def test_kubernetes_validate_config_accepts_valid_config():
    """Test that valid config passes validation"""
    strategy = KubernetesStrategy()

    config = {
        "kubectl_context": "prod-cluster",
        "manifest_path": "k8s/production/",
        "deployment_name": "api-server",
    }

    assert await strategy.validate_config(config)


@pytest.mark.asyncio
async def test_kubernetes_execute_deployment_returns_success():
    """Test that execute_deployment returns success result"""
    strategy = KubernetesStrategy()

    config = {
        "kubectl_context": "test-cluster",
        "manifest_path": "/tmp/nonexistent/",
        "deployment_name": "test-api",
    }

    # Mock kubernetes client and manifest parsing
    with patch("python.tools.deployment_strategies.kubernetes.config") as mock_config:
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            with patch.object(strategy, "_parse_manifests") as mock_parse:
                with patch.object(strategy, "_apply_manifests") as mock_apply:
                    with patch.object(strategy, "_wait_for_rollout") as mock_wait:
                        # Mock manifest parsing and application
                        mock_parse.return_value = [{"kind": "Deployment", "metadata": {"name": "test-api"}}]
                        mock_apply.return_value = ["Deployment/test-api"]
                        mock_wait.return_value = None

                        # Mock deployment object
                        mock_deployment = MagicMock()
                        mock_deployment.metadata.generation = 1

                        mock_api = MagicMock()
                        mock_api.read_namespaced_deployment.return_value = mock_deployment
                        mock_client.AppsV1Api.return_value = mock_api

                        # Collect all yielded updates
                        final_result = None
                        async for update in strategy.execute_deployment(config):
                            final_result = update

                        assert final_result["status"] == "success"
                        assert "deployment_name" in final_result


@pytest.mark.asyncio
async def test_kubernetes_smoke_tests_returns_results():
    """Test that smoke tests return results dict"""
    strategy = KubernetesStrategy()

    config = {"namespace": "default", "deployment_name": "test-api"}

    # Mock kubernetes API
    mock_deployment = MagicMock()
    mock_deployment.status.available_replicas = 2
    mock_deployment.spec.replicas = 2

    strategy.apps_v1_api = MagicMock()
    strategy.apps_v1_api.read_namespaced_deployment.return_value = mock_deployment

    passed, results = await strategy.run_smoke_tests(config)

    assert isinstance(passed, bool)
    assert "pods_running" in results
    assert passed is True


@pytest.mark.asyncio
async def test_kubernetes_rollback_undoes_deployment():
    """Test that rollback executes kubectl rollout undo"""
    strategy = KubernetesStrategy()
    strategy.last_deployment_metadata = {
        "deployment_name": "api-server",
        "namespace": "default",
        "context": "test-cluster",
    }

    # Mock kubernetes client
    with patch("python.tools.deployment_strategies.kubernetes.config") as mock_config:
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            # Mock deployment object
            mock_deployment = MagicMock()
            mock_deployment.metadata.generation = 1
            mock_deployment.status.updated_replicas = 1
            mock_deployment.status.available_replicas = 1
            mock_deployment.spec.replicas = 1

            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = mock_deployment
            mock_client.AppsV1Api.return_value = mock_api

            # Collect all yielded updates
            final_result = None
            async for update in strategy.rollback():
                final_result = update

            assert final_result["rollback_successful"] is True
