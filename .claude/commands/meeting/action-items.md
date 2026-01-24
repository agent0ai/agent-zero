---
description: Extract and assign action items with deadlines
argument-hint: [--source <meeting-notes|transcript|recording>] [--meeting <title>] [--auto-assign]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Meeting Action Items - Intelligent Task Extraction & Assignment

## Overview

Meeting Action Items is an AI-powered system that automatically extracts commitments, tasks, and next steps from meeting notes, transcripts, or recordings. It assigns owners, suggests deadlines, prioritizes work, and integrates with your task management system to ensure nothing falls through the cracks.

For solo entrepreneurs, meetings generate dozens of commitments weekly. This system ensures every "I'll do that by Friday" gets captured, assigned, tracked, and completed—transforming verbal commitments into executed work.

**ROI: $40,000/year** through eliminated dropped tasks (preventing 3-5 costly mistakes/year at $5-10K each), reduced meeting follow-up time (8 hours/month saved), improved team accountability, and faster project velocity from clear ownership.

## Key Benefits

**Zero Dropped Commitments**

- AI extracts 100% of action items from meeting discussions
- No reliance on manual note-taking or memory
- Captures implicit commitments ("let me check on that" = action item)
- Prevents costly mistakes from forgotten follow-ups

**Clear Accountability**

- Every action item has explicit owner (no ambiguity)
- Deadlines assigned or suggested based on context
- Priority levels guide work sequencing
- Dependencies identified to prevent blocked work

**Automated Task Management**

- Action items auto-exported to your task system (Asana, Todoist, etc.)
- Tracking integrated into existing workflow
- Reminders sent before deadlines
- Completion status synced back to meeting notes

**Team Visibility & Coordination**

- Everyone sees their commitments immediately after meeting
- Cross-functional dependencies surfaced
- Bottlenecks identified before they cause delays
- Progress visible to all stakeholders

## Implementation Steps

### Step 1: Provide Meeting Source Material

Action item extraction works from multiple input types:

```bash
# From meeting notes (most common)
/meeting:action-items --source meeting-notes --meeting "Board Meeting Q1 2024"

# From transcript (Zoom, Otter.ai, etc.)
/meeting:action-items --source transcript --file transcript.txt --meeting "Client Call - TechCorp"

# From recording with auto-transcription
/meeting:action-items --source recording --file meeting-recording.mp4 --auto-transcribe

# From rough notes or bullet points
/meeting:action-items --source notes --file rough-notes.md --meeting "Sprint Planning"

# Auto-assign based on participant roles and historical patterns
/meeting:action-items --meeting "Board Meeting Q1 2024" --auto-assign
```

The system will:

- Parse the source material (notes, transcript, recording)
- Identify explicit and implicit commitments
- Extract owner, deadline, and context for each action item
- Suggest priorities based on urgency and importance
- Flag dependencies between related action items
- Format for export to task management systems

### Step 2: Action Item Extraction Logic

AI identifies commitments using multiple patterns:

**Explicit Commitments:**

- "I'll [do X] by [deadline]"
- "Sarah will [task] before [date]"
- "We need to [action] by [time]"
- "Can you [request] this week?"
- "Let's [action] before next meeting"

**Implicit Commitments:**

- "Let me check on that" → [Person] check on [topic]
- "We should probably [action]" → Someone needs to [action]
- "I'll look into it" → [Person] research [topic]
- "Good point, I hadn't thought of that" → May imply follow-up action

**Questions Requiring Follow-Up:**

- "What's the status of [project]?" → [Owner] provide status update
- "Do we have data on [metric]?" → Someone gather data
- "Can we [capability]?" → Investigate feasibility

**Decisions Requiring Implementation:**

- "Let's go with option A" → Someone implement option A
- "Approved, move forward" → Project team execute plan
- "Hire for this role" → Someone start hiring process

**Meeting-End Commitments:**

- "I'll send the deck after this call" → [Person] send deck
- "Next steps are X, Y, Z" → Create actions for X, Y, Z
- "Let's schedule follow-up" → Someone schedule meeting

### Step 3: Automatic Owner Assignment

System assigns owners using multiple strategies:

**Explicit Assignment (Highest Confidence):**

- Direct statement: "Sarah, can you handle this?"
- Volunteering: "I'll take care of that"
- Role-based: "We need engineering to [task]" → Assign to engineering lead

**Role-Based Assignment (Medium Confidence):**

- Financial tasks → CFO or finance team
- Technical tasks → CTO or engineering lead
- Marketing tasks → VP Marketing or marketing team
- Sales tasks → Head of Sales or sales team

**Historical Pattern Assignment (Medium-Low Confidence):**

- Person who handled similar tasks in past meetings
- Person who raised the topic or concern
- Person with most context or expertise on the topic

**Default Assignment (Low Confidence):**

- If unclear, assign to meeting organizer or project lead
- Flag as "needs assignment" for manual review
- Suggest 2-3 potential owners based on analysis

**Example Extraction:**

```
From Discussion:
"Michael brought up the churn concern. Sarah, can you pull together an analysis by cohort and present it at the next board meeting? We need to understand if this is a product issue, customer success issue, or sales qualification issue."

Extracted Action Item:
-----------------------
Task: Analyze customer churn by cohort and identify root cause patterns

Owner: Sarah Johnson (CFO)
Confidence: HIGH (explicit assignment)
Alternative: None

Deadline: April 15, 2024 (next board meeting)
Source: "present it at the next board meeting"
Confidence: HIGH (explicit deadline)

Priority: HIGH
Rationale:
- Board concern (requires leadership attention)
- Blocks Q2 strategic planning decisions
- Mentioned by board member (high-stakes stakeholder)

Dependencies:
- Access to customer data in Salesforce
- Potential need for engineering support on data extraction

Context:
Churn increased from 3.8% to 4.2% in Q1. Board member Michael Lee raised concern about sustainability. Analysis will inform whether Q2 should focus on customer success, sales qualification, or product improvements.

Deliverable Type: Analysis + Presentation
Estimated Effort: 8-12 hours
Skills Required: Data analysis, SQL, presentation
```

### Step 4: Deadline Extraction & Suggestion

System determines deadlines using multiple approaches:

**Explicit Deadlines (Use As-Is):**

- "By Friday" → This Friday's date
- "By next board meeting" → Next meeting date from calendar
- "In two weeks" → Date 14 days from meeting
- "End of quarter" → Last day of current quarter

**Relative Deadlines (Calculate Date):**

- "By next meeting" → Next scheduled meeting with same participants
- "Before Q2 starts" → March 31 if currently in Q1
- "This month" → Last day of current month
- "Soon" / "ASAP" → Suggest 3-5 business days

**Implied Deadlines (Infer from Context):**

- Mentioned during Q2 planning → Assume before Q2 ends
- Blocking other work → Urgent, suggest 1 week
- Board request → Due before next board meeting
- "No rush" → Suggest 2-4 weeks

**Default Deadlines (If No Signal):**

- High priority tasks: 1 week
- Medium priority tasks: 2 weeks
- Low priority tasks: 1 month
- Research/analysis: 2 weeks
- Quick follow-ups: 3-5 business days

### Step 5: Priority Assessment

Prioritize action items using multi-factor scoring:

**Priority Factors:**

1. **Stakeholder Importance (Weight: 30%)**
   - Board/investor request: +50 points
   - Customer request: +40 points
   - Internal leadership: +30 points
   - Team request: +20 points

2. **Urgency (Weight: 25%)**
   - Blocks other work: +50 points
   - Time-sensitive deadline: +40 points
   - "ASAP" or "urgent" mentioned: +35 points
   - Within 1 week: +30 points
   - Within 2 weeks: +20 points

3. **Business Impact (Weight: 25%)**
   - Revenue impact: +50 points
   - Customer retention impact: +45 points
   - Strategic decision dependency: +40 points
   - Team productivity impact: +30 points
   - Nice-to-have improvement: +10 points

4. **Effort vs. Value (Weight: 20%)**
   - High value, low effort (quick win): +50 points
   - High value, high effort (strategic): +40 points
   - Low value, low effort (easy): +20 points
   - Low value, high effort (avoid): +5 points

**Priority Scoring:**

- 80-100 points: **CRITICAL** (drop everything, do now)
- 60-79 points: **HIGH** (this week)
- 40-59 points: **MEDIUM** (this month)
- 20-39 points: **LOW** (backlog)
- 0-19 points: **OPTIONAL** (consider not doing)

**Example Priority Assessment:**

```
Action Item: Analyze churn by cohort (Sarah)

Stakeholder Importance: Board request (+50) = 50 points
Urgency: Due at next board meeting in 5 weeks (+20) = 20 points
Business Impact: Strategic decision dependency (+40) = 40 points
Effort vs Value: High value, high effort (+40) = 40 points

Total Score: 150 points (weighted avg: 72 points)
Priority: HIGH

Justification:
Board-level concern with strategic implications for Q2 planning. Not time-critical (5 weeks out), but high value for decision-making. Effort is substantial (8-12 hours) but justified by impact.
```

### Step 6: Dependency Identification

Identify relationships between action items:

**Blocking Dependencies:**

- Task A must complete before Task B can start
- Example: "Hire engineer" blocks "Assign Slack integration"

**Information Dependencies:**

- Task A produces information needed for Task B
- Example: "Churn analysis" informs "Q2 customer success strategy"

**Resource Dependencies:**

- Task A and Task B require same person/resource
- Example: Both tasks assigned to Sarah (capacity constraint)

**Timeline Dependencies:**

- Task A and Task B must coordinate timing
- Example: "Send proposal" must happen before "Proposal presentation meeting"

**Decision Dependencies:**

- Task A requires decision to be made first
- Example: "Implement feature X" depends on "Decide to build vs buy"

**Example Dependency Graph:**

```
Action Items from Sprint Planning Meeting:

1. [Chris] Complete onboarding wizard designs
   ↓ BLOCKS (design must finish before engineering)
2. [Jamie] Build onboarding wizard
   ↓ BLOCKS (feature must be ready before testing)
3. [Taylor] QA test onboarding wizard
   ↓ INFORMS (testing may reveal issues)
4. [Sarah] Update product roadmap with Q2 priorities
   (PARALLEL - no dependencies)

Dependencies Flagged:
- Task 2 cannot start until Task 1 completes (blocking)
- Task 3 cannot start until Task 2 completes (blocking)
- Task 4 is independent and can proceed immediately

Critical Path: 1 → 2 → 3 (Any delay cascades)
Parallel Work: Task 4 (no blockers, start immediately)

Capacity Conflict:
- Jamie assigned to Task 2 (onboarding) and also performance optimization
- Risk: 150% capacity allocation in Sprint 1
- Recommendation: Sequence tasks or add resources
```

### Step 7: Task Management Integration

Export action items to your preferred system:

**Supported Integrations:**

- **Asana**: Project-based task management with subtasks
- **Todoist**: Personal task lists with priorities and labels
- **Trello**: Kanban boards with cards and checklists
- **ClickUp**: Comprehensive project management with custom fields
- **Linear**: Engineering-focused issue tracking
- **Jira**: Enterprise project and issue tracking
- **Notion**: Database-based task tracking in pages
- **Google Tasks**: Simple integration with Gmail and Calendar
- **Microsoft To-Do**: Integration with Outlook and Teams

**Export Format Example (Asana):**

```
Project: Board of Directors
Section: Q1 2024 - March Meeting

Task: Analyze customer churn by cohort
Assignee: Sarah Johnson
Due Date: April 15, 2024
Priority: High
Description:
Analyze customer churn by cohort (sign-up date, customer segment, ACV, product usage) and identify root cause patterns. Present findings at April 15 board meeting.

Board is concerned about churn increase from 3.8% to 4.2%. Analysis should answer: Is this product issue, customer success issue, or sales qualification issue?

Subtasks:
- [ ] Extract churn data from Salesforce
- [ ] Pull usage metrics from Mixpanel
- [ ] Segment analysis by cohort
- [ ] Identify patterns and root causes
- [ ] Develop retention recommendations
- [ ] Create presentation deck
- [ ] Review with CEO before board meeting

Tags: board-meeting, strategic, analysis, retention
Time Estimate: 8-12 hours
Source: Board Meeting Q1 2024 (March 10)

Dependencies:
- Requires: Access to Salesforce and Mixpanel data
- Blocks: Q2 customer success strategy planning

Related Tasks:
- Update Q2 plan (CEO) - Depends on this analysis
- Hire CS team (CEO) - Informed by this analysis
```

### Step 8: Action Item Tracking & Reminders

Monitor progress and send timely reminders:

**Reminder Schedule:**

**3 Days Before Deadline:**

```
Subject: Action Item Due Soon: Analyze customer churn

Hi Sarah,

Reminder that your action item from the March 10 Board Meeting is due in 3 days:

Task: Analyze customer churn by cohort
Due: April 15, 2024 (Friday)
Priority: HIGH

You have completed 3 of 7 subtasks (43% complete). Based on remaining work and time available, you may need to adjust scope or ask for help to meet deadline.

Subtasks Remaining:
- [ ] Identify patterns and root causes
- [ ] Develop retention recommendations
- [ ] Create presentation deck
- [ ] Review with CEO before board meeting

Need an extension? Reply to this email or contact John (CEO) to discuss.

View task in Asana: [Link]
```

**Day of Deadline:**

```
Subject: Action Item Due Today: Analyze customer churn

Hi Sarah,

Your action item is due today:

Task: Analyze customer churn by cohort
Due: Today, April 15, 2024
Priority: HIGH
Status: 71% complete (5 of 7 subtasks)

If you're not on track to complete by end of day, please:
1. Update status in Asana
2. Notify John (CEO) and board members
3. Propose new deadline or adjusted scope

View task in Asana: [Link]
```

**1 Day Past Due (If Not Completed):**

```
Subject: Overdue Action Item: Analyze customer churn

Hi Sarah,

Your action item from the March 10 Board Meeting is now overdue:

Task: Analyze customer churn by cohort
Original Due: April 15, 2024 (yesterday)
Priority: HIGH
Status: 71% complete

This task is blocking:
- Q2 customer success strategy planning
- Board meeting agenda (scheduled for today)

Please provide update:
1. Current status and completion %
2. New estimated completion date
3. Any blockers or help needed

CC: John (CEO) for visibility

View task in Asana: [Link]
```

**Weekly Digest (All Action Items):**

```
Subject: Your Action Items - Week of April 15, 2024

Hi Sarah,

You have 7 active action items from recent meetings:

DUE THIS WEEK (2):
- [HIGH] Analyze customer churn by cohort - Due Today (April 15)
- [MEDIUM] Review Q2 budget draft - Due Thursday (April 18)

DUE NEXT WEEK (1):
- [HIGH] Finalize Q2 hiring plan - Due Monday (April 22)

DUE LATER (4):
- [MEDIUM] Research accounting software options - Due May 1
- [LOW] Update financial dashboard template - Due May 15
- [MEDIUM] Q2 finance team OKRs - Due May 1
- [LOW] Expense policy documentation - Due May 31

Completed This Week (3):
✓ Q1 financial close
✓ Board deck financial slides
✓ Contractor payment processing

View all tasks in Asana: [Link]
```

### Step 9: Completion Tracking & Follow-Up

Track completion and update source documents:

**Completion Triggers:**

- Task marked complete in Asana/Todoist/etc. (automatic sync)
- Manual confirmation via email or Slack
- Deliverable shared (e.g., "Churn analysis" deck uploaded)
- Mentioned as complete in next meeting

**Automatic Updates:**

```
Action Item Completed: Analyze customer churn by cohort

Task: Analyze customer churn by cohort
Owner: Sarah Johnson
Completed: April 15, 2024 (on time)
Time Taken: 10 hours (vs 8-12 hour estimate - accurate)

Deliverable: Churn Analysis Q1 2024.pdf [Link]

Impact:
- Enabled Q2 strategic planning decision
- Presented at April 15 board meeting
- Informed customer success hiring priorities

Related Updates:
- Board Meeting April 15 notes updated (marked complete)
- Q2 Strategic Plan informed by this analysis
- Customer Success hiring plan updated based on findings

Completion Rate for Sarah: 95% (19 of 20 recent action items completed on time)
```

**Stuck/Blocked Item Escalation:**

```
Action Item Blocked: Hire customer success team

Task: Hire 2 customer success team members
Owner: John (CEO)
Original Due: March 31, 2024
Status: BLOCKED (14 days overdue)

Blocker: No qualified candidates in pipeline despite 3 weeks of recruiting

Impact:
- Delays Q2 retention strategy implementation
- Impacts ability to address churn concerns raised by board
- Blocks customer success process implementation

Escalation Recommended:
- Consider fractional CS consultant while recruiting
- Expand candidate sources (agencies, different geographies)
- Adjust role requirements if too narrow
- Brief board on delay and mitigation plan

Discuss at next meeting: Executive Team Meeting (April 25)
```

### Step 10: Action Item Analytics

Track patterns and improve meeting effectiveness:

**Individual Performance Metrics:**

```
Sarah Johnson - Action Item Analytics (Last 90 Days)

Total Action Items: 23
Completed: 21 (91% completion rate)
On Time: 19 (90% of completed items)
Average Time to Complete: 8.5 days (vs 10.2 day avg deadline)

Priority Breakdown:
- High priority: 8 items (100% completed, 88% on time)
- Medium priority: 12 items (92% completed, 92% on time)
- Low priority: 3 items (67% completed, 67% on time)

Pattern: Sarah completes high-priority items reliably but low-priority items sometimes slip. Consider: Don't assign low-priority items to Sarah if backlog is full.

Action Item Sources:
- Board meetings: 6 items (100% completion)
- Exec team meetings: 11 items (91% completion)
- Finance team meetings: 6 items (83% completion)

Average Effort Estimation Accuracy: 95%
(Estimated 8-12 hours, actual 10 hours avg)

Strengths:
- Reliable on strategic, high-impact items
- Accurate time estimates
- Proactive communication when blocked

Areas for Improvement:
- Low-priority items fall off radar (consider delegating)
- Occasionally misses soft deadlines without explicit date
```

**Meeting Effectiveness Metrics:**

```
Board Meetings - Action Item Analytics (Last 12 Months)

Total Meetings: 4 (quarterly)
Action Items Generated: 47 (avg 11.8 per meeting)
Completion Rate: 89% (42 of 47 completed)
On-Time Rate: 85% (40 of 47 completed by deadline)

Action Item Trends:
- Q1 2023: 14 items (93% completion)
- Q2 2023: 10 items (90% completion)
- Q3 2023: 12 items (83% completion)
- Q4 2023: 11 items (91% completion)

Most Common Action Types:
1. Analysis/Research (14 items, 93% completion)
2. Strategic Planning (11 items, 91% completion)
3. Hiring/Personnel (8 items, 75% completion) ⚠ Lower completion
4. Communication/Updates (7 items, 100% completion)
5. Process Implementation (7 items, 86% completion)

Insights:
- Hiring-related action items have lower completion rate (75% vs 89% avg)
- May indicate hiring is harder than expected or timelines unrealistic
- Consider: Build more buffer time for hiring actions

Average Time from Assignment to Completion:
- High priority: 12 days
- Medium priority: 18 days
- Low priority: 31 days

Meeting Action Item Efficiency Score: 85/100
(Based on completion rate, on-time rate, and follow-through)

Recommendations:
- Reduce hiring action items per meeting (break into smaller milestones)
- Set more realistic deadlines for complex tasks
- Consider quarterly action item review (what's still open from 2+ meetings ago?)
```

## Usage Examples

### Example 1: Extract from Meeting Notes

**Command:**

```bash
/meeting:action-items --source meeting-notes --meeting "Board Meeting Q1 2024"
```

**Output:**

```
ACTION ITEMS EXTRACTED: Board Meeting Q1 2024
Date: March 10, 2024
Participants: John (CEO), Sarah (CFO), Michael Lee (Board Member), Emily Chen (Board Observer)

=== ACTION ITEMS SUMMARY ===
Total Items Extracted: 4
High Priority: 2
Medium Priority: 2
Low Priority: 0

Assignments:
- Sarah Johnson: 1 item
- John Smith: 3 items

=== DETAILED ACTION ITEMS ===

─────────────────────────────────────────────
ACTION ITEM #1 [HIGH PRIORITY]

Task: Analyze customer churn by cohort and identify root cause patterns

Owner: Sarah Johnson (CFO)
Assignment Confidence: HIGH (explicit: "Sarah, can you pull together an analysis")

Deadline: April 15, 2024 (next board meeting)
Deadline Confidence: HIGH (explicit: "present it at the next board meeting")

Priority: HIGH (Score: 72/100)
Rationale:
- Board member concern (stakeholder importance: high)
- Strategic decision dependency (business impact: high)
- 5-week timeline (urgency: medium)
- High value, high effort (effort vs value: strategic work)

Dependencies:
- Requires: Salesforce data access, Mixpanel usage metrics
- May need: Engineering support for data extraction
- Blocks: Q2 customer success strategy planning

Deliverable:
- Analysis document with cohort segmentation
- Root cause identification (product, CS, or sales qualification)
- Presentation deck for board review
- Recommendations with resource requirements

Estimated Effort: 8-12 hours

Context (From Meeting):
"Michael brought up the churn concern. Sarah, can you pull together an analysis by cohort and present it at the next board meeting? We need to understand if this is a product issue, customer success issue, or sales qualification issue."

Churn increased from 3.8% to 4.2% in Q1. Board member Michael Lee raised sustainability concerns. This analysis will inform Q2 strategic focus.

Export to Asana:
Project: Board of Directors
Section: Q1 2024 - March Meeting
[View in Asana] [Create Task]

─────────────────────────────────────────────
ACTION ITEM #2 [HIGH PRIORITY]

Task: Send updated Q2 strategic plan reflecting retention focus

Owner: John Smith (CEO)
Assignment Confidence: HIGH (explicit: "CEO to send updated Q2 plan")

Deadline: Friday, March 15, 2024 (3 business days)
Deadline Confidence: HIGH (explicit: "by Friday")

Priority: HIGH (Score: 78/100)
Rationale:
- Board decision requiring implementation (stakeholder: high)
- Short deadline (urgency: very high)
- Strategic planning impact (business impact: high)
- Medium effort, high value (effort vs value: good ratio)

Dependencies:
- Informs: Board async review over weekend
- Blocks: Q2 execution planning
- Requires: Board meeting decisions documented

Deliverable:
- Updated Q2 Strategic Plan document
- Key changes:
  * Revenue target: $560K MRR (15% growth vs 20% original)
  * Hiring: Prioritize 2 CS hires over sales hires
  * Product: Focus retention features
  * Success metrics: Churn reduction to 3%
- Shared with all board members via email

Estimated Effort: 3-4 hours

Context (From Meeting):
Board unanimously approved shift from growth focus to retention focus for Q2. CEO committed to sending updated plan by Friday for board to review async over weekend.

Export to Asana:
Project: Strategic Planning
Section: Q2 2024
[View in Asana] [Create Task]

─────────────────────────────────────────────
ACTION ITEM #3 [MEDIUM PRIORITY]

Task: Hire 2 customer success team members

Owner: John Smith (CEO)
Assignment Confidence: MEDIUM (implied: CEO typically owns hiring)

Deadline: March 31, 2024 (end of Q1)
Deadline Confidence: HIGH (explicit: "end of Q1")

Priority: MEDIUM (Score: 58/100)
Rationale:
- Strategic initiative from board decision (stakeholder: high)
- 3-week timeline (urgency: medium)
- Customer retention impact (business impact: high)
- High effort (hiring is time-intensive) (effort vs value: strategic)

Dependencies:
- Blocks: Customer success process implementation
- Blocks: Ability to address churn concerns
- Informs: Q2 operational capacity

Deliverable:
- 2 customer success hires completed
- Onboarded and productive by early Q2
- Positions: CS Manager + CS Associate (based on retention strategy)

Estimated Effort: 20-30 hours (recruiting, interviews, offers)

Context (From Meeting):
Part of Q2 retention-focused strategy approved by board. Prioritize CS hires over additional sales hires. Critical for addressing 4.2% churn rate.

Risk Note: 3-week timeline for 2 hires is aggressive. May need to adjust expectations or extend timeline.

Export to Asana:
Project: Hiring
Section: Q1 2024
[View in Asana] [Create Task]

─────────────────────────────────────────────
ACTION ITEM #4 [MEDIUM PRIORITY]

Task: Review Q2 strategic plan and provide async feedback

Owner: Board Members (Michael Lee, Emily Chen)
Assignment Confidence: HIGH (explicit: "Board to review")

Deadline: Weekend of March 16-17, 2024
Deadline Confidence: MEDIUM (implied: "over weekend after Friday send")

Priority: MEDIUM (Score: 52/100)
Rationale:
- Enables Q2 execution (business impact: medium)
- Short timeline (urgency: medium)
- Low effort review task (effort vs value: quick win)

Dependencies:
- Requires: Updated Q2 plan from CEO (Action Item #2)
- Blocks: Final Q2 plan approval and execution start

Deliverable:
- Async feedback on updated Q2 plan
- Approval or requests for changes
- Questions or concerns to address

Estimated Effort: 1-2 hours per board member

Context (From Meeting):
CEO will send updated Q2 plan Friday. Board members review over weekend and provide feedback async. Ensures everyone aligned before Q2 execution begins April 1.

Export to Asana:
Project: Board of Directors
Section: Q1 2024 - March Meeting
[View in Asana] [Create Task]

─────────────────────────────────────────────

=== DEPENDENCY GRAPH ===

```

Timeline:
Week 1 (March 11-15):
  [John] Update Q2 Plan → Due Friday
    ↓ BLOCKS
Week 1 (March 16-17):
  [Board] Review Q2 Plan → Due Weekend
    ↓ INFORMS
Week 2-3 (March 18-31):
  [John] Hire CS Team → Due End of Q1
    ↓ BLOCKS
Week 4-9 (April 1-May 12):
  [Sarah] Churn Analysis → Due April 15
    ↓ INFORMS
Q2 Strategy:
  Customer Success Implementation

```

Critical Path:
Q2 Plan Update → Board Review → Q2 Execution

Parallel Work:
- CS Hiring (independent, can start immediately)
- Churn Analysis (independent, longer timeline)

─────────────────────────────────────────────

=== EXPORT OPTIONS ===

[Export All to Asana] [Export to Todoist] [Export to Notion]
[Send Email Summary to Participants]
[Add to Google Calendar Reminders]

=== TRACKING & REMINDERS ===

Reminder Schedule Set:
- March 13 (3 days before): John - Q2 Plan reminder
- March 15 (due date): John - Q2 Plan due today
- March 16 (after dependency): Board - Q2 Plan ready for review
- March 28 (3 days before): John - CS Hiring reminder
- April 12 (3 days before): Sarah - Churn Analysis reminder

Weekly Digest: Enabled for all participants
Completion Tracking: Enabled (auto-sync with Asana)
Escalation: Auto-escalate if 3+ days overdue

=== MEETING INSIGHTS ===

Action Items Per Participant:
- John (CEO): 2 items (50% of total)
- Sarah (CFO): 1 item (25% of total)
- Board Members: 1 item (25% of total)

Workload Balance: Reasonable
John has most action items but that's appropriate for CEO role.

Timeline Pressure:
- 1 item due this week (high pressure)
- 2 items due this month (manageable)
- 1 item due next month (plenty of time)

Risk Assessment:
⚠ Hiring timeline aggressive (2 hires in 3 weeks)
✓ Other items have realistic timelines
✓ No capacity conflicts identified

Meeting Efficiency Score: 88/100
- Clear ownership (100%)
- Explicit deadlines (75% explicit, 25% implied)
- Well-prioritized (50% high priority, strategic focus)
- Manageable volume (4 items, not overwhelming)
```

## Quality Control Checklist

**Extraction Completeness:**

- [ ] All explicit commitments extracted from source material
- [ ] Implicit commitments identified (e.g., "let me check on that")
- [ ] Questions requiring follow-up converted to action items
- [ ] Decisions requiring implementation captured as tasks
- [ ] End-of-meeting next steps documented

**Owner Assignment:**

- [ ] Every action item has explicit owner (no ambiguity)
- [ ] Assignment confidence level assessed (high/medium/low)
- [ ] Role-based assignments validated (right person for task type)
- [ ] Capacity conflicts identified (person assigned too many tasks)
- [ ] Ambiguous assignments flagged for manual review

**Deadline Quality:**

- [ ] Explicit deadlines captured verbatim from source
- [ ] Relative deadlines calculated correctly (e.g., "next meeting" = specific date)
- [ ] Implied deadlines inferred from context reasonably
- [ ] Default deadlines assigned when no signal available
- [ ] Aggressive timelines flagged as risk

**Priority Assessment:**

- [ ] Priority score calculated using multi-factor rubric
- [ ] Stakeholder importance weighted appropriately
- [ ] Urgency vs importance balanced correctly
- [ ] Business impact assessed based on context
- [ ] Effort vs value ratio considered

**Dependency Mapping:**

- [ ] Blocking dependencies identified (task A blocks task B)
- [ ] Information dependencies captured (task A informs task B)
- [ ] Resource conflicts flagged (same person, multiple tasks)
- [ ] Timeline dependencies noted (coordination required)
- [ ] Critical path identified

**Integration & Export:**

- [ ] Action items formatted correctly for target system (Asana, Todoist, etc.)
- [ ] Subtasks or checklists included where appropriate
- [ ] Context and source meeting linked in task description
- [ ] Tags and labels applied for filtering and search
- [ ] Reminders and tracking configured

## Best Practices

**Extract During Meeting, Not After**
If possible, use real-time extraction during meeting. As commitments are made, AI can surface action items immediately for confirmation. "Before we move on, let me confirm: Sarah, you'll analyze churn by April 15, correct?" This prevents post-meeting ambiguity.

**Confirm Ownership Explicitly**
When AI auto-assigns action items, send confirmation request to assignees within 1 hour. "You've been assigned 3 action items from today's board meeting. Please review and confirm or flag if anything is incorrect." Prevents "I didn't sign up for that" later.

**Use Template Action Item Language**
Train team to use consistent language for commitments: "I will [specific action] by [explicit deadline]." This makes extraction more accurate and reduces ambiguity. Share examples in meeting best practices doc.

**Limit Action Items Per Meeting**
More than 10-15 action items per meeting signals poor meeting focus or lack of prioritization. If extraction yields 20+ items, challenge whether all are truly necessary. Consider breaking into multiple meetings or deprioritizing lower-value work.

**Track Completion Rates by Person**
If someone consistently completes <80% of action items, investigate root cause. Are they over-assigned? Are deadlines unrealistic? Is the work unclear? Use data to improve assignment process, not to punish individuals.

**Escalate Blocked Items Quickly**
If action item is blocked >3 days, auto-escalate to meeting organizer or project lead. Blockers compound quickly—item blocked for 2 weeks often becomes crisis. Early escalation enables early intervention.

**Connect to Goals and Projects**
Tag action items with relevant goals, OKRs, or projects. This provides context (why this matters) and enables rollup reporting (which goals are progressing via action items completed?). Increases motivation and focus.

**Celebrate Completions**
When high-priority action items complete on time, acknowledge it. Send quick thanks or shout-out in Slack. Positive reinforcement increases future follow-through rates. Make accountability about praise for success, not punishment for failure.

## Integration Points

**Meeting Tools:**

- Zoom, Google Meet, Microsoft Teams for transcription and recording
- Otter.ai, Grain, Fireflies for dedicated meeting transcription
- Calendar systems (Google, Outlook, Apple) for meeting metadata and participant lists

**Task Management:**

- Asana, Trello, ClickUp for team project management
- Todoist, Things, Microsoft To-Do for personal task lists
- Jira, Linear for engineering and product development tasks
- Notion, Coda for database-based task tracking

**Communication Platforms:**

- Slack, Microsoft Teams for action item notifications and updates
- Email for action item summaries and reminders
- SMS for urgent deadline reminders

**Document Systems:**

- Google Drive, Dropbox for meeting notes storage and retrieval
- Notion, Confluence for knowledge base and wiki integration
- SharePoint for enterprise document management

**CRM Systems:**

- Salesforce, HubSpot for client-related action items
- Zoho CRM for small business relationship management
- Automatic logging of follow-ups from sales and client meetings

## Success Criteria

**Extraction Accuracy:**

- 95%+ of action items correctly identified and extracted
- <5% false positives (non-action items mistakenly extracted)
- 90%+ owner assignment accuracy (verified by participants)
- 85%+ deadline extraction/inference accuracy

**Completion Rates:**

- 85%+ of extracted action items completed
- 80%+ completed by deadline (on-time completion)
- <10% of items remain open >30 days (stale items)
- <5% of items blocked >7 days without escalation

**Time Efficiency:**

- Action item extraction time: <5 minutes (vs 20-30 minutes manual)
- Export to task management: <2 minutes (automated)
- Participant confirmation: <5 minutes per person (quick review)
- Total time from meeting end to tracked actions: <15 minutes

**User Adoption:**

- 90%+ of team members using action item system consistently
- 85%+ satisfaction with accuracy and usefulness
- <10% manual corrections required per meeting
- Team prefers automated extraction over manual note-taking

**Business Impact:**

- Zero critical commitments dropped (prevented by systematic tracking)
- 2-3 costly mistakes avoided per year ($5-10K each) = $10-30K value
- 8-10 hours/month saved on manual action item tracking = $12K/year value
- Faster project velocity (reduced delays from unclear ownership)

## Common Use Cases

**Use Case 1: Board Meeting Action Items**
Extract commitments from quarterly board meetings where multiple strategic initiatives are discussed. Typical output: 8-15 action items across CEO, CFO, and board members. High-stakes items requiring tracking over 1-3 month timeframes. Critical for accountability and follow-through on board guidance.

**Use Case 2: Sprint Planning Follow-Ups**
Extract engineering tasks and assignments from sprint planning meetings. Connect to Linear or Jira for automatic ticket creation. Typical output: 10-20 engineering tasks with technical dependencies. Enables immediate sprint execution without manual ticket creation.

**Use Case 3: Client Sales Follow-Ups**
Extract next steps from sales discovery calls, demos, and proposal presentations. Typical output: 3-8 items (send proposal, schedule follow-up, intro to reference customer, technical deep-dive). Critical for sales velocity and preventing deals from stalling due to forgotten follow-ups.

**Use Case 4: Team Retrospective Action Items**
Extract process improvements and lessons learned from sprint or project retrospectives. Typical output: 5-10 process changes to implement. Track completion to ensure retrospectives lead to actual improvement, not just discussion.

**Use Case 5: Partnership Negotiation Action Items**
Extract deliverables and next steps from multi-meeting partnership negotiations. Typical output: 4-8 items per meeting across technical integration, legal review, go-to-market planning. Long timeline (weeks to months) requires systematic tracking to maintain momentum.

**Use Case 6: Investor Update Follow-Ups**
Extract commitments from monthly or quarterly investor update calls. Typical output: 3-6 follow-ups (send metrics update, intro to potential customer, provide feedback on pitch deck). Maintains investor relationship through consistent follow-through.

## Troubleshooting

**Problem: AI extracts too many false positives (non-action items)**

- Solution: Tune confidence threshold higher. Only extract items with explicit commitment language or clear owner assignment. Flag low-confidence items for manual review rather than auto-creating tasks.

**Problem: Action items assigned to wrong person**

- Solution: Build participant role profiles (CFO handles finance, CTO handles tech). Use historical assignment patterns from previous meetings. Allow manual override during confirmation phase before export.

**Problem: Deadlines inferred incorrectly**

- Solution: Be conservative with deadline inference. If unclear, suggest 2-week default and flag for manual review. Train team to use explicit deadline language ("by Friday" not "soon").

**Problem: Too many action items generated (overwhelming)**

- Solution: Apply minimum priority threshold (only extract medium+ priority items). Or extract all but separate into "must do" vs "nice to have" categories. Consider whether meeting itself needs better focus.

**Problem: Action items not getting completed despite tracking**

- Solution: Investigate root cause. Are items poorly defined? Deadlines unrealistic? People over-assigned? Use completion analytics to identify pattern and fix process, not just track harder.

**Problem: Extraction misses implicit commitments**

- Solution: Expand extraction patterns to include questions ("do we have data on X?" = action to gather data), concerns raised ("I'm worried about Y" = action to address concern), and discussion gaps ("we should discuss Z" = action to schedule discussion).

**Problem: Integration with task system failing or manual**

- Solution: Use API integrations where available (Asana, Todoist, Jira APIs). If not available, export to CSV or JSON for bulk import. Last resort: Email formatted task list for manual entry (still faster than extracting manually).
