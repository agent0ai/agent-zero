---
description: "Create a new strategic scenario for analysis and comparison"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[scenario-name] [--description \"description\"] [--parameters '{...}']"
---

# /scenario:create - Create Strategic Scenario

Create a new scenario for analyzing "what-if" situations. Scenarios let you evaluate different strategic paths, compare outcomes, and make data-driven decisions across life, business, and real estate goals.

## Quick Start

**Create scenario interactively:**

```bash
/scenario:create
```

**Create scenario with name only:**

```bash
/scenario:create "Hire vs Outsource Developer"
```

**Create scenario with all details:**

```bash
/scenario:create "Hire vs Outsource" --description "Should we hire a full-time developer or outsource to an agency?" --parameters '{"hire_fulltime": true, "salary": 80000, "hours_needed": 20}'
```

---

## Scenario Types

### 1. Business Decisions

- Should I hire a developer or outsource?
- Should I raise prices or stay competitive?
- Should I expand to new market or focus on current?
- Should I build product or sell services?

### 2. Real Estate Decisions

- Should I buy property X or wait for better deal?
- Should I invest in single-family or multi-unit?
- Should I do cash-out refi or save cash?
- Should I manage properties or hire PM?

### 3. Time & Capacity Decisions

- Can I take on project Y with current workload?
- Should I add another responsibility or delegate?
- How do I balance multiple active initiatives?
- Can I afford to reduce hours without income impact?

### 4. Investment Decisions

- Should I invest in education/certification?
- Should I invest in business tools/software?
- Should I invest in personal health/fitness?
- Should I build savings or invest?

### 5. Life Balance Decisions

- Should I prioritize career growth or health?
- Should I focus on making money or enjoying life?
- Should I relocate for opportunity or stay?
- Should I take risky opportunity or play it safe?

---

## How It Works

**Step 1: Define Scenario**

- Give it a clear name (e.g., "Hire vs Outsource")
- Describe the situation/question (e.g., "Should we hire full-time or outsource?")
- Specify what's changing (scenario parameters)

**Step 2: Set Parameters**

- What aspects will differ between options?
- Examples:
  - Financial: costs, revenue impact, ROI
  - Time: hours/week, duration, impact on capacity
  - Goals: alignment with life/business/real estate goals
  - Other: risk level, strategic value, alignment with values

**Step 3: Analyze**

- Run the scenario through alignment scoring
- Calculate financial/time/goal impact
- Detect conflicts with other goals
- Generate recommendations

**Step 4: Compare**

- Create multiple scenarios for different options
- Compare side-by-side
- See pros/cons, risks/opportunities
- Get recommendation on best path

**Step 5: Decide**

- Make final decision with confidence score
- Record rationale
- Update goals/plans based on decision
- Archive scenario for learning

---

## Example Scenarios

### Scenario 1: "Hire Full-Time Developer"

```
Name: Hire Full-Time Developer
Description: Hire a full-time developer to expand our capacity

Parameters:
- Hire: true (vs false for outsource)
- Salary: $80,000/year
- Benefits: $20,000/year
- Onboarding: 4 weeks
- Management time: 5 hours/week
- Expected output: +40 billable hours/week
- Morale impact: +10 (team building)
```

### Scenario 2: "Outsource to Agency"

```
Name: Outsource to Agency
Description: Contract with external agency instead of hiring

Parameters:
- Outsource: true
- Hourly rate: $100/hour
- Hours/week: 20
- Management time: 3 hours/week
- Expected output: +20 billable hours/week (lower quality)
- Morale impact: 0 (no team addition)
```

### Scenario 3: "Buy Property X"

```
Name: Acquire 456 Elm Avenue
Description: Purchase duplex investment property

Parameters:
- Purchase price: $310,000
- Down payment: $62,000
- Loan amount: $248,000
- Interest rate: 4.5%
- Expected monthly rent: $2,800
- Monthly expenses: $2,035
- Cash-on-cash return: 14.8%
- Alignment with FI goal: High
```

---

## Data Structure

When you create a scenario, it stores:

```json
{
  "id": "sc-1733514245000-abc123def456",
  "name": "Hire vs Outsource Developer",
  "description": "Compare hiring FTE vs outsourcing to agency",
  "status": "draft",
  "created_by": "aaron",
  "created_at": "2025-12-06T15:30:45Z",

  "parameters": {
    "hire_fulltime": true,
    "salary": 80000,
    "benefits": 20000,
    "management_hours": 5,
    "expected_output_hours": 40,
    "morale_impact": 10
  },

  "analysis_commands": [
    { "command": "/software-business:team", "args": { "action": "analyze_capacity" } },
    { "command": "/software-business:revenue", "args": { "action": "forecast" } },
    { "command": "/life:time", "args": { "action": "audit" } },
    { "command": "/life:goals", "args": { "action": "alignment_check" } }
  ]
}
```

---

## Next Steps

After creating a scenario:

1. **View scenario details:**

   ```bash
   /scenario:details <scenario-id>
   ```

2. **Run analysis:**

   ```bash
   /scenario:analyze <scenario-id>
   ```

3. **Compare scenarios:**

   ```bash
   /scenario:compare <scenario-id-1> <scenario-id-2>
   ```

4. **Make final decision:**

   ```bash
   /scenario:decide <scenario-id> --chosen
   ```

5. **List all scenarios:**

   ```bash
   /scenario:list
   ```

---

## Success Criteria

**After creating a scenario:**

- ✅ Scenario has clear name and description
- ✅ Parameters capture what's different
- ✅ Scenario saved with unique ID
- ✅ Ready for analysis

**After analyzing scenarios:**

- ✅ Financial impact calculated
- ✅ Time impact calculated
- ✅ Alignment score generated (0-100)
- ✅ Conflicts detected
- ✅ Recommendations provided

**After comparing scenarios:**

- ✅ Side-by-side comparison visible
- ✅ Pros/cons clear for each
- ✅ Overall recommendation given
- ✅ Confidence level provided

---

**Create strategic scenarios to make better decisions**
**Compare alternatives to find the optimal path**
**Use data to guide your life, business, and real estate decisions**
