# parallel_tools.py DOX

## Purpose

- Own the shared runtime for parallel tool-call jobs.
- Normalize wrapped tool-call payloads, start background jobs, await or cancel jobs, and render prompt extras for active parallel work.
- Keep this file-level DOX profile synchronized with `parallel_tools.py` because this directory is intentionally flat.

## Ownership

- `parallel_tools.py` owns the runtime implementation.
- `parallel_tools.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Public concepts:
- `NormalizedToolCall`
- `ParallelJob`
- `start_parallel_jobs(...)`
- `await_parallel_jobs(...)`
- `cancel_parallel_jobs(...)`
- `build_parallel_jobs_extras(...)`
- `format_parallel_results(...)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Wrapped tool-call items must use the same shape as normal tool calls: a tool name plus arguments.
- Normalization accepts full agent-reply-shaped objects when `tool_name` and `tool_args` are present; non-contract planning fields such as `thoughts` or `headline` are ignored.
- `tool_calls` should be an array, but normalization also accepts a valid JSON string encoding of that array to recover provider/model stringification.
- Normalization rejects `document_query` inside `parallel` because document parsing and Q&A fan out into heavier worker/model paths that must run sequentially.
- `call_subordinate` jobs run in isolated child chat contexts tagged with parent-chat metadata; they must not be added to the scheduler task list and may use normal child-chat tools, including `parallel`.
- Direct tool jobs run in isolated background contexts and are blocked from recursively invoking `parallel`.
- Direct tool background context cleanup removes both the in-memory context and any transient chat folder left on disk.
- Parent-visible child log items are created for each wrapped call so the WebUI can inspect concurrent children separately while the wrapper result remains model-history-only.
- Child tool logs mirror normal tool-call visible args; job ids remain available through wrapper results and prompt extras rather than visible process-step args.
- Wrapped tool child logs use each tool's native `get_log_object()` output when available, preserving special log rendering (for example: `code_execution_tool` uses `code_exe`, `wait` uses `progress`, MCP tools use `mcp`, and regular tools use `tool`).
- Direct parallel worker execution reuses the parent-visible child log item so tool `before_execution()` cannot create a second generic worker log or lose the native badge type.
- Job IDs are stable handles for later await, collect, or cancel operations.
- Prompt extras must stay bounded and expose only job IDs, tool names, status, and compact result/error summaries.

## Key Concepts

- The parent context stores in-flight jobs under a private data key; collected terminal jobs are removed from that registry.
- `wait=True` starts jobs and awaits them before returning until all requested jobs finish or the wait timeout is reached; the timeout stops waiting but does not cancel running jobs.
- `collect` returns already-finished job results without waiting; `await` waits for requested job IDs.
- Canceled jobs should be marked terminal and should stop their background `DeferredTask` when cancellation is possible.

## Work Guidance

- Keep normalization compatible with provider tool-call envelopes and direct JSON objects.
- Avoid importing heavy runtime modules at import time unless startup behavior is verified.
- Coordinate argument, output, or status changes with `tools/parallel.py`, prompt instructions, and tests.

## Verification

- Run targeted tests for normalization, recursion guard, prompt extras, and tool result formatting.
- Run a live Agent Zero chat when changing parallel execution, child chat metadata, or subordinate task behavior.

## Child DOX Index

No child DOX files.
