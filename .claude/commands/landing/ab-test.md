---
description: Set up A/B tests for landing page optimization
argument-hint: <landing-page-url> --variant <headline|cta|pricing|form|layout>
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Write, Bash
---

Setup A/B test: **${ARGUMENTS}**

## A/B Testing Setup

**Test Variants**: Headline, CTA, pricing display, form fields, layout
**Statistical Significance**: Minimum 95% confidence
**Sample Size**: Auto-calculated based on current traffic
**Integration**: Zoho PageSense, Google Optimize, or custom

Routes to **frontend-architect**:

```javascript
await Task({
  subagent_type: 'frontend-architect',
  description: 'Setup A/B test',
  prompt: `Setup A/B test for: ${LANDING_PAGE_URL}

Variant to test: ${VARIANT}

Create A/B test configuration:

## 1. Define Test Hypothesis

**Variant**: ${VARIANT}

**Hypothesis Template**:
"By changing [element] from [control] to [variant], we expect [metric] to improve by [X]% because [reasoning]."

Examples:
- "By changing headline from 'Best Project Management Tool' to 'Manage Projects 3x Faster', we expect signups to improve by 20% because it's more benefit-driven and specific."
- "By changing CTA from 'Learn More' to 'Start Free Trial', we expect clicks to improve by 15% because it's more action-oriented."

Generate hypothesis for ${VARIANT}.

## 2. Create Test Variants

### Control (Current)
[Document current state]

### Variant A
**Change**: [What's different]
**Rationale**: [Why this might work better]
**Expected Impact**: +[X]% improvement

### Variant B (Optional)
**Change**: [Alternative variation]
**Rationale**: [Why this might work better]

## 3. Calculate Sample Size

Based on current traffic and conversion rate:

\`\`\`javascript
// Sample size calculator
function calculateSampleSize(baseRate, minDetectableEffect, significance = 0.95, power = 0.80) {
  // Simplified calculation
  const z_alpha = 1.96; // 95% confidence
  const z_beta = 0.84;  // 80% power

  const p1 = baseRate;
  const p2 = baseRate * (1 + minDetectableEffect);
  const p_avg = (p1 + p2) / 2;

  const numerator = Math.pow(z_alpha + z_beta, 2) * p_avg * (1 - p_avg);
  const denominator = Math.pow(p2 - p1, 2);

  return Math.ceil(2 * (numerator / denominator));
}

// Example:
// Base conversion: 2%
// Want to detect: 20% improvement (2% → 2.4%)
// Sample needed: ~15,000 visitors per variant

const sampleSize = calculateSampleSize(${BASE_RATE}, ${MIN_EFFECT});
const daysToComplete = sampleSize / (${DAILY_TRAFFIC} / 2); // Split 50/50

console.log(\`Sample size needed: \${sampleSize} per variant\`);
console.log(\`Days to complete: \${Math.ceil(daysToComplete)} days\`);
\`\`\`

## 4. Zoho PageSense Configuration

\`\`\`javascript
// Zoho PageSense A/B test setup
const testConfig = {
  name: "${VARIANT} Test - ${LANDING_PAGE_URL}",
  url: "${LANDING_PAGE_URL}",
  type: "A/B",
  variants: [
    {
      name: "Control",
      traffic_allocation: 50,
      changes: [] // No changes, current version
    },
    {
      name: "Variant A",
      traffic_allocation: 50,
      changes: [
        {
          selector: ${SELECTOR},
          property: ${PROPERTY},
          value: ${NEW_VALUE}
        }
      ]
    }
  ],
  goals: [
    {
      name: "Form Submission",
      type: "click",
      selector: "button[type='submit']"
    }
  ],
  audience: {
    include: "all",
    exclude: ["bots", "returning_visitors"] // Test on new visitors only
  },
  duration: {
    start: "immediate",
    end: "auto" // End when statistical significance reached
  }
};

// Deploy test via PageSense API
await deployABTest(testConfig);
\`\`\`

## 5. Google Optimize Configuration (Alternative)

\`\`\`html
<!-- Google Optimize Container -->
<script src="https://www.googleoptimize.com/optimize.js?id=OPT-XXXXXX"></script>

<script>
// Define test variants
const variants = {
  '0': 'control',
  '1': 'variant_a',
  '2': 'variant_b'
};

// Get assigned variant
const variant = window.google_optimize.get('EXPERIMENT_ID');

// Apply changes based on variant
if (variant === '1') {
  // Variant A changes
  document.querySelector('${SELECTOR}').${PROPERTY} = '${NEW_VALUE}';
}
</script>
\`\`\`

## 6. Test-Specific Configurations

### Headline Test
\`\`\`javascript
{
  variant: "headline",
  selector: "h1.hero-headline",
  control: "${CURRENT_HEADLINE}",
  variant_a: "${NEW_HEADLINE_A}",
  variant_b: "${NEW_HEADLINE_B}",
  metric: "signup_rate",
  expected_lift: "15-25%"
}
\`\`\`

### CTA Test
\`\`\`javascript
{
  variant: "cta",
  selector: "button.primary-cta",
  control: {
    text: "Learn More",
    color: "#007bff"
  },
  variant_a: {
    text: "Start Free Trial",
    color: "#007bff"
  },
  variant_b: {
    text: "Get Started Free",
    color: "#28a745"
  },
  metric: "cta_clicks",
  expected_lift: "10-20%"
}
\`\`\`

### Form Test
\`\`\`javascript
{
  variant: "form",
  selector: "form.signup-form",
  control: {
    fields: ["name", "email", "company", "phone", "role", "team_size", "message"]
  },
  variant_a: {
    fields: ["name", "email", "company"] // Simplified
  },
  variant_b: {
    fields: ["email", "password"] // Minimal
  },
  metric: "form_completion_rate",
  expected_lift: "20-40%"
}
\`\`\`

### Pricing Test
\`\`\`javascript
{
  variant: "pricing",
  selector: "div.pricing-tiers",
  control: "monthly_pricing",
  variant_a: "annual_savings_highlighted",
  variant_b: "tiered_comparison_table",
  metric: "trial_starts",
  expected_lift: "15-30%"
}
\`\`\`

## 7. Monitoring & Analysis

**Key Metrics to Track**:
- Primary: [Conversion rate, signups, trial starts]
- Secondary: [Bounce rate, time on page, scroll depth]
- Guardrail: [Page load time doesn't degrade]

**Stop Conditions**:
- Statistical significance reached (95% confidence)
- Sample size achieved
- Clear winner emerges (>20% lift with 99% confidence)
- Test duration > 2 weeks (minimum)

**Analysis Dashboard**:
\`\`\`
A/B Test Results - ${VARIANT}
═══════════════════════════════════
Duration: 14 days
Visitors: 10,000 per variant

Control:
  Visitors: 10,000
  Conversions: 200
  Rate: 2.00%

Variant A:
  Visitors: 10,000
  Conversions: 250
  Rate: 2.50%
  Improvement: +25.0% ↑
  Confidence: 99.2% ✓

Variant B:
  Visitors: 10,000
  Conversions: 190
  Rate: 1.90%
  Improvement: -5.0% ↓
  Confidence: 87.3%

Winner: Variant A
Recommendation: Deploy Variant A to 100% of traffic

Expected Annual Impact:
  Current: 200 conversions/month
  With Variant A: 250 conversions/month
  Additional: +50 conversions/month
  Revenue Impact: +$2,500/month (at $50 LTV)
═══════════════════════════════════
\`\`\`

## 8. Implementation Guide

**Step 1: Create Variants**
\`\`\`bash
# Create variant HTML files
cp landing-page.html landing-page-control.html
cp landing-page.html landing-page-variant-a.html

# Edit variant A
# Change: [specific change for ${VARIANT}]
\`\`\`

**Step 2: Deploy Test**
\`\`\`bash
# Using Zoho PageSense
curl -X POST "https://www.zoho.com/pagesense/api/experiments" \\
  -H "Authorization: Bearer \${ZOHO_TOKEN}" \\
  -d @ab-test-config.json

# Or deploy to staging for preview
/landing/create variant-a --environment staging
\`\`\`

**Step 3: Monitor Results**
\`\`\`bash
# Check test status daily
curl "https://www.zoho.com/pagesense/api/experiments/\${TEST_ID}/results" \\
  -H "Authorization: Bearer \${ZOHO_TOKEN}"
\`\`\`

**Step 4: Deploy Winner**
When test completes:
- If Variant A wins → Deploy to 100%
- If Control wins → Keep current version
- If inconclusive → Run longer or try different variant

## 9. Generate Test Report

\`\`\`markdown
# A/B Test Setup Report

**Test Name**: ${VARIANT} Test
**Page**: ${LANDING_PAGE_URL}
**Start Date**: [Today]
**Expected End**: [Date + calculated days]

## Hypothesis
${HYPOTHESIS}

## Variants

### Control
${CONTROL_DESCRIPTION}

### Variant A
${VARIANT_A_DESCRIPTION}
Expected Impact: +${EXPECTED_LIFT}%

### Variant B (if applicable)
${VARIANT_B_DESCRIPTION}

## Test Configuration

**Sample Size**: ${SAMPLE_SIZE} visitors per variant
**Traffic Split**: 50% Control / 50% Variant
**Duration**: ${DURATION} days (estimated)
**Significance Level**: 95%
**Minimum Detectable Effect**: ${MIN_EFFECT}%

## Success Metrics

**Primary**: ${PRIMARY_METRIC}
**Secondary**: ${SECONDARY_METRICS}
**Guardrail**: Page load time < 2s

## Implementation

- [ ] Variants created
- [ ] Test configured in Zoho PageSense
- [ ] Tracking verified
- [ ] Test launched

## Monitoring Plan

- Check results daily
- Alert if guardrail metrics degrade
- Stop test early if 99% confidence reached
- Minimum 2-week test duration

## Decision Criteria

**Deploy Variant if**:
- 95%+ confidence
- 10%+ improvement
- No degradation in secondary metrics

**Keep Control if**:
- No significant improvement
- Variant degrades experience

\`\`\`

Save to: ab-tests/${VARIANT}-test-${DATE}.md
  `
})
```

## Usage Examples

```bash
# Test headline variations
/landing/ab-test https://myproduct.com --variant headline

# Test CTA button
/landing/ab-test https://myproduct.com --variant cta

# Test form field reduction
/landing/ab-test https://myproduct.com --variant form

# Test pricing display
/landing/ab-test https://myproduct.com --variant pricing
```

## Success Criteria

- ✓ Clear hypothesis defined
- ✓ Control and variant(s) created
- ✓ Sample size calculated
- ✓ Test configured in PageSense/Optimize
- ✓ Tracking verified
- ✓ Monitoring dashboard setup
- ✓ Decision criteria established
- ✓ Test launched successfully

---
**Uses**: frontend-architect
**Output**: A/B test configuration + monitoring dashboard
**Next Commands**: `/landing/optimize` (after test completes)
**Expected Impact**: 10-40% conversion improvement (if variant wins)
**Duration**: 1-4 weeks depending on traffic
