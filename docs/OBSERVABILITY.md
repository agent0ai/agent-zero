# Observability & Telemetry

Agent Jumbo can collect lightweight telemetry per thread to track tool usage, latency, and errors.

## Enable

1. Open Settings → Developer → Observability.
2. Toggle "Enable telemetry".
3. Choose an external provider (optional).
4. Use "Open Observability" to inspect the current thread.

## External Providers

You can route telemetry to LangSmith, Langfuse, or both. Configure provider keys in the
Observability settings section. Credentials are stored in `.env`.

Supported settings:

- LangSmith: API key, project, endpoint (optional)
- Langfuse: public key, secret key, host

## What's Captured

- Tool start/end events
- Duration in milliseconds
- Success/error status
- Masked tool arguments
- Per-tool counters and average duration

## Workflow Runs

Tool activity is captured into workflow runs for the current thread. When
"Auto-store workflow runs" is enabled, steps are appended automatically. Use
"Save Run" to snapshot a workflow for training/evaluation.

## Clear Telemetry

Use the "Clear" button in the Observability modal to reset the current thread's telemetry.
