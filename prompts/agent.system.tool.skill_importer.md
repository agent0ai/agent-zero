# Skill Importer Tool

The **skill_importer** tool enables importing Claude Code plugins, skills, hooks, agents, and MCP server configurations into Agent Jumbo.

## Purpose

- Import individual skills from markdown files
- Import complete Claude Code plugins with all components
- Manage imported skills and plugins
- Generate Agent Jumbo-compatible tool prompts
- Export MCP server configurations for integration

## Available Actions

### Skill Management

#### 1. import_skill

**Import a single skill from a markdown file**

```
{{skill_importer(
  action="import_skill",
  source_path="/path/to/skill.md",
  category="my-category"
)}}
```

**Parameters:**

- `source_path` (required): Path to the skill markdown file
- `category` (optional): Category for organization

**Returns:** skill_id, name, description, arguments, status

---

#### 2. list_skills

**List all imported skills**

```
{{skill_importer(
  action="list_skills",
  enabled_only=true,
  category="my-category",
  plugin_name="my-plugin"
)}}
```

**Parameters:**

- `enabled_only` (optional): Only show enabled skills (default: true)
- `category` (optional): Filter by category
- `plugin_name` (optional): Filter by source plugin

**Returns:** List of skills with ID, name, description, status

---

#### 3. get_skill

**Get details of a specific skill**

```
{{skill_importer(
  action="get_skill",
  skill_id=1
)}}
```

**Parameters:**

- `skill_id` (optional): Skill ID
- `name` (optional): Skill name (use either skill_id or name)

**Returns:** Full skill details including content, arguments, tool requirements

---

#### 4. remove_skill

**Remove an imported skill**

```
{{skill_importer(
  action="remove_skill",
  skill_id=1
)}}
```

**Parameters:**

- `skill_id` (required): ID of skill to remove

**Returns:** Success status

---

#### 5. toggle_skill

**Enable or disable a skill**

```
{{skill_importer(
  action="toggle_skill",
  skill_id=1,
  enabled=false
)}}
```

**Parameters:**

- `skill_id` (required): Skill ID
- `enabled` (optional): Enable (true) or disable (false)

---

#### 6. generate_prompt

**Generate Agent Jumbo tool prompt from imported skill**

```
{{skill_importer(
  action="generate_prompt",
  skill_id=1
)}}
```

**Parameters:**

- `skill_id` (required): Skill ID

**Returns:** Markdown prompt suitable for prompts/agent.system.tool.{name}.md

---

#### 7. get_skill_context

**Get execution context for a skill**

```
{{skill_importer(
  action="get_skill_context",
  skill_id=1
)}}
```

**Parameters:**

- `skill_id` (required): Skill ID

**Returns:** Execution context including required tools, arguments, and compatibility info

---

### Plugin Management

#### 8. import_plugin

**Import a complete Claude Code plugin**

```
{{skill_importer(
  action="import_plugin",
  plugin_path="/path/to/plugin"
)}}
```

**Parameters:**

- `plugin_path` (required): Path to plugin directory (containing plugin.json or .claude/ structure)

**Returns:** Plugin ID, imported components (skills, hooks, agents, MCP servers)

**Supported Plugin Structures:**

- Standard: `plugin.json`, `skills/`, `hooks/`, `agents/`
- Claude: `.claude/plugin.json`, `.claude/skills/`, `.claude/hooks/`

---

#### 9. list_plugins

**List all imported plugins**

```
{{skill_importer(
  action="list_plugins",
  enabled_only=true
)}}
```

**Parameters:**

- `enabled_only` (optional): Only show enabled plugins (default: true)

**Returns:** List of plugins with component counts

---

#### 10. get_plugin

**Get details of a specific plugin**

```
{{skill_importer(
  action="get_plugin",
  plugin_id=1
)}}
```

**Parameters:**

- `plugin_id` (optional): Plugin ID
- `name` (optional): Plugin name

**Returns:** Full plugin details including all components

---

#### 11. remove_plugin

**Remove a plugin and all its components**

```
{{skill_importer(
  action="remove_plugin",
  plugin_id=1
)}}
```

**Parameters:**

- `plugin_id` (required): Plugin ID to remove

**Returns:** Success status, removed component counts

---

#### 12. get_mcp_config

**Get MCP configuration for Agent Jumbo integration**

```
{{skill_importer(
  action="get_mcp_config",
  plugin_id=1
)}}
```

**Parameters:**

- `plugin_id` (required): Plugin ID

**Returns:** JSON MCP configuration to add to Agent Jumbo settings

---

### Bulk Operations

#### 13. sync_directory

**Bulk import skills from a directory**

```
{{skill_importer(
  action="sync_directory",
  directory="/path/to/plugins",
  recursive=true
)}}
```

**Parameters:**

- `directory` (required): Directory to scan for skills
- `recursive` (optional): Search subdirectories (default: true)

**Returns:** Import summary with success/failure counts

---

### Statistics

#### 14. get_stats

**Get execution statistics**

```
{{skill_importer(
  action="get_stats",
  skill_id=1
)}}
```

**Parameters:**

- `skill_id` (optional): Filter stats by skill ID

**Returns:** Execution counts, success rates, average duration

---

## Typical Workflows

### Import a Claude Code Plugin

```
# 1. Import the plugin
{{skill_importer(action="import_plugin", plugin_path="~/.claude/plugins/my-plugin")}}

# 2. List imported components
{{skill_importer(action="get_plugin", name="my-plugin")}}

# 3. Get MCP config if needed
{{skill_importer(action="get_mcp_config", plugin_id=1)}}
```

### Import Skills from Directory

```
# 1. Sync a plugins directory
{{skill_importer(action="sync_directory", directory="~/.claude/plugins")}}

# 2. List all imported skills
{{skill_importer(action="list_skills")}}

# 3. Generate prompt for a specific skill
{{skill_importer(action="generate_prompt", skill_id=5)}}
```

---

## Integration with Other Tools

### With Virtual Team

After importing developer-focused skills, route tasks:

```
# Import developer tools plugin
{{skill_importer(action="import_plugin", plugin_path="/plugins/dev-tools")}}

# Use imported capabilities in workflows
{{virtual_team(action="delegate_to_specialist", agent_role="developer", task="Use imported git-review skill")}}
```

### With Deployment Orchestrator

Import CI/CD related skills:

```
{{skill_importer(action="import_plugin", plugin_path="/plugins/deployment")}}
{{deployment_orchestrator(action="generate_cicd", ...)}}
```

---

## Notes

- Database auto-creates on first use at `instruments/custom/skill_importer/data/skill_importer.db`
- Skills are stored with their original source path for reference
- MCP server configs can be exported and merged into Agent Jumbo settings
- Imported hooks are stored but require manual integration into Agent Jumbo extensions
- Agent definitions can be converted to Agent Jumbo profiles
