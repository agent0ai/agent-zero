---
description: Audit Claude Code project setup and generate comprehensive health report
argument-hint: "[--format <markdown|json|html>] [--export <file>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - Write
---

# Project Audit Command

## Overview

Audits your Claude Code project setup and generates a comprehensive health report with recommendations for improvements.

## Usage

```bash
# Interactive audit with recommendations
/project:audit

# Export as JSON
/project:audit --format json --export audit-report.json

# Export as HTML dashboard
/project:audit --format html --export dashboard.html

# Quick markdown summary
/project:audit --format markdown
```

## What This Command Audits

1. **Directory Structure**
   - Required directories present
   - Recommended directories missing
   - Unexpected files flagged

2. **Commands**
   - Total command count
   - Command categories
   - Unused commands
   - Broken commands (syntax errors)
   - Commands without documentation

3. **Skills**
   - Project skills count
   - Personal skills available
   - Skill activation rate
   - Skills with errors
   - Duplicate skills

4. **Automation**
   - Analytics configured
   - CI/CD pipelines active
   - Git hooks installed
   - Cron jobs running
   - Automation script health

5. **Configuration**
   - CLAUDE.md completeness
   - Git configuration
   - Dependencies up to date
   - Security vulnerabilities

6. **Documentation**
   - Documentation coverage
   - Outdated documentation
   - Missing documentation
   - Documentation quality

7. **Testing**
   - Test coverage
   - Skill tests present
   - Integration tests
   - CI test status

8. **Performance**
   - Command execution time
   - Skill activation speed
   - Resource usage
   - Optimization opportunities

## Audit Report Format

```markdown
# Claude Code Project Audit Report

Generated: 2025-01-24 14:30:22
Project: [Project Name]
Type: Node.js/TypeScript

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 Overall Health Score: 87/100 (Good)

### Score Breakdown
- Structure: 95/100 ✅ Excellent
- Commands: 85/100 ✅ Good
- Skills: 80/100 ✅ Good
- Automation: 90/100 ✅ Excellent
- Configuration: 88/100 ✅ Good
- Documentation: 75/100 ⚠️  Needs Improvement
- Testing: 82/100 ✅ Good
- Performance: 91/100 ✅ Excellent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📁 Directory Structure (95/100)

**Present:**
- ✅ .claude/commands/ (13 commands)
- ✅ .claude/skills/ (3 skills)
- ✅ automation/scripts/ (12 scripts)
- ✅ tests/skills/ (test framework)
- ✅ docs/ (4 documents)
- ✅ .github/workflows/ (3 workflows)

**Missing (Recommended):**
- ⚠️  .claude/templates/ - For command/skill templates
- ⚠️  tests/integration/ - For integration tests

**Unexpected:**
- ⚠️  .claude/.cache/ - Should be in .gitignore
- ⚠️  automation/scripts/old/ - Orphaned directory

**Recommendations:**
1. Create .claude/templates/ for consistency
2. Add tests/integration/ for comprehensive testing
3. Add .claude/.cache to .gitignore
4. Remove or document automation/scripts/old/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚙️  Commands (85/100)

**Summary:**
- Total commands: 13
- Working: 12 (92%)
- Broken: 1 (8%)
- Documented: 11 (85%)
- Used (last 30 days): 9 (69%)

**By Category:**
- Development: 5 commands
- Database: 3 commands
- API: 2 commands
- Project Management: 3 commands

**Issues Found:**

❌ **Broken Command** (1)
- `/dev:deploy` - Syntax error on line 45
  ```

  Error: Missing closing quote in bash command
  Location: .claude/commands/dev/deploy.md:45
  Fix: Add closing quote to --message parameter

  ```

⚠️  **Undocumented Commands** (2)
- `/db:backup` - No description in frontmatter
- `/api:mock` - Missing usage examples

⚠️  **Unused Commands** (4)
- `/dev:profile` - Never used (created 45 days ago)
- `/db:explain` - Last used 60 days ago
- `/api:contract-test` - Never used
- `/docs:validate` - Last used 90 days ago

**Recommendations:**
1. Fix `/dev:deploy` syntax error
2. Add documentation to `/db:backup` and `/api:mock`
3. Review unused commands - remove or promote usage
4. Consider archiving commands unused >90 days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 Skills (80/100)

**Project Skills:** 3
- code-reviewer (last activated: 2 days ago)
- custom-linter (last activated: 5 days ago)
- deployment-helper (last activated: 12 days ago)

**Personal Skills Available:** 4
- stripe-revenue-analyzer
- content-optimizer
- brand-voice
- vercel-landing-page-builder

**Activation Stats (30 days):**
- Total activations: 47
- Successful: 44 (94%)
- Failed: 3 (6%)
- Average response time: 2.3s

**Issues Found:**

❌ **Skill Errors** (1)
- `custom-linter` - Failed to activate 3 times in last week
  ```

  Error: SKILL.md line 23: Invalid allowed-tools syntax
  Fix: Change 'Bash,Read' to array format: ['Bash', 'Read']

  ```

⚠️  **Inactive Skills** (1)
- `deployment-helper` - Not activated in 12 days
  ```

  Last used: 2025-01-12
  Activation frequency: Declining (was daily, now weekly)
  Action: Review if still needed or improve activation trigger

  ```

**Recommendations:**
1. Fix `custom-linter` SKILL.md syntax
2. Review `deployment-helper` activation triggers
3. Consider creating skill for repetitive tasks
4. Document skill usage patterns for team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🤖 Automation (90/100)

**Analytics:**
- ✅ Daily collection configured (6 PM)
- ✅ Weekly analysis configured (Monday 6 AM)
- ✅ Last run: 23 hours ago (successful)
- ✅ Data directory: 2.1 GB (45 days)

**CI/CD:**
- ✅ GitHub Actions: 3 workflows active
- ✅ test.yml: Passing (last run: 2 hours ago)
- ✅ lint.yml: Passing (last run: 2 hours ago)
- ⚠️  deploy.yml: Last failed (3 days ago)

**Git Hooks:**
- ✅ pre-commit: Installed and active
- ✅ commit-msg: Installed and active
- ✅ Last execution: 4 hours ago (passed)

**Cron Jobs:**
- ✅ Daily analytics: Running
- ✅ Weekly analysis: Running
- ⚠️  Dependency updates: Not configured

**Issues Found:**

⚠️  **Failed CI/CD** (1)
- `deploy.yml` workflow failed 3 days ago
  ```

  Error: Vercel API key expired
  Action: Update VERCEL_TOKEN secret in GitHub
  Last successful deploy: 2025-01-21

  ```

⚠️  **Missing Automation** (1)
- Dependency updates not automated
  ```

  Recommendation: Add Dependabot or Renovate
  Impact: Security vulnerabilities, outdated packages
  Effort: 15 minutes setup

  ```

**Recommendations:**
1. Fix Vercel deployment - update API token
2. Add dependency update automation (Dependabot)
3. Set up backup rotation (analytics data growing)
4. Add monitoring for automation failures

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚙️  Configuration (88/100)

**.claude/CLAUDE.md:**
- ✅ Project overview present
- ✅ Commands documented
- ✅ Skills listed
- ⚠️  Automation section outdated (mentions old scripts)
- ⚠️  Quality standards not defined

**Git Configuration:**
- ✅ .gitignore properly configured
- ✅ Git hooks installed
- ✅ Commit template configured

**Dependencies:**
- ✅ All production dependencies up to date
- ⚠️  3 dev dependencies outdated:
  - jest: 29.5.0 → 29.7.0 (minor update available)
  - eslint: 8.45.0 → 8.56.0 (patch updates)
  - typescript: 5.1.6 → 5.3.3 (minor update)

**Security:**
- ✅ No high-severity vulnerabilities
- ⚠️  1 moderate vulnerability:
  - semver: 7.5.3 (update to 7.5.4)

**Recommendations:**
1. Update CLAUDE.md automation section
2. Define quality standards in CLAUDE.md
3. Update dev dependencies (npm update)
4. Fix semver vulnerability (npm audit fix)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📚 Documentation (75/100)

**Present:**
- ✅ docs/COMMANDS.md (comprehensive)
- ✅ docs/WORKFLOWS.md (good examples)
- ⚠️  docs/SKILLS.md (outdated, missing 2 skills)
- ⚠️  README.md (mentions old setup)

**Missing:**
- ⚠️  CONTRIBUTING.md
- ⚠️  docs/TROUBLESHOOTING.md
- ⚠️  docs/ARCHITECTURE.md

**Quality Issues:**

⚠️  **Outdated Documentation** (2)
- docs/SKILLS.md: Missing `custom-linter` and `deployment-helper`
- README.md: References old command structure

⚠️  **Coverage Gaps** (3)
- No troubleshooting guide
- Architecture not documented
- Contribution guidelines missing

**Recommendations:**
1. Update docs/SKILLS.md with current skills
2. Update README.md with current structure
3. Add CONTRIBUTING.md for team
4. Create docs/TROUBLESHOOTING.md
5. Document architecture in docs/ARCHITECTURE.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🧪 Testing (82/100)

**Test Coverage:**
- Overall: 78% (target: 80%+)
- Commands: Not tested
- Skills: 67% tested (2 of 3 have tests)
- Integration: 0% (no integration tests)

**Test Files:**
- tests/skills/TESTING-FRAMEWORK.md: ✅ Present
- tests/skills/stripe-revenue-analyzer/: ✅ Complete
- tests/skills/content-optimizer/: ✅ Complete
- tests/skills/brand-voice/: ✅ Complete
- tests/skills/code-reviewer/: ⚠️  Missing
- tests/integration/: ❌ No integration tests

**CI Test Results:**
- Unit tests: ✅ 124/124 passing
- Linting: ✅ No errors
- Type checking: ✅ No errors

**Issues Found:**

⚠️  **Missing Tests** (1)
- `code-reviewer` skill has no tests
  ```

  Risk: Skill may have issues not caught
  Recommendation: Create test suite
  Priority: Medium

  ```

❌ **No Integration Tests** (1)
- No tests for multi-skill workflows
  ```

  Risk: Skills may not work together correctly
  Recommendation: Add tests/integration/
  Example: Test stripe-revenue-analyzer + content-optimizer
  Priority: High

  ```

⚠️  **Coverage Below Target** (1)
- 78% coverage (target: 80%+)
  ```

  Gap: 2 percentage points
  Missing coverage: Error handling paths

  ```

**Recommendations:**
1. Create tests for `code-reviewer` skill
2. Add integration test suite
3. Increase coverage to 80%+ (focus on error paths)
4. Add test documentation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚡ Performance (91/100)

**Command Execution:**
- Average: 1.8s (excellent)
- Fastest: 0.3s (/dev:test --list)
- Slowest: 12.4s (/dev:deploy)
- 90th percentile: 3.2s

**Skill Activation:**
- Average: 2.3s (good)
- Fastest: 1.1s (brand-voice)
- Slowest: 4.7s (code-reviewer)
- Success rate: 94%

**Resource Usage:**
- Disk: 2.3 GB (analytics data)
- Memory: ~200 MB average
- CPU: <5% average

**Optimization Opportunities:**

⚠️  **Slow Command** (1)
- `/dev:deploy` takes 12.4s average
  ```

  Bottleneck: API calls to Vercel
  Optimization: Implement caching, parallel uploads
  Potential improvement: 40% faster (7.4s)

  ```

⚠️  **Large Data Directory** (1)
- analytics-data/ is 2.3 GB
  ```

  Growth rate: 50 MB/day
  Recommendation: Implement data rotation (keep 90 days)
  Disk saved: ~1.8 GB

  ```

**Recommendations:**
1. Optimize `/dev:deploy` with caching
2. Implement analytics data rotation
3. Add performance monitoring for skills
4. Set up performance budget alerts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 Priority Recommendations

### High Priority (Fix Immediately)

1. **Fix `/dev:deploy` Syntax Error**
   - Impact: Command broken
   - Effort: 5 minutes
   - File: .claude/commands/dev/deploy.md:45

2. **Update Vercel API Token**
   - Impact: Deployments failing
   - Effort: 10 minutes
   - Location: GitHub Secrets

3. **Add Integration Tests**
   - Impact: Risk of skill incompatibility
   - Effort: 2-3 hours
   - Directory: tests/integration/

### Medium Priority (This Week)

4. **Fix `custom-linter` Skill**
   - Impact: Skill activation failures
   - Effort: 15 minutes
   - File: .claude/skills/custom-linter/SKILL.md

5. **Update Documentation**
   - Impact: Team confusion
   - Effort: 1 hour
   - Files: docs/SKILLS.md, README.md

6. **Add Missing Documentation**
   - Impact: Onboarding friction
   - Effort: 2-3 hours
   - Files: CONTRIBUTING.md, docs/TROUBLESHOOTING.md

### Low Priority (This Month)

7. **Set Up Dependency Automation**
   - Impact: Security, maintenance
   - Effort: 15 minutes
   - Tool: Dependabot or Renovate

8. **Optimize `/dev:deploy` Performance**
   - Impact: Developer experience
   - Effort: 1-2 hours
   - Improvement: 40% faster

9. **Implement Data Rotation**
   - Impact: Disk usage
   - Effort: 30 minutes
   - Savings: 1.8 GB

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📈 Trends (30-day comparison)

**Improvements:**
- ✅ Command usage up 23%
- ✅ Skill activation success up 4%
- ✅ Test coverage up 8%
- ✅ Documentation completeness up 12%

**Declines:**
- ⚠️  Deploy success rate down 15%
- ⚠️  Average command execution time up 0.3s

**New:**
- ✅ Added 3 new commands
- ✅ Added 1 new skill
- ✅ Added 2 new automation scripts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 Health Score History

| Date       | Score | Change | Notes                    |
|------------|-------|--------|--------------------------|
| 2025-01-24 | 87/100| +3     | Added integration tests  |
| 2025-01-17 | 84/100| +2     | Fixed documentation      |
| 2025-01-10 | 82/100| -5     | Deploy issues started    |
| 2025-01-03 | 87/100| +1     | Added new skills         |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔧 Quick Fixes

Run these commands to fix high-priority issues:

```bash
# Fix deploy syntax error
vim .claude/commands/dev/deploy.md  # Line 45: Add closing quote

# Update dependencies and fix vulnerability
npm update
npm audit fix

# Create missing directories
mkdir -p .claude/templates tests/integration

# Add to .gitignore
echo ".claude/.cache" >> .gitignore

# Fix custom-linter skill
# Edit .claude/skills/custom-linter/SKILL.md
# Change line 23: allowed-tools to array format

# Update Vercel token
# GitHub → Settings → Secrets → Update VERCEL_TOKEN
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 Next Audit

**Recommended frequency:** Monthly

**Schedule next audit:**

```bash
# Add to calendar
# Date: 2025-02-24
# Command: /project:audit
```

**Focus areas for next audit:**

- Integration test coverage
- Documentation completeness
- Deployment reliability

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```

## Export Formats

### JSON Export

```json
{
  "audit_date": "2025-01-24T14:30:22Z",
  "project_name": "My Project",
  "overall_score": 87,
  "scores": {
    "structure": 95,
    "commands": 85,
    "skills": 80,
    "automation": 90,
    "configuration": 88,
    "documentation": 75,
    "testing": 82,
    "performance": 91
  },
  "issues": {
    "high": 3,
    "medium": 6,
    "low": 9
  },
  "recommendations": [...]
}
```

### HTML Dashboard

Interactive dashboard with:

- Score gauges
- Trend charts
- Issue drill-downs
- Quick fix buttons
- Export to PDF

---

*Regular audits keep your Claude Code setup healthy and optimized*
