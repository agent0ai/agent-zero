# tests/test_integration_deployment.py
import pytest

from python.tools.deployment_config import DeploymentConfig
from python.tools.deployment_strategies.aws import AWSStrategy
from python.tools.deployment_strategies.gcp import GCPStrategy
from python.tools.deployment_strategies.github_actions import GitHubActionsStrategy
from python.tools.deployment_strategies.kubernetes import KubernetesStrategy
from python.tools.deployment_strategies.ssh import SSHStrategy


@pytest.mark.asyncio
async def test_kubernetes_end_to_end_deployment():
    """Test complete Kubernetes deployment workflow"""
    # Step 1: Create strategy
    strategy = KubernetesStrategy()

    # Step 2: Validate configuration
    config = {"kubectl_context": "prod-cluster", "manifest_path": "k8s/production/", "deployment_name": "api-server"}

    valid = await strategy.validate_config(config)
    assert valid is True

    # Step 3: Execute deployment
    result = await strategy.execute_deployment(config)
    assert result["status"] == "success"
    assert "deployment_name" in result

    # Step 4: Run smoke tests
    passed, smoke_results = await strategy.run_smoke_tests(config)
    assert isinstance(passed, bool)
    assert "http_health" in smoke_results

    # Step 5: Rollback capability
    rollback_result = await strategy.rollback()
    assert rollback_result["rollback_successful"] is True


@pytest.mark.asyncio
async def test_ssh_end_to_end_deployment():
    """Test complete SSH deployment workflow"""
    strategy = SSHStrategy()

    config = {"host": "prod-server.example.com", "deploy_script": "deploy.sh", "user": "deployer"}

    # Validation
    valid = await strategy.validate_config(config)
    assert valid is True

    # Deployment
    result = await strategy.execute_deployment(config)
    assert result["status"] == "success"
    assert result["host"] == "prod-server.example.com"

    # Smoke tests
    passed, smoke_results = await strategy.run_smoke_tests({"health_checks": {"service_name": "api"}})
    assert isinstance(passed, bool)
    assert "service_running" in smoke_results

    # Rollback
    rollback_result = await strategy.rollback()
    assert rollback_result["rollback_successful"] is True


@pytest.mark.asyncio
async def test_github_actions_end_to_end_deployment():
    """Test complete GitHub Actions deployment workflow"""
    strategy = GitHubActionsStrategy()

    config = {"repository": "org/repo", "workflow_file": "deploy.yml", "environment": "production"}

    # Validation
    valid = await strategy.validate_config(config)
    assert valid is True

    # Deployment (triggers workflow)
    result = await strategy.execute_deployment(config)
    assert result["status"] == "success"
    assert "workflow_run_id" in result

    # Smoke tests (check workflow status)
    smoke_config = {"workflow_run_id": result["workflow_run_id"]}
    passed, smoke_results = await strategy.run_smoke_tests(smoke_config)
    assert isinstance(passed, bool)
    assert "workflow_status" in smoke_results

    # Rollback (trigger rollback workflow)
    rollback_result = await strategy.rollback()
    assert rollback_result["rollback_successful"] is True


@pytest.mark.asyncio
async def test_aws_end_to_end_deployment():
    """Test complete AWS deployment workflow"""
    strategy = AWSStrategy()

    # Test ECS deployment
    config = {"service": "ecs", "cluster": "prod-cluster", "task_definition": "api"}

    # Validation
    valid = await strategy.validate_config(config)
    assert valid is True

    # Deployment
    result = await strategy.execute_deployment(config)
    assert result["status"] == "success"
    assert "deployment_id" in result
    assert result["service"] == "ecs"

    # Smoke tests
    passed, smoke_results = await strategy.run_smoke_tests(config)
    assert isinstance(passed, bool)
    assert "deployment_status" in smoke_results

    # Rollback
    rollback_result = await strategy.rollback()
    assert rollback_result["rollback_successful"] is True


@pytest.mark.asyncio
async def test_gcp_end_to_end_deployment():
    """Test complete GCP deployment workflow"""
    strategy = GCPStrategy()

    # Test Cloud Run deployment
    config = {"service": "cloudrun", "service_name": "api-server", "region": "us-central1"}

    # Validation
    valid = await strategy.validate_config(config)
    assert valid is True

    # Deployment
    result = await strategy.execute_deployment(config)
    assert result["status"] == "success"
    assert "deployment_id" in result
    assert result["service"] == "cloudrun"

    # Smoke tests
    passed, smoke_results = await strategy.run_smoke_tests(config)
    assert isinstance(passed, bool)
    assert "service_status" in smoke_results

    # Rollback
    rollback_result = await strategy.rollback()
    assert rollback_result["rollback_successful"] is True


def test_config_loader_integration():
    """Test deployment config integration with all platforms"""
    config_loader = DeploymentConfig()

    # Test all valid platforms
    for platform in ["kubernetes", "ssh", "github-actions", "aws", "gcp"]:
        assert config_loader.validate_platform(platform) is True

    # Test invalid platform raises ValueError
    with pytest.raises(ValueError, match="Invalid platform"):
        config_loader.validate_platform("invalid")

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
    """Test switching between different deployment strategies"""
    configs = {
        "kubernetes": {
            "kubectl_context": "prod",
            "manifest_path": "k8s/",
        },
        "ssh": {
            "host": "server.example.com",
            "deploy_script": "deploy.sh",
        },
        "github-actions": {
            "repository": "org/repo",
            "workflow_file": "deploy.yml",
        },
        "aws": {
            "service": "lambda",
            "function_name": "api-handler",
        },
        "gcp": {
            "service": "gke",
            "cluster": "prod-cluster",
        },
    }

    strategies = {
        "kubernetes": KubernetesStrategy(),
        "ssh": SSHStrategy(),
        "github-actions": GitHubActionsStrategy(),
        "aws": AWSStrategy(),
        "gcp": GCPStrategy(),
    }

    # Test that each strategy can validate and deploy
    for platform, strategy in strategies.items():
        config = configs[platform]

        # Validate
        valid = await strategy.validate_config(config)
        assert valid is True, f"{platform} validation failed"

        # Deploy
        result = await strategy.execute_deployment(config)
        assert result["status"] == "success", f"{platform} deployment failed"
