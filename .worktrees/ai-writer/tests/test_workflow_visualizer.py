"""
Unit tests for WorkflowVisualizer.
Tests Mermaid diagram generation, ASCII progress bars, and dashboard output.
"""

import os

# Add parent directory to path
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.custom.workflow_engine.workflow_visualizer import WorkflowVisualizer


class TestWorkflowVisualizer:
    """Test suite for WorkflowVisualizer"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Create visualizer instance"""
        self.visualizer = WorkflowVisualizer()

    # ========== Workflow Diagram Tests ==========

    def test_generate_workflow_diagram_basic(self):
        """Test generating basic workflow diagram"""
        workflow = {
            "definition": {
                "stages": [
                    {"id": "design", "name": "Design Phase", "type": "design"},
                    {"id": "build", "name": "Build Phase", "type": "custom"},
                    {"id": "deploy", "name": "Deploy Phase", "type": "production"}
                ]
            }
        }

        diagram = self.visualizer.generate_workflow_diagram(workflow)

        assert "```mermaid" in diagram
        assert "flowchart TD" in diagram
        assert "design[Design Phase]" in diagram
        assert "build[Build Phase]" in diagram
        assert "deploy[Deploy Phase]" in diagram
        assert "design --> build" in diagram
        assert "build --> deploy" in diagram
        assert "```" in diagram

    def test_generate_workflow_diagram_with_transitions(self):
        """Test diagram with explicit transitions"""
        workflow = {
            "definition": {
                "stages": [
                    {"id": "s1", "name": "Start"},
                    {"id": "s2", "name": "Process"},
                    {"id": "s3", "name": "End"}
                ],
                "transitions": [
                    {"from": "s1", "to": "s2", "condition": "data_ready"},
                    {"from": "s2", "to": "s3", "condition": "processed"},
                    {"from": "s2", "to": "s1", "condition": "retry_needed"}
                ]
            }
        }

        diagram = self.visualizer.generate_workflow_diagram(workflow)

        assert "s1 -->|data_ready| s2" in diagram
        assert "s2 -->|processed| s3" in diagram
        assert "s2 -->|retry_needed| s1" in diagram

    def test_generate_workflow_diagram_with_status(self):
        """Test diagram with execution status coloring"""
        workflow = {
            "definition": {
                "stages": [
                    {"id": "design", "name": "Design"},
                    {"id": "build", "name": "Build"},
                    {"id": "test", "name": "Test"}
                ]
            }
        }

        execution_status = {
            "stage_details": [
                {"stage_id": "design", "status": "completed"},
                {"stage_id": "build", "status": "in_progress"},
                {"stage_id": "test", "status": "pending"}
            ]
        }

        diagram = self.visualizer.generate_workflow_diagram(workflow, execution_status)

        # Check class definitions exist
        assert "classDef completed" in diagram
        assert "classDef inProgress" in diagram
        assert "classDef pending" in diagram

        # Check classes are applied
        assert "class design completed" in diagram
        assert "class build inProgress" in diagram
        assert "class test pending" in diagram

    def test_generate_workflow_diagram_empty_stages(self):
        """Test diagram with no stages"""
        workflow = {"definition": {"stages": []}}

        diagram = self.visualizer.generate_workflow_diagram(workflow)

        assert "```mermaid" in diagram
        assert "flowchart TD" in diagram
        # Should still be valid Mermaid, just empty

    def test_generate_workflow_diagram_definition_only(self):
        """Test diagram when workflow is just the definition"""
        workflow = {
            "stages": [
                {"id": "s1", "name": "Stage 1"},
                {"id": "s2", "name": "Stage 2"}
            ]
        }

        diagram = self.visualizer.generate_workflow_diagram(workflow)

        assert "s1[Stage 1]" in diagram
        assert "s1 --> s2" in diagram

    # ========== Task Diagram Tests ==========

    def test_generate_task_diagram_basic(self):
        """Test generating task dependency diagram"""
        stage = {
            "id": "design",
            "name": "Design Phase",
            "tasks": [
                {"id": "research", "name": "Research", "dependencies": []},
                {"id": "wireframe", "name": "Wireframes", "dependencies": ["research"]},
                {"id": "review", "name": "Review", "dependencies": ["wireframe"]}
            ]
        }

        diagram = self.visualizer.generate_task_diagram(stage)

        assert "```mermaid" in diagram
        assert "flowchart LR" in diagram
        assert "start((Start))" in diagram
        assert "finish((End))" in diagram
        assert "research" in diagram
        assert "wireframe" in diagram
        assert "start --> research" in diagram
        assert "research --> wireframe" in diagram
        assert "wireframe --> review" in diagram

    def test_generate_task_diagram_parallel_tasks(self):
        """Test diagram with parallel tasks (multiple tasks with same dependency)"""
        stage = {
            "tasks": [
                {"id": "init", "name": "Initialize", "dependencies": []},
                {"id": "task_a", "name": "Task A", "dependencies": ["init"]},
                {"id": "task_b", "name": "Task B", "dependencies": ["init"]},
                {"id": "merge", "name": "Merge", "dependencies": ["task_a", "task_b"]}
            ]
        }

        diagram = self.visualizer.generate_task_diagram(stage)

        assert "init --> task_a" in diagram
        assert "init --> task_b" in diagram
        assert "task_a --> merge" in diagram
        assert "task_b --> merge" in diagram

    def test_generate_task_diagram_with_status(self):
        """Test task diagram with status"""
        stage = {
            "tasks": [
                {"id": "t1", "name": "Task 1", "dependencies": []},
                {"id": "t2", "name": "Task 2", "dependencies": ["t1"]}
            ]
        }

        task_status = [
            {"task_id": "t1", "status": "completed"},
            {"task_id": "t2", "status": "running"}
        ]

        diagram = self.visualizer.generate_task_diagram(stage, task_status)

        assert "classDef completed" in diagram
        assert "classDef running" in diagram

    def test_generate_task_diagram_with_roles(self):
        """Test task diagram shows roles"""
        stage = {
            "tasks": [
                {"id": "t1", "name": "Code Review", "role": "senior_dev", "dependencies": []},
                {"id": "t2", "name": "Testing", "role": "qa", "dependencies": ["t1"]}
            ]
        }

        diagram = self.visualizer.generate_task_diagram(stage)

        assert "(senior_dev)" in diagram
        assert "(qa)" in diagram

    def test_generate_task_diagram_empty_tasks(self):
        """Test task diagram with no tasks"""
        stage = {"tasks": []}

        diagram = self.visualizer.generate_task_diagram(stage)

        assert "start((Start))" in diagram
        assert "finish((End))" in diagram

    # ========== Progress Bar Tests ==========

    def test_generate_progress_bar_zero(self):
        """Test progress bar at 0%"""
        bar = self.visualizer.generate_progress_bar(0, 10, width=10)

        assert "[" in bar
        assert "]" in bar
        assert "0%" in bar
        assert "░" * 10 in bar

    def test_generate_progress_bar_half(self):
        """Test progress bar at 50%"""
        bar = self.visualizer.generate_progress_bar(5, 10, width=10)

        assert "50%" in bar
        assert "█" * 5 in bar
        assert "░" * 5 in bar

    def test_generate_progress_bar_full(self):
        """Test progress bar at 100%"""
        bar = self.visualizer.generate_progress_bar(10, 10, width=10)

        assert "100%" in bar
        assert "█" * 10 in bar
        assert "░" not in bar.split("]")[0]  # No empty blocks before ]

    def test_generate_progress_bar_empty_total(self):
        """Test progress bar with zero total"""
        bar = self.visualizer.generate_progress_bar(0, 0, width=10)

        assert "0%" in bar

    def test_generate_progress_bar_custom_width(self):
        """Test progress bar with custom width"""
        bar = self.visualizer.generate_progress_bar(5, 10, width=20)

        # Should have 10 filled, 10 empty
        content = bar.split("[")[1].split("]")[0]
        assert len(content) == 20

    # ========== Stage Progress Tests ==========

    def test_generate_stage_progress(self):
        """Test generating stage progress visualization"""
        stages = [
            {"id": "s1", "name": "Stage 1"},
            {"id": "s2", "name": "Stage 2"},
            {"id": "s3", "name": "Stage 3"}
        ]

        execution_status = {
            "stage_details": [
                {"stage_id": "s1", "status": "completed"},
                {"stage_id": "s2", "status": "in_progress"},
                {"stage_id": "s3", "status": "pending"}
            ]
        }

        progress = self.visualizer.generate_stage_progress(stages, execution_status)

        assert "Stage 1" in progress
        assert "Stage 2" in progress
        assert "Stage 3" in progress
        assert "✓" in progress  # Completed
        assert "▶" in progress  # In progress
        assert "○" in progress  # Pending

    def test_generate_stage_progress_all_pending(self):
        """Test stage progress with all pending"""
        stages = [
            {"id": "s1", "name": "First"},
            {"id": "s2", "name": "Second"}
        ]

        execution_status = {"stage_details": []}

        progress = self.visualizer.generate_stage_progress(stages, execution_status)

        assert "First" in progress
        assert "Second" in progress
        # All should show pending icon
        assert progress.count("○") == 2

    # ========== Timeline Tests ==========

    def test_generate_timeline(self):
        """Test generating execution timeline"""
        execution = {"execution_id": 1}
        events = [
            {
                "timestamp": "2024-01-15T10:00:00",
                "event_type": "execution_started",
                "stage_id": None,
                "task_id": None
            },
            {
                "timestamp": "2024-01-15T10:05:00",
                "event_type": "stage_updated",
                "stage_id": "design",
                "task_id": None
            },
            {
                "timestamp": "2024-01-15T10:10:00",
                "event_type": "task_updated",
                "stage_id": "design",
                "task_id": "research"
            }
        ]

        timeline = self.visualizer.generate_timeline(execution, events)

        assert "```" in timeline
        assert "Timeline" in timeline
        assert "execution_started" in timeline
        assert "stage_updated" in timeline
        assert "task_updated" in timeline
        assert "🚀" in timeline  # execution_started icon
        assert "📍" in timeline  # stage_updated icon
        assert "✏️" in timeline  # task_updated icon

    def test_generate_timeline_empty(self):
        """Test timeline with no events"""
        timeline = self.visualizer.generate_timeline({}, [])

        assert "```" in timeline
        assert "Timeline" in timeline

    # ========== Skill Chart Tests ==========

    def test_generate_skill_chart(self):
        """Test generating skill proficiency chart"""
        skills = [
            {"skill_id": "python", "name": "Python", "category": "technical", "current_level": 4, "completions": 30},
            {"skill_id": "docker", "name": "Docker", "category": "tool", "current_level": 3, "completions": 15},
            {"skill_id": "agile", "name": "Agile", "category": "process", "current_level": 2, "completions": 8}
        ]

        chart = self.visualizer.generate_skill_chart(skills)

        assert "```" in chart
        assert "Skill Proficiency" in chart
        assert "TECHNICAL" in chart
        assert "TOOL" in chart
        assert "PROCESS" in chart
        assert "Python" in chart
        assert "★" in chart  # Filled stars
        assert "☆" in chart  # Empty stars

    def test_generate_skill_chart_empty(self):
        """Test skill chart with no skills"""
        chart = self.visualizer.generate_skill_chart([])

        assert "```" in chart
        assert "Skill Proficiency" in chart

    def test_generate_skill_chart_star_count(self):
        """Test skill chart has correct star counts"""
        skills = [
            {"skill_id": "s1", "name": "Skill1", "category": "cat", "current_level": 3, "completions": 0}
        ]

        chart = self.visualizer.generate_skill_chart(skills)

        # Level 3 should have 3 filled stars and 2 empty
        assert "★★★☆☆" in chart

    # ========== Learning Path Map Tests ==========

    def test_generate_learning_path_map(self):
        """Test generating learning path visualization"""
        path = {
            "name": "Developer Path",
            "modules": [
                {"module_id": "basics", "id": "basics", "required": True, "prerequisites": []},
                {"module_id": "intermediate", "id": "intermediate", "required": True, "prerequisites": ["basics"]},
                {"module_id": "advanced", "id": "advanced", "required": False, "prerequisites": ["intermediate"]}
            ],
            "certification": {"name": "Certified Developer"}
        }

        progress = {"modules_completed": ["basics"]}

        diagram = self.visualizer.generate_learning_path_map(path, progress)

        assert "```mermaid" in diagram
        assert "flowchart TD" in diagram
        assert "basics" in diagram
        assert "intermediate" in diagram
        assert "basics --> intermediate" in diagram
        assert "🏆" in diagram  # Certification
        assert "Certified Developer" in diagram

    def test_generate_learning_path_map_no_progress(self):
        """Test learning path map without progress"""
        path = {
            "modules": [
                {"module_id": "m1", "required": True},
                {"module_id": "m2", "required": True, "prerequisites": ["m1"]}
            ]
        }

        diagram = self.visualizer.generate_learning_path_map(path)

        assert "```mermaid" in diagram
        assert "m1 --> m2" in diagram

    def test_generate_learning_path_map_no_certification(self):
        """Test learning path map without certification"""
        path = {
            "modules": [{"module_id": "m1", "required": True}],
            "certification": None
        }

        diagram = self.visualizer.generate_learning_path_map(path)

        assert "🏆" not in diagram

    # ========== Dashboard Tests ==========

    def test_generate_dashboard(self):
        """Test generating comprehensive dashboard"""
        stats = {
            "total_workflows": 10,
            "workflow_templates": 3,
            "total_executions": 50,
            "total_skills": 15,
            "total_learning_paths": 5,
            "executions_by_status": {
                "completed": 30,
                "running": 15,
                "failed": 5
            }
        }

        recent_executions = [
            {"name": "Project Alpha", "status": "completed"},
            {"name": "Project Beta", "status": "running"},
            {"name": "Project Gamma", "status": "failed"}
        ]

        skills = [
            {"skill_id": "s1", "name": "Python", "current_level": 5, "completions": 50},
            {"skill_id": "s2", "name": "Docker", "current_level": 3, "completions": 20}
        ]

        dashboard = self.visualizer.generate_dashboard(stats, recent_executions, skills)

        assert "```" in dashboard
        assert "WORKFLOW ENGINE DASHBOARD" in dashboard
        assert "Workflows: 10" in dashboard
        assert "Templates: 3" in dashboard
        assert "Executions: 50" in dashboard
        assert "Skills: 15" in dashboard
        assert "Learning Paths: 5" in dashboard
        assert "completed: 30" in dashboard or "30" in dashboard
        assert "Project Alpha" in dashboard
        assert "Python" in dashboard
        assert "★" in dashboard

    def test_generate_dashboard_minimal(self):
        """Test dashboard with minimal stats"""
        stats = {
            "total_workflows": 0,
            "workflow_templates": 0,
            "total_executions": 0,
            "total_skills": 0,
            "total_learning_paths": 0
        }

        dashboard = self.visualizer.generate_dashboard(stats)

        assert "WORKFLOW ENGINE DASHBOARD" in dashboard
        assert "Workflows: 0" in dashboard

    def test_generate_dashboard_no_extras(self):
        """Test dashboard without recent executions or skills"""
        stats = {"total_workflows": 5, "total_executions": 10,
                 "total_skills": 3, "total_learning_paths": 2,
                 "workflow_templates": 1}

        dashboard = self.visualizer.generate_dashboard(stats)

        assert "WORKFLOW ENGINE DASHBOARD" in dashboard
        # Should not have Recent Executions or Top Skills sections
        assert "Recent Executions" not in dashboard or dashboard.count("Recent Executions") == 0

    # ========== Gantt Chart Tests ==========

    def test_generate_gantt(self):
        """Test generating Gantt chart"""
        workflow = {
            "definition": {
                "name": "Product Development",
                "stages": [
                    {
                        "id": "design",
                        "name": "Design",
                        "type": "design",
                        "duration_days": 14,
                        "tasks": [
                            {"id": "research", "name": "Research"},
                            {"id": "wireframe", "name": "Wireframes"}
                        ]
                    },
                    {
                        "id": "build",
                        "name": "Build",
                        "type": "poc",
                        "duration_days": 21
                    }
                ]
            }
        }

        gantt = self.visualizer.generate_gantt(workflow)

        assert "```mermaid" in gantt
        assert "gantt" in gantt
        assert "title Product Development Timeline" in gantt
        assert "dateFormat YYYY-MM-DD" in gantt
        assert "section Design" in gantt
        assert "section Build" in gantt
        assert "Research" in gantt
        assert "Wireframes" in gantt

    def test_generate_gantt_custom_start_date(self):
        """Test Gantt chart with custom start date"""
        workflow = {
            "definition": {
                "name": "Project",
                "stages": [{"id": "s1", "name": "Stage 1"}]
            }
        }

        gantt = self.visualizer.generate_gantt(workflow, start_date="2025-06-01")

        assert "```mermaid" in gantt
        assert "gantt" in gantt

    def test_generate_gantt_no_tasks(self):
        """Test Gantt chart for stages without tasks"""
        workflow = {
            "definition": {
                "name": "Simple Workflow",
                "stages": [
                    {"id": "phase1", "name": "Phase 1", "duration_days": 7},
                    {"id": "phase2", "name": "Phase 2", "duration_days": 14}
                ]
            }
        }

        gantt = self.visualizer.generate_gantt(workflow)

        assert "Phase 1 work" in gantt
        assert "Phase 2 work" in gantt


class TestWorkflowVisualizerEdgeCases:
    """Edge case tests for WorkflowVisualizer"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.visualizer = WorkflowVisualizer()

    def test_unicode_in_names(self):
        """Test handling unicode characters in names"""
        workflow = {
            "definition": {
                "stages": [
                    {"id": "设计", "name": "设计阶段 📐"},
                    {"id": "构建", "name": "构建阶段 🏗️"}
                ]
            }
        }

        diagram = self.visualizer.generate_workflow_diagram(workflow)

        assert "设计阶段" in diagram
        assert "📐" in diagram

    def test_special_characters_in_names(self):
        """Test handling special characters"""
        stage = {
            "tasks": [
                {"id": "t1", "name": "Task with 'quotes'", "dependencies": []},
                {"id": "t2", "name": "Task & ampersand", "dependencies": ["t1"]}
            ]
        }

        diagram = self.visualizer.generate_task_diagram(stage)

        assert "quotes" in diagram
        assert "ampersand" in diagram

    def test_long_names_truncation(self):
        """Test long names in skill chart"""
        skills = [
            {
                "skill_id": "long",
                "name": "This is a very long skill name that should be truncated",
                "category": "test",
                "current_level": 3,
                "completions": 10
            }
        ]

        chart = self.visualizer.generate_skill_chart(skills)

        # Name should be truncated to 20 chars
        assert len(chart) > 0  # Just ensure it doesn't error

    def test_blocked_stage_status(self):
        """Test blocked stage status styling"""
        workflow = {
            "definition": {
                "stages": [{"id": "blocked_stage", "name": "Blocked"}]
            }
        }

        execution_status = {
            "stage_details": [{"stage_id": "blocked_stage", "status": "blocked"}]
        }

        diagram = self.visualizer.generate_workflow_diagram(workflow, execution_status)

        assert "class blocked_stage blocked" in diagram
        assert "classDef blocked" in diagram


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
