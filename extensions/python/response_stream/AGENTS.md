# Response Stream Extensions DOX

## Purpose

- Own handling of full assistant response stream updates.

## Ownership

- Ordered Python files own response logging, include-alias replacement, and live response updates.

## Local Contracts

- Keep streaming output synchronized with UI log items.
- The `step` KVP shown beside a streamed tool call comes from `build_step_description`, which seeds `Using <tool name with underscores as spaces>...` and then dispatches the `tool_step_description` hook with a mutable `ctx` holding `tool_name`, `tool_args`, and `step`. Plugins contribute label text by rewriting `ctx["step"]`; the core module holds no per-tool formatting. After the hook chain the builder appends the compact serialized tool_args length as ` (N)` to the final step, so argument streaming stays visible for every tool; extensions must not add their own counters. The hook is display-only: a raising hook logs through `PrintStyle.debug` and leaves the default step text instead of aborting the remaining `response_stream` extensions or skipping the log update for that chunk. Core extensions in this point label `parallel` (`Using in parallel <first> and N more tools`) and `call_subordinate` (`Calling subordinate <profile> agent`).
- Agent.handle_response_stream normalizes complete tool name/argument aliases before these consumers; incomplete snapshots remain partial data. This display normalization does not execute or authorize tools.
- Treat parsed stream snapshots as partial data; nested tool fields may be `None`
  until their values arrive.
- Preserve include-alias replacement semantics where prompts/tools rely on them.
- Do not expose unmasked secrets in live responses.

## Work Guidance

- Coordinate stream changes with chunk/end hooks and message rendering.

## Verification

- Smoke-test streamed responses, live updates, and include alias replacement after changes.

## Child DOX Index

No child DOX files.
