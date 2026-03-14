# RC2: Lifecycle Expansion Candidate

## Objective

Expand RC1 lifecycle baseline with collaborative controls and lightweight reporting while preserving RC1 API compatibility.

## Planned Features

- Lifecycle scheduling controls in project UI:
  - add/update/remove phase cron schedules
  - show schedule state per phase
- Access control management in project UI:
  - owner assignment
  - collaborator list editing
- Cross-project run summary view:
  - recent runs across projects
  - basic status counts by phase and outcome

## API and Tool Compatibility

- Keep existing `project_lifecycle` actions stable.
- Extend usage of existing actions already available in backend:
  - `set_access`
  - `add_phase_schedule`
  - `remove_phase_schedule`
- Any new reporting endpoint must be additive (no breaking response shape changes for RC1 actions).

## Acceptance Criteria

- User can configure schedule + access policies from UI without editing JSON files.
- Scheduler-created lifecycle runs appear in project run history.
- Unauthorized actor receives explicit access error on lifecycle mutation actions.
- Cross-project summary updates with latest run statuses from all participating projects.
- RC1 tests continue to pass unchanged.

## Test Focus

- UI integration tests for schedule and access workflows.
- API tests for access and scheduling edge cases.
- Manual validation for scheduled lifecycle runs and report accuracy.
