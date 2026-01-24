---
description: Design system architecture with comprehensive trade-off analysis, technology selection, and scalability planning
argument-hint: "[--type <microservices|monolith|serverless|hybrid>] [--scale <startup|growth|enterprise>] [--constraints <budget|time|team>]"
allowed-tools: [Read, Write, Bash, Glob, Grep, WebSearch, AskUserQuestion]
---

# Architecture Design Command

## What This Command Does

This command helps you design robust, scalable system architectures by:

- Analyzing requirements and constraints
- Evaluating architectural patterns and trade-offs
- Selecting appropriate technologies and infrastructure
- Creating detailed architecture specifications
- Planning for scalability, security, and maintainability
- Documenting design decisions and rationale

The command uses AI-assisted analysis to recommend optimal architectural approaches based on your specific context, constraints, and goals.

## Usage Examples

### Basic Architecture Design

```bash
/architecture:design
```

Interactive mode will gather requirements about your system, scale, constraints, and goals.

### Design Microservices Architecture

```bash
/architecture:design --type microservices --scale growth
```

Design a microservices-based architecture optimized for a growing company.

### Design with Specific Constraints

```bash
/architecture:design --type serverless --constraints budget,time
```

Design a serverless architecture optimized for budget and fast time-to-market.

### Design for Enterprise Scale

```bash
/architecture:design --type hybrid --scale enterprise
```

Design a hybrid architecture (mix of patterns) for enterprise-level scale and complexity.

## Architecture Patterns Evaluated

### Monolithic Architecture

**Best For**: MVPs, small teams, simple domains
**Pros**: Simple deployment, easier debugging, single codebase
**Cons**: Limited scalability, tight coupling, slow iteration
**When to Choose**: Early stage startups, proof of concepts, tight budgets

### Microservices Architecture

**Best For**: Large teams, complex domains, independent scaling
**Pros**: Independent deployment, technology flexibility, fault isolation
**Cons**: Operational complexity, distributed system challenges, higher costs
**When to Choose**: Growth stage, multiple teams, evolving requirements

### Serverless Architecture

**Best For**: Event-driven workloads, variable traffic, minimal ops
**Pros**: Auto-scaling, pay-per-use, no server management
**Cons**: Cold starts, vendor lock-in, debugging complexity
**When to Choose**: Startups, variable workloads, minimal DevOps resources

### Hybrid Architecture

**Best For**: Transitioning systems, mixed requirements, gradual modernization
**Pros**: Flexibility, risk mitigation, incremental migration
**Cons**: Increased complexity, multiple deployment strategies
**When to Choose**: Legacy modernization, diverse workload types

## Design Process

### Phase 1: Requirements Gathering

- System purpose and core functionality
- Expected scale (users, transactions, data volume)
- Performance requirements (latency, throughput)
- Budget and timeline constraints
- Team size and expertise
- Compliance and security requirements

### Phase 2: Constraint Analysis

- Technical constraints (existing systems, technology stack)
- Business constraints (budget, time-to-market, team)
- Operational constraints (DevOps maturity, monitoring)
- Regulatory constraints (HIPAA, PCI-DSS, GDPR, SOC2)

### Phase 3: Pattern Evaluation

- Evaluate each architectural pattern against requirements
- Score patterns on key dimensions:
  - Scalability (horizontal, vertical, auto-scaling)
  - Maintainability (code organization, deployment)
  - Performance (latency, throughput, reliability)
  - Cost (infrastructure, operational, development)
  - Team fit (expertise required, learning curve)
  - Time-to-market (development speed, deployment)

### Phase 4: Technology Selection

- **Data Layer**: Database selection (SQL vs NoSQL, caching, queues)
- **Application Layer**: Frameworks, languages, runtime environments
- **Infrastructure Layer**: Cloud provider, containers, orchestration
- **Observability**: Monitoring, logging, tracing, alerting
- **Security**: Authentication, authorization, encryption, secrets

### Phase 5: Architecture Design

- Component breakdown and responsibilities
- Data flow and communication patterns
- API design and contracts
- State management and data consistency
- Error handling and resilience
- Deployment and CI/CD strategy

### Phase 6: Documentation

- High-level architecture overview
- Component diagrams and data flow
- Technology stack justification
- Trade-off analysis and decision rationale
- Scalability and growth plan
- Security and compliance considerations
- Operational requirements and runbooks

## Output Specifications

### Architecture Design Document

```markdown
# System Architecture Design: [Project Name]

## Executive Summary
- System purpose and scope
- Recommended architecture pattern
- Key technology decisions
- Expected outcomes and ROI

## Requirements & Constraints
- Functional requirements
- Non-functional requirements (performance, security, compliance)
- Business constraints (budget, timeline, team)
- Technical constraints (existing systems, integrations)

## Architecture Pattern: [Selected Pattern]
- Pattern overview and rationale
- Why this pattern fits your context
- Trade-offs accepted and mitigated
- Alternative patterns considered

## System Components
- Component diagram
- Component responsibilities
- Communication patterns
- Data flow

## Technology Stack
- Frontend: [Technologies] - Rationale
- Backend: [Technologies] - Rationale
- Data Layer: [Technologies] - Rationale
- Infrastructure: [Technologies] - Rationale
- Observability: [Technologies] - Rationale

## Scalability Strategy
- Horizontal scaling approach
- Vertical scaling limits
- Caching strategy
- Database scaling (sharding, replication)
- Load balancing and traffic management

## Security Architecture
- Authentication & authorization approach
- Data encryption (at rest, in transit)
- Secrets management
- Network security (VPC, firewalls, WAF)
- Compliance requirements (HIPAA, PCI-DSS, etc.)

## Deployment & Operations
- CI/CD pipeline design
- Environment strategy (dev, staging, prod)
- Deployment strategy (blue-green, canary, rolling)
- Monitoring and alerting
- Backup and disaster recovery

## Trade-Off Analysis
- Decision matrix with scoring
- Risks and mitigation strategies
- Future evolution and extensibility

## Implementation Roadmap
- Phase 1: MVP / Core functionality
- Phase 2: Scaling and optimization
- Phase 3: Advanced features
- Estimated timeline and milestones

## Cost Estimation
- Infrastructure costs (monthly estimates)
- Development costs (team, timeline)
- Operational costs (monitoring, maintenance)
- Total cost of ownership (TCO) over 3 years
```

## Business Value & ROI

### For Startups

- **Faster Time-to-Market**: Choose architectures optimized for speed (serverless, monolith)
- **Cost Efficiency**: Pay-per-use pricing, minimal operational overhead
- **Validation Speed**: Simple architectures that can pivot quickly
- **ROI**: 3-6 months faster launch = competitive advantage

### For Growth Companies

- **Scalability**: Architecture that grows with user base without rewrites
- **Team Productivity**: Clear component boundaries enable parallel development
- **Reliability**: Fault isolation and resilience patterns reduce downtime
- **ROI**: 50% reduction in scaling-related incidents, 30% faster feature delivery

### For Enterprises

- **Risk Mitigation**: Well-documented decisions reduce technical debt
- **Compliance**: Built-in security and compliance from day one
- **Maintainability**: Clear architecture reduces onboarding time by 40%
- **ROI**: Avoid costly rewrites ($500K-$5M+), reduce tech debt accumulation

### Quantifiable Benefits

- **Reduced Development Costs**: Clear architecture reduces rework by 30-50%
- **Improved Reliability**: 99.9% uptime vs 95% = $X saved per hour of downtime
- **Faster Hiring**: Well-documented systems reduce onboarding from 3 months to 3 weeks
- **Better Decision Making**: Trade-off analysis prevents costly technology mistakes

## Success Metrics

### Design Quality Metrics

- [ ] All major components identified and documented
- [ ] Trade-offs explicitly analyzed with scoring
- [ ] Technology choices justified with rationale
- [ ] Scalability plan defined with specific targets
- [ ] Security requirements mapped to architecture
- [ ] Cost estimates provided with breakdown

### Business Alignment Metrics

- [ ] Architecture aligns with business constraints (budget, timeline)
- [ ] Supports current team expertise or includes training plan
- [ ] Enables key business capabilities and differentiators
- [ ] Compliance requirements fully addressed
- [ ] Future evolution path clearly defined

### Technical Excellence Metrics

- [ ] Follows industry best practices for chosen pattern
- [ ] Includes observability and operational considerations
- [ ] Error handling and resilience patterns defined
- [ ] API design follows REST/GraphQL best practices
- [ ] Data consistency and state management clearly specified

### Stakeholder Readiness Metrics

- [ ] Non-technical stakeholders can understand executive summary
- [ ] Technical team can implement from documentation
- [ ] Operations team has runbooks and monitoring plan
- [ ] Security team can audit compliance requirements
- [ ] Finance team has accurate cost projections

## Execution Protocol

1. **Gather Context** (5-10 minutes)
   - Run interactive questionnaire to understand requirements
   - Analyze existing codebase (if applicable)
   - Review business constraints and goals

2. **Analyze Patterns** (10-15 minutes)
   - Evaluate 4 architectural patterns against requirements
   - Score each pattern on 6 key dimensions
   - Identify top 2 candidates

3. **Deep Dive Design** (20-30 minutes)
   - Design detailed architecture for recommended pattern
   - Select specific technologies for each layer
   - Create component breakdown and data flow
   - Document trade-offs and decision rationale

4. **Create Documentation** (15-20 minutes)
   - Generate comprehensive architecture design document
   - Include diagrams (component, data flow, deployment)
   - Add implementation roadmap and cost estimates

5. **Review & Refine** (10 minutes)
   - Present design to stakeholder
   - Gather feedback and adjust
   - Finalize documentation

**Total Time**: 60-85 minutes for comprehensive architecture design

## Integration with Other Commands

- **Generate ADR**: Use `/architecture:adr` to document key decisions from design
- **Create Diagrams**: Use `/architecture:diagram` to visualize the architecture
- **Review Design**: Use `/architecture:review` to audit the architecture
- **Plan Implementation**: Use `/dev:feature-request` to break down into stories

---

**Next Steps After Design:**

1. Create ADRs for major technology decisions (`/architecture:adr`)
2. Generate architecture diagrams (`/architecture:diagram`)
3. Set up initial project structure (`/dev:create-branch`)
4. Define API contracts and interfaces
5. Begin Phase 1 implementation
