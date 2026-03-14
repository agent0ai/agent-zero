# App Spec Bundle

This folder contains structured JSON specs and schemas to help coding agents quickly understand Agent Jumbo features, workflows, and integration points.

## Files

- `app_spec.json`: Root index and entrypoints (at repo root).
- `overview.json`: Product summary and capabilities.
- `use_cases.json`: Key use cases.
- `user_stories.json`: User stories and acceptance criteria.
- `components.json`: Major components and responsibilities.
- `apis.json`: API endpoints and purpose.
- `data_models.json`: Core models and fields.
- `permissions.json`: Approval and permission model summary.
- `ui_routes.json`: UI entry points.
- `operations.json`: Run/config/test guidance.
- `feature_map.json`: Maps features to files and spec IDs.
- `acceptance_tests.json`: Manual acceptance test steps.
- `eval_cases.json`: Automated evaluation prompts and expectations.
- `eval_cases_extended.json`: Additional evaluation coverage for safety, telemetry, and no-tool cases.
- `eval_results.sample.json`: Example results format for the eval runner.
- `eval_results_extended.sample.json`: Example results format for extended evals.
- `manifest.json`: Lists all specs and schemas.

## Schemas

Each JSON file has a matching schema named `<file>.schema.json`.

## Usage

- Use `app_spec.json` to locate spec files.
- Use schema files to validate or lint updates.
- Use `feature_map.json` to find implementation locations.
- Use `acceptance_tests.json` as a manual QA checklist.
- Run `scripts/validate_app_spec.py` or `scripts/validate_app_spec.sh` to validate specs against schemas.
- Run `scripts/run_eval_cases.py --results path/to/results.json` to score eval outputs.
