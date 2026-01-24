# Agent Registry Guide

**Version**: 1.0.0
**Last Updated**: 2026-01-20

## Overview

The Agent Registry is a centralized catalog of all available agents in the Mahoosuc Operating System, providing discovery, routing, performance tracking, and capability mapping.

## Quick Start

### Finding the Right Agent

```yaml
# View all agent-os agents
agent_os:
  - product-planner # Product planning and roadmap
  - spec-initializer # Initialize spec folder
  - spec-shaper # Gather requirements
  - spec-writer # Write specifications
  - spec-verifier # Validate specs
  - contract-designer # Design API contracts
  - integration-architect # Design integrations
  - tasks-list-creator # Create task lists
  - implementer # Full-stack implementation
  - implementation-verifier # Verify implementation
  - full-stack-verifier # Verify full-stack integration

# View all product-management agents
product_management:
  - master-orchestrator # Workflow coordination
  - rollout-coordinator # Feature rollouts
  - adoption-tracker # Adoption metrics
  - deprecation-manager # Feature deprecation
  - playbook-engine # Customer success playbooks
  - health-monitor # Customer health monitoring
  - trend-analyzer # Market trend analysis
  - competitor-watcher # Competitor monitoring
  - deployment-guard # Deployment validation
  - rollback-sentinel # Rollback coordination
```

### Agent Selection by Task

| Task Type | Recommended Agent | Cost | Time |
|-----------|------------------|------|------|
| **Plan product** | product-planner | $0.12 | 3 min |
| **Create spec** | spec-initializer → spec-shaper → spec-writer | $0.42 | 10 min |
| **Design API** | contract-designer | $0.20 | 4 min |
| **Implement feature** | implementer | $0.45 | 15 min |
| **Verify implementation** | implementation-verifier | $0.28 | 6 min |
| **Verify full-stack** | full-stack-verifier | $0.32 | 7 min |
| **Plan rollout** | rollout-coordinator | $0.24 | 5 min |
| **Track adoption** | adoption-tracker | $0.18 | 4 min |
| **Analyze market** | trend-analyzer | $0.31 | 7 min |
| **Monitor competitors** | competitor-watcher | $0.26 | 5 min |
| **Validate deployment** | deployment-guard | $0.22 | 5 min |
| **Coordinate rollback** | rollback-sentinel | $0.29 | 6 min |

---

## Agent Registry Structure

### Registry File Location

```
.claude/agents/registry.yaml
```

### Registry Schema

```yaml
metadata:
  version: 1.0.0
  total_agents: 21
  last_updated: 2026-01-20

agent_os:
  agents:
    - name: agent-name
      version: 2.0.0
      path: .claude/agents/agent-os/agent-name.md
      description: What the agent does
      tools: [Tool1, Tool2, Tool3]
      model: inherit
      color: blue

      capabilities:
        - capability_1
        - capability_2

      metrics:
        avg_cost_per_invocation: 0.15
        avg_execution_time: 180
        success_rate: 0.95
        total_invocations: 50

      performance:
        quality_score: 0.93
        user_satisfaction: 0.91
        time_to_value: 200

      routing:
        best_for: ["use case 1", "use case 2"]
        not_suitable_for: ["anti-pattern 1"]
        prerequisites: ["other-agent"]
```

---

## Using the Registry

### 1. Agent Discovery

**Find agents by capability:**

```bash
# Search registry for specific capabilities
grep -A 5 "api_contract_design" .claude/agents/registry.yaml
# Returns: contract-designer

grep -A 5 "full_stack_development" .claude/agents/registry.yaml
# Returns: implementer
```

**Find agents by task category:**

```yaml
# Planning agents
planning:
  agents: [product-planner, spec-initializer, spec-shaper, tasks-list-creator]

# Implementation agents
implementation:
  agents: [implementer]

# Verification agents
verification:
  agents: [implementation-verifier, full-stack-verifier, spec-verifier]
```

### 2. Agent Selection

**Use routing intelligence to select the best agent:**

```javascript
// Automatic agent routing based on task description
const agent = await routeTask({
  description: "Create API contracts for user authentication",
  category: "specification"
})
// Returns: contract-designer

const agent = await routeTask({
  description: "Implement user login feature",
  category: "implementation"
})
// Returns: implementer
```

**Manual agent selection with validation:**

```javascript
// Select agent with prerequisite validation
const agent = await selectAgent({
  name: "implementer",
  validate_prerequisites: true
})
// Checks: tasks-list-creator was run first
```

### 3. Agent Invocation

**Modern pattern (named agent):**

```javascript
// NEW: Named agent with validation
await Task({
  subagent: 'spec-shaper',  // Agent name from registry
  context: {
    spec_name: 'user-authentication',
    standards_dir: '.claude/standards/'
  },
  validation: {
    required_outputs: ['requirements.md'],
    quality_threshold: 0.9
  },
  retry: {
    max_attempts: 3,
    on_failure: 'notify-user'
  },
  cost_limit: 0.25
})
```

**Old pattern (generic):**

```javascript
// OLD: Generic subagent type
await Task({
  subagent_type: 'general-purpose',
  prompt: `...`
})
// ⚠️ Deprecated - migrate to named agents
```

---

## Agent Capabilities

### Agent OS - Spec-Driven Development

#### Product Planner

**Capabilities**: product_vision_definition, roadmap_creation, tech_stack_selection, milestone_planning

**Best For**:

- Creating product vision and mission
- Building product roadmap (3-5 sections)
- Selecting technology stack
- Defining success metrics

**Not Suitable For**:

- Code implementation
- Testing
- Deployment

**Workflow Position**: Start of Agent OS workflow

---

#### Spec Initializer

**Capabilities**: spec_folder_creation, idea_preservation, initial_structure_setup

**Best For**:

- Starting new feature specs
- Creating spec directory structure
- Preserving initial ideas

**Not Suitable For**:

- Existing specs (use spec-shaper or spec-writer)
- Implementation

**Workflow Position**: Phase 2, Step 1 of Agent OS workflow

---

#### Spec Shaper

**Capabilities**: requirements_gathering, visual_analysis, targeted_questioning, constraint_identification

**Best For**:

- Gathering detailed requirements
- Analyzing mockups and screenshots
- Asking targeted questions
- Identifying constraints and scope

**Not Suitable For**:

- Writing final spec (use spec-writer)
- Implementation
- Testing

**Workflow Position**: Phase 2, Step 2 of Agent OS workflow

---

#### Spec Writer

**Capabilities**: specification_writing, technical_design, api_documentation, acceptance_criteria

**Best For**:

- Creating detailed specification documents
- Technical design documentation
- API documentation
- Acceptance criteria definition

**Not Suitable For**:

- Requirements gathering (use spec-shaper)
- Implementation (use implementer)
- Validation (use spec-verifier)

**Workflow Position**: Phase 2, Step 3 of Agent OS workflow

---

#### Spec Verifier

**Capabilities**: spec_validation, completeness_checking, standards_alignment, quality_assurance

**Best For**:

- Validating spec completeness
- Checking standards alignment
- Quality assurance before implementation
- Gap identification

**Not Suitable For**:

- Writing specs (use spec-writer)
- Implementation (use implementer)

**Workflow Position**: Phase 2, Step 4 of Agent OS workflow

---

#### Contract Designer

**Capabilities**: api_contract_design, type_definition, error_schema_creation, frontend_backend_alignment

**Best For**:

- Designing API contracts
- Defining shared TypeScript types
- Creating error schemas
- Aligning frontend and backend expectations

**Not Suitable For**:

- Implementation
- UI design (use Design OS skills)

**Workflow Position**: Phase 3, Step 1 of Agent OS workflow (NEW)

---

#### Integration Architect

**Capabilities**: integration_design, state_management_patterns, data_fetching_strategies, error_handling_patterns

**Best For**:

- Designing data fetching patterns
- State management architecture
- Error handling strategies
- Caching and optimistic updates

**Not Suitable For**:

- Backend-only features
- Pure UI components

**Workflow Position**: Phase 3, Step 2 of Agent OS workflow (NEW)

---

#### Tasks List Creator

**Capabilities**: task_breakdown, dependency_management, test_planning, implementation_sequencing

**Best For**:

- Breaking down spec into tasks
- Identifying dependencies
- Planning test strategy
- Sequencing implementation

**Not Suitable For**:

- Actual implementation (use implementer)
- Design decisions (use spec-writer)

**Workflow Position**: Phase 4, Step 1 of Agent OS workflow

---

#### Implementer

**Capabilities**: full_stack_development, test_driven_development, ui_implementation, api_implementation, database_operations

**Best For**:

- Full-stack feature implementation
- Test-driven development
- UI/UX implementation
- API development
- Database design

**Not Suitable For**:

- Planning (use product-planner or spec-shaper)
- Design (use Design OS skills)
- Architecture (use contract-designer or integration-architect)

**Workflow Position**: Phase 4, Step 2 of Agent OS workflow

**Metrics**:

- Highest cost per invocation ($0.45)
- Longest execution time (15 min avg)
- Good success rate (89%)

---

#### Implementation Verifier

**Capabilities**: end_to_end_testing, implementation_verification, acceptance_testing, documentation_validation

**Best For**:

- Verifying implementation completeness
- Acceptance testing
- Documentation validation
- Quality assurance

**Not Suitable For**:

- Implementation (use implementer)
- Design (use spec-writer)

**Workflow Position**: Phase 4, Step 3 of Agent OS workflow

---

#### Full-Stack Verifier

**Capabilities**: contract_compliance_testing, integration_verification, data_flow_validation, end_to_end_testing

**Best For**:

- Verifying frontend-backend integration
- Testing API contract compliance
- Validating data flow
- End-to-end testing

**Not Suitable For**:

- Unit testing (use implementation-verifier)
- Implementation (use implementer)

**Workflow Position**: Phase 5 of Agent OS workflow (NEW)

---

### Product Management Agents

*(See registry.yaml for full product management agent capabilities)*

---

## Performance Metrics

### Tracked Metrics

All agents track the following performance metrics:

1. **Cost Metrics**
   - `avg_cost_per_invocation`: Average cost per agent run
   - `total_cost`: Cumulative cost across all invocations

2. **Time Metrics**
   - `avg_execution_time`: Average time to complete (seconds)
   - `time_to_value`: Average time until first useful output

3. **Quality Metrics**
   - `success_rate`: Percentage of successful completions
   - `quality_score`: Overall output quality (0-1 scale)
   - `user_satisfaction`: User satisfaction score (0-1 scale)

4. **Volume Metrics**
   - `total_invocations`: Number of times agent was called

### Performance Baselines

Agents are expected to meet these performance baselines:

```yaml
quality_score_threshold: 0.85
success_rate_threshold: 0.90
user_satisfaction_threshold: 0.85
cost_per_invocation_threshold: 0.50
execution_time_threshold: 600  # 10 minutes
```

### Alert Conditions

Automatic alerts are triggered when:

- **Quality Score < 0.85** → High severity, notify team
- **Success Rate < 0.85** → Critical severity, escalate
- **Avg Cost > $0.75** → Medium severity, optimize prompt

---

## Routing Intelligence

### Automatic Task Routing

The registry includes routing intelligence to automatically select the best agent for a task:

```yaml
routing_intelligence:
  categories:
    planning:
      agents: [product-planner, spec-initializer, spec-shaper, tasks-list-creator]
      confidence_threshold: 0.8

    implementation:
      agents: [implementer]
      confidence_threshold: 0.9

    verification:
      agents: [implementation-verifier, full-stack-verifier, spec-verifier]
      confidence_threshold: 0.85
```

### Confidence Thresholds

- **0.9+**: High confidence, direct routing
- **0.8-0.89**: Medium confidence, suggest alternatives
- **< 0.8**: Low confidence, request clarification

### Fallback Strategy

If routing confidence is below threshold:

1. Use `master-orchestrator` as fallback
2. Allow maximum 3 routing attempts
3. Timeout after 30 seconds
4. Request manual agent selection

---

## Agent Versioning

### Version Format

All agents use semantic versioning: `MAJOR.MINOR.PATCH`

**Example**: `2.0.0`

- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Version History

Each agent maintains a changelog:

```yaml
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Added validation schemas"
      - "Implemented retry logic"
      - "Added cost controls"

  - version: 1.5.0
    date: 2025-12-15
    changes:
      - "Improved prompt clarity"
      - "Added examples"
```

### Version Compatibility

The registry tracks version compatibility to ensure smooth upgrades:

- All agents are currently version 2.0.0 (modernized)
- Version 1.x agents are deprecated
- Migration path documented in each agent

---

## Best Practices

### Agent Selection

1. **Use the Registry**: Always check registry before creating custom agents
2. **Follow Prerequisites**: Respect agent dependency chains
3. **Check Metrics**: Review success rate and cost before using expensive agents
4. **Validate Context**: Ensure agent has necessary context to succeed

### Agent Invocation

1. **Named Agents**: Always use named agents (not `general-purpose`)
2. **Add Validation**: Include validation schemas for outputs
3. **Set Cost Limits**: Prevent runaway costs with budget limits
4. **Enable Retry**: Add retry logic for flaky operations
5. **Pass Context**: Provide structured context, not raw prompts

### Performance Optimization

1. **Monitor Metrics**: Track agent performance over time
2. **Optimize Prompts**: If cost > threshold, optimize agent prompt
3. **Cache Results**: Cache expensive agent outputs when possible
4. **Batch Operations**: Group similar tasks for efficiency
5. **Parallel Execution**: Run independent agents in parallel

---

## Troubleshooting

### Agent Not Found

**Problem**: Agent name not recognized

**Solutions**:

1. Check spelling in registry
2. Verify agent file exists at path
3. Check agent is enabled
4. Review prerequisites are met

### Agent Failing

**Problem**: Agent returns errors or times out

**Solutions**:

1. Review agent metrics (success rate)
2. Check agent has required tools
3. Verify context is complete
4. Increase timeout if needed
5. Review agent logs

### Unexpected Results

**Problem**: Agent produces incorrect or low-quality output

**Solutions**:

1. Check quality_score in registry
2. Review agent description (is it the right agent?)
3. Validate input context
4. Check prerequisites were met
5. Review agent prompt for clarity

### High Costs

**Problem**: Agent exceeds cost budget

**Solutions**:

1. Check avg_cost_per_invocation in registry
2. Set cost_limit on Task invocation
3. Optimize agent prompt
4. Use cheaper alternative agent
5. Cache results to reduce invocations

---

## Future Enhancements

### Planned Features

- [ ] **Agent Marketplace**: Share and discover community agents
- [ ] **Visual Agent Builder**: GUI for creating agents
- [ ] **Agent Analytics Dashboard**: Real-time performance tracking
- [ ] **Agent A/B Testing**: Test agent variants
- [ ] **Agent Composition**: Chain agents automatically
- [ ] **Smart Routing**: ML-powered agent selection
- [ ] **Cost Optimization**: Automatic prompt optimization
- [ ] **Agent Templates**: Pre-built agent patterns

---

## Reference

### Registry Fields Reference

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique agent identifier |
| `version` | string | Semantic version |
| `path` | string | File path to agent definition |
| `description` | string | What the agent does |
| `tools` | array | Available tools |
| `model` | string | Model override or inherit |
| `color` | string | Visual identifier |
| `capabilities` | array | Agent capabilities |
| `metrics.avg_cost_per_invocation` | number | Average cost ($) |
| `metrics.avg_execution_time` | number | Average time (seconds) |
| `metrics.success_rate` | number | Success rate (0-1) |
| `metrics.total_invocations` | number | Total calls |
| `performance.quality_score` | number | Quality (0-1) |
| `performance.user_satisfaction` | number | Satisfaction (0-1) |
| `performance.time_to_value` | number | Time to output (seconds) |
| `routing.best_for` | array | Ideal use cases |
| `routing.not_suitable_for` | array | Anti-patterns |
| `routing.prerequisites` | array | Required agents |

---

**Last Updated**: 2026-01-20
**Version**: 1.0.0
**Maintained By**: Mahoosuc Operating System Team
