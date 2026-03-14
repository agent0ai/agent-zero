# Motion Integration Tool

The **motion_integration** tool manages Motion tasks and syncs high-priority Linear issues into Motion time blocks.

## Available Actions

### 1. create_task

#### Create a new Motion task

```text
{{motion_integration(
  action="create_task",
  name="Review PR #42",
  workspace_id="WORKSPACE_ID",
  description="Code review for auth feature",
  priority="HIGH",
  duration=60,
  deadline="2026-03-20"
)}}
```text

**Parameters:**

- `name` (required): Task name
- `workspace_id` (required): Motion workspace ID
- `description` (optional): Task description
- `priority` (optional): ASAP, HIGH, MEDIUM, LOW (default: MEDIUM)
- `duration` (optional): Minutes (default: 30)
- `deadline` (optional): ISO date string
- `project_id` (optional): Motion project ID
- `labels` (optional): List of label strings

---

### 2. list_tasks

#### List tasks in a workspace

```text
{{motion_integration(
  action="list_tasks",
  workspace_id="WORKSPACE_ID",
  status="active"
)}}
```text

**Parameters:**

- `workspace_id` (required): Motion workspace ID
- `project_id` (optional): Filter by project
- `status` (optional): Filter by status
- `use_cache` (optional, default false): Query local cache

---

### 3. get_schedule

#### Get scheduled tasks/time blocks

```text
{{motion_integration(
  action="get_schedule",
  workspace_id="WORKSPACE_ID"
)}}
```text

---

### 4. sync_from_linear

#### Sync P0/P1 Linear issues → Motion tasks (idempotent)

```text
{{motion_integration(
  action="sync_from_linear",
  workspace_id="WORKSPACE_ID",
  linear_team_id="TEAM_ID"
)}}
```text

**Parameters:**

- `workspace_id` (required): Motion workspace ID
- `linear_team_id` (optional): Filter Linear issues by team

**Behavior:**

- Queries Linear for In Progress issues with priority 1 (Urgent) or 2 (High)
- Checks mapping table to skip already-synced issues
- Creates Motion tasks with mapped priority (Urgent→ASAP, High→HIGH)
- Rate-limited: 2s pause between Motion API calls (30 req/min cap)

---

## Configuration

- `motion_api_key` / `MOTION_API_KEY`: Motion API key
- `linear_api_key` / `LINEAR_API_KEY`: For sync_from_linear
- `linear_default_team_id`: Default Linear team filter
