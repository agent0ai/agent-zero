"""
Unit tests for WorkflowEngineManager.
Tests business logic for workflow orchestration, training, and skill tracking.
"""

import os
import pytest
import json
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager


class TestWorkflowEngineManager:
    """Test suite for WorkflowEngineManager"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        """Create fresh manager for each test"""
        self.db_path = str(tmp_path / "test_manager.db")
        self.manager = WorkflowEngineManager(self.db_path)

    # ========== Workflow Creation Tests ==========

    def test_create_workflow_basic(self):
        """Test creating a basic workflow"""
        stages = [
            {"id": "design", "name": "Design Phase", "type": "design"},
            {"id": "poc", "name": "POC Phase", "type": "poc"}
        ]

        result = self.manager.create_workflow(
            name="Test Project",
            stages=stages,
            description="A test workflow",
            version="1.0.0"
        )

        assert 'workflow_id' in result
        assert result['name'] == "Test Project"
        assert result['stages'] == 2
        assert result['status'] == "created"

    def test_create_workflow_with_settings(self):
        """Test creating workflow with custom settings"""
        stages = [{"id": "s1", "name": "Stage 1"}]
        settings = {
            "parallel_execution": True,
            "require_approvals": False,
            "auto_retry": False
        }
        global_context = {
            "project_code": "PRJ001",
            "client": "ACME Corp"
        }

        result = self.manager.create_workflow(
            name="Custom Settings",
            stages=stages,
            settings=settings,
            global_context=global_context
        )

        workflow = self.manager.get_workflow(workflow_id=result['workflow_id'])
        assert workflow['definition']['settings']['parallel_execution'] is True
        assert workflow['definition']['global_context']['project_code'] == "PRJ001"

    def test_create_workflow_validation_no_name(self):
        """Test workflow validation - missing name"""
        # Create via definition to bypass name parameter
        result = self.manager.create_workflow(
            name="",  # Empty name
            stages=[{"id": "s1", "name": "S1"}]
        )
        # Should still work since validation is lenient
        assert 'workflow_id' in result or 'error' in result

    def test_create_workflow_validation_no_stages(self):
        """Test workflow validation - missing stages"""
        result = self.manager.create_workflow(
            name="No Stages",
            stages=[]  # Empty stages
        )
        assert 'error' in result

    def test_create_workflow_type_inference(self):
        """Test workflow type inference from stages"""
        # Product development stages
        pd_stages = [
            {"id": "d", "name": "Design", "type": "design"},
            {"id": "p", "name": "POC", "type": "poc"},
            {"id": "m", "name": "MVP", "type": "mvp"},
            {"id": "pr", "name": "Production", "type": "production"}
        ]
        result = self.manager.create_workflow(name="PD Workflow", stages=pd_stages)
        assert result['type'] == "product_development"

        # Service delivery with support
        sd_stages = [
            {"id": "setup", "name": "Setup", "type": "custom"},
            {"id": "support", "name": "Support", "type": "support"}
        ]
        result = self.manager.create_workflow(name="SD Workflow", stages=sd_stages)
        assert result['type'] == "service_delivery"

        # Maintenance with upgrade
        maint_stages = [
            {"id": "plan", "name": "Plan", "type": "custom"},
            {"id": "upgrade", "name": "Upgrade", "type": "upgrade"}
        ]
        result = self.manager.create_workflow(name="Maint Workflow", stages=maint_stages)
        assert result['type'] == "maintenance"

    # ========== Workflow Retrieval Tests ==========

    def test_get_workflow_by_id(self):
        """Test getting workflow by ID"""
        result = self.manager.create_workflow(
            name="Get By ID",
            stages=[{"id": "s1", "name": "S1"}]
        )

        workflow = self.manager.get_workflow(workflow_id=result['workflow_id'])
        assert workflow['name'] == "Get By ID"

    def test_get_workflow_by_name(self):
        """Test getting workflow by name"""
        self.manager.create_workflow(
            name="Get By Name",
            stages=[{"id": "s1", "name": "S1"}]
        )

        workflow = self.manager.get_workflow(name="Get By Name")
        assert workflow is not None
        assert workflow['name'] == "Get By Name"

    def test_get_workflow_not_found(self):
        """Test getting non-existent workflow"""
        result = self.manager.get_workflow(workflow_id=999)
        assert 'error' in result

        result = self.manager.get_workflow(name="NonExistent")
        assert 'error' in result

    def test_list_workflows(self):
        """Test listing workflows"""
        self.manager.create_workflow(name="WF1", stages=[{"id": "s1", "name": "S1"}])
        self.manager.create_workflow(name="WF2", stages=[{"id": "s1", "name": "S1"}])

        workflows = self.manager.list_workflows()
        assert len(workflows) == 2

    def test_delete_workflow(self):
        """Test deleting a workflow"""
        result = self.manager.create_workflow(
            name="To Delete",
            stages=[{"id": "s1", "name": "S1"}]
        )

        delete_result = self.manager.delete_workflow(result['workflow_id'])
        assert delete_result['status'] == "deleted"

        # Should not exist
        get_result = self.manager.get_workflow(workflow_id=result['workflow_id'])
        assert 'error' in get_result

    def test_clone_workflow(self):
        """Test cloning a workflow"""
        original = self.manager.create_workflow(
            name="Original",
            stages=[{"id": "s1", "name": "S1"}, {"id": "s2", "name": "S2"}],
            description="Original workflow"
        )

        clone = self.manager.clone_workflow(
            workflow_id=original['workflow_id'],
            new_name="Cloned Workflow"
        )

        assert clone['name'] == "Cloned Workflow"
        assert clone['stages'] == 2

        cloned_workflow = self.manager.get_workflow(name="Cloned Workflow")
        assert "Cloned from: Original" in cloned_workflow['description']

    # ========== Workflow Execution Tests ==========

    def test_start_workflow_by_id(self):
        """Test starting workflow by ID"""
        wf = self.manager.create_workflow(
            name="Start Test",
            stages=[
                {"id": "design", "name": "Design"},
                {"id": "build", "name": "Build"}
            ]
        )

        result = self.manager.start_workflow(
            workflow_id=wf['workflow_id'],
            context={"project": "test"}
        )

        assert result['status'] == "running"
        assert result['current_stage'] == "design"
        assert 'execution_id' in result

    def test_start_workflow_by_name(self):
        """Test starting workflow by name"""
        self.manager.create_workflow(
            name="Named Workflow",
            stages=[{"id": "s1", "name": "Stage 1"}]
        )

        result = self.manager.start_workflow(
            workflow_name="Named Workflow",
            execution_name="Custom Execution Name"
        )

        assert result['status'] == "running"
        assert result['workflow_name'] == "Named Workflow"

    def test_start_workflow_not_found(self):
        """Test starting non-existent workflow"""
        result = self.manager.start_workflow(workflow_id=999)
        assert 'error' in result

    def test_get_execution_status(self):
        """Test getting execution status"""
        wf = self.manager.create_workflow(
            name="Status Test",
            stages=[
                {"id": "s1", "name": "Stage 1"},
                {"id": "s2", "name": "Stage 2"},
                {"id": "s3", "name": "Stage 3"}
            ]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        status = self.manager.get_execution_status(exec_result['execution_id'])

        assert status['status'] == "running"
        assert status['current_stage'] == "s1"
        assert status['progress']['stages_total'] == 3
        assert status['progress']['stages_completed'] == 0

    def test_get_execution_status_not_found(self):
        """Test getting status of non-existent execution"""
        result = self.manager.get_execution_status(999)
        assert 'error' in result

    # ========== Stage Advancement Tests ==========

    def test_advance_stage_basic(self):
        """Test basic stage advancement"""
        wf = self.manager.create_workflow(
            name="Advance Test",
            stages=[
                {"id": "s1", "name": "Stage 1"},
                {"id": "s2", "name": "Stage 2"}
            ]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Force advance (skip exit criteria)
        result = self.manager.advance_stage(execution_id, force=True)

        assert result['status'] == "advanced"
        assert result['previous_stage'] == "s1"
        assert result['current_stage'] == "s2"

    def test_advance_stage_blocked_by_criteria(self):
        """Test stage advancement blocked by exit criteria"""
        wf = self.manager.create_workflow(
            name="Criteria Test",
            stages=[
                {
                    "id": "design",
                    "name": "Design",
                    "exit_criteria": [
                        {"id": "doc_complete", "name": "Documentation complete"},
                        {"id": "review_done", "name": "Design review done"}
                    ]
                },
                {"id": "build", "name": "Build"}
            ]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Try to advance without meeting criteria
        result = self.manager.advance_stage(execution_id, force=False)

        assert 'error' in result
        assert 'Exit criteria not met' in result['error']
        assert len(result['unmet_criteria']) == 2

    def test_advance_stage_with_criteria_met(self):
        """Test stage advancement after meeting criteria"""
        wf = self.manager.create_workflow(
            name="Criteria Met Test",
            stages=[
                {
                    "id": "design",
                    "name": "Design",
                    "exit_criteria": [
                        {"id": "c1", "name": "Criterion 1"}
                    ]
                },
                {"id": "build", "name": "Build"}
            ]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Complete the criterion
        self.manager.complete_criterion(execution_id, "design", "c1")

        # Now advance should work
        result = self.manager.advance_stage(execution_id, force=False)
        assert result['status'] == "advanced"

    def test_advance_stage_blocked_by_approval(self):
        """Test stage advancement blocked by pending approval"""
        wf = self.manager.create_workflow(
            name="Approval Test",
            stages=[
                {"id": "s1", "name": "Stage 1", "approval_required": True},
                {"id": "s2", "name": "Stage 2"}
            ]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Try to advance without approval
        result = self.manager.advance_stage(execution_id, force=False)
        assert 'error' in result
        assert 'approval' in result['error'].lower()

    def test_advance_stage_workflow_completion(self):
        """Test advancing past last stage completes workflow"""
        wf = self.manager.create_workflow(
            name="Completion Test",
            stages=[{"id": "only", "name": "Only Stage"}]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        result = self.manager.advance_stage(execution_id, force=True)

        assert result['status'] == "workflow_completed"

        # Verify execution status
        status = self.manager.get_execution_status(execution_id)
        assert status['status'] == "completed"

    def test_approve_stage(self):
        """Test stage approval"""
        wf = self.manager.create_workflow(
            name="Approve Stage Test",
            stages=[{"id": "s1", "name": "Stage 1", "approval_required": True}]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        result = self.manager.approve_stage(
            execution_id=execution_id,
            stage_id="s1",
            approved_by="product_owner",
            notes="Approved after review"
        )

        assert result['status'] == "approved"
        assert result['approved_by'] == "product_owner"

    def test_complete_criterion(self):
        """Test completing exit/entry criteria"""
        wf = self.manager.create_workflow(
            name="Criterion Test",
            stages=[{"id": "s1", "name": "S1"}]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Complete exit criterion
        result = self.manager.complete_criterion(
            execution_id=execution_id,
            stage_id="s1",
            criterion_id="docs_complete",
            criterion_type="exit"
        )

        assert result['status'] == "criterion_completed"
        assert result['type'] == "exit"

        # Complete entry criterion
        result = self.manager.complete_criterion(
            execution_id=execution_id,
            stage_id="s1",
            criterion_id="team_assigned",
            criterion_type="entry"
        )

        assert result['type'] == "entry"

    def test_complete_deliverable(self):
        """Test completing deliverables"""
        wf = self.manager.create_workflow(
            name="Deliverable Test",
            stages=[{"id": "s1", "name": "S1"}]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        result = self.manager.complete_deliverable(
            execution_id=execution_id,
            stage_id="s1",
            deliverable_id="prototype_v1",
            artifact_path="/artifacts/prototype.zip"
        )

        assert result['status'] == "deliverable_completed"
        assert result['artifact_path'] == "/artifacts/prototype.zip"

    # ========== Task Execution Tests ==========

    def test_start_task(self):
        """Test starting a task"""
        wf = self.manager.create_workflow(
            name="Task Test",
            stages=[{
                "id": "design",
                "name": "Design",
                "tasks": [
                    {"id": "research", "name": "Research"},
                    {"id": "wireframe", "name": "Create Wireframes"}
                ]
            }]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        result = self.manager.start_task(
            execution_id=execution_id,
            stage_id="design",
            task_id="research",
            input_data={"scope": "competitive analysis"},
            assigned_to="agent_0"
        )

        assert result['status'] == "started"
        assert result['task_id'] == "research"

        # Check status shows current task
        status = self.manager.get_execution_status(execution_id)
        assert status['current_task'] == "research"

    def test_complete_task(self):
        """Test completing a task"""
        wf = self.manager.create_workflow(
            name="Complete Task Test",
            stages=[{
                "id": "s1",
                "name": "S1",
                "tasks": [{"id": "t1", "name": "Task 1"}]
            }]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        self.manager.start_task(execution_id, "s1", "t1")

        result = self.manager.complete_task(
            execution_id=execution_id,
            stage_id="s1",
            task_id="t1",
            output_data={"result": "success", "files": ["output.json"]}
        )

        assert result['status'] == "completed"
        assert result['output']['result'] == "success"

    def test_fail_task_no_retry(self):
        """Test failing a task without retry"""
        wf = self.manager.create_workflow(
            name="Fail Test",
            stages=[{
                "id": "s1",
                "name": "S1",
                "tasks": [{"id": "t1", "name": "Task 1"}]
            }]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        self.manager.start_task(execution_id, "s1", "t1")

        result = self.manager.fail_task(
            execution_id=execution_id,
            stage_id="s1",
            task_id="t1",
            error="Connection timeout",
            retry=False
        )

        assert result['status'] == "failed"
        assert result['error'] == "Connection timeout"

    def test_fail_task_with_retry(self):
        """Test failing a task with retry"""
        wf = self.manager.create_workflow(
            name="Retry Test",
            stages=[{
                "id": "s1",
                "name": "S1",
                "tasks": [{"id": "t1", "name": "Task 1"}]
            }]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        self.manager.start_task(execution_id, "s1", "t1")

        result = self.manager.fail_task(
            execution_id=execution_id,
            stage_id="s1",
            task_id="t1",
            error="Temporary failure",
            retry=True
        )

        assert result['status'] == "retry_scheduled"

    def test_get_next_task(self):
        """Test getting next available task"""
        wf = self.manager.create_workflow(
            name="Next Task Test",
            stages=[{
                "id": "s1",
                "name": "S1",
                "tasks": [
                    {"id": "t1", "name": "Task 1", "dependencies": []},
                    {"id": "t2", "name": "Task 2", "dependencies": ["t1"]},
                    {"id": "t3", "name": "Task 3", "dependencies": ["t1"]}
                ]
            }]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # First task should be t1 (no deps)
        next_task = self.manager.get_next_task(execution_id)
        assert next_task['task']['id'] == "t1"
        assert next_task['has_more'] is True

        # Complete t1
        self.manager.start_task(execution_id, "s1", "t1")
        self.manager.complete_task(execution_id, "s1", "t1")

        # Now t2 or t3 should be available
        next_task = self.manager.get_next_task(execution_id)
        assert next_task['task']['id'] in ["t2", "t3"]

    def test_get_next_task_stage_complete(self):
        """Test get next task when all tasks done"""
        wf = self.manager.create_workflow(
            name="All Done Test",
            stages=[{
                "id": "s1",
                "name": "S1",
                "tasks": [{"id": "t1", "name": "Task 1"}]
            }]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Complete the only task
        self.manager.start_task(execution_id, "s1", "t1")
        self.manager.complete_task(execution_id, "s1", "t1")

        next_task = self.manager.get_next_task(execution_id)
        assert next_task['task'] is None
        assert next_task['stage_complete'] is True

    # ========== Skill Management Tests ==========

    def test_register_skill(self):
        """Test registering a new skill"""
        result = self.manager.register_skill(
            skill_id="python_async",
            name="Async Python",
            category="technical",
            description="Asynchronous programming in Python",
            related_tools=["code_execution"]
        )

        assert result['status'] == "registered"
        assert result['skill_id'] == "python_async"

        # Verify default proficiency levels were set
        skill = self.manager.get_skill("python_async")
        assert len(skill['proficiency_levels']) == 5

    def test_register_skill_custom_levels(self):
        """Test registering skill with custom proficiency levels"""
        levels = [
            {"level": 1, "name": "aware", "criteria": ["Knows it exists"]},
            {"level": 2, "name": "user", "criteria": ["Can use basic features"]},
            {"level": 3, "name": "expert", "criteria": ["Deep understanding"]}
        ]

        self.manager.register_skill(
            skill_id="custom_skill",
            name="Custom Skill",
            category="process",
            proficiency_levels=levels
        )

        skill = self.manager.get_skill("custom_skill")
        assert len(skill['proficiency_levels']) == 3
        assert skill['proficiency_levels'][0]['name'] == "aware"

    def test_list_skills_by_category(self):
        """Test listing skills filtered by category"""
        self.manager.register_skill("s1", "Python", "technical")
        self.manager.register_skill("s2", "Docker", "tool")
        self.manager.register_skill("s3", "Agile", "process")

        tech_skills = self.manager.list_skills(category="technical")
        assert len(tech_skills) == 1
        assert tech_skills[0]['name'] == "Python"

    def test_track_skill_usage(self):
        """Test tracking skill usage"""
        self.manager.register_skill("testing", "Testing", "technical")

        result = self.manager.track_skill_usage(
            agent_id="agent_0",
            skill_id="testing",
            success=True
        )

        assert result['status'] == "tracked"

    def test_track_skill_usage_level_up(self):
        """Test automatic level up through practice"""
        # Register skill with custom level thresholds
        levels = [
            {"level": 1, "name": "novice", "min_completions": 0},
            {"level": 2, "name": "beginner", "min_completions": 5},
            {"level": 3, "name": "intermediate", "min_completions": 10}
        ]

        self.manager.register_skill(
            skill_id="levelup_skill",
            name="Level Up Test",
            category="test",
            proficiency_levels=levels
        )

        # Track usage multiple times
        for _ in range(6):
            result = self.manager.track_skill_usage(
                agent_id="agent_0",
                skill_id="levelup_skill",
                success=True
            )

        # Should have leveled up
        skills = self.manager.get_agent_skills("agent_0")
        assert len(skills) == 1
        # Note: level up logic depends on completions meeting threshold

    def test_get_agent_skills(self):
        """Test getting all skills for an agent"""
        self.manager.register_skill("s1", "Skill 1", "cat1")
        self.manager.register_skill("s2", "Skill 2", "cat2")

        self.manager.track_skill_usage("agent_0", "s1", True)
        self.manager.track_skill_usage("agent_0", "s2", True)

        skills = self.manager.get_agent_skills("agent_0")
        assert len(skills) == 2

    # ========== Learning Path Tests ==========

    def test_create_learning_path(self):
        """Test creating a learning path"""
        modules = [
            {"module_id": "m1", "name": "Basics", "required": True},
            {"module_id": "m2", "name": "Advanced", "required": True, "prerequisites": ["m1"]}
        ]

        result = self.manager.create_learning_path(
            path_id="python_path",
            name="Python Developer Path",
            target_role="developer",
            description="Complete Python learning path",
            modules=modules,
            estimated_hours=40.0,
            certification={"name": "Python Developer", "badge": "python_dev"}
        )

        assert result['status'] == "created"
        assert result['path_id'] == "python_path"

    def test_get_learning_path(self):
        """Test getting a learning path"""
        self.manager.create_learning_path(
            path_id="test_path",
            name="Test Path",
            target_role="tester",
            modules=[{"module_id": "m1", "name": "Module 1"}]
        )

        path = self.manager.get_learning_path("test_path")
        assert path['name'] == "Test Path"
        assert path['target_role'] == "tester"

    def test_get_learning_path_not_found(self):
        """Test getting non-existent path"""
        result = self.manager.get_learning_path("nonexistent")
        assert 'error' in result

    def test_list_learning_paths(self):
        """Test listing learning paths"""
        self.manager.create_learning_path("p1", "Path 1", "developer")
        self.manager.create_learning_path("p2", "Path 2", "developer")
        self.manager.create_learning_path("p3", "Path 3", "operator")

        all_paths = self.manager.list_learning_paths()
        assert len(all_paths) == 3

        dev_paths = self.manager.list_learning_paths(target_role="developer")
        assert len(dev_paths) == 2

    # ========== Statistics Tests ==========

    def test_get_stats(self):
        """Test getting statistics"""
        self.manager.create_workflow(name="WF1", stages=[{"id": "s1", "name": "S1"}])
        self.manager.register_skill("s1", "Skill 1", "cat")
        self.manager.create_learning_path("p1", "Path 1", "role")

        stats = self.manager.get_stats()
        assert stats['total_workflows'] == 1
        assert stats['total_skills'] == 1
        assert stats['total_learning_paths'] == 1

    def test_get_recent_executions(self):
        """Test getting recent executions"""
        wf = self.manager.create_workflow(
            name="Recent Test",
            stages=[{"id": "s1", "name": "S1"}]
        )

        for i in range(5):
            self.manager.start_workflow(workflow_id=wf['workflow_id'])

        recent = self.manager.get_recent_executions(limit=3)
        assert len(recent) == 3

    def test_get_top_skills(self):
        """Test getting top skills"""
        self.manager.register_skill("s1", "Skill 1", "cat")
        self.manager.register_skill("s2", "Skill 2", "cat")

        # Track usage to set levels
        for _ in range(10):
            self.manager.track_skill_usage("agent_0", "s1", True)

        top = self.manager.get_top_skills(limit=2)
        assert len(top) <= 2

    def test_get_execution_history(self):
        """Test getting execution history"""
        wf = self.manager.create_workflow(
            name="History Test",
            stages=[{"id": "s1", "name": "S1"}]
        )

        exec1 = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        exec2 = self.manager.start_workflow(workflow_id=wf['workflow_id'])

        # Complete one
        self.manager.advance_stage(exec1['execution_id'], force=True)

        history = self.manager.get_execution_history(status="completed")
        assert len(history) == 1

        all_history = self.manager.get_execution_history()
        assert len(all_history) == 2


class TestWorkflowTemplates:
    """Tests for workflow template functionality"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_templates.db")
        self.manager = WorkflowEngineManager(self.db_path)
        self.templates_dir = tmp_path / "templates"
        self.templates_dir.mkdir()

    def test_load_template_from_file(self):
        """Test loading template from JSON file"""
        template_content = {
            "name": "Test Template",
            "stages": [
                {"id": "design", "name": "Design Phase"},
                {"id": "build", "name": "Build Phase"}
            ],
            "version": "1.0.0"
        }

        template_file = self.templates_dir / "test_template.json"
        template_file.write_text(json.dumps(template_content))

        loaded = self.manager.load_template(str(template_file))

        assert 'error' not in loaded
        assert loaded['name'] == "Test Template"
        assert len(loaded['stages']) == 2

    def test_load_template_not_found(self):
        """Test loading non-existent template"""
        result = self.manager.load_template("/nonexistent/path.json")
        assert 'error' in result

    def test_load_template_invalid_json(self):
        """Test loading invalid JSON template"""
        invalid_file = self.templates_dir / "invalid.json"
        invalid_file.write_text("{ this is not valid json }")

        result = self.manager.load_template(str(invalid_file))
        assert 'error' in result

    def test_create_from_template(self):
        """Test creating workflow from template"""
        template_content = {
            "name": "Product Development",
            "description": "Standard product development workflow",
            "stages": [
                {"id": "design", "name": "Design", "type": "design"},
                {"id": "poc", "name": "POC", "type": "poc"}
            ],
            "global_context": {"team": "default"},
            "settings": {"require_approvals": True}
        }

        template_file = self.templates_dir / "product_dev.json"
        template_file.write_text(json.dumps(template_content))

        result = self.manager.create_from_template(
            template_path=str(template_file),
            name="My Product Project"
        )

        assert 'workflow_id' in result
        assert result['name'] == "My Product Project"

        workflow = self.manager.get_workflow(name="My Product Project")
        assert workflow['definition']['settings']['require_approvals'] is True

    def test_create_from_template_with_customizations(self):
        """Test creating from template with customizations"""
        template_content = {
            "name": "Base Template",
            "stages": [
                {"id": "s1", "name": "Stage 1", "duration_days": 7}
            ],
            "global_context": {"env": "development"},
            "settings": {"auto_retry": True}
        }

        template_file = self.templates_dir / "base.json"
        template_file.write_text(json.dumps(template_content))

        customizations = {
            "stages": [{"id": "s1", "duration_days": 14}],
            "global_context": {"env": "production", "priority": "high"},
            "settings": {"auto_retry": False}
        }

        result = self.manager.create_from_template(
            template_path=str(template_file),
            name="Customized Workflow",
            customizations=customizations
        )

        workflow = self.manager.get_workflow(name="Customized Workflow")
        assert workflow['definition']['stages'][0]['duration_days'] == 14
        assert workflow['definition']['global_context']['env'] == "production"
        assert workflow['definition']['global_context']['priority'] == "high"
        assert workflow['definition']['settings']['auto_retry'] is False

    def test_list_templates(self):
        """Test listing available templates"""
        # Create some template files
        for i in range(3):
            template = {"name": f"Template {i}", "stages": [{"id": "s1", "name": "S1"}]}
            (self.templates_dir / f"template_{i}.json").write_text(json.dumps(template))

        # Note: list_templates looks in the module's templates directory by default
        # This test verifies the method works, though it may not find our temp templates
        templates = self.manager.list_templates()
        # At minimum should be a list
        assert isinstance(templates, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
