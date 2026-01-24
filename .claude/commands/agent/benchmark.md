---
description: Benchmark AI agent performance on standardized tasks
argument-hint: [--agents all|dev|content|<name>] [--tasks <file>] [--compare <date>]
model: claude-sonnet-4-5-20250929
allowed-tools: [Task, Bash, Read, Write]
---

# /agent:benchmark

Benchmark agents: **${ARGUMENTS:-all agents}**

## Step 1: Define Benchmark Tasks

Create standardized task suite:

```javascript
const benchmarkTasks = {
  simple: [
    { name: "format-code", description: "Format JavaScript code", expectedModel: "haiku" },
    { name: "extract-data", description: "Extract data from JSON", expectedModel: "haiku" }
  ],
  medium: [
    { name: "api-endpoint", description: "Create REST API endpoint", expectedModel: "sonnet" },
    { name: "component-refactor", description: "Refactor React component", expectedModel: "sonnet" }
  ],
  complex: [
    { name: "feature-implementation", description: "Implement feature end-to-end", expectedModel: "opus" },
    { name: "architecture-design", description: "Design system architecture", expectedModel: "opus" }
  ]
};
```

## Step 2: Run Benchmarks

For each agent and task:

```javascript
const result = await runBenchmark({
  agent: agentName,
  task: taskSpec,
  metrics: ['time', 'tokens', 'cost', 'quality']
});
```

## Step 3: Measure Performance

Track:

- Time to completion (seconds)
- Token usage (input + output)
- Cost (tokens × model price)
- Success rate (% of successful completions)
- Output quality (0-10 score)

## Step 4: Generate Report

```markdown
# 📊 Agent Benchmark Report

## Summary
- Agents tested: ${agentCount}
- Tasks completed: ${taskCount}
- Total time: ${totalTime}s
- Total cost: $${totalCost}

## Performance Matrix

| Agent | Simple | Medium | Complex | Avg Score | Cost |
|-------|--------|--------|---------|-----------|------|
${agents.map(a => `| ${a.name} | ${a.simple} | ${a.medium} | ${a.complex} | ${a.avg} | $${a.cost} |`).join('\n')}

## Best Agent per Task Type
- Simple: ${best.simple} (${best.simpleScore}/10, $${best.simpleCost})
- Medium: ${best.medium} (${best.mediumScore}/10, $${best.mediumCost})
- Complex: ${best.complex} (${best.complexScore}/10, $${best.complexCost})

## Recommendations
${recommendations.map(r => `- ${r}`).join('\n')}
```

**Command Complete** 📊
