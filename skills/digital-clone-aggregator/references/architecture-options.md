# Architecture Options

## Option A: In-app pipelines (Agent Jumbo native)

### Summary

Use Agent Jumbo tools, instruments, MCP servers, and workflow_engine to ingest, summarize, and store knowledge. Deliver digests via a Telegram tool.

### Pros

- Lowest operational overhead
- Leverages existing memory (FAISS) and knowledge (RAG)
- Easier to keep prompts, tools, and workflows aligned

### Cons

- Scheduling and retries depend on internal orchestration
- Heavy ingestion may compete with interactive usage

## Option B: External ingestion service

### Summary

Run an external ETL service (cron or serverless) that fetches sources, stores them in a DB/vector store, and pushes summaries to Agent Jumbo via API.

### Pros

- Stronger scheduling and retries
- Scales independently of the agent runtime

### Cons

- More moving parts and deployment complexity
- Requires separate auth and observability

## Option C: Hybrid (recommended)

### Summary

Keep core reasoning and storage in Agent Jumbo, but use a lightweight external scheduler to trigger ingestion and backfill. Agent Jumbo remains the brain; the scheduler is only a trigger.

### Pros

- Keeps architecture simple
- Improves reliability of scheduled jobs
- Avoids a full external ETL stack

### Cons

- Still needs a small external job or cron

## Decision

Choose Option C. It balances reliability and simplicity while keeping the agent as the system of record for memory, knowledge, and synthesis.
