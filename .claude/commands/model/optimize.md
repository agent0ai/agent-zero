---
description: Optimize model selection across agents for cost/performance balance
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
---

# Model Optimization Command

## What This Command Does

Analyzes your current AI agent ecosystem and optimizes model selection across all agents, slash commands, and workflows to maximize cost savings while maintaining quality. Reviews historical usage patterns, identifies over-engineering, and provides actionable recommendations.

**Key Features:**

- Analyzes all agents in `.claude/agents/` and commands in `.claude/commands/`
- Reviews historical task patterns and outcomes
- Identifies cost optimization opportunities
- Suggests model reassignments with impact analysis
- Generates optimization plan with ROI projections
- Optional auto-apply mode for immediate optimization

## Core Optimization Strategies

### 1. Agent-Level Optimization

Review each agent's default model selection and recommend adjustments based on actual task complexity.

### 2. Command-Level Optimization

Analyze slash command usage patterns and optimize model routing per command.

### 3. Workflow-Level Optimization

Optimize multi-agent workflows to use the right model at each stage.

### 4. Pattern-Based Optimization

Identify recurring task patterns and create optimized routing rules.

## Usage Examples

### Example 1: Basic Optimization Scan

```bash
/model:optimize
```

**Expected Output:**

```
AI Model Optimization Analysis
==============================

Scanning project: /home/webemo-aaron/projects/prompt-blueprint

📊 Current State (Last 30 Days)
-------------------------------
Total Tasks: 1,247
Total Cost: $187.43
Average Cost/Task: $0.150

Model Distribution:
- Haiku:  234 tasks (18.8%) → $2.34 (1.2%)
- Sonnet: 891 tasks (71.4%) → $133.65 (71.3%)
- Opus:   122 tasks (9.8%) → $51.44 (27.5%)

🎯 Optimization Opportunities
------------------------------

1. OVER-ENGINEERING: Documentation Updates
   Current: 89 tasks using Sonnet
   Recommended: Use Haiku
   Savings: $17.80/month (89 tasks × $0.20 saved)
   Confidence: 95%

   Examples:
   - "Fix typo in README.md" → Sonnet (wasteful)
   - "Update version number" → Sonnet (wasteful)
   - "Add code comment" → Sonnet (wasteful)

2. UNDER-ENGINEERING: Security Reviews
   Current: 12 tasks using Sonnet
   Recommended: Use Opus
   Additional Cost: $8.40/month (12 tasks × $0.70)
   Risk Reduction: CRITICAL (prevents security vulnerabilities)

   Examples:
   - "Review authentication logic" → Sonnet (risky)
   - "Audit API permissions" → Sonnet (risky)

3. WORKFLOW INEFFICIENCY: Multi-Agent Pipelines
   Current: All steps use Sonnet
   Recommended: Mixed approach
   Savings: $23.50/month

   Example: Feature Development Pipeline
   - Step 1: Planning → Sonnet ✓ (correct)
   - Step 2: Boilerplate generation → Haiku (downgrade)
   - Step 3: Core logic → Sonnet ✓ (correct)
   - Step 4: Documentation → Haiku (downgrade)
   - Step 5: Security review → Opus (upgrade)

4. AGENT MISCONFIGURATION: Documentation Agent
   Current: Default model = Sonnet
   Recommended: Default model = Haiku
   Savings: $45.30/month (227 tasks × $0.20)
   Quality Impact: NONE (Haiku excellent for docs)

💰 Total Optimization Potential
--------------------------------
Net Monthly Savings: $77.60
Cost Reduction: 41.4%
Quality Improvement: +15% (better model matching)

Optimized Costs:
- Haiku:  412 tasks → $4.12 (3.8%)
- Sonnet: 701 tasks → $105.15 (95.6%)
- Opus:   134 tasks → $0.54 (0.6%)
Total: $109.83/month (was $187.43)

📋 Recommended Actions
-----------------------
1. Update documentation-agent.md (line 12): model: haiku
2. Add routing rule for security tasks: always use Opus
3. Update /dev:implement workflow: use Haiku for boilerplate
4. Create pattern: "typo|fix|update version" → Haiku

Apply these optimizations? (y/n)
```

### Example 2: Auto-Apply Optimization

```bash
/model:optimize --auto-apply --backup
```

**Expected Output:**

```
AI Model Optimization (Auto-Apply Mode)
========================================

✓ Created backup: .claude/backups/optimization-2025-11-25-14-30-00/

Applying optimizations...

1. Updating agent: documentation-expert-agent.md
   Change: model: sonnet → model: haiku
   ✓ Applied

2. Creating routing rule: security-tasks-opus.rule
   Pattern: security|audit|compliance|HIPAA|PCI-DSS
   Rule: minimum_model = opus
   ✓ Applied

3. Updating workflow: /dev:implement
   Step 2 (boilerplate): sonnet → haiku
   Step 4 (documentation): sonnet → haiku
   Step 5 (review): sonnet → opus (if security-related)
   ✓ Applied

4. Creating pattern rules: simple-tasks.rules
   Patterns: typo|version|comment|spacing|formatting
   Rule: model = haiku
   ✓ Applied

✅ Optimization Complete
------------------------
Changes Applied: 4
Estimated Savings: $77.60/month
Quality Impact: +15%

Rollback command: /model:optimize --rollback 2025-11-25-14-30-00
```

### Example 3: Specific Agent Optimization

```bash
/model:optimize --agent documentation-expert-agent
```

**Expected Output:**

```
Agent Optimization: documentation-expert-agent
===============================================

📊 Current Configuration
------------------------
Default Model: Sonnet
Fallback: Opus (if Sonnet fails)
Cost per invocation: ~$0.0003

📈 Usage Statistics (Last 30 Days)
----------------------------------
Total Invocations: 227
Total Cost: $68.10
Success Rate: 98.7%
Average Response Time: 2.3s

Task Breakdown:
- Create documentation: 89 tasks (39.2%)
- Update documentation: 112 tasks (49.3%)
- Review documentation: 19 tasks (8.4%)
- Format/fix typos: 7 tasks (3.1%)

💡 Optimization Recommendation
-------------------------------
Recommended Model: Haiku
Confidence: 95%

Reasoning:
✓ Documentation is straightforward writing task
✓ No complex reasoning required
✓ Haiku has excellent writing capabilities
✓ 98.7% success rate indicates task simplicity
✓ Speed improvement: 2.3s → <1s

Cost Impact:
- Current: 227 tasks × $0.0003 = $68.10/month
- Optimized: 227 tasks × $0.0001 = $22.70/month
- Savings: $45.40/month (66.7% reduction)

Quality Impact: NONE (Haiku matches Sonnet for documentation)

⚠️ Exception Handling
----------------------
For complex technical documentation (API specs, architecture docs):
- Keep using Sonnet
- Estimated: 15% of tasks (34 tasks/month)
- Cost: $10.20/month

Refined Optimization:
- Simple docs (85%): Haiku → $19.30/month
- Complex docs (15%): Sonnet → $10.20/month
- Total: $29.50/month
- Savings: $38.60/month (56.7% reduction)

Apply optimization? (y/n)
```

### Example 4: Workflow-Specific Optimization

```bash
/model:optimize --workflow /dev:full-cycle
```

**Expected Output:**

```
Workflow Optimization: /dev:full-cycle
=======================================

Current Workflow Steps (8 steps, all using Sonnet):
1. Feature planning & requirements → Sonnet
2. Architecture design → Sonnet
3. Boilerplate generation → Sonnet
4. Core implementation → Sonnet
5. Test generation → Sonnet
6. Documentation → Sonnet
7. Code review → Sonnet
8. Security audit → Sonnet

💰 Current Cost per Execution: $0.0024 (8 × $0.0003)

🎯 Optimized Workflow
---------------------

1. Feature planning & requirements
   Current: Sonnet ✓
   Optimized: Sonnet (KEEP)
   Reason: Requires reasoning and decision-making

2. Architecture design
   Current: Sonnet ✓
   Optimized: Opus (UPGRADE) ⚠️
   Reason: Critical decisions, long-term impact
   Additional Cost: +$0.0007

3. Boilerplate generation
   Current: Sonnet ✗
   Optimized: Haiku (DOWNGRADE)
   Reason: Repetitive code generation, no complex logic
   Savings: -$0.0002

4. Core implementation
   Current: Sonnet ✓
   Optimized: Sonnet (KEEP)
   Reason: Business logic requires moderate complexity

5. Test generation
   Current: Sonnet ✗
   Optimized: Haiku (DOWNGRADE)
   Reason: Pattern-based test generation
   Savings: -$0.0002

6. Documentation
   Current: Sonnet ✗
   Optimized: Haiku (DOWNGRADE)
   Reason: Straightforward writing task
   Savings: -$0.0002

7. Code review
   Current: Sonnet ✓
   Optimized: Sonnet (KEEP)
   Reason: Requires analysis and judgment

8. Security audit
   Current: Sonnet ✗
   Optimized: Opus (UPGRADE) ⚠️
   Reason: CRITICAL - security requires deep analysis
   Additional Cost: +$0.0007

📊 Cost-Benefit Analysis
-------------------------
Current Cost: $0.0024 per execution
Optimized Cost: $0.0025 per execution
Net Change: +$0.0001 (+4.2%)

BUT:
- Quality Improvement: +35% (better architecture, better security)
- Risk Reduction: 85% (Opus for security catches critical issues)
- Time Savings: 15% (Haiku faster on simple tasks)

ROI: Prevents potential production issues worth $10,000+ per incident

Recommendation: ACCEPT (+4% cost for 35% quality improvement)

Apply optimization? (y/n)
```

## Business Value / ROI

### Cost Optimization

- **Typical savings: 30-50%** across all model usage
- **No quality loss**: Maintains or improves task success rates
- **Automatic enforcement**: Once configured, optimization is continuous

### Quality Improvements

- **Better model matching**: Use Opus when it matters, Haiku when it doesn't
- **Risk reduction**: Automatically upgrade security/compliance tasks to Opus
- **Faster simple tasks**: Haiku responds in <1 second vs Sonnet's 1-3 seconds

### Real-World ROI Examples

**Small Team (500 tasks/month)**

- Current spend: $75/month (all Sonnet)
- Optimized: $42/month (40% Haiku, 50% Sonnet, 10% Opus)
- **Monthly savings: $33 → Annual savings: $396**

**Medium Team (2,000 tasks/month)**

- Current spend: $300/month (mixed, unoptimized)
- Optimized: $168/month (systematic optimization)
- **Monthly savings: $132 → Annual savings: $1,584**

**Enterprise (10,000 tasks/month)**

- Current spend: $1,500/month
- Optimized: $825/month
- **Monthly savings: $675 → Annual savings: $8,100**

## Success Metrics

### Cost Metrics

- **Cost Per Task**: Average spend per AI task
  - **Target: <$0.0002** (indicates good Haiku usage)
- **Monthly Spend**: Total AI model costs
  - **Target: 30-50% reduction after optimization**

### Quality Metrics

- **Task Success Rate**: % of tasks completed successfully first try
  - **Target: 95%+** (optimization shouldn't hurt quality)
- **Escalation Rate**: % of tasks that need model upgrade
  - **Target: <5%** (indicates good initial routing)

### Efficiency Metrics

- **Average Response Time**: Speed of task completion
  - **Target: Improve 10-20%** (more Haiku = faster responses)
- **Over-Engineering Rate**: % of tasks using unnecessarily powerful models
  - **Target: <10%** (was typically 30-40% before optimization)

### Business Metrics

- **ROI**: Savings vs. optimization time investment
  - **Target: 10x return** (1 hour optimization saves 10+ hours of waste)
- **Quality Incidents**: Production issues due to model selection
  - **Target: 0** (security tasks should auto-upgrade to Opus)

## Advanced Options

### Flags

- `--auto-apply`: Apply optimizations without confirmation
- `--backup`: Create backup before applying changes (recommended)
- `--dry-run`: Show what would change without applying
- `--agent <name>`: Optimize specific agent only
- `--workflow <name>`: Optimize specific workflow only
- `--timeframe <days>`: Analyze usage over N days (default: 30)
- `--threshold <percentage>`: Minimum savings threshold to recommend (default: 10%)
- `--aggressive`: More aggressive optimization (higher risk)
- `--conservative`: Conservative optimization (lower risk)
- `--rollback <timestamp>`: Revert to previous configuration

### Configuration Files

**Optimization Rules** (`.claude/config/optimization-rules.yaml`):

```yaml
rules:
  # Never downgrade security tasks
  - pattern: "security|audit|compliance|HIPAA|PCI-DSS|SOC2"
    minimum_model: opus
    override: never

  # Always downgrade documentation
  - pattern: "documentation|readme|comment|typo"
    maximum_model: haiku
    exceptions:
      - "API documentation"
      - "architecture documentation"

  # Workflow-specific rules
  - workflow: "/dev:full-cycle"
    steps:
      architecture: opus
      boilerplate: haiku
      security: opus
```

**Budget Constraints** (`.claude/config/budget.yaml`):

```yaml
budget:
  monthly_limit: 200.00
  alert_threshold: 0.80  # Alert at 80% of budget

  model_quotas:
    opus:
      max_monthly_spend: 60.00
      max_tasks: 1000
      require_approval_above: 100  # tasks/month

    sonnet:
      max_monthly_spend: 120.00
      preferred: true

    haiku:
      max_monthly_spend: 20.00
      unlimited: true  # No quota enforcement
```

## Optimization Strategies

### Conservative Strategy (Default)

- Only optimize tasks with 95%+ confidence
- Preserve all existing upgrades (Opus stays Opus)
- Minimal risk to quality
- Typical savings: 30-35%

### Balanced Strategy

- Optimize tasks with 85%+ confidence
- Smart downgrades with fallback mechanisms
- Some calculated risk for higher savings
- Typical savings: 40-45%

### Aggressive Strategy

- Optimize tasks with 70%+ confidence
- Aggressive downgrades with auto-escalation
- Higher risk, but monitors for failures
- Typical savings: 50-60%
- **Use with caution**: Monitor closely for quality issues

## Integration with Other Commands

```bash
# Step 1: Analyze current state
/model:report --detailed

# Step 2: Run optimization
/model:optimize --dry-run

# Step 3: Review and apply
/model:optimize --auto-apply --backup

# Step 4: Monitor results
/model:report --compare-before-after

# Step 5: Fine-tune
/model:optimize --agent specific-agent --aggressive
```

## Rollback and Safety

### Automatic Backups

Every optimization creates a timestamped backup:

```
.claude/backups/optimization-2025-11-25-14-30-00/
├── agents/
├── commands/
├── config/
└── manifest.json
```

### Rollback

```bash
# List available backups
/model:optimize --list-backups

# Rollback to specific backup
/model:optimize --rollback 2025-11-25-14-30-00

# Rollback last optimization
/model:optimize --rollback last
```

### Safety Mechanisms

1. **Dry-run mode**: Preview changes before applying
2. **Automatic backups**: Every change is reversible
3. **Confidence thresholds**: Only optimize high-confidence changes
4. **Never downgrade security**: Critical tasks stay on Opus
5. **Monitoring**: Track success rates after optimization
6. **Auto-escalation**: Failed tasks automatically retry with better model

## Error Handling

**Insufficient Data:**

```
⚠️ Insufficient usage data for optimization
Current data: 47 tasks over 7 days
Recommended: 200+ tasks over 30 days

Suggestions:
1. Wait for more usage data (recommended)
2. Run optimization with --conservative flag
3. Use /model:analyze for individual task optimization
```

**Conflicting Requirements:**

```
⚠️ Optimization conflict detected

Agent: security-audit-agent
Current: Opus
Recommendation: Sonnet (cost optimization)
Conflict: Security policy requires Opus minimum

Resolution: Keeping Opus (policy override)
This agent excluded from optimization.
```

## Best Practices

1. **Run monthly**: Optimize at least once per month as patterns change
2. **Start conservative**: Use default strategy first, then try balanced
3. **Monitor quality**: Track success rates after optimization
4. **Use backups**: Always create backups before auto-apply
5. **Review suggestions**: Don't blindly accept all recommendations
6. **Set budgets**: Configure budget constraints to prevent overspending
7. **Document exceptions**: Add comments for manual overrides
