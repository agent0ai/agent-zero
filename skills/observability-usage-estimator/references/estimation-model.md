# Estimation Model

## Monthly usage

For each project:

- `sessions = active_users * sessions_per_user_per_day * days_per_month`
- `turns = sessions * avg_turns_per_session`
- `trace_events = turns * max(tool_events_per_turn, 1)`
- `buffered_events = trace_events * (1 + growth_buffer_pct/100)`

## Commercial estimate

Use user-provided or default placeholder rates:

- `commercial_fixed_usd = seats * seat_price_usd`
- `commercial_variable_usd = (max(buffered_events - included_events, 0) / billing_unit) * unit_price_usd`
- `commercial_total_usd = commercial_fixed_usd + commercial_variable_usd`

## Self-hosted estimate

- `ops_labor_usd = ops_hours_per_month * ops_hourly_rate_usd`
- `self_hosted_total_usd = infra_monthly_usd + ops_labor_usd`

## Break-even event volume (approx)

When variable pricing dominates:

- `break_even_events ~= ((self_hosted_total_usd - commercial_fixed_usd) / unit_price_usd) * billing_unit + included_events`

Only compute when `unit_price_usd > 0`.
