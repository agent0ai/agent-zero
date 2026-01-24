---
description: AI-powered smart meeting scheduling with optimal time detection and context awareness
argument-hint: "<meeting-name> [--attendees <emails>] [--duration <time>] [--preferred-times <slots>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Smart Meeting Scheduling Command

## Overview

AI-powered meeting scheduling that finds the optimal time for all attendees by analyzing calendars, time zones, work patterns, and energy levels. Eliminates the back-and-forth of "what time works for you?"

**Part of Phase 3**: Motion + AI Autopilot integration

## What This Command Does

- ✅ Analyzes all attendees' calendars for availability
- ✅ Detects optimal meeting times (not Friday 4 PM!)
- ✅ Respects time zones and working hours
- ✅ Considers energy levels (morning vs afternoon)
- ✅ Avoids back-to-back meetings and scheduling conflicts
- ✅ Sends calendar invites with optimal time
- ✅ Suggests prep time and follow-up blocks
- ✅ **Saves 15-20 min per meeting scheduled**

## Usage

```bash
# Schedule meeting with AI time optimization
/schedule:smart "Client Presentation" --attendees "john@client.com,sarah@team.com"

# With preferred duration
/schedule:smart "Team Sync" --attendees "team@company.com" --duration "30 min"

# With time preferences
/schedule:smart "Project Kickoff" --attendees "stakeholders@company.com" --preferred-times "mornings,Tue-Thu"

# With deadline
/schedule:smart "Budget Review" --attendees "cfo@company.com" --by "2025-02-01"

# Recurring meeting
/schedule:smart "Weekly 1:1" --attendees "manager@company.com" --recurring "weekly"
```

## AI Scheduling Intelligence

The AI considers:

1. **Calendar Availability**: All attendees' free/busy status
2. **Time Zone Optimization**: Best time across all zones
3. **Meeting Type Analysis**:
   - Creative/strategic → morning (high energy)
   - Status updates → early afternoon
   - Administrative → late afternoon
4. **Work Pattern Respect**:
   - No Friday afternoons for important meetings
   - No Monday 8 AM meetings
   - No meetings during typical lunch hours (12-1 PM)
5. **Context Awareness**:
   - Prep time before important meetings
   - Buffer time between back-to-back meetings
   - Follow-up blocks after decision meetings
6. **Energy Level Matching**:
   - High-stakes meetings → peak energy times
   - Routine meetings → lower energy times

## Implementation Details

### Step 1: Analyze Meeting Requirements

```javascript
// AI determines meeting type and requirements
const meetingContext = await claude.analyze({
  prompt: `Analyze this meeting and determine optimal scheduling:

  Meeting: "${meetingName}"
  Attendees: ${attendees.join(', ')}

  Determine:
  1. Meeting Type: strategic|creative|administrative|status_update|decision_making
  2. Optimal Duration: Based on meeting type
  3. Energy Level Required: high|medium|low
  4. Prep Time Needed: 0-60 minutes
  5. Follow-up Time Needed: 0-30 minutes
  6. Preferred Time of Day: morning|early_afternoon|late_afternoon

  Return JSON with these fields.
  `
});

// Example result:
// {
//   "type": "strategic",
//   "optimal_duration": 60,
//   "energy_level": "high",
//   "prep_time": 30,
//   "followup_time": 15,
//   "preferred_time": "morning"
// }
```

### Step 2: Fetch All Attendees' Calendars

```javascript
// Using Google Calendar MCP
const calendars = await Promise.all(
  attendees.map(email =>
    mcp.calendar.getFreeBusy({
      email: email,
      timeMin: new Date().toISOString(),
      timeMax: addDays(new Date(), 14).toISOString() // Next 2 weeks
    })
  )
);

// Combine into availability matrix
const availability = buildAvailabilityMatrix(calendars);
```

### Step 3: AI Finds Optimal Time Slots

```javascript
const optimalSlots = await claude.findOptimalTimes({
  prompt: `Find optimal meeting times based on this data:

  MEETING REQUIREMENTS:
  Type: ${meetingContext.type}
  Duration: ${meetingContext.optimal_duration} minutes
  Energy Level: ${meetingContext.energy_level}
  Prep Time: ${meetingContext.prep_time} minutes

  AVAILABILITY MATRIX:
  ${JSON.stringify(availability, null, 2)}

  ATTENDEE TIME ZONES:
  ${attendees.map(a => `${a.email}: ${a.timezone}`).join('\n')}

  CONSTRAINTS:
  - No Friday afternoons for strategic meetings
  - No Monday mornings before 10 AM
  - No meetings during 12-1 PM (lunch)
  - Minimum 15-minute buffer between meetings
  - Respect working hours (9 AM - 5 PM local time)

  PREFERENCES:
  - High energy meetings → 9-11 AM
  - Creative meetings → morning
  - Status updates → early afternoon (2-3 PM)
  - Avoid back-to-back meetings

  Return top 3 time slots ranked by optimality score (0-100).
  Include reasoning for each recommendation.

  Return JSON:
  [
    {
      "start": "2025-01-24T10:00:00-05:00",
      "end": "2025-01-24T11:00:00-05:00",
      "score": 95,
      "reasoning": "Morning slot, all attendees available, optimal energy level",
      "timezone_summary": "10 AM EST / 7 AM PST / 3 PM GMT",
      "pros": ["High energy time", "No conflicts"],
      "cons": ["Early for PST attendees"]
    }
  ]
  `
});
```

### Step 4: Present Options to User

```javascript
console.log(`
🤖 AI SMART SCHEDULING: "${meetingName}"

Analyzed ${attendees.length} attendees across ${uniqueTimezones} time zones
Scanned next 2 weeks for optimal availability

TOP 3 RECOMMENDED TIME SLOTS:

[1] BEST (Score: 95/100) ⭐
    📅 Thursday, Jan 24, 2025
    ⏰ 10:00 AM - 11:00 AM EST
    🌍 Time Zones: 10 AM EST / 7 AM PST / 3 PM GMT

    ✅ Pros:
       • Morning slot (optimal for strategic meetings)
       • All attendees available
       • High energy time for decision-making
       • No meetings before or after (buffer time)

    ⚠️  Cons:
       • Early morning for PST attendees (7 AM)

    Why this time:
    Perfect for strategic discussions. All attendees free.
    Morning energy levels ideal for creative thinking.

[2] GOOD (Score: 88/100)
    📅 Tuesday, Jan 22, 2025
    ⏰ 2:00 PM - 3:00 PM EST
    🌍 Time Zones: 2 PM EST / 11 AM PST / 7 PM GMT

    ✅ Pros:
       • All attendees available
       • Better for PST timezone (11 AM)
       • Post-lunch energy suitable

    ⚠️  Cons:
       • Late afternoon for GMT attendees (7 PM)
       • Lower energy than morning slot

    Why this time:
    Balanced across time zones. Suitable for status updates
    and collaborative work.

[3] OK (Score: 75/100)
    📅 Wednesday, Jan 23, 2025
    ⏰ 3:00 PM - 4:00 PM EST
    🌍 Time Zones: 3 PM EST / 12 PM PST / 8 PM GMT

    ✅ Pros:
       • All attendees available
       • Lunch time for PST (convenient)

    ⚠️  Cons:
       • Late evening for GMT (8 PM)
       • Energy levels declining
       • Close to end of day for EST

    Why this time:
    Latest acceptable time. Not ideal but workable if
    other slots don't fit.

Which time slot works best? [1/2/3/custom]
`);
```

### Step 5: Create Calendar Event with Prep & Follow-up

```javascript
// User selects option 1
const selectedSlot = optimalSlots[0];

// Create prep time block (if needed)
if (meetingContext.prep_time > 0) {
  await mcp.calendar.createEvent({
    summary: `📋 Prep: ${meetingName}`,
    description: `Preparation time for upcoming meeting\n\nMeeting: ${meetingName}\nAttendees: ${attendees.join(', ')}`,
    start: {
      dateTime: subtractMinutes(selectedSlot.start, meetingContext.prep_time),
      timeZone: context.timezone
    },
    end: {
      dateTime: selectedSlot.start,
      timeZone: context.timezone
    },
    colorId: '6', // Orange for prep
    reminders: {
      useDefault: false,
      overrides: [
        { method: 'popup', minutes: 10 }
      ]
    }
  });
}

// Create main meeting event
const meetingEvent = await mcp.calendar.createEvent({
  summary: meetingName,
  description: `AI-optimized meeting time selected based on:
• Attendee availability across ${uniqueTimezones} time zones
• Meeting type: ${meetingContext.type}
• Optimal energy levels for ${meetingContext.type} discussions

Time Zones:
${selectedSlot.timezone_summary}

Agenda: [To be added]
`,
  start: {
    dateTime: selectedSlot.start,
    timeZone: context.timezone
  },
  end: {
    dateTime: selectedSlot.end,
    timeZone: context.timezone
  },
  attendees: attendees.map(email => ({ email: email })),
  conferenceData: {
    createRequest: {
      requestId: generateUUID(),
      conferenceSolutionKey: { type: 'hangoutsMeet' }
    }
  },
  reminders: {
    useDefault: false,
    overrides: [
      { method: 'email', minutes: 24 * 60 }, // 1 day before
      { method: 'popup', minutes: 30 } // 30 min before
    ]
  },
  extendedProperties: {
    private: {
      scheduledBy: 'claude-code-smart-schedule',
      optimizationScore: selectedSlot.score,
      meetingType: meetingContext.type
    }
  }
});

// Create follow-up time block (if needed)
if (meetingContext.followup_time > 0) {
  await mcp.calendar.createEvent({
    summary: `📝 Follow-up: ${meetingName}`,
    description: `Time to process meeting outcomes and send follow-ups\n\nMeeting: ${meetingName}`,
    start: {
      dateTime: selectedSlot.end,
      timeZone: context.timezone
    },
    end: {
      dateTime: addMinutes(selectedSlot.end, meetingContext.followup_time),
      timeZone: context.timezone
    },
    colorId: '6', // Orange for follow-up
    reminders: {
      useDefault: false,
      overrides: [
        { method: 'popup', minutes: 0 } // Right when meeting ends
      ]
    }
  });
}
```

### Step 6: Sync to Motion and Notion

```javascript
// Sync to Motion (if enabled)
if (context.integrations.motion.enabled) {
  await mcp.motion.createTask({
    name: `Attend: ${meetingName}`,
    deadline: selectedSlot.start,
    duration: meetingContext.optimal_duration,
    priority: meetingContext.type === 'strategic' ? 'high' : 'medium',
    status: 'scheduled',
    calendar_event_id: meetingEvent.id
  });
}

// Sync to Notion (if enabled)
if (context.integrations.notion.enabled) {
  await mcp.notion.createPage({
    parent: { database_id: context.integrations.notion.database_ids.meetings },
    properties: {
      Name: { title: [{ text: { content: meetingName } }] },
      Date: { date: { start: selectedSlot.start } },
      Duration: { number: meetingContext.optimal_duration },
      Attendees: { multi_select: attendees.map(email => ({ name: email })) },
      Type: { select: { name: meetingContext.type } },
      'Calendar Link': { url: meetingEvent.htmlLink },
      'Optimization Score': { number: selectedSlot.score }
    }
  });
}
```

### Confirmation

```
✓ Meeting scheduled with AI optimization

📅 "${meetingName}"
⏰ Thursday, Jan 24, 2025 @ 10:00 AM - 11:00 AM EST
🌍 10 AM EST / 7 AM PST / 3 PM GMT

👥 Attendees (3):
   • john@client.com
   • sarah@team.com
   • you@company.com

📊 Optimization Score: 95/100 (Excellent)

✅ What was scheduled:
   [1] 9:30 AM - 10:00 AM: Prep time (30 min)
   [2] 10:00 AM - 11:00 AM: Main meeting (60 min)
   [3] 11:00 AM - 11:15 AM: Follow-up time (15 min)

📧 Calendar invites sent to all attendees
🔗 Google Meet link: https://meet.google.com/abc-defg-hij
📝 Synced to Notion meetings database
📋 Synced to Motion tasks

Why this time was chosen:
• Morning slot optimal for strategic discussions
• All attendees available with no conflicts
• High energy time for decision-making
• Respectful of all time zones (within working hours)
• No back-to-back meetings before or after

Next Actions:
[1] Add agenda → Update calendar event
[2] Add prep notes → Create Notion page
[3] Reschedule → Find alternative time
[4] Cancel → Delete calendar event
```

## AI Scheduling Features

### Timezone Intelligence

```javascript
// AI optimizes across time zones
const timezoneAnalysis = {
  attendees: [
    { email: 'john@client.com', timezone: 'America/New_York', offset: -5 },
    { email: 'sarah@team.com', timezone: 'America/Los_Angeles', offset: -8 },
    { email: 'alex@partner.com', timezone: 'Europe/London', offset: 0 }
  ],
  constraints: [
    // No meetings before 9 AM or after 5 PM local time
    { rule: 'working_hours', min: '09:00', max: '17:00' },
    // Minimize extreme hours (before 8 AM or after 6 PM)
    { rule: 'reasonable_hours', min: '08:00', max: '18:00' }
  ]
};

// AI finds "sweet spot" that works for all
```

### Meeting Type Detection

```javascript
// AI detects meeting type from name and attendees
const detectMeetingType = (name, attendees) => {
  const keywords = {
    strategic: ['strategy', 'planning', 'roadmap', 'vision'],
    creative: ['brainstorm', 'ideation', 'design', 'workshop'],
    decision: ['review', 'approval', 'decision', 'budget'],
    status: ['sync', 'standup', 'update', 'check-in'],
    administrative: ['admin', 'housekeeping', 'logistics']
  };

  // Match keywords or analyze context
  // Strategic meetings → morning
  // Status updates → early afternoon
  // Administrative → late afternoon
};
```

### Recurring Meeting Optimization

```bash
# For recurring meetings
/schedule:smart "Weekly Team Sync" --recurring "weekly" --attendees "team@company.com"

# AI finds consistently good time across weeks
# Avoids holidays and common conflict patterns
# Suggests best day of week (typically Tue-Thu)
```

## Integration with Other Commands

### With `/motion:task`

```bash
# Scheduled meetings automatically create Motion tasks
# Motion AI ensures prep time is optimally scheduled
```

### With `/workflow:meeting-complete`

```bash
# After meeting ends, workflow automatically triggers:
# → Capture notes
# → Extract action items
# → Create tasks
```

### With `/email:smart-reply`

```bash
# "Can we schedule a call?" emails
# → AI drafts reply with 3 optimal time options
# → One-click to schedule
```

## Business Value

**Time Savings**:

- Manual scheduling: 15-20 min per meeting (email back-and-forth)
- Smart scheduling: <2 min
- **Saves 15-20 min per meeting**

**Quality Improvements**:

- Optimal times (not Friday 4 PM!)
- Respects time zones and energy levels
- Includes prep and follow-up time
- Reduces no-shows and late arrivals

**Productivity Gains**:

- Average professional: 8-12 meetings/week
- Time saved: 2-4 hours/week
- **Value: $300-600/week**

## Success Metrics

✅ Scheduling time <2 minutes
✅ Attendee satisfaction >8/10
✅ Conflict rate <5%
✅ Meeting quality score improvement >20%
✅ No-show rate reduction >30%

## Advanced Options

### Custom Time Preferences

```bash
# Only mornings
/schedule:smart "Deep Work Session" --preferred-times "mornings"

# Specific days
/schedule:smart "Team Lunch" --preferred-times "Fri"

# Avoid certain times
/schedule:smart "Client Call" --avoid "Mon,Fri"
```

### Emergency Scheduling

```bash
# Find soonest available time
/schedule:smart "Urgent: Bug Review" --urgent --duration "30 min"

# AI finds next available slot (even if not optimal)
```

### Team Preferences

```bash
# Load team scheduling preferences
/schedule:smart "All Hands" --attendees "@engineering-team" --respect-preferences

# Uses stored preferences:
# - No meetings before 10 AM
# - No Friday afternoons
# - Prefer Tue-Thu for important meetings
```

## Related Commands

- `/motion:task` - AI-scheduled task creation
- `/motion:schedule` - Weekly schedule optimization
- `/workflow:meeting-complete` - Post-meeting automation
- `/email:smart-reply` - Context-aware email responses
- `/calendar:sync-tasks` - Task → Calendar sync

## Notes

**Calendar Access**: Requires read access to all attendees' calendars (free/busy minimum).

**Privacy**: Only accesses free/busy status, not meeting details.

**Fallback**: If AI can't find optimal time, provides best available options with reasoning.

**Learning**: AI improves over time by learning your scheduling preferences and patterns.

---

*Never waste time on "what time works for you?" again. Let AI find the perfect time.*
