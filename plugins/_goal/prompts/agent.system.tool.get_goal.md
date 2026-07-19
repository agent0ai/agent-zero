### get_goal
Inspect the current chat goal.

Use this when the user asks about the goal, asks you to manage a goal, or you need to check whether a goal already exists before creating one.

Args: none.

Rules:
- Do not invent a goal if none exists.
- If a goal is paused, complete, or blocked, treat it as state to report unless the user asks you to resume or replace it.
