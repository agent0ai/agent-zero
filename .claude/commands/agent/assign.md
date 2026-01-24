---
description: Manually assign a specific task to a designated AI agent
argument-hint: "<task-description> <agent-type> [--priority high|normal|low]"
allowed-tools: ["Task"]
---

# Manual Agent Task Assignment

Manually route a specific task to a designated AI agent, bypassing automatic routing for precise control.

## What This Command Does

Override automatic agent routing to assign tasks directly to specific agents when you need:

- **Specific Expertise**: Route complex tasks to specialized agents
- **Priority Override**: Ensure critical tasks get immediate attention
- **Agent Testing**: Test new agents or validate agent capabilities
- **Workload Management**: Balance load across agents manually

## Usage

```bash
# Assign GCP infrastructure task to specific agent
/agent:assign "Set up Cloud SQL with read replicas" gcp-infrastructure-architect

# High priority security audit
/agent:assign "Audit authentication system" code-reviewer --priority high

# Test new agent with sample task
/agent:assign "Generate test data" new-data-agent --priority low
```

## Supported Agent Types

### Infrastructure & Cloud

- `gcp-infrastructure-architect` - GCP infrastructure and IaC
- `gcp-database-architect` - Database design and optimization
- `gcp-monitoring-sre` - Monitoring and observability
- `serverless-architect` - Cloud Functions and Cloud Run

### Development & Testing

- `code-reviewer` - Code quality and security audits
- `frontend-architect` - Frontend architecture and design
- `playwright-test-architect` - Test automation
- `qa-testing-engineer` - Testing strategies

### DevOps & Operations

- `devops-github-docker-agent` - CI/CD and containerization
- `cicd-pipeline-architect` - Pipeline design
- `gcp-troubleshooting-specialist` - Issue diagnosis

### Specialized Domains

- `healthcare-api-integration-expert` - Healthcare integrations
- `accessibility-auditor` - WCAG compliance
- `web-performance-optimizer` - Performance optimization

## Priority Levels

- **high**: Execute immediately, preempting normal tasks
- **normal** (default): Queue in standard priority order
- **low**: Execute when no higher priority tasks pending

## Business Value

**Use Cases**:

- Critical production incidents requiring immediate expert attention
- Specialized tasks needing specific domain expertise
- Load balancing during high-volume periods
- Agent capability validation and testing

---

*Manual assignment provides precise control over task routing when automatic routing isn't optimal.*
