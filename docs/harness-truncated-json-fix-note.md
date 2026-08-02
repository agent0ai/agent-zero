# Harness Fix: Truncated/Unterminated JSON Tool Requests

Status: Applied in `/a0` working tree, validated, **not yet committed/pushed to fork**.
Date: 2026-08-02 (EDT)

## Purpose
Durable context so this isolated Agent Zero harness change can be committed and pushed to the user's fork later, without mixing with the markdown-notes repo.

## Symptom
The chat store contains the exact harness diagnostic:

```
A0: Message misformat, no valid tool request found. Reason: truncated or unterminated JSON tool request (3085 chars).
```

The model emitted a ~3085-character string that began as a valid JSON tool envelope but was cut off mid-object (no closing `}`). The harness logged the generic misformat warning and gave the model `prompts/fw.msg_misformat.md` instead of telling it to complete the truncated JSON.

## Root cause
1. `helpers/extract_tools.py::extract_tool_request()` requires the entire response to be exactly one parseable JSON root object; truncated JSON fails (`root != content` -> `None`).
2. `recover_embedded_tool_request()` only repairs a different failure mode (a complete valid JSON envelope wrapped in planning prose); it cannot recover an unterminated JSON block and returns `None`.
3. `agent.py::process_tools()` therefore fell through to the generic misformat warning.
4. The logged reason had no `finish_reason=length` prefix, so provider max-token truncation was not signaled. The most plausible cause is an early stream/completion termination (drop, stop-before-close, or self-termination while emitting a long envelope).

## Changes applied
- `helpers/extract_tools.py`
  - Added `is_truncated_tool_request(content)`.
  - Added `_json_root_object_balanced(content)` helper.
- `agent.py`
  - Truncated reasoning is now adopted and forwarded to `process_tools()`.
  - Responses-mode no longer routes truncated tool JSON to the plain-text `response` tool.
  - The warning branch now uses the targeted truncated-request prompt and logs a clearer reason for truncated JSON; balanced invalid JSON still uses the generic misformat prompt.
- `extensions/python/_functions/agent/Agent/hist_add_warning/end/_90_stop_unusable_response_loop.py`
  - The unusable-response loop guard now also tracks the new truncated-request warning, preventing infinite repair loops.
- `prompts/fw.msg_truncated_request.md` (new)
  - Instructs the model to respond only with a complete, valid, closed JSON tool request.
- Tests
  - `tests/test_tool_request_normalization.py`: unit tests for the detector.
  - `tests/test_deepseek_harness_reliability.py`: reasoning forwarding, truncated-repropmt routing, balanced-invalid JSON still uses misformat.
  - `tests/test_unusable_response_loop.py`: truncated-request warning participates in the stop loop.

## Validation evidence
- Targeted harness suites: **78 passed**
  - `test_deepseek_harness_reliability.py`
  - `test_tool_request_normalization.py`
  - `test_responses_architecture.py`
  - `test_unusable_response_loop.py`
- Core Agent Zero suite: **1239 passed** via `python3 -m pytest tests/ -q`.
- All touched Python files compile: `py_compile` OK.
- `git diff --check` CLEAN.
- Detector sanity checks: truncated envelope -> `True`; balanced JSON -> `False`; prose/empty/None -> `False`.
- Root-level `pytest -q` collection still hits a **pre-existing, unrelated** collision: multiple `plugins/*_integration/api/test_connection.py` files share the module basename. This is unrelated to this fix.

## Current git state (`/a0`)
The change is uncommitted. Relevant modified/untracked items include:
- Modified: `agent.py`, `helpers/extract_tools.py`, `extensions/python/_functions/agent/Agent/hist_add_warning/end/_90_stop_unusable_response_loop.py`, `tests/test_tool_request_normalization.py`, `tests/test_deepseek_harness_reliability.py`, `tests/test_unusable_response_loop.py`.
- New: `prompts/fw.msg_truncated_request.md`.

There are also many other pre-existing uncommitted framework changes in `/a0` (DeepSeek reliability work, timezone tests, connector work, etc.) that should NOT be bundled into this fix commit without explicit review. A clean worktree clone at `/home/drei/a0-harness-fork` on branch `fix/deepseek-harness-reliability` was prepared on the authenticated CLI host for isolated patching.

## Planned fork push flow (next steps)
1. On the authenticated CLI host (`/home/drei`), clone/checkout the user fork branch that should receive this patch (candidate: `fix/deepseek-harness-reliability`).
2. Copy only the harness truncation delta into the clean worktree.
3. Verify targeted tests + core suite in that worktree.
4. Commit logically (e.g. `fix(harness): recover truncated/unterminated JSON tool requests`).
5. Push to the user fork and, if appropriate, update the associated PR.

## Caveat / open question
GitHub queries from the CLI (`gh pr list` / API) returned no open PRs for the fork branches (`fix/deepseek-harness-reliability`, `fix/test-suite-live-usr-guard`, `fix/timezone-auto-persistence`) even though the user says 3 PRs are open. The fork branches exist. Before pushing, confirm the exact PR/branch target with GitHub (or via the WebUI).
