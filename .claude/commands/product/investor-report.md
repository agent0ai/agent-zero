---
description: Determine if product is investor-worthy with competitive analysis, market sizing, and investment readiness scoring
argument-hint: --folder <path> [--batch <path1,path2,...>] [--target-investor-type vc|angel|bootstrap] [--include-pitch-deck] [--export pdf|markdown] [--skip-extraction]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash, WebSearch
---

# Product Investor Readiness Report

Generate comprehensive investor worthiness analysis with competitive intelligence, market opportunity sizing, and actionable recommendations.

## ROI: $75,000/year

- Avoid wasting time on non-fundable ideas: $30,000/year
- Better investor targeting (higher close rate): $25,000/year
- Competitive intelligence gathering: $15,000/year
- Pitch deck quality improvement: $5,000/year

## Overview

**Purpose**: Determine if your AI solution / product is ready for investor fundraising by analyzing:

1. **Market Opportunity** - TAM/SAM/SOM sizing
2. **Competitive Landscape** - Direct & indirect competitors
3. **Differentiation Score** - Unique value proposition strength
4. **Traction Potential** - Growth indicators and early signals
5. **Team/Execution** - Capability assessment
6. **Investment Worthiness Score** - 0-100 with breakdown

**Target Outcome**: Clear GO/NO-GO decision for investor outreach with:

- Investor worthiness score (0-100)
- Recommended investor types (VC/angel/bootstrap)
- 30-60-90 day action plan to increase score
- Auto-generated pitch deck (if score > 70)
- Competitive analysis PDF report

### Execution Time

- **Product data extraction** (Step 0): 2-4 minutes (file discovery + extraction + AI inference)
- **Competitive research**: 5-8 minutes (AI web search + analysis)
- **Market sizing**: 3-5 minutes (TAM/SAM/SOM calculation)
- **Score calculation**: 2-3 minutes (weighted scoring algorithm)
- **Report generation**: 4-6 minutes (PDF + pitch deck creation)
- **Total**: 17-27 minutes vs. 40-60 hours manually
- **Batch mode**: ~5-7 minutes per product (parallel extraction + sequential analysis)
*(Includes: data extraction, competitive research, market analysis, financial modeling, pitch deck creation)*

## When to Use This Command

Use `/product/investor-report` when you need to:

1. **Validate Fundability**: Check if idea is investor-worthy before spending months building
2. **Investor Targeting**: Determine which investor types to approach (VC, angel, bootstrap)
3. **Competitive Intelligence**: Understand market landscape and positioning
4. **Pitch Preparation**: Get data-driven insights for investor conversations
5. **Progress Tracking**: Measure improvement in investment readiness over time
6. **Portfolio Review**: Evaluate multiple products for investment priority

## Command Syntax

```bash
# Full investor report for AI solution folder
/product/investor-report --folder ./ai-solutions/cloud-cost-optimizer

# Target specific investor type
/product/investor-report --folder ./ai-solutions/workflow-automation --target-investor-type vc

# Include auto-generated pitch deck
/product/investor-report --folder ./my-product --include-pitch-deck --export pdf

# Quick validation (no pitch deck)
/product/investor-report --folder ./new-idea --export markdown

# Batch processing for portfolio analysis (NEW)
/product/investor-report --batch ./ai-solutions/optimizer,./ai-solutions/workflow,./ai-solutions/assistant

# Skip extraction if product-info.md already exists
/product/investor-report --folder ./my-product --skip-extraction
```

## Workflow

### Input Requirements

${ARGUMENTS}

**Folder Structure** (AI solution folder):

```
./ai-solutions/cloud-cost-optimizer/
├── product-info.md (REQUIRED - auto-generated if missing)
├── README.md (used for extraction)
├── solution.md (used for extraction)
├── pricing.md (used for extraction)
├── strategy/*.md (used for extraction)
├── WEEK-*-COMPLETION-REPORT.md (used for extraction)
└── package.json (used for tech stack extraction)
```

**NEW: Automatic Data Extraction**

If `product-info.md` doesn't exist, Step 0 will automatically extract product data from available files using the `/lib/extraction/` library. This provides intelligent data extraction with confidence scoring.

### Step 0: Product Data Extraction (2-4 min) **[NEW]**

**ONLY runs if `product-info.md` is missing or incomplete**

Uses the `/lib/extraction/` library to:

1. **Discover files** in the folder (README, completion reports, strategy files, etc.)
2. **Extract data** from multiple sources with priority waterfall:
   - Product name: completion reports (95%) > README H1 (85%) > package.json (70%) > folder name (60%)
   - Description: README paragraphs (85%) > completion report (85%) > solution.md (80%)
   - Problem: README problem section (85%) > solution.md (80%) > strategy files (75%)
   - Features: README features (85%) > solution.md (80%) > strategy files (75%)
   - Target Customer: strategy files (75%) > README (70%)
   - Pricing: pricing.md (80%) > README (75%)
   - Tech Stack: package.json (70%) > code analysis (60%)
   - Metrics: completion reports ONLY (95%) - never inferred
3. **Calculate confidence** using weighted scoring algorithm:
   - Overall confidence = weighted sum of field confidences
   - Threshold: ≥70% auto-proceed, 50-69% prompt for gaps, <50% block
4. **AI inference** for missing data (if enabled and confidence < 70%):
   - Infers description, problem, features, target customer (50% confidence)
   - Never infers: product name, metrics, exact pricing amounts
5. **Generate product-info.md** with confidence annotations:
   - High confidence sections (80%+): minimal review needed
   - Medium confidence (60-79%): verification recommended
   - Low confidence (<60%): likely needs revision
   - Missing data: marked with `<!-- CRITICAL -->` comments

**Extraction Process**:

```javascript
const { extractAndSave } = require('/lib/extraction');

const result = await extractAndSave(folderPath, {
  useAiInference: true,
  confidenceThreshold: 70,
  verbose: true
});

if (result.success && result.confidence.autoProceed) {
  // Proceed to investor analysis (Steps 1-8)
} else {
  // Show extraction report and prompt user to fill gaps
}
```

**Skip Extraction**: Use `--skip-extraction` flag if you have a manually created `product-info.md` and want to skip this step entirely.

**Batch Processing** **[NEW]**:

If `--batch` flag is provided with comma-separated folder paths, the system will:

1. Run Step 0 extraction for each folder in parallel
2. Generate product-info.md for each folder
3. Track overall progress (X/Y folders processed)
4. Continue with investor analysis for each folder sequentially
5. Generate portfolio summary report at the end

```javascript
const { batchExtract, generateBatchSummary } = require('/lib/extraction');

const folders = ['./folder1', './folder2', './folder3'];
const results = await batchExtract(folders, { useAiInference: true });

const summary = generateBatchSummary(results);
// summary.successful, summary.highConfidence, summary.averageConfidence
```

### Step 1: Parse Solution Folder (2 min)

- Read product-info.md (generated in Step 0 or pre-existing)
- Extract product name, description, target market
- Identify revenue model and pricing
- Capture any existing traction data
- List known competitors (if provided)

### Step 2: Market Opportunity Analysis (4 min)

- **TAM** (Total Addressable Market): Global market size
- **SAM** (Serviceable Available Market): Realistic target segment
- **SOM** (Serviceable Obtainable Market): 3-year capture estimate
- Market growth rate & trends
- Regulatory/macro tailwinds or headwinds

### Step 3: Competitive Intelligence Gathering (6 min)

- Web search for direct competitors (same solution)
- Identify indirect competitors (alternative approaches)
- Analyze competitor funding rounds (Crunchbase, PitchBook data)
- Compare features, pricing, market share
- Identify white space opportunities

### Step 4: Differentiation Scoring (3 min)

Evaluate uniqueness on 5 dimensions:

1. **Technology Innovation** (0-20 points): Novel approach or commodity?
2. **Market Positioning** (0-20 points): Blue ocean or red ocean?
3. **Defensibility** (0-20 points): Moats (network effects, data, IP)
4. **Go-to-Market** (0-20 points): Unique distribution advantage?
5. **Timing** (0-20 points): Market ready or too early/late?

### Step 5: Traction Potential Assessment (2 min)

- Revenue indicators (if launched)
- User growth trajectory
- Market validation signals
- Partnership/pilot potential
- Viral coefficient estimate

### Step 6: Team/Execution Capability (2 min)

- Founder domain expertise
- Technical capability assessment
- Prior startup experience
- Network strength (advisors, partners)

### Step 7: Investment Worthiness Score Calculation (1 min)

Weighted scoring:

- **Market Opportunity**: 25 points
- **Competition & Differentiation**: 20 points
- **Traction Potential**: 20 points
- **Team/Execution**: 15 points
- **Business Model Viability**: 20 points

**Score Interpretation**:

- **90-100**: Exceptional - ready for top-tier VC
- **80-89**: Strong - ready for VC/angel fundraise
- **70-79**: Good - refine positioning, then fundraise
- **60-69**: Promising - build traction first (3-6 months)
- **50-59**: Weak - significant pivots needed
- **<50**: Not fundable - consider bootstrap or pivot

### Step 8: Generate Recommendations (3 min)

- **GO/NO-GO** decision for investor outreach
- **Recommended Investor Types**: VC (stage?), angel, strategic, or bootstrap
- **30-60-90 Day Action Plan** to increase score
- **Pitch Deck Auto-Generation** (if score > 70)
- **Competitive Positioning Statement**

### Output Deliverables

1. **Investor Worthiness Report** (PDF/Markdown)
   - Executive summary (1 page)
   - Market opportunity analysis (TAM/SAM/SOM)
   - Competitive landscape matrix
   - Differentiation scorecard
   - Investment recommendation

2. **Competitive Analysis Dashboard**
   - Competitor feature comparison table
   - Funding history & valuations
   - Market share estimates
   - Pricing comparison

3. **Pitch Deck** (if score > 70) - Auto-generated PowerPoint/PDF
   - Problem statement
   - Solution overview
   - Market opportunity (TAM/SAM/SOM)
   - Competitive positioning
   - Business model
   - Traction (or traction plan)
   - Team
   - Ask

4. **Action Plan** (30-60-90 days)
   - Quick wins to increase score
   - Traction milestones
   - Competitive positioning refinements
   - Pitch preparation checklist

## Success Criteria

✅ Investor worthiness score calculated (0-100)
✅ Market opportunity sized (TAM/SAM/SOM)
✅ Competitive landscape mapped (5+ competitors)
✅ Clear GO/NO-GO recommendation
✅ Action plan to improve score (if < 80)
✅ Pitch deck generated (if score > 70)
✅ Report exported (PDF/Markdown)

## Example Output

```
═══════════════════════════════════════════════════════
 INVESTOR READINESS REPORT: Cloud Cost Optimizer
═══════════════════════════════════════════════════════

📊 INVESTMENT WORTHINESS SCORE: 78/100

✅ RECOMMENDATION: PROCEED TO FUNDRAISE
   Target: Seed-stage VCs + technical angels
   Estimated raise potential: $1.5M - $3M

───────────────────────────────────────────────────────
MARKET OPPORTUNITY
───────────────────────────────────────────────────────
• TAM: $82B (cloud infrastructure management)
• SAM: $12B (cost optimization segment)
• SOM: $180M (realistic 3-year capture)
• Growth Rate: 28% CAGR (2024-2029)
• Score: 23/25 ⭐ STRONG OPPORTUNITY

───────────────────────────────────────────────────────
COMPETITIVE LANDSCAPE
───────────────────────────────────────────────────────
Direct Competitors Found: 7
• CloudHealth (VMware) - $600M ARR
• Spot.io (NetApp) - $150M+ ARR
• Cast AI - $20M ARR (Series A: $10M)
• ProsperOps - Bootstrap, $5M ARR
• Yotascale - Series B: $45M raised
• Vantage - Series A: $21M raised
• Cloudability (Apptio/IBM) - Enterprise

White Space: AI-powered predictive optimization
Score: 16/20 ⚠️  CROWDED BUT DIFFERENTIATED

───────────────────────────────────────────────────────
DIFFERENTIATION ANALYSIS
───────────────────────────────────────────────────────
• Technology: AI predictive models vs. rule-based (18/20)
• Defensibility: Data moat from optimization patterns (14/20)
• GTM: Developer-first vs. enterprise sales (16/20)
• Timing: Cloud costs hitting C-suite pain threshold (19/20)

Total Differentiation Score: 67/80 (84%)

───────────────────────────────────────────────────────
TRACTION POTENTIAL
───────────────────────────────────────────────────────
• Viral Coefficient: 1.4x (strong word-of-mouth)
• Sales Cycle: 2-4 weeks (fast for B2B SaaS)
• Expansion Revenue: 180% net dollar retention potential
• Partnership Potential: AWS/GCP marketplace listing

Score: 18/20 ⭐ HIGH TRACTION POTENTIAL

───────────────────────────────────────────────────────
30-60-90 DAY ACTION PLAN
───────────────────────────────────────────────────────

NEXT 30 DAYS (Quick Wins to hit 85+ score):
✓ Launch beta with 5 early adopter logos
✓ Get 1 case study with quantified ROI
✓ Refine pitch deck with traction data
✓ Identify 10 target VCs (cloud infrastructure focus)

60-DAY MILESTONES:
□ $10K MRR or 50 active users
□ 2-3 investor conversations (warm intros)
□ Competitive positioning doc finalized
□ Financial model with unit economics

90-DAY TARGETS:
□ $25K MRR or 150 users
□ Lead investor term sheet
□ Advisory board (2-3 domain experts)
□ Series Seed deck refined

───────────────────────────────────────────────────────
📄 OUTPUTS GENERATED
───────────────────────────────────────────────────────
✅ investor-report.pdf (18 pages)
✅ competitive-analysis.pdf (12 pages)
✅ pitch-deck.pptx (15 slides)
✅ action-plan-30-60-90.md

───────────────────────────────────────────────────────
💡 NEXT STEPS
───────────────────────────────────────────────────────
1. Review pitch deck: ./investor-report/pitch-deck.pptx
2. Execute 30-day plan to increase score to 85+
3. Schedule 10 investor conversations
4. Use /pitch/rehearse to practice delivery
5. Track progress with weekly /product/investor-report runs
```

## Integration Points

**Triggers Automatically**:

- `/pitch/generate` - If score > 70, auto-generate pitch deck
- `/startup/competitive` - Detailed competitive analysis
- `/startup/gtm` - Go-to-market strategy if score > 75

**Can Trigger Manually**:

- `/social/generate` - Create launch announcements
- `/campaign/create` - Marketing campaign for beta launch
- `/product/pricing` - Optimize pricing strategy

## Technical Implementation

**AI Agent Stack**:

1. **Market Research Agent** - TAM/SAM/SOM sizing (WebSearch + analysis)
2. **Competitive Intelligence Agent** - Competitor discovery & analysis
3. **Scoring Algorithm** - Weighted calculation based on 5 dimensions
4. **Pitch Deck Generator** - Auto-create investor slides
5. **Report Writer** - PDF generation with charts

**Data Sources**:

- Web search for competitor intelligence
- Crunchbase/PitchBook (if available via API)
- Industry reports & market research
- Product folder analysis
- Traction data (if provided)

## Notes

**Update Shopify Credentials**:
For real Shopify integration, update Vault credentials:

```bash
source vault/lib/mcp-vault-client.sh && store_mcp_credential shopify-admin-api \
  shop_domain="your-store.myshopify.com" \
  access_token="shpat_your_actual_token" \
  api_version="2024-01"
```

**Scoring Algorithm**:

- Scores are comparative to industry benchmarks
- Market size matters: smaller TAM = lower score ceiling
- Competition is weighted: blue ocean > red ocean
- Traction is king: revenue trumps potential

**Limitations**:

- Competitor funding data may be incomplete (private companies)
- Market sizing is estimate-based (not exact science)
- Score is directional, not absolute truth
- Human judgment still required for final decision
