"""
Integration tests for Workflow API endpoints.
Tests WorkflowDashboard, WorkflowEngineApi, and WorkflowTrainingApi handlers.
"""

import os

# Add parent directory to path
import sys
import threading
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockRequest:
    """Mock request object for API handler testing"""

    def __init__(self):
        self.headers = {}
        self.cookies = {}
        self.query_params = {}


class MockFlaskApp:
    """Mock Flask app for API handler testing"""

    def __init__(self):
        self.config = {}
        self.debug = False


@pytest.fixture
def mock_flask_app():
    """Create a mock Flask app"""
    return MockFlaskApp()


@pytest.fixture
def mock_thread_lock():
    """Create a thread lock for API handlers"""
    return threading.Lock()


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path"""
    return str(tmp_path / "test_api_workflow.db")


@pytest.fixture
def mock_files_get_abs_path(temp_db_path):
    """Mock files.get_abs_path to use temp database"""
    with patch('python.helpers.files.get_abs_path') as mock:
        mock.return_value = temp_db_path
        yield mock


class TestWorkflowDashboardApi:
    """Tests for WorkflowDashboard API endpoint"""

    @pytest.mark.asyncio
    async def test_dashboard_empty_database(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test dashboard with empty database"""
        from python.api.workflow_dashboard import WorkflowDashboard

        handler = WorkflowDashboard(mock_flask_app, mock_thread_lock)
        result = await handler.process({}, MockRequest())

        assert result['success'] is True
        assert 'stats' in result
        assert result['stats']['total_workflows'] == 0
        assert result['stats']['total_executions'] == 0
        assert result['stats']['total_skills'] == 0
        assert result['stats']['total_learning_paths'] == 0
        assert result['recent_executions'] == []
        assert result['top_skills'] == []
        assert result['workflows'] == []
        assert result['learning_paths'] == []

    @pytest.mark.asyncio
    async def test_dashboard_with_data(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test dashboard with populated data"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_dashboard import WorkflowDashboard

        # Pre-populate data
        manager = WorkflowEngineManager(temp_db_path)
        manager.create_workflow(
            name="Test Workflow",
            stages=[{"id": "s1", "name": "Stage 1"}]
        )
        manager.register_skill("test_skill", "Test Skill", "technical")
        manager.create_learning_path("test_path", "Test Path", "developer")

        handler = WorkflowDashboard(mock_flask_app, mock_thread_lock)
        result = await handler.process({}, MockRequest())

        assert result['success'] is True
        assert result['stats']['total_workflows'] == 1
        assert result['stats']['total_skills'] == 1
        assert result['stats']['total_learning_paths'] == 1
        assert len(result['workflows']) == 1
        assert len(result['learning_paths']) == 1

    @pytest.mark.asyncio
    async def test_dashboard_with_executions(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test dashboard shows recent executions"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_dashboard import WorkflowDashboard

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(
            name="Execution Test",
            stages=[{"id": "s1", "name": "Stage 1"}]
        )

        # Create executions
        for _i in range(7):
            manager.start_workflow(workflow_id=wf['workflow_id'])

        handler = WorkflowDashboard(mock_flask_app, mock_thread_lock)
        result = await handler.process({}, MockRequest())

        assert result['success'] is True
        assert result['stats']['total_executions'] == 7
        # Should only return 5 recent
        assert len(result['recent_executions']) == 5


class TestWorkflowEngineApi:
    """Tests for WorkflowEngineApi endpoint"""

    @pytest.mark.asyncio
    async def test_list_workflows_empty(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test listing workflows on empty database"""
        from python.api.workflow_engine_api import WorkflowEngineApi

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({"action": "list_workflows"}, MockRequest())

        assert result['success'] is True
        assert result['workflows'] == []

    @pytest.mark.asyncio
    async def test_list_workflows_with_data(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test listing workflows with data"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.create_workflow(name="WF1", stages=[{"id": "s1", "name": "S1"}])
        manager.create_workflow(name="WF2", stages=[{"id": "s1", "name": "S1"}])

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({"action": "list_workflows"}, MockRequest())

        assert result['success'] is True
        assert len(result['workflows']) == 2

    @pytest.mark.asyncio
    async def test_get_workflow_by_id(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test getting workflow by ID"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(
            name="Get By ID",
            stages=[{"id": "design", "name": "Design"}],
            description="Test workflow"
        )

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_workflow",
            "workflow_id": wf['workflow_id']
        }, MockRequest())

        assert result['success'] is True
        assert result['workflow']['name'] == "Get By ID"
        assert result['workflow']['description'] == "Test workflow"

    @pytest.mark.asyncio
    async def test_get_workflow_by_name(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test getting workflow by name"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.create_workflow(name="Named Workflow", stages=[{"id": "s1", "name": "S1"}])

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_workflow",
            "name": "Named Workflow"
        }, MockRequest())

        assert result['success'] is True
        assert result['workflow']['name'] == "Named Workflow"

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test getting non-existent workflow"""
        from python.api.workflow_engine_api import WorkflowEngineApi

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_workflow",
            "workflow_id": 999
        }, MockRequest())

        assert result['success'] is False
        assert "not found" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_visualize_workflow(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test workflow visualization"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(
            name="Visual Workflow",
            stages=[
                {"id": "design", "name": "Design"},
                {"id": "build", "name": "Build"}
            ]
        )

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "visualize_workflow",
            "workflow_id": wf['workflow_id']
        }, MockRequest())

        assert result['success'] is True
        assert 'diagram' in result
        assert "```mermaid" in result['diagram']
        assert "flowchart" in result['diagram']
        assert "Design" in result['diagram']
        assert "Build" in result['diagram']

    @pytest.mark.asyncio
    async def test_visualize_workflow_with_execution(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test workflow visualization with execution status"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(
            name="Exec Visual",
            stages=[
                {"id": "s1", "name": "Stage 1"},
                {"id": "s2", "name": "Stage 2"}
            ]
        )
        exec_result = manager.start_workflow(workflow_id=wf['workflow_id'])

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "visualize_workflow",
            "workflow_id": wf['workflow_id'],
            "execution_id": exec_result['execution_id']
        }, MockRequest())

        assert result['success'] is True
        assert 'diagram' in result

    @pytest.mark.asyncio
    async def test_visualize_workflow_not_found(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test visualizing non-existent workflow"""
        from python.api.workflow_engine_api import WorkflowEngineApi

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "visualize_workflow",
            "workflow_id": 999
        }, MockRequest())

        assert result['success'] is False
        assert "not found" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_list_executions(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test listing executions"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(name="Exec List", stages=[{"id": "s1", "name": "S1"}])
        manager.start_workflow(workflow_id=wf['workflow_id'])
        manager.start_workflow(workflow_id=wf['workflow_id'])

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "list_executions",
            "workflow_id": wf['workflow_id']
        }, MockRequest())

        assert result['success'] is True
        assert len(result['executions']) == 2

    @pytest.mark.asyncio
    async def test_get_status(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test getting execution status"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(
            name="Status Test",
            stages=[{"id": "s1", "name": "S1"}, {"id": "s2", "name": "S2"}]
        )
        exec_result = manager.start_workflow(workflow_id=wf['workflow_id'])

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_status",
            "execution_id": exec_result['execution_id']
        }, MockRequest())

        assert result['success'] is True
        assert 'execution' in result
        assert 'status' in result
        assert result['status']['current_stage'] == "s1"
        assert result['status']['progress']['stages_total'] == 2

    @pytest.mark.asyncio
    async def test_get_status_missing_id(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test get_status without execution_id"""
        from python.api.workflow_engine_api import WorkflowEngineApi

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_status"
        }, MockRequest())

        assert result['success'] is False
        assert "required" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_visualize_gantt(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test Gantt chart visualization"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(
            name="Gantt Test",
            stages=[
                {"id": "phase1", "name": "Phase 1", "duration_days": 7},
                {"id": "phase2", "name": "Phase 2", "duration_days": 14}
            ]
        )

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "visualize_gantt",
            "workflow_id": wf['workflow_id']
        }, MockRequest())

        assert result['success'] is True
        assert 'diagram' in result
        assert "gantt" in result['diagram']
        assert "Phase 1" in result['diagram']

    @pytest.mark.asyncio
    async def test_visualize_tasks(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test task diagram visualization"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(
            name="Task Visual",
            stages=[{
                "id": "dev",
                "name": "Development",
                "tasks": [
                    {"id": "code", "name": "Write Code", "dependencies": []},
                    {"id": "test", "name": "Write Tests", "dependencies": ["code"]}
                ]
            }]
        )

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "visualize_tasks",
            "workflow_id": wf['workflow_id'],
            "stage_id": "dev"
        }, MockRequest())

        assert result['success'] is True
        assert 'diagram' in result
        assert "Write Code" in result['diagram']
        assert "Write Tests" in result['diagram']

    @pytest.mark.asyncio
    async def test_visualize_tasks_stage_not_found(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test task visualization with non-existent stage"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        wf = manager.create_workflow(
            name="Stage Not Found",
            stages=[{"id": "s1", "name": "S1"}]
        )

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "visualize_tasks",
            "workflow_id": wf['workflow_id'],
            "stage_id": "nonexistent"
        }, MockRequest())

        assert result['success'] is False
        assert "not found" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_get_dashboard(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test get_dashboard action"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_engine_api import WorkflowEngineApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.create_workflow(name="Dashboard WF", stages=[{"id": "s1", "name": "S1"}])

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_dashboard"
        }, MockRequest())

        assert result['success'] is True
        assert 'dashboard' in result
        assert "WORKFLOW ENGINE DASHBOARD" in result['dashboard']

    @pytest.mark.asyncio
    async def test_unknown_action(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test unknown action returns error"""
        from python.api.workflow_engine_api import WorkflowEngineApi

        handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "nonexistent_action"
        }, MockRequest())

        assert result['success'] is False
        assert "Unknown action" in result['error']


class TestWorkflowTrainingApi:
    """Tests for WorkflowTrainingApi endpoint"""

    @pytest.mark.asyncio
    async def test_list_skills_empty(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test listing skills on empty database"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "list_skills"
        }, MockRequest())

        assert result['success'] is True
        assert result['skills'] == []

    @pytest.mark.asyncio
    async def test_list_skills_with_data(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test listing skills with data"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.register_skill("py", "Python", "technical")
        manager.register_skill("docker", "Docker", "tool")

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "list_skills"
        }, MockRequest())

        assert result['success'] is True
        assert len(result['skills']) == 2

    @pytest.mark.asyncio
    async def test_list_skills_by_category(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test listing skills filtered by category"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.register_skill("s1", "Skill 1", "technical")
        manager.register_skill("s2", "Skill 2", "technical")
        manager.register_skill("s3", "Skill 3", "process")

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "list_skills",
            "category": "technical"
        }, MockRequest())

        assert result['success'] is True
        assert len(result['skills']) == 2

    @pytest.mark.asyncio
    async def test_get_skill(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test getting a specific skill"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.register_skill(
            "python_async",
            "Async Python",
            "technical",
            description="Async programming"
        )

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_skill",
            "skill_id": "python_async"
        }, MockRequest())

        assert result['success'] is True
        assert result['skill']['name'] == "Async Python"
        assert result['skill']['category'] == "technical"

    @pytest.mark.asyncio
    async def test_get_skill_missing_id(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test get_skill without skill_id"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_skill"
        }, MockRequest())

        assert result['success'] is False
        assert "required" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test getting non-existent skill"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_skill",
            "skill_id": "nonexistent"
        }, MockRequest())

        assert result['success'] is False
        assert "not found" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_get_proficiency(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test getting agent proficiency"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.register_skill("s1", "Skill 1", "cat")
        manager.track_skill_usage("agent_0", "s1", success=True)

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_proficiency"
        }, MockRequest())

        assert result['success'] is True
        assert 'proficiency' in result

    @pytest.mark.asyncio
    async def test_get_proficiency_custom_agent(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test getting proficiency for specific agent"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.register_skill("s1", "Skill 1", "cat")
        manager.track_skill_usage("agent_custom", "s1", success=True)

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_proficiency",
            "agent_id": "agent_custom"
        }, MockRequest())

        assert result['success'] is True
        assert 'proficiency' in result

    @pytest.mark.asyncio
    async def test_list_paths(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test listing learning paths"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.create_learning_path("p1", "Path 1", "developer")
        manager.create_learning_path("p2", "Path 2", "operator")

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "list_paths"
        }, MockRequest())

        assert result['success'] is True
        assert len(result['paths']) == 2

    @pytest.mark.asyncio
    async def test_list_paths_by_role(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test listing paths filtered by target role"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.create_learning_path("p1", "Path 1", "developer")
        manager.create_learning_path("p2", "Path 2", "developer")
        manager.create_learning_path("p3", "Path 3", "operator")

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "list_paths",
            "target_role": "developer"
        }, MockRequest())

        assert result['success'] is True
        assert len(result['paths']) == 2

    @pytest.mark.asyncio
    async def test_get_path(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test getting a specific learning path"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.create_learning_path(
            "py_dev",
            "Python Developer",
            "developer",
            description="Learn Python development",
            modules=[{"module_id": "m1", "name": "Basics"}]
        )

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_path",
            "path_id": "py_dev"
        }, MockRequest())

        assert result['success'] is True
        assert result['path']['name'] == "Python Developer"
        assert len(result['path']['modules']) == 1

    @pytest.mark.asyncio
    async def test_get_path_missing_id(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test get_path without path_id"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_path"
        }, MockRequest())

        assert result['success'] is False
        assert "required" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_get_path_not_found(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test getting non-existent path"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_path",
            "path_id": "nonexistent"
        }, MockRequest())

        assert result['success'] is False
        assert "not found" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_get_progress(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test getting learning progress"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.create_learning_path("test_path", "Test Path", "tester")

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_progress",
            "path_id": "test_path"
        }, MockRequest())

        assert result['success'] is True
        assert 'progress' in result

    @pytest.mark.asyncio
    async def test_get_progress_missing_path_id(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test get_progress without path_id"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_progress"
        }, MockRequest())

        assert result['success'] is False
        assert "required" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_get_module(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test getting a training module (currently returns None for nonexistent)"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_module",
            "module_id": "nonexistent"
        }, MockRequest())

        assert result['success'] is False
        assert "not found" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_get_module_missing_id(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test get_module without module_id"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "get_module"
        }, MockRequest())

        assert result['success'] is False
        assert "required" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_skill_report(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test generating skill report with chart"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.register_skill("s1", "Skill 1", "technical")
        manager.track_skill_usage("agent_0", "s1", success=True)

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "skill_report"
        }, MockRequest())

        assert result['success'] is True
        assert 'skills' in result
        assert 'chart' in result
        assert "Skill Proficiency" in result['chart']

    @pytest.mark.asyncio
    async def test_training_dashboard(self, mock_files_get_abs_path, temp_db_path, mock_flask_app, mock_thread_lock):
        """Test generating training dashboard"""
        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
        from python.api.workflow_training_api import WorkflowTrainingApi

        manager = WorkflowEngineManager(temp_db_path)
        manager.register_skill("s1", "Skill 1", "technical")
        manager.create_learning_path("p1", "Path 1", "developer")

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "training_dashboard"
        }, MockRequest())

        assert result['success'] is True
        assert 'dashboard' in result
        assert "WORKFLOW ENGINE DASHBOARD" in result['dashboard']

    @pytest.mark.asyncio
    async def test_unknown_action(self, mock_files_get_abs_path, mock_flask_app, mock_thread_lock):
        """Test unknown action returns error"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
        result = await handler.process({
            "action": "nonexistent_action"
        }, MockRequest())

        assert result['success'] is False
        assert "Unknown action" in result['error']


class TestApiErrorHandling:
    """Tests for API error handling"""

    @pytest.mark.asyncio
    async def test_dashboard_exception_handling(self, mock_flask_app, mock_thread_lock):
        """Test dashboard handles exceptions gracefully"""
        from python.api.workflow_dashboard import WorkflowDashboard

        # Mock to raise exception
        with patch('python.helpers.files.get_abs_path') as mock:
            mock.side_effect = Exception("Database error")

            handler = WorkflowDashboard(mock_flask_app, mock_thread_lock)
            result = await handler.process({}, MockRequest())

            # Should return error structure, not raise
            assert result['success'] is False
            assert 'error' in result
            assert result['stats']['total_workflows'] == 0

    @pytest.mark.asyncio
    async def test_engine_api_exception_handling(self, mock_flask_app, mock_thread_lock):
        """Test engine API handles exceptions gracefully"""
        from python.api.workflow_engine_api import WorkflowEngineApi

        with patch('python.helpers.files.get_abs_path') as mock:
            mock.side_effect = Exception("Database connection failed")

            handler = WorkflowEngineApi(mock_flask_app, mock_thread_lock)
            result = await handler.process({"action": "list_workflows"}, MockRequest())

            assert result['success'] is False
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_training_api_exception_handling(self, mock_flask_app, mock_thread_lock):
        """Test training API handles exceptions gracefully"""
        from python.api.workflow_training_api import WorkflowTrainingApi

        with patch('python.helpers.files.get_abs_path') as mock:
            mock.side_effect = Exception("Connection refused")

            handler = WorkflowTrainingApi(mock_flask_app, mock_thread_lock)
            result = await handler.process({"action": "list_skills"}, MockRequest())

            assert result['success'] is False
            assert 'error' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
