---
description: Validate specifications for completeness, consistency, and feasibility with multiple validation modes
allowed-tools: [Bash, Read, Write, AskUserQuestion]
argument-hint: "<design-id> [--mode <clarify|analyze|checklist|all>] [--fix-issues]"
---

# /spec-kit:validate - Validate Specifications

Comprehensive specification validation to ensure completeness, consistency, and feasibility before implementation.

## Overview

The `validate` command provides three validation approaches:

- **Clarify Mode**: Detect underspecified requirements and ambiguities
- **Analyze Mode**: Deep analysis for consistency, feasibility, and risks
- **Checklist Mode**: Systematic QA checklist evaluation
- **All Modes**: Run all three validations sequentially

## Prerequisites

**Required:** Specification must exist

- Run `/spec-kit:specify <design-id>` before validation
- Workflow must be in 'specify' phase or later

## Execution Steps

### Step 1: Verify Specification Exists

Check workflow status:

```bash
curl -X GET http://localhost:3000/api/specifications/designs/{design_id}/workflow
```

Verify current phase:

- ❌ If phase = 'clarify' or earlier → Must complete specify first
- ✅ If phase = 'specify' or later → Proceed with validation
- ✅ If phase = 'plan' or 'tasks' → Can re-validate

If specification doesn't exist:

```
❌ No specification found for design {design_id}

Current workflow phase: {current_phase}
Required phase: specify or later

Generate specification first:
  /spec-kit:specify {design_id}
```

### Step 2: Choose Validation Mode

**Ask:** "Which validation mode would you like to run?"

**Mode Options:**

1. **Clarify** - Find underspecified requirements
   - Detects ambiguous language ("might", "could", "maybe")
   - Identifies missing details and edge cases
   - Highlights vague acceptance criteria
   - Suggests clarifying questions
   - **Use when**: Requirements feel incomplete or unclear

2. **Analyze** - Deep consistency and feasibility analysis
   - Checks for conflicting requirements
   - Validates technical feasibility
   - Identifies performance bottlenecks
   - Detects security vulnerabilities
   - Assesses scalability concerns
   - **Use when**: Need comprehensive technical review

3. **Checklist** - Systematic QA checklist
   - Validates against best practices
   - Checks completeness of all sections
   - Verifies API contract consistency
   - Ensures test coverage considerations
   - Reviews documentation quality
   - **Use when**: Final pre-implementation quality gate

4. **All** - Run all three modes sequentially
   - Comprehensive validation with all checks
   - Prioritized findings report
   - **Use when**: First-time validation or major changes

### Step 3: Run Validation via API

**For Clarify Mode:**

```bash
curl -X POST http://localhost:3000/api/spec-kit/clarify \
  -H "Content-Type: application/json" \
  -d '{
    "feature": "{feature_name}",
    "requirements": "{requirements_text}"
  }'
```

**For Analyze Mode:**

```bash
curl -X POST http://localhost:3000/api/spec-kit/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "feature": "{feature_name}",
    "requirements": "{requirements_text}"
  }'
```

**For Checklist Mode:**

```bash
curl -X POST http://localhost:3000/api/spec-kit/checklist \
  -H "Content-Type: application/json" \
  -d '{
    "feature": "{feature_name}",
    "requirements": "{requirements_text}"
  }'
```

**For All Modes (via workflow validation):**

```bash
curl -X POST http://localhost:3000/api/specifications/designs/{design_id}/validate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "all",
    "include_constitution_check": true
  }'
```

The API will:

1. Load specification from database
2. Call spec-kit CLI validation commands
3. Parse validation results
4. Store findings in spec_kit_validations table
5. Calculate confidence score
6. Return prioritized findings

### Step 4: Display Validation Results

Show comprehensive validation report:

```
✅ Validation Complete: {mode} Mode

Design ID: {design_id}
Validation ID: {validation_id}
Execution Time: {execution_time_ms}ms
Overall Status: {pass|warning|fail}

📊 VALIDATION SUMMARY

Confidence Score: {score}/100
Status: {status}

Findings Breakdown:
🔴 Critical Issues: {critical_count}
🟠 Major Issues: {major_count}
🟡 Minor Issues: {minor_count}
🔵 Suggestions: {suggestion_count}

═══════════════════════════════════════════════════════════
CLARIFY MODE RESULTS (Underspecified Requirements)
═══════════════════════════════════════════════════════════

🔴 CRITICAL: Ambiguous Performance Requirement
Location: Non-Functional Requirements, Section 3.2
Issue: "The system should be fast" - No measurable target specified

❓ Clarifying Questions:
1. What is the target API response time? (e.g., <500ms p95)
2. What is the expected throughput? (e.g., 1000 req/sec)
3. Under what load conditions? (e.g., 10k concurrent users)

Recommendation: Specify concrete performance targets with percentiles

───────────────────────────────────────────────────────────

🟠 MAJOR: Missing Edge Case Handling
Location: User Story 3 - "User can search products"
Issue: No specification for empty search results or invalid queries

❓ Clarifying Questions:
1. What message is displayed for no results?
2. How are malformed queries handled?
3. Is fuzzy search or autocorrect enabled?
4. What happens with special characters in search?

Recommendation: Add edge case user stories

───────────────────────────────────────────────────────────

🟡 MINOR: Vague Authentication Requirement
Location: Security Requirements, Section 5.1
Issue: "Users must log in" - Authentication method not specified

❓ Clarifying Questions:
1. Which auth method? (OAuth 2.0, JWT, Session-based, SAML)
2. Support social login? (Google, GitHub, etc.)
3. Multi-factor authentication required?
4. Token expiration policy?

Recommendation: Specify exact authentication mechanism and flows

───────────────────────────────────────────────────────────

Clarify Summary:
• 12 ambiguous requirements found
• 8 missing edge cases identified
• 15 clarifying questions generated
• 6 sections need more detail

═══════════════════════════════════════════════════════════
ANALYZE MODE RESULTS (Consistency & Feasibility)
═══════════════════════════════════════════════════════════

🔴 CRITICAL: Conflicting Requirements
Location: Requirement 2.3 vs 4.5
Conflict:
  - Req 2.3: "All data must be encrypted at rest using AES-256"
  - Req 4.5: "Database queries must return in <50ms"

Analysis: Full database encryption may impact query performance.
AES-256 encryption/decryption overhead: ~20-40ms per query.
Meeting both requirements simultaneously may be infeasible.

Recommendation:
- Use transparent database encryption (TDE) for at-rest encryption
- Encrypt sensitive columns only (selective field encryption)
- Review performance requirements vs security requirements
- Consider caching layer to mitigate performance impact

───────────────────────────────────────────────────────────

🟠 MAJOR: Scalability Bottleneck
Location: Data Model Design
Issue: Single PostgreSQL instance specified for 100k concurrent users

Analysis:
- PostgreSQL max connections: ~500 with default config
- 100k concurrent users requires connection pooling
- Single instance is single point of failure
- Write operations will bottleneck on single master

Recommendation:
- Implement read replicas for read-heavy operations
- Use connection pooler (PgBouncer or pgpool)
- Consider sharding strategy for horizontal scaling
- Add load balancer in front of database cluster

───────────────────────────────────────────────────────────

🟠 MAJOR: Security Vulnerability
Location: API Design - File Upload Endpoint
Issue: POST /upload accepts any file type with no validation

Risk Assessment:
- Malicious file upload (malware, scripts)
- Storage exhaustion attacks
- Code injection via file processing
- OWASP A03:2021 - Injection

Recommendation:
- Whitelist allowed file extensions
- Validate MIME types server-side
- Implement file size limits (e.g., 10MB max)
- Scan uploads with antivirus
- Store uploads outside web root
- Use Content Security Policy headers

───────────────────────────────────────────────────────────

🟡 MINOR: Missing Error Handling
Location: Payment Processing Flow
Issue: No specification for payment gateway timeout handling

Analysis:
- Stripe API timeout: 80 seconds default
- No retry logic specified
- Missing idempotency key usage
- Duplicate charge risk

Recommendation:
- Implement exponential backoff retry (3 attempts)
- Use idempotency keys for all payment requests
- Add webhook for async payment confirmation
- Store payment attempt logs for debugging

───────────────────────────────────────────────────────────

Analyze Summary:
• 3 conflicting requirements detected
• 5 technical feasibility concerns
• 8 security vulnerabilities identified
• 4 scalability bottlenecks found
• 6 performance risks highlighted

═══════════════════════════════════════════════════════════
CHECKLIST MODE RESULTS (Systematic QA)
═══════════════════════════════════════════════════════════

📋 COMPLETENESS CHECK

✓ User Stories Defined: 12/12 complete
✓ Functional Requirements: 18/18 complete
✓ Non-Functional Requirements: 8/10 complete
  ⚠ Missing: Disaster recovery requirements
  ⚠ Missing: Compliance requirements (GDPR, CCPA)
✓ API Endpoints Documented: 15/15 complete
✓ Data Models Defined: 6/6 tables complete
✗ Error Handling Specified: 8/15 endpoints (53%)
✗ Test Scenarios Defined: 0 scenarios (0%)

Completeness Score: 72/100

───────────────────────────────────────────────────────────

📋 API CONTRACT CONSISTENCY

✓ All endpoints have HTTP methods specified
✓ Request schemas defined with examples
✓ Response schemas defined with status codes
✗ Missing error response schemas: 7/15 endpoints
✗ Rate limiting not documented
✗ Authentication requirements inconsistent across endpoints
  - 8 endpoints require auth
  - 7 endpoints don't specify auth requirements

Consistency Score: 65/100

───────────────────────────────────────────────────────────

📋 SECURITY CHECKLIST

✓ Authentication mechanism specified (OAuth 2.0)
✓ Authorization roles defined (user, admin)
✗ Input validation missing for 12/15 endpoints
✗ SQL injection prevention not documented
✗ XSS protection strategy not specified
✗ CSRF tokens not mentioned
✗ Rate limiting per user/IP not configured
✗ Secrets management strategy missing

Security Score: 35/100 ⚠️ NEEDS IMPROVEMENT

───────────────────────────────────────────────────────────

📋 PERFORMANCE CHECKLIST

✓ Database indexes specified for foreign keys
✗ Query optimization strategy missing
✗ Caching strategy not defined
✗ Pagination not specified for list endpoints
✗ CDN usage not documented
✗ Asset optimization not mentioned

Performance Score: 25/100 ⚠️ NEEDS IMPROVEMENT

───────────────────────────────────────────────────────────

📋 TESTING CHECKLIST

✗ Unit test coverage target not specified
✗ Integration test scenarios missing
✗ E2E test plan not defined
✗ Load testing requirements not specified
✗ Security testing (OWASP Top 10) not mentioned
✗ Accessibility testing (WCAG) not included

Testing Score: 0/100 ⚠️ CRITICAL

───────────────────────────────────────────────────────────

📋 DOCUMENTATION CHECKLIST

✓ API documentation format specified (OpenAPI 3.0)
✓ README structure outlined
✗ Deployment guide missing
✗ Architecture diagrams not generated
✗ Database ERD not created
✗ Runbook for common operations missing

Documentation Score: 40/100

───────────────────────────────────────────────────────────

Checklist Summary:
• Overall Quality Score: 48/100
• 6 categories evaluated
• 28 checks passed
• 34 checks failed
• High-priority gaps: Security, Testing, Performance

═══════════════════════════════════════════════════════════
CONSTITUTION COMPLIANCE (if constitution linked)
═══════════════════════════════════════════════════════════

Constitution: SaaS Best Practices (const-abc-123)
Compliance Score: 68/100

✓ Passed Checks (8):
  ✓ Authentication required (OAuth 2.0 specified)
  ✓ Database backups mentioned
  ✓ HTTPS enforced
  ✓ Logging specified
  ✓ Error handling present (partial)
  ✓ API versioning included
  ✓ TypeScript as primary language
  ✓ PostgreSQL as database

⚠ Warnings (5):
  ⚠ Rate limiting not explicitly configured
  ⚠ Multi-tenancy isolation not detailed
  ⚠ Scalability targets below recommended (10k vs 50k users)
  ⚠ Monitoring/observability strategy incomplete
  ⚠ CI/CD pipeline not specified

❌ Violations (3):
  ❌ No encryption specified for data at rest (CRITICAL)
  ❌ Missing disaster recovery plan (HIGH)
  ❌ Using MySQL instead of preferred PostgreSQL for cache (MEDIUM)

Recommendations:
1. Add AES-256 encryption for sensitive data (CRITICAL)
2. Define RPO/RTO targets and backup strategy (HIGH)
3. Replace MySQL cache with Redis per constitution (MEDIUM)
4. Add explicit rate limiting configuration
5. Document multi-tenant isolation mechanism

═══════════════════════════════════════════════════════════
PRIORITIZED ACTION ITEMS
═══════════════════════════════════════════════════════════

🔴 MUST FIX (Critical - Block Implementation):
1. Resolve conflicting encryption vs performance requirements
2. Add data-at-rest encryption specification
3. Define comprehensive security strategy (input validation, XSS, CSRF)
4. Specify test coverage targets and test plan
5. Add disaster recovery requirements

🟠 SHOULD FIX (Major - High Priority):
1. Add scalability strategy (read replicas, connection pooling)
2. Specify error handling for all API endpoints
3. Define rate limiting per user/IP
4. Add missing edge case handling
5. Create architecture and database diagrams
6. Fix file upload security vulnerability

🟡 NICE TO FIX (Minor - Medium Priority):
1. Clarify ambiguous performance requirements with metrics
2. Add caching strategy documentation
3. Specify pagination for list endpoints
4. Add deployment and runbook documentation
5. Define monitoring/observability strategy
6. Add compliance requirements (GDPR, CCPA)

🔵 SUGGESTIONS (Optional - Low Priority):
1. Consider fuzzy search implementation
2. Add social login options
3. Implement CDN for static assets
4. Add automated accessibility testing
5. Create OpenAPI examples for all endpoints

═══════════════════════════════════════════════════════════
NEXT STEPS
═══════════════════════════════════════════════════════════

Recommended Path Forward:

1. Address Critical Issues First (Est. 16 hours)
   - Resolve encryption vs performance conflict
   - Add comprehensive security specification
   - Define test strategy and coverage targets

2. Fix Major Issues (Est. 12 hours)
   - Add scalability plan
   - Complete API error handling
   - Add missing diagrams

3. Clarify Ambiguities (Est. 4 hours)
   - Answer clarifying questions
   - Update specification with concrete metrics
   - Add edge case handling

4. Re-validate (Est. 1 hour)
   - Run validation again after fixes
   - Verify all critical issues resolved
   - Ensure compliance score >80

5. Proceed to Planning (Est. 0 hours)
   - Once validation passes, generate implementation plan:
     /spec-kit:plan {design_id}

📁 Export Options:
• View full report: /spec-kit:validate {design_id} --export ./validation-report.md
• Fix issues automatically: /spec-kit:validate {design_id} --fix-issues
• Re-run single mode: /spec-kit:validate {design_id} --mode clarify
```

### Step 5: Optional Actions

**Ask:** "Would you like to take any actions?"

**Available Actions:**

1. **Fix Issues Automatically** (if supported)
   - Auto-generate missing error schemas
   - Add basic input validation
   - Create skeleton test files
   - Generate architecture diagrams

2. **Export Validation Report**
   - Save to Markdown file
   - Export to PDF
   - Share with team

3. **Update Specification**
   - Address findings one-by-one
   - Re-run validation after updates

4. **Proceed to Planning**
   - If validation passes (score >70)
   - Generate implementation plan

5. **Request Constitution Review**
   - If compliance score low
   - Update constitution or override specific rules

## Advanced Features

### Run Specific Mode

```bash
/spec-kit:validate <design-id> --mode clarify
```

Single mode validation for faster feedback.

### Auto-Fix Issues

```bash
/spec-kit:validate <design-id> --fix-issues
```

Automatically fix common issues:

- Add missing error schemas
- Generate basic input validation
- Create test file skeletons
- Add pagination to list endpoints

API call:

```bash
curl -X POST http://localhost:3000/api/specifications/designs/{design_id}/validate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "all",
    "auto_fix": true
  }'
```

### Export Validation Report

```bash
/spec-kit:validate <design-id> --export ./reports/validation.md
```

Export comprehensive report to file.

### Continuous Validation

```bash
/spec-kit:validate <design-id> --watch
```

Re-run validation on specification changes (useful during editing).

### Constitution-Only Validation

```bash
/spec-kit:validate <design-id> --constitution-only
```

Validate only against linked constitution without spec-kit checks.

## Validation Modes Deep Dive

### Clarify Mode

**What it does:**

- Analyzes natural language for ambiguity
- Detects vague terms ("might", "should", "fast", "soon")
- Identifies missing details in user stories
- Highlights undefined edge cases
- Generates clarifying questions

**Example Findings:**

```
🟠 Ambiguous: "The system should handle errors gracefully"
❓ Questions:
  - What error types? (validation, network, database)
  - What is the retry strategy?
  - How are errors logged?
  - What user-facing error messages?
```

**When to use:**

- Requirements gathering phase
- Before technical design
- When stakeholders aren't technical
- First-time validation

### Analyze Mode

**What it does:**

- Deep technical analysis
- Consistency checking across requirements
- Feasibility assessment
- Security vulnerability detection
- Performance bottleneck identification
- Scalability concern highlighting

**Example Findings:**

```
🔴 Conflict Detected:
  Req 3.1: "Support 1M daily active users"
  Req 3.2: "Deploy on single t2.micro EC2 instance"

  Analysis: t2.micro has 1GB RAM, ~1 vCPU
  Capacity: ~100 concurrent users max

  Recommendation: Use autoscaling group with m5.large instances
```

**When to use:**

- After clarification complete
- Before implementation starts
- Major architecture changes
- Pre-production review

### Checklist Mode

**What it does:**

- Systematic best practices check
- Completeness verification
- Standards compliance (REST, OpenAPI)
- Security checklist (OWASP)
- Testing coverage check
- Documentation quality

**Example Findings:**

```
📋 Security Checklist: 5/12 passed

✓ Authentication present
✗ Input validation missing
✗ SQL injection protection not documented
✗ XSS prevention not specified
✗ CSRF tokens missing
```

**When to use:**

- Final quality gate before implementation
- Pre-deployment checklist
- Compliance audits
- Stakeholder sign-off

## Error Handling

**If specification not found:**

```
❌ No specification found for design {design_id}

Available designs with specifications:
1. design-abc-123: E-commerce Platform (specify phase)
2. design-def-456: Mobile App Backend (plan phase)
3. design-ghi-789: Analytics Dashboard (tasks phase)

Generate specification:
  /spec-kit:specify {design_id}
```

**If validation fails to run:**

```
❌ Validation failed to execute: {error_message}

Common causes:
1. Specification file corrupted
2. spec-kit CLI not available
3. Workspace permission issues

Try:
1. Check spec-kit health: curl http://localhost:3000/api/spec-kit/health
2. Regenerate spec: /spec-kit:specify {design_id}
3. Check logs: docker logs shopify-backend
```

**If score too low to proceed:**

```
⚠️ Validation score below threshold: {score}/100

Minimum score to proceed: 70/100
Current blockers: {blocker_count} critical issues

Must fix before proceeding to plan phase:
1. {critical_issue_1}
2. {critical_issue_2}
3. {critical_issue_3}

Would you like to:
1. View detailed findings
2. Auto-fix common issues
3. Update specification manually
```

## Example Usage

### Example 1: First-time Validation

```
User: /spec-kit:validate design-abc-123 --mode all
Assistant: Running comprehensive validation (clarify + analyze + checklist)...
  Clarify: 12 ambiguities found
  Analyze: 3 conflicts, 5 risks detected
  Checklist: Overall score 48/100
Assistant: ⚠️ Validation found critical issues
  Must address 5 blockers before implementation
```

### Example 2: Quick Clarity Check

```
User: /spec-kit:validate design-def-456 --mode clarify
Assistant: Running clarify mode...
  15 clarifying questions generated
  8 sections need more detail
Assistant: ✅ Most requirements clear
  Minor clarifications needed in auth section
```

### Example 3: Final Quality Gate

```
User: /spec-kit:validate design-ghi-789 --mode checklist
Assistant: Running systematic QA checklist...
  Completeness: 92/100
  Security: 85/100
  Performance: 78/100
  Testing: 90/100
Assistant: ✅ Validation passed!
  Ready for implementation planning
  Run: /spec-kit:plan design-ghi-789
```

### Example 4: Auto-fix and Re-validate

```
User: /spec-kit:validate design-xyz-101 --fix-issues
Assistant: Auto-fixing common issues...
  ✓ Added error schemas to 7 endpoints
  ✓ Generated input validation for 12 endpoints
  ✓ Created test file skeletons
  ✓ Added pagination to 5 list endpoints
Assistant: Re-running validation...
  Previous score: 48/100
  New score: 72/100
  Ready to proceed!
```

## Success Criteria

✅ Validation executed successfully across selected modes
✅ Findings categorized by severity and priority
✅ Confidence score calculated (0-100)
✅ Actionable recommendations provided
✅ Constitution compliance checked (if applicable)
✅ Results stored in database
✅ User understands next steps (fix issues or proceed)

## Notes

- Validation can be run multiple times (iterative improvement)
- Results are versioned in spec_kit_validations table
- Auto-fix is conservative (only obvious improvements)
- Constitution compliance is automatic if design linked
- Validation results inform planning phase
- Critical issues block progression to plan/tasks phases
- Use validation as quality gate before implementation
- Share validation reports with stakeholders for sign-off

## Integration with Workflow

```
Constitution → Specify → **Validate** → Plan → Tasks → Implement
                            ↑             ↓
                            └─────────────┘
                          (iterate until valid)
```

Validation is the quality gate between specification and planning. The workflow won't progress to plan phase until validation score is acceptable (typically >70/100 or all critical issues resolved).
