---
description: Generate market positioning and competitive differentiation for product
argument-hint: <product-name> [--competitors "<comma-separated-list>"]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, WebSearch, Write
---

Product positioning: **${ARGUMENTS}**

## Market Positioning Strategy

**Generates**:

- Positioning statement
- Value proposition
- Target market definition
- Competitive differentiation
- Messaging framework
- Pricing positioning

Routes to **prompt-engineering-agent** + **ux-research-analyst**:

```javascript
await Task({
  subagent_type: 'prompt-engineering-agent',
  description: 'Generate product positioning strategy',
  prompt: `Generate market positioning for: ${PRODUCT_NAME}

Competitors: ${COMPETITORS || 'Research and identify top 3-5 competitors'}

Execute comprehensive positioning analysis:

## 1. Research Market and Competitors

### Identify Competitors

${COMPETITORS ? \`
Analyze specified competitors: \${COMPETITORS}
\` : \`
Research and identify top 3-5 competitors in the market.

Use WebSearch to find:
- Direct competitors (same product category)
- Indirect competitors (alternative solutions)
- Category leaders (market share leaders)
\`}

### Analyze Competitor Positioning

For each competitor, extract:

\`\`\`javascript
const competitorAnalysis = {
  name: 'Competitor Name',
  positioning: 'How they position themselves',
  targetMarket: 'Who they target',
  keyFeatures: ['Feature 1', 'Feature 2', 'Feature 3'],
  pricing: { model: 'freemium/subscription/one-time', tiers: [...] },
  strengths: ['Strength 1', 'Strength 2'],
  weaknesses: ['Weakness 1', 'Weakness 2'],
  differentiators: ['What makes them unique']
};
\`\`\`

Use WebSearch for competitor websites, G2, Capterra reviews.

## 2. Define Target Market

### Ideal Customer Profile (ICP)

\`\`\`markdown
## Ideal Customer Profile

**Company Size**: [Startups / SMB / Mid-Market / Enterprise]
**Industry**: [Primary industries that benefit most]
**Geography**: [Target regions]
**Tech Stack**: [Tools they currently use]
**Budget**: [Annual budget for this category]

**Pain Points**:
1. [Primary pain point]
2. [Secondary pain point]
3. [Tertiary pain point]

**Goals**:
1. [What they want to achieve]
2. [What success looks like]

**Buying Process**:
- **Decision Maker**: [Title/role]
- **Influencers**: [Other stakeholders]
- **Budget Cycle**: [When they buy]
- **Evaluation Criteria**: [What they care about]
\`\`\`

### Buyer Personas

Create 2-3 primary personas:

\`\`\`markdown
## Persona 1: [Name] - [Title]

**Demographics**:
- Title: [e.g., VP of Engineering]
- Company Size: [e.g., 50-500 employees]
- Industry: [e.g., SaaS, E-commerce]

**Goals**:
- Improve team productivity by 30%
- Reduce manual work and errors
- Scale operations without hiring

**Pain Points**:
- Too much time on repetitive tasks
- Lack of visibility into team performance
- Tools don't integrate well

**How We Help**:
- Automate 60% of repetitive tasks
- Real-time dashboards and analytics
- Native integrations with all major tools

**Messaging**:
"Help your engineering team ship 2x faster with automated workflows"

**Channels**:
- LinkedIn
- Technical blogs
- Developer communities
\`\`\`

## 3. Craft Positioning Statement

### Positioning Framework

Use Geoffrey Moore's positioning template:

\`\`\`
For [target customer]
Who [statement of need or opportunity]
[Product name] is a [product category]
That [statement of key benefit]

Unlike [primary competitive alternative]
Our product [statement of primary differentiation]
\`\`\`

### Example Positioning Statement

\`\`\`markdown
For **growing SaaS companies**
Who **struggle with manual sales processes and pipeline visibility**

**\${PRODUCT_NAME}** is a **sales automation and analytics platform**
That **automates 70% of sales admin work and provides real-time revenue insights**

Unlike **Salesforce**
Our product **is 10x faster to set up, costs 1/3 the price, and includes AI-powered forecasting out of the box**
\`\`\`

## 4. Define Value Proposition

### Value Proposition Canvas

\`\`\`markdown
## Value Proposition

**For**: \${TARGET_CUSTOMER}

### Customer Jobs
What they're trying to get done:
1. [Functional job - what they need to accomplish]
2. [Social job - how they want to be perceived]
3. [Emotional job - how they want to feel]

### Customer Pains
What frustrates them:
1. **Obstacle**: [What prevents them from getting the job done]
2. **Risk**: [What could go wrong]
3. **Unwanted Outcome**: [What they want to avoid]

### Customer Gains
What they want to achieve:
1. **Required**: [Must-have outcomes]
2. **Expected**: [Should-have outcomes]
3. **Desired**: [Nice-to-have outcomes]
4. **Unexpected**: [Beyond expectations]

---

### Our Solution

**Products & Services**:
1. [Core product/feature 1]
2. [Core product/feature 2]
3. [Core product/feature 3]

**Pain Relievers**:
How we eliminate or reduce pains:
1. **Eliminates**: [How we remove obstacle 1]
2. **Reduces**: [How we minimize risk 1]
3. **Prevents**: [How we avoid unwanted outcome 1]

**Gain Creators**:
How we create gains:
1. **Delivers**: [How we produce required gain 1]
2. **Maximizes**: [How we exceed expected gain 1]
3. **Surprises**: [How we deliver unexpected gain 1]
\`\`\`

### One-Liner Value Proposition

**Formula**: [What you do] for [who] to [outcome] without [pain]

**Example**:
"\${PRODUCT_NAME} automates sales workflows for B2B teams to close 30% more deals without hiring more reps"

## 5. Competitive Differentiation

### Differentiation Matrix

\`\`\`markdown
## Competitive Differentiation

| Feature/Attribute | Us | Competitor 1 | Competitor 2 | Competitor 3 |
|-------------------|-------|--------------|--------------|--------------|
| Setup Time | ✅ 15 min | ❌ 2-3 weeks | ⚠️ 2-3 days | ✅ 1 hour |
| AI-Powered Forecasting | ✅ Built-in | ❌ Add-on ($$$) | ❌ No | ⚠️ Basic |
| Native Integrations | ✅ 50+ | ✅ 100+ | ⚠️ 20 | ⚠️ 15 |
| Pricing | ✅ $49/user | ❌ $150/user | ✅ $39/user | ⚠️ $99/user |
| Mobile App | ✅ Excellent | ✅ Good | ❌ No | ⚠️ Basic |
| Customer Support | ✅ 24/7 chat | ⚠️ Email only | ⚠️ Business hours | ✅ 24/7 phone |

**Legend**: ✅ Strong, ⚠️ Adequate, ❌ Weak/Missing
\`\`\`

### Unique Differentiators

\`\`\`markdown
## What Makes Us Different

### 1. **[Differentiator 1 Title]**
**What**: [What we do differently]
**Why it matters**: [Customer benefit]
**Proof**: [Evidence - metric, testimonial, case study]

### 2. **[Differentiator 2 Title]**
**What**: [What we do differently]
**Why it matters**: [Customer benefit]
**Proof**: [Evidence]

### 3. **[Differentiator 3 Title]**
**What**: [What we do differently]
**Why it matters**: [Customer benefit]
**Proof**: [Evidence]
\`\`\`

## 6. Messaging Framework

### Core Messages by Audience

\`\`\`markdown
## Messaging Framework

### For Decision Makers (C-Suite, VPs)

**Core Message**: "Accelerate revenue growth while reducing sales costs"

**Supporting Messages**:
1. "Increase sales productivity by 40% without adding headcount"
2. "Predictable revenue with AI-powered forecasting (95% accuracy)"
3. "ROI in 90 days or money back"

**Proof Points**:
- Average customer sees 30% revenue increase in 6 months
- Customers save 15 hours per rep per week
- 4.8/5 G2 rating from 500+ reviews

---

### For Users (Sales Reps, Managers)

**Core Message**: "Spend more time selling, less time on admin"

**Supporting Messages**:
1. "Automate data entry, follow-ups, and reporting"
2. "Know exactly which deals to focus on with AI prioritization"
3. "Works seamlessly with tools you already use"

**Proof Points**:
- 10x faster than manual CRM entry
- Mobile app lets you work from anywhere
- Set up in 15 minutes, no IT required

---

### For Buyers/Evaluators

**Core Message**: "Enterprise power at SMB price and speed"

**Supporting Messages**:
1. "Get started in 15 minutes, not 2 weeks"
2. "1/3 the cost of Salesforce, 10x easier to use"
3. "Scales with you from 5 to 500 reps"

**Proof Points**:
- $49/user vs $150/user (competitors)
- 15-minute setup vs 2-3 week implementations
- 99.9% uptime SLA
\`\`\`

## 7. Pricing Positioning

### Pricing Strategy

\`\`\`markdown
## Pricing Positioning

**Strategy**: [Value-based / Competitive / Penetration / Premium]

**Positioning in Market**:
- Competitors range: $39 - $150 per user/month
- Our pricing: $49 per user/month
- **Position**: Mid-market value leader

**Why This Price**:
1. **Above**: Cheaper competitors lack critical features (AI, integrations)
2. **Below**: Enterprise competitors overcharge for bloated features
3. **Sweet Spot**: Premium features at accessible price

**Value Messaging**:
"Enterprise-grade sales automation at 1/3 the price of Salesforce"

**Anchoring**:
- ROI: "Save 15 hours/week per rep = $15,000/year value for $588/year cost"
- Alternative: "Hiring one extra rep ($60K/year) vs our product ($588/year)"
- Comparison: "Salesforce ($1,800/year) vs us ($588/year) = save $1,212/year"
\`\`\`

## 8. Generate Complete Positioning Document

\`\`\`markdown
# Product Positioning: \${PRODUCT_NAME}

**Date**: \${DATE}
**Market**: \${MARKET_CATEGORY}

---

## Executive Summary

**Positioning Statement**:
\${POSITIONING_STATEMENT}

**One-Line Value Proposition**:
\${ONE_LINER}

**Target Market**: \${TARGET_MARKET}
**Price Point**: $\${PRICE} per user/month
**Market Position**: \${MARKET_POSITION}

---

## Target Market

### Ideal Customer Profile (ICP)

\${ICP_DETAILS}

### Primary Buyer Personas

\${PERSONA_1}

\${PERSONA_2}

\${PERSONA_3}

---

## Value Proposition

\${VALUE_PROP_CANVAS}

**One-Liner**: \${ONE_LINER_VALUE_PROP}

**Key Benefits**:
1. \${BENEFIT_1}
2. \${BENEFIT_2}
3. \${BENEFIT_3}

---

## Competitive Landscape

### Direct Competitors

\${COMPETITOR_ANALYSIS}

### Differentiation Matrix

\${DIFFERENTIATION_MATRIX}

### Our Unique Advantages

\${UNIQUE_DIFFERENTIATORS}

---

## Messaging Framework

\${MESSAGING_BY_AUDIENCE}

### Elevator Pitch (30 seconds)

"\${ELEVATOR_PITCH}"

### 2-Minute Pitch

"\${TWO_MINUTE_PITCH}"

---

## Pricing Positioning

\${PRICING_STRATEGY}

**Price**: $\${PRICE}/user/month
**Position in Market**: \${PRICE_POSITION}
**Value Message**: "\${PRICE_VALUE_MESSAGE}"

---

## Go-to-Market Recommendations

### Channels
1. **Primary**: \${PRIMARY_CHANNEL} (Why: \${REASON})
2. **Secondary**: \${SECONDARY_CHANNEL}
3. **Tertiary**: \${TERTIARY_CHANNEL}

### Campaign Ideas
1. \${CAMPAIGN_1}
2. \${CAMPAIGN_2}
3. \${CAMPAIGN_3}

### Content Strategy
- **Blog Topics**: \${BLOG_TOPICS}
- **Case Studies**: \${CASE_STUDY_THEMES}
- **SEO Keywords**: \${TARGET_KEYWORDS}

---

## Next Steps

1. **This Week**:
   - [ ] Update website homepage with new positioning
   - [ ] Revise sales deck with messaging framework
   - [ ] Train sales team on new positioning

2. **This Month**:
   - [ ] Create content based on messaging framework
   - [ ] Update all marketing materials
   - [ ] Run A/B test on new vs old positioning

3. **This Quarter**:
   - [ ] Launch competitive campaign
   - [ ] Measure positioning effectiveness
   - [ ] Refine based on market feedback

---

**Review Date**: \${REVIEW_DATE} (quarterly recommended)
\`\`\`

Save to: product-positioning/\${PRODUCT_NAME}-positioning-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Generate positioning for product
/product/positioning "SalesFlow AI"

# With known competitors
/product/positioning "SalesFlow AI" --competitors "Salesforce, HubSpot, Pipedrive"

# Research competitors first
/product/positioning "TaskMaster Pro"
```

## Output Includes

1. **Positioning Statement** (Geoffrey Moore framework)
2. **Value Proposition** (Value Proposition Canvas)
3. **Target Market** (ICP + Personas)
4. **Competitive Analysis** (Differentiation matrix)
5. **Messaging Framework** (By audience)
6. **Pricing Positioning** (Market position)
7. **GTM Recommendations** (Channels, campaigns)

## Success Criteria

- ✓ Clear positioning statement
- ✓ Differentiation from competitors identified
- ✓ Target market defined (ICP + personas)
- ✓ Value proposition articulated
- ✓ Messaging framework created
- ✓ Pricing strategy defined
- ✓ GTM recommendations provided
- ✓ Complete positioning document saved

## When to Use

- **New Product Launch**: Define positioning before launch
- **Repositioning**: Market shift or new competitors
- **Pricing Changes**: Justify and communicate new pricing
- **Sales Enablement**: Train sales team on positioning
- **Marketing Campaigns**: Ensure consistent messaging
- **Quarterly Reviews**: Refresh positioning based on market feedback

---
**Uses**: prompt-engineering-agent, ux-research-analyst, WebSearch (competitor research)
**Output**: Complete product positioning document with GTM recommendations
**Next Commands**: `/product/summarize` (generate marketing copy), `/landing/create` (build landing page)
**Review Frequency**: Quarterly recommended
