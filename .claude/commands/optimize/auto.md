---
description: Continuous AI-powered self-optimization that runs daily to improve productivity automatically
argument-hint: "[--frequency <daily|weekly>] [--auto-apply] [--dry-run]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
---

# Auto-Optimization Command

## Overview

**THE ULTIMATE AUTOPILOT FEATURE**: AI continuously analyzes your productivity system and automatically optimizes it. Runs daily to adjust schedules, improve workflows, predict tasks, and eliminate inefficiencies. This is "set it and forget it" productivity.

**Part of Phase 3**: Motion + AI Autopilot integration

## What This Command Does

- ✅ **Daily automatic execution** (6 AM default)
- ✅ Analyzes yesterday's productivity patterns
- ✅ Adjusts today's schedule for optimal productivity
- ✅ Predicts and creates upcoming tasks
- ✅ Optimizes email triage rules
- ✅ Balances context allocation
- ✅ Protects deep work blocks
- ✅ Learns from your behavior and improves over time
- ✅ **Saves 3-5 hours/week through continuous optimization**

## Usage

```bash
# Run optimization once
/optimize:auto

# Enable daily auto-run
/optimize:auto --enable-daily

# Dry run (preview changes without applying)
/optimize:auto --dry-run

# Auto-apply all recommendations
/optimize:auto --auto-apply

# Weekly deep optimization
/optimize:auto --frequency weekly --deep-analysis
```

## Daily Optimization Workflow

When run automatically at 6 AM every day:

### Step 1: Analyze Yesterday (5 min)

```javascript
// Fetch yesterday's data
const yesterday = {
  tasks: await mcp.motion.listTasks({
    completedAfter: yesterdayStart,
    completedBefore: yesterdayEnd
  }),
  calendar: await mcp.calendar.listEvents({
    timeMin: yesterdayStart,
    timeMax: yesterdayEnd
  }),
  emails: await mcp.gmail.listMessages({
    after: yesterdayTimestamp
  })
};

// AI analyzes productivity
const analysis = await claude.analyzeDailyProductivity({
  prompt: `Analyze yesterday's productivity and identify patterns:

  TASKS COMPLETED:
  ${yesterday.tasks.map(t => `• ${t.name} (${t.duration}m)`).join('\n')}

  TIME ALLOCATION:
  ${categorizeTimeAllocation(yesterday.calendar)}

  EMAIL METRICS:
  • Total emails: ${yesterday.emails.length}
  • Processed: ${yesterday.emails.filter(e => e.labels.includes('INBOX')).length}
  • Auto-archived: ${yesterday.emails.filter(e => e.labels.includes('Auto-Archived')).length}

  WHAT WENT WELL:
  • Task completion rate: ${taskCompletionRate}%
  • Deep work hours: ${deepWorkHours}
  • Email response time: ${avgEmailResponseTime}

  WHAT NEEDS IMPROVEMENT:
  • Context switches: ${contextSwitches}
  • Meeting overrun: ${meetingOverrunMinutes} minutes
  • Unplanned interruptions: ${interruptions}

  Provide:
  1. Top 3 wins from yesterday
  2. Top 3 issues that need fixing
  3. Specific optimizations for today's schedule
  `
});
```

### Step 2: Optimize Today's Schedule (10 min)

```javascript
// Fetch today's schedule
const todaySchedule = await mcp.calendar.listEvents({
  timeMin: todayStart,
  timeMax: todayEnd
});

const todayTasks = await mcp.motion.listTasks({
  scheduledAfter: todayStart,
  scheduledBefore: todayEnd
});

// AI optimizes schedule
const optimizations = await claude.optimizeSchedule({
  prompt: `Optimize today's schedule based on yesterday's analysis:

  YESTERDAY'S LEARNINGS:
  ${JSON.stringify(analysis.learnings, null, 2)}

  TODAY'S SCHEDULE:
  ${formatSchedule(todaySchedule, todayTasks)}

  OPTIMIZATION GOALS:
  • Protect deep work blocks (9-11 AM)
  • Reduce context switching
  • Balance meeting vs focused work
  • Leave buffer time between tasks
  • Respect energy levels (high morning, low afternoon)

  Provide specific schedule adjustments:
  {
    "reschedule": [
      {
        "task": "task_id",
        "currentTime": "10:00 AM",
        "newTime": "2:00 PM",
        "reason": "Move to lower energy time"
      }
    ],
    "protect": ["Deep Work: Client Project"],
    "decline": ["Low-value recurring meeting"],
    "addBuffer": [{"after": "Client Call", "duration": 15}]
  }
  `
});

// Apply optimizations
for (const change of optimizations.reschedule) {
  await mcp.motion.updateTask({
    id: change.task,
    scheduledTime: change.newTime
  });
}

for (const meeting of optimizations.decline) {
  await declineMeetingWithReason(meeting, "Protecting deep work time");
}
```

### Step 3: Predict and Create Tasks (5 min)

```javascript
// Run predictive task generation
const predictions = await runCommand('/autopilot:predict-tasks', {
  period: 'week',
  confidenceThreshold: 70,
  autoCreate: true
});

// Log predictions
console.log(`
✓ Predicted ${predictions.length} upcoming tasks
✓ Auto-created ${predictions.filter(p => p.created).length} high-confidence tasks
✓ Flagged ${predictions.filter(p => p.needsApproval).length} for approval
`);
```

### Step 4: Optimize Email Triage Rules (3 min)

```javascript
// Analyze email triage effectiveness
const triageAnalysis = await analyzeEmailTriage(yesterday.emails);

// AI improves triage rules
const improvedRules = await claude.optimizeTriageRules({
  prompt: `Improve email triage rules based on yesterday's data:

  CURRENT RULES:
  ${JSON.stringify(currentTriageRules, null, 2)}

  YESTERDAY'S EMAIL TRIAGE:
  • Auto-archived: ${triageAnalysis.autoArchived} emails
  • False positives (important emails archived): ${triageAnalysis.falsePositives}
  • False negatives (spam not caught): ${triageAnalysis.falseNegatives}
  • Manual overrides: ${triageAnalysis.manualOverrides}

  PATTERNS OBSERVED:
  ${triageAnalysis.patterns}

  Suggest rule improvements to:
  1. Reduce false positives (never miss important emails)
  2. Catch more low-priority emails automatically
  3. Add new senders to urgent list
  4. Update keyword filters

  Return updated triage rules JSON.
  `
});

// Apply improved rules
await updateTriageRules(improvedRules);
```

### Step 5: Balance Context Allocation (5 min)

```javascript
// Run context analysis
const contextAnalysis = await runCommand('/context:analyze', {
  period: 'week',
  export: false
});

// AI rebalances if needed
if (contextAnalysis.hasImbalance) {
  const rebalancing = await claude.rebalanceContexts({
    prompt: `Rebalance context allocation for this week:

    CURRENT ALLOCATION (This Week So Far):
    ${formatContextAllocation(contextAnalysis.current)}

    IDEAL ALLOCATION:
    ${formatContextAllocation(contextAnalysis.ideal)}

    DELTA:
    ${formatContextDelta(contextAnalysis.delta)}

    Suggest specific actions to rebalance:
    • Which tasks to reschedule
    • Which meetings to decline/delegate
    • Where to add deep work blocks
    • Context to prioritize today
    `
  });

  // Apply rebalancing
  await applyContextRebalancing(rebalancing);
}
```

### Step 6: Generate Daily Brief (2 min)

```javascript
// Compile daily brief
const dailyBrief = {
  date: new Date().toLocaleDateString(),
  yesterdayAnalysis: analysis,
  todayOptimizations: optimizations,
  predictedTasks: predictions,
  contextBalance: contextAnalysis,
  recommendations: generateRecommendations(analysis, optimizations)
};

// Display brief
console.log(`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI AUTO-OPTIMIZATION DAILY BRIEF
${dailyBrief.date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 YESTERDAY'S PERFORMANCE

Top Wins:
  ${analysis.wins.map(w => `✅ ${w}`).join('\n  ')}

Areas Improved:
  ${analysis.improvements.map(i => `📈 ${i}`).join('\n  ')}

Issues Fixed Automatically:
  ${optimizations.fixed.map(f => `🔧 ${f}`).join('\n  ')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 TODAY'S OPTIMIZATIONS APPLIED

Schedule Adjustments:
  ${optimizations.reschedule.map(r => `• ${r.task}: ${r.currentTime} → ${r.newTime}\n    Reason: ${r.reason}`).join('\n  ')}

Protected Time Blocks:
  ${optimizations.protect.map(p => `• ${p}`).join('\n  ')}

Meetings Declined:
  ${optimizations.decline.map(m => `• ${m}`).join('\n  ')}

Buffer Time Added:
  ${optimizations.addBuffer.map(b => `• ${b.duration}m after ${b.after}`).join('\n  ')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔮 TASKS PREDICTED & CREATED

High Confidence (Auto-Created):
  ${predictions.filter(p => p.created).map(p => `• ${p.task} (${p.confidence}% confidence)\n    Deadline: ${p.deadline}`).join('\n  ')}

Needs Your Review:
  ${predictions.filter(p => p.needsApproval).map(p => `• ${p.task} (${p.confidence}% confidence)\n    Reasoning: ${p.reasoning}`).join('\n  ')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 EMAIL TRIAGE IMPROVEMENTS

Rules Updated:
  ${improvedRules.updates.map(u => `• ${u.description}`).join('\n  ')}

Expected Impact:
  • ${improvedRules.expectedImpact.additionalEmailsFiltered} more emails auto-filtered
  • ${improvedRules.expectedImpact.timeSaved} min/day saved

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚖️  CONTEXT BALANCE

${contextAnalysis.hasImbalance ? `
Current Imbalance Detected:
  ${contextAnalysis.imbalances.map(i => `• ${i.context}: ${i.delta}% ${i.direction}`).join('\n  ')}

Rebalancing Actions Taken:
  ${rebalancing.actions.map(a => `• ${a}`).join('\n  ')}
` : '
✅ Contexts well-balanced this week
'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 AI RECOMMENDATIONS FOR TODAY

${dailyBrief.recommendations.map((rec, i) => `
[${i + 1}] ${rec.title}
    ${rec.description}
    Impact: ${rec.impact}
`).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 OPTIMIZATION IMPACT

Time Saved Today: ${calculateTimeSaved(optimizations)} hours
Productivity Boost: +${calculateProductivityBoost(optimizations)}%

Weekly Impact So Far:
  • Total time saved: ${weeklyTimeSaved} hours
  • Tasks auto-created: ${weeklyTasksCreated}
  • Meetings optimized: ${weeklyMeetingsOptimized}
  • Email time reduced: ${weeklyEmailTimeSaved} hours

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 STATUS: Your productivity system is optimized and ready!

Next auto-optimization: Tomorrow at 6:00 AM
`);
```

## Daily Execution Setup

### Add to Morning Routine

```bash
# Edit morning routine script
# File: automation/scripts/morning/daily-routine.sh

# Add after email triage
log "Step 7: Running AI auto-optimization..."
/optimize:auto --auto-apply 2>/dev/null || log "Auto-optimization skipped"
```

### Cron Job Setup

```bash
# Run daily at 6 AM
0 6 * * * /usr/local/bin/claude /optimize:auto --auto-apply >> ~/logs/auto-optimize.log 2>&1
```

## Weekly Deep Optimization

Run every Sunday for strategic optimization:

```bash
# Weekly deep analysis
/optimize:auto --frequency weekly --deep-analysis
```

**Weekly optimization includes**:

- Full context rebalancing
- Long-term pattern analysis
- Strategic task prediction (next month)
- Email triage rule overhaul
- Meeting cadence optimization
- Deep work block optimization
- Learning from 4-week trends

## Auto-Apply vs Manual Review

### Auto-Apply Mode (Recommended)

```bash
# AI makes all changes automatically
/optimize:auto --auto-apply
```

**What gets auto-applied**:

- ✅ Schedule optimizations (reschedule tasks)
- ✅ Email triage rule updates
- ✅ High-confidence task predictions (>85%)
- ✅ Buffer time additions
- ✅ Deep work protection

**What requires approval**:

- ⚠️  Meeting declines (notification sent)
- ⚠️  Medium-confidence tasks (70-84%)
- ⚠️  Major context rebalancing (>20% shift)

### Manual Review Mode

```bash
# Preview all changes first
/optimize:auto --dry-run
```

Shows all proposed changes and asks for approval before applying.

## Learning and Improvement

The AI learns from:

1. **Your Preferences**:
   - Which optimizations you accept vs reject
   - Preferred work patterns and schedules
   - Meeting acceptance/decline patterns
   - Email categorization corrections

2. **Productivity Outcomes**:
   - Task completion rates after optimizations
   - Deep work quality scores
   - Meeting effectiveness ratings
   - Email response times

3. **Behavioral Patterns**:
   - When you actually do deep work
   - Which tasks you procrastinate on
   - Energy level fluctuations
   - Context switching frequency

4. **Feedback**:
   - Manual schedule adjustments (learns preferences)
   - Task prediction corrections
   - Email triage overrides
   - Context allocation changes

**Result**: System gets smarter every day, continuously improving recommendations.

## Business Value

**Time Savings**:

- Daily optimization: 30 min saved per day = 2.5 hrs/week
- Predictive task creation: 30 min/week
- Email triage improvement: 30 min/week
- Context rebalancing: 1 hr/week
- **Total: 4.5-5 hours/week**

**Quality Improvements**:

- Proactive vs reactive (never miss recurring tasks)
- Optimal schedule adherence
- Protected deep work time
- Reduced context switching
- Better work-life balance

**ROI**:

- Weekly time saved: 4.5 hours
- Weekly value: $675 (at $150/hr)
- Annual value: $33,750
- **Investment**: 30 min setup
- **Payback**: Immediate

## Success Metrics

✅ Daily optimization time <5 minutes
✅ Auto-apply success rate >90%
✅ Manual override rate <10%
✅ Time saved >3 hours/week
✅ User satisfaction >9/10
✅ System continuously improving (learning curve)

## Advanced Configuration

### Custom Optimization Goals

```json
{
  "optimization_goals": {
    "maximize_deep_work": true,
    "minimize_meetings": true,
    "protect_mornings": true,
    "batch_similar_tasks": true,
    "respect_energy_levels": true,
    "work_life_balance": 0.8
  },
  "auto_apply_thresholds": {
    "schedule_changes": 0.8,
    "task_predictions": 0.85,
    "email_rules": 0.9,
    "meeting_declines": 0.95
  }
}
```

### Optimization Frequency

```bash
# Multiple runs per day
/optimize:auto --frequency 3x-daily  # 6 AM, 12 PM, 6 PM

# Real-time optimization (experimental)
/optimize:auto --real-time  # Optimizes as events occur
```

## Integration with All Phase 1-3 Commands

Auto-optimization orchestrates ALL productivity commands:

- `/email:triage` - Optimizes triage rules
- `/calendar:sync-tasks` - Optimizes task scheduling
- `/motion:task` - Creates predicted tasks
- `/motion:schedule` - Optimizes weekly schedule
- `/schedule:smart` - Finds optimal meeting times
- `/email:smart-reply` - Learns email patterns
- `/context:analyze` - Balances context allocation
- `/autopilot:predict-tasks` - Proactive task creation

**Result**: Complete productivity autopilot.

## Monitoring and Logs

```bash
# View optimization log
tail -f ~/logs/auto-optimize.log

# View weekly summary
/optimize:auto --summary week

# View optimization history
/optimize:auto --history month
```

## Troubleshooting

### Too Aggressive Optimizations

```bash
# Reduce auto-apply threshold
/optimize:auto --threshold 0.95  # Only very high confidence

# Disable specific optimizations
/optimize:auto --disable meeting-declines,context-rebalancing
```

### Not Optimizing Enough

```bash
# More aggressive optimization
/optimize:auto --aggressive

# Lower confidence threshold
/optimize:auto --threshold 0.7
```

## Related Commands

- `/productivity:metrics` - Track optimization impact
- `/context:analyze` - Detailed time allocation analysis
- `/autopilot:predict-tasks` - Proactive task prediction
- `/motion:schedule` - Weekly schedule optimization

## Notes

**Learning Period**: AI needs 2-4 weeks to learn your patterns well. Effectiveness improves over time.

**Privacy**: All optimization is local. No data sent to external servers.

**Fallback**: If optimization fails, system maintains current schedule (safe by default).

**Override**: You can always manually override AI decisions. System learns from overrides.

---

*Set it once. Forget it. Your productivity system optimizes itself every day.*
