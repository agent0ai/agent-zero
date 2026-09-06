# responses_history.py DOX

## Purpose and Ownership

- Project eligible local Responses call/result groups within complete prepared input. Agent supplies the completed prompt boundary; this helper owns per-build replay state and rendering/masking adaptation. The transport owns affinity, tool scope and request selection.
- `prepare_groups` reads visible rendered records and durable result metadata without changing stored history. `project_history` replaces only exact prepared spans. `prefix_hashes` binds stable visible prefixes to transport/tool scope in linear input size.

- `start_prompt`, `remember_prompt`, and `prepare_call` keep replay bookkeeping in existing `LoopData.params_temporary`, without adding transport fields to `LoopData`. Capture after prompt construction and validate after model-call hooks; retain explicit prompt-replacement overrides.

## Contracts

- Persist only `history_prefix_hash` in existing result capability metadata, never copies of old prompt inputs or a diagnostic replay counter. Hash system, protocol and prepared history; retain freshly prepared extras in each request.
- Require canonical visible arguments, original unique call IDs, immediately paired result records, compatible local Responses state and unchanged prefix/scope. Legacy records without digests stay as text.
- Replay only function calls and encrypted reasoning, with original provider items. Reject known unmasked secrets, textual follow-ups, unsupported items, incomplete pairs and non-text result layouts.
- Build tool outputs from visible rendered result content, preserving additional fields. Never restore raw tool output metadata or invent a final response-tool result.
- Preserve summaries, unmatched/custom layouts, attachments and all remaining prepared input. No execution or policy authorization occurs here.
- Internal history context is removed before every provider request; Chat and fallback messages remain untouched.

## Verification

- Run native history, Responses architecture/transport, prompt protocol, history and tool-policy tests. Verify named Codex and Venice presets live after integration changes.
