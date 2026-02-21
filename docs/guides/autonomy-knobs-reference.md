# Autonomy Knobs Reference

This reference documents autonomy-related settings introduced in `feature/autonomy`.

All keys use:

- `A0_SET_<setting_name>`

Example:

- `A0_SET_agent_max_iterations=100`
- `A0_SET_queue_drop_policy=reject`

---

## 1) Monologue Safety Floor

- `agent_max_iterations`
  - Hard cap on iterations in one monologue cycle.
- `agent_max_runtime_seconds`
  - Hard cap on monologue wall-clock runtime.
- `agent_max_consecutive_misformats`
  - Terminates repeated malformed tool-request output loops.
- `agent_max_consecutive_repairable_errors`
  - Terminates repeated recoverable-error loops.

---

## 2) Tool Argument Payload Controls

- `tool_args_max_chars`
  - Max total tool payload size before rejection.
- `tool_args_spill_threshold_chars`
  - Per-string threshold for spill-to-file rewrite.
- `tool_args_spill_dir`
  - Relative spill file directory.
- `tool_args_autorewrite_enabled`
  - Enables spill/resolve behavior.

Notes:

- Spill behavior is rewrite/resolve, not multi-call chunking.
- Oversized payloads above `tool_args_max_chars` are rejected.

---

## 3) Code Execution Reliability

- `code_exec_first_output_timeout`
  - Max wait for first command output.
- `code_exec_between_output_timeout`
  - Max idle gap between output chunks.
- `code_exec_max_exec_timeout`
  - Hard cap on total command runtime.
- `code_exec_dialog_timeout`
  - Early-return detection for interactive prompt waits.
- `code_exec_output_max_chars`
  - Max in-band output returned to the model.
- `code_exec_auto_dump_large_output`
  - Auto-save oversized output to file.
- `code_exec_dump_dir`
  - Relative output dump directory.
- `code_exec_prefer_python_file_write`
  - When true, terminal heredoc file writes are blocked or converted to Python file write paths.

---

## 4) Subordinate Delegation Controls

- `subordinate_max_depth`
  - Max subordinate nesting depth.
- `subordinate_max_calls_per_turn`
  - Max subordinate calls per parent turn.
- `subordinate_max_runtime_seconds`
  - Runtime cap per subordinate execution.

---

## 5) Queue / Backpressure Controls

- `queue_max_items`
  - Max number of queued items.
- `queue_max_total_chars`
  - Max total text chars in queue.
- `queue_drop_policy`
  - Overflow handling policy:
    - `drop_oldest`
    - `drop_newest`
    - `reject`
- `queue_send_all_max_items`
  - Max items aggregated in send-all operation.

---

## 6) Memory Load Guardrails

- `memory_load_limit_max`
  - Upper bound for memory load limit parameter.
- `memory_load_query_max_chars`
  - Query-size clamp.
- `memory_load_response_max_chars`
  - Response-size clamp.

---

## 7) History Compression Tuning

- `history_compression_target_ratio`
  - Overall compression target.
- `history_current_topic_ratio`
  - Allocation for current topic detail.
- `history_topic_ratio`
  - Allocation for topic summaries.
- `history_bulk_ratio`
  - Allocation for bulk/older summaries.
- `history_attention_current_ratio`
  - Current-context weighting for compression.
- `history_attention_past_ratio`
  - Past-context weighting for compression.
- `history_compress_max_passes`
  - Max repeated compression passes.

---

## 8) Runtime Budgets

- `runtime_turn_budget_seconds`
  - Optional per-turn budget (`0` disables).
- `runtime_task_budget_seconds`
  - Optional per-task budget (`0` disables).
- `runtime_subordinate_budget_seconds`
  - Optional subordinate budget (`0` disables).

---

## 9) Model Call Parameters (commonly used with autonomy)

- `chat_model_kwargs`
  - Per-chat-model LiteLLM call kwargs.
- `litellm_global_kwargs`
  - Global LiteLLM kwargs applied across calls.

Common use:

- Set output/token and timeout behavior explicitly for deterministic tool-call generation.

---

## Tuning workflow

1. Start from `docs/setup/env-examples/profile_balanced_production.env`
2. Adjust one knob family at a time
3. Validate using `guides/autonomy-testing.md`
4. Promote stable values into your deployment profile
