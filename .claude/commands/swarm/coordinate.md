---
description: Coordinate multiple agents on complex multi-phase tasks
argument-hint: <task-description> [--agents <list>] [--max-parallel 3] [--strategy speed|cost|quality]
model: claude-opus-4-5-20251101
allowed-tools: [Task, Read, Write, AskUserQuestion, TodoWrite]
---

# /swarm:coordinate

Coordinate agents for: **$ARGUMENTS**

## Step 1: Analyze Task Complexity

Break down task into phases:

- Identify subtasks
- Determine dependencies
- Find parallelizable work
- Estimate complexity per subtask

## Step 2: Create Task Graph

```javascript
const taskGraph = {
  nodes: [
    { id: 'A', name: 'Design API', agent: 'architect', duration: 30 },
    { id: 'B', name: 'Design DB', agent: 'database-architect', duration: 25 },
    { id: 'C', name: 'Frontend UI', agent: 'frontend-dev', duration: 40 },
    { id: 'D', name: 'Backend API', agent: 'backend-dev', duration: 45, deps: ['A', 'B'] },
    { id: 'E', name: 'Integration', agent: 'full-stack-verifier', duration: 20, deps: ['C', 'D'] }
  ]
};
```

## Step 3: Assign Agents

Match agents to subtasks based on:

- Required expertise
- Agent availability
- Current workload
- Historical performance

## Step 4: Create Execution Plan

```markdown
# 🐝 Swarm Coordination Plan

## Task: ${taskName}

### Phase 1 (Parallel)
- Agent A: Design API (30min)
- Agent B: Design DB (25min)
- Agent C: Frontend UI (40min)

### Phase 2 (After A, B complete)
- Agent D: Backend API (45min)

### Phase 3 (After C, D complete)
- Agent E: Integration (20min)

**Total Time**: ~95 minutes (with parallelization)
**Sequential Time**: ~160 minutes
**Time Saved**: 65 minutes (41%)

Approve plan? (y/n)
```

## Step 5: Execute Coordination

Launch agents in parallel when possible:

```javascript
// Phase 1
await Promise.all([
  Task({ subagent_type: 'architect', prompt: designAPI }),
  Task({ subagent_type: 'database-architect', prompt: designDB }),
  Task({ subagent_type: 'frontend-dev', prompt: buildUI })
]);

// Phase 2 (waits for Phase 1)
await Task({ subagent_type: 'backend-dev', prompt: buildAPI });

// Phase 3 (waits for all)
await Task({ subagent_type: 'full-stack-verifier', prompt: integrate });
```

## Step 6: Monitor Progress

Track:

- Current phase
- Agent statuses
- Completion percentage
- Estimated time remaining
- Encountered issues

## Step 7: Handle Failures

If agent fails:

1. Analyze error
2. Retry with different agent
3. Escalate if retry fails
4. Adjust downstream tasks

## Step 8: Aggregate Results

Combine agent outputs:

- Merge code changes
- Resolve conflicts
- Validate integration
- Run tests

## Step 9: Generate Report

```markdown
# ✅ Swarm Coordination Complete

## Results
- **Task**: ${taskName}
- **Agents Used**: ${agentCount}
- **Total Time**: ${actualTime} (est: ${estimatedTime})
- **Total Cost**: $${totalCost}

### Phase Breakdown
${phases.map(p => `
#### Phase ${p.number}: ${p.name}
- Agents: ${p.agents.join(', ')}
- Time: ${p.actualTime} (est: ${p.estimatedTime})
- Status: ${p.status}
`).join('\n')}

### Issues Encountered
${issues.map(i => `- ${i.description} (resolved by: ${i.resolution})`).join('\n')}

### Deliverables
${deliverables.map(d => `- ${d}`).join('\n')}
```

**Command Complete** 🐝
