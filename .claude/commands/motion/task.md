---
description: Motion AI-scheduled task creation with automatic calendar optimization
argument-hint: "<task-name> [--deadline <date>] [--duration <time>] [--priority <level>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Motion Task Command

## Overview

Create tasks in Motion with AI-powered automatic scheduling. Motion's AI finds the optimal time based on your calendar, priorities, deadlines, and work patterns.

**Part of Phase 3**: Motion + AI Autopilot integration

## What This Command Does

- ✅ Creates task in Motion with AI scheduling
- ✅ Motion AI finds optimal calendar slot automatically
- ✅ Syncs to Google Calendar as time block
- ✅ Syncs to Notion and Trello (bidirectional)
- ✅ Adapts to your work patterns and energy levels
- ✅ Auto-reschedules when conflicts arise

## Usage

```bash
# Create task with AI scheduling
/motion:task "Complete API integration" --deadline "2025-02-01"

# With duration estimate
/motion:task "Write proposal" --duration "3 hours" --priority high

# Let Motion AI optimize completely
/motion:task "Client presentation prep" --auto-schedule

# Recurring task
/motion:task "Weekly team sync prep" --recurring "weekly"

# With dependencies
/motion:task "Deploy feature" --depends-on "Complete testing"
```

## Motion AI Scheduling

Motion's AI scheduling engine considers:

1. **Your Calendar**: Existing meetings and blocks
2. **Deadlines**: Works backward from due dates
3. **Priorities**: High priority tasks scheduled first
4. **Work Patterns**: When you're most productive
5. **Energy Levels**: Complex tasks in high-energy times
6. **Dependencies**: Tasks that must complete first
7. **Buffer Time**: Breaks and transitions
8. **Team Availability**: For collaborative tasks

**Result**: Optimal schedule that maximizes productivity and respects your workflow.

## Implementation Details

### MCP Server Required

```bash
# Install Motion MCP server
/mcp:install motion --auth-type api-key

# Or via Composio
/mcp:install composio --add-integration motion
```

### Context Integration

```json
{
  "integrations": {
    "motion": {
      "enabled": true,
      "workspace_id": "workspace-123",
      "sync_to_google_calendar": true,
      "mcp_server": "motion-mcp"
    },
    "motion_settings": {
      "auto_schedule": true,
      "respect_deep_work": true,
      "work_hours": {
        "start": "09:00",
        "end": "17:00"
      },
      "energy_profile": {
        "high": ["09:00-12:00"],
        "medium": ["14:00-16:00"],
        "low": ["16:00-17:00"]
      }
    }
  }
}
```

## Step-by-Step Execution

### 1. Create Task in Motion

```javascript
// Motion MCP API call
const motionTask = await mcp.motion.createTask({
  name: taskName,
  description: taskDescription,
  deadline: deadline ? new Date(deadline).toISOString() : null,
  duration: parseDuration(options.duration) || 60, // minutes
  priority: options.priority || 'medium',
  status: 'auto_scheduled',
  workspace: context.integrations.motion.workspace_id,
  labels: [context.name, 'from-claude-code'],
  scheduling_preferences: {
    auto_schedule: true,
    respect_calendar: true,
    energy_level: determineEnergyLevel(taskName, options.priority),
    chunk_size: options.chunkSize || 'continuous' // or 'pomodoro'
  }
});

// Motion AI automatically finds optimal time slot
```

### 2. Motion AI Finds Optimal Slot

```javascript
// Motion's AI scheduling engine (automatic)
// Analyzes:
// - Current calendar for next 2 weeks
// - Task deadline and duration
// - Priority vs other tasks
// - Historical productivity patterns
// - Energy level requirements
// - Buffer time and transitions

// Returns optimal schedule:
const schedule = motionTask.scheduled_time;
// Example: "2025-01-23T09:00:00Z to 2025-01-23T12:00:00Z"
```

### 3. Sync to Google Calendar

```javascript
// Automatic sync if enabled
if (context.integrations.motion.sync_to_google_calendar) {
  const calendarEvent = await mcp.calendar.createEvent({
    summary: `📋 ${taskName} (Motion)`,
    description: `Motion Task: ${motionTask.id}

AI-Scheduled Time Slot
Priority: ${options.priority}
Estimated Duration: ${options.duration}

Motion: ${motionTask.web_url}
`,
    start: {
      dateTime: schedule.start,
      timeZone: context.timezone
    },
    end: {
      dateTime: schedule.end,
      timeZone: context.timezone
    },
    colorId: '7', // Peacock blue for Motion tasks
    extendedProperties: {
      private: {
        motionTaskId: motionTask.id,
        source: 'motion'
      }
    }
  });

  // Link back to Motion
  await mcp.motion.updateTask({
    id: motionTask.id,
    calendar_event_id: calendarEvent.id,
    calendar_link: calendarEvent.htmlLink
  });
}
```

### 4. Sync to Notion & Trello

```javascript
// Sync to Notion
const notionTask = await mcp.notion.createPage({
  parent: { database_id: context.integrations.notion.database_ids.tasks },
  properties: {
    Name: { title: [{ text: { content: taskName } }] },
    Status: { select: { name: 'Scheduled' } },
    Priority: { select: { name: options.priority } },
    Due: deadline ? { date: { start: deadline } } : null,
    'Scheduled Time': { date: { start: schedule.start, end: schedule.end } },
    'Motion Task': { url: motionTask.web_url },
    Source: { select: { name: 'Motion AI' } }
  }
});

// Sync to Trello
const trelloCard = await mcp.trello.createCard({
  name: taskName,
  desc: `Motion AI Scheduled: ${new Date(schedule.start).toLocaleString()}

Duration: ${options.duration}
Priority: ${options.priority}

Motion: ${motionTask.web_url}
Notion: ${notionTask.url}
Calendar: ${calendarEvent.htmlLink}
`,
  idList: getListByPriority(options.priority),
  due: deadline,
  pos: 'top'
});
```

### 5. Confirmation

```
✓ Task created and AI-scheduled by Motion

📋 "Complete API integration"
⏱️  Duration: 3 hours
📅 Deadline: Feb 1, 2025
🎯 Priority: High

🤖 Motion AI Scheduled:
   Tomorrow, 9:00 AM - 12:00 PM (3 hours)

   Why this time:
   • High priority → scheduled in morning
   • 3-hour block → matches deep work window
   • No conflicts → calendar clear
   • Energy level: High (optimal for complex work)
   • 1 day before next high-priority task

📅 Synced to Google Calendar
   🔗 https://calendar.google.com/event/abc123

📝 Synced to Notion Tasks
   Status: Scheduled
   🔗 https://notion.so/task-xyz789

📋 Synced to Trello
   Board: Active Projects | List: This Week
   🔗 https://trello.com/c/def456

🔗 Motion: https://app.usemotion.com/task/ghi789

Auto-Rescheduling: ✓ Enabled
  If conflicts arise, Motion will automatically
  reschedule to next optimal time slot.

Next Actions:
[1] View in Motion → Opens Motion app
[2] View schedule → Shows this week's schedule
[3] Adjust time → Manually reschedule
[4] Start now → Opens task and starts timer
```

## Motion AI Features

### Auto-Rescheduling

```javascript
// When calendar changes (new meeting added)
// Motion automatically reschedules conflicting tasks
// No manual intervention needed

// Example:
// - Task scheduled: Tomorrow 2:00 PM - 4:00 PM
// - New meeting added: Tomorrow 2:30 PM - 3:30 PM
// - Motion AI: Automatically reschedules task to 9:00 AM - 11:00 AM
```

### Intelligent Chunking

```javascript
// Large tasks automatically broken into chunks
/motion:task "Write 50-page report" --duration "20 hours"

// Motion AI creates:
// - 4 chunks × 5 hours each
// - Scheduled across 2 weeks
// - Morning slots (high energy for writing)
// - Respects other commitments
```

### Team Coordination

```javascript
// For collaborative tasks
/motion:task "Client presentation" --with "john@team.com,sarah@team.com"

// Motion AI finds:
// - Time when all attendees are available
// - Optimal meeting slot (not Friday 4 PM!)
// - Respects timezone differences
// - Suggests prep time before meeting
```

## Integration with Other Commands

### With /calendar:sync-tasks

Motion becomes the primary scheduler:

```bash
# Tasks from other sources → Motion AI schedules
/assistant:tasks → Motion → Calendar
```

### With /autopilot:predict-tasks

Proactive scheduling:

```bash
# AI predicts upcoming tasks
/autopilot:predict-tasks
# → Creates Motion tasks automatically
# → Motion AI schedules optimally
```

### With /workflow:email-to-task

Email → Motion task:

```bash
# Email flagged "Action Required"
# → Motion task created
# → AI schedules automatically
```

## Business Value

**Time Savings**:

- Manual scheduling: 15-20 min per task
- Motion AI: Instant (<5 seconds)
- **Saves 2-3 hours/week**

**Productivity Gains**:

- Optimal task placement (right work at right time)
- Auto-rescheduling (no manual calendar Tetris)
- Respects energy levels and work patterns
- Eliminates scheduling stress

**Motion AI ROI**:

- 25% more tasks completed on time
- 40% better schedule adherence
- 60% less scheduling overhead
- **Value: $300-450/week**

## Success Metrics

✅ Task creation time <5 seconds
✅ AI scheduling accuracy >90%
✅ Auto-reschedule success >95%
✅ Calendar sync 100% reliable
✅ User satisfaction >9/10

## Security & Privacy

- Motion API key encrypted storage
- Calendar sync respects privacy settings
- Task data synced bidirectionally
- Audit logging enabled

## Troubleshooting

### Motion MCP Not Installed

```bash
Error: Motion MCP server not found

Solution:
/mcp:install motion --auth-type api-key
```

### Task Not Auto-Scheduled

```bash
# Check Motion AI settings
/motion:settings --verify

# Ensure calendar access granted
/mcp:configure motion --verify-calendar-access

# Manual schedule
/motion:task "Task name" --schedule "tomorrow 9am"
```

### Sync Failed

```bash
# Retry sync
/motion:task sync --task-id task_123 --to "notion,trello,calendar"

# Check sync status
/motion:task list --show-sync-status
```

## Advanced Options

### Custom Scheduling Preferences

```bash
# Prefer mornings
/motion:task "Deep work" --prefer morning

# Batch with similar tasks
/motion:task "Email clients" --batch-with "email"

# Allow interruptions
/motion:task "Admin work" --interruptible
```

### Energy-Based Scheduling

```bash
# High energy required
/motion:task "Strategic planning" --energy high

# Low energy ok
/motion:task "File organization" --energy low
```

## Related Commands

- `/motion:project` - Project with auto-scheduled tasks
- `/motion:schedule` - Optimize entire weekly schedule
- `/calendar:sync-tasks` - Sync non-Motion tasks
- `/autopilot:predict-tasks` - Proactive task creation
- `/optimize:auto` - Continuous schedule optimization

## Notes

**Motion Subscription**: Requires Motion Pro or Team plan ($34-64/month).

**AI Learning**: Motion AI improves over time by learning your patterns.

**Offline**: Can create tasks offline, schedules when back online.

**Limits**: Motion API rate limit: 100 requests/minute.

---

*Let Motion's AI handle scheduling so you can focus on getting work done.*
