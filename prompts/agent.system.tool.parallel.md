### parallel
run independent tool calls concurrently, or await/cancel background parallel jobs.

Use only for independent work. Each `tool_calls` item is a normal tool request object using the same `tool_name` and `tool_args` shape as a top-level reply: `{ "tool_name": "...", "tool_args": { ... } }`.
Only `tool_name` and `tool_args` are used; if an item is copied from a full reply object, planning fields like `thoughts` or `headline` are ignored.
Batch all independent calls that are ready now into one `tool_calls` list, even when they use different tools. Do not split by tool type.

Rules:
- do not use for one simple call, dependent steps, ordered steps, shared mutable state, or state/tool-availability changes that must happen in the parent context
- never nest `parallel`
- Never include `document_query` in `tool_calls`; it is too heavy for parallel workers, so call it sequentially.
- Call `goal` sequentially in the owning chat; direct parallel workers have a temporary context and cannot read or update the parent goal.
- Call `response` only as a top-level tool so it ends the message loop; never wrap it inside `parallel.tool_calls`.
- `call_subordinate` uses the same child lifecycle here as it does top-level; fresh siblings are next-level agents, and each job's `context_id` can be continued later with `reset: false`
- Local code jobs keep their own terminal alive until the command finishes or the job is cancelled. Use `wait: false` for long-running servers; await or cancel them with `job_ids`, including after an output timeout.
- Terminal session numbers are isolated per job. Do not send `input`, `runtime: output`, or `runtime: reset` as a new parallel call; use sequential terminal calls for persistent interactive sessions.
- use `wait: false` only when you will collect results later with `job_ids`
- if extras list running or ready parallel jobs, collect them before final synthesis
- `timeout` only limits how long this call waits; running jobs continue and can be awaited again by `job_ids`

Args: `tool_calls`, `job_ids`, `wait` default `true`, `action` as `start|await|collect|cancel`, `timeout`.

Start and wait:
~~~json
{
  "tool_name": "parallel",
  "tool_args": {
    "tool_calls": [
      {"tool_name": "call_subordinate", "tool_args": {"message": "Review option A and return key risks.", "reset": true}},
      {"tool_name": "search_engine", "tool_args": {"query": "official API changelog release notes"}}
    ],
    "wait": true
  }
}
~~~

Collect existing jobs:
~~~json
{"tool_name": "parallel", "tool_args": {"action": "await", "job_ids": ["job-id"], "timeout": 300}}
~~~
