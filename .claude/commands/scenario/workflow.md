---
description: "Run a pre-built decision workflow to analyze and compare scenarios"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[workflow-id] [--inputs '{...}'] [--auto-run]"
---

# /scenario:workflow - Run Strategic Workflow

Run a pre-built decision workflow to automatically create scenarios, collect inputs, analyze options, and get recommendations. Workflows handle complete decision analysis in minutes instead of hours.

## Quick Start

**List all available workflows:**

```bash
/scenario:workflow --list
```

**Run a specific workflow:**

```bash
/scenario:workflow hire-vs-outsource
```

**Run workflow with pre-filled inputs:**

```bash
/scenario:workflow hire-vs-outsource --inputs '{"role":"Senior Developer","hours_needed":40,"duration_months":12}'
```

**Run workflow and auto-analyze:**

```bash
/scenario:workflow buy-property --auto-run
```

---

## Available Workflows (10 Total)

### Phase 1 Workflows (3 - Complete)

**1. hire-vs-outsource** - Developer staffing decision

- **Question**: Should I hire a full-time developer or outsource to an agency?
- **Inputs**: Role, hours/week, duration, salary, agency rate
- **Scenarios**: Hire Full-Time vs Outsource to Agency
- **Commands Used**: `/software-business:team`, `/software-business:revenue`, `/life:time`, `/life:goals`
- **Best For**: Evaluating team expansion vs flexibility trade-offs

**2. buy-property** - Real estate investment decision

- **Question**: Should I buy property X or wait for better deal?
- **Inputs**: Property name, price, down payment, monthly rent, monthly expenses
- **Scenarios**: Buy Now vs Wait for Better Deal
- **Commands Used**: `/real-estate:deals`, `/real-estate:portfolio`, `/life:goals`, `/life:time`
- **Best For**: Property acquisition evaluation with market analysis

**3. take-project** - Service project decision

- **Question**: Should I take on project Y or focus on product development?
- **Inputs**: Project name, revenue, hours/week, duration, strategic value
- **Scenarios**: Take the Service Project vs Focus on Product Development
- **Commands Used**: `/software-business:projects`, `/software-business:revenue`, `/life:time`, `/life:goals`
- **Best For**: Opportunity evaluation with long-term strategy consideration

### Phase 2+ Workflows (7 - Planned)

**4. raise-prices** - Pricing strategy (planned)
**5. build-vs-buy** - Product development approach (planned)
**6. add-commitment** - Time capacity analysis (planned)
**7. invest-capital** - Capital allocation (planned)
**8. delegate-task** - Delegation decision (planned)
**9. scale-business** - Growth strategy (planned)
**10. life-balance** - Work-life balance optimization (planned)

---

## How Workflows Work

### Step 1: Select Workflow

Choose from available workflows or specify a workflow ID.

### Step 2: Answer Input Questions

The workflow will ask for specific inputs relevant to your decision:

- **Hire-vs-Outsource**: Role, hours needed, duration, salary, agency rate
- **Buy-Property**: Property details, pricing, expected income
- **Take-Project**: Project details, revenue, time, strategic value

### Step 3: Automatic Scenario Creation

The workflow automatically:

- Creates 2-3 scenarios based on the template
- Populates parameters with your inputs
- Registers both scenarios in the system

### Step 4: Run Analysis

Each scenario is analyzed using integrated slash commands:

- Calculates alignment scores
- Detects conflicts
- Generates recommendations
- Produces metrics (pros/cons/risks/opportunities)

### Step 5: Get Comparison & Recommendation

Results include:

- Side-by-side scenario comparison
- Overall recommendation with confidence score
- Decision logic explaining the recommendation
- Next steps guidance

---

## Workflow: Hire vs Outsource Developer

**Real-world Example**

```
/scenario:workflow hire-vs-outsource

========================================
WORKFLOW: Should I hire a developer?
========================================

ANSWERING INPUT QUESTIONS:

Q1: What role do you need?
    → Senior Full Stack Developer

Q2: How many hours per week?
    → 40

Q3: For how many months?
    → 12

Q4: What salary range? (default: $80,000)
    → [accepting default]

Q5: Agency hourly rate? (default: $100)
    → [accepting default]

========================================
CREATING SCENARIOS...
========================================

✅ Scenario 1: Hire Full-Time Developer
   - Created with ID: sc-1733596400000-abc123
   - Parameters saved: hire_fulltime, salary, benefits_cost, etc.

✅ Scenario 2: Outsource to Agency
   - Created with ID: sc-1733596400000-def456
   - Parameters saved: outsource, hourly_rate, hours_per_week, etc.

========================================
ANALYZING SCENARIOS...
========================================

Scenario 1: Hire Full-Time Developer
├─ Running: /software-business:team analyze
├─ Running: /software-business:revenue forecast
├─ Running: /life:time audit
├─ Running: /life:goals alignment_check
└─ ✅ Analysis Complete

Scenario 2: Outsource to Agency
├─ Running: /software-business:projects analyze
├─ Running: /software-business:revenue forecast
├─ Running: /life:time audit
├─ Running: /life:goals alignment_check
└─ ✅ Analysis Complete

========================================
COMPARISON RESULTS
========================================

OPTION 1: Hire Full-Time Developer
├─ Overall Score: 82/100 ⭐⭐⭐
├─ Financial Impact: -$100K/year cost, +$160K revenue potential
├─ Time Impact: +5 hours/week management, frees up 40 billable hours
├─ Goal Alignment: 9/10 (Strong)
│
├─ PROS:
│  ✅ Long-term team asset
│  ✅ Dedicated capacity
│  ✅ Builds company value
│  ✅ Team morale boost
│
├─ CONS:
│  ❌ High fixed cost ($100K/year)
│  ❌ Hiring/onboarding effort
│  ❌ Less flexibility
│
├─ RISKS:
│  ⚠️ Hiring wrong person
│  ⚠️ Not enough work
│  ⚠️ Salary expectations increase
│
└─ OPPORTUNITIES:
   💡 Build leadership skills
   💡 Create scalable business

─────────────────────────────────────

OPTION 2: Outsource to Agency
├─ Overall Score: 71/100 ⭐⭐
├─ Financial Impact: -$52K/year cost (20 hrs/week @ $100/hr)
├─ Time Impact: +3 hours/week management, +20 billable hours
├─ Goal Alignment: 7/10 (Moderate)
│
├─ PROS:
│  ✅ Lower cost
│  ✅ Flexible capacity
│  ✅ No hiring overhead
│  ✅ Quick to start
│
├─ CONS:
│  ❌ Lower quality
│  ❌ Less committed
│  ❌ Communication overhead
│
├─ RISKS:
│  ⚠️ Quality issues
│  ⚠️ Turnover on agency side
│  ⚠️ Timezone challenges
│
└─ OPPORTUNITIES:
   💡 Test before committing
   💡 Scale flexibility
   💡 On-demand expertise

========================================
RECOMMENDATION
========================================

🏆 BEST SCENARIO: Hire Full-Time Developer
├─ Score Gap: 11 points (82 vs 71)
├─ Confidence: 78% (High confidence)
│
└─ DECISION LOGIC:
   Choose Option 1 (Hire) IF:
   • You want to scale business significantly
   • You have consistent work (40+ billable hours)
   • You can afford $100K/year fixed cost
   • You value team/culture
   • You plan to be in business for 5+ years

   Choose Option 2 (Outsource) IF:
   • You want to test before committing
   • Work is variable/unpredictable
   • You prefer flexibility
   • You want to minimize overhead
   • You're uncertain about market demand

========================================
NEXT STEPS
========================================

1. DECIDE: Make decision using /scenario:decide
   /scenario:decide sc-1733596400000-abc123 --chosen

2. REFINE: Adjust parameters if needed
   /scenario:compare sc-1733596400000-abc123 sc-1733596400000-def456 --detail

3. DELEGATE: Assign analysis to team member
   /scenario:delegate sc-1733596400000-abc123 --to john@company.com

4. ARCHIVE: Save for future reference
   /scenario:archive sc-1733596400000-abc123 sc-1733596400000-def456
```

---

## Comparison of Workflow Types

### Hire vs Outsource (Business Decision)

- **Domain**: Team & Capacity
- **Decision**: Employment commitment vs flexibility
- **Timeline**: Affects next 12-24 months
- **Reversibility**: Medium (can be reversed but costly)
- **Key Trade-off**: Cost vs control

### Buy Property (Real Estate Decision)

- **Domain**: Wealth Building
- **Decision**: Capital deployment vs market patience
- **Timeline**: Affects 10+ years
- **Reversibility**: Low (real estate is illiquid)
- **Key Trade-off**: Opportunity vs timing

### Take Project (Strategic Decision)

- **Domain**: Business Strategy
- **Decision**: Short-term revenue vs long-term product
- **Timeline**: Affects next 3-12 months
- **Reversibility**: High (projects are finite)
- **Key Trade-off**: Revenue vs growth investment

---

## Workflow Execution Flow

```
START: User invokes /scenario:workflow hire-vs-outsource
  ↓
LOAD: Workflow template from YAML
  ↓
INPUT: Collect user responses
  - Role: "Senior Developer"
  - Hours: 40
  - Months: 12
  - Salary: $80,000
  - Agency Rate: $100/hr
  ↓
CREATE: Two scenarios
  - Scenario 1: "Hire Full-Time Developer"
  - Scenario 2: "Outsource to Agency"
  ↓
SUBSTITUTE: Replace template variables with inputs
  - salary: 80000
  - benefits_cost: 20000 (80000 * 0.25)
  - monthly_cost: 6667 (80000/12)
  - agency_cost: 172,800 (100 * 40 * 4.33 * 12)
  ↓
SAVE: Store scenarios in database
  ↓
ANALYZE: Run each scenario
  - Calculate alignment score
  - Detect conflicts
  - Generate metrics
  ↓
COMPARE: Side-by-side comparison
  - Overall scores
  - Financial impact
  - Time impact
  - Goal alignment
  ↓
RECOMMEND: Generate recommendation
  - Best scenario
  - Confidence score
  - Decision logic
  ↓
OUTPUT: Display results
  ↓
NEXT: User decides, delegates, or refines
END
```

---

## Advanced Usage

### Pre-filled Inputs

Run workflow with all inputs at once (no prompts):

```bash
/scenario:workflow hire-vs-outsource --inputs '{
  "role": "Senior Backend Developer",
  "hours_needed": 40,
  "duration_months": 12,
  "desired_salary": 120000,
  "agency_hourly_rate": 150
}'
```

### Auto-Run (Skip Prompts)

If all inputs are provided via `--inputs`, automatically run without prompting:

```bash
/scenario:workflow hire-vs-outsource --inputs '{...}' --auto-run
```

### Export Results

After workflow completes, export to file:

```bash
/scenario:workflow hire-vs-outsource > workflow-results.txt
```

### Compare with Different Inputs

Run workflow multiple times with different assumptions:

```bash
/scenario:workflow hire-vs-outsource --inputs '{"desired_salary": 80000}' > scenario-a.txt
/scenario:workflow hire-vs-outsource --inputs '{"desired_salary": 120000}' > scenario-b.txt
/scenario:compare [scenario-a-ids] [scenario-b-ids]
```

---

## Workflow Template Structure (For Reference)

Each workflow template is a YAML file with:

```yaml
workflow_id: "hire-vs-outsource"
name: "Should I hire or outsource?"
description: "Compare hiring a developer vs outsourcing to agency"
category: "business_decision"

inputs:
  - name: "role"
    type: "string"
    prompt: "What role do you need?"
    required: true

  - name: "hours_needed"
    type: "number"
    prompt: "How many hours per week?"
    required: true

scenario_1:
  name: "Hire Full-Time Developer"
  description: "..."
  parameters:
    hire_fulltime: true
    salary: "${inputs.desired_salary}"
    benefits_cost: "${inputs.desired_salary * 0.25}"
  commands:
    - command: "/software-business:team"
    - command: "/software-business:revenue"
    # ...

scenario_2:
  name: "Outsource to Agency"
  # Similar structure...

comparison_criteria:
  - metric: "financial_impact"
    weight: 30
  - metric: "time_impact"
    weight: 20
  # ...

recommendation_logic: |
  Choose "Hire" IF:
  - Consistent work available
  - Can afford fixed cost
  # ...
```

---

## Success Criteria

**After running a workflow:**

- ✅ Two scenarios created with proper parameters
- ✅ Both scenarios analyzed with metrics
- ✅ Side-by-side comparison generated
- ✅ Recommendation provided with reasoning
- ✅ Confidence score calculated (0-100%)
- ✅ Decision logic explained
- ✅ Next steps recommended
- ✅ Results saved to database for comparison/delegation

---

## Common Workflows & When to Use

| Workflow | Use When | Time | Decision |
|----------|----------|------|----------|
| **hire-vs-outsource** | Need to expand capacity | 15 min | Employment |
| **buy-property** | Considering acquisition | 20 min | Investment |
| **take-project** | Opportunity presents itself | 10 min | Strategic |
| **raise-prices** | Evaluating pricing power | 10 min | Revenue |
| **build-vs-buy** | Deciding product strategy | 15 min | Strategic |
| **add-commitment** | Managing time capacity | 5 min | Planning |
| **invest-capital** | Deploying savings | 15 min | Financial |
| **delegate-task** | Considering delegation | 10 min | Efficiency |
| **scale-business** | Planning growth | 20 min | Strategic |
| **life-balance** | Evaluating priorities | 10 min | Personal |

---

**Run pre-built workflows to make strategic decisions fast**
**Answer 5 questions, get recommendation in minutes**
**Use data to choose between alternatives with confidence**
