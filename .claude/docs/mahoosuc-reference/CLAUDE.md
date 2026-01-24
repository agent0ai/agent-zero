# Prompt Blueprint - Claude Code Configuration

## Project Overview

This project is a comprehensive AI agent orchestration system that combines:

- **Prompt Engineering Knowledge Base**: Best practices from OpenAI, Anthropic, Google
- **Meta-Agents**: AI agents that create other AI agents
- **Zoho ONE Integration**: CRM, Mail, and SMS automation
- **Multi-Interface System**: CLI slash commands, web UI, and Zoho widgets

## Core Philosophy

### Data Model Enhancement

- **ENHANCE the data model by ADDING columns/fields** - We can remove them later after systems are functioning
- **ENHANCE OVER REMOVING** - Always prefer to add functionality rather than remove existing code
- **Iterate with expansion** - Build comprehensive systems first, optimize second

### Zoho ONE Integration Priority

- **CRM**: All lead, contact, and deal management flows through Zoho CRM
- **MAIL**: Email campaigns and communications via Zoho Mail
- **SMS**: SMS campaigns and notifications via Zoho SMS
- All Zoho operations require **human approval** before execution

## Slash Command Usage

### Compound Engineering Workflow Commands (NEW)

Based on the principle that each unit of work should make subsequent work easier through systematic knowledge capture.

**ArchitectFlow** (Planning with git worktrees):

- `/architect:plan --title "Feature Name"` - Create planning session with isolated git worktree
- `/architect:review [workflow-id] --wait` - Trigger multi-agent review (Security, Performance, Architecture, Testing)

**DevFlow** (In-sprint reviews with git branches):

- `/devflow:review --title "Feature Name"` - Create in-sprint review session with git branch
- `/devflow:compound --category pattern --title "..." --impactScore 8` - Capture compound learnings

**Learning Categories:**

- `pattern` - Reusable design or code pattern discovered
- `anti-pattern` - Pattern to avoid (learned the hard way)
- `best-practice` - Recommended approach that worked well
- `gotcha` - Common pitfall or mistake to watch out for
- `tip` - Helpful hint or optimization trick

**Knowledge Integration:**

- Learnings automatically integrate into CLAUDE.md and DEVB knowledge base
- 30-day TTL with archive option for cleanup
- Tag-based semantic search for retrieval
- Impact scoring (1-10) for prioritization

**Multi-Agent Reviews:**

- 4 specialized AI agents run in parallel via worker queue
- Security: Vulnerabilities, auth issues, crypto weaknesses
- Performance: N+1 queries, algorithm complexity, caching opportunities
- Architecture: SOLID principles, design patterns, coupling issues
- Testing: Coverage gaps, edge cases, flaky tests

### DEVB (Design-Emulate-Validate-Build) System Commands

- `/design:solution` - Create comprehensive solution design specification
- `/design:emulate [design-id]` - Test design without building (3 methods: dry-run, static-analysis, simulation)
- `/design:validate [design-id]` - AI validation from 4 perspectives (Security, Performance, Cost, UX)
- `/design:spec [design-id]` - Generate complete specifications (diagrams, OpenAPI, test plan, checklist)

### Design OS Commands (Product Planning & UI Design)

The Design OS workflow provides a structured approach to product design before implementation:

**Phase 1: Product Planning**

- `/design-os/product-vision` - Define product vision, problems, solutions, and key features
- `/design-os/product-roadmap` - Create 3-5 buildable sections ordered by priority
- `/design-os/data-model` - Define core data entities and relationships

**Phase 2: Design System**

- `/design-os/design-tokens` - Set colors (Tailwind) and typography (Google Fonts)
- `/design-os/design-shell` - Create app navigation shell and layout

**Phase 3: Section Design** (repeat per section)

- `/design-os/shape-section <section>` - Define section specs, flows, UI patterns
- `/design-os/sample-data <section>` - Generate realistic sample data + TypeScript types
- `/design-os/design-screen <section>` - Create production-grade React components
- `/design-os/screenshot-design <section>` - Capture screenshots for documentation

**Phase 4: Export**

- `/design-os/export-product` - Generate complete implementation handoff package

### Prompt Engineering Commands

- `/prompt/generate [description]` - Generate new AI prompts using PromptCraft∞ Elite agent
- `/prompt/review [file]` - Review prompts against unified best practices
- `/prompt/optimize [file]` - Optimize existing prompts for better performance
- `/prompt/test [file]` - Test prompt variants and compare results

### Zoho Operations Commands

- `/zoho/create-lead [details]` - Create CRM lead with approval workflow
- `/zoho/send-email [recipient] [template]` - Send email via Zoho Mail
- `/zoho/send-sms [recipient] [message]` - Send SMS via Zoho SMS
- `/zoho/sync-data [source] [target]` - Sync data between systems
- `/zoho/query-crm [query]` - Query CRM using natural language

### Agent Coordination Commands

- `/agent/route [task]` - Automatically route task to best agent
- `/agent/status` - Check all agent statuses and performance
- `/agent/assign [task] [agent]` - Manually assign task to specific agent
- `/agent/monitor` - Real-time agent activity monitor

### Workflow Commands

- `/workflow/approve [pending-id]` - Approve pending operations
- `/workflow/collect-data [form-type]` - Start structured data collection

### Agent OS Commands (Spec-Driven Development)

The Agent OS workflow provides spec-driven feature development with specialized agents:

**Phase 1: Planning**

- `/agent-os/plan-product` - Create product mission, roadmap, and tech stack

**Phase 2: Specification** (per feature)

- `/agent-os/init-spec <feature>` - Initialize spec folder and capture initial idea
- `/agent-os/shape-spec <feature>` - Gather requirements through targeted questions
- `/agent-os/write-spec <feature>` - Create detailed specification document
- `/agent-os/verify-spec <feature>` - Validate spec completeness and alignment

**Phase 3: Contract & Integration** (NEW - Full-Stack Unification)

- `/agent-os/design-contract <feature>` - Create unified API contracts (types, errors, endpoints)
- `/agent-os/design-integration <feature>` - Design data fetching, caching, error handling patterns

**Phase 4: Implementation**

- `/agent-os/create-tasks <feature>` - Create organized task list with dependencies
- `/agent-os/implement-tasks <feature>` - Execute tasks with test-driven development
- `/agent-os/verify-implementation <feature>` - Verify completion and update roadmap

**Phase 5: Full-Stack Verification** (NEW)

- `/agent-os/verify-integration <feature>` - End-to-end frontend/backend verification

**Specialized Agents** (in `.claude/agents/agent-os/`):

*Planning & Specification:*

- `product-planner` - Product documentation creation
- `spec-initializer` - Spec folder setup
- `spec-shaper` - Requirements gathering
- `spec-writer` - Specification writing
- `spec-verifier` - Spec validation

*Full-Stack Integration (NEW):*

- `contract-designer` - Unified API contracts shared by frontend & backend
- `integration-architect` - Data fetching, state management, error handling patterns
- `full-stack-verifier` - End-to-end integration verification

*Implementation:*

- `tasks-list-creator` - Task breakdown
- `implementer` - Full-stack implementation
- `implementation-verifier` - Final verification

**Standards** (in `.claude/standards/`):

- `global/` - Coding style, conventions, error handling, validation, tech stack, **API contracts**
- `frontend/` - Component patterns, accessibility, performance
- `backend/` - API design, database, security, architecture
- `testing/` - Unit, integration, E2E testing patterns

## Agent Routing Guidelines

### When to Use Which Agent

**For Prompt Engineering:**

- Use `prompt-engineering-agent` from `/meta-prompts/` for creating new prompts
- Use `documentation-expert-agent` for creating/updating documentation
- Reference `/guides/unified-best-practices__claude_sonnet_4.md` for best practices

**For Zoho Integration:**

- Route CRM operations through Zoho CRM integration patterns
- Route email operations through Zoho Mail integration patterns
- Route SMS operations through Zoho SMS integration patterns
- **Always** include approval workflow for data modifications

**For Multi-Agent Coordination:**

- Use agent-router patterns to determine best agent for task
- Use workflow orchestration for complex multi-step processes
- Maintain context sharing between agents

## Approval Workflows

All operations that modify data require human approval:

1. **CRM Operations** (create lead, update contact, create deal)
   - Preview data to be created/modified
   - Show which fields will be populated
   - Request explicit confirmation
   - Log approval decision

2. **Communication Operations** (send email, send SMS)
   - Show full message content
   - Display recipient list
   - Preview merge fields/personalization
   - Confirm send authorization

3. **Data Sync Operations** (sync between systems)
   - Show data mapping
   - Display records to be affected
   - Highlight any conflicts
   - Require confirmation to proceed

## Compound Engineering System

### Philosophy: 80/20 Planning vs. Execution

Based on the principle that **each unit of work should make subsequent work easier** through systematic knowledge capture. Invest 80% of effort in planning and review, 20% in execution.

### Two Workflow Types

#### 1. ArchitectFlow (Upfront Planning)

**Use for:** Major features, architectural changes, greenfield projects
**Git Strategy:** Isolated worktrees in `/tmp/architect-{sessionId}`
**Purpose:** Deep architectural planning before implementation

**Workflow:**

```bash
# Step 1: Create planning session
/architect:plan --title "Microservices Architecture"

# Claude creates:
# - Workflow session in database
# - Git worktree at /tmp/architect-{sessionId}
# - Branch: plan/{sessionId}

# Step 2: Work in isolated environment
cd /tmp/architect-{sessionId}
# Do planning work, create diagrams, write specs

# Step 3: Trigger multi-agent review (optional)
/architect:review {workflow-id} --wait --captureLearnings

# Step 4: Capture learnings
/devflow:compound {workflow-id} --category pattern --title "..."
```

**Benefits:**

- Parallel planning sessions possible
- No interference with main workspace
- Clean separation of concerns
- Automatic cleanup via 30-day TTL

#### 2. DevFlow (In-Sprint Reviews)

**Use for:** Mid-sprint quality checks, pre-merge reviews, feature completion
**Git Strategy:** Lightweight branches `review/{feature-name}`
**Purpose:** Quick reviews during active development

**Workflow:**

```bash
# Step 1: Create review session
/devflow:review --title "Authentication System" --reviewType security

# Claude creates:
# - Workflow session in database
# - Git branch: review/authentication-system-{short-id}
# - Queues review agents

# Step 2: Wait for review (optional)
/devflow:review --title "..." --wait --autoCompound

# Step 3: Manually capture important learnings
/devflow:compound --category gotcha --title "N+1 Queries" --impactScore 10
```

### Multi-Agent Parallel Reviews

When you trigger a review with `--reviewType all`, the system queues **4 specialized AI agents** to run in parallel:

#### 1. Security Agent

**Checks:**

- SQL injection, XSS, CSRF vulnerabilities
- Authentication and authorization issues
- Sensitive data exposure
- Cryptographic weaknesses
- Dependency vulnerabilities (CVEs)

**Output Format:**

```json
{
  "severity": "critical|high|medium|low|info",
  "category": "sql-injection|xss|auth|crypto|...",
  "title": "Potential SQL Injection Vulnerability",
  "file": "src/database/queries.ts",
  "line": 42,
  "recommendation": "Use parameterized queries",
  "fixExample": "const result = await db.query('SELECT * FROM users WHERE id = $1', [userId]);"
}
```

#### 2. Performance Agent

**Checks:**

- N+1 query problems
- Inefficient algorithms (O(n²) loops)
- Memory leaks
- Missing caching opportunities
- Inefficient database queries

#### 3. Architecture Agent

**Checks:**

- SOLID principle violations
- Circular dependencies
- God classes (too many responsibilities)
- Tight coupling
- Missing abstractions

#### 4. Testing Agent

**Checks:**

- Missing test coverage
- Weak assertions
- Flaky tests
- Untested edge cases
- Integration test gaps

**Parallel Execution:**

- All 4 agents run concurrently via Redis worker queue
- Total time: 3-5 minutes (vs. 12-20 minutes sequential)
- Results aggregated in `review_sessions.agent_results` JSONB field

### Knowledge Compounding

#### Learning Categories

1. **Pattern** (✨) - Reusable design or code pattern
   - Example: "Repository Pattern for Database Access"
   - Use when: You discover a useful pattern worth repeating

2. **Anti-Pattern** (⚠️) - Pattern to avoid
   - Example: "God Classes with 500+ Lines"
   - Use when: You identify something that causes problems

3. **Best Practice** (✅) - Recommended approach
   - Example: "Always Use Parameterized Queries"
   - Use when: You find an approach that works well

4. **Gotcha** (🔥) - Common pitfall or mistake
   - Example: "N+1 Queries in Loops"
   - Use when: You discover a common mistake to watch for

5. **Tip** (💡) - Helpful hint or optimization
   - Example: "Use const over let for Immutability"
   - Use when: You find a small optimization or trick

#### Impact Scoring (1-10)

- **10:** Game-changing insight that will save hours
- **8-9:** Very valuable, will definitely use again
- **6-7:** Useful knowledge worth remembering
- **4-5:** Helpful but specific to this project
- **1-3:** Minor observation

#### Automatic Integration

Learnings with `impactScore >= 5` automatically integrate into:

1. **CLAUDE.md** - Project documentation
   - Added to "Compound Learnings" section
   - Formatted with category emoji
   - Includes code examples, tags, file paths
   - Searchable by Claude in future sessions

2. **DEVB Knowledge Base** - `.claude/knowledge/devb-learnings.md`
   - Organized by category sections
   - Cross-referenced with workflow sessions
   - Feeds into DEVB AI analysis

3. **PostgreSQL Database** - `compound_learnings` table
   - 30-day TTL with automatic archival
   - Full-text search via tags and keywords
   - Frequency tracking (how often pattern appears)

#### Search and Retrieval

```bash
# Search by keyword
GET /api/v1/learnings/search?q=repository

# Filter by category
GET /api/v1/learnings?category=pattern

# Filter by impact
GET /api/v1/learnings?minImpactScore=8

# Get statistics
GET /api/v1/learnings/stats
```

**Database Features:**

- Tag-based search using PostgreSQL arrays
- ILIKE for case-insensitive text search
- Sorting by impact score and frequency
- Automatic expiry via TTL triggers

### Database Schema

#### Workflow Sessions

```sql
workflow_sessions (
  id UUID PRIMARY KEY,
  workflow_type VARCHAR(50),  -- 'architectflow' | 'devflow'
  title VARCHAR(255),
  git_worktree_path TEXT,     -- ArchitectFlow only
  git_branch_name TEXT,        -- DevFlow only
  git_base_branch VARCHAR(255),
  status VARCHAR(50),          -- 'planning' | 'reviewing' | 'completed' | 'archived'
  expires_at TIMESTAMP,        -- 30-day TTL
  ...
)
```

#### Review Sessions

```sql
review_sessions (
  id UUID PRIMARY KEY,
  workflow_session_id UUID REFERENCES workflow_sessions(id),
  review_type VARCHAR(50),     -- 'security' | 'performance' | 'architecture' | 'testing' | 'all'
  status VARCHAR(50),          -- 'pending' | 'in_progress' | 'completed' | 'failed'
  agent_results JSONB,         -- Array of agent results with findings
  processing_time_ms INTEGER,
  cost_in_cents DECIMAL,
  ...
)
```

#### Compound Learnings

```sql
compound_learnings (
  id UUID PRIMARY KEY,
  workflow_session_id UUID REFERENCES workflow_sessions(id),
  category VARCHAR(50),        -- 'pattern' | 'anti-pattern' | 'best-practice' | 'gotcha' | 'tip'
  title VARCHAR(255),
  description TEXT,
  code_example TEXT,
  tags TEXT[],                 -- PostgreSQL array
  file_paths TEXT[],
  impact_score INTEGER,        -- 1-10
  frequency_score INTEGER,     -- Auto-incremented on similar findings
  added_to_claude_md BOOLEAN,
  added_to_devb BOOLEAN,
  expires_at TIMESTAMP,        -- 30-day TTL
  ...
)
```

### API Endpoints

**Workflows:**

- `POST /api/v1/workflows` - Create workflow session
- `GET /api/v1/workflows` - List workflows
- `GET /api/v1/workflows/:id` - Get workflow details
- `PATCH /api/v1/workflows/:id/status` - Update status
- `POST /api/v1/workflows/cleanup` - Archive expired

**Reviews:**

- `POST /api/v1/reviews` - Create review session
- `GET /api/v1/reviews/:id` - Get review details
- `GET /api/v1/reviews/workflow/:workflowId` - List by workflow
- `PATCH /api/v1/reviews/:id/status` - Update status
- `GET /api/v1/reviews/stats` - Get statistics

**Learnings:**

- `POST /api/v1/learnings` - Create learning
- `GET /api/v1/learnings/:id` - Get learning details
- `GET /api/v1/learnings` - List with pagination/filters
- `GET /api/v1/learnings/search?q=query` - Search learnings
- `GET /api/v1/learnings/stats` - Get statistics
- `POST /api/v1/learnings/cleanup` - Archive expired

### Example Usage

**Scenario: Planning a New Microservices Architecture**

```bash
# 1. Start ArchitectFlow planning session
/architect:plan --title "E-Commerce Microservices" --autoReview

# Claude responds:
# ✅ ArchitectFlow planning session created
# 📂 Workspace: /tmp/architect-abc123
# 🌿 Branch: plan/abc123
# 🔍 Review queued: xyz789 (4 agents running)

# 2. Work in isolated worktree
cd /tmp/architect-abc123
# Create architecture diagrams, design documents, API specs

# 3. Wait for review to complete
/architect:review abc123 --wait --captureLearnings

# Claude responds:
# ✅ Review completed: E-Commerce Microservices
# 📊 Findings: 8 total
#    🔴 Critical: 1 (SQL injection in payment service)
#    🟠 High: 2 (Missing auth checks, N+1 queries)
#    🟡 Medium: 5
# ⏱️  Processing: 4200ms
# 💰 Cost: $0.068

# 4. Captured learnings appear in CLAUDE.md:
# ## Compound Learnings
# #### 🔥 SQL Injection in Payment Processing
# **Category:** gotcha | **Impact:** 10/10
# Always use parameterized queries when handling payment data...

# 5. Query learnings later
GET /api/v1/learnings/search?q=payment
```

**Scenario: Mid-Sprint Code Review**

```bash
# 1. Create DevFlow review for current feature
/devflow:review --title "User Authentication" --reviewType security --wait

# Claude responds:
# ✅ DevFlow review completed
# 🌿 Branch: review/user-authentication-def456
# 📊 Findings: 3 total
#    🟠 High: 1 (Weak password hashing)
#    🟡 Medium: 2

# 2. Manually capture critical learning
/devflow:compound --category anti-pattern \
  --title "Using MD5 for Password Hashing" \
  --description "MD5 is cryptographically broken. Use bcrypt or Argon2." \
  --impactScore 10

# Claude responds:
# ✨ Learning captured: Using MD5 for Password Hashing
# 📁 Category: anti-pattern
# ⭐ Impact: 10/10
# Integration:
#   ✅ CLAUDE.md
#   ✅ DEVB knowledge base
```

## Available Skills

Five powerful skills are available to enhance your workflow:

### 1. **Stripe Revenue Analyzer**

Analyzes Stripe revenue data for trends, growth patterns, top customers, churn rates, and payment metrics.

```bash
Skill("stripe-revenue-analyzer")
```

Use for: Financial analysis, customer insights, subscription health monitoring, pricing decisions

### 2. **Brand Voice**

Maintains consistent AI solutioning brand voice across all client-facing content with data-driven, practical, authority-building tone.

```bash
Skill("brand-voice")
```

Use for: Marketing materials, proposals, client communications, thought leadership, social media

### 3. **Content Optimizer**

Optimizes content for specific platforms (Reddit, LinkedIn, Twitter, HackerNews, Discord) with platform-specific formatting and engagement strategies.

```bash
Skill("content-optimizer")
```

Use for: Social media content, platform-specific posts, community engagement, content marketing

### 4. **Vercel Landing Page Builder**

Automates landing page creation using v0.dev for design and Vercel for instant deployment.

```bash
Skill("vercel-landing-page-builder")
```

Use for: Product launches, SaaS pages, marketing sites, conversion-optimized landing pages, rapid prototyping

### 5. **Frontend Design**

Creates distinctive, production-grade frontend interfaces that avoid generic AI aesthetics. Applies bold design direction with intentional typography, color, and motion.

```bash
Skill("frontend-design")
```

Use for: React components, UI/UX implementation, dashboards, landing pages, design system creation. Automatically activated by `/design-os/design-screen` command.

**See `.claude/SKILLS_REFERENCE.md` for comprehensive skill documentation.**

## Comprehensive Slash Commands

This project includes **120+ slash commands** across 45+ categories:

### Quick Access by Category

**Core Development**:

- `/dev:*` - Feature implementation, reviews, testing, CI/CD integration (10 commands)
- `/devops:*` - Infrastructure, deployment, monitoring, cost optimization (8 commands)
- `/cicd:*` - Pipeline setup, testing, deployment automation (4 commands)
- `/db:*` - Database operations, migrations, backups (5 commands)

**Data & Insights**:

- `/finance:*` - Financial reports, budgeting, tax planning, investments (5 commands)
- `/product:*` - Positioning, pricing, investor reports, definitions (5 commands)
- `/startup:*` - GTM strategy, metrics, idea validation, competitive analysis (5 commands)
- `/ai-search:*` - Content optimization for AI search engines, citation tracking (4 commands)

**Communication & Content**:

- `/zoho:*` - CRM, email, SMS operations with approval workflows (3 commands)
- `/scripts:*` - Video, podcast, screenplay, dialogue generation (5 commands)
- `/research:*` - Organization, annotation, summarization, citation (5 commands)
- `/brand:*` - Brand asset management, mention monitoring (2 commands)

**User Experience & Quality**:

- `/accessibility:*` - WCAG audits, fixes, automated testing (3 commands)
- `/auth:*` - Authentication setup, testing, key rotation, compliance audits (4 commands)
- `/ui:*` - Dashboard and interface management (1 command)

**Personal & Team**:

- `/assistant:*` - Research, scheduling, task management, email handling (5 commands)
- `/travel:*` - Trip planning, optimization, document management (5 commands)
- `/resume:*` - Resume building, portfolio creation, LinkedIn optimization (5 commands)
- `/career:*` - Job search, interview prep, salary negotiation (implied in resume commands)

**Advanced Capabilities**:

- `/integrations:*` - Figma, Jira, Notion synchronization (3 commands)
- `/gamify:*` - Game mechanics, reward systems, analytics (4 commands)
- `/model:analyze` - Intelligent model selection and complexity analysis

**Product Design**:

- `/design-os:*` - Product planning, design system, section design, export (10 commands)

**Spec-Driven Development**:

- `/agent-os:*` - Spec initialization, shaping, writing, tasks, implementation (8 commands)

**Complete reference**: See `.claude/SLASH_COMMANDS_REFERENCE.md` for all 128+ commands with full documentation.

## Resource References

### DEVB System Documentation

- `.claude/DEVB_SYSTEM_GUIDE.md` - Comprehensive guide to DEVB system (1,000+ lines)
- DEVB System Architecture: Design → Emulate → Validate → Build (NVIDIA-inspired)
- Use for: Any new feature, workflow chain, infrastructure, or complete solution design
- Database Migration: `shopify-dashboard/backend/postgres/migrations/011-devb-system.sql`

### Guides (Best Practices)

- `/guides/unified-best-practices__claude_sonnet_4.md` - Primary reference (3,277 lines)
- `/guides/anthropic-best-practices__chatgpt-4_5.md` - Anthropic-specific patterns
- `/guides/openai-best-practices__chatgpt-4_5.md` - OpenAI-specific patterns
- `/guides/google-best-practices__chatgpt-4_5.md` - Google-specific patterns

### Meta-Prompts (Agent Definitions)

- `/meta-prompts/prompt-engineering-agent.md` - PromptCraft∞ Elite (7-stage workflow)
- `/meta-prompts/documentation-expert-agent.md` - Documentation specialist

### Examples (Templates)

- `/examples/customer-support-agent.md` - Customer support agent template

### Patterns (Integration Strategies)

- `/patterns/integration/` - Zoho and external API patterns
- `/patterns/orchestration/` - Multi-agent coordination patterns
- `/patterns/interfaces/` - CLI, web, and Zoho widget patterns

### Templates (Reusable Agents)

- `/templates/zoho-crm-agent.md` - CRM operations specialist
- `/templates/zoho-mail-agent.md` - Email operations specialist
- `/templates/zoho-sms-agent.md` - SMS operations specialist
- `/templates/routing-coordinator-agent.md` - Task routing coordinator

## Development Workflow

### Adding New Functionality

1. **Enhance, don't remove** - Add new fields/columns to data model
2. **Create meta-agent first** - Define the AI agent for the new capability
3. **Build integration pattern** - Document how it integrates with existing systems
4. **Create slash command** - Make it accessible via CLI
5. **Add to web interface** - Expose in web UI (if applicable)
6. **Integrate with Zoho** - Connect to Zoho ONE systems (if applicable)
7. **Test end-to-end** - Validate complete workflow
8. **Document thoroughly** - Update guides and examples

### Creating New Slash Commands

1. Create command file in appropriate subdirectory (`.claude/commands/`)
2. Use frontmatter for configuration (allowed-tools, argument-hint, description)
3. Reference existing agents and patterns from repository
4. Include human approval steps for data modifications
5. Test command thoroughly
6. Update README.md with command documentation

### Creating New Agents

1. Use `/meta-prompts/prompt-engineering-agent.md` to generate agent definition
2. Follow the professional template structure:
   - ROLE & EXPERTISE
   - MISSION CRITICAL OBJECTIVE
   - OPERATIONAL CONTEXT
   - INPUT PROCESSING PROTOCOL
   - REASONING METHODOLOGY
   - OUTPUT SPECIFICATIONS
   - QUALITY CONTROL CHECKLIST
   - EXECUTION PROTOCOL
3. Save to `/templates/` for reusable agents
4. Save to `/examples/` for specific use case examples
5. Document integration patterns in `/patterns/`

## Quality Standards

### All Prompts Must

- Follow unified best practices from `/guides/unified-best-practices__claude_sonnet_4.md`
- Include clear role definition and expertise areas
- Specify operational context (domain, audience, quality tier)
- Define input processing protocol
- Specify reasoning methodology (CoT, ReAct, etc.)
- Include quality control checklist
- Provide execution protocol

### All Integrations Must

- Include error handling and retry logic
- Implement approval workflows for data modifications
- Log all operations for audit trail
- Handle rate limiting and API quotas
- Provide clear error messages and recovery paths

### All Slash Commands Must

- Have clear, descriptive names
- Include helpful argument hints
- Provide step-by-step execution
- Reference relevant guides and patterns
- Include success/failure criteria
- Keep implementation under 10 major steps

## Troubleshooting

### Command Not Working?

1. Check command file syntax (markdown + optional frontmatter)
2. Verify file location (`.claude/commands/[category]/[name].md`)
3. Test with `/help` to see if command is listed
4. Check for typos in command name or arguments

### Agent Not Behaving Correctly?

1. Review agent definition against template structure
2. Check if operational context is clear enough
3. Verify reasoning methodology is specified
4. Test with different inputs to isolate issue
5. Reference `/guides/unified-best-practices__claude_sonnet_4.md` for improvements

### Zoho Integration Issues?

1. Verify API credentials and authentication
2. Check rate limits and quotas
3. Review approval workflow logs
4. Test with simpler operations first
5. Consult integration patterns in `/patterns/integration/`

## Important Notes

- **Security**: Never commit Zoho API credentials to version control
- **Performance**: Cache frequently accessed CRM data to minimize API calls
- **Scalability**: Design for multiple simultaneous agent operations
- **Monitoring**: Track agent performance and success rates
- **Documentation**: Keep guides and examples up to date with new capabilities
