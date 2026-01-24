---
description: Train agent with example scenarios, feedback loops, and continuous improvement
allowed-tools: [Bash, Read, Write, Task, AskUserQuestion]
argument-hint: "<agent-name> [--mode <supervised|reinforcement|hybrid>] [--examples <path>]"
---

# /agent-foundry/train - Train AI Agent

Improve agent performance through training scenarios, feedback loops, and knowledge enhancement.

## Overview

Training methods:

1. **Supervised Training** - Learn from labeled examples
2. **Reinforcement Learning** - Learn from success/failure feedback
3. **Hybrid Training** - Combined approach with human feedback
4. **Few-Shot Learning** - Learn from minimal examples
5. **Knowledge Distillation** - Learn from expert agent outputs

## Training Process

### Step 1: Prepare Training Data

Collect training scenarios from multiple sources:

```typescript
interface TrainingScenario {
  id: string
  capability: string
  input: any
  expectedOutput: any
  explanation: string
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  tags: string[]
  successCriteria: Array<{
    metric: string
    threshold: number
  }>
}
```

**Data Sources**:

1. **Agent examples** - From design specification
2. **Historical usage** - Real user interactions (anonymized)
3. **Synthetic data** - Generated test scenarios
4. **Expert demonstrations** - Curated by domain experts
5. **Failed cases** - Previous errors for improvement

### Step 2: Supervised Training

Train with labeled example pairs:

```yaml
training_examples:
  - scenario: "Design multi-tenant schema"
    input:
      requirements: "SaaS app with users, orgs, billing"
      constraints: ["PostgreSQL", "UUID PKs"]
    expert_output: |
      CREATE TABLE organizations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
      );

      CREATE TABLE users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id),
        email TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ DEFAULT NOW()
      );

      CREATE INDEX idx_users_org_id ON users(organization_id);
      CREATE INDEX idx_users_email ON users(email);
    feedback: "Perfect multi-tenant isolation with proper indexing"
    rating: 10/10
```

**Training Loop**:

```typescript
for (const example of trainingExamples) {
  // 1. Agent generates output
  const agentOutput = await agent.execute(example.input)

  // 2. Compare with expert output
  const similarity = compareOutputs(agentOutput, example.expert_output)

  // 3. Calculate loss/error
  const error = calculateError(similarity, example.successCriteria)

  // 4. Update agent knowledge (conceptual - actual implementation varies)
  if (error > threshold) {
    agent.learn({
      scenario: example,
      mistake: agentOutput,
      correction: example.expert_output,
      explanation: example.feedback
    })
  }
}
```

### Step 3: Reinforcement Learning

Learn from success/failure feedback:

```typescript
interface ReinforcementSignal {
  action: any
  reward: number  // -1 to +1
  state: any
  nextState: any
  done: boolean
}

// Example: Database optimization
const trainingEpisode = {
  task: "Optimize slow query",
  initialState: {
    query: "SELECT * FROM users WHERE email = ?",
    performance: "250ms average"
  },
  actions: [
    {
      action: "Add index on email column",
      reward: 0.8,  // Good improvement
      newPerformance: "45ms average"
    },
    {
      action: "Denormalize user data",
      reward: -0.5,  // Works but violates normalization
      newPerformance: "30ms but data duplication"
    },
    {
      action: "Use covering index",
      reward: 1.0,  // Optimal solution
      newPerformance: "25ms, no tradeoffs"
    }
  ]
}
```

### Step 4: Human-in-the-Loop Feedback

Collect feedback from real usage:

```yaml
feedback_collection:
  - scenario_id: "db-001"
    user_rating: 9/10
    comments: "Great schema, but could use more comments in migration"
    improvements:
      - Add inline comments to SQL
      - Include rollback scripts

  - scenario_id: "db-002"
    user_rating: 6/10
    comments: "Missed opportunity for partitioning on large table"
    improvements:
      - Analyze table size in requirements
      - Suggest partitioning for >1M rows

  - scenario_id: "db-003"
    user_rating: 10/10
    comments: "Perfect! Exactly what I needed"
    keep_doing:
      - Clear explanations
      - Complete migration scripts
      - Performance estimates
```

**Feedback Integration**:

```typescript
function integrateHumanFeedback(feedback: Feedback[]): void {
  // 1. Identify patterns in feedback
  const patterns = analyzePatterns(feedback)

  // 2. Update agent prompts/examples
  for (const pattern of patterns) {
    if (pattern.frequency > 0.3) {
      agent.addGuideline(pattern.improvement)
    }
  }

  // 3. Create new training examples from positive feedback
  const exemplars = feedback.filter(f => f.rating >= 9)
  for (const ex of exemplars) {
    trainingSet.add(convertToExample(ex))
  }

  // 4. Create negative examples from failures
  const failures = feedback.filter(f => f.rating <= 5)
  for (const fail of failures) {
    agent.addAntiPattern(fail.scenario, fail.comments)
  }
}
```

### Step 5: Knowledge Enhancement

Expand agent's knowledge base:

**Domain Knowledge**:

```yaml
knowledge_additions:
  database_best_practices:
    - "Always use UUID for primary keys in multi-tenant systems"
    - "Index all foreign keys by default"
    - "Use TIMESTAMPTZ for all timestamps"
    - "Implement soft deletes with deleted_at column"

  performance_patterns:
    - "N+1 query problem: Use JOINs or batch loading"
    - "Index covering for read-heavy queries"
    - "Partitioning for tables >10M rows"

  anti_patterns:
    - "AVOID: SELECT * in production code"
    - "AVOID: Using NULL for booleans"
    - "AVOID: String concatenation for SQL (injection risk)"
```

**Case Library**:

```typescript
// Build case library from successful scenarios
interface Case {
  problem: string
  context: any
  solution: any
  reasoning: string
  applicability: string[]
}

agent.caseLibrary.add({
  problem: "Multi-tenant data isolation",
  context: { architecture: "SaaS", database: "PostgreSQL" },
  solution: {
    pattern: "organization_id on all tables",
    indexes: "index on organization_id + other query columns",
    policies: "Row-level security policies"
  },
  reasoning: "Ensures data isolation while maintaining query performance",
  applicability: ["SaaS", "multi-tenant", "B2B"]
})
```

### Step 6: Continuous Improvement

Set up ongoing learning:

```typescript
// Training schedule
const improvementPlan = {
  daily: {
    action: "Review new user interactions",
    threshold: "Process if >10 new scenarios"
  },
  weekly: {
    action: "Retrain on failed cases",
    threshold: "If error rate >5%"
  },
  monthly: {
    action: "Comprehensive retraining",
    threshold: "Always - incorporate all feedback"
  },
  triggered: {
    action: "Immediate retraining",
    threshold: "If critical error or security issue"
  }
}
```

### Step 7: Validate Training Effectiveness

Measure improvement:

```yaml
before_training:
  test_pass_rate: 87%
  user_satisfaction: 7.2/10
  avg_response_time: 3.8s
  edge_case_handling: 65%

after_training:
  test_pass_rate: 96%  # +9%
  user_satisfaction: 8.9/10  # +24%
  avg_response_time: 2.1s  # -45%
  edge_case_handling: 89%  # +24%

improvements:
  most_improved: "Edge case handling"
  areas_to_work: "Complex multi-table queries"
  ready_for_production: true
```

### Step 8: Training Report

```markdown
# Training Report: {agent-name}

## Training Summary

- **Training Method**: Hybrid (Supervised + Reinforcement + Human Feedback)
- **Training Duration**: {duration}
- **Scenarios Processed**: {count}
- **Feedback Integrated**: {count}

## Performance Improvements

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Test Pass Rate | 87% | 96% | +9% |
| User Rating | 7.2/10 | 8.9/10 | +24% |
| Response Time | 3.8s | 2.1s | -45% |
| Edge Cases | 65% | 89% | +24% |

## Knowledge Enhancements

### Added Capabilities
- Partition strategy for large tables
- Advanced index optimization
- Query plan analysis

### Improved Areas
- Multi-table JOIN optimization
- Deadlock detection and resolution
- Migration script generation

### Anti-Patterns Learned
- Avoid denormalization without justification
- Don't use ENUM for frequently changing values
- Check for circular dependencies in FKs

## Training Examples

### Example 1: Multi-Tenant Schema
**Before**: Basic schema without proper isolation
**After**: Complete multi-tenant design with RLS policies
**Improvement**: 100% data isolation, 40% better queries

### Example 2: Query Optimization
**Before**: Suggested single-column index
**After**: Covering index with optimal column order
**Improvement**: 3x faster queries

## User Feedback Integration

Positive feedback themes:
- Clear, actionable recommendations
- Complete migration scripts
- Performance impact estimates

Areas for improvement:
- More complex JOIN scenarios
- Better handling of legacy schemas
- Rollback script generation

## Next Steps

✓ Training complete - Ready for evaluation
→ Run: /agent-foundry/evaluate {agent-name}
→ Run: /agent-foundry/grade {agent-name}

## Recommendation

Agent shows significant improvement and is ready for:
1. Comprehensive evaluation
2. Grading against production standards
3. Beta deployment to select customers
```

## Training Modes

### Mode 1: Supervised

Learn from expert-labeled examples

**Duration**: 2-4 hours
**Data Required**: 50-100 labeled examples
**Best For**: Well-defined tasks with clear right/wrong answers

### Mode 2: Reinforcement

Learn from reward signals

**Duration**: 4-8 hours
**Data Required**: Environment for trial-and-error
**Best For**: Optimization tasks with measurable outcomes

### Mode 3: Hybrid (Default)

Combined approach with human feedback

**Duration**: 6-12 hours
**Data Required**: Examples + feedback + real usage
**Best For**: Complex tasks requiring both accuracy and user satisfaction

## Usage Examples

### Example 1: Train Database Architect

```bash
/agent-foundry/train database-architect --mode hybrid --examples ./training-data/
```

Trains with:

- 75 expert examples
- Real user feedback
- Performance optimization rewards

### Example 2: Quick Training

```bash
/agent-foundry/train security-auditor --mode supervised
```

Fast training from curated examples only.

### Example 3: Continuous Learning

```bash
/agent-foundry/train cost-optimizer --mode reinforcement --continuous
```

Sets up ongoing learning from usage data.

## Quality Gates

Before proceeding to evaluation:

✅ Improvement in all key metrics
✅ No regression in previously working scenarios
✅ Edge case handling improved
✅ User satisfaction increased
✅ Performance within acceptable range
✅ Knowledge base enriched
✅ Ready for production evaluation

## Best Practices

1. **Start Small** - Begin with supervised training on core capabilities
2. **Iterate Quickly** - Short training cycles with validation
3. **Collect Feedback** - User feedback is the most valuable signal
4. **Avoid Overfitting** - Ensure agent generalizes well
5. **Monitor Regression** - Track performance on baseline tests
6. **Document Learning** - Record what improved and why
