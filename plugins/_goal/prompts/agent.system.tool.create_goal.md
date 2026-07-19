### create_goal
Create or replace the current chat goal.

Use only when the user asks for a goal, asks you to manage a goal, or `/goal auto` asks you to create one.

Args: `objective`, optional `token_budget`.

Rules:
- Create one concise objective that describes the current work, not a generic plan.
- The new goal becomes active.
- Do not create goals for casual replies or ordinary one-shot answers.

Example:
~~~json
{
  "thoughts": ["The user asked me to manage this task as a goal."],
  "headline": "Creating goal",
  "tool_name": "create_goal",
  "tool_args": {
    "objective": "Add the built-in goal plugin with a Web UI strip and slash command"
  }
}
~~~
