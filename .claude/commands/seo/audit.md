---
description: Comprehensive SEO audit covering technical SEO, on-page, off-page, and Core Web Vitals with actionable recommendations
argument-hint: [--url <url>] [--depth <shallow|medium|deep>] [--competitor-analysis]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, WebFetch, Bash
---

SEO Audit: **${ARGUMENTS}**

## Performing Comprehensive SEO Audit

Use the Task tool with subagent_type=seo-specialist to conduct a complete SEO audit with the following specifications:

### Input Parameters

**URL**: ${URL:-current-site} (Website to audit)
**Depth**: ${DEPTH:-medium} (shallow, medium, deep)
**Competitor Analysis**: ${COMPETITOR_ANALYSIS:-false}
**Export Format**: ${FORMAT:-html} (html, pdf, json, markdown)

### Objectives

You are tasked with performing a comprehensive SEO audit that identifies all optimization opportunities. Your implementation must:

#### 1. Technical SEO Audit

**Site Crawl and Analysis**:

```javascript
// Technical SEO checks
const technicalChecks = {
  // Crawlability
  robotsTxt: {
    exists: true,
    accessible: 'https://example.com/robots.txt',
    issues: [],
    blocking: ['admin/', 'private/'],
    status: 'PASS'
  },

  sitemapXml: {
    exists: true,
    url: 'https://example.com/sitemap.xml',
    pages: 1250,
    errors: 0,
    lastModified: '2024-11-15',
    status: 'PASS'
  },

  // Indexability
  indexation: {
    indexablePages: 1200,
    noindexPages: 50,
    blocked: 0,
    orphanPages: 15,
    status: 'WARNING'  // Orphan pages found
  },

  // Site Speed (Core Web Vitals)
  coreWebVitals: {
    LCP: 1.8,  // Largest Contentful Paint (target: <2.5s)
    FID: 45,   // First Input Delay (target: <100ms)
    CLS: 0.08, // Cumulative Layout Shift (target: <0.1)
    FCP: 1.2,  // First Contentful Paint
    TTI: 2.5,  // Time to Interactive
    TBT: 180,  // Total Blocking Time
    SI: 2.1,   // Speed Index
    status: 'GOOD'
  },

  // Mobile Usability
  mobileFriendly: {
    responsive: true,
    viewport: true,
    tapTargets: true,
    fontSizes: true,
    flashUsage: false,
    score: 95,
    status: 'PASS'
  },

  // HTTPS & Security
  https: {
    enforced: true,
    certificate: {
      valid: true,
      issuer: "Let's Encrypt",
      expires: '2025-02-15'
    },
    mixedContent: false,
    hsts: true,
    status: 'PASS'
  },

  // Structured Data
  structuredData: {
    found: true,
    types: ['Organization', 'WebSite', 'BreadcrumbList', 'Article'],
    errors: 2,
    warnings: 5,
    status: 'WARNING'
  },

  // Canonical URLs
  canonicals: {
    implemented: true,
    selfReferencing: 1180,
    crossDomain: 0,
    conflicts: 3,
    status: 'WARNING'
  },

  // Pagination
  pagination: {
    relNextPrev: false,  // Deprecated but still useful
    canonicalChaining: false,
    status: 'INFO'
  },

  // International SEO
  hreflang: {
    implemented: false,
    languages: 1,
    errors: 0,
    status: 'N/A'
  }
};
```

**Performance Analysis**:

```markdown
## Core Web Vitals Assessment

### Desktop Performance
| Metric | Score | Status | Target |
|--------|-------|--------|--------|
| LCP | 1.8s | ✅ GOOD | <2.5s |
| FID | 45ms | ✅ GOOD | <100ms |
| CLS | 0.08 | ✅ GOOD | <0.1 |
| FCP | 1.2s | ✅ GOOD | <1.8s |
| TTI | 2.5s | ✅ GOOD | <3.8s |
| TBT | 180ms | ⚠️ NEEDS IMPROVEMENT | <200ms |
| SI | 2.1s | ✅ GOOD | <3.4s |

**Overall Desktop Score**: 92/100 (Good)

### Mobile Performance
| Metric | Score | Status | Target |
|--------|-------|--------|--------|
| LCP | 2.4s | ✅ GOOD | <2.5s |
| FID | 68ms | ✅ GOOD | <100ms |
| CLS | 0.12 | ⚠️ NEEDS IMPROVEMENT | <0.1 |
| FCP | 1.8s | ✅ GOOD | <1.8s |
| TTI | 3.5s | ✅ GOOD | <3.8s |
| TBT | 240ms | ⚠️ NEEDS IMPROVEMENT | <200ms |
| SI | 3.0s | ✅ GOOD | <3.4s |

**Overall Mobile Score**: 78/100 (Needs Improvement)

### Performance Issues
1. **Layout shift on hero section** (CLS 0.12 mobile)
   - Cause: Images without width/height attributes
   - Fix: Add explicit dimensions to all images
   - Impact: +14 points

2. **Long JavaScript execution** (TBT 240ms mobile)
   - Cause: Large third-party analytics bundle
   - Fix: Defer non-critical scripts, code-split
   - Impact: +8 points

3. **Render-blocking resources**
   - 3 CSS files (145KB total)
   - 2 font files (80KB)
   - Fix: Inline critical CSS, preload fonts
   - Impact: +5 points
```

#### 2. On-Page SEO Audit

**Content Analysis**:

```markdown
## Page-Level SEO Analysis

### Homepage (/)

**Title Tag**: "Best SaaS Platform for Project Management | CompanyName"
- Length: 62 characters ✅ (50-60 optimal)
- Keywords: ✅ Primary keyword included
- Branding: ✅ Company name included
- Uniqueness: ✅ Unique across site
- **Score**: 95/100

**Meta Description**: "Streamline your projects with our award-winning SaaS platform. Features include task management, team collaboration, and real-time reporting. Try free for 14 days."
- Length: 168 characters ✅ (150-160 optimal)
- Call-to-action: ✅ "Try free"
- Keywords: ✅ Relevant keywords
- Persuasive: ✅ Benefits-focused
- **Score**: 92/100

**H1 Heading**: "Project Management Made Simple"
- Count: 1 ✅ (exactly one H1)
- Length: 30 characters ✅
- Keywords: ✅ Includes target keywords
- Matches title intent: ✅
- **Score**: 98/100

**Heading Structure**:
```

H1: Project Management Made Simple (1)
  H2: Features (1)
    H3: Task Management (1)
    H3: Team Collaboration (1)
    H3: Reporting & Analytics (1)
  H2: Pricing (1)
    H3: Starter Plan (1)
    H3: Professional Plan (1)
    H3: Enterprise Plan (1)
  H2: Testimonials (1)

```
- Hierarchy: ✅ Logical structure
- Skipped levels: ❌ None
- Multiple H1s: ✅ Only one
- **Score**: 100/100

**Content Quality**:
- Word count: 1,850 ✅ (>1,500 for competitive keywords)
- Keyword density: 1.8% ✅ (1-2% optimal)
- LSI keywords: ✅ 12 related terms found
- Readability: 68 (Flesch Reading Ease) ✅
- Grammar: 2 minor issues ⚠️
- **Score**: 88/100

**Internal Linking**:
- Internal links: 24
- External links: 5
- Broken links: 0 ✅
- Anchor text: ✅ Descriptive
- Deep links: ⚠️ Only 3 (increase recommended)
- **Score**: 82/100

**Image Optimization**:
- Total images: 18
- Alt text: 16/18 ⚠️ (2 missing)
- File size: ⚠️ 3 images >200KB
- Format: ✅ WebP used (12/18)
- Lazy loading: ✅ Implemented
- Dimensions: ⚠️ 4 missing width/height
- **Score**: 75/100

### Issues Found Across Site

**Critical** (Fix Immediately):
1. **Missing alt text** on 45 images (3% of total)
   - Impact: Accessibility + Image SEO
   - Pages affected: 12
   - Fix: Add descriptive alt text to all images

2. **Duplicate title tags** on 8 pages
   - Impact: Search engine confusion
   - Examples: /blog/post-1, /blog/post-2 both have "Blog Post"
   - Fix: Make all title tags unique

3. **Thin content** on 15 pages (<300 words)
   - Impact: Low rankings
   - Pages: Category pages, old blog posts
   - Fix: Expand content or consolidate pages

**High Priority**:
4. **Missing meta descriptions** on 22 pages
   - Impact: Lower click-through rates
   - Pages: Product pages, blog posts
   - Fix: Write unique descriptions for each

5. **Broken internal links**: 12 instances
   - Impact: User experience + crawl budget
   - Fix: Update or remove broken links

6. **Multiple H1 tags** on 6 pages
   - Impact: SEO dilution
   - Fix: Use single H1, convert others to H2

**Medium Priority**:
7. **Large images** slowing load time
   - 34 images >200KB
   - Fix: Compress + convert to WebP

8. **Missing canonical tags** on 18 pages
   - Risk: Duplicate content issues
   - Fix: Add self-referencing canonicals
```

#### 3. Off-Page SEO Audit

**Backlink Analysis**:

```markdown
## Backlink Profile

**Summary**:
- Total backlinks: 1,245
- Referring domains: 387
- Domain Rating (DR): 58/100
- Trust Flow: 34
- Citation Flow: 42
- Trust Ratio: 0.81 ✅ (healthy)

**Link Quality Distribution**:
| Quality | Count | Percentage |
|---------|-------|------------|
| High (DR 50+) | 156 | 40% ✅ |
| Medium (DR 20-49) | 178 | 46% ✅ |
| Low (DR 0-19) | 53 | 14% ⚠️ |

**Anchor Text Distribution**:
| Type | Count | Percentage | Health |
|------|-------|------------|--------|
| Branded | 487 | 39% | ✅ Natural |
| Naked URL | 311 | 25% | ✅ Natural |
| Generic | 249 | 20% | ✅ Natural |
| Exact Match | 124 | 10% | ✅ Safe |
| Partial Match | 74 | 6% | ✅ Safe |

**Toxic Links**: 8 domains (2% of total)
- Spam score >40%
- Action: Disavow recommended

**Link Velocity**:
- New links this month: 23
- Lost links: 12
- Net gain: +11 ✅ Healthy growth

**Top Linking Domains**:
1. techcrunch.com (DR 93) - 3 links
2. forbes.com (DR 94) - 2 links
3. producthunt.com (DR 87) - 5 links
4. github.com (DR 96) - 12 links (user profiles)
5. reddit.com (DR 91) - 8 links (r/productivity)

**Opportunities**:
- Competitor has 156 more referring domains
- Missing links from top industry publications
- No links from .edu or .gov domains
```

#### 4. Competitor Analysis

**Top 3 Competitors**:

```markdown
## Competitive Landscape

| Metric | Your Site | Competitor A | Competitor B | Competitor C |
|--------|-----------|--------------|--------------|--------------|
| **Domain Authority** | 58 | 67 ↑ | 62 ↑ | 54 ↓ |
| **Organic Keywords** | 2,340 | 4,120 ↑ | 3,200 ↑ | 1,890 ↓ |
| **Organic Traffic** | 12,500/mo | 28,000/mo ↑ | 18,500/mo ↑ | 9,200/mo ↓ |
| **Backlinks** | 1,245 | 3,450 ↑ | 2,100 ↑ | 890 ↓ |
| **Referring Domains** | 387 | 892 ↑ | 621 ↑ | 278 ↓ |
| **Page Speed (Mobile)** | 78 | 85 ↑ | 72 ↓ | 81 ↑ |
| **Content Pages** | 145 | 320 ↑ | 210 ↑ | 98 ↓ |

### Keyword Gap Analysis

**Keywords competitors rank for (you don't)**:
1. "project management software comparison" - Comp A ranks #3 (1,200 monthly searches)
2. "best pm tool for remote teams" - Comp B ranks #2 (800 searches)
3. "agile project management guide" - Comp A ranks #1 (2,400 searches)
4. "project tracking templates" - Comp B ranks #4 (950 searches)
5. "team collaboration platform" - Comp A ranks #2 (1,600 searches)

**Total opportunity**: 7,000+ monthly searches

### Content Gap Analysis

**Competitor A has, you don't**:
- Comprehensive comparison guides (15 articles)
- Industry-specific case studies (22 articles)
- Video tutorials (38 videos)
- Free templates library (50+ templates)
- Weekly podcast (45 episodes)

### Link Gap Analysis

**High-value domains linking to competitors**:
1. capterra.com (DR 94) - Links to A & B, not you
2. g2.com (DR 88) - Links to all competitors
3. softwareadvice.com (DR 82) - Links to A & C
4. makeuseof.com (DR 76) - Links to B only
5. zapier.com/blog (DR 85) - Links to A only

**Action**: Pursue listings/mentions on these platforms
```

#### 5. Local SEO Audit (if applicable)

```markdown
## Local SEO Performance

**Google Business Profile**:
- Verified: ✅
- Complete: 92%
- Photos: 45 ✅
- Reviews: 287 (4.6★) ✅
- Posts: Last posted 2 days ago ✅
- Questions: 12 answered ✅
- Attributes: Complete ✅

**Local Citations**:
- Found: 78 citations
- NAP consistency: 94% ✅
- Top directories: ✅ Listed
- Industry directories: ⚠️ Missing 4

**Local Keywords**:
- Ranking for: 24/30 target keywords
- "Project management Boston": #3
- "Boston PM software": #8
- "Project tools near me": #12

**Reviews**:
- Average rating: 4.6/5 ✅
- Total reviews: 287
- Review velocity: 12/month ✅
- Response rate: 98% ✅
- Response time: <24 hours ✅
```

### Implementation Steps

**Step 1: Crawl & Analyze**

1. Crawl entire website (all pages)
2. Check robots.txt and sitemap
3. Analyze site structure
4. Identify indexation issues

**Step 2: Technical Assessment**

1. Run Lighthouse audits
2. Check Core Web Vitals
3. Test mobile usability
4. Verify HTTPS implementation
5. Analyze structured data

**Step 3: Content Audit**

1. Review all title tags and meta descriptions
2. Analyze heading structure
3. Check content quality and length
4. Identify thin/duplicate content
5. Review internal linking

**Step 4: Backlink Analysis**

1. Export backlink profile
2. Analyze link quality
3. Identify toxic links
4. Review anchor text distribution
5. Compare with competitors

**Step 5: Recommendations**

1. Prioritize issues by impact
2. Generate action plan
3. Estimate implementation time
4. Project ranking improvements

### Output Requirements

**Generated Files**:

- `SEO_AUDIT_REPORT.html` - Complete audit report
- `SEO_ACTION_PLAN.md` - Prioritized recommendations
- `TECHNICAL_ISSUES.csv` - List of technical problems
- `CONTENT_GAPS.csv` - Content opportunities
- `BACKLINK_ANALYSIS.json` - Link profile data

**SEO Audit Report Structure**:

```markdown
# SEO Audit Report - example.com

**Date**: November 15, 2024
**Overall SEO Score**: 72/100

---

## Executive Summary

Your website has a solid SEO foundation but significant opportunities for improvement:

**Strengths**:
- ✅ Strong Core Web Vitals (desktop)
- ✅ Mobile-friendly design
- ✅ HTTPS properly implemented
- ✅ Quality backlink profile
- ✅ Good content depth on key pages

**Weaknesses**:
- ❌ 45 images missing alt text
- ❌ 8 pages with duplicate titles
- ❌ Mobile performance needs improvement (CLS issues)
- ❌ 387 fewer referring domains than top competitor
- ❌ Missing 7,000+ monthly search opportunities

**Quick Wins** (High Impact, Low Effort):
1. Add missing alt text (2 hours) → +5 points
2. Fix duplicate titles (1 hour) → +4 points
3. Add missing meta descriptions (3 hours) → +3 points
4. Compress large images (1 hour) → +8 performance points

**Potential Traffic Impact**:
- Fix critical issues: +15% organic traffic (est. +1,875 monthly visits)
- Implement all recommendations: +45% organic traffic (est. +5,625 visits)

---

## Detailed Findings

[Technical SEO section]
[On-Page SEO section]
[Off-Page SEO section]
[Competitor Analysis section]

---

## Action Plan (Prioritized)

### Phase 1: Quick Wins (Week 1)
**Effort**: 8 hours
**Impact**: +15% traffic

1. ✅ Add alt text to all images
2. ✅ Fix duplicate title tags
3. ✅ Write meta descriptions
4. ✅ Compress large images

### Phase 2: Technical Optimization (Weeks 2-3)
**Effort**: 20 hours
**Impact**: +12% traffic

1. ⚙️ Fix layout shift issues
2. ⚙️ Defer non-critical JavaScript
3. ⚙️ Implement code splitting
4. ⚙️ Add missing canonicals

### Phase 3: Content Expansion (Ongoing)
**Effort**: 40 hours/month
**Impact**: +18% traffic

1. 📝 Create comparison guides
2. 📝 Write case studies
3. 📝 Expand thin content
4. 📝 Target keyword gaps

### Phase 4: Link Building (Ongoing)
**Effort**: 20 hours/month
**Impact**: +15% over 6 months

1. 🔗 Get listed on review sites
2. 🔗 Create linkable assets
3. 🔗 Outreach to industry publications
4. 🔗 Build relationships with bloggers

---

## ROI Projection

**Current Performance**:
- Organic traffic: 12,500/month
- Conversion rate: 2.5%
- Conversions: 313/month
- Value per conversion: $120
- Monthly value: $37,560

**After Phase 1** (Month 1):
- Traffic: 14,375/month (+15%)
- Conversions: 360/month
- Monthly value: $43,200
- **Gain**: +$5,640/month

**After All Phases** (Month 6):
- Traffic: 18,125/month (+45%)
- Conversions: 453/month
- Monthly value: $54,375
- **Gain**: +$16,815/month

**12-Month ROI**: $201,780
**Implementation Cost**: ~$20,000 (100 hours @ $200/hr)
**Net ROI**: $181,780
**ROI Ratio**: 9x

---

## Monitoring & Maintenance

**Track These Metrics**:
1. Organic traffic (Google Analytics)
2. Keyword rankings (weekly)
3. Core Web Vitals (monthly)
4. Backlinks (monthly)
5. Domain authority (quarterly)

**Recommended Tools**:
- Google Search Console (free)
- Google Analytics 4 (free)
- Ahrefs or SEMrush (paid)
- Screaming Frog (free/paid)
- PageSpeed Insights (free)

---

**Next Review**: 3 months
**Priority Level**: HIGH
**Est. Traffic Uplift**: +45% in 6 months
```

## ROI Impact

**Organic Traffic Growth**:

- **+45% traffic in 6 months** through systematic optimization
- **+7,000 monthly searches** from keyword gap opportunities
- **$201,780/year** additional revenue from increased conversions

**Cost Savings**:

- **Reduced paid search spend**: $30,000/year (less PPC needed)
- **Higher conversion rates**: Better on-page SEO improves CVR
- **Long-term compounding**: SEO gains accumulate over time

**Time Savings**:

- **Automated auditing**: 8 hours → 30 minutes
- **Data-driven decisions**: Clear priorities vs guesswork
- **Continuous monitoring**: Automated tracking

**Total Value**: $90,000/year

- Incremental revenue: $60,000/year
- Reduced PPC: $20,000/year
- Time savings: $10,000/year

## Success Criteria

✅ **Complete site audit performed**
✅ **Technical issues identified and categorized**
✅ **Content gaps documented**
✅ **Competitor analysis complete**
✅ **Prioritized action plan created**
✅ **ROI projection provided**

**Audit Quality Targets**:

- All pages crawled: 100%
- Issues categorized by severity
- Specific recommendations (not generic)
- Quantified impact projections
- Clear implementation steps

## Next Steps

1. Review complete audit report
2. Approve Phase 1 quick wins
3. Implement fixes in priority order
4. Monitor impact over 30 days
5. Schedule next audit (3 months)

---

**SEO Audit Status**: 🟢 Complete
**Overall Score**: 72/100
**Potential Uplift**: +45% traffic
**Annual ROI**: $90,000
