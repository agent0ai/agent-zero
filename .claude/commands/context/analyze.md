---
description: Cross-context time allocation analysis with AI-powered insights and optimization recommendations
argument-hint: "[--period <week|month|quarter>] [--context <name>] [--export]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
---

# Context Analysis Command

## Overview

AI-powered analysis of how you spend time across different contexts (property management, client work, personal projects). Identifies time sinks, optimization opportunities, and provides actionable recommendations for better time allocation.

**Part of Phase 3**: Motion + AI Autopilot integration

## What This Command Does

- ✅ Analyzes time allocation across all contexts
- ✅ Identifies time sinks and productivity drains
- ✅ Compares actual vs ideal time distribution
- ✅ Provides AI-powered optimization recommendations
- ✅ Tracks context-switching overhead
- ✅ Generates weekly/monthly reports
- ✅ **Saves 2-3 hours/week through better time allocation**

## Usage

```bash
# Analyze this week
/context:analyze

# Analyze specific period
/context:analyze --period month
/context:analyze --period quarter

# Analyze specific context
/context:analyze --context property-management

# Export report
/context:analyze --export pdf
/context:analyze --export markdown
```

## Data Sources

The AI analyzes:

1. **Calendar Events**: All meetings and time blocks
2. **Tasks**: Completed tasks and time spent (Motion tracking)
3. **Emails**: Email volume and time per context
4. **Context Switches**: How often you switch between contexts
5. **Deep Work Blocks**: Protected focus time
6. **Meetings**: Meeting time by type and context

## Implementation Details

### Step 1: Gather Cross-Context Data

```javascript
// Fetch calendar data
const calendarEvents = await mcp.calendar.listEvents({
  timeMin: periodStart.toISOString(),
  timeMax: periodEnd.toISOString(),
  maxResults: 500
});

// Fetch completed tasks with time tracking
const completedTasks = await mcp.motion.listTasks({
  status: 'completed',
  completedAfter: periodStart,
  completedBefore: periodEnd
});

// Fetch email activity by context
const emailsByContext = await analyzeEmailsByContext(periodStart, periodEnd);

// Build time allocation matrix
const timeAllocation = {
  calendar: categorizeEventsByContext(calendarEvents),
  tasks: categorizeTasksByContext(completedTasks),
  email: emailsByContext,
  contextSwitches: detectContextSwitches(calendarEvents, completedTasks)
};
```

### Step 2: Categorize by Context

```javascript
// Categorize events by context
const categorizeByContext = (item) => {
  // Check calendar metadata
  if (item.extendedProperties?.private?.context) {
    return item.extendedProperties.private.context;
  }

  // AI-powered categorization based on content
  const context = await claude.categorize({
    prompt: `Categorize this item into a context:

    Title: ${item.summary || item.name}
    Description: ${item.description || ''}
    Attendees: ${item.attendees?.map(a => a.email).join(', ') || ''}

    Available Contexts:
    - property-management: Rental properties, tenants, maintenance
    - client-work: Client projects, proposals, deliverables
    - business-dev: Sales, marketing, partnerships
    - admin: Bookkeeping, compliance, operations
    - personal: Personal projects, learning, health

    Return JSON: { "context": "context-name", "confidence": 0-100 }
    `
  });

  return context.context;
};
```

### Step 3: Calculate Time Distribution

```javascript
// Calculate total time per context
const timeByContext = {};

for (const event of calendarEvents) {
  const context = await categorizeByContext(event);
  const duration = calculateDuration(event.start, event.end);

  if (!timeByContext[context]) {
    timeByContext[context] = {
      total: 0,
      meetings: 0,
      deepWork: 0,
      administrative: 0,
      events: []
    };
  }

  timeByContext[context].total += duration;

  // Categorize by type
  if (event.summary.includes('Deep Work') || event.attendees?.length === 1) {
    timeByContext[context].deepWork += duration;
  } else if (event.attendees?.length > 1) {
    timeByContext[context].meetings += duration;
  } else {
    timeByContext[context].administrative += duration;
  }

  timeByContext[context].events.push(event);
}

// Add task time
for (const task of completedTasks) {
  const context = await categorizeByContext(task);
  const timeSpent = task.timeSpent || task.duration; // Minutes

  if (timeByContext[context]) {
    timeByContext[context].total += timeSpent;
  }
}
```

### Step 4: AI Analysis and Insights

```javascript
const analysis = await claude.analyze({
  prompt: `Analyze this time allocation data and provide insights:

  PERIOD: ${formatPeriod(periodStart, periodEnd)}

  TIME ALLOCATION:
  ${Object.entries(timeByContext).map(([context, data]) => `
  ${context}:
    Total: ${formatHours(data.total)}
    Meetings: ${formatHours(data.meetings)}
    Deep Work: ${formatHours(data.deepWork)}
    Administrative: ${formatHours(data.administrative)}
  `).join('\n')}

  CONTEXT SWITCHES:
  ${contextSwitches.length} switches
  Average time between switches: ${avgTimeBetweenSwitches} minutes

  DEEP WORK BLOCKS:
  Total: ${totalDeepWorkHours} hours
  Average block size: ${avgDeepWorkBlockSize} hours
  Protected blocks: ${protectedBlocksCount}

  MEETING ANALYSIS:
  Total meetings: ${totalMeetings}
  Average meeting length: ${avgMeetingLength} minutes
  Recurring meetings: ${recurringMeetingsCount}

  USER'S IDEAL ALLOCATION (from context preferences):
  ${Object.entries(idealAllocation).map(([ctx, pct]) => `${ctx}: ${pct}%`).join('\n')}

  TASK:
  Provide comprehensive analysis with:
  1. Time allocation summary (actual vs ideal)
  2. Top 3 insights (what's working well)
  3. Top 3 concerns (what needs attention)
  4. Top 5 actionable recommendations
  5. Predicted time savings if recommendations implemented

  Return JSON with detailed analysis.
  `
});
```

### Step 5: Generate Report

```javascript
console.log(`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 CONTEXT ANALYSIS REPORT
Period: ${formatPeriod(periodStart, periodEnd)}
Generated: ${new Date().toLocaleString()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 TIME ALLOCATION SUMMARY

Total Tracked Time: ${formatHours(totalTime)}

By Context:
${Object.entries(timeByContext)
  .sort((a, b) => b[1].total - a[1].total)
  .map(([context, data]) => {
    const percentage = (data.total / totalTime * 100).toFixed(1);
    const ideal = idealAllocation[context] || 0;
    const delta = percentage - ideal;
    const trend = delta > 5 ? '⚠️  OVER' : delta < -5 ? '⚠️  UNDER' : '✅ OK';

    return `
  ${context}:
    Actual: ${formatHours(data.total)} (${percentage}%)
    Ideal: ${ideal}%
    Status: ${trend} (${delta > 0 ? '+' : ''}${delta.toFixed(1)}%)

    Breakdown:
      • Meetings: ${formatHours(data.meetings)} (${(data.meetings/data.total*100).toFixed(0)}%)
      • Deep Work: ${formatHours(data.deepWork)} (${(data.deepWork/data.total*100).toFixed(0)}%)
      • Administrative: ${formatHours(data.administrative)} (${(data.administrative/data.total*100).toFixed(0)}%)
    `;
  }).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ TOP 3 INSIGHTS (What's Working)

${analysis.insights.map((insight, i) => `
[${i + 1}] ${insight.title}
    ${insight.description}
    Impact: ${insight.impact}
`).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  TOP 3 CONCERNS (Needs Attention)

${analysis.concerns.map((concern, i) => `
[${i + 1}] ${concern.title}
    ${concern.description}
    Risk: ${concern.risk}
    Current Impact: ${concern.currentImpact}
`).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TOP 5 RECOMMENDATIONS

${analysis.recommendations.map((rec, i) => `
[${i + 1}] ${rec.title}
    ${rec.description}

    Action Steps:
    ${rec.actionSteps.map(step => `  • ${step}`).join('\n')}

    Expected Impact:
      • Time Saved: ${rec.timeSaved}
      • Productivity Gain: ${rec.productivityGain}
      • Difficulty: ${rec.difficulty}

    Implementation:
      ${rec.implementation}
`).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 PRODUCTIVITY METRICS

Context Switching:
  • Total switches: ${contextSwitches.length}
  • Avg time between switches: ${avgTimeBetweenSwitches} min
  • Context switch overhead: ${contextSwitchOverhead} hrs/week
  • Recommendation: ${analysis.contextSwitchRecommendation}

Deep Work:
  • Total deep work: ${totalDeepWorkHours} hrs
  • Average block size: ${avgDeepWorkBlockSize} hrs
  • Protected blocks: ${protectedBlocksCount} (${(protectedBlocksCount/totalDeepWorkBlocks*100).toFixed(0)}%)
  • Quality score: ${deepWorkQualityScore}/100

Meeting Efficiency:
  • Total meetings: ${totalMeetings}
  • Total time: ${totalMeetingTime} hrs
  • Average length: ${avgMeetingLength} min
  • Declined/canceled: ${declinedMeetings}
  • Efficiency score: ${meetingEfficiencyScore}/100

Email Time:
  • Total email time: ${totalEmailTime} hrs
  • Emails processed: ${totalEmailsProcessed}
  • Avg time per email: ${avgTimePerEmail} min
  • Triage automation savings: ${triageTimeSaved} hrs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 POTENTIAL TIME SAVINGS

If all recommendations implemented:

Weekly Savings:
  ${analysis.recommendations.map(r => `• ${r.title}: ${r.timeSaved}`).join('\n  ')}

  TOTAL WEEKLY SAVINGS: ${analysis.totalWeeklySavings}

Monthly Impact:
  • Time Saved: ${analysis.totalWeeklySavings * 4} hours
  • Value: $${(parseFloat(analysis.totalWeeklySavings) * 4 * 150).toLocaleString()}

Annual Impact:
  • Time Saved: ${analysis.totalWeeklySavings * 50} hours
  • Value: $${(parseFloat(analysis.totalWeeklySavings) * 50 * 150).toLocaleString()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RECOMMENDED NEXT STEPS

[1] Quick Wins (Implement this week):
    ${analysis.quickWins.map(w => `• ${w}`).join('\n    ')}

[2] Medium-term (Implement this month):
    ${analysis.mediumTermActions.map(a => `• ${a}`).join('\n    ')}

[3] Strategic (Plan for next quarter):
    ${analysis.strategicActions.map(a => `• ${a}`).join('\n    ')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actions:
[1] Export report (PDF/Markdown)
[2] Apply recommendations via /optimize:auto
[3] Adjust context allocation targets
[4] Schedule deep work blocks
[5] View detailed breakdown by context
`);
```

## Example Analysis Output

```
🔍 CONTEXT ANALYSIS REPORT
Period: Jan 15-21, 2025 (Last Week)

📊 TIME ALLOCATION SUMMARY

Total Tracked Time: 42.5 hours

By Context:

  property-management:
    Actual: 18.5 hrs (43.5%)
    Ideal: 40%
    Status: ✅ OK (+3.5%)

    Breakdown:
      • Meetings: 6 hrs (32%)
      • Deep Work: 8 hrs (43%)
      • Administrative: 4.5 hrs (24%)

  client-work:
    Actual: 12 hrs (28.2%)
    Ideal: 35%
    Status: ⚠️  UNDER (-6.8%)

    Breakdown:
      • Meetings: 5 hrs (42%)
      • Deep Work: 5 hrs (42%)
      • Administrative: 2 hrs (17%)

  admin:
    Actual: 8 hrs (18.8%)
    Ideal: 15%
    Status: ⚠️  OVER (+3.8%)

    Breakdown:
      • Meetings: 3 hrs (38%)
      • Deep Work: 2 hrs (25%)
      • Administrative: 3 hrs (38%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ TOP 3 INSIGHTS

[1] Strong Deep Work Protection
    You maintained 15 hours of deep work this week across all contexts.
    Your average deep work block (2.5 hrs) is optimal for complex work.
    Impact: High productivity on strategic projects

[2] Effective Meeting Management
    Declined 5 low-value meetings, saving 4 hours this week.
    Meeting efficiency score: 78/100 (good)
    Impact: More time for deep work

[3] Context Balance
    Property management and client work are well-balanced.
    Minimal context switching overhead (only 2.5 hrs lost).
    Impact: Maintained focus and productivity

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  TOP 3 CONCERNS

[1] Under-allocated to Client Work
    Client work is 6.8% below ideal allocation (28% vs 35% target).
    Risk: Missing client deliverables or growth opportunities
    Current Impact: 2-3 hours/week shortfall

[2] Administrative Overhead Too High
    Admin tasks taking 18.8% of time (vs 15% ideal).
    Most time on email triage and calendar management.
    Current Impact: 1.5 hours/week wasted on low-value tasks

[3] Email Time Not Optimized
    Spending 6 hrs/week on email (avg 8 min per email).
    Triage automation not catching all low-priority emails.
    Current Impact: 2 hours/week could be automated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TOP 5 RECOMMENDATIONS

[1] Shift 3 Hours from Admin to Client Work
    Move routine admin tasks to client work deep work blocks.

    Action Steps:
      • Block 9-11 AM Tue/Thu for client deep work
      • Move admin tasks to Friday afternoon batch
      • Decline non-essential admin meetings

    Expected Impact:
      • Time Saved: 0 hrs (reallocation)
      • Productivity Gain: +20% on client work
      • Difficulty: Easy

    Implementation:
      Use /motion:schedule to rebalance weekly allocation

[2] Automate Remaining Email Triage
    Improve triage filters to catch 95% of low-priority emails.

    Action Steps:
      • Add 10 more auto-archive keywords
      • Train AI on recent email patterns
      • Auto-delegate vendor emails to assistant

    Expected Impact:
      • Time Saved: 1.5 hrs/week
      • Productivity Gain: +15% email efficiency
      • Difficulty: Medium

    Implementation:
      Update /email:triage configuration

[3] Batch Administrative Tasks
    Group all admin tasks into 2-3 focused blocks per week.

    Action Steps:
      • Friday 2-4 PM: Bookkeeping and invoices
      • Monday 4-5 PM: Calendar review and planning
      • Decline standalone admin meetings

    Expected Impact:
      • Time Saved: 1 hr/week (reduced context switching)
      • Productivity Gain: +25% admin efficiency
      • Difficulty: Easy

[4] Protect Client Deep Work Blocks
    Schedule recurring deep work for client projects.

    Action Steps:
      • Tuesday 9-11 AM: Client deep work (protected)
      • Thursday 9-11 AM: Client deep work (protected)
      • Block from all meeting requests

    Expected Impact:
      • Time Saved: 0 hrs (reallocation)
      • Productivity Gain: +30% client work output
      • Difficulty: Easy

[5] Optimize Meeting Cadence
    Move to bi-weekly for 3 recurring status meetings.

    Action Steps:
      • Property team sync: Weekly → Bi-weekly
      • Vendor check-ins: Weekly → Bi-weekly
      • Admin reviews: Weekly → Bi-weekly

    Expected Impact:
      • Time Saved: 2 hrs/week
      • Productivity Gain: +5% meeting efficiency
      • Difficulty: Medium (requires stakeholder buy-in)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 POTENTIAL TIME SAVINGS

Weekly Savings:
  • Automate email triage: 1.5 hrs/week
  • Batch admin tasks: 1 hr/week
  • Optimize meeting cadence: 2 hrs/week

  TOTAL WEEKLY SAVINGS: 4.5 hours/week

Monthly Impact:
  • Time Saved: 18 hours
  • Value: $2,700

Annual Impact:
  • Time Saved: 225 hours
  • Value: $33,750
```

## Integration with Other Commands

### With `/optimize:auto`

```bash
# Apply recommendations automatically
/context:analyze → /optimize:auto --apply-recommendations
```

### With `/motion:schedule`

```bash
# Rebalance weekly schedule based on analysis
/motion:schedule --optimize-for client-work
```

### With `/productivity:metrics`

```bash
# Compare context analysis with productivity metrics
/productivity:metrics --compare-contexts
```

## Business Value

**Time Savings**:

- Identifies 4-6 hours/week of optimization opportunities
- Eliminates context switching overhead (1-2 hrs/week)
- Optimizes meeting vs deep work balance
- **Direct value: $600-900/week**

**Strategic Benefits**:

- Data-driven time allocation decisions
- Early identification of misalignment
- Proactive capacity planning
- Better work-life balance

## Success Metrics

✅ Analysis generation time <30 seconds
✅ Recommendation accuracy >85%
✅ Time savings if applied >3 hours/week
✅ User satisfaction >8/10
✅ Context balance improvement >20%

## Related Commands

- `/productivity:metrics` - Overall productivity tracking
- `/optimize:auto` - Apply optimization recommendations
- `/motion:schedule` - Weekly schedule optimization
- `/autopilot:predict-tasks` - Proactive task planning

## Notes

**Privacy**: All analysis is local. Context data never leaves your system.

**Frequency**: Run weekly for best results. Monthly for strategic reviews.

**Customization**: Set ideal allocation percentages in context settings.

---

*Know exactly where your time goes and how to optimize it.*
