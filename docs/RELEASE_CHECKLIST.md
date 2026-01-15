# Release Checklist

## Automated Validation

- [ ] `scripts/validate_app_spec.sh`
- [ ] `pytest tests/test_app_spec_consistency.py tests/test_eval_cases_schema.py tests/test_eval_cases_extended_schema.py`
- [ ] `scripts/run_eval_cases.py --results path/to/results.json`
- [ ] `scripts/run_eval_cases.py --results path/to/results.json --cases app_spec/eval_cases_extended.json`

## Manual UI Smoke Tests

- [ ] Cowork: approval required for out-of-scope action
- [ ] Cowork: approve & retry resumes the action
- [ ] Cowork: approval inheritance for subagents
- [ ] Observability: telemetry events and stats populate
- [ ] Observability: clear telemetry resets view
- [ ] Observability: LangSmith/Langfuse provider selection works
- [ ] Observability: workflow runs render and can be saved
- [ ] Gmail: OAuth flow, account listed, test send succeeds
- [ ] MCP: config applied and tools available

## Docs & Packaging

- [ ] `docs/COWORK_MODE.md` matches UI behavior
- [ ] `docs/OBSERVABILITY.md` matches UI behavior
- [ ] Update release notes/changelog

## Environment Prep

- [ ] Dependencies installed for full test suite
- [ ] Docker build/redeploy (if applicable)
- [ ] UI launch smoke test
