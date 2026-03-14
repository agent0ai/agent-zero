# Customer Lifecycle & Virtual Team Integration Guide

## Overview

This guide covers the new **Customer Lifecycle Manager** and **Virtual Team Orchestrator** features added to Agent Jumbo.

### Features

- **Customer Lifecycle Manager**: Automates lead → customer → delivery cycle
- **Virtual Team Orchestrator**: Coordinates specialized AI agents (architect, developer, DBA, QA, DevOps)

## Installation

These features are installed as custom instruments in Agent Jumbo:

```
instruments/custom/
├── customer_lifecycle/
│   ├── lifecycle_db.py          # Database schema
│   ├── lifecycle_manager.py     # Business logic
│   └── data/                    # SQLite databases (auto-created)
└── virtual_team/
    ├── team_db.py               # Database schema
    ├── team_orchestrator.py     # Team coordination logic
    └── data/                    # SQLite databases (auto-created)
```

### Tool Integration

Tools are registered in `python/tools/`:

- `customer_lifecycle.py` - Customer lifecycle management tool
- `virtual_team.py` - Virtual team orchestration tool

Prompts are in `prompts/`:

- `agent.system.tool.customer_lifecycle.md` - Customer lifecycle tool documentation
- `agent.system.tool.virtual_team.md` - Virtual team tool documentation

## Quick Start

### Customer Lifecycle Example

```python
# 1. Capture lead
{{customer_lifecycle(
  action="capture_lead",
  name="Sarah Johnson",
  company="MedTech Inc",
  email="sarah@medtech.com",
  industry="Healthcare"
)}}
# Returns: customer_id = 1

# 2. Conduct requirements interview
{{customer_lifecycle(
  action="conduct_interview",
  customer_id=1,
  responses={
    "What business problem are you trying to solve?": "Need HIPAA-compliant patient portal",
    "What are your timeline expectations?": "6 months",
    "What is your budget range?": "$100k-$200k"
  }
)}}
# Returns: requirement_id = 1

# 3. Design solution
{{customer_lifecycle(
  action="design_solution",
  customer_id=1,
  requirement_id=1,
  solution_name="Patient Portal Platform"
)}}
# Returns: solution_id = 1

# 4. Generate proposal
{{customer_lifecycle(
  action="generate_proposal",
  customer_id=1,
  solution_id=1,
  pricing_model="fixed_price",
  discount_percentage=10
)}}
# Returns: proposal_id = 1

# 5. Track proposal
{{customer_lifecycle(
  action="track_proposal",
  proposal_id=1,
  status="sent"
)}}

# 6. Check customer health
{{customer_lifecycle(
  action="check_customer_health",
  customer_id=1
)}}
```

### Virtual Team Example

```python
# 1. Start workflow for full-stack development
{{virtual_team(
  action="start_workflow",
  workflow_name="Patient Portal Build",
  template="full_stack_development",
  customer_id=1,
  project_id=5
)}}
# Returns: workflow_id = 1, creates 7 tasks across all roles

# 2. Check workflow progress
{{virtual_team(
  action="get_workflow_progress",
  workflow_id=1
)}}
# Returns: progress_percentage, task statuses

# 3. Delegate specific task
{{virtual_team(
  action="delegate_to_specialist",
  task_name="Optimize database queries",
  specialist_role="dba",
  description="Optimize patient records query performance"
)}}

# 4. Monitor team dashboard
{{virtual_team(
  action="get_team_dashboard"
)}}
# Returns: active_agents, workload_by_role, task_stats
```

## Complete End-to-End Workflow

### Scenario: New Customer Project

```python
# === STEP 1: Capture Lead ===
{{customer_lifecycle(
  action="capture_lead",
  name="David Chen",
  company="RetailCo",
  email="david@retailco.com",
  industry="Retail",
  source="referral"
)}}
# customer_id = 2

# === STEP 2: Requirements Gathering ===
{{customer_lifecycle(
  action="conduct_interview",
  customer_id=2,
  responses={
    "What business problem are you trying to solve?": "Need real-time inventory management",
    "Who are the primary users?": "Warehouse staff (100) and managers (10)",
    "What are your main pain points?": "Manual tracking, no visibility, stock-outs",
    "What does success look like?": "Real-time updates, mobile access, predictive alerts",
    "What are your timeline expectations?": "Launch in 4 months",
    "What is your budget range?": "$75k-$150k"
  }
)}}
# requirement_id = 2

# === STEP 3: Solution Design ===
{{customer_lifecycle(
  action="design_solution",
  customer_id=2,
  requirement_id=2,
  solution_name="Real-Time Inventory Platform"
)}}
# solution_id = 2

# === STEP 4: Generate Proposal ===
{{customer_lifecycle(
  action="generate_proposal",
  customer_id=2,
  solution_id=2,
  pricing_model="milestone_based",
  discount_percentage=5
)}}
# proposal_id = 2

# === STEP 5: Send Proposal ===
{{customer_lifecycle(
  action="track_proposal",
  proposal_id=2,
  status="sent"
)}}

# ... Customer accepts proposal ...

# === STEP 6: Update Customer Stage ===
{{customer_lifecycle(
  action="track_proposal",
  proposal_id=2,
  status="accepted"
)}}
# Auto-updates customer stage to "customer"

# === STEP 7: Create Project ===
{{portfolio_manager(
  action="create_project",
  project_name="RetailCo Inventory Platform",
  client="RetailCo"
)}}
# project_id = 8

# === STEP 8: Assign Virtual Team ===
{{virtual_team(
  action="start_workflow",
  workflow_name="Inventory Platform Development",
  template="full_stack_development",
  customer_id=2,
  project_id=8
)}}
# workflow_id = 2
# Creates tasks: architect → design (1), dba → schema (1),
# developer → backend/frontend (2), qa → testing (1),
# security → review (1), devops → deployment (1)

# === STEP 9: Monitor Progress ===
{{virtual_team(
  action="get_workflow_progress",
  workflow_id=2
)}}

# === STEP 10: Check Customer Health (Ongoing) ===
{{customer_lifecycle(
  action="check_customer_health",
  customer_id=2
)}}
```

## Database Schemas

### Customer Lifecycle Tables

- **customers**: Customer/lead records
- **requirements**: Requirements gathering sessions
- **solutions**: Solution designs
- **proposals**: Customer proposals
- **contracts**: Signed contracts
- **customer_projects**: Project links
- **support_tickets**: Support requests
- **interactions**: Customer touchpoints

### Virtual Team Tables

- **agents**: Agent profiles (architect, developer, DBA, QA, DevOps, security, pm)
- **tasks**: Task queue
- **task_assignments**: Agent assignments
- **task_results**: Deliverables
- **workflows**: Multi-task processes
- **workflow_tasks**: Task sequences
- **collaboration_sessions**: Team collaboration
- **agent_performance**: Performance metrics
- **team_knowledge**: Shared learnings

## Testing

### Manual Testing

#### Customer Lifecycle

```bash
# Test lead capture
1. Capture 3 leads with different industries
2. Conduct interviews for each
3. Design solutions
4. Generate proposals
5. Track proposal status changes
6. Check customer health scores
7. Get pipeline summary
```

#### Virtual Team

```bash
# Test task routing
1. Route 5 different task types
2. Verify correct agent assignments
3. Start full_stack_development workflow
4. Check workflow progress
5. Escalate a task
6. Check team dashboard
7. Coordinate parallel tasks
```

### Automated Testing Script

Create `tests/test_customer_lifecycle.py`:

```python
import sys
sys.path.append('..')

from instruments.custom.customer_lifecycle.lifecycle_manager import CustomerLifecycleManager

def test_full_lifecycle():
    manager = CustomerLifecycleManager("data/test_lifecycle.db")

    # Test 1: Capture lead
    lead = manager.capture_lead(
        name="Test Customer",
        company="Test Corp",
        email="test@example.com"
    )
    assert lead['customer_id'] > 0
    print("✓ Lead capture works")

    # Test 2: Interview
    interview = manager.conduct_requirements_interview(
        customer_id=lead['customer_id'],
        responses={"What business problem?": "Test problem"}
    )
    assert interview['requirement_id'] > 0
    print("✓ Requirements interview works")

    # Test 3: Solution design
    solution = manager.design_solution(
        customer_id=lead['customer_id'],
        requirement_id=interview['requirement_id']
    )
    assert solution['solution_id'] > 0
    print("✓ Solution design works")

    # Test 4: Proposal
    proposal = manager.generate_proposal(
        customer_id=lead['customer_id'],
        solution_id=solution['solution_id']
    )
    assert proposal['proposal_id'] > 0
    print("✓ Proposal generation works")

    # Test 5: Customer health
    health = manager.get_customer_health_score(lead['customer_id'])
    assert health['health_score'] >= 0
    print("✓ Customer health check works")

    print("\n✅ All customer lifecycle tests passed!")

if __name__ == "__main__":
    test_full_lifecycle()
```

Create `tests/test_virtual_team.py`:

```python
import sys
sys.path.append('..')

from instruments.custom.virtual_team.team_orchestrator import VirtualTeamOrchestrator

def test_team_orchestration():
    orchestrator = VirtualTeamOrchestrator("data/test_team.db")

    # Test 1: Route task
    task = orchestrator.route_task(
        task_name="Test Architecture",
        task_type="architecture_design",
        description="Test design task"
    )
    assert task['task_id'] > 0
    print("✓ Task routing works")

    # Test 2: Delegate to specialist
    delegation = orchestrator.delegate_to_specialist(
        task_name="Test Development",
        specialist_role="developer",
        description="Test dev task"
    )
    assert delegation['task_id'] > 0
    print("✓ Specialist delegation works")

    # Test 3: Start workflow
    workflow = orchestrator.start_workflow(
        workflow_name="Test Workflow",
        template="api_development"
    )
    assert workflow['workflow_id'] > 0
    assert workflow['tasks_created'] > 0
    print("✓ Workflow creation works")

    # Test 4: Get workflow progress
    progress = orchestrator.get_workflow_progress(workflow['workflow_id'])
    assert 'progress_percentage' in progress
    print("✓ Workflow progress tracking works")

    # Test 5: Team dashboard
    dashboard = orchestrator.get_team_dashboard()
    assert dashboard['active_agents'] > 0
    print("✓ Team dashboard works")

    print("\n✅ All virtual team tests passed!")

if __name__ == "__main__":
    test_team_orchestration()
```

Run tests:

```bash
cd tests
python test_customer_lifecycle.py
python test_virtual_team.py
```

## Integration Patterns

### Pattern 1: Lead to Delivery

```
Customer Lifecycle → Virtual Team → Portfolio Manager
```

1. Capture lead (Customer Lifecycle)
2. Conduct interview (Customer Lifecycle)
3. Design solution (Customer Lifecycle)
4. Generate proposal (Customer Lifecycle)
5. Accept proposal (Customer Lifecycle)
6. Create project (Portfolio Manager)
7. Start workflow (Virtual Team)
8. Monitor progress (Virtual Team + Portfolio Manager)

### Pattern 2: Parallel Development

```
Virtual Team (parallel tasks) → Customer Lifecycle (updates)
```

1. Start workflow with parallel tasks (Virtual Team)
2. Monitor multiple agent progress (Virtual Team)
3. Log customer interactions (Customer Lifecycle)
4. Track project health (Portfolio Manager)

## Troubleshooting

### Database Issues

**Problem**: Database file not found

```
Solution: Databases auto-create in instruments/custom/*/data/
Check file permissions in data/ directory
```

**Problem**: SQLite locked error

```
Solution: Close connections properly
Restart Agent Jumbo if needed
```

### Task Assignment Issues

**Problem**: No agent available for task

```
Solution: Check agent initialization in VirtualTeamOrchestrator
Verify agent role matches task requirements
Call list_agents to see registered agents
```

**Problem**: Task stuck in pending

```
Solution: Check task_queue for pending tasks
Manually assign using assign_task
Verify workflow dependencies
```

## Performance Tips

1. **Batch operations**: Use workflows for multiple related tasks
2. **Parallel execution**: Leverage parallel_group for concurrent tasks
3. **Index queries**: Database indexes on customer_id, task_id, workflow_id
4. **Cache results**: Reuse customer_360 views, team dashboards
5. **Clean old data**: Archive completed workflows/closed proposals

## Next Steps

### Phase 3 Enhancements (Planned)

- Multi-tenant SaaS Manager (blueprint solutions)
- AI-powered requirement analysis
- Automated proposal customization
- Agent performance learning
- Cross-project resource optimization

## Support

For issues or questions:

1. Check tool documentation: `prompts/agent.system.tool.*.md`
2. Review database schemas: `instruments/custom/*/db.py`
3. Run test scripts to verify functionality
4. Check Agent Jumbo logs for errors

## License

Inherits Agent Jumbo license (see LICENSE in project root)
