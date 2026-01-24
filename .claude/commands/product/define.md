---
description: Define and refine product with AI-assisted analysis and questioning
argument-hint: <product-name> [--category saas|app|service|hardware] [--from-solution <folder-path>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, AskUserQuestion, Write, Bash, Read
---

Define product: **${ARGUMENTS}**

## Product Definition Process

**AI-Assisted Product Discovery** - Deep questioning to refine concept
**Market Analysis** - Competitor research and positioning
**Feature Prioritization** - AI-powered feature ranking
**Pricing Strategy** - Value-based pricing recommendations
**Zoho Catalog Integration** - Store in central product database

## Argument Parsing

Parse arguments to check for `--from-solution` flag:

```javascript
const args = parseArguments(ARGUMENTS)
const productName = args.positional[0]
const category = args['--category']
const solutionFolder = args['--from-solution']

if (solutionFolder) {
  // Load extracted product definition from solution folder
  const jsonPath = `${solutionFolder}/extracted-product-definition.json`

  try {
    const extractedData = await Read(jsonPath)
    const productData = JSON.parse(extractedData)

    console.log(`✓ Loaded extracted product definition from ${jsonPath}`)
    console.log(`📦 Product: ${productData.product.name}`)
    console.log(`📊 Confidence: ${productData.confidence.overall}`)
    console.log(`📁 Data sources: ${productData.metadata.dataSources.completionReports.length + productData.metadata.dataSources.strategyFiles.length} files`)

    // Pre-populate discovery with extracted data
    // Continue to Step "AI Product Definition with Pre-Loaded Data" below
  } catch (error) {
    console.log(`⚠️ Warning: Could not load ${jsonPath}`)
    console.log(`Run /product:extract-from-solution ${solutionFolder} first`)
    console.log(`Falling back to interactive discovery...`)
    // Fall through to normal interactive flow
  }
}
```

## AI Product Definition with Pre-Loaded Data

If `--from-solution` flag was provided and JSON loaded successfully:

Routes to **prompt-engineering-agent** with pre-populated data:

```javascript
await Task({
  subagent_type: 'prompt-engineering-agent',
  description: 'Define and refine product concept',
  prompt: `Conduct product definition refinement with pre-loaded data.

**Pre-Loaded Product Data**:
${JSON.stringify(productData, null, 2)}

Execute refined product discovery workflow:

## 1. Review Extracted Data

Present extracted data to user for validation:

**Product Overview**:
  • Name: ${productData.product.name}
  • Type: ${productData.product.type}
  • Description: ${productData.product.description.short}

**Metrics** (from ${productData.metadata.dataSources.completionReports[0]}):
  • Quality Score: ${productData.product.metrics.qualityScore}/100
  • Time Savings: ${productData.product.metrics.timeSavings}
  • Cost Savings: ${productData.product.metrics.costSavings}
  • ROI: ${productData.product.metrics.roi}

**Features** (${productData.product.features.length} extracted):
${productData.product.features.map((f, i) => `  ${i + 1}. ${f.name} - ${f.description}`).join('\n')}

**Target Audience**:
  • Role: ${productData.product.targetAudience.primaryPersona.role}
  • Company Size: ${productData.product.targetAudience.primaryPersona.companySize}
  • Industry: ${productData.product.targetAudience.primaryPersona.industry}

**Pricing Recommendations**:
  • Starter: $${productData.product.pricingRecommendations.recommendedPricing.starter.price}/month
  • Pro: $${productData.product.pricingRecommendations.recommendedPricing.pro.price}/month
  • Enterprise: $${productData.product.pricingRecommendations.recommendedPricing.enterprise.price}/month

**Confidence**: ${productData.confidence.overall}
${productData.confidence.missingData.length > 0 ? `\n**Missing Data**: ${productData.confidence.missingData.join(', ')}` : ''}

**Data Sources Used**:
${productData.metadata.dataSources.completionReports.map(f => `  ✓ ${f}`).join('\n')}
${productData.metadata.dataSources.strategyFiles.map(f => `  ✓ ${f}`).join('\n')}

Ask user to confirm extracted data accuracy using AskUserQuestion:

"Review the extracted product data above. What would you like to do?"

Options:
1. "Looks good - proceed with refinement" → Continue to Step 2
2. "Need to correct some data" → Ask which fields to correct, update productData
3. "Start fresh with interactive discovery" → Ignore extracted data, go to normal flow

## 2. Focused Refinement Questions

Ask targeted questions to fill gaps or refine extracted data:

**Gap-Filling Questions** (only ask if data missing):
${productData.confidence.missingData.includes('Product images/screenshots') ? '- Do you have product images/screenshots? If yes, where are they located?' : ''}
${productData.confidence.missingData.includes('Competitor analysis') ? '- Who are your top 3 competitors?' : ''}
${productData.confidence.missingData.includes('User testimonials') ? '- Do you have any customer testimonials or case studies?' : ''}

**Refinement Questions** (even if data exists):
- Is the extracted value proposition accurate? Would you refine it?
- Are the pricing recommendations aligned with your go-to-market strategy?
- Should we adjust the feature prioritization based on your roadmap?
- Any additional use cases or personas we should include?

Use AskUserQuestion for interactive refinement.

## 3. Enhanced Product Definition

Generate comprehensive product definition incorporating:
- Extracted data (metrics, features, audience)
- User corrections (from Step 1-2)
- AI analysis and recommendations
- Market validation and competitive positioning

Use the same markdown template as normal /product:define flow, but pre-populate with extracted data.

## 4. Zoho Catalog Integration

After human approval, create product in Zoho Catalog with richer data:

\`\`\`json
{
  "product_name": "${productData.product.name}",
  "product_description": "${productData.product.description.long}",
  "product_category": "${productData.product.type}",

  // Enhanced with extracted metrics
  "custom_fields": {
    "quality_score": ${productData.product.metrics.qualityScore},
    "time_savings": "${productData.product.metrics.timeSavings}",
    "cost_savings": "${productData.product.metrics.costSavings}",
    "roi": "${productData.product.metrics.roi}",
    "confidence_level": "${productData.confidence.overall}"
  },

  "pricing_tiers": [
    {
      "name": "Starter",
      "price": ${productData.product.pricingRecommendations.recommendedPricing.starter.price},
      "billing_cycle": "monthly",
      "features": ${JSON.stringify(productData.product.pricingRecommendations.recommendedPricing.starter.features)}
    },
    {
      "name": "Pro",
      "price": ${productData.product.pricingRecommendations.recommendedPricing.pro.price},
      "billing_cycle": "monthly",
      "features": ${JSON.stringify(productData.product.pricingRecommendations.recommendedPricing.pro.features)}
    },
    {
      "name": "Enterprise",
      "price": ${productData.product.pricingRecommendations.recommendedPricing.enterprise.price},
      "billing_cycle": "monthly",
      "features": ${JSON.stringify(productData.product.pricingRecommendations.recommendedPricing.enterprise.features)}
    }
  ],

  "target_market": {
    "primary_persona": "${productData.product.targetAudience.primaryPersona.role}",
    "company_size": "${productData.product.targetAudience.primaryPersona.companySize}",
    "industry": "${productData.product.targetAudience.primaryPersona.industry}"
  },

  "competitive_positioning": "${productData.product.competitivePositioning.positioningStatement}",
  "tags": ["${productData.product.type}", "ai", "automation"],
  "status": "in_development"
}
\`\`\`

Save to:
  • Local file: products/${productData.product.name.toLowerCase().replace(/\s+/g, '-')}-definition.md
  • Zoho Catalog: Create product record
  • Update extracted JSON with Zoho product ID

Provide next steps:
  1. Review and approve product definition
  2. Run /product/summarize to generate marketing copy
  3. Run /campaign:create to build marketing campaign
  4. Create Shopify product listing (manual or /shopify:sync when available)
  `
})
```

## AI Product Definition

Routes to **prompt-engineering-agent** to conduct structured product discovery:

```javascript
await Task({
  subagent_type: 'prompt-engineering-agent',
  description: 'Define and refine product concept',
  prompt: `Conduct comprehensive product definition for: ${PRODUCT_NAME}

Category: ${CATEGORY || 'not specified - need to determine'}

Execute structured product discovery:

## 1. Initial Concept Validation

Ask critical questions to understand the product:

**Target Market Questions**:
- Who is this product for? (Be specific: role, company size, industry)
- What is their current pain point or problem?
- How are they solving this problem today?
- Why is the current solution inadequate?
- What would make them switch to your solution?

**Product Questions**:
- What does this product do? (One sentence value proposition)
- What are the 3 core features that deliver the main value?
- What features are "nice to have" but not essential?
- What will you NOT build (important to define scope)?
- How is this different from competitors?

**Business Model Questions**:
- How will customers pay? (Subscription, one-time, usage-based?)
- What's the target price point? (Or pricing range?)
- What's the expected customer lifetime value?
- What's an acceptable customer acquisition cost?

Use AskUserQuestion to gather answers iteratively.

## 2. AI Analysis & Recommendations

Based on answers, provide:

**Market Validation**:
- Is there a clear pain point being solved?
- Is the target market well-defined and reachable?
- What's the estimated market size?
- Who are the top 3 competitors?
- What's your unique positioning?

**Feature Prioritization** (using RICE framework):
For each proposed feature, score:
- Reach: How many customers need this?
- Impact: How much does it improve their outcome?
- Confidence: How sure are we about this?
- Effort: How hard is it to build?

Calculate RICE score: (Reach × Impact × Confidence) / Effort

Rank features by RICE score.

**Pricing Recommendations**:
- Analyze competitor pricing
- Calculate value-based pricing
- Suggest tiering strategy (Free, Pro, Enterprise)
- Estimate price elasticity

**Risk Assessment**:
- What could kill this product?
- What assumptions need to be validated?
- What's the minimum viable feature set?

## 3. Generate Product Definition Document

Create structured product definition:

\`\`\`markdown
# Product Definition: [Product Name]

## Executive Summary
[One paragraph: What, Who, Why]

## Problem Statement
**Who has the problem**: [Target customer]
**What the problem is**: [Specific pain point]
**Current solution**: [How they solve it today]
**Why current solution fails**: [Inadequacies]

## Solution
**Value Proposition**: [One sentence]
**How it works**: [2-3 sentences]
**Key Benefits**:
  1. [Primary benefit with metric if possible]
  2. [Secondary benefit]
  3. [Tertiary benefit]

## Target Market

**Primary Persona**:
  • Role: [Job title]
  • Company Size: [Employee count range]
  • Industry: [Specific industries]
  • Pain Points: [Top 3]
  • Goals: [What they want to achieve]

**Secondary Persona**: [If applicable]

**Market Size**:
  • TAM (Total Addressable Market): [Estimate]
  • SAM (Serviceable Available Market): [Estimate]
  • SOM (Serviceable Obtainable Market): [3-year target]

## Product Features

**Core Features** (MVP):
  1. [Feature 1] - RICE Score: [X]
     - User Story: As a [user], I want to [action] so that [benefit]
     - Acceptance Criteria: [What defines "done"]

  2. [Feature 2] - RICE Score: [X]
  3. [Feature 3] - RICE Score: [X]

**Roadmap Features** (Post-MVP):
  1. [Feature 4] - RICE Score: [X]
  2. [Feature 5] - RICE Score: [X]

**Out of Scope** (Won't Build):
  - [Feature X] - Reason: [Why not]
  - [Feature Y] - Reason: [Why not]

## Competitive Landscape

| Competitor | Strengths | Weaknesses | Our Advantage |
|------------|-----------|------------|---------------|
| [Comp 1]   | [Strength]| [Weakness] | [How we win]  |
| [Comp 2]   | [Strength]| [Weakness] | [How we win]  |

**Positioning Statement**:
For [target customer] who [need/want], [Product] is a [category] that [key benefit]. Unlike [competitor], we [unique differentiator].

## Pricing Strategy

**Pricing Model**: [Subscription / One-time / Usage-based / Hybrid]

**Tiers**:

1. **Free** (Lead Generation)
   - Price: $0
   - Features: [Limited features for trial]
   - Limitations: [What's restricted]
   - Target: [Individual users, small projects]

2. **Pro** (Primary Revenue)
   - Price: $[X]/month (or $[Y]/year with discount)
   - Features: [All core features + some advanced]
   - Target: [Small teams, growing companies]
   - Why this price: [Value-based justification]

3. **Team/Business** (Expansion Revenue)
   - Price: $[X]/user/month or $[X]/month for team
   - Features: [Collaboration, advanced features]
   - Target: [Teams of 5-50]

4. **Enterprise** (High-value Accounts)
   - Price: Custom (starting at $[X]/month)
   - Features: [SSO, dedicated support, SLA]
   - Target: [50+ users, compliance requirements]

**Pricing Rationale**:
- Competitor range: $[X] - $[Y]
- Value delivered: $[Z] (ROI calculation)
- Our positioning: [Premium / Mid-market / Budget]

## Success Metrics

**Product Metrics**:
  • Activation: [What defines an active user?]
  • Engagement: [DAU/MAU ratio target]
  • Retention: [% still active after 30/60/90 days]
  • NPS Target: [Score]

**Business Metrics**:
  • MRR Target (Month 3): $[X]
  • Customer Count (Month 6): [Y]
  • Average Deal Size: $[Z]
  • CAC Target: $[A]
  • LTV Target: $[B]
  • LTV:CAC Ratio: [C:1]

## Go-to-Market Strategy

**Launch Strategy**:
  1. [Phase 1: Beta / Private Launch]
  2. [Phase 2: Public Launch / Product Hunt]
  3. [Phase 3: Scale / Paid Acquisition]

**Distribution Channels**:
  • Primary: [e.g., Product Hunt, Direct Sales, Content Marketing]
  • Secondary: [e.g., Partnerships, Affiliates]

**Key Risks & Mitigation**:
  1. **Risk**: [What could go wrong]
     **Mitigation**: [How to prevent/handle it]

  2. **Risk**: [Another risk]
     **Mitigation**: [Mitigation strategy]

## Development Roadmap

**Phase 1: MVP** (Weeks 1-8)
  - [Core Feature 1]
  - [Core Feature 2]
  - [Core Feature 3]
  - [Basic Landing Page]
  - [Payment Integration]

**Phase 2: Launch** (Weeks 9-12)
  - [Polish & QA]
  - [Marketing Materials]
  - [Launch Campaign]

**Phase 3: Iterate** (Months 4-6)
  - [Feature 4 based on feedback]
  - [Feature 5 based on feedback]
  - [Scale Infrastructure]

## Assumptions to Validate

1. **Assumption**: [e.g., "Users will pay $X/month"]
   **Validation Method**: [e.g., "Landing page with pricing, measure conversion"]

2. **Assumption**: [e.g., "Feature Y is most important"]
   **Validation Method**: [e.g., "User interviews, feature voting"]

## Appendix

**Resources**:
  • Competitor Analysis: [Link to doc]
  • User Research: [Link to interviews]
  • Market Research: [Link to reports]

**Change Log**:
  • v1.0 (2024-01-15): Initial product definition
\`\`\`

## 4. Zoho Catalog Integration

After human approval, create product in Zoho Catalog:

\`\`\`json
{
  "product_name": "[Product Name]",
  "product_description": "[From summary]",
  "product_category": "[Category]",
  "pricing_tiers": [
    {
      "name": "Free",
      "price": 0,
      "features": ["Feature 1", "Feature 2"]
    },
    {
      "name": "Pro",
      "price": 29,
      "billing_cycle": "monthly",
      "features": ["All Free features", "Feature 3", "Feature 4"]
    }
  ],
  "target_market": {
    "primary_persona": "[Role]",
    "company_size": "[Range]",
    "industry": "[Industries]"
  },
  "competitive_positioning": "[Positioning statement]",
  "tags": ["saas", "productivity", "ai"],
  "status": "in_development"
}
\`\`\`

Save to:
  • Local file: products/[product-name]-definition.md
  • Zoho Catalog: Create product record
  • Generate ID for tracking

Provide next steps:
  1. Review and approve product definition
  2. Run /product/summarize to generate marketing copy
  3. Run /product/pricing to validate pricing strategy
  4. Run /landing/create to build landing page
  `
})
```

## Example Usage

```bash
/product/define "AI Meeting Assistant"

# AI conducts discovery interview
# Questions about target market, features, pricing
# Human provides answers

# AI generates comprehensive product definition
# Includes market analysis, feature prioritization, pricing
# Saves to Zoho Catalog

# Next steps suggested:
#   /product/summarize "AI Meeting Assistant"
#   /landing/create "AI Meeting Assistant"
```

## Success Criteria

- ✓ Complete product definition document generated
- ✓ Market validation performed (TAM/SAM/SOM)
- ✓ Features prioritized using RICE framework
- ✓ Pricing strategy validated against competitors
- ✓ Risks and assumptions identified
- ✓ Product saved to Zoho Catalog
- ✓ Next steps clear (summarize, create landing page)

---
**Uses**: prompt-engineering-agent, ux-research-analyst, agent-router
**Output**: Product definition markdown file + Zoho Catalog entry
**Next Commands**: `/product/summarize`, `/product/pricing`, `/landing/create`
