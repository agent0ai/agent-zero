---
description: "Assign scenario analysis to a team member"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[scenario-id] [--to team-member-email] [--due YYYY-MM-DD] [--notes 'optional notes']"
---

# /scenario:delegate - Delegate Scenario Analysis

Assign a scenario analysis task to a team member with clear expectations and deadlines. The team member receives a notification and can track progress through their delegation dashboard.

## Quick Start

**Delegate scenario to team member:**

```bash
/scenario:delegate sc-1733596400000-abc123 --to john@company.com
```

**Add deadline and notes:**

```bash
/scenario:delegate sc-1733596400000-abc123 --to john@company.com --due 2025-12-20 --notes "Focus on financial impact analysis"
```

**List all delegations assigned by you:**

```bash
/scenario:delegate --list-mine
```

**List delegations assigned to you:**

```bash
/scenario:delegate --list-for-me
```

**Check status of a delegation:**

```bash
/scenario:delegate sc-1733596400000-abc123 --status
```

---

## How Delegation Works

### Step 1: Select Scenario and Assignee

Choose which scenario needs analysis and who should analyze it.

### Step 2: Set Expectations

Define:

- **Deadline** (optional): When analysis should be complete
- **Notes** (optional): Specific guidance or focus areas
- **Deliverable**: Recommendation with supporting evidence

### Step 3: Notify Assignee

Team member receives email notification with:

- Scenario summary
- Analysis requirements
- Deadline (if set)
- Link to scenario details

### Step 4: Assignee Works

Team member:

- Views scenario details and parameters
- Runs analysis using slash commands
- Collects evidence and metrics
- Documents findings

### Step 5: Submit & Review

Team member submits deliverable:

- Recommendation (which scenario)
- Confidence score (0-100%)
- Supporting evidence
- Key findings

### Step 6: Manager Approves

Manager reviews and:

- **Approves** - Accept recommendation and make decision
- **Requests Changes** - Ask for more analysis
- **Rejects** - Suggest different approach

### Step 7: Decision

Manager makes final decision using `/scenario:decide` with delegation input

---

## Delegation Status Workflow

```
ASSIGNED → IN_PROGRESS → REVIEW → APPROVED
                         ↓
                      REJECTED (restart analysis)
```

### Status Definitions

| Status | Meaning | Who Can Change |
|--------|---------|-----------------|
| **assigned** | Waiting for assignee to start | Assignee (→ in_progress) |
| **in_progress** | Analysis underway | Assignee (→ review) |
| **review** | Submitted for approval | Manager (→ approved/rejected) |
| **approved** | Manager accepted analysis | End state |
| **rejected** | Manager wants more work | Assignee (→ in_progress) |

---

## Example: Hire vs Outsource Delegation

```
/scenario:delegate sc-1733596400000-abc123 --to john@company.com --due 2025-12-20 --notes "Analyze both cost and team impact"

========================================
DELEGATION CREATED
========================================

✅ Scenario: Hire Full-Time Developer
📧 Assigned to: John Smith (john@company.com)
🎯 Assigned by: Aaron (aaron@company.com)
📅 Due: Friday, December 20, 2025
📝 Notes: Analyze both cost and team impact

Delegation ID: del-1733596400000-abc123
Status: assigned
Created: 2025-12-06 10:30 AM

========================================
TASKS TO COMPLETE
========================================

1. Analyze financial impact
   - Total cost vs revenue potential
   - Payback period and ROI
   - Cash flow implications

2. Analyze time impact
   - Management hours required
   - Impact on other projects
   - Team capacity analysis

3. Evaluate goal alignment
   - Alignment with scaling goals
   - Impact on company culture
   - Strategic fit

4. Provide recommendation
   - Which scenario is better
   - Confidence level (0-100%)
   - Key reasoning

========================================
NOTIFICATION SENT
========================================

📧 Email sent to john@company.com
   Subject: "Scenario Analysis Delegation: Hire vs Outsource"

   Key details provided:
   - Scenario overview
   - Analysis requirements
   - Deadline: December 20, 2025
   - Guidance notes
   - Link to dashboard

========================================
NEXT STEPS
========================================

For John (Assignee):
1. Check email notification
2. Log into dashboard
3. View scenario details
4. Run analysis using suggested commands
5. Submit recommendation with evidence
6. Address any feedback from Aaron

For Aaron (Manager):
1. Check delegation status: /scenario:delegate del-1733596400000-abc123 --status
2. Follow up if near deadline: /scenario:delegate --overdue
3. Review when submitted: /scenario:delegate del-1733596400000-abc123 --review
4. Approve or request changes
5. Make final decision: /scenario:decide sc-1733596400000-abc123

View your delegations:
- /scenario:delegate --list-mine     (delegations you created)
- /scenario:delegate --list-for-me   (delegations assigned to you)
```

---

## Delegation Template

Each delegation includes:

### Context

- Scenario summary (name, description, parameters)
- What's being analyzed (2-3 scenarios to compare)
- Why it matters (business impact)

### Analysis Requirements

- Financial analysis (costs, revenue, ROI)
- Time analysis (hours needed, impact on capacity)
- Goal alignment (strategic fit)
- Recommendation (which option is better)

### Deliverable Format

```
RECOMMENDATION SUMMARY
======================

Scenario Chosen: [Name]
Confidence Level: [0-100]%
Key Finding: [1-2 sentences]

SUPPORTING EVIDENCE
===================

Financial Impact:
- Cost: $XXX
- Revenue: $XXX
- ROI: XX months
- Payback: XXX

Time Impact:
- Hours/week: XX
- Total investment: XX hours
- Impact on capacity: XX%

Goal Alignment:
- Life goals: [description]
- Business goals: [description]
- Values alignment: [description]

KEY STRENGTHS OF CHOSEN SCENARIO
===============================
- Strength 1
- Strength 2
- Strength 3

RISKS & MITIGATION
==================
- Risk 1: [Mitigation strategy]
- Risk 2: [Mitigation strategy]

ALTERNATIVES CONSIDERED
========================
- Why other scenario was rejected
- What would need to change for consideration
```

---

## Common Workflows

### Quick Delegation to Senior Developer

```bash
/scenario:delegate sc-scenario-id --to senior@company.com --due 2025-12-13
```

→ Uses default notes, sets 1-week deadline

### Detailed Delegation with Guidance

```bash
/scenario:delegate sc-scenario-id --to junior@company.com --due 2025-12-20 --notes "Walk through each scenario step-by-step. Focus on financial impact. Example answers in the scenario dashboard."
```

→ Provides mentoring context for less experienced analyst

### Multi-Person Delegation

```bash
/scenario:delegate sc-scenario-id --to john@company.com
/scenario:delegate sc-scenario-id --to jane@company.com --notes "Compare your analyses when both are complete"
```

→ Have multiple people analyze independently, compare conclusions

### Emergency Delegation

```bash
/scenario:delegate sc-scenario-id --to lead@company.com --due 2025-12-07 --notes "URGENT: Decision needed by EOD Monday. Please fast-track analysis."
```

→ Clear urgency, same-day or next-day deadline

---

## Delegation Metrics

View delegation performance:

```bash
/scenario:delegate --metrics
```

Shows:

- Total delegations created
- Average completion time
- % approved vs rejected
- Overdue delegations
- Team member performance

---

## Advanced Features

### Add Message to Delegation

```bash
/scenario:delegate del-xyz --message "Reviewed your initial findings, looks good. Can you add sensitivity analysis for 5-10% cost variation?"
```

→ Two-way communication without email

### Check Delegation Progress

```bash
/scenario:delegate del-xyz --progress
```

Shows:

- Status: assigned/in_progress/review/approved/rejected
- % Tasks complete
- Days until deadline
- Recent messages
- Submission status

### Recall Delegation

```bash
/scenario:delegate del-xyz --recall --reason "Decision needed sooner than expected"
```

→ Cancel delegation, get back control

### Track Overdue Delegations

```bash
/scenario:delegate --overdue
```

Shows:

- All delegations past due date
- Days overdue
- Contact info
- Status

---

## Success Criteria

**After delegating a scenario:**

- ✅ Assignee receives notification
- ✅ Delegation created with unique ID
- ✅ Status tracked: assigned → in_progress → review → approved
- ✅ Two-way messaging enabled
- ✅ Deadline tracked (if set)
- ✅ Dashboard shows delegation status

**After assignee submits:**

- ✅ Recommendation documented
- ✅ Evidence attached
- ✅ Confidence score provided
- ✅ Status changes to "review"
- ✅ Manager notified

**After manager decides:**

- ✅ Delegation approved or rejected
- ✅ Decision recorded with rationale
- ✅ Team member gets feedback
- ✅ Scenario status updated
- ✅ Organizational learning captured

---

## Permissions

| Action | Role | Allowed |
|--------|------|---------|
| Create delegation | Manager/Owner | ✅ Yes |
| Accept delegation | Team Member | ✅ Yes |
| Add messages | Both | ✅ Yes |
| Submit analysis | Team Member | ✅ Yes |
| Review submission | Manager | ✅ Yes |
| Approve/Reject | Manager | ✅ Yes |
| View own | Team Member | ✅ Yes |
| View created | Manager | ✅ Yes |

---

**Delegate scenario analysis to leverage team expertise**
**Scale decision-making across your organization**
**Build analytical culture with shared ownership**
