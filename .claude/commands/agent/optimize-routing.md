---
description: Optimize agent task routing based on historical performance
argument-hint: [--period 30d|90d|all] [--optimize-for speed|cost|quality] [--dry-run]
model: claude-sonnet-4-5-20250929
allowed-tools: [Task, Read, Write, Bash, Grep]
---

# /agent:optimize-routing

Optimize routing: **${ARGUMENTS:-last 30 days}**

## Step 1: Analyze Historical Performance

Read agent logs and extract:

- Task descriptions
- Agent assignments
- Success rates
- Completion times
- Costs
- Quality scores

## Step 2: Identify Patterns

Use pattern matching to find:

- Keywords → Best agent mappings
- Task complexity → Model selection
- Success predictors
- Failure indicators

## Step 3: Generate Routing Rules

```yaml
routing_rules:
  - pattern: ".*API endpoint.*"
    agent: gcp-api-architect
    model: sonnet
    confidence: 0.95

  - pattern: ".*database.*migration.*"
    agent: gcp-database-architect
    model: sonnet
    confidence: 0.92

  - pattern: ".*simple.*format.*"
    agent: general-purpose
    model: haiku
    confidence: 0.88
```

## Step 4: Simulate New Routing

Test new rules on historical tasks:

```javascript
const simulation = historicalTasks.map(task => {
  const oldAgent = task.assignedAgent;
  const newAgent = routingEngine.selectAgent(task.description, newRules);

  return {
    task: task.id,
    old: { agent: oldAgent, cost: task.cost, quality: task.quality },
    new: { agent: newAgent, projectedCost, projectedQuality }
  };
});
```

## Step 5: Calculate Impact

```markdown
# 🎯 Routing Optimization Report

## Projected Impact

### Cost Reduction
- Current: $${currentCost}/month
- Projected: $${projectedCost}/month
- Savings: $${savings}/month (${savingsPercent}%)

### Quality Improvement
- Current avg: ${currentQuality}/10
- Projected avg: ${projectedQuality}/10
- Improvement: +${qualityDelta}

### Success Rate
- Current: ${currentSuccess}%
- Projected: ${projectedSuccess}%
- Improvement: +${successDelta}%

## New Routing Rules (${rulesCount})
${rules.map(r => `- ${r.pattern} → ${r.agent} (${r.confidence * 100}% confidence)`).join('\n')}
```

Apply with: `/agent:optimize-routing --apply`

**Command Complete** 🎯
