# Notion Integration Tool

The **notion_integration** tool manages Notion pages and syncs specs and CRM data from Linear and customer_lifecycle.

## Available Actions

### 1. create_page

#### Create a new page in a Notion database

```text
{{notion_integration(
  action="create_page",
  database_id="DATABASE_ID",
  title="Project Specification",
  properties={"Status": {"select": {"name": "Draft"}}},
  content_blocks=[{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Spec content here"}}]}}]
)}}
```text

**Parameters:**

- `database_id` (optional if `notion_default_database_id` set): Target database
- `title` (required): Page title
- `properties` (optional): Additional Notion properties
- `content_blocks` (optional): Notion block objects for page body

---

### 2. update_page

#### Update an existing page

```text
{{notion_integration(
  action="update_page",
  page_id="PAGE_ID",
  properties={"Status": {"select": {"name": "Complete"}}}
)}}
```text

---

### 3. query_database

#### Query a Notion database with filters

```text
{{notion_integration(
  action="query_database",
  database_id="DATABASE_ID",
  filter={"property": "Status", "select": {"equals": "Active"}},
  page_size=50
)}}
```text

---

### 4. sync_specs

#### Sync Linear issues with Spec label → Notion pages (incremental)

```text
{{notion_integration(
  action="sync_specs",
  database_id="SPECS_DATABASE_ID",
  spec_label="Spec"
)}}
```text

**Parameters:**

- `database_id` (required): Notion specs database
- `linear_team_id` (optional): Filter by team
- `spec_label` (optional, default "Spec"): Label name to filter

**Behavior:**

- Queries Linear for issues with the Spec label
- Checks mapping table to skip already-synced
- Creates Notion pages with issue title, description, and status

---

### 5. sync_crm

#### Sync customer_lifecycle data → Notion contacts database

```text
{{notion_integration(
  action="sync_crm",
  database_id="CONTACTS_DATABASE_ID"
)}}
```text

**Behavior:**

- Reads all customers from customer_lifecycle SQLite DB
- Creates Notion pages with name, company, email, stage
- Incremental: skips already-mapped customers

---

## Configuration

- `notion_api_key` / `NOTION_API_KEY`: Notion integration API key
- `notion_default_database_id` / `NOTION_DEFAULT_DATABASE_ID`: Default database
- `linear_api_key` / `LINEAR_API_KEY`: For sync_specs
