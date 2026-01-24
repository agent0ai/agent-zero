---
description: End-to-end campaign launch - Shopify product + multi-platform ads + landing pages + social content in one command
argument_hint: --product-id <shopify-id> --budget <amount> --duration <days> [--platforms facebook,instagram,google] [--objective conversion|awareness|traffic]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Integrated Campaign Launch Command

Launch complete marketing campaign with Shopify product setup, multi-platform advertising, landing pages, and scheduled social content - all in one automated workflow.

## ROI: $95,000/year

- Time savings (24 hours → 45 minutes per launch): $60,000/year
- Higher ROAS from optimized setup: $25,000/year
- Reduced errors & missed steps: $10,000/year

## Overview

**Purpose**: Transform AI solution → live ecommerce product → multi-channel marketing campaign in under 1 hour (vs. 2-3 days manually).

**Integrated Workflow**:

1. **Shopify Product** - Create/update product listing
2. **Landing Pages** - Deploy v0.dev pages to Vercel
3. **Ad Campaigns** - Facebook, Instagram, Google Ads setup
4. **Social Content** - 30 days of scheduled posts
5. **Analytics** - Unified dashboard tracking

**Target Outcome**: Fully operational campaign with:

- Product live on Shopify
- Ads running on 2-3 platforms
- Landing page deployed
- 30 days of social content scheduled
- Real-time performance dashboard

### Execution Time

- **Shopify product setup**: 5-8 minutes (if not exists)
- **Landing page generation**: 8-12 minutes (v0.dev + Vercel deploy)
- **Ad campaign setup**: 12-18 minutes (all platforms)
- **Social content creation**: 6-10 minutes (30 posts across platforms)
- **Analytics dashboard**: 4-6 minutes (unified tracking setup)
- **Total**: 35-55 minutes vs. 16-24 hours manually
*(Includes: Product creation, creative generation, ad account setup, landing page deployment, social scheduling)*

## When to Use This Command

Use `/campaign/launch-integrated` when you need to:

1. **Product Launch**: Take new AI solution from idea to market in <1 hour
2. **Campaign Refresh**: Relaunch existing product with new creative/strategy
3. **Seasonal Promotions**: Quick campaign for holidays, events, sales
4. **A/B Testing**: Launch variant campaigns for optimization
5. **Market Expansion**: Launch in new geographic markets
6. **Beta Launch**: Controlled rollout with limited budget

## Command Syntax

```bash
# Full integrated launch for existing Shopify product
/campaign/launch-integrated \
  --product-id 12345 \
  --budget 5000 \
  --duration 30 \
  --platforms facebook,instagram,google \
  --objective conversion

# Quick launch with auto platform selection
/campaign/launch-integrated --product-id 12345 --budget 2000 --duration 14

# Launch from solution folder (creates product first)
/campaign/launch-integrated \
  --folder ./ai-solutions/cloud-optimizer \
  --budget 10000 \
  --duration 60 \
  --platforms facebook,instagram,google,linkedin

# Beta launch (limited budget, awareness focus)
/campaign/launch-integrated \
  --product-id 12345 \
  --budget 500 \
  --duration 7 \
  --objective awareness \
  --platforms facebook
```

## Workflow

### Input Requirements

${ARGUMENTS}

**Required Arguments**:

- `--product-id <shopify-id>` OR `--folder <path>` - Existing product or create new
- `--budget <amount>` - Total campaign budget in USD

**Optional Arguments**:

- `--duration <days>` - Campaign length (default: 30)
- `--platforms <list>` - Comma-separated: facebook,instagram,google,linkedin,tiktok (default: auto-select)
- `--objective <type>` - conversion (default), awareness, traffic, lead_gen
- `--auto-launch` - Skip final approval, launch immediately
- `--landing-page-template` - saas, ecommerce, waitlist (default: auto)

### Step 1: Product Validation/Creation (5 min)

**If --product-id provided**:

- Fetch product from Shopify API
- Verify product status (draft/active)
- Extract product data for campaign creation

**If --folder provided**:

- Parse AI solution folder
- Gate 1: Product listing approval
- Create Shopify product (draft)
- Use new product_id for campaign

### Step 2: Landing Page Generation (10 min)

- Analyze product data + target audience
- Generate landing page design (v0.dev)
  - Hero section with value proposition
  - Features/benefits section
  - Pricing/CTA
  - Social proof (testimonials placeholder)
  - FAQ section
- Deploy to Vercel (live URL)
- Set up conversion tracking pixels

**Output**: <https://your-product.vercel.app>

### Step 3: Campaign Strategy Generation (4 min)

Based on:

- Product type (SaaS, ecommerce, service)
- Budget allocation
- Target objective
- Competition analysis (quick web search)

**Deliverables**:

- Platform recommendations + budget split
- Audience targeting strategy per platform
- Creative themes + messaging
- Bidding strategy
- Expected performance (CTR, CPA, ROAS)

### Step 4: Ad Creative Generation (8 min)

For each platform, generate:

**Facebook/Instagram**:

- 3-5 image ad variants (AI-generated via templates)
- 2-3 carousel ads
- 1-2 video ad scripts
- Ad copy (5 variants per creative)

**Google Ads**:

- Responsive search ads (15 headlines, 4 descriptions)
- Display ad creatives (multiple sizes)
- Shopping feed setup (if ecommerce)

**LinkedIn** (if B2B SaaS):

- Sponsored content ads
- InMail campaigns
- Lead gen forms

**TikTok** (if selected):

- Video ad scripts
- Trending audio hooks

### Step 5: Ad Campaign Setup (12 min)

**Automated Setup** (via APIs):

- Create campaigns in Facebook Business Manager
- Set up Google Ads campaigns
- Configure LinkedIn Campaign Manager (if applicable)
- Set budgets, bidding strategies, targeting
- Install conversion tracking pixels
- Set up A/B test structure

**Gate 2 Approval**: Review campaign before launch

- Preview all ad creatives
- Review targeting & budgets
- Approve/reject before going live

### Step 6: Social Content Generation (8 min)

Create 30 days of scheduled content:

**Twitter/X**: 30 tweets (threads, quotes, tips)
**LinkedIn**: 10 professional posts
**Instagram**: 20 posts (feed + stories)
**Facebook**: 15 community posts
**TikTok**: 10 video scripts (if applicable)

All content:

- Optimized for platform algorithms
- Includes hashtags, CTAs, links
- Scheduled for optimal times
- A/B test variants

### Step 7: Analytics Dashboard Setup (5 min)

Create unified tracking dashboard:

- Shopify sales data
- Ad platform metrics (Facebook, Google, LinkedIn)
- Landing page conversion rates
- Social media engagement
- Attribution modeling
- ROI calculation

**Real-time Alerts**:

- Budget pacing warnings
- Underperforming ads (pause recommendations)
- Conversion rate drops
- Anomaly detection

### Step 8: Campaign Launch & Monitoring (2 min)

**Final Checklist**:
✓ Shopify product status: Active
✓ Landing page deployed: Live
✓ Conversion tracking: Installed
✓ Ad creatives approved: Gate 2
✓ Social content scheduled: 30 days
✓ Analytics dashboard: Active

**Launch Sequence**:

1. Publish Shopify product (if draft)
2. Activate ad campaigns (Facebook, Google, LinkedIn)
3. Deploy social content schedule
4. Send launch notification (email/Slack)
5. Enable real-time monitoring dashboard

## Success Criteria

✅ Shopify product published (status: ACTIVE)
✅ Landing page deployed to Vercel (live URL)
✅ Ad campaigns running on 2+ platforms
✅ 30 days of social content scheduled
✅ Analytics dashboard tracking all metrics
✅ Conversion tracking pixels installed
✅ Campaign budget allocated across platforms
✅ Real-time alerts configured

## Example Output

```
═══════════════════════════════════════════════════════
 INTEGRATED CAMPAIGN LAUNCH: Cloud Cost Optimizer
═══════════════════════════════════════════════════════

🚀 LAUNCH STATUS: COMPLETE (38 minutes)

───────────────────────────────────────────────────────
SHOPIFY PRODUCT
───────────────────────────────────────────────────────
✅ Product ID: 8472639201
✅ Status: ACTIVE (published)
✅ URL: https://your-store.myshopify.com/products/cloud-cost-optimizer
✅ Price: $99/month
✅ Variants: 3 (Starter, Pro, Enterprise)

───────────────────────────────────────────────────────
LANDING PAGE
───────────────────────────────────────────────────────
✅ Deployed: https://cloud-optimizer.vercel.app
✅ Performance Score: 98/100 (Lighthouse)
✅ Conversion Tracking: Installed (Google Analytics 4 + Facebook Pixel)
✅ Load Time: 1.2s

───────────────────────────────────────────────────────
AD CAMPAIGNS LAUNCHED
───────────────────────────────────────────────────────

FACEBOOK + INSTAGRAM:
✅ Campaign ID: 120398471203
✅ Budget: $2,500/month ($83/day)
✅ Targeting: 250K DevOps engineers, CTOs (US, EU)
✅ Ad Sets: 4 (Interest, Lookalike, Retargeting, Behavioral)
✅ Creatives: 12 variants (3 images, 2 carousels, 1 video)
✅ Status: ACTIVE
✅ Estimated Reach: 50K-75K/month

GOOGLE ADS:
✅ Campaign ID: 98234719823
✅ Budget: $2,000/month ($67/day)
✅ Search Ads: 3 ad groups (Brand, Generic, Competitor)
✅ Display Network: 5 creatives
✅ Responsive Search Ads: 15 headlines, 4 descriptions
✅ Status: ACTIVE
✅ Expected Impressions: 120K/month

LINKEDIN (B2B Focus):
✅ Campaign ID: LI-47298347
✅ Budget: $500/month ($17/day)
✅ Sponsored Content: 3 posts
✅ InMail Campaign: 1 sequence
✅ Targeting: 15K CTOs, VP Engineering (500+ employees)
✅ Status: ACTIVE

───────────────────────────────────────────────────────
SOCIAL CONTENT SCHEDULED
───────────────────────────────────────────────────────
✅ Twitter: 30 tweets (1/day for 30 days)
✅ LinkedIn: 10 professional posts
✅ Instagram: 20 posts + 15 stories
✅ Facebook: 15 community engagement posts
✅ TikTok: 10 video scripts (ready for recording)

First Post Goes Live: Tomorrow at 9:00 AM EST

───────────────────────────────────────────────────────
ANALYTICS & TRACKING
───────────────────────────────────────────────────────
✅ Unified Dashboard: http://localhost:3000/analytics
✅ Google Analytics 4: Configured
✅ Facebook Pixel: Installed
✅ Conversion Tracking: Active
✅ Attribution Model: Data-driven (7-day click)
✅ Real-time Alerts: Enabled

───────────────────────────────────────────────────────
PERFORMANCE PROJECTIONS (30 Days)
───────────────────────────────────────────────────────
Budget Allocated: $5,000
Platform Split:
  • Facebook/Instagram: $2,500 (50%)
  • Google Ads: $2,000 (40%)
  • LinkedIn: $500 (10%)

Expected Results:
  • Impressions: 350K-450K
  • Clicks: 7K-10K (CTR: 2.0-2.5%)
  • Landing Page Visitors: 5K-8K
  • Conversions: 50-80 (CR: 1.0-1.5%)
  • Revenue: $4,950-$7,920 (ROAS: 0.99-1.58x)
  • Customer Acquisition Cost: $62-$100

Note: ROAS typically improves 40-60% after first 30 days of optimization

───────────────────────────────────────────────────────
CAMPAIGN MONITORING
───────────────────────────────────────────────────────
🔔 Alerts Configured:
  • Daily budget pacing check (notify if >20% variance)
  • Underperforming ads (pause if CTR <0.5% after 1000 impressions)
  • Conversion rate drop (alert if CR drops >30%)
  • Cost per acquisition spike (alert if CPA >$150)

📊 Daily Reports: Sent to email at 8:00 AM EST
📈 Weekly Optimization: AI recommendations every Monday

───────────────────────────────────────────────────────
NEXT STEPS
───────────────────────────────────────────────────────
1. Monitor campaign dashboard (first 48 hours critical)
2. Review ad performance after 3 days, pause losers
3. Scale winning ad sets by 20% every 5 days
4. Add user testimonials to landing page (week 2)
5. Launch retargeting campaign (week 3)
6. Optimize for ROAS >2.0x (target month 2)

📄 CAMPAIGN ASSETS CREATED:
✅ /campaign-assets/ad-creatives/ (12 Facebook ads, 5 Google ads)
✅ /campaign-assets/social-content/ (85 posts across platforms)
✅ /campaign-assets/landing-page/ (Vercel deployed)
✅ /campaign-assets/campaign-strategy.pdf (18 pages)

═══════════════════════════════════════════════════════
🎯 CAMPAIGN IS LIVE - MONITORING ACTIVE
═══════════════════════════════════════════════════════
```

## Integration Points

**Automatically Triggers**:

- `/shopify/sync` - If --folder provided (create product)
- `/landing-page/create` - v0.dev + Vercel deployment
- `/social/generate` - 30 days of content
- `/campaign/create` - Strategy generation

**Manual Triggers**:

- `/campaign/optimize` - After 7 days, optimize underperformers
- `/social/analytics` - Track social performance
- `/product/pricing` - Adjust pricing based on CPA data

## Technical Implementation

**API Integrations Required**:

1. **Shopify Admin API** - Product management
2. **Facebook Business API** - Campaign setup
3. **Google Ads API** - Search + Display campaigns
4. **LinkedIn Marketing API** - B2B campaigns (if applicable)
5. **Vercel API** - Landing page deployment
6. **v0.dev** - Landing page generation
7. **Social Scheduling** - Buffer, Hootsuite, or native APIs

**Approval Gates**:

- **Gate 1** (if creating product): Product listing review
- **Gate 2**: Campaign strategy & budget approval
- **Gate 3**: Final launch confirmation

## Notes

**Platform Budget Allocation**:

- Default split based on product type:
  - **SaaS (B2B)**: Google 40%, LinkedIn 30%, Facebook 30%
  - **SaaS (B2C)**: Facebook 50%, Google 40%, Instagram 10%
  - **Ecommerce**: Facebook 45%, Instagram 30%, Google 25%
  - **Services**: Google 50%, LinkedIn 30%, Facebook 20%

**Creative Best Practices**:

- Facebook/Instagram: Video outperforms static (2.5x CTR)
- Google: Responsive search ads get 15% more conversions
- LinkedIn: Carousel ads perform best for B2B SaaS
- TikTok: Native-looking content (not polished ads) wins

**Cost Estimates** (per platform):

- Facebook CPC: $0.50-$2.00
- Instagram CPC: $0.70-$2.50
- Google Search CPC: $1.50-$5.00
- LinkedIn CPC: $2.00-$6.00
- TikTok CPC: $0.30-$1.50

## Troubleshooting

**Campaign not launching?**

- Check API credentials in Vault
- Verify ad account permissions
- Ensure payment method added to ad accounts
- Review ad policy compliance

**Low ROAS?**

- Run `/campaign/optimize` after 7 days
- Check landing page conversion rate (should be >1%)
- Review audience targeting (too broad?)
- A/B test ad creatives

**Landing page not deploying?**

- Verify Vercel API token in Vault
- Check domain configuration
- Review build logs for errors
