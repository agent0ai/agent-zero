# Release Checklist

Follow this checklist when preparing a release.

## Pre-Release (48 hours before)

- [ ] All tests passing: `pytest tests/ -v`
- [ ] All code quality checks passing:
  - [ ] `black --check python/`
  - [ ] `ruff check python/`
  - [ ] `mypy python/`
  - [ ] `bandit -r python/`
- [ ] Documentation is up-to-date
  - [ ] README.md reflects current features
  - [ ] INSTALL.md has latest instructions
  - [ ] API documentation matches code
  - [ ] Quick reference has working examples
- [ ] No security issues in dependencies: `pip-audit`
- [ ] Coverage remains above 90%: `pytest --cov`

## Release Day (Day of Release)

### Code Preparation

- [ ] Create release branch: `git checkout -b release/v1.x.x`
- [ ] Update version in:
  - [ ] `setup.py` or `pyproject.toml`
  - [ ] `python/__init__.py`
  - [ ] `docs/conf.py` (if using Sphinx)
- [ ] Update CHANGELOG.md
  - [ ] Move [Unreleased] changes to version header
  - [ ] Add release date
  - [ ] Review all changes are documented
- [ ] Commit: `git commit -m "chore: release v1.x.x"`
- [ ] Tag: `git tag -a v1.x.x -m "Release v1.x.x"`
- [ ] Push: `git push origin release/v1.x.x && git push origin v1.x.x`

### GitHub Release

- [ ] Go to <https://github.com/agent-jumbo-deploy/agent-jumbo-devops/releases>
- [ ] Click "Draft a new release"
- [ ] Select tag: `v1.x.x`
- [ ] Title: `Release v1.x.x`
- [ ] Description: Copy from CHANGELOG.md
- [ ] If beta: Check "Pre-release"
- [ ] Click "Publish release"

### PyPI Publishing

- [ ] Build distribution: `python setup.py sdist bdist_wheel`
- [ ] Verify build: `twine check dist/*`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Verify on PyPI: <https://pypi.org/project/agent-jumbo-devops/>

### Documentation

- [ ] Update docs to reference new version
- [ ] Update installation guide with new version
- [ ] Verify all links work
- [ ] Deploy documentation if using Read the Docs

### Communication

- [ ] Write blog post announcing release
- [ ] Post to dev.to
- [ ] Update GitHub discussions
- [ ] Announce on community channels
- [ ] Thank contributors in announcement

## RC Validation (Before promoting a release candidate)

- [ ] Validate against RC-specific criteria document (if present)
  - [ ] Current RC baseline: `docs/RC1_LIFECYCLE_BROWSER.md`
  - [ ] MCP performance RC baseline: `docs/RC_MCP_TOOL_PERFORMANCE.md`
- [ ] Complete targeted functional smoke scenarios for RC scope
- [ ] Confirm explicit failure behavior for known misconfiguration cases

## Post-Release (24 hours after)

- [ ] Monitor GitHub issues for problems
- [ ] Check PyPI stats
- [ ] Monitor discussions for feedback
- [ ] Create hotfix branch if critical issues found
- [ ] Merge release branch to main (if not already)
- [ ] Delete release branch: `git branch -d release/v1.x.x`
- [ ] Create new development branch: `git checkout -b develop`

## Rollback Plan

If critical issue found:

1. Create hotfix branch: `git checkout -b hotfix/v1.x.x`
2. Fix the issue
3. Run full test suite
4. Create new release with patch version
5. Follow release checklist for hotfix
6. Announce hotfix release

## Release Schedule

- **Regular releases**: Monthly (first Friday of month)
- **Hotfixes**: As needed (same day)
- **Major releases**: Quarterly (with planning period)
- **LTS releases**: Annually (12 months support)

## Communication Template

```text
# Release: Agent Jumbo DevOps v1.x.x

We're excited to announce v1.x.x!

## What's New

- Feature 1
- Feature 2
- Bug fix 1

## Upgrade Guide

pip install --upgrade agent-jumbo-devops

## Breaking Changes

(If any)

## Contributors

Thank you to: @contributor1, @contributor2

[Full Changelog](https://github.com/agent-jumbo-deploy/agent-jumbo-devops/blob/main/CHANGELOG.md)
```
