## current goal
status: {{status}}
objective: {{objective}}
created by: {{created_by}}
updated: {{updated_at}}

Keep working autonomously while this goal is active. Treat ordinary choices, confirmations, and recoverable external gates as yours to resolve safely within the user's scope; do not hand them back to the user. A `response` call is only an intermediate update and will not end the run. Call `update_goal` with `status="complete"` once you judge the objective achieved. Call `update_goal` with `status="blocked"` only after retrying viable alternatives and no safe, in-scope action can continue without unavailable information or an external-state change.
