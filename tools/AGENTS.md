# Agent Tools DOX

## Purpose

- Own core agent tool implementations available to Agent Zero agents.
- Keep tool execution contracts, progress logging, intervention handling, and tool-result formatting stable.

## Ownership

- Tool modules in this directory are discovered by the framework and should define `Tool` subclasses.
- Shared tool base classes and response contracts live in `helpers/tool.py`.
- Plugin-specific tools belong in plugin `tools/` directories.

## Local Contracts

- Tools must derive from `helpers.tool.Tool` and implement `async def execute(...)`.
- Return `helpers.tool.Response(message=..., break_loop=...)`.
- Use `await self.agent.handle_intervention(...)` when a long-running or external result should respect pause/intervention flow.
- Sanitize or mask secrets before logging, returning, or storing tool outputs.
- Do not perform destructive filesystem or network actions without the tool contract making that behavior explicit.
- This directory is a file-documented DOX profile: every direct `*.py` tool module must have a same-directory `*.py.dox.md` file named by appending `.dox.md` to the full Python filename.
- The `*.py.dox.md` file owns tool purpose, tool arguments/concepts, output and `break_loop` behavior, side effects, important helper dependencies, prompt-contract notes, and verification guidance.
- When a tool module is added, removed, renamed, or behaviorally changed, update its matching `*.py.dox.md` in the same change.
- Do not leave stale file-level DOX after tool deletion or rename.

## Work Guidance

- Keep tool output concise enough for message history while preserving actionable detail.
- Put reusable parsing, provider, filesystem, or network logic in `helpers/`.
- Update prompt tool instructions when changing tool names, arguments, or behavior.
- During the DOX pass, verify that every direct `*.py` file has a matching `*.py.dox.md` and that changed tool behavior is described there.

## Verification

- Run targeted tool tests after changing a tool or its prompt contract.
- Run prompt/snapshot tests when tool instructions or output shape changes.
- Check file-level documentation coverage with a script or shell loop that verifies each `tools/*.py` has a matching `tools/*.py.dox.md`.

## Child DOX Index

No child DOX files.
