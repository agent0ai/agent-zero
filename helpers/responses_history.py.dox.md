# responses_history.py DOX

## Purpose and Ownership

- Project eligible local Responses call/result groups within complete prepared input. Agent supplies the completed prompt boundary; this helper owns per-build replay state and rendering/masking adaptation. The transport owns affinity, tool scope and request selection.
- `prepare_groups` reads visible rendered records and durable result metadata without changing stored history. `project_history` replaces only exact prepared spans. `prefix_hashes` binds stable visible prefixes to transport/tool scope in linear input size.

- `start_prompt`, `remember_prompt`, and `prepare_call` keep replay bookkeeping in existing `LoopData.params_temporary`, without adding transport fields to `LoopData`. Capture after prompt construction and validate after model-call hooks; retain explicit prompt-replacement overrides.

## Contracts

- Persist only `history_prefix_hash` in capability metadata. `LLMResult.history_extras` separately retains that turn's prepared text suffix, never copies of accumulated input. Restore eligible snapshots before their assistant records so growing requests preserve their original prefix; append freshly prepared extras for the current turn.
- Require canonical visible arguments, compatible local Responses state and unchanged prefix/scope. Native output replay additionally requires original unique call IDs and immediately paired result records. An unpaired final response may retain its extras snapshot but stays as text; never fabricate a tool acknowledgement. Legacy records without digests stay as text.
- Replay function calls, encrypted reasoning and explicitly tagged assistant commentary with text-only content, preserving original provider items and phase. Reject final/unmarked messages, refusals, incomplete commentary, known unmasked secrets (including extras snapshots), unsupported items, incomplete pairs and non-text result layouts.
- This helper is a transport adapter over generic rendered records and metadata. Shared history storage/rendering remains API-agnostic; replay only changes copied provider input.
- Build tool outputs from visible rendered result content, preserving additional fields. Never restore raw tool output metadata or invent a final response-tool result.
- Preserve summaries, unmatched/custom layouts, attachments and all remaining prepared input. No execution or policy authorization occurs here.
- Internal history context is removed before every provider request; Chat and fallback messages remain untouched.
- Mask the current extras suffix before sending and retaining it, using the same secret manager as replay validation. This keeps safe snapshots eligible and preserves identical request boundaries even when a configured secret matches extras text.

- Skip replay preparation for Chat mode after model-call hooks. Reuse the transport conversion primitive rather than private Agent methods; the actual request retains final fallback and input-validation checks.

## Verification

- Run native history, Responses architecture/transport, prompt protocol, history and tool-policy tests. Verify named Codex and Venice presets live after integration changes.
