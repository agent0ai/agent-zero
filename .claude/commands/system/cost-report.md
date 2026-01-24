---
description: Generate cost report across all services and infrastructure
argument-hint: [--period 30d|90d|12m] [--provider aws|gcp|azure|all] [--detailed] [--budget <amount>]
model: claude-sonnet-4-5-20250929
allowed-tools: [Bash, Read, Write, Task, WebFetch]
---

# /system:cost-report

Generate cost report: **${ARGUMENTS:-last 30 days}**

## Step 1: Detect Cloud Providers

```bash
# Check for AWS credentials
if [ -f ~/.aws/credentials ]; then
  PROVIDERS="$PROVIDERS aws"
fi

# Check for GCP
if command -v gcloud &> /dev/null; then
  PROVIDERS="$PROVIDERS gcp"
fi
```

## Step 2: Fetch AWS Costs

```bash
aws ce get-cost-and-usage \
  --time-period Start=$START_DATE,End=$END_DATE \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output json > /tmp/aws-costs.json
```

## Step 3: Fetch GCP Costs

```bash
gcloud billing accounts list --format=json > /tmp/gcp-accounts.json

# Query BigQuery for billing data
bq query --format=json --use_legacy_sql=false \
  "SELECT service.description, SUM(cost) as total_cost
   FROM \`project.billing_export.gcp_billing_export\`
   WHERE DATE(_PARTITIONTIME) BETWEEN '$START_DATE' AND '$END_DATE'
   GROUP BY service.description"
```

## Step 4: Fetch Third-Party API Costs

Check for:

- OpenAI API usage
- Anthropic API usage
- Stripe processing fees
- Vercel hosting
- Other SaaS tools

## Step 5: Categorize Costs

Group by:

- Environment (dev, staging, prod)
- Service type (compute, storage, bandwidth, APIs)
- Department/project

## Step 6: Calculate Trends

```javascript
const monthOverMonth = (current - previous) / previous * 100;
const costPerUser = totalCost / activeUsers;
const projectedMonthlyCost = (totalCost / daysInPeriod) * 30;
```

## Step 7: Generate Report

```markdown
# 💰 Cost Report (${period})

## Total Monthly Cost: $${totalCost}

### By Provider
- AWS: $${awsCost} (${awsPercent}%)
- GCP: $${gcpCost} (${gcpPercent}%)
- Third-Party APIs: $${apiCost} (${apiPercent}%)

### By Category
1. Compute: $${computeCost}
2. Database: $${dbCost}
3. Storage: $${storageCost}
4. Bandwidth: $${bandwidthCost}
5. APIs: $${apiCallCost}

### Top 10 Cost Drivers
${topCosts.map((c, i) => `${i+1}. ${c.service}: $${c.cost}`).join('\n')}

### Trends
- Month-over-Month: ${trend}%
- Cost per user: $${costPerUser}
- Projected monthly: $${projected}

### Optimization Opportunities
${recommendations.map(r => `- ${r.title}: Save $${r.savings}/month`).join('\n')}
```

**Command Complete** 💰
