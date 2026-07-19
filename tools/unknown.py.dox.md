# unknown.py DOX

## Purpose

- Own the `unknown.py` agent tool.
- This module handles unknown or malformed tool-call requests.
- Keep this file-level DOX profile synchronized with `unknown.py` because this directory is intentionally flat.

## Ownership

- `unknown.py` owns the runtime implementation.
- `unknown.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Unknown` (`Tool`)
  - `async execute(self, **kwargs)`

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return `helpers.tool.Response` from `execute(...)`.
- Update this file whenever tool arguments, output shape, `break_loop` behavior, intervention handling, prompt instructions, or side effects change.
- `Unknown` is a `Tool`.
- `Unknown` defines `execute(...)`.
- Imported dependency areas include: `extensions.python.system_prompt._11_tools_prompt`, `helpers.tool`.

## Key Concepts

- Important called helpers/classes observed in the source: `Response`, `build_tools_prompt`, `self.agent.read_prompt`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history persistence.
- Coordinate argument or behavior changes with prompt tool instructions and skill guidance.
- Respect intervention flow for long-running, external, or user-visible operations.

## Verification

- Run targeted tool and prompt-contract tests for changed behavior; smoke-test agent execution when no focused test exists.
- Related tests observed by source search:
  - `tests/test_file_tree_visualize.py`
  - `tests/test_oauth_providers.py`
  - `tests/test_socketio_unknown_namespace.py`
  - `tests/test_tunnel_remote_link.py`
  - `tests/test_ws_manager.py`

## Child DOX Index

No child DOX files.
