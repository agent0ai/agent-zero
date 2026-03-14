# Plugin Marketplace Tool

The **plugin_marketplace** tool enables discovery, browsing, and installation of plugins from Claude Code marketplaces. It provides access to the growing ecosystem of community and official plugins.

## Purpose

- Discover plugins from multiple marketplace sources
- Search and browse plugins by name, tag, or popularity
- Install plugins from marketplaces
- Track installed plugins and check for updates
- Import installed plugins into Agent Jumbo via skill_importer

## Available Marketplaces

| Marketplace | Type | Description |
|-------------|------|-------------|
| **claude-plugins-dev** | community | Community-maintained plugin registry |
| **anthropic-official** | official | Official Anthropic plugins (GitHub) |
| **local** | local | Locally installed plugins (~/.claude/plugins) |

---

## Available Actions

### Marketplace Management

#### 1. add_marketplace

**Add a new marketplace source**

```
{{plugin_marketplace(
  action="add_marketplace",
  name="my-registry",
  url="https://my-registry.example.com",
  api_endpoint="https://my-registry.example.com/api/plugins",
  type="community"
)}}
```

**Parameters:**

- `name` (required): Marketplace name
- `url` (required): Marketplace URL
- `api_endpoint` (optional): API endpoint for fetching plugins
- `type` (optional): community, official, local (default: community)
- `auto_update` (optional): Auto-sync on startup (default: false)

---

#### 2. list_marketplaces

**List configured marketplaces**

```
{{plugin_marketplace(action="list_marketplaces")}}
{{plugin_marketplace(action="list_marketplaces", enabled_only=true)}}
```

---

#### 3. remove_marketplace / toggle_marketplace

**Manage marketplaces**

```
{{plugin_marketplace(action="remove_marketplace", marketplace_id=5)}}
{{plugin_marketplace(action="toggle_marketplace", marketplace_id=1, enabled=false)}}
```

---

### Sync Operations

#### 4. sync_marketplace

**Sync plugins from a specific marketplace**

```
{{plugin_marketplace(action="sync_marketplace", marketplace_id=1)}}
{{plugin_marketplace(action="sync_marketplace", name="claude-plugins-dev")}}
```

---

#### 5. sync_all

**Sync all enabled marketplaces**

```
{{plugin_marketplace(action="sync_all")}}
```

**Note:** Run this periodically to refresh plugin listings.

---

### Plugin Discovery

#### 6. search_plugins

**Search plugins by name/description**

```
{{plugin_marketplace(
  action="search_plugins",
  query="code review",
  limit=20
)}}

{{plugin_marketplace(
  action="search_plugins",
  query="testing",
  tags=["development", "ci"],
  marketplace_id=1
)}}
```

**Parameters:**

- `query` (required): Search term
- `marketplace_id` (optional): Limit to specific marketplace
- `tags` (optional): Filter by tags
- `limit` (optional): Max results (default: 20)

---

#### 7. list_plugins

**List plugins with sorting**

```
{{plugin_marketplace(
  action="list_plugins",
  sort_by="downloads",
  limit=20
)}}
```

**Parameters:**

- `marketplace_id` (optional): Filter by marketplace
- `sort_by` (optional): downloads, stars, recent, name (default: downloads)
- `limit` (optional): Max results (default: 20)
- `offset` (optional): Pagination offset

---

#### 8. list_popular / list_trending

**Quick access to popular/recent plugins**

```
{{plugin_marketplace(action="list_popular", limit=10)}}
{{plugin_marketplace(action="list_trending", limit=10)}}
```

---

#### 9. browse_by_tag

**Browse plugins by tag**

```
{{plugin_marketplace(action="browse_by_tag", tag="development")}}
{{plugin_marketplace(action="browse_by_tag", tag="productivity", limit=30)}}
```

---

#### 10. get_plugin_details

**Get detailed plugin information**

```
{{plugin_marketplace(
  action="get_plugin_details",
  identifier="@anthropics/feature-dev"
)}}
```

**Returns:** Full plugin info including description, version, author, tags, repository, install command

---

### Installation

#### 11. install_plugin

**Install a plugin from marketplace**

```
{{plugin_marketplace(
  action="install_plugin",
  identifier="@wshobson/pr-review-toolkit"
)}}

{{plugin_marketplace(
  action="install_plugin",
  identifier="my-plugin",
  use_cli=false,
  target_path="/custom/path"
)}}
```

**Parameters:**

- `identifier` (required): Plugin identifier
- `marketplace_id` (optional): Source marketplace
- `use_cli` (optional): Use Claude Code CLI for installation (default: true)
- `target_path` (optional): Custom installation path (only for use_cli=false)

**Installation Methods:**

1. **CLI (recommended)**: Uses `npx claude-plugins install` or `claude plugin install`
2. **Direct**: Git clones from repository URL

---

#### 12. uninstall_plugin

**Uninstall a plugin**

```
{{plugin_marketplace(action="uninstall_plugin", identifier="plugin-name")}}
```

---

#### 13. list_installed

**List installed plugins**

```
{{plugin_marketplace(action="list_installed")}}
```

**Shows:** Plugin identifier, version, install date, import status

---

#### 14. check_updates

**Check for available updates**

```
{{plugin_marketplace(action="check_updates")}}
```

---

#### 15. update_plugin

**Update a plugin to latest version**

```
{{plugin_marketplace(action="update_plugin", identifier="plugin-name")}}
```

---

### Integration

#### 16. import_to_agent_jumbo

**Import installed plugin into Agent Jumbo**

```
{{plugin_marketplace(
  action="import_to_agent_jumbo",
  identifier="@anthropics/feature-dev"
)}}
```

This uses the `skill_importer` tool to:

- Import plugin skills as Agent Jumbo tools
- Register hooks
- Configure MCP servers
- Set up agent profiles

---

### Statistics

#### 17. get_stats

**Get marketplace statistics**

```
{{plugin_marketplace(action="get_stats")}}
```

**Returns:** Marketplace counts, cached plugins, installed plugins, top tags

---

## Typical Workflows

### Discover and Install a Plugin

```
# 1. Sync marketplaces first
{{plugin_marketplace(action="sync_all")}}

# 2. Search for plugins
{{plugin_marketplace(action="search_plugins", query="code review")}}

# 3. Get details
{{plugin_marketplace(action="get_plugin_details", identifier="@wshobson/pr-review-toolkit")}}

# 4. Install
{{plugin_marketplace(action="install_plugin", identifier="@wshobson/pr-review-toolkit")}}

# 5. Import to Agent Jumbo
{{plugin_marketplace(action="import_to_agent_jumbo", identifier="@wshobson/pr-review-toolkit")}}
```

### Browse Popular Plugins

```
{{plugin_marketplace(action="list_popular", limit=20)}}
{{plugin_marketplace(action="browse_by_tag", tag="productivity")}}
```

### Keep Plugins Updated

```
{{plugin_marketplace(action="check_updates")}}
{{plugin_marketplace(action="update_plugin", identifier="outdated-plugin")}}
```

---

## Integration with Other Tools

### With skill_importer

After installation, use `import_to_agent_jumbo` to make plugins available in Agent Jumbo:

```
{{plugin_marketplace(action="import_to_agent_jumbo", identifier="plugin-name")}}
```

This is equivalent to:

```
{{skill_importer(action="import_plugin", plugin_path="~/.claude/plugins/plugin-name")}}
```

---

## Notes

- Sync marketplaces before searching to ensure fresh data
- CLI installation is recommended for proper validation
- Imported plugins become available as Agent Jumbo tools
- Local plugins in `~/.claude/plugins` are auto-discovered
- Plugin cache is stored in SQLite for offline browsing
