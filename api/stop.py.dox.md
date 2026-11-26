# stop.py DOX

## Purpose

- Own the authenticated WebUI endpoint that stops an active agent run without deleting or resetting its chat context.

## Ownership

- `stop.py` resolves the requested in-memory context and exposes the shared `stop_context()` operation used by the endpoint and slash command.

## Runtime Contracts

- Stopping a team conversation requires the exact active run ID and either its sender or the platform administrator. The stop request keeps occupancy until the underlying coroutine confirms exit.

- `Stop` derives from `ApiHandler`, retaining the default authentication and CSRF protections.
- Input uses the selected chat ID in `context`; the endpoint never creates a missing context.
- Stopping cancels the context task through `AgentContext.kill_process()`, clears pause state, preserves chat history and queued messages, and does not start another run.
- The endpoint clears active progress and logs a terminal `Agent process stopped.` info step so the WebUI closes the interrupted process group.
- The response contains `message`, `context`, and a `stopped` boolean indicating whether the context was running when requested.
- Other authenticated entry points should call `stop_context()` so cancellation, progress cleanup, and terminal logging remain identical to the Stop button.

## Work Guidance

- Keep this endpoint aligned with the composer stop-button state and the existing `AgentContext` task lifecycle.

## Verification

- Run `pytest tests/test_stop_agent.py` and smoke-test stopping during model streaming and tool execution.

## Child DOX Index

No child DOX files.
