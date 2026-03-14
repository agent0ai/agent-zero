# RC1: Lifecycle + Browser Validation

## Objective

Deliver a release candidate that enables repeatable, project-scoped lifecycle execution with visual browser validation using existing Google-authenticated browser profiles.

## Included Features

- Project lifecycle phases: `design`, `development`, `testing`, `validation`, `ai_agent_evaluation`
- Lifecycle orchestration via workflow templates and run history persistence
- Visual validation integration per phase using `agent-browser`
- Per-user browser profile binding through lifecycle settings:
  - `browser.profile_name` (fallback default)
  - `browser.profiles.<actor>` (user-specific override)
- Projects UI lifecycle panel:
  - set current phase
  - run current phase
  - inspect recent run history

## RC1 Success Criteria

### Functional

- Lifecycle API actions pass smoke checks: `get`, `upsert`, `set_phase`, `run_phase`, `list_phase_runs`
- At least one phase run per project type can be started and recorded
- Run history is persisted under `.a0proj/lifecycle/runs`
- Single-run lock prevents overlapping lifecycle execution on the same project
- Run records include `started_at`, `finished_at`, and `duration_ms`

### Visual Validation

- If `run_visual=true` and no `visual_suite` is configured for the phase, run fails with explicit error
- If no browser profile is configured (`browser.profile_name` and `browser.profiles.<actor>` both missing), run fails with explicit error
- If actor-specific profile exists, it is preferred over fallback profile

### UI

- Lifecycle panel loads without breaking project edit flow
- User can set phase and run phase from the modal
- Recent run list refreshes after run

### Quality Gate

- Targeted tests pass:
  - `tests/test_project_validation.py`
  - `tests/test_project_lifecycle.py`
- Retention policy validated (`retention.max_runs`) to cap run-history growth

## RC Evidence Package

Collect the following before RC1 go/no-go:

- Test output logs for compile + targeted pytest commands
- Manual smoke evidence for:
  - phase set/run/history in UI
  - actor-specific Google-auth profile run
  - explicit failure messages for missing suite/profile
- List of known limitations and workarounds
- Rollback notes for disabling lifecycle visual runs if needed

## Test Commands

```bash
python -m py_compile python/helpers/project_lifecycle.py python/api/project_lifecycle.py python/tools/project_lifecycle.py
pytest -q tests/test_project_validation.py tests/test_project_lifecycle.py
```
