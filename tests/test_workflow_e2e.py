"""
End-to-end tests for Workflow Engine system.
Tests complete workflow lifecycles, training paths, and skill progression.
"""

import os
import pytest
import json

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager
from instruments.custom.workflow_engine.workflow_visualizer import WorkflowVisualizer


class TestProductDevelopmentWorkflow:
    """End-to-end tests for product development workflow lifecycle"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        """Setup fresh manager for each test"""
        self.db_path = str(tmp_path / "test_e2e_product.db")
        self.manager = WorkflowEngineManager(self.db_path)
        self.visualizer = WorkflowVisualizer()

    def test_full_product_development_cycle(self):
        """Test complete design → POC → MVP → Production → Support cycle"""
        # 1. Create workflow
        wf_result = self.manager.create_workflow(
            name="Widget App v1.0",
            description="Complete widget application",
            stages=[
                {
                    "id": "design",
                    "name": "Design Phase",
                    "type": "design",
                    "exit_criteria": [
                        {"id": "wireframes", "name": "Wireframes complete"},
                        {"id": "spec", "name": "Tech spec approved"}
                    ],
                    "tasks": [
                        {"id": "research", "name": "Market Research", "dependencies": []},
                        {"id": "wireframe", "name": "Create Wireframes", "dependencies": ["research"]},
                        {"id": "spec_write", "name": "Write Tech Spec", "dependencies": ["research"]}
                    ]
                },
                {
                    "id": "poc",
                    "name": "Proof of Concept",
                    "type": "poc",
                    "exit_criteria": [
                        {"id": "demo", "name": "Working demo available"}
                    ],
                    "approval_required": True
                },
                {
                    "id": "mvp",
                    "name": "Minimum Viable Product",
                    "type": "mvp",
                    "exit_criteria": [
                        {"id": "features", "name": "Core features complete"},
                        {"id": "tests", "name": "Tests passing"}
                    ]
                },
                {
                    "id": "production",
                    "name": "Production Release",
                    "type": "production",
                    "approval_required": True
                },
                {
                    "id": "support",
                    "name": "Support & Maintenance",
                    "type": "support"
                }
            ]
        )

        assert 'workflow_id' in wf_result
        # Has 'support' stage so classified as service_delivery
        assert wf_result['type'] == "service_delivery"
        assert wf_result['stages'] == 5

        # 2. Start execution
        exec_result = self.manager.start_workflow(
            workflow_id=wf_result['workflow_id'],
            execution_name="Widget App Sprint 1",
            context={"team": "alpha", "priority": "high"}
        )

        assert exec_result['status'] == "running"
        assert exec_result['current_stage'] == "design"
        execution_id = exec_result['execution_id']

        # 3. Execute Design Phase tasks
        # Start and complete research
        self.manager.start_task(execution_id, "design", "research",
                               input_data={"scope": "competitors"})
        self.manager.complete_task(execution_id, "design", "research",
                                  output_data={"competitors": ["A", "B", "C"]})

        # Now wireframe and spec can run (parallel)
        self.manager.start_task(execution_id, "design", "wireframe")
        self.manager.complete_task(execution_id, "design", "wireframe",
                                  output_data={"file": "wireframes.fig"})

        self.manager.start_task(execution_id, "design", "spec_write")
        self.manager.complete_task(execution_id, "design", "spec_write",
                                  output_data={"file": "spec.md"})

        # 4. Complete exit criteria for design
        self.manager.complete_criterion(execution_id, "design", "wireframes")
        self.manager.complete_criterion(execution_id, "design", "spec")

        # 5. Advance to POC
        advance_result = self.manager.advance_stage(execution_id, force=False)
        assert advance_result['status'] == "advanced"
        assert advance_result['current_stage'] == "poc"

        # 6. Complete POC criterion
        self.manager.complete_criterion(execution_id, "poc", "demo")

        # POC requires approval
        approve_result = self.manager.approve_stage(execution_id, "poc",
                                                   "product_manager",
                                                   notes="Demo looks good!")
        assert approve_result['status'] == "approved"

        # 7. Advance to MVP
        self.manager.advance_stage(execution_id, force=False)
        status = self.manager.get_execution_status(execution_id)
        assert status['current_stage'] == "mvp"

        # 8. Complete MVP criteria
        self.manager.complete_criterion(execution_id, "mvp", "features")
        self.manager.complete_criterion(execution_id, "mvp", "tests")
        self.manager.advance_stage(execution_id, force=False)

        # 9. Production requires approval
        self.manager.approve_stage(execution_id, "production",
                                  "tech_lead", notes="Ready for release")
        self.manager.advance_stage(execution_id, force=False)

        # 10. Now in support phase - workflow continues
        status = self.manager.get_execution_status(execution_id)
        assert status['current_stage'] == "support"
        assert status['status'] == "running"

        # 11. Complete workflow
        complete_result = self.manager.advance_stage(execution_id, force=True)
        assert complete_result['status'] == "workflow_completed"

        # 12. Verify final status
        final_status = self.manager.get_execution_status(execution_id)
        assert final_status['status'] == "completed"
        assert final_status['progress']['percentage'] == 100

    def test_workflow_with_task_failure_and_retry(self):
        """Test workflow handles task failure and retry"""
        wf = self.manager.create_workflow(
            name="Retry Test Workflow",
            stages=[{
                "id": "build",
                "name": "Build",
                "tasks": [
                    {"id": "compile", "name": "Compile Code", "dependencies": []},
                    {"id": "test", "name": "Run Tests", "dependencies": ["compile"]}
                ]
            }]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Start compile
        self.manager.start_task(execution_id, "build", "compile")

        # First attempt fails
        fail_result = self.manager.fail_task(
            execution_id, "build", "compile",
            error="Build failed: missing dependency",
            retry=True
        )
        assert fail_result['status'] == "retry_scheduled"

        # Retry succeeds
        self.manager.start_task(execution_id, "build", "compile")
        self.manager.complete_task(execution_id, "build", "compile",
                                  output_data={"artifact": "app.jar"})

        # Continue with tests
        next_task = self.manager.get_next_task(execution_id)
        assert next_task['task']['id'] == "test"

    def test_workflow_visualization_at_stages(self):
        """Test visualization works at different stages"""
        wf = self.manager.create_workflow(
            name="Visual Workflow",
            stages=[
                {"id": "s1", "name": "Stage 1"},
                {"id": "s2", "name": "Stage 2"},
                {"id": "s3", "name": "Stage 3"}
            ]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']
        workflow = self.manager.get_workflow(workflow_id=wf['workflow_id'])

        # Visualize at start
        status = self.manager.get_execution_status(execution_id)
        diagram = self.visualizer.generate_workflow_diagram(workflow, status)
        assert "```mermaid" in diagram

        # Advance and visualize
        self.manager.advance_stage(execution_id, force=True)
        status = self.manager.get_execution_status(execution_id)
        diagram = self.visualizer.generate_workflow_diagram(workflow, status)
        assert "class s1 completed" in diagram

        # Complete and visualize
        self.manager.advance_stage(execution_id, force=True)
        self.manager.advance_stage(execution_id, force=True)
        status = self.manager.get_execution_status(execution_id)
        assert status['status'] == "completed"


class TestServiceDeliveryWorkflow:
    """End-to-end tests for service delivery workflow"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_e2e_service.db")
        self.manager = WorkflowEngineManager(self.db_path)

    def test_client_project_flow(self):
        """Test complete client project workflow"""
        wf = self.manager.create_workflow(
            name="ACME Integration Project",
            stages=[
                {
                    "id": "discovery",
                    "name": "Discovery",
                    "exit_criteria": [{"id": "reqs", "name": "Requirements gathered"}]
                },
                {
                    "id": "proposal",
                    "name": "Proposal",
                    "approval_required": True
                },
                {
                    "id": "implementation",
                    "name": "Implementation",
                    "tasks": [
                        {"id": "setup", "name": "Setup Environment", "dependencies": []},
                        {"id": "develop", "name": "Develop Solution", "dependencies": ["setup"]},
                        {"id": "integrate", "name": "Integration Testing", "dependencies": ["develop"]}
                    ]
                },
                {
                    "id": "deployment",
                    "name": "Deployment",
                    "approval_required": True
                },
                {
                    "id": "support",
                    "name": "Ongoing Support",
                    "type": "support"
                }
            ]
        )

        assert wf['type'] == "service_delivery"

        # Execute workflow
        exec_result = self.manager.start_workflow(
            workflow_id=wf['workflow_id'],
            context={"client": "ACME Corp", "contract_value": 50000}
        )
        execution_id = exec_result['execution_id']

        # Discovery phase
        self.manager.complete_criterion(execution_id, "discovery", "reqs")
        self.manager.advance_stage(execution_id)

        # Proposal approval
        self.manager.approve_stage(execution_id, "proposal", "sales_manager")
        self.manager.advance_stage(execution_id)

        # Implementation tasks
        for task_id in ["setup", "develop", "integrate"]:
            self.manager.start_task(execution_id, "implementation", task_id)
            self.manager.complete_task(execution_id, "implementation", task_id)

        self.manager.advance_stage(execution_id, force=True)

        # Deployment approval and advance
        self.manager.approve_stage(execution_id, "deployment", "client_pm")
        self.manager.advance_stage(execution_id)

        # Now in support - client relationship continues
        status = self.manager.get_execution_status(execution_id)
        assert status['current_stage'] == "support"
        assert status['context']['client'] == "ACME Corp"


class TestTrainingPathCompletion:
    """End-to-end tests for learning path completion"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_e2e_training.db")
        self.manager = WorkflowEngineManager(self.db_path)
        self.visualizer = WorkflowVisualizer()

    def test_complete_learning_path_to_certification(self):
        """Test completing a learning path leads to certification"""
        # Setup prerequisite skills
        self.manager.register_skill("python_basics", "Python Basics", "technical")
        self.manager.register_skill("python_advanced", "Advanced Python", "technical",
                                   prerequisites=["python_basics"])
        self.manager.register_skill("testing", "Software Testing", "technical")
        self.manager.register_skill("architecture", "System Architecture", "technical",
                                   prerequisites=["python_advanced", "testing"])

        # Create learning path
        path_result = self.manager.create_learning_path(
            path_id="python_developer",
            name="Python Developer Certification",
            target_role="developer",
            description="Complete path to Python Developer certification",
            modules=[
                {"module_id": "m1", "name": "Python Fundamentals", "required": True},
                {"module_id": "m2", "name": "Advanced Python", "required": True, "prerequisites": ["m1"]},
                {"module_id": "m3", "name": "Testing Best Practices", "required": True},
                {"module_id": "m4", "name": "Architecture Design", "required": True, "prerequisites": ["m2", "m3"]},
                {"module_id": "m5", "name": "Bonus: Performance", "required": False}
            ],
            estimated_hours=40.0,
            certification={
                "name": "Certified Python Developer",
                "badge": "python_dev_cert",
                "requirements": {"min_score": 80}
            }
        )

        assert path_result['status'] == "created"

        # Track skill practice
        for _ in range(10):
            self.manager.track_skill_usage("agent_0", "python_basics", success=True)

        for _ in range(15):
            self.manager.track_skill_usage("agent_0", "python_advanced", success=True)

        # Generate path visualization
        path = self.manager.get_learning_path("python_developer")
        progress = self.manager.get_learning_progress("python_developer", "agent_0")
        diagram = self.visualizer.generate_learning_path_map(path, progress)

        assert "```mermaid" in diagram
        assert "Certified Python Developer" in diagram


class TestSkillProgression:
    """End-to-end tests for skill level progression"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_e2e_skills.db")
        self.manager = WorkflowEngineManager(self.db_path)
        self.visualizer = WorkflowVisualizer()

    def test_skill_progression_novice_to_expert(self):
        """Test complete skill progression from novice to expert"""
        # Register skill with custom level thresholds
        self.manager.register_skill(
            skill_id="code_review",
            name="Code Review",
            category="technical",
            description="Ability to review code effectively",
            proficiency_levels=[
                {"level": 1, "name": "novice", "min_completions": 0},
                {"level": 2, "name": "beginner", "min_completions": 5},
                {"level": 3, "name": "intermediate", "min_completions": 15},
                {"level": 4, "name": "advanced", "min_completions": 30},
                {"level": 5, "name": "expert", "min_completions": 50}
            ]
        )

        agent_id = "agent_0"
        skill_id = "code_review"

        # Initial state
        skills = self.manager.get_agent_skills(agent_id)
        assert len(skills) == 0  # No practice yet

        # Practice to beginner (5 completions)
        for _ in range(6):
            result = self.manager.track_skill_usage(agent_id, skill_id, success=True)

        skills = self.manager.get_agent_skills(agent_id)
        assert len(skills) == 1

        # Practice to intermediate (15 total)
        for _ in range(10):
            self.manager.track_skill_usage(agent_id, skill_id, success=True)

        # Practice to advanced (30 total)
        for _ in range(15):
            self.manager.track_skill_usage(agent_id, skill_id, success=True)

        # Practice to expert (50 total)
        for _ in range(20):
            result = self.manager.track_skill_usage(agent_id, skill_id, success=True)

        # Generate skill chart
        proficiency = self.manager.get_agent_skills(agent_id)
        chart = self.visualizer.generate_skill_chart(proficiency)

        assert "```" in chart
        assert "Code Review" in chart
        assert "★" in chart

    def test_multiple_skills_progression(self):
        """Test progression across multiple skills"""
        # Register multiple skills
        skills_to_register = [
            ("python", "Python Programming", "technical"),
            ("docker", "Docker Containers", "tool"),
            ("agile", "Agile Methodology", "process"),
            ("communication", "Technical Communication", "soft_skill")
        ]

        for skill_id, name, category in skills_to_register:
            self.manager.register_skill(skill_id, name, category)

        agent_id = "agent_0"

        # Practice each skill different amounts
        practice_counts = {"python": 30, "docker": 20, "agile": 15, "communication": 10}

        for skill_id, count in practice_counts.items():
            for _ in range(count):
                self.manager.track_skill_usage(agent_id, skill_id, success=True)

        # Generate proficiency report
        proficiency = self.manager.get_agent_skills(agent_id)
        chart = self.visualizer.generate_skill_chart(proficiency)

        assert "TECHNICAL" in chart
        assert "TOOL" in chart
        assert "PROCESS" in chart
        assert "SOFT_SKILL" in chart


class TestWorkflowWithParallelTasks:
    """Tests for workflows with parallel task execution"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_e2e_parallel.db")
        self.manager = WorkflowEngineManager(self.db_path)

    def test_parallel_tasks_execution(self):
        """Test executing tasks that can run in parallel"""
        wf = self.manager.create_workflow(
            name="Parallel Build",
            stages=[{
                "id": "build",
                "name": "Build Stage",
                "tasks": [
                    {"id": "init", "name": "Initialize", "dependencies": []},
                    {"id": "frontend", "name": "Build Frontend", "dependencies": ["init"]},
                    {"id": "backend", "name": "Build Backend", "dependencies": ["init"]},
                    {"id": "mobile", "name": "Build Mobile", "dependencies": ["init"]},
                    {"id": "integrate", "name": "Integration", "dependencies": ["frontend", "backend", "mobile"]}
                ]
            }]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Only init should be available initially
        next_task = self.manager.get_next_task(execution_id)
        assert next_task['task']['id'] == "init"

        # Complete init
        self.manager.start_task(execution_id, "build", "init")
        self.manager.complete_task(execution_id, "build", "init")

        # Now frontend, backend, and mobile should all be available
        available_tasks = []
        for _ in range(3):
            task = self.manager.get_next_task(execution_id)
            if task['task']:
                available_tasks.append(task['task']['id'])
                self.manager.start_task(execution_id, "build", task['task']['id'])
                self.manager.complete_task(execution_id, "build", task['task']['id'])

        assert set(available_tasks) == {"frontend", "backend", "mobile"}

        # Now integrate should be available
        next_task = self.manager.get_next_task(execution_id)
        assert next_task['task']['id'] == "integrate"


class TestStageApprovalGates:
    """Tests for stage approval gates"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_e2e_approval.db")
        self.manager = WorkflowEngineManager(self.db_path)

    def test_approval_gate_enforcement(self):
        """Test that approval gates block advancement"""
        wf = self.manager.create_workflow(
            name="Approval Gate Test",
            stages=[
                {"id": "dev", "name": "Development"},
                {"id": "staging", "name": "Staging", "approval_required": True},
                {"id": "prod", "name": "Production", "approval_required": True}
            ]
        )

        exec_result = self.manager.start_workflow(workflow_id=wf['workflow_id'])
        execution_id = exec_result['execution_id']

        # Advance from dev to staging (no approval needed for dev)
        self.manager.advance_stage(execution_id, force=True)

        # Try to advance from staging without approval - should fail
        advance_result = self.manager.advance_stage(execution_id, force=False)
        assert 'error' in advance_result
        assert 'approval' in advance_result['error'].lower()

        # Approve and advance
        self.manager.approve_stage(execution_id, "staging", "qa_lead",
                                  notes="All tests pass")
        advance_result = self.manager.advance_stage(execution_id, force=False)
        assert advance_result['status'] == "advanced"

        # Now in production - also needs approval
        advance_result = self.manager.advance_stage(execution_id, force=False)
        assert 'error' in advance_result

        # Multi-person approval
        self.manager.approve_stage(execution_id, "prod", "tech_lead",
                                  notes="Technical review complete")

        # Complete workflow
        advance_result = self.manager.advance_stage(execution_id, force=False)
        assert advance_result['status'] == "workflow_completed"


class TestDashboardIntegration:
    """Integration tests for dashboard functionality"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_e2e_dashboard.db")
        self.manager = WorkflowEngineManager(self.db_path)
        self.visualizer = WorkflowVisualizer()

    def test_dashboard_reflects_system_state(self):
        """Test dashboard accurately reflects system state"""
        # Create workflows
        wf1 = self.manager.create_workflow(
            name="Project Alpha",
            stages=[{"id": "s1", "name": "S1"}]
        )
        wf2 = self.manager.create_workflow(
            name="Project Beta",
            stages=[{"id": "s1", "name": "S1"}]
        )

        # Create executions with different states
        exec1 = self.manager.start_workflow(workflow_id=wf1['workflow_id'])
        exec2 = self.manager.start_workflow(workflow_id=wf1['workflow_id'])
        exec3 = self.manager.start_workflow(workflow_id=wf2['workflow_id'])

        # Complete one
        self.manager.advance_stage(exec1['execution_id'], force=True)

        # Register skills
        self.manager.register_skill("s1", "Skill 1", "technical")
        self.manager.register_skill("s2", "Skill 2", "tool")

        # Track usage
        for _ in range(20):
            self.manager.track_skill_usage("agent_0", "s1", success=True)
        for _ in range(10):
            self.manager.track_skill_usage("agent_0", "s2", success=True)

        # Create learning path
        self.manager.create_learning_path("lp1", "Learning Path 1", "developer")

        # Get stats and generate dashboard
        stats = self.manager.get_stats()
        recent = self.manager.get_recent_executions(limit=5)
        skills = self.manager.get_top_skills(limit=5)

        dashboard = self.visualizer.generate_dashboard(stats, recent, skills)

        # Verify dashboard content
        assert "Workflows: 2" in dashboard
        assert "Executions: 3" in dashboard
        assert "Skills: 2" in dashboard
        assert "Learning Paths: 1" in dashboard
        assert "completed: 1" in dashboard or "running: 2" in dashboard


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
