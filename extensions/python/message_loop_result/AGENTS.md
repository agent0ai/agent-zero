# Message Loop Result Extensions DOX

## Purpose

- Own normalization and policy handling after a model turn completes, before default assistant-history and tool-dispatch processing.

## Ownership

- Extensions receive mutable `result_data` with `llm_result` and may set `skip_default_processing` after fully handling the turn.
- `_20_empty_response.py` retries fully empty turns (no response and no reasoning): count them toward the unusable-response limit without adding a warning to model history, and use `fw.msg_empty_response.md` for agent-prefixed UI warning text only.
- `_20_empty_response.py` retries reasoning-only turns: add an agent-facing `fw.msg_reasoning_only.md` history warning with a separate `fw.msg_reasoning_only_response.md` user notice, and count them through the stop-unusable-response-loop extension.
- `_30_repeat_response.py` retries response content that exactly matches `loop_data.last_response`, regardless of reasoning, using `fw.msg_repeat.md` for history and `fw.msg_repeat_response.md` for the agent-prefixed UI warning text.

## Local Contracts

- Files run in deterministic filename order.
- A handler that sets `skip_default_processing` owns needed history and UI side effects for that turn.
- Handlers that should not add side effects after an earlier extension has handled the result must return when `skip_default_processing` is set.
- Do not use this point to mutate streamed partial content.

## Work Guidance

- Normalize a completed result before policy extensions compare or persist it.
- Keep loop-control policy independent from optional plugins.

## Verification

- Run message-loop and unusable-response regression tests.

## Child DOX Index

No child DOX files.
