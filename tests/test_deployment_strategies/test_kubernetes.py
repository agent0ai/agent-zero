# tests/test_deployment_strategies/test_kubernetes.py
from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.exceptions import ApiException

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

    config = {"kubectl_context": "prod-cluster", "manifest_path": "k8s/production/", "deployment_name": "api-server"}

    assert await strategy.validate_config(config)


@pytest.mark.asyncio
async def test_kubernetes_execute_deployment_returns_success():
    """Test that execute_deployment returns success result"""
    strategy = KubernetesStrategy()

    config = {
        "kubectl_context": "test-cluster",
        "manifest_path": "tests/fixtures/k8s/deployment.yaml",
        "deployment_name": "test-api",
    }

    # Mock kubernetes client
    with patch("kubernetes.config.load_kube_config"):
        with patch("kubernetes.client.ApiClient"):
            with patch("kubernetes.client.AppsV1Api") as mock_apps_api:
                with patch("kubernetes.client.CoreV1Api"):
                    # Mock deployment status for rollout waiting
                    mock_deployment = MagicMock()
                    mock_deployment.metadata.name = "test-api"
                    mock_deployment.spec.replicas = 3
                    mock_deployment.status.updated_replicas = 3
                    mock_deployment.status.ready_replicas = 3
                    mock_deployment.status.available_replicas = 3

                    mock_api_instance = mock_apps_api.return_value
                    mock_api_instance.read_namespaced_deployment.side_effect = [
                        ApiException(status=404),
                        mock_deployment,
                    ]

                    result = None
                    async for item in strategy.execute_deployment(config):
                        result = item

                    assert result["status"] == "success"
                    assert "deployment_name" in result


@pytest.mark.asyncio
async def test_kubernetes_smoke_tests_check_http_endpoint():
    """Test that smoke tests check HTTP health endpoint"""
    strategy = KubernetesStrategy()

    config = {"health_checks": {"http_endpoint": "http://localhost:8080/health"}}

    # This is a mock test - real implementation would make HTTP request
    passed, results = await strategy.run_smoke_tests(config)

    assert isinstance(passed, bool)
    assert "http_health" in results


@pytest.mark.asyncio
async def test_kubernetes_rollback_undoes_deployment():
    """Test that rollback executes kubectl rollout undo"""
    strategy = KubernetesStrategy()

    # Set up deployment metadata (normally set by execute_deployment)
    strategy.last_deployment_metadata = {
        "deployment_name": "api-server",
        "namespace": "default",
        "kubectl_context": "test-context",
        "timestamp": 1234567890.0,
    }

    # Mock kubernetes client
    with patch("kubernetes.config.load_kube_config"):
        with patch("kubernetes.client.ApiClient"):
            with patch("kubernetes.client.AppsV1Api") as mock_apps_api:
                with patch("kubernetes.client.CoreV1Api"):
                    # Mock deployment for rollback
                    mock_deployment = MagicMock()
                    mock_deployment.metadata.name = "api-server"
                    mock_deployment.metadata.annotations = {"deployment.kubernetes.io/revision": "3"}
                    mock_deployment.spec.replicas = 3
                    mock_deployment.status.updated_replicas = 3
                    mock_deployment.status.ready_replicas = 3
                    mock_deployment.status.available_replicas = 3

                    mock_api_instance = mock_apps_api.return_value
                    mock_api_instance.read_namespaced_deployment.return_value = mock_deployment

                    result = None
                    async for item in strategy.rollback():
                        result = item

                    assert result["rollback_successful"]


@pytest.mark.asyncio
async def test_kubernetes_real_deployment_with_mock():
    """Test real Kubernetes deployment logic with mocked client"""
    strategy = KubernetesStrategy()

    config = {
        "kubectl_context": "test-context",
        "namespace": "default",
        "manifest_path": "tests/fixtures/k8s/deployment.yaml",
        "deployment_name": "test-app",
    }

    # Mock kubernetes client
    with patch("kubernetes.config.load_kube_config"):
        with patch("kubernetes.client.ApiClient"):
            with patch("kubernetes.client.AppsV1Api") as mock_apps_api:
                with patch("kubernetes.client.CoreV1Api"):
                    # Mock deployment status for rollout waiting
                    mock_deployment = MagicMock()
                    mock_deployment.metadata.name = "test-app"
                    mock_deployment.spec.replicas = 3
                    mock_deployment.status.updated_replicas = 3
                    mock_deployment.status.ready_replicas = 3
                    mock_deployment.status.available_replicas = 3

                    # First call for create/update check (404 = not found)
                    # Second+ calls for rollout waiting (return ready deployment)
                    mock_api_instance = mock_apps_api.return_value
                    mock_api_instance.read_namespaced_deployment.side_effect = [
                        ApiException(status=404),  # Not found, will create
                        mock_deployment,  # Rollout check - ready
                    ]

                    result = None
                    async for update in strategy.execute_deployment(config, "rolling"):
                        if update.get("type") != "progress":
                            result = update

                    assert result["status"] == "success"
                    assert result["deployment_name"] == "test-app"

                    # Verify deployment was created
                    mock_api_instance.create_namespaced_deployment.assert_called_once()
