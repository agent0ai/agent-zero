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

Local `input`, remote `input` with `destination: host`, and remote terminal execution are enabled
by default. No Agent Editor change is needed to use remote input once host
execution and Read&Write access are enabled in the CLI or Launcher. In v2.15,
custom policies that block remote terminal execution also block `input` with `destination: host`,
because keyboard input can execute shell commands. Restricted profiles must
permit both `input` with `destination: host` and the `terminal` action of `code_execution_tool` with `destination: host`.

Bundled tools with multiple actions support independent permissions for each
action: memory, scheduler, local/remote text editors and code execution,
remote computer use, office artifacts, goals, skills, and parallel jobs.
Action IDs append the action to the tool ID, for example
`plugin:_text_editor:text_editor:read`. Memory keeps its existing
`plugin:_memory:memory_load` and other legacy action IDs.

Explicit blocks win over allows across both whole-tool and action rules.
Existing whole-tool rules still work, and missing policies still inherit normal
access. Code execution also checks an explicit reset flag; parallel requests check the operations they actually perform and
each worker checks its own tool call. Model prompts and native schemas expose the
permitted actions. Custom tools and MCP tools retain whole-tool controls.

Browser is controlled by its `browser-automation` skill and does not appear as
a separate Agent Editor tool permission. If saved Tool Access policy denies
Browser or any of its former actions, the Browser plugin blocks the entire
capability and hides its skills in that scope, including scoped overrides.

For a default-block profile that granted the former `local:document_query`
entry, allow `plugin:_document_query:document_query` in Agent Editor to use the
bundled skill. The former local ID is still honored as a denial. It could also
identify a custom file override, so allow the bundled plugin explicitly.

Action controls restrict these tool calls. They are not a filesystem or process
sandbox: an allowed terminal or browser JavaScript action can still perform work
that another tool's action is blocked from doing.
