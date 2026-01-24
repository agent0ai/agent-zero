---
description: Publish existing Shopify product + launch full marketing campaign
argument-hint: --product-id <shopify-id> [--campaign-budget <amount>] [--duration <days>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, AskUserQuestion
---

Publish Shopify product with campaign: **${ARGUMENTS}**

## Shopify Product Publishing + Campaign Launch

**Product Activation** - Verify Shopify product and prepare for launch
**Campaign Generation** - Generate 30+ files in 15-20 minutes
**Multi-Channel Deployment** - Google Shopping, Facebook, Instagram, LinkedIn, Twitter
**ROI Tracking** - Set up conversion tracking and analytics

## Workflow

```
STEP 1: Fetch Product from Shopify
   ├─ Validate product ID exists
   ├─ Retrieve product data (title, price, URL)
   └─ Confirm product is active

STEP 2: Extract Product Type
   ├─ Analyze product data
   ├─ Determine type (SaaS, E-commerce, Service)
   └─ Set campaign parameters

STEP 3: Generate Campaign
   ├─ Invoke /campaign:create
   ├─ Generate 18+ ad variants
   ├─ Create landing pages
   ├─ Build Google Shopping feed
   └─ Generate 90-day GTM plan

STEP 4: Campaign Review (Approval Gate)
   ├─ Preview campaign deliverables
   ├─ Show projected results
   ├─ Request approval to launch
   └─ If approved → Deploy

STEP 5: Deployment Checklist
   ├─ Set up conversion tracking
   ├─ Upload creatives to ad platforms
   └─ Launch campaigns
```

## Implementation

```javascript
const args = parseArguments(ARGUMENTS)
const productId = args['--product-id']
const budget = args['--campaign-budget'] || 5000
const duration = args['--duration'] || 90

if (!productId) {
  console.error('Missing required: --product-id')
  console.log('Usage: /shopify:publish --product-id 1234567890 --campaign-budget 5000 --duration 90')
  return
}

// Step 1: Fetch product from Shopify
const product = await fetchShopifyProduct(productId)

// Step 2: Determine product type
const productType = detectProductType(product)

// Step 3: Generate campaign
const campaign = await generateCampaign({
  productName: product.title,
  productType,
  productUrl: product.url,
  budget,
  duration
})

// Step 4: Request approval
const approved = await requestCampaignApproval(campaign)

if (approved) {
  // Step 5: Provide deployment checklist
  displayDeploymentChecklist(campaign)
}
```

## Success Criteria

- [ ] Fetches product from Shopify successfully
- [ ] Generates complete campaign (30+ files)
- [ ] Includes approval gate
- [ ] Provides deployment checklist

---

**Uses**: /campaign:create, Shopify API
**Next**: Deploy ads to platforms, monitor with /shopify:monitor
