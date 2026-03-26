# Error Retry

Retry once after an unexpected critical exception so the agent has a chance to recover instead of failing immediately.

## What It Does

This plugin hooks into the agent lifecycle and automatically retries the current loop once when an unhandled critical exception occurs.

It does **not** retry exceptions that are already treated as controlled agent flow, such as:

- `HandledException`
- `RepairableException`

## Main Behavior

- **Counter reset per monologue**
  - Clears the retry counter at the start of a new monologue.
- **Critical exception retry**
  - On an unexpected exception, logs a warning, waits briefly, injects an agent-facing critical error message into history, and suppresses the original exception once.
- **Single retry only**
  - Uses an internal counter so the retry happens at most one time per monologue.

## Key Files

- `extensions/python/_functions/agent/Agent/monologue/start/_10_reset_critical_exception_counter.py`
- `extensions/python/_functions/agent/Agent/handle_exception/end/_80_retry_critical_exception.py`

## Configuration Scope

- **Settings section**: `agent`
- **Per-project config**: `true`
- **Per-agent config**: `true`
- **Always enabled**: `false`

## Plugin Metadata

- **Name**: `_error_retry`
- **Title**: `Error Retry`
- **Description**: Retry on critical exceptions before failing.
