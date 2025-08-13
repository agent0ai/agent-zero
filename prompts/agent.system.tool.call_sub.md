### call_subordinate

#### Description
Use this tool to delegate work to exactly one specialized subordinate identified by a settings profile. The tool will create or reuse the subordinate context, send your message, wait for the response, and return it directly.

- Maintains a mapping of spawned subordinates on the superior agent: `{ settings_profile -> subordinate_agent }`
- Spawns a subordinate for the settings profile that does not exist yet
- Optionally resets the settings profile to start a fresh subordinate

#### Arguments
- `message` (string, required): What to send to the subordinate
- `settings_profile` (string, optional): Target settings profile. Empty or omitted means the default profile
- `attachments` (list[string], optional): Attachment URIs to pass along
- `reset` (boolean|string, optional): Set to `true` to replace the subordinate for the given profile

#### Guidance
- Describe the role, task, constraints, and expected output clearly in `message`.
- Delegate specific subtasks, not the entire project.
- Prefer specialized settings profiles when appropriate; leave empty for the default profile.
- Subordinates should call the `subordinate_finish` tool when done to remove themselves from the registry and clean up their context.

#### Usage Examples

##### Single profile
```json
{
  "thoughts": [
    "I need a coder to refactor the module while I plan the integration."
  ],
  "tool_name": "call_subordinate",
  "tool_args": {
    "settings_profile": "coder",
    "message": "Refactor the payment service: extract DB ops, add retries, write a smoke test.",
    "attachments": [],
    "reset": false
  }
}
```

##### Default profile
```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "settings_profile": "",
    "message": "Draft a migration plan for the database schema."
  }
}
```

##### Reset a profile
```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "settings_profile": "coder",
    "message": "Start a fresh take: re-derive the module structure and list open risks.",
    "reset": true
  }
}
```

#### Available settings profiles
{{agent_profiles}}
