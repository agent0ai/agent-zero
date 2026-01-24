---
description: Update existing Shopify product from updated solution folder (sync changes)
argument-hint: --folder <solution-path> --product-id <shopify-id> [--preview]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Bash, AskUserQuestion
---

Update Shopify product from solution folder: **${ARGUMENTS}**

## Shopify Product Update Automation

**Change Detection** - Re-parse solution folder, detect what changed
**Diff Preview** - Show current vs new data side-by-side
**Selective Update** - Choose which fields to update
**Campaign Sync** - Optionally regenerate campaign if product changed significantly

## Workflow

```
STEP 1: Parse Arguments
   ├─ --folder: Solution folder path
   ├─ --product-id: Existing Shopify product ID
   └─ --preview: Show diff without updating

STEP 2: Re-Extract Data
   ├─ Invoke Folder Parser Agent
   ├─ Extract fresh data from solution folder
   └─ Compare with current Shopify product

STEP 3: Detect Changes
   ├─ Compare title
   ├─ Compare description
   ├─ Compare pricing
   ├─ Compare tags
   └─ Generate diff report

STEP 4: Preview Changes (Approval Gate)
   ├─ Show current values
   ├─ Show new values
   ├─ Highlight differences
   └─ Request approval to update

STEP 5: Apply Updates
   ├─ Update product via Shopify API
   ├─ Log transaction
   └─ Optionally regenerate campaign
```

## Implementation

```javascript
const args = parseArguments(ARGUMENTS)
const folderPath = args['--folder']
const productId = args['--product-id']
const previewOnly = args['--preview'] !== undefined

if (!folderPath || !productId) {
  console.error('Missing required arguments')
  console.log('Usage: /shopify:update --folder test-outputs/scenario-1-saas/ --product-id 1234567890')
  return
}

// Step 1: Fetch current product from Shopify
const currentProduct = await fetchShopifyProduct(productId)

// Step 2: Re-extract data from solution folder
const newData = await extractProductData(folderPath)

// Step 3: Detect changes
const diff = detectChanges(currentProduct, newData)

if (diff.hasChanges === false) {
  console.log('✓ No changes detected. Product is up to date.')
  return
}

// Step 4: Display diff
displayDiff(diff)

if (previewOnly) {
  console.log('\n--preview mode: No changes applied.')
  return
}

// Step 5: Request approval
const approved = await requestUpdateApproval(diff)

if (approved) {
  await updateShopifyProduct(productId, diff.updates)
  console.log('✓ Product updated successfully')
}
```

## Change Detection Output

```markdown
═══════════════════════════════════════════════════
       SHOPIFY PRODUCT UPDATE - DIFF PREVIEW
═══════════════════════════════════════════════════

PRODUCT ID: 1234567890
PRODUCT URL: https://yourstore.com/products/ai-email-assistant
SOURCE FOLDER: test-outputs/scenario-1-saas/

───────────────────────────────────────────────────
DETECTED CHANGES (3)
───────────────────────────────────────────────────

1. TITLE
   Current:  "AI Email Assistant - Save 45 Hours Monthly"
   New:      "AI Email Assistant - Save 50 Hours Monthly"
   Change:   Updated benefit claim (45 → 50 hours)

2. DESCRIPTION
   Current:  "Save 93% of your email management time..."
   New:      "Save 96% of your email management time..."
   Change:   Updated time savings percentage (93% → 96%)

3. PRICING (Starter Tier)
   Current:  $299/month
   New:      $349/month
   Change:   Price increased by $50 (+16.7%)

───────────────────────────────────────────────────
NO CHANGES DETECTED IN:
───────────────────────────────────────────────────

  • Product type (still "SaaS")
  • Tags (no changes)
  • Feature list (same 7 features)
  • Target audience (unchanged)
  • Images (no new images)

───────────────────────────────────────────────────
APPROVAL REQUIRED
───────────────────────────────────────────────────

Apply these 3 updates to Shopify product?

  [Approve All] - Apply all changes
  [Selective]   - Choose which changes to apply
  [Cancel]      - Cancel update

───────────────────────────────────────────────────
CAMPAIGN SYNC RECOMMENDATION
───────────────────────────────────────────────────

Significant changes detected:
  • Pricing changed (may affect ad copy)
  • Benefit claim changed (may affect messaging)

Recommendation: Regenerate campaign with /campaign:create
  • Update ad creative with new pricing
  • Update landing pages with new benefit claim
  • Maintain campaign ID for continuity

═══════════════════════════════════════════════════
```

## Success Criteria

- [ ] Detects changes between solution folder and Shopify product
- [ ] Shows diff preview with current vs new values
- [ ] Allows selective updates (choose which fields)
- [ ] Updates product via Shopify API
- [ ] Recommends campaign regeneration if needed

---

**Uses**: Folder Parser Agent, Shopify API
**When to Use**: After updating solution folders (new metrics, features, pricing)
**Next**: Run /campaign:create if significant changes to product messaging
