# 🤖 AI Solutioning - Operator Quick Reference

## Overview

This guide covers the complete AI solutioning workflow for operators using Agent Jumbo. As an operator, you'll deliver end-to-end AI solutions from discovery through deployment and optimization.

---

## 🚀 Quick Start

### 1. Start a New AI Solutioning Project

```
{{workflow_engine(
  action="create_from_template",
  template_path="templates/ai_solutioning.json",
  name="Client ABC - AI Automation Project"
)}}
```

### 2. Begin Execution

```
{{workflow_engine(
  action="start_workflow",
  workflow_name="Client ABC - AI Automation Project"
)}}
```

### 3. Track Progress

```
{{workflow_engine(action="get_status", execution_id=1)}}
```

---

## 📋 The AI Solutioning Workflow

| Stage | Duration | Key Activities |
|-------|----------|----------------|
| **Discovery** | 3 days | Customer intake, Business X-Ray, requirements |
| **Solution Design** | 5 days | Task classification, workflow design, architecture |
| **Proposal** | 2 days | ROI calculation, proposal creation, roadmap |
| **POC** | 14 days | Build proof of concept, demo to customer |
| **Implementation** | 30 days | Full solution development, testing |
| **Deployment** | 5 days | CI/CD, containerization, go-live |
| **Training** | 3 days | Customer training sessions |
| **Optimization** | Ongoing | Monitor, optimize, enhance |

### Stage 2: Solution Design & Architecture

| Tool | Action | Purpose |
|------|--------|---------|
| `ai_migration` | `classify_tasks` | Identify AI/Human tasks |
| `workflow_engine` | `create_workflow` | Design execution logic |
| `knowledge_base` | `search` | Consult architectural patterns |

**Architectural Excellence Guidelines:**

1. **Consult Patterns**: Always search `knowledge/custom/architectural_patterns/` before proposing a design. Familiarize yourself with EDA, Microservices, and Serverless patterns stored there.
2. **Trade-off Analysis**: Use the `tradeoff_analysis` skill to compare at least two architectural options (e.g., Centralized vs. Decentralized).
3. **WAF Alignment**: Ensure solutions align with the Azure Well-Architected Framework (Cost, Security, Reliability, Performance, Operational Excellence).

**Example Design Flow:**

```
# 1. Search for patterns
{{knowledge_search(query="Event Driven Architecture for AI Agents")}}

# 2. Perform Trade-off Analysis
I've compared the Monolithic vs Event-Driven approach for Acme Corp.
- Results: EDA provides better horizontal scale but higher initial complexity.
- Recommendation: EDA via Azure Service Bus.
```

---

## � Swarm Coordination (Advanced)

For extremely complex projects (e.g., analyzing 50+ business processes simultaneously), use the **SwarmBatch** tool.

**Purpose**: Spawns multiple "specialist" agents in parallel. Each agent focuses on a sub-task and reports back to the master architect.

**Example Swarm Command:**

```
{{swarm_batch(
  tasks=[
    "Analyze the manufacturing supply chain flow",
    "Evaluate the current inventory management database",
    "Identify security bottlenecks in the outbound shipping API"
  ],
  profile="architect"
)}}
```

## 📜 Architectural Memory (ADRs)

Agent Jumbo now features **Automated ADR Generation**.

- **Extraction**: Every time you conclude a technical decision, the `adr_generator` extension saves a record in `knowledge/custom/architectural_patterns/adrs/`.
- **Injection**: Future agents will automatically see these decisions in their system prompt via the `adr_context` extension. This ensures **Architectural Consistency** over time.

---

## �🛠️ Tools by Stage

### Stage 1: Discovery & Assessment

| Tool | Action | Purpose |
|------|--------|---------|
| `customer_lifecycle` | `add_customer` | Create customer record |
| `business_xray` | `full_analysis` | Analyze business processes |
| `customer_lifecycle` | `capture_requirement` | Document requirements |
| `ai_migration` | `start_assessment` | Evaluate AI readiness |

**Example Discovery Flow:**

```
# 1. Add customer
{{customer_lifecycle(
  action="add_customer",
  name="Acme Corp",
  contact_email="ceo@acme.com",
  industry="Manufacturing"
)}}

# 2. Run Business X-Ray
{{business_xray(
  action="full_analysis",
  company_name="Acme Corp",
  industry="Manufacturing"
)}}

# 3. Capture requirements
{{customer_lifecycle(
  action="capture_requirement",
  customer_id=1,
  title="Automate Invoice Processing",
  description="Process 500+ invoices/month, currently takes 2 FTEs",
  priority="high"
)}}

# 4. Assess AI readiness
{{ai_migration(
  action="start_assessment",
  company_name="Acme Corp",
  assessment_type="comprehensive"
)}}
```

---

### Stage 2: Solution Design

| Tool | Action | Purpose |
|------|--------|---------|
| `ai_migration` | `identify_quick_wins` | Find easy automation wins |
| `ai_migration` | `classify_tasks` | Human/AI/Hybrid classification |
| `ai_migration` | `design_workflow` | Create optimized workflows |
| `diagram_architect` | `analyze_architecture` | Design system architecture |
| `diagram_architect` | `export_all` | Generate diagrams |

**Example Design Flow:**

```
# 1. Identify quick wins
{{ai_migration(
  action="identify_quick_wins",
  assessment_id=1
)}}

# 2. Classify tasks
{{ai_migration(
  action="classify_tasks",
  assessment_id=1,
  process_name="Invoice Processing"
)}}

# 3. Design human-AI workflow
{{ai_migration(
  action="design_workflow",
  assessment_id=1,
  process_name="Invoice Processing"
)}}

# 4. Create architecture
{{diagram_architect(
  action="analyze_architecture",
  project_path="./client_projects/acme",
  include_ai_components=true
)}}
```

---

### Stage 3: Proposal & ROI

| Tool | Action | Purpose |
|------|--------|---------|
| `ai_migration` | `project_roi` | Calculate ROI projections |
| `ai_migration` | `generate_roadmap` | Create migration roadmap |
| `sales_generator` | `generate_proposal` | Create full proposal |
| `customer_lifecycle` | `propose_solution` | Record solution |

**Example Proposal Flow:**

```
# 1. Calculate ROI
{{ai_migration(
  action="project_roi",
  assessment_id=1,
  investment_amount=50000,
  time_horizon_years=3
)}}

# 2. Generate roadmap
{{ai_migration(
  action="generate_roadmap",
  assessment_id=1,
  phases=3
)}}

# 3. Create proposal
{{sales_generator(
  action="generate_proposal",
  customer_id=1,
  solution_name="AI-Powered Invoice Processing",
  pricing_tier="professional"
)}}
```

---

### Stage 4: POC Development

| Tool | Action | Purpose |
|------|--------|---------|
| `project_scaffold` | `scaffold_project` | Initialize project |
| `project_scaffold` | `add_component` | Add AI components |

**Example POC Setup:**

```
# Scaffold POC project
{{project_scaffold(
  action="scaffold_project",
  project_name="acme-invoice-poc",
  template="api/fastapi",
  features=["openai", "postgres", "docker"]
)}}
```

---

### Stage 5: Full Implementation

| Tool | Action | Purpose |
|------|--------|---------|
| `project_scaffold` | `scaffold_project` | Production project setup |
| Agent Jumbo | Code execution | Implement features |

---

### Stage 6: Deployment

| Tool | Action | Purpose |
|------|--------|---------|
| `deployment_orchestrator` | `generate_cicd` | CI/CD pipelines |
| `deployment_orchestrator` | `generate_docker` | Docker configuration |
| `deployment_orchestrator` | `setup_environment` | Infrastructure |
| `deployment_orchestrator` | `deploy` | Execute deployment |
| `deployment_orchestrator` | `health_check` | Verify deployment |

**Example Deployment Flow:**

```
# 1. Generate CI/CD
{{deployment_orchestrator(
  action="generate_cicd",
  project_path="./client_projects/acme",
  platform="github_actions",
  environments=["staging", "production"]
)}}

# 2. Generate Docker
{{deployment_orchestrator(
  action="generate_docker",
  project_path="./client_projects/acme",
  runtime="python",
  include_compose=true
)}}

# 3. Deploy
{{deployment_orchestrator(
  action="deploy",
  project_path="./client_projects/acme",
  environment="staging"
)}}

# 4. Health check
{{deployment_orchestrator(
  action="health_check",
  environment="staging",
  endpoints=["/health", "/api/v1/status"]
)}}
```

---

### Stage 7 & 8: Training & Optimization

| Tool | Action | Purpose |
|------|--------|---------|
| `customer_lifecycle` | `track_interaction` | Log customer interactions |
| `customer_lifecycle` | `progress_stage` | Update customer stage |
| `deployment_orchestrator` | `health_check` | Monitor solution |

---

## 📊 Skills & Training

### Your Skills Progress

```
{{workflow_training(
  action="get_proficiency",
  agent_id="operator_1"
)}}
```

### Track Skill Usage

When you complete a task successfully:

```
{{workflow_training(
  action="assess_skill",
  skill_id="business_analysis",
  agent_id="operator_1",
  score=90,
  notes="Completed Acme Corp analysis"
)}}
```

### Skill Levels

| Level | Completions | Description |
|-------|-------------|-------------|
| Novice | 0 | Just starting |
| Beginner | 5+ | Basic proficiency |
| Intermediate | 15+ | Comfortable |
| Advanced | 30+ | Highly proficient |
| Expert | 50+ | Master level |

---

## 📚 Learning Paths

### 1. Quick Start for Operators (6 hours)

Fast-track to start delivering AI solutions.

```
{{workflow_training(
  action="enroll_path",
  path_id="quick_start_operator",
  agent_id="operator_1"
)}}
```

### 2. AI Solution Architect (30 hours)

Complete certification path covering all skills.

```
{{workflow_training(
  action="enroll_path",
  path_id="ai_solution_architect",
  agent_id="operator_1"
)}}
```

---

## 🎯 Key Skills for Operators

### Discovery Skills

- `customer_intake` - Customer Intake & Qualification
- `business_analysis` - Business Analysis & X-Ray
- `requirements_gathering` - Requirements Gathering
- `ai_readiness_assessment` - AI Readiness Assessment

### Solution Design Skills

- `task_classification` - Task Classification (Human/AI/Hybrid)
- `workflow_design` - Human-AI Workflow Design
- `architecture_design` - AI Solution Architecture
- `prompt_engineering` - Prompt Engineering

### Sales Skills

- `roi_calculation` - ROI Calculation & Projection
- `proposal_creation` - Proposal Creation
- `roadmap_planning` - Migration Roadmap Planning

### Implementation Skills

- `project_scaffolding` - Project Scaffolding
- `ai_integration` - AI Model Integration
- `testing` - AI Solution Testing

### Deployment Skills

- `cicd_setup` - CI/CD Pipeline Setup
- `containerization` - Docker Containerization
- `cloud_deployment` - Cloud Deployment

### Support Skills

- `performance_monitoring` - AI Performance Monitoring
- `prompt_optimization` - Prompt Optimization
- `customer_success` - Customer Success Management

---

## 📈 Workflow Dashboard

Access the workflow dashboard in the UI:

**Settings → Workflows tab**

### Dashboard Views

1. **Dashboard** - Overview stats, recent executions
2. **Workflows** - All workflows with status
3. **Training** - Learning paths and progress
4. **Skills** - Skill inventory and proficiency

---

## 🔄 Typical Operator Day

### Morning Routine

```
# Check active workflows
{{workflow_engine(action="list_workflows", status="in_progress")}}

# Check pending tasks
{{workflow_engine(action="get_next_task", execution_id=1)}}

# Review customer pipeline
{{customer_lifecycle(action="list_customers", stage="prospect")}}
```

### Working on Projects

```
# Start working on a task
{{workflow_engine(action="start_task", execution_id=1, task_id="business_xray")}}

# Complete a task
{{workflow_engine(
  action="complete_task",
  execution_id=1,
  task_id="business_xray",
  result={"score": 85, "opportunities": 5}
)}}

# Advance to next stage
{{workflow_engine(
  action="advance_stage",
  execution_id=1,
  target_stage="solution_design"
)}}
```

### End of Day

```
# Update skill progress
{{workflow_training(
  action="assess_skill",
  skill_id="business_analysis",
  agent_id="operator_1",
  score=88
)}}

# Check learning progress
{{workflow_training(
  action="get_progress",
  path_id="ai_solution_architect",
  agent_id="operator_1"
)}}
```

---

## 📞 Customer Lifecycle Stages

| Stage | Description | Actions |
|-------|-------------|---------|
| `prospect` | Initial contact | Business X-Ray, discovery |
| `qualified` | Verified opportunity | Requirements, assessment |
| `proposal` | Proposal delivered | ROI, proposal, roadmap |
| `negotiation` | Contract discussion | Revisions, pricing |
| `contracted` | Deal signed | POC kickoff |
| `active` | Project underway | Implementation |
| `deployed` | Solution live | Training, support |
| `renewal` | Ongoing relationship | Optimization, upsell |

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Stage won't advance | Check exit criteria are met |
| Task blocked | Check dependencies completed |
| Customer not found | Verify customer_id exists |
| Proposal fails | Ensure requirements captured first |
| Deployment fails | Check health_check for errors |

---

## 📝 Quick Commands

```bash
# List all tools
{{response(text="List available tools")}}

# Get help on a tool
{{response(text="Help with business_xray tool")}}

# View workflow templates
{{workflow_engine(action="list_templates")}}

# Create workflow from template
{{workflow_engine(action="create_from_template", template_path="templates/ai_solutioning.json", name="My Project")}}
```

---

## ✅ Certification Requirements

### AI Solutioning Quickstart Certificate

- Complete Quick Start path (6 hours)
- Achieve Beginner level in 4 essential skills

### Certified AI Solution Architect

- Complete full path (30 hours)
- Achieve Intermediate level in all 20 skills
- Complete one end-to-end AI project

---

*Created for Agent Jumbo operators delivering AI solutions.*
