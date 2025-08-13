### subordinate_broadcast

#### Description
Broadcast a single message to all currently spawned subordinates, or to a targeted subset by profile. Each subordinate runs in its own persistent background context. This tool will queue the message to each addressed subordinate, run or reuse its background monologue, wait for all to finish, and return an aggregated response with each block prefixed by the subordinate’s profile key.

#### Arguments
- `message` (string, required): The message to broadcast
- `attachments` (list[string], optional): Attachment URIs to pass along
- `agent_profile` (string, optional): Target a single subordinate by profile
- `agent_profiles` (string|list, optional): Target multiple subordinates by comma-separated string or list of strings; if omitted, broadcast to all

#### Behavior
- If there are no subordinates stored yet, returns a helpful notice
- If `agent_profile(s)` provided, only addresses those profiles that exist; if none match, returns a helpful notice
- If a subordinate already has a running task, it reuses it instead of starting a new one
- Aggregated response format:
  - `[profile]\n<response>`

#### Usage Examples

##### Broadcast to all
```json
{
  "tool_name": "subordinate_broadcast",
  "tool_args": {
    "message": "Status update: summarize progress, blockers, and ETA.",
    "attachments": []
  }
}
```

##### Targeted subset
```json
{
  "tool_name": "subordinate_broadcast",
  "tool_args": {
    "agent_profiles": "scientist,coder",
    "message": "Provide your next-step proposal and estimate."
  }
}
```
