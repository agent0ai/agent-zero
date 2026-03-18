---
    title: "📋 Changelog: Security Hardening Series"
    labels: "documentation, security"
    ---

    This series of PRs implements comprehensive security hardening for Agent Zero.

    ## Series Overview

    | PR | Title | Status | Impact | Risk |
    |----|-------|--------|--------|------|
    | #1 | 🔒 Encrypted secrets storage | Planned | Critical | High |
    | #2 | 🛡️ Container security hardening | Planned | Critical | High |
    | #3 | 🔍 Remove dangerous deserialization | Planned | Critical | Medium |
    | #4 | 📊 Structured JSON logging | Planned | High | Low |
    | #5 | 🚨 Alerting & monitoring | Planned | High | Low |
    | #6 | 🔐 RBAC & authentication | Planned | Medium | Medium |
    | #7 | 🧪 Security test suite | Planned | High | Low |

    ## Individual PR Details

    ### PR #1: Encrypted Secrets Storage

    **Problem:** Secrets stored in plaintext `usr/secrets.env`

    **Solution:** Implement encrypted storage using:
    - Primary: Docker secrets (for Docker deployments)
    - Fallback: OS keyring (keyring library)
    - Enterprise: External vault (HashiCorp, AWS, Azure)

    **Files changed:**
    - `python/helpers/secrets.py` (new)
    - `python/helpers/rfc_exchange.py`
    - `docker/base/fs/ins/setup_venv.sh`
    - `docs/setup/security-hardening.md`

    **Breaking changes:** No (transparent migration)

    **Migration:** Auto-migrates plaintext → encrypted on first boot

    ---

    ### PR #2: Container Security Hardening

    **Problem:** Container runs as root with excessive capabilities

    **Solution:**
    - Create non-root `agentzero` user (UID 1000)
    - Drop all capabilities except minimum required
    - Apply seccomp profile (restrict syscalls)
    - Optional: AppArmor/SELinux profiles
    - SSH hardened (key-only auth, no root)

    **Files changed:**
    - `docker/base/Dockerfile`
    - `docker/run/Dockerfile`
    - `docker/run/docker-compose.yml`
    - `docker/seccomp-agent-zero.json` (new)
    - `docs/setup/security-hardening.md`

    **Breaking changes:** Yes (requires rebuild and pull)

    **Rollback:** Old images still work, just less secure

    ---

    ### PR #3: Remove FAISS Dangerous Deserialization

    **Problem:** `allow_dangerous_deserialization=True` allows arbitrary code execution via malicious FAISS files

    **Solution:** 
    - Use FAISS v1.7+ safe deserialization API (if compatible)
    - OR migrate to ChromaDB (safe by default)
    - Provide migration tool

    **Files changed:**
    - `python/helpers/memory.py`
    - `tests/security/test_deserialization.py` (new)

    **Breaking changes:** Maybe (existing memory indexes may need conversion)

    **Migration:** Auto-convert on first load, or provide `a0 migrate-memory` command

    ---

    ### PR #4: Structured JSON Logging

    **Problem:** Logs are plaintext HTML, not machine-parseable

    **Solution:**
    - Add `LOG_FORMAT=json|text` environment variable
    - Use `python-json-logger` for structured output
    - Include trace_id, agent_id, timestamp, level, etc.
    - Docker logging driver: `json-file` (default)

    **Files changed:**
    - `python/helpers/log.py`
    - `docker/run/fs/etc/supervisor/conf.d/supervisord.conf` (log format)
    - `monitoring/README.md` (new)

    **Breaking changes:** No (text format still default)

    ---

    ### PR #5: Alerting & Monitoring

    **Problem:** No way to know when things go wrong

    **Solution:**
    - Prometheus metrics endpoint (`/metrics`)
    - Common metrics: request rate, latency, errors, memory, CPU
    - Alertmanager rules (Slack, email, PagerDuty)
    - Grafana dashboards

    **Files changed:**
    - `requirements.txt` (+prometheus-client)
    - `python/helpers/metrics.py` (new)
    - `run_ui.py` (add /metrics)
    - `monitoring/prometheus/alerts.yml` (new)
    - `monitoring/grafana/dashboards/agent-zero.json` (new)

    **Breaking changes:** No (opt-in via feature flag)

    ---

    ### PR #6: RBAC & Authentication

    **Problem:** Any authenticated user has full access

    **Solution:**
    - Define roles: `admin`, `operator`, `viewer`, `agent`
    - Add `users:` section to settings (or integrate with LDAP/OIDC)
    - Enforce per-endpoint permissions
    - Session management improvements

    **Files changed:**
    - `python/api/auth.py` (new)
    - `python/api/endpoints/` (add @require_role decorators)
    - `conf/rbac.yaml` (new)
    - `webui/src/components/Login.jsx` (role-based UI)

    **Breaking changes:** Yes (API auth required)

    ---

    ### PR #7: Security Test Suite

    **Problem:** No automated security testing

    **Solution:**
    - Unit tests for vulnerabilities (injection, XSS, etc.)
    - Integration tests for auth, RBAC, encryption
    - OWASP ZAP baseline scan in CI
    - Dependency vuln scanning (Safety, Snyk)

    **Files changed:**
    - `tests/security/` (new directory)
    - `.github/workflows/security.yml` (new)
    - `requirements-dev.txt` (+bandit, +safety)

    **Breaking changes:** No

    ---

    ## Series Strategy

    1. **Week 1-2:** PR #1 (secrets) + PR #2 (container hardening)
       - These are foundational, dependent on each other
       - Deploy together as "security baseline"

    2. **Week 3:** PR #3 (FAISS deserialization)
       - Critical vuln, should be fast-tracked
       - Can be independent of others

    3. **Week 4:** PR #4 (logging) + PR #5 (monitoring)
       - Observability needed to monitor security fixes
       - Deploy as "ops readiness" bundle

    4. **Week 5-6:** PR #6 (RBAC) + PR #7 (tests)
       - Complete the security story
       - Tests ensure no regressions

    ## How to Follow Along

    1. **Watch PR #1283** (Bug Fixes - already open)
    2. **Star the repo** to get notifications
    3. **Check Issues** with `security` label
    4. **Join Discord** (if public) for discussions

    ## Questions?

    Open an issue tagged `question` or comment on the relevant PR.

    ## Credits

    This changelog and issue templates were generated by an AI analysis of the agent-zero codebase.

    ---
    *Security is a process, not a destination. This series represents significant progress toward production-ready security.*
    