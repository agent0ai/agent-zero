---
description: Initialize existing project with complete Claude Code infrastructure
argument-hint: "[--type <nodejs|python|go|ruby|web>] [--skip-git] [--skip-ci]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Write
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# Project Initialization Command

## Overview

Initializes an existing project folder with complete Claude Code infrastructure including skills, commands, automation, testing, and CI/CD configuration.

**This command is idempotent** - safe to run multiple times, will not overwrite existing customizations.

## Usage

```bash
# Interactive mode (recommended for first time)
/project:init

# Quick init for Node.js project
/project:init --type nodejs

# Initialize without Git setup
/project:init --skip-git

# Initialize without CI/CD
/project:init --skip-ci

# Full customization
/project:init --type web --skip-ci
```

## What This Command Does

1. **Analyzes current project**
   - Detects project type (Node.js, Python, Go, Ruby, etc.)
   - Identifies existing tools (package managers, test frameworks)
   - Checks for existing Claude Code setup
   - Scans for configuration files

2. **Creates `.claude/` infrastructure**
   - Commands directory with project-specific commands
   - Skills directory for team-shared skills
   - Configuration files (CLAUDE.md, .gitignore)
   - Templates for custom commands/skills

3. **Sets up automation**
   - Analytics collection scripts
   - CI/CD integration scripts
   - Git hooks for commit quality
   - Automated testing runners

4. **Configures project-specific tooling**
   - Test runners for project type
   - Linters and formatters
   - Build scripts
   - Deployment automation

5. **Initializes documentation**
   - README.md enhancements
   - CONTRIBUTING.md
   - Command documentation
   - Skill documentation

6. **Sets up Git infrastructure** (unless --skip-git)
   - .gitignore for Claude Code
   - Git hooks
   - Branch protection recommendations
   - Commit message templates

7. **Configures CI/CD** (unless --skip-ci)
   - GitHub Actions workflows
   - GitLab CI configuration
   - Testing automation
   - Deployment pipelines

## Project Types

### Node.js/TypeScript (`--type nodejs`)

**Detected if:**

- `package.json` exists
- `node_modules/` present
- `.js`, `.ts`, `.jsx`, `.tsx` files

**Sets up:**

- `/dev:test` - Run Jest/Vitest tests
- `/dev:build` - Build production bundle
- `/dev:lint` - ESLint + Prettier
- `/dev:deploy` - Deploy to Vercel/Netlify
- `/db:migrate` - Prisma/TypeORM migrations
- `/api:test` - API endpoint testing

**Skills added:**

- `code-reviewer` (JavaScript/TypeScript specific)
- `dependency-updater` (npm/yarn/pnpm)

---

### Python (`--type python`)

**Detected if:**

- `requirements.txt`, `pyproject.toml`, or `Pipfile` exists
- `.py` files present
- Virtual environment detected

**Sets up:**

- `/dev:test` - Run pytest
- `/dev:lint` - Black + Flake8 + mypy
- `/dev:format` - Black formatter
- `/api:test` - FastAPI/Flask testing
- `/db:migrate` - Alembic/Django migrations

**Skills added:**

- `code-reviewer` (Python specific)
- `dependency-updater` (pip/poetry/pipenv)

---

### Go (`--type go`)

**Detected if:**

- `go.mod` exists
- `.go` files present

**Sets up:**

- `/dev:test` - go test
- `/dev:build` - go build
- `/dev:lint` - golangci-lint
- `/dev:bench` - go test -bench
- `/api:test` - HTTP handler testing

**Skills added:**

- `code-reviewer` (Go specific)

---

### Ruby (`--type ruby`)

**Detected if:**

- `Gemfile` exists
- `.rb` files present
- Rails detected

**Sets up:**

- `/dev:test` - RSpec/Minitest
- `/dev:lint` - RuboCop
- `/dev:console` - Rails console
- `/db:migrate` - Rails migrations
- `/api:test` - Rails controller tests

---

### Web/Static (`--type web`)

**Detected if:**

- `index.html` exists
- No backend framework detected

**Sets up:**

- `/dev:build` - Build static site
- `/dev:deploy` - Deploy to Vercel/Netlify
- `/lighthouse` - Performance audit
- `/seo:check` - SEO analysis

## Directory Structure Created

```
project-root/
├── .claude/
│   ├── CLAUDE.md                      # Project configuration
│   ├── commands/                      # Custom slash commands
│   │   ├── dev/                       # Development commands
│   │   │   ├── test.md
│   │   │   ├── build.md
│   │   │   ├── lint.md
│   │   │   └── deploy.md
│   │   ├── db/                        # Database commands
│   │   │   ├── migrate.md
│   │   │   ├── seed.md
│   │   │   └── backup.md
│   │   ├── api/                       # API commands
│   │   │   └── test.md
│   │   └── project/                   # Project management
│   │       ├── init.md (this file)
│   │       ├── update.md
│   │       └── audit.md
│   ├── skills/                        # Project-specific skills
│   │   ├── README.md
│   │   └── .gitkeep
│   ├── templates/                     # Command/skill templates
│   │   ├── command-template.md
│   │   └── skill-template.md
│   └── .gitignore                     # Claude-specific ignores
├── automation/
│   ├── scripts/
│   │   ├── analytics/
│   │   │   ├── collect-daily-data.sh
│   │   │   └── weekly-analysis.sh
│   │   ├── ci-cd/
│   │   │   ├── test-runner.sh
│   │   │   └── deploy.sh
│   │   └── git-hooks/
│   │       ├── pre-commit
│   │       └── commit-msg
│   └── README.md
├── tests/
│   ├── skills/                        # Skill tests
│   │   └── TESTING-FRAMEWORK.md
│   └── integration/                   # Integration tests
├── docs/
│   ├── COMMANDS.md                    # Command documentation
│   ├── SKILLS.md                      # Skill documentation
│   └── WORKFLOWS.md                   # Common workflows
├── .github/                           # GitHub-specific
│   └── workflows/
│       ├── test.yml
│       ├── lint.yml
│       └── deploy.yml
└── .gitignore                         # Updated with Claude paths
```

## Implementation Steps

### Step 1: Project Analysis

```bash
# Detect project type
if [ -f "package.json" ]; then
    PROJECT_TYPE="nodejs"
elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    PROJECT_TYPE="python"
elif [ -f "go.mod" ]; then
    PROJECT_TYPE="go"
elif [ -f "Gemfile" ]; then
    PROJECT_TYPE="ruby"
elif [ -f "index.html" ]; then
    PROJECT_TYPE="web"
else
    PROJECT_TYPE="generic"
fi

# Check for existing Claude setup
if [ -d ".claude" ]; then
    echo "⚠️  Existing Claude Code setup detected"
    echo "This command will enhance (not overwrite) your current setup"
fi
```

### Step 2: Create Directory Structure

```bash
# Create .claude directories
mkdir -p .claude/{commands,skills,templates}
mkdir -p .claude/commands/{dev,db,api,project}

# Create automation directories
mkdir -p automation/scripts/{analytics,ci-cd,git-hooks}

# Create test directories
mkdir -p tests/{skills,integration,e2e}

# Create docs directory
mkdir -p docs
```

### Step 3: Generate CLAUDE.md

```markdown
# [Project Name] - Claude Code Configuration

## Project Overview

**Type:** [Detected type]
**Stack:** [Detected technologies]
**Initialized:** [Date]

## Project-Specific Commands

### Development
- `/dev:test` - Run test suite
- `/dev:build` - Build production bundle
- `/dev:lint` - Run linters
- `/dev:deploy` - Deploy to production

### Database
- `/db:migrate` - Run migrations
- `/db:seed` - Seed database
- `/db:backup` - Backup database

### API
- `/api:test` - Test API endpoints
- `/api:docs` - Generate API documentation

### Project Management
- `/project:init` - Initialize project (this command)
- `/project:update` - Update Claude Code setup
- `/project:audit` - Audit project configuration

## Skills Available

### Project Skills (.claude/skills/)
- [List of project-specific skills]

### Personal Skills (~/.claude/skills/)
- stripe-revenue-analyzer
- content-optimizer
- brand-voice
- vercel-landing-page-builder

## Automation

### Analytics
- Daily data collection: 6 PM
- Weekly analysis: Monday 6 AM

### CI/CD
- Automated testing on PR
- Automated deployment on merge to main

## Development Workflow

1. Create feature branch: `/dev:create-branch feature-name`
2. Implement feature
3. Run tests: `/dev:test`
4. Run linter: `/dev:lint`
5. Self-review: `/dev:review`
6. Create PR: `/dev:create-pr`
7. Merge after approval

## Quality Standards

- Code coverage: >80%
- All tests passing
- Linter errors: 0
- Type errors: 0 (if TypeScript)

## Resources

- Commands: `docs/COMMANDS.md`
- Skills: `docs/SKILLS.md`
- Workflows: `docs/WORKFLOWS.md`
```

### Step 4: Create Project-Specific Commands

**Node.js Example - `/dev:test.md`:**

```markdown
---
description: Run test suite with coverage
argument-hint: "[--watch] [--coverage] [--file <pattern>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
---

# Run Tests

Run the project test suite using Jest/Vitest.

## Usage

```bash
# Run all tests
/dev:test

# Watch mode
/dev:test --watch

# With coverage
/dev:test --coverage

# Specific file/pattern
/dev:test --file user.test.ts
```

## Implementation

```bash
# Detect test runner
if [ -f "vitest.config.ts" ] || grep -q "vitest" package.json; then
    TEST_RUNNER="vitest"
elif [ -f "jest.config.js" ] || grep -q "jest" package.json; then
    TEST_RUNNER="jest"
else
    echo "No test runner detected"
    exit 1
fi

# Build command
if [ "$WATCH" = true ]; then
    npm run test:watch
elif [ "$COVERAGE" = true ]; then
    npm run test:coverage
elif [ -n "$FILE" ]; then
    $TEST_RUNNER $FILE
else
    npm test
fi
```

```

### Step 5: Setup Git Configuration

**`.gitignore` additions:**

```gitignore
# Claude Code
.claude/.cache
.claude/temp
analytics-data/
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
```

**Git hooks** (`automation/scripts/git-hooks/pre-commit`):

```bash
#!/bin/bash
# Pre-commit hook: Run linter and tests

echo "Running pre-commit checks..."

# Run linter
if [ -f "package.json" ]; then
    npm run lint || exit 1
fi

# Run tests
if [ -f "package.json" ]; then
    npm test || exit 1
fi

echo "✅ Pre-commit checks passed"
```

### Step 6: Setup CI/CD

**GitHub Actions** (`.github/workflows/test.yml`):

```yaml
name: Test

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run tests
        run: npm test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Step 7: Generate Documentation

**`docs/COMMANDS.md`:**

```markdown
# Project Commands

Complete list of available Claude Code commands for this project.

## Development

- `/dev:test` - Run test suite
- `/dev:build` - Build production bundle
- `/dev:lint` - Run linters and formatters
- `/dev:deploy` - Deploy to production

[Full command documentation...]
```

## Output Format

```markdown
# Project Initialized: [Project Name]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔍 Project Analysis

**Type:** Node.js/TypeScript
**Package Manager:** npm
**Test Framework:** Jest
**Build Tool:** Webpack
**Detected Tools:** ESLint, Prettier, TypeScript

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📁 Directory Structure Created

✅ .claude/commands/dev/        (5 commands)
✅ .claude/commands/db/         (3 commands)
✅ .claude/commands/api/        (2 commands)
✅ .claude/commands/project/    (3 commands)
✅ .claude/skills/              (ready for team skills)
✅ automation/scripts/          (analytics, ci-cd, git-hooks)
✅ tests/skills/                (testing framework)
✅ docs/                        (command and workflow docs)
✅ .github/workflows/           (CI/CD pipelines)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚙️  Commands Created

### Development (5 commands)
- `/dev:test` - Run Jest test suite
- `/dev:build` - Build production bundle with Webpack
- `/dev:lint` - Run ESLint + Prettier
- `/dev:type-check` - TypeScript type checking
- `/dev:deploy` - Deploy to Vercel

### Database (3 commands)
- `/db:migrate` - Run Prisma migrations
- `/db:seed` - Seed database with test data
- `/db:backup` - Backup production database

### API (2 commands)
- `/api:test` - Test API endpoints
- `/api:docs` - Generate OpenAPI documentation

### Project Management (3 commands)
- `/project:init` - Initialize project (this command)
- `/project:update` - Update Claude Code setup
- `/project:audit` - Audit project configuration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔧 Automation Configured

**Analytics:**
- ✅ Daily data collection (6 PM)
- ✅ Weekly analysis (Monday 6 AM)

**CI/CD:**
- ✅ GitHub Actions: test.yml
- ✅ GitHub Actions: lint.yml
- ✅ GitHub Actions: deploy.yml

**Git Hooks:**
- ✅ pre-commit: Run linter + tests
- ✅ commit-msg: Validate commit format

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📚 Documentation Created

- ✅ .claude/CLAUDE.md - Project configuration
- ✅ docs/COMMANDS.md - Command reference
- ✅ docs/SKILLS.md - Skill documentation
- ✅ docs/WORKFLOWS.md - Common workflows
- ✅ CONTRIBUTING.md - Contribution guidelines

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ✅ Git Configuration

- ✅ .gitignore updated
- ✅ Git hooks installed
- ✅ Commit template configured
- ✅ Branch protection recommendations provided

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📝 Next Steps

1. **Review Configuration**
   - Check `.claude/CLAUDE.md` for project settings
   - Review generated commands in `.claude/commands/`
   - Customize as needed for your workflow

2. **Try Commands**
   ```bash
   /dev:test              # Run test suite
   /dev:lint              # Run linters
   /dev:build             # Build production
   ```

3. **Add Project Skills**
   - Create skills in `.claude/skills/`
   - Example: code-reviewer, deployment-helper
   - Skills are shared with entire team via Git

4. **Configure Analytics**

   ```bash
   ./automation/scripts/setup-analytics-automation.sh
   ```

5. **Customize Workflows**
   - Edit commands in `.claude/commands/`
   - Add new commands using templates
   - Update `.claude/CLAUDE.md` with team conventions

6. **Commit Setup**

   ```bash
   git add .claude/ automation/ tests/ docs/ .github/
   git commit -m "feat: Initialize Claude Code project infrastructure"
   git push
   ```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 Project Status

**Initialization:** ✅ Complete
**Commands Available:** 13
**Automation:** ✅ Configured
**CI/CD:** ✅ Ready
**Documentation:** ✅ Generated

**Your team can now:**

- Use consistent slash commands for development
- Share skills via Git
- Automate testing and deployment
- Track productivity metrics
- Collaborate with standardized workflows

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```

## Customization

After initialization, customize for your team:

### Add Custom Commands

```bash
# Use template
cp .claude/templates/command-template.md .claude/commands/dev/my-command.md

# Edit command
# Test command: /dev:my-command
```

### Add Project Skills

```bash
# Create skill
mkdir -p .claude/skills/my-skill
vim .claude/skills/my-skill/SKILL.md

# Skill activates automatically when relevant
```

### Update Workflows

Edit `.claude/CLAUDE.md` to document your team's:

- Branching strategy
- Code review process
- Deployment workflow
- Quality standards

## Integration with Existing Setup

**If `.claude/` already exists:**

- Command merges with existing structure
- Won't overwrite customized files
- Adds missing components only
- Reports conflicts for manual resolution

**Safe operations:**

- ✅ Add new commands to existing directories
- ✅ Create missing directories
- ✅ Enhance existing CLAUDE.md
- ✅ Add new automation scripts

**Manual review needed:**

- ⚠️ Existing command with same name
- ⚠️ Conflicting CLAUDE.md settings
- ⚠️ Different Git hook implementations

## Troubleshooting

**Command doesn't detect project type:**

```bash
# Specify manually
/project:init --type nodejs
```

**Existing files conflict:**

- Command will report conflicts
- Review manually: `git diff`
- Keep your customizations
- Merge useful additions

**CI/CD not working:**

- Check GitHub Actions permissions
- Verify workflow files in `.github/workflows/`
- Check runner OS compatibility

---

*This command standardizes Claude Code setup across your entire team*
