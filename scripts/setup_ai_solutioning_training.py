#!/usr/bin/env python3
"""
Setup AI Solutioning Training for Operators

This script creates:
1. Skills for AI Solution Architects
2. Learning paths for operators
3. Training modules with practical exercises

Run: python scripts/setup_ai_solutioning_training.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.helpers import files

def setup_training():
    """Setup complete AI Solutioning training program"""

    # Import workflow manager
    from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager

    db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
    manager = WorkflowEngineManager(db_path)

    print("=" * 60)
    print("Setting up AI Solutioning Training Program")
    print("=" * 60)

    # ========================================
    # CATEGORY 1: Discovery & Assessment Skills
    # ========================================
    discovery_skills = [
        {
            "skill_id": "customer_intake",
            "name": "Customer Intake & Qualification",
            "category": "discovery",
            "description": "Effectively capture customer information, qualify leads, and set up customer records",
            "prerequisites": [],
            "learning_resources": [
                "Customer Lifecycle Tool Documentation",
                "CRM Best Practices Guide"
            ]
        },
        {
            "skill_id": "business_analysis",
            "name": "Business Analysis & X-Ray",
            "category": "discovery",
            "description": "Use Business X-Ray tool to analyze customer's business processes, identify pain points, and score AI opportunities",
            "prerequisites": ["customer_intake"],
            "learning_resources": [
                "Business X-Ray Tool Guide",
                "Process Mapping Techniques"
            ]
        },
        {
            "skill_id": "requirements_gathering",
            "name": "Requirements Gathering",
            "category": "discovery",
            "description": "Capture detailed technical and business requirements, define success criteria",
            "prerequisites": ["customer_intake"],
            "learning_resources": [
                "Requirements Engineering Guide",
                "User Story Writing"
            ]
        },
        {
            "skill_id": "ai_readiness_assessment",
            "name": "AI Readiness Assessment",
            "category": "discovery",
            "description": "Evaluate customer's data quality, infrastructure, and team capabilities for AI adoption",
            "prerequisites": ["business_analysis"],
            "learning_resources": [
                "AI Readiness Checklist",
                "Data Quality Assessment Guide"
            ]
        },
    ]

    # ========================================
    # CATEGORY 2: Solution Design Skills
    # ========================================
    design_skills = [
        {
            "skill_id": "task_classification",
            "name": "Task Classification (Human/AI/Hybrid)",
            "category": "solution_design",
            "description": "Classify tasks as fully automatable, AI-assisted, or human-required using AI Migration tool",
            "prerequisites": ["business_analysis"],
            "learning_resources": [
                "AI Migration Tool Guide",
                "Automation Scoring Methodology"
            ]
        },
        {
            "skill_id": "workflow_design",
            "name": "Human-AI Workflow Design",
            "category": "solution_design",
            "description": "Design optimized workflows that combine human judgment with AI automation",
            "prerequisites": ["task_classification"],
            "learning_resources": [
                "Workflow Design Patterns",
                "Human-in-the-Loop Architectures"
            ]
        },
        {
            "skill_id": "architecture_design",
            "name": "AI Solution Architecture",
            "category": "solution_design",
            "description": "Design technical architectures for AI solutions using Diagram Architect",
            "prerequisites": ["workflow_design"],
            "learning_resources": [
                "Diagram Architect Tool Guide",
                "Cloud Architecture Patterns"
            ]
        },
        {
            "skill_id": "prompt_engineering",
            "name": "Prompt Engineering",
            "category": "solution_design",
            "description": "Design effective prompts for AI models to achieve desired outputs",
            "prerequisites": [],
            "learning_resources": [
                "Prompt Engineering Guide",
                "Claude Best Practices"
            ]
        },
    ]

    # ========================================
    # CATEGORY 3: Sales & ROI Skills
    # ========================================
    sales_skills = [
        {
            "skill_id": "roi_calculation",
            "name": "ROI Calculation & Projection",
            "category": "sales",
            "description": "Calculate and project ROI for AI solutions at 1, 3, and 5 year horizons",
            "prerequisites": ["task_classification"],
            "learning_resources": [
                "ROI Calculation Guide",
                "AI Investment Analysis"
            ]
        },
        {
            "skill_id": "proposal_creation",
            "name": "Proposal Creation",
            "category": "sales",
            "description": "Generate professional proposals with pricing, timelines, and deliverables",
            "prerequisites": ["roi_calculation", "architecture_design"],
            "learning_resources": [
                "Sales Generator Tool Guide",
                "Proposal Writing Best Practices"
            ]
        },
        {
            "skill_id": "roadmap_planning",
            "name": "Migration Roadmap Planning",
            "category": "sales",
            "description": "Create phased implementation roadmaps for AI migrations",
            "prerequisites": ["workflow_design"],
            "learning_resources": [
                "Roadmap Planning Guide",
                "Agile Release Planning"
            ]
        },
    ]

    # ========================================
    # CATEGORY 4: Implementation Skills
    # ========================================
    implementation_skills = [
        {
            "skill_id": "project_scaffolding",
            "name": "Project Scaffolding",
            "category": "implementation",
            "description": "Generate project structures from templates using Project Scaffold tool",
            "prerequisites": ["architecture_design"],
            "learning_resources": [
                "Project Scaffold Tool Guide",
                "Project Structure Best Practices"
            ]
        },
        {
            "skill_id": "ai_integration",
            "name": "AI Model Integration",
            "category": "implementation",
            "description": "Integrate AI models (Claude, OpenAI, local models) into solutions",
            "prerequisites": ["prompt_engineering"],
            "learning_resources": [
                "Claude API Documentation",
                "Model Integration Patterns"
            ]
        },
        {
            "skill_id": "testing",
            "name": "AI Solution Testing",
            "category": "implementation",
            "description": "Write comprehensive tests for AI solutions including edge cases",
            "prerequisites": ["ai_integration"],
            "learning_resources": [
                "Testing AI Systems Guide",
                "pytest Best Practices"
            ]
        },
    ]

    # ========================================
    # CATEGORY 5: Deployment Skills
    # ========================================
    deployment_skills = [
        {
            "skill_id": "cicd_setup",
            "name": "CI/CD Pipeline Setup",
            "category": "deployment",
            "description": "Configure automated build, test, and deployment pipelines",
            "prerequisites": ["testing"],
            "learning_resources": [
                "Deployment Orchestrator Guide",
                "GitHub Actions Tutorial"
            ]
        },
        {
            "skill_id": "containerization",
            "name": "Docker Containerization",
            "category": "deployment",
            "description": "Create Docker images and compose files for AI solutions",
            "prerequisites": [],
            "learning_resources": [
                "Docker Best Practices",
                "Container Security Guide"
            ]
        },
        {
            "skill_id": "cloud_deployment",
            "name": "Cloud Deployment",
            "category": "deployment",
            "description": "Deploy AI solutions to cloud environments (AWS, GCP, Azure)",
            "prerequisites": ["cicd_setup", "containerization"],
            "learning_resources": [
                "Cloud Deployment Guide",
                "Infrastructure as Code"
            ]
        },
    ]

    # ========================================
    # CATEGORY 6: Support & Optimization Skills
    # ========================================
    support_skills = [
        {
            "skill_id": "performance_monitoring",
            "name": "AI Performance Monitoring",
            "category": "support",
            "description": "Monitor AI accuracy, latency, costs, and user satisfaction",
            "prerequisites": ["cloud_deployment"],
            "learning_resources": [
                "Observability Guide",
                "AI Metrics Dashboard"
            ]
        },
        {
            "skill_id": "prompt_optimization",
            "name": "Prompt Optimization",
            "category": "support",
            "description": "Refine prompts based on production data to improve AI performance",
            "prerequisites": ["prompt_engineering", "performance_monitoring"],
            "learning_resources": [
                "Prompt Iteration Guide",
                "A/B Testing Prompts"
            ]
        },
        {
            "skill_id": "customer_success",
            "name": "Customer Success Management",
            "category": "support",
            "description": "Manage ongoing customer relationships and ensure success",
            "prerequisites": ["customer_intake"],
            "learning_resources": [
                "Customer Lifecycle Guide",
                "Support Best Practices"
            ]
        },
    ]

    # Register all skills
    all_skills = (
        discovery_skills +
        design_skills +
        sales_skills +
        implementation_skills +
        deployment_skills +
        support_skills
    )

    print(f"\n📚 Registering {len(all_skills)} skills...")
    for skill in all_skills:
        result = manager.register_skill(
            skill_id=skill["skill_id"],
            name=skill["name"],
            category=skill["category"],
            description=skill.get("description", ""),
            prerequisites=skill.get("prerequisites", []),
            related_tools=skill.get("learning_resources", [])  # Map to related_tools
        )
        print(f"  ✓ {skill['name']} ({skill['category']})")

    # ========================================
    # LEARNING PATHS
    # ========================================
    learning_paths = [
        {
            "path_id": "ai_solution_architect",
            "name": "AI Solution Architect",
            "description": "Complete path to become an AI Solution Architect - from discovery through deployment",
            "target_role": "operator",
            "modules": [
                {
                    "module_id": "discovery_fundamentals",
                    "name": "Discovery Fundamentals",
                    "description": "Master customer discovery and business analysis",
                    "skills": ["customer_intake", "business_analysis", "requirements_gathering", "ai_readiness_assessment"],
                    "lessons": [
                        {"title": "Introduction to AI Solutioning", "content": "Overview of the AI solutioning process"},
                        {"title": "Using Customer Lifecycle Tool", "content": "Hands-on: Add a customer and capture requirements"},
                        {"title": "Business X-Ray Analysis", "content": "Hands-on: Run a full business analysis"},
                        {"title": "AI Readiness Assessment", "content": "Evaluate customer readiness for AI adoption"}
                    ],
                    "estimated_hours": 4
                },
                {
                    "module_id": "solution_design_mastery",
                    "name": "Solution Design Mastery",
                    "description": "Design effective AI solutions with human-AI workflows",
                    "skills": ["task_classification", "workflow_design", "architecture_design", "prompt_engineering"],
                    "lessons": [
                        {"title": "Task Classification Framework", "content": "Classify tasks as human/AI/hybrid"},
                        {"title": "Workflow Design Patterns", "content": "Design human-in-the-loop workflows"},
                        {"title": "Architecture with Diagram Architect", "content": "Generate system diagrams"},
                        {"title": "Prompt Engineering Basics", "content": "Write effective AI prompts"}
                    ],
                    "estimated_hours": 6
                },
                {
                    "module_id": "sales_and_roi",
                    "name": "Sales & ROI",
                    "description": "Create compelling proposals with clear ROI",
                    "skills": ["roi_calculation", "proposal_creation", "roadmap_planning"],
                    "lessons": [
                        {"title": "ROI Calculation Methods", "content": "Calculate 1/3/5 year ROI projections"},
                        {"title": "Using Sales Generator", "content": "Generate professional proposals"},
                        {"title": "Roadmap Planning", "content": "Create phased implementation plans"}
                    ],
                    "estimated_hours": 3
                },
                {
                    "module_id": "implementation_excellence",
                    "name": "Implementation Excellence",
                    "description": "Build production-ready AI solutions",
                    "skills": ["project_scaffolding", "ai_integration", "testing"],
                    "lessons": [
                        {"title": "Project Setup", "content": "Scaffold projects from templates"},
                        {"title": "AI Model Integration", "content": "Connect Claude and other AI models"},
                        {"title": "Testing AI Solutions", "content": "Write comprehensive tests"}
                    ],
                    "estimated_hours": 8
                },
                {
                    "module_id": "deployment_operations",
                    "name": "Deployment & Operations",
                    "description": "Deploy and operate AI solutions in production",
                    "skills": ["cicd_setup", "containerization", "cloud_deployment"],
                    "lessons": [
                        {"title": "CI/CD Pipeline Setup", "content": "Configure automated deployments"},
                        {"title": "Docker Containerization", "content": "Package applications for deployment"},
                        {"title": "Cloud Deployment", "content": "Deploy to production environments"}
                    ],
                    "estimated_hours": 5
                },
                {
                    "module_id": "optimization_support",
                    "name": "Optimization & Support",
                    "description": "Optimize AI performance and ensure customer success",
                    "skills": ["performance_monitoring", "prompt_optimization", "customer_success"],
                    "lessons": [
                        {"title": "Monitoring AI Performance", "content": "Track metrics and KPIs"},
                        {"title": "Prompt Iteration", "content": "Improve prompts based on data"},
                        {"title": "Customer Success", "content": "Manage ongoing relationships"}
                    ],
                    "estimated_hours": 4
                }
            ],
            "certification": {
                "name": "Certified AI Solution Architect",
                "requirements": [
                    "Complete all modules",
                    "Achieve Intermediate level in all skills",
                    "Complete one end-to-end AI Solutioning project"
                ]
            },
            "total_hours": 30
        },
        {
            "path_id": "quick_start_operator",
            "name": "Quick Start for Operators",
            "description": "Fast-track path to start delivering AI solutions",
            "target_role": "operator",
            "modules": [
                {
                    "module_id": "essentials",
                    "name": "Essential Skills",
                    "description": "Core skills to start AI solutioning",
                    "skills": ["customer_intake", "business_analysis", "task_classification", "prompt_engineering"],
                    "lessons": [
                        {"title": "AI Solutioning Overview", "content": "Quick intro to the process"},
                        {"title": "Essential Tools", "content": "Customer Lifecycle + Business X-Ray + AI Migration"},
                        {"title": "Quick Win Identification", "content": "Find fast automation opportunities"}
                    ],
                    "estimated_hours": 2
                },
                {
                    "module_id": "first_project",
                    "name": "Your First AI Project",
                    "description": "End-to-end walkthrough of a simple AI solution",
                    "skills": ["workflow_design", "proposal_creation", "project_scaffolding"],
                    "lessons": [
                        {"title": "Project Walkthrough", "content": "From discovery to deployment"},
                        {"title": "Using Workflow Templates", "content": "Start from AI Solutioning template"},
                        {"title": "Hands-on Exercise", "content": "Build a simple AI automation"}
                    ],
                    "estimated_hours": 4
                }
            ],
            "certification": {
                "name": "AI Solutioning Quickstart Certificate",
                "requirements": [
                    "Complete both modules",
                    "Achieve Beginner level in essential skills"
                ]
            },
            "total_hours": 6
        }
    ]

    print(f"\n📖 Creating {len(learning_paths)} learning paths...")
    for path in learning_paths:
        result = manager.create_learning_path(
            path_id=path["path_id"],
            name=path["name"],
            description=path["description"],
            target_role=path["target_role"],
            modules=path["modules"],
            certification=path["certification"]
        )
        print(f"  ✓ {path['name']} ({path['total_hours']} hours)")
        for module in path["modules"]:
            print(f"      - {module['name']}")

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("AI Solutioning Training Setup Complete!")
    print("=" * 60)

    stats = manager.get_stats()
    print(f"""
Summary:
  Skills registered: {len(all_skills)}
  Learning paths: {len(learning_paths)}

Skill Categories:
  - Discovery & Assessment: {len(discovery_skills)}
  - Solution Design: {len(design_skills)}
  - Sales & ROI: {len(sales_skills)}
  - Implementation: {len(implementation_skills)}
  - Deployment: {len(deployment_skills)}
  - Support & Optimization: {len(support_skills)}

Learning Paths:
  1. AI Solution Architect (30 hours) - Complete certification path
  2. Quick Start for Operators (6 hours) - Fast-track intro

Next Steps:
  1. Start the AI Solutioning workflow:
     {{workflow_engine(action="create_from_template", template_path="templates/ai_solutioning.json", name="My First AI Project")}}

  2. Enroll in a learning path:
     {{workflow_training(action="enroll_path", path_id="quick_start_operator", agent_id="operator_1")}}

  3. Track skill progress:
     {{workflow_training(action="assess_skill", skill_id="customer_intake", agent_id="operator_1", score=85)}}

  4. View training dashboard in UI:
     Settings → Workflows → Training tab
""")

    return {
        "skills": len(all_skills),
        "paths": len(learning_paths),
        "categories": 6
    }


if __name__ == "__main__":
    result = setup_training()
    print("\n✅ Training setup successful!")
