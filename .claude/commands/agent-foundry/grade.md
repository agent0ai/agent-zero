---
description: Grade agent against production quality standards and certification criteria
allowed-tools: [Bash, Read, Write, Task]
argument-hint: "<agent-name> [--certification <bronze|silver|gold|platinum>]"
---

# /agent-foundry/grade - Grade Agent Quality

Assign quality grade and certification level based on comprehensive evaluation against production standards.

## Grading System

### Certification Levels

**🥉 Bronze** (70-79%)

- Basic functionality working
- Acceptable for internal use
- Requires supervision
- Limited deployment

**🥈 Silver** (80-89%)

- Good reliability
- Suitable for beta users
- Monitored deployment
- Most scenarios covered

**🥇 Gold** (90-94%)

- Production quality
- General availability ready
- Minimal monitoring needed
- Edge cases handled well

**💎 Platinum** (95-100%)

- Exceptional quality
- Enterprise-grade
- Autonomous operation
- Industry-leading performance

## Grading Process

### Step 1: Aggregate Scores

Collect scores from evaluation:

```typescript
interface GradingScores {
  functional: number        // From evaluation
  performance: number       // From evaluation
  quality: number          // From evaluation
  robustness: number       // From evaluation
  userExperience: number   // From evaluation
  production: number       // From evaluation

  // Additional grading criteria
  documentation: number
  testCoverage: number
  compliance: number
  innovation: number
}
```

### Step 2: Calculate Weighted Score

Different criteria have different weights:

```typescript
const weights = {
  functional: 0.25,        // 25% - Most important
  performance: 0.15,       // 15%
  quality: 0.15,          // 15%
  robustness: 0.15,       // 15%
  userExperience: 0.10,   // 10%
  production: 0.10,       // 10%
  documentation: 0.05,    // 5%
  testCoverage: 0.05      // 5%
}

const overallScore = Object.entries(scores).reduce((total, [key, score]) => {
  return total + (score * weights[key])
}, 0)
```

### Step 3: Apply Quality Multipliers

Bonuses and penalties:

```yaml
quality_multipliers:
  bonuses:
    - condition: "Zero critical bugs"
      multiplier: 1.02  # +2%

    - condition: "Test coverage >95%"
      multiplier: 1.01  # +1%

    - condition: "User rating >9/10"
      multiplier: 1.03  # +3%

    - condition: "Innovative approach"
      multiplier: 1.02  # +2%

  penalties:
    - condition: "Security vulnerability"
      multiplier: 0.90  # -10%

    - condition: "Performance regression"
      multiplier: 0.95  # -5%

    - condition: "Incomplete documentation"
      multiplier: 0.98  # -2%
```

### Step 4: Certification Requirements

Each level has specific requirements:

#### Bronze Certification (70-79%)

```yaml
bronze_requirements:
  minimum_scores:
    functional: 70%
    performance: 65%
    production: 60%

  must_have:
    - Core capabilities working
    - Basic error handling
    - Some documentation
    - Passed smoke tests

  allowed_gaps:
    - Edge cases not fully covered
    - Performance could be better
    - Limited observability
    - Requires supervision

  deployment_restrictions:
    - Internal use only
    - Development environments
    - Limited user base (<10)
    - Requires monitoring
```

#### Silver Certification (80-89%)

```yaml
silver_requirements:
  minimum_scores:
    functional: 80%
    performance: 75%
    production: 75%
    userExperience: 75%

  must_have:
    - All core capabilities working
    - Good error handling
    - Comprehensive documentation
    - Integration tests passing
    - Most edge cases covered

  allowed_gaps:
    - Some advanced features missing
    - Performance optimization opportunities
    - Partial observability
    - Occasional issues

  deployment_restrictions:
    - Beta users
    - Staged rollout
    - Active monitoring required
    - Feedback collection mandatory
```

#### Gold Certification (90-94%)

```yaml
gold_requirements:
  minimum_scores:
    functional: 90%
    performance: 88%
    quality: 88%
    robustness: 85%
    production: 88%

  must_have:
    - All capabilities production-ready
    - Excellent error handling
    - Complete documentation
    - All tests passing (>95% coverage)
    - Edge cases handled
    - Good observability
    - Security validated

  allowed_gaps:
    - Minor performance improvements possible
    - Some advanced features could be added
    - Documentation could be enhanced

  deployment_restrictions:
    - General availability
    - Standard monitoring
    - Regular updates
```

#### Platinum Certification (95-100%)

```yaml
platinum_requirements:
  minimum_scores:
    functional: 95%
    performance: 93%
    quality: 95%
    robustness: 93%
    userExperience: 93%
    production: 95%

  must_have:
    - Exceptional quality across all dimensions
    - Zero critical issues
    - Outstanding documentation
    - 100% test coverage
    - All edge cases handled gracefully
    - Comprehensive observability
    - Security excellence
    - Innovation / unique value

  allowed_gaps:
    - Minimal - near perfection

  deployment_restrictions:
    - None - full production
    - Enterprise customers
    - Mission-critical use cases
    - Autonomous operation
```

### Step 5: Generate Certification Badge

Create visual certification indicator:

```markdown
## Certification Badge

╔══════════════════════════════════════╗
║                                      ║
║    🥇 GOLD CERTIFIED                 ║
║                                      ║
║    DATABASE ARCHITECT AGENT          ║
║                                      ║
║    Overall Score: 92.4%              ║
║    Certification: Gold               ║
║    Valid Until: 2026-04-16          ║
║                                      ║
║    ✓ Production Ready                ║
║    ✓ General Availability            ║
║    ✓ Enterprise Supported            ║
║                                      ║
╚══════════════════════════════════════╝

Certificate ID: AGENT-DBA-2026-001
Issued: January 16, 2026
Certifying Authority: Prompt Blueprint Agent Foundry
```

### Step 6: Detailed Grade Report

```markdown
# Grade Report: {agent-name}

## Certification Summary

**🥇 GOLD CERTIFIED** (92.4%)

**Validity**: 90 days (renewable)
**Certificate ID**: AGENT-{name}-{year}-{number}
**Issued**: {date}

## Score Breakdown

| Category | Score | Weight | Contribution | Grade |
|----------|-------|--------|--------------|-------|
| Functional Correctness | 94.7% | 25% | 23.7% | A |
| Performance | 96.0% | 15% | 14.4% | A |
| Output Quality | 95.0% | 15% | 14.3% | A |
| Robustness | 93.0% | 15% | 14.0% | A |
| User Experience | 92.0% | 10% | 9.2% | A- |
| Production Readiness | 93.0% | 10% | 9.3% | A |
| Documentation | 88.0% | 5% | 4.4% | B+ |
| Test Coverage | 96.0% | 5% | 4.8% | A |

**Weighted Total**: 94.1%

### Quality Multipliers Applied

✓ Zero critical bugs (+2%)
✓ Test coverage >95% (+1%)
⚠ User rating pending (no bonus)

**Final Score**: 92.4% → **GOLD**

## Certification Requirements Met

### Gold Standard Checklist

✅ Functional ≥90%: 94.7%
✅ Performance ≥88%: 96.0%
✅ Quality ≥88%: 95.0%
✅ Robustness ≥85%: 93.0%
✅ Production ≥88%: 93.0%
✅ All tests passing: 96% coverage
✅ Edge cases handled: 93%
✅ Security validated: No issues
✅ Complete documentation: Yes
✅ Good observability: Yes

**Result**: All Gold requirements met ✓

## Strengths

1. **Exceptional Performance** (96%)
   - All latency targets exceeded
   - Efficient resource usage
   - Scales well

2. **High Quality Outputs** (95%)
   - Technically excellent
   - Clear and actionable
   - Production-ready code

3. **Strong Fundamentals** (94.7%)
   - All capabilities working
   - Reliable and consistent
   - Well-tested

## Areas for Improvement (for Platinum)

To achieve Platinum (95%+):

1. **User Experience** → 93%+ (currently 92%)
   - Add progress indicators for long tasks
   - Enhance error recovery
   - Improve response streaming

2. **Documentation** → 95%+ (currently 88%)
   - More advanced examples
   - Video tutorials
   - Interactive guides

3. **Innovation** → Demonstrate unique value
   - Novel optimization techniques
   - Industry-first capabilities
   - Research contributions

## Deployment Authorization

**Authorized For**:
✅ Production environments
✅ General availability
✅ Enterprise customers
✅ Mission-critical (with monitoring)
✅ Multi-tenant deployments

**Not Authorized For**:
⚠ Fully autonomous (without fallback)
⚠ Life-critical systems (not evaluated)
⚠ Financial trading (compliance pending)

## Maintenance Requirements

Gold certification requires:
- **Quarterly re-evaluation**
- **Incident response <4 hours**
- **Bug fixes <48 hours**
- **Feature updates monthly**
- **Security patches immediate**

## Competitive Standing

**Industry Benchmark**: 85% (average production agent)
**Position**: Top 15%
**Competitive Advantage**: Yes

## Recommendation

**PROCEED TO DEPLOYMENT**

Agent has achieved Gold certification and is:
✓ Production-ready
✓ Suitable for general availability
✓ Meets enterprise standards
✓ Competitive in market

Next Steps:
1. Run: /agent-foundry/deploy {agent-name} --stage beta
2. Monitor for 2 weeks
3. Expand to general availability
4. Plan Platinum improvements

## Certification Validity

**Valid Until**: April 16, 2026 (90 days)

**Renewal Requirements**:
- Maintain ≥90% score
- No critical incidents
- Positive user feedback
- Security compliance
```

### Step 7: Comparison Matrix

Compare against other agents:

```yaml
competitive_matrix:
  agents:
    database-architect: 92.4% (Gold)
    security-auditor: 89.2% (Silver)
    cost-optimizer: 87.5% (Silver)
    implementer: 94.8% (Gold)

  ranking:
    1. implementer (94.8%)
    2. database-architect (92.4%)
    3. security-auditor (89.2%)
    4. cost-optimizer (87.5%)

  upgrade_paths:
    security-auditor: "Improve edge case handling → Gold"
    cost-optimizer: "Enhance performance analysis → Silver+"
```

### Step 8: Certification Output

Create certification artifacts:

```bash
# Files Generated:
.claude/agents/database-architect/certification.json
.claude/agents/database-architect/badge.svg
.claude/agents/database-architect/grade-report.md
```

## Usage Examples

### Example 1: Standard Grading

```bash
/agent-foundry/grade database-architect
```

Assigns certification based on evaluation scores.

### Example 2: Target Certification

```bash
/agent-foundry/grade security-auditor --certification gold
```

Grades against Gold requirements specifically.

### Example 3: Re-certification

```bash
/agent-foundry/grade implementer --recertify
```

Renew expiring certification.

## Certification Policies

### Automatic Downgrade

Certifications are automatically downgraded if:

- Critical bug discovered
- Security vulnerability found
- Performance degradation >20%
- User satisfaction <7/10

### Immediate Revocation

Certifications are revoked for:

- Data breach
- Compliance violation
- Malicious behavior
- System compromise

### Appeals Process

Agents can be re-evaluated if:

- Scores are disputed
- Requirements clarification needed
- Special circumstances exist

## Quality Gates

Before issuing certification:

✅ All evaluation tests passed
✅ Minimum scores met for tier
✅ No security issues
✅ No critical bugs
✅ Documentation complete
✅ User acceptance (if available)

## Best Practices

1. **Aim High** - Target Gold minimum for production
2. **Continuous Improvement** - Don't stop at certification
3. **Monitor Performance** - Track against certification criteria
4. **Plan Renewals** - Start renewal process at 75 days
5. **Document Changes** - Track what improved the grade
6. **Share Learnings** - Help other agents achieve certification
