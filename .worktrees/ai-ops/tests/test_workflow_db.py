"""
Unit tests for WorkflowEngineDatabase.
Tests CRUD operations for workflows, executions, skills, and learning paths.
"""

import os

# Add parent directory to path
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.custom.workflow_engine.workflow_db import WorkflowEngineDatabase


class TestWorkflowEngineDatabase:
    """Test suite for WorkflowEngineDatabase"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        """Create fresh database for each test"""
        self.db_path = str(tmp_path / "test_workflow.db")
        self.db = WorkflowEngineDatabase(self.db_path)

    # ========== Workflow Definition Tests ==========

    def test_save_and_get_workflow(self):
        """Test saving and retrieving a workflow"""
        definition = {
            "id": "test_workflow",
            "name": "Test Workflow",
            "stages": [
                {"id": "stage_1", "name": "Stage 1", "type": "design"},
                {"id": "stage_2", "name": "Stage 2", "type": "poc"}
            ]
        }

        workflow_id = self.db.save_workflow(
            name="Test Workflow",
            definition=definition,
            version="1.0.0",
            description="A test workflow",
            workflow_type="product_development"
        )

        assert workflow_id > 0, "Should return valid workflow ID"

        # Retrieve by ID
        workflow = self.db.get_workflow(workflow_id=workflow_id)
        assert workflow is not None, "Should retrieve workflow by ID"
        assert workflow['name'] == "Test Workflow"
        assert workflow['version'] == "1.0.0"
        assert len(workflow['definition']['stages']) == 2

        # Retrieve by name
        workflow_by_name = self.db.get_workflow(name="Test Workflow")
        assert workflow_by_name is not None, "Should retrieve workflow by name"
        assert workflow_by_name['workflow_id'] == workflow_id

    def test_save_workflow_upsert(self):
        """Test that saving existing workflow updates it"""
        definition = {"id": "v1", "name": "V1", "stages": []}
        self.db.save_workflow(name="Upsert Test", definition=definition, version="1.0.0")

        # Update with same name
        updated_definition = {"id": "v2", "name": "V2", "stages": []}
        self.db.save_workflow(name="Upsert Test", definition=updated_definition, version="2.0.0")

        workflow = self.db.get_workflow(name="Upsert Test")
        assert workflow['version'] == "2.0.0", "Version should be updated"
        assert workflow['definition']['id'] == "v2", "Definition should be updated"

    def test_list_workflows(self):
        """Test listing workflows with filters"""
        # Create multiple workflows
        self.db.save_workflow(
            name="Product 1",
            definition={"stages": []},
            workflow_type="product_development"
        )
        self.db.save_workflow(
            name="Service 1",
            definition={"stages": []},
            workflow_type="service_delivery"
        )
        self.db.save_workflow(
            name="Template 1",
            definition={"stages": []},
            workflow_type="product_development",
            is_template=True
        )

        # List all
        all_workflows = self.db.list_workflows()
        assert len(all_workflows) == 3, "Should list all workflows"

        # Filter by type
        product_workflows = self.db.list_workflows(workflow_type="product_development")
        assert len(product_workflows) == 2, "Should filter by type"

        # Filter templates only
        templates = self.db.list_workflows(templates_only=True)
        assert len(templates) == 1, "Should filter templates"
        assert templates[0]['name'] == "Template 1"

    def test_delete_workflow(self):
        """Test deleting a workflow"""
        workflow_id = self.db.save_workflow(
            name="To Delete",
            definition={"stages": []}
        )

        assert self.db.delete_workflow(workflow_id), "Should return True on deletion"
        assert self.db.get_workflow(workflow_id=workflow_id) is None, "Workflow should be gone"
        assert not self.db.delete_workflow(999), "Should return False for non-existent"

    def test_get_workflow_not_found(self):
        """Test getting non-existent workflow"""
        assert self.db.get_workflow(workflow_id=999) is None
        assert self.db.get_workflow(name="NonExistent") is None
        assert self.db.get_workflow() is None  # No criteria

    # ========== Execution Tests ==========

    def test_start_and_get_execution(self):
        """Test starting and retrieving an execution"""
        # First create a workflow
        workflow_id = self.db.save_workflow(
            name="Exec Test Workflow",
            definition={"stages": [{"id": "s1", "name": "S1"}]}
        )

        context = {"project": "test_project", "priority": "high"}
        execution_id = self.db.start_execution(
            workflow_id=workflow_id,
            name="Test Run 1",
            context=context
        )

        assert execution_id > 0, "Should return valid execution ID"

        execution = self.db.get_execution(execution_id)
        assert execution is not None, "Should retrieve execution"
        assert execution['workflow_id'] == workflow_id
        assert execution['name'] == "Test Run 1"
        assert execution['status'] == "running"
        assert execution['context']['project'] == "test_project"
        assert execution['started_at'] is not None

    def test_update_execution(self):
        """Test updating execution state"""
        workflow_id = self.db.save_workflow(name="Update Test", definition={"stages": []})
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        # Update status
        self.db.update_execution(
            execution_id=execution_id,
            status="completed",
            current_stage_id="stage_2",
            current_task_id="task_1",
            result="Success"
        )

        execution = self.db.get_execution(execution_id)
        assert execution['status'] == "completed"
        assert execution['current_stage_id'] == "stage_2"
        assert execution['current_task_id'] == "task_1"
        assert execution['completed_at'] is not None

    def test_list_executions(self):
        """Test listing executions with filters"""
        wf_id_1 = self.db.save_workflow(name="WF1", definition={"stages": []})
        wf_id_2 = self.db.save_workflow(name="WF2", definition={"stages": []})

        # Create multiple executions
        exec_1 = self.db.start_execution(workflow_id=wf_id_1)
        self.db.start_execution(workflow_id=wf_id_1)
        self.db.start_execution(workflow_id=wf_id_2)

        # Mark one as completed
        self.db.update_execution(execution_id=exec_1, status="completed")

        # List all
        all_execs = self.db.list_executions()
        assert len(all_execs) == 3

        # Filter by workflow
        wf1_execs = self.db.list_executions(workflow_id=wf_id_1)
        assert len(wf1_execs) == 2

        # Filter by status
        running_execs = self.db.list_executions(status="running")
        assert len(running_execs) == 2

        completed_execs = self.db.list_executions(status="completed")
        assert len(completed_execs) == 1

    def test_get_execution_not_found(self):
        """Test getting non-existent execution"""
        assert self.db.get_execution(999) is None

    # ========== Stage Progress Tests ==========

    def test_update_and_get_stage_progress(self):
        """Test stage progress tracking"""
        workflow_id = self.db.save_workflow(
            name="Stage Progress Test",
            definition={"stages": [{"id": "design", "name": "Design"}]}
        )
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        # Update stage progress
        self.db.update_stage_progress(
            execution_id=execution_id,
            stage_id="design",
            status="in_progress",
            entry_criteria_met=["criteria_1", "criteria_2"],
            notes="Starting design phase"
        )

        # Get single stage progress
        progress = self.db.get_stage_progress(execution_id, stage_id="design")
        assert progress is not None
        assert progress['status'] == "in_progress"
        assert len(progress['entry_criteria_met']) == 2
        assert progress['started_at'] is not None

    def test_stage_progress_completion(self):
        """Test completing a stage"""
        workflow_id = self.db.save_workflow(name="Completion Test", definition={"stages": []})
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        self.db.update_stage_progress(
            execution_id=execution_id,
            stage_id="poc",
            status="in_progress"
        )

        self.db.update_stage_progress(
            execution_id=execution_id,
            stage_id="poc",
            status="completed",
            exit_criteria_met=["demo_ready", "approved"],
            deliverables_completed=["prototype_v1"]
        )

        progress = self.db.get_stage_progress(execution_id, stage_id="poc")
        assert progress['status'] == "completed"
        assert progress['completed_at'] is not None
        assert len(progress['exit_criteria_met']) == 2
        assert "prototype_v1" in progress['deliverables_completed']

    def test_stage_approval(self):
        """Test stage approval tracking"""
        workflow_id = self.db.save_workflow(name="Approval Test", definition={"stages": []})
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        self.db.update_stage_progress(
            execution_id=execution_id,
            stage_id="mvp",
            approval_status="approved",
            approved_by="product_owner",
            notes="Ready for production"
        )

        progress = self.db.get_stage_progress(execution_id, stage_id="mvp")
        assert progress['approval_status'] == "approved"
        assert progress['approved_by'] == "product_owner"
        assert "Ready for production" in progress['notes']

    def test_get_all_stage_progress(self):
        """Test getting all stages for an execution"""
        workflow_id = self.db.save_workflow(name="All Stages", definition={"stages": []})
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        for stage_id in ["design", "poc", "mvp"]:
            self.db.update_stage_progress(
                execution_id=execution_id,
                stage_id=stage_id,
                status="pending"
            )

        all_progress = self.db.get_stage_progress(execution_id)
        assert isinstance(all_progress, list)
        assert len(all_progress) == 3

    # ========== Task Execution Tests ==========

    def test_task_execution_lifecycle(self):
        """Test task execution from pending to completed"""
        workflow_id = self.db.save_workflow(name="Task Test", definition={"stages": []})
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        # Start task
        self.db.update_task_execution(
            execution_id=execution_id,
            stage_id="design",
            task_id="research",
            status="running",
            input_data={"scope": "full"},
            assigned_to="agent_0"
        )

        tasks = self.db.get_task_executions(execution_id, stage_id="design")
        assert len(tasks) == 1
        task = tasks[0]
        assert task['status'] == "running"
        assert task['input_data']['scope'] == "full"
        assert task['started_at'] is not None
        assert task['attempt_count'] == 1

        # Complete task
        self.db.update_task_execution(
            execution_id=execution_id,
            stage_id="design",
            task_id="research",
            status="completed",
            output_data={"findings": ["insight1", "insight2"]}
        )

        tasks = self.db.get_task_executions(execution_id, stage_id="design")
        task = tasks[0]
        assert task['status'] == "completed"
        assert task['completed_at'] is not None
        assert len(task['output_data']['findings']) == 2

    def test_task_failure_and_retry(self):
        """Test task failure and retry tracking"""
        workflow_id = self.db.save_workflow(name="Retry Test", definition={"stages": []})
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        # First attempt - fail
        self.db.update_task_execution(
            execution_id=execution_id,
            stage_id="poc",
            task_id="build",
            status="running"
        )
        self.db.update_task_execution(
            execution_id=execution_id,
            stage_id="poc",
            task_id="build",
            status="failed",
            error="Build error: missing dependency"
        )

        tasks = self.db.get_task_executions(execution_id, stage_id="poc")
        assert tasks[0]['status'] == "failed"
        assert "missing dependency" in tasks[0]['error']

        # Retry - run again
        self.db.update_task_execution(
            execution_id=execution_id,
            stage_id="poc",
            task_id="build",
            status="running"
        )

        tasks = self.db.get_task_executions(execution_id, stage_id="poc")
        assert tasks[0]['attempt_count'] == 2

    def test_get_all_task_executions(self):
        """Test getting all tasks across stages"""
        workflow_id = self.db.save_workflow(name="All Tasks", definition={"stages": []})
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        # Tasks in multiple stages
        for stage_id, task_id in [("design", "t1"), ("design", "t2"), ("poc", "t3")]:
            self.db.update_task_execution(
                execution_id=execution_id,
                stage_id=stage_id,
                task_id=task_id,
                status="pending"
            )

        all_tasks = self.db.get_task_executions(execution_id)
        assert len(all_tasks) == 3

        design_tasks = self.db.get_task_executions(execution_id, stage_id="design")
        assert len(design_tasks) == 2

    # ========== Skill Tests ==========

    def test_save_and_get_skill(self):
        """Test saving and retrieving a skill"""
        self.db.save_skill(
            skill_id="python_basics",
            name="Python Fundamentals",
            category="technical",
            description="Core Python programming",
            proficiency_levels=[
                {"level": 1, "name": "novice"},
                {"level": 2, "name": "beginner"},
                {"level": 3, "name": "intermediate"}
            ],
            prerequisites=[],
            related_tools=["code_execution", "code_review"]
        )

        skill = self.db.get_skill("python_basics")
        assert skill is not None
        assert skill['name'] == "Python Fundamentals"
        assert skill['category'] == "technical"
        assert len(skill['proficiency_levels']) == 3
        assert "code_execution" in skill['related_tools']

    def test_list_skills(self):
        """Test listing skills with category filter"""
        self.db.save_skill("py1", "Python 1", "technical")
        self.db.save_skill("py2", "Python 2", "technical")
        self.db.save_skill("agile", "Agile", "process")
        self.db.save_skill("comm", "Communication", "soft_skill")

        all_skills = self.db.list_skills()
        assert len(all_skills) == 4

        tech_skills = self.db.list_skills(category="technical")
        assert len(tech_skills) == 2

        process_skills = self.db.list_skills(category="process")
        assert len(process_skills) == 1

    def test_skill_not_found(self):
        """Test getting non-existent skill"""
        assert self.db.get_skill("nonexistent") is None

    def test_update_skill_progress(self):
        """Test updating agent skill progress"""
        self.db.save_skill("docker", "Docker", "tool")

        # Initial progress
        self.db.update_skill_progress(
            agent_id="agent_0",
            skill_id="docker",
            current_level=1,
            completions=1
        )

        progress = self.db.get_skill_progress("agent_0", "docker")
        assert len(progress) == 1
        assert progress[0]['current_level'] == 1
        assert progress[0]['completions'] == 1
        assert progress[0]['last_practiced'] is not None

        # Add more completions
        self.db.update_skill_progress(
            agent_id="agent_0",
            skill_id="docker",
            completions=5
        )

        progress = self.db.get_skill_progress("agent_0", "docker")
        assert progress[0]['completions'] == 6  # 1 + 5

    def test_skill_progress_with_assessment(self):
        """Test skill progress with assessment scores"""
        self.db.save_skill("k8s", "Kubernetes", "tool")

        self.db.update_skill_progress(
            agent_id="agent_1",
            skill_id="k8s",
            assessment_score=85.5
        )

        self.db.update_skill_progress(
            agent_id="agent_1",
            skill_id="k8s",
            assessment_score=92.0
        )

        progress = self.db.get_skill_progress("agent_1", "k8s")
        scores = progress[0]['assessment_scores']
        assert len(scores) == 2
        assert scores[0]['score'] == 85.5
        assert scores[1]['score'] == 92.0

    def test_get_all_skill_progress(self):
        """Test getting all skills for an agent"""
        self.db.save_skill("s1", "Skill 1", "cat1")
        self.db.save_skill("s2", "Skill 2", "cat2")

        self.db.update_skill_progress("agent_0", "s1", current_level=3)
        self.db.update_skill_progress("agent_0", "s2", current_level=2)

        progress = self.db.get_skill_progress("agent_0")
        assert len(progress) == 2

    # ========== Learning Path Tests ==========

    def test_save_and_get_learning_path(self):
        """Test saving and retrieving a learning path"""
        modules = [
            {"module_id": "m1", "name": "Module 1", "required": True},
            {"module_id": "m2", "name": "Module 2", "required": True},
            {"module_id": "m3", "name": "Module 3", "required": False}
        ]
        certification = {
            "name": "Python Developer",
            "requirements": {"min_score": 80}
        }

        self.db.save_learning_path(
            path_id="python_dev",
            name="Python Developer Path",
            target_role="developer",
            description="Learn Python development",
            estimated_hours=40.5,
            modules=modules,
            certification=certification
        )

        path = self.db.get_learning_path("python_dev")
        assert path is not None
        assert path['name'] == "Python Developer Path"
        assert path['target_role'] == "developer"
        assert path['estimated_hours'] == 40.5
        assert len(path['modules']) == 3
        assert path['certification']['name'] == "Python Developer"

    def test_list_learning_paths(self):
        """Test listing learning paths"""
        self.db.save_learning_path("dev1", "Dev Path 1", "developer")
        self.db.save_learning_path("dev2", "Dev Path 2", "developer")
        self.db.save_learning_path("ops1", "Ops Path 1", "operator")

        all_paths = self.db.list_learning_paths()
        assert len(all_paths) == 3

        dev_paths = self.db.list_learning_paths(target_role="developer")
        assert len(dev_paths) == 2

    def test_learning_path_not_found(self):
        """Test getting non-existent learning path"""
        assert self.db.get_learning_path("nonexistent") is None

    def test_get_learning_progress(self):
        """Test getting learning progress"""
        self.db.save_learning_path("test_path", "Test Path", "tester")

        # No progress yet
        progress = self.db.get_learning_progress("test_path", "agent_0")
        assert progress['path_id'] == "test_path"
        assert progress['modules_completed'] == []
        assert progress['overall_score'] == 0

    # ========== Event Logging Tests ==========

    def test_event_logging(self):
        """Test workflow event logging"""
        workflow_id = self.db.save_workflow(name="Event Test", definition={"stages": []})
        execution_id = self.db.start_execution(workflow_id=workflow_id)

        # Events are logged automatically by operations
        # But we can also test the get method
        events = self.db.get_execution_events(execution_id)
        assert len(events) >= 1  # At least execution_started

        # Check event structure
        event = events[0]
        assert 'event_id' in event
        assert 'event_type' in event
        assert 'timestamp' in event
        assert 'data' in event

    # ========== Statistics Tests ==========

    def test_get_stats_empty(self):
        """Test statistics on empty database"""
        stats = self.db.get_stats()
        assert stats['total_workflows'] == 0
        assert stats['total_executions'] == 0
        assert stats['total_skills'] == 0
        assert stats['total_learning_paths'] == 0

    def test_get_stats_with_data(self):
        """Test statistics with data"""
        # Create some data
        wf1 = self.db.save_workflow(name="WF1", definition={"stages": []})
        self.db.save_workflow(name="WF2", definition={"stages": []}, is_template=True)

        self.db.start_execution(workflow_id=wf1)
        exec2 = self.db.start_execution(workflow_id=wf1)
        self.db.update_execution(execution_id=exec2, status="completed")

        self.db.save_skill("s1", "Skill 1", "cat")
        self.db.save_learning_path("p1", "Path 1", "role")

        stats = self.db.get_stats()
        assert stats['total_workflows'] == 2
        assert stats['workflow_templates'] == 1
        assert stats['total_executions'] == 2
        assert stats['executions_by_status']['running'] == 1
        assert stats['executions_by_status']['completed'] == 1
        assert stats['total_skills'] == 1
        assert stats['total_learning_paths'] == 1

    def test_get_recent_executions(self):
        """Test getting recent executions"""
        wf_id = self.db.save_workflow(name="Recent Test", definition={"stages": []})

        for i in range(10):
            self.db.start_execution(workflow_id=wf_id, name=f"Exec {i}")

        recent = self.db.get_recent_executions(limit=5)
        assert len(recent) == 5
        # Should be in reverse chronological order
        assert recent[0]['name'] == "Exec 9"

    def test_get_top_skills(self):
        """Test getting top skills by level"""
        self.db.save_skill("s1", "Skill 1", "cat")
        self.db.save_skill("s2", "Skill 2", "cat")
        self.db.save_skill("s3", "Skill 3", "cat")

        self.db.update_skill_progress("agent_0", "s1", current_level=5, completions=50)
        self.db.update_skill_progress("agent_0", "s2", current_level=3, completions=20)
        self.db.update_skill_progress("agent_0", "s3", current_level=1, completions=5)

        top = self.db.get_top_skills(limit=2)
        assert len(top) == 2
        assert top[0]['current_level'] == 5
        assert top[1]['current_level'] == 3

    def test_get_training_module(self):
        """Test getting training module (returns None if not exists)"""
        result = self.db.get_training_module("nonexistent")
        assert result is None

    def test_get_agent_proficiency(self):
        """Test getting agent proficiency"""
        self.db.save_skill("tech1", "Tech Skill", "technical")
        self.db.save_skill("soft1", "Soft Skill", "soft_skill")

        self.db.update_skill_progress("agent_0", "tech1", current_level=4, completions=30)

        proficiency = self.db.get_agent_proficiency("agent_0")
        assert len(proficiency) == 2  # Both skills

        # Check the one with progress
        tech_prof = next(p for p in proficiency if p['skill_id'] == "tech1")
        assert tech_prof['current_level'] == 4
        assert tech_prof['completions'] == 30


class TestWorkflowEngineDatabaseEdgeCases:
    """Edge case and error handling tests"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_edge.db")
        self.db = WorkflowEngineDatabase(self.db_path)

    def test_empty_definition(self):
        """Test workflow with empty definition"""
        workflow_id = self.db.save_workflow(
            name="Empty Definition",
            definition={}
        )
        workflow = self.db.get_workflow(workflow_id=workflow_id)
        assert workflow['definition'] == {}

    def test_complex_metadata(self):
        """Test workflow with complex metadata"""
        metadata = {
            "tags": ["production", "critical"],
            "owner": {"name": "Team A", "email": "team@example.com"},
            "config": {
                "timeout": 3600,
                "retries": 3,
                "nested": {"deep": {"value": 42}}
            }
        }

        workflow_id = self.db.save_workflow(
            name="Complex Metadata",
            definition={"stages": []},
            metadata=metadata
        )

        workflow = self.db.get_workflow(workflow_id=workflow_id)
        assert workflow['metadata']['tags'] == ["production", "critical"]
        assert workflow['metadata']['config']['nested']['deep']['value'] == 42

    def test_unicode_content(self):
        """Test handling of unicode characters"""
        self.db.save_workflow(
            name="Unicode 日本語 🚀",
            definition={"stages": [{"id": "s1", "name": "设计阶段 📐"}]},
            description="Description with émojis 🎉"
        )

        workflow = self.db.get_workflow(name="Unicode 日本語 🚀")
        assert workflow is not None
        assert "日本語" in workflow['name']
        assert "🚀" in workflow['name']

    def test_large_context(self):
        """Test execution with large context data"""
        workflow_id = self.db.save_workflow(name="Large Context", definition={"stages": []})

        large_context = {
            "data": ["item"] * 1000,
            "nested": {str(i): f"value_{i}" for i in range(100)}
        }

        execution_id = self.db.start_execution(
            workflow_id=workflow_id,
            context=large_context
        )

        execution = self.db.get_execution(execution_id)
        assert len(execution['context']['data']) == 1000
        assert execution['context']['nested']['50'] == "value_50"

    def test_null_optional_fields(self):
        """Test handling of null optional fields"""
        self.db.save_skill(
            skill_id="minimal",
            name="Minimal Skill",
            category="test",
            description=None,
            proficiency_levels=None,
            prerequisites=None,
            related_tools=None
        )

        skill = self.db.get_skill("minimal")
        assert skill['description'] is None
        assert skill['proficiency_levels'] == []
        assert skill['prerequisites'] == []
        assert skill['related_tools'] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
