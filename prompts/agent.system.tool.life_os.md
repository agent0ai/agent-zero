### life_os

Life OS dashboard aggregator and event sink for operational workflows.

Actions:
- `emit_event(type, payload={})`
- `get_dashboard()`
- `generate_daily_plan(date)`
- `configure_widgets(widgets=[...])`

Examples:
```
{{life_os(action="emit_event", type="workflow.stage_changed", payload={"stage": "discovery"})}}
{{life_os(action="get_dashboard")}}
{{life_os(action="generate_daily_plan", date="2025-01-01")}}
```
