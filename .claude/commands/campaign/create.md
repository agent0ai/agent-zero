---
description: Generate complete multi-platform advertising campaign with strategy, creative, GTM plan, and landing pages
argument-hint: <product-name> [--budget <amount>] [--duration <days>] [--product-type <saas|ecommerce|services>] [--objective <conversion|awareness|traffic|lead_gen>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Campaign Creation - Master Orchestrator

Generate a complete, ready-to-launch multi-platform advertising campaign in minutes instead of days.

## Overview

**What This Command Does**:

Creates a comprehensive campaign package including:

1. **Channel Strategy** - Platform selection, budget allocation, targeting
2. **18 Ad Creative Variants** - 6 platforms × 3 angles with copy + visual direction
3. **Landing Page** - Conversion-optimized page with A/B test variants
4. **90-Day GTM Plan** - Day-by-day action items and milestones
5. **Social Media Calendar** - 30-60-90 day content schedule
6. **Tracking Setup** - Pixel installation, UTM parameters, conversion events

**Time Savings**: 40-60 hours of manual work → 15-20 minutes with AI generation
*(Time varies by product complexity: 10-25 minutes typical)*

**Expected Output**: Complete campaign ready for review and launch

## When to Use This Command

Use `/campaign:create` when you need to:

1. **Launch a new product** with multi-platform advertising
2. **Scale an existing product** to new advertising channels
3. **Rebrand/reposition** with updated messaging across platforms
4. **Test new markets** with localized campaign strategy
5. **Compete aggressively** by launching comprehensive campaigns fast

## Command Syntax

```bash
# Basic usage (required arguments only)
/campaign:create "AI Email Assistant"

# Full specification
/campaign:create "AI Email Assistant" \
  --budget 10000 \
  --duration 90 \
  --product-type saas \
  --objective conversion \
  --platforms "facebook,instagram,google,linkedin,twitter,tiktok"

# E-commerce product
/campaign:create "Magnetic Cable Organizer" \
  --budget 5000 \
  --duration 60 \
  --product-type ecommerce \
  --objective conversion \
  --price 29.99

# Service business
/campaign:create "Executive Coaching Services" \
  --budget 7500 \
  --duration 90 \
  --product-type services \
  --objective lead_gen \
  --target-audience "executives,c-level"
```

## Parameters

### Required

**`<product-name>`** (positional)

- Product or service name
- Example: `"AI Email Assistant"`

### Optional

**`--budget <amount>`** (default: 5000)

- Total campaign budget in USD
- Minimum: $3,000 (sufficient for 2-3 platforms)
- Recommended: $10,000+ (full multi-platform approach)
- Example: `--budget 10000`

**`--duration <days>`** (default: 90)

- Campaign duration in days
- Minimum: 30 days (learning phase + optimization)
- Recommended: 90 days (full cycle with scaling)
- Example: `--duration 90`

**`--product-type <type>`** (default: saas)

- Product category for strategy optimization
- Options: `saas`, `ecommerce`, `services`
- Affects platform selection and creative approach
- Example: `--product-type saas`

**`--objective <goal>`** (default: conversion)

- Primary campaign objective
- Options:
  - `conversion` - Sales, trials, signups (default)
  - `awareness` - Brand awareness, reach
  - `traffic` - Website visitors, landing page views
  - `lead_gen` - Demo requests, quote requests, form submissions
- Example: `--objective conversion`

**`--platforms <list>`** (default: all)

- Comma-separated platform list
- Options: `facebook`, `instagram`, `google`, `linkedin`, `twitter`, `tiktok`
- Default: All platforms (AI selects based on product-market fit)
- Example: `--platforms "facebook,google,linkedin"`

**`--target-audience <description>`** (optional)

- Brief target audience description
- Example: `--target-audience "SaaS founders, 28-45, $500K+ ARR"`
- If omitted, AI infers from product type

**`--price <amount>`** (optional)

- Product price point (helps with CAC targeting)
- Example: `--price 29.99` or `--price 99/month`

**`--competitors <list>`** (optional)

- Comma-separated competitor list
- Example: `--competitors "Superhuman,Spark,Edison Mail"`
- Used for competitive analysis and differentiation

**`--existing-data`** (optional flag)

- Indicates you have historical campaign data
- AI will ask for current CAC, conversion rates, performing channels
- Example: `--existing-data`

## Execution Workflow

When you run this command, it orchestrates multiple AI agents and processes:

### Step 1: Product Research (2-3 minutes)

**Gather product intelligence**:

```
1. Analyze product name and type
2. Search for competitive landscape
3. Identify target audience characteristics
4. Extract key benefits and differentiators
5. Research platform-market fit benchmarks
```

**User Prompts**:

```
- "What are the top 3 benefits of [product]?"
- "Who is the primary target customer?"
- "What's the key differentiator vs. competitors?"
- "Any existing campaign data? (CAC, conversion rates, etc.)"
```

### Step 2: Campaign Strategy Generation (3-5 minutes)

**Invoke `campaign-strategy-agent`**:

```
1. Calculate platform-product fit scores (0-100)
2. Allocate budget across platforms (anchor/growth/test)
3. Generate 30-60-90 day timeline with milestones
4. Define success metrics and KPIs
5. Identify risks and mitigation strategies
```

**Output Preview**:

```
═══════════════════════════════════════════════
   CAMPAIGN STRATEGY: AI Email Assistant
═══════════════════════════════════════════════

Budget: $10,000 over 90 days
Primary Channels: Facebook (40%), Google (30%), LinkedIn (20%)
Expected CAC: $15 (conservative) to $10 (optimistic)
Expected ROAS: 3.5x after 60 days

Platform Breakdown:
  Facebook/Instagram: $4,000 (40%) - Highest volume
  Google Ads: $3,000 (30%) - Highest intent
  LinkedIn: $2,000 (20%) - B2B targeting
  Twitter: $600 (6%) - Test platform
  TikTok: $400 (4%) - Emerging awareness

Success Criteria:
  ✅ Facebook CPA <$12 by day 30
  ✅ Google ROAS >5x by day 45
  ✅ LinkedIn CPL <$25 by day 30
  ✅ 600+ total conversions by day 90
```

### Step 3: Ad Creative Generation (4-6 minutes)

**Invoke `ad-creative-generator-agent`**:

```
1. Generate 3 creative angles (data-driven, problem-focused, contrarian)
2. Create 18 ad variants (6 platforms × 3 angles)
3. Write platform-specific copy (headlines, body, CTAs)
4. Provide visual direction for designers
5. Include format specs (dimensions, file types)
```

**Output Preview**:

```
═══════════════════════════════════════════════
   18 AD CREATIVE VARIANTS GENERATED
═══════════════════════════════════════════════

FACEBOOK:
✓ Variant 1: Data-driven image ad (1080×1080px)
✓ Variant 2: Problem-focused video ad (15s)
✓ Variant 3: Contrarian carousel ad (5 cards)

INSTAGRAM:
✓ Variant 4: Data-driven Reels (30s)
✓ Variant 5: Problem-focused Stories (15s)
✓ Variant 6: Contrarian carousel (7 cards)

GOOGLE:
✓ Variant 7: Data-driven search ad (15 headlines)
✓ Variant 8: Problem-focused search ad
✓ Variant 9: Contrarian search ad

[...18 total variants with complete copy + visual direction]

All variants ready for designer handoff →
    /campaigns/ai-email-assistant/creative/
```

### Step 4: Landing Page Creation (2-3 minutes)

**Invoke landing page generator**:

```
1. Design conversion-optimized landing page
2. Match messaging to ad creative
3. Generate A/B test variant (alternative headline/CTA)
4. Include conversion tracking setup
5. Provide mobile-responsive code
```

**Output**:

```
Landing Page Created:
  Main Variant: /campaigns/ai-email-assistant/landing-page-a.html
  A/B Variant: /campaigns/ai-email-assistant/landing-page-b.html

Key Elements:
  ✓ Above-fold hero with benefit-driven headline
  ✓ Social proof section (testimonials, logos, stats)
  ✓ Feature comparison vs. competitors
  ✓ Pricing / CTA section
  ✓ FAQ section
  ✓ Exit-intent popup (bonus offer)
```

### Step 5: GTM Plan Generation (2-3 minutes)

**Extend `/startup/gtm` command**:

```
1. Generate 90-day launch timeline
2. Create daily action items
3. Build social media calendar (30-60-90 days)
4. Define launch day hour-by-hour playbook
5. Include milestone tracking and success criteria
```

**Output Preview**:

```
═══════════════════════════════════════════════
   90-DAY GTM PLAN
═══════════════════════════════════════════════

WEEK 1 (Pre-Launch):
  Day 1-2: Campaign setup, pixel installation, audience creation
  Day 3: Launch anchor platform (Facebook) with 3 variants
  Day 4: Launch Google Search ads
  Day 5: Launch LinkedIn + Instagram
  Day 6-7: Monitor initial performance, quick fixes only

[...complete 90-day calendar with 270+ action items]

Social Media Calendar:
  30-day content: 45 posts across 5 platforms
  60-day content: 90 posts (scaling phase)
  90-day content: 135 posts (optimization phase)
```

### Step 6: Tracking Setup (1-2 minutes)

**Generate tracking implementation guide**:

```
1. Facebook Pixel code + conversion events
2. Google Ads conversion tracking
3. LinkedIn Insight Tag
4. UTM parameter structure
5. Google Analytics 4 goals
```

**Output**:

```
Tracking Setup Instructions:
  1. Install Facebook Pixel → /campaigns/ai-email-assistant/tracking/fb-pixel.html
  2. Install Google Ads Tag → /campaigns/ai-email-assistant/tracking/google-tag.html
  3. Install LinkedIn Insight Tag → /campaigns/ai-email-assistant/tracking/linkedin-tag.html
  4. UTM Structure → /campaigns/ai-email-assistant/tracking/utm-guide.md
  5. Conversion Events → /campaigns/ai-email-assistant/tracking/events.json
```

### Step 7: Output Compilation (1 minute)

**Generate final campaign package**:

```
Create comprehensive output in:
    /campaigns/ai-email-assistant/

Structure:
  /campaigns/ai-email-assistant/
    ├── README.md (campaign overview)
    ├── strategy/
    │   ├── channel-strategy.md (platform recommendations)
    │   ├── budget-allocation.md (daily/monthly breakdown)
    │   ├── timeline.md (30-60-90 day plan)
    │   └── kpis.md (success metrics)
    ├── creative/
    │   ├── facebook/ (3 variants with copy + visual direction)
    │   ├── instagram/ (3 variants)
    │   ├── google/ (3 variants)
    │   ├── linkedin/ (3 variants)
    │   ├── twitter/ (3 variants)
    │   ├── tiktok/ (3 variants)
    │   └── asset-requirements.md (designer checklist)
    ├── landing-pages/
    │   ├── page-a.html (main variant)
    │   ├── page-b.html (A/B test variant)
    │   └── mobile-preview.png
    ├── gtm-plan/
    │   ├── 90-day-calendar.md (daily action items)
    │   ├── launch-day-playbook.md (hour-by-hour)
    │   ├── social-calendar.md (30-60-90 day posts)
    │   └── milestones.md (success checkpoints)
    ├── tracking/
    │   ├── fb-pixel.html (Facebook tracking code)
    │   ├── google-tag.html (Google Ads tracking)
    │   ├── linkedin-tag.html (LinkedIn tracking)
    │   ├── utm-guide.md (parameter structure)
    │   └── events.json (conversion events)
    └── LAUNCH-CHECKLIST.md (pre-launch verification)
```

## Output Structure

### Campaign README.md

```markdown
# Campaign: AI Email Assistant
**Created**: [Date]
**Budget**: $10,000 over 90 days
**Objective**: Conversions (Trial Signups)

## Executive Summary

**Recommended Strategy**: Multi-platform approach with Facebook as anchor (40% budget)

**Expected Results**:
- 600+ conversions over 90 days
- $10-15 CPA (customer acquisition cost)
- 3.5x ROAS (return on ad spend)
- 1.2M+ total impressions

**Primary Channels**:
1. Facebook/Instagram (40%) - Highest volume potential
2. Google Ads (30%) - Highest purchase intent
3. LinkedIn (20%) - B2B professional targeting

**Risk Level**: Medium - Manageable with proper monitoring

## Quick Start

1. Review strategy: `strategy/channel-strategy.md`
2. Review creative: `creative/` (18 variants ready)
3. Review landing pages: `landing-pages/`
4. Set up tracking: Follow `tracking/` instructions
5. Launch checklist: `LAUNCH-CHECKLIST.md`

## Files Overview

| Directory | Purpose | Files |
|-----------|---------|-------|
| `strategy/` | Campaign strategy documents | 4 files |
| `creative/` | Ad copy + visual direction | 18 variants (6 platforms × 3 each) |
| `landing-pages/` | Landing page HTML + A/B variant | 2 files |
| `gtm-plan/` | 90-day launch timeline | 4 files |
| `tracking/` | Tracking code and setup | 5 files |

## Next Steps

**Today**:
1. ✅ Campaign package generated
2. [ ] Review strategy and creative
3. [ ] Request design assets based on visual direction
4. [ ] Set up ad accounts (if not done)

**This Week**:
1. [ ] Install tracking pixels on website
2. [ ] Create landing pages (use provided HTML)
3. [ ] Upload creative to ad platforms
4. [ ] Launch anchor platform (Facebook)

**This Month**:
1. [ ] Monitor daily performance
2. [ ] Launch remaining platforms
3. [ ] Optimize based on early data
4. [ ] Scale budget on winners

═══════════════════════════════════════════════
          CAMPAIGN READY FOR LAUNCH 🚀
═══════════════════════════════════════════════
```

## Example Workflows

### Workflow 1: New SaaS Product Launch

```bash
# Step 1: Generate campaign
/campaign:create "AI Email Assistant" \
  --budget 15000 \
  --duration 90 \
  --product-type saas \
  --objective conversion

# Output: Complete campaign in /campaigns/ai-email-assistant/

# Step 2: Review and customize
# - Review strategy/channel-strategy.md
# - Customize creative if needed
# - Approve budget allocation

# Step 3: Set up tracking
# - Copy code from tracking/fb-pixel.html to website
# - Copy code from tracking/google-tag.html to website
# - Verify pixel firing with Facebook Pixel Helper

# Step 4: Launch
/campaign:execute ai-email-assistant
# (This will be covered in /campaign:execute command)
```

### Workflow 2: E-commerce Product Launch

```bash
# Generate campaign for physical product
/campaign:create "Magnetic Cable Organizer" \
  --budget 8000 \
  --duration 60 \
  --product-type ecommerce \
  --objective conversion \
  --price 29.99 \
  --platforms "facebook,instagram,google,tiktok"

# Output emphasizes:
# - Visual platforms (Instagram, TikTok)
# - Dynamic product ads (Facebook catalog)
# - Google Shopping ads
# - Short 15-30 second video ads
```

### Workflow 3: B2B Service Launch

```bash
# Generate campaign for professional services
/campaign:create "Executive Coaching" \
  --budget 10000 \
  --duration 90 \
  --product-type services \
  --objective lead_gen \
  --target-audience "executives,c-level,50-65" \
  --platforms "linkedin,google"

# Output emphasizes:
# - LinkedIn lead gen ads
# - Google Search (intent-based)
# - Longer-form content (thought leadership)
# - Higher CPA targets ($50-100 typical for B2B services)
```

## Best Practices

### Before Running This Command

**1. Prepare Product Information**:

```
Have ready:
- Clear product description (1-2 sentences)
- Top 3 benefits
- Primary target customer
- Key differentiators vs. competitors
- Price point
- Any existing campaign data (CAC, conversion rates)
```

**2. Define Success Criteria**:

```
Know your targets:
- What is acceptable CAC?
- What is your LTV (lifetime value)?
- What ROAS do you need? (LTV/CAC ratio)
- How many conversions/month is success?
```

**3. Set Up Ad Accounts** (optional but recommended):

```
Create accounts in advance:
- Facebook Business Manager
- Google Ads account
- LinkedIn Campaign Manager
- (Twitter/TikTok if using)
```

### After Campaign Generation

**1. Review Strategy First**:

```
Priority order:
1. Read strategy/channel-strategy.md (10 min)
2. Validate budget allocation makes sense for your business
3. Check timeline aligns with launch goals
4. Verify KPIs are measurable
```

**2. Customize Creative if Needed**:

```
Creative is 80% ready, but you may want to:
- Adjust tone/voice to match brand closer
- Add specific customer testimonials
- Include product-specific stats/data
- Swap visual concepts if needed
```

**3. Test Landing Pages**:

```
Before launching ads:
- Deploy landing-page-a.html to your site
- Test on mobile (50%+ traffic is mobile)
- Verify forms submit correctly
- Check page load speed (<3 seconds)
- Install tracking pixels and test
```

**4. Phase Launch (Recommended)**:

```
Week 1: Launch anchor platform only (Facebook or Google)
Week 2: Add 1-2 growth platforms (Instagram, LinkedIn)
Week 3-4: Add test platforms (Twitter, TikTok)

Why? Easier to manage, learn faster, reduce risk
```

## Troubleshooting

**Issue: Budget seems too low for all platforms**

```
Solution:
- Use --platforms flag to focus on 2-3 platforms
- Example: --platforms "facebook,google"
- Start with anchor + 1 growth platform
- Scale to more platforms as you see ROI
```

**Issue: Creative doesn't match brand voice**

```
Solution:
- Edit creative files in /creative/ directory
- Keep structure/format, adjust tone/wording
- Regenerate specific variants:
  /campaign:create [product] --creative-only --platform facebook --angle data-driven
```

**Issue: Need different product type**

```
Solution:
- Use --product-type flag more specifically
- Options: saas-b2b, saas-b2c, ecommerce-physical, ecommerce-digital, services-local, services-online
- Example: --product-type saas-b2b
```

**Issue: Want to test multiple budget scenarios**

```
Solution:
- Run command multiple times with different budgets
- Compare strategy recommendations
- Example:
  /campaign:create "Product" --budget 5000
  /campaign:create "Product" --budget 10000
  /campaign:create "Product" --budget 20000
```

## Integration with Other Commands

**This command orchestrates**:

- `/social/generate` - For social content (organic + paid)
- `/landing/create` - For landing page generation
- `/startup/gtm` - For go-to-market planning
- Campaign strategy agent - For channel selection
- Ad creative generator agent - For 18 variants

**Next steps after this command**:

- `/campaign:execute` - Deploy campaign to platforms via APIs
- `/campaign:monitor` - Real-time performance dashboard
- `/campaign:optimize` - AI-powered budget reallocation
- `/campaign:report` - Generate stakeholder reports

## Expected Time Investment

**AI Generation Time**: 10-15 minutes

**Your Review Time**: 30-60 minutes

- Strategy review: 10 min
- Creative review: 20-30 min
- Landing page customization: 10-20 min

**Designer Time** (if using designers): 8-12 hours

- 18 ad creatives: 6-8 hours
- Landing page customization: 2-4 hours

**Setup Time**: 2-4 hours

- Ad account setup: 1 hour
- Tracking pixel installation: 30 min
- Landing page deployment: 1-2 hours
- Campaign upload to platforms: 30-60 min

**Total Time to Launch**: 1-2 days (vs. 2-3 weeks manual)

## ROI Calculation

**Manual Approach**:

- Strategy development: 8-12 hours @ $150/hr = $1,200-1,800
- Creative copywriting: 12-16 hours @ $100/hr = $1,200-1,600
- Visual concept development: 8-10 hours @ $150/hr = $1,200-1,500
- Landing page copy/design: 8-12 hours @ $100/hr = $800-1,200
- GTM planning: 6-8 hours @ $150/hr = $900-1,200
- **Total: $5,300-7,300 in labor costs**
- **Timeline: 2-3 weeks**

**AI-Assisted Approach** (this command):

- AI generation: 15 minutes (negligible cost)
- Your review/customization: 1-2 hours @ $150/hr = $150-300
- Designer execution: 8-12 hours @ $100/hr = $800-1,200
- **Total: $950-1,500**
- **Timeline: 1-2 days**

**Savings**: $4,350-5,800 (82-85% cost reduction)
**Time Savings**: 10-20 days faster to market

## Notes

- This command creates strategy and creative, but does NOT deploy to platforms
- Use `/campaign:execute` to deploy after review
- All generated files are markdown/HTML (human-readable and editable)
- Campaign structure follows industry best practices (30-60-90 day framework)
- Budget recommendations based on Q1 2025 benchmarks

---

## Implementation Instructions

When this command is executed, perform the following steps:

**IMPORTANT**: Output progress messages to the user at the start and end of each step using the format:

- ⏳ = Step starting
- ✅ = Step complete (with summary)
- 📝 = Files being generated (with count)

---

### Step 1: Gather Product Information (2-3 min)

**Output to user**: `⏳ Step 1/13: Gathering product information...`

Use AskUserQuestion tool to collect critical information:

**Question 1: Product Benefits**

- Header: "Benefits"
- Question: "What are the top 3 benefits of [product-name]?"
- Options:
  - Saves time
  - Saves money
  - Improves productivity
  - Better quality
  - (Other - user can specify)
- MultiSelect: true

**Question 2: Target Customer**

- Header: "Audience"
- Question: "Who is the primary target customer for [product-name]?"
- Options:
  - B2B SaaS companies
  - E-commerce businesses
  - Individual consumers
  - Enterprise companies
  - (Other - user can specify)

**Question 3: Key Differentiator**

- Header: "Advantage"
- Question: "What's the key differentiator vs. competitors?"
- Options:
  - Price (cheaper/better value)
  - Speed (faster performance)
  - Features (more capabilities)
  - Ease of use (simpler UX)
  - (Other - user can specify)

**Question 4: Existing Campaign Data**

- Header: "Data"
- Question: "Do you have existing campaign data? (CAC, conversion rates, performing channels)"
- Options:
  - Yes, I have historical data
  - No, this is our first campaign
- If "Yes": Ask follow-up for CAC, conversion rates, top channels

**Output to user**: `✅ Step 1/13: Product information collected`

---

### Step 2: Execute Campaign Strategy Agent (3-5 min)

**Output to user**: `⏳ Step 2/13: Analyzing platform-product fit...`
**Output to user**: `(This may take 3-5 minutes while AI evaluates platforms)`

1. **Read agent template**: `/home/webemo-aaron/projects/prompt-blueprint/templates/campaign-strategy-agent.md`
2. **Provide input data structure**:

   ```json
   {
     "product": {
       "name": "[from command parameter]",
       "type": "[from --product-type parameter]",
       "description": "[from user input]",
       "benefits": "[from Step 1, Question 1]",
       "target": "[from Step 1, Question 2]",
       "differentiator": "[from Step 1, Question 3]",
       "pricePoint": "[from --price parameter if provided]"
     },
     "budget": {
       "total": "[from --budget parameter]",
       "duration": "[from --duration parameter]",
       "objective": "[from --objective parameter]"
     },
     "existingData": {
       "hasData": "[from Step 1, Question 4]",
       "cac": "[if applicable]",
       "conversionRate": "[if applicable]",
       "topChannels": "[if applicable]"
     },
     "constraints": {
       "platforms": "[from --platforms parameter if specified]",
       "competitors": "[from --competitors parameter if specified]"
     }
   }
   ```

3. **Execute agent reasoning**: Follow the agent's OPERATIONAL CONTEXT → REASONING METHODOLOGY → OUTPUT SPECIFICATIONS
4. **Capture output**:
   - Platform selection with fit scores (0-100)
   - Budget allocation by platform (anchor/growth/test)
   - 30-60-90 day timeline
   - Success metrics and KPIs
   - Risk assessment

**Output to user**: `✅ Step 2/13: Platform strategy complete`
**Output to user**: `- [Platform 1]: [%] ($[amount]) - Fit Score: [score]/100`
**Output to user**: `- [Platform 2]: [%] ($[amount]) - Fit Score: [score]/100`
**Output to user**: `- [Platform 3]: [%] ($[amount]) - Fit Score: [score]/100`

---

### Step 3: Execute Ad Creative Generator Agent (4-6 min)

**Output to user**: `⏳ Step 3/13: Generating ad creative variants...`
**Output to user**: `(Creating 18 platform-optimized ad variants)`

1. **Read agent template**: `/home/webemo-aaron/projects/prompt-blueprint/templates/ad-creative-generator-agent.md`
2. **Provide input**: Combine product info from Step 1 + strategy from Step 2
3. **Generate 18 ad variants**:
   - Facebook: 3 variants (data-driven, problem-focused, contrarian)
   - Instagram: 3 variants
   - Google: 3 variants
   - LinkedIn: 3 variants
   - Twitter: 3 variants
   - TikTok: 3 variants
4. **For each variant, generate**:
   - Platform-specific copy (headlines, body, CTA)
   - Visual direction for designers
   - Format specifications (dimensions, file types)
   - Character count validation
   - Compliance check (platform policies)

**Output to user**: `✅ Step 3/13: Ad creative generation complete (18 variants)`

---

### Step 4: Create Directory Structure

**Output to user**: `⏳ Step 4/13: Creating campaign directory structure...`

Create campaign directory structure:

```bash
/campaigns/[product-name]/
├── README.md
├── strategy/
│   ├── channel-strategy.md
│   ├── budget-allocation.md
│   ├── timeline.md
│   └── kpis.md
├── creative/
│   ├── facebook/
│   ├── instagram/
│   ├── google/
│   ├── linkedin/
│   ├── twitter/
│   ├── tiktok/
│   └── asset-requirements.md
├── landing-pages/
│   ├── page-a.html
│   ├── page-b.html
│   └── mobile-preview.png
├── gtm-plan/
│   ├── 90-day-calendar.md
│   ├── launch-day-playbook.md
│   ├── social-calendar.md
│   └── milestones.md
├── tracking/
│   ├── fb-pixel.html
│   ├── google-tag.html
│   ├── linkedin-tag.html
│   ├── utm-guide.md
│   └── events.json
└── LAUNCH-CHECKLIST.md
```

**Output to user**: `✅ Step 4/13: Directory structure created`

---

### Step 5: Generate Strategy Files (Output from Step 2)

**Output to user**: `⏳ Step 5/13: Generating strategy files...`
**Output to user**: `📝 Creating 4 strategy documents`

Create 4 strategy files in `/campaigns/[product-name]/strategy/`:

**File 1: channel-strategy.md**

```markdown
# Channel Strategy: [Product Name]
**Created**: [Current Date]
**Total Budget**: $[budget] over [duration] days

## Recommended Platform Mix

[For each recommended platform from Step 2 agent output:]
### [Platform Name] - [Budget %]
**Budget Allocation**: $[amount] ([percentage]%)
**Platform Fit Score**: [0-100]/100
**Rationale**: [Why this platform was selected]
**Expected Results**:
- Impressions: [estimate]
- Clicks: [estimate]
- Conversions: [estimate]
- CPA Target: $[amount]

## Platform Prioritization
1. **Anchor Platform**: [Platform] - [Budget %] - Highest volume potential
2. **Growth Platforms**: [List] - [Budget %] - Proven secondary channels
3. **Test Platforms**: [List] - [Budget %] - Experimental channels

## Success Criteria
[List KPIs from agent output with benchmarks]
```

**File 2: budget-allocation.md**

- Daily budget breakdown
- Weekly pacing schedule
- Scaling milestones
- Budget reallocation triggers

**File 3: timeline.md**

- 30-60-90 day plan from agent output
- Week-by-week milestones
- Launch phases (learning, scaling, optimization)

**File 4: kpis.md**

- Primary metrics (conversions, CPA, ROAS)
- Secondary metrics (CTR, CPC, CPM)
- Benchmarks and targets

**Output to user**: `✅ Step 5/13: Strategy files complete (4 files created)`

---

### Step 6: Generate Creative Files (Output from Step 3)

**Output to user**: `⏳ Step 6/13: Generating creative assets...`
**Output to user**: `📝 Creating 18 ad variants across platforms`

For each platform in `/campaigns/[product-name]/creative/[platform]/`:

Create 3 variant files:

- `variant-1-data-driven.md`
- `variant-2-problem-focused.md`
- `variant-3-contrarian.md`

Each variant file contains:

```markdown
# [Platform] Ad - Variant [N]: [Angle]
**Format**: [Image/Video/Carousel/etc.]
**Objective**: [Awareness/Conversion/Traffic/Lead Gen]

## Ad Copy

**Headline**: [Text within character limit]
*([X]/[limit] characters)*

**Body Text**: [Text within character limit]
*([X]/[limit] characters)*

**CTA**: [Call to action text]

**Hashtags** (if applicable): [List]

## Visual Direction

**Concept**: [Description of visual concept]
**Style**: [Photography/Illustration/Video/Animation]
**Key Elements**:
- [Element 1]
- [Element 2]
- [Element 3]

**Specifications**:
- Dimensions: [e.g., 1080×1080px]
- File type: [JPG/PNG/MP4]
- File size: [Max size]
- Duration: [If video, e.g., 15 seconds]

## Designer Brief
[Detailed instructions for designer to execute this creative]

## Performance Prediction
**Expected CTR**: [X]%
**Expected CPC**: $[X]
**Expected CPA**: $[X]
```

Also create: `creative/asset-requirements.md` with complete designer checklist

**FOR E-COMMERCE CAMPAIGNS ONLY** (when `--product-type ecommerce`):
Also create: `creative/product-photography-brief.md` using template from `/templates/product-photography-brief-template.md`

- Customize all {PLACEHOLDERS} with product-specific information
- Include shot list, specifications, styling direction, timeline
- Budget allocation: Calculate as 15-20% of total creative budget

**Output to user**: `✅ Step 6/13: Creative files complete (18 ad variants + requirements doc + photography brief)`

---

### Step 7: Generate Landing Pages

**Output to user**: `⏳ Step 7/13: Generating landing pages...`
**Output to user**: `(Invoking frontend-architect agent for conversion-optimized HTML)`

**Use Task tool to invoke frontend-architect agent**:

Invoke the frontend-architect agent to create 2 landing page HTML files in `/campaigns/[product-name]/landing-pages/`:

```
Task tool invocation:
  subagent_type: 'frontend-architect'
  description: 'Generate landing pages'
  prompt: Create 2 conversion-optimized landing page variants for [PRODUCT_NAME]:

**Product Context**:
- Product Name: [from Step 1]
- Key Benefit: [from Step 1 user answers]
- Target Audience: [from Step 1 user answers]
- Pricing: [from Step 1 user answers]
- Platform Strategy: [from Step 4 channel-strategy.md]

**File 1: page-a.html** (Main variant)
- Hero section with benefit-driven headline
- Social proof (testimonials, logos, stats)
- Feature comparison vs. competitors
- Pricing/CTA section
- FAQ section
- Exit-intent popup
- Conversion tracking pixel placeholder

**File 2: page-b.html** (A/B test variant)
- Alternative headline/value proposition
- Different CTA copy
- Reordered sections for testing

Requirements:
- Mobile-responsive, conversion-optimized HTML/CSS/JS
- Include inline CSS for fast loading
- Add analytics tracking placeholders
- Follow best practices from platform strategy
```

**Output to user**: `✅ Step 7/13: Landing pages complete (2 variants created)`

---

### Step 8: Generate GTM Plan Files

**Output to user**: `⏳ Step 8/13: Generating GTM plan files...`
**Output to user**: `📝 Creating 4 go-to-market planning documents`

Create 4 GTM files in `/campaigns/[product-name]/gtm-plan/`:

**File 1: 90-day-calendar.md**

- Day-by-day action items
- Week-by-week focus areas
- Month-by-month objectives

**File 2: launch-day-playbook.md**

- Hour-by-hour timeline (6 AM - 10 PM)
- Platform launch sequence
- Monitoring checklist

**File 3: social-calendar.md**

- 30-day: Daily posts
- 60-day: 3x/week posts
- 90-day: 2x/week posts + strategic announcements

**File 4: milestones.md**

- Success checkpoints
- Go/no-go decision points
- Scaling triggers

**FOR B2B SERVICES CAMPAIGNS ONLY** (when `--product-type services`):
Also create:

- **File 5: consultation-call-script.md** - Using template from `/templates/consultation-call-script-template.md`
  - Customize 4-phase process (Discovery, Diagnosis, Design, Decision)
  - Include discovery questions specific to service type
  - Add objection handling for pricing/timing concerns
  - Include close rate benchmarks (15-25% for high-ticket services)

**Output to user**: `✅ Step 8/13: GTM plan files complete (4 files created + consultation script)`

---

### Step 9: Generate Tracking Setup Files

**Output to user**: `⏳ Step 9/13: Generating tracking setup files...`
**Output to user**: `📝 Creating 5 tracking implementation files`

Create 5 tracking files in `/campaigns/[product-name]/tracking/`:

**File 1: fb-pixel.html**

```html
<!-- Facebook Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'YOUR_PIXEL_ID');
fbq('track', 'PageView');
</script>
<!-- End Facebook Pixel Code -->
```

**File 2: google-tag.html**
**File 3: linkedin-tag.html**
**File 4: utm-guide.md** - UTM parameter structure for all campaigns
**File 5: events.json** - Conversion events to track

**FOR E-COMMERCE CAMPAIGNS ONLY** (when `--product-type ecommerce`):
Also create:

- **File 6: google-shopping-feed.xml** - Using template from `/templates/google-shopping-feed-template.xml`
  - Customize all {PLACEHOLDERS} with product data
  - Include required fields (ID, title, description, link, image, price, brand, GTIN)
  - Add recommended fields (category, additional images, shipping, custom labels)
- **File 7: google-shopping-setup-guide.md** - Using template from `/templates/google-shopping-setup-guide.md`
  - Step-by-step Merchant Center setup
  - Feed upload instructions
  - Campaign creation guide
  - Optimization recommendations

**Output to user**: `✅ Step 9/13: Tracking files complete (5 files created + 2 Google Shopping files)`

---

### Step 10: Create Campaign README

**Output to user**: `⏳ Step 10/13: Creating campaign README...`

Generate `/campaigns/[product-name]/README.md`:

```markdown
# Campaign: [Product Name]
**Created**: [Date]
**Budget**: $[budget] over [duration] days
**Objective**: [Objective] ([Specific goal, e.g., "Trial Signups"])

## Executive Summary

**Recommended Strategy**: [Summary from Step 2]

**Expected Results**:
- [X] conversions over [duration] days
- $[X]-[X] CPA (customer acquisition cost)
- [X]x ROAS (return on ad spend)
- [X]M+ total impressions

**Primary Channels**:
1. [Platform] ([Budget %]) - [Rationale]
2. [Platform] ([Budget %]) - [Rationale]
3. [Platform] ([Budget %]) - [Rationale]

**Risk Level**: [Low/Medium/High] - [Risk summary]

## Quick Start

1. Review strategy: `strategy/channel-strategy.md`
2. Review creative: `creative/` (18 variants ready)
3. Review landing pages: `landing-pages/`
4. Set up tracking: Follow `tracking/` instructions
5. Launch checklist: `LAUNCH-CHECKLIST.md`

## Files Overview

| Directory | Purpose | Files |
|-----------|---------|-------|
| `strategy/` | Campaign strategy documents | 4 files |
| `creative/` | Ad copy + visual direction | 18 variants (6 platforms × 3 each) |
| `landing-pages/` | Landing page HTML + A/B variant | 2 files |
| `gtm-plan/` | 90-day launch timeline | 4 files |
| `tracking/` | Tracking code and setup | 5 files |

## Next Steps

**Today**:
1. ✅ Campaign package generated
2. [ ] Review strategy and creative
3. [ ] Request design assets based on visual direction
4. [ ] Set up ad accounts (if not done)

**This Week**:
1. [ ] Install tracking pixels on website
2. [ ] Create landing pages (use provided HTML)
3. [ ] Upload creative to ad platforms
4. [ ] Launch anchor platform ([Platform from Step 2])

**This Month**:
1. [ ] Monitor daily performance
2. [ ] Launch remaining platforms
3. [ ] Optimize based on early data
4. [ ] Scale budget on winners

═══════════════════════════════════════════════
          CAMPAIGN READY FOR LAUNCH 🚀
═══════════════════════════════════════════════
```

**Output to user**: `✅ Step 10/13: Campaign README created`

---

### Step 11: Create Launch Checklist

**Output to user**: `⏳ Step 11/13: Creating launch checklist...`

Generate `/campaigns/[product-name]/LAUNCH-CHECKLIST.md`:

```markdown
# Pre-Launch Checklist: [Product Name]

## Product Readiness
- [ ] Product/service is live and accessible
- [ ] Payment processing tested and working
- [ ] Customer support channels ready
- [ ] Onboarding flow tested

## Marketing Assets
- [ ] All 18 ad creatives designed and exported
- [ ] Landing pages deployed and tested
- [ ] A/B test variant ready
- [ ] Mobile responsiveness verified

## Tracking & Analytics
- [ ] Facebook Pixel installed and firing
- [ ] Google Ads conversion tracking installed
- [ ] LinkedIn Insight Tag installed
- [ ] Google Analytics goals configured
- [ ] UTM parameters documented

## Ad Account Setup
- [ ] Facebook Business Manager configured
- [ ] Google Ads account ready
- [ ] LinkedIn Campaign Manager setup
- [ ] Payment methods added to all platforms
- [ ] Billing thresholds set

## Campaign Configuration
- [ ] Budget allocated across platforms
- [ ] Targeting parameters configured
- [ ] Bid strategies selected
- [ ] Ad scheduling set (if applicable)
- [ ] Conversion events defined

## Team Alignment
- [ ] Stakeholders reviewed and approved strategy
- [ ] Design team completed all creative assets
- [ ] Customer support briefed on campaign
- [ ] Sales team (if applicable) prepared for leads

## Launch Day
- [ ] Monitor campaigns hourly for first 6 hours
- [ ] Respond to all comments/messages within 1 hour
- [ ] Track metrics in real-time dashboard
- [ ] Be ready to pause underperforming ads quickly

═══════════════════════════════════════════════
        Complete this checklist before launch
═══════════════════════════════════════════════
```

**Output to user**: `✅ Step 11/13: Launch checklist created`

---

### Step 12: Output Verification

**Output to user**: `⏳ Step 12/13: Verifying all files...`

Verify all files created:

- [ ] `/campaigns/[product-name]/README.md`
- [ ] `/campaigns/[product-name]/LAUNCH-CHECKLIST.md`
- [ ] `/campaigns/[product-name]/strategy/` (4 files)
- [ ] `/campaigns/[product-name]/creative/facebook/` (3 variants)
- [ ] `/campaigns/[product-name]/creative/instagram/` (3 variants)
- [ ] `/campaigns/[product-name]/creative/google/` (3 variants)
- [ ] `/campaigns/[product-name]/creative/linkedin/` (3 variants)
- [ ] `/campaigns/[product-name]/creative/twitter/` (3 variants)
- [ ] `/campaigns/[product-name]/creative/tiktok/` (3 variants)
- [ ] `/campaigns/[product-name]/creative/asset-requirements.md`
- [ ] `/campaigns/[product-name]/landing-pages/` (2 HTML files)
- [ ] `/campaigns/[product-name]/gtm-plan/` (4 files)
- [ ] `/campaigns/[product-name]/tracking/` (5 files)

**Total Expected Files**: 30+

**Output to user**: `✅ Step 12/13: File verification complete ([X] files created)`

---

### Step 13: Display Success Message

**Output to user**: `⏳ Step 13/13: Finalizing campaign package...`

```
════════════════════════════════════════════════════════════
   ✅ CAMPAIGN PACKAGE GENERATED: [Product Name]
════════════════════════════════════════════════════════════

📁 Location: /campaigns/[product-name]/
📄 Files Created: [X] files

📊 Campaign Summary:
   • Budget: $[budget] over [duration] days
   • Platforms: [List of platforms]
   • Expected Conversions: [X]
   • Target CPA: $[X]

📋 What Was Generated:
   ✓ Campaign strategy (4 documents)
   ✓ 18 ad creative variants (6 platforms × 3 angles)
   ✓ 2 landing page variants (A/B test ready)
   ✓ 90-day GTM plan (4 documents)
   ✓ Tracking setup guide (5 files)
   ✓ Launch checklist

🚀 Next Steps:
   1. Review README.md for campaign overview
   2. Review strategy/channel-strategy.md
   3. Review all 18 creative variants in creative/
   4. Customize landing pages if needed
   5. Complete LAUNCH-CHECKLIST.md
   6. Launch with anchor platform: [Platform]

⏱️  Expected Time to Launch: 1-2 days
💰 Expected ROI: [X]x ROAS after [duration] days

════════════════════════════════════════════════════════════
              READY FOR REVIEW AND LAUNCH 🎯
════════════════════════════════════════════════════════════

View campaign: /campaigns/[product-name]/README.md
```

**Output to user**: `✅ Step 13/13: Campaign package complete!`
**Output to user**: ``
**Output to user**: `🎉 All files successfully generated! Review /campaigns/[product-name]/README.md to get started.`

---

**Ready to launch your campaign?** Run `/campaign:create` to get started.
