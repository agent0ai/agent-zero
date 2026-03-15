# Comprehensive Test Coverage for Agent Zero Python Codebase

**Date:** 2026-03-07
**Status:** Approved

## Problem

The Agent Zero project has 224 Python modules (~28K LOC) but only ~40 test files covering a small fraction of the codebase. A production-breaking bug (`DatabaseNotCreatedError` from missing `cognee.setup()`) shipped because the test suite didn't cover the initialization flow. Tests must cover the entire Python codebase to prevent regressions.

## Decisions

| Decision | Choice |
|----------|--------|
| Prioritization | Layer-by-layer: helpers → api → extensions → tools → root |
| Test depth | Full unit tests for all public functions, edge cases, mocks |
| External deps | Mocked by default; optional `@pytest.mark.integration` for real services |
| Test runner | Local `.venv` + GitHub Actions CI |
| Test infra | Shared `conftest.py` with reusable fixtures |
| File organization | Mirror structure 1:1 (e.g., `python/helpers/foo.py` → `tests/helpers/test_foo.py`) |

## Architecture

### File Structure

```
tests/
├── conftest.py                    # Shared fixtures (mock_agent, mock_settings, mock_cognee, etc.)
├── helpers/                       # ← python/helpers/ (85 modules)
│   ├── test_settings.py
│   ├── test_files.py
│   ├── test_memory.py
│   ├── test_cognee_init.py
│   ├── test_cognee_background.py
│   ├── test_task_scheduler.py
│   ├── test_websocket_manager.py
│   ├── test_mcp_handler.py
│   ├── test_backup.py
│   ├── test_call_llm.py
│   ├── test_history.py
│   ├── test_secrets.py
│   ├── test_files.py
│   ├── test_file_tree.py
│   └── ... (one file per module)
├── api/                           # ← python/api/ (74 handlers)
│   ├── test_memory_dashboard.py
│   ├── test_api_message.py
│   ├── test_settings_get.py
│   ├── test_projects.py
│   └── ... (one file per handler)
├── extensions/                    # ← python/extensions/ (42 files)
│   ├── test_recall_memories.py
│   ├── test_memorize_fragments.py
│   ├── test_system_prompt.py
│   └── ... (one file per extension)
├── tools/                         # ← python/tools/ (19 files)
│   ├── test_code_execution_tool.py
│   ├── test_browser_agent.py
│   ├── test_scheduler.py
│   └── ... (one file per tool)
└── integration/                   # Optional, real-service tests
    ├── test_cognee_integration.py
    ├── test_llm_integration.py
    └── test_email_integration.py
```

### Shared Fixtures (conftest.py)

Core fixtures available to all tests:

| Fixture | Purpose |
|---------|---------|
| `mock_agent` | MagicMock Agent with context, config, get_data/set_data |
| `mock_settings` | Mock `settings.get_settings()` returning defaults |
| `patch_settings` | Auto-patches `get_settings()` globally |
| `mock_cognee` | Mock cognee module (add, search, setup, datasets) |
| `tmp_workdir` | tmp_path with knowledge/, chats/, memory/ subdirs |
| `mock_files` | Mock `python.helpers.files` using tmp_workdir paths |
| `suppress_print_style` | Autouse — suppresses PrintStyle output |

Markers registered:
- `@pytest.mark.integration` — requires real external services (skipped by default in CI)
- `@pytest.mark.slow` — tests that take >5s

### Layer Strategy

**Layer 1: `python/helpers/` (85 files, ~22K LOC)**

Core business logic. Full unit tests for every public function/class.

Top-20 critical modules by LOC and importance:

| Module | LOC | Test focus |
|--------|-----|------------|
| `task_scheduler.py` | 1262 | CRUD, cron parsing, execution, recovery |
| `websocket_manager.py` | 1152 | Connections, rooms, broadcast, disconnect |
| `mcp_handler.py` | 1147 | Tool discovery, invocation, response parsing |
| `backup.py` | 842 | Create/restore, validation, rollback |
| `settings.py` | 833 | get/set, defaults, typing, persistence |
| `document_query.py` | 701 | Document loading, chunking, embedding |
| `files.py` | 673 | Path operations, read/write, path security |
| `file_tree.py` | 670 | Tree visualization, filtering, recursion |
| `history.py` | 603 | Chat history management, truncation |
| `email_client.py` | 587 | Email parsing, SMTP/IMAP |
| `memory.py` | 570 | Cognee CRUD, search, metadata, dedup |
| `secrets.py` | 540 | Masking/unmasking, storage |
| `skills.py` | 519 | Skill loading, installation, deps |
| `projects.py` | 515 | Project CRUD, file structure |
| `mcp_server.py` | 489 | MCP server lifecycle |
| `log.py` | 435 | Logging, formatting |
| `call_llm.py` | ~300 | LLM calls, retry, streaming |
| `cognee_init.py` | ~200 | Configuration, provider mapping, setup |
| `cognee_background.py` | ~200 | Background pipeline, dirty tracking |
| `dirty_json.py` | ~100 | Invalid JSON parsing |

Remaining ~65 modules: 2-15 tests each proportional to complexity.

**Layer 2: `python/api/` (74 handlers, ~4K LOC)**

Thin wrappers around helpers. Test:
- Input validation (empty body, invalid JSON)
- Correct routing to helper methods
- Error handling (404, 500, auth)
- Response format (JSON structure)

**Layer 3: `python/extensions/` (42 files, ~2K LOC)**

Agent lifecycle hooks. Test:
- Correct invocation conditions
- Prompt/history modifications via mock assertions
- Edge cases (empty history, missing agent, timeouts)

**Layer 4: `python/tools/` (19 files, ~2K LOC)**

Agent tools. Test:
- Argument parsing from JSON
- Execution with mocked dependencies
- Response format
- Error handling per tool

**Layer 5: Root + websocket_handlers (12 files)**

- `agent.py`, `initialize.py`, `models.py` — integration tests
- `run_ui.py`, `preload.py` — smoke tests

### Migration of Existing Tests

356 existing tests move from flat `tests/` to new subdirectories:

| Current | New |
|---------|-----|
| `test_cognee_init.py` | `helpers/test_cognee_init.py` |
| `test_memory_cognee.py` | `helpers/test_memory.py` |
| `test_cognee_background.py` | `helpers/test_cognee_background.py` |
| `test_memory_dashboard.py` | `api/test_memory_dashboard.py` |
| `test_recall_memories.py` | `extensions/test_recall_memories.py` |
| `test_websocket_manager.py` | `helpers/test_websocket_manager.py` |
| `test_llm_retry_and_hooks.py` | `helpers/test_call_llm.py` |
| `test_skill_install.py` | `api/test_skill_install.py` |
| `test_metrics_collector.py` | `helpers/test_metrics_collector.py` |
| `test_task_recovery.py` | `helpers/test_task_scheduler.py` |
| `test_state_monitor.py` | `helpers/test_state_monitor.py` |
| `test_websocket_*.py` | `helpers/test_websocket_*.py` |
| `test_http_auth_csrf.py` | `api/test_csrf_token.py` |
| `chunk_parser_test.py` | `helpers/test_extract_tools.py` |
| `email_parser_test.py` | `helpers/test_email_client.py` |

Existing tests are adapted to use shared `conftest.py` fixtures.

### CI Pipeline

```yaml
# .github/workflows/tests.yml
name: Tests
on:
  push:
    branches: [main, develop]
    paths: ['python/**', 'tests/**']
  pull_request:
    paths: ['python/**', 'tests/**']

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12', cache: pip }
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: python -m pytest tests/ -m "not integration" --tb=short -q
        env: { PYTHONPATH: . }

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12', cache: pip }
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: python -m pytest tests/ -m integration --tb=short -q
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          PYTHONPATH: .
```

## Success Criteria

| Criteria | Target |
|----------|--------|
| Test files | ~224 (1:1 with modules) |
| Total tests | 1500-2000 |
| Unit test runtime | < 60 seconds |
| Determinism | Zero flaky tests (all external deps mocked) |
| Isolation | Each test independent, order doesn't matter |
| Coverage | All public functions have happy path + main error paths |
| Runnability | Works locally (`python -m pytest tests/`) and in CI |

## What's NOT Included

- E2E tests (full agent startup) — too brittle and slow
- Frontend/JS tests — different language
- 100% line coverage target — quality over quantity
