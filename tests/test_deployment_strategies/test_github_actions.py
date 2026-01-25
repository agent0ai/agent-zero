import pytest

from python.tools.deployment_strategies.github_actions import GitHubActionsStrategy


def test_github_actions_strategy_can_be_instantiated():
    """Test that we can create a GitHub Actions strategy"""
    strategy = GitHubActionsStrategy()
    assert strategy is not None


@pytest.mark.asyncio
async def test_github_actions_validate_config_requires_repo():
    """Test that config validation requires repository"""
    strategy = GitHubActionsStrategy()

    with pytest.raises(ValueError, match="repository"):
        await strategy.validate_config({})


@pytest.mark.asyncio
async def test_github_actions_validate_config_requires_workflow():
    """Test that config validation requires workflow file"""
    strategy = GitHubActionsStrategy()

    with pytest.raises(ValueError, match="workflow_file"):
        await strategy.validate_config({"repository": "owner/repo"})


@pytest.mark.asyncio
async def test_github_actions_validate_config_accepts_valid_config():
    """Test that valid config passes validation"""
    strategy = GitHubActionsStrategy()

    config = {"repository": "owner/repo", "workflow_file": "deploy.yml", "branch": "main"}

    assert await strategy.validate_config(config)


@pytest.mark.asyncio
async def test_github_actions_execute_deployment_triggers_workflow():
    """Test that execute_deployment triggers GitHub workflow"""
    strategy = GitHubActionsStrategy()

    config = {"repository": "owner/repo", "workflow_file": "deploy.yml", "environment": "production"}

    result = await strategy.execute_deployment(config)

    assert result["status"] == "success"
    assert "workflow_run_id" in result


@pytest.mark.asyncio
async def test_github_actions_smoke_tests_check_workflow_status():
    """Test that smoke tests verify workflow completed successfully"""
    strategy = GitHubActionsStrategy()

    config = {"workflow_run_id": "123456"}

    passed, results = await strategy.run_smoke_tests(config)

    assert isinstance(passed, bool)
    assert "workflow_status" in results


@pytest.mark.asyncio
async def test_github_actions_rollback_triggers_rollback_workflow():
    """Test that rollback triggers rollback workflow"""
    strategy = GitHubActionsStrategy()
    strategy.last_repository = "owner/repo"

    result = await strategy.rollback()

    assert result["rollback_successful"]
