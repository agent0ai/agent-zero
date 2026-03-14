# Linear Integration Tool

The **linear_integration** tool manages Linear issues, projects, and sync pipelines. It is the system-of-record bridge for the Mahoosuc Operating System (MOS).

## Available Actions

### 1. create_issue

#### Create a new Linear issue

```text
{{linear_integration(
  action="create_issue",
  title="Implement user auth",
  team_id="TEAM_ID",
  description="Add JWT-based authentication",
  priority=2,
  project_id="PROJECT_ID",
  label_ids=["LABEL_ID_1", "LABEL_ID_2"]
)}}
```text

**Parameters:**

- `title` (required): Issue title
- `team_id` (optional if `linear_default_team_id` set): Team ID
- `description` (optional): Markdown description
- `priority` (optional): 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
- `project_id` (optional): Assign to project
- `label_ids` (optional): List of label IDs
- `state_id` (optional): Workflow state ID

---

### 2. update_issue

#### Update an existing issue

```text
{{linear_integration(
  action="update_issue",
  issue_id="ISSUE_ID",
  state_id="DONE_STATE_ID",
  priority=3
)}}
```text

**Parameters:**

- `issue_id` (required): Linear issue ID
- `title`, `description`, `state_id`, `priority`, `label_ids` (all optional)

---

### 3. search_issues

#### Search issues by text query

```text
{{linear_integration(
  action="search_issues",
  query="authentication",
  team_id="TEAM_ID",
  limit=10
)}}
```text

**Parameters:**

- `query` (required): Search text (searches title + description)
- `team_id` (optional): Filter by team
- `limit` (optional, default 25): Max results
- `use_cache` (optional, default false): Search local cache instead of API

---

### 4. get_project_issues

#### Get all issues for a Linear project

```text
{{linear_integration(
  action="get_project_issues",
  project_id="PROJECT_ID",
  limit=50
)}}
```text

**Parameters:**

- `project_id` (required): Linear project ID
- `limit` (optional, default 50): Max results
- `use_cache` (optional, default false): Query local cache

---

### 5. sync_pipeline

#### Full sync: projects + issues from Linear → local cache

```text
{{linear_integration(
  action="sync_pipeline",
  team_id="TEAM_ID"
)}}
```text

**Parameters:**

- `team_id` (optional): Sync specific team (uses default if not set)

**Returns:** Projects synced count, total items synced

---

### 6. get_dashboard

#### Get aggregated dashboard data from local cache

```text
{{linear_integration(action="get_dashboard")}}
```text

**Returns:** Total issues, issues by state, issues by priority, project count, last sync info

---

## Configuration

Set in Agent Zero settings or environment variables:

- `linear_api_key` / `LINEAR_API_KEY`: Linear API key (required)
- `linear_default_team_id` / `LINEAR_DEFAULT_TEAM_ID`: Default team ID (optional)

---

## Typical Workflows

### Create and track an issue

```text
# Create issue
{{linear_integration(action="create_issue", title="Fix login bug", priority=1)}}

# Search for it later
{{linear_integration(action="search_issues", query="login bug")}}

# Update state to done
{{linear_integration(action="update_issue", issue_id="...", state_id="DONE_STATE_ID")}}
```text

### Daily sync + dashboard

```text
# Sync all data
{{linear_integration(action="sync_pipeline")}}

# View dashboard
{{linear_integration(action="get_dashboard")}}
```text

## Integration with MOS

- **customer_lifecycle** → auto-creates Linear issues on lead capture
- **deployment_orchestrator** → closes issues on successful deploy
- **life_os** → merges Linear cycle items into daily plans
- **digest_builder** → includes Linear activity in daily digests
