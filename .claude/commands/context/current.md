---
description: Display detailed information about the currently active context
argument-hint: "[--detail full|summary] [--export json|markdown|html] [--include metrics|projects|timeline|all]"
model: claude-3-5-haiku-20241022
allowed-tools: ["Read", "Bash", "AskUserQuestion"]
---

# Show Current Business Context

Display comprehensive information about your currently active business context, including environment state, active projects, metrics, and upcoming deadlines.

## What This Command Does

Get a complete picture of where you are right now:

- **Current Status**: What business context you're in and why
- **Environment**: All variables, integrations, and configurations loaded
- **Active Work**: Projects, tasks, and in-progress items
- **Key Metrics**: Business health indicators at a glance
- **Timeline**: What's happening next (next 7/30 days)
- **Quick Actions**: Most common next steps for this context

## Why This Matters for Multi-Business Operators

When switching between businesses constantly, you need instant clarity:

- What's my current business context?
- What was I working on last?
- What's the status of everything?
- What should I prioritize right now?
- What integrations are active?

**Business Impact**: Eliminates "where was I?" seconds after context switch; saves 2-3 minutes per context switch × 5 daily switches = 10-15 minutes/day

## Usage

```bash
# Quick status of current context
/context:current

# Full detailed view with all information
/context:current --detail full

# Brief summary only
/context:current --detail summary

# Export current context info as JSON
/context:current --export json

# Export as markdown document
/context:current --export markdown

# Include only metrics in output
/context:current --include metrics

# Include projects, timeline, and metrics
/context:current --include projects,timeline,metrics

# Get everything
/context:current --include all
```

## Output Examples

### Full View (Default)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    CURRENT CONTEXT: Property Management                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📍 LOCATION & IDENTITY
────────────────────────────────────────────────────────────────────────────────
  Business Name       Main Street Properties LLC
  Context Type        Property Management
  Location            Austin, TX
  Active Since        Jan 15, 2025 (41 days)
  Last Activity       Today, 2:34 PM (just now)
  Status              ✓ Active | Primary Focus

💼 ENVIRONMENT STATE
────────────────────────────────────────────────────────────────────────────────
  Business ID         BIZ-00142
  Zoho CRM ID         12345
  Primary Currency    USD
  Tax Rate            8.25% (TX)
  Fiscal Year Start   Jan 1
  Working Directory   /properties/main-street-properties/

🔗 INTEGRATIONS (All Active)
────────────────────────────────────────────────────────────────────────────────
  ✓ Zoho CRM          Connected | Last sync: 2 hours ago
  ✓ Google Calendar   Connected | 8 upcoming events
  ✓ QuickBooks        Connected | Last sync: 1 hour ago
  ✓ Slack             Connected | #property-updates active
  ✓ Stripe (Payment)  Connected | Processing enabled

📊 KEY METRICS (This Month)
────────────────────────────────────────────────────────────────────────────────
  Portfolio Value     $2,850,000 (5 properties)
  Monthly Revenue     $12,450 (from rent)
  Occupancy Rate      95% (19/20 units)
  Maintenance Budget  $2,300 remaining ($5,000 total)
  Tenant Health       Good (2 lease renewals pending)
  Days Cash Reserve   112 (very healthy)

📋 ACTIVE PROJECTS (2 in flight)
────────────────────────────────────────────────────────────────────────────────
  1. 🔧 123 Main St - Roof Maintenance
     Status: In Progress | Owner: Aaron
     Timeline: Feb 1-5, 2025
     Budget: $4,200 | Spent: $0
     Contractor: ABC Roofing Inc
     Notes: 2 bids received, selected best value

  2. 📄 March Lease Renewals
     Status: Planning | Owner: Aaron
     Timeline: Mar 1-15, 2025
     Impact: 3 units affected
     Current Status: Letter sent to tenants
     Next: Collect signed renewals

🎯 IN-PROGRESS TASKS
────────────────────────────────────────────────────────────────────────────────
  □ Schedule roof repair contractor visit (Due: Today)
  □ Review roof repair quotes (Due: Today)
  ✓ Send lease renewal notices (Completed yesterday)
  □ Tenant meeting - Unit 2B (Due: Jan 28)
  □ Update QuickBooks with Jan expenses (Due: Jan 31)

📅 UPCOMING DEADLINES (Next 7 Days)
────────────────────────────────────────────────────────────────────────────────
  TODAY              Schedule roof contractor
  Tomorrow           Get signed roof quotes
  Jan 28 (3 days)    Tenant meeting for Unit 2B
  Jan 30 (5 days)    Quarterly maintenance review
  Jan 31 (6 days)    January financial close

📈 UPCOMING MILESTONES (Next 30 Days)
────────────────────────────────────────────────────────────────────────────────
  Feb 1-5            Roof repair (123 Main St)
  Feb 15             Deadline: Lease renewal signatures
  Feb 28             February financial report
  Mar 1-15           Execute March lease renewals

💬 RECENT NOTES (Last 5)
────────────────────────────────────────────────────────────────────────────────
  Jan 25 2:34 PM     Called contractor - available Feb 1-5
  Jan 24 4:15 PM     Reviewed roofing bids - ABC Roofing selected
  Jan 23 10:20 AM    Unit 2B tenant requested 6-month extension
  Jan 22 7:45 PM     Quarterly reserves review complete - healthy position
  Jan 21 3:30 PM     Maintenance issue resolved (gutter repair)

🚀 QUICK ACTIONS (Most Common Next Steps)
────────────────────────────────────────────────────────────────────────────────
  /property:schedule "roof-repair" --contractor "ABC Roofing"
  /finance:report --month january --property "123-main-st"
  /tenant:contact "unit-2b" --template lease-renewal
  /calendar:add "roof-repair" --date "2025-02-01"

📞 KEY CONTACTS
────────────────────────────────────────────────────────────────────────────────
  Property Manager   You (Aaron)
  Maintenance Lead   Mike Johnson | 512-555-0123
  Tax Advisor        Sarah Chen CPA | sarah@chen-accounting.com
  Property Attorney  Legal Associates LLC | 512-555-0199

🔄 CONTEXT SNAPSHOT
────────────────────────────────────────────────────────────────────────────────
  Saved: Just now (auto-save every 30 minutes)
  Switch History: 3 times today (9:00am, 12:30pm, 2:34pm)
  Time in Context: 47 minutes today | 8.5 hours this week
  Last Backup: 2 hours ago | Next: 30 minutes
```

### Summary View

```
CURRENT: Property Management (Main Street Properties LLC)
Active Since: 41 days | Last Activity: Just now
Status: ✓ Active | 2 projects | 5 tasks | On track

Quick Stats:
  Revenue: $12,450/mo | Occupancy: 95% | Maintenance: $2,300 budget

Next Up:
  • Schedule roof contractor (TODAY)
  • Tenant meeting (Jan 28)
  • Lease renewals (Mar 1-15)

Ready to work? Try:
  /property:schedule, /tenant:contact, /finance:report
```

### JSON Export

```json
{
  "context": {
    "name": "property-management",
    "type": "property",
    "business_name": "Main Street Properties LLC",
    "location": "Austin, TX",
    "status": "active",
    "created": "2025-01-15T08:00:00Z",
    "last_active": "2025-01-25T14:34:00Z",
    "active_duration_days": 41
  },
  "environment": {
    "business_id": "BIZ-00142",
    "zoho_crm_id": "12345",
    "currency": "USD",
    "tax_rate": 0.0825,
    "fiscal_year_start": "2025-01-01",
    "working_directory": "/properties/main-street-properties/"
  },
  "integrations": [
    {
      "name": "Zoho CRM",
      "status": "connected",
      "last_sync": "2025-01-25T12:34:00Z"
    },
    {
      "name": "Google Calendar",
      "status": "connected",
      "upcoming_events": 8
    }
  ],
  "metrics": {
    "portfolio_value": 2850000,
    "monthly_revenue": 12450,
    "occupancy_rate": 0.95,
    "maintenance_budget_remaining": 2300,
    "days_cash_reserve": 112
  },
  "active_projects": 2,
  "in_progress_tasks": 5,
  "next_deadline": "2025-01-25T17:00:00Z",
  "next_milestone": "2025-02-01T00:00:00Z"
}
```

## Step-by-Step Execution

### 1. Load Active Context

```bash
# Read current context identifier
ACTIVE_CONTEXT=$(cat ~/.claude/context_active)

# Load context configuration
CONTEXT_FILE=~/.claude/contexts/${ACTIVE_CONTEXT}.json
```

### 2. Extract Environment State

```bash
# Parse from context file:
- Business name, type, location
- Created and last_active timestamps
- Environment variables (Zoho IDs, locations, etc)
- Integration status and configs
```

### 3. Calculate Key Metrics

```bash
# Extract business-specific metrics:
- Revenue (from finance integration)
- Occupancy rates (from property data)
- Project status (from project management)
- Task counts and status
```

### 4. Build Timeline

```bash
# Next 7 days: Extract from calendar/tasks
# Next 30 days: Extract from project milestones
# Sort by date and priority
```

### 5. Gather Active Items

```bash
# In-progress projects: Status = "active"
# Open tasks: Status = "pending" or "in_progress"
# Recent notes: Last 5 entries
# Recent activity: Switch history
```

### 6. Format and Display

```bash
# Apply formatting based on --detail and --export options
# Default: full detailed display with sections
# Summary: condensed version
# JSON: structured export
```

## Information Categories

### Context Identity

- Business name
- Context type
- Location/region
- Days active
- Current status
- Primary focus indicator

### Environment

- Business ID
- Zoho CRM ID
- Currency settings
- Tax configuration
- Fiscal year info
- Working directory

### Integrations

- Status (connected/disconnected)
- Last sync timestamp
- Health indicators
- Connection details

### Key Metrics

- Business-specific KPIs
- Financial summaries
- Operational metrics
- Health indicators
- Trend comparisons

### Active Work

- In-flight projects
- Pending tasks
- Active collaborations
- Blockers/risks

### Timeline

- Immediate (next 24 hours)
- Short-term (next 7 days)
- Medium-term (next 30 days)
- Major milestones

### Quick Actions

- Most common next steps
- Context-specific commands
- Related resources

## Business Value

**Decision Speed**:

- Time to "what should I do now?": <10 seconds
- Eliminates decision paralysis
- **Impact**: 5-10 minutes saved per context switch

**Operational Efficiency**:

- Complete picture at a glance
- Spot bottlenecks instantly
- Better priority decisions
- **Improvement**: 20-30% faster workflow execution

**Time Savings**:

- No "refresh my memory" searches
- Integration status visible immediately
- Next actions pre-computed
- **Saves**: 2-3 minutes per switch × 5 daily = 10-15 min/day

**Risk Reduction**:

- Catch deadline conflicts immediately
- See budget overruns at a glance
- Spot stalled projects early
- **Value**: $500-1,000/week in avoided issues

## Success Metrics

✅ Display loads within 1 second
✅ All environment variables loaded correctly
✅ Metrics reflect current business state
✅ Timeline includes all due items in next 30 days
✅ Integration status is accurate
✅ JSON export is valid and complete
✅ Quick actions are contextually relevant
✅ Summary view under 10 lines

## Related Commands

- `/context:switch` - Switch to different context
- `/context:list` - See all available contexts
- `/context:create` - Create new business context
- `/dashboard:overview` - Full interactive dashboard
- `/timeline:upcoming` - Detailed milestone view across all contexts

## Notes

**Auto-Refresh**: Context data auto-syncs every 30 minutes from integrations.

**Customization**: Can add custom metric sections by extending context schema.

**Performance**: Display generation optimized for <1 second response.

**Privacy**: Only shows data you have access to in each integration.

---

*Everything you need to know about your current business in one screen. No hunting through tabs, no forgotten details, no context loss.*
