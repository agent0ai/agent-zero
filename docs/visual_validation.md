# Visual Validation Foundation

This project now includes a project-scoped visual validation layer built on top of `agent-browser`.

It is also integrated with project lifecycle runs (`project_lifecycle.run_phase`), so validation can execute as part of design/development/testing/validation workflows.

## Scope

- Reusable validation suites per project
- Persistent run history per project
- Per-run artifact folders (screenshots and command outputs)
- Support for headed runs, CDP-attached runs, and persistent profile folders

All data is stored under each project:

`usr/projects/<project_name>/.a0proj/validation/`

- `suites/`
- `runs/`
- `profiles/`

## API

`POST /project_validation`

Actions:

- `list_suites`
- `load_suite`
- `save_suite`
- `delete_suite`
- `run_suite`
- `list_runs`
- `get_run`

Required for all actions:

- `project_name`

## Tool

Use tool: `visual_validation`

Arguments mirror the API actions and payloads.

## Suite format

```json
{
  "name": "Google Auth Smoke",
  "description": "Open app, inspect page, capture screenshot",
  "base_url": "http://localhost:5000",
  "steps": [
    { "name": "Open app", "action": "open", "args": ["/"] },
    { "name": "Interactive snapshot", "action": "snapshot", "args": ["-i"] },
    { "name": "Capture", "action": "screenshot", "full_page": true }
  ]
}
```

## Run options

`run_suite` supports:

- `headed` (default `true`)
- `session`
- `cdp`
- `profile_name`
- `per_step_timeout_seconds`
- `base_url_override`

Use `cdp` when you need to attach to a pre-authenticated Chrome window.

## Lifecycle integration notes

- Lifecycle phase bindings can define `visual_suite` per phase.
- Lifecycle browser settings support per-user profile binding:
  - `browser.profiles.<actor>` preferred
  - `browser.profile_name` fallback
- When lifecycle run requests visual validation and configuration is missing, the run returns explicit errors.
