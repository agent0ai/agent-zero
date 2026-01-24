---
description: Scaffold new project with templates, dependencies, and initial setup
argument-hint: <project-name> [--template <nodejs|python|react|nextjs>]
allowed-tools: Task, Bash, Write, AskUserQuestion
model: claude-sonnet-4-5
timeout: 900
retry: 2
cost_estimate: 0.15-0.25

validation:
  input:
    project_name:
      required: true
      pattern: "^[a-z0-9-]+$"
      min_length: 3
      error_message: "Project name must be lowercase with hyphens (e.g., my-new-project)"
  output:
    schema: .claude/validation/schemas/dev/scaffold-output.json
    required_files:
      - '${project_name}/package.json'
      - '${project_name}/README.md'
    min_file_size: 200
    quality_threshold: 0.85
    content_requirements:
      - "Project directory created"
      - "Template applied"
      - "Dependencies installed"
      - "Git initialized"
      - "README generated"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for project name"
      - "Added output validation for scaffolded projects"
      - "Streamlined from 743 lines to focused workflow"
      - "Multi-template support (Node.js/Python/React/Next.js)"
  - version: 1.0.0
    date: 2025-08-25
    changes:
      - "Initial implementation with Node.js template"
---

# Scaffold New Project

Project: **$ARGUMENTS**

## Step 1: Validate Input & Parse Arguments

```bash
ARGS="$ARGUMENTS"
PROJECT_NAME=$(echo "$ARGS" | awk '{print $1}')
TEMPLATE=$(echo "$ARGS" | grep -oP '\-\-template\s+\K\w+' || echo "nodejs")

# Check project name provided
if [ -z "$PROJECT_NAME" ]; then
  echo "❌ ERROR: Missing project name"
  echo ""
  echo "Usage: /dev/scaffold <project-name> [--template <type>]"
  echo "Example: /dev/scaffold my-new-project --template react"
  exit 1
fi

# Validate project name format
if ! echo "$PROJECT_NAME" | grep -qE '^[a-z0-9-]+$'; then
  echo "❌ ERROR: Invalid project name format"
  echo "Must be lowercase with hyphens: my-new-project"
  echo "Provided: $PROJECT_NAME"
  exit 1
fi

# Check minimum length
if [ ${#PROJECT_NAME} -lt 3 ]; then
  echo "❌ ERROR: Project name too short (minimum 3 characters)"
  exit 1
fi

# Check if directory already exists
if [ -d "$PROJECT_NAME" ]; then
  echo "❌ ERROR: Directory already exists: $PROJECT_NAME"
  exit 1
fi

echo "✓ Input validated"
echo "  Project: $PROJECT_NAME"
echo "  Template: $TEMPLATE"
```

## Step 2: Scaffold Project Using Agent

```javascript
const PROJECT_NAME = process.env.PROJECT_NAME;
const TEMPLATE = process.env.TEMPLATE || 'nodejs';

await Task({
  subagent_type: 'general-purpose',
  description: 'Scaffold new project from template',
  prompt: `Scaffold a new ${TEMPLATE} project named "${PROJECT_NAME}".

SCAFFOLDING WORKFLOW:

**1. Create Project Directory**:
- Create directory: ${PROJECT_NAME}/
- Create standard subdirectories based on template

**2. Apply Template**:

${TEMPLATE === 'nodejs' ? `
**Node.js Template**:
- package.json (with name, version, scripts)
- tsconfig.json (TypeScript configuration)
- src/index.ts (entry point)
- src/__tests__/index.test.ts (sample test)
- .gitignore (node_modules, dist, etc.)
- .eslintrc.js (linting config)
- .prettierrc (code formatting)
- jest.config.js (testing config)
` : ''}

${TEMPLATE === 'python' ? `
**Python Template**:
- pyproject.toml or setup.py
- requirements.txt (dependencies)
- src/main.py (entry point)
- tests/test_main.py (sample test)
- .gitignore (venv, __pycache__, etc.)
- pytest.ini (testing config)
- .flake8 (linting config)
` : ''}

${TEMPLATE === 'react' ? `
**React Template**:
- package.json (React + TypeScript)
- tsconfig.json
- src/App.tsx (main component)
- src/index.tsx (entry point)
- src/App.test.tsx (sample test)
- public/index.html
- .gitignore
- vite.config.ts or webpack.config.js
` : ''}

${TEMPLATE === 'nextjs' ? `
**Next.js Template**:
- package.json (Next.js + TypeScript)
- tsconfig.json
- next.config.js
- pages/index.tsx (home page)
- pages/api/hello.ts (API route)
- public/ (static assets)
- styles/ (CSS modules)
- .gitignore
` : ''}

**3. Generate README.md**:
Include:
- Project name and description
- Installation instructions
- Development setup
- Available scripts
- Project structure
- License information

**4. Initialize Git**:
- git init
- Create initial commit: "chore: initialize project"
- Add .gitignore

**5. Install Dependencies**:
- npm install (for Node.js/React/Next.js)
- pip install -r requirements.txt (for Python)
- Verify installation successful

**6. Run Initial Tests**:
- npm test (verify test framework working)
- Or pytest (for Python)
- Ensure initial tests pass

**7. Generate Project Report**:
Save to: ${PROJECT_NAME}/PROJECT_SETUP.md
Include:
- Files created
- Dependencies installed
- Git initialized
- Next steps for development

Provide:
- Number of files created
- Dependencies count
- Project is ready for development`,

  context: {
    project_name: PROJECT_NAME,
    template: TEMPLATE,
    setup_report: `${PROJECT_NAME}/PROJECT_SETUP.md`
  }
});
```

## Step 3: Validate Output

```bash
PROJECT_NAME="$PROJECT_NAME"

# Check project directory created
if [ ! -d "$PROJECT_NAME" ]; then
  echo "❌ ERROR: Project directory not created"
  exit 1
fi

# Check key files exist
if [ ! -f "$PROJECT_NAME/package.json" ] && [ ! -f "$PROJECT_NAME/pyproject.toml" ]; then
  echo "❌ ERROR: No package.json or pyproject.toml found"
  exit 1
fi

if [ ! -f "$PROJECT_NAME/README.md" ]; then
  echo "❌ ERROR: README.md not created"
  exit 1
fi

# Check git initialized
if [ ! -d "$PROJECT_NAME/.git" ]; then
  echo "⚠️  WARNING: Git not initialized"
fi

# Count files created
FILE_COUNT=$(find "$PROJECT_NAME" -type f | wc -l)
echo "✓ Output validation complete"
echo "  Files created: $FILE_COUNT"
```

## Completion

```
═══════════════════════════════════════════════════
       PROJECT SCAFFOLDING COMPLETE ✓
═══════════════════════════════════════════════════

Project: $PROJECT_NAME
Template: $TEMPLATE
Command: /dev/scaffold
Version: 2.0.0

Project Created:
  ✓ Directory structure
  ✓ Configuration files
  ✓ Source files
  ✓ Test files
  ✓ README.md
  ✓ Git initialized
  ✓ Dependencies installed

Files Created: [count]

Validations Passed:
  ✓ Input validation (project name valid)
  ✓ Output validation (project created)
  ✓ Template applied successfully
  ✓ Quality threshold (≥0.85)

NEXT STEPS:

1. Navigate to project:
   cd $PROJECT_NAME

2. Start development server:
   npm run dev  (or python src/main.py)

3. Run tests:
   npm test  (or pytest)

4. Start coding!
   Open in your editor and begin development

═══════════════════════════════════════════════════
```

## Guidelines

- **Choose Right Template**: Select template matching your project type
- **Customize After Scaffold**: Modify generated files to match needs
- **Add Dependencies**: Install additional packages as needed
- **Configure Linting**: Adjust ESLint/Flake8 rules for your team
- **Setup CI/CD**: Add pipeline configuration after scaffolding
- **Document Decisions**: Update README with project-specific info
