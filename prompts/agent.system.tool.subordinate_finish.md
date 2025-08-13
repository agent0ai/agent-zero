### subordinate_finish

#### Description
A subordinate uses this tool to signal that it has completed its work. When called:
- The subordinate removes itself from its superior’s subordinate registry (keyed by its `profile`)
- Its background context is cleaned up asynchronously
- The tool returns with `break_loop: true` to end the subordinate’s current monologue

#### When to Use
- After producing a final result for the current task
- When the subordinate should be de-registered and its resources freed

#### Arguments
- No arguments required

#### Usage Example
```json
{
  "thoughts": [
    "I’ve completed the assigned work and will clean up my context."
  ],
  "tool_name": "subordinate_finish",
  "tool_args": {}
}
```
