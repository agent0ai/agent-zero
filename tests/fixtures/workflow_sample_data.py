"""
Sample Data Generator for Workflow Engine.
Creates realistic sample data for testing, demos, and UI validation.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager


class WorkflowSampleDataGenerator:
    """Generate comprehensive sample data for the workflow engine"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to the actual workflow database
            base_path = Path(__file__).parent.parent.parent
            db_path = str(base_path / "instruments/custom/workflow_engine/data/workflow.db")

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.manager = WorkflowEngineManager(db_path)
        self.db_path = db_path

    def generate_all(self) -> dict:
        """Generate complete sample dataset"""
        results = {
            "skills": self.create_sample_skills(),
            "learning_paths": self.create_sample_learning_paths(),
            "workflows": self.create_sample_workflows(),
            "executions": self.create_sample_executions(),
            "skill_progress": self.create_sample_skill_progress()
        }

        # Get summary stats
        stats = self.manager.get_stats()
        results["summary"] = {
            "total_workflows": stats.get("total_workflows", 0),
            "total_executions": stats.get("total_executions", 0),
            "total_skills": stats.get("total_skills", 0),
            "total_learning_paths": stats.get("total_learning_paths", 0),
            "db_path": self.db_path
        }

        return results

    def create_sample_skills(self) -> list:
        """Create sample skills across various categories"""
        skills = [
            # Technical skills
            ("python_fundamentals", "Python Fundamentals", "technical",
             "Core Python programming concepts and syntax"),
            ("python_async", "Async Python", "technical",
             "Asynchronous programming with asyncio"),
            ("python_testing", "Python Testing", "technical",
             "Unit testing, pytest, and test-driven development"),
            ("api_design", "RESTful API Design", "technical",
             "Designing clean, maintainable APIs"),
            ("database_design", "Database Design", "technical",
             "Schema design, normalization, and query optimization"),
            ("frontend_basics", "Frontend Basics", "technical",
             "HTML, CSS, JavaScript fundamentals"),

            # Tool skills
            ("git_workflow", "Git Workflow", "tool",
             "Version control best practices"),
            ("docker", "Docker Containers", "tool",
             "Containerization and Docker Compose"),
            ("kubernetes", "Kubernetes", "tool",
             "Container orchestration and K8s deployment"),
            ("ci_cd", "CI/CD Pipelines", "tool",
             "Continuous integration and deployment"),

            # Process skills
            ("agile", "Agile Methodology", "process",
             "Scrum, sprint planning, and agile practices"),
            ("code_review", "Code Review", "process",
             "Effective code review techniques"),
            ("documentation", "Technical Documentation", "process",
             "Writing clear technical docs"),

            # Domain skills
            ("security_basics", "Security Basics", "domain",
             "Application security fundamentals"),
            ("cloud_architecture", "Cloud Architecture", "domain",
             "Cloud-native application design"),
            ("data_analysis", "Data Analysis", "domain",
             "Data processing and analysis techniques"),

            # Soft skills
            ("communication", "Technical Communication", "soft_skill",
             "Clear technical communication"),
            ("problem_solving", "Problem Solving", "soft_skill",
             "Systematic approach to problem solving"),
            ("mentoring", "Mentoring", "soft_skill",
             "Teaching and guiding others")
        ]

        created = []
        for skill_id, name, category, description in skills:
            result = self.manager.register_skill(
                skill_id=skill_id,
                name=name,
                category=category,
                description=description,
                related_tools=self._get_related_tools(category)
            )
            created.append(result)

        return created

    def _get_related_tools(self, category: str) -> list:
        """Get related tools based on skill category"""
        tool_mappings = {
            "technical": ["code_execution", "code_review_tool"],
            "tool": ["terminal", "docker_tool"],
            "process": ["project_management", "documentation_tool"],
            "domain": ["analysis_tool", "monitoring_tool"],
            "soft_skill": ["communication_tool", "collaboration_tool"]
        }
        return tool_mappings.get(category, [])

    def create_sample_learning_paths(self) -> list:
        """Create sample learning paths"""
        paths = [
            {
                "path_id": "python_developer",
                "name": "Python Developer Path",
                "target_role": "developer",
                "description": "Complete path to become a proficient Python developer",
                "estimated_hours": 60.0,
                "modules": [
                    {"module_id": "py_basics", "name": "Python Basics", "required": True},
                    {"module_id": "py_oop", "name": "Object-Oriented Python", "required": True, "prerequisites": ["py_basics"]},
                    {"module_id": "py_async", "name": "Async Programming", "required": True, "prerequisites": ["py_oop"]},
                    {"module_id": "py_testing", "name": "Testing & TDD", "required": True, "prerequisites": ["py_basics"]},
                    {"module_id": "py_advanced", "name": "Advanced Topics", "required": False, "prerequisites": ["py_async", "py_testing"]}
                ],
                "certification": {
                    "name": "Certified Python Developer",
                    "badge": "python_dev",
                    "requirements": {"min_score": 80, "modules_required": ["py_basics", "py_oop", "py_async", "py_testing"]}
                }
            },
            {
                "path_id": "devops_engineer",
                "name": "DevOps Engineer Path",
                "target_role": "devops",
                "description": "Learn DevOps practices and tools",
                "estimated_hours": 80.0,
                "modules": [
                    {"module_id": "devops_intro", "name": "DevOps Introduction", "required": True},
                    {"module_id": "docker_mastery", "name": "Docker Mastery", "required": True, "prerequisites": ["devops_intro"]},
                    {"module_id": "k8s_basics", "name": "Kubernetes Basics", "required": True, "prerequisites": ["docker_mastery"]},
                    {"module_id": "ci_cd_pipelines", "name": "CI/CD Pipelines", "required": True, "prerequisites": ["docker_mastery"]},
                    {"module_id": "monitoring", "name": "Monitoring & Observability", "required": False}
                ],
                "certification": {
                    "name": "DevOps Professional",
                    "badge": "devops_pro"
                }
            },
            {
                "path_id": "team_lead",
                "name": "Technical Team Lead Path",
                "target_role": "lead",
                "description": "Develop leadership and technical management skills",
                "estimated_hours": 40.0,
                "modules": [
                    {"module_id": "leadership_basics", "name": "Technical Leadership", "required": True},
                    {"module_id": "code_review_mastery", "name": "Code Review Mastery", "required": True},
                    {"module_id": "agile_leadership", "name": "Agile Leadership", "required": True},
                    {"module_id": "mentoring_skills", "name": "Mentoring Skills", "required": True},
                    {"module_id": "architecture_decisions", "name": "Architecture Decisions", "required": False}
                ],
                "certification": {
                    "name": "Technical Team Lead",
                    "badge": "tech_lead"
                }
            }
        ]

        created = []
        for path in paths:
            result = self.manager.create_learning_path(
                path_id=path["path_id"],
                name=path["name"],
                target_role=path["target_role"],
                description=path["description"],
                modules=path["modules"],
                estimated_hours=path["estimated_hours"],
                certification=path.get("certification")
            )
            created.append(result)

        return created

    def create_sample_workflows(self) -> list:
        """Create sample workflow definitions"""
        workflows = []

        # Product Development Workflow
        pd_result = self.manager.create_workflow(
            name="Product Development Workflow",
            description="Standard product development lifecycle",
            stages=[
                {
                    "id": "discovery",
                    "name": "Discovery & Planning",
                    "type": "design",
                    "duration_days": 14,
                    "exit_criteria": [
                        {"id": "requirements", "name": "Requirements documented"},
                        {"id": "stakeholder_approval", "name": "Stakeholder sign-off"}
                    ],
                    "tasks": [
                        {"id": "research", "name": "Market Research", "role": "analyst", "dependencies": []},
                        {"id": "user_interviews", "name": "User Interviews", "role": "ux", "dependencies": []},
                        {"id": "requirements_doc", "name": "Requirements Document", "role": "pm", "dependencies": ["research", "user_interviews"]}
                    ]
                },
                {
                    "id": "design",
                    "name": "Design Phase",
                    "type": "design",
                    "duration_days": 21,
                    "exit_criteria": [
                        {"id": "wireframes", "name": "Wireframes approved"},
                        {"id": "tech_spec", "name": "Technical spec approved"}
                    ],
                    "tasks": [
                        {"id": "wireframing", "name": "Create Wireframes", "role": "designer", "dependencies": []},
                        {"id": "tech_design", "name": "Technical Design", "role": "architect", "dependencies": []},
                        {"id": "review", "name": "Design Review", "role": "team", "dependencies": ["wireframing", "tech_design"]}
                    ],
                    "approval_required": True
                },
                {
                    "id": "poc",
                    "name": "Proof of Concept",
                    "type": "poc",
                    "duration_days": 14,
                    "exit_criteria": [
                        {"id": "demo", "name": "Working demo available"}
                    ]
                },
                {
                    "id": "mvp",
                    "name": "MVP Development",
                    "type": "mvp",
                    "duration_days": 42,
                    "exit_criteria": [
                        {"id": "features", "name": "Core features complete"},
                        {"id": "tests", "name": "Test coverage > 80%"}
                    ],
                    "tasks": [
                        {"id": "backend", "name": "Backend Development", "role": "backend_dev", "dependencies": []},
                        {"id": "frontend", "name": "Frontend Development", "role": "frontend_dev", "dependencies": []},
                        {"id": "integration", "name": "Integration", "role": "fullstack_dev", "dependencies": ["backend", "frontend"]},
                        {"id": "testing", "name": "Testing", "role": "qa", "dependencies": ["integration"]}
                    ]
                },
                {
                    "id": "production",
                    "name": "Production Release",
                    "type": "production",
                    "duration_days": 7,
                    "approval_required": True
                },
                {
                    "id": "support",
                    "name": "Support & Iteration",
                    "type": "support",
                    "duration_days": 90
                }
            ]
        )
        workflows.append(pd_result)

        # Client Integration Workflow
        ci_result = self.manager.create_workflow(
            name="Client Integration Project",
            description="Standard client integration workflow",
            stages=[
                {
                    "id": "kickoff",
                    "name": "Project Kickoff",
                    "type": "custom",
                    "duration_days": 7,
                    "exit_criteria": [
                        {"id": "contract", "name": "Contract signed"},
                        {"id": "team", "name": "Team assigned"}
                    ]
                },
                {
                    "id": "analysis",
                    "name": "Requirements Analysis",
                    "type": "design",
                    "duration_days": 14
                },
                {
                    "id": "development",
                    "name": "Development",
                    "type": "custom",
                    "duration_days": 28
                },
                {
                    "id": "uat",
                    "name": "User Acceptance Testing",
                    "type": "custom",
                    "duration_days": 14,
                    "approval_required": True
                },
                {
                    "id": "go_live",
                    "name": "Go Live",
                    "type": "production",
                    "duration_days": 7
                },
                {
                    "id": "hypercare",
                    "name": "Hypercare Support",
                    "type": "support",
                    "duration_days": 30
                }
            ]
        )
        workflows.append(ci_result)

        # Quick Sprint Workflow
        sprint_result = self.manager.create_workflow(
            name="Two-Week Sprint",
            description="Agile sprint workflow",
            stages=[
                {
                    "id": "planning",
                    "name": "Sprint Planning",
                    "type": "custom",
                    "duration_days": 1
                },
                {
                    "id": "development",
                    "name": "Development",
                    "type": "custom",
                    "duration_days": 8,
                    "tasks": [
                        {"id": "stories", "name": "Complete User Stories", "dependencies": []},
                        {"id": "code_review", "name": "Code Reviews", "dependencies": ["stories"]},
                        {"id": "testing", "name": "Testing", "dependencies": ["stories"]}
                    ]
                },
                {
                    "id": "review",
                    "name": "Sprint Review",
                    "type": "custom",
                    "duration_days": 1
                },
                {
                    "id": "retro",
                    "name": "Retrospective",
                    "type": "custom",
                    "duration_days": 1
                }
            ]
        )
        workflows.append(sprint_result)

        return workflows

    def create_sample_executions(self) -> list:
        """Create sample workflow executions"""
        executions = []

        # Get workflows
        workflows = self.manager.list_workflows()

        if len(workflows) >= 1:
            # Start and progress first workflow
            wf = workflows[0]
            exec1 = self.manager.start_workflow(
                workflow_id=wf['workflow_id'],
                execution_name=f"{wf['name']} - Q1 2024",
                context={"quarter": "Q1", "year": "2024", "priority": "high"}
            )
            executions.append(exec1)

            # Advance some stages
            if 'execution_id' in exec1:
                self.manager.advance_stage(exec1['execution_id'], force=True)

            # Create another execution
            exec2 = self.manager.start_workflow(
                workflow_id=wf['workflow_id'],
                execution_name=f"{wf['name']} - Q2 2024",
                context={"quarter": "Q2", "year": "2024", "priority": "medium"}
            )
            executions.append(exec2)

        if len(workflows) >= 2:
            # Start second workflow
            wf2 = workflows[1]
            exec3 = self.manager.start_workflow(
                workflow_id=wf2['workflow_id'],
                execution_name="ACME Corp Integration",
                context={"client": "ACME Corp", "contract_value": 75000}
            )
            executions.append(exec3)

            # Advance and complete some stages
            if 'execution_id' in exec3:
                self.manager.advance_stage(exec3['execution_id'], force=True)
                self.manager.advance_stage(exec3['execution_id'], force=True)

        if len(workflows) >= 3:
            # Start multiple sprints
            wf3 = workflows[2]
            for sprint_num in range(1, 4):
                exec = self.manager.start_workflow(
                    workflow_id=wf3['workflow_id'],
                    execution_name=f"Sprint {sprint_num}",
                    context={"sprint_number": sprint_num}
                )
                executions.append(exec)

                # Complete older sprints
                if sprint_num < 3 and 'execution_id' in exec:
                    for _ in range(4):
                        self.manager.advance_stage(exec['execution_id'], force=True)

        return executions

    def create_sample_skill_progress(self) -> dict:
        """Create sample skill progress for agents"""
        progress = {
            "agent_0": [],
            "agent_1": []
        }

        # Skill practice counts for realistic progression
        agent_0_skills = {
            "python_fundamentals": 45,
            "python_async": 25,
            "python_testing": 30,
            "git_workflow": 50,
            "docker": 20,
            "agile": 35,
            "code_review": 40,
            "communication": 25
        }

        agent_1_skills = {
            "python_fundamentals": 20,
            "api_design": 15,
            "docker": 30,
            "kubernetes": 25,
            "ci_cd": 35,
            "security_basics": 10
        }

        # Track usage for agent_0
        for skill_id, count in agent_0_skills.items():
            for _ in range(count):
                result = self.manager.track_skill_usage(
                    agent_id="agent_0",
                    skill_id=skill_id,
                    success=True
                )
            progress["agent_0"].append({"skill_id": skill_id, "completions": count})

        # Track usage for agent_1
        for skill_id, count in agent_1_skills.items():
            for _ in range(count):
                result = self.manager.track_skill_usage(
                    agent_id="agent_1",
                    skill_id=skill_id,
                    success=True
                )
            progress["agent_1"].append({"skill_id": skill_id, "completions": count})

        return progress

    def get_summary(self) -> dict:
        """Get summary of generated data"""
        stats = self.manager.get_stats()
        recent = self.manager.get_recent_executions(limit=10)
        top_skills = self.manager.get_top_skills(limit=10)

        return {
            "stats": stats,
            "recent_executions": recent,
            "top_skills": top_skills,
            "db_path": self.db_path
        }


def main():
    """Generate sample data when run directly"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate sample data for Workflow Engine")
    parser.add_argument("--db-path", type=str, help="Custom database path")
    parser.add_argument("--summary-only", action="store_true", help="Only show summary of existing data")
    args = parser.parse_args()

    generator = WorkflowSampleDataGenerator(args.db_path)

    if args.summary_only:
        summary = generator.get_summary()
        print("\n=== Workflow Engine Summary ===")
        print(f"Database: {generator.db_path}")
        print(f"\nStatistics:")
        for key, value in summary["stats"].items():
            print(f"  {key}: {value}")
        print(f"\nRecent Executions: {len(summary['recent_executions'])}")
        print(f"Top Skills: {len(summary['top_skills'])}")
    else:
        print("\n=== Generating Sample Data ===")
        results = generator.generate_all()

        print(f"\nGenerated:")
        print(f"  Skills: {len(results['skills'])}")
        print(f"  Learning Paths: {len(results['learning_paths'])}")
        print(f"  Workflows: {len(results['workflows'])}")
        print(f"  Executions: {len(results['executions'])}")

        print(f"\nSummary:")
        for key, value in results["summary"].items():
            print(f"  {key}: {value}")

        print("\nSample data generation complete!")


if __name__ == "__main__":
    main()
