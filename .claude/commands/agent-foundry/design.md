---
description: Design a new AI agent with role, expertise, mission, and capabilities
allowed-tools: [Bash, Read, Write, Grep, AskUserQuestion, Task]
argument-hint: "<agent-name> [--domain <domain>] [--complexity <simple|moderate|complex|expert>]"
---

# /agent-foundry/design - Design New AI Agent

Design a new specialized AI agent for the Prompt Blueprint system.

## Overview

Creates a comprehensive agent specification including:

- Role & expertise definition
- Mission statement
- Reasoning methodology
- Input/output protocols
- Quality standards
- Success metrics

## Process

### Step 1: Gather Requirements

**Ask user:**

1. **Agent Name** (Required)
   - "What should this agent be called?"
   - Example: "database-architect", "security-auditor", "cost-optimizer"

2. **Primary Domain** (Required)
   - "What domain does this agent specialize in?"
   - Options: development, operations, security, compliance, performance, cost-optimization, customer-success, integration, data-analysis, documentation

3. **Core Expertise** (Required - 3-5 items)
   - "What are the agent's core skills/expertise areas?"
   - Example: "Schema design, query optimization, migration strategies, performance tuning"

4. **Mission Statement** (Required)
   - "What is the agent's primary objective?"
   - Example: "Design scalable, performant database schemas that support multi-tenant architecture while maintaining data integrity and compliance"

5. **Complexity Level** (Optional)
   - "What complexity level should this agent handle?"
   - Options: simple, moderate, complex, expert
   - Default: moderate

### Step 2: Define Capabilities

Based on domain and expertise, define:

**Capabilities** (5-10 specific abilities):

- Input analysis and validation
- Problem decomposition
- Solution generation
- Quality assurance
- Documentation creation
- Implementation guidance

**Example for database-architect**:

```yaml
capabilities:
  - Analyze data requirements and design optimal schemas
  - Design multi-tenant database architectures
  - Create migration strategies with zero downtime
  - Optimize query performance and indexing
  - Ensure ACID compliance and data integrity
  - Design backup and disaster recovery plans
  - Validate schema against best practices
  - Generate comprehensive database documentation
```

### Step 3: Reasoning Methodology

Define how the agent approaches problems:

**Framework Options**:

- Chain-of-Thought (CoT) - Sequential reasoning
- Tree-of-Thought (ToT) - Multiple solution paths
- Constitutional - Value-aligned decisions
- DEVB - Design → Emulate → Validate → Build
- Test-Driven - Test-first approach

**Example**:

```markdown
## Reasoning Methodology

**Primary Framework**: Chain-of-Thought with Validation Gates

### Decision Process

1. **Analyze Requirements**
   - Extract entities and relationships
   - Identify constraints and NFRs
   - Determine scale and growth projections

2. **Design Schema**
   - Choose appropriate data types
   - Design indexes for query patterns
   - Plan partitioning strategy
   - Define constraints and triggers

3. **Validate Design**
   - Check normalization (3NF minimum)
   - Verify multi-tenant isolation
   - Assess query performance
   - Validate against compliance requirements

4. **Generate Implementation**
   - Create migration scripts
   - Write seed data
   - Document schema decisions
```

### Step 4: Input/Output Protocols

Define interface specifications:

**Input Processing**:

```yaml
input_protocol:
  required_fields:
    - problem_statement
    - business_requirements
    - technical_constraints
  optional_fields:
    - existing_schema
    - performance_requirements
    - compliance_requirements
  validation:
    - Check completeness
    - Validate formats
    - Flag ambiguities
```

**Output Format**:

```yaml
output_protocol:
  format: structured
  sections:
    - executive_summary
    - schema_design
    - migration_plan
    - performance_analysis
    - compliance_validation
    - implementation_guide
  deliverables:
    - SQL migration scripts
    - Entity-relationship diagrams
    - Index optimization plan
    - Documentation
```

### Step 5: Quality Standards

Define acceptance criteria:

**Quality Checklist**:

- [ ] Schema follows naming conventions
- [ ] All tables have primary keys (UUIDs)
- [ ] Timestamps (created_at, updated_at) on all tables
- [ ] Multi-tenant isolation via organization_id
- [ ] Indexes on all foreign keys and query columns
- [ ] Soft delete columns where appropriate
- [ ] Migration scripts are idempotent
- [ ] Documentation is comprehensive

**Success Metrics**:

- Schema normalization score: ≥ 3NF
- Query performance: p95 < 50ms
- Multi-tenant isolation: 100%
- Documentation coverage: 100%
- Migration safety: Zero data loss

### Step 6: Generate Agent File

Create agent definition at `.claude/agents/<category>/<agent-name>.md`:

```markdown
# {Agent Name} - Professional AI Assistant

## ROLE & EXPERTISE

You are a **{Role Title}** with deep expertise in:
- {Expertise 1}
- {Expertise 2}
- {Expertise 3}
- {Expertise 4}
- {Expertise 5}

## MISSION CRITICAL OBJECTIVE

**{Mission statement with measurable outcomes}**

## OPERATIONAL CONTEXT

- **Domain**: {domain}
- **Audience**: {target users}
- **Quality Tier**: {quality level}
- **Compliance Requirements**: {regulations if any}

## INPUT PROCESSING PROTOCOL

{Input handling steps}

## REASONING METHODOLOGY

**Primary Framework**: {chosen framework}

{Detailed reasoning process}

## OUTPUT PROTOCOL

{Output format specification}

## QUALITY STANDARDS

{Quality checklist and success metrics}

## EXAMPLE INTERACTIONS

{3-5 example conversations showing capability}
```

### Step 7: Validation

Validate the agent design:

1. **Completeness Check**
   - All required sections present
   - Examples demonstrate all capabilities
   - Quality metrics are measurable

2. **Consistency Check**
   - Mission aligns with capabilities
   - Input/output protocols match use cases
   - Reasoning methodology fits complexity

3. **Integration Check**
   - Compatible with existing agents
   - No capability overlap/conflicts
   - Clear routing criteria

### Step 8: Output Summary

```
✓ Agent Design Complete: {agent-name}

📁 File Created:
   .claude/agents/{category}/{agent-name}.md

📊 Specifications:
   Domain: {domain}
   Complexity: {complexity}
   Capabilities: {count}
   Examples: {count}

🎯 Next Steps:
   1. Review agent definition
   2. Run: /agent-foundry/build {agent-name}
   3. Run: /agent-foundry/test {agent-name}
   4. Run: /agent-foundry/train {agent-name}

📚 Related Commands:
   /agent-foundry/list       - View all agents
   /agent-foundry/build      - Implement agent
   /agent-foundry/test       - Test agent
```

## Usage Examples

### Example 1: Database Architect

```bash
/agent-foundry/design database-architect --domain development --complexity expert
```

Agent will ask:

- Core expertise areas
- Mission statement
- Specific capabilities needed

Result: `.claude/agents/development/database-architect.md`

### Example 2: Cost Optimizer

```bash
/agent-foundry/design cost-optimizer --domain operations --complexity moderate
```

Generates agent specialized in:

- Cloud billing analysis
- Resource optimization
- Cost forecasting

### Example 3: Security Auditor

```bash
/agent-foundry/design security-auditor --domain security --complexity expert
```

Creates comprehensive security agent with:

- OWASP compliance checking
- Vulnerability scanning
- Security best practices validation

## Design Templates

### Template 1: Analysis Agent

For agents that analyze and report (auditors, analyzers, reviewers)

### Template 2: Creation Agent

For agents that generate artifacts (designers, architects, writers)

### Template 3: Optimization Agent

For agents that improve existing systems (optimizers, refactors, enhancers)

### Template 4: Integration Agent

For agents that connect systems (integrators, orchestrators, coordinators)

## Quality Gates

Before proceeding to build:

✅ Clear, specific mission statement
✅ 5-10 well-defined capabilities
✅ Reasoning methodology documented
✅ Input/output protocols specified
✅ Quality metrics are measurable
✅ 3+ example interactions provided
✅ No conflicts with existing agents
✅ Routing criteria defined

## Best Practices

1. **Start with Mission** - Clear objective drives everything else
2. **Be Specific** - "Optimize database queries" > "Help with databases"
3. **Define Success** - Measurable metrics, not vague goals
4. **Show Examples** - Demonstrate capabilities with real scenarios
5. **Consider Integration** - How does this agent work with others?
6. **Plan for Evolution** - Agents should be updatable as needs change
