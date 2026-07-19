# parallel.py DOX

## Purpose

- Own the `parallel.py` agent tool.
- This tool wraps independent tool calls so they can be started together, awaited by job ID, collected, or canceled.
- Keep this file-level DOX profile synchronized with `parallel.py` because this directory is intentionally flat.

## Ownership

- `parallel.py` owns the runtime implementation.
- `parallel.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `ParallelTool` (`Tool`)
  - `async execute(self, tool_calls=..., calls=..., items=..., job_ids=..., wait=..., action=..., timeout=..., **kwargs)`
  - `async before_execution(self, **kwargs)`
  - `async after_execution(self, response, **kwargs)`

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return `helpers.tool.Response` from `execute(...)`.
- Wrapped items use the same schema as normal tool calls: a tool name plus arguments.
- The tool is intended for independent calls only; dependent operations remain sequential.
- Independent calls should share one batch even when they use different tools; split only for dependencies, ordering, shared mutable state, or parent-context state/tool-availability changes.
- `document_query` is intentionally excluded from wrapped calls because it is too heavy for parallel workers and must be called sequentially.
- `action="start"` starts calls and optionally waits according to `wait`.
- `action="await"` waits for requested job IDs until completion or `timeout`; timeout returns running job handles without canceling them.
- `action="collect"` returns completed job results without waiting.
- `action="cancel"` requests cancellation for requested job IDs.
- Recursive use of `parallel` from inside a direct background tool worker is blocked before execution; subordinate child chats started by `call_subordinate` can use normal child-chat tools, including `parallel`.
- The wrapper tool does not create its own visible process-step log; each wrapped child call owns the visible log row, and the wrapper result is recorded only in model history.

## Key Concepts

- `tool_calls`, `calls`, and `items` are accepted aliases for the wrapped call list; a valid JSON string encoding of the list is tolerated for provider/model recovery.
- Wrapped call items can use the same `tool_name`/`tool_args` shape as top-level agent replies; extra planning fields are ignored by normalization.
- `job_ids` can be supplied as a string or list when awaiting, collecting, or canceling existing jobs.
- The response is compact JSON intended for the model to read and continue with.
- Visible child rows are emitted by `helpers/parallel_tools.py` before each background job starts.

## Work Guidance

- Keep output concise enough for message history while preserving job IDs, statuses, and results.
- Coordinate tool argument or output changes with `prompts/agent.system.tool.parallel.md`, prompt contract tests, and helper tests.
- Avoid adding tool-specific execution logic here; shared execution behavior belongs in `helpers/parallel_tools.py`.

## Verification

- Run targeted tool and prompt-contract tests after changing behavior.
- Run a live WebUI or CLI chat that invokes `parallel` with multiple subordinate jobs.

## Child DOX Index

No child DOX files.
