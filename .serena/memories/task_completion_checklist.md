# Task Completion Checklist

When completing a development task on Apollos AI:

## Code Quality
1. **Run linter**: `mise run lint` (Ruff for Python, Biome for CSS)
2. **Check formatting**: `mise run format:check` (or `mise run format` to auto-fix)
3. **Run tests**: `mise run test` (pytest with async support)
4. **Run CI checks**: `mise run ci` (all-in-one: lint + format + test)

## Pre-commit (hk hooks)
5. **Hooks auto-run on commit** via `hk` (configured in `hk.pkl`):
   - Ruff lint + format check
   - Biome CSS lint
   - Security checks (no secrets/env files)
   - File hygiene (trailing whitespace, EOF newlines)
6. **Commit message format**: Conventional Commits (`type(scope): description`)
   - Install hooks if missing: `mise run hooks:install`
   - Check manually: `mise run hooks:check`

## Structural Checks
7. **Auto-discovery**: If adding new tools/API handlers/WS handlers, ensure they follow naming and class conventions for auto-discovery
8. **Extension hooks**: If modifying agent loop behavior, verify extension hooks are not broken
9. **Environment variables**: If adding new config, consider `A0_SET_` prefix convention, update settings.py, and add to `docs/reference/environment-variables.md` and `usr/.env.example`

## Dependency Changes
10. **Add deps via**: `mise run deps:add <pkg>` (updates pyproject.toml + regenerates requirements.txt)
11. **Never edit requirements.txt manually** — it's auto-generated from `uv export`
12. **Check lockfile**: `uv.lock` should be committed after dependency changes

## Optional Quality Steps
13. **Drift analysis**: `mise run drift:scan` to check for pattern violations
14. **Quality gates**: `mise run drift:gate` (advisory, not blocking)
15. **Test the web UI**: If UI changes, verify at the configured web URL

## CI/CD (GitHub Actions)
- Push/PR to main triggers: lint, format check, test (parallel jobs)
- PRs to main also run: hk hook validation
- Source changes to python/tests/prompts trigger: drift analysis
- Tag push `v*` triggers: changelog generation + GitHub release
