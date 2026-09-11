# Context Doctor

Repairs model tool call JSON before sending it to history and tool processing.

## Behavior

- Uses `json_repair` after native parsing has completed.
- Accepts only complete Agent Zero tool calls (`tool_name` and object `tool_args`).
- Stores repaired tool calls as compact JSON; log kvps retain streamed reasoning and add transformed fields.
- Expands blank-line-separated thoughts into separate entries after repair when the split strategy is enabled.
- Optionally replaces XML-like output with `{}` in cases where model uses native XML tool calls.
