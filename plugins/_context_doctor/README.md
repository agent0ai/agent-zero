# Context Doctor

Repairs model tool call JSON before sending it to history and tool processing.

## Behavior

- Uses `json_repair` after native parsing has completed.
- Accepts only complete Agent Zero tool calls (`tool_name` and object `tool_args`).
- Stores repaired tool calls as compact JSON; log kvps retain streamed reasoning and add transformed fields.
- Expands blank-line-separated thoughts into separate entries after repair when the split strategy is enabled.
- Core recovery validates standalone leaked XML/DSML/native calls against offered tools before this plugin. For rejected or truncated calls, Context Doctor formats the history and log before core performs the bounded retry. Responses retries also drop the rejected turn's provider continuation and replayable output items.
- Uses the core recovery decision without parsing it again; quoted tool examples remain non-executable.
- Suppresses unusable XML-like output in model history by default. Turning suppression off keeps rejected XML as non-executable thoughts, respecting thought splitting and log settings. Rejected JSON remains suppressed.
- Core still retries safely with `{}` in history when Context Doctor is disabled.
