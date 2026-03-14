---
name: observability-usage-estimator
version: "0.1.0"
author: Agent Jumbo Team
tier: 1
trust_level: builtin
description: Estimate observability usage and monthly cost for managed and self-hosted deployments across one or more projects.
categories:
  - observability
  - finance
  - planning
dependencies: []
capabilities:
  - filesystem
enabled: true
---

# Observability Usage Estimator

Use this skill when the user asks:

- "How much will LangSmith/Langfuse cost us?"
- "Estimate usage for this project and others"
- "Compare commercial vs self-hosted observability cost"

## Inputs

Collect these values per project:

1. `active_users`
2. `sessions_per_user_per_day`
3. `avg_turns_per_session`
4. `tool_events_per_turn`
5. `days_per_month` (default 30)
6. `team_seats` (for per-seat plans)
7. `infra_monthly_usd` (for self-hosted)
8. `ops_hours_per_month`
9. `ops_hourly_rate_usd`
10. `growth_buffer_pct` (default 20)

If missing, declare assumptions explicitly before calculating.

## Core workflow

1. Review repo/runtime signals to ground assumptions:
   - chat volume indicators (logs, test workloads, known user base)
   - tool usage density (MCP/tools enabled)
2. Build a per-project monthly estimate:
   - sessions = active_users *sessions_per_user_per_day* days_per_month
   - turns = sessions * avg_turns_per_session
   - trace_events = turns * max(tool_events_per_turn, 1)
   - buffered_events = trace_events * (1 + growth_buffer_pct/100)
3. Generate two cost scenarios:
   - managed (commercial plan assumptions)
   - self-hosted (infra + ops labor)
4. Provide a break-even view:
   - event volume where self-hosted and commercial costs cross
5. Output a standardized report using `references/report-template.md`.

## Guardrails

- Never present cost numbers as contractual vendor pricing unless user provides plan terms.
- Label all rate assumptions and date-stamp the estimate.
- Keep formulas visible and reproducible.
- For multiple projects, include both per-project and portfolio totals.

## Fast command

You can generate a deterministic estimate JSON with:

```bash
python skills/observability-usage-estimator/scripts/estimate_usage.py \
  --input skills/observability-usage-estimator/examples/sample_input.json
```
