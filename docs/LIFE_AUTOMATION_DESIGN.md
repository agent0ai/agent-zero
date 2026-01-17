# Life Automation Design (MM + Plugins, Event-Driven)

This design covers the first three systems:
- Calendar & Scheduling Hub (Google first, mock OAuth, pluggable providers)
- Life OS Dashboard (event-driven, lifecycle-aware)
- Personal/Business Finance Automation (bank feeds + OCR + tax)

Architecture choice: **Modular Monolith + Plugin Registry**. Blockchain identity used for **auth** and **audit/verification**.

## 1) Architecture Overview

### 1.1 Modular Monolith (core)
- Single WebUI with feature-sliced modules for consistent UX.
- Shared state and design system in `webui/`.
- Core services live in `python/` tools and `instruments/`.

### 1.2 Plugin Registry (optional systems)
- Plugin manifest describes UI panels, dashboard cards, tools, and events.
- Allows feature toggles and staged rollout per system.

**Proposed manifest (JSON)**
```json
{
  "id": "calendar_hub",
  "version": "0.1.0",
  "ui": {
    "dashboard_card": "dashboards/calendar/calendar-dashboard.html",
    "panel": "components/panels/calendar-panel.html"
  },
  "tools": ["calendar_hub"],
  "events": ["calendar.event_created", "calendar.reminder_due"]
}
```

### 1.3 Event-Driven Core (local)
- Local event bus to coordinate concurrent workflows and avoid UI deadlocks.
- Event handlers enqueue tasks into `scheduler.py` and emit notifications.
- Supports background tasks (sync, OCR, report generation).

**Event flow**
```
Tool action -> Event emitted -> Handler -> Task/Scheduler -> Notification -> UI refresh
```

### 1.4 Blockchain Identity + Audit
- Sign-in auth uses DID/VC (future) and standard OAuth now.
- Audit trail: event hashes are recorded in a local ledger; optional remote chain anchoring.

---

## 2) Calendar & Scheduling Hub

### 2.1 Scope (MVP)
- Google Calendar two-way sync (mock OAuth, placeholder tokens).
- Create/update/delete events from chat and UI.
- Prep brief generation from Gmail context.
- Auto follow-ups via `scheduler.py`.
- Conflict detection using local rules.

**Non-goals (MVP)**
- Full Outlook sync (planned).
- Advanced scheduling links/booking pages.
- Mobile push beyond current notifications.

### 2.2 Data Model (SQLite)
- `calendar_accounts` (provider, auth_state, token_ref, scopes)
- `calendar_calendars` (account_id, external_id, name, color)
- `calendar_events` (calendar_id, external_id, title, start, end, attendees, location, status)
- `calendar_rules` (user_id, working_hours, buffers, no_meeting_days)
- `calendar_preps` (event_id, brief_text, sources)
- `calendar_followups` (event_id, task_id, status)
- `calendar_audit` (event_id, hash, chain_tx_ref, created_at)

### 2.3 Tool API (calendar_hub)
Actions:
- `connect_account(provider, mock=true)`
- `list_calendars(account_id)`
- `sync_events(account_id, start, end)`
- `create_event(calendar_id, title, start, end, attendees, notes)`
- `update_event(event_id, fields)`
- `delete_event(event_id)`
- `generate_prep(event_id, sources=["gmail"])`
- `create_followup(event_id, summary, due_at)`
- `set_rules(rules)`

### 2.4 UX (Dashboard + Panel)
Dashboard card:
- Next 7 days list
- Conflicts indicator
- “Prep due” badge

Panel:
- Calendar grid
- Event detail drawer with prep brief and follow-ups
- Scheduling rules editor

### 2.5 Integration
- Gmail: invite parsing + prep brief content.
- Scheduler: reminders/follow-ups.
- Notifications: T-24h, T-1h, conflict alert.

---

## 3) Life OS Dashboard (Event-Driven)

### 3.1 Scope (MVP)
- Dynamic widgets based on customer lifecycle stage.
- Unified activity feed (workflows, tasks, calendar, finance, properties).
- Daily plan generation and weekly review.

**Non-goals (MVP)**
- Cross-device sync beyond current session.
- Deep analytics or predictive scoring.

### 3.2 Data Model
- `life_events` (type, source, entity_id, payload, created_at)
- `life_widgets` (widget_id, enabled, order, config)
- `life_daily_plans` (date, content, status)
- `life_reviews` (week_start, summary, actions)

### 3.3 Tool API (life_os)
Actions:
- `get_dashboard(context)`
- `emit_event(type, payload)`
- `generate_daily_plan(date)`
- `generate_weekly_review(week_start)`
- `configure_widgets(config)`

### 3.4 UX
Dashboard:
- Top priorities (from workflow_engine + scheduler)
- Today’s appointments (calendar_hub)
- Pipeline status (customer_lifecycle)
- Property alerts (property_manager)
- Finance snapshot (finance_manager)

Dynamic behavior:
- Early lifecycle: onboarding + discovery tasks.
- Mid lifecycle: delivery, implementation, status.
- Late lifecycle: renewal and support.

### 3.5 Integration
- Workflow Engine: stage-based widgets.
- Scheduler: daily/weekly briefs.
- Notifications: overload alerts, missed priority nudges.
- Event Bus: all tools emit life events for aggregation.

---

## 4) Finance Automation

### 4.1 Scope (MVP)
- Bank/credit feed ingest (mock connector).
- Receipt OCR (local + mock).
- Auto categorization with manual override.
- Monthly report and tax estimate.
- Property Manager linkage for expenses.
- Business X‑Ray ROI rollups.

**Non-goals (MVP)**
- Full accounting features (GL, reconciliation).
- Payroll or invoicing.

### 4.2 Data Model
- `finance_accounts` (provider, external_id, status)
- `finance_transactions` (account_id, date, amount, merchant, category, status)
- `finance_receipts` (txn_id, file_path, ocr_text)
- `finance_categories` (name, rules)
- `finance_reports` (period, summary)
- `finance_tax_estimates` (period, estimate)
- `finance_audit` (event_id, hash, chain_tx_ref)

### 4.3 Tool API (finance_manager)
Actions:
- `connect_account(provider, mock=true)`
- `sync_transactions(account_id, start, end)`
- `categorize(transaction_id, category)`
- `auto_categorize(batch_id)`
- `upload_receipt(file_path, transaction_id)`
- `generate_report(period)`
- `estimate_tax(period)`
- `link_property_expense(transaction_id, property_id)`
- `roi_snapshot(period)`

### 4.4 UX
Dashboard card:
- Month cashflow
- Uncategorized count
- Upcoming tax reminder

Panel:
- Transactions inbox (bulk categorize)
- Receipt OCR results with confirm
- Reports + tax estimates

### 4.5 Integration
- Property Manager: expense linkage.
- Business X‑Ray: ROI summaries.
- Notifications: high spend, uncategorized backlog, tax deadlines.

---

## 5) Event Bus and Concurrency

### 5.1 Local Event Bus
- In-process pub/sub with async handlers.
- Events persisted for resilience and UI rebuild.

**Core event types**
- `calendar.event_created`, `calendar.reminder_due`
- `life.event_emitted`
- `finance.txn_ingested`, `finance.receipt_ocr_complete`
- `workflow.stage_changed`, `customer.lifecycle_changed`

### 5.2 Concurrency Strategy
- Async tasks with per-tool queues.
- TaskScheduler used for delayed/repeating work.
- Backpressure via rate-limited queues and notifications.

---

## 6) Blockchain Identity & Audit

### 6.1 Auth (future)
- DID-based login optional; OAuth is default.
- Token storage encrypted at rest.

### 6.2 Audit
- Hash each critical event payload.
- Store hash in `*_audit` tables.
- Optional chain anchoring using a configured provider (later).

---

## 7) TDD Plan and Milestones

### Phase A: Foundation
1. Event bus + persistence tests.
2. Plugin registry loader tests.
3. Audit hashing tests.

### Phase B: Calendar Hub
1. Tool API unit tests for CRUD.
2. Sync mocks + conflict detection tests.
3. Scheduler integration tests.
4. UI smoke tests (dashboard + panel).

### Phase C: Life OS
1. Life event aggregation tests.
2. Daily plan generation tests.
3. Widget config tests.
4. UI smoke tests.

### Phase D: Finance
1. Ingest + categorize tests.
2. OCR pipeline tests (mock).
3. Report + tax estimate tests.
4. Property linkage + ROI tests.
5. UI smoke tests.

---

## 8) Open Decisions (for later)
- Provider list order (Outlook, iCloud, CalDAV).
- OCR engine default (Tesseract vs cloud).
- Chain anchoring provider (optional).
