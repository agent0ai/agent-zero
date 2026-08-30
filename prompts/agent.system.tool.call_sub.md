### call_subordinate
delegate research or complex subtasks to a specialized agent.
always use specialized subordinate agents for specialized tasks matching their prompt profile
when a request calls for independent perspectives, challenges, or workstreams, delegate them to separate subordinates instead of performing them all with parent tools
args: `message`, optional `profile`, `reset`, `context_id`
- `profile`: optional prompt profile key for the subordinate; when provided, it must exactly match an available profile; leave empty for the default profile
- `reset`: use json boolean `true` to create a fresh child; use `false` to continue the default child or the supplied `context_id`
- `context_id`: stable child ID returned by an earlier direct or parallel call; use it with `reset: false` to continue that exact child
- `message`: define role, goal, and the concrete task
each caller creates its next agent level: A0 creates A1 children, A1 creates A2 children, and so on
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
