---
description: Extract product definition from AI solution folder (completion reports, campaign files, templates)
argument-hint: <solution-folder-path> [--save-to <output-path>]
model: claude-sonnet-4-5-20250929
allowed-tools: Read, Glob, Write, Bash, AskUserQuestion
---

Extract product data from solution folder: **${ARGUMENTS}**

## Product Extraction from AI Solution Folders

**Intelligent Data Extraction** - Parse completion reports, campaign files, and templates
**Metrics Extraction** - Quality scores, ROI, time savings, cost savings
**Structured Output** - JSON ready for `/product:define --from-solution`
**Quality Validation** - Verify extracted data completeness and accuracy

## Extraction Process

### Step 1: Validate Solution Folder

Parse folder path from arguments:

```javascript
const args = parseArguments(ARGUMENTS)
const folderPath = args.positional[0]
const savePath = args['--save-to'] || `${folderPath}/extracted-product-definition.json`
```

Validate folder exists and contains expected structure:

- ✓ Completion reports (WEEK-*-COMPLETION-REPORT.md)
- ✓ README.md or campaign README
- ✓ Strategy files (strategy/*.md) OR templates/*.md
- ✓ Campaign output files (creative/*.md, gtm-plan/*.md)

If folder doesn't exist or is missing critical files, show error and suggest valid paths.

### Step 2: Extract Metrics from Completion Reports

**Priority 1: Completion Reports** (highest quality data source)

Search for completion reports:

```bash
find ${folderPath} -type f -name "*WEEK*COMPLETION*REPORT*.md" -o -name "*completion*report*.md"
```

For each completion report found, extract:

**Quality Metrics**:

- Quality Score: Look for patterns like "Quality: XX/100", "Score: XX%", "Quality Assessment: XX.X/100"
- Extract numeric value (e.g., "93.3/100" → 93.3)

**Time Savings**:

- Manual time: Look for "Manual: XX hours", "Without AI: XX-XX hours"
- AI time: Look for "AI-powered: XX minutes", "With AI: XX-XX minutes"
- Percentage: Look for "XX% faster", "XX% time reduction"
- Format as: "31-45 hours manual → 15-20 min AI (93-96% reduction)"

**Cost Savings**:

- Look for dollar amounts: "$X,XXX saved", "Cost reduction: $X,XXX-X,XXX"
- Extract range if present (e.g., "$4,300-6,200")
- Format as: "$4,300-6,200 per campaign"

**ROI Metrics**:

- Look for "ROAS: X.Xx", "ROI: XX:1", "Return: Xx multiplier"
- Extract numeric value (e.g., "3.5x ROAS" → "3.5x ROAS")

If multiple completion reports exist, use the most recent (highest WEEK number).

### Step 3: Extract Product Overview from README

**Priority 2: README.md** (product name, description, overview)

Find README:

```bash
# Check campaign folder first
find ${folderPath} -type f -name "README.md" -o -name "readme.md" | head -1
```

Extract:

**Product Name**:

- Look for title (# heading) or "Product:" or "Campaign:" labels
- Clean formatting (remove markdown, extra spaces)
- Example: "# AI Email Assistant Campaign" → "AI Email Assistant"

**Product Description**:

- Extract first 2-3 paragraphs after title
- Look for "Overview", "What is", "About" sections
- Limit to 300-500 characters
- Remove markdown formatting

**Key Features**:

- Look for "Features", "Key Features", "Capabilities", "What it does" sections
- Extract bullet points or numbered lists
- Limit to top 5-7 features
- Format as array: ["Feature 1", "Feature 2", ...]

### Step 4: Extract Target Audience from Strategy Files

**Priority 3: Strategy Files** (target audience, personas, positioning)

Search for strategy files:

```bash
find ${folderPath} -type f -path "*/strategy/*.md"
```

Extract from these files:

**Target Audience** (from `01-target-audience.md` or similar):

- Look for "Persona", "Target Market", "Ideal Customer" sections
- Extract:
  - Primary Persona (role, company size, industry)
  - Pain Points (top 3-5 problems they face)
  - Goals (what they want to achieve)
- Format as structured object

**Value Proposition** (from `02-value-proposition.md` or similar):

- Look for "Unique Value", "Key Benefits", "Why Choose Us" sections
- Extract main value statement (1-2 sentences)
- Extract top 3 benefits with metrics if available

**Positioning** (from `03-positioning.md` or similar):

- Look for positioning statement
- Competitive advantages
- Differentiation points

If strategy files don't exist, fall back to template analysis (next step).

### Step 5: Extract Capabilities from Templates

**Priority 4: Templates** (for agent-based products)

Search for template/agent definition files:

```bash
find ${folderPath} -type f -path "*/templates/*.md" -o -path "*/*agent*.md"
```

Extract:

**Agent Capabilities**:

- Look for "CAPABILITIES", "FEATURES", "WHAT IT DOES" sections
- Extract bullet points
- Map to product features

**Technical Specifications**:

- Input/Output formats
- Integration points
- Performance characteristics

**Use Cases**:

- Look for "EXAMPLES", "USE CASES", "SCENARIOS" sections
- Extract specific use case descriptions

### Step 6: Identify Product Type

Determine product category based on extracted data:

**SaaS Product** (if):

- Recurring pricing model mentioned
- Web/cloud-based delivery
- Subscription language ("monthly", "annual", "plans")
- Keywords: "dashboard", "platform", "tool", "software"

**E-commerce Product** (if):

- One-time purchase
- Physical or digital goods
- Shopping/cart language
- Keywords: "buy", "shop", "order", "product catalog"

**B2B Service** (if):

- Consultation/coaching mentioned
- Professional services
- Custom/enterprise solutions
- Keywords: "consulting", "implementation", "strategy", "done-for-you"

**Digital Product** (if):

- Templates, courses, guides
- One-time download
- Educational content
- Keywords: "template", "guide", "course", "framework"

### Step 7: Generate Pricing Recommendations

Based on extracted ROI and value metrics, suggest pricing:

**Calculation Logic**:

1. If cost savings extracted (e.g., "$4,300-6,200"):
   - Suggest pricing at 10-20% of cost savings
   - Example: $4,300 savings → Price at $430-860/month

2. If time savings extracted (e.g., "45 hours saved"):
   - Assume $100/hour value
   - 45 hours × $100 = $4,500 value
   - Price at 10-20% → $450-900/month

3. If ROI extracted (e.g., "3.5x ROAS"):
   - Suggest pricing that maintains 2x+ ROI for customer
   - Example: If customer spends $1000, gets $3,500 return
   - Product can be priced up to $1,750 while maintaining 2x ROI

**Pricing Tiers** (recommend 3-tier structure):

- **Starter**: 60% of calculated price (entry point)
- **Pro**: 100% of calculated price (primary offering)
- **Enterprise**: 200-300% of calculated price (custom features)

### Step 8: Synthesize into Product Definition JSON

Generate structured JSON output:

```json
{
  "metadata": {
    "sourceFolder": "/path/to/solution/folder",
    "extractedAt": "2024-01-15T10:30:00Z",
    "extractionConfidence": {
      "metrics": "high|medium|low",
      "description": "high|medium|low",
      "features": "high|medium|low",
      "audience": "high|medium|low",
      "overall": "high|medium|low"
    },
    "dataSources": {
      "completionReports": ["WEEK-5-COMPLETION-REPORT.md"],
      "readmeFiles": ["campaigns/ai-email-assistant/README.md"],
      "strategyFiles": ["strategy/01-target-audience.md", "strategy/02-value-proposition.md"],
      "templateFiles": []
    }
  },

  "product": {
    "name": "AI Email Assistant",
    "type": "saas",
    "category": "Productivity / AI Tools",

    "description": {
      "short": "One-sentence value proposition extracted from README or strategy files",
      "long": "2-3 paragraph description extracted from README",
      "tagline": "Catchy 5-8 word tagline summarizing the value"
    },

    "metrics": {
      "qualityScore": 93.3,
      "qualityScoreSource": "WEEK-5-COMPLETION-REPORT.md line 127",
      "timeSavings": "31-45 hours manual → 15-20 min AI (93-96% reduction)",
      "timeSavingsSource": "WEEK-5-COMPLETION-REPORT.md line 134-138",
      "costSavings": "$4,300-6,200 per campaign",
      "costSavingsSource": "WEEK-5-COMPLETION-REPORT.md line 145",
      "roi": "3.5x ROAS for SaaS campaigns",
      "roiSource": "WEEK-5-COMPLETION-REPORT.md line 158"
    },

    "features": [
      {
        "name": "Feature 1 extracted from README or strategy",
        "description": "What this feature does",
        "source": "README.md line 45"
      },
      {
        "name": "Feature 2",
        "description": "What this feature does",
        "source": "strategy/02-value-proposition.md line 23"
      }
    ],

    "targetAudience": {
      "primaryPersona": {
        "role": "Extracted from strategy/01-target-audience.md",
        "companySize": "Extracted from strategy files",
        "industry": "Extracted from strategy files",
        "painPoints": [
          "Pain point 1 from strategy files",
          "Pain point 2",
          "Pain point 3"
        ],
        "goals": [
          "Goal 1 from strategy files",
          "Goal 2"
        ]
      },
      "secondaryPersona": {
        "role": "If multiple personas mentioned",
        "companySize": "...",
        "industry": "..."
      }
    },

    "pricingRecommendations": {
      "model": "subscription|one-time|usage-based",
      "calculationBasis": "Based on cost savings of $4,300-6,200 per campaign",
      "recommendedPricing": {
        "starter": {
          "price": 299,
          "billingCycle": "monthly",
          "features": ["Core features", "Limited usage"],
          "rationale": "Entry point at 60% of calculated value ($4,300 × 10% × 0.6)"
        },
        "pro": {
          "price": 499,
          "billingCycle": "monthly",
          "features": ["All core features", "Unlimited usage", "Priority support"],
          "rationale": "Primary offering at 10% of cost savings value"
        },
        "enterprise": {
          "price": 1299,
          "billingCycle": "monthly",
          "features": ["Everything in Pro", "Custom integrations", "Dedicated support", "SLA"],
          "rationale": "Premium tier at 25% of cost savings value"
        }
      },
      "alternativePricing": {
        "oneTime": {
          "price": 2999,
          "rationale": "6x monthly Pro price for lifetime access"
        },
        "usageBased": {
          "basePrice": 99,
          "perUnitPrice": 49,
          "unit": "campaign",
          "rationale": "Base fee + per-campaign pricing based on value delivered"
        }
      }
    },

    "competitivePositioning": {
      "category": "Determined from product type and features",
      "positioningStatement": "For [target] who [need], [product] is a [category] that [benefit]. Unlike [competitors], we [differentiator].",
      "uniqueAdvantages": [
        "Extracted from strategy files or inferred from metrics",
        "E.g., '93% time savings vs industry average of 60%'"
      ]
    }
  },

  "confidence": {
    "overall": "high|medium|low",
    "recommendations": [
      "Review pricing calculations - based on estimated hourly value of $100",
      "Validate target audience - extracted from strategy files",
      "Add product images - none found in solution folder"
    ],
    "missingData": [
      "Product images/screenshots",
      "Competitor analysis",
      "User testimonials"
    ]
  },

  "nextSteps": [
    "Review extracted data for accuracy",
    "Run /product:define --from-solution to refine with AI assistance",
    "Manually add product images to creative/ folder",
    "Run /campaign:create to generate marketing campaign"
  ]
}
```

### Step 9: Save JSON Output

Write JSON to file:

```javascript
const outputPath = args['--save-to'] || `${folderPath}/extracted-product-definition.json`
await Write(outputPath, JSON.stringify(productDefinition, null, 2))
```

Display summary to user:

```
✓ Product Extraction Complete

📦 Product: AI Email Assistant
📊 Confidence: High (4/5 data sources found)

Extracted Metrics:
  • Quality Score: 93.3/100 ✓
  • Time Savings: 93-96% (31-45 hours → 15-20 min) ✓
  • Cost Savings: $4,300-6,200 per campaign ✓
  • ROI: 3.5x ROAS ✓

Extracted Features: 7 features ✓
Target Audience: 1 primary persona ✓
Pricing Recommendations: 3 tiers (Starter $299, Pro $499, Enterprise $1,299) ✓

Data Sources Used:
  ✓ WEEK-5-COMPLETION-REPORT.md (metrics)
  ✓ campaigns/ai-email-assistant/README.md (overview)
  ✓ strategy/01-target-audience.md (persona)
  ✓ strategy/02-value-proposition.md (benefits)

💾 Saved to: test-outputs/scenario-1-saas/extracted-product-definition.json

Next Steps:
  1. Review extracted data for accuracy
  2. Run: /product:define --from-solution test-outputs/scenario-1-saas/
  3. Manually add product images to creative/ folder (if needed)
  4. Run: /campaign:create --product-type saas --budget 5000 --duration 30
```

### Step 10: Offer to Run /product:define

After successful extraction, ask user:

```
Would you like me to run /product:define now with the extracted data?

This will:
  • Load the extracted product definition
  • Ask clarifying questions to refine the data
  • Generate a comprehensive product definition document
  • Save to products/[product-name]-definition.md

[Yes - Run /product:define now]
[No - I'll review the JSON first]
```

If user selects "Yes", invoke:

```bash
/product:define --from-solution ${folderPath}
```

## Extraction Algorithms

### Algorithm 1: Quality Score Extraction

```javascript
function extractQualityScore(completionReportText) {
  // Patterns to match
  const patterns = [
    /quality[:\s]+(\d+(?:\.\d+)?)\s*\/\s*100/i,
    /score[:\s]+(\d+(?:\.\d+)?)\s*%/i,
    /(\d+(?:\.\d+)?)\s*\/\s*100\s+quality/i,
    /quality assessment[:\s]+(\d+(?:\.\d+)?)/i
  ]

  for (const pattern of patterns) {
    const match = completionReportText.match(pattern)
    if (match) {
      return {
        score: parseFloat(match[1]),
        source: `Line ${getLineNumber(match.index)}`
      }
    }
  }

  return { score: null, source: "Not found" }
}
```

### Algorithm 2: Time Savings Extraction

```javascript
function extractTimeSavings(completionReportText) {
  // Look for time comparisons
  const manualTimePattern = /(?:manual|without AI|traditional)[:\s]+(\d+(?:-\d+)?)\s*hours?/i
  const aiTimePattern = /(?:AI|automated|with AI)[:\s]+(\d+(?:-\d+)?)\s*(?:min(?:ute)?s?|hours?)/i
  const percentPattern = /(\d+(?:\.\d+)?)\s*%\s*(?:faster|time reduction|time saved)/i

  const manualMatch = completionReportText.match(manualTimePattern)
  const aiMatch = completionReportText.match(aiTimePattern)
  const percentMatch = completionReportText.match(percentPattern)

  let result = ""

  if (manualMatch && aiMatch) {
    result = `${manualMatch[1]} hours manual → ${aiMatch[1]} AI`
  }

  if (percentMatch) {
    result += ` (${percentMatch[1]}% reduction)`
  }

  return result || "Not found"
}
```

### Algorithm 3: Product Type Detection

```javascript
function detectProductType(folderContents) {
  const allText = folderContents.join(' ').toLowerCase()

  // Scoring system
  const scores = {
    saas: 0,
    ecommerce: 0,
    service: 0,
    digital: 0
  }

  // SaaS indicators
  if (allText.includes('subscription') || allText.includes('monthly') || allText.includes('saas')) {
    scores.saas += 3
  }
  if (allText.includes('dashboard') || allText.includes('platform') || allText.includes('app')) {
    scores.saas += 2
  }

  // E-commerce indicators
  if (allText.includes('shopping') || allText.includes('cart') || allText.includes('checkout')) {
    scores.ecommerce += 3
  }
  if (allText.includes('product catalog') || allText.includes('inventory')) {
    scores.ecommerce += 2
  }

  // Service indicators
  if (allText.includes('consulting') || allText.includes('implementation') || allText.includes('done-for-you')) {
    scores.service += 3
  }
  if (allText.includes('strategy') || allText.includes('coaching')) {
    scores.service += 2
  }

  // Digital product indicators
  if (allText.includes('template') || allText.includes('course') || allText.includes('guide')) {
    scores.digital += 3
  }
  if (allText.includes('download') || allText.includes('ebook')) {
    scores.digital += 2
  }

  // Return highest scoring type
  return Object.entries(scores).reduce((a, b) => a[1] > b[1] ? a : b)[0]
}
```

## Confidence Calculation

Assign confidence levels based on data source completeness:

**High Confidence** (3+ data sources with complete data):

- ✓ Completion report found with all metrics
- ✓ README with description and features
- ✓ Strategy files with target audience and value prop
- ✓ All pricing inputs available

**Medium Confidence** (2-3 data sources, some gaps):

- ✓ Completion report with partial metrics
- ✓ README found but incomplete
- ✗ Strategy files missing (fallback to templates)
- ⚠ Pricing calculated from incomplete ROI data

**Low Confidence** (1 data source, major gaps):

- ⚠ Completion report missing or very incomplete
- ⚠ No README found
- ✗ No strategy files
- ✗ Pricing recommendations not possible

If confidence is LOW, warn user:

```
⚠️ Low Confidence Extraction

Only found: README.md
Missing: Completion reports, strategy files, templates

Recommendation: This solution folder may not be complete.
  1. Check if this is a finished campaign/solution
  2. Look for completion reports in parent directories
  3. Manually provide missing data via /product:define

Proceed with limited data? [Yes/No]
```

## Error Handling

### Error 1: Folder Not Found

```
❌ Error: Solution folder not found

Path: test-outputs/scenario-4-invalid/

Did you mean:
  • test-outputs/scenario-1-saas/ ✓
  • test-outputs/scenario-2-ecommerce/ ✓
  • test-outputs/scenario-3-b2b-services/ ✓

Usage: /product:extract-from-solution <folder-path>
```

### Error 2: No Extractable Data

```
⚠️ Warning: No completion reports or README found

Folder: custom-solution/
Found files: 3 markdown files, 2 images

This folder doesn't appear to be an AI solution folder.

Expected structure:
  ✓ WEEK-*-COMPLETION-REPORT.md
  ✓ README.md or campaign/README.md
  ✓ strategy/*.md OR templates/*.md

Would you like to:
  1. Search parent directories for completion reports
  2. Specify a different folder
  3. Skip extraction and use /product:define directly

[Option 1] [Option 2] [Option 3]
```

### Error 3: Partial Data Extraction

```
⚠️ Partial extraction completed

Found data:
  ✓ Product name: "AI Email Assistant"
  ✓ Description: Extracted from README
  ✗ Metrics: No completion report found
  ✗ Target audience: No strategy files found
  ⚠ Pricing: Calculated from generic assumptions

Confidence: Low (2/5 data sources)

Recommendation: Manually provide missing data in /product:define

Proceed with partial data? [Yes/No]
```

## Example Usage

### Example 1: Extract from SaaS Campaign

```bash
/product:extract-from-solution test-outputs/scenario-1-saas/campaigns/ai-email-assistant/

# Output:
✓ Product Extraction Complete
📦 Product: AI Email Assistant
📊 Confidence: High (4/5 data sources found)
💾 Saved to: test-outputs/scenario-1-saas/campaigns/ai-email-assistant/extracted-product-definition.json

Next: /product:define --from-solution test-outputs/scenario-1-saas/campaigns/ai-email-assistant/
```

### Example 2: Extract with Custom Save Path

```bash
/product:extract-from-solution test-outputs/scenario-2-ecommerce/ --save-to products/ecommerce-platform-definition.json

# Output:
✓ Product Extraction Complete
💾 Saved to: products/ecommerce-platform-definition.json
```

### Example 3: Extract and Auto-Define

```bash
/product:extract-from-solution test-outputs/scenario-3-b2b-services/

# Asks: "Would you like me to run /product:define now?"
# User selects: Yes

# Automatically runs:
/product:define --from-solution test-outputs/scenario-3-b2b-services/

# AI conducts discovery interview with pre-filled extracted data
# Human refines and approves
# Comprehensive product definition generated
```

## Success Criteria

- ✓ Successfully extracts product data from 3+ different solution folder types
- ✓ Achieves 90%+ accuracy on metric extraction (quality, time, cost, ROI)
- ✓ Generates valid JSON that loads into /product:define
- ✓ Handles missing data gracefully with clear error messages
- ✓ Provides confidence scores for transparency
- ✓ Saves 80%+ of manual data entry time (30 min → 6 min)

---

**Uses**: Read, Glob, Write (for JSON output), Bash (for file finding)
**Output**: Structured JSON product definition
**Next Commands**: `/product:define --from-solution`, `/campaign:create`
