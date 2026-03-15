# Comprehensive Test Coverage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Cover all 224 Python modules in agent-zero with full unit tests, organized in a mirror file structure with shared fixtures, and add CI pipeline.

**Architecture:** Layer-by-layer approach (helpers → api → extensions → tools → root). Each module gets a 1:1 test file. All external dependencies mocked via shared `conftest.py` fixtures. Optional `@pytest.mark.integration` tests for real services.

**Tech Stack:** pytest, pytest-asyncio, pytest-mock, unittest.mock, GitHub Actions

---

## Phase 0: Infrastructure Setup

### Task 0.1: Create pytest configuration

**Files:**
- Create: `pyproject.toml` (pytest section) or update if exists
- Create: `requirements-test.txt`

**Step 1: Create requirements-test.txt**

```
pytest
pytest-asyncio
pytest-mock
pytest-cov
```

**Step 2: Add pytest config to pyproject.toml**

Add `[tool.pytest.ini_options]` section:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: requires real external services (skipped in CI by default)",
    "slow: tests that take >5s",
]
filterwarnings = [
    "ignore::pytest.PytestCollectionWarning",
]
```

If `pyproject.toml` doesn't exist, create `pytest.ini` instead.

**Step 3: Install test deps**

Run: `source .venv/bin/activate && pip install -r requirements-test.txt`

**Step 4: Commit**

```bash
git add requirements-test.txt pyproject.toml
git commit -m "chore: add test infrastructure config"
```

---

### Task 0.2: Create directory structure and conftest.py

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/helpers/__init__.py`
- Create: `tests/api/__init__.py`
- Create: `tests/extensions/__init__.py`
- Create: `tests/tools/__init__.py`
- Create: `tests/integration/__init__.py`

**Step 1: Create directories**

```bash
mkdir -p tests/{helpers,api,extensions,tools,integration}
touch tests/{helpers,api,extensions,tools,integration}/__init__.py
```

**Step 2: Write conftest.py**

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# === Agent & Context ===

@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.config = MagicMock()
    agent.config.chat_model = "openrouter/test-model"
    agent.config.embeddings_model = "openai/text-embedding-3-small"
    agent.context = MagicMock()
    agent.context.id = "test-ctx-001"
    agent.context.log = MagicMock()
    agent.context.communicate = AsyncMock()
    agent.context.streaming_agent = None
    agent.context.paused = False
    agent.number = 0
    agent.get_data = MagicMock(return_value=None)
    agent.set_data = MagicMock()
    agent.hist_add_tool_result = MagicMock()
    agent.read_prompt = MagicMock(return_value="test prompt")
    return agent


@pytest.fixture
def mock_loop_data():
    ld = MagicMock()
    ld.message = "test user message"
    ld.extras_temporary = ""
    ld.extras_persistent = ""
    ld.agent = MagicMock()
    ld.iteration = 1
    return ld


# === Settings ===

@pytest.fixture
def default_settings():
    return {
        "chat_model": "openrouter/test-model",
        "embeddings_model": "openai/text-embedding-3-small",
        "cognee_search_type": "CHUNKS",
        "cognee_chunk_size": 1024,
        "cognee_chunk_overlap": 128,
        "cognee_temporal_enabled": False,
        "cognee_search_system_prompt": "",
    }


@pytest.fixture
def mock_settings(default_settings):
    settings = MagicMock()
    settings.get = MagicMock(side_effect=lambda key, default=None: default_settings.get(key, default))
    return settings


@pytest.fixture
def patch_settings(mock_settings):
    with patch("python.helpers.settings.get_settings", return_value=mock_settings):
        yield mock_settings


# === Cognee ===

@pytest.fixture
def mock_cognee():
    cognee = MagicMock()
    cognee.add = AsyncMock()
    cognee.search = AsyncMock(return_value=[])
    cognee.setup = AsyncMock()
    cognee.cognify = AsyncMock()
    cognee.memify = AsyncMock()
    cognee.config = MagicMock()
    cognee.datasets = MagicMock()
    cognee.datasets.list_datasets = AsyncMock(return_value=[])
    cognee.datasets.list_data = AsyncMock(return_value=[])
    cognee.datasets.delete_data = AsyncMock()
    return cognee


# === File system ===

@pytest.fixture
def tmp_workdir(tmp_path):
    for d in ["knowledge", "chats", "memory", "logs", "projects", "work_dir"]:
        (tmp_path / d).mkdir()
    return tmp_path


@pytest.fixture
def mock_files(tmp_workdir):
    files_mock = MagicMock()
    files_mock.get_abs_path = MagicMock(
        side_effect=lambda *args: str(tmp_workdir / "/".join(str(a) for a in args))
    )
    files_mock.get_base_dir = MagicMock(return_value=str(tmp_workdir))
    return files_mock


# === PrintStyle suppression ===

@pytest.fixture(autouse=True)
def suppress_print_style():
    with patch("python.helpers.print_style.PrintStyle", MagicMock()):
        yield


# === API Handler ===

@pytest.fixture
def mock_app():
    from unittest.mock import MagicMock
    import threading
    app = MagicMock()
    lock = threading.Lock()
    return app, lock


# === Markers ===

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires real external services")
    config.addinivalue_line("markers", "slow: tests that take >5s")
```

**Step 3: Verify conftest loads**

Run: `cd agent-zero && source .venv/bin/activate && python -m pytest tests/ --collect-only -q 2>&1 | tail -3`
Expected: tests collected without conftest errors

**Step 4: Commit**

```bash
git add tests/conftest.py tests/helpers/ tests/api/ tests/extensions/ tests/tools/ tests/integration/
git commit -m "chore: add conftest.py and test directory structure"
```

---

### Task 0.3: Create GitHub Actions CI workflow

**Files:**
- Create: `.github/workflows/tests.yml`

**Step 1: Create workflow**

```yaml
name: Tests
on:
  push:
    branches: [main, develop]
    paths: ['python/**', 'tests/**', 'requirements*.txt']
  pull_request:
    paths: ['python/**', 'tests/**']

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
      - name: Install dependencies
        run: |
          pip install -r requirements.txt -r requirements-test.txt
      - name: Run unit tests
        run: python -m pytest tests/ -m "not integration" --tb=short -q --timeout=30
        env:
          PYTHONPATH: .

  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
      - name: Install dependencies
        run: |
          pip install -r requirements.txt -r requirements-test.txt
      - name: Run integration tests
        run: python -m pytest tests/integration/ --tb=short -q --timeout=60
        env:
          PYTHONPATH: .
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

**Step 2: Commit**

```bash
git add .github/workflows/tests.yml
git commit -m "ci: add GitHub Actions test workflow"
```

---

## Phase 1: Migrate Existing Tests

### Task 1.1: Move existing tests to new structure

Move all existing test files to their new locations. Update imports to use conftest fixtures where possible.

**Mapping:**

```bash
# helpers/
mv tests/test_cognee_init.py tests/helpers/test_cognee_init.py
mv tests/test_memory_cognee.py tests/helpers/test_memory.py
mv tests/test_cognee_background.py tests/helpers/test_cognee_background.py
mv tests/test_websocket_manager.py tests/helpers/test_websocket_manager.py
mv tests/test_llm_retry_and_hooks.py tests/helpers/test_call_llm.py
mv tests/test_metrics_collector.py tests/helpers/test_metrics_collector.py
mv tests/test_stream_truncation.py tests/helpers/test_stream_truncation.py
mv tests/test_task_recovery.py tests/helpers/test_task_scheduler.py
mv tests/test_state_monitor.py tests/helpers/test_state_monitor.py
mv tests/test_state_sync_handler.py tests/helpers/test_state_sync_handler.py
mv tests/test_snapshot_parity.py tests/helpers/test_snapshot_parity.py
mv tests/test_snapshot_schema_v1.py tests/helpers/test_snapshot_schema_v1.py
mv tests/test_websocket_harness.py tests/helpers/test_websocket_harness.py
mv tests/test_websocket_handlers.py tests/helpers/test_websocket_handlers.py
mv tests/test_websocket_namespaces.py tests/helpers/test_websocket_namespaces.py
mv tests/test_websocket_namespaces_integration.py tests/helpers/test_websocket_namespaces_integration.py
mv tests/test_websocket_namespace_discovery.py tests/helpers/test_websocket_namespace_discovery.py
mv tests/test_websocket_namespace_security.py tests/helpers/test_websocket_namespace_security.py
mv tests/test_websocket_root_namespace.py tests/helpers/test_websocket_root_namespace.py
mv tests/test_websocket_client_api_surface.py tests/helpers/test_websocket_client_api_surface.py
mv tests/test_websocket_csrf.py tests/helpers/test_websocket_csrf.py
mv tests/test_socketio_library_semantics.py tests/helpers/test_socketio_library_semantics.py
mv tests/test_socketio_unknown_namespace.py tests/helpers/test_socketio_unknown_namespace.py
mv tests/test_context_isolation.py tests/helpers/test_context.py
mv tests/test_persist_chat_log_ids.py tests/helpers/test_persist_chat.py
mv tests/test_cap_max_tokens.py tests/helpers/test_cap_max_tokens.py
mv tests/test_fasta2a_client.py tests/helpers/test_fasta2a_client.py
mv tests/test_multi_tab_isolation.py tests/helpers/test_multi_tab_isolation.py
mv tests/test_state_sync_welcome_screen.py tests/helpers/test_state_sync_welcome_screen.py
mv tests/chunk_parser_test.py tests/helpers/test_extract_tools.py
mv tests/email_parser_test.py tests/helpers/test_email_client.py
mv tests/rate_limiter_test.py tests/helpers/test_rate_limiter.py
mv tests/websocket_namespace_test_utils.py tests/helpers/websocket_namespace_test_utils.py

# api/
mv tests/test_memory_dashboard.py tests/api/test_memory_dashboard.py
mv tests/test_skill_install.py tests/api/test_skill_install.py
mv tests/test_http_auth_csrf.py tests/api/test_http_auth_csrf.py
mv tests/test_settings_developer_sections.py tests/api/test_settings_developer_sections.py
mv tests/test_run_ui_config.py tests/api/test_run_ui_config.py

# extensions/
mv tests/test_recall_memories.py tests/extensions/test_recall_memories.py
```

**Step 2: Fix imports in moved test files**

Any import like `from .websocket_namespace_test_utils import ...` needs updating to the new path.

**Step 3: Run all tests to verify nothing broke**

Run: `python -m pytest tests/ --ignore=tests/helpers/test_rate_limiter.py -q --tb=short`
Expected: all 356 tests pass (excluding rate_limiter which requires API key)

**Step 4: Commit**

```bash
git add tests/
git commit -m "refactor: migrate existing tests to mirror directory structure"
```

---

## Phase 2: Helpers — Core (Top 20 Critical Modules)

Each task below covers one or more related helper modules. For each module, write tests for all public functions and classes: happy path, error handling, edge cases. Use conftest fixtures (`mock_agent`, `mock_settings`, `mock_files`, `mock_cognee`, `tmp_workdir`).

**Pattern for every test file:**

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Import the module under test
# Test every public function/class
# Mock external dependencies
# Test: happy path, error handling, edge cases, boundary values
```

### Task 2.1: test_settings.py (833 LOC)

**Files:**
- Create: `tests/helpers/test_settings.py`
- Source: `python/helpers/settings.py`

**What to test:**
- `get_settings()` — returns settings object, caching behavior
- `Settings.get()` — default values, type coercion, missing keys
- `Settings.set()` — persistence, validation
- Settings file loading/saving from disk
- Developer sections (if exposed)
- Environment variable overrides

### Task 2.2: test_files.py (673 LOC)

**Files:**
- Create: `tests/helpers/test_files.py`
- Source: `python/helpers/files.py`

**What to test:**
- `get_abs_path()` — path joining, base dir resolution
- `get_base_dir()` — correct base dir detection
- File read/write helpers
- Path traversal prevention (security)
- File existence checks
- Directory creation

### Task 2.3: test_history.py (603 LOC)

**Files:**
- Create: `tests/helpers/test_history.py`
- Source: `python/helpers/history.py`

**What to test:**
- History append/truncate operations
- Message format (role, content, timestamp)
- Token counting integration
- History persistence to disk
- Max history length enforcement

### Task 2.4: test_call_llm.py — extend existing (69 LOC source, 36 existing tests)

**Files:**
- Modify: `tests/helpers/test_call_llm.py` (already moved from test_llm_retry_and_hooks.py)
- Source: `python/helpers/call_llm.py`

**What to test (add missing):**
- Streaming response handling
- Model fallback behavior
- Token limit enforcement
- Provider-specific formatting

### Task 2.5: test_task_scheduler.py (1262 LOC)

**Files:**
- Modify: `tests/helpers/test_task_scheduler.py` (already has 12 tests)
- Source: `python/helpers/task_scheduler.py`

**What to test (add missing):**
- Task CRUD operations
- Cron expression parsing and validation
- Next-run calculation
- Concurrent task execution
- Task recovery after crash
- Deletion/update race conditions

### Task 2.6: test_mcp_handler.py (1147 LOC)

**Files:**
- Create: `tests/helpers/test_mcp_handler.py`
- Source: `python/helpers/mcp_handler.py`

**What to test:**
- Tool discovery from MCP server
- Tool invocation with parameters
- Response parsing (success, error, timeout)
- Server connection lifecycle (connect, disconnect, reconnect)
- Tool schema validation
- Multiple server management

### Task 2.7: test_backup.py (842 LOC)

**Files:**
- Create: `tests/helpers/test_backup.py`
- Source: `python/helpers/backup.py`

**What to test:**
- Backup creation (file collection, archive format)
- Backup restoration (extract, validation, overwrite)
- Backup listing and inspection
- Preview/grouped preview
- Invalid backup handling
- Partial restore (selected files only)

### Task 2.8: test_document_query.py (701 LOC)

**Files:**
- Create: `tests/helpers/test_document_query.py`
- Source: `python/helpers/document_query.py`

**What to test:**
- Document loading (text, PDF, URL)
- Text chunking (size, overlap)
- Query execution against loaded docs
- Error handling (invalid format, empty doc)
- Token counting for chunks

### Task 2.9: test_file_tree.py (670 LOC)

**Files:**
- Create: `tests/helpers/test_file_tree.py`
- Source: `python/helpers/file_tree.py`

**What to test:**
- Tree visualization format
- File filtering (include/exclude patterns)
- Recursive directory traversal
- Max depth limiting
- Special character handling in filenames
- Empty directory handling

### Task 2.10: test_rfc_files.py (622 LOC)

**Files:**
- Create: `tests/helpers/test_rfc_files.py`
- Source: `python/helpers/rfc_files.py`

**What to test:**
- RFC file reading and parsing
- File change tracking
- Diff generation
- File path resolution

### Task 2.11: test_email_client.py — extend (587 LOC)

**Files:**
- Modify: `tests/helpers/test_email_client.py` (already has 1 test)
- Source: `python/helpers/email_client.py`

**What to test (add missing):**
- Email parsing (headers, body, attachments)
- SMTP connection (mocked)
- IMAP connection (mocked)
- Template rendering
- Encoding handling (UTF-8, ASCII)

### Task 2.12: test_fasta2a_server.py (581 LOC)

**Files:**
- Create: `tests/helpers/test_fasta2a_server.py`
- Source: `python/helpers/fasta2a_server.py`

**What to test:**
- Server initialization
- Request handling
- Response formatting
- Error handling
- Authentication flow

### Task 2.13: test_secrets.py (540 LOC)

**Files:**
- Create: `tests/helpers/test_secrets.py`
- Source: `python/helpers/secrets.py`

**What to test:**
- Secret masking in text
- Secret unmasking
- Secret storage and retrieval
- Pattern matching for API keys, passwords
- Nested secret handling

### Task 2.14: test_skills.py (519 LOC)

**Files:**
- Create: `tests/helpers/test_skills.py`
- Source: `python/helpers/skills.py`

**What to test:**
- Skill discovery from filesystem
- Skill loading and parsing
- Dependency resolution
- Skill metadata extraction
- Invalid skill handling

### Task 2.15: test_projects.py (515 LOC)

**Files:**
- Create: `tests/helpers/test_projects.py`
- Source: `python/helpers/projects.py`

**What to test:**
- Project CRUD
- Project file structure creation
- Project listing
- Project switching
- Knowledge subdirectory mapping

### Task 2.16: test_mcp_server.py (489 LOC)

**Files:**
- Create: `tests/helpers/test_mcp_server.py`
- Source: `python/helpers/mcp_server.py`

**What to test:**
- Server lifecycle (start, stop)
- Tool registration
- Request/response handling
- Error propagation

### Task 2.17: test_log.py (435 LOC)

**Files:**
- Create: `tests/helpers/test_log.py`
- Source: `python/helpers/log.py`

**What to test:**
- Log message formatting
- Log level filtering
- Log file writing
- Log rotation/truncation

### Task 2.18: test_dirty_json.py (335 LOC)

**Files:**
- Create: `tests/helpers/test_dirty_json.py`
- Source: `python/helpers/dirty_json.py`

**What to test:**
- Parsing valid JSON (baseline)
- Parsing JSON with trailing commas
- Parsing JSON with single quotes
- Parsing JSON with unquoted keys
- Parsing JSON with comments
- Parsing truncated JSON
- Parsing JSON with extra brackets/braces
- Nested dirty JSON
- Empty/null input handling

### Task 2.19: test_extract_tools.py — extend existing

**Files:**
- Modify: `tests/helpers/test_extract_tools.py` (already has 2 tests)
- Source: `python/helpers/extract_tools.py`

**What to test (add missing):**
- Tool call extraction from LLM responses
- Multi-tool extraction
- Malformed tool calls
- Tool arguments parsing
- Edge cases (empty response, partial tool call)

### Task 2.20: test_tokens.py (44 LOC)

**Files:**
- Create: `tests/helpers/test_tokens.py`
- Source: `python/helpers/tokens.py`

**What to test:**
- Token counting accuracy
- Different model tokenizers
- Empty string handling
- Long text handling

**After completing Tasks 2.1-2.20:**

Run: `python -m pytest tests/helpers/ -q --tb=short`
Expected: all tests pass

```bash
git add tests/helpers/
git commit -m "test: add unit tests for core helpers (top 20 modules)"
```

---

## Phase 3: Helpers — Supporting (Remaining ~65 Modules)

Group remaining helpers by domain. Each task covers 3-8 related modules.

### Task 3.1: Browser & Playwright modules

**Test files to create:**
- `tests/helpers/test_browser.py` ← `python/helpers/browser.py` (385 LOC)
- `tests/helpers/test_browser_use.py` ← `python/helpers/browser_use.py` (3 LOC)
- `tests/helpers/test_browser_use_monkeypatch.py` ← `python/helpers/browser_use_monkeypatch.py` (162 LOC)
- `tests/helpers/test_playwright.py` ← `python/helpers/playwright.py` (38 LOC)

Mock all playwright/browser interactions.

### Task 3.2: State management modules

**Test files to create:**
- `tests/helpers/test_state_snapshot.py` ← `python/helpers/state_snapshot.py` (319 LOC)
- `tests/helpers/test_state_monitor_integration.py` ← `python/helpers/state_monitor_integration.py` (13 LOC)

Extend existing `test_state_monitor.py` with more coverage.

### Task 3.3: Shell & Process modules

**Test files to create:**
- `tests/helpers/test_shell_local.py` ← `python/helpers/shell_local.py` (48 LOC)
- `tests/helpers/test_shell_ssh.py` ← `python/helpers/shell_ssh.py` (245 LOC)
- `tests/helpers/test_docker.py` ← `python/helpers/docker.py` (99 LOC)
- `tests/helpers/test_process.py` ← `python/helpers/process.py` (35 LOC)
- `tests/helpers/test_tty_session.py` ← `python/helpers/tty_session.py` (327 LOC)

Mock subprocess calls, Docker API, SSH connections.

### Task 3.4: Communication modules

**Test files to create:**
- `tests/helpers/test_websocket.py` ← `python/helpers/websocket.py` (568 LOC)
- `tests/helpers/test_notification.py` ← `python/helpers/notification.py` (228 LOC)
- `tests/helpers/test_message_queue.py` ← `python/helpers/message_queue.py` (188 LOC)
- `tests/helpers/test_messages.py` ← `python/helpers/messages.py` (75 LOC)

### Task 3.5: Subagent & RFC modules

**Test files to create:**
- `tests/helpers/test_subagents.py` ← `python/helpers/subagents.py` (359 LOC)
- `tests/helpers/test_rfc.py` ← `python/helpers/rfc.py` (81 LOC)
- `tests/helpers/test_rfc_exchange.py` ← `python/helpers/rfc_exchange.py` (18 LOC)

### Task 3.6: Search modules

**Test files to create:**
- `tests/helpers/test_duckduckgo_search.py` ← `python/helpers/duckduckgo_search.py` (29 LOC)
- `tests/helpers/test_perplexity_search.py` ← `python/helpers/perplexity_search.py` (32 LOC)
- `tests/helpers/test_searxng.py` ← `python/helpers/searxng.py` (12 LOC)

Mock HTTP requests. Test query formatting, response parsing, error handling.

### Task 3.7: Skills management modules

**Test files to create:**
- `tests/helpers/test_skills_cli.py` ← `python/helpers/skills_cli.py` (364 LOC)
- `tests/helpers/test_skills_import.py` ← `python/helpers/skills_import.py` (264 LOC)

### Task 3.8: File & Knowledge modules

**Test files to create:**
- `tests/helpers/test_file_browser.py` ← `python/helpers/file_browser.py` (355 LOC)
- `tests/helpers/test_knowledge_import.py` ← `python/helpers/knowledge_import.py` (210 LOC)
- `tests/helpers/test_attachment_manager.py` ← `python/helpers/attachment_manager.py` (93 LOC)
- `tests/helpers/test_images.py` ← `python/helpers/images.py` (35 LOC)

### Task 3.9: Infrastructure modules

**Test files to create:**
- `tests/helpers/test_defer.py` ← `python/helpers/defer.py` (230 LOC)
- `tests/helpers/test_job_loop.py` ← `python/helpers/job_loop.py` (53 LOC)
- `tests/helpers/test_persist_chat.py` — extend existing ← `python/helpers/persist_chat.py` (309 LOC)
- `tests/helpers/test_runtime.py` ← `python/helpers/runtime.py` (194 LOC)
- `tests/helpers/test_migration.py` ← `python/helpers/migration.py` (110 LOC)

### Task 3.10: Formatting & String modules

**Test files to create:**
- `tests/helpers/test_strings.py` ← `python/helpers/strings.py` (176 LOC)
- `tests/helpers/test_log_format.py` ← `python/helpers/log_format.py` (49 LOC)
- `tests/helpers/test_print_style.py` ← `python/helpers/print_style.py` (237 LOC)
- `tests/helpers/test_print_catch.py` ← `python/helpers/print_catch.py` (30 LOC)
- `tests/helpers/test_localization.py` ← `python/helpers/localization.py` (185 LOC)

### Task 3.11: Auth, Security & Networking modules

**Test files to create:**
- `tests/helpers/test_security.py` ← `python/helpers/security.py` (49 LOC)
- `tests/helpers/test_login.py` ← `python/helpers/login.py` (15 LOC)
- `tests/helpers/test_crypto.py` ← `python/helpers/crypto.py` (66 LOC)
- `tests/helpers/test_tunnel_manager.py` ← `python/helpers/tunnel_manager.py` (131 LOC)

### Task 3.12: Miscellaneous small modules

**Test files to create:**
- `tests/helpers/test_vector_db.py` ← `python/helpers/vector_db.py` (142 LOC)
- `tests/helpers/test_providers.py` ← `python/helpers/providers.py` (100 LOC)
- `tests/helpers/test_api.py` ← `python/helpers/api.py` (102 LOC)
- `tests/helpers/test_extension.py` ← `python/helpers/extension.py` (66 LOC)
- `tests/helpers/test_tool.py` ← `python/helpers/tool.py` (66 LOC)
- `tests/helpers/test_context.py` — extend existing ← `python/helpers/context.py` (46 LOC)
- `tests/helpers/test_dotenv.py` ← `python/helpers/dotenv.py` (43 LOC)
- `tests/helpers/test_errors.py` ← `python/helpers/errors.py` (80 LOC)
- `tests/helpers/test_guids.py` ← `python/helpers/guids.py` (4 LOC)
- `tests/helpers/test_wait.py` ← `python/helpers/wait.py` (68 LOC)
- `tests/helpers/test_timed_input.py` ← `python/helpers/timed_input.py` (9 LOC)
- `tests/helpers/test_update_check.py` ← `python/helpers/update_check.py` (14 LOC)
- `tests/helpers/test_git.py` ← `python/helpers/git.py` (179 LOC)

### Task 3.13: Audio modules

**Test files to create:**
- `tests/helpers/test_whisper.py` ← `python/helpers/whisper.py` (96 LOC)
- `tests/helpers/test_kokoro_tts.py` ← `python/helpers/kokoro_tts.py` (126 LOC)

### Task 3.14: Cognee & Memory modules (extend existing)

Extend already-existing test files with any missing coverage:
- `tests/helpers/test_cognee_init.py` — verify all config methods, provider mapping gaps
- `tests/helpers/test_memory.py` — verify all Memory.Area paths
- `tests/helpers/test_cognee_background.py` — verify all pipeline states

### Task 3.15: Fasta2a & WebSocket modules (extend existing)

- `tests/helpers/test_fasta2a_client.py` — extend (currently 1 test)
- `tests/helpers/test_rate_limiter.py` — fix broken test (remove external API dependency)

**After completing all Phase 3 tasks:**

Run: `python -m pytest tests/helpers/ -q --tb=short`

```bash
git add tests/helpers/
git commit -m "test: add unit tests for all remaining helpers (~65 modules)"
```

---

## Phase 4: API Handlers (74 files)

API handlers are mostly thin wrappers. For each handler, test:
1. Correct request parsing
2. Delegation to correct helper function
3. Error responses (400, 404, 500)
4. Response format

Group by domain.

### Task 4.1: Memory & Cognee API

**Test files:**
- Extend: `tests/api/test_memory_dashboard.py` (already 20 tests)
- Create: `tests/api/test_import_knowledge.py`
- Create: `tests/api/test_knowledge_path_get.py`
- Create: `tests/api/test_knowledge_reindex.py`

### Task 4.2: Chat API

**Test files:**
- Create: `tests/api/test_chat_create.py`
- Create: `tests/api/test_chat_load.py`
- Create: `tests/api/test_chat_remove.py`
- Create: `tests/api/test_chat_reset.py`
- Create: `tests/api/test_chat_export.py`
- Create: `tests/api/test_chat_files_path_get.py`

### Task 4.3: Message API

**Test files:**
- Create: `tests/api/test_api_message.py` ← `python/api/api_message.py` (179 LOC)
- Create: `tests/api/test_message.py` ← `python/api/message.py` (71 LOC)
- Create: `tests/api/test_message_async.py` ← `python/api/message_async.py` (11 LOC)
- Create: `tests/api/test_message_queue_add.py`
- Create: `tests/api/test_message_queue_remove.py`
- Create: `tests/api/test_message_queue_send.py`

### Task 4.4: Settings & Config API

**Test files:**
- Create: `tests/api/test_settings_get.py`
- Create: `tests/api/test_settings_set.py`
- Create: `tests/api/test_settings_workdir_file_structure.py`
- Extend: `tests/api/test_settings_developer_sections.py`

### Task 4.5: Scheduler API

**Test files:**
- Create: `tests/api/test_scheduler_task_create.py`
- Create: `tests/api/test_scheduler_task_update.py`
- Create: `tests/api/test_scheduler_task_delete.py`
- Create: `tests/api/test_scheduler_task_run.py`
- Create: `tests/api/test_scheduler_tasks_list.py`
- Create: `tests/api/test_scheduler_tick.py`

### Task 4.6: File Management API

**Test files:**
- Create: `tests/api/test_get_work_dir_files.py`
- Create: `tests/api/test_upload_work_dir_files.py`
- Create: `tests/api/test_download_work_dir_file.py`
- Create: `tests/api/test_edit_work_dir_file.py`
- Create: `tests/api/test_delete_work_dir_file.py`
- Create: `tests/api/test_rename_work_dir_file.py`
- Create: `tests/api/test_upload.py`
- Create: `tests/api/test_file_info.py`
- Create: `tests/api/test_api_files_get.py`
- Create: `tests/api/test_api_log_get.py`

### Task 4.7: Backup API

**Test files:**
- Create: `tests/api/test_backup_create.py`
- Create: `tests/api/test_backup_restore.py`
- Create: `tests/api/test_backup_restore_preview.py`
- Create: `tests/api/test_backup_inspect.py`
- Create: `tests/api/test_backup_preview_grouped.py`
- Create: `tests/api/test_backup_get_defaults.py`
- Create: `tests/api/test_backup_test.py`

### Task 4.8: Notification & Banner API

**Test files:**
- Create: `tests/api/test_notification_create.py`
- Create: `tests/api/test_notifications_clear.py`
- Create: `tests/api/test_notifications_history.py`
- Create: `tests/api/test_notifications_mark_read.py`
- Create: `tests/api/test_banners.py`

### Task 4.9: MCP & Skills API

**Test files:**
- Create: `tests/api/test_mcp_servers_apply.py`
- Create: `tests/api/test_mcp_servers_status.py`
- Create: `tests/api/test_mcp_server_get_detail.py`
- Create: `tests/api/test_mcp_server_get_log.py`
- Extend: `tests/api/test_skill_install.py` (already 26 tests)
- Create: `tests/api/test_skills.py`

### Task 4.10: Remaining API handlers

**Test files:**
- Create: `tests/api/test_agents.py`
- Create: `tests/api/test_subagents.py`
- Create: `tests/api/test_projects.py`
- Create: `tests/api/test_synthesize.py`
- Create: `tests/api/test_transcribe.py`
- Create: `tests/api/test_image_get.py`
- Create: `tests/api/test_csrf_token.py`
- Create: `tests/api/test_health.py`
- Create: `tests/api/test_history_get.py`
- Create: `tests/api/test_ctx_window_get.py`
- Create: `tests/api/test_poll.py`
- Create: `tests/api/test_pause.py`
- Create: `tests/api/test_nudge.py`
- Create: `tests/api/test_restart.py`
- Create: `tests/api/test_logout.py`
- Create: `tests/api/test_rfc.py`
- Create: `tests/api/test_tunnel.py`
- Create: `tests/api/test_tunnel_proxy.py`
- Create: `tests/api/test_metrics_dashboard.py`
- Create: `tests/api/test_api_reset_chat.py`
- Create: `tests/api/test_api_terminate_chat.py`

**After completing all Phase 4 tasks:**

Run: `python -m pytest tests/api/ -q --tb=short`

```bash
git add tests/api/
git commit -m "test: add unit tests for all API handlers (74 modules)"
```

---

## Phase 5: Extensions (42 files)

Each extension file is a hook that modifies agent behavior. Test that the hook function:
1. Modifies the expected attribute (prompt, history, data)
2. Handles missing/empty inputs gracefully
3. Respects conditions (e.g., agent.number > 0)

Group by hook type.

### Task 5.1: Agent Init extensions

**Test files:**
- Create: `tests/extensions/test_initial_message.py` ← `_10_initial_message.py`
- Create: `tests/extensions/test_load_profile_settings.py` ← `_15_load_profile_settings.py`

### Task 5.2: Banner extensions

**Test files:**
- Create: `tests/extensions/test_unsecured_connection.py`
- Create: `tests/extensions/test_missing_api_key.py`
- Create: `tests/extensions/test_system_resources.py`

### Task 5.3: Message Loop — Prompts After

**Test files:**
- Extend: `tests/extensions/test_recall_memories.py` (already 23 tests)
- Create: `tests/extensions/test_include_current_datetime.py`
- Create: `tests/extensions/test_include_loaded_skills.py`
- Create: `tests/extensions/test_include_agent_info.py`
- Create: `tests/extensions/test_include_workdir_extras.py`
- Create: `tests/extensions/test_recall_wait.py`

### Task 5.4: Message Loop — Other hooks

**Test files:**
- Create: `tests/extensions/test_organize_history_wait.py`
- Create: `tests/extensions/test_iteration_no.py`
- Create: `tests/extensions/test_organize_history.py`
- Create: `tests/extensions/test_save_chat.py`

### Task 5.5: Monologue extensions

**Test files:**
- Create: `tests/extensions/test_memorize_fragments.py`
- Create: `tests/extensions/test_memorize_solutions.py`
- Create: `tests/extensions/test_waiting_for_input_msg.py`
- Create: `tests/extensions/test_memory_init.py`
- Create: `tests/extensions/test_rename_chat.py`

### Task 5.6: Response Stream extensions

**Test files:**
- Create: `tests/extensions/test_log_from_stream.py`
- Create: `tests/extensions/test_replace_include_alias.py`
- Create: `tests/extensions/test_live_response.py`
- Create: `tests/extensions/test_mask_stream.py`
- Create: `tests/extensions/test_mask_end.py`
- Create: `tests/extensions/test_log_from_stream_end.py`

### Task 5.7: Tool, Reasoning & System extensions

**Test files:**
- Create: `tests/extensions/test_mask_secrets_tool.py`
- Create: `tests/extensions/test_unmask_secrets.py`
- Create: `tests/extensions/test_replace_last_tool_output.py`
- Create: `tests/extensions/test_system_prompt.py`
- Create: `tests/extensions/test_behaviour_prompt.py`
- Create: `tests/extensions/test_reasoning_stream.py`
- Create: `tests/extensions/test_log_for_stream.py`
- Create: `tests/extensions/test_mask_secrets_model.py`

### Task 5.8: Process Chain & UI extensions

**Test files:**
- Create: `tests/extensions/test_process_queue.py`
- Create: `tests/extensions/test_task_status_sync.py`
- Create: `tests/extensions/test_update_check.py`
- Create: `tests/extensions/test_mask_content.py`
- Create: `tests/extensions/test_save_tool_call_file.py`

**After completing all Phase 5 tasks:**

Run: `python -m pytest tests/extensions/ -q --tb=short`

```bash
git add tests/extensions/
git commit -m "test: add unit tests for all extensions (42 modules)"
```

---

## Phase 6: Tools (19 files)

Each tool has an `execute()` method. Test argument parsing, mocked execution, and response format.

### Task 6.1: Core tools

**Test files:**
- Create: `tests/tools/test_code_execution_tool.py` ← (495 LOC, most complex)
- Create: `tests/tools/test_browser_agent.py` ← (428 LOC)
- Create: `tests/tools/test_scheduler.py` ← (280 LOC)
- Create: `tests/tools/test_skills_tool.py` ← (138 LOC)

### Task 6.2: Memory tools

**Test files:**
- Create: `tests/tools/test_memory_save.py`
- Create: `tests/tools/test_memory_load.py`
- Create: `tests/tools/test_memory_delete.py`
- Create: `tests/tools/test_memory_forget.py`

### Task 6.3: Communication tools

**Test files:**
- Create: `tests/tools/test_call_subordinate.py`
- Create: `tests/tools/test_a2a_chat.py`
- Create: `tests/tools/test_notify_user.py`
- Create: `tests/tools/test_input.py`
- Create: `tests/tools/test_response.py`

### Task 6.4: Utility tools

**Test files:**
- Create: `tests/tools/test_vision_load.py`
- Create: `tests/tools/test_wait.py`
- Create: `tests/tools/test_behaviour_adjustment.py`
- Create: `tests/tools/test_document_query.py`
- Create: `tests/tools/test_search_engine.py`
- Create: `tests/tools/test_unknown.py`

**After completing all Phase 6 tasks:**

Run: `python -m pytest tests/tools/ -q --tb=short`

```bash
git add tests/tools/
git commit -m "test: add unit tests for all tools (19 modules)"
```

---

## Phase 7: Root & WebSocket Handlers

### Task 7.1: WebSocket handlers

**Test files:**
- Create: `tests/helpers/test_default_handler.py` ← `websocket_handlers/_default.py`
- Create: `tests/helpers/test_dev_websocket_test_handler.py` ← `dev_websocket_test_handler.py`
- Create: `tests/helpers/test_hello_handler.py` ← `hello_handler.py`
- Extend: `tests/helpers/test_state_sync_handler.py` ← `state_sync_handler.py`

### Task 7.2: Root Python files

**Test files:**
- Create: `tests/test_agent.py` ← `agent.py`
- Create: `tests/test_initialize.py` ← `initialize.py`
- Create: `tests/test_models.py` ← `models.py`

**After completing all Phase 7 tasks:**

Run: `python -m pytest tests/ -q --tb=short`

```bash
git add tests/
git commit -m "test: add tests for websocket handlers and root modules"
```

---

## Phase 8: Final Verification

### Task 8.1: Full test suite run

Run: `python -m pytest tests/ -m "not integration" -v --tb=short -q`

Expected: ~1500+ tests pass, 0 failures, 0 errors.

### Task 8.2: Coverage report

Run: `python -m pytest tests/ -m "not integration" --cov=python --cov-report=term-missing --cov-report=html -q`

Review coverage report, identify any critical gaps.

### Task 8.3: CI validation

Push to branch, verify GitHub Actions workflow runs successfully.

```bash
git add .
git commit -m "test: comprehensive test coverage complete"
```

---

## Execution Notes

- **Each task should be independently runnable** — don't depend on other tasks within the same phase
- **Use conftest fixtures** — don't duplicate mock setup in test files
- **Mock external dependencies** at the import boundary (e.g., `patch("python.helpers.memory._get_cognee")`)
- **Test file naming** must match: `test_<module_name>.py`
- **Run tests after each task** to catch issues early
- **Commit after each phase** at minimum (more frequent commits preferred)
