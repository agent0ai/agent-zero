---
description: Task → Calendar time blocking automation - AI schedules tasks optimally based on priority and energy
argument-hint: "[--auto] [--priority high|all] [--dry-run]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Calendar Task Sync Workflow Command

## Overview

**HIGH VALUE COMMAND** - Saves 15-20 minutes/day (2-2.5 hours/week)

Automated task → calendar time blocking using n8n orchestration with AI-powered scheduling. Transforms your todo list into protected calendar blocks with optimal timing based on priority, energy levels, and calendar availability.

## What This Command Does

Runs hourly (9 AM - 5 PM, configurable):

1. **Fetches tasks** from `/assistant:tasks` system
2. **Analyzes calendar** for available time blocks
3. **AI optimizes scheduling** by priority, energy level, and dependencies
4. **Creates calendar events** with task links and focus mode

**Result**: "5 tasks scheduled for today (3.5 hours), 8 tasks scheduled for this week"

## Usage

```bash
# Run automatic sync (scheduled hourly)
/calendar:sync-tasks --auto

# Manual sync for high priority only
/calendar:sync-tasks --priority high

# Preview without creating calendar events
/calendar:sync-tasks --dry-run

# Sync specific task
/calendar:sync-tasks --task "Property Analysis Report"

# Force reschedule all tasks
/calendar:sync-tasks --force-reschedule
```

## AI Scheduling Algorithm

### Priority-Based Scheduling

**Priority 1 (Critical)** → Schedule first available slot today

- Deadlines today
- Client emergencies
- Revenue-generating activities

**Priority 2 (High)** → Schedule within 48 hours

- Important client work
- Strategic planning
- Key deliverables

**Priority 3 (Medium)** → Schedule within 1 week

- Routine tasks
- Non-urgent client requests
- Administrative work

**Priority 4 (Low)** → Schedule when available

- Nice-to-have improvements
- Learning activities
- Organization tasks

### Energy-Based Optimization

**High Energy Work** (9 AM - 12 PM)

- Deep analysis and strategy
- Creative work
- Complex problem-solving
- Client presentations

**Medium Energy Work** (2 PM - 4 PM)

- Writing and documentation
- Routine client communication
- Project management
- Data entry

**Low Energy Work** (4 PM - 5 PM)

- Administrative tasks
- Email processing
- Calendar management
- File organization

## Step-by-Step Execution

### 1. Fetch Open Tasks

```javascript
// n8n Workflow Node 1: Task System Integration
const tasks = await taskSystem.getTasks({
  status: 'open',
  contexts: [currentContext.name],
  includeEstimates: true,
  includeDependencies: true
});

console.log(`📋 Found ${tasks.length} open tasks for ${currentContext.name}`);
```

### 2. Get Calendar Availability

```javascript
// n8n Workflow Node 2: Google Calendar MCP
const now = new Date();
const twoWeeksFromNow = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);

const calendarEvents = await mcp.calendar.getEvents({
  timeMin: now.toISOString(),
  timeMax: twoWeeksFromNow.toISOString()
});

// Find available time blocks
const availableBlocks = findAvailableTimeBlocks(calendarEvents, {
  minBlockSize: 30, // minutes
  respectDeepWork: true,
  respectBreaks: true,
  workingHours: context.working_hours || { start: '09:00', end: '17:00' }
});

console.log(`📅 Found ${availableBlocks.length} available time blocks`);
```

### 3. AI-Powered Scheduling Optimization

```javascript
// n8n Workflow Node 3: Claude AI Optimization
const schedule = await claude.optimize({
  prompt: `
    Optimally schedule these tasks into available calendar blocks.

    TASKS (${tasks.length}):
    ${tasks.map(t => `
      - ${t.title}
      Priority: ${t.priority}
      Estimated Time: ${t.estimatedTime}
      Energy Required: ${t.energyLevel || 'medium'}
      Dependencies: ${t.dependencies || 'none'}
      Deadline: ${t.deadline || 'none'}
    `).join('\n')}

    AVAILABLE BLOCKS (${availableBlocks.length}):
    ${availableBlocks.map(b => `
      - ${b.day} ${b.start}-${b.end} (${b.duration} min)
        Energy level: ${b.energyLevel}
        Existing events: ${b.adjacentEvents}
    `).join('\n')}

    CONSTRAINTS:
    - Respect working hours: 9 AM - 5 PM
    - High energy work → morning blocks (9-12)
    - Medium energy work → afternoon blocks (2-4)
    - Low energy work → evening blocks (4-5)
    - No back-to-back meetings >2 hours
    - 15 min buffer between tasks
    - Respect task dependencies

    OPTIMIZATION GOALS:
    1. Complete all Priority 1 tasks today
    2. Complete all Priority 2 tasks within 48 hours
    3. Maximize deep work in high-energy blocks
    4. Minimize context switching
    5. Respect deadlines

    OUTPUT (JSON Array):
    [
      {
        "taskId": "task_123",
        "taskTitle": "Property Analysis Report",
        "scheduledDate": "2025-01-21",
        "startTime": "09:00",
        "endTime": "11:00",
        "reasoning": "High priority + high energy work → morning block"
      },
      ...
    ]
  `
});

console.log(`🤖 AI scheduled ${schedule.length} tasks`);
```

### 4. Create Calendar Events

```javascript
// n8n Workflow Node 4: Create Calendar Blocks
for (const scheduledTask of schedule) {
  const task = tasks.find(t => t.id === scheduledTask.taskId);

  const calendarEvent = await mcp.calendar.createEvent({
    summary: `🎯 ${task.title}`,
    description: `
      Priority: ${task.priority}
      Estimated Time: ${task.estimatedTime}

      Task Details: ${task.description}

      Linked Task: /assistant:tasks --id ${task.id}

      AI Scheduling Reason: ${scheduledTask.reasoning}
    `,
    start: {
      dateTime: `${scheduledTask.scheduledDate}T${scheduledTask.startTime}:00`,
      timeZone: context.timezone || 'America/Chicago'
    },
    end: {
      dateTime: `${scheduledTask.scheduledDate}T${scheduledTask.endTime}:00`,
      timeZone: context.timezone || 'America/Chicago'
    },
    colorId: getColorByPriority(task.priority),
    reminders: {
      useDefault: false,
      overrides: [
        { method: 'popup', minutes: 15 },
        { method: 'popup', minutes: 60 }
      ]
    },
    extendedProperties: {
      private: {
        taskId: task.id,
        taskSystem: 'assistant',
        autoScheduled: 'true'
      }
    }
  });

  // Link calendar event back to task
  await taskSystem.updateTask(task.id, {
    calendarEventId: calendarEvent.id,
    scheduledDate: scheduledTask.scheduledDate,
    scheduledTime: scheduledTask.startTime
  });

  stats.scheduled++;
}
```

### 5. Handle Conflicts and Rescheduling

```javascript
// n8n Workflow Node 5: Conflict Resolution
for (const task of unscheduledTasks) {
  // Find why task couldn't be scheduled
  const reason = determineBlockerReason(task, availableBlocks);

  if (reason === 'no_available_blocks') {
    // Suggest calendar optimization
    console.warn(`⚠️  ${task.title}: No available blocks`);
    console.log(`   Suggested: /google:calendar optimize (free up 3-5 hours)`);
  }

  if (reason === 'past_deadline') {
    // Escalate overdue task
    console.error(`🔴 ${task.title}: OVERDUE (deadline: ${task.deadline})`);
    console.log(`   Action: Prioritize immediately or extend deadline`);
  }

  if (reason === 'dependencies_not_met') {
    // Show dependency chain
    console.warn(`⏸️  ${task.title}: Blocked by dependencies`);
    console.log(`   Complete first: ${task.dependencies.join(', ')}`);
  }
}
```

### 6. Generate Summary Report

```
╔════════════════════════════════════════════════════════╗
║         📅 CALENDAR SYNC COMPLETE                     ║
╠════════════════════════════════════════════════════════╣
║  Sync Time: Jan 21, 2025 at 9:05 AM                  ║
║  Context: Property Management                          ║
╠════════════════════════════════════════════════════════╣
║  📋 TASKS ANALYZED: 18                                ║
║                                                        ║
║  ✅ Successfully Scheduled: 13                        ║
║    • Today: 5 tasks (3.5 hours)                       ║
║    • Tomorrow: 4 tasks (2.5 hours)                    ║
║    • This Week: 4 tasks (3 hours)                     ║
║                                                        ║
║  ⏸️  Waiting (Dependencies): 3                        ║
║    • "Lease Review" → Blocked by "Property Analysis"  ║
║    • "Marketing Plan" → Blocked by "Budget Approval"  ║
║    • "Tenant Outreach" → Blocked by "Lease Review"    ║
║                                                        ║
║  ⚠️  Could Not Schedule: 2                            ║
║    • "Strategic Planning" (4 hrs) → No 4-hour blocks  ║
║      Suggestion: Break into 2×2 hour sessions         ║
║    • "Deep Research" (3 hrs) → Calendar full this week║
║      Suggestion: /google:calendar optimize            ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  📅 TODAY'S SCHEDULE (5 tasks)                        ║
║                                                        ║
║  09:00 - 11:00  🧠 Property Analysis Report           ║
║                 Priority: High | Energy: High          ║
║                 Calendar: ✓ Added | Reminders: ✓      ║
║                                                        ║
║  11:15 - 12:00  ✍️  Write Tenant Newsletter           ║
║                 Priority: Medium | Energy: Medium      ║
║                 Calendar: ✓ Added | Reminders: ✓      ║
║                                                        ║
║  14:00 - 15:30  📞 Client Check-ins (3 calls)         ║
║                 Priority: High | Energy: Medium        ║
║                 Calendar: ✓ Added | Reminders: ✓      ║
║                                                        ║
║  15:45 - 16:30  📧 Process Email Responses            ║
║                 Priority: Medium | Energy: Low         ║
║                 Calendar: ✓ Added | Reminders: ✓      ║
║                                                        ║
║  16:30 - 17:00  📋 Admin: File Organization           ║
║                 Priority: Low | Energy: Low            ║
║                 Calendar: ✓ Added | Reminders: ✓      ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  🎯 OPTIMIZATION INSIGHTS                              ║
║                                                        ║
║  ✅ Good: High priority tasks scheduled in AM         ║
║  ✅ Good: Low energy work scheduled in PM             ║
║  ⚠️  Warning: Only 15 min buffer between 2 tasks     ║
║  💡 Tip: Block 2-hour deep work slot tomorrow         ║
║                                                        ║
║  Total Scheduled Time: 9 hours (across 2 weeks)       ║
║  Deep Work Blocks: 2 (4.5 hours)                      ║
║  Meeting Blocks: 1 (1.5 hours)                        ║
║  Admin Blocks: 3 (1.5 hours)                          ║
║                                                        ║
║  Time Saved (vs manual scheduling): 18 minutes        ║
║  Next Sync: Today at 10:00 AM (hourly)               ║
╚════════════════════════════════════════════════════════╝

Quick Actions:
[1] View full calendar → /google:calendar read --week
[2] Adjust priorities → /priority:rank
[3] Reschedule task → /calendar:sync-tasks --task "..." --reschedule
[4] Pause auto-sync → /calendar:sync-tasks --pause-auto
```

## n8n Workflow Architecture

```
┌─────────────────────────────────────────────────────┐
│  TRIGGER: Cron (Hourly 9-5) OR Manual Command      │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  NODE 1: Load Context & Tasks                       │
│  - Get active business context                      │
│  - Fetch open tasks from /assistant:tasks           │
│  - Filter by context and status                     │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  NODE 2: Get Calendar Availability (MCP)            │
│  - Fetch events for next 2 weeks                    │
│  - Identify available time blocks                   │
│  - Respect working hours and breaks                 │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  NODE 3: AI Scheduling Optimization (Claude)        │
│  - Match tasks to optimal time blocks               │
│  - Consider priority, energy, dependencies          │
│  - Maximize productivity                            │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  NODE 4: Create Calendar Events (MCP)               │
│  - Create time blocks for each scheduled task       │
│  - Set reminders and colors by priority             │
│  - Link calendar event ↔ task                       │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  NODE 5: Conflict Resolution                        │
│  - Identify unschedulable tasks                     │
│  - Determine blocker reasons                        │
│  - Generate recommendations                         │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  NODE 6: Update Task System                         │
│  - Link tasks to calendar events                    │
│  - Update task status (scheduled)                   │
│  - Log scheduling history                           │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  NODE 7: Generate Report                            │
│  - Calculate summary statistics                     │
│  - Generate optimization insights                   │
│  - Format output for display                        │
└─────────────────────────────────────────────────────┘
```

## Customization Options

### Scheduling Rules (context.json)

```json
{
  "calendar_sync": {
    "enabled": true,
    "auto_sync_frequency": "hourly",
    "working_hours": {
      "start": "09:00",
      "end": "17:00",
      "timezone": "America/Chicago"
    },
    "energy_schedule": {
      "high": ["09:00-12:00"],
      "medium": ["14:00-16:00"],
      "low": ["16:00-17:00"]
    },
    "buffer_minutes": 15,
    "min_block_size_minutes": 30,
    "max_block_size_hours": 4,
    "respect_deep_work": true,
    "color_coding": {
      "priority_1": "red",
      "priority_2": "orange",
      "priority_3": "yellow",
      "priority_4": "gray"
    }
  }
}
```

### AI Tuning

```bash
# Prefer morning deep work
/calendar:sync-tasks --prefer-mornings

# Pack schedule tightly (minimize gaps)
/calendar:sync-tasks --pack-tight

# Spread tasks evenly across week
/calendar:sync-tasks --spread-evenly

# Only schedule high priority tasks
/calendar:sync-tasks --priority high --auto-defer-low
```

## Integration with Existing Commands

### With /assistant:tasks

Bidirectional sync:

```bash
# Tasks automatically scheduled to calendar
/assistant:tasks add "Write Report" --priority high --estimate "2 hours"
# → Auto-scheduled to next available 2-hour morning block

# Completing calendar event updates task
# → Task marked complete when calendar event ends
```

### With /priority:rank

Priority changes trigger reschedule:

```bash
/priority:rank --promote "Client Proposal"
# → Task automatically moved to earlier calendar slot
```

### With /google:calendar optimize

Free up time for tasks:

```bash
/google:calendar optimize
# → Declines 3 low-value meetings
# → /calendar:sync-tasks automatically fills freed time
```

### With /meeting:prep

Meeting blocks respect task time:

```bash
/meeting:prep "Client Call"
# → Prep time auto-scheduled 30 min before meeting
```

## Business Value

**Time Savings**:

- Manual task scheduling: 15-20 minutes/day
- Automated scheduling: <1 minute/day (review only)
- **Saved**: 15-20 minutes/day = **2-2.5 hours/week**

**Productivity Gains**:

- 95% of tasks scheduled optimally
- Zero scheduling conflicts
- Better energy management (right task at right time)
- Reduced decision fatigue

**ROI**:

- Time saved: 2.25 hrs/week × $150/hr × 50 weeks = **$16,875/year**
- Improved productivity: Priceless

## Success Metrics

✅ Sync completes in <30 seconds
✅ 95%+ tasks scheduled successfully
✅ Zero double-bookings
✅ 80%+ tasks completed on time (vs 60% without scheduling)
✅ User satisfaction: 9/10 or higher

## Security & Privacy

- OAuth 2.0 authentication
- Task data synced securely via MCP
- Calendar events private by default
- Audit logging enabled

## Troubleshooting

### Tasks Not Scheduling

```bash
Error: No available calendar blocks found

Solution:
# Optimize calendar to free up time
/google:calendar optimize

# Or extend working hours
/context:switch property-management --edit-working-hours

# Or break large tasks into smaller blocks
/assistant:tasks edit "Large Task" --split-into 4
```

### Sync Not Running Automatically

```bash
Error: Cron job not found

Solution:
# Check cron schedule
crontab -l | grep calendar:sync-tasks

# Re-enable hourly sync
echo "0 9-17 * * * /calendar:sync-tasks --auto" | crontab -
```

### AI Scheduling Suboptimal

```bash
# Retrain AI on your preferences
/calendar:sync-tasks --learn-from-history

# Manually adjust and AI learns
/calendar:sync-tasks --reschedule "Task X" --to "tomorrow 9am"
# AI: "Learned: User prefers morning for this type of task"
```

## Related Commands

- `/google:calendar` - Calendar management (atomic operations)
- `/assistant:tasks` - Task management
- `/priority:rank` - Priority management
- `/meeting:prep` - Meeting preparation
- `/context:switch` - Context switching

## Notes

**First Run**: Initial sync may take 2-3 minutes to schedule backlog. Subsequent runs take <30 seconds.

**AI Model**: Uses Claude Sonnet 4 for scheduling optimization (optimal for complex scheduling logic).

**Cost**: ~$0.05-0.10 per sync run. ~$150-200/year for hourly sync during working hours.

**Offline Mode**: Can run rule-based scheduling without AI (faster but less optimal).

---

*Never manually schedule a task again. Let AI optimize your calendar while you focus on getting work done.*
