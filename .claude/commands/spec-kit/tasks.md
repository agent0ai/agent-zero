---
description: Generate actionable task breakdown from implementation plan with estimates, dependencies, and export options
allowed-tools: [Bash, Read, Write, AskUserQuestion]
argument-hint: "<design-id> [--format <markdown|jira|github|linear>] [--export <path>]"
---

# /spec-kit:tasks - Generate Task Breakdown

Generate comprehensive task breakdown from implementation plan with time estimates, dependencies, priority levels, and export to project management tools.

## Overview

The `tasks` command transforms implementation plans into actionable work items:

- **Task List**: Granular, assignable tasks
- **Time Estimates**: Story points and hour estimates
- **Dependencies**: Task sequencing and prerequisites
- **Priority Levels**: Critical path identification
- **Export Formats**: Markdown, JIRA CSV, GitHub JSON, Linear import
- **Resource Allocation**: Skill-based task assignment

## Prerequisites

**Required:** Implementation plan must exist

- Run `/spec-kit:plan <design-id>` before tasks
- Workflow must be in 'tasks' phase or later

## Execution Steps

### Step 1: Verify Plan Exists

Check workflow status:

```bash
curl -X GET http://localhost:3000/api/specifications/designs/{design_id}/workflow
```

Verify current phase:

- ❌ If phase = 'specify' or earlier → Must complete plan first
- ✅ If phase = 'tasks' → Proceed
- ✅ If phase = 'complete' → Can regenerate tasks

If plan doesn't exist:

```
❌ No implementation plan found for design {design_id}

Current workflow phase: {current_phase}
Required phase: tasks

Generate plan first:
  /spec-kit:plan {design_id}
```

### Step 2: Configure Task Generation

**Ask user for task breakdown preferences:**

**2.1 Granularity Level**
Ask: "What level of task detail?"

- **High-level** (10-20 tasks) - Feature-level tasks
- **Medium** (30-50 tasks) - Component-level tasks (recommended)
- **Detailed** (80-150 tasks) - Function/file-level tasks

**2.2 Estimation Method**
Ask: "How should tasks be estimated?"

- **Story Points** (Fibonacci: 1, 2, 3, 5, 8, 13)
- **Hours** (0.5h to 40h)
- **Both** (Story points + hours)
- **None** (no estimates)

**2.3 Team Size**
Ask: "How many developers on the team?" (1-10)

- Used for parallel task assignment
- Identifies critical path

**2.4 Sprint Planning**
Ask: "Plan tasks into sprints?" (Yes/No)
If Yes:

- Sprint duration (1 week / 2 weeks / custom)
- Team velocity (story points per sprint)

### Step 3: Generate Tasks via API

Call the task generation endpoint:

```bash
curl -X POST http://localhost:3000/api/specifications/designs/{design_id}/tasks \
  -H "Content-Type: application/json"
```

The API will:

1. Load plan artifact from workspace
2. Call spec-kit CLI to generate tasks
3. Parse task breakdown
4. Store in workflow (100% complete)
5. Mark workflow as complete
6. Return tasks with metadata

### Step 4: Display Task Breakdown

Show comprehensive task list:

```
✅ Task Breakdown Generated!

Design ID: {design_id}
Workflow Status: Complete (100%)
Generation Time: {execution_time_ms}ms

📊 TASK SUMMARY

Total Tasks: 62
Estimated Effort: 240 hours (30 story points)
Estimated Duration: 6 weeks (with 2 developers)
Critical Path: 18 tasks (120 hours)

By Priority:
🔴 Critical: 12 tasks (48 hours)
🟠 High: 18 tasks (72 hours)
🟡 Medium: 22 tasks (88 hours)
🟢 Low: 10 tasks (32 hours)

By Category:
🏗️ Infrastructure: 8 tasks (32 hours)
🎨 Frontend: 18 tasks (72 hours)
⚙️ Backend: 24 tasks (96 hours)
🗄️ Database: 6 tasks (24 hours)
🧪 Testing: 6 tasks (16 hours)

📋 TASK LIST

═══════════════════════════════════════════════════════════
PHASE 1: Foundation & Setup (Week 1)
═══════════════════════════════════════════════════════════

TASK-001 🔴 Critical | Backend | 4h | 2 SP
Title: Initialize backend project structure
Description:
- Set up Node.js project with TypeScript
- Configure tsconfig.json for strict mode
- Install core dependencies (Fastify, Prisma)
- Set up folder structure (routes, services, models)
Dependencies: None
Assigned To: Backend Developer
Skills Required: TypeScript, Node.js

TASK-002 🔴 Critical | Database | 3h | 2 SP
Title: Create database schema with Prisma
Description:
- Define Prisma schema for all tables
- Configure PostgreSQL connection
- Create initial migration
- Seed sample data
Dependencies: TASK-001
Assigned To: Backend Developer
Skills Required: PostgreSQL, Prisma

TASK-003 🔴 Critical | Infrastructure | 6h | 3 SP
Title: Set up Docker Compose for local development
Description:
- Create Dockerfile for backend
- Create Dockerfile for frontend
- Configure docker-compose.yml
- Set up PostgreSQL and Redis containers
- Document local setup process
Dependencies: TASK-001, TASK-002
Assigned To: DevOps Engineer
Skills Required: Docker, Docker Compose

TASK-004 🟠 High | Backend | 4h | 2 SP
Title: Implement authentication middleware
Description:
- JWT token generation and validation
- Refresh token logic
- Auth middleware for protected routes
- Error handling for unauthorized access
Dependencies: TASK-001
Assigned To: Backend Developer
Skills Required: JWT, Authentication

[... tasks 005-015 ...]

═══════════════════════════════════════════════════════════
PHASE 2: Core Backend Development (Week 2-3)
═══════════════════════════════════════════════════════════

TASK-016 🔴 Critical | Backend | 8h | 5 SP
Title: Implement product CRUD API endpoints
Description:
- GET /products (list with pagination)
- GET /products/:id (single product)
- POST /products (create - admin only)
- PATCH /products/:id (update - admin only)
- DELETE /products/:id (delete - admin only)
- Add input validation with Zod
- Write unit tests
Dependencies: TASK-002, TASK-004
Assigned To: Backend Developer
Skills Required: Fastify, REST API, Zod

TASK-017 🟠 High | Backend | 6h | 3 SP
Title: Implement shopping cart service
Description:
- Add item to cart
- Update cart item quantity
- Remove item from cart
- Get cart with calculated totals
- Clear cart
- Session-based cart for anonymous users
Dependencies: TASK-016
Assigned To: Backend Developer
Skills Required: Node.js, Session Management

[... tasks 018-035 ...]

═══════════════════════════════════════════════════════════
PHASE 3: Frontend Development (Week 3-4)
═══════════════════════════════════════════════════════════

TASK-036 🔴 Critical | Frontend | 5h | 3 SP
Title: Set up Next.js project with App Router
Description:
- Initialize Next.js 14 project
- Configure TypeScript and ESLint
- Set up Tailwind CSS
- Create layout structure
- Configure routing
Dependencies: TASK-003
Assigned To: Frontend Developer
Skills Required: React, Next.js, Tailwind CSS

TASK-037 🟠 High | Frontend | 6h | 3 SP
Title: Implement product listing page
Description:
- Create product card component
- Implement product grid layout
- Add pagination controls
- Add filter by category
- Add search functionality
- Connect to backend API
Dependencies: TASK-036, TASK-016
Assigned To: Frontend Developer
Skills Required: React, Next.js, API Integration

[... tasks 038-053 ...]

═══════════════════════════════════════════════════════════
PHASE 4: Integration & Testing (Week 5)
═══════════════════════════════════════════════════════════

TASK-054 🟠 High | Integration | 8h | 5 SP
Title: Integrate Stripe payment processing
Description:
- Set up Stripe SDK
- Implement payment intent creation
- Handle webhook for payment confirmation
- Update order status on payment success
- Error handling for payment failures
Dependencies: TASK-030 (order API)
Assigned To: Backend Developer
Skills Required: Stripe API, Webhooks

TASK-055 🟡 Medium | Testing | 6h | 3 SP
Title: Write integration tests for critical flows
Description:
- Test user registration and login
- Test product search and filtering
- Test cart operations
- Test order creation and payment
- Achieve 80% coverage
Dependencies: All backend tasks
Assigned To: QA Engineer
Skills Required: Jest, Supertest

[... tasks 056-060 ...]

═══════════════════════════════════════════════════════════
PHASE 5: Deployment & Launch (Week 6)
═══════════════════════════════════════════════════════════

TASK-061 🔴 Critical | Infrastructure | 12h | 8 SP
Title: Set up production infrastructure on AWS
Description:
- Create ECS cluster and services
- Configure RDS PostgreSQL instance
- Set up ElastiCache Redis
- Configure S3 bucket for static assets
- Set up CloudFront CDN
- Configure security groups and IAM roles
Dependencies: All development tasks
Assigned To: DevOps Engineer
Skills Required: AWS, Terraform, ECS

TASK-062 🔴 Critical | DevOps | 6h | 3 SP
Title: Configure CI/CD pipeline
Description:
- Set up GitHub Actions workflows
- Configure automated testing
- Build and push Docker images to ECR
- Deploy to staging and production
- Set up deployment notifications
Dependencies: TASK-061
Assigned To: DevOps Engineer
Skills Required: GitHub Actions, Docker, CI/CD

═══════════════════════════════════════════════════════════

📊 DEPENDENCY GRAPH

Critical Path (18 tasks, 120 hours):
TASK-001 → TASK-002 → TASK-003 → TASK-016 → TASK-036 →
TASK-037 → TASK-030 → TASK-054 → TASK-061 → TASK-062

Parallel Work Opportunities:
• Frontend (TASK-036-053) can proceed once TASK-003 is done
• Backend APIs (TASK-016-035) can be developed in parallel
• Testing (TASK-055-060) can run concurrently with integration

⏱️ SPRINT PLANNING (2-week sprints, team of 2)

Sprint 1 (Week 1-2): Foundation
• TASK-001 to TASK-015
• Goal: Infrastructure ready, auth working
• Velocity: 25 story points

Sprint 2 (Week 3-4): Core Features
• TASK-016 to TASK-035
• Goal: Backend APIs complete, cart functional
• Velocity: 30 story points

Sprint 3 (Week 5-6): Frontend
• TASK-036 to TASK-053
• Goal: User-facing features complete
• Velocity: 28 story points

Sprint 4 (Week 7-8): Integration & Launch
• TASK-054 to TASK-062
• Goal: Production deployment, go-live
• Velocity: 22 story points

🎯 TEAM ALLOCATION

Backend Developer (100 hours):
• TASK-001, 002, 004, 016-035, 054
• Focus: API development, database, integrations

Frontend Developer (72 hours):
• TASK-036-053
• Focus: UI/UX, components, pages

DevOps Engineer (38 hours):
• TASK-003, 061, 062
• Focus: Infrastructure, deployment, CI/CD

QA Engineer (16 hours):
• TASK-055-060
• Focus: Testing, quality assurance

📁 Next Steps:
• Export tasks: /spec-kit:tasks {design_id} --export ./tasks/
• Export to JIRA: /spec-kit:tasks {design_id} --format jira --export ./jira-import.csv
• Export to GitHub: /spec-kit:tasks {design_id} --format github --export ./github-import.json
• Start implementation: Pick TASK-001 and begin!
```

### Step 5: Export Options

**Ask:** "Would you like to export tasks?"

**Available Export Formats:**

1. **Markdown** - Human-readable task list
2. **JIRA CSV** - Import into JIRA
3. **GitHub JSON** - Create GitHub Issues
4. **Linear** - Import into Linear
5. **Asana** - Import into Asana
6. **Trello** - Import into Trello

### Step 6: Create Exports

**Markdown Export:**

```markdown
# Task Breakdown: E-commerce Platform

## Summary
- Total Tasks: 62
- Estimated Hours: 240h
- Story Points: 30 SP
- Duration: 6 weeks

## Tasks

### TASK-001: Initialize backend project structure
**Priority:** Critical
**Estimate:** 4h / 2 SP
**Dependencies:** None
**Description:** Set up Node.js project...

[... all tasks ...]
```

**JIRA CSV Export:**

```csv
Summary,Description,Priority,Story Points,Labels,Dependencies
"Initialize backend project structure","Set up Node.js project with TypeScript...",Critical,2,"backend,setup",""
"Create database schema","Define Prisma schema...",Critical,2,"database,backend","TASK-001"
...
```

**GitHub JSON Export:**

```json
{
  "issues": [
    {
      "title": "Initialize backend project structure",
      "body": "**Priority:** Critical\n**Estimate:** 4h / 2 SP\n\n Set up Node.js project...",
      "labels": ["backend", "setup", "critical"],
      "milestone": "Sprint 1"
    },
    ...
  ]
}
```

## Advanced Features

### Export to File

```bash
/spec-kit:tasks <design-id> --export <path>
```

Exports tasks in specified format.

### Export to JIRA

```bash
/spec-kit:tasks <design-id> --format jira --export ./tasks.csv
```

Generates JIRA-compatible CSV for bulk import.

### Export to GitHub

```bash
/spec-kit:tasks <design-id> --format github --export ./issues.json
```

Creates GitHub Issues JSON for import via API.

### View Critical Path

```bash
/spec-kit:tasks <design-id> --critical-path
```

Shows only critical path tasks.

### Filter by Priority

```bash
/spec-kit:tasks <design-id> --priority critical
```

Shows only critical or high-priority tasks.

### Regenerate Tasks

```bash
/spec-kit:tasks <design-id> --regenerate
```

Generates new task breakdown with updated preferences.

## Error Handling

**If plan not found:**

```
❌ Cannot generate tasks: No plan found

Workflow Phase: {current_phase}
Expected Phase: tasks

Generate plan first:
  /spec-kit:plan {design_id}
```

**If task generation fails:**

```
❌ Task generation failed: {error_message}

Try:
1. Check plan exists: /spec-kit:plan {design_id} --status
2. Regenerate plan: /spec-kit:plan {design_id} --regenerate
3. Check spec-kit health: curl http://localhost:3000/api/spec-kit/health
```

## Example Usage

### Example 1: Generate and Export to JIRA

```
User: /spec-kit:tasks design-abc-123 --format jira --export ./jira-import.csv
Assistant: Generating task breakdown...
  Total tasks: 62
  Estimated: 240 hours
  Sprint planning: 4 sprints
Assistant: ✅ Tasks generated!
  Exported to: ./jira-import.csv
  Ready to import into JIRA
```

### Example 2: View Critical Path

```
User: /spec-kit:tasks design-def-456 --critical-path
Assistant: Critical Path (18 tasks, 120 hours):
  1. TASK-001: Initialize backend (4h)
  2. TASK-002: Database schema (3h)
  3. TASK-003: Docker setup (6h)
  ...
  18. TASK-062: CI/CD pipeline (6h)
```

### Example 3: Detailed Breakdown

```
User: /spec-kit:tasks design-ghi-789
Assistant: What level of detail? (high-level/medium/detailed)
User: detailed
Assistant: Generating 142 detailed tasks...
Assistant: ✅ Task breakdown complete!
  Tasks: 142
  Average task size: 1.7 hours
  Ready for assignment
```

## Success Criteria

✅ Task breakdown generated with all tasks
✅ Time estimates provided
✅ Dependencies identified
✅ Critical path calculated
✅ Export format generated
✅ Workflow marked as complete (100%)
✅ Team ready to start implementation

## Notes

- Tasks can be exported to multiple formats
- Critical path helps identify bottlenecks
- Sprint planning aids in resource allocation
- Dependency graph ensures correct sequencing
- Tasks are versioned in the database
- Use tasks as source of truth during development
