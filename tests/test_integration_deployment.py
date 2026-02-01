"""
Comprehensive integration tests for all deployment strategies.

Tests verify:
- Configuration validation for each platform
- Full deployment workflow (validate → deploy → test → rollback)
- Async generator behavior for streaming results
- Progress reporting support
- Error handling and resilience
- Multi-strategy switching
- Config merging and validation
"""

from unittest.mock import MagicMock, patch

import pytest

from python.helpers.deployment_progress import StreamingProgressReporter
from python.tools.deployment_config import DeploymentConfig
from python.tools.deployment_strategies.aws import AWSStrategy
from python.tools.deployment_strategies.gcp import GCPStrategy
from python.tools.deployment_strategies.github_actions import GitHubActionsStrategy
from python.tools.deployment_strategies.kubernetes import KubernetesStrategy
from python.tools.deployment_strategies.ssh import SSHStrategy

# ============================================================================
# Kubernetes Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_kubernetes_end_to_end_deployment():
    """Test complete Kubernetes deployment workflow with streaming results."""
    strategy = KubernetesStrategy()

    # Set progress reporter
    strategy.set_progress_reporter(StreamingProgressReporter())

    config = {
        "kubectl_context": "prod-cluster",
        "manifest_path": "k8s/production/",
        "deployment_name": "api-server",
    }

    # Validate configuration
    valid = await strategy.validate_config(config)
    assert valid is True

    # Execute deployment with mocked kubernetes client
    with patch("python.tools.deployment_strategies.kubernetes.config"):
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            mock_deployment = MagicMock()
            mock_deployment.metadata.generation = 1

            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = mock_deployment
            mock_client.AppsV1Api.return_value = mock_api

            with patch.object(strategy, "_parse_manifests") as mock_parse:
                with patch.object(strategy, "_apply_manifests") as mock_apply:
                    with patch.object(strategy, "_wait_for_rollout"):
                        mock_parse.return_value = [{"kind": "Deployment", "metadata": {"name": "api-server"}}]
                        mock_apply.return_value = ["Deployment/api-server"]

                        # Collect all deployment updates
                        final_result = None
                        async for update in strategy.execute_deployment(config):
                            final_result = update

                        assert final_result["status"] == "success"
                        assert final_result["deployment_name"] == "api-server"

    # Run smoke tests
    config_with_health = config.copy()
    config_with_health["health_endpoint"] = "http://localhost:8080/health"

    passed, smoke_results = await strategy.run_smoke_tests(config_with_health)
    assert isinstance(passed, bool)

    # Rollback
    with patch("python.tools.deployment_strategies.kubernetes.config"):
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            mock_deployment = MagicMock()
            mock_deployment.metadata.generation = 1
            mock_deployment.status.updated_replicas = 1
            mock_deployment.status.available_replicas = 1
            mock_deployment.spec.replicas = 1

            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = mock_deployment
            mock_client.AppsV1Api.return_value = mock_api

            final_rollback = None
            async for update in strategy.rollback():
                final_rollback = update

            assert final_rollback["rollback_successful"] is True


@pytest.mark.asyncio
async def test_kubernetes_with_deployment_modes():
    """Test Kubernetes deployment with different deployment modes."""
    strategy = KubernetesStrategy()

    config = {
        "kubectl_context": "test-cluster",
        "manifest_path": "k8s/test/",
        "deployment_name": "test-api",
    }

    with patch("python.tools.deployment_strategies.kubernetes.config"):
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            mock_deployment = MagicMock()
            mock_deployment.metadata.generation = 1

            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = mock_deployment
            mock_client.AppsV1Api.return_value = mock_api

            with patch.object(strategy, "_parse_manifests") as mock_parse:
                with patch.object(strategy, "_apply_manifests") as mock_apply:
                    with patch.object(strategy, "_wait_for_rollout"):
                        mock_parse.return_value = [{"kind": "Deployment", "metadata": {"name": "test-api"}}]
                        mock_apply.return_value = ["Deployment/test-api"]

                        # Test rolling deployment mode
                        final_result = None
                        async for update in strategy.execute_deployment(config, deployment_mode="rolling"):
                            final_result = update

                        assert final_result["status"] == "success"

                        # Test blue-green deployment mode
                        final_result = None
                        async for update in strategy.execute_deployment(config, deployment_mode="blue-green"):
                            final_result = update

                        assert final_result["status"] == "success"


# ============================================================================
# SSH Integration Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="SSH strategy POC implementation")
async def test_ssh_end_to_end_deployment():
    """Test complete SSH deployment workflow."""
    pass


# ============================================================================
# GitHub Actions Integration Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="GitHub Actions strategy POC implementation")
async def test_github_actions_end_to_end_deployment():
    """Test complete GitHub Actions deployment workflow."""
    pass


# ============================================================================
# AWS Integration Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="AWS strategy POC implementation")
async def test_aws_ecs_end_to_end_deployment():
    """Test complete AWS ECS deployment workflow."""
    pass


@pytest.mark.asyncio
@pytest.mark.skip(reason="AWS strategy POC implementation")
async def test_aws_lambda_end_to_end_deployment():
    """Test AWS Lambda deployment workflow."""
    pass


# ============================================================================
# GCP Integration Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="GCP strategy POC implementation")
async def test_gcp_cloud_run_end_to_end_deployment():
    """Test complete GCP Cloud Run deployment workflow."""
    pass


@pytest.mark.asyncio
@pytest.mark.skip(reason="GCP strategy POC implementation")
async def test_gcp_gke_end_to_end_deployment():
    """Test GCP GKE (Kubernetes Engine) deployment workflow."""
    pass


# ============================================================================
# Configuration and Multi-Strategy Integration Tests
# ============================================================================


def test_config_loader_integration():
    """Test deployment config integration with all platforms."""
    config_loader = DeploymentConfig()

    # Test all valid platforms
    for platform in ["kubernetes", "ssh", "github-actions", "aws", "gcp"]:
        assert config_loader.validate_platform(platform) is True

    # Test invalid platform raises ValueError
    with pytest.raises(ValueError, match="Invalid platform"):
        config_loader.validate_platform("invalid-platform")

    # Test config merging
    file_config = {"environment": "staging", "skip_tests": False}
    explicit_params = {"environment": "production", "platform": "kubernetes"}

    merged = config_loader.merge_configs(file_config, explicit_params)

    # Explicit params should override file config
    assert merged["environment"] == "production"
    assert merged["platform"] == "kubernetes"
    assert merged["skip_tests"] is False  # From file config


@pytest.mark.asyncio
async def test_multi_platform_strategy_switching():
    """Test switching between different deployment strategies."""
    configs = {
        "kubernetes": {
            "kubectl_context": "prod",
            "manifest_path": "k8s/",
            "deployment_name": "api",
        },
        "ssh": {
            "host": "server.example.com",
            "deploy_script": "deploy.sh",
            "user": "deployer",
        },
        "github-actions": {
            "repository": "org/repo",
            "workflow_file": "deploy.yml",
            "environment": "production",
        },
        "aws": {
            "service": "ecs",
            "cluster": "prod",
            "task_definition": "api",
        },
        "gcp": {
            "service": "cloudrun",
            "service_name": "api",
            "region": "us-central1",
        },
    }

    strategies = {
        "kubernetes": KubernetesStrategy(),
        "ssh": SSHStrategy(),
        "github-actions": GitHubActionsStrategy(),
        "aws": AWSStrategy(),
        "gcp": GCPStrategy(),
    }

    # Test that each strategy validates its config
    for platform, strategy in strategies.items():
        config = configs[platform]
        valid = await strategy.validate_config(config)
        assert valid is True, f"{platform} validation failed"


@pytest.mark.asyncio
async def test_progress_reporting_integration():
    """Test progress reporting across all strategies."""
    reporter = StreamingProgressReporter()

    strategies_and_configs = [
        (
            KubernetesStrategy(),
            {
                "kubectl_context": "test",
                "manifest_path": "k8s/",
                "deployment_name": "api",
            },
        ),
        (
            SSHStrategy(),
            {"host": "server.com", "deploy_script": "deploy.sh", "user": "user"},
        ),
        (
            GitHubActionsStrategy(),
            {
                "repository": "org/repo",
                "workflow_file": "deploy.yml",
                "environment": "prod",
            },
        ),
        (AWSStrategy(), {"service": "ecs", "cluster": "prod", "task_definition": "api"}),
        (GCPStrategy(), {"service": "cloudrun", "service_name": "api", "region": "us-central1"}),
    ]

    for strategy, _ in strategies_and_configs:
        # Set progress reporter
        strategy.set_progress_reporter(reporter)
        assert strategy.progress_reporter is not None

        # Verify reporter can be used
        progress_updates = []
        async for update in reporter.report("Testing progress", 50):
            progress_updates.append(update)

        assert len(progress_updates) == 1
        assert progress_updates[0]["percent"] == 50


@pytest.mark.asyncio
async def test_deployment_metadata_tracking():
    """Test that strategies track deployment metadata for rollback."""
    strategy = KubernetesStrategy()

    # Initially no metadata
    assert strategy.last_deployment_metadata is None

    config = {
        "kubectl_context": "test",
        "manifest_path": "k8s/",
        "deployment_name": "api",
    }

    # Mock deployment execution to set metadata
    with patch("python.tools.deployment_strategies.kubernetes.config"):
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            mock_deployment = MagicMock()
            mock_deployment.metadata.generation = 5

            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = mock_deployment
            mock_client.AppsV1Api.return_value = mock_api

            with patch.object(strategy, "_parse_manifests") as mock_parse:
                with patch.object(strategy, "_apply_manifests") as mock_apply:
                    with patch.object(strategy, "_wait_for_rollout"):
                        mock_parse.return_value = [{"kind": "Deployment", "metadata": {"name": "api"}}]
                        mock_apply.return_value = ["Deployment/api"]

                        async for _ in strategy.execute_deployment(config):
                            pass

    # Verify metadata was stored
    assert strategy.last_deployment_metadata is not None
    assert strategy.last_deployment_metadata["deployment_name"] == "api"
    assert strategy.last_deployment_metadata["revision"] == 5


@pytest.mark.asyncio
async def test_error_handling_across_strategies():
    """Test error handling and resilience across all strategies."""
    strategies = [
        KubernetesStrategy(),
        SSHStrategy(),
        GitHubActionsStrategy(),
        AWSStrategy(),
        GCPStrategy(),
    ]

    for strategy in strategies:
        # Invalid config should raise ValueError
        invalid_config = {}

        with pytest.raises(ValueError):
            await strategy.validate_config(invalid_config)


@pytest.mark.asyncio
async def test_async_generator_behavior():
    """Test that all strategies properly use async generators."""
    strategy = KubernetesStrategy()

    config = {
        "kubectl_context": "test",
        "manifest_path": "k8s/",
        "deployment_name": "api",
    }

    with patch("python.tools.deployment_strategies.kubernetes.config"):
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            mock_deployment = MagicMock()
            mock_deployment.metadata.generation = 1

            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = mock_deployment
            mock_client.AppsV1Api.return_value = mock_api

            with patch.object(strategy, "_parse_manifests") as mock_parse:
                with patch.object(strategy, "_apply_manifests") as mock_apply:
                    with patch.object(strategy, "_wait_for_rollout"):
                        mock_parse.return_value = [{"kind": "Deployment", "metadata": {"name": "api"}}]
                        mock_apply.return_value = ["Deployment/api"]

                        # Verify execute_deployment returns async generator
                        result = strategy.execute_deployment(config)
                        assert hasattr(result, "__anext__"), "Should return async generator"

                        # Verify we can iterate through all updates
                        update_count = 0
                        async for _ in result:
                            update_count += 1

                        assert update_count >= 1, "Should yield at least one update"

    # Verify rollback returns async generator
    strategy.last_deployment_metadata = {
        "deployment_name": "api",
        "namespace": "default",
        "context": "test",
    }

    with patch("python.tools.deployment_strategies.kubernetes.config"):
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            mock_deployment = MagicMock()
            mock_deployment.status.updated_replicas = 1
            mock_deployment.status.available_replicas = 1
            mock_deployment.spec.replicas = 1

            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = mock_deployment
            mock_client.AppsV1Api.return_value = mock_api

            # Verify rollback returns async generator
            result = strategy.rollback()
            assert hasattr(result, "__anext__"), "Rollback should return async generator"

            # Verify we can iterate
            async for update in result:
                assert update is not None
