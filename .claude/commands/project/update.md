---
description: Update existing Claude Code project infrastructure to latest standards
argument-hint: "[--force] [--dry-run] [--component <commands|skills|automation|ci|docs>]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Write
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# Project Update Command

## Overview

Updates an existing Claude Code project setup to the latest standards, adding new features and improvements while preserving customizations.

**This command is safe** - respects existing customizations, provides dry-run mode, creates backups.

## Usage

```bash
# Interactive update (recommended)
/project:update

# Dry run (see what would change)
/project:update --dry-run

# Update specific component
/project:update --component commands

# Force update (overwrite customizations)
/project:update --force

# Update multiple components
/project:update --component commands,skills,automation
```

## What This Command Does

1. **Audits current setup**
   - Checks Claude Code version
   - Identifies outdated components
   - Detects missing features
   - Reviews custom vs. standard components

2. **Plans updates**
   - Lists files to add/update/preserve
   - Calculates compatibility
   - Identifies conflicts
   - Shows before/after comparison

3. **Creates backup** (automatic)
   - Saves current `.claude/` directory
   - Timestamps: `.claude.backup-YYYYMMDD-HHMMSS/`
   - Preserves for rollback if needed

4. **Applies updates**
   - Adds new commands
   - Updates existing commands (preserving customizations)
   - Adds new skills
   - Updates automation scripts
   - Refreshes CI/CD configurations
   - Updates documentation

5. **Validates changes**
   - Tests updated commands
   - Validates skill syntax
   - Checks automation scripts
   - Verifies CI/CD pipelines

6. **Reports results**
   - Summary of changes
   - List of preserved customizations
   - New features available
   - Migration notes if needed

## Update Components

### Commands (`--component commands`)

**Updates:**

- New slash commands added to Claude Code
- Improved command templates
- Enhanced argument parsing
- Better error messages

**Preserves:**

- Your custom commands
- Modified standard commands
- Team-specific workflows

**Example changes:**

```
Added:
- /dev:profile - Performance profiling
- /db:query - Interactive database queries
- /api:mock - Generate API mocks

Updated:
- /dev:test - Added --parallel flag
- /dev:deploy - Added rollback capability
- /db:migrate - Added --preview mode

Preserved:
- /custom:workflow (your custom command)
- /dev:test (your modifications)
```

---

### Skills (`--component skills`)

**Updates:**

- New project skills available
- Improved skill activation
- Enhanced skill documentation
- Better error handling

**Preserves:**

- Your custom skills
- Modified standard skills

**Example changes:**

```
Added:
- dependency-security-scanner
- code-complexity-analyzer
- performance-optimizer

Updated:
- code-reviewer - Improved accuracy
- test-generator - Added edge case support

Preserved:
- custom-linter (your custom skill)
```

---

### Automation (`--component automation`)

**Updates:**

- Enhanced analytics scripts
- Improved CI/CD templates
- Better Git hooks
- New automation workflows

**Preserves:**

- Custom automation scripts
- Modified standard scripts
- Team-specific workflows

**Example changes:**

```
Added:
- automation/scripts/performance-monitoring.sh
- automation/scripts/security-scan.sh

Updated:
- automation/scripts/analytics/collect-daily-data.sh
  → Added integration health checks
- automation/scripts/ci-cd/test-runner.sh
  → Added parallel test execution

Preserved:
- automation/scripts/custom-deploy.sh
```

---

### CI/CD (`--component ci`)

**Updates:**

- Latest GitHub Actions workflows
- GitLab CI improvements
- CircleCI templates
- Deployment optimizations

**Preserves:**

- Custom workflows
- Modified standard workflows
- Team-specific configurations

**Example changes:**

```
Added:
- .github/workflows/security-scan.yml
- .github/workflows/performance-test.yml

Updated:
- .github/workflows/test.yml
  → Added caching for faster runs
- .github/workflows/deploy.yml
  → Added blue-green deployment

Preserved:
- .github/workflows/custom-pipeline.yml
```

---

### Documentation (`--component docs`)

**Updates:**

- Latest command documentation
- Improved workflow guides
- Enhanced skill documentation
- Updated best practices

**Preserves:**

- Custom documentation
- Team-specific guides

**Example changes:**

```
Added:
- docs/SECURITY.md
- docs/PERFORMANCE.md

Updated:
- docs/COMMANDS.md - Added new commands
- docs/WORKFLOWS.md - Enhanced examples

Preserved:
- docs/TEAM_GUIDELINES.md
```

## Dry Run Mode

See what would change without making changes:

```bash
/project:update --dry-run
```

**Output:**

```markdown
# Update Preview (Dry Run)

## Files to Add (12)
- .claude/commands/dev/profile.md
- .claude/commands/api/mock.md
- automation/scripts/performance-monitoring.sh
[...]

## Files to Update (5)
- .claude/commands/dev/test.md
  Changes: Added --parallel flag, improved error messages
- .github/workflows/test.yml
  Changes: Added caching, parallel execution
[...]

## Files to Preserve (8)
- .claude/commands/custom/workflow.md (custom)
- .claude/skills/custom-linter/ (custom)
[...]

## Conflicts Detected (2)
- .claude/commands/dev/deploy.md
  Your version: Custom deployment to AWS
  Standard version: Deployment to Vercel
  Resolution: Keep your version, add note about standard approach

## Summary
- Add: 12 files
- Update: 5 files
- Preserve: 8 files
- Conflicts: 2 files (manual review recommended)

Run without --dry-run to apply these changes.
```

## Conflict Resolution

When conflicts detected:

### Strategy 1: Preserve Custom (Default)

```
Your custom version is kept.
Standard version saved as: file.md.standard
Review manually: diff file.md file.md.standard
```

### Strategy 2: Update with Note

```
Your custom version updated.
Your original saved as: file.md.backup
Custom parts preserved and noted.
```

### Strategy 3: Manual Review (Force Mode)

```
Both versions saved:
- file.md.yours
- file.md.standard

Choose one or merge manually.
```

## Backup and Rollback

### Automatic Backup

Every update creates backup:

```
.claude.backup-20250124-143022/
├── commands/
├── skills/
└── CLAUDE.md

automation.backup-20250124-143022/
└── scripts/
```

### Rollback

If update causes issues:

```bash
# View backups
ls -la .claude.backup-*

# Rollback to specific backup
mv .claude .claude.failed
mv .claude.backup-20250124-143022 .claude

# Or use helper command
/project:rollback --to 20250124-143022
```

## Implementation

### Step 1: Audit Current Setup

```bash
# Check Claude Code version
CURRENT_VERSION=$(grep "version:" .claude/CLAUDE.md | cut -d: -f2)

# Count components
COMMAND_COUNT=$(find .claude/commands -name "*.md" | wc -l)
SKILL_COUNT=$(find .claude/skills -name "SKILL.md" | wc -l)

# Identify customizations
CUSTOM_COMMANDS=$(grep -l "custom:" .claude/commands/**/*.md)
```

### Step 2: Plan Updates

```bash
# Compare with latest templates
AVAILABLE_COMMANDS=$(list_standard_commands)
NEW_COMMANDS=$(diff $AVAILABLE_COMMANDS $CURRENT_COMMANDS)

# Check for conflicts
for file in $STANDARD_FILES; do
    if [ -f "$file" ] && is_customized "$file"; then
        mark_conflict "$file"
    fi
done
```

### Step 3: Create Backup

```bash
BACKUP_DIR=".claude.backup-$(date +%Y%m%d-%H%M%S)"

# Backup .claude
cp -r .claude $BACKUP_DIR

# Backup automation
cp -r automation "automation.backup-$(date +%Y%m%d-%H%M%S)"

echo "✅ Backup created: $BACKUP_DIR"
```

### Step 4: Apply Updates

```bash
# Add new files
for file in $NEW_FILES; do
    cp "templates/$file" ".claude/$file"
done

# Update existing (preserving customizations)
for file in $UPDATE_FILES; do
    if is_customized "$file"; then
        # Preserve custom, save standard as reference
        cp "templates/$file" "${file}.standard"
    else
        # Safe to update
        cp "templates/$file" ".claude/$file"
    fi
done
```

### Step 5: Update CLAUDE.md

```bash
# Merge configurations
OLD_CONFIG=$(<.claude/CLAUDE.md)
NEW_CONFIG=$(<templates/CLAUDE.md)

# Preserve custom sections
# Update standard sections
# Add new sections
```

### Step 6: Validate

```bash
# Test commands exist
test_command "/dev:test"
test_command "/dev:build"

# Validate skill syntax
validate_skills

# Check automation scripts
bash -n automation/scripts/**/*.sh
```

## Output Format

```markdown
# Project Update Complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📦 Backup Created

**Location:** `.claude.backup-20250124-143022/`
**Size:** 2.4 MB
**Files:** 47

To rollback if needed:
```bash
/project:rollback --to 20250124-143022
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ✅ Changes Applied

### Commands (12 new, 5 updated)

**Added:**

- `/dev:profile` - Performance profiling with flamegraphs
- `/dev:benchmark` - Benchmark performance against baseline
- `/api:mock` - Generate API mocks from OpenAPI spec
- `/api:contract-test` - Contract testing with Pact
- `/db:query` - Interactive database queries
- `/db:explain` - Explain query execution plans
- `/security:scan` - Security vulnerability scanning
- `/security:audit` - Comprehensive security audit
- `/performance:analyze` - Analyze application performance
- `/performance:optimize` - Auto-optimize bottlenecks
- `/docs:generate` - Generate documentation from code
- `/docs:validate` - Validate documentation accuracy

**Updated:**

- `/dev:test` - Added --parallel, --bail flags
- `/dev:deploy` - Added rollback capability
- `/db:migrate` - Added --preview mode
- `/api:test` - Enhanced assertion library
- `/project:init` - Improved project detection

**Preserved:**

- `/custom:workflow` - Your team workflow (custom)
- `/dev:deploy` - Your AWS deployment (modified standard)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Skills (3 new, 2 updated)

**Added:**

- `dependency-security-scanner` - Scans for vulnerable dependencies
- `code-complexity-analyzer` - Analyzes code complexity metrics
- `performance-optimizer` - Suggests performance improvements

**Updated:**

- `code-reviewer` - Improved accuracy, added security checks
- `test-generator` - Added edge case generation

**Preserved:**

- `custom-linter` - Your custom linting rules

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Automation (4 new, 3 updated)

**Added:**

- `automation/scripts/performance-monitoring.sh`
- `automation/scripts/security-scan.sh`
- `automation/scripts/dependency-updates.sh`
- `automation/scripts/backup-automation.sh`

**Updated:**

- `automation/scripts/analytics/collect-daily-data.sh`
  → Added integration health, dependency checks
- `automation/scripts/ci-cd/test-runner.sh`
  → Added parallel execution, better reporting
- `automation/scripts/git-hooks/pre-commit`
  → Added security checks, faster execution

**Preserved:**

- `automation/scripts/custom-deploy.sh`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### CI/CD (2 new, 2 updated)

**Added:**

- `.github/workflows/security-scan.yml`
- `.github/workflows/performance-test.yml`

**Updated:**

- `.github/workflows/test.yml`
  → Added dependency caching, parallel jobs
- `.github/workflows/deploy.yml`
  → Added blue-green deployment, automatic rollback

**Preserved:**

- `.github/workflows/custom-pipeline.yml`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Documentation (2 new, 3 updated)

**Added:**

- `docs/SECURITY.md` - Security best practices
- `docs/PERFORMANCE.md` - Performance optimization guide

**Updated:**

- `docs/COMMANDS.md` - Added 12 new commands
- `docs/WORKFLOWS.md` - Enhanced examples
- `.claude/CLAUDE.md` - Updated configuration

**Preserved:**

- `docs/TEAM_GUIDELINES.md`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚠️  Manual Review Recommended (2 conflicts)

1. **`.claude/commands/dev/deploy.md`**
   - Your version: Custom AWS deployment
   - Standard version: Vercel deployment
   - Resolution: Kept your version
   - Reference: `.claude/commands/dev/deploy.md.standard`

2. **`.github/workflows/test.yml`**
   - Your version: Custom test configuration
   - Standard version: Enhanced caching
   - Resolution: Merged both approaches
   - Original: `.github/workflows/test.yml.backup`

Review conflicts:

```bash
diff .claude/commands/dev/deploy.md{,.standard}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 New Features Available

### Performance Monitoring

```bash
/dev:profile          # Profile application performance
/dev:benchmark        # Benchmark against baseline
/performance:analyze  # Comprehensive analysis
```

### Security

```bash
/security:scan   # Scan for vulnerabilities
/security:audit  # Full security audit
```

### Enhanced Testing

```bash
/dev:test --parallel  # Run tests in parallel
/api:contract-test    # Contract testing with Pact
```

### Database Tools

```bash
/db:query            # Interactive queries
/db:explain          # Explain query plans
/db:migrate --preview # Preview migrations
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📝 Next Steps

1. **Try New Commands**

   ```bash
   /dev:profile
   /security:scan
   /performance:analyze
   ```

2. **Review Conflicts** (if any)

   ```bash
   diff .claude/commands/dev/deploy.md{,.standard}
   ```

3. **Update Team**
   - Share new commands with team
   - Update team workflows
   - Document any custom integrations

4. **Commit Changes**

   ```bash
   git add .claude/ automation/ .github/ docs/
   git commit -m "chore: Update Claude Code infrastructure to latest"
   git push
   ```

5. **Test Everything**
   - Run new commands
   - Verify automation
   - Check CI/CD pipelines

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 Update Summary

**Total Files Changed:** 31

- Added: 21
- Updated: 10
- Preserved: 8
- Conflicts: 2 (manual review)

**Backup:** `.claude.backup-20250124-143022/`

**Status:** ✅ Update successful

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```

## Best Practices

**Before updating:**
- ✅ Commit current changes
- ✅ Review what will change (--dry-run)
- ✅ Communicate with team
- ✅ Plan rollback if needed

**After updating:**
- ✅ Test new commands
- ✅ Review conflicts
- ✅ Update team documentation
- ✅ Commit changes

**Regular updates:**
- Monthly: Check for updates
- Quarterly: Full infrastructure review
- After major releases: Update immediately

## Troubleshooting

**Update fails midway:**
```bash
# Rollback to backup
/project:rollback --to [timestamp]

# Or manually
rm -rf .claude
mv .claude.backup-[timestamp] .claude
```

**Conflicts unresolved:**

```bash
# View differences
diff original.md original.md.standard

# Merge manually
vim original.md

# Or keep standard and migrate customizations
mv original.md original.md.custom
mv original.md.standard original.md
# Manually port custom parts
```

**New commands not working:**

- Restart Claude Code
- Check command syntax
- Verify allowed-tools
- Review error messages

---

*Keep your Claude Code infrastructure up-to-date with the latest features and improvements*
