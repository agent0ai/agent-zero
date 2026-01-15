# Workflow Training Tool

Manage skill development, training modules, and learning progressions for agents. Track proficiency levels, complete lessons, and follow structured learning paths to build expertise systematically.

## User Stories

### Story 1: Onboarding a New Agent
*"As a team lead, I want to onboard a new agent with the skills needed for their role."*

```
# Define the core skills for developers
{{workflow_training(
  action="define_skill",
  skill_id="python_basics",
  name="Python Fundamentals",
  category="technical",
  description="Core Python programming concepts"
)}}

{{workflow_training(
  action="define_skill",
  skill_id="git_workflow",
  name="Git Workflow",
  category="process",
  description="Version control with Git",
  prerequisites=[{"skill_id": "cli_basics", "min_level": 2}]
)}}

{{workflow_training(
  action="define_skill",
  skill_id="api_design",
  name="RESTful API Design",
  category="technical",
  prerequisites=[{"skill_id": "python_basics", "min_level": 3}]
)}}

# Create a learning path for developers
{{workflow_training(
  action="create_path",
  path_id="junior_developer",
  name="Junior Developer Onboarding",
  target_role="developer",
  description="Essential skills for new developers",
  estimated_hours=40,
  modules=[
    {"module_id": "python_fundamentals", "required": true},
    {"module_id": "git_essentials", "required": true},
    {"module_id": "api_basics", "required": true, "prerequisites": ["python_fundamentals"]}
  ],
  certification={
    "name": "Junior Developer Certified",
    "requirements": {
      "min_modules_completed": 3,
      "min_overall_score": 75,
      "required_skills": [
        {"skill_id": "python_basics", "min_level": 2},
        {"skill_id": "git_workflow", "min_level": 2}
      ]
    }
  }
)}}

# Enroll the new agent
{{workflow_training(action="enroll_path", path_id="junior_developer")}}
```

### Story 2: Self-Paced Learning
*"As an agent, I want to learn at my own pace and track my progress."*

```
# See available learning paths
{{workflow_training(action="list_paths", target_role="developer")}}

# Check my current skills
{{workflow_training(action="get_proficiency")}}

# Get personalized recommendations
{{workflow_training(action="get_recommendations")}}

# Start a lesson
{{workflow_training(
  action="start_lesson",
  module_id="python_fundamentals",
  lesson_id="functions"
)}}

# Complete the lesson with my score
{{workflow_training(
  action="complete_lesson",
  module_id="python_fundamentals",
  lesson_id="functions",
  score=92
)}}

# Check my updated progress
{{workflow_training(action="get_progress", path_id="junior_developer")}}
```

### Story 3: Skill Assessment & Leveling Up
*"As an agent, I want to practice skills and level up my proficiency."*

```
# Get a practice task for my current level
{{workflow_training(action="practice_task", skill_id="python_basics")}}

# After completing the practice, record my result
{{workflow_training(
  action="assess_skill",
  skill_id="python_basics",
  success=true,
  score=88
)}}

# Check if I leveled up
{{workflow_training(action="get_proficiency")}}

# Take a formal assessment
{{workflow_training(
  action="take_assessment",
  skill_id="python_basics",
  score=90
)}}
```

**Level Up Response:**
```
## Level Up! 🎉

**Skill:** python_basics
**New Level:** 3 (intermediate)
```

### Story 4: Creating Training Content
*"As a training coordinator, I want to create structured learning materials."*

```
# Create a training module with lessons
{{workflow_training(
  action="create_module",
  module_id="async_programming",
  name="Asynchronous Programming",
  description="Master async/await patterns in Python",
  skills_taught=["python_async", "concurrency"],
  skill_level_target=3,
  lessons=[
    {
      "id": "intro_async",
      "name": "Introduction to Async",
      "type": "concept",
      "duration_minutes": 20,
      "content": {
        "objectives": [
          "Understand why async is needed",
          "Learn async/await syntax"
        ],
        "introduction": "Async programming enables concurrent execution without threads.",
        "key_points": [
          "async functions return coroutines",
          "await suspends execution until result is ready",
          "Event loop manages concurrent tasks"
        ]
      }
    },
    {
      "id": "async_practice",
      "name": "Async Practice",
      "type": "guided_practice",
      "duration_minutes": 45,
      "content": {
        "objectives": ["Write async functions", "Handle multiple concurrent tasks"],
        "steps": [
          {"instruction": "Create an async function", "action": "async def fetch_data():"},
          {"instruction": "Use await for I/O", "action": "result = await api.get()"},
          {"instruction": "Run tasks concurrently", "action": "await asyncio.gather(*tasks)"}
        ]
      },
      "practice_task": {
        "prompt": "Build an async data fetcher that retrieves from 3 APIs concurrently",
        "tools_allowed": ["code"],
        "success_criteria": [
          "Uses asyncio.gather or similar",
          "Handles errors gracefully",
          "Demonstrates time savings"
        ],
        "max_attempts": 3
      }
    },
    {
      "id": "async_assessment",
      "name": "Async Assessment",
      "type": "assessment",
      "content": {
        "objectives": ["Verify async programming knowledge"]
      },
      "assessment": {
        "type": "task_completion",
        "passing_score": 80,
        "questions": [
          {
            "question": "What does 'await' do in Python?",
            "type": "multiple_choice",
            "options": [
              "Creates a new thread",
              "Pauses execution until the awaited coroutine completes",
              "Blocks the entire program",
              "Starts a subprocess"
            ],
            "correct_answer": 1,
            "points": 2
          }
        ]
      }
    }
  ]
)}}

# Get the module details
{{workflow_training(action="get_module", module_id="async_programming")}}
```

### Story 5: Team Skill Reporting
*"As a manager, I want to see the skill levels across my team."*

```
# Get a full skill report for an agent
{{workflow_training(action="skill_report", agent_id="agent_0")}}

# View the training dashboard
{{workflow_training(action="training_dashboard")}}

# List all skills by category
{{workflow_training(action="list_skills", category="technical")}}
```

**Skill Report Output:**
```
## Skill Proficiency Report

**Total Skills:** 5
**Average Level:** 2.4
**Total Practice Completions:** 47

### Technical
- Python Basics [★★★☆☆]
- Python Async [★★☆☆☆]
- JavaScript [★★☆☆☆]

### Process
- Agile [★★★☆☆]
- Git Workflow [★★☆☆☆]
```

### Story 6: Prerequisite-Based Learning
*"As a learner, I want to ensure I have the foundational skills before advancing."*

```
# Check skill prerequisites
{{workflow_training(action="get_skill", skill_id="api_design")}}

# Get recommendations based on prerequisites
{{workflow_training(action="get_recommendations")}}

# Response shows what I need first:
# "Prerequisites not met for api_design. Complete python_basics to level 3 first."
```

---

## Core Concepts

### Skills
Skills are tracked competencies with 5 proficiency levels:

| Level | Name | Description | Typical Completions |
|-------|------|-------------|---------------------|
| 1 | **Novice** | Basic understanding | 0 |
| 2 | **Beginner** | Can perform with guidance | 5+ |
| 3 | **Intermediate** | Can perform independently | 15+ |
| 4 | **Advanced** | Can optimize and improve | 30+ |
| 5 | **Expert** | Can teach and innovate | 50+ |

### Skill Categories
- **technical** - Programming, frameworks, tools
- **process** - Methodologies, workflows, CI/CD
- **domain** - Business domain knowledge
- **tool** - Specific tool proficiency (Docker, K8s, etc.)
- **soft_skill** - Communication, collaboration, leadership

### Training Modules
Structured courses containing:
- **Lessons** - Individual learning units with content
- **Practice Tasks** - Hands-on exercises with success criteria
- **Assessments** - Evaluations for proficiency verification

### Lesson Types
- `concept` - Theory and explanations
- `demonstration` - Showing how something works
- `guided_practice` - Step-by-step practice with hints
- `independent_practice` - Self-directed practice
- `assessment` - Evaluation and scoring

### Learning Paths
Role-targeted curricula with:
- Ordered modules (required/optional)
- Prerequisites between modules
- Certification requirements upon completion

---

## Available Actions

### Skill Management

| Action | Description |
|--------|-------------|
| `define_skill` | Define a new skill with proficiency levels |
| `get_skill` | Get skill details including prerequisites |
| `list_skills` | List all skills (optionally by category) |
| `assess_skill` | Record skill practice or assessment |
| `get_proficiency` | Get agent's current skill levels |

### Training Modules

| Action | Description |
|--------|-------------|
| `create_module` | Create a training module with lessons |
| `get_module` | Get module details and lesson list |
| `start_lesson` | Start a lesson and get its content |
| `complete_lesson` | Mark lesson as completed with score |

### Learning Paths

| Action | Description |
|--------|-------------|
| `create_path` | Create a learning path with modules |
| `list_paths` | List paths (optionally by target role) |
| `get_path` | Get path details and requirements |
| `enroll_path` | Enroll agent in a learning path |
| `get_progress` | Get learning progress for agent |

### Practice & Assessment

| Action | Description |
|--------|-------------|
| `practice_task` | Generate practice task for current skill level |
| `take_assessment` | Take a skill assessment |
| `get_recommendations` | Get personalized skill recommendations |

### Reporting

| Action | Description |
|--------|-------------|
| `skill_report` | Generate comprehensive skill report |
| `training_dashboard` | Get training overview dashboard |

---

## Detailed Action Reference

### define_skill
Define a new skill with optional custom proficiency levels.

```
{{workflow_training(
  action="define_skill",
  skill_id="kubernetes",
  name="Kubernetes Administration",
  category="tool",
  description="Container orchestration with Kubernetes",
  related_tools=["deployment_orchestrator"],
  prerequisites=[
    {"skill_id": "docker", "min_level": 3},
    {"skill_id": "linux_admin", "min_level": 2}
  ],
  proficiency_levels=[
    {"level": 1, "name": "novice", "criteria": ["Understand pod concepts"], "min_completions": 0},
    {"level": 2, "name": "beginner", "criteria": ["Can deploy simple apps"], "min_completions": 5},
    {"level": 3, "name": "intermediate", "criteria": ["Can configure services, ingress"], "min_completions": 15},
    {"level": 4, "name": "advanced", "criteria": ["Can troubleshoot production issues"], "min_completions": 30},
    {"level": 5, "name": "expert", "criteria": ["Can design cluster architecture"], "min_completions": 50}
  ]
)}}
```

### create_module
Create a comprehensive training module.

```
{{workflow_training(
  action="create_module",
  module_id="docker_basics",
  name="Docker Fundamentals",
  description="Learn containerization with Docker",
  skills_taught=["docker"],
  skill_level_target=2,
  lessons=[
    {
      "id": "containers_intro",
      "name": "What are Containers?",
      "type": "concept",
      "duration_minutes": 15,
      "content": {
        "objectives": ["Understand containers vs VMs", "Learn Docker architecture"],
        "introduction": "Containers package applications with their dependencies...",
        "key_points": ["Lightweight isolation", "Portable across environments", "Fast startup"]
      }
    },
    {
      "id": "first_container",
      "name": "Your First Container",
      "type": "guided_practice",
      "duration_minutes": 30,
      "content": {
        "steps": [
          {"instruction": "Pull an image", "action": "docker pull nginx"},
          {"instruction": "Run a container", "action": "docker run -d -p 80:80 nginx"},
          {"instruction": "Check running containers", "action": "docker ps"}
        ]
      },
      "practice_task": {
        "prompt": "Run a custom nginx container serving your own HTML",
        "success_criteria": ["Container is running", "Custom HTML is served", "Port is correctly mapped"]
      }
    }
  ]
)}}
```

### create_path
Create a role-targeted learning path.

```
{{workflow_training(
  action="create_path",
  path_id="devops_engineer",
  name="DevOps Engineer Path",
  target_role="devops",
  description="Complete DevOps skills from basics to advanced",
  estimated_hours=80,
  modules=[
    {"module_id": "linux_fundamentals", "required": true},
    {"module_id": "docker_basics", "required": true, "prerequisites": ["linux_fundamentals"]},
    {"module_id": "kubernetes_basics", "required": true, "prerequisites": ["docker_basics"]},
    {"module_id": "cicd_pipelines", "required": true, "prerequisites": ["docker_basics"]},
    {"module_id": "monitoring", "required": false, "prerequisites": ["kubernetes_basics"]}
  ],
  certification={
    "name": "DevOps Engineer Certification",
    "requirements": {
      "min_modules_completed": 4,
      "min_overall_score": 80,
      "required_skills": [
        {"skill_id": "docker", "min_level": 3},
        {"skill_id": "kubernetes", "min_level": 2},
        {"skill_id": "cicd", "min_level": 2}
      ]
    }
  }
)}}
```

### practice_task
Generate a practice task appropriate for current skill level.

```
{{workflow_training(action="practice_task", skill_id="python_async")}}
```

**Output (for intermediate level):**
```
## Practice Task: Python Async Programming

**Skill Level:** 3
**Type:** independent

### Task
Solve this problem applying Python Async Programming concepts:
Build an async web scraper that fetches 5 URLs concurrently and extracts their titles.

### Tools Available
code, deployment_orchestrator

### Hints
Disabled at this level

*Complete this task and use `assess_skill` to record your result.*
```

### training_dashboard
Get a comprehensive training overview.

```
{{workflow_training(action="training_dashboard")}}
```

**Output:**
```
## Training Dashboard

### Overview
- Skills Tracked: 8
- Average Proficiency: 2.6/5
- Learning Paths Enrolled: 2
- Available Paths: 4

### Quick Stats
- Total Skills Available: 15
- Learning Paths Available: 4
- Total Workflows: 3

### Top Skills
- Python Basics: Level 4
- Docker: Level 3
- Git Workflow: Level 3

### Active Learning
- DevOps Engineer Path: 3 modules completed
- Junior Developer Path: 2 modules completed
```

---

## Integration with Workflow Engine

The training tool shares the same database as `workflow_engine`:
- Skills are tracked across both tools
- Workflow tasks can improve related skills
- Learning paths can prepare agents for specific workflows

**Example: Skill tracking from workflow tasks**
```
# When a workflow task completes, track the skill
{{workflow_training(
  action="assess_skill",
  skill_id="deployment",
  success=true
)}}
```

**Example: Prerequisites for workflow roles**
```
# Before assigning architect role in workflow, check skills
{{workflow_training(action="get_proficiency")}}
# Ensure architecture_design skill >= level 3
```

---

## Target Roles

Learning paths can target these roles:
- `architect` - System and solution architects
- `developer` - Software developers
- `dba` - Database administrators
- `qa` - Quality assurance engineers
- `devops` - DevOps engineers
- `security` - Security specialists
- `pm` - Project managers
- `designer` - UI/UX designers
- `analyst` - Business analysts
- `generalist` - General/multi-role

---

## Proficiency Level Thresholds

Default progression (customizable per skill):

| Level | Name | Min Completions |
|-------|------|-----------------|
| 1 | Novice | 0 |
| 2 | Beginner | 5 |
| 3 | Intermediate | 15 |
| 4 | Advanced | 30 |
| 5 | Expert | 50 |

Agents level up automatically when they reach the completion threshold and pass assessments.

---

## Best Practices

### 1. Define Prerequisites
Create skill dependencies to ensure proper learning progression:
```
{{workflow_training(
  action="define_skill",
  skill_id="advanced_python",
  prerequisites=[{"skill_id": "python_basics", "min_level": 3}]
)}}
```

### 2. Use Practice Tasks Regularly
Regular practice accelerates skill development:
```
{{workflow_training(action="practice_task", skill_id="python_basics")}}
# Complete the task
{{workflow_training(action="assess_skill", skill_id="python_basics", success=true)}}
```

### 3. Track Real Work as Skill Practice
When completing actual work tasks, record them as skill practice:
```
# After completing a deployment
{{workflow_training(
  action="assess_skill",
  skill_id="deployment",
  success=true,
  score=95
)}}
```

### 4. Review Progress Regularly
Use the dashboard to identify skill gaps:
```
{{workflow_training(action="training_dashboard")}}
{{workflow_training(action="get_recommendations")}}
```

### 5. Create Role-Specific Paths
Design learning paths that prepare agents for specific workflow roles:
```
{{workflow_training(
  action="create_path",
  path_id="architect_track",
  target_role="architect",
  modules=[...]
)}}
```
