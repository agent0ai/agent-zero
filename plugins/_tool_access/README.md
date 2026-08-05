# Tool Access

Tool Access is the always-enabled runtime owner for Agent Editor tool policy.
Policies use the standard plugin precedence: active project profile, active
project, user profile, bundled/plugin profile, then the default. Sparse project
policy lives under `.a0proj/plugins/_tool_access/config.json`; profile policy
lives under `usr/agents/<profile>/plugins/_tool_access/config.json`.

One resolver filters textual prompts and provider-native schemas, rejects local
and MCP execution, and keeps delegated agents bound to their own effective scope.
The required final-response capability is always available.
