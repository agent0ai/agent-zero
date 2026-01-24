---
description: Generate revenue forecast based on pipeline and historical data
argument-hint: [--horizon <months>] [--confidence <conservative|realistic|optimistic>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Write
---

Revenue forecast: **${ARGUMENTS}**

## Revenue Forecasting

**Generates**:

- Monthly/quarterly revenue projections
- Confidence intervals (conservative/realistic/optimistic)
- Expected close dates for pipeline deals
- Revenue attainment vs quota
- Trending analysis
- Risk-adjusted forecast

Routes to **agent-router**:

```javascript
await Task({
  subagent_type: 'agent-router',
  description: 'Generate revenue forecast',
  prompt: `Generate revenue forecast:

Forecast horizon: ${HORIZON || '3'} months
Confidence level: ${CONFIDENCE || 'realistic'}

Execute comprehensive revenue forecasting:

## 1. Gather Historical Data

### Fetch Historical Closed Deals

\`\`\`bash
# Get last 12 months of closed deals
START_DATE=$(date -d "12 months ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

curl "https://www.zohoapis.com/crm/v2/Deals" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Closing_Date:between:\${START_DATE},\${END_DATE})" \\
  --data-urlencode "per_page=200"
\`\`\`

### Fetch Current Pipeline

\`\`\`bash
# Get all open deals
curl "https://www.zohoapis.com/crm/v2/Deals" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Stage:not_equals:Closed Won)AND(Stage:not_equals:Closed Lost)" \\
  --data-urlencode "per_page=200"
\`\`\`

### Fetch Monthly Quotas

\`\`\`bash
# Get team quotas (if configured in Zoho)
# Otherwise, use historical average as baseline
\`\`\`

## 2. Calculate Historical Metrics

### Win Rate by Stage

\`\`\`javascript
function calculateWinRateByStage(historicalDeals) {
  const stageWinRates = {};

  const stages = ['Qualification', 'Needs Analysis', 'Proposal', 'Negotiation'];

  stages.forEach(stage => {
    const dealsInStage = historicalDeals.filter(d =>
      d.stageHistory && d.stageHistory.some(s => s.stage === stage)
    );

    const won = dealsInStage.filter(d => d.stage === 'Closed Won').length;

    stageWinRates[stage] = dealsInStage.length > 0
      ? (won / dealsInStage.length * 100).toFixed(1)
      : 0;
  });

  return stageWinRates;
}

const winRateByStage = calculateWinRateByStage(historicalDeals);

// Example output:
// {
//   'Qualification': 15,
//   'Needs Analysis': 30,
//   'Proposal': 50,
//   'Negotiation': 75
// }
\`\`\`

### Average Sales Cycle by Stage

\`\`\`javascript
function calculateAvgSalesCycleFromStage(historicalDeals) {
  const cycleTimes = {};

  const stages = ['Qualification', 'Needs Analysis', 'Proposal', 'Negotiation'];

  stages.forEach(stage => {
    const dealsFromStage = historicalDeals.filter(d =>
      d.stageHistory && d.stageHistory.some(s => s.stage === stage) &&
      d.stage === 'Closed Won'
    );

    const totalDays = dealsFromStage.reduce((sum, deal) => {
      const stageEntry = deal.stageHistory.find(s => s.stage === stage);
      const closeDate = new Date(deal.closingDate);
      const stageDate = new Date(stageEntry.enteredAt);
      const days = (closeDate - stageDate) / (1000 * 60 * 60 * 24);
      return sum + days;
    }, 0);

    cycleTimes[stage] = dealsFromStage.length > 0
      ? Math.round(totalDays / dealsFromStage.length)
      : 0;
  });

  return cycleTimes;
}

const avgSalesCycleFromStage = calculateAvgSalesCycleFromStage(wonDeals);

// Example output:
// {
//   'Qualification': 60,   // 60 days from Qualification to Close
//   'Needs Analysis': 45,  // 45 days from Needs Analysis to Close
//   'Proposal': 30,        // 30 days from Proposal to Close
//   'Negotiation': 15      // 15 days from Negotiation to Close
// }
\`\`\`

### Monthly Revenue Trend

\`\`\`javascript
function calculateMonthlyRevenue(deals) {
  const monthlyRevenue = {};

  deals.forEach(deal => {
    if (deal.stage === 'Closed Won') {
      const closeDate = new Date(deal.closingDate);
      const monthKey = \`\${closeDate.getFullYear()}-\${String(closeDate.getMonth() + 1).padStart(2, '0')}\`;

      if (!monthlyRevenue[monthKey]) {
        monthlyRevenue[monthKey] = 0;
      }
      monthlyRevenue[monthKey] += deal.amount;
    }
  });

  return monthlyRevenue;
}

const monthlyRevenue = calculateMonthlyRevenue(historicalDeals);

// Calculate trend
const revenues = Object.values(monthlyRevenue);
const avgMonthlyRevenue = revenues.reduce((sum, r) => sum + r, 0) / revenues.length;
const trend = revenues.slice(-3).reduce((sum, r) => sum + r, 0) / 3; // Last 3 months avg

const trendDirection = trend > avgMonthlyRevenue * 1.1 ? 'Growing' :
                       trend < avgMonthlyRevenue * 0.9 ? 'Declining' :
                       'Stable';

console.log(\`Avg monthly revenue: $\${avgMonthlyRevenue.toLocaleString()}\`);
console.log(\`Recent trend: \${trendDirection}\`);
\`\`\`

## 3. Forecast Pipeline Deals

### Predict Close Dates and Probabilities

\`\`\`javascript
function forecastPipelineDeals(pipelineDeals, winRateByStage, avgSalesCycleFromStage, confidence) {
  const confidenceMultipliers = {
    'conservative': { winRate: 0.7, cycle: 1.3 },  // Lower win rate, longer cycle
    'realistic': { winRate: 1.0, cycle: 1.0 },     // Historical averages
    'optimistic': { winRate: 1.2, cycle: 0.8 }     // Higher win rate, faster cycle
  };

  const multiplier = confidenceMultipliers[confidence] || confidenceMultipliers['realistic'];

  return pipelineDeals.map(deal => {
    const stage = deal.stage;
    const baseWinRate = parseFloat(winRateByStage[stage] || 0) / 100;
    const baseCycleDays = avgSalesCycleFromStage[stage] || 30;

    // Adjust by confidence level
    const adjustedWinRate = Math.min(1, baseWinRate * multiplier.winRate);
    const adjustedCycleDays = Math.round(baseCycleDays * multiplier.cycle);

    // Calculate expected close date
    const today = new Date();
    const expectedCloseDate = new Date(today);
    expectedCloseDate.setDate(today.getDate() + adjustedCycleDays);

    // Calculate weighted value
    const weightedValue = deal.amount * adjustedWinRate;

    return {
      ...deal,
      winProbability: (adjustedWinRate * 100).toFixed(0),
      expectedCloseDate: expectedCloseDate.toISOString().split('T')[0],
      expectedCloseDays: adjustedCycleDays,
      weightedValue: Math.round(weightedValue)
    };
  });
}

const forecastedDeals = forecastPipelineDeals(
  pipelineDeals,
  winRateByStage,
  avgSalesCycleFromStage,
  \${CONFIDENCE}
);
\`\`\`

### Group by Expected Close Month

\`\`\`javascript
function groupByMonth(forecastedDeals) {
  const byMonth = {};

  forecastedDeals.forEach(deal => {
    const closeDate = new Date(deal.expectedCloseDate);
    const monthKey = \`\${closeDate.getFullYear()}-\${String(closeDate.getMonth() + 1).padStart(2, '0')}\`;

    if (!byMonth[monthKey]) {
      byMonth[monthKey] = {
        deals: [],
        totalValue: 0,
        weightedValue: 0,
        count: 0
      };
    }

    byMonth[monthKey].deals.push(deal);
    byMonth[monthKey].totalValue += deal.amount;
    byMonth[monthKey].weightedValue += deal.weightedValue;
    byMonth[monthKey].count++;
  });

  return byMonth;
}

const forecastByMonth = groupByMonth(forecastedDeals);
\`\`\`

## 4. Generate Forecast Scenarios

\`\`\`javascript
function generateScenarios(forecastByMonth, avgMonthlyRevenue) {
  const scenarios = {
    'conservative': {},
    'realistic': {},
    'optimistic': {}
  };

  Object.keys(forecastByMonth).forEach(month => {
    const data = forecastByMonth[month];

    scenarios['conservative'][month] = Math.round(data.weightedValue * 0.7);
    scenarios['realistic'][month] = Math.round(data.weightedValue);
    scenarios['optimistic'][month] = Math.round(data.weightedValue * 1.2);
  });

  return scenarios;
}

const scenarios = generateScenarios(forecastByMonth, avgMonthlyRevenue);
\`\`\`

## 5. Calculate Attainment vs Quota

\`\`\`javascript
function calculateAttainment(forecastRevenue, quota) {
  const attainment = (forecastRevenue / quota * 100).toFixed(0);

  const status =
    attainment >= 100 ? '✅ On Track' :
    attainment >= 90 ? '⚠️ At Risk' :
    '🚨 Below Target';

  return { attainment, status };
}

// Example for each month
const monthlyAttainment = {};
Object.keys(scenarios['realistic']).forEach(month => {
  const forecast = scenarios['realistic'][month];
  const quota = monthlyQuota[month] || avgMonthlyRevenue;

  monthlyAttainment[month] = calculateAttainment(forecast, quota);
});
\`\`\`

## 6. Identify Risks and Opportunities

\`\`\`javascript
function identifyRisksAndOpportunities(forecastedDeals) {
  const risks = [];
  const opportunities = [];

  forecastedDeals.forEach(deal => {
    const winProb = parseFloat(deal.winProbability);
    const daysUntilClose = deal.expectedCloseDays;

    // High-value deal with low probability = Risk
    if (deal.amount > 50000 && winProb < 50) {
      risks.push({
        type: 'High-value deal at risk',
        deal: deal.name,
        value: deal.amount,
        probability: \`\${winProb}%\`,
        action: 'Increase engagement, schedule executive sponsor meeting'
      });
    }

    // Deal stagnating = Risk
    if (daysUntilClose > 60) {
      risks.push({
        type: 'Long sales cycle',
        deal: deal.name,
        value: deal.amount,
        daysUntilClose: daysUntilClose,
        action: 'Re-engage with urgency, identify blockers'
      });
    }

    // High-value deal with high probability = Opportunity
    if (deal.amount > 50000 && winProb > 70) {
      opportunities.push({
        type: 'High-probability large deal',
        deal: deal.name,
        value: deal.amount,
        probability: \`\${winProb}%\`,
        action: 'Prioritize closing, remove any final blockers'
      });
    }

    // Fast-moving deal = Opportunity
    if (daysUntilClose < 15 && winProb > 60) {
      opportunities.push({
        type: 'Fast-closing deal',
        deal: deal.name,
        value: deal.amount,
        daysUntilClose: daysUntilClose,
        action: 'Strike while hot, expedite contract process'
      });
    }
  });

  return { risks, opportunities };
}

const { risks, opportunities } = identifyRisksAndOpportunities(forecastedDeals);
\`\`\`

## 7. Generate Forecast Report

\`\`\`markdown
# Revenue Forecast Report

**Forecast Horizon**: Next \${HORIZON} months
**Confidence Level**: \${CONFIDENCE}
**Generated**: \${DATE}

---

## Executive Summary

**Forecasted Revenue** (next 3 months):
- 🟢 **Optimistic**: $\${OPTIMISTIC_TOTAL.toLocaleString()}
- 🟡 **Realistic**: $\${REALISTIC_TOTAL.toLocaleString()} ← **Most Likely**
- 🔴 **Conservative**: $\${CONSERVATIVE_TOTAL.toLocaleString()}

**Quota Attainment**: \${ATTAINMENT}% \${ATTAINMENT_STATUS}

**Trend**: \${TREND_DIRECTION} (\${TREND_PCT}% vs avg)

---

## Monthly Forecast Breakdown

| Month | Conservative | Realistic | Optimistic | Quota | Attainment |
|-------|--------------|-----------|------------|-------|------------|
| \${MONTH_1} | $\${CONS_1} | $\${REAL_1} | $\${OPT_1} | $\${QUOTA_1} | \${ATT_1}% \${STATUS_1} |
| \${MONTH_2} | $\${CONS_2} | $\${REAL_2} | $\${OPT_2} | $\${QUOTA_2} | \${ATT_2}% \${STATUS_2} |
| \${MONTH_3} | $\${CONS_3} | $\${REAL_3} | $\${OPT_3} | $\${QUOTA_3} | \${ATT_3}% \${STATUS_3} |
| **Total** | **$\${CONS_TOTAL}** | **$\${REAL_TOTAL}** | **$\${OPT_TOTAL}** | **$\${QUOTA_TOTAL}** | **\${ATT_AVG}%** |

### Visual Forecast

\`\`\`
Revenue Forecast (Next 3 Months)

$500K │                                    ┌─── Optimistic
      │                            ┌───────┘
$400K │                    ┌───────┘
      │            ┌───────┘               ┌─── Realistic
$300K │    ┌───────┘                ┌──────┘
      │────┘                 ┌──────┘
$200K │                ┌─────┘              ┌─── Conservative
      │          ┌─────┘              ┌─────┘
$100K │    ┌─────┘                ────┘
      │────┘
   0K └────┴────┴────┴────┴────┴────┴────┴────┴────┴────
         Month 1      Month 2      Month 3
\`\`\`

---

## Pipeline Composition

**Total Pipeline Value**: $\${TOTAL_PIPELINE_VALUE.toLocaleString()}
**Weighted Pipeline**: $\${WEIGHTED_PIPELINE_VALUE.toLocaleString()}

### By Stage

| Stage | Deals | Total Value | Weighted Value | Avg Win Rate |
|-------|-------|-------------|----------------|--------------|
| Qualification | \${QUAL_COUNT} | $\${QUAL_VALUE} | $\${QUAL_WEIGHTED} | \${QUAL_WIN_RATE}% |
| Needs Analysis | \${NEEDS_COUNT} | $\${NEEDS_VALUE} | $\${NEEDS_WEIGHTED} | \${NEEDS_WIN_RATE}% |
| Proposal | \${PROP_COUNT} | $\${PROP_VALUE} | $\${PROP_WEIGHTED} | \${PROP_WIN_RATE}% |
| Negotiation | \${NEG_COUNT} | $\${NEG_VALUE} | $\${NEG_WEIGHTED} | \${NEG_WIN_RATE}% |
| **Total** | **\${TOTAL_COUNT}** | **$\${TOTAL_VALUE}** | **$\${TOTAL_WEIGHTED}** | **\${AVG_WIN_RATE}%** |

---

## Top Opportunities (High Probability)

${opportunities.slice(0, 5).map((opp, i) => \`
### \${i + 1}. \${opp.deal}
**Type**: \${opp.type}
**Value**: $\${opp.value.toLocaleString()}
**Probability**: \${opp.probability || 'N/A'}
**Action**: \${opp.action}
\`).join('\\n')}

---

## Key Risks

${risks.slice(0, 5).map((risk, i) => \`
### \${i + 1}. \${risk.deal}
**Type**: \${risk.type}
**Value**: $\${risk.value.toLocaleString()}
**Issue**: \${risk.probability ? 'Low win probability: ' + risk.probability : 'Long cycle: ' + risk.daysUntilClose + ' days'}
**Action**: \${risk.action}
\`).join('\\n')}

---

## Historical Performance

**Last 12 Months**:
- Total closed: $\${HISTORICAL_TOTAL.toLocaleString()}
- Monthly average: $\${HISTORICAL_AVG.toLocaleString()}
- Win rate: \${HISTORICAL_WIN_RATE}%
- Avg sales cycle: \${HISTORICAL_CYCLE} days

**Recent Trend** (last 3 months):
- \${TREND_DIRECTION}: \${TREND_PCT}% vs 12-month average
- \${TREND_DIRECTION === 'Growing' ? 'Momentum is positive ✅' : TREND_DIRECTION === 'Declining' ? 'Needs attention ⚠️' : 'Steady performance'}

---

## Recommended Actions to Hit Quota

**To achieve quota for \${MONTH_1}**:
1. \${ACTION_1}
2. \${ACTION_2}
3. \${ACTION_3}

**To improve forecast accuracy**:
1. Update close dates on stale deals (>30 days old)
2. Qualify or disqualify deals in Qualification stage
3. Increase engagement on high-value, low-probability deals

**Pipeline building** (for \${MONTH_2} and \${MONTH_3}):
1. Generate \${NEW_DEALS_NEEDED} new qualified leads
2. Target deal size: $\${TARGET_DEAL_SIZE}
3. Focus on industries: \${TOP_INDUSTRIES}

---

## Forecast Confidence

**Confidence in forecast**: \${FORECAST_CONFIDENCE}

**Factors**:
- ✅ Historical data: 12 months of closed deals
- ✅ Win rate by stage: Calculated from \${HISTORICAL_DEAL_COUNT} deals
- ✅ Sales cycle timing: Based on \${WON_DEAL_COUNT} won deals
- ⚠️ Pipeline quality: \${PIPELINE_QUALITY} (\${STALE_DEAL_COUNT} stale deals >30 days)

**To improve confidence**:
- Keep deal stages and close dates current
- Track loss reasons to improve win rate predictions
- Update pipeline weekly

---

**Next Forecast**: \${NEXT_FORECAST_DATE}
**Contact**: sales-ops@example.com
\`\`\`

Save to: sales-analytics/forecast-\${HORIZON}-months-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# 3-month realistic forecast
/sales/forecast

# 6-month conservative forecast
/sales/forecast --horizon 6 --confidence conservative

# Optimistic forecast for planning
/sales/forecast --confidence optimistic
```

## Forecast Models

**Conservative** (70% of realistic):

- Lower win rates
- Longer sales cycles
- Best for: Minimum guarantees, budgeting

**Realistic** (most likely):

- Historical averages
- Actual win rates and cycles
- Best for: Planning, quota setting

**Optimistic** (120% of realistic):

- Higher win rates
- Faster sales cycles
- Best for: Stretch goals, maximum potential

## Success Criteria

- ✓ 3 forecast scenarios generated
- ✓ Monthly breakdown provided
- ✓ Quota attainment calculated
- ✓ Risks and opportunities identified
- ✓ Historical trends analyzed
- ✓ Actionable recommendations provided
- ✓ Report saved

## Accuracy Tracking

Track forecast vs actual:

- Month 1: Typically 80-90% accurate
- Month 2: Typically 70-80% accurate
- Month 3: Typically 60-70% accurate

**Improvement over time**:

- Clean pipeline data → +10% accuracy
- Regular updates → +15% accuracy
- Longer historical data → +5% accuracy

---
**Uses**: agent-router (Zoho CRM, analytics, forecasting models)
**Output**: Multi-scenario revenue forecast with confidence intervals
**Next Commands**: `/sales/pipeline` (review bottlenecks), `/sales/follow-up` (engage at-risk deals)
**Update Frequency**: Weekly recommended
