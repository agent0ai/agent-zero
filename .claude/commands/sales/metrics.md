---
description: Generate sales KPI dashboard with key metrics
argument-hint: [--period <this-week|this-month|this-quarter|this-year>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Write
---

Sales metrics dashboard: **${ARGUMENTS}**

## Sales KPI Dashboard

**Tracks**:

- Revenue metrics (MRR, ARR, growth rate)
- Pipeline metrics (velocity, coverage, quality)
- Activity metrics (calls, emails, meetings)
- Conversion metrics (lead-to-opportunity, opportunity-to-win)
- Rep performance metrics

Routes to **agent-router**:

```javascript
await Task({
  subagent_type: 'agent-router',
  description: 'Generate sales KPI dashboard',
  prompt: `Generate sales KPI dashboard:

Period: ${PERIOD || 'this-month'}

Execute comprehensive sales metrics analysis:

## 1. Fetch Data from Zoho CRM

\`\`\`bash
PERIOD_START=\${START_DATE}
PERIOD_END=\${END_DATE}

# Closed deals (won)
curl "https://www.zohoapis.com/crm/v2/Deals" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Stage:equals:Closed Won)AND(Closing_Date:between:\${PERIOD_START},\${PERIOD_END})"

# Closed deals (lost)
curl "https://www.zohoapis.com/crm/v2/Deals" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Stage:equals:Closed Lost)AND(Closing_Date:between:\${PERIOD_START},\${PERIOD_END})"

# Current pipeline
curl "https://www.zohoapis.com/crm/v2/Deals" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Stage:not_equals:Closed Won)AND(Stage:not_equals:Closed Lost)"

# New leads
curl "https://www.zohoapis.com/crm/v2/Leads" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Created_Time:between:\${PERIOD_START},\${PERIOD_END})"

# Activities (calls, emails, meetings)
curl "https://www.zohoapis.com/crm/v2/Activities" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -G --data-urlencode "criteria=(Activity_Date:between:\${PERIOD_START},\${PERIOD_END})"
\`\`\`

## 2. Calculate Revenue Metrics

### MRR (Monthly Recurring Revenue)

\`\`\`javascript
function calculateMRR(wonDeals) {
  return wonDeals.reduce((sum, deal) => {
    // Convert to monthly (assuming annual deals)
    const mrr = deal.recurring ? deal.amount / 12 : 0;
    return sum + mrr;
  }, 0);
}

const currentMRR = calculateMRR(wonDealsThisMonth);
const previousMRR = calculateMRR(wonDealsPreviousMonth);
const mrrGrowth = ((currentMRR - previousMRR) / previousMRR * 100).toFixed(1);

console.log(\`Current MRR: $\${currentMRR.toLocaleString()}\`);
console.log(\`MRR Growth: \${mrrGrowth}%\`);
\`\`\`

### ARR (Annual Recurring Revenue)

\`\`\`javascript
const currentARR = currentMRR * 12;
const previousARR = previousMRR * 12;
const arrGrowth = ((currentARR - previousARR) / previousARR * 100).toFixed(1);

console.log(\`Current ARR: $\${currentARR.toLocaleString()}\`);
console.log(\`ARR Growth: \${arrGrowth}%\`);
\`\`\`

### Revenue Growth Rate

\`\`\`javascript
function calculateGrowthRate(current, previous) {
  return ((current - previous) / previous * 100).toFixed(1);
}

const revenueThisPeriod = wonDeals.reduce((sum, d) => sum + d.amount, 0);
const revenuePreviousPeriod = wonDealsPrevious.reduce((sum, d) => sum + d.amount, 0);
const revenueGrowth = calculateGrowthRate(revenueThisPeriod, revenuePreviousPeriod);
\`\`\`

## 3. Calculate Pipeline Metrics

### Pipeline Velocity

\`\`\`javascript
// How fast deals move through pipeline ($ per day)
function calculatePipelineVelocity(deals, days) {
  const wonValue = deals.filter(d => d.stage === 'Closed Won')
    .reduce((sum, d) => sum + d.amount, 0);

  return (wonValue / days).toFixed(0);
}

const velocity = calculatePipelineVelocity(dealsThisPeriod, daysInPeriod);
console.log(\`Pipeline velocity: $\${velocity}/day\`);
\`\`\`

### Pipeline Coverage

\`\`\`javascript
// Pipeline value / Quota (should be 3-4x)
function calculatePipelineCoverage(pipelineValue, quota) {
  return (pipelineValue / quota).toFixed(1);
}

const coverage = calculatePipelineCoverage(totalPipelineValue, monthlyQuota);
const coverageStatus =
  coverage >= 4 ? '✅ Excellent' :
  coverage >= 3 ? '✅ Good' :
  coverage >= 2 ? '⚠️ Low' :
  '🚨 Critical';

console.log(\`Pipeline coverage: \${coverage}x (\${coverageStatus})\`);
\`\`\`

### Pipeline Quality Score

\`\`\`javascript
function calculatePipelineQuality(pipeline) {
  let score = 100;

  // Deduct for stale deals (>30 days no activity)
  const staleDealPct = (staleDeals.length / totalDeals * 100);
  if (staleDealPct > 30) score -= 20;
  else if (staleDealPct > 20) score -= 10;

  // Deduct for low-value deals (<$1K)
  const lowValuePct = (lowValueDeals.length / totalDeals * 100);
  if (lowValuePct > 40) score -= 15;
  else if (lowValuePct > 30) score -= 10;

  // Deduct for missing close dates
  const missingCloseDatePct = (noCloseDateDeals.length / totalDeals * 100);
  if (missingCloseDatePct > 20) score -= 15;
  else if (missingCloseDatePct > 10) score -= 10;

  // Deduct for all deals in one stage (>50%)
  const maxStagePct = Math.max(...Object.values(stageDistribution));
  if (maxStagePct > 50) score -= 10;

  return Math.max(0, score);
}

const qualityScore = calculatePipelineQuality(pipeline);
\`\`\`

## 4. Calculate Conversion Metrics

### Lead-to-Opportunity Conversion

\`\`\`javascript
const leadsCreated = leads.length;
const leadsConverted = leads.filter(l => l.convertedToOpportunity).length;
const leadConversionRate = (leadsConverted / leadsCreated * 100).toFixed(1);

console.log(\`Lead conversion: \${leadConversionRate}% (\${leadsConverted}/\${leadsCreated})\`);
\`\`\`

### Opportunity-to-Win Conversion

\`\`\`javascript
const opportunitiesCreated = opportunities.length;
const opportunitiesWon = opportunities.filter(o => o.stage === 'Closed Won').length;
const winRate = (opportunitiesWon / opportunitiesCreated * 100).toFixed(1);

console.log(\`Win rate: \${winRate}% (\${opportunitiesWon}/\${opportunitiesCreated})\`);
\`\`\`

### Average Deal Size

\`\`\`javascript
const avgDealSize = wonDeals.reduce((sum, d) => sum + d.amount, 0) / wonDeals.length;
const avgDealSizePrevious = wonDealsPrevious.reduce((sum, d) => sum + d.amount, 0) / wonDealsPrevious.length;
const dealSizeGrowth = ((avgDealSize - avgDealSizePrevious) / avgDealSizePrevious * 100).toFixed(1);

console.log(\`Avg deal size: $\${avgDealSize.toLocaleString()} (\${dealSizeGrowth}% vs previous period)\`);
\`\`\`

### Average Sales Cycle

\`\`\`javascript
const avgSalesCycle = wonDeals.reduce((sum, d) => {
  const created = new Date(d.createdTime);
  const closed = new Date(d.closingDate);
  const days = (closed - created) / (1000 * 60 * 60 * 24);
  return sum + days;
}, 0) / wonDeals.length;

console.log(\`Avg sales cycle: \${avgSalesCycle.toFixed(0)} days\`);
\`\`\`

## 5. Calculate Activity Metrics

### Calls, Emails, Meetings

\`\`\`javascript
const activityByType = {
  calls: activities.filter(a => a.type === 'Call').length,
  emails: activities.filter(a => a.type === 'Email').length,
  meetings: activities.filter(a => a.type === 'Meeting').length
};

const totalActivities = Object.values(activityByType).reduce((sum, count) => sum + count, 0);

console.log(\`Total activities: \${totalActivities}\`);
console.log(\`Calls: \${activityByType.calls}\`);
console.log(\`Emails: \${activityByType.emails}\`);
console.log(\`Meetings: \${activityByType.meetings}\`);
\`\`\`

### Activities per Deal

\`\`\`javascript
const activitiesPerDeal = (totalActivities / wonDeals.length).toFixed(1);
console.log(\`Activities per won deal: \${activitiesPerDeal}\`);
\`\`\`

### Activity Efficiency

\`\`\`javascript
// Revenue per activity
const revenuePerActivity = (revenueThisPeriod / totalActivities).toFixed(0);
console.log(\`Revenue per activity: $\${revenuePerActivity}\`);
\`\`\`

## 6. Calculate Rep Performance

### Individual Rep Metrics

\`\`\`javascript
function calculateRepMetrics(deals, activities, repId) {
  const repDeals = deals.filter(d => d.ownerId === repId);
  const repWonDeals = repDeals.filter(d => d.stage === 'Closed Won');
  const repActivities = activities.filter(a => a.ownerId === repId);

  return {
    dealsWon: repWonDeals.length,
    revenue: repWonDeals.reduce((sum, d) => sum + d.amount, 0),
    avgDealSize: repWonDeals.reduce((sum, d) => sum + d.amount, 0) / repWonDeals.length,
    winRate: (repWonDeals.length / repDeals.length * 100).toFixed(1),
    activities: repActivities.length,
    activitiesPerDeal: (repActivities.length / repWonDeals.length).toFixed(1)
  };
}

// Get all unique reps
const reps = [...new Set(deals.map(d => d.ownerId))];

const repPerformance = reps.map(repId => {
  const repName = getRepName(repId); // Fetch from CRM
  const metrics = calculateRepMetrics(deals, activities, repId);

  return {
    name: repName,
    ...metrics
  };
}).sort((a, b) => b.revenue - a.revenue);
\`\`\`

## 7. Generate KPI Dashboard

\`\`\`markdown
# Sales KPI Dashboard

**Period**: \${PERIOD}
**Generated**: \${DATE}

---

## 📊 Revenue Metrics

| Metric | Current | Previous | Growth | Status |
|--------|---------|----------|--------|--------|
| **MRR** | $\${MRR.toLocaleString()} | $\${PREV_MRR.toLocaleString()} | \${MRR_GROWTH}% | \${MRR_GROWTH >= 10 ? '✅' : MRR_GROWTH >= 5 ? '⚠️' : '🚨'} |
| **ARR** | $\${ARR.toLocaleString()} | $\${PREV_ARR.toLocaleString()} | \${ARR_GROWTH}% | \${ARR_GROWTH >= 10 ? '✅' : ARR_GROWTH >= 5 ? '⚠️' : '🚨'} |
| **Revenue** | $\${REVENUE.toLocaleString()} | $\${PREV_REVENUE.toLocaleString()} | \${REV_GROWTH}% | \${REV_GROWTH >= 10 ? '✅' : REV_GROWTH >= 5 ? '⚠️' : '🚨'} |

**Quota Attainment**: \${QUOTA_ATTAINMENT}% \${QUOTA_STATUS}

---

## 🔄 Pipeline Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Pipeline Value** | $\${PIPELINE_VALUE.toLocaleString()} | - | - |
| **Weighted Pipeline** | $\${WEIGHTED_PIPELINE.toLocaleString()} | - | - |
| **Pipeline Coverage** | \${COVERAGE}x | 3-4x | \${COVERAGE >= 3 ? '✅' : '⚠️'} |
| **Pipeline Velocity** | $\${VELOCITY}/day | - | - |
| **Pipeline Quality** | \${QUALITY_SCORE}/100 | >80 | \${QUALITY_SCORE >= 80 ? '✅' : QUALITY_SCORE >= 60 ? '⚠️' : '🚨'} |

---

## 🎯 Conversion Metrics

| Metric | Rate | Previous | Change | Target |
|--------|------|----------|--------|--------|
| **Lead → Opportunity** | \${LEAD_CONV}% | \${PREV_LEAD_CONV}% | \${LEAD_CONV_CHANGE}% | >30% |
| **Opportunity → Win** | \${WIN_RATE}% | \${PREV_WIN_RATE}% | \${WIN_RATE_CHANGE}% | >30% |
| **Overall (Lead → Win)** | \${OVERALL_CONV}% | \${PREV_OVERALL_CONV}% | \${OVERALL_CONV_CHANGE}% | >10% |

---

## 💰 Deal Metrics

| Metric | Value | Previous | Change |
|--------|-------|----------|--------|
| **Avg Deal Size** | $\${AVG_DEAL_SIZE.toLocaleString()} | $\${PREV_AVG_DEAL_SIZE.toLocaleString()} | \${DEAL_SIZE_CHANGE}% |
| **Avg Sales Cycle** | \${AVG_CYCLE} days | \${PREV_AVG_CYCLE} days | \${CYCLE_CHANGE} days |
| **Deals Closed** | \${DEALS_CLOSED} | \${PREV_DEALS_CLOSED} | \${DEALS_CLOSED_CHANGE} |

---

## 📞 Activity Metrics

| Activity | Count | Per Day | Per Deal Won |
|----------|-------|---------|--------------|
| **Calls** | \${CALLS} | \${CALLS_PER_DAY} | \${CALLS_PER_DEAL} |
| **Emails** | \${EMAILS} | \${EMAILS_PER_DAY} | \${EMAILS_PER_DEAL} |
| **Meetings** | \${MEETINGS} | \${MEETINGS_PER_DAY} | \${MEETINGS_PER_DEAL} |
| **Total** | \${TOTAL_ACTIVITIES} | \${TOTAL_PER_DAY} | \${TOTAL_PER_DEAL} |

**Activity Efficiency**: $\${REVENUE_PER_ACTIVITY} revenue per activity

---

## 👥 Rep Performance

| Rep | Deals Won | Revenue | Avg Deal | Win Rate | Activities |
|-----|-----------|---------|----------|----------|------------|
${repPerformance.map(rep => \`| \${rep.name} | \${rep.dealsWon} | $\${rep.revenue.toLocaleString()} | $\${rep.avgDealSize.toLocaleString()} | \${rep.winRate}% | \${rep.activities} |\`).join('\\n')}

**Top Performer**: \${TOP_REP_NAME} ($\${TOP_REP_REVENUE.toLocaleString()})

---

## 📈 Trending

\`\`\`
Revenue Trend (Last 6 months)

$300K │                                      ●
      │                                   ●
$250K │                              ●
      │                          ●
$200K │                     ●
      │                ●
$150K │           ●
      │      ●
$100K │ ●
      │
   0K └──────────────────────────────────────
      M-5  M-4  M-3  M-2  M-1  Now
\`\`\`

**Trend**: \${TREND} (\${TREND_PCT}% vs 6-month avg)

---

## ⚡ Key Insights

### Wins 🎉
${generateWins(metrics)}

### Areas for Improvement 🎯
${generateImprovements(metrics)}

### Action Items 📋
1. \${ACTION_1}
2. \${ACTION_2}
3. \${ACTION_3}

---

## 🎯 Goals vs Actual

| Goal | Target | Actual | Variance | Status |
|------|--------|--------|----------|--------|
| Revenue | $\${REVENUE_TARGET} | $\${REVENUE_ACTUAL} | \${REVENUE_VARIANCE}% | \${REVENUE_STATUS} |
| New Deals | \${DEALS_TARGET} | \${DEALS_ACTUAL} | \${DEALS_VARIANCE} | \${DEALS_STATUS} |
| Win Rate | \${WIN_RATE_TARGET}% | \${WIN_RATE_ACTUAL}% | \${WIN_RATE_VARIANCE}% | \${WIN_RATE_STATUS} |
| Activities | \${ACTIVITIES_TARGET} | \${ACTIVITIES_ACTUAL} | \${ACTIVITIES_VARIANCE} | \${ACTIVITIES_STATUS} |

---

**Next Review**: \${NEXT_REVIEW_DATE}
**Dashboard**: [View in Zoho Analytics](https://analytics.zoho.com)
\`\`\`

Save to: sales-analytics/metrics-\${PERIOD}-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# This month metrics
/sales/metrics

# This week metrics
/sales/metrics --period this-week

# Quarterly metrics
/sales/metrics --period this-quarter

# Annual metrics
/sales/metrics --period this-year
```

## Key Performance Indicators

### Revenue KPIs

- **MRR Growth**: Target >10% month-over-month
- **ARR**: Target $1M+ (varies by company)
- **Quota Attainment**: Target 100%+

### Pipeline KPIs

- **Pipeline Coverage**: Target 3-4x quota
- **Pipeline Velocity**: Higher is better ($ per day)
- **Pipeline Quality**: Target >80/100

### Conversion KPIs

- **Lead → Opportunity**: Target >30%
- **Opportunity → Win**: Target >30%
- **Overall (Lead → Win)**: Target >10%

### Activity KPIs

- **Activities per Won Deal**: Target 15-25
- **Revenue per Activity**: Higher is better
- **Meetings per Week**: Target 10-15 per rep

### Deal KPIs

- **Average Deal Size**: Track growth over time
- **Sales Cycle**: Target <60 days
- **Win Rate**: Target >30%

## Success Criteria

- ✓ All revenue metrics calculated
- ✓ Pipeline health assessed
- ✓ Conversion rates tracked
- ✓ Activity metrics aggregated
- ✓ Rep performance analyzed
- ✓ Trends identified
- ✓ Action items generated
- ✓ Dashboard saved

## Benchmarks

**SaaS Industry Benchmarks**:

- MRR Growth: 10-20% per month (early stage)
- Win Rate: 25-35%
- Sales Cycle: 45-90 days (SMB), 90-180 days (Enterprise)
- Pipeline Coverage: 3-5x quota
- Lead Conversion: 20-40%

---
**Uses**: agent-router (Zoho CRM, analytics)
**Output**: Comprehensive KPI dashboard with trends and insights
**Next Commands**: `/sales/pipeline` (drill into bottlenecks), `/sales/forecast` (revenue projections)
**Update Frequency**: Weekly or monthly recommended
