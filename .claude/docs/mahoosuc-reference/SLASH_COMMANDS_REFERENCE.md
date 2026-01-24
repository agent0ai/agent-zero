# Slash Commands Reference

Comprehensive documentation of all available slash commands organized by category.

## DevOps Commands

### Infrastructure & Deployment

- **`/devops:cost-analyze [--project <gcp-project-id>] [--period <days>] [--format <json|markdown|csv>]`**
  GCP cost analysis with service breakdown, trend analysis, and anomaly detection

- **`/devops:deploy <environment> [--version tag] [--strategy blue-green|canary|rolling]`**
  Deploy application to cloud environment with safety checks

- **`/devops:monitor [service-name] [--metrics cpu|memory|requests|errors|latency]`**
  Monitor production deployments with real-time metrics and alerts

- **`/devops:verify [service-name] [--environment production|staging] [--critical-path-only]`**
  Post-deployment verification with automated smoke tests and health checks

- **`/devops:cost-optimize [--project <gcp-project-id>] [--auto-apply] [--savings-threshold <min-savings>]`**
  GCP cost optimization recommendations with committed use discounts and right-sizing

- **`/devops:setup <environment> [--provider gcp|aws|azure]`**
  Set up and configure cloud infrastructure with AI assistance

- **`/devops:debug [service-name] [--issue error|latency|crash|memory]`**
  Debug production issues with AI-assisted log analysis and troubleshooting

- **`/devops:rollback [service-name] [--to-revision revision-id]`**
  Emergency rollback to previous stable version with database migration reversal

## Model Selection

- **`/model:analyze <task description>`**
  Analyze task complexity and recommend optimal Claude model (Haiku/Sonnet/Opus)

## Finance Commands

- **`/finance:report [--type <income|balance|cashflow|pnl>] [--period <month|quarter|year>] [--format <pdf|excel>]`**
  Generate financial reports and statements

- **`/finance:budget [--type <personal|business>] [--period <monthly|annual>] [--categories <auto|custom>]`**
  Create and manage personal/business budgets with tracking and forecasting

- **`/finance:goals [--goal <house|retirement|education|business>] [--timeline <years>] [--current-savings]`**
  Set and track financial goals with milestone planning

- **`/finance:invest [--portfolio <current>] [--risk-tolerance <low|medium|high>] [--goals <retirement|growth|income>]`**
  Investment analysis and portfolio optimization recommendations

- **`/finance:tax [--year <2024>] [--filing-status <single|married|business>] [--optimize-deductions]`**
  Tax planning and deduction optimization

## Authentication Commands

- **`/auth:test [--endpoint login|logout|refresh|protected] [--coverage]`**
  Test authentication system with comprehensive security validation

- **`/auth:audit [--framework hipaa|pci-dss|soc2|all]`**
  Security audit of authentication system with compliance validation

- **`/auth:setup <jwt|oauth|session> [--provider google|github|auth0]`**
  Set up authentication system with JWT, OAuth, or session-based auth

- **`/auth:rotate-keys [--key-type jwt|api|all] [--graceful-transition]`**
  Rotate JWT signing keys, API keys, and secrets with zero downtime

## Travel Commands

- **`/travel:optimize [--route <origin-destination>] [--flexibility <days>] [--find-deals]`**
  Optimize travel costs (flights, hotels, transportation)

- **`/travel:plan [--destination <city>] [--dates <range>] [--budget <amount>] [--interests <culture|food|adventure>]`**
  Plan complete trips with itinerary, bookings, and recommendations

- **`/travel:docs [--destination <country>] [--check-requirements] [--organize]`**
  Manage travel documents (visas, insurance, confirmations)

- **`/travel:pack [--destination <city>] [--duration <days>] [--activities <list>] [--weather-check]`**
  Generate smart packing lists based on destination and activities

- **`/travel:guide [--city <name>] [--interests <food|culture|nightlife|nature>] [--local-insider]`**
  Create personalized travel guides with local tips and hidden gems

## Zoho Integration Commands

- **`/zoho:send-sms <phone-number> [message or template]`**
  Send SMS via Zoho CRM/SMS with approval workflow and compliance checks

- **`/zoho:create-lead <lead details or interactive>`**
  Create a new lead in Zoho CRM with human approval workflow

- **`/zoho:send-email <recipient> [template-name]`**
  Send email via Zoho Mail with approval workflow and template support

## Research Commands

- **`/research:organize [--structure <topic|chronological|source>] [--tags] [--export]`**
  Organize research materials into structured knowledge base

- **`/research:annotate [--doc <path>] [--auto-highlight] [--export-notes]`**
  Add annotations, highlights, and notes to research documents

- **`/research:summarize [--length <short|medium|long>] [--audience <technical|executive|general>]`**
  Create executive summaries and research briefs

- **`/research:cite [--style <apa|mla|chicago|harvard>] [--format <inline|footnote|endnote>]`**
  Generate and manage citations and bibliographies

- **`/research:gather [--topic <subject>] [--sources <academic|news|web|all>] [--depth <quick|thorough>]`**
  Gather and synthesize research from academic papers, articles, and web sources

## Scripting Commands

- **`/scripts:video [--platform <youtube|tiktok|corporate>] [--length <seconds>] [--hook-style]`**
  Write video scripts for YouTube, TikTok, or corporate videos

- **`/scripts:storyboard [--script <file>] [--shot-types] [--export-pdf]`**
  Create visual storyboards from scripts with shot descriptions

- **`/scripts:dialogue [--characters <list>] [--tone <dramatic|comedic|casual>] [--context <scene-description>]`**
  Generate natural, character-specific dialogue

- **`/scripts:screenplay [--type <film|tv|short|commercial>] [--genre <drama|comedy|action|thriller>] [--length <pages>]`**
  Write screenplays with industry-standard formatting

- **`/scripts:podcast [--length <minutes>] [--format <interview|narrative|panel>] [--segments]`**
  Create podcast scripts with intro/outro, transitions, and timing

## UI Commands

- **`/ui:dashboard [--port <port>] [--open] [--dev]`**
  Launch the native web-based dashboard for visual command execution and monitoring

## Gamification Commands

- **`/gamify:mechanics [--mechanics <points|badges|levels|quests>] [--platform <web|mobile|both>]`**
  Implement game mechanics (points, badges, leaderboards, challenges)

- **`/gamify:design [--type <app|training|marketing|community>] [--goals <engagement|retention|learning>]`**
  Design gamification systems for apps, products, or training programs

- **`/gamify:analytics [--metrics <engagement|retention|completion>] [--dashboard]`**
  Track and optimize gamification performance metrics

- **`/gamify:rewards [--type <intrinsic|extrinsic|mixed>] [--progression <linear|exponential>]`**
  Design reward systems and progression loops

## System Commands

- **`/system:subscription-status`**
  Check Claude Code subscription status and API usage configuration

## Development Commands

### Code Workflow

- **`/dev:create-branch <feature-name> [issue-number]`**
  Create a feature branch and set up development environment

- **`/dev:implement <feature-name or description>`**
  AI-assisted feature implementation with intelligent agent routing

- **`/dev:review [file-pattern or 'all']`**
  Self-review code before creating PR with AI assistance

- **`/dev:test [test-pattern or 'all']`**
  Run tests and fix failures with AI assistance

- **`/dev:feature-request <feature description>`**
  Plan and scope a new feature request with AI assistance

- **`/dev:full-cycle <feature-description> [--skip-review] [--auto-deploy]`**
  Complete development workflow from feature idea to production deployment

- **`/dev:hotfix <bug-description> [--severity critical|high]`**
  Fast-track critical production bug fixes with streamlined workflow

### API Testing & Quality

- **`/dev:contract-test [--spec <openapi-file>] [--mode <validate|breaking|ci>] [--fail-on <breaking|warning>]`**
  API contract testing with OpenAPI/Swagger schema validation and breaking change detection

### Git & Pull Requests

- **`/dev:create-pr [--draft] [--base branch]`**
  Create a pull request with AI-generated description and checklist

- **`/dev:merge [PR-number or current branch]`**
  Merge approved PR with safety checks and cleanup

## Accessibility Commands

- **`/accessibility:test [--tool <axe|lighthouse|pa11y|all>] [--url <url>] [--ci] [--fail-on <critical|high|medium>]`**
  Automated accessibility testing with axe-core, Lighthouse, and CI/CD integration

- **`/accessibility:fix [--audit-report <path>] [--auto-apply] [--severity <critical|high|medium|low>]`**
  Automated accessibility fixes for common WCAG violations with code transformations

- **`/accessibility:audit [--url <url>] [--level <A|AA|AAA>] [--format <json|markdown|html>]`**
  Comprehensive WCAG 2.1/2.2 accessibility compliance audit with scoring and auto-fix recommendations

## AI Search Optimization

- **`/ai-search:optimize [--page <path>] [--ai-engines <chatgpt|claude|perplexity|sge|all>] [--preview]`**
  Optimize content for AI-powered search engines (ChatGPT, Claude, Perplexity, Google SGE)

- **`/ai-search:monitor [--focus <citations|snippets|traffic|competitive|all>] [--period <daily|weekly|monthly>] [--dashboard]`**
  Monitor and analyze AI search performance across ChatGPT, Claude, Perplexity, and Google SGE

- **`/ai-search:citations [--mode <build|track|analyze>] [--page <path>] [--ai-engines <chatgpt|claude|perplexity|all>]`**
  Build citation-worthy content and track AI engine citations of your content

- **`/ai-search:snippets [--page <path>] [--snippet-types <definition|howto|comparison|statistic|all>] [--preview]`**
  Optimize content for AI-generated snippets and direct answers in ChatGPT, Claude, Perplexity

## Database Commands

- **`/db:backup <environment> [--retention days]`**
  Backup database with encryption, compression, and cloud storage

- **`/db:query <natural language query> [--explain]`**
  AI-powered SQL query generation from natural language with safety checks

- **`/db:migrate <create|up|down|status> [migration-name]`**
  Create and run database migrations with AI assistance

- **`/db:restore <environment> <backup-file> [--verify-only]`**
  Restore database from backup with verification and safety checks

- **`/db:seed <environment> [--data-set test|demo|defaults]`**
  Seed database with test data, demo data, or production defaults

## Design & Build (DEVB System)

The DEVB System implements NVIDIA's approach to pre-production validation: design, emulate, validate, and generate specifications before building - catching design flaws in simulation rather than expensive production implementation.

### `/design:solution` - Create Design Specification

Create comprehensive specifications for any solution type (workflow chains, features, infrastructure, complete solutions)

**Usage**: `/design:solution`

**Interactive Prompts**:

- Solution name (required)
- Solution type: workflow-chain | feature | infrastructure | complete-solution
- Description (required)
- Functional requirements (comma-separated list)
- Non-functional requirements (performance, security, scalability)
- Constraints (budget, timeline, tech stack)
- Dependencies (existing systems)
- Architecture description (optional)

**Outputs**:

- Design specification with all components
- Component definitions (services, APIs, databases)
- Data model schema changes
- API contract definitions
- Workflow chain compositions
- Design stored in PostgreSQL with full-text search

**Example**:

```
/design:solution

Solution Name: Revenue Growth Automation
Type: complete-solution
Description: AI-powered revenue analytics with Stripe integration...
[interactive prompts continue]

✅ Design created: rev-growth-automation-001
Next: /design:emulate [design-id]
```

**Use Case**: Starting point for any new solution design

---

### `/design:emulate` - Emulate Solution Without Building

Test solutions without side effects using three emulation methods to find design flaws before implementation

**Usage**: `/design:emulate [design-id|design-name]`

**Emulation Methods**:

1. **Dry-Run** - Execute workflow chains with mocked dependencies (no database writes)
2. **Static Analysis** - Analyze design for security, performance, database issues
3. **Simulation** - Test mock implementations with test data and edge cases

**Outputs** (For each method):

- Issues found (critical, high, medium, low)
- Estimated fix times
- Actionable recommendations
- Overall quality score (0-100)
- Details on execution time, resource usage, data flows

**Example Results**:

```
DRY-RUN: Executed 8 workflow steps in 2.4 seconds
- Found 0 critical errors, 0 high severity issues

STATIC ANALYSIS: Analyzed 12 components
- Critical: Missing Stripe API error handling (1 issue)
- High: N+1 query in revenue dashboard (1 issue)
- Medium: Missing database indexes (2 issues)

SIMULATION: Tested 12 scenarios with mock data
- Success rate: 91.7% (11/12 passed)
- Race condition found in cache updates

Overall Quality Score: 75/100
Recommendation: Fix critical issues before validation
```

**Next**: `/design:validate [design-id]`

---

### `/design:validate` - Multi-Perspective AI Validation

Validate design from 4 perspectives (Security, Performance, Cost, UX) before generating specifications

**Usage**: `/design:validate [design-id|design-name]`

**4 Validation Perspectives**:

1. **Security & Compliance** (0-100 score)
   - Authentication (OAuth, JWT, Sessions)
   - Authorization and access control
   - Data protection (encryption, HIPAA, GDPR, PCI-DSS)
   - Vulnerability assessment (SQL injection, XSS, CSRF)
   - Compliance readiness (HIPAA, GDPR, PCI-DSS, SOC2)

2. **Performance & Scalability** (0-100 score)
   - Database optimization (N+1 queries, indexes)
   - Caching strategy evaluation
   - Load capacity (max concurrent users)
   - API latency targets (P95, P99)
   - Horizontal scaling readiness

3. **Cost & ROI** (0-100 score)
   - Infrastructure cost estimation (compute, storage, bandwidth)
   - Maintenance cost projection
   - ROI timeline (payback period)
   - Cost per user metrics
   - Cost optimization opportunities

4. **User Experience** (0-100 score)
   - API design quality (REST compliance)
   - Accessibility (WCAG 2.1 AA/AAA)
   - Documentation quality and coverage
   - Error handling clarity
   - Mobile responsiveness

**Outputs**:

- Individual score for each perspective (0-100)
- Overall design score (average of 4)
- Readiness status: READY (≥80) | NEEDS_FIXES (60-79) | BLOCKED (<60)
- Critical issues with fix time estimates
- Recommendations for improvement

**Example Results**:

```
SECURITY: 82/100 ✅
- JWT with refresh tokens ✅
- Encryption at rest/transit ✅
- HIPAA Ready: Yes ✅
- Issues: Rate limiting on sensitive endpoints (HIGH - 2-3 hours)

PERFORMANCE: 75/100 ⚠️
- Max concurrent users: 5,000
- P95 latency: <200ms
- Issues: N+1 query in dashboard (HIGH - 2-3 hours)

COST: 78/100 ⚠️
- Monthly: $2,500
- Year 1: $35,000
- Payback: 4.2 months
- ROI: 186% Year 1 ✅

UX: 85/100 ✅
- API design: Excellent
- WCAG: AA compliant
- Documentation: Complete

OVERALL: 80/100 ✅
READINESS: READY FOR BUILD
```

**Next**: `/design:spec [design-id]`

---

### `/design:spec` - Generate Complete Specifications

Generate production-ready specifications with 4 types of artifacts (diagrams, OpenAPI, test plan, checklist)

**Usage**: `/design:spec [design-id|design-name]`

**4 Specification Outputs**:

1. **Architecture Diagrams** (4 Mermaid diagrams)
   - System Architecture Diagram (high-level components)
   - Data Flow Diagram (how data moves through system)
   - Component Interaction Diagram (detailed relationships)
   - Database ER Diagram (entity relationships and schema)

2. **OpenAPI 3.0 Specification**
   - Complete REST API definition
   - All endpoints with request/response schemas
   - Authentication requirements
   - Rate limiting configuration
   - Error responses
   - Ready for Swagger UI, ReDoc, SDK generation

3. **Comprehensive Test Plan**
   - Unit tests (per component, 90%+ coverage)
   - Integration tests (component interactions)
   - E2E tests (complete user workflows)
   - Performance tests (load testing scenarios)
   - Security tests (vulnerability testing)
   - Total test cases: 80-100+
   - Estimated hours: 40-60

4. **Implementation Checklist**
   - Pre-implementation tasks
   - Database schema and migration steps
   - API endpoint implementation
   - Testing and validation
   - Deployment procedures
   - 40-50+ checklist items
   - Effort estimates (100-200+ hours)

**Export Formats**:

- JSON (structured data for tooling)
- PDF (12-20 page professional report)
- Markdown (wiki-ready documentation)

**Example Output**:

```
Specifications Generated Successfully ✅

ARTIFACTS:
- System Architecture (4 diagrams, Mermaid)
- OpenAPI Spec (12 endpoints)
- Test Plan (92 test cases, 50 hours)
- Implementation Checklist (48 items, 160 hours)

EFFORT ESTIMATE:
- Development: 160 hours
- Testing: 40 hours
- Deployment: 20 hours
- Total: 220 hours (5.5 weeks for 1 developer)

COST ESTIMATE: $16,500 (at $75/hour)

EXPORTS:
- specification.json (3.2 MB)
- specification.pdf (20 pages)
- specification.md (documentation)
```

**Next**: Implementation using generated specifications

---

### DEVB System Benefits

| Phase | Purpose | Outcomes |
|-------|---------|----------|
| **DESIGN** | Capture requirements and create specifications | Complete design artifacts for 4 solution types |
| **EMULATE** | Test design without side effects | Find 5-10 design flaws early before implementation |
| **VALIDATE** | Multi-perspective AI analysis | 80-100 readiness score before building |
| **BUILD** | Generate implementation specifications | Architecture diagrams, API specs, test plans, checklists |

**Key Benefits**:

- ✅ Catch design flaws in emulation (not production)
- ✅ Validate from 4 perspectives (security, performance, cost, UX)
- ✅ Generate complete specifications automatically
- ✅ Save 40-60 hours of manual documentation
- ✅ Increase implementation success rate
- ✅ Reduce implementation time by 20-30%

**Comparable to**: NVIDIA's GPU emulation approach - test before you fabricate

---

### Example Complete Workflow

```bash
# Step 1: Design solution
/design:solution
→ Create specification for "Revenue Growth Automation"

# Step 2: Emulate design
/design:emulate rev-growth-automation-001
→ Find 6 design issues, improve design to 87/100

# Step 3: Validate design
/design:validate rev-growth-automation-001
→ 80/100 overall score, READY for build

# Step 4: Generate specifications
/design:spec rev-growth-automation-001
→ Generate 4 artifacts, 160-hour implementation roadmap

# Result: Production-ready specifications ready for implementation
```

---

## Problem Solutioning Commands

AI-powered commands for designing and implementing complete technical solutions with approval checkpoints and comprehensive documentation.

### Analysis & Design

- **`/solve:analyze <problem-description> [--output <file>]`**
  Decompose complex technical problems into solvable sub-problems with effort estimation, dependency analysis, and roadmap creation

- **`/solve:design <solution-name> [--approach <architectural-pattern>] [--validate]`**
  Design comprehensive technical solutions with architecture diagrams, API contracts, data models, and risk analysis

### Implementation & Execution

- **`/solve:implement <design-file> [--scaffold] [--test-coverage <percent>] [--deploy]`**
  Generate implementation code, setup testing infrastructure, create Docker configuration, and deployment guides

- **`/solve:debug <service-name> [--issue <description>] [--hypothesis]`**
  Multi-phase debugging with root cause analysis, AI-assisted investigation, and automated testing for regression prevention

### Database & Infrastructure

- **`/solve:db-design <requirements> [--db-type <postgres|mysql|mongodb>] [--scale <small|medium|large>]`**
  Design optimized database schemas with normalization analysis, indexing strategies, scalability planning, and zero-downtime migration support

- **`/solve:database-migration <change-description> [--strategy <concurrent|batch|multistep>] [--backup]`**
  Execute zero-downtime database migrations with automated backup, rollback procedures, and performance validation

### API & Integration

- **`/solve:api-integration <provider-name> [--oauth] [--webhook] [--rate-limiting]`**
  Complete OAuth 2.0 API integration from discovery to production with rate limiting, webhook verification, and comprehensive tests

- **`/solve:webhook-setup <provider> [--events <event-list>] [--signature <method>]`**
  Configure secure, production-ready webhook receivers with HMAC signature verification, retry logic, and comprehensive monitoring

- **`/solve:api-sync <source-system> <target-system> [--sync-type <unidirectional|bidirectional>] [--frequency <realtime|batch>]`**
  Design and implement data synchronization workflows with conflict resolution, change detection, idempotency, and rollback support

### Validation & Quality

- **`/solve:validate <solution-name> [--framework <requirement-file>] [--depth <quick|thorough|comprehensive>]`**
  Validate implemented solutions against requirements with test automation, performance analysis, security checks, and comprehensive reporting

## Product Commands

- **`/product:positioning <product-name> [--competitors "<comma-separated-list>"]`**
  Generate market positioning and competitive differentiation for product

- **`/product:investor-report --folder <path> [--batch <path1,path2,...>] [--target-investor-type vc|angel|bootstrap] [--include-pitch-deck] [--export pdf|markdown] [--skip-extraction]`**
  Determine if product is investor-worthy with competitive analysis, market sizing, and investment readiness scoring

- **`/product:define <product-name> [--category saas|app|service|hardware]`**
  Define and refine product with AI-assisted analysis and questioning

- **`/product:summarize <product-name> [--length short|medium|long] [--audience founder|investor|customer|developer]`**
  Generate AI-powered product summaries for different audiences and channels

- **`/product:pricing <product-name> [--strategy value|cost-plus|competitive|freemium]`**
  AI-powered pricing analysis and strategy recommendations

## Project Commands

- **`/project:visualize [project-path] [--focus <category>] [--level <high|medium|detail>] [--update]`**
  Analyze project and generate comprehensive Mermaid diagrams across 7 categories (architecture, data, API, UI, events, agents, runbooks) with auto-detection and user control

## Assistant Commands

- **`/assistant:research [--topic <subject>] [--depth <quick|thorough>] [--summarize]`**
  Quick research and information gathering for any topic

- **`/assistant:schedule [--calendar <google|outlook|apple>] [--optimize] [--conflicts]`**
  Manage calendar, meetings, and time blocking

- **`/assistant:tasks [--add <task>] [--prioritize] [--delegate] [--tracking]`**
  Organize tasks, to-dos, and project management

- **`/assistant:remind [--reminder <text>] [--when <time>] [--recurring] [--context]`**
  Set up intelligent reminders and follow-ups

- **`/assistant:email [--action <draft|summarize|prioritize|respond>] [--tone <formal|friendly|brief>]`**
  Draft, summarize, and manage emails with AI assistance

## CI/CD Commands

- **`/cicd:monitor [--dashboard] [--alerts] [--metrics] [--historical]`**
  Monitor CI/CD pipeline health, track metrics, and set up alerts for failures

- **`/cicd:test-pipeline [--framework <jest|pytest|go-test>] [--coverage-threshold <percentage>] [--include-e2e] [--include-perf]`**
  Create comprehensive test pipeline with unit, integration, E2E, and performance tests

- **`/cicd:setup [--platform <github|gitlab|circleci>] [--project-type <nodejs|python|go|java|docker>] [--environments <dev,staging,prod>]`**
  Initialize comprehensive CI/CD pipeline with GitHub Actions, GitLab CI, or CircleCI

- **`/cicd:deploy-pipeline [--environments <dev,staging,prod>] [--strategy <rolling|blue-green|canary>] [--auto-rollback]`**
  Create deployment pipeline with multi-environment support, approval gates, and rollback mechanisms

## Integration Commands

- **`/integrations:figma [--file <figma-file-id>] [--mode <tokens|export|components>] [--output <output-dir>]`**
  Figma design system integration - sync design tokens, export designs, and generate component stubs

- **`/integrations:jira [--mode <create|update|link>] [--ticket <ticket-id>] [--auto]`**
  Jira integration - create tickets from code, update status from commits, link PRs to tickets

- **`/integrations:notion [--mode <sync-docs|changelog|create-page>] [--page <notion-page-id>] [--auto]`**
  Notion integration - sync documentation, update changelogs, create project pages

## Career & Resume Commands

- **`/resume:optimize [--resume <file>] [--job-posting <url|text>] [--analyze-keywords]`**
  Optimize resume for specific job postings and ATS systems

- **`/resume:portfolio [--projects <list>] [--template <minimal|creative|corporate>] [--deploy]`**
  Create professional portfolio websites and case studies

- **`/resume:build [--template <modern|professional|creative|ats>] [--role <job-title>] [--export <pdf|docx>]`**
  Create professional resumes and CVs with ATS optimization

- **`/resume:cover-letter [--job <posting>] [--company <name>] [--tone <formal|enthusiastic|confident>]`**
  Generate personalized cover letters for job applications

- **`/resume:linkedin [--section <headline|summary|experience|all>] [--industry <field>]`**
  Optimize LinkedIn profile with headline, summary, and experience descriptions

## Startup Commands

- **`/startup:gtm [--idea <description>] [--budget <amount>] [--timeline <months>]`**
  Generate go-to-market strategy and launch plan

- **`/startup:metrics [--stage <pre-seed|seed|growth>] [--model <saas|marketplace|ecommerce>]`**
  Define key metrics and build financial projections

- **`/startup:generate [--industry <saas|fintech|healthtech|ecommerce>] [--constraints <budget|time|team>] [--validate]`**
  Generate and validate startup ideas using market data and trend analysis

- **`/startup:competitive [--idea <description>] [--competitors <list>] [--positioning]`**
  Analyze competitive landscape and identify market positioning opportunities

- **`/startup:validate [--idea <description>] [--deep-dive] [--market-research]`**
  Validate startup ideas against market demand, competition, and feasibility

## Brand & Marketing Commands

- **`/brand:assets [--generate <type>] [--organize] [--audit] [--export <format>]`**
  Manage and organize brand assets (logos, colors, fonts, templates)

- **`/brand:monitor [--channels <social|web|news|all>] [--period <realtime|daily|weekly>] [--alerts]`**
  Monitor brand mentions, sentiment, and compliance across all channels

## Quick Reference by Use Case

### When You Need to

**Design and validate solutions before building**: `/design:solution`, `/design:emulate`, `/design:validate`, `/design:spec`

**Solve complex technical problems**: `/solve:analyze`, `/solve:design`, `/solve:implement`, `/solve:validate`

**Design database schemas**: `/solve:db-design`, `/solve:database-migration`, `/db:migrate`

**Integrate APIs**: `/solve:api-integration`, `/solve:webhook-setup`, `/solve:api-sync`

**Debug production issues**: `/solve:debug`, `/devops:debug`, `/dev:hotfix`, `/devops:monitor`

**Deploy code**: `/solve:implement`, `/dev:full-cycle`, `/devops:deploy`, `/cicd:deploy-pipeline`

**Optimize costs**: `/devops:cost-optimize`, `/devops:cost-analyze`

**Manage Zoho data**: `/zoho:create-lead`, `/zoho:send-email`, `/zoho:send-sms`

**Test quality**: `/solve:validate`, `/accessibility:test`, `/dev:test`, `/auth:test`, `/dev:contract-test`

**Make decisions**: `/model:analyze`, `/product:pricing`, `/startup:validate`

**Plan & organize**: `/assistant:tasks`, `/assistant:schedule`, `/research:organize`

**Optimize content**: `/ai-search:optimize`, `/ai-search:snippets`, `/ai-search:citations`

**Build features**: `/dev:implement`, `/dev:feature-request`, `/dev:review`

**Manage databases**: `/solve:db-design`, `/db:backup`, `/db:query`, `/db:migrate`, `/db:restore`

**Create marketing content**: `/scripts:video`, `/scripts:podcast`, `/scripts:screenplay`, `/brand:assets`

---

## Command Categories Summary

- **Design & Build (DEVB)** (`/design:*`) - 4 commands for pre-production validation and specification generation
- **Problem Solutioning** (`/solve:*`) - 10 commands for designing and implementing complete technical solutions
- **Development** (`/dev:*`) - 10 commands for feature implementation, testing, code review, and CI/CD
- **DevOps** (`/devops:*`) - 8 commands for infrastructure, deployment, monitoring, and optimization
- **Database** (`/db:*`) - 5 commands for backups, migrations, queries, and data seeding
- **Authentication** (`/auth:*`) - 4 commands for auth setup, testing, and compliance
- **Finance** (`/finance:*`) - 5 commands for reports, budgeting, investments, and tax planning
- **Product** (`/product:*`) - 5 commands for positioning, pricing, definitions, and investor analysis
- **Startup** (`/startup:*`) - 5 commands for GTM strategy, metrics, validation, and competitive analysis
- **Communication & Content** - 18 commands across Zoho (`/zoho:*`), Scripts (`/scripts:*`), Research (`/research:*`), and Brand (`/brand:*`)
- **Accessibility** (`/accessibility:*`) - 3 commands for WCAG audits, fixes, and testing
- **AI Search** (`/ai-search:*`) - 4 commands for content optimization and monitoring
- **CI/CD** (`/cicd:*`) - 4 commands for pipeline setup, testing, and deployment
- **Integrations** (`/integrations:*`) - 3 commands for Figma, Jira, and Notion sync
- **Travel** (`/travel:*`) - 5 commands for planning, optimization, and document management
- **Resume & Career** (`/resume:*`) - 5 commands for portfolio, LinkedIn, and job optimization
- **Assistant & Personal** (`/assistant:*`) - 5 commands for research, scheduling, and task management
- **Gamification** (`/gamify:*`) - 4 commands for mechanics, design, rewards, and analytics
- **UI** (`/ui:*`) - 1 command for dashboard management

**Total: 104+ slash commands across 41+ categories**

---

**Last Updated**: 2025-12-06 | **DEVB System**: Phase 1-4 Complete (4 commands) | **Problem Solutioning Engine**: Phase 1-4 Complete (10 commands)
