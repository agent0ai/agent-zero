---
description: Motion weekly schedule optimization with AI-powered workload balancing
argument-hint: "[--week <date>] [--optimize <productivity|balance|deadline>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
---

# Motion Schedule Optimization Command

## Overview

Optimize your entire weekly schedule using Motion's AI. Balances workload, respects energy levels, protects deep work, and maximizes productivity.

**Part of Phase 3**: Motion + AI Autopilot

## Usage

```bash
# Optimize this week
/motion:schedule

# Optimize next week
/motion:schedule --week "next"

# Optimize for specific goal
/motion:schedule --optimize productivity  # Max output
/motion:schedule --optimize balance      # Work-life balance
/motion:schedule --optimize deadline     # Hit all deadlines
```

## Motion AI Optimization

```javascript
const optimization = await mcp.motion.optimizeSchedule({
  week: weekStart,
  goals: {
    maximize_deep_work: true,
    respect_energy_levels: true,
    protect_personal_time: true,
    hit_deadlines: true
  },
  constraints: {
    max_hours_per_day: 8,
    min_break_minutes: 15,
    no_work_after: '18:00'
  }
});
```

### Results

```
✓ Weekly schedule optimized by Motion AI

📊 This Week (Jan 22-26, 2025)

Optimization Results:
  Deep work blocks: 15 hours (was 8 hours) ↑ +88%
  Meeting time: 6 hours (was 10 hours) ↓ -40%
  Task completion forecast: 95% (was 70%) ↑ +36%
  Work-life balance score: 85/100 (was 60/100) ↑ +42%

Changes Made:
  ✓ Declined 3 low-value meetings
  ✓ Moved 5 tasks to optimal time slots
  ✓ Created 3 deep work blocks (3 hrs each)
  ✓ Added buffer time before deadlines
  ✓ Balanced workload across week

📅 Mon: 7.5 hrs (balanced)
📅 Tue: 8 hrs (heavy - client deadline)
📅 Wed: 6 hrs (light - post-deadline recovery)
📅 Thu: 8 hrs (balanced)
📅 Fri: 5 hrs (light - weekly review)

Apply optimizations? (y/n)
```

## Related Commands

- `/motion:task` - Create AI-scheduled tasks
- `/motion:project` - Project auto-scheduling
- `/optimize:auto` - Continuous optimization

---

*Perfect weekly schedule in seconds with Motion AI.*
