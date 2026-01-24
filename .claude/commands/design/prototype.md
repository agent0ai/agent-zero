---
description: Generate interactive UI prototypes with demo data from approved discovery
argument-hint: "[discovery-id] [--screens dashboard,detail,settings] [--deploy]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Design Prototype - Interactive UI Wireframe Generator

**Purpose**: Generate interactive UI prototypes with realistic demo data based on approved discovery
**Input**: Approved discovery document (from `/design:discover`)
**Output**: Visual wireframes, demo data, and deployable prototype

---

## EXECUTION PROTOCOL

This command will guide you through:

1. **Select Discovery** - Choose which approved discovery to prototype
2. **Screen Selection** - Pick which screens/views to generate
3. **Customization** - Configure demo data, colors, features
4. **Generation** - Create prototype with realistic data
5. **Preview** - Review generated screens and demo data
6. **Actions** - Deploy, export, or iterate

**Navigation Options**:

- Type "next" to proceed to next step
- Type "back" to return to previous step
- Type "regenerate [screen]" to recreate a specific screen
- Type "preview [screen]" to view a specific screen in detail

---

## PREREQUISITES

**Calling API**: GET /api/discovery?status=approved

Fetching approved discoveries...

---

# STEP 1: SELECT DISCOVERY

## Available Approved Discoveries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ APPROVED DISCOVERIES                                                         │
├──────┬──────────────────────┬────────────────────────────┬───────────────────┤
│ ID   │ Customer             │ Project                    │ Approved Date     │
├──────┼──────────────────────┼────────────────────────────┼───────────────────┤
│ 001  │ Acme Corporation     │ Lead Scoring System        │ 2024-12-01        │
│ 002  │ TechStart Inc        │ Customer Portal            │ 2024-12-03        │
│ 003  │ Global Retail Co     │ Inventory Dashboard        │ 2024-12-05        │
│ 004  │ FinServ Partners     │ Compliance Tracking        │ 2024-12-06        │
└──────┴──────────────────────┴────────────────────────────┴───────────────────┘
```

**Question 1**: Which discovery would you like to prototype?

Enter discovery ID (e.g., "001") or type "details [ID]" to view discovery summary.

---

## Discovery Details: [Selected ID]

**Calling API**: GET /api/discovery/[discovery-id]

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ DISCOVERY SUMMARY                                                            ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Customer: [Company Name]                                                     ║
║ Project: [Project Name]                                                      ║
║ Primary Contact: [Name] ([Title])                                            ║
║ Approved: [Date] by [Approver]                                               ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ PAIN POINTS: [X]                                                             ║
║ 1. [Pain Point 1] - Annual Cost: $[X]                                       ║
║ 2. [Pain Point 2] - Annual Cost: $[X]                                       ║
║ 3. [Pain Point 3] - Annual Cost: $[X]                                       ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ WORKFLOWS MAPPED: [Y]                                                        ║
║ 1. [Workflow 1] - Time Savings: [X]%                                        ║
║ 2. [Workflow 2] - Time Savings: [X]%                                        ║
║ 3. [Workflow 3] - Time Savings: [X]%                                        ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ REQUIREMENTS: [Z] Total                                                      ║
║ - Must Have: [A]                                                             ║
║ - Should Have: [B]                                                           ║
║ - Nice to Have: [C]                                                          ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ SUCCESS METRICS:                                                             ║
║ - Goal 1: [Description] - Target: [X]                                       ║
║ - Goal 2: [Description] - Target: [Y]                                       ║
║ - ROI: [X]% over 3 years                                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Is this the correct discovery?**

- Type "yes" to proceed
- Type "no" to select a different discovery
- Type "back" to see all discoveries

---

# STEP 2: SCREEN SELECTION

Based on your discovery requirements, I recommend these screens:

## Available Screen Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SCREEN CATALOG                                                               │
├─────┬────────────────────────────┬──────────────────────────────────────────┤
│ ☐   │ SCREEN TYPE                │ DESCRIPTION                              │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Dashboard Home             │ KPI cards, charts, data table, filters   │
│     │                            │ Best for: Executive overview, metrics    │
│     │                            │ Components: 4-6 KPI cards, 2-3 charts,   │
│     │                            │             1 data table                 │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Detail View                │ Single item details, tabs, actions       │
│     │                            │ Best for: Record details, drilldown      │
│     │                            │ Components: Header, tabs, action buttons,│
│     │                            │             related items                │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ List/Table View            │ Sortable table, bulk actions, search     │
│     │                            │ Best for: Data management, CRUD ops      │
│     │                            │ Components: Search, filters, pagination, │
│     │                            │             column controls              │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Form/Editor                │ Input fields, validation, save/cancel    │
│     │                            │ Best for: Create/edit records            │
│     │                            │ Components: Form fields, validation,     │
│     │                            │             submit buttons               │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Analytics/Reporting        │ Charts, trends, comparisons, exports     │
│     │                            │ Best for: Business intelligence, trends  │
│     │                            │ Components: Multiple charts, date range, │
│     │                            │             export options               │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Settings/Configuration     │ Editable settings, preferences, toggles  │
│     │                            │ Best for: System config, user prefs      │
│     │                            │ Components: Tabs, form fields, toggles,  │
│     │                            │             save button                  │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ User Management            │ User table, roles, permissions, actions  │
│     │                            │ Best for: Admin, user admin              │
│     │                            │ Components: User table, role selector,   │
│     │                            │             add/edit/delete buttons      │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Workflow/Process View      │ Steps, status, timeline, actions         │
│     │                            │ Best for: Multi-step processes           │
│     │                            │ Components: Step indicator, status,      │
│     │                            │             action buttons               │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Kanban Board               │ Columns, cards, drag-and-drop            │
│     │                            │ Best for: Task management, pipelines     │
│     │                            │ Components: Swimlanes, cards, filters    │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Calendar/Schedule          │ Calendar view, events, scheduling        │
│     │                            │ Best for: Appointments, deadlines        │
│     │                            │ Components: Calendar grid, event cards,  │
│     │                            │             add event modal              │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Chat/Communication         │ Message thread, compose, notifications   │
│     │                            │ Best for: Internal comms, support        │
│     │                            │ Components: Message list, compose box,   │
│     │                            │             user presence                │
├─────┼────────────────────────────┼──────────────────────────────────────────┤
│ ☐   │ Onboarding/Wizard          │ Multi-step wizard, progress bar          │
│     │                            │ Best for: Setup, guided flows            │
│     │                            │ Components: Steps, progress, next/back   │
└─────┴────────────────────────────┴──────────────────────────────────────────┘
```

---

## AI Recommendations

Based on your discovery requirements, I recommend starting with:

```
✓ RECOMMENDED SCREENS (Auto-selected based on requirements)

☑ Dashboard Home
  Why: You need visibility into [KPIs from requirements]
  Required KPIs: [List from requirements]
  Charts needed: [List from requirements]

☑ [Entity] List View
  Why: [Reason from workflows/requirements]
  Data entities: [List from data model]
  Actions needed: [CRUD operations from requirements]

☑ [Entity] Detail View
  Why: [Reason from pain points]
  Fields to display: [From data model]
  Related data: [From entity relationships]

☐ Additional Recommended:
  - [Screen type]: [Reason]
  - [Screen type]: [Reason]
```

**Question 1**: Which screens would you like to generate?

Options:

- Type "recommended" to use AI recommendations
- Type "custom" to manually select screens
- Type "all" to generate all screen types
- Type "details [screen-type]" to learn more about a screen

---

### Manual Screen Selection

**Question 2**: Select screens to generate (check boxes):

```
Enter screen numbers separated by commas (e.g., "1,2,3,5")
Or type screen names (e.g., "dashboard,detail,settings")

Selected Screens: [List]

Total screens: [X]
Estimated generation time: [Y] minutes
```

---

### Screen Dependencies

```
⚠️  DEPENDENCY CHECK

Screen: [Detail View]
Requires: [List View] to be generated first for navigation flow

Screen: [Form/Editor]
Requires: [List View] to be generated for save/cancel flow

Would you like to add missing dependencies?
- Type "yes" to add dependencies
- Type "no" to proceed without them
```

---

# STEP 3: CUSTOMIZATION

For each selected screen, let's configure the details.

---

## Global Settings

**Question 1**: Demo data configuration

```
Demo Data Volume:
- [ ] Small (50 records) - Fast generation, good for review
- [ ] Medium (100 records) - Realistic volume, balanced
- [ ] Large (500 records) - High volume, stress testing
- [ ] Extra Large (1000 records) - Production-like scale

Selected: [X records]

Data Quality:
- [ ] Realistic (names, emails, addresses match real patterns)
- [ ] Edge Cases (include nulls, long strings, special chars)
- [ ] Balanced (mix of statuses, types, etc.)
- [ ] Custom (specify data distribution)

Selected: [Quality type]
```

**Question 2**: Color scheme and branding

```
Color Scheme:
- [ ] Brand Colors (specify primary, secondary, accent)
  Primary: [#HEX] or [Name]
  Secondary: [#HEX] or [Name]
  Accent: [#HEX] or [Name]

- [ ] Default Theme
  - [ ] Blue (Professional)
  - [ ] Green (Growth-focused)
  - [ ] Purple (Creative)
  - [ ] Orange (Energetic)
  - [ ] Gray (Minimal)

- [ ] Dark Mode
- [ ] Light Mode (default)

Selected: [Theme]

Logo:
- [ ] Upload logo: [Path or URL]
- [ ] Use initials: [Company initials]
- [ ] Skip logo for now

Typography:
- [ ] Default (Inter, system fonts)
- [ ] Custom: [Font family name]
```

**Question 3**: Feature toggles

```
Global Features:
☐ Search functionality
☐ Advanced filtering
☐ Export to CSV/Excel
☐ Print view
☐ Dark mode toggle
☐ Responsive mobile design
☐ Keyboard shortcuts
☐ Notifications/alerts
☐ Help/documentation links
☐ User profile menu

Selected: [List]
```

---

## Screen-Specific Customization

### Screen 1: Dashboard Home

**Question 4a**: Which KPIs should be displayed?

```
Based on your success metrics, I recommend:

KPI Card 1:
- Metric: [From success metrics]
- Current Value: [Demo value]
- Format: [Number/Currency/Percentage/Trend]
- Comparison: [vs. last month/quarter/year]
- Trend: [Up/Down/Flat]

KPI Card 2:
- Metric: [From success metrics]
- Current Value: [Demo value]
- Format: [Type]
- Comparison: [Period]
- Trend: [Direction]

KPI Card 3:
- Metric: [From success metrics]
- Current Value: [Demo value]
- Format: [Type]
- Comparison: [Period]
- Trend: [Direction]

KPI Card 4:
- Metric: [Custom or from list]
- Current Value: [Demo value]
- Format: [Type]
- Comparison: [Period]
- Trend: [Direction]

Add more KPIs? (Up to 6 total)
- Type "yes" to add more
- Type "no" to proceed
```

**Question 4b**: Which charts should be included?

```
Chart 1:
- Type: [Line/Bar/Pie/Area/Scatter/Donut]
- Data: [What to visualize? From requirements]
- Time Range: [Last 7/30/90 days, YTD, Custom]
- Drill-down: [Yes/No]
- Filters: [What filters are available?]

Chart 2:
- Type: [Chart type]
- Data: [What to visualize?]
- Time Range: [Range]
- Drill-down: [Yes/No]
- Filters: [Filters]

Chart 3:
- Type: [Chart type]
- Data: [What to visualize?]
- Time Range: [Range]
- Drill-down: [Yes/No]
- Filters: [Filters]

Add more charts? (Up to 4 total recommended)
- Type "yes" to add more
- Type "no" to proceed
```

**Question 4c**: Data table configuration

```
Data Table:
- Entity: [What data? From data model]
- Columns to display: [Select from entity fields]
  ☐ [Field 1]
  ☐ [Field 2]
  ☐ [Field 3]
  ... (all available fields listed)

- Default sort: [Field] [Asc/Desc]
- Rows per page: [10/25/50/100]
- Filterable columns: [Which columns?]
- Searchable columns: [Which columns?]
- Actions: [View/Edit/Delete/Custom]
```

---

### Screen 2: [Selected Screen Type]

**Question 5a**: Entity and fields

```
Entity: [From data model]

Fields to display:
☐ [Field 1] - [Type] - [Label]
☐ [Field 2] - [Type] - [Label]
☐ [Field 3] - [Type] - [Label]
... (all available fields)

Field Organization:
- [ ] Single column layout
- [ ] Two column layout
- [ ] Tabs (group related fields)
  Tab 1: [Name] - Fields: [List]
  Tab 2: [Name] - Fields: [List]
  Tab 3: [Name] - Fields: [List]

Selected: [Layout]
```

**Question 5b**: Actions and interactions

```
Available Actions:
☐ Create new [entity]
☐ Edit [entity]
☐ Delete [entity]
☐ Duplicate [entity]
☐ Export [entity]
☐ Print [entity]
☐ Share [entity]
☐ Custom action: [Specify]

Selected actions: [List]

Action Placement:
- [ ] Top right (header buttons)
- [ ] Bottom right (floating action button)
- [ ] Context menu (right-click)
- [ ] Row actions (in table)

Selected: [Placement]
```

---

### Screen 3: [Selected Screen Type]

[Repeat customization questions for each selected screen]

---

## Customization Summary

```
✓ Customization Complete

Global Settings:
  - Demo Data: [X] records, [Quality type]
  - Color Scheme: [Theme]
  - Features: [Count] enabled

Screens Configured: [Count]
  1. Dashboard Home
     - KPIs: [X]
     - Charts: [Y]
     - Data Table: [Entity name]

  2. [Screen 2 Type]
     - Entity: [Name]
     - Fields: [Count]
     - Actions: [Count]

  3. [Screen 3 Type]
     - [Configuration summary]

Total Components: [X KPIs + Y charts + Z tables + A forms]
Total Demo Records: [N]
```

**Ready to generate prototype?**

- Type "yes" to proceed
- Type "back" to modify customization
- Type "preview" to see configuration details

---

# STEP 4: GENERATION

**Calling API**: POST /api/discovery/[discovery-id]/prototype

```json
{
  "discovery_id": "[discovery-id]",
  "screens": [
    {
      "type": "dashboard",
      "config": {
        "kpis": [
          {"metric": "[Metric]", "format": "[Format]", "comparison": "[Period]"}
        ],
        "charts": [
          {"type": "[Type]", "data": "[Data]", "timeRange": "[Range]"}
        ],
        "dataTable": {
          "entity": "[Entity]",
          "columns": ["[Field1]", "[Field2]"],
          "defaultSort": {"field": "[Field]", "order": "asc"},
          "rowsPerPage": 25
        }
      }
    },
    {
      "type": "detail",
      "config": {
        "entity": "[Entity]",
        "fields": ["[Field1]", "[Field2]"],
        "layout": "two-column",
        "actions": ["edit", "delete", "duplicate"]
      }
    }
  ],
  "demo_data": {
    "volume": 100,
    "quality": "realistic"
  },
  "branding": {
    "colorScheme": "[Theme]",
    "logo": "[URL or null]",
    "typography": "[Font family]"
  },
  "features": ["search", "export", "responsive"]
}
```

---

## Generation Progress

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ PROTOTYPE GENERATION IN PROGRESS                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

[████████████████████████████████████████] 100% Complete

✓ Step 1: Analyzing discovery requirements... DONE (2s)
✓ Step 2: Generating data model... DONE (3s)
✓ Step 3: Creating demo data ([X] records)... DONE (5s)
✓ Step 4: Generating screen layouts... DONE (8s)
  ✓ Dashboard Home
  ✓ [Screen 2]
  ✓ [Screen 3]
✓ Step 5: Configuring navigation flow... DONE (2s)
✓ Step 6: Applying branding and theme... DONE (3s)
✓ Step 7: Building interactive prototype... DONE (10s)
✓ Step 8: Generating preview screenshots... DONE (5s)

Total generation time: 38 seconds

Prototype ID: proto-[discovery-id]-[timestamp]
Status: ✅ READY FOR PREVIEW
```

---

# STEP 5: PREVIEW

## Prototype Overview

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ PROTOTYPE PREVIEW                                                            ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Customer: [Company Name]                                                     ║
║ Project: [Project Name]                                                      ║
║ Discovery ID: [discovery-id]                                                 ║
║ Prototype ID: proto-[discovery-id]-[timestamp]                               ║
║ Generated: [Date Time]                                                       ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ SCREENS CREATED: [X]                                                         ║
║ DEMO RECORDS: [Y]                                                            ║
║ COMPONENTS: [Z]                                                              ║
║ NAVIGATION FLOWS: [A]                                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Screen Previews

### Screen 1: Dashboard Home

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [LOGO]                                    Search... 🔍  [User ▼]  [Help ⓘ]  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Sidebar]  ┌──────────────────────────────────────────────────────────────┐│
│             │ Dashboard Overview                                           ││
│  Dashboard  │                                                              ││
│  [Entities] │ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         ││
│  Analytics  │ │ [KPI 1] │  │ [KPI 2] │  │ [KPI 3] │  │ [KPI 4] │         ││
│  Settings   │ │ 1,234   │  │ $56.7K  │  │ 89.2%   │  │ +12.3%  │         ││
│  Users      │ │ ↑ +5%   │  │ ↑ +8%   │  │ ↓ -2%   │  │ ↑ +15%  │         ││
│             │ └─────────┘  └─────────┘  └─────────┘  └─────────┘         ││
│             │                                                              ││
│             │ ┌────────────────────────┐  ┌────────────────────────────┐  ││
│             │ │ [Chart 1: Line Graph]  │  │ [Chart 2: Bar Chart]       │  ││
│             │ │                        │  │                            │  ││
│             │ │  Trend over last 30d   │  │  Breakdown by category     │  ││
│             │ │                        │  │                            │  ││
│             │ │  ╱╲  ╱╲                │  │  ▂▄▆█▆▄▂                   │  ││
│             │ │ ╱  ╲╱  ╲               │  │  ┬ ┬ ┬ ┬ ┬ ┬ ┬            │  ││
│             │ └────────────────────────┘  └────────────────────────────┘  ││
│             │                                                              ││
│             │ [Data Table: Recent [Entity Name]]                           ││
│             │ ┌────────┬──────────┬──────────┬──────────┬──────────────┐  ││
│             │ │ Name   │ Status   │ Value    │ Date     │ Actions      │  ││
│             │ ├────────┼──────────┼──────────┼──────────┼──────────────┤  ││
│             │ │ Item 1 │ Active   │ $1,234   │ 12/01/24 │ View Edit 🗑 │  ││
│             │ │ Item 2 │ Pending  │ $2,345   │ 12/02/24 │ View Edit 🗑 │  ││
│             │ │ Item 3 │ Complete │ $3,456   │ 12/03/24 │ View Edit 🗑 │  ││
│             │ │ Item 4 │ Active   │ $4,567   │ 12/04/24 │ View Edit 🗑 │  ││
│             │ │ Item 5 │ Pending  │ $5,678   │ 12/05/24 │ View Edit 🗑 │  ││
│             │ └────────┴──────────┴──────────┴──────────┴──────────────┘  ││
│             │ Showing 1-5 of 100 | [< Prev] [1] [2] [3] ... [20] [Next >]││
│             └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
```

**Demo Data Preview** (First 5 rows):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ DEMO DATA: [Entity Name] (Showing 5 of 100 records)                         │
├────┬──────────────────┬──────────┬──────────┬────────────┬─────────────────┤
│ ID │ Name             │ Status   │ Value    │ Date       │ Additional Info │
├────┼──────────────────┼──────────┼──────────┼────────────┼─────────────────┤
│  1 │ Acme Corp Lead   │ Active   │ $1,234   │ 2024-12-01 │ High priority   │
│  2 │ TechStart Opp    │ Pending  │ $2,345   │ 2024-12-02 │ Follow-up req   │
│  3 │ Global Retail    │ Complete │ $3,456   │ 2024-12-03 │ Closed won      │
│  4 │ FinServ Partners │ Active   │ $4,567   │ 2024-12-04 │ Negotiation     │
│  5 │ MedTech Solutions│ Pending  │ $5,678   │ 2024-12-05 │ Proposal sent   │
└────┴──────────────────┴──────────┴──────────┴────────────┴─────────────────┘

View full dataset: /downloads/demo-data-[entity]-[prototype-id].csv
```

---

### Screen 2: [Screen Type Name]

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [LOGO]                                    Search... 🔍  [User ▼]  [Help ⓘ]  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Sidebar]  ┌──────────────────────────────────────────────────────────────┐│
│             │ [Screen Title]                                               ││
│  Dashboard  │                                                              ││
│  [Entities] │ [Screen-specific content - ASCII wireframe visualization]   ││
│  Analytics  │                                                              ││
│  Settings   │ [Component 1]                                                ││
│  Users      │                                                              ││
│             │ [Component 2]                                                ││
│             │                                                              ││
│             │ [Component 3]                                                ││
│             │                                                              ││
│             │ [Actions/Buttons]                                            ││
│             └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
```

**Interactive Elements**:

- [List interactive features: buttons, forms, filters, etc.]
- [Show sample interactions: "Click Edit → Opens modal", etc.]

---

### Screen 3: [Screen Type Name]

[ASCII wireframe for this screen]

---

## Navigation Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ NAVIGATION FLOW                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          [Dashboard Home]                                    │
│                                   │                                          │
│                    ┌──────────────┼──────────────┐                           │
│                    ▼              ▼              ▼                           │
│            [[Entity] List]  [Analytics]  [Settings]                          │
│                    │                                                         │
│         ┌──────────┼──────────┐                                              │
│         ▼          ▼          ▼                                              │
│    [View Item] [Edit Item] [Delete Item]                                    │
│         │          │                                                         │
│         │          ▼                                                         │
│         │    [Edit Form]                                                     │
│         │          │                                                         │
│         │    ┌─────┴─────┐                                                   │
│         │    ▼           ▼                                                   │
│         │  [Save]    [Cancel]                                                │
│         │    │           │                                                   │
│         │    └─────┬─────┘                                                   │
│         │          ▼                                                         │
│         └───► [Detail View]                                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Inventory

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ COMPONENT SUMMARY                                                            ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ KPI Cards: [X]                                                               ║
║   - [KPI 1 Name]: [Format]                                                   ║
║   - [KPI 2 Name]: [Format]                                                   ║
║   - [KPI 3 Name]: [Format]                                                   ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Charts: [Y]                                                                  ║
║   - [Chart 1]: [Type] - [Data source]                                        ║
║   - [Chart 2]: [Type] - [Data source]                                        ║
║   - [Chart 3]: [Type] - [Data source]                                        ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Data Tables: [Z]                                                             ║
║   - [Table 1]: [Entity] - [Row count] rows                                   ║
║   - [Table 2]: [Entity] - [Row count] rows                                   ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Forms: [A]                                                                   ║
║   - [Form 1]: [Entity] - [Field count] fields                                ║
║   - [Form 2]: [Entity] - [Field count] fields                                ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Navigation Elements: [B]                                                     ║
║   - Sidebar menu: [Link count] links                                         ║
║   - Top navigation: [Link count] links                                       ║
║   - Breadcrumbs: Yes                                                         ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Interactive Elements: [C]                                                    ║
║   - Buttons: [Count]                                                         ║
║   - Modals/Dialogs: [Count]                                                  ║
║   - Filters: [Count]                                                         ║
║   - Search bars: [Count]                                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Demo Data Statistics

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ DEMO DATA SUMMARY                                                            ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Total Records Generated: [X]                                                 ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ [Entity 1]: [Count] records                                                  ║
║   - Status Distribution:                                                     ║
║     • Active: [X] ([%])                                                      ║
║     • Pending: [Y] ([%])                                                     ║
║     • Complete: [Z] ([%])                                                    ║
║   - Value Range: $[Min] - $[Max]                                             ║
║   - Date Range: [Start] to [End]                                             ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ [Entity 2]: [Count] records                                                  ║
║   - Distribution: [Details]                                                  ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ [Entity 3]: [Count] records                                                  ║
║   - Distribution: [Details]                                                  ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Data Quality:                                                                ║
║   ✓ Realistic names and addresses                                            ║
║   ✓ Valid email formats                                                      ║
║   ✓ Proper phone number formats                                              ║
║   ✓ Logical relationships between entities                                   ║
║   ✓ Edge cases included (nulls, long strings)                                ║
║   ✓ Balanced distribution across categories                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Download Demo Data**:

- CSV: `/downloads/demo-data-all-[prototype-id].csv`
- JSON: `/downloads/demo-data-all-[prototype-id].json`
- SQL: `/downloads/demo-data-all-[prototype-id].sql`

---

## Technical Specifications

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ TECHNICAL DETAILS                                                            ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Framework: React 18.x + TypeScript                                           ║
║ UI Library: Tailwind CSS + shadcn/ui                                         ║
║ Charts: Recharts / Chart.js                                                  ║
║ Data Management: TanStack Table + React Query                                ║
║ Forms: React Hook Form + Zod validation                                      ║
║ Routing: React Router v6                                                     ║
║ State Management: Zustand / Context API                                      ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Responsive: ✓ Mobile, Tablet, Desktop                                        ║
║ Accessibility: ✓ WCAG 2.1 AA compliant                                       ║
║ Performance: ✓ Code splitting, lazy loading                                  ║
║ SEO: ✓ Meta tags, structured data                                            ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Deployment:                                                                  ║
║   Platform: Vercel                                                           ║
║   Build time: ~2 minutes                                                     ║
║   Environment: Production-ready                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

# STEP 6: ACTIONS

Now that your prototype is ready, choose what to do next:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ AVAILABLE ACTIONS                                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. 🚀 Deploy to Vercel                                                      │
│     Deploy prototype to live URL for customer review                        │
│     Estimated time: 2-3 minutes                                              │
│     Output: Live URL + QR code                                               │
│                                                                              │
│  2. 🔄 Regenerate Screen                                                     │
│     Make changes to a specific screen based on feedback                     │
│     Estimated time: 30 seconds per screen                                    │
│                                                                              │
│  3. 📤 Export to Figma                                                       │
│     Export prototype as Figma design for design review                      │
│     Estimated time: 1 minute                                                 │
│     Output: Figma file URL                                                   │
│                                                                              │
│  4. 📄 Export to PDF                                                         │
│     Generate PDF documentation with all screens and data                    │
│     Estimated time: 30 seconds                                               │
│     Output: PDF file download                                                │
│                                                                              │
│  5. 📊 Generate Presentation                                                 │
│     Create PowerPoint/Google Slides for stakeholder review                  │
│     Estimated time: 1 minute                                                 │
│     Output: PPTX file download                                               │
│                                                                              │
│  6. ✅ Approve & Proceed to Technical Design                                 │
│     Mark prototype as approved and generate technical spec                  │
│     Estimated time: 5 minutes                                                │
│     Output: Technical design document                                        │
│                                                                              │
│  7. 💬 Request Customer Feedback                                             │
│     Send prototype to customer for review and feedback                      │
│     Output: Feedback form link                                               │
│                                                                              │
│  8. 🗑️  Discard Prototype                                                    │
│     Delete this prototype and start over                                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Which action would you like to take?**
Type the number or name (e.g., "1", "deploy", "export to pdf")

---

## ACTION 1: Deploy to Vercel

**Calling API**: POST /api/prototype/[prototype-id]/deploy

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ DEPLOYING TO VERCEL                                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

[████████████████████████████████████████] 100% Complete

✓ Step 1: Building production bundle... DONE (45s)
✓ Step 2: Optimizing assets... DONE (15s)
✓ Step 3: Uploading to Vercel... DONE (20s)
✓ Step 4: Deploying to edge network... DONE (10s)
✓ Step 5: Running deployment checks... DONE (5s)

Total deployment time: 95 seconds

╔══════════════════════════════════════════════════════════════════════════════╗
║ ✅ DEPLOYMENT SUCCESSFUL                                                     ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Live URL: https://[company-name]-[project-slug].vercel.app                   ║
║                                                                              ║
║ QR Code:                                                                     ║
║  ┌─────────────────────┐                                                     ║
║  │ ███ ▄▄▄ █▀▄ ▄▄▄ ███ │  Scan to view prototype on mobile                  ║
║  │ █   █ █ ██▀ █ █   █ │                                                     ║
║  │ █ ▀ ▀ ▀ ██▀ ▀ ▀ ▀ █ │                                                     ║
║  │ ▀▀▀▀▀▀▀ ▀ ▀ ▀▀▀▀▀▀▀ │                                                     ║
║  │   ▀█ ▀  ▀ ▀  ▀█ ▀   │                                                     ║
║  │ ▀ █ █ ▀ ▀ ▀ ▀ █ █ ▀ │                                                     ║
║  │ ███ ▀▀▀ ▀▀▀ ▀▀▀ ███ │                                                     ║
║  └─────────────────────┘                                                     ║
║                                                                              ║
║ Deployment Details:                                                          ║
║   - Build ID: [build-id]                                                     ║
║   - Region: Global Edge Network                                              ║
║   - Status: Active                                                           ║
║   - SSL: Enabled (Auto HTTPS)                                                ║
║   - Analytics: Enabled                                                       ║
║                                                                              ║
║ Admin Access:                                                                ║
║   - Dashboard: https://vercel.com/[org]/[project]                            ║
║   - Logs: https://vercel.com/[org]/[project]/deployments                     ║
║                                                                              ║
║ Sharing:                                                                     ║
║   - Email template generated: /downloads/prototype-email-[id].html           ║
║   - Social share image: /downloads/prototype-og-[id].png                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Share Prototype**:

Email template generated and ready to send:

```
Subject: [Project Name] Prototype Ready for Review

Hi [Customer Name],

Your prototype for [Project Name] is now live and ready for review!

🔗 View Prototype: https://[company-name]-[project-slug].vercel.app

What's Included:
✓ [X] interactive screens
✓ [Y] demo records
✓ Fully functional navigation
✓ Mobile responsive design

Please review and provide feedback:
📝 Feedback Form: [URL]

Key Features to Test:
1. [Feature 1]
2. [Feature 2]
3. [Feature 3]

Questions? Reply to this email or schedule a review call.

Best regards,
[Your Name]
```

---

## ACTION 2: Regenerate Screen

**Question**: Which screen would you like to regenerate?

```
Available screens:
1. Dashboard Home
2. [Screen 2 Name]
3. [Screen 3 Name]

Type screen number or name.
```

**Question**: What changes would you like to make?

```
Current configuration for [Screen Name]:
[Show current config]

What to change:
- [ ] Add/remove components
- [ ] Change layout
- [ ] Modify demo data
- [ ] Update colors/styling
- [ ] Add/remove features
- [ ] Other (specify)

Describe changes:
[User input]
```

**Calling API**: POST /api/prototype/[prototype-id]/regenerate-screen

```
Regenerating [Screen Name]...

[████████████████████████████████████████] 100% Complete

✓ Screen regenerated successfully
✓ Demo data updated
✓ Navigation flow maintained
✓ Prototype redeployed (if previously deployed)

Preview updated screen:
[Show ASCII wireframe of updated screen]

Is this correct?
- Type "yes" to accept
- Type "no" to try again
```

---

## ACTION 3: Export to Figma

**Calling API**: POST /api/prototype/[prototype-id]/export-figma

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ EXPORTING TO FIGMA                                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

[████████████████████████████████████████] 100% Complete

✓ Step 1: Converting screens to Figma frames... DONE
✓ Step 2: Creating component library... DONE
✓ Step 3: Setting up design tokens... DONE
✓ Step 4: Generating auto-layout... DONE
✓ Step 5: Uploading to Figma... DONE

╔══════════════════════════════════════════════════════════════════════════════╗
║ ✅ FIGMA EXPORT SUCCESSFUL                                                   ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Figma File: https://figma.com/file/[file-id]/[project-name]                  ║
║                                                                              ║
║ Contents:                                                                    ║
║   📄 Pages: [X]                                                              ║
║      - Screens (all [X] screens)                                             ║
║      - Components (reusable components)                                      ║
║      - Design Tokens (colors, typography, spacing)                           ║
║      - Demo Data (sample content)                                            ║
║                                                                              ║
║   🎨 Components: [Y]                                                         ║
║      - KPI Card                                                              ║
║      - Chart variants                                                        ║
║      - Data table                                                            ║
║      - Form fields                                                           ║
║      - Buttons                                                               ║
║      - Navigation                                                            ║
║                                                                              ║
║   🔤 Design Tokens:                                                          ║
║      - Color palette ([count] colors)                                        ║
║      - Typography scale ([count] styles)                                     ║
║      - Spacing system (8px grid)                                             ║
║      - Border radius values                                                  ║
║                                                                              ║
║ Access:                                                                      ║
║   - Shared with: [Customer email]                                            ║
║   - Permission: Can view/Can edit                                            ║
║   - Expires: Never / [Date]                                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ACTION 4: Export to PDF

**Calling API**: POST /api/prototype/[prototype-id]/export-pdf

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ GENERATING PDF DOCUMENTATION                                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

[████████████████████████████████████████] 100% Complete

✓ Step 1: Rendering all screens... DONE
✓ Step 2: Generating flow diagrams... DONE
✓ Step 3: Creating data samples... DONE
✓ Step 4: Formatting documentation... DONE
✓ Step 5: Building PDF... DONE

╔══════════════════════════════════════════════════════════════════════════════╗
║ ✅ PDF EXPORT SUCCESSFUL                                                     ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ File: /downloads/prototype-[project-slug]-[date].pdf                         ║
║ Size: [X] MB                                                                 ║
║ Pages: [Y]                                                                   ║
║                                                                              ║
║ Contents:                                                                    ║
║   1. Cover Page                                                              ║
║   2. Executive Summary                                                       ║
║   3. Discovery Summary                                                       ║
║   4. Screen Previews ([X] screens)                                           ║
║   5. Navigation Flow Diagram                                                 ║
║   6. Component Inventory                                                     ║
║   7. Demo Data Samples                                                       ║
║   8. Technical Specifications                                                ║
║   9. Next Steps                                                              ║
║                                                                              ║
║ Download: /downloads/prototype-[project-slug]-[date].pdf                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ACTION 5: Generate Presentation

**Calling API**: POST /api/prototype/[prototype-id]/export-presentation

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ GENERATING STAKEHOLDER PRESENTATION                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

[████████████████████████████████████████] 100% Complete

✓ Step 1: Creating slide layouts... DONE
✓ Step 2: Adding screenshots... DONE
✓ Step 3: Generating talking points... DONE
✓ Step 4: Building presentation... DONE

╔══════════════════════════════════════════════════════════════════════════════╗
║ ✅ PRESENTATION EXPORT SUCCESSFUL                                            ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ File: /downloads/prototype-presentation-[project-slug].pptx                  ║
║ Slides: [X]                                                                  ║
║                                                                              ║
║ Slide Breakdown:                                                             ║
║   1. Title Slide                                                             ║
║   2. Agenda                                                                  ║
║   3. Problem Statement (pain points)                                         ║
║   4. Proposed Solution (overview)                                            ║
║   5-[X]. Screen Previews (one per screen)                                    ║
║   [X+1]. Navigation Flow                                                     ║
║   [X+2]. Technical Architecture                                              ║
║   [X+3]. Success Metrics                                                     ║
║   [X+4]. Timeline & Budget                                                   ║
║   [X+5]. Next Steps                                                          ║
║   [X+6]. Q&A                                                                 ║
║                                                                              ║
║ Speaker Notes: ✓ Included on every slide                                     ║
║ Animations: ✓ Subtle transitions                                             ║
║ Branding: ✓ Company colors and logo                                          ║
║                                                                              ║
║ Download: /downloads/prototype-presentation-[project-slug].pptx              ║
║ Google Slides: [URL] (if requested)                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ACTION 6: Approve & Proceed to Technical Design

**Question**: Is this prototype approved by the customer?

```
Before proceeding to technical design, please confirm:

✓ Customer has reviewed the prototype
✓ All screens are approved
✓ Demo data is representative
✓ Navigation flow is correct
✓ Features align with requirements
✓ Stakeholders have signed off

Type "yes" to confirm approval and proceed
Type "no" to cancel
```

**APPROVAL CONFIRMATION**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ PROTOTYPE APPROVAL                                                           ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Customer: [Company Name]                                                     ║
║ Project: [Project Name]                                                      ║
║ Prototype ID: proto-[discovery-id]-[timestamp]                               ║
║                                                                              ║
║ Approved by: [Name]                                                          ║
║ Title: [Title]                                                               ║
║ Date: [Date Time]                                                            ║
║ Signature: [Digital signature]                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Calling API**: POST /api/prototype/[prototype-id]/approve

**Calling API**: POST /api/technical-design/generate

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ GENERATING TECHNICAL DESIGN SPECIFICATION                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

[████████████████████████████████████████] 100% Complete

✓ Step 1: Analyzing prototype components... DONE
✓ Step 2: Designing database schema... DONE
✓ Step 3: Defining API endpoints... DONE
✓ Step 4: Creating architecture diagram... DONE
✓ Step 5: Generating security specs... DONE
✓ Step 6: Creating deployment plan... DONE
✓ Step 7: Estimating development timeline... DONE
✓ Step 8: Building technical document... DONE

╔══════════════════════════════════════════════════════════════════════════════╗
║ ✅ TECHNICAL DESIGN COMPLETE                                                 ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Technical Design ID: tech-[prototype-id]-[timestamp]                         ║
║                                                                              ║
║ Document Contents:                                                           ║
║   1. System Architecture                                                     ║
║      - Frontend: React + TypeScript                                          ║
║      - Backend: Node.js + Express / Python + FastAPI                         ║
║      - Database: PostgreSQL                                                  ║
║      - Cache: Redis                                                          ║
║      - Storage: AWS S3 / Cloudflare R2                                       ║
║      - Hosting: Vercel (frontend), Railway/Fly.io (backend)                  ║
║                                                                              ║
║   2. Database Schema                                                         ║
║      - [X] tables defined                                                    ║
║      - All relationships mapped                                              ║
║      - Indexes optimized                                                     ║
║      - Migration scripts included                                            ║
║                                                                              ║
║   3. API Design                                                              ║
║      - [Y] endpoints defined                                                 ║
║      - OpenAPI/Swagger spec generated                                        ║
║      - Authentication flow documented                                        ║
║      - Rate limiting specified                                               ║
║                                                                              ║
║   4. Security Specifications                                                 ║
║      - Authentication: JWT-based                                             ║
║      - Authorization: RBAC                                                   ║
║      - Encryption: TLS 1.3, AES-256                                          ║
║      - Compliance: [GDPR/HIPAA/etc.]                                         ║
║                                                                              ║
║   5. Development Plan                                                        ║
║      - Timeline: [X] weeks                                                   ║
║      - Team size: [Y] developers                                             ║
║      - Sprints: [Z] (2-week sprints)                                         ║
║      - Milestones: [Count] defined                                           ║
║                                                                              ║
║   6. Testing Strategy                                                        ║
║      - Unit tests: [Framework]                                               ║
║      - Integration tests: [Framework]                                        ║
║      - E2E tests: Playwright/Cypress                                         ║
║      - Performance tests: k6                                                 ║
║                                                                              ║
║   7. Deployment Plan                                                         ║
║      - CI/CD: GitHub Actions                                                 ║
║      - Environments: Dev, Staging, Prod                                      ║
║      - Monitoring: Sentry, Datadog                                           ║
║      - Backup strategy: Daily automated                                      ║
║                                                                              ║
║ Files Generated:                                                             ║
║   📄 Technical Spec: /downloads/tech-spec-[project-slug].pdf                 ║
║   📊 Architecture Diagram: /downloads/architecture-[project-slug].png        ║
║   🗄️  Database Schema: /downloads/db-schema-[project-slug].sql               ║
║   🔌 API Spec: /downloads/api-spec-[project-slug].yaml (OpenAPI 3.0)         ║
║   📅 Project Plan: /downloads/project-plan-[project-slug].xlsx               ║
║                                                                              ║
║ Estimated Budget: $[X] - $[Y]                                                ║
║ Estimated Timeline: [Z] weeks                                                ║
║                                                                              ║
║ Next Step: Begin Development                                                 ║
║   Command: /dev:start-project [technical-design-id]                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ACTION 7: Request Customer Feedback

**Calling API**: POST /api/prototype/[prototype-id]/request-feedback

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ FEEDBACK REQUEST SENT                                                        ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Email sent to:                                                               ║
║   - [Primary Contact Email]                                                  ║
║   - [Stakeholder 1 Email]                                                    ║
║   - [Stakeholder 2 Email]                                                    ║
║                                                                              ║
║ Feedback Form: https://feedback.app/[prototype-id]                           ║
║                                                                              ║
║ Questions Asked:                                                             ║
║   1. Does this prototype address your pain points? (Yes/No + Comments)       ║
║   2. Are the workflows intuitive? (1-5 scale + Comments)                     ║
║   3. Is any important functionality missing? (Open text)                     ║
║   4. What would you change about the design? (Open text)                     ║
║   5. Are you ready to approve this prototype? (Yes/No + Comments)            ║
║                                                                              ║
║ Notification: You'll receive an email when feedback is submitted             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## COMPLETION SUMMARY

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ ✅ PROTOTYPE GENERATION COMPLETE                                             ║
╟──────────────────────────────────────────────────────────────────────────────╢
║ Discovery ID: [discovery-id]                                                 ║
║ Prototype ID: proto-[discovery-id]-[timestamp]                               ║
║                                                                              ║
║ Customer: [Company Name]                                                     ║
║ Project: [Project Name]                                                      ║
║                                                                              ║
║ Generated:                                                                   ║
║   ✓ Screens: [X]                                                             ║
║   ✓ Components: [Y]                                                          ║
║   ✓ Demo Records: [Z]                                                        ║
║   ✓ Navigation Flows: [A]                                                    ║
║                                                                              ║
║ Outputs:                                                                     ║
║   🌐 Live URL: https://[company-name]-[project-slug].vercel.app              ║
║   🎨 Figma: https://figma.com/file/[file-id]/[project-name]                  ║
║   📄 PDF: /downloads/prototype-[project-slug].pdf                            ║
║   📊 Presentation: /downloads/prototype-presentation-[project-slug].pptx     ║
║                                                                              ║
║ Status: [Pending Review / Approved]                                          ║
║                                                                              ║
║ Next Steps:                                                                  ║
║   1. Customer reviews prototype                                              ║
║   2. Gather and incorporate feedback                                         ║
║   3. Obtain approval                                                         ║
║   4. Proceed to technical design                                             ║
║   5. Begin development                                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## WHAT'S NEXT?

**Project Progression**:

```
[✓] Discovery        → COMPLETE
[✓] Prototype        → COMPLETE
[ ] Technical Design → /design:technical-spec [prototype-id]
[ ] Development      → /dev:start-project [tech-design-id]
[ ] Testing          → /dev:test-project [project-id]
[ ] Deployment       → /devops:deploy [project-id]
[ ] Launch           → /product:launch [project-id]
```

**Available Commands**:

- View all prototypes: `/design:list-prototypes`
- Edit this prototype: `/design:prototype [prototype-id] --edit`
- Create new prototype: `/design:prototype [new-discovery-id]`
- Generate tech spec: `/design:technical-spec [prototype-id]`

---

## PROTOTYPE SAVED

```json
{
  "prototype_id": "proto-[discovery-id]-[timestamp]",
  "discovery_id": "[discovery-id]",
  "customer": {
    "company_name": "[Company Name]",
    "project_name": "[Project Name]"
  },
  "screens": [
    {
      "type": "dashboard",
      "components": {
        "kpis": [{"metric": "[Metric]", "value": "[Value]"}],
        "charts": [{"type": "[Type]", "data": "[Data]"}],
        "tables": [{"entity": "[Entity]", "rows": 100}]
      }
    }
  ],
  "demo_data": {
    "total_records": 100,
    "entities": [
      {"name": "[Entity 1]", "count": 100},
      {"name": "[Entity 2]", "count": 50}
    ]
  },
  "deployments": {
    "vercel_url": "https://[url]",
    "figma_url": "https://[url]",
    "pdf_path": "/downloads/[file].pdf"
  },
  "status": "pending_review|approved",
  "approval": {
    "approved_by": "[Name]",
    "date": "[Date]",
    "signature": "[Signature]"
  },
  "created_at": "[ISO DateTime]",
  "updated_at": "[ISO DateTime]"
}
```

**Saved to database**: ✓

---

## END OF PROTOTYPE WORKFLOW

🎉 Your prototype is ready! Share it with your customer and gather feedback.

Type "help" to see all available commands or "exit" to return to main menu.
