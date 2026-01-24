---
description: Analyze task complexity and recommend optimal Claude model (Haiku/Sonnet/Opus)
argument-hint: <task description>
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
---

# Model Analysis Command

## What This Command Does

Analyzes the complexity of a given task and recommends the optimal Claude model to use, balancing cost-effectiveness with performance requirements. Uses a 5-dimensional scoring system to evaluate tasks and route them to Haiku (fast/cheap), Sonnet (balanced), or Opus (powerful).

**Key Features:**

- Multi-dimensional complexity scoring (1-5 on each dimension)
- Cost-benefit analysis with pricing transparency
- Confidence ratings for recommendations
- Alternative model suggestions
- Estimated completion time by model

## Complexity Scoring Dimensions

Tasks are evaluated on 5 dimensions (1-5 each, total 5-25 points):

1. **Cognitive Load** (1-5)
   - 1: Single-step, straightforward task
   - 3: Multi-step with moderate complexity (3-8 steps)
   - 5: Highly complex, many interdependent steps (9+ steps)

2. **Domain Expertise** (1-5)
   - 1: General knowledge, no specialized skills
   - 3: Moderate domain knowledge (API integration, standard frameworks)
   - 5: Deep expertise required (security audits, advanced algorithms, compliance)

3. **Reasoning Depth** (1-5)
   - 1: Direct/literal execution
   - 3: Some decision-making and logic
   - 5: Complex reasoning, novel problem-solving, architecture design

4. **Risk & Impact** (1-5)
   - 1: Low risk, easily reversible
   - 3: Moderate risk, affects non-critical systems
   - 5: High risk, production systems, security, compliance

5. **Ambiguity** (1-5)
   - 1: Crystal clear requirements
   - 3: Some interpretation needed
   - 5: Highly ambiguous, requires clarification and exploration

## Model Routing Rules

**Total Score → Model Selection:**

- **5-10 points**: Claude Haiku (simple/straightforward)
- **11-17 points**: Claude Sonnet (medium complexity) ⭐ Most tasks
- **18-25 points**: Claude Opus (high complexity)

## Usage Examples

### Example 1: Simple File Edit

```bash
/model:analyze "Fix typo in README.md line 42, change 'teh' to 'the'"
```

**Expected Output:**

```
Task Complexity Analysis
========================

Task: Fix typo in README.md line 42, change 'teh' to 'the'

Dimension Scores:
- Cognitive Load: 1/5 (single step, clear action)
- Domain Expertise: 1/5 (no specialized knowledge)
- Reasoning Depth: 1/5 (direct literal change)
- Risk & Impact: 1/5 (low risk, documentation)
- Ambiguity: 1/5 (perfectly clear)

TOTAL SCORE: 5/25

Recommended Model: Claude Haiku (claude-3-5-haiku-20241022)
Confidence: 100%

Cost Comparison:
- Haiku: ~$0.0001 per task ✓ RECOMMENDED
- Sonnet: ~$0.0003 per task (3x more expensive, no benefit)
- Opus: ~$0.001 per task (10x more expensive, massive overkill)

Estimated Time: <1 second
ROI: Optimal choice - Haiku perfect for simple edits
```

### Example 2: Medium Complexity API Integration

```bash
/model:analyze "Implement OAuth 2.0 authentication for Zoho CRM API with token refresh logic and error handling"
```

**Expected Output:**

```
Task Complexity Analysis
========================

Task: Implement OAuth 2.0 authentication for Zoho CRM API with token refresh logic and error handling

Dimension Scores:
- Cognitive Load: 3/5 (multi-step workflow: auth flow, token storage, refresh, error handling)
- Domain Expertise: 3/5 (OAuth 2.0 knowledge, API integration patterns)
- Reasoning Depth: 3/5 (decision-making on error handling strategies)
- Risk & Impact: 3/5 (affects CRM integration, moderate business impact)
- Ambiguity: 2/5 (clear OAuth spec, some implementation choices)

TOTAL SCORE: 14/25

Recommended Model: Claude Sonnet (claude-sonnet-4-5-20250929)
Confidence: 95%

Cost Comparison:
- Haiku: ~$0.0001 per task (may struggle with OAuth complexity)
- Sonnet: ~$0.0003 per task ✓ RECOMMENDED (sweet spot)
- Opus: ~$0.001 per task (3x more, unnecessary for standard OAuth)

Estimated Time: 2-4 seconds
ROI: Optimal choice - Sonnet handles API integration well at moderate cost

Alternative: If budget is tight and task is well-documented, try Haiku first
```

### Example 3: Complex Security Audit

```bash
/model:analyze "Perform comprehensive security audit of authentication system for HIPAA compliance with threat modeling and penetration testing recommendations"
```

**Expected Output:**

```
Task Complexity Analysis
========================

Task: Perform comprehensive security audit of authentication system for HIPAA compliance

Dimension Scores:
- Cognitive Load: 5/5 (multi-faceted: code review, compliance check, threat modeling, recommendations)
- Domain Expertise: 5/5 (HIPAA regulations, security best practices, healthcare compliance)
- Reasoning Depth: 5/5 (threat analysis, risk assessment, strategic recommendations)
- Risk & Impact: 5/5 (CRITICAL - HIPAA compliance, patient data security)
- Ambiguity: 3/5 (HIPAA clear but threat landscape complex)

TOTAL SCORE: 23/25

Recommended Model: Claude Opus (claude-opus-4-20250514)
Confidence: 100%

Cost Comparison:
- Haiku: ~$0.0001 per task (UNSAFE - will miss critical security issues)
- Sonnet: ~$0.0003 per task (RISKY - may miss subtle compliance gaps)
- Opus: ~$0.001 per task ✓ REQUIRED (only model with depth for security audits)

Estimated Time: 5-15 seconds
ROI: CRITICAL INVESTMENT - Opus prevents compliance violations (potential $50K+ HIPAA fines)

⚠️ SECURITY CRITICAL: This task requires Opus-level reasoning. Do not downgrade.
```

### Example 4: Batch Analysis

```bash
/model:analyze --file tasks.txt --format csv --output model-recommendations.csv
```

**Input file (tasks.txt):**

```
Update button color in CSS
Refactor user authentication module
Add logging to payment processor
Fix database connection pool leak
Design microservices architecture for e-commerce platform
```

**Expected Output (model-recommendations.csv):**

```csv
Task,Score,Model,Confidence,Estimated_Cost,Reason
"Update button color in CSS",5,Haiku,100%,$0.0001,Simple styling change
"Refactor user authentication module",16,Sonnet,90%,$0.0003,Moderate complexity refactoring
"Add logging to payment processor",13,Sonnet,85%,$0.0003,Payment system requires care
"Fix database connection pool leak",15,Sonnet,95%,$0.0003,Technical debugging with moderate risk
"Design microservices architecture",21,Opus,100%,$0.001,Complex architecture requiring deep reasoning
```

## Business Value / ROI

### Cost Savings

- **Automatic optimization**: Avoid using Opus ($0.001/task) when Haiku ($0.0001/task) suffices → **90% cost reduction**
- **Prevent over-engineering**: Stop using Sonnet for simple tasks → **66% cost reduction on simple tasks**
- **Confidence in upgrades**: Know when to invest in Opus for critical tasks → **Prevents rework and failures**

### Real-World Scenarios

**Scenario 1: Documentation Updates**

- 100 simple doc edits/month
- Without analysis: Using Sonnet = $0.03/month
- With analysis: Using Haiku = $0.01/month
- **Savings: $0.02/month** (66% reduction)

**Scenario 2: Mixed Development Tasks**

- 200 tasks/month: 100 simple, 80 medium, 20 complex
- Without analysis: Using Sonnet for all = $60/month
- With analysis: 100 Haiku ($10) + 80 Sonnet ($24) + 20 Opus ($20) = $54/month
- **Savings: $6/month** (10% reduction) + **Better quality on complex tasks**

**Scenario 3: Enterprise Security Project**

- 5 security audits/month
- Without analysis: Using Sonnet (inadequate) = $1.50/month + **risk of missed vulnerabilities**
- With analysis: Using Opus (appropriate) = $5/month + **comprehensive security coverage**
- **ROI: Prevents potential $50,000+ HIPAA violation fines**

### Productivity Gains

- **Faster simple tasks**: Haiku responds in <1 second vs Sonnet's 1-3 seconds
- **Better quality on complex tasks**: Opus prevents rework on critical systems
- **Confidence**: Know you're using the right tool for the job

## Success Metrics

### Accuracy Metrics

- **Recommendation Acceptance Rate**: % of times users follow the recommendation
- **Target: 85%+** (indicates accurate complexity assessment)

### Cost Metrics

- **Average Cost Per Task**: Total spend / total tasks
- **Target: <$0.0004/task** (indicates good Haiku/Sonnet mix)

### Quality Metrics

- **Task Success Rate**: % of tasks completed successfully on first try
- **Target: 95%+** (indicates model was appropriately matched to complexity)
- **Downgrade Rate**: % of Opus/Sonnet tasks that could have used cheaper model
- **Target: <5%** (indicates we're not over-engineering)

### Performance Metrics

- **Analysis Time**: Time to analyze and recommend
- **Target: <2 seconds** (shouldn't slow down workflow)
- **Batch Throughput**: Tasks analyzed per minute in batch mode
- **Target: 30+ tasks/minute**

## Advanced Options

### Flags

- `--file <path>`: Analyze tasks from file (one per line)
- `--format <json|csv|markdown>`: Output format for results
- `--output <path>`: Save analysis to file
- `--override-risk <low|medium|high>`: Override risk assessment
- `--budget <amount>`: Factor budget constraints into recommendations
- `--explain`: Show detailed reasoning for each dimension score
- `--compare`: Show side-by-side comparison of all three models

### Override Rules

**Security Tasks**: Always Sonnet minimum

```bash
/model:analyze "Update user password hashing algorithm" --override-risk high
```

**Compliance Tasks**: Always Opus for HIPAA/PCI-DSS/SOC2

```bash
/model:analyze "Review payment processing for PCI-DSS compliance" --override-risk critical
```

**Budget-Constrained**: Try Haiku first, escalate if needed

```bash
/model:analyze "Implement feature X" --budget tight
```

## Implementation Notes

The analysis engine uses:

1. **Natural Language Processing**: Extract task components and requirements
2. **Pattern Matching**: Identify security, compliance, and high-risk keywords
3. **Complexity Heuristics**: Count steps, dependencies, decision points
4. **Historical Data**: Learn from past task outcomes
5. **Cost Modeling**: Real-time pricing from Anthropic API

## Integration with Other Commands

```bash
# Analyze before executing
/model:analyze "Refactor authentication module"
# Based on recommendation, run with appropriate model
/dev:implement "Refactor authentication module" --model sonnet

# Batch optimize all pending tasks
/model:analyze --file backlog.txt --output recommendations.csv
/model:optimize --apply recommendations.csv
```

## Error Handling

**Ambiguous Tasks:**

```
⚠️ Task ambiguity detected (score: 5/5)
Recommended action: Request clarification before selecting model

Questions to resolve:
1. What specific aspects of the system should be refactored?
2. Are there performance/security requirements?
3. What is the acceptable risk level?

Tentative recommendation: Start with Sonnet, escalate to Opus if needed
```

**Budget Conflicts:**

```
⚠️ Budget constraint conflict
Recommended model: Opus ($0.001)
Budget allows: Sonnet ($0.0003)

Risk: Using Sonnet may result in incomplete security analysis
Recommendation: Either increase budget or reduce scope

Alternative: Break task into phases
- Phase 1: Sonnet for initial review → $0.0003
- Phase 2: Opus for critical findings → $0.001 (only if issues found)
```
