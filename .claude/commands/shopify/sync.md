---
description: Sync AI solution folder(s) to Shopify products with approval workflow (single or batch)
argument-hint: --folder <path> [--batch <parent-path>] [--review] [--auto-apply]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Write, Bash, AskUserQuestion
---

Sync AI solution folders to Shopify: **${ARGUMENTS}**

## Shopify Product Sync Automation

**Intelligent Product Sync** - Extract data from AI solution folders and create Shopify products
**Two-Gate Approval** - Human review for product listing and campaign strategy
**Batch Processing** - Sync 10+ products in one command
**Time Savings** - 80% reduction (30 min manual → 6 min automated per product)

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SHOPIFY SYNC WORKFLOW                     │
└─────────────────────────────────────────────────────────────┘

STEP 1: Parse Arguments
   ├─ --folder <path>: Single product sync
   ├─ --batch <parent-path>: Bulk sync (all subfolders)
   ├─ --review: Require approval (default)
   └─ --auto-apply: Skip approval (USE WITH CAUTION)

STEP 2: Folder Discovery
   ├─ Single: Validate folder exists
   └─ Batch: Find all solution folders under parent path

STEP 3: For Each Folder →
   ├─ Invoke Folder Parser Agent
   │  ├─ Extract metrics (quality, ROI, time/cost savings)
   │  ├─ Extract product data (name, description, features)
   │  ├─ Extract target audience
   │  ├─ Calculate pricing
   │  └─ Return JSON + confidence score
   │
   ├─ Invoke Shopify Product Agent
   │  ├─ Enrich for Shopify (SEO, HTML, tags, variants)
   │  ├─ Gate 1: Product listing review (approval required)
   │  ├─ Create product via Shopify API
   │  ├─ Gate 2: Campaign strategy review (approval required)
   │  └─ Launch campaign (if approved)
   │
   └─ Log Result
      ├─ Success: Product ID, URL, campaign status
      └─ Failure: Error details, suggested fixes

STEP 4: Summary Report
   ├─ Total products processed
   ├─ Success count
   ├─ Failure count
   ├─ Time saved
   └─ Next steps
```

## Argument Parsing

Parse command line arguments:

```javascript
const args = parseArguments(ARGUMENTS)

// Single product mode
const folderPath = args['--folder']

// Batch mode
const batchPath = args['--batch']

// Approval mode
const requireApproval = !args['--auto-apply'] // Default: true (require approval)
const reviewMode = args['--review'] !== undefined // Explicit review flag

// Validation
if (!folderPath && !batchPath) {
  showError('Missing required argument: --folder or --batch')
  showUsage()
  return
}

if (folderPath && batchPath) {
  showError('Cannot use both --folder and --batch. Choose one.')
  showUsage()
  return
}
```

## Usage Examples

```bash
# Single product sync (with approval)
/shopify:sync --folder test-outputs/scenario-1-saas/

# Batch sync (all products under parent folder)
/shopify:sync --batch test-outputs/

# Explicit review mode (same as default)
/shopify:sync --folder test-outputs/scenario-1-saas/ --review

# Auto-apply mode (skip approvals - USE WITH CAUTION)
/shopify:sync --folder test-outputs/scenario-1-saas/ --auto-apply
```

## Step 1: Folder Discovery

### Single Product Mode

```javascript
if (folderPath) {
  console.log(`📂 Single product sync mode`)
  console.log(`   Folder: ${folderPath}`)

  // Validate folder exists
  const exists = await Bash({
    command: `test -d "${folderPath}" && echo "exists" || echo "not_found"`,
    description: 'Check if folder exists'
  })

  if (exists.trim() === 'not_found') {
    console.error(`❌ Folder not found: ${folderPath}`)

    // Suggest alternatives
    const suggestions = await Bash({
      command: `find test-outputs/ -type d -maxdepth 2 | head -10`,
      description: 'Find available solution folders'
    })

    console.log('\nDid you mean one of these?')
    console.log(suggestions)
    return
  }

  // Process single folder
  const result = await syncFolder(folderPath, requireApproval)
  displayResults([result])
}
```

### Batch Mode

```javascript
if (batchPath) {
  console.log(`📂 Batch sync mode`)
  console.log(`   Parent folder: ${batchPath}`)

  // Find all solution folders (folders containing completion reports or READMEs)
  const findCommand = `
    find "${batchPath}" -type d -name "scenario-*" -o -name "campaigns" |
    while read dir; do
      if [ -f "$dir/README.md" ] || ls "$dir"/*COMPLETION*.md 2>/dev/null | grep -q .; then
        echo "$dir"
      fi
    done
  `

  const folders = await Bash({
    command: findCommand,
    description: 'Find solution folders in batch mode'
  })

  const folderList = folders.trim().split('\n').filter(f => f.length > 0)

  if (folderList.length === 0) {
    console.error(`❌ No solution folders found under ${batchPath}`)
    console.log('\nExpected: Folders containing README.md or *COMPLETION*.md files')
    return
  }

  console.log(`\n✓ Found ${folderList.length} solution folders:`)
  folderList.forEach((f, i) => console.log(`  ${i+1}. ${f}`))

  // Confirm batch operation
  if (requireApproval) {
    const confirm = await AskUserQuestion({
      questions: [{
        question: `Process ${folderList.length} folders and sync to Shopify?`,
        header: "Batch Confirm",
        options: [
          { label: "Yes - Process all", description: `Sync ${folderList.length} products (with approval gates)` },
          { label: "No - Cancel", description: "Cancel batch operation" }
        ],
        multiSelect: false
      }]
    })

    if (confirm.answers['0'] === 'No - Cancel') {
      console.log('⏹️  Batch operation cancelled')
      return
    }
  }

  // Process all folders
  const results = []
  for (let i = 0; i < folderList.length; i++) {
    console.log(`\n━━━ Processing ${i+1}/${folderList.length}: ${folderList[i]} ━━━`)
    const result = await syncFolder(folderList[i], requireApproval)
    results.push(result)
  }

  displayResults(results)
}
```

## Step 2: Sync Individual Folder

```javascript
async function syncFolder(folderPath, requireApproval = true) {
  const startTime = Date.now()

  try {
    // ━━━ PHASE 1: DATA EXTRACTION ━━━
    console.log('\n📦 PHASE 1: EXTRACTING PRODUCT DATA')
    console.log('   Invoking Folder Parser Agent...')

    const extractionResult = await Task({
      subagent_type: 'prompt-engineering-agent', // Will invoke folder-parser-agent
      description: 'Extract product data from solution folder',
      prompt: `
        You are the Folder Parser Agent (see templates/folder-parser-agent.md).

        Extract product data from solution folder: ${folderPath}

        Follow the extraction workflow:
        1. Discover data sources (completion reports, README, strategy files)
        2. Extract metrics (quality, ROI, time/cost savings)
        3. Extract product overview (name, description, features)
        4. Extract target audience
        5. Calculate pricing recommendations
        6. Assess confidence score
        7. Generate JSON output

        Return structured JSON conforming to the product definition schema.
        Include metadata with data sources and confidence scores.
      `
    })

    console.log('   ✓ Extraction complete')

    // Parse extraction result (assume JSON in extractionResult)
    const extractedData = parseExtractionResult(extractionResult)

    // Check confidence level
    if (extractedData.confidence.overall === 'low') {
      console.warn('\n⚠️  WARNING: Low confidence extraction')
      console.warn(`   Confidence: ${extractedData.confidence.overall}`)
      console.warn(`   Missing data: ${extractedData.confidence.missingData.join(', ')}`)

      if (requireApproval) {
        const proceed = await AskUserQuestion({
          questions: [{
            question: "Low confidence extraction. Proceed anyway?",
            header: "Low Confidence",
            options: [
              { label: "Yes - Proceed", description: "Continue with limited data" },
              { label: "No - Skip", description: "Skip this product" },
              { label: "Manual Entry", description: "Use /product:define instead" }
            ],
            multiSelect: false
          }]
        })

        if (proceed.answers['0'] !== 'Yes - Proceed') {
          return {
            folder: folderPath,
            status: 'skipped',
            reason: 'Low confidence, user declined to proceed',
            duration: (Date.now() - startTime) / 1000
          }
        }
      }
    }

    console.log(`   📊 Confidence: ${extractedData.confidence.overall}`)
    console.log(`   📁 Data sources: ${extractedData.metadata.dataSources.completionReports.length + extractedData.metadata.dataSources.strategyFiles.length}`)

    // ━━━ PHASE 2: SHOPIFY PRODUCT CREATION ━━━
    console.log('\n🛍️  PHASE 2: CREATING SHOPIFY PRODUCT')
    console.log('   Invoking Shopify Product Agent...')

    const productResult = await Task({
      subagent_type: 'prompt-engineering-agent', // Will invoke shopify-product-agent
      description: 'Create Shopify product with approval workflow',
      prompt: `
        You are the Shopify Product Agent (see templates/shopify-product-agent.md).

        Create Shopify product from extracted data:
        ${JSON.stringify(extractedData, null, 2)}

        Follow the product creation workflow:
        1. Validate input data
        2. Enrich for Shopify (SEO, HTML, tags, variants, metafields)
        ${requireApproval ? '3. Gate 1: Product listing review (REQUEST APPROVAL)' : '3. Gate 1: SKIPPED (auto-apply mode)'}
        4. Create product via Shopify API (rate limiting, retry logic)
        ${requireApproval ? '5. Gate 2: Campaign strategy review (REQUEST APPROVAL)' : '5. Gate 2: SKIPPED (auto-apply mode)'}
        6. Launch campaign (if approved)
        7. Return result with product ID, URL, campaign status

        Shopify API Configuration:
        - Shop Domain: ${process.env.SHOPIFY_SHOP_DOMAIN || 'yourstore.myshopify.com'}
        - API Version: 2024-01
        - Rate Limit: 2 requests/second
        - Approval Mode: ${requireApproval ? 'ENABLED' : 'DISABLED (auto-apply)'}

        Use patterns from:
        - patterns/integration/shopify-api-integration.md (API reference)
        - templates/shopify-product-agent.md (agent protocol)
      `
    })

    console.log('   ✓ Shopify product creation complete')

    // Parse product result
    const productData = parseProductResult(productResult)

    const duration = (Date.now() - startTime) / 1000

    return {
      folder: folderPath,
      status: 'success',
      product: {
        id: productData.product.id,
        url: productData.product.url,
        title: productData.product.title,
        pricingTiers: productData.product.variants?.length || 3
      },
      campaign: productData.campaign ? {
        launched: true,
        id: productData.campaign.id,
        status: productData.campaign.status
      } : {
        launched: false
      },
      confidence: extractedData.confidence.overall,
      duration,
      timeSaved: 30 - (duration / 60) // 30 min manual - actual time in minutes
    }

  } catch (error) {
    const duration = (Date.now() - startTime) / 1000

    return {
      folder: folderPath,
      status: 'failed',
      error: error.message,
      duration
    }
  }
}
```

## Step 3: Display Results

### Single Product Result

```javascript
function displayResults(results) {
  const result = results[0] // Single result

  if (result.status === 'success') {
    console.log(`
═══════════════════════════════════════════════════
      PRODUCT SYNCED SUCCESSFULLY TO SHOPIFY
═══════════════════════════════════════════════════

📂 SOURCE FOLDER: ${result.folder}
📊 EXTRACTION CONFIDENCE: ${result.confidence}

PRODUCT CREATED:
  • Product ID: ${result.product.id}
  • Product URL: ${result.product.url}
  • Title: ${result.product.title}
  • Pricing Tiers: ${result.product.pricingTiers}

CAMPAIGN ${result.campaign.launched ? 'LAUNCHED ✓' : 'NOT LAUNCHED'}
${result.campaign.launched ? `  • Campaign ID: ${result.campaign.id}
  • Status: ${result.campaign.status}` : '  • User skipped campaign launch'}

───────────────────────────────────────────────────

⏱️  TIME SAVED: ${result.timeSaved.toFixed(1)} minutes
   (30 min manual → ${(result.duration / 60).toFixed(1)} min automated = ${((result.timeSaved / 30) * 100).toFixed(0)}% reduction)

NEXT STEPS:
  1. Test product page: ${result.product.url}
  2. Add product images (Shopify Admin → Products → ${result.product.id})
  ${result.campaign.launched ? '3. Deploy campaign creative to ad platforms' : '3. Run /campaign:create to generate campaign'}
  4. Monitor performance: /shopify:monitor --product-id ${result.product.id}

═══════════════════════════════════════════════════
    `)
  } else if (result.status === 'skipped') {
    console.log(`
⏹️  PRODUCT SYNC SKIPPED

📂 Folder: ${result.folder}
   Reason: ${result.reason}
    `)
  } else if (result.status === 'failed') {
    console.log(`
❌ PRODUCT SYNC FAILED

📂 Folder: ${result.folder}
   Error: ${result.error}

SUGGESTED FIXES:
  1. Check folder contains completion reports or README
  2. Verify Shopify API credentials (SHOPIFY_ACCESS_TOKEN)
  3. Run /product:extract-from-solution ${result.folder} to debug extraction
  4. Check Shopify API status: https://www.shopifystatus.com
    `)
  }
}
```

### Batch Results Summary

```javascript
function displayResults(results) {
  const successCount = results.filter(r => r.status === 'success').length
  const failedCount = results.filter(r => r.status === 'failed').length
  const skippedCount = results.filter(r => r.status === 'skipped').length

  const totalDuration = results.reduce((sum, r) => sum + r.duration, 0)
  const totalTimeSaved = results.reduce((sum, r) => sum + (r.timeSaved || 0), 0)

  console.log(`
═══════════════════════════════════════════════════
         BATCH SYNC COMPLETE - SUMMARY REPORT
═══════════════════════════════════════════════════

PROCESSED: ${results.length} products
  ✓ Success: ${successCount}
  ❌ Failed: ${failedCount}
  ⏹️  Skipped: ${skippedCount}

TIME STATISTICS:
  • Total Time: ${(totalDuration / 60).toFixed(1)} minutes
  • Average Time per Product: ${(totalDuration / 60 / results.length).toFixed(1)} minutes
  • Time Saved: ${totalTimeSaved.toFixed(0)} minutes (vs ${results.length * 30} min manual)
  • Efficiency: ${((totalTimeSaved / (results.length * 30)) * 100).toFixed(0)}% time reduction

───────────────────────────────────────────────────

DETAILED RESULTS:
`)

  results.forEach((result, i) => {
    const icon = result.status === 'success' ? '✓' : result.status === 'failed' ? '❌' : '⏹️'
    console.log(`${i+1}. ${icon} ${result.folder}`)

    if (result.status === 'success') {
      console.log(`     Product ID: ${result.product.id}`)
      console.log(`     URL: ${result.product.url}`)
      console.log(`     Campaign: ${result.campaign.launched ? 'Launched ✓' : 'Not launched'}`)
    } else if (result.status === 'failed') {
      console.log(`     Error: ${result.error}`)
    } else if (result.status === 'skipped') {
      console.log(`     Reason: ${result.reason}`)
    }
    console.log('')
  })

  console.log(`═══════════════════════════════════════════════════`)

  if (failedCount > 0) {
    console.log(`\n⚠️  ${failedCount} product(s) failed. Review errors above and retry.`)
  }

  if (successCount > 0) {
    console.log(`\n✓ ${successCount} product(s) successfully synced to Shopify!`)
    console.log(`\nNext Steps:`)
    console.log(`  1. Review products in Shopify Admin`)
    console.log(`  2. Add product images for each product`)
    console.log(`  3. Deploy campaign creative to ad platforms`)
    console.log(`  4. Monitor performance: /shopify:monitor`)
  }
}
```

## Error Handling

### Folder Not Found

```markdown
❌ Folder not found: test-outputs/invalid-folder/

Did you mean one of these?
  test-outputs/scenario-1-saas/
  test-outputs/scenario-2-ecommerce/
  test-outputs/scenario-3-b2b-services/

Usage:
  /shopify:sync --folder test-outputs/scenario-1-saas/
  /shopify:sync --batch test-outputs/
```

### Shopify API Credentials Missing

```markdown
❌ SHOPIFY API ERROR

Shopify API credentials not configured.

Required environment variables:
  • SHOPIFY_SHOP_DOMAIN (yourstore.myshopify.com)
  • SHOPIFY_ACCESS_TOKEN (Admin API access token)
  • SHOPIFY_API_VERSION (2024-01) [optional, defaults to 2024-01]

How to set up:
  1. Go to Shopify Admin → Settings → Apps and sales channels → Develop apps
  2. Create a new app → Configure Admin API scopes → Grant: write_products, read_products
  3. Install app → Reveal API token
  4. Set environment variables:
     export SHOPIFY_SHOP_DOMAIN="yourstore.myshopify.com"
     export SHOPIFY_ACCESS_TOKEN="shpat_xxxxx"

Retry after configuring credentials.
```

### Rate Limit Exceeded

```markdown
⏳ SHOPIFY API RATE LIMIT EXCEEDED

Too many requests to Shopify API (>2 req/sec).

Automatic handling:
  ✓ Waiting 2 seconds before retry...
  ✓ Request throttled and queued

If you see this repeatedly:
  • Consider reducing batch size (process fewer products at once)
  • Check for other scripts calling Shopify API simultaneously
  • Wait 1 minute and retry
```

### Low Confidence Extraction

```markdown
⚠️  LOW CONFIDENCE EXTRACTION WARNING

Folder: custom-project/
Confidence: Low (1/5 data sources found)

Found:
  ✓ README.md (product name, basic description)

Missing:
  ✗ Completion reports (no metrics)
  ✗ Strategy files (no audience data)
  ✗ Templates (no capabilities)

Proceeding will create a Shopify product with:
  • Limited product description
  • Estimated pricing (no ROI data)
  • Generic target audience
  • No proven metrics

RECOMMENDATIONS:
  1. Run /product:define manually for this product
  2. Search for completion reports in parent directories
  3. Skip this product and sync others

Continue anyway? [Yes / No / Skip]
```

## Helper Functions

```javascript
function parseArguments(argsString) {
  // Parse command-line style arguments
  const args = {}
  const parts = argsString.split(/\s+/)

  for (let i = 0; i < parts.length; i++) {
    if (parts[i].startsWith('--')) {
      const key = parts[i]
      const value = parts[i+1] && !parts[i+1].startsWith('--') ? parts[i+1] : true
      args[key] = value
      if (value !== true) i++ // Skip next item (it was the value)
    } else {
      // Positional argument
      args.positional = args.positional || []
      args.positional.push(parts[i])
    }
  }

  return args
}

function parseExtractionResult(result) {
  // Parse Folder Parser Agent output
  // Assume result contains JSON in a code block or raw JSON
  const jsonMatch = result.match(/```json\n([\s\S]*?)\n```/) || result.match(/(\{[\s\S]*\})/)

  if (jsonMatch) {
    return JSON.parse(jsonMatch[1])
  }

  throw new Error('Failed to parse extraction result. Expected JSON output from Folder Parser Agent.')
}

function parseProductResult(result) {
  // Parse Shopify Product Agent output
  // Assume result contains structured product data
  const jsonMatch = result.match(/```json\n([\s\S]*?)\n```/) || result.match(/(\{[\s\S]*\})/)

  if (jsonMatch) {
    return JSON.parse(jsonMatch[1])
  }

  // Fallback: Parse from markdown output
  const productIdMatch = result.match(/Product ID:\s*(\d+)/)
  const productUrlMatch = result.match(/Product URL:\s*(https?:\/\/[^\s]+)/)
  const titleMatch = result.match(/TITLE:\s*(.+)/)

  if (productIdMatch && productUrlMatch) {
    return {
      product: {
        id: productIdMatch[1],
        url: productUrlMatch[1],
        title: titleMatch ? titleMatch[1] : 'Unknown',
        variants: []
      },
      campaign: {
        launched: result.includes('CAMPAIGN LAUNCHED: Yes'),
        id: null,
        status: 'generated'
      }
    }
  }

  throw new Error('Failed to parse product result. Expected product ID and URL from Shopify Product Agent.')
}

function showUsage() {
  console.log(`
Usage:
  /shopify:sync --folder <path>           # Sync single product
  /shopify:sync --batch <parent-path>     # Sync multiple products
  /shopify:sync --folder <path> --review  # Explicit review mode (default)
  /shopify:sync --folder <path> --auto-apply  # Skip approvals (dangerous!)

Examples:
  /shopify:sync --folder test-outputs/scenario-1-saas/
  /shopify:sync --batch test-outputs/
  /shopify:sync --folder custom-project/ --review

Options:
  --folder <path>       Path to AI solution folder (single product)
  --batch <path>        Path to parent folder (sync all subfolders)
  --review              Require approval at gates (default behavior)
  --auto-apply          Skip approval gates (USE WITH CAUTION - no human review)

See Also:
  /product:extract-from-solution <folder>  # Extract data only (no Shopify)
  /product:define --from-solution <folder> # Refine product manually
  /shopify:publish --product-id <id>       # Launch campaign for existing product
  /shopify:update --folder <folder>        # Update existing product from folder
  `)
}

function showError(message) {
  console.error(`\n❌ ERROR: ${message}\n`)
}
```

## Success Criteria

- [ ] Successfully syncs single AI solution folder to Shopify product
- [ ] Successfully syncs batch of 3+ folders to Shopify products
- [ ] Implements two-gate approval workflow (product listing + campaign)
- [ ] Respects API rate limits (2 req/sec, no 429 errors)
- [ ] Handles low confidence extractions with user warning
- [ ] Provides clear error messages with fix suggestions
- [ ] Achieves 80%+ time savings (30 min → 6 min per product)
- [ ] Logs all transactions for audit trail

## Notes

- **Time Savings**: 80% reduction per product (30 min manual → 6 min automated)
- **Batch Efficiency**: Process 10 products in 60 minutes vs 300 minutes manual (80% savings maintained)
- **Approval Gates**: Two mandatory approvals ensure quality (product listing + campaign strategy)
- **Auto-Apply Mode**: Available but discouraged (bypasses human review)
- **Rate Limiting**: Automatic throttling prevents 429 errors from Shopify
- **Confidence Scores**: Transparent data quality assessment (High/Medium/Low)
- **Error Recovery**: Retry logic for transient failures, clear messages for permanent errors
- **Audit Trail**: All operations logged (timestamp, action, product ID, source folder)

---

**Uses**: Folder Parser Agent, Shopify Product Agent, Campaign System
**Dependencies**: Shopify API credentials (SHOPIFY_ACCESS_TOKEN, SHOPIFY_SHOP_DOMAIN)
**Output**: Shopify products live + optional marketing campaigns launched
**Next Commands**: `/shopify:monitor`, `/shopify:update`, `/campaign:create`
