"""
Shared Test Fixtures for Agent Jumbo Tests

Import fixtures from this module in your tests:
    from tests.fixtures.common import sample_workflow, sample_skills

Or use pytest's conftest.py to auto-load fixtures.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

# ========== Path Fixtures ==========


@pytest.fixture
def project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def instruments_path(project_root):
    """Get instruments directory"""
    return project_root / "instruments" / "custom"


@pytest.fixture
def test_output_dir(tmp_path):
    """Get temp directory for test outputs"""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


# ========== Database Fixtures ==========


@pytest.fixture
def test_db_path(tmp_path):
    """Get isolated database path for tests"""
    return str(tmp_path / "test.db")


@pytest.fixture
def populated_db(test_db_path):
    """
    Database with sample data pre-loaded.
    Useful for read-heavy tests.
    """
    # Import and populate here
    # from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
    # manager = WorkflowEngineManager(test_db_path)
    # manager.create_workflow(name="Sample", stages=[...])
    # return test_db_path
    return test_db_path


# ========== Sample Data Fixtures ==========


@pytest.fixture
def sample_workflow_definition():
    """Sample workflow definition"""
    return {
        "name": "Test Workflow",
        "version": "1.0.0",
        "stages": [
            {
                "id": "stage1",
                "name": "Stage 1",
                "type": "design",
                "tasks": [{"id": "task1", "name": "Task 1", "duration_hours": 4}],
            },
            {
                "id": "stage2",
                "name": "Stage 2",
                "type": "development",
                "tasks": [{"id": "task2", "name": "Task 2", "duration_hours": 8}],
            },
        ],
        "settings": {"parallel_execution": False, "require_approvals": True},
    }


@pytest.fixture
def sample_user_context():
    """Sample user context for tests"""
    return {
        "user_id": "test_user_001",
        "email": "test@example.com",
        "preferences": {"timezone": "UTC", "notifications": True},
    }


@pytest.fixture
def sample_timestamps():
    """Sample timestamps for testing"""
    now = datetime.now()
    return {
        "now": now.isoformat(),
        "yesterday": (now - timedelta(days=1)).isoformat(),
        "last_week": (now - timedelta(weeks=1)).isoformat(),
        "last_month": (now - timedelta(days=30)).isoformat(),
    }


# ========== Mock Fixtures ==========


@pytest.fixture
def mock_agent_context():
    """
    Mock agent context for testing tools.
    Simulates the agent environment without full initialization.
    """

    class MockAgent:
        def __init__(self):
            self.number = 0
            self.agent_name = "TestAgent0"
            self.config = MockConfig()
            self.history = []

        def read_prompt(self, name, **kwargs):
            return f"Prompt: {name}"

    class MockConfig:
        def __init__(self):
            self.profile = "default"
            self.memory_subdir = "test"

    return MockAgent()


@pytest.fixture
def mock_tool_args():
    """Sample tool arguments"""
    return {"action": "create", "name": "Test Item", "options": {"key": "value"}}


# ========== Cleanup Fixtures ==========


@pytest.fixture(autouse=False)
def clean_test_artifacts(tmp_path):
    """
    Clean up test artifacts after test.
    Use with autouse=True on specific test classes if needed.
    """
    yield
    # Cleanup code here if needed
    import shutil

    for item in tmp_path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
