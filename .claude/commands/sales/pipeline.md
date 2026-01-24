---
description: Visualize sales pipeline and identify bottlenecks
argument-hint: [--period <this-month|this-quarter|this-year>] [--team <team-name>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Write
---

Sales pipeline visualization: **${ARGUMENTS}**

## Pipeline Analytics

**Visualizes**:

- Deals by stage (count + value)
- Conversion rates between stages
- Average time in each stage
- Bottlenecks and drop-offs
- Win/loss analysis
- Pipeline health score

Routes to **agent-router**:

```javascript
await Task({
  subagent_type: 'agent-router',
  description: 'Generate sales pipeline analytics',
  prompt: `Generate sales pipeline analytics:

Period: ${PERIOD || 'this-month'}
Team: ${TEAM || 'All teams'}

Execute comprehensive pipeline analysis:

## 1. Fetch Pipeline Data from Zoho CRM

\`\`\`bash
# Get all deals in pipeline
curl "https://www.zohoapis.com/crm/v2/Deals" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Stage:not_equals:Closed Won)AND(Stage:not_equals:Closed Lost)" \\
  --data-urlencode "per_page=200"

# Get closed deals for conversion analysis
curl "https://www.zohoapis.com/crm/v2/Deals" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Closing_Date:between:${START_DATE},${END_DATE})" \\
  --data-urlencode "per_page=200"
\`\`\`

Extract deal data:
- Deal ID
- Stage (Qualification, Needs Analysis, Proposal, Negotiation, Closed Won/Lost)
- Amount
- Owner
- Created date
- Stage history (time in each stage)
- Close probability
- Lost reason (if applicable)

## 2. Calculate Pipeline Metrics

### Deals by Stage

\`\`\`javascript
const pipeline = {
  'Qualification': { count: 0, value: 0, deals: [] },
  'Needs Analysis': { count: 0, value: 0, deals: [] },
  'Proposal': { count: 0, value: 0, deals: [] },
  'Negotiation': { count: 0, value: 0, deals: [] }
};

deals.forEach(deal => {
  if (pipeline[deal.stage]) {
    pipeline[deal.stage].count++;
    pipeline[deal.stage].value += deal.amount;
    pipeline[deal.stage].deals.push(deal);
  }
});

// Calculate totals
const totalDeals = Object.values(pipeline).reduce((sum, stage) => sum + stage.count, 0);
const totalValue = Object.values(pipeline).reduce((sum, stage) => sum + stage.value, 0);

console.log(\`Total deals in pipeline: \${totalDeals}\`);
console.log(\`Total pipeline value: $\${totalValue.toLocaleString()}\`);
\`\`\`

### Conversion Rates

\`\`\`javascript
// Calculate stage-to-stage conversion rates
function calculateConversionRates(historicalDeals) {
  const conversions = {
    'Qualification → Needs Analysis': 0,
    'Needs Analysis → Proposal': 0,
    'Proposal → Negotiation': 0,
    'Negotiation → Closed Won': 0
  };

  // Analyze historical deals
  historicalDeals.forEach(deal => {
    const stages = deal.stageHistory; // Array of stages deal went through

    if (stages.includes('Qualification') && stages.includes('Needs Analysis')) {
      conversions['Qualification → Needs Analysis']++;
    }
    if (stages.includes('Needs Analysis') && stages.includes('Proposal')) {
      conversions['Needs Analysis → Proposal']++;
    }
    if (stages.includes('Proposal') && stages.includes('Negotiation')) {
      conversions['Proposal → Negotiation']++;
    }
    if (stages.includes('Negotiation') && deal.stage === 'Closed Won') {
      conversions['Negotiation → Closed Won']++;
    }
  });

  // Calculate percentages
  const totalQualified = historicalDeals.filter(d => d.stageHistory.includes('Qualification')).length;
  const totalNeedsAnalysis = historicalDeals.filter(d => d.stageHistory.includes('Needs Analysis')).length;
  const totalProposal = historicalDeals.filter(d => d.stageHistory.includes('Proposal')).length;
  const totalNegotiation = historicalDeals.filter(d => d.stageHistory.includes('Negotiation')).length;

  return {
    'Qualification → Needs Analysis': (conversions['Qualification → Needs Analysis'] / totalQualified * 100).toFixed(1),
    'Needs Analysis → Proposal': (conversions['Needs Analysis → Proposal'] / totalNeedsAnalysis * 100).toFixed(1),
    'Proposal → Negotiation': (conversions['Proposal → Negotiation'] / totalProposal * 100).toFixed(1),
    'Negotiation → Closed Won': (conversions['Negotiation → Closed Won'] / totalNegotiation * 100).toFixed(1)
  };
}

const conversionRates = calculateConversionRates(closedDeals);
\`\`\`

### Average Time in Stage

\`\`\`javascript
function calculateAverageTimeInStage(deals) {
  const stageTimes = {};

  deals.forEach(deal => {
    deal.stageHistory.forEach((stageEntry, index) => {
      const stage = stageEntry.stage;
      const enteredAt = new Date(stageEntry.enteredAt);
      const leftAt = index < deal.stageHistory.length - 1
        ? new Date(deal.stageHistory[index + 1].enteredAt)
        : new Date(); // Still in this stage

      const daysInStage = (leftAt - enteredAt) / (1000 * 60 * 60 * 24);

      if (!stageTimes[stage]) {
        stageTimes[stage] = { total: 0, count: 0 };
      }
      stageTimes[stage].total += daysInStage;
      stageTimes[stage].count++;
    });
  });

  const averages = {};
  Object.keys(stageTimes).forEach(stage => {
    averages[stage] = (stageTimes[stage].total / stageTimes[stage].count).toFixed(1);
  });

  return averages;
}

const avgTimeInStage = calculateAverageTimeInStage(allDeals);
console.log('Average days in each stage:', avgTimeInStage);
\`\`\`

### Win/Loss Analysis

\`\`\`javascript
const closedThisPeriod = closedDeals.filter(d => {
  const closeDate = new Date(d.closingDate);
  return closeDate >= new Date(\${START_DATE}) && closeDate <= new Date(\${END_DATE});
});

const won = closedThisPeriod.filter(d => d.stage === 'Closed Won');
const lost = closedThisPeriod.filter(d => d.stage === 'Closed Lost');

const winRate = (won.length / closedThisPeriod.length * 100).toFixed(1);
const avgDealSize = won.reduce((sum, d) => sum + d.amount, 0) / won.length;
const avgSalesCycle = won.reduce((sum, d) => sum + d.salesCycleDays, 0) / won.length;

// Loss reasons
const lossReasons = {};
lost.forEach(d => {
  const reason = d.lostReason || 'Unknown';
  lossReasons[reason] = (lossReasons[reason] || 0) + 1;
});

console.log(\`Win rate: \${winRate}%\`);
console.log(\`Avg deal size: $\${avgDealSize.toLocaleString()}\`);
console.log(\`Avg sales cycle: \${avgSalesCycle.toFixed(0)} days\`);
console.log('Loss reasons:', lossReasons);
\`\`\`

## 3. Identify Bottlenecks

\`\`\`javascript
function identifyBottlenecks(pipeline, conversionRates, avgTimeInStage) {
  const bottlenecks = [];

  // Low conversion rate (<50%)
  Object.entries(conversionRates).forEach(([transition, rate]) => {
    if (parseFloat(rate) < 50) {
      bottlenecks.push({
        type: 'Low Conversion',
        stage: transition,
        metric: \`\${rate}%\`,
        severity: 'High',
        recommendation: \`Investigate why deals are dropping off at \${transition.split(' → ')[0]}\`
      });
    }
  });

  // Long time in stage (>30 days)
  Object.entries(avgTimeInStage).forEach(([stage, days]) => {
    if (parseFloat(days) > 30) {
      bottlenecks.push({
        type: 'Stagnation',
        stage: stage,
        metric: \`\${days} days average\`,
        severity: 'Medium',
        recommendation: \`Deals staying too long in \${stage}. Consider more aggressive follow-up or qualification.\`
      });
    }
  });

  // Large concentration in one stage (>40% of pipeline)
  Object.entries(pipeline).forEach(([stage, data]) => {
    const percentage = (data.count / totalDeals * 100).toFixed(1);
    if (parseFloat(percentage) > 40) {
      bottlenecks.push({
        type: 'Concentration',
        stage: stage,
        metric: \`\${percentage}% of pipeline\`,
        severity: 'Low',
        recommendation: \`Too many deals in \${stage}. Prioritize moving deals forward or disqualifying.\`
      });
    }
  });

  return bottlenecks.sort((a, b) => {
    const severityOrder = { High: 3, Medium: 2, Low: 1 };
    return severityOrder[b.severity] - severityOrder[a.severity];
  });
}

const bottlenecks = identifyBottlenecks(pipeline, conversionRates, avgTimeInStage);
\`\`\`

## 4. Calculate Pipeline Health Score

\`\`\`javascript
function calculatePipelineHealth(metrics) {
  let score = 100;

  // Deduct for low conversion rates
  Object.values(metrics.conversionRates).forEach(rate => {
    if (parseFloat(rate) < 40) score -= 15;
    else if (parseFloat(rate) < 50) score -= 10;
    else if (parseFloat(rate) < 60) score -= 5;
  });

  // Deduct for long sales cycles
  Object.values(metrics.avgTimeInStage).forEach(days => {
    if (parseFloat(days) > 45) score -= 10;
    else if (parseFloat(days) > 30) score -= 5;
  });

  // Deduct for low win rate
  if (metrics.winRate < 20) score -= 20;
  else if (metrics.winRate < 30) score -= 15;
  else if (metrics.winRate < 40) score -= 10;

  // Deduct for pipeline imbalance
  const stagePercentages = Object.values(metrics.pipeline).map(s =>
    s.count / metrics.totalDeals * 100
  );
  if (Math.max(...stagePercentages) > 50) score -= 10;

  return Math.max(0, score);
}

const healthScore = calculatePipelineHealth({
  conversionRates,
  avgTimeInStage,
  winRate: parseFloat(winRate),
  pipeline,
  totalDeals
});

const healthGrade =
  healthScore >= 90 ? 'A (Excellent)' :
  healthScore >= 80 ? 'B (Good)' :
  healthScore >= 70 ? 'C (Fair)' :
  healthScore >= 60 ? 'D (Needs Improvement)' :
  'F (Critical)';

console.log(\`Pipeline Health: \${healthScore}/100 (\${healthGrade})\`);
\`\`\`

## 5. Generate Visual Pipeline Report

\`\`\`markdown
# Sales Pipeline Report

**Period**: \${PERIOD}
**Team**: \${TEAM}
**Generated**: \${DATE}

## Pipeline Health: \${HEALTH_SCORE}/100 (\${HEALTH_GRADE})

**Overall Status**: \${HEALTH_SCORE >= 80 ? '✅ Healthy' : HEALTH_SCORE >= 60 ? '⚠️ Needs Attention' : '🚨 Critical'}

---

## Pipeline Overview

**Total Deals**: \${TOTAL_DEALS}
**Total Value**: $\${TOTAL_VALUE.toLocaleString()}
**Avg Deal Size**: $\${AVG_DEAL_SIZE.toLocaleString()}

\`\`\`
┌─────────────────────────────────────────────────────────────────┐
│                    SALES PIPELINE FUNNEL                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Qualification          │ \${QUAL_COUNT} deals  │ $\${QUAL_VALUE}K   │
│  ████████████████████████████████████████ (100%)               │
│                         ↓ \${CONV_RATE_1}% conversion            │
│                                                                 │
│  Needs Analysis         │ \${NEEDS_COUNT} deals │ $\${NEEDS_VALUE}K  │
│  ███████████████████████████ (\${NEEDS_PCT}%)                   │
│                         ↓ \${CONV_RATE_2}% conversion            │
│                                                                 │
│  Proposal               │ \${PROP_COUNT} deals  │ $\${PROP_VALUE}K   │
│  ████████████████ (\${PROP_PCT}%)                               │
│                         ↓ \${CONV_RATE_3}% conversion            │
│                                                                 │
│  Negotiation            │ \${NEG_COUNT} deals   │ $\${NEG_VALUE}K    │
│  ██████ (\${NEG_PCT}%)                                          │
│                         ↓ \${CONV_RATE_4}% conversion            │
│                                                                 │
│  Closed Won             │ \${WON_COUNT} deals   │ $\${WON_VALUE}K    │
│  ███ (\${WON_PCT}%)                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
\`\`\`

## Pipeline by Stage

| Stage | Deals | Value | % of Pipeline | Avg Days in Stage |
|-------|-------|-------|---------------|-------------------|
| Qualification | \${QUAL_COUNT} | $\${QUAL_VALUE} | \${QUAL_PCT}% | \${QUAL_DAYS} days |
| Needs Analysis | \${NEEDS_COUNT} | $\${NEEDS_VALUE} | \${NEEDS_PCT}% | \${NEEDS_DAYS} days |
| Proposal | \${PROP_COUNT} | $\${PROP_VALUE} | \${PROP_PCT}% | \${PROP_DAYS} days |
| Negotiation | \${NEG_COUNT} | $\${NEG_VALUE} | \${NEG_PCT}% | \${NEG_DAYS} days |
| **Total** | **\${TOTAL_DEALS}** | **$\${TOTAL_VALUE}** | **100%** | **\${AVG_TOTAL_DAYS} days** |

## Conversion Rates

| Transition | Rate | Status |
|------------|------|--------|
| Qualification → Needs Analysis | \${CONV_1}% | \${CONV_1 >= 60 ? '✅' : CONV_1 >= 50 ? '⚠️' : '🚨'} |
| Needs Analysis → Proposal | \${CONV_2}% | \${CONV_2 >= 60 ? '✅' : CONV_2 >= 50 ? '⚠️' : '🚨'} |
| Proposal → Negotiation | \${CONV_3}% | \${CONV_3 >= 60 ? '✅' : CONV_3 >= 50 ? '⚠️' : '🚨'} |
| Negotiation → Closed Won | \${CONV_4}% | \${CONV_4 >= 60 ? '✅' : CONV_4 >= 50 ? '⚠️' : '🚨'} |
| **Overall Win Rate** | **\${WIN_RATE}%** | **\${WIN_RATE >= 30 ? '✅' : WIN_RATE >= 20 ? '⚠️' : '🚨'}** |

## Win/Loss Analysis

**Closed This Period**: \${CLOSED_COUNT} deals
- ✅ **Won**: \${WON_COUNT} deals ($\${WON_VALUE})
- ❌ **Lost**: \${LOST_COUNT} deals ($\${LOST_VALUE})
- **Win Rate**: \${WIN_RATE}%

**Average Deal Size**: $\${AVG_DEAL_SIZE}
**Average Sales Cycle**: \${AVG_SALES_CYCLE} days

### Top Loss Reasons

1. **\${LOSS_REASON_1}**: \${LOSS_COUNT_1} deals (\${LOSS_PCT_1}%)
2. **\${LOSS_REASON_2}**: \${LOSS_COUNT_2} deals (\${LOSS_PCT_2}%)
3. **\${LOSS_REASON_3}**: \${LOSS_COUNT_3} deals (\${LOSS_PCT_3}%)

## Bottlenecks Identified

${bottlenecks.length > 0 ? bottlenecks.map((b, i) => \`
### \${i + 1}. \${b.type} - \${b.stage}
**Severity**: \${b.severity === 'High' ? '🚨' : b.severity === 'Medium' ? '⚠️' : '💡'} \${b.severity}
**Metric**: \${b.metric}
**Recommendation**: \${b.recommendation}
\`).join('\\n') : 'No critical bottlenecks identified ✅'}

## Key Insights

### Strengths 💪
${generateStrengths(metrics)}

### Areas for Improvement 🎯
${generateImprovements(metrics)}

## Recommended Actions

**This Week**:
1. \${ACTION_1}
2. \${ACTION_2}
3. \${ACTION_3}

**This Month**:
1. \${ACTION_4}
2. \${ACTION_5}

## Top Deals to Focus On

**Highest Value Deals**:
${topDeals.map((d, i) => \`\${i + 1}. \${d.name} - $\${d.amount} (\${d.stage}) - Owner: \${d.owner}\`).join('\\n')}

**Deals at Risk** (stagnant >30 days):
${atRiskDeals.map((d, i) => \`\${i + 1}. \${d.name} - \${d.daysInStage} days in \${d.stage} - Action: \${d.recommendedAction}\`).join('\\n')}

---
**Next Review**: \${NEXT_REVIEW_DATE}
**Generated by**: AI Sales Analytics
\`\`\`

Save to: sales-analytics/pipeline-\${PERIOD}-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Current month pipeline
/sales/pipeline

# This quarter pipeline
/sales/pipeline --period this-quarter

# Specific team
/sales/pipeline --team enterprise-sales

# This year overview
/sales/pipeline --period this-year
```

## Success Criteria

- ✓ Pipeline visualized by stage
- ✓ Conversion rates calculated
- ✓ Bottlenecks identified
- ✓ Health score calculated (0-100)
- ✓ Win/loss analysis completed
- ✓ Actionable recommendations provided
- ✓ Report saved with visualizations

## Metrics Tracked

**Pipeline Metrics**:

- Total deals and value by stage
- Conversion rates between stages
- Average time in each stage
- Pipeline concentration/balance

**Performance Metrics**:

- Win rate (target: >30%)
- Average deal size
- Average sales cycle (target: <60 days)
- Loss reasons distribution

**Health Indicators**:

- Conversion rate health (target: >50% each stage)
- Sales cycle health (target: <30 days per stage)
- Pipeline balance (no stage >40% of total)
- Overall health score (target: >80/100)

---
**Uses**: agent-router (Zoho CRM integration, analytics)
**Output**: Visual pipeline report with bottlenecks and recommendations
**Next Commands**: `/sales/forecast` (revenue forecasting), `/sales/follow-up` (engage deals at risk)
**Update Frequency**: Weekly recommended
