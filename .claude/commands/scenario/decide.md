---
description: "Make final decision on a scenario with rationale and implementation plan"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[scenario-id] --chosen [--rationale 'explanation'] [--confidence 0-100] [--next-steps 'actions'] [--notify team@company.com]"
---

# /scenario:decide - Make & Record Decision

Make a final decision on a scenario, document your rationale, set confidence level, and create implementation plan. Decisions are recorded for organizational learning and accountability.

## Quick Start

**Choose a scenario as the winner:**

```bash
/scenario:decide sc-1733596400000-abc123 --chosen
```

**Record detailed decision with rationale:**

```bash
/scenario:decide sc-1733596400000-abc123 --chosen --rationale "Best financial outcome with strong team alignment" --confidence 85
```

**Include implementation next steps:**

```bash
/scenario:decide sc-1733596400000-abc123 --chosen --next-steps "Week 1: Post job, Week 2: Interview, Week 3: Offer, Week 4: Onboard"
```

**Notify team about decision:**

```bash
/scenario:decide sc-1733596400000-abc123 --chosen --notify team@company.com
```

**View decision details:**

```bash
/scenario:decide sc-1733596400000-abc123 --status
```

**Archive completed decision:**

```bash
/scenario:decide sc-1733596400000-abc123 --archive
```

---

## Decision Workflow

```
SCENARIO CREATED
      ↓
ANALYSIS COMPLETE
      ↓
COMPARISON REVIEWED
      ↓
DECISION MADE (this command)
      ↓
RATIONALE DOCUMENTED
      ↓
TEAM NOTIFIED
      ↓
IMPLEMENTATION STARTED
      ↓
OUTCOME TRACKED (future)
      ↓
LEARNING CAPTURED (future)
```

---

## What Gets Recorded

When you make a decision, the system captures:

### Core Decision

- **Chosen Scenario**: Which option was selected
- **Rejected Alternatives**: Why other options weren't chosen
- **Decision Date/Time**: When decision was made
- **Decision Maker**: Who made the decision
- **Confidence Level**: 0-100% confidence in decision

### Rationale

- **Key Reasons**: Why this choice
- **Trade-offs**: What you're giving up
- **Strategic Alignment**: How it fits goals
- **Risk Assessment**: Known risks and mitigation

### Implementation

- **Next Steps**: Actions to take
- **Timeline**: When things happen
- **Owners**: Who's responsible
- **Success Metrics**: How to measure success
- **Checkpoints**: When to review progress

### Stakeholder Communication

- **Team Notification**: Who should know
- **Message**: What to tell them
- **Updates**: When to provide progress

---

## Example: Hire Full-Time Developer Decision

```
/scenario:decide sc-1733596400000-abc123 --chosen --rationale "Higher long-term value and team morale boost. Financial ROI strong at 12-month mark." --confidence 82 --next-steps "Week 1: Post opening + Review resumes; Week 2: First round interviews; Week 3: Final interviews and offer; Week 4: Onboarding" --notify team@company.com

========================================
DECISION RECORDED
========================================

✅ DECISION: Hire Full-Time Developer

Scenario Chosen: Hire Full-Time Developer
Scenario ID: sc-1733596400000-abc123
Comparison: Hire vs Outsource

Decision Made By: Aaron (aaron@company.com)
Decision Date: December 6, 2025
Confidence Level: 82%

========================================
RATIONALE
========================================

Why This Choice:
"Higher long-term value and team morale boost. Financial ROI strong at 12-month mark."

Financial Analysis:
- Year 1 Cost: $100,000
- Year 1 Revenue Impact: +$160,000
- Year 2+ Value: Compounding (team asset)
- Payback Period: 7-9 months
- Decision: Worth the investment

Strategic Analysis:
- Supports Business Growth: ✅ Excellent alignment
- Team Building: ✅ Morale boost (+10)
- Long-term Scalability: ✅ Enables future hiring
- Reduces Dependency: ✅ Less reliant on freelancers

Alternative Considered (Outsourcing):
- Cost savings in Year 1: $48K less
- Quality concerns: -20% expected output
- Less strategic value: No team building
- Less flexible: Can't scale team easily
- Rejected because: Strategic value doesn't justify cost savings

Risk Mitigation:
- Risk: Wrong hire / poor fit
  Mitigation: Structured interviews, probation period, clear KPIs

- Risk: Not enough work to keep busy
  Mitigation: 40+ hours booked before hiring

- Risk: Salary expectations increase
  Mitigation: Clear compensation structure in offer

========================================
IMPLEMENTATION PLAN
========================================

WEEK 1: Prepare & Recruit
├─ Owner: Aaron
├─ Tasks:
│   ├─ Post job on 3 platforms (LinkedIn, AngelList, Stack Overflow)
│   ├─ Set salary range: $80-95K
│   ├─ Prepare job description highlighting growth opportunity
│   ├─ Schedule referral bonus ($2K)
│   └─ Target: 20+ qualified applicants
│
└─ Success Metric: 20+ quality applications by Friday

WEEK 2: Screen & Interview Round 1
├─ Owner: Aaron + Senior Dev
├─ Tasks:
│   ├─ Resume screening (2 hours)
│   ├─ 30-min phone screens (10 candidates)
│   ├─ Technical coding challenge (5 candidates)
│   ├─ Debrief with team on top 3
│   └─ Select 3 for in-person interviews
│
└─ Success Metric: 3 strong candidates selected

WEEK 3: Final Interviews & Offer
├─ Owner: Aaron + Team
├─ Tasks:
│   ├─ Full-day interviews (3 candidates)
│   ├─ Team lunch/culture fit (2 candidates)
│   ├─ Reference checks (top 2 candidates)
│   ├─ Compensation negotiation with 1st choice
│   └─ Send offer by Friday
│
└─ Success Metric: Offer signed

WEEK 4: Onboarding Preparation
├─ Owner: Aaron + HR
├─ Tasks:
│   ├─ Background check & paperwork
│   ├─ Equipment setup (laptop, tools, access)
│   ├─ Office space prepared
│   ├─ Onboarding materials created
│   ├─ Assign onboarding buddy
│   └─ Schedule first week meetings
│
└─ Success Metric: Ready for Day 1

========================================
CHECKPOINTS
========================================

30-Day Check-In (January 6, 2026)
├─ Is hire productive? (Should have completed first project)
├─ How's culture fit? (Team feedback)
├─ Any issues to address?
└─ Adjust if needed

90-Day Review (March 6, 2026)
├─ Probation period decision
├─ Performance review
├─ Confirmation or changes
└─ Compensation adjustment discussion

6-Month Review (June 6, 2026)
├─ Is ROI matching expectations?
├─ Team growth impact
├─ Career development plan
└─ Next hiring decision?

12-Month Review (December 6, 2026)
├─ Year 1 results vs projections
├─ Team expansion feasibility
├─ Business impact assessment
└─ Decision: Keep/upgrade/transition

========================================
TEAM NOTIFICATION
========================================

✅ Team Notification Prepared
Recipient: team@company.com
Message: "We've made a decision to hire a full-time Senior Developer..."

Key Points Included:
✅ Decision and rationale
✅ Expected start date: ~4 weeks
✅ Role and responsibilities
✅ How this affects team capacity
✅ Team member involvement in hiring
✅ Timeline and next steps
✅ Questions welcome

Status: Ready to send
Send Time: Immediate
Confirm Before Send: Yes (you can edit message)

========================================
SUCCESS METRICS
========================================

Way to Measure Success:

Financial:
- [ ] Dev completes 40+ billable hours/week by month 2
- [ ] Revenue impact reaches +$160K by month 12
- [ ] ROI payback within 9 months (target: 7-9 months)

Operational:
- [ ] On-time project delivery increases by 30%
- [ ] Development cycle time reduced by 25%
- [ ] Code quality metrics improve (fewer bugs)

Team:
- [ ] Team morale survey improvement
- [ ] Retention of existing team members
- [ ] Capacity to take on larger projects

Strategic:
- [ ] Foundation for future hiring
- [ ] Ability to scale to 2-3 person team
- [ ] Business growth acceleration

========================================
ORGANIZATIONAL LEARNING
========================================

This decision will be analyzed later:
- Actual cost vs projected
- Revenue impact vs projected
- Team morale impact (survey)
- Scaling impact (future hiring)
- What worked / what didn't
- Lessons for next hiring decision

Archive Location: decisions/2025-12/hire-developer-final
Decision ID: dec-1733596400000-abc123

========================================
NEXT ACTIONS FOR YOU
========================================

Immediate (Today):
✅ Decision recorded
✅ Rationale documented
✅ Confidence level set (82%)
⏳ Send team notification (optional)

This Week:
⏳ Post job opening (Week 1 starts)
⏳ Prepare interview questions
⏳ Schedule interviews

Ongoing:
⏳ Track hiring progress
⏳ Monitor implementation plan
⏳ Adjust if needed
⏳ Prepare for 30-day check-in
```

---

## Decision Structure

### Core Elements

**1. Chosen Scenario** (Required)

```bash
--chosen
```

The scenario you've selected as the decision

**2. Confidence Level** (Optional, 0-100)

```bash
--confidence 82
```

How confident you are (Default: inferred from scenario analysis)

**3. Rationale** (Optional, 1-3 sentences)

```bash
--rationale "Higher long-term value and team alignment"
```

Why you chose this option

**4. Next Steps** (Optional, bullet list)

```bash
--next-steps "Week 1: Post job. Week 2: Interview. Week 3: Offer. Week 4: Onboard"
```

Implementation plan (can be detailed)

**5. Notify Team** (Optional, email)

```bash
--notify team@company.com
```

Who should be informed about decision

---

## Confidence Level Guidelines

| Level | Meaning | Use When |
|-------|---------|----------|
| **90-100%** | Obvious choice | Clear winner, minimal trade-offs |
| **80-89%** | High confidence | Good data, some unknowns acceptable |
| **70-79%** | Moderate confidence | Reasonable data, some risks |
| **60-69%** | Lower confidence | Limited data, more unknowns |
| **Below 60%** | Uncertain | Coin flip territory, may need more analysis |

---

## Decision Retention

Decisions are archived and used for:

**1. Organizational Learning**

- What worked? What didn't?
- Accuracy of projections
- Decision quality over time

**2. Future Reference**

- Similar decisions later
- Lessons learned
- Process improvements

**3. Accountability**

- Who decided?
- When was it decided?
- What was the rationale?

**4. Outcomes Tracking**

- Did we achieve projections?
- What actually happened?
- Return on decision

---

## Common Patterns

### Pattern 1: Clear Winner

```bash
/scenario:decide sc-123 --chosen --confidence 85
```

→ Use when analysis is clear, multiple factors align

### Pattern 2: Compromise Decision

```bash
/scenario:decide sc-123 --chosen --rationale "Balancing cost and quality" --confidence 72
```

→ Use when trade-offs required, lower confidence acceptable

### Pattern 3: Strategic Bet

```bash
/scenario:decide sc-123 --chosen --rationale "Long-term vision over short-term cost" --confidence 78
```

→ Use when choosing growth over optimization

### Pattern 4: Data-Driven Decision

```bash
/scenario:decide sc-123 --chosen --rationale "Exceeds our ROI threshold of 50% by year 1" --confidence 88
```

→ Use when metrics clearly support choice

### Pattern 5: Delegated Decision

```bash
/scenario:decide sc-123 --chosen --delegation-id del-456 --rationale "Team recommends this approach"
```

→ Use when delegation input included in decision

---

## After Decision

### Track Progress

```bash
/scenario:decide sc-123 --add-milestone "Month 1: First hire onboarded"
/scenario:decide sc-123 --add-milestone "Month 3: First revenue impact"
/scenario:decide sc-123 --add-milestone "Month 6: ROI trending positive"
```

### Update Status

```bash
/scenario:decide sc-123 --update-status "In Progress"
/scenario:decide sc-123 --update-status "Completed"
```

### Review Results

```bash
/scenario:decide sc-123 --compare-actual "Actual cost: $102K (projected $100K), Revenue: $150K (projected $160K)"
/scenario:decide sc-123 --lessons-learned "Process worked well. Adjust hiring timeline for next time."
```

---

## Success Criteria

**After making a decision:**

- ✅ Decision is recorded with unique ID
- ✅ Chosen scenario is documented
- ✅ Rationale explains why
- ✅ Confidence level set (0-100%)
- ✅ Implementation plan created
- ✅ Team notified (if applicable)
- ✅ Checkpoints scheduled
- ✅ Success metrics defined

**After implementation starts:**

- ✅ Tasks assigned to owners
- ✅ Timeline is clear
- ✅ Progress is tracked
- ✅ Issues are addressed quickly
- ✅ Adjustments made if needed

**After 30/60/90 days:**

- ✅ Results compared to projections
- ✅ Actual cost vs budget
- ✅ Actual impact vs expected
- ✅ Team feedback collected
- ✅ Lessons documented

---

**Make final decisions with confidence and clarity**
**Document rationale for organizational learning**
**Create implementation plans for execution**
**Track outcomes to improve future decisions**
