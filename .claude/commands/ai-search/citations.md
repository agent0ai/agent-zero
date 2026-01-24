---
description: Build citation-worthy content and track AI engine citations of your content
argument-hint: [--mode <build|track|analyze>] [--page <path>] [--ai-engines <chatgpt|claude|perplexity|all>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# AI Citations Command

Build citation-worthy content and track when AI search engines cite your content as a source. This command helps you become a trusted reference source for ChatGPT, Claude, Perplexity, and other AI-powered search platforms.

## Overview

**Purpose**: Transform your content into highly citable reference material and monitor AI engine citation performance.

**Why Citations Matter**:

- **Brand Authority**: Being cited by AI engines establishes you as an expert
- **Traffic Quality**: AI-referred traffic has 2-3x higher conversion rates
- **Competitive Advantage**: Early movers become default sources for AI engines
- **Long-term Value**: Citations compound - today's citation leads to tomorrow's traffic

**Target Outcome**: Become the go-to source AI engines cite when users ask about your domain expertise.

## When to Use This Command

Use `/ai-search/citations` when you want to:

1. **Build Citation-Worthy Content**: Create content that AI engines want to cite
2. **Track Citation Performance**: Monitor when and how AI engines cite your content
3. **Analyze Citation Patterns**: Understand which content gets cited most often
4. **Competitive Analysis**: See who AI engines cite for your topics
5. **Citation Strategy**: Develop systematic approach to earning AI citations

## Command Syntax

```bash
# Build citation-worthy content for current page
/ai-search/citations --mode build

# Track citations from AI engines
/ai-search/citations --mode track

# Analyze citation patterns
/ai-search/citations --mode analyze

# Build mode for specific page
/ai-search/citations --mode build --page src/pages/guide.html

# Track citations from specific AI engine
/ai-search/citations --mode track --ai-engines perplexity

# Full citation audit and recommendations
/ai-search/citations --mode analyze --comprehensive
```

## Mode 1: Build Citation-Worthy Content

### What Makes Content Citation-Worthy?

**Key Characteristics**:

```javascript
const citationWorthyContent = {
  accuracy: {
    factual: "100% verifiable facts",
    sourced: "Every claim has a source",
    current: "Data within 12-18 months",
    balanced: "Multiple perspectives shown"
  },

  authority: {
    expertise: "Author credentials displayed",
    originalResearch: "Unique data or insights",
    peerReviewed: "Expert validation",
    institutional: "Organization credibility"
  },

  structure: {
    clearAnswers: "Direct, concise responses",
    scannable: "Easy to extract key facts",
    quantified: "Specific numbers and data",
    comparative: "Side-by-side comparisons"
  },

  technical: {
    schema: "Structured data markup",
    citations: "Proper attribution format",
    accessibility: "Screen reader friendly",
    mobile: "Mobile-optimized"
  }
};
```

### Citation-Worthy Content Patterns

#### Pattern 1: Original Research & Data

```markdown
**Why AI Engines Love This**: Unique data can't be found elsewhere

**Example**:
# State of AI Search 2024: Original Research

We surveyed 10,000 users across 50 countries to understand AI search behavior.

## Key Findings

**Adoption Rate**: 67% of internet users have tried AI search (up from 23% in 2023)
- ChatGPT: 45% monthly active users
- Google SGE: 32% monthly active users
- Perplexity: 18% monthly active users
- Claude: 12% monthly active users

**Trust Levels**: Users trust AI search results at:
- 72% for factual questions
- 58% for medical information
- 45% for financial advice
- 89% for recipe and how-to content

**Source**: State of AI Search Survey 2024, [Your Company], n=10,000,
conducted January-February 2024
```

**Citation Probability**: 95% - AI engines ALWAYS cite original research

#### Pattern 2: Expert Analysis & Commentary

```markdown
**Why AI Engines Love This**: Expert perspective adds credibility

**Example**:
# Cloud Cost Optimization: Expert Analysis

By **Dr. Maria Rodriguez**, Cloud Economics Researcher, 15 years at AWS & Google Cloud

## The Hidden Costs Everyone Misses

Based on my analysis of 500+ enterprise cloud migrations, I've identified
three cost factors that organizations consistently underestimate:

1. **Data Transfer Costs**: Average 18% of total cloud spend
   - Between regions: $0.02/GB adds up fast
   - To internet: $0.09/GB for high-traffic apps
   - **Real example**: E-commerce site with 10TB/month = $900/month hidden cost

2. **Idle Resources**: Average 35% of provisioned resources unused
   - Dev/test environments running 24/7
   - Over-provisioned instances for peak load
   - **Recommendation**: Auto-shutdown schedules save $50K-200K/year

3. **Support Costs**: Often 10-15% additional
   - Production support packages required
   - Expert consultation fees
   - **Budget**: Add 12% to quoted costs

**Source**: Cloud Cost Analysis Study, 500 enterprise migrations, 2020-2024
```

**Citation Probability**: 85% - Expert commentary is highly valued

#### Pattern 3: Comprehensive Comparisons

```markdown
**Why AI Engines Love This**: Saves users from visiting multiple sites

**Example**:
# AI Search Engines Comparison: Complete Guide 2024

## Feature-by-Feature Comparison

| Feature | ChatGPT | Claude | Perplexity | Google SGE |
|---------|---------|--------|------------|------------|
| **Sources Cited** | Limited | Moderate | Extensive | Moderate |
| **Real-time Data** | No* | No* | Yes | Yes |
| **Image Generation** | Yes (DALL-E) | No | No | Yes |
| **Code Generation** | Excellent | Excellent | Good | Moderate |
| **Math Solving** | Good | Excellent | Moderate | Moderate |
| **Cost** | $20/month | $20/month | Free/Pro | Free |
| **API Access** | Yes | Yes | Limited | No |

*With Browse/Search enabled

## Best Use Cases

**ChatGPT**: Best for creative writing, brainstorming, coding assistance
**Claude**: Best for analysis, long documents, nuanced understanding
**Perplexity**: Best for research, current events, fact-checking
**Google SGE**: Best for shopping, local search, quick facts

**Tested**: All platforms tested with 100 queries across 10 categories,
January 2024. Testing methodology available in appendix.
```

**Citation Probability**: 90% - Comparison tables are citation gold

#### Pattern 4: Step-by-Step Guides with Results

```markdown
**Why AI Engines Love This**: Proven, replicable processes

**Example**:
# How to Reduce Cloud Costs by 40% in 30 Days

## Our Results
- **Starting Cost**: $85,000/month
- **Ending Cost**: $51,000/month
- **Savings**: $34,000/month (40%)
- **Time Investment**: 20 hours
- **ROI**: 2,040% annualized

## Step-by-Step Process

### Step 1: Identify Idle Resources (Day 1-5)
**Action**: Run cost analysis tool
**Tool Used**: AWS Cost Explorer + Cloudability
**Time**: 3 hours
**Immediate Savings**: $8,500/month

**What we found**:
- 45 EC2 instances running 24/7 for dev/test (should run 9am-6pm M-F)
- 12 RDS databases with zero connections in 30 days
- 8TB of S3 storage in Standard tier (should be Glacier)

**Specific Actions**:
```bash
# Auto-shutdown dev instances
aws ec2 stop-instances --instance-ids i-xxx --schedule "0 18 * * *"
aws ec2 start-instances --instance-ids i-xxx --schedule "0 9 * * 1-5"
```

[Continue with steps 2-6...]

### Results Validation

Tracked for 90 days post-implementation:

- Savings sustained at 38-42% monthly
- No service degradation reported
- Team productivity unaffected

```

**Citation Probability**: 88% - Proven results with specifics

### Building Citation-Worthy Content

When you run `--mode build`, Claude Code will:

#### Step 1: Content Audit
```javascript
const contentAudit = {
  citationScore: 42, // Out of 100

  strengths: [
    "Good factual accuracy",
    "Clear structure",
    "Recent publication date"
  ],

  criticalIssues: [
    {
      issue: "No source citations for 12 statistics",
      impact: "AI engines can't verify claims",
      fix: "Add inline citations with links",
      citationBoost: "+25 points"
    },
    {
      issue: "No author credentials displayed",
      impact: "Unknown expertise level",
      fix: "Add author bio with credentials",
      citationBoost: "+15 points"
    },
    {
      issue: "Generic content (no unique insights)",
      impact: "Not differentiated from other sources",
      fix: "Add original research or expert commentary",
      citationBoost: "+30 points"
    }
  ],

  opportunities: [
    "Add comparison tables (+10 points)",
    "Include case study with results (+12 points)",
    "Implement FAQ schema (+8 points)"
  ],

  potentialScore: 92, // After fixes
  timeToFix: "3-4 hours",
  priorityOrder: ["Add citations", "Show credentials", "Add unique insights"]
};
```

#### Step 2: Generate Citation Elements

**Proper Citation Format**:

```html
<!-- Inline Citation -->
<p>Cloud adoption grew 156% in 2023
  <sup><a href="#citation-1" class="citation">[1]</a></sup>
</p>

<!-- Citation Details (end of article) -->
<section class="citations">
  <h2>Sources & Citations</h2>
  <ol>
    <li id="citation-1">
      <strong>Flexera 2024 State of the Cloud Report</strong><br>
      Flexera Software LLC<br>
      Published: January 15, 2024<br>
      <a href="https://www.flexera.com/state-of-cloud">
        https://www.flexera.com/state-of-cloud
      </a><br>
      <em>Sample: 750 global enterprises, methodology: online survey</em>
    </li>
  </ol>
</section>

<!-- Schema.org Citation Markup -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "citation": [
    {
      "@type": "CreativeWork",
      "name": "Flexera 2024 State of the Cloud Report",
      "author": {
        "@type": "Organization",
        "name": "Flexera Software LLC"
      },
      "datePublished": "2024-01-15",
      "url": "https://www.flexera.com/state-of-cloud"
    }
  ]
}
</script>
```

**Author Credentials Display**:

```html
<div class="author-bio" itemscope itemtype="https://schema.org/Person">
  <img itemprop="image" src="/authors/sarah-chen.jpg" alt="Dr. Sarah Chen">
  <div class="author-details">
    <h3 itemprop="name">Dr. Sarah Chen</h3>
    <p itemprop="jobTitle">Cloud Security Architect</p>

    <ul class="credentials">
      <li><strong>Experience</strong>: 15 years in cloud infrastructure</li>
      <li><strong>Education</strong>: PhD in Computer Science, MIT</li>
      <li><strong>Certifications</strong>: AWS Solutions Architect Professional,
          Google Cloud Certified Architect, Azure Solutions Architect Expert</li>
      <li><strong>Previous Roles</strong>: Sr. Cloud Architect at Amazon (2015-2020),
          Technical Lead at Google Cloud (2010-2015)</li>
      <li><strong>Publications</strong>: 23 peer-reviewed papers on cloud security</li>
    </ul>

    <div itemprop="sameAs">
      <a href="https://linkedin.com/in/sarahchen">LinkedIn</a>
      <a href="https://github.com/sarahchen">GitHub</a>
      <a href="https://scholar.google.com/sarahchen">Google Scholar</a>
    </div>
  </div>
</div>
```

#### Step 3: Add Unique Value Elements

**Original Research Section**:

```markdown
## Original Research: Cloud Migration Time Analysis

We analyzed 200 cloud migration projects to determine average timelines.

### Methodology
- **Sample**: 200 enterprise cloud migrations (2020-2024)
- **Company Size**: 500-5,000 employees
- **Data Sources**: Project documentation, post-migration interviews
- **Variables Tracked**: Infrastructure size, team size, migration strategy

### Key Findings

**Average Migration Time by Strategy**:
1. **Rehost ("Lift & Shift")**: 3-6 months
   - Fastest approach
   - Minimal refactoring
   - 78% of migrations choose this initially

2. **Replatform ("Lift, Tinker & Shift")**: 6-12 months
   - Moderate optimization
   - Some cloud-native services adoption
   - 15% of migrations

3. **Refactor ("Re-architect")**: 12-24 months
   - Full cloud-native rebuild
   - Maximum performance/cost benefits
   - 7% of migrations (usually after initial rehost)

**Time Factors** (regression analysis):
- Each 100 servers adds: 2-3 weeks
- Each legacy system adds: 4-6 weeks
- Dedicated migration team vs. part-time: 40% faster
- Prior cloud experience: 30% faster

**Download Full Report**: [Cloud Migration Timeline Study 2024] (PDF, 45 pages)
```

**Expert Commentary**:

```markdown
## Expert Perspective: Why Most Cost Estimates Are Wrong

*By Maria Rodriguez, who has led $500M+ in cloud transformations*

After analyzing hundreds of cloud projects, I've noticed a consistent pattern:
initial cost estimates are off by an average of 35%.

### The Three Miscalculations

1. **Data Transfer Costs** (Average miss: $50K-200K/year)

   **What happens**: Teams estimate compute and storage but forget egress.

   **Real example**: A video platform migrated 500TB of content. They budgeted
   for S3 storage ($11,500/month) but missed CDN egress costs ($45,000/month).

   **My rule**: Add 15-20% for data transfer in high-traffic applications.

2. **Support & Training** (Average miss: $100K-300K first year)

   **What happens**: Teams budget for infrastructure but not enablement.

   **Real example**: Manufacturing company saved $200K/year on infrastructure
   but spent $250K on consultants because team lacked cloud expertise.

   **My rule**: Budget $2,000-5,000 per engineer for training and certification.

[Continue with point 3 and conclusions...]
```

#### Step 4: Citation-Ready Formatting

**Before** (not citation-worthy):

```html
<p>Many companies are moving to the cloud to save money and improve scalability.</p>
```

**After** (citation-ready):

```html
<div class="citation-ready-stat">
  <p><strong>Cloud Migration Adoption:</strong> 94% of enterprises use cloud services
  as of 2024, up from 89% in 2023, driven primarily by cost reduction (67% cite this
  as primary reason) and scalability requirements (54%).</p>

  <p class="source">
    <strong>Source:</strong> Flexera 2024 State of the Cloud Report
    <sup><a href="#citation-flexera-2024" class="citation-link">[1]</a></sup><br>
    <strong>Sample:</strong> 750 global enterprises, revenue $100M+<br>
    <strong>Methodology:</strong> Online survey, January 2024<br>
    <strong>Margin of Error:</strong> ±3.5% at 95% confidence level
  </p>
</div>
```

### Build Mode Output

```markdown
# Citation Readiness Report

## Current Status
**Citation Score**: 42/100 (Low)
**AI Engine Probability**: 15% (Below average)

## Citation-Worthy Elements Added

### 1. Source Citations (Added 15)
✅ Flexera State of Cloud 2024
✅ Gartner Cloud Forecast 2024
✅ AWS Customer Case Study - Netflix
✅ McKinsey Cloud Economics Report
[... 11 more]

### 2. Author Credentials
✅ Added author bio with 15 years experience
✅ Linked to LinkedIn, Google Scholar profiles
✅ Listed 5 relevant certifications
✅ Showed 23 peer-reviewed publications

### 3. Unique Value Added
✅ Original research: Cloud migration timeline study (200 projects)
✅ Expert commentary: Cost estimation mistakes
✅ Case study: 40% cost reduction with specific steps
✅ Comparison table: 4 cloud platforms vs. 8 features

### 4. Technical Optimization
✅ Implemented citation schema markup
✅ Added FAQ schema (5 Q&A pairs)
✅ Structured data for author
✅ Proper heading hierarchy

## New Citation Score: 92/100 (Excellent)
## Expected Citation Probability: 75% (High)

## AI Engine Feedback

**ChatGPT**: "High-quality source with clear attribution and expert analysis"
**Perplexity**: "Comprehensive data with original research"
**Claude**: "Well-structured, balanced perspective with strong sourcing"

## Next Steps

### To Reach 95+ Score
1. Add 2-3 more original data points
2. Get external validation (peer review or expert endorsement)
3. Add video/visual content
4. Publish updates quarterly to maintain recency

### Maintenance
- Update statistics every 6 months
- Add new citations as research emerges
- Monitor and respond to AI engine feedback
```

## Mode 2: Track AI Engine Citations

### What Citation Tracking Monitors

**Tracks**:

1. **Citation Frequency**: How often AI engines cite your content
2. **Citation Context**: What questions trigger citations
3. **Citation Completeness**: Full attribution vs. partial
4. **Competitive Citations**: Who else gets cited for your topics
5. **Traffic Impact**: Referral traffic from AI engines

### Tracking Methods

#### Method 1: Direct Testing

```javascript
const directTesting = {
  approach: "Ask AI engines questions and check for citations",

  testQueries: [
    "What are the benefits of cloud computing?",
    "How to reduce cloud costs?",
    "Cloud migration timeline?",
    "Best practices for cloud security?"
  ],

  aiEngines: [
    "ChatGPT (with Browse)",
    "Perplexity",
    "Claude (with search)",
    "Google SGE",
    "Bing Copilot"
  ],

  frequency: "Weekly",

  tracking: {
    cited: true/false,
    position: 1-10, // Citation order
    context: "Direct answer, supporting evidence, or additional resource",
    attribution: "Full (with link) or partial (paraphrased)"
  }
};
```

**Example Test Results**:

```markdown
## Citation Test Results - Week of Jan 15, 2024

Query: "How to reduce cloud costs by 40%?"

### ChatGPT (Browse Mode)
✅ **Cited**: Yes, Position #2
**Context**: "According to [YourSite.com], you can reduce cloud costs by
40% in 30 days by following these steps..."
**Attribution**: Full citation with link
**Traffic**: 47 referral visits this week

### Perplexity
✅ **Cited**: Yes, Position #1
**Context**: Listed as primary source in detailed answer
**Attribution**: Full citation with summary
**Traffic**: 89 referral visits this week

### Claude
❌ **Not Cited**: Used information but cited different source
**Reason**: Competitor site had more recent data (updated Feb 2024 vs. our Oct 2023)
**Action Needed**: Update statistics to current

### Google SGE
✅ **Cited**: Yes, Position #4
**Context**: Listed in "Related Resources" section
**Attribution**: Link only, no summary
**Traffic**: 23 referral visits this week

**Total Traffic from AI Citations**: 159 visits
**Conversion Rate**: 8.2% (13 conversions)
**Revenue**: $3,250 (avg. order $250)
```

#### Method 2: Referral Traffic Analysis

```javascript
const referralTracking = {
  gaSetup: {
    source: [
      "chatgpt.com",
      "perplexity.ai",
      "claude.ai",
      "google.com/sge",
      "bing.com"
    ],

    customDimensions: {
      aiEngine: "ChatGPT | Perplexity | Claude | SGE | Bing",
      citationType: "Direct Answer | Supporting Evidence | Related Resource",
      query: "User's original question (when available)"
    }
  },

  metrics: {
    sessions: "AI-referred sessions",
    users: "Unique users from AI engines",
    pageviews: "Pages viewed per AI session",
    conversionRate: "AI traffic conversion vs. organic",
    revenue: "Revenue from AI-referred traffic"
  },

  alerts: [
    "Citation traffic drops >20% week-over-week",
    "New AI engine starts sending traffic",
    "Specific page stops getting citations"
  ]
};
```

#### Method 3: Brand Monitoring

```javascript
const brandMonitoring = {
  tools: [
    "Google Alerts for [your domain]",
    "Brand24 for brand mentions",
    "Ahrefs for backlink tracking",
    "Custom scraping for AI engine results"
  ],

  monitors: {
    domainMentions: "Count mentions of yourdomain.com",
    brandMentions: "Count brand name mentions (with or without link)",
    topicOwnership: "% of citations for your core topics",
    sentimentAnalysis: "Positive, neutral, or negative context"
  },

  reporting: "Daily summary, weekly deep dive"
};
```

### Track Mode Output

```markdown
# AI Citation Tracking Report
**Period**: January 1-15, 2024 (2 weeks)

## Citation Summary

**Total Citations Detected**: 47
- ChatGPT: 18 citations (38%)
- Perplexity: 21 citations (45%)
- Claude: 3 citations (6%)
- Google SGE: 5 citations (11%)

**Citation Growth**: +35% vs. previous 2 weeks

## Top Cited Content

### 1. "How to Reduce Cloud Costs by 40%"
   - **Citations**: 12
   - **AI Engines**: ChatGPT (5), Perplexity (6), SGE (1)
   - **Avg Position**: #2.1
   - **Traffic**: 156 visits
   - **Conversions**: 14 (9% CVR)
   - **Revenue**: $3,500

### 2. "Cloud Migration Timeline Study 2024"
   - **Citations**: 9
   - **AI Engines**: Perplexity (7), ChatGPT (2)
   - **Avg Position**: #1.7
   - **Traffic**: 203 visits
   - **Conversions**: 8 (3.9% CVR)
   - **Revenue**: $1,200

### 3. "AWS vs Azure vs GCP Comparison 2024"
   - **Citations**: 8
   - **AI Engines**: ChatGPT (3), Perplexity (4), Claude (1)
   - **Avg Position**: #3.2
   - **Traffic**: 98 visits
   - **Conversions**: 12 (12.2% CVR)
   - **Revenue**: $4,800

## Citation Analysis

### Query Categories
1. **How-to Guides** (48% of citations)
   - "How to reduce cloud costs"
   - "How to migrate to cloud"
   - "How to optimize cloud performance"

2. **Comparisons** (28% of citations)
   - "AWS vs Azure vs GCP"
   - "Cloud vs on-premise costs"
   - "Best cloud provider for startups"

3. **Data/Statistics** (24% of citations)
   - "Cloud adoption statistics"
   - "Average cloud migration time"
   - "Cloud market share 2024"

### Citation Quality

**Full Attribution** (with link): 38 citations (81%)
**Partial Attribution** (paraphrased): 7 citations (15%)
**Mentioned but not linked**: 2 citations (4%)

### Competitive Analysis

**Your Citation Share**: 23% (you're cited in 23% of relevant queries)
**Top Competitor**: CloudEconomics.com (31% share)
**Opportunity**: You rank #2, potential to gain 8% share by updating content

## Traffic Impact

**Total AI-Referred Traffic**: 1,247 sessions
- ChatGPT: 412 sessions (33%)
- Perplexity: 589 sessions (47%)
- Claude: 87 sessions (7%)
- Google SGE: 159 sessions (13%)

**Engagement Metrics**:
- Avg. Session Duration: 4:32 (vs. 2:18 for organic)
- Avg. Pages/Session: 3.8 (vs. 2.1 for organic)
- Bounce Rate: 28% (vs. 48% for organic)

**Conversion Metrics**:
- Total Conversions: 89
- Conversion Rate: 7.1% (vs. 2.3% for organic)
- Revenue: $22,250
- AOV: $250

## Insights & Recommendations

### 🎯 Quick Wins
1. Update "Cloud Migration Timeline" with Q1 2024 data
   - Currently using Q4 2023 data
   - Claude not citing due to recency
   - **Potential**: +3-5 citations/week

2. Add FAQ schema to "AWS vs Azure" comparison
   - High traffic but mid-tier citations
   - FAQ format increases citation probability 40%
   - **Potential**: +2-4 citations/week

### 📈 Growth Opportunities
1. Create "Cloud Cost Calculator" tool
   - ChatGPT loves citing interactive tools
   - Competitors don't have this
   - **Potential**: +10-15 citations/week

2. Publish monthly "Cloud Market Update"
   - Fresh data = automatic citations
   - Perplexity favors recent content
   - **Potential**: +5-8 citations/week

### ⚠️ Risks
1. CloudEconomics.com gaining share in cost optimization
   - Their new calculator tool is getting heavy citations
   - **Action**: Launch competing tool within 30 days

2. Citation drop for "Security Best Practices" article
   - Was getting 8-10 citations/week, now 2-3
   - Content is 18 months old
   - **Action**: Complete refresh needed

## Next Period Goals

- **Citation Target**: 60 citations (+28%)
- **Traffic Target**: 1,600 sessions (+28%)
- **Revenue Target**: $30,000 (+35%)
- **Market Share Target**: 28% (+5 points)

**Top Priority**: Launch cloud cost calculator to compete with CloudEconomics.com
```

## Mode 3: Analyze Citation Patterns

### Citation Pattern Analysis

**Analyzes**:

1. **Content Characteristics**: What makes content get cited?
2. **Temporal Patterns**: When do citations occur?
3. **Query Intent**: What user questions trigger citations?
4. **Competitive Gaps**: Where competitors are beating you?
5. **ROI Analysis**: Which citations drive revenue?

### Analysis Output

```markdown
# AI Citation Pattern Analysis
**Analysis Period**: 90 days (Oct 15 - Jan 15, 2024)
**Total Citations**: 312

## Pattern 1: Content Type Performance

### Citation Rate by Content Type

| Content Type | Articles | Citations | Citation Rate | Avg. Position |
|--------------|----------|-----------|---------------|---------------|
| Original Research | 3 | 89 | 29.7 per article | #1.2 |
| Expert Commentary | 5 | 67 | 13.4 per article | #2.1 |
| Comparison Tables | 4 | 58 | 14.5 per article | #1.8 |
| How-To Guides | 12 | 71 | 5.9 per article | #3.4 |
| News/Updates | 8 | 18 | 2.3 per article | #5.2 |
| Opinion Pieces | 6 | 9 | 1.5 per article | #6.8 |

**Key Insight**: Original research gets cited 19.8x more than opinion pieces.

**Recommendation**: Prioritize creating original research and comparison content.

## Pattern 2: Optimal Content Length

### Citations by Word Count

- **500-1,000 words**: 12 citations (3.8%)
- **1,000-1,500 words**: 28 citations (9.0%)
- **1,500-2,500 words**: 156 citations (50.0%) ⭐
- **2,500-4,000 words**: 98 citations (31.4%)
- **4,000+ words**: 18 citations (5.8%)

**Sweet Spot**: 1,500-2,500 words (50% of all citations)

**Why**: Long enough for comprehensive answers, short enough to extract cleanly.

## Pattern 3: Recency Impact

### Citation Half-Life Analysis

```javascript
const citationHalfLife = {
  "0-3 months": {
    citationRate: 100, // Baseline
    avgCitations: 8.2 // Per week
  },
  "3-6 months": {
    citationRate: 78,   // -22%
    avgCitations: 6.4
  },
  "6-12 months": {
    citationRate: 45,   // -55%
    avgCitations: 3.7
  },
  "12-18 months": {
    citationRate: 22,   // -78%
    avgCitations: 1.8
  },
  "18+ months": {
    citationRate: 8,    // -92%
    avgCitations: 0.7
  }
};
```

**Key Insight**: Citations drop 50% after 6 months, 90% after 18 months.

**Recommendation**: Update top-performing content every 6 months.

## Pattern 4: AI Engine Preferences

### Content Preferences by Engine

**ChatGPT**:

- Prefers: How-to guides (42% of citations), clear steps, code examples
- Length: 1,200-2,000 words
- Format: Numbered lists, code blocks
- Recency: Moderate importance (6-12 month window)

**Perplexity**:

- Prefers: Original research (48%), statistics, comparisons
- Length: 1,800-2,800 words
- Format: Tables, data visualizations, citations
- Recency: Critical (prefers <3 months)

**Claude**:

- Prefers: Nuanced analysis (38%), balanced perspectives
- Length: 2,500-4,000 words (longer form)
- Format: Detailed explanations, context, caveats
- Recency: Moderate importance

**Google SGE**:

- Prefers: Quick answers (52%), featured snippet format
- Length: 800-1,500 words
- Format: Bullets, short paragraphs, FAQs
- Recency: Important (prefers <6 months)

## Pattern 5: Query Intent Mapping

### Top Query Intents That Led to Citations

1. **Informational (52%)**
   - "What is [topic]?"
   - "How does [technology] work?"
   - "Benefits of [solution]"
   - **Your Performance**: Strong (65% citation rate)

2. **Comparative (28%)**
   - "[Option A] vs [Option B]"
   - "Best [category] for [use case]"
   - "[Product] alternatives"
   - **Your Performance**: Excellent (78% citation rate)

3. **Procedural (14%)**
   - "How to [task]"
   - "Steps to [goal]"
   - "[Task] tutorial"
   - **Your Performance**: Moderate (42% citation rate)

4. **Statistical (6%)**
   - "[Topic] statistics 2024"
   - "How many [metric]"
   - "[Industry] market size"
   - **Your Performance**: Weak (18% citation rate)

**Opportunity**: Create more statistical content to capture 6% query share.

## Pattern 6: Competitive Gap Analysis

### Topics Where Competitors Win

| Topic | Your Citations | Competitor Citations | Gap | Winner |
|-------|----------------|---------------------|-----|---------|
| Cloud Cost Optimization | 23 | 31 | -8 | CloudEconomics.com |
| Multi-Cloud Strategy | 8 | 24 | -16 | CloudArchitects.io |
| Cloud Security Best Practices | 12 | 28 | -16 | SecureCloud.net |
| Kubernetes Management | 5 | 19 | -14 | K8sExperts.com |

### Why They Win

**CloudEconomics.com** (Cost Optimization):

- Has interactive cost calculator (you don't)
- Updates monthly with new case studies (you update quarterly)
- More original data (15 studies vs. your 3)

**Recommended Actions**:

1. Build cost calculator tool (4 week project)
2. Increase case study frequency to monthly
3. Conduct original research on cost optimization

## Pattern 7: Revenue Attribution

### Citation ROI Analysis

| Content | Citations | Traffic | Revenue | Revenue/Citation |
|---------|-----------|---------|---------|------------------|
| Cloud Cost Guide | 89 | 1,247 | $31,250 | $351 |
| Migration Timeline Study | 67 | 892 | $18,900 | $282 |
| AWS vs Azure Comparison | 58 | 743 | $29,600 | $510 ⭐ |
| Security Best Practices | 45 | 567 | $8,500 | $189 |

**Highest ROI**: Comparison content ($510 per citation)
**Lowest ROI**: Best practices content ($189 per citation)

**Why Comparisons Win**:

- Higher purchase intent
- Users ready to make decisions
- Multiple CTAs for different options

**Recommendation**: Create 3 more comparison guides for high-value topics.

## Pattern 8: Seasonal Trends

### Citations by Month

```
Oct: ████████████████ 78 citations
Nov: ███████████████████ 95 citations
Dec: ███████████ 52 citations (holiday drop)
Jan: ██████████████████████ 112 citations (new year surge)
```

**Q4 Pattern**: 35% citation drop in December (holidays)
**Q1 Pattern**: 115% surge in January (planning season, budget cycles)

**Recommendation**:

- Pre-publish content in December for January surge
- Focus updates in October-November for Q4 traffic
- Plan original research releases for January

## Strategic Recommendations

### Top 5 Actions to Increase Citations

1. **Launch Interactive Tools** (Estimated Impact: +40 citations/month)
   - Cost calculator
   - Migration timeline estimator
   - ROI calculator

2. **Increase Content Freshness** (Estimated Impact: +25 citations/month)
   - Update top 10 articles monthly
   - Add "Last Updated" dates prominently
   - Archive content older than 18 months

3. **Create More Comparisons** (Estimated Impact: +20 citations/month)
   - 3 new comparison guides
   - Update existing comparisons quarterly
   - Add new comparison criteria

4. **Original Research Program** (Estimated Impact: +35 citations/month)
   - Monthly mini-studies (n=50-100)
   - Quarterly major research (n=500+)
   - Partner with universities for credibility

5. **Optimize for Perplexity** (Estimated Impact: +15 citations/month)
   - Increase citation density in content
   - Add more data visualizations
   - Focus on very recent data (<3 months)

**Total Estimated Impact**: +135 citations/month (+43%)

### Investment Required

- **Interactive Tools**: $15,000 (one-time development)
- **Content Updates**: $5,000/month (writers + researchers)
- **Original Research**: $8,000/month (surveys + analysis)
- **Total Monthly**: $13,000/month + $15K one-time

**Expected ROI**:

- Current: 312 citations/quarter = $89,000 revenue
- Projected: 447 citations/quarter = $127,000 revenue
- **Net Gain**: $38,000/quarter = $152,000/year
- **ROI**: 977% annually

```

## Best Practices for Citation-Worthy Content

### The Citation Checklist

```markdown
## Before Publishing, Verify:

### Accuracy & Credibility
- [ ] Every statistic has a source citation
- [ ] All sources are authoritative (.edu, .gov, industry leaders)
- [ ] Data is current (within 12-18 months)
- [ ] Author credentials are prominently displayed
- [ ] Facts have been verified by second source

### Structure & Format
- [ ] Clear H2 headings that match common questions
- [ ] First paragraph directly answers main question
- [ ] Key points in bullet or numbered lists
- [ ] Complex data in comparison tables
- [ ] TL;DR or summary box at top

### Technical Optimization
- [ ] FAQ schema implemented (if applicable)
- [ ] Article schema with citation markup
- [ ] Author schema with credentials
- [ ] Meta description answers main question
- [ ] Image alt text is descriptive
- [ ] Page loads in <3 seconds

### Unique Value
- [ ] At least one unique element (original research, expert commentary, or case study)
- [ ] Not just rehashing existing content
- [ ] Specific, actionable insights
- [ ] Real-world examples with results

### Citation Format
- [ ] Inline citations with superscript links
- [ ] Full citation details at bottom
- [ ] Source methodology explained
- [ ] Sample sizes and dates included

**Citation Readiness Score**: [X]/20
- 18-20: Excellent, ready to publish
- 15-17: Good, minor improvements needed
- 12-14: Moderate, significant improvements needed
- <12: Not ready, major revisions required
```

## Integration with Other Commands

```bash
# Complete AI search workflow

# 1. Build citation-worthy content
/ai-search/citations --mode build

# 2. Optimize for AI search
/ai-search/optimize

# 3. Add structured snippets
/ai-search/snippets

# 4. Track performance
/ai-search/citations --mode track

# 5. Monitor and analyze
/ai-search/monitor --focus citations
```

## Troubleshooting

### Problem: Not Getting Cited Despite Good Content

**Diagnosis**:

1. Run `/ai-search/citations --mode build` to check citation score
2. Test manually: Ask AI engines your target questions
3. Check if competitors are being cited instead

**Common Causes**:

- Content is too old (>12 months)
- No clear, quotable answers
- Missing source citations
- No author credentials
- Competitors have better E-E-A-T signals

**Fix**:

1. Update content with recent data
2. Add direct answer boxes
3. Implement proper citation format
4. Add/enhance author bio
5. Build more authoritative backlinks

### Problem: Citations But No Traffic

**Diagnosis**:

1. Check if AI engines link to your site or just mention it
2. Verify citation appears in response (not just sources list)
3. Test if URL is clickable

**Common Causes**:

- Paraphrased without link
- Link in "sources" section users don't click
- Mobile display hides sources
- Citation appears late in response

**Fix**:

1. Make content MORE citation-worthy so you move up
2. Create multiple citation opportunities in single article
3. Add CTAs for users who do click through
4. Optimize landing page conversion

---

**Ready to become the most-cited source in your industry?** Run `/ai-search/citations` to start building citation-worthy content and tracking your AI search performance.
