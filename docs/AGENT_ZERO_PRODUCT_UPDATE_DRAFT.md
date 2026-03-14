# Agent Jumbo Product Update Draft (for Agent Zero Team)

## Subject

Agent Jumbo fork update: reliability + MCP performance improvements and proposed upstream collaboration

## Summary

We are running Agent Jumbo as a specialized platform for AI Architects on top of an Agent Zero-derived codebase.
Recent work focused on reliability and local performance in constrained laptop/free-tier environments.

## Recently shipped changes

1. MCP tool loading performance improvements and reload controls
2. Runtime readiness/validation gates for startup stability
3. Chat fault tolerance:

- strict queue mode for new messages (`queue_strict`)
- pause buffering with resume/drain behavior
- queue status surfaced through poll/UI/settings

## Why this matters

1. Reduces chat stalls and "first message timeout" failures
2. Improves recovery behavior during startup and heavy tool registration
3. Improves user trust with explicit queue/paused/runtime indicators

## Upstream candidate scope

These are proposed as separate, reviewable PRs:

1. MCP prompt/tool caching and explicit reload endpoint
2. Chat queue/pause fault-tolerance mode with tests
3. Runtime readiness signaling improvements

## Evidence package to include

1. Commit list and isolated diffs
2. Validation output (`validate_360` + targeted pytest results)
3. Before/after startup and first-response timing snapshots

## Collaboration intent

We want to maintain compatibility with Agent Zero while contributing generic improvements upstream and keeping Agent Jumbo-specific product layers in fork-only modules.

## Ask

1. Confirm preferred upstream contribution workflow (issue-first vs direct PR)
2. Confirm acceptance criteria for runtime/performance changes
3. Confirm naming/compatibility boundaries for fork-specific features
