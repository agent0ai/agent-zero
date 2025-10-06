## project_manager

Manage organized project workspaces with contexts and instructions.

**Actions**: list, create (A0 only), activate, deactivate, edit

**Examples**:
```json
{"tool_name": "project_manager", "tool_args": {"action": "list"}}
{"tool_name": "project_manager", "tool_args": {"action": "create", "name": "web_scraper", "description": "Web scraping tool", "instructions": "Build with rate limiting and error handling"}}
{"tool_name": "project_manager", "tool_args": {"action": "activate", "project_name": "web_scraper"}}
{"tool_name": "project_manager", "tool_args": {"action": "edit", "project_name": "web_scraper", "description": "Enhanced description"}}
{"tool_name": "project_manager", "tool_args": {"action": "deactivate"}}
```

When active, all work is performed within project context and directory. Project context is automatically passed to subordinate agents.