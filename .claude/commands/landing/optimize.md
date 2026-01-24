---
description: Analyze and optimize landing page for conversion rate improvement
argument-hint: <landing-page-url> [--analyze-only]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, WebFetch, Read, Write
---

Optimize landing page: **${ARGUMENTS}**

## Conversion Rate Optimization

**Analysis Areas**:

- Copy effectiveness (headline, CTA, benefits)
- Visual hierarchy and layout
- Page speed and performance
- Mobile responsiveness
- Trust signals and social proof
- Form friction
- A/B test suggestions

Routes to **frontend-architect** + **ux-research-analyst**:

```javascript
await Task({
  subagent_type: 'frontend-architect',
  description: 'Landing page CRO analysis',
  prompt: `Analyze and optimize landing page: ${LANDING_PAGE_URL}

Fetch page content and perform comprehensive CRO analysis:

## 1. Fetch and Analyze Page

Use WebFetch to get page content.
Read any associated product files if local page.

## 2. Copy Analysis

**Headline Effectiveness**:
- Does it communicate clear value proposition?
- Is it benefit-driven (not feature-driven)?
- Does it answer "What's in it for me?"
- Character count optimal? (6-12 words ideal)

**Current**: [Extract current headline]
**Issues**: [What's wrong]
**Improved**: [Suggested rewrite]

**Subheadline**:
- Does it expand on headline?
- Is it specific and concrete?
- Length optimal? (15-25 words)

**CTA (Call to Action)**:
- Is it action-oriented? (Start, Get, Try vs Learn More)
- Does it communicate value? (Start Free Trial vs Submit)
- Placement above the fold?
- Button color contrasts with background?
- Multiple CTAs throughout page?

**Current CTA**: [Extract]
**Score**: [X/10]
**Improved**: [Suggestion]

## 3. Visual Hierarchy Analysis

**F-Pattern/Z-Pattern**:
- Does layout follow natural eye movement?
- Most important elements in prime positions?

**Contrast & Readability**:
- Text contrast ratio ≥ 4.5:1 (WCAG AA)?
- Font size readable? (16px+ for body)
- Line length optimal? (50-75 characters)

**White Space**:
- Enough breathing room?
- Cluttered vs clean?

**Score**: [X/10]
**Issues**: [List issues]
**Improvements**: [Specific suggestions]

## 4. Performance Analysis

**Page Speed**:
- Load time < 2 seconds?
- Images optimized?
- Unnecessary scripts?
- Lazy loading enabled?

Test with Lighthouse/PageSpeed Insights.

**Current Load Time**: [X seconds]
**Target**: < 2 seconds
**Issues**: [Bottlenecks]
**Fixes**: [Specific optimizations]

## 5. Mobile Responsiveness

**Mobile-First Check**:
- Responsive design?
- Touch targets ≥ 44x44 px?
- Text readable without zooming?
- Horizontal scrolling?
- Mobile CTA easily clickable?

**Score**: [X/10]
**Issues**: [Problems on mobile]

## 6. Trust Signals

**Social Proof**:
- Customer testimonials present? (need 3-5)
- Customer logos? (recognizable brands)
- User count/stats? ("Join 10,000+ users")
- Reviews/ratings?

**Current**: [What's present]
**Missing**: [What should be added]
**Impact**: High/Medium/Low

**Security Indicators**:
- SSL badge?
- Privacy policy linked?
- Money-back guarantee?
- Trust badges (BBB, verified, etc.)?

## 7. Form Friction Analysis

**Form Fields**:
- Field count minimal? (< 5 fields ideal)
- Required fields clearly marked?
- Inline validation?
- Error messages helpful?
- Auto-complete enabled?

**Current**: [X fields]
**Recommended**: [Y fields - which to remove]

**Submit Button**:
- Clear what happens after submit?
- No "Submit" - use action word
- Loading state indication?

## 8. Conversion Funnel

**Above the Fold**:
- Value prop clear?
- CTA visible?
- No distractions?

**Mid-Page**:
- Features/benefits compelling?
- Social proof present?
- Objections addressed?

**Bottom**:
- Final CTA strong?
- FAQ addresses concerns?
- No friction to convert?

## 9. A/B Test Suggestions

Generate 3-5 high-impact A/B tests:

**Test 1: Headline Variation**
- Control: [Current headline]
- Variant: [Improved headline]
- Expected Impact: +[X]% conversions
- Effort: Low

**Test 2: CTA Button**
- Control: [Current CTA]
- Variant A: [Different copy]
- Variant B: [Different color]
- Expected Impact: +[X]% clicks

**Test 3: Social Proof Placement**
- Control: [Current location]
- Variant: [Move to above fold]
- Expected Impact: +[X]% trust

**Test 4: Form Fields**
- Control: [X fields]
- Variant: [Y fields - remove least critical]
- Expected Impact: +[X]% completions

**Test 5: Pricing Display**
- Control: [Current format]
- Variant: [Annual savings highlighted]
- Expected Impact: +[X]% conversions

## 10. Comprehensive Optimization Report

\`\`\`markdown
# Landing Page Optimization Report

**Page**: ${LANDING_PAGE_URL}
**Analyzed**: [Date]
**Current Conversion Rate**: [X%] (if known)

## Overall Score: [X/100]

**Breakdown**:
- Copy: [X/20]
- Visual Design: [X/20]
- Performance: [X/20]
- Mobile: [X/15]
- Trust Signals: [X/15]
- Form Optimization: [X/10]

## Critical Issues (Fix Immediately)

### Issue 1: [Title]
**Impact**: High
**Current**: [Problem]
**Fix**: [Solution]
**Expected Lift**: +[X]% conversions

### Issue 2: [Title]
**Impact**: High
**Current**: [Problem]
**Fix**: [Solution]

## Quick Wins (< 1 hour to fix)

1. [Fix 1] - Expected: +[X]% conversions
2. [Fix 2] - Expected: +[X]% conversions
3. [Fix 3] - Expected: +[X]% conversions

## Detailed Recommendations

### Copy Improvements
- **Headline**: [Rewrite suggestion]
- **Subheadline**: [Improvement]
- **CTA**: [Action-oriented copy]
- **Benefits**: [Reframe features as benefits]

### Design Changes
- Increase headline size to 48px
- Move CTA above the fold
- Add customer logos section
- Improve visual hierarchy with better spacing

### Performance Optimizations
- Compress images (current: 2.5MB, target: < 500KB)
- Enable lazy loading for images
- Minify CSS/JS (save 45KB)
- Use CDN for assets

### Mobile Optimizations
- Increase touch target sizes to 48px
- Simplify mobile navigation
- Stack form fields vertically
- Larger mobile CTA button

### Trust Building
- Add 3-5 customer testimonials
- Include customer logos (if available)
- Add "Join 10,000+ users" stat
- Display security badges

### Form Optimization
- Reduce from 7 fields to 3 (email, name, company)
- Add inline validation
- Change "Submit" to "Start Free Trial"
- Add privacy note under form

## A/B Test Priority Queue

1. **Headline Rewrite** (Highest Impact)
   - Expected: +15-25% improvement
   - Effort: 5 minutes
   - Test duration: 2 weeks

2. **CTA Button Copy**
   - Expected: +10-15% improvement
   - Effort: 2 minutes
   - Test duration: 1 week

3. **Form Field Reduction**
   - Expected: +20-30% completions
   - Effort: 30 minutes
   - Test duration: 2 weeks

## Implementation Checklist

**Week 1: Quick Wins**
- [ ] Update headline
- [ ] Improve CTA copy
- [ ] Add customer testimonials
- [ ] Optimize images

**Week 2: A/B Tests**
- [ ] Set up headline test
- [ ] Set up CTA test
- [ ] Set up form test

**Week 3: Performance**
- [ ] Implement lazy loading
- [ ] Minify assets
- [ ] Enable CDN

**Week 4: Measure & Iterate**
- [ ] Analyze A/B test results
- [ ] Implement winners
- [ ] Plan next round of tests

## Predicted Impact

**Current Conversion Rate**: [X%]
**After Quick Wins**: [X+Y]%
**After All Optimizations**: [X+Z]%

**Expected ROI**:
- If 1,000 visitors/month
- Current: [X] conversions
- After optimization: [Y] conversions
- Additional revenue: $[Z]/month
\`\`\`

Save report to: landing-pages/[product]-optimization-report-[date].md

If --analyze-only NOT set:
  - Generate optimized HTML/CSS
  - Show side-by-side comparison
  - Request approval to deploy changes
  `
})
```

## Example Output

```
Landing Page Optimization Report
═══════════════════════════════════
Page: https://myproduct.com
Overall Score: 68/100

Critical Issues (2):

1. CTA Below the Fold [HIGH IMPACT]
   Current: "Learn More" button at 800px down
   Fix: Move "Start Free Trial" to hero section
   Expected Lift: +25% conversions

2. Page Load Time: 4.2 seconds [HIGH IMPACT]
   Current: Unoptimized images (2.5MB)
   Fix: Compress images, enable lazy loading
   Expected Lift: +15% conversions (faster = better)

Quick Wins (< 1 hour):
✓ Update headline: "Save 10 hours/week" → "Automate Your Workflow in Minutes"
✓ Change CTA: "Submit" → "Start Free Trial"
✓ Add social proof: "Join 10,000+ users"
Expected Combined Lift: +30-40% conversions

A/B Test Priority:
1. Headline (test in 2 weeks, expected +20%)
2. CTA color (test in 1 week, expected +10%)
3. Form fields: 7 → 3 (test in 2 weeks, expected +25%)

[Generate Optimized Version] [Setup A/B Tests] [View Full Report]
```

## Success Criteria

- ✓ Comprehensive CRO analysis completed
- ✓ Overall score calculated (0-100)
- ✓ Critical issues identified with impact
- ✓ Quick wins prioritized (< 1 hour fixes)
- ✓ A/B test suggestions with expected impact
- ✓ Implementation checklist provided
- ✓ Predicted conversion improvement
- ✓ Optimization report saved

---
**Uses**: frontend-architect, ux-research-analyst
**Output**: CRO report + optimized version (optional)
**Next Commands**: `/landing/ab-test`, `/landing/create` (deploy optimized version)
**Expected Impact**: 20-50% conversion rate improvement
