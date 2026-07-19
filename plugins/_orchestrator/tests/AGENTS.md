# Orchestrator Tests - AGENTS.md

## Purpose

- Provide lightweight regression checks for the plugin's source contracts.
- Catch accidental reintroduction of the old tool/runner architecture and important skill instruction drift.

## Ownership

- Owns direct test scripts under `tests/`, currently `test_status_adapters.py`.
- Does not own generated caches or live CLI credentials.

## Local Contracts

- Tests must run with the Agent Zero framework runtime, not the agent execution runtime.
- Keep tests self-contained and deterministic. They may inspect files and adapter metadata but should not call network login endpoints or run real terminal agents.
- When adding an adapter, assert registry order and status-only behavior as needed.
- When changing setup/login guidance, add or update assertions for the phrases that protect the workflow.

## Work Guidance

- Prefer simple assert-based checks that can run as a script inside Docker.
- Avoid broad snapshots of full docs; assert the contract phrases that matter.

## Verification

- Main check:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python plugins/_orchestrator/tests/test_status_adapters.py'
  ```

## Child DOX Index

This folder has no child DOX files.
