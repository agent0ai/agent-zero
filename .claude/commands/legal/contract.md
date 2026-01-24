---
description: Generate business contracts (NDA, MSA, SLA, consulting agreements)
argument-hint: <contract-type> [--parties "Company A, Company B"] [--jurisdiction <state|country>] [--export <docx|pdf>]
model: claude-sonnet-4-5-20250929
allowed-tools: Write, Read, Glob, Grep, AskUserQuestion, Bash
---

# Business Contract Generator

Generate professional business contracts with jurisdiction-specific clauses and industry best practices.

## LEGAL DISCLAIMER

**IMPORTANT**: These are contract TEMPLATES only and are NOT legal advice. All generated contracts MUST be reviewed and approved by a qualified attorney licensed in your jurisdiction before use. This tool does not create an attorney-client relationship. By using this command, you acknowledge that you will seek proper legal counsel before executing any contract.

## What This Command Does

Generates comprehensive business contracts tailored to your specific needs:

- **NDA (Non-Disclosure Agreement)**: Unilateral or mutual confidentiality agreements
- **MSA (Master Services Agreement)**: Framework for ongoing business relationships
- **SLA (Service Level Agreement)**: Performance guarantees and uptime commitments
- **Consulting Agreement**: Independent contractor and consulting services contracts
- **SOW (Statement of Work)**: Project-specific scope and deliverables
- **Partnership Agreement**: Business partnership terms and profit sharing
- **Licensing Agreement**: Software, IP, or content licensing terms
- **Vendor Agreement**: Supplier and procurement contracts

Each contract includes:

- Jurisdiction-specific legal language
- Standard protective clauses
- Payment terms and conditions
- Termination and dispute resolution
- Industry-specific provisions
- OPTIONAL: E-signature integration readiness

## Usage Examples

### Generate NDA (Non-Disclosure Agreement)

```bash
/legal:contract nda --parties "TechCorp Inc, ConsultantCo LLC" --jurisdiction california --export docx
```

**Generated Sections**:

- Definition of confidential information
- Obligations of receiving party
- Permitted disclosures and exceptions
- Term and survival clauses
- Remedies for breach
- Governing law and jurisdiction

### Generate Master Services Agreement (MSA)

```bash
/legal:contract msa --parties "ClientCorp, ServiceProvider Inc" --jurisdiction delaware --export pdf
```

**Generated Sections**:

- Scope of services framework
- Statement of Work (SOW) attachment process
- Payment terms and invoicing procedures
- Intellectual property ownership
- Warranties and representations
- Limitation of liability
- Indemnification clauses
- Term, renewal, and termination
- Dispute resolution and arbitration

### Generate Service Level Agreement (SLA)

```bash
/legal:contract sla --parties "CloudHost Inc, Enterprise Client LLC" --jurisdiction new-york --export docx
```

**Generated Sections**:

- Service availability commitments (e.g., 99.9% uptime)
- Performance metrics and measurement
- Service credits and remedies
- Maintenance windows and notifications
- Support response times
- Escalation procedures
- Force majeure and exclusions

### Generate Consulting Agreement

```bash
/legal:contract consulting --parties "FreelanceConsultant, StartupCo Inc" --jurisdiction texas --export pdf
```

**Generated Sections**:

- Independent contractor status
- Scope of consulting services
- Compensation and expenses
- Work product and IP assignment
- Non-compete and non-solicitation (if applicable)
- Confidentiality obligations
- Term and termination rights
- Insurance requirements

## Business Value / ROI

### Direct Cost Savings

- **Legal drafting fees**: $500-$5,000 per contract (depending on complexity)
- **Template development**: $2,000-$10,000 for custom contract library
- **Turnaround time**: Reduce from 3-7 days to 30 minutes
- **Annual savings**: $15,000-$50,000 for businesses executing 10-20 contracts/year

### Risk Mitigation

- **Standardization**: Consistent legal language reduces interpretation disputes
- **Completeness**: AI ensures all critical clauses are included
- **Compliance**: Jurisdiction-specific provisions reduce regulatory risk
- **Version control**: Track contract evolution and changes

### Business Velocity

- **Sales acceleration**: Close deals faster with ready-to-sign contracts
- **Vendor onboarding**: Streamline supplier and partner onboarding
- **Expansion readiness**: Scale contract generation as business grows
- **Self-service**: Enable non-legal teams to draft initial agreements

### Quantified ROI Example

**Mid-sized SaaS Company (50 employees)**:

- Contracts per year: 30 (customers, vendors, consultants)
- Legal fees saved: 30 × $2,000 = $60,000
- Time saved: 30 × 5 days × $500/day = $75,000 (opportunity cost)
- **Total annual value**: $135,000
- **Cost to implement**: $5,000 (lawyer review of templates)
- **Net ROI Year 1**: $130,000 (2,600% return)

## Success Metrics

### Quality Metrics

- [ ] All mandatory clauses included (force majeure, governing law, notices)
- [ ] Jurisdiction-specific language correct
- [ ] Clear definitions section included
- [ ] No contradictory or ambiguous terms
- [ ] Professional formatting and structure
- [ ] Signature blocks and execution instructions

### Compliance Metrics

- [ ] Contract reviewed by qualified attorney
- [ ] Compliance with local contract law requirements
- [ ] Industry-specific regulations addressed (e.g., GDPR for EU parties)
- [ ] Tax and regulatory implications considered
- [ ] Insurance requirements specified (if applicable)

### Business Metrics

- [ ] Contract execution time: < 7 days (target: < 48 hours)
- [ ] Legal review cost: < $1,000 per contract
- [ ] Contract disputes: < 2% of executed contracts
- [ ] Customer satisfaction: > 4.5/5 for contracting process
- [ ] Revenue impact: Measure deal velocity improvement

## Contract Types Reference

### NDA (Non-Disclosure Agreement)

**When to use**: Before disclosing confidential information (fundraising, M&A, partnerships)
**Typical term**: 2-5 years
**Key provisions**: Definition of confidential info, exclusions, return/destruction obligations

### MSA (Master Services Agreement)

**When to use**: Establishing ongoing relationship with recurring services
**Typical term**: 1-3 years (auto-renewing)
**Key provisions**: SOW process, payment terms, IP ownership, liability caps

### SLA (Service Level Agreement)

**When to use**: Defining service commitments and performance guarantees
**Typical term**: Tied to underlying service agreement
**Key provisions**: Uptime commitments, measurement methodology, service credits

### Consulting Agreement

**When to use**: Engaging independent contractors or consultants
**Typical term**: Project-based or 3-12 months
**Key provisions**: IC status, work product ownership, termination rights

### SOW (Statement of Work)

**When to use**: Defining specific project scope under an MSA
**Typical term**: Project duration (weeks to months)
**Key provisions**: Deliverables, milestones, acceptance criteria, change orders

### Partnership Agreement

**When to use**: Forming business partnerships with shared ownership
**Typical term**: Indefinite (until dissolution)
**Key provisions**: Ownership %, profit sharing, decision-making, exit rights

### Licensing Agreement

**When to use**: Granting rights to use IP, software, or content
**Typical term**: Perpetual or fixed term (1-5 years)
**Key provisions**: License scope, restrictions, fees, sublicensing rights

### Vendor Agreement

**When to use**: Engaging suppliers for goods or services
**Typical term**: 1-3 years
**Key provisions**: Pricing, delivery terms, quality standards, warranties

## Integration with Other Commands

**Sales Pipeline**:

```bash
/sales/proposal        # Create proposal
/legal:contract msa    # Generate MSA when deal is closing
/zoho/create-deal      # Track in CRM
```

**Consulting Workflow**:

```bash
/legal:contract consulting  # Generate consulting agreement
/finance/budget            # Set up project billing
/dev/create-branch         # Start project work
```

**Vendor Management**:

```bash
/legal:contract vendor  # Generate vendor agreement
/finance/budget         # Allocate vendor spend
/devops/setup           # Grant vendor access (if needed)
```

## Jurisdictional Considerations

### United States

- **Delaware**: Popular for MSAs and corporate agreements (business-friendly)
- **California**: Strong employee protections, restrictive non-competes
- **New York**: Common for financial services and licensing agreements
- **Texas**: Business-friendly, enforceable non-competes (with limitations)

### International

- **UK**: English common law, similar to US contracts
- **EU**: GDPR compliance mandatory for data processing
- **Canada**: Provincial variations (Quebec civil law vs. common law)
- **Australia**: Fair Work Act considerations for employment-related contracts

### Key Differences to Consider

- **Non-compete enforceability**: Varies widely (California generally prohibits, Texas permits)
- **Indemnification**: Some jurisdictions limit or prohibit certain indemnity clauses
- **Mandatory arbitration**: Some jurisdictions restrict consumer arbitration clauses
- **Data protection**: EU GDPR, California CCPA, Canada PIPEDA requirements

## Attorney Review Process

**Recommended Workflow**:

1. **Generate contract** using this command with your specific parameters
2. **Internal review** by business stakeholders (ensure business terms are correct)
3. **Attorney review** by lawyer licensed in governing jurisdiction
4. **Revisions** based on attorney feedback
5. **Template refinement** for future similar contracts
6. **Execution** after all parties approve and sign
7. **Storage** in secure contract management system

**Cost-Effective Attorney Review**:

- **Template review** (one-time): $2,000-$5,000 to review and approve templates
- **Per-contract review**: $500-$1,500 for minor customizations
- **Retainer arrangement**: $2,000-$5,000/month for unlimited reviews (high volume)

## Commands

**`/legal:contract nda`** - Generate Non-Disclosure Agreement
**`/legal:contract msa`** - Generate Master Services Agreement
**`/legal:contract sla`** - Generate Service Level Agreement
**`/legal:contract consulting`** - Generate Consulting Agreement
**`/legal:contract sow`** - Generate Statement of Work
**`/legal:privacy`** - Generate privacy policies (GDPR, CCPA, PIPEDA)
**`/legal:terms`** - Generate terms of service
**`/legal:gdpr`** - GDPR compliance checklist and documentation

---
**REMEMBER**: These are templates requiring attorney review. Not legal advice.
**Related**: /sales/proposal, /finance/budget, /zoho/create-deal
