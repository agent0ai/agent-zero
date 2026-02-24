# Autonomy Testing Guide

This guide provides a repeatable validation flow for autonomy guardrails and knobs.

## Test layers

1. Smoke validation
2. Knob-family functional tests
3. Stress/soak tests

## Preconditions

- Runtime built from `feature/autonomy` changes
- Persistent data backed up before destructive tests
- Settings can be changed through UI or `A0_SET_*` env keys
- Profile examples available in `docs/setup/env-examples/`

---

## A) Smoke tests

### A1. Startup and health

- Start/restart service 2-3 times
- Verify UI/API health checks stay green
- Confirm settings panel loads and save works

### A2. Baseline balanced profile

- Apply `profile_balanced_production.env`
- Run normal day-to-day tasks
- Confirm no immediate guardrail regressions

---

## B) Functional tests by knob family

### B1. Monologue guardrails

Use tight values:

- `agent_max_iterations=3`
- `agent_max_runtime_seconds=30`
- `agent_max_consecutive_misformats=2`
- `agent_max_consecutive_repairable_errors=2`

Expected:

- explicit guardrail termination reasons
- no endless looping

### B2. Tool payload controls

Use:

- `tool_args_max_chars=2000`
- `tool_args_spill_threshold_chars=400`

Expected:

- payload > threshold spills
- payload > max is rejected with warning

### B3. Code execution reliability

Use:

- low first/between/max timeouts
- small output max chars + dump enabled

Expected:

- each timeout path triggers predictably
- large output truncates and dumps

### B4. File-write policy behavior

Use:

- `code_exec_prefer_python_file_write=true`

Expected:

- terminal heredoc writes are blocked or converted to Python write path
- malformed heredoc fails fast with clear warning
- no long wait loops from unterminated heredoc

### B5. Subordinate limits

Use:

- depth/calls/runtime set low

Expected:

- predictable subordinate guardrail warnings
- no runaway delegation trees

### B6. Queue backpressure

Use low queue limits and test both:

- `queue_drop_policy=drop_oldest`
- `queue_drop_policy=reject`

Expected:

- behavior matches policy
- `reject` path surfaces queue rejections cleanly

### B7. Memory load bounds

Use low memory-load clamps.

Expected:

- query truncated
- limit clamped
- response bounded

### B8. History compression

Compare aggressive vs lenient ratios/pass limits on same chat corpus.

Expected:

- aggressive profile compresses more
- lenient retains more context

### B9. Runtime budgets

Set small turn/task/subordinate budgets.

Expected:

- deterministic budget-triggered exits

---

## C) Soak and stability

### C1. Balanced soak (2+ hours)

- mixed workloads, periodic tool usage
- monitor for looping, stalls, crash cycles

### C2. Safety stress (15-30 minutes)

- conservative/tight profile under bursty load
- confirm predictable rejection and guardrail behavior

---

## Evidence checklist

Capture for each test:

- profile/knob values
- trigger prompt or API input
- relevant log window
- expected vs actual
- pass/fail decision and reason

Store outputs in timestamped test run folders for PR evidence.
