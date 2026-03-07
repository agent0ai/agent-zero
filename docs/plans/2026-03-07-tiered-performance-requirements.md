# Tiered Performance Requirements (Free Tier vs Pro Tier)

**Date**: 2026-03-07
**Status**: Draft for implementation
**Goal**: Define measurable performance requirements that gate free-tier release and establish pro-tier targets.

---

## 1) Why this exists

We need a stable, lower-complexity release point for a free tier while continuing advanced Agent 0 capabilities in pro tier (including persona-trained business system implementation).
This document defines the minimum and target performance standards for both tracks.

---

## 2) Tier definitions

### Free Tier

- Core agent loop
- Core tools and workflows
- No advanced persona-training features
- Cost-efficient defaults and lower concurrency limits

### Pro Tier

- Everything in free tier
- Advanced functionality (including persona-trained implementation flows)
- Higher concurrency and stronger responsiveness targets
- Premium reliability expectations

---

## 3) Performance SLOs by tier

All latency targets are measured at p95 unless otherwise specified.

| Metric | Free Tier Requirement | Pro Tier Requirement |
|---|---:|---:|
| Agent turn overhead (non-LLM internal) | <= 120 ms | <= 70 ms |
| API endpoint latency (`/api/*`) | <= 350 ms | <= 200 ms |
| Tool execution success rate | >= 99.0% | >= 99.5% |
| Error rate (5xx + hard failures) | <= 1.0% | <= 0.3% |
| Concurrent active sessions (steady) | 25 | 100 |
| P95 queue wait before tool dispatch | <= 500 ms | <= 200 ms |
| Memory retrieval latency | <= 120 ms | <= 80 ms |
| Startup time (cold start to ready) | <= 45 s | <= 30 s |

Notes:

- End-user total response time is still provider-dependent; these are platform-side controls.
- If running local models, collect results separately to avoid mixing provider latency with platform latency.

---

## 4) Performance budgets (internal)

These budgets enforce where latency can be spent.

### Free Tier (internal target total <= 120 ms)

- Security/audit layer: 40 ms
- Extension hooks: 35 ms
- Tool dispatch overhead: 25 ms
- Memory retrieval orchestration: 20 ms

### Pro Tier (internal target total <= 70 ms)

- Security/audit layer: 20 ms
- Extension hooks: 20 ms
- Tool dispatch overhead: 15 ms
- Memory retrieval orchestration: 15 ms

---

## 5) Release gates

## Free-tier push (must pass)

1. Unit and integration suite passes.
2. Performance marker suite passes with no regressions > 10% from baseline.
3. 30-minute soak test:

- Error rate <= 1.0%
- P95 non-LLM internal overhead <= 120 ms

1. No high-severity performance alerts open.

## Pro-tier release (must pass)

1. All free-tier gates pass.
2. Persona-flow benchmarks pass under concurrent load.
3. 60-minute soak test:

- Error rate <= 0.3%
- P95 non-LLM internal overhead <= 70 ms

1. Capacity test confirms 100 active sessions at target SLO.

---

## 6) Validation matrix (current repo)

Use existing markers and tests already present in the codebase as the baseline automation surface.

```bash
# Core quality gates
pytest tests -q

# Performance-focused tests
pytest tests -m performance -q

# Example targeted suites already present
pytest tests/test_reasoning_planning_engine.py -m performance -q
pytest tests/test_specialist_agent_framework.py -m performance -q
```

Optional for release hardening:

- Add a dedicated load harness for queue wait, session concurrency, and API p95 tracking.
- Persist metrics per run and compare against last accepted baseline.

---

## 7) Tier feature gating model

Use feature flags so free/pro differences are explicit and testable:

- `TIER=free|pro`
- `ENABLE_PERSONA_SYSTEMS=true|false`
- `MAX_CONCURRENT_SESSIONS=<int>`
- `PERF_SLO_PROFILE=free|pro`

Minimum behavior:

- Free tier defaults to `ENABLE_PERSONA_SYSTEMS=false`.
- Pro tier enables persona systems and higher concurrency profile.

---

## 8) Implementation sequence

1. Lock free-tier branch from pre-OPA baseline.
2. Add `TIER` + perf profile config in runtime settings.
3. Add CI job to run performance marker suite and publish p95/p99 metrics.
4. Establish baseline artifacts for free tier and pro tier separately.
5. Enforce release gate checks before push/tag.

---

## 9) Immediate next step for current release

For the next free-tier push, use these initial acceptance criteria:

- `pytest tests -m performance -q` passes
- No performance regression > 10% versus current baseline
- 30-minute soak run recorded with p95 internal overhead <= 120 ms

After this baseline is accepted, raise free-tier strictness gradually and keep pro-tier targets as the premium envelope.
