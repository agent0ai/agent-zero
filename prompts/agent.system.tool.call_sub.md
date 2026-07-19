### call_subordinate
delegate research or complex subtasks to a specialized agent.
args: `message`, optional `profile`, `reset`
- `profile`: optional prompt profile name for the subordinate; leave empty for the default profile
- `reset`: use json boolean `true` for the first message or when changing profile; use `false` to continue
- `message`: define role, goal, and the concrete task
after the subordinate returns, answer from its result directly when it satisfies the user request
do not repeat the same solving work or call extra tools after a sufficient subordinate result
example:
~~~json
{
  "thoughts": ["Need focused external research before I continue."],
  "headline": "Delegating research subtask",
  "tool_name": "call_subordinate",
  "tool_args": {
    "profile": "researcher",
    "message": "Research Italy AI trends and return key findings.",
    "reset": true
  }
}
~~~
reuse long subordinate output with `§§include(path)` instead of rewriting it
{{if agent_profiles}}
available profiles:
{{agent_profiles}}
{{endif}}
