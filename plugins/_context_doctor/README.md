# Context Doctor

Repairs model tool call JSON before sending it to history and tool processing.

## Behavior

- Uses `json_repair` on completed model output, including missing brackets, braces and unfinished arguments.
- Selects a repaired Agent Zero tool call (`tool_name` and object `tool_args`) or preserves model-authored thoughts and headlines.
- Stores repaired tool calls as compact JSON; log kvps retain streamed reasoning and add transformed fields.
- Expands blank-line-separated thoughts into separate entries after repair when the split strategy is enabled.
- Core first attempts conversion of complete alternate-format XML/DSML/native calls. Unconverted text still reaches Context Doctor's normal repair path.
- With **Update log content** off (default), View Details keeps the original model output, including recovered XML/DSML. Turn it on to show repaired JSON instead. Recovery notices use the UTL badge and follow **Show utility messages**.
- When repair cannot find usable Agent Zero content, Chat Completions output is stored as thoughts and the agent is prompted to try again. Unusable XML-like output is suppressed by default; turning suppression off keeps it as thoughts.
- Repaired calls use normal tool dispatch and permissions. Native transport calls and earlier output-limit handling retain their existing paths.
