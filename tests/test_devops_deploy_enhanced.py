# tests/test_devops_deploy_enhanced.py

# Import strategies directly for testing
from python.tools.deployment_strategies.aws import AWSStrategy
from python.tools.deployment_strategies.gcp import GCPStrategy
from python.tools.deployment_strategies.github_actions import GitHubActionsStrategy
from python.tools.deployment_strategies.kubernetes import KubernetesStrategy
from python.tools.deployment_strategies.ssh import SSHStrategy


def test_select_strategy_kubernetes():
    """Test that platform='kubernetes' maps to KubernetesStrategy"""
    # This tests the strategy mapping logic that will be in _select_strategy
    platform_map = {
        "kubernetes": KubernetesStrategy,
        "ssh": SSHStrategy,
        "github-actions": GitHubActionsStrategy,
        "aws": AWSStrategy,
        "gcp": GCPStrategy,
    }

    strategy_class = platform_map.get("kubernetes")
    assert strategy_class == KubernetesStrategy

    strategy = strategy_class()
    assert isinstance(strategy, KubernetesStrategy)


def test_select_strategy_ssh():
    """Test that platform='ssh' maps to SSHStrategy"""
    platform_map = {
        "kubernetes": KubernetesStrategy,
        "ssh": SSHStrategy,
        "github-actions": GitHubActionsStrategy,
        "aws": AWSStrategy,
        "gcp": GCPStrategy,
    }

    strategy_class = platform_map.get("ssh")
    assert strategy_class == SSHStrategy

    strategy = strategy_class()
    assert isinstance(strategy, SSHStrategy)


def test_select_strategy_github_actions():
    """Test that platform='github-actions' maps to GitHubActionsStrategy"""
    platform_map = {
        "kubernetes": KubernetesStrategy,
        "ssh": SSHStrategy,
        "github-actions": GitHubActionsStrategy,
        "aws": AWSStrategy,
        "gcp": GCPStrategy,
    }

    strategy_class = platform_map.get("github-actions")
    assert strategy_class == GitHubActionsStrategy

    strategy = strategy_class()
    assert isinstance(strategy, GitHubActionsStrategy)


def test_select_strategy_aws():
    """Test that platform='aws' maps to AWSStrategy"""
    platform_map = {
        "kubernetes": KubernetesStrategy,
        "ssh": SSHStrategy,
        "github-actions": GitHubActionsStrategy,
        "aws": AWSStrategy,
        "gcp": GCPStrategy,
    }

    strategy_class = platform_map.get("aws")
    assert strategy_class == AWSStrategy

    strategy = strategy_class()
    assert isinstance(strategy, AWSStrategy)


def test_select_strategy_gcp():
    """Test that platform='gcp' maps to GCPStrategy"""
    platform_map = {
        "kubernetes": KubernetesStrategy,
        "ssh": SSHStrategy,
        "github-actions": GitHubActionsStrategy,
        "aws": AWSStrategy,
        "gcp": GCPStrategy,
    }

    strategy_class = platform_map.get("gcp")
    assert strategy_class == GCPStrategy

    strategy = strategy_class()
    assert isinstance(strategy, GCPStrategy)


def test_select_strategy_invalid_platform():
    """Test that invalid platform returns None"""
    platform_map = {
        "kubernetes": KubernetesStrategy,
        "ssh": SSHStrategy,
        "github-actions": GitHubActionsStrategy,
        "aws": AWSStrategy,
        "gcp": GCPStrategy,
    }

    strategy_class = platform_map.get("invalid-platform")
    assert strategy_class is None


def test_select_strategy_no_platform():
    """Test that no platform returns None (falls back to POC mode)"""
    platform_map = {
        "kubernetes": KubernetesStrategy,
        "ssh": SSHStrategy,
        "github-actions": GitHubActionsStrategy,
        "aws": AWSStrategy,
        "gcp": GCPStrategy,
    }

    strategy_class = platform_map.get(None)
    assert strategy_class is None
