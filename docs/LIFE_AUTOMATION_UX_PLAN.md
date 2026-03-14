# Life Automation UX Plan + Agent Jumbo Integration

This document defines the UX plan for the proposed life-automation systems and how they integrate into Agent Jumbo's existing WebUI, tools, and data model.

## UX Principles

- Single-command entry: every flow can start from chat with a natural-language command.
- Dashboard-first visibility: each system has a lightweight dashboard card and a detail view.
- Actionable notifications: push or toast notifications always include a primary action.
- Cross-linking: items link to related entities (client, property, workflow, task).

## Systems and UX

### 1) Calendar & Scheduling Hub

**Primary goal**: unify meetings, reminders, and auto-prep/follow-up.

**Entry points**

- Sidebar quick action: "Schedule"
- Dashboard card: "Next 7 days"
- Chat commands: "schedule", "reschedule", "prep brief"

**Key screens**

- Calendar overview: week/month grid with filters (Work, Personal, Client)
- Meeting detail: agenda, prep checklist, related emails, action buttons
- Scheduling rules: availability windows, buffer rules, conflict policy

**Key flows**

- Create event from chat -> time suggestions -> confirm -> invite -> auto-follow-up task.
- "Prep brief" -> digest of relevant emails, files, notes.
- "Auto-reschedule" when conflict is detected.

**Notifications**

- T-24h and T-1h reminder with "Open agenda" action.
- Conflict alert with "Propose new time" action.

**Integration points**

- Tool: `calendar_hub` (new), uses `scheduler` for reminders.
- Gmail integration for invites and email parsing.
- Workflow link to create "Meeting outcomes" tasks.

**Implementation requirements (full)**

- WebUI: new dashboard card + detail view, meeting detail modal, rule editor.
- Backend tool: `calendar_hub` (create/update/delete, availability, conflict detection, prep briefs).
- Integrations: Google Calendar API, Microsoft Graph Calendar API, Gmail API for invites and replies.
- Data: calendar accounts, calendar mappings, meeting prep sources, follow-up templates.
- Scheduler: reminder jobs + follow-up tasks via `scheduler.py`.
- Notifications: reminders, conflicts, follow-ups, changes sync alerts.
- Security: OAuth2 token storage, least-privilege scopes, audit logs.
- Tests: API integration mocks, scheduling conflict rules, reminder and follow-up flows.

---

### 2) Unified Personal Ops Dashboard ("Life OS")

**Primary goal**: one screen for tasks, commitments, and priorities.

**Entry points**

- Sidebar dashboard icon (new)
- Welcome screen tile: "Life OS"

**Key screens**

- Today overview: top 3 priorities, upcoming events, inbox triage count.
- Projects strip: active projects with status and next action.
- Health/time widget: deep work % and energy check-in.

**Key flows**

- Morning check-in -> auto-generate "Today plan" -> schedule focus blocks.
- Weekly review -> summary + declutter inbox tasks.

**Notifications**

- Daily brief at configured time.
- "Overloaded day" warning with "Rebalance" action.

**Integration points**

- Aggregates across Workflow Engine, Scheduler, Email, Properties, CRM.
- Uses `digest_builder` for daily/weekly summaries.

**Implementation requirements (full)**

- WebUI: Life OS dashboard, widgets (tasks/events/pipeline/finance), filterable timeline.
- Backend tool: `life_os` (aggregate view, personalized daily plan, weekly review).
- Data: unified activity feed schema; links to workflows, tasks, properties, pipeline.
- Scheduler: daily brief + weekly review generation jobs.
- Notifications: overload alerts, missed priority nudges, daily brief delivery.
- Security: role-based access for sensitive panels (finance, personal).
- Tests: aggregation correctness, widget filters, notification triggers.

---

### 3) Personal/Business Finance Automation

**Primary goal**: track cashflow, expenses, and automation ROI.

**Entry points**

- Dashboard card: "Cashflow this month"
- Chat: "Import receipts", "Show tax estimate"

**Key screens**

- Transactions inbox: uncategorized items with one-click categories.
- Cashflow view: income vs expenses, projections.
- Tax estimates: quarterly estimate panel.

**Key flows**

- Receipt upload -> OCR -> category suggestion -> approve.
- Monthly close -> generate report -> send via email.

**Notifications**

- "High spend category" alert with "Review" action.
- Tax payment reminders.

**Integration points**

- Tool: `finance_manager` (new), optional connectors.
- Links to Property Manager expenses and Business X-Ray ROI.

**Implementation requirements (full)**

- WebUI: transactions inbox, categorization UI, cashflow charts, tax estimates.
- Backend tool: `finance_manager` (sync, categorize, report, tax estimate).
- Integrations: bank/credit feeds (Plaid/Stripe/QuickBooks), OCR (Tesseract/Cloud Vision).
- Data: transaction ledger, categories, receipt store, tax rules, property expense linkage.
- Scheduler: monthly close, tax reminder tasks, anomaly checks.
- Notifications: high-spend alerts, uncategorized backlog, tax deadlines.
- Security: encrypted receipts, scoped tokens, audit trails, PII handling.
- Tests: categorization accuracy, OCR pipeline, report generation, ROI link.

---

### 4) Relationship CRM (Personal + Business)

**Primary goal**: manage relationships and touchpoints.

**Entry points**

- Dashboard card: "Keep-in-touch"
- Chat: "Log interaction with ..."

**Key screens**

- Contacts list with tags (Client, Friend, Vendor).
- Contact detail: last interaction, next reminder, notes.
- Relationship pipeline: warm/cold/at-risk.

**Key flows**

- Email arrives -> auto-tag contact -> create follow-up reminder.
- "Introduce" -> suggests warm connections based on tags.

**Notifications**

- "No touch in 30 days" with "Send check-in" action.

**Integration points**

- Gmail metadata and `customer_lifecycle` data.
- Optional Slack/Telegram identity linking.

---

### 5) Document Automation + E-Sign

**Primary goal**: templated docs, approvals, and signatures.

**Entry points**

- Chat: "Generate contract for ..."
- Dashboard card: "Pending signatures"

**Key screens**

- Template library with versioning.
- Document detail: status, recipients, audit trail.
- Approval flow: reviewer steps, comments, final send.

**Key flows**

- Generate doc -> auto-fill data -> review -> send -> track status.
- "Renewal reminder" -> reissue updated agreement.

**Notifications**

- "Signature received" with "Archive" action.
- "Stalled approval" with "Nudge" action.

**Integration points**

- Tool: `doc_automation` (new).
- Email integration for delivery and reminders.

---

### 6) Home/Asset Maintenance Manager

**Primary goal**: track maintenance schedules, warranties, and vendors.

**Entry points**

- Dashboard card: "Upcoming maintenance"
- Chat: "Add maintenance schedule for ..."

**Key screens**

- Asset list: vehicles, appliances, equipment.
- Maintenance calendar: next due items.
- Vendor list with contact and service history.

**Key flows**

- Add asset -> import warranty details -> schedule service.
- Maintenance due -> create task -> notify vendor.

**Notifications**

- "Service due in 14 days" with "Schedule" action.

**Integration points**

- Reuses `scheduler` and `notifications`.
- Links to Property Manager where relevant.

---

### 7) Health & Habit Tracker

**Primary goal**: simple daily tracking and coaching nudges.

**Entry points**

- Morning/Evening check-in prompt.
- Chat: "Log workout", "Start 7-day sleep reset"

**Key screens**

- Daily check-in: mood, energy, sleep.
- Habit streaks with small charts.
- Goal view: active habits and weekly targets.

**Key flows**

- Daily check-in -> suggest 1 small action.
- "Weekly recap" -> digest + next week plan.

**Notifications**

- Gentle nudges for missed habit.

**Integration points**

- `scheduler` for check-ins, `digest_builder` for recaps.
- Optional device sync (future).

---

### 8) Communication Inbox Router

**Primary goal**: unify inbound channels and triage.

**Entry points**

- Inbox router dashboard.
- Chat: "Triage inbox"

**Key screens**

- Unified inbox with channel filters (Gmail, Telegram, Slack, SMS).
- Triage lane: urgent, important, low.
- Rules page: if-then routing rules.

**Key flows**

- New message -> classify -> auto-route to workflow or task.
- Bulk archive with "summarize 20 messages" action.

**Notifications**

- "High priority message" alert with "Reply" action.

**Integration points**

- Gmail and Telegram are already supported; add Slack/SMS connectors.
- Uses Workflow Engine to create tasks.

---

### 9) Travel & Logistics Concierge

**Primary goal**: consolidate itineraries and plan logistics.

**Entry points**

- Dashboard card: "Next trip"
- Chat: "Build itinerary from emails"

**Key screens**

- Itinerary view: flights, lodging, meetings, map links.
- Packing checklist with reminders.
- Expense capture for travel.

**Key flows**

- Parse booking emails -> build itinerary -> add to calendar.
- "Travel day" -> auto-send agenda and hotel details.

**Notifications**

- "Check-in opens" alert with "Open airline" action.

**Integration points**

- Email parsing + calendar hub.
- Finance tool for receipts.

## Agent Jumbo Integration Map

**WebUI**

- Add a "Life OS" dashboard and additional dashboards per system as needed.
- Reuse `webui/dashboards/dashboard-router.js` for new dashboard entries.
- Implement detail panels in `webui/components/panels/` for quick views.
- Add settings modules in `webui/components/settings/` for per-system config.

**Tools and Instruments**

- New tools: `calendar_hub`, `finance_manager`, `crm_contacts`, `doc_automation`,
  `asset_maintenance`, `habit_tracker`, `inbox_router`, `travel_concierge`.
- Each tool gets a prompt file in `prompts/` and an instrument under
  `instruments/custom/<tool>/` with SQLite data in `data/`.

**Data and Events**

- Use Notifications for high-priority actions (existing system).
- Use Scheduler for reminders and recurring check-ins.
- Use Observability for per-tool usage metrics.

## Architecture Options

### Baseline: MFE (Micro-Frontend)

Use MFEs when teams need to ship UI modules independently and at different cadences. This helps if each system becomes large and warrants separate ownership.

### Three Other Patterns to Consider

1) **Modular Monolith (Feature-Sliced UI)**
   - Why: simplest build/deploy, shared design system, fewer runtime failure points.
   - Fit: good if a single team maintains all systems and you want fast iteration.

2) **Plugin/Extension Registry**
   - Why: lets you enable/disable systems at runtime and load features by manifest.
   - Fit: aligns with Agent Jumbo's tool/instrument model and keeps the UI lightweight.

3) **Backend-Driven UI (Schema-Based)**
   - Why: ships UI changes via JSON schema without full frontend redeploys.
   - Fit: ideal for rapid iteration on forms and dashboards, reduces UI churn.

## Architecture Patterns: Pros and Cons

### MFE (Micro-Frontend)

**Pros**

- Independent deploys for each domain UI.
- Smaller bundles per feature, lazy-loaded dashboards.
- Team autonomy with clear ownership boundaries.

**Cons**

- More build/runtime complexity (version drift, routing, shared state).
- Duplicated dependencies and design system drift risk.
- Harder global performance optimization.

### Modular Monolith (Feature-Sliced UI)

**Pros**

- Simplest deploy model and shared component library.
- Easier cross-feature interactions and consistent UX.
- Lower runtime complexity and fewer integration failures.

**Cons**

- Larger release trains, less autonomy per feature.
- Risk of tight coupling as modules grow.
- Scaling teams requires stronger governance.

### Plugin/Extension Registry

**Pros**

- Enable/disable systems dynamically per user.
- Aligns with Agent Jumbo's tool/instrument design.
- Reduces baseline UI weight.

**Cons**

- Requires manifest/versioning system.
- Plugin compatibility testing overhead.
- Harder to ensure consistent UX across plugins.

### Backend-Driven UI (Schema-Based)

**Pros**

- Fast iteration without full frontend redeploys.
- Works well for form-heavy workflows and admin panels.
- Easy to roll out A/B experiments.

**Cons**

- Limited flexibility for complex interactions.
- Schema tooling and validation burden.
- Harder to achieve bespoke UX polish.

## Recommended Next Steps

1) Decide on a primary architecture (MFE vs modular monolith vs plugin registry).
2) Pick the first two systems to implement and create their dashboards/panels.
3) Define the data contracts for each new tool (inputs/outputs, entities).
