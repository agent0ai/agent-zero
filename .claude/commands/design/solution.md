---
description: Create comprehensive solution design with optional constitution-first governance and spec-kit integration
allowed-tools: [Bash, Read, Write, Grep, Glob, Task, AskUserQuestion]
argument-hint: "<description> [--constitution <id>] [--constitution-first] [--domain <type>]"
---

# /design:solution - Create Solution Design

Create comprehensive technical solution designs with optional constitution-first governance for projects requiring structured decision frameworks and compliance validation.

## Overview

The `solution` command creates detailed solution designs using DEVB methodology:

- **Standard Mode**: Design → Emulate → Validate → Build workflow
- **Constitution-First Mode**: Constitution → Design → Spec-Kit Workflow → Build
- **From Existing Constitution**: Apply governance to new design

## Execution Steps

### Step 1: Determine Design Approach

**Ask:** "How would you like to create this solution design?"

**Option A: Standard DEVB** (Default - Fast)

- Create design specification immediately
- No governance constraints
- Flexible architecture decisions
- **Use when**: Prototyping, MVPs, internal tools, experimental projects
- **Time**: 5-10 minutes

**Option B: Constitution-First** (Recommended for Production)

- Define governance principles first
- Create design within constitution constraints
- Automatic compliance validation
- **Use when**: Production systems, regulated industries, team projects, client work
- **Time**: 15-25 minutes

**Option C: Use Existing Constitution**

- Apply existing governance framework
- Link design to constitution
- Inherit principles and constraints
- **Use when**: Adding features to existing system, organizational standards
- **Time**: 5-10 minutes

### Step 2a: Standard DEVB Design Creation

**For Option A (Standard Mode):**

**2.1 Gather Requirements**

Ask user for design details:

**Problem Statement** (Required):
"What problem are you solving?" (1-3 sentences)

Example: "We need a real-time notification system that can handle 100k concurrent connections with <100ms latency for mobile app users."

**Functional Requirements** (Required):
"What must the system do?" (5-10 bullet points)

Example:

- Send push notifications to iOS and Android
- Support in-app notifications with read/unread status
- Enable email fallback for offline users
- Allow notification preferences per user
- Track delivery and open rates

**Non-Functional Requirements** (Required):
"What are the performance, security, and scalability needs?"

Example:

- Handle 100k concurrent WebSocket connections
- <100ms notification delivery (p95)
- 99.9% uptime SLA
- End-to-end encryption for sensitive notifications
- GDPR compliance for user data

**Constraints** (Optional):
"Any technology or budget constraints?"

Example:

- Must use existing AWS infrastructure
- Max $5k/month infrastructure cost
- Support legacy REST API integration

**2.2 Create Design via API**

Call the design specification API:

```bash
curl -X POST http://localhost:3000/api/design/specifications \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "{workspace_id}",
    "title": "{solution_title}",
    "description": "{problem_statement}",
    "requirements": {
      "functional": [{requirements_array}],
      "non_functional": [{nfr_array}],
      "constraints": [{constraints_array}]
    },
    "created_by": "{user_id}"
  }'
```

### Step 2b: Constitution-First Design Creation

**For Option B (Constitution-First):**

**2.1 Create Constitution Interactively**

Guide user through constitution creation:

**Project Overview:**

- Project name: "{name}"
- Description: "{1-2 sentence description}"
- Domain: api | event-driven | graphql | saas | mobile | general

**Core Principles** (3-5 principles):
Ask: "What are your core principles?"

Examples:

1. "Security First - All data encrypted, zero-trust architecture"
2. "Performance - API response time <200ms, 99.99% uptime"
3. "Developer Experience - Well-documented, easy to use APIs"
4. "Cost Efficiency - Optimize for <$10k/month infrastructure"
5. "Scalability - Horizontal scaling, 1M+ users supported"

**Constraints** (3-5 hard rules):
Ask: "What are your hard constraints?"

Examples:

1. "No direct database access from frontend" (architecture)
2. "All APIs must require authentication" (security)
3. "Data at rest must be encrypted with AES-256" (security)
4. "API response time must be <500ms p95" (performance)
5. "Use PostgreSQL for primary database" (technology)

**Quality Gates** (3-5 gates):
Ask: "What quality gates must be met?"

Examples:

1. "Test coverage >80%" (automated: yes)
2. "Zero critical security vulnerabilities" (automated: yes)
3. "API documentation coverage 100%" (automated: yes)
4. "Performance tests pass (load, stress, spike)" (automated: yes)
5. "Code review approved by 2+ engineers" (automated: no)

**Technology Stack:**
Ask: "What technologies are preferred/required?"

- Languages: TypeScript, Python, Go, Java, etc.
- Frameworks: React, Next.js, FastAPI, Express, etc.
- Databases: PostgreSQL, MySQL, MongoDB, Redis, etc.
- Cloud: AWS, GCP, Azure, DigitalOcean, etc.

**2.2 Create Constitution via API**

```bash
curl -X POST http://localhost:3000/api/constitutions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{project_name}",
    "description": "{description}",
    "principles": [
      {"title": "Security First", "description": "...", "priority": "must"},
      {"title": "Performance", "description": "...", "priority": "must"}
    ],
    "constraints": [
      {"category": "architecture", "rule": "...", "enforcement": "hard"},
      {"category": "security", "rule": "...", "enforcement": "hard"}
    ],
    "quality_gates": [
      {"name": "Test Coverage", "criteria": ">80%", "automated": true},
      {"name": "Security Scan", "criteria": "zero critical", "automated": true}
    ],
    "preferred_stack": {
      "languages": ["TypeScript", "Python"],
      "frameworks": ["Next.js", "FastAPI"],
      "databases": ["PostgreSQL", "Redis"],
      "cloud": ["AWS"]
    },
    "created_by": "{user_id}"
  }'
```

**2.3 Create Design with Constitution**

```bash
curl -X POST http://localhost:3000/api/specifications/designs/with-constitution \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "{workspace_id}",
    "project_name": "{project_name}",
    "description": "{description}",
    "domain": "{domain}",
    "user_id": "{user_id}",
    "constitution_template": null
  }'
```

This will:

1. Create constitution first
2. Create design specification
3. Link constitution to design
4. Initialize spec-kit workflow
5. Return constitution ID, design ID, and workflow ID

### Step 2c: Use Existing Constitution

**For Option C (Existing Constitution):**

**2.1 List Available Constitutions**

```bash
curl -X GET http://localhost:3000/api/constitutions
```

Display:

```
Available Constitutions:

1. const-abc-123: SaaS Best Practices
   - Principles: 5 (Security, Performance, Scalability, Developer Experience, Cost)
   - Constraints: 8 hard rules
   - Used by: 3 projects

2. const-def-456: Healthcare HIPAA Compliance
   - Principles: 6 (Patient Privacy, Data Security, Audit Trail, BAA, Encryption, Compliance)
   - Constraints: 12 hard rules
   - Used by: 2 projects

3. const-ghi-789: Fintech PCI-DSS
   - Principles: 7 (Payment Security, PCI Compliance, Fraud Detection, Encryption, Audit, SOC2, Zero Trust)
   - Constraints: 15 hard rules
   - Used by: 1 project
```

**2.2 Select Constitution**
Ask: "Which constitution would you like to use? (1-{count})"

**2.3 Create Design with Constitution**

```bash
curl -X POST http://localhost:3000/api/design/specifications \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "{workspace_id}",
    "title": "{solution_title}",
    "description": "{problem_statement}",
    "requirements": {...},
    "constitution_id": "{selected_constitution_id}",
    "created_by": "{user_id}"
  }'
```

Then link:

```bash
curl -X POST http://localhost:3000/api/constitutions/{constitution_id}/designs/{design_id}/link \
  -H "Content-Type: application/json" \
  -d '{
    "is_primary": true,
    "override_principles": []
  }'
```

### Step 3: Display Design Summary

Show comprehensive design creation summary:

```
✅ Solution Design Created Successfully!

Design ID: {design_id}
Design Name: {solution_title}
Created: {timestamp}

📋 DESIGN OVERVIEW

Problem Statement:
{problem_statement}

Functional Requirements ({count}):
1. {requirement_1}
2. {requirement_2}
3. {requirement_3}
...

Non-Functional Requirements ({count}):
Performance:
  • API response time: <500ms (p95)
  • Throughput: 10,000 req/sec
  • Uptime: 99.9% SLA

Security:
  • OAuth 2.0 + JWT authentication
  • AES-256 encryption at rest
  • TLS 1.3 for data in transit
  • Rate limiting: 1000 req/hour per user

Scalability:
  • Horizontal scaling with auto-scaling
  • Support 1M+ concurrent users
  • Multi-region deployment

Constraints ({count}):
• Technology: AWS infrastructure only
• Budget: $10k/month maximum
• Timeline: 8 weeks to MVP

═══════════════════════════════════════════════════════════
CONSTITUTION GOVERNANCE (if constitution-first)
═══════════════════════════════════════════════════════════

Constitution ID: {constitution_id}
Constitution Name: {constitution_name}

🔑 Core Principles ({count}):
1. [MUST] Security First
   → All data encrypted at rest and in transit
   → Zero-trust architecture
   → Regular security audits

2. [MUST] Performance Excellence
   → API response <200ms (p95)
   → 99.99% uptime target
   → Automated performance testing

3. [SHOULD] Developer Experience
   → Comprehensive API documentation
   → Easy local development setup
   → Clear error messages

⚠️ Critical Constraints ({count}):
1. [HARD] No direct database access from frontend
2. [HARD] All APIs require authentication
3. [HARD] Data at rest encrypted with AES-256
4. [SOFT] Prefer PostgreSQL over MySQL

✓ Quality Gates ({count}):
1. Test coverage >80% ✓ Automated
2. Zero critical vulnerabilities ✓ Automated
3. API documentation 100% ✓ Automated
4. Code review by 2+ engineers ✗ Manual

💻 Preferred Technology Stack:
Languages: TypeScript, Python
Frameworks: Next.js, FastAPI, React
Databases: PostgreSQL, Redis
Cloud: AWS (ECS, RDS, ElastiCache, S3)
CI/CD: GitHub Actions

═══════════════════════════════════════════════════════════
SPEC-KIT WORKFLOW INITIALIZED (if constitution-first)
═══════════════════════════════════════════════════════════

Workflow ID: {workflow_id}
Current Phase: Clarify (20% complete)

Workflow Progression:
Constitution ✓ → Clarify → Analyze → Specify → Plan → Tasks → Implement

Next Steps in Workflow:
1. /spec-kit:specify {design_id}
   → Create detailed specification with user stories

2. /spec-kit:validate {design_id}
   → Validate specification for completeness and compliance

3. /spec-kit:plan {design_id}
   → Generate technical implementation plan

4. /spec-kit:tasks {design_id}
   → Break down into actionable tasks

═══════════════════════════════════════════════════════════
IMMEDIATE NEXT STEPS
═══════════════════════════════════════════════════════════

✨ Recommended Actions:

**For Standard DEVB:**
1. Emulate design (test without building):
   → /design:emulate {design_id}

2. Validate from 4 perspectives (Security, Performance, Cost, UX):
   → /design:validate {design_id}

3. Generate comprehensive specification:
   → /design:spec {design_id} --format all

**For Constitution-First:**
1. Create detailed specification:
   → /spec-kit:specify {design_id}

2. Validate specification:
   → /spec-kit:validate {design_id} --mode all

3. Generate implementation plan:
   → /spec-kit:plan {design_id}

4. Generate task breakdown:
   → /spec-kit:tasks {design_id}

5. Generate final spec package:
   → /design:spec {design_id} --include-spec-kit --format all

📁 Design Stored:
• Database: design_specifications table (ID: {design_id})
• Constitution linked: Yes (ID: {constitution_id})
• Spec-kit workflow: Active (ID: {workflow_id})
• Next phase: Specify (run /spec-kit:specify)

🎯 Quality Checklist:
Before implementation, ensure:
□ Constitution compliance validated
□ Specification generated and reviewed
□ Implementation plan created
□ Task breakdown with estimates
□ Architecture diagrams created
□ API contracts defined (OpenAPI/AsyncAPI)
□ Test strategy documented
□ Team sign-off obtained
```

### Step 4: Optional Actions

**Ask:** "Would you like to proceed with next steps?"

**Available Actions:**

1. **Start Spec-Kit Workflow** (if constitution-first)
   - Run /spec-kit:specify to create detailed specification

2. **Emulate Design** (if standard DEVB)
   - Test design before building

3. **Validate Design** (if standard DEVB)
   - AI validation from Security, Performance, Cost, UX perspectives

4. **Generate Specification**
   - Create comprehensive documentation

5. **View Constitution Details** (if linked)
   - See full governance framework

6. **Update Design**
   - Make changes to requirements or constraints

## Advanced Features

### Use Constitution Template

```bash
/design:solution "Project Name" --constitution-template saas
```

Use built-in template (saas, api, microservices, mobile, fintech, healthtech, ecommerce, event-driven, enterprise, startup).

API call:

```bash
curl -X POST http://localhost:3000/api/constitutions/templates/saas/apply \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Project Name",
    "description": "Description",
    "created_by": "user-id"
  }'
```

### Specify Domain for Better Defaults

```bash
/design:solution "API Gateway" --domain api
```

Domains: api, event-driven, graphql, saas, mobile, general

### Link Multiple Constitutions

```bash
/design:solution "Project" --constitution org-const-123 --constitution team-const-456
```

Apply organizational and team-level governance.

### Override Constitution Principles

```bash
/design:solution "Project" --constitution const-123 --override "Use MySQL instead of PostgreSQL"
```

Override specific principles while maintaining others.

## Error Handling

**If constitution not found:**

```
❌ Constitution not found: {constitution_id}

Available constitutions:
1. const-abc-123: SaaS Best Practices
2. const-def-456: Healthcare HIPAA
3. const-ghi-789: Fintech PCI-DSS

Select one or create new:
  /spec-kit:constitution "New Constitution"
```

**If design creation fails:**

```
❌ Design creation failed: {error_message}

Common causes:
1. Invalid workspace ID
2. Missing required fields
3. Database connection issue

Try:
1. Check workspace exists: /workspace/list
2. Simplify requirements and try again
3. Check backend logs: docker logs shopify-backend
```

**If constitution validation fails:**

```
⚠️ Design violates constitution constraints

Constitution: {constitution_name}
Violations ({count}):
1. [CRITICAL] Using MySQL but PostgreSQL is required
2. [MAJOR] No encryption specified for data at rest
3. [MINOR] API response time target exceeds <500ms requirement

Would you like to:
1. Override violations (requires justification)
2. Update design to comply
3. Modify constitution constraints
```

## Example Usage

### Example 1: Quick Prototype (Standard)

```
User: /design:solution "Chat feature for mobile app"
Assistant: Creating standard DEVB design...
  Problem statement: {collected}
  Requirements: {collected}
Assistant: ✅ Design created! design-abc-123
  Next: /design:emulate design-abc-123
```

### Example 2: Production System (Constitution-First)

```
User: /design:solution "Payment Processing System" --constitution-first --domain fintech
Assistant: Let's create a constitution first for governance...
  Core principles: {5 collected}
  Constraints: {8 collected}
  Quality gates: {5 collected}
  Tech stack: {collected}
Assistant: ✅ Constitution created! const-def-456
Assistant: Creating design with constitution...
Assistant: ✅ Design created! design-ghi-789
  Constitution compliance: 100%
  Next: /spec-kit:specify design-ghi-789
```

### Example 3: Use Existing Governance

```
User: /design:solution "User Profile Service" --constitution const-abc-123
Assistant: Using existing constitution: SaaS Best Practices
  Inheriting: 5 principles, 8 constraints
  Tech stack: TypeScript, Next.js, PostgreSQL, AWS
Assistant: Creating design...
Assistant: ✅ Design created! design-xyz-101
  Constitution compliance: 95% (1 warning)
  Warning: API timeout not specified (recommend <500ms)
```

### Example 4: Template-Based

```
User: /design:solution "Healthcare Portal" --constitution-template healthtech
Assistant: Applying Healthcare HIPAA template...
  Principles: Patient Privacy, Data Security, Audit Trail, BAA, Encryption, Compliance
  Constraints: 12 HIPAA-specific rules
  Quality gates: Security scan, Privacy impact assessment, Compliance audit
Assistant: ✅ Constitution applied! const-health-456
Assistant: Creating design...
Assistant: ✅ Design created! design-health-789
  HIPAA compliance: 100%
  Next: /spec-kit:specify design-health-789
```

## Success Criteria

✅ Design created with complete requirements
✅ Constitution linked (if specified)
✅ Spec-kit workflow initialized (if constitution-first)
✅ Design ID and constitution ID returned
✅ User understands next steps in workflow

## Notes

- **Standard DEVB** is fastest for prototypes and MVPs (5-10 min)
- **Constitution-first** is recommended for production systems (15-25 min)
- Constitutions can be reused across multiple designs
- Constitution compliance validated automatically
- 10 built-in templates available for common domains
- Multiple constitutions can be linked (organizational + team + project level)
- Principles can be overridden with justification
- Spec-kit workflow provides structured approach from design to implementation
- All designs versioned in database

## Integration with Workflows

### Standard DEVB Workflow

```
Solution → Emulate → Validate → Spec → Implement
```

### Constitution-First Workflow

```
Constitution → Solution → Specify → Validate → Plan → Tasks → Implement
```

### Hybrid Workflow

```
Solution → Constitution (retroactive) → Validate → Spec → Implement
```

Use constitution-first for:

- Production systems
- Regulated industries (healthcare, fintech, government)
- Team projects with shared standards
- Client work requiring governance
- Long-term maintainable systems

Use standard DEVB for:

- Prototypes and MVPs
- Internal tools
- Experimental projects
- Solo developer projects
- Time-sensitive initiatives
