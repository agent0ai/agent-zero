---
description: AI predicts upcoming tasks and deadlines based on patterns and creates them proactively
argument-hint: "[--period <week|month|quarter>] [--confidence <threshold>]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# Autopilot Predict Tasks Command

## Overview

**ULTIMATE PRODUCTIVITY FEATURE**: AI analyzes your patterns and proactively predicts upcoming tasks before you think of them.

**Part of Phase 3**: AI Autopilot features

## What This Command Does

- ✅ Analyzes historical patterns (emails, calendar, tasks)
- ✅ Predicts upcoming needs (lease renewals, reports, deadlines)
- ✅ Creates tasks automatically with AI-estimated deadlines
- ✅ Schedules via Motion AI for optimal completion
- ✅ Learns from your corrections and feedback
- ✅ **Saves 2-3 hours/week** in planning

## Usage

```bash
# Predict this week's tasks
/autopilot:predict-tasks

# Predict next month
/autopilot:predict-tasks --period month

# Only high-confidence predictions
/autopilot:predict-tasks --confidence 80

# Preview without creating
/autopilot:predict-tasks --dry-run
```

## AI Prediction Engine

```javascript
// Analyze patterns
const predictions = await claude.predictTasks({
  prompt: `Analyze these data sources and predict upcoming tasks:

  CALENDAR PATTERNS:
  - Monthly team meetings (last Friday of month)
  - Quarterly board meetings (every 3 months)
  - Client check-ins (every 2 weeks)

  EMAIL PATTERNS:
  - Invoice reminders (1st of month)
  - Report requests (deadline: 5th of month)
  - Lease renewals (90 days before expiry)

  TASK HISTORY:
  - Monthly financial reconciliation (completed last 12 months)
  - Quarterly tax estimates (completed last 4 quarters)
  - Weekly property inspections (every Thursday)

  CURRENT DATE: ${new Date().toISOString()}
  PREDICT FOR: Next ${period}

  For each prediction, provide:
  {
    "task": "Clear task description",
    "reasoning": "Why this is predicted",
    "deadline": "Estimated deadline",
    "confidence": 0-100,
    "recurrence": "one-time|weekly|monthly|quarterly",
    "priority": "low|medium|high",
    "estimatedDuration": "2 hours"
  }
  `
});
```

## Example Predictions

```
🤖 AI AUTOPILOT: Task Predictions for Next Week

Found 8 predicted tasks (confidence >70%)

HIGH CONFIDENCE (90-100%)
[1] 95% - Prepare Q1 Financial Report
    Reasoning: Completed same time last 4 quarters
    Deadline: Feb 5, 2025 (in 2 weeks)
    Duration: 4 hours
    Pattern: Quarterly on 5th of month
    ✓ Auto-created in Motion

[2] 92% - Monthly Team Meeting Agenda
    Reasoning: Last Friday of month pattern
    Deadline: Jan 31, 2025 (in 9 days)
    Duration: 1 hour
    Pattern: Monthly recurring
    ✓ Auto-created in Motion

[3] 90% - Send Invoice to Client Acme
    Reasoning: Monthly on 1st, last sent Dec 1
    Deadline: Feb 1, 2025 (in 10 days)
    Duration: 30 minutes
    Pattern: Monthly recurring
    ✓ Auto-created in Motion

MEDIUM CONFIDENCE (70-89%)
[4] 85% - Property Inspection - 123 Main St
    Reasoning: Every Thursday pattern
    Deadline: Jan 23, 2025 (tomorrow)
    Duration: 2 hours
    Pattern: Weekly recurring
    ✓ Auto-created in Motion

[5] 78% - Client Check-in Call - Acme Corp
    Reasoning: Bi-weekly pattern, last call Jan 8
    Deadline: Jan 22, 2025 (today!)
    Duration: 30 minutes
    Pattern: Bi-weekly
    ✓ Auto-created in Motion

[6] 75% - Quarterly Tax Estimate Payment
    Reasoning: Jan 15 deadline approaching
    Deadline: Jan 15, 2025 (OVERDUE!)
    Duration: 1 hour
    Priority: HIGH (deadline passed)
    🔴 URGENT: Create now

[7] 72% - Lease Renewal Notice - Unit 2B
    Reasoning: 90 days before lease expiry (Apr 15)
    Deadline: Jan 30, 2025 (in 8 days)
    Duration: 2 hours
    Pattern: One-time
    ⚠️  Approval needed (affects tenant)

LOW CONFIDENCE (60-69%)
[8] 65% - Annual Insurance Review
    Reasoning: Completed last January
    Deadline: Jan 31, 2025 (in 9 days)
    Duration: 3 hours
    Pattern: Annual
    ⏸️  Skipped (confidence too low)

SUMMARY:
  ✓ 5 tasks auto-created in Motion
  ⚠️  1 urgent task (overdue deadline)
  🔔 1 task needs approval
  ⏸️  1 task skipped (low confidence)

All auto-created tasks:
  • Scheduled by Motion AI
  • Added to Google Calendar
  • Synced to Notion & Trello
  • Notification sent

Next Autopilot Run: Tomorrow at 6 AM

Actions:
[1] Approve pending tasks
[2] Adjust predictions
[3] View schedule
[4] Train AI (mark incorrect predictions)
```

## Pattern Learning

The AI learns from:

1. **Calendar events**: Recurring patterns, meeting frequencies
2. **Email analysis**: Recurring requests, deadline patterns
3. **Completed tasks**: Historical completion dates
4. **Business cycles**: Monthly/quarterly/annual rhythms
5. **Context patterns**: Property-specific, client-specific cycles

### Examples of Learned Patterns

```
Lease Renewals:
  Pattern: 90 days before lease expiry
  Confidence: 98%
  Source: 12 past renewals, all sent 90 days prior

Monthly Reports:
  Pattern: 5th of each month
  Confidence: 95%
  Source: Completed last 18 months on 5th

Client Check-ins:
  Pattern: Every 2 weeks, Tuesdays 2 PM
  Confidence: 92%
  Source: Calendar history shows bi-weekly pattern

Property Inspections:
  Pattern: Weekly, Thursdays 10 AM
  Confidence: 90%
  Source: Task completion history
```

## Integration with Other Commands

### With /motion:task

Predictions auto-create Motion tasks:

```bash
# Autopilot predicts task
→ Creates Motion task automatically
→ Motion AI schedules optimally
→ Syncs to all tools
```

### With /email:smart-reply

Proactive email prep:

```bash
# Predicts: "Client check-in call tomorrow"
→ Prepares draft email for follow-up
→ Ready to send after call
```

### With /optimize:auto

Continuous improvement:

```bash
# Daily autopilot predictions
→ Continuous schedule optimization
→ Proactive task creation
→ Never miss recurring tasks
```

## Business Value

**Time Savings**:

- Manual planning: 30-60 min/week
- Autopilot predictions: Automatic
- **Saves 2-3 hours/week**

**Productivity Gains**:

- Never miss recurring tasks
- Proactive vs reactive
- Optimal deadline spacing
- Reduced mental load

**Prediction Accuracy**:

- 90%+ for high-confidence (>85%)
- 75%+ for medium-confidence (70-84%)
- Improves over time with feedback

## Success Metrics

✅ Prediction accuracy >80%
✅ False positive rate <15%
✅ Task creation time <5 seconds
✅ User satisfaction >8/10
✅ Missed recurring tasks: 0

## Training the AI

```bash
# Mark prediction as incorrect
/autopilot:predict-tasks --feedback incorrect --task-id pred_123

# Suggest missing pattern
/autopilot:predict-tasks --add-pattern "Weekly team lunch, Fridays 12pm"

# View learned patterns
/autopilot:predict-tasks --show-patterns
```

## Related Commands

- `/motion:task` - AI-scheduled tasks
- `/optimize:auto` - Continuous optimization
- `/calendar:sync-tasks` - Task → Calendar sync

## Notes

**Learning Period**: AI needs 2-4 weeks to learn your patterns.

**Accuracy**: Improves from 60% → 90%+ over 3 months.

**Cost**: ~$0.10-0.20 per prediction run (AI analysis).

---

*Never forget a recurring task again. AI predicts and creates them for you.*
