# Tool Access

Tool Access is the always-enabled runtime owner for Agent Editor tool policy.
Policies use the standard plugin precedence: active project profile, active
project, user profile, bundled/plugin profile, then the default. Sparse project
policy lives under `.a0proj/plugins/_tool_access/config.json`; Global profile
policy lives under `usr/agents/<profile>/plugins/_tool_access/config.json`, and
project-profile policy lives under
`usr/projects/<project>/.a0proj/agents/<profile>/plugins/_tool_access/config.json`.
The Plugins screen exposes these scoped files through its existing
configuration list; policy choices remain owned by Agent Editor.

One resolver filters textual prompts and provider-native schemas, rejects local
and MCP execution, and keeps delegated agents bound to their own effective scope.
The required final-response capability is always available.

Bundled tools with multiple actions support independent permissions for each
action: memory, scheduler, local/remote text editors and code execution, browser,
remote computer use, office artifacts, goals, skills, and parallel jobs.
Action IDs append the action to the tool ID, for example
`plugin:_text_editor:text_editor:read`. Memory keeps its existing
`plugin:_memory:memory_load` and other legacy action IDs.

Explicit blocks win over allows across both whole-tool and action rules.
Existing whole-tool rules still work, and missing policies still inherit normal
access. Browser batches check each member; code execution also checks an explicit
reset flag; parallel requests check the operations they actually perform and
each worker checks its own tool call. Model prompts and native schemas expose the
permitted actions. Custom tools and MCP tools retain whole-tool controls.

Action controls restrict these tool calls. They are not a filesystem or process
sandbox: an allowed terminal or browser JavaScript action can still perform work
that another tool's action is blocked from doing.
