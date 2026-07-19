### update_goal
Mark the current chat goal complete or blocked.

Use when the active goal is actually achieved, or when progress is genuinely blocked by missing user input or an external-state change.

Args: `status` (`complete` or `blocked`), optional `objective`, optional `note`.

Rules:
- Mark `complete` only when the objective has been achieved.
- Mark `blocked` only when meaningful progress cannot continue without user input or an external-state change.
- Pause, resume, edit, and delete are user controls; do not claim to perform them with this tool.
