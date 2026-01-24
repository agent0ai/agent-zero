---
description: Create Architecture Decision Records (ADRs) to document key technical decisions with context, consequences, and alternatives
argument-hint: "[--decision <description>] [--status <proposed|accepted|deprecated|superseded>] [--template <minimal|comprehensive>]"
allowed-tools: [Read, Write, Bash, Glob, Grep, AskUserQuestion]
---

# Architecture Decision Records (ADR) Command

## What This Command Does

This command helps you create, manage, and maintain Architecture Decision Records (ADRs) by:

- Documenting important architectural and technical decisions
- Capturing context, constraints, and rationale
- Evaluating alternatives with trade-off analysis
- Tracking consequences (positive and negative)
- Linking related ADRs and evolution over time
- Following industry-standard ADR formats

ADRs create an audit trail of technical decisions, making it easier to understand "why" decisions were made and enabling better future decision-making.

## Usage Examples

### Create New ADR (Interactive)

```bash
/architecture:adr
```

Interactive mode will guide you through creating a comprehensive ADR.

### Create ADR for Specific Decision

```bash
/architecture:adr --decision "Migrate from REST to GraphQL"
```

Create an ADR documenting the decision to adopt GraphQL.

### Create ADR with Status

```bash
/architecture:adr --decision "Use PostgreSQL for main database" --status accepted
```

Create an ADR that has already been accepted by the team.

### Create Minimal ADR

```bash
/architecture:adr --decision "Adopt TypeScript" --template minimal
```

Create a lightweight ADR with essential sections only.

### Deprecate Previous ADR

```bash
/architecture:adr --decision "Use MongoDB" --status deprecated
```

Mark an existing ADR as deprecated (when superseded by new decision).

## What is an ADR?

**Architecture Decision Record (ADR)** is a document that captures an important architectural decision made along with its context and consequences.

### When to Create an ADR

Create an ADR for decisions that:

- **Affect structure**: Changes to system components, layers, or modules
- **Impact multiple teams**: Decisions that cross team boundaries
- **Are hard to reverse**: Significant cost or effort to change later
- **Set precedent**: Establishes patterns others will follow
- **Involve trade-offs**: Multiple valid options with different pros/cons
- **Cost significant money**: Major infrastructure or licensing decisions
- **Address quality attributes**: Performance, security, scalability, maintainability

### When NOT to Create an ADR

Skip ADRs for:

- Trivial decisions easily reversed (code formatting, variable naming)
- Team-local decisions with no broader impact
- Obvious choices with no reasonable alternatives
- Implementation details that don't affect architecture
- Temporary workarounds or experiments

## ADR Format & Structure

### Standard ADR Template (Comprehensive)

```markdown
# ADR-[NUMBER]: [Short Title of Decision]

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: [YYYY-MM-DD]
**Decision Makers**: [Names/Roles]
**Consulted**: [Stakeholders consulted]
**Informed**: [Teams/individuals informed]

## Context

[Describe the problem, challenge, or opportunity that requires a decision]

**Background**:
- What is the current state?
- What problem are we trying to solve?
- What constraints do we have?

**Business Context**:
- Why does this matter to the business?
- What are the business goals or requirements?
- What is the timeline or urgency?

**Technical Context**:
- What is our current architecture?
- What technologies are we already using?
- What are the technical constraints?

## Decision

[State the decision clearly and concisely]

We will [action] because [primary reason].

**Specific Implementation**:
- Technology/approach chosen: [Details]
- Key configuration or setup: [Details]
- Integration points: [Details]

## Alternatives Considered

### Alternative 1: [Name]
**Description**: [Brief description]
**Pros**:
- [Advantage 1]
- [Advantage 2]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]

**Why Not Chosen**: [Rationale]

### Alternative 2: [Name]
[Same structure as Alternative 1]

### Alternative 3: [Name]
[Same structure as Alternative 1]

## Consequences

### Positive Consequences
- [Benefit 1]: [Description and impact]
- [Benefit 2]: [Description and impact]
- [Benefit 3]: [Description and impact]

### Negative Consequences
- [Trade-off 1]: [Description and mitigation plan]
- [Trade-off 2]: [Description and mitigation plan]
- [Risk 1]: [Description and mitigation plan]

### Neutral Consequences
- [Change 1]: [Description of neutral impact]
- [Change 2]: [Description of neutral impact]

## Compliance & Security

[If applicable - remove if not relevant]

- **Compliance Requirements**: [HIPAA, PCI-DSS, GDPR, SOC2, etc.]
- **Security Implications**: [Authentication, encryption, data protection]
- **Audit Requirements**: [Logging, monitoring, reporting]

## Costs & Resources

**One-Time Costs**:
- Development effort: [Estimate in hours/days]
- Migration effort: [If applicable]
- Training: [Team training required]
- Licensing: [One-time fees]

**Ongoing Costs**:
- Infrastructure: [Monthly/annual costs]
- Maintenance: [Ongoing effort required]
- Licensing: [Recurring fees]
- Support: [Vendor support costs]

**Total Cost of Ownership (3 years)**: [Estimate]

## Implementation Plan

1. **Phase 1**: [Initial implementation steps]
   - Timeline: [Estimate]
   - Owner: [Team/Person]

2. **Phase 2**: [Migration or rollout]
   - Timeline: [Estimate]
   - Owner: [Team/Person]

3. **Phase 3**: [Completion and cleanup]
   - Timeline: [Estimate]
   - Owner: [Team/Person]

## Success Metrics

**How we'll measure success**:
- [Metric 1]: [Target value and measurement method]
- [Metric 2]: [Target value and measurement method]
- [Metric 3]: [Target value and measurement method]

**Review Timeline**: Review this decision in [timeframe] to assess outcomes.

## Related Decisions

- **Supersedes**: [ADR-XXX] - [Brief description]
- **Related to**: [ADR-YYY] - [Brief description]
- **Superseded by**: [ADR-ZZZ] - [If applicable]

## References

- [Link to design document]
- [Link to research or benchmark]
- [Link to vendor documentation]
- [Link to related discussions or RFCs]

---

**Notes**:
- [Any additional context, caveats, or future considerations]
```

### Minimal ADR Template

```markdown
# ADR-[NUMBER]: [Short Title]

**Status**: [Proposed | Accepted]
**Date**: [YYYY-MM-DD]

## Context
[Brief description of the problem or decision needed]

## Decision
[Clear statement of what we decided to do]

## Consequences
**Pros**:
- [Benefit 1]
- [Benefit 2]

**Cons**:
- [Trade-off 1]
- [Trade-off 2]
```

## ADR Lifecycle

### Status Definitions

- **Proposed**: Decision is being considered, not yet accepted
- **Accepted**: Decision has been approved and is being implemented
- **Deprecated**: Decision is no longer recommended (but may still be in use)
- **Superseded**: Decision has been replaced by a newer ADR

### Status Transitions

```
Proposed → Accepted → [In Use] → Deprecated → Superseded
         ↓
      Rejected (document why, but don't delete)
```

## ADR Numbering & Organization

### Recommended Directory Structure

```
docs/
  architecture/
    decisions/
      0001-use-postgresql-for-primary-database.md
      0002-adopt-microservices-architecture.md
      0003-implement-graphql-api.md
      0004-choose-aws-over-gcp.md
      README.md (Index of all ADRs)
```

### Naming Convention

Format: `[4-digit-number]-[kebab-case-short-title].md`

Examples:

- `0001-use-react-for-frontend.md`
- `0012-migrate-to-kubernetes.md`
- `0025-adopt-event-driven-architecture.md`

### ADR Index (README.md)

```markdown
# Architecture Decision Records

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-use-postgresql.md) | Use PostgreSQL for Primary Database | Accepted | 2025-01-15 |
| [0002](0002-adopt-microservices.md) | Adopt Microservices Architecture | Accepted | 2025-01-20 |
| [0003](0003-implement-graphql.md) | Implement GraphQL API | Proposed | 2025-01-25 |
| [0004](0004-use-mongodb.md) | Use MongoDB for Analytics | Deprecated | 2024-12-10 |

## By Category

**Infrastructure**:
- ADR-0001: PostgreSQL
- ADR-0004: MongoDB (Deprecated)

**Architecture Patterns**:
- ADR-0002: Microservices

**API Design**:
- ADR-0003: GraphQL

## By Status

**Accepted**: 2
**Proposed**: 1
**Deprecated**: 1
**Superseded**: 0
```

## Business Value & ROI

### Knowledge Preservation

- **Problem**: Key decisions lost when team members leave
- **Solution**: ADRs create institutional memory
- **ROI**: 50% reduction in time spent answering "why did we do this?" questions

### Better Decision Making

- **Problem**: Repeating past mistakes or reconsidering settled decisions
- **Solution**: ADRs document context and alternatives considered
- **ROI**: Avoid $50K-$500K+ cost of reversing bad architectural decisions

### Faster Onboarding

- **Problem**: New team members don't understand system rationale
- **Solution**: ADRs provide historical context and learning resource
- **ROI**: Reduce onboarding time from 3 months to 4-6 weeks

### Compliance & Auditing

- **Problem**: Cannot prove security/compliance decisions to auditors
- **Solution**: ADRs provide audit trail for technical decisions
- **ROI**: Pass SOC2/HIPAA audits faster, avoid compliance penalties

### Stakeholder Communication

- **Problem**: Non-technical stakeholders don't understand technical choices
- **Solution**: ADRs explain business impact of technical decisions
- **ROI**: Better alignment, fewer conflicts, smoother approvals

## Success Metrics

### ADR Quality Checklist

- [ ] Clear, concise title that describes the decision
- [ ] Context section explains why decision is needed
- [ ] Decision statement is unambiguous
- [ ] At least 2-3 alternatives considered and documented
- [ ] Consequences (positive and negative) identified
- [ ] Costs estimated (one-time and ongoing)
- [ ] Implementation plan with timeline and owners
- [ ] Success metrics defined for review
- [ ] Related ADRs linked
- [ ] Status and date clearly marked

### Process Metrics

- [ ] ADR created before major implementation begins
- [ ] Stakeholders consulted and listed in ADR
- [ ] ADR reviewed by team/architecture board
- [ ] ADR committed to version control
- [ ] ADR index updated with new entry
- [ ] Team notified of new ADR (Slack, email, etc.)

### Adoption Metrics

- **Coverage**: % of major decisions documented with ADRs (Target: 80%+)
- **Currency**: % of ADRs reviewed in last 12 months (Target: 100% of active)
- **Effectiveness**: Time to answer "why" questions (Target: <5 minutes)
- **Onboarding**: New team member comprehension score (Target: 8+/10)

## Execution Protocol

### Creating a New ADR

1. **Identify Decision** (5 minutes)
   - Verify this decision warrants an ADR
   - Check if existing ADR covers this topic
   - Assign next ADR number

2. **Gather Context** (15-20 minutes)
   - Document current state and problem
   - Identify business and technical constraints
   - List stakeholders to consult
   - Research industry best practices

3. **Evaluate Alternatives** (20-30 minutes)
   - Identify 3-5 viable alternatives
   - Score each alternative on key criteria
   - Document pros, cons, and trade-offs
   - Estimate costs for each option

4. **Make Recommendation** (10 minutes)
   - Select recommended approach
   - Write clear decision statement
   - Justify why this option is best
   - Identify risks and mitigation strategies

5. **Document Consequences** (15 minutes)
   - List positive consequences and benefits
   - Identify negative consequences and trade-offs
   - Plan for mitigation of risks
   - Define success metrics

6. **Review & Refine** (10-15 minutes)
   - Share with stakeholders for feedback
   - Incorporate feedback and revise
   - Get final approval from decision makers
   - Update status to "Accepted"

7. **Publish & Communicate** (5 minutes)
   - Commit ADR to version control
   - Update ADR index
   - Notify team via Slack/email
   - Link ADR in relevant tickets/PRs

**Total Time**: 80-100 minutes for comprehensive ADR

## Integration with Other Commands

- **Architecture Design**: Use `/architecture:design` to generate architecture, then create ADRs for key decisions
- **Diagrams**: Use `/architecture:diagram` to visualize decisions from ADR
- **Review**: Use `/architecture:review` to audit if ADRs are being followed
- **Development**: Reference ADR numbers in PR descriptions and commit messages

## Examples of Good ADRs

### Example 1: Database Selection

**ADR-0005: Use PostgreSQL for Primary Database**

- **Context**: Need ACID compliance for financial transactions
- **Decision**: PostgreSQL over MongoDB
- **Alternatives**: MongoDB (no ACID), MySQL (license concerns), DynamoDB (vendor lock-in)
- **Consequences**: Strong consistency (+), steeper learning curve (-), mature ecosystem (+)

### Example 2: API Design

**ADR-0012: Implement GraphQL API**

- **Context**: Mobile app needs flexible queries, REST causing over-fetching
- **Decision**: GraphQL with Apollo Server
- **Alternatives**: REST (less flexible), gRPC (web incompatible), tRPC (TypeScript only)
- **Consequences**: Reduced bandwidth (+), query complexity management (-), great DX (+)

### Example 3: Deployment Strategy

**ADR-0018: Adopt Blue-Green Deployment**

- **Context**: Zero-downtime deployments required for 99.9% SLA
- **Decision**: Blue-green deployment on Kubernetes
- **Alternatives**: Rolling updates (downtime), canary (complex), feature flags (not enough)
- **Consequences**: Instant rollback (+), 2x infrastructure cost (-), simplified testing (+)

---

**Best Practices**:

1. Write ADRs **before** implementing major decisions
2. Keep ADRs concise but comprehensive (2-5 pages)
3. Review ADRs annually to update status
4. Link ADRs in code comments and documentation
5. Don't delete deprecated ADRs - they're historical record
6. Use consistent formatting and numbering
7. Get stakeholder review before marking "Accepted"
