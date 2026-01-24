---
description: "Compare multiple scenarios side-by-side to find the optimal path"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[scenario-id-1] [scenario-id-2] [--detail] [--export pdf|json|csv]"
---

# /scenario:compare - Compare Strategic Scenarios

Compare 2-5 scenarios side-by-side to see pros, cons, risks, opportunities, and overall recommendations. Helps you make data-driven decisions by visualizing different strategic paths.

## Quick Start

**Compare two scenarios:**

```bash
/scenario:compare sc-123 sc-456
```

**Compare three scenarios with details:**

```bash
/scenario:compare sc-123 sc-456 sc-789 --detail
```

**Export comparison to PDF:**

```bash
/scenario:compare sc-123 sc-456 --export pdf
```

---

## How Comparison Works

### 1. Gather Data

- Pulls all scenario data (parameters, results, metrics)
- Verifies all scenarios are complete (analyzed)
- Validates scenario count (minimum 2, maximum 5)

### 2. Compare Metrics

For each scenario, compares:

- **Overall Score** (0-100): Weighted alignment rating
- **Financial Impact**: Costs, revenue, profit, ROI
- **Time Impact**: Hours per week, total hours, timeline
- **Goal Alignment**: Impact on life/business/real estate goals
- **Conflicts**: Any detected conflicts with other goals

### 3. Calculate Pros/Cons

Identifies advantages and disadvantages for each:

- **Pros**: Positive impacts, opportunities
- **Cons**: Drawbacks, challenges
- **Risks**: Potential problems to watch
- **Opportunities**: Upside potential

### 4. Generate Recommendation

- Identifies best scenario based on overall score
- Calculates confidence level
- Provides reasoning
- Suggests decision logic

---

## Comparison Output

### Example: Hire vs Outsource Developer

```
SCENARIO COMPARISON (2 scenarios)
═════════════════════════════════════════════════════════════

OPTION 1: Hire Full-Time Developer
├── Overall Score: 82/100 ⭐⭐⭐
├── Financial Impact: -$100K/year cost, +$160K revenue potential
├── Time Impact: +5 hours/week management, frees up 40 billable hours
├── Alignment: Strong (9/10) - Supports scaling and revenue goals
│
├── PROS:
│   ✅ Long-term team asset (improves business culture)
│   ✅ Dedicated capacity (reliable output)
│   ✅ Builds company value (sellable asset)
│   ✅ Loyalty & continuity (better long-term)
│   ✅ Morale boost (+10 team building)
│
├── CONS:
│   ❌ $100K/year fixed cost (high commitment)
│   ❌ Hiring/onboarding effort (4 weeks)
│   ❌ Management overhead (5 hours/week)
│   ❌ Risk of poor fit or turnover
│   ❌ Less flexibility if business changes
│
├── RISKS:
│   ⚠️ Hiring wrong person (wasted time/money)
│   ⚠️ Not enough work to keep them busy
│   ⚠️ Salary expectations increase over time
│   ⚠️ Employment/benefits complexity
│
└── OPPORTUNITIES:
    💡 Build leadership/management skills
    💡 Create scalable business (not dependent on you)
    💡 Potential to hire more team members

─────────────────────────────────────────────────────────────

OPTION 2: Outsource to Agency
├── Overall Score: 71/100 ⭐⭐
├── Financial Impact: -$52K/year cost (20 hrs/week @ $100/hr)
├── Time Impact: +3 hours/week management, +20 billable hours
├── Alignment: Moderate (7/10) - Lower quality concern
│
├── PROS:
│   ✅ Lower cost ($52K vs $100K)
│   ✅ Flexible capacity (increase/decrease hours)
│   ✅ No hiring/management (turn-key)
│   ✅ External expertise (fresh perspective)
│   ✅ Quick to start (no onboarding)
│
├── CONS:
│   ❌ Lower quality (external team vs internal)
│   ❌ Less committed (not invested in your success)
│   ❌ Communication overhead (coordination needed)
│   ❌ Dependency on external company
│   ❌ No morale boost (external team)
│
├── RISKS:
│   ⚠️ Quality issues with deliverables
│   ⚠️ Turnover on agency side
│   ⚠️ Communication/timezone challenges
│   ⚠️ Less control over priorities
│
└── OPPORTUNITIES:
    💡 Test market demand without commitment
    💡 Maintain flexibility (scale down easily)
    💡 Access specialized skills on-demand

─────────────────────────────────────────────────────────────

RECOMMENDATION
═════════════════════════════════════════════════════════════

🏆 BEST SCENARIO: Option 1 - Hire Full-Time Developer
├── Score: 82/100 (11 points higher than outsource)
├── Reasoning: Higher alignment with scaling goals, team building,
│              and long-term business value
├── Confidence: 78% (high confidence in this choice)
│
└── DECISION LOGIC:
    • Choose Option 1 IF:
      - You want to scale business significantly
      - You have consistent work (40+ billable hours)
      - You can afford $100K/year fixed cost
      - You value team/culture
      - You plan to be in business for 5+ years

    • Choose Option 2 IF:
      - You want to test before committing
      - Work is variable/unpredictable
      - You prefer flexibility
      - You want to minimize overhead
      - You're uncertain about market demand

─────────────────────────────────────────────────────────────

SUMMARY MATRIX
═════════════════════════════════════════════════════════════

Metric                  | Hire (82) | Outsource (71) | Winner
───────────────────────────────────────────────────────────
Cost/Year               | -$100K    | -$52K          | Outsource
Revenue Potential       | +$160K    | +$80K          | Hire
Time Commitment         | 5 hrs/wk  | 3 hrs/wk       | Outsource
Team Impact             | +10       | 0              | Hire
Long-term Value        | High      | Low            | Hire
Flexibility            | Low       | High           | Outsource
Scaling Potential      | Excellent | Limited        | Hire
Risk Level             | Medium    | Low-Medium     | Outsource
Alignment w/ Goals     | 9/10      | 7/10           | Hire
───────────────────────────────────────────────────────────
OVERALL WINNER         |           |                | HIRE
═════════════════════════════════════════════════════════════
```

---

## Comparison Criteria

### Financial Comparison

- Initial cost (down payment, setup fees)
- Monthly/annual costs
- Revenue impact
- Profit impact
- ROI and payback period

### Time Comparison

- Hours per week required
- Total hours needed
- Timeline (weeks to complete)
- Impact on capacity

### Goal Alignment

- Life goal alignment (-100 to +100)
- Business goal alignment
- Real estate goal alignment
- Overall alignment score (0-100)

### Risk Assessment

- Market risk (external factors)
- Execution risk (can you pull it off?)
- Financial risk (ability to absorb losses)
- Operational risk (day-to-day challenges)

### Strategic Fit

- Supports long-term vision
- Leverages strengths
- Addresses gaps
- Competitive advantage

---

## Confidence Scoring

The recommendation includes a confidence level (0-100%):

**High Confidence (80%+)**

- Clear winner with significant score gap (>15 points)
- Data strongly supports recommendation
- Low uncertainty

**Medium Confidence (60-79%)**

- Winner clear but not dominant (10-15 point gap)
- Some trade-offs to consider
- Moderate uncertainty

**Low Confidence (<60%)**

- Close call between scenarios (<10 points)
- Trade-offs roughly equal
- High uncertainty - choose based on personal preference

---

## Next Steps After Comparison

**1. If Winner is Clear:**

- Make decision: `/scenario:decide <winning-id> --chosen`
- Update goals/plans based on decision
- Archive other scenarios for learning

**2. If Close Call:**

- Get more details: `/scenario:details <scenario-id> --deep-dive`
- Adjust parameters: `/scenario:update <id> --param cost 50000`
- Re-analyze: `/scenario:analyze <id>`

**3. If Multiple Trade-offs:**

- Create hybrid scenario combining best of both
- Run new analysis
- Compare original vs hybrid

**4. For Team Discussion:**

- Export comparison: `/scenario:compare --export pdf`
- Share with team for input
- Gather feedback before deciding

---

## Advanced Options

**Sort Comparison:**

```bash
/scenario:compare sc-1 sc-2 sc-3 --sort score
/scenario:compare sc-1 sc-2 sc-3 --sort cost
/scenario:compare sc-1 sc-2 sc-3 --sort time
```

**Focus on Specific Metric:**

```bash
/scenario:compare sc-1 sc-2 --focus financial
/scenario:compare sc-1 sc-2 --focus time
/scenario:compare sc-1 sc-2 --focus goals
```

**Detailed Analysis:**

```bash
/scenario:compare sc-1 sc-2 --detail      # Show all details
/scenario:compare sc-1 sc-2 --analysis    # Show analysis methodology
/scenario:compare sc-1 sc-2 --sensitivity # Show sensitivity to changes
```

**Export Options:**

```bash
/scenario:compare sc-1 sc-2 --export pdf      # PDF with charts
/scenario:compare sc-1 sc-2 --export json     # Raw JSON data
/scenario:compare sc-1 sc-2 --export csv      # Spreadsheet format
```

---

## Success Criteria

**After comparing scenarios:**

- ✅ All metrics visible side-by-side
- ✅ Pros/cons clear for each option
- ✅ Winner identified with reasoning
- ✅ Confidence score provided
- ✅ Clear decision logic explained
- ✅ Next steps recommended

---

**Compare scenarios to make better strategic decisions**
**Use data to evaluate trade-offs and find the optimal path**
**Increase decision confidence with side-by-side analysis**
