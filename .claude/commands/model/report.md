---
description: Generate comprehensive model usage and cost reports with trend analysis
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
---

# Model Usage & Cost Report Command

## What This Command Does

Generates comprehensive reports on AI model usage, costs, and performance across all agents, commands, and workflows. Provides trend analysis, cost breakdowns, efficiency metrics, and actionable insights for optimization.

**Key Features:**

- Detailed cost breakdowns by model, agent, command, and time period
- Usage trends and forecasting
- Performance metrics (success rate, response time, quality)
- Comparison reports (before/after optimization, period over period)
- Export to multiple formats (JSON, CSV, PDF, Markdown)
- Interactive dashboard mode

## Report Types

### 1. Summary Report (Default)

High-level overview of model usage and costs.

### 2. Detailed Report

Comprehensive breakdown with all metrics and dimensions.

### 3. Trend Report

Historical analysis with forecasting.

### 4. Comparison Report

Compare two time periods or before/after optimization.

### 5. Agent Report

Detailed analysis of specific agent's model usage.

### 6. Cost Audit Report

Financial audit with budget tracking and alerts.

## Usage Examples

### Example 1: Basic Summary Report

```bash
/model:report
```

**Expected Output:**

```
AI Model Usage Report
=====================
Period: Last 30 days (Oct 26 - Nov 25, 2025)
Project: prompt-blueprint

📊 Executive Summary
--------------------
Total Tasks: 1,247
Total Cost: $187.43
Average Cost/Task: $0.150
Success Rate: 96.8%
Average Response Time: 2.1s

💰 Cost Breakdown by Model
---------------------------
┌──────────┬───────┬─────────┬──────────┬─────────┐
│ Model    │ Tasks │ % Tasks │ Cost ($) │ % Cost  │
├──────────┼───────┼─────────┼──────────┼─────────┤
│ Haiku    │   234 │  18.8%  │     2.34 │   1.2%  │
│ Sonnet   │   891 │  71.4%  │   133.65 │  71.3%  │
│ Opus     │   122 │   9.8%  │    51.44 │  27.5%  │
├──────────┼───────┼─────────┼──────────┼─────────┤
│ Total    │ 1,247 │ 100.0%  │   187.43 │ 100.0%  │
└──────────┴───────┴─────────┴──────────┴─────────┘

📈 Trends (vs. Previous 30 Days)
--------------------------------
Tasks: +23.4% (1,011 → 1,247)
Cost: +18.7% ($157.89 → $187.43)
Efficiency: +3.8% (cost/task improved)

🎯 Top Cost Drivers
-------------------
1. /dev:full-cycle workflow: $45.23 (24.1%)
2. security-audit-agent: $28.90 (15.4%)
3. /prompt:generate command: $22.15 (11.8%)
4. /zoho:sync-data workflow: $18.67 (10.0%)
5. documentation-expert-agent: $15.40 (8.2%)

⚡ Performance Highlights
-------------------------
✓ Fast Tasks (<1s): 234 (18.8%) - All Haiku
✓ High Success Rate: 96.8% (1,207/1,247 successful)
✗ Failed Tasks: 40 (3.2%) - Cost: $8.94 (wasted)

🔍 Optimization Opportunities
------------------------------
Potential Monthly Savings: $77.60 (41.4%)
Primary Opportunities:
1. Documentation tasks using Sonnet → Haiku: $45.40/mo
2. Boilerplate generation using Sonnet → Haiku: $18.20/mo
3. Security tasks using Sonnet → Opus: Better quality, +$8.40/mo

💡 Recommendations
------------------
1. Run /model:optimize for detailed optimization plan
2. Review failed tasks - may need model upgrades
3. Consider budget alerts (currently at 93.7% of $200 limit)

Full detailed report: /model:report --detailed
```

### Example 2: Detailed Report with Export

```bash
/model:report --detailed --export pdf --output model-report-2025-11.pdf
```

**Expected Output:**

```
Generating Detailed AI Model Usage Report...
=============================================

Period: Last 30 days (Oct 26 - Nov 25, 2025)

📊 SECTION 1: Cost Analysis
============================

1.1 Total Costs
---------------
Total Spend: $187.43
Budget: $200.00
Utilization: 93.7%
Status: ⚠️ NEAR LIMIT (6.3% remaining)

1.2 Cost by Model
-----------------
Haiku:  $2.34   (1.2%)  [████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]
Sonnet: $133.65 (71.3%) [████████████████████████░░░░░░░░░░░]
Opus:   $51.44  (27.5%) [█████████░░░░░░░░░░░░░░░░░░░░░░░░░]

1.3 Cost by Category
--------------------
Development:     $89.34  (47.7%)
Documentation:   $34.12  (18.2%)
Security:        $28.90  (15.4%)
Integration:     $22.45  (12.0%)
Other:           $12.62  (6.7%)

1.4 Daily Cost Trend (Last 30 Days)
-----------------------------------
[ASCII graph showing daily costs]
Peak: Nov 15 ($12.34)
Average: $6.25/day
Trend: Increasing (+2.3%/week)

📈 SECTION 2: Usage Analysis
=============================

2.1 Task Volume by Model
-------------------------
Date Range: Oct 26 - Nov 25, 2025

Week 1 (Oct 26-Nov 1):
  Haiku:  52 tasks | Sonnet: 198 tasks | Opus: 28 tasks | Total: 278
Week 2 (Nov 2-Nov 8):
  Haiku:  58 tasks | Sonnet: 223 tasks | Opus: 31 tasks | Total: 312
Week 3 (Nov 9-Nov 15):
  Haiku:  61 tasks | Sonnet: 234 tasks | Opus: 32 tasks | Total: 327
Week 4 (Nov 16-Nov 22):
  Haiku:  63 tasks | Sonnet: 236 tasks | Opus: 31 tasks | Total: 330

Trend: +18.7% growth (Week 1 → Week 4)

2.2 Usage by Command
--------------------
┌─────────────────────────┬───────┬────────┬──────────┐
│ Command                 │ Tasks │ Model  │ Cost ($) │
├─────────────────────────┼───────┼────────┼──────────┤
│ /dev:implement          │   234 │ Sonnet │    35.10 │
│ /prompt:generate        │   189 │ Sonnet │    28.35 │
│ /dev:review             │   156 │ Sonnet │    23.40 │
│ /zoho:create-lead       │   123 │ Sonnet │    18.45 │
│ /dev:test               │    98 │ Sonnet │    14.70 │
│ /docs:update            │    89 │ Sonnet │    13.35 │ ⚠️ Should use Haiku
│ /security:audit         │    67 │ Opus   │    28.90 │
│ /auth:test              │    55 │ Sonnet │     8.25 │
│ (Others)                │   236 │ Mixed  │    17.03 │
└─────────────────────────┴───────┴────────┴──────────┘

2.3 Usage by Agent
------------------
┌──────────────────────────┬───────┬────────┬──────────┐
│ Agent                    │ Tasks │ Model  │ Cost ($) │
├──────────────────────────┼───────┼────────┼──────────┤
│ prompt-engineering-agent │   289 │ Sonnet │    43.35 │
│ documentation-agent      │   227 │ Sonnet │    34.05 │ ⚠️ Should use Haiku
│ security-audit-agent     │    67 │ Opus   │    28.90 │
│ zoho-crm-agent          │   156 │ Sonnet │    23.40 │
│ routing-coordinator      │   134 │ Sonnet │    20.10 │
│ dev-workflow-agent       │    98 │ Sonnet │    14.70 │
│ (Others)                 │   276 │ Mixed  │    22.93 │
└──────────────────────────┴───────┴────────┴──────────┘

⚡ SECTION 3: Performance Metrics
==================================

3.1 Success Rates by Model
---------------------------
Haiku:  231/234 = 98.7% success ✓ Excellent
Sonnet: 865/891 = 97.1% success ✓ Good
Opus:   111/122 = 91.0% success ⚠️ Below target

3.2 Response Time Distribution
-------------------------------
Haiku:
  Avg: 0.7s | P50: 0.6s | P95: 1.2s | P99: 1.8s

Sonnet:
  Avg: 2.1s | P50: 1.9s | P95: 4.2s | P99: 6.8s

Opus:
  Avg: 6.4s | P50: 5.8s | P95: 12.3s | P99: 18.9s

3.3 Quality Metrics
-------------------
Task Completion Rate: 96.8% (target: 95%+) ✓
First-Try Success: 94.2% (target: 90%+) ✓
Retry Rate: 3.8% (target: <5%) ✓
Escalation Rate: 2.1% (tasks requiring model upgrade)

3.4 Failed Tasks Analysis
--------------------------
Total Failures: 40 (3.2%)
Wasted Cost: $8.94

Failure Reasons:
- Insufficient model capability: 18 (45.0%) → Should have used Opus
- Timeout: 12 (30.0%) → Opus too slow, should optimize
- API errors: 7 (17.5%) → Infrastructure issues
- Other: 3 (7.5%)

💡 SECTION 4: Optimization Insights
====================================

4.1 Over-Engineering Detected
------------------------------
Tasks using more powerful model than needed:

Documentation updates: 89 tasks using Sonnet
  Recommended: Haiku
  Potential Savings: $17.80/month

Simple edits: 34 tasks using Sonnet
  Recommended: Haiku
  Potential Savings: $6.80/month

4.2 Under-Engineering Detected
-------------------------------
Tasks using less powerful model than needed:

Security reviews: 12 tasks using Sonnet (failed 3)
  Recommended: Opus
  Additional Cost: $8.40/month
  Risk Reduction: CRITICAL

4.3 Budget Forecast
-------------------
Current Trajectory: $187.43/month
7-Day Trend: +2.3%/week
30-Day Forecast: $204.78/month
Status: ⚠️ WILL EXCEED BUDGET in ~12 days

Recommendations:
1. Immediate optimization: -$77.60/month → $109.83/month
2. Budget increase to $250/month (accommodate growth)
3. Implement task prioritization for budget constraints

📑 SECTION 5: Recommendations
==============================

Priority 1 (HIGH IMPACT):
✓ Run /model:optimize to implement $77.60/month in savings
✓ Update documentation-agent to use Haiku by default
✓ Upgrade security tasks to Opus (prevent failures)

Priority 2 (MEDIUM IMPACT):
○ Review failed Opus tasks - may indicate timeout issues
○ Consider caching for repeated similar tasks
○ Implement budget alerts at 80% threshold

Priority 3 (LOW IMPACT):
○ Monitor Haiku success rate - currently excellent at 98.7%
○ Review routing rules monthly for pattern changes
○ Consider A/B testing Haiku vs Sonnet on borderline tasks

════════════════════════════════════════════════════════

✅ Report generated successfully
   Output: model-report-2025-11.pdf
   Size: 2.4 MB
   Pages: 18

   View report: open model-report-2025-11.pdf
   Share link: file:///home/webemo-aaron/projects/prompt-blueprint/reports/model-report-2025-11.pdf
```

### Example 3: Trend Analysis Report

```bash
/model:report --trend --period 90 --forecast 30
```

**Expected Output:**

```
AI Model Usage Trend Analysis
==============================
Historical Period: Last 90 days (Aug 27 - Nov 25, 2025)
Forecast Period: Next 30 days (Nov 26 - Dec 25, 2025)

📈 Historical Trends
--------------------

Total Tasks (by month):
August (partial):     456 tasks |  $68.40
September:            892 tasks | $133.80
October:            1,108 tasks | $166.20
November (to date): 1,247 tasks | $187.43

Growth Rate: +173% over 90 days (+29% month-over-month avg)

Cost Trends (by month):
[ASCII line graph showing cost growth]

Model Mix Evolution:
Month     | Haiku | Sonnet | Opus
----------|-------|--------|-------
August    | 12%   | 82%    | 6%
September | 15%   | 78%    | 7%
October   | 17%   | 73%    | 10%
November  | 19%   | 71%    | 10%

Trend: Increasing Haiku usage (+58% relative growth) ✓ Good
       Decreasing Sonnet reliance (-13% relative) ✓ Good
       Increasing Opus for critical tasks (+67% relative) ✓ Good

📊 Forecast (Next 30 Days)
--------------------------

Projected Tasks: 1,535 (+23% month-over-month)
Projected Cost: $230.25 (+23%)

Model Mix Forecast (if current trends continue):
- Haiku:  290 tasks (18.9%) →  $2.90 (1.3%)
- Sonnet: 1,091 tasks (71.1%) → $163.65 (71.1%)
- Opus:   154 tasks (10.0%) →  $63.70 (27.7%)

⚠️ Budget Impact
-----------------
Current Budget: $200.00/month
Forecasted: $230.25/month
Overage: $30.25 (15.2% over budget)

Status: WILL EXCEED BUDGET on ~Dec 12, 2025

Recommendations:
1. IMMEDIATE: Run /model:optimize (saves $77.60/month)
2. BUDGET: Increase monthly budget to $250 (accommodate growth)
3. CONTROL: Implement task prioritization when near budget limit

📉 Efficiency Trends
--------------------

Cost per Task:
August:    $0.150
September: $0.150
October:   $0.150
November:  $0.150 (stable) ✓

With Optimization (projected):
December:  $0.088 (-41% if optimization applied) ✓✓

Success Rate Trends:
August:    94.2%
September: 95.8%
October:   96.1%
November:  96.8% (improving) ✓

Response Time Trends:
August:    2.4s average
September: 2.3s average
October:   2.2s average
November:  2.1s average (improving with more Haiku) ✓

🎯 Seasonality & Patterns
--------------------------

Day of Week Analysis (Last 90 Days):
Monday:    highest activity (23.4% of weekly tasks)
Tuesday:   high activity (19.8%)
Wednesday: high activity (18.2%)
Thursday:  moderate activity (16.5%)
Friday:    moderate activity (14.3%)
Weekend:   low activity (7.8%)

Time of Day Analysis:
Peak Hours: 9am-11am, 2pm-4pm (68% of tasks)
Off-Peak: 5pm-9am (32% of tasks)

Insight: Consider off-peak batch processing for non-urgent tasks

🔮 Confidence Intervals
------------------------

30-Day Forecast Confidence:
- Tasks: 1,535 ± 120 (90% confidence)
- Cost: $230.25 ± $18.50 (90% confidence)

Forecast Accuracy (historical):
Last month's forecast vs actual: 96.4% accurate
Model: Improving (data quality increasing)
```

### Example 4: Comparison Report (Before/After Optimization)

```bash
/model:report --compare --before 2025-10-01 --after 2025-11-01
```

**Expected Output:**

```
Model Usage Comparison Report
==============================

Period 1 (Before): Oct 1-31, 2025 (Before Optimization)
Period 2 (After):  Nov 1-30, 2025 (After Optimization)

📊 Overall Comparison
---------------------
                 Before    After     Change    % Change
Tasks            1,108     1,247     +139      +12.5%
Cost ($)         166.20    187.43    +21.23    +12.8%
Cost/Task ($)    0.1500    0.1503    +0.0003   +0.2%
Success Rate     96.1%     96.8%     +0.7%     +0.7%
Avg Response     2.2s      2.1s      -0.1s     -4.5%

💰 Cost Changes by Model
-------------------------
             Before        After         Change
Haiku        $1.88 (1.1%)  $2.34 (1.2%)  +$0.46 (+24.5%)
Sonnet       $128.19 (77%) $133.65 (71%) +$5.46 (+4.3%)
Opus         $36.13 (22%)  $51.44 (27%)  +$15.31 (+42.4%)

📈 Model Mix Shift
------------------
             Before    After     Change
Haiku Tasks  188 (17%) 234 (19%) +46 (+24.5%) ✓ Good (more efficient)
Sonnet Tasks 809 (73%) 891 (71%) +82 (+10.1%) ✓ Good (less reliance)
Opus Tasks   111 (10%) 122 (10%) +11 (+9.9%)  ✓ Good (kept proportion)

Interpretation:
✓ Successfully increased Haiku usage for simple tasks
✓ Maintained quality with similar Opus proportion
✓ Overall more efficient model distribution

⚡ Performance Comparison
--------------------------

Success Rates:
             Before    After     Change
Haiku        98.4%     98.7%     +0.3%  ✓
Sonnet       96.8%     97.1%     +0.3%  ✓
Opus         89.2%     91.0%     +1.8%  ✓✓ Significant improvement

Response Times:
             Before    After     Change
Haiku        0.8s      0.7s      -0.1s  ✓
Sonnet       2.3s      2.1s      -0.2s  ✓
Opus         7.1s      6.4s      -0.7s  ✓

Failed Tasks:
Before: 43 failures (3.9%) - Wasted $9.67
After:  40 failures (3.2%) - Wasted $8.94
Change: -3 failures (-7.0%) - Saved $0.73 ✓

🎯 Optimization Impact
----------------------

Changes Made on Nov 1, 2025:
1. Updated documentation-agent: Sonnet → Haiku
2. Added security task routing: Auto-upgrade to Opus
3. Optimized /dev:full-cycle workflow: Mixed models

Results (November vs October):
✓ Documentation costs: $34.05 vs $51.20 (-33.5%)
✓ Security success rate: 91.0% vs 89.2% (+1.8%)
✓ Workflow efficiency: 15% faster on simple steps
⚠️ Total costs: +12.8% (but task volume +12.5%)

ROI Analysis:
Investment: 2 hours optimization work
Monthly Savings (if flat task volume): ~$25/month
Payback Period: <1 month
Annualized ROI: 150x

💡 Key Insights
---------------

1. Cost Growth Matched Task Growth
   - October: 1,108 tasks = $166.20 → $0.150/task
   - November: 1,247 tasks = $187.43 → $0.150/task
   - Efficiency maintained despite growth ✓

2. Quality Improved
   - Success rate: 96.1% → 96.8%
   - Particularly in Opus tasks (security focus)
   - Faster response times across all models

3. Better Model Matching
   - 24.5% more Haiku usage (simple tasks)
   - Security tasks now consistently use Opus
   - Documentation workload shifted to Haiku

📋 Recommendations
------------------

✓ Optimization working well - maintain current configuration
✓ Continue monitoring security task success rates
○ Consider further Haiku expansion for routine tasks
○ Review high Opus usage - may indicate complex period
```

## Business Value / ROI

### Financial Visibility

- **Track every dollar**: Know exactly where AI costs are going
- **Budget management**: Alerts when approaching limits
- **Cost allocation**: Attribute costs to teams, projects, agents

### Strategic Insights

- **Usage patterns**: Understand which tasks are most common
- **Efficiency trends**: Track improvement over time
- **Forecasting**: Predict future costs and needs

### Optimization Foundation

- **Data-driven decisions**: Reports guide optimization strategy
- **Before/after validation**: Measure optimization impact
- **Continuous improvement**: Track long-term trends

### Real-World Value

**Scenario 1: Budget Management**

- Monthly budget: $200
- Report shows: On track to hit $230 by month-end
- Action: Run optimization to cut $77/month
- Result: Stay under budget while growing task volume

**Scenario 2: Department Chargeback**

- Engineering: 60% of tasks → $112/month
- Marketing: 25% of tasks → $47/month
- Support: 15% of tasks → $28/month
- Result: Fair cost allocation across departments

**Scenario 3: ROI Justification**

- Before optimization: $200/month
- After optimization: $110/month
- Savings: $90/month = $1,080/year
- Result: Easy ROI case for AI tooling investment

## Success Metrics

### Reporting Metrics

- **Report Generation Time**: How fast reports are created
  - **Target: <30 seconds** for summary, <2 minutes for detailed
- **Data Accuracy**: Correctness of usage/cost data
  - **Target: 100%** (automated tracking)

### Business Metrics

- **Budget Adherence**: % of months staying within budget
  - **Target: 95%+** (with proper alerts and forecasting)
- **Cost Predictability**: Forecast accuracy
  - **Target: 90%+** accuracy on 30-day forecasts
- **Optimization ROI**: Savings from optimization actions
  - **Target: 10x+** (optimize once, save for months)

### Adoption Metrics

- **Report Usage**: How often reports are generated
  - **Target: Weekly** for summary, monthly for detailed
- **Action Rate**: % of report recommendations acted upon
  - **Target: 60%+** (reports should drive action)

## Advanced Options

### Flags

- `--period <days>`: Report timeframe (default: 30)
- `--detailed`: Include comprehensive metrics and breakdowns
- `--trend`: Show historical trends and forecasting
- `--compare`: Compare two time periods
- `--before <date>`: Start date for comparison
- `--after <date>`: End date for comparison
- `--export <format>`: Export format (json, csv, pdf, markdown)
- `--output <path>`: Output file path
- `--agent <name>`: Report for specific agent only
- `--command <name>`: Report for specific command only
- `--workflow <name>`: Report for specific workflow only
- `--dashboard`: Launch interactive web dashboard
- `--budget <amount>`: Compare against specific budget
- `--forecast <days>`: Forecast future usage (default: 30)

### Output Formats

**JSON** (for programmatic access):

```bash
/model:report --export json --output report.json
```

**CSV** (for spreadsheets):

```bash
/model:report --export csv --output report.csv
```

**PDF** (for executive summaries):

```bash
/model:report --detailed --export pdf --output report.pdf
```

**Markdown** (for documentation):

```bash
/model:report --export markdown --output report.md
```

**Dashboard** (interactive web UI):

```bash
/model:report --dashboard --port 3000
```

## Integration with Other Commands

```bash
# Monthly reporting workflow
/model:report --detailed --export pdf --output monthly-$(date +%Y-%m).pdf

# Before optimization
/model:report --baseline

# Run optimization
/model:optimize --auto-apply

# After optimization
/model:report --compare --before baseline --after now

# Continuous monitoring
/model:report --dashboard  # Leave running for real-time metrics
```

## Scheduling and Automation

### Automated Reports

Configure automatic report generation:

```bash
# Daily summary email
/model:report --schedule daily --email team@company.com

# Weekly detailed report
/model:report --detailed --schedule weekly --export pdf

# Monthly executive summary
/model:report --trend --forecast 30 --schedule monthly --export pdf
```

### Budget Alerts

```bash
# Alert at 80% of budget
/model:report --budget-alert 0.80 --notify slack:#ai-costs

# Daily budget check
/model:report --budget-check --schedule daily
```
