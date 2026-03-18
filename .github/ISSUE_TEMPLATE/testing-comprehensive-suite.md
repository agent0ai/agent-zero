---
    title: "🧪 Test: Comprehensive test suite for security-critical components"
    labels: "testing, security, enhancement"
    ---

    ## Problem Statement

    Current test coverage is insufficient for critical components:

    - **Only 25 unit tests** for 265 Python files (<10% coverage)
    - **Zero E2E tests** for user-facing workflows
    - **No security tests** for injection, authentication, data validation
    - **No integration tests** for MCP, database, external APIs

    This creates high regression risk and makes contributions risky.

    ## Current State

    ```
    tests/
    ├── unit/
    │   ├── test_websocket_namespace_security.py (3 tests - only hardcoded tokens)
    │   ├── test_http_auth_csrf.py (2 tests)
    │   └── ... (others appear minimal)
    └── NO integration tests
    └── NO e2e tests
    ```

    ## Proposed Test Suite Structure

    ```
    tests/
    ├── unit/
    │   ├── test_mcp_handler.py           (MCP client/server)
    │   ├── test_memory.py                (vector DB operations)
    │   ├── test_secrets.py               (secret storage/retrieval)
    │   ├── test_code_execution.py        (shell detection, timeouts)
    │   ├── test_tools.py                 (tool base class, validation)
    │   ├── test_extensions.py            (extension loading/execution)
    │   ├── test_settings.py              (config validation)
    │   ├── test_rate_limiter.py          (rate limiting logic)
    │   └── test_path_validation.py       (path traversal prevention)
    ├── integration/
    │   ├── test_mcp_integration.py       (MCP server end-to-end)
    │   ├── test_agent_workflow.py        (agent complete workflow)
    │   ├── test_tool_chaining.py         (multi-tool execution)
    │   ├── test_memory_knowledge.py      (memory + knowledge RAG)
    │   ├── test_project_isolation.py     (project scoping)
    │   └── test_skill_system.py          (SKILL.md loading/usage)
    ├── e2e/
    │   ├── test_user_chat.py             (web UI chat flow)
    │   ├── test_browser_automation.py    (browser agent)
    │   ├── test_scheduler.py             (scheduled tasks)
    │   ├── test_backup_restore.py        (backup/restore flow)
    │   └── test_multi_agent.py           (subordinate agent creation)
    └── security/
        ├── test_injection.py             (prompt injection, code injection)
        ├── test_path_traversal.py        (../ attacks)
        ├── test_ssrf.py                  (server-side request forgery)
        ├── test_secrets_leakage.py       (verifies no secrets in logs)
        ├── test_auth_bypass.py           (authentication/authorization)
        ├── test_xss.py                   (web UI XSS prevention)
        ├── test_csrf.py                  (CSRF token validation)
        └── test_deserialization.py       (FAISS pickle attacks)
    ```

    ## Implementation Plan

    ### Phase 1: Foundation (Week 1-2)
    1. Set up test infrastructure:
       - `pytest` with `pytest-asyncio`
       - `pytest-cov` for coverage reporting
       - `pytest-mock` for mocking
       - `pytest-xdist` for parallel tests
       - Test fixtures in `conftest.py`

    2. Create test fixtures:
       - Mock LLM responses (avoid API costs)
       - Temporary memory DB (in-memory FAISS)
       - Fake MCP servers
       - Temporary project directories

    3. Achieve 50% baseline coverage:
       - Test all `__init__.py` exports
       - Test error handling paths
       - Test input validation

    ### Phase 2: Unit Tests (Week 3-4)
    1. Prioritize security-critical modules:
       - `python/helpers/mcp_handler.py`
       - `python/helpers/memory.py`
       - `python/helpers/secrets.py` (to be created)
       - `python/tools/code_execution_tool.py`

    2. Use mutation testing to find gaps:
       - `mutmut` or `cosmic-ray`
       - Ensure tests actually catch bugs

    3. Target: 80% code coverage overall

    ### Phase 3: Integration Tests (Week 5-6)
    1. Set up test fixtures:
       - Real Docker containers for integration tests
       - Mock MCP servers (stdio and SSE)
       - Temporary vector DB (use RAM disk)

    2. Test critical workflows:
       - Agent receives task → uses tools → returns result
       - Memory save → recall → update → delete
       - MCP server connection → tool call → response
       - Project creation → memory isolation

    3. Target: All main workflows tested end-to-end

    ### Phase 4: Security Tests (Week 7-8)
    1. Penetration testing:
       - Try to escape Docker via agent tools
       - Try path traversal in file operations
       - Try prompt injection to access secrets
       - Try SSRF via browser agent

    2. Static analysis integration:
       - Bandit (Python security scanner)
       - Safety (dependency vuln scanning)
       - Semgrep (semantic code analysis)
       - Snyk (commercial, but good)

    3. Dynamic analysis:
       - OWASP ZAP for web UI
       - Fuzzing tool inputs

    ### Phase 5: E2E Tests (Week 9-10)
    1. Playwright/Selenium tests:
       - User creates account, logs in
       - Creates project, adds knowledge
       - Chat with agent, verify tool usage
       - Export/import chats

    2. Performance testing:
       - Locust or k6 for load testing
       - Measure concurrent user capacity
       - Identify bottlenecks

    3. Accessibility testing:
       - axe DevTools integration
       - Screen reader compatibility

    ## CI/CD Integration

    ```yaml
    # .github/workflows/ci.yml
    name: CI
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.10'
          - name: Install dependencies
            run: pip install -r requirements.txt -r requirements-dev.txt
          - name: Run unit tests
            run: pytest tests/unit --cov=python --cov-report=xml
          - name: Run integration tests
            run: pytest tests/integration
          - name: Run security tests
            run: bandit -r python/ && safety check
          - name: Upload coverage
            uses: codecov/codecov-action@v3
    ```

    ## Metrics

    - **Coverage target:** 80%+ overall, 90%+ for security modules
    - **Test execution time:** <10 minutes for unit, <30 for full suite
    - **Security findings:** 0 high, <5 medium, <10 low

    ## Dependencies

    - `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`
    - `bandit`, `safety`, `semgrep`
    - `playwright` (for e2e)
    - `locust` (for load testing)

    ## Acceptance Criteria

    1. All tests pass on clean checkout
    2. Coverage report shows >80%
    3. No security scanner findings (or approved exemptions)
    4. E2E tests demonstrate core user workflows
    5. CI pipeline runs on all PRs

    ## Why This Matters

    - **Quality:** Catches regressions before they reach users
    - **Security:** Proves security controls work as intended
    - **Confidence:** Enables refactoring without fear
    - **Onboarding:** New contributors can run tests to verify setup
    - **Documentation:** Tests serve as executable examples

    ---
    *Comprehensive testing is essential for a security-critical AI agent framework.*
    