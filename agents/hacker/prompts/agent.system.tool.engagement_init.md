## engagement_init
Initialize or manage a penetration testing engagement workspace.
Run this at the start of every engagement before any active testing.

### Actions

**init** — create workspace, write scope/RoE files, save engagement context to memory
**status** — display current engagement context (alternatively: memory_load with query "ACTIVE ENGAGEMENT")
**list** — list all existing engagement workspaces

### Arguments
- `action` — "init" (default), "status", or "list"
- `target` — engagement name / target identifier (used as directory name, e.g. "10.10.10.5" or "corp-external")
- `scope` — (optional) scope content to write to scope.txt on init
- `roe` — (optional) rules of engagement content to write to roe.txt on init

### Usage

```json
{
    "thoughts": ["I need to initialize the engagement workspace before starting."],
    "headline": "Initializing engagement workspace for target",
    "tool_name": "engagement_init",
    "tool_args": {
        "action": "init",
        "target": "10.10.10.5",
        "scope": "10.10.10.5\n10.10.10.0/24"
    }
}
```

```json
{
    "thoughts": ["Let me check what engagements exist."],
    "headline": "Listing all engagements",
    "tool_name": "engagement_init",
    "tool_args": {
        "action": "list"
    }
}
```
