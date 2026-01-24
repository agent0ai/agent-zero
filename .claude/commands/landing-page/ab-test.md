---
description: Create A/B test variants of landing page elements for conversion optimization
argument-hint: "[--element <headline|cta|hero|pricing>] [--variants <count>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Write
---

# Landing Page A/B Test Command

## Overview

Creates multiple variants of landing page elements for A/B testing to optimize conversion rates.

## Usage

```bash
# Test headlines
/landing-page:ab-test --element headline

# Test CTAs with 3 variants
/landing-page:ab-test --element cta --variants 3

# Test hero section
/landing-page:ab-test --element hero

# Test pricing display
/landing-page:ab-test --element pricing
```

## What This Command Does

1. **Analyzes current element** - Reviews existing copy/design
2. **Generates variants** - Creates 2-4 different versions
3. **Provides implementation** - Code for Vercel Edge Config or similar
4. **Sets up tracking** - Analytics events for each variant
5. **Recommends test duration** - Based on traffic estimates

## Test Elements

### Headlines

**Variant approaches:**

- Data-driven (lead with numbers)
- Problem-focused (emphasize pain point)
- Benefit-focused (highlight main benefit)
- Question format (engage with question)

**Example output:**

```
Variant A (Data-driven):
"Join 10,000+ Teams Closing Deals 3X Faster"

Variant B (Problem-focused):
"Tired of Losing Deals to Slow Follow-ups?"

Variant C (Benefit-focused):
"Close More Deals in Half the Time"

Variant D (Question):
"What If You Could Double Your Close Rate?"
```

### CTAs (Call-to-Action)

**Variant approaches:**

- Action-oriented ("Start", "Get", "Try")
- Benefit-oriented ("Save Time", "Grow Faster")
- Urgency-oriented ("Today", "Now", "Instant")
- Risk-reversal ("Free Trial", "No Credit Card")

**Example output:**

```
Variant A: "Start Free Trial" (action)
Variant B: "Save 10 Hours/Week" (benefit)
Variant C: "Get Instant Access" (urgency)
Variant D: "Try Free - No Credit Card" (risk reversal)
```

### Hero Images/Videos

**Variant approaches:**

- Product screenshot
- Customer using product
- Before/after comparison
- Demo video
- Illustration/animation

### Pricing Display

**Variant approaches:**

- Monthly vs annual toggle
- Most popular highlighted
- Price anchoring (show higher tier first)
- Feature comparison table
- Single CTA vs multiple tiers

## Implementation Code

For each variant test, provides Vercel Edge Config setup:

```typescript
// middleware.ts
import { get } from '@vercel/edge-config'
import { NextResponse } from 'next/server'

export async function middleware(request: Request) {
  // Get user's variant (sticky via cookie or random)
  let variant = request.cookies.get('ab_test_variant')?.value

  if (!variant) {
    // Assign random variant (50/50 split)
    variant = Math.random() < 0.5 ? 'A' : 'B'
  }

  const response = NextResponse.next()
  response.cookies.set('ab_test_variant', variant)

  return response
}
```

**Component with variants:**

```typescript
// components/Hero.tsx
import { cookies } from 'next/headers'

export function Hero() {
  const variant = cookies().get('ab_test_variant')?.value || 'A'

  const headlines = {
    A: "Join 10,000+ Teams Closing Deals 3X Faster",
    B: "Tired of Losing Deals to Slow Follow-ups?",
    C: "Close More Deals in Half the Time",
  }

  return (
    <h1>{headlines[variant]}</h1>
  )
}
```

**Analytics tracking:**

```typescript
// Track which variant user saw
posthog.capture('ab_test_view', {
  test: 'headline',
  variant: variant,
})

// Track conversion
posthog.capture('cta_clicked', {
  test: 'headline',
  variant: variant,
})
```

## Test Duration Calculator

Based on your traffic:

**Low traffic (< 1000 visitors/week):**

- Minimum: 4 weeks
- Confidence level: Lower (harder to reach statistical significance)
- Recommendation: Test big changes only

**Medium traffic (1000-10000 visitors/week):**

- Minimum: 2 weeks
- Confidence level: Medium
- Recommendation: Test major elements (headlines, CTAs)

**High traffic (> 10000 visitors/week):**

- Minimum: 1 week
- Confidence level: High
- Recommendation: Test minor variations

## Statistical Significance

**Provides calculator:**

```
Current conversion rate: 5%
Minimum detectable change: 20% (to 6%)
Required sample size per variant: 3,841 visitors
At 1,000 visitors/week: 8 weeks needed
```

## Best Practices

**Do:**

- ✅ Test one element at a time
- ✅ Run test until statistical significance
- ✅ Declare winner and implement
- ✅ Document learnings

**Don't:**

- ❌ Test multiple elements simultaneously
- ❌ Stop test early
- ❌ Ignore small sample sizes
- ❌ Keep testing forever without decision

## Example Workflow

```bash
# 1. Create baseline landing page
/landing-page:create --product "TaskFlow"

# 2. Generate headline variants
/landing-page:ab-test --element headline --variants 3

# 3. Implement A/B test code (provided by command)

# 4. Deploy to Vercel
vercel --prod

# 5. Monitor in PostHog/Vercel Analytics

# 6. After 2-4 weeks, declare winner

# 7. Implement winning variant permanently

# 8. Move to next element (CTA, pricing, etc.)
```

## Output Format

```markdown
# A/B Test Variants: [Element]

## Variant A (Control - Current)
[Current copy/design]

## Variant B (Test 1)
[Alternative version 1]
**Hypothesis:** [Why this might perform better]

## Variant C (Test 2)
[Alternative version 2]
**Hypothesis:** [Why this might perform better]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Implementation Code

[Middleware, component code, analytics tracking]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Test Configuration

**Element:** [headline|cta|hero|pricing]
**Variants:** [count]
**Traffic split:** 50/50 (or 33/33/33 for 3 variants)
**Primary metric:** Conversion rate
**Secondary metrics:** Bounce rate, time on page

**Estimated test duration:**
- Low traffic: 4 weeks
- Medium traffic: 2 weeks
- High traffic: 1 week

**Sample size needed:** [calculated]
**Current weekly traffic:** [if known]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Next Steps

1. [ ] Review variants and choose 2-3 to test
2. [ ] Implement code in landing page
3. [ ] Deploy to Vercel production
4. [ ] Verify tracking in analytics dashboard
5. [ ] Monitor for [duration] weeks
6. [ ] Analyze results when significant
7. [ ] Implement winner
8. [ ] Document learnings
9. [ ] Plan next test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

*Systematic A/B testing is the fastest way to improve conversion rates*
