---
description: Benchmark model performance on different task types with comparative analysis
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
---

# Model Benchmarking Command

## What This Command Does

Runs comprehensive benchmarks comparing Claude Haiku, Sonnet, and Opus performance across different task types. Measures speed, quality, cost-effectiveness, and provides data-driven recommendations for model selection strategies.

**Key Features:**

- Side-by-side comparison of all three models on identical tasks
- Multiple benchmark categories (coding, documentation, analysis, security, etc.)
- Quality scoring with human-in-the-loop validation options
- Performance metrics (speed, success rate, consistency)
- Cost-benefit analysis per task category
- Custom benchmark creation for project-specific tasks

## Benchmark Categories

### 1. Code Generation

Test models on creating code from specifications.

### 2. Documentation Writing

Test models on creating technical documentation.

### 3. Code Review

Test models on finding bugs and suggesting improvements.

### 4. Data Analysis

Test models on analyzing and interpreting data.

### 5. Security Auditing

Test models on identifying security vulnerabilities.

### 6. Problem Solving

Test models on novel/complex problems.

### 7. Refactoring

Test models on improving existing code.

### 8. Testing

Test models on generating test cases.

## Usage Examples

### Example 1: Quick Benchmark (All Categories)

```bash
/model:benchmark
```

**Expected Output:**

```
Claude Model Benchmark Suite
=============================
Running comprehensive benchmarks...

Test Categories: 8
Tasks per Category: 5
Total Tests: 120 (40 per model)

⏱️ Estimated Time: 15-20 minutes

[Progress Bar]
████████████████████████████████████ 100%

📊 BENCHMARK RESULTS
====================

CATEGORY 1: Code Generation
----------------------------
Task: "Create REST API endpoint for user authentication"

Haiku (claude-3-5-haiku-20241022):
  ✓ Completed: 4.2s
  ✓ Quality Score: 7.2/10 (functional but basic)
  ✓ Cost: $0.0001
  ✓ Lines of Code: 45
  Issues: Missing error handling, no input validation

Sonnet (claude-sonnet-4-5-20250929):
  ✓ Completed: 8.7s
  ✓ Quality Score: 9.1/10 (production-ready)
  ✓ Cost: $0.0003
  ✓ Lines of Code: 78
  Features: Error handling, validation, logging, tests

Opus (claude-opus-4-20250514):
  ✓ Completed: 15.3s
  ✓ Quality Score: 9.4/10 (enterprise-grade)
  ✓ Cost: $0.0010
  ✓ Lines of Code: 112
  Features: Comprehensive error handling, security best practices,
            extensive tests, documentation

Winner: Sonnet (best cost/quality ratio)
Recommendation: Use Sonnet for API development
              Use Opus only for security-critical endpoints

---

CATEGORY 2: Documentation Writing
----------------------------------
Task: "Write API documentation for authentication endpoint"

Haiku:
  ✓ Completed: 2.1s
  ✓ Quality Score: 8.8/10 (clear and comprehensive)
  ✓ Cost: $0.0001
  ✓ Word Count: 342
  Quality: Well-structured, covers all essentials

Sonnet:
  ✓ Completed: 4.3s
  ✓ Quality Score: 9.0/10 (detailed with examples)
  ✓ Cost: $0.0003
  ✓ Word Count: 456
  Quality: Includes code examples, edge cases

Opus:
  ✓ Completed: 7.8s
  ✓ Quality Score: 9.1/10 (comprehensive with diagrams)
  ✓ Cost: $0.0010
  ✓ Word Count: 523
  Quality: Detailed examples, error scenarios, architecture notes

Winner: Haiku (excellent quality at 1/10th cost)
Recommendation: Use Haiku for documentation
              Only use Sonnet for complex architecture docs

---

CATEGORY 3: Code Review
-----------------------
Task: "Review authentication code for bugs and security issues"

Haiku:
  ✓ Completed: 3.2s
  ✓ Issues Found: 4 (2 critical, 2 minor)
  ✓ Quality Score: 7.5/10 (caught obvious issues)
  ✓ Cost: $0.0001
  Missed: Subtle timing attack vulnerability, race condition

Sonnet:
  ✓ Completed: 6.8s
  ✓ Issues Found: 7 (3 critical, 2 medium, 2 minor)
  ✓ Quality Score: 8.9/10 (thorough review)
  ✓ Cost: $0.0003
  Caught: All Haiku issues + timing attack + race condition
  Missed: Obscure edge case in token refresh

Opus:
  ✓ Completed: 12.4s
  ✓ Issues Found: 8 (3 critical, 2 medium, 3 minor)
  ✓ Quality Score: 9.6/10 (comprehensive security review)
  ✓ Cost: $0.0010
  Caught: All issues including edge case in token refresh

Winner: Sonnet (caught critical issues at reasonable cost)
Recommendation: Use Sonnet for code reviews
              Use Opus for security-critical or high-risk code

---

CATEGORY 4: Security Auditing
------------------------------
Task: "Security audit of authentication system"

Haiku:
  ⚠️ Completed: 4.1s
  ⚠️ Issues Found: 5 (basic security issues)
  ⚠️ Quality Score: 6.2/10 (insufficient depth)
  ✓ Cost: $0.0001
  Assessment: NOT RECOMMENDED for security audits

Sonnet:
  ✓ Completed: 9.3s
  ✓ Issues Found: 11 (moderate security review)
  ✓ Quality Score: 8.1/10 (good but not comprehensive)
  ✓ Cost: $0.0003
  Assessment: Acceptable for non-critical systems

Opus:
  ✓ Completed: 18.7s
  ✓ Issues Found: 16 (comprehensive security audit)
  ✓ Quality Score: 9.7/10 (expert-level analysis)
  ✓ Cost: $0.0010
  Assessment: REQUIRED for production security audits

Winner: Opus (only model providing sufficient depth)
Recommendation: ALWAYS use Opus for security audits
              Never compromise on security tasks

---

📈 AGGREGATE RESULTS
====================

Overall Performance by Model:

Haiku:
  Average Speed: 2.8s (FASTEST)
  Average Quality: 7.6/10 (GOOD)
  Average Cost: $0.0001 (CHEAPEST)
  Success Rate: 95.0%
  Best For: Documentation, simple edits, formatting
  Avoid For: Security, complex algorithms, architecture

Sonnet:
  Average Speed: 7.2s (BALANCED)
  Average Quality: 8.9/10 (EXCELLENT)
  Average Cost: $0.0003 (MODERATE)
  Success Rate: 98.2%
  Best For: Development, refactoring, code review, APIs
  Default Choice: YES (best all-around model)

Opus:
  Average Speed: 14.6s (SLOWEST)
  Average Quality: 9.5/10 (OUTSTANDING)
  Average Cost: $0.0010 (EXPENSIVE)
  Success Rate: 96.8%
  Best For: Security, architecture, complex algorithms
  Use When: Quality/correctness critical, high risk

💰 COST-BENEFIT ANALYSIS
=========================

Task Category → Recommended Model:

1. Simple Edits/Formatting → Haiku (10x cheaper, equal quality)
2. Documentation → Haiku (3x cheaper, nearly equal quality)
3. Code Generation → Sonnet (3x cheaper than Opus, 90% quality)
4. Code Review → Sonnet (good depth, reasonable cost)
5. Refactoring → Sonnet (best balance)
6. Testing → Sonnet (comprehensive test generation)
7. Security Auditing → Opus (REQUIRED, no substitute)
8. Architecture Design → Opus (long-term impact justifies cost)

Optimal Model Mix (estimated for typical project):
- 30% Haiku (docs, simple tasks) → $3/month
- 60% Sonnet (development) → $18/month
- 10% Opus (security, architecture) → $10/month
Total: $31/month for 1,000 tasks

vs. All-Sonnet Approach:
- 100% Sonnet → $300/month for 1,000 tasks
Savings: $269/month (89.7% reduction)

vs. All-Opus Approach:
- 100% Opus → $1,000/month for 1,000 tasks
Savings: $969/month (96.9% reduction)

🎯 KEY INSIGHTS
===============

1. Haiku Surprises
   - Documentation: 8.8/10 quality at 1/3 cost
   - Simple code: 7.2/10 quality, often sufficient
   - Speed: 3-5x faster than Sonnet
   Verdict: Massively underutilized in most projects

2. Sonnet Sweet Spot
   - Best all-around model for development
   - 98.2% success rate (highest)
   - Quality/cost ratio optimal for most tasks
   Verdict: Should be default choice

3. Opus Precision
   - Security audits: 9.7/10 (60% better than Sonnet)
   - Complex algorithms: 9.4/10 (15% better than Sonnet)
   - Speed: 2x slower than Sonnet
   Verdict: Reserved for critical high-impact tasks

4. The 30-60-10 Rule
   - 30% Haiku (simple/documentation)
   - 60% Sonnet (development/default)
   - 10% Opus (critical/complex)
   Result: 90% cost savings vs all-Opus, minimal quality loss

📋 RECOMMENDATIONS
==================

Immediate Actions:
1. Switch documentation tasks to Haiku → Save $45/month
2. Keep development on Sonnet → Maintain quality
3. Upgrade security audits to Opus → Prevent incidents

Long-Term Strategy:
1. Default to Sonnet, prove need for Opus
2. Aggressively move simple tasks to Haiku
3. Never compromise on security (always Opus)
4. Monitor success rates to validate model choices

Configuration Changes:
1. Update .claude/config/routing-rules.yaml:
   - documentation: haiku
   - development: sonnet
   - security: opus
2. Set budget alerts for Opus usage
3. Track Haiku success rate on expanded tasks
```

### Example 2: Specific Category Benchmark

```bash
/model:benchmark --category security --tasks 10 --validate
```

**Expected Output:**

```
Security Auditing Benchmark
============================
Category: Security
Tasks: 10
Human Validation: ENABLED

Running security-specific benchmarks...

Test 1: Authentication System Audit
------------------------------------
Haiku:   6.2/10 | 4.1s | $0.0001 | Found: 5 issues
Sonnet:  8.1/10 | 9.3s | $0.0003 | Found: 11 issues
Opus:    9.7/10 | 18.7s | $0.0010 | Found: 16 issues ✓ WINNER

Test 2: SQL Injection Vulnerability Scan
-----------------------------------------
Haiku:   5.8/10 | 3.2s | $0.0001 | Found: 3 issues (missed critical)
Sonnet:  7.9/10 | 7.8s | $0.0003 | Found: 7 issues
Opus:    9.8/10 | 16.2s | $0.0010 | Found: 9 issues ✓ WINNER

Test 3: XSS Attack Vector Analysis
-----------------------------------
Haiku:   6.5/10 | 3.8s | $0.0001 | Found: 4 issues
Sonnet:  8.4/10 | 8.9s | $0.0003 | Found: 8 issues
Opus:    9.6/10 | 17.3s | $0.0010 | Found: 11 issues ✓ WINNER

[... 7 more tests ...]

🔒 SECURITY BENCHMARK RESULTS
==============================

Average Quality Scores:
- Haiku:  6.1/10 ⚠️ INSUFFICIENT for production
- Sonnet: 8.2/10 ⚠️ ACCEPTABLE for non-critical only
- Opus:   9.7/10 ✓ REQUIRED for production security

Critical Issues Detected:
- Haiku:  Missed 47% of critical vulnerabilities
- Sonnet: Missed 23% of critical vulnerabilities
- Opus:   Missed 3% of critical vulnerabilities

Cost per Security Audit:
- Haiku:  $0.0001 (but 47% false negative rate) ⛔
- Sonnet: $0.0003 (but 23% false negative rate) ⚠️
- Opus:   $0.0010 (3% false negative rate) ✓

⚠️ CRITICAL FINDING
====================

Using Haiku or Sonnet for security audits creates FALSE SENSE OF SECURITY.

Real-World Impact:
- Missed vulnerability → Production breach
- Average data breach cost: $4.45M (IBM 2023)
- Opus cost: $0.001 per audit
- ROI: Prevents $4.45M loss for $0.001 → 4,450,000,000% ROI

RECOMMENDATION: ALWAYS USE OPUS FOR SECURITY TASKS

Human Validation Results:
✓ 3 security experts reviewed Opus findings
✓ 97% agreement on critical issues
✓ 94% agreement on medium issues
✓ Expert consensus: "Opus-level depth required for production"
```

### Example 3: Custom Benchmark

```bash
/model:benchmark --custom --tasks-file my-benchmark-tasks.json
```

**Input file (my-benchmark-tasks.json):**

```json
{
  "benchmark_name": "E-Commerce Platform Tasks",
  "tasks": [
    {
      "id": "ecom-1",
      "category": "api-integration",
      "description": "Implement Stripe payment processing with webhook handling",
      "expected_features": ["payment intent", "webhook verification", "error handling"],
      "quality_criteria": {
        "security": 10,
        "error_handling": 9,
        "testing": 8
      }
    },
    {
      "id": "ecom-2",
      "category": "data-processing",
      "description": "Generate daily sales report with trend analysis",
      "expected_features": ["data aggregation", "trend calculation", "export to CSV"],
      "quality_criteria": {
        "accuracy": 10,
        "performance": 8,
        "formatting": 7
      }
    },
    {
      "id": "ecom-3",
      "category": "security",
      "description": "Audit user authentication and session management",
      "expected_features": ["vulnerability scan", "compliance check", "recommendations"],
      "quality_criteria": {
        "thoroughness": 10,
        "accuracy": 10,
        "actionability": 9
      }
    }
  ]
}
```

**Expected Output:**

```
Custom Benchmark: E-Commerce Platform Tasks
============================================

Running 3 custom tasks × 3 models = 9 tests

Task 1: Stripe Payment Integration
-----------------------------------
Haiku:   7.4/10 | 5.2s | $0.0001
  ✓ Payment intent implementation
  ✗ Basic webhook verification (missing signature validation)
  ✗ Minimal error handling
  Score Breakdown: Security: 6/10, Error Handling: 7/10, Testing: 9/10

Sonnet:  9.2/10 | 10.8s | $0.0003 ✓ WINNER (quality/cost)
  ✓ Complete payment intent with idempotency
  ✓ Secure webhook verification with signature check
  ✓ Comprehensive error handling and retry logic
  ✓ Unit and integration tests
  Score Breakdown: Security: 9/10, Error Handling: 10/10, Testing: 9/10

Opus:    9.6/10 | 19.2s | $0.0010
  ✓ Enterprise-grade implementation
  ✓ Advanced security (rate limiting, fraud detection)
  ✓ Extensive test coverage
  Score Breakdown: Security: 10/10, Error Handling: 10/10, Testing: 9/10
  Note: Marginally better than Sonnet, 3x more expensive

Task 2: Sales Report Generation
--------------------------------
Haiku:   8.6/10 | 3.1s | $0.0001 ✓ WINNER (sufficient quality, best cost)
  ✓ Accurate data aggregation
  ✓ Good trend analysis
  ✓ Clean CSV export
  Score Breakdown: Accuracy: 9/10, Performance: 9/10, Formatting: 8/10

Sonnet:  9.1/10 | 7.2s | $0.0003
  ✓ Advanced trend analysis with forecasting
  ✓ Multiple export formats
  Score Breakdown: Accuracy: 10/10, Performance: 9/10, Formatting: 9/10
  Note: Slightly better but 3x cost not justified

Opus:    9.3/10 | 14.8s | $0.0010
  ✓ Statistical analysis with confidence intervals
  Score Breakdown: Accuracy: 10/10, Performance: 8/10, Formatting: 10/10
  Note: Overkill for this task

Task 3: Security Audit
----------------------
Haiku:   6.8/10 | 4.3s | $0.0001 ⚠️ INSUFFICIENT
  ✓ Basic vulnerability scan
  ✗ Missed critical session fixation vulnerability
  Score Breakdown: Thoroughness: 6/10, Accuracy: 6/10, Actionability: 8/10

Sonnet:  8.5/10 | 9.7s | $0.0003 ⚠️ MARGINAL
  ✓ Good vulnerability coverage
  ⚠️ Missed subtle timing attack
  Score Breakdown: Thoroughness: 8/10, Accuracy: 8/10, Actionability: 9/10

Opus:    9.8/10 | 18.9s | $0.0010 ✓ REQUIRED
  ✓ Comprehensive security analysis
  ✓ Found all vulnerabilities including timing attack
  ✓ Detailed remediation steps
  Score Breakdown: Thoroughness: 10/10, Accuracy: 10/10, Actionability: 10/10

📊 CUSTOM BENCHMARK SUMMARY
============================

Optimal Model per Task:
1. Payment Integration → Sonnet (9.2/10 at 30% of Opus cost)
2. Sales Reports → Haiku (8.6/10 at 10% of Sonnet cost)
3. Security Audit → Opus (9.8/10, no substitute)

Cost Comparison (for 100 executions):
All Haiku:   $0.01 (but fails security)
All Sonnet:  $0.03 (acceptable but not optimal)
All Opus:    $0.10 (best quality, 10x cost)
Optimized:   $0.047 (best quality per task)

Savings: 53% vs All-Opus, maintains quality

💡 PROJECT-SPECIFIC RECOMMENDATIONS
====================================

For your E-Commerce platform:
1. Payment processing: Default to Sonnet
   - Cost: $0.0003 per integration task
   - Quality: Production-ready (9.2/10)
   - Security audit afterward with Opus

2. Reporting/Analytics: Default to Haiku
   - Cost: $0.0001 per report
   - Quality: Excellent for data tasks (8.6/10)
   - 3x faster than Sonnet

3. Security tasks: ALWAYS Opus
   - Cost: $0.001 per audit
   - Quality: Critical (9.8/10)
   - Non-negotiable for production

Expected Monthly Costs (1,000 tasks):
- 400 payment tasks × Sonnet = $120
- 500 report tasks × Haiku = $50
- 100 security tasks × Opus = $100
Total: $270/month

vs. All-Sonnet: $300/month (10% savings, better quality)
vs. All-Opus: $1,000/month (73% savings, equivalent quality)
```

### Example 4: Continuous Benchmarking

```bash
/model:benchmark --continuous --interval daily --alert-on-regression
```

**Expected Output:**

```
Continuous Benchmarking Mode
=============================

Configuration:
- Frequency: Daily (runs at 2:00 AM)
- Tasks: Standard benchmark suite (40 tasks)
- Alerts: Enabled (regression threshold: 5%)
- Storage: .claude/benchmarks/daily/

✓ Benchmark scheduler started
✓ First run: Tomorrow at 2:00 AM
✓ Results will be emailed to: team@company.com

Dashboard: http://localhost:3000/benchmarks
```

**Daily Email Report:**

```
Daily Benchmark Report - Nov 25, 2025
======================================

Overall Status: ✓ STABLE

Model Performance (vs. Yesterday):
- Haiku:  7.6/10 (no change)
- Sonnet: 8.9/10 (+0.1, improved)
- Opus:   9.5/10 (no change)

Speed Benchmarks:
- Haiku:  2.8s (no change)
- Sonnet: 7.2s (+0.3s, 4% slower) ⚠️ ATTENTION
- Opus:   14.6s (no change)

⚠️ REGRESSION DETECTED
-----------------------
Task: Code Generation
Model: Sonnet
Yesterday: 8.7s
Today: 11.2s (+29% slower)
Possible Cause: API latency increase

Action: Investigating with Anthropic support

Cost Tracking:
- Daily benchmark cost: $0.048
- Monthly projection: $1.44
- ROI: Prevents model selection errors worth $100+/month

Full report: https://dashboard.example.com/benchmarks/2025-11-25
```

## Business Value / ROI

### Model Selection Confidence

- **Data-driven decisions**: No more guessing which model to use
- **Quantified trade-offs**: Exact cost/quality/speed for each model
- **Risk mitigation**: Know when cheaper model is risky

### Cost Optimization

- **Identify savings opportunities**: See where Haiku can replace Sonnet
- **Justify Opus usage**: Prove when premium model is worth it
- **Optimize budget allocation**: Spend on quality where it matters

### Quality Assurance

- **Prevent under-engineering**: Catch cases where cheap model is risky
- **Validate optimization**: Ensure cost-cutting doesn't hurt quality
- **Continuous monitoring**: Track model performance over time

### Real-World ROI

**Scenario 1: Pre-Optimization Benchmarking**

- Time investment: 2 hours to run comprehensive benchmarks
- Finding: 40% of tasks can use Haiku instead of Sonnet
- Monthly savings: $120
- Payback period: <1 day

**Scenario 2: Security Task Validation**

- Benchmark shows: Opus required for security (Sonnet misses 23% of issues)
- Decision: Upgrade all security tasks to Opus
- Cost increase: +$50/month
- Prevented incidents: Potentially $4.45M breach (industry average)
- ROI: Infinite (prevents catastrophic loss)

**Scenario 3: Continuous Monitoring**

- Daily benchmarks detect performance regression
- Issue: Sonnet suddenly 30% slower
- Root cause: API region routing issue
- Resolution: Switch to different endpoint
- Value: Restored 30% productivity improvement

## Success Metrics

### Benchmark Quality Metrics

- **Coverage**: % of task types covered by benchmarks
  - **Target: 80%+** of common tasks
- **Accuracy**: Benchmark results match real-world performance
  - **Target: 95%+** correlation

### Decision Impact Metrics

- **Recommendation Adoption**: % of benchmark recommendations followed
  - **Target: 70%+** (indicates useful recommendations)
- **Optimization ROI**: Savings from benchmark-driven optimization
  - **Target: 100x+** (benchmark cost vs savings)

### Performance Tracking

- **Regression Detection**: Time to detect model performance changes
  - **Target: <24 hours** with continuous benchmarking
- **Quality Stability**: Variation in model performance over time
  - **Target: <5%** variance month-over-month

## Advanced Options

### Flags

- `--category <name>`: Benchmark specific category only
- `--tasks <number>`: Number of tasks per model (default: 5)
- `--custom`: Use custom benchmark tasks
- `--tasks-file <path>`: JSON file with custom tasks
- `--validate`: Include human validation of results
- `--export <format>`: Export results (json, csv, pdf, markdown)
- `--output <path>`: Output file path
- `--continuous`: Enable continuous benchmarking
- `--interval <frequency>`: Benchmark frequency (hourly, daily, weekly)
- `--alert-on-regression`: Send alerts if performance degrades
- `--compare <date>`: Compare against previous benchmark
- `--models <haiku,sonnet,opus>`: Benchmark specific models only

### Custom Task Definition

Create custom benchmarks for your specific needs:

```json
{
  "benchmark_name": "Healthcare Compliance Tasks",
  "description": "HIPAA-compliant medical record processing",
  "tasks": [
    {
      "id": "hipaa-1",
      "category": "compliance-check",
      "description": "Review patient data handling for HIPAA compliance",
      "input": "path/to/code/patient-records.py",
      "expected_features": [
        "encryption at rest",
        "audit logging",
        "access controls"
      ],
      "quality_criteria": {
        "compliance_coverage": 10,
        "accuracy": 10,
        "false_positives": 8
      },
      "minimum_model": "opus",
      "rationale": "HIPAA requires comprehensive review"
    }
  ]
}
```

## Integration with Other Commands

```bash
# Benchmark before optimization
/model:benchmark --export json --output baseline.json

# Run optimization
/model:optimize

# Benchmark after optimization
/model:benchmark --export json --output optimized.json

# Compare results
/model:benchmark --compare baseline.json optimized.json

# Generate report
/model:report --benchmark-analysis baseline.json optimized.json
```

## Error Handling

**Benchmark Failures:**

```
⚠️ Benchmark Failure

Task: Security Audit
Model: Opus
Error: Timeout after 60s

Possible causes:
1. Task too complex for time limit
2. API performance issue
3. Task definition error

Actions taken:
- Retried with 120s timeout: SUCCESS
- Logged for investigation
- Continued with remaining tests

Recommendation: Review task complexity or increase timeout
```

**Quality Validation Disagreement:**

```
⚠️ Human Validation Conflict

Task: Code Review
Model: Sonnet
AI Quality Score: 9.1/10
Human Validator Score: 7.5/10
Disagreement: 1.6 points (18%)

Validator feedback:
"Missed subtle edge case in error handling"

Action: Incorporating feedback into quality scoring model
Status: Learning from human expert input
```

## Best Practices

1. **Benchmark regularly**: Run benchmarks monthly or after major changes
2. **Use representative tasks**: Benchmark tasks should match real workloads
3. **Include human validation**: Especially for quality-critical categories
4. **Track trends**: Monitor performance changes over time
5. **Act on findings**: Use benchmark results to guide optimization
6. **Document exceptions**: Note when you override benchmark recommendations
7. **Share results**: Make benchmark findings accessible to team
