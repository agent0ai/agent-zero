---
description: Monitor automation performance with real-time success rates, execution metrics, and intelligent alerts
argument-hint: [--workflow name] [--period 24h|7d|30d] [--metric execution|success|speed|errors] [--dashboard]
model: claude-3-5-haiku-20241022
allowed-tools: Bash, AskUserQuestion
---

# Automation Performance Monitoring

Real-time monitoring dashboard for all your automated workflows with alerts, analytics, and performance optimization recommendations.

## Step 1: Determine Monitoring View

Choose what to monitor:

**Viewing Options**:

1. **Overview Dashboard**: All workflows at a glance
2. **Workflow Details**: Drill into specific workflow
3. **Time Period Analysis**: 24 hours, 7 days, 30 days, custom
4. **Performance Metrics**: Execution speed, success rate, errors
5. **Alert Management**: See and configure alerts
6. **Trending Analysis**: Performance trends and anomalies
7. **Cost Analytics**: Task usage, cost per workflow

## Step 2: Display Overview Dashboard

Get high-level view of all automations:

```
═══════════════════════════════════════════════════════════════
                 AUTOMATION MONITORING DASHBOARD
═══════════════════════════════════════════════════════════════

Time Period: Last 24 hours | [7 days] [30 days] [Custom]

SYSTEM HEALTH: ✓ EXCELLENT (99.8%)

Summary Metrics:
┌──────────────────────────────────────────────────────────┐
│ Total Workflows: 12 (all active)                         │
│ Total Executions: 2,847                                  │
│ Success Rate: 99.8% (2,843/2,847)                       │
│ Failed Executions: 4 (0.2%)                              │
│ Avg Execution Time: 1.2 seconds                          │
│ P95 Execution Time: 3.8 seconds                          │
│ P99 Execution Time: 5.2 seconds                          │
└──────────────────────────────────────────────────────────┘

ACTIVE ALERTS: 1 ⚠️
  ⚠️ HIGH LATENCY: "Rent Collection" averaging 4.2s (target: 2s)
     Recommendation: Check Zoho CRM API performance
     Action: [View Details] [Acknowledge] [Create Ticket]

═══════════════════════════════════════════════════════════════

YOUR WORKFLOWS:

┌──────────────────────────────────────────────────────────┐
│ 1. PROPERTY LEAD AUTOMATION                              │
├──────────────────────────────────────────────────────────┤
│ Status: ✓ HEALTHY                                        │
│ Executions (24h): 847                                    │
│ Success Rate: 99.9% (846/847)                           │
│ Failed: 1 | Warnings: 0                                  │
│ Avg Time: 0.9s | P95: 2.4s                              │
│ Last Run: 2 minutes ago (SUCCESS)                        │
│ Trend: ↗ Improving (98% → 99.9% over 7d)               │
│                                                          │
│ [Details] [View Logs] [Performance] [Alerts]             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 2. MAINTENANCE REQUEST WORKFLOW                          │
├──────────────────────────────────────────────────────────┤
│ Status: ✓ HEALTHY                                        │
│ Executions (24h): 423                                    │
│ Success Rate: 99.8% (422/423)                           │
│ Failed: 1 | Warnings: 2                                  │
│ Avg Time: 1.8s | P95: 4.1s                              │
│ Last Run: 15 minutes ago (SUCCESS)                       │
│ Trend: → Stable (99.7-99.9% over 7d)                    │
│                                                          │
│ [Details] [View Logs] [Performance] [Alerts]             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 3. RENT COLLECTION AUTOMATION                            │
├──────────────────────────────────────────────────────────┤
│ Status: ⚠️ WARNING (High Latency)                        │
│ Executions (24h): 156                                    │
│ Success Rate: 99.4% (155/156)                           │
│ Failed: 1 | Warnings: 8                                  │
│ Avg Time: 4.2s | P95: 8.1s (⚠️ High)                    │
│ Last Run: 3 minutes ago (SUCCESS - slow)                 │
│ Trend: ↘ Degrading (3.1s → 4.2s over 7d)              │
│                                                          │
│ Alert: Zoho CRM API latency increased 35%               │
│ Recommendation: Review API rate limits, consider caching │
│                                                          │
│ [Details] [View Logs] [Performance] [Optimize]           │
└──────────────────────────────────────────────────────────┘

[Show More Workflows] (9 more)
```

## Step 3: View Detailed Workflow Metrics

Deep dive into specific workflow performance:

```
═══════════════════════════════════════════════════════════════
              WORKFLOW DETAILS: Property Lead Automation
═══════════════════════════════════════════════════════════════

Overview:
  Status: ✓ HEALTHY
  Created: 2025-01-01
  Last Modified: 2025-01-15
  Last Execution: 2025-01-15 14:32:15 UTC (2 minutes ago)

Execution Metrics (24 hours):
┌──────────────────────────────────────────────────────────┐
│ Total Executions: 847                                    │
│ Successful: 846 (99.9%)                                  │
│ Failed: 1 (0.1%)                                         │
│ Warnings: 0                                              │
│ Retried: 0 (no failures needed retry)                    │
│                                                          │
│ Average Execution Time: 0.9 seconds                      │
│ Median Execution Time: 0.8 seconds                       │
│ Min: 0.3s | Max: 4.8s                                   │
│ P50 (median): 0.8s                                       │
│ P95: 2.4s (95% complete within this time)               │
│ P99: 3.8s (99% complete within this time)               │
│                                                          │
│ Execution Rate: 35 executions/hour (steady)              │
│ Peak Hour: 14:00 UTC (47 executions)                     │
│ Off-Peak Hour: 02:00 UTC (8 executions)                 │
└──────────────────────────────────────────────────────────┘

Detailed Metrics by Step:
```

| Step | Name | Executions | Success | Avg Time | Issues |
|------|------|------------|---------|----------|--------|
| 1 | Webhook | 847 | 100% | 0.1s | 0 |
| 2 | Validate Input | 847 | 100% | 0.1s | 0 |
| 3 | CRM: Create Lead | 847 | 99.9% | 0.4s | 1 timeout |
| 4 | Email: Welcome | 846 | 99.9% | 0.2s | 0 |
| 5 | Slack: Notify | 846 | 100% | 0.1s | 0 |

```

Success Breakdown:
```

✓ Success: 846 executions

- Completed normally: 846 (99.9%)

✗ Failed: 1 execution

- CRM API timeout: 1
    Error: Zoho CRM API took > 10s
    Time: 2025-01-15 09:47:22 UTC
    Recovery: Auto-retry succeeded (1.2s later)
    Impact: Lead created successfully after retry

⚠️ Warnings: 0

```

Execution Timeline (Last 24 hours):
```

Time  | Count | Success | Avg Time | Status
------|-------|---------|----------|-------
00:00 | 8     | 100%    | 0.8s     | ✓
01:00 | 12    | 100%    | 0.9s     | ✓
02:00 | 8     | 100%    | 0.7s     | ✓
...
12:00 | 41    | 99.2%   | 1.1s     | ⚠️ (1 timeout)
13:00 | 47    | 100%    | 0.9s     | ✓
14:00 | 39    | 100%    | 0.8s     | ✓

```

Traffic Distribution:
```

└─ Business Hours (8 AM - 6 PM): 62% of executions
   └─ Peak: 2-3 PM (187 total)
   └─ Avg Success: 99.8%

└─ Evening (6 PM - 12 AM): 25% of executions
   └─ Avg Success: 100%

└─ Night (12 AM - 8 AM): 13% of executions
   └─ Avg Success: 99.9%

```

═══════════════════════════════════════════════════════════════

Most Recent Executions:
```

Time | Status | Duration | Details
-----|--------|----------|--------
14:32 | ✓ SUCCESS | 0.8s | 2847 leads processed total
14:31 | ✓ SUCCESS | 0.9s | lead_id: L-456789
14:30 | ✓ SUCCESS | 0.7s | lead_id: L-456788
14:29 | ✓ SUCCESS | 1.1s | lead_id: L-456787
14:28 | ✓ SUCCESS | 0.8s | lead_id: L-456786

```

═══════════════════════════════════════════════════════════════
```

## Step 4: View Error Details & Analysis

See what's going wrong and get recommendations:

```
═══════════════════════════════════════════════════════════════
                    ERROR ANALYSIS (24h)
═══════════════════════════════════════════════════════════════

Total Errors: 4 across all workflows

ERROR BREAKDOWN BY WORKFLOW:
┌──────────────────────────────────────────────────────────┐
│ Property Lead Automation: 1 error                         │
│   • CRM API timeout (1)                                   │
│   • Error Rate: 0.1%                                      │
│   • Severity: Low (auto-recovered)                        │
│                                                          │
│ Maintenance Request: 1 error                              │
│   • Slack API timeout (1)                                │
│   • Error Rate: 0.2%                                      │
│   • Severity: Low (message queued, retried)               │
│                                                          │
│ Rent Collection: 2 errors                                │
│   • Zoho CRM: Rate limit exceeded (1)                    │
│   • Email service: Temporary failure (1)                 │
│   • Error Rate: 1.3%                                      │
│   • Severity: Medium (needs optimization)                │
└──────────────────────────────────────────────────────────┘

ERROR TIMELINE:
```

09:47 - CRM timeout (Property Lead Automation)
  Type: API Timeout
  Cause: Zoho CRM API slow response
  Recovery: Auto-retry succeeded (1.2s later)
  Impact: No data loss

12:34 - Slack timeout (Maintenance Request)
  Type: Network Timeout
  Cause: Slack API temporarily unavailable
  Recovery: Automatic retry in 30 seconds
  Impact: Notification delayed but sent

13:22 - Rate limit (Rent Collection)
  Type: Rate Limit Exceeded
  Cause: 156 simultaneous CRM queries
  Recovery: Exponential backoff, retry succeeded
  Impact: 30-second delay

15:01 - Email service error (Rent Collection)
  Type: Service Unavailable
  Cause: Email provider temporary outage
  Recovery: Queued for retry (automatic)
  Impact: Email delayed but will be sent

```

ERROR PATTERN ANALYSIS:
```

Patterns Detected:

  1. CRM API slow during 9-10 AM (after data refresh?)
     Recommendation: Optimize CRM queries, add caching

  2. Email service has ~1 error per 500 sends
     Current: 2 errors (1 recoverable, 1 sending queue)
     Action: Monitor and consider backup email service

  3. Slack has occasional timeouts
     Frequency: ~1 per 2000 messages (0.05%)
     Status: Acceptable, already handled with retry

Overall Error Health:
  ✓ 4 errors out of 2,847 executions = 0.2% error rate
  ✓ All errors recovered automatically or handled gracefully
  ✓ No data loss
  ✓ User impact: Minimal to none

```

RECOMMENDATIONS:
  1. Monitor CRM latency during 9-10 AM peak
  2. Consider bulk query optimization for Rent Collection
  3. Add email service backup for critical workflows
  4. Increase Slack message buffer (already done in Step 5a)
```

## Step 5: Performance Analysis & Optimization

Get speed and efficiency insights:

```
═══════════════════════════════════════════════════════════════
               PERFORMANCE & OPTIMIZATION ANALYSIS
═══════════════════════════════════════════════════════════════

EXECUTION SPEED COMPARISON:
┌──────────────────────────────────────────────────────────┐
│ Workflow | 24h Avg | 7d Avg | Trend | Target | Status  │
├──────────────────────────────────────────────────────────┤
│ Lead Automation | 0.9s | 0.8s | ↗ | 2s | ✓ EXCELLENT |
│ Maintenance | 1.8s | 1.9s | → | 3s | ✓ EXCELLENT |
│ Rent Collection | 4.2s | 3.1s | ↘ | 2s | ⚠️ DEGRADING |
│ ...more workflows | ... | ... | ... | ... | ... |
└──────────────────────────────────────────────────────────┘

BOTTLENECK ANALYSIS (Rent Collection - Slow Workflow):

Slowest Step Breakdown:
```

Step | Name | Executions | Avg | P95 | Max | Issue
-----|------|------------|-----|-----|-----|------
1 | Trigger | 156 | 0.1s | 0.1s | 0.2s | None
2 | CRM Query | 156 | 2.1s | 4.2s | 8.1s | ⚠️ SLOW
3 | Data Transform | 155 | 0.2s | 0.3s | 0.5s | None
4 | Stripe Payment | 155 | 0.8s | 1.5s | 2.1s | Okay
5 | Update CRM | 155 | 0.6s | 1.2s | 1.8s | Okay
6 | Send Email | 155 | 0.4s | 0.8s | 1.2s | Okay

```

ROOT CAUSE: CRM Query Step
```

Current Implementation:

- Query: "SELECT * FROM contacts WHERE rent_due = TODAY"
- Records returned: 150-200 per execution
- Processing time: 2.1s average
- API calls: 1 (good!)

Problems Identified:

  1. Query returns full contact records (unnecessary fields)
  2. No caching of results
  3. Run during peak hours (CRM server slow)
  4. Data transform on all fields (only need 5)

Optimization Recommendations:

  1. Use projection to select only needed fields (save 40%)
     FROM: SELECT *
     TO: SELECT id, name, email, phone, rent_amount
     Estimated Savings: 0.6-0.8s per execution

  2. Add 5-minute cache for rent due list
     Benefit: Eliminate redundant queries
     Estimated Savings: 0.3-0.5s (80% of cases)

  3. Schedule during off-peak hours
     Move from: Throughout day
     Move to: 2-4 AM daily (batch)
     Benefit: Eliminate latency concerns

  4. Use parallel processing for large batches
     Benefit: Process 200 records in parallel
     Estimated Savings: 0.4-0.7s

OPTIMIZATION IMPACT (Estimated):

```
Current: 4.2s average
  - Add field projection: -0.7s → 3.5s
  - Add caching: -0.4s → 3.1s
  - Schedule batch: 2.0-2.5s (isolated)
  - Parallel processing: -0.5s → 1.5-2.0s

Target After Optimization: 2.0s average

═══════════════════════════════════════════════════════════════

COST ANALYSIS (By Workflow):
```

Workflow | Monthly Tasks | Avg Cost | $/Task | Trend | Notes
---------|---------------|----------|--------|-------|--------
Lead Auto | 25,410 | $12.70 | $0.0005 | → | Efficient
Maintenance | 12,690 | $6.35 | $0.0005 | → | Efficient
Rent Collection | 4,680 | $2.34 | $0.0005 | → | Could optimize
...more | ... | ... | ... | ... | ...
TOTAL | 2,847,000 | $1,424 | $0.0005 | → | Great ROI

```

Potential Savings from Optimization:
  • Rent Collection Optimization: $0.60/day ($18/month)
  • All workflow improvements: $45-75/month
  • Improved user experience: Priceless!

═══════════════════════════════════════════════════════════════
```

## Step 6: Alerts & Notifications

Configure and manage alerts:

```
═══════════════════════════════════════════════════════════════
                     ALERT MANAGEMENT
═══════════════════════════════════════════════════════════════

ACTIVE ALERTS: 1

⚠️ HIGH LATENCY WARNING
   Workflow: Rent Collection Automation
   Metric: Avg execution time
   Current Value: 4.2s
   Threshold: 2.0s
   Triggered: 2025-01-15 13:22:15 UTC
   Duration: 1 hour 10 minutes (ongoing)
   Severity: MEDIUM
   Status: ALERTING (ongoing)

   Recommended Action:
   1. Review optimization recommendations above
   2. Optimize CRM query step
   3. Add caching layer
   4. Consider batch processing

   [View Details] [Acknowledge] [Snooze 1h] [Create Ticket]

════════════════════════════════════════════════════════════

ALERT CONFIGURATION:

Alert Type | Threshold | Channel | Status
-----------|-----------|---------|-------
Execution Failed | > 0 errors | Email, Slack | ✓ Enabled
High Latency | > 2.0s | Slack | ✓ Enabled
Success Rate | < 99% | Slack, PagerDuty | ✓ Enabled
Timeout | > 30s | Email (urgent) | ✓ Enabled
Rate Limited | Yes | Slack | ✓ Enabled
Custom Pattern | Defined | Selected | ✓ Enabled

NOTIFICATION CHANNELS:

Email:
  ✓ Enabled for: Critical failures, timeouts
  ✓ Recipient: ops-team@company.com
  ✓ Frequency: Immediate

Slack:
  ✓ Enabled for: All alerts
  ✓ Channel: #automation-alerts
  ✓ Frequency: Real-time

PagerDuty:
  ✓ Enabled for: Critical failures (< 99% success)
  ✓ Escalation: On-call engineer
  ✓ Frequency: Immediate

SMS:
  ✓ Enabled for: Critical system failures
  ✓ Recipients: Ops lead, Engineering manager
  ✓ Frequency: Critical only

Dashboard:
  ✓ Enabled: All workflows, all metrics
  ✓ Refresh: Real-time
  ✓ Retention: 90 days

[Add Alert] [Edit Alerts] [Test Notification]

════════════════════════════════════════════════════════════
```

## Step 7: Historical Trends & Analytics

Analyze long-term patterns:

```
═══════════════════════════════════════════════════════════════
               HISTORICAL TRENDS (30-Day View)
═══════════════════════════════════════════════════════════════

TREND CHARTS:

Success Rate Over Time:
```

100% ┌───────────────────────────────────────────────────┐
     │                                  ╱╲              │
99%  │       ╱╲      ╱╲         ╱╲    ╱  ╲    ╱╲       │
98%  │      ╱  ╲    ╱  ╲       ╱  ╲  ╱    ╲  ╱  ╲      │
97%  │────╱────╲──╱────╲─────╱────╲╱──────╲╱────╲──────│
     └───────────────────────────────────────────────────┘
     1  5  10  15  20  25  30
     Days

Average: 99.3%
Min: 97.1% (Jan 8 - Issue with CRM API)
Max: 99.9% (Jan 15 - Current)
Trend: ↗ Improving

```

Execution Speed Trend:
```

5s   ┌───────────────────────────────────────────────────┐
4s   │                                        ╱╲         │
3s   │             ╱╲              ╱╲   ╱╲  ╱  ╲        │
2s   │    ╱╲      ╱  ╲            ╱  ╲ ╱  ╲╱    ╲   ╱╲  │
1s   │───╱──╲────╱────╲──────────╱────╱────────╲─╱──╲──│
     └───────────────────────────────────────────────────┘
     1  5  10  15  20  25  30
     Days

Average: 1.8s
Min: 0.9s (Jan 12 - Optimized CRM query)
Max: 4.2s (Jan 15 - Current - High latency alert)
Trend: ↘ Degrading (needs attention)

```

Execution Volume by Hour (Pattern):
```

Peak Hours: 2-3 PM (40-50 executions/hour)
Off-Peak: 2-4 AM (5-10 executions/hour)
Weekend: 30% lower volume
Holiday: No automation run (scheduled pause)

```

Error Rate by Workflow (30 days):
```

Property Lead: 0.08% (10 errors / 12,410 executions)
Maintenance: 0.15% (7 errors / 4,620 executions)
Rent Collection: 1.25% (15 errors / 1,200 executions) ← Highest
Communication: 0.05% (2 errors / 4,050 executions)
Data Sync: 0.30% (5 errors / 1,670 executions)

```

═══════════════════════════════════════════════════════════════
```

## Step 8: Generate Reports

Export monitoring data:

```
═══════════════════════════════════════════════════════════════
              GENERATE PERFORMANCE REPORTS
═══════════════════════════════════════════════════════════════

Report Options:

☐ Executive Summary (1 page)
  - High-level metrics
  - Key findings
  - Recommendations

☑ Detailed Performance Report (10 pages)
  - All metrics by workflow
  - Error analysis
  - Performance trends
  - Optimization recommendations

☐ Cost Analysis Report (5 pages)
  - Task usage by workflow
  - Cost breakdowns
  - Cost optimization opportunities
  - ROI analysis

☐ Custom Report
  - Select metrics
  - Date range
  - Workflows included
  - Format (PDF, CSV, JSON)

Export Format:
  ⦿ PDF (formatted, ready to share)
  ○ CSV (data analysis in Excel)
  ○ JSON (programmatic access)
  ○ HTML (web view)

Date Range:
  ○ Last 24 hours
  ○ Last 7 days
  ○ Last 30 days
  ⦿ Last 90 days
  ○ Custom: [start] to [end]

Recipients:
  ☑ ops-team@company.com
  ☑ Include in Slack notification
  ☐ Schedule daily delivery
  ☐ Schedule weekly delivery

[Generate Report] [Preview] [Email Now] [Schedule]
```

## Step 9: Recommendations & Actions

Get AI-powered optimization suggestions:

```
═══════════════════════════════════════════════════════════════
           OPTIMIZATION RECOMMENDATIONS (AI-Generated)
═══════════════════════════════════════════════════════════════

HIGH PRIORITY:
1. Optimize Rent Collection Workflow
   Issue: Execution speed degrading (3.1s → 4.2s over 7 days)
   Root Cause: CRM query not optimized, no caching
   Estimated Benefit: Save 2.2s per execution (52% faster)
   Estimated Cost Savings: $18/month
   Effort: 30 minutes (easy)
   Impact: Medium (156 daily executions)

   Action Items:
   ☐ Add field projection to CRM query
   ☐ Implement 5-minute result caching
   ☐ Move execution to off-peak hours (2-4 AM)
   ☐ Test and monitor results

   [View Detailed Steps] [Create Task] [Auto-Fix]

2. Email Service Redundancy
   Issue: Email failures (1 error per 500 sends)
   Risk: Critical business process disruption
   Recommendation: Add fallback email service
   Implementation: 1 hour setup, $10/month additional
   Benefit: 99.99% email delivery guarantee

   [Learn More] [Implement]

MEDIUM PRIORITY:
3. CRM API Rate Limiting
   Issue: Peak hours causing rate limit errors
   Solution: Implement request queuing and batching
   Expected Impact: Eliminate rate limit errors
   Effort: 2 hours

   [View Details] [Implement]

4. Slack Integration Buffering
   Issue: Occasional Slack timeouts (0.05% error rate)
   Solution: Implement message queue
   Expected Impact: Zero timeouts
   Effort: 45 minutes

   [View Details] [Implement]

LOW PRIORITY:
5. Monitoring Dashboard Enhancement
   Issue: Dashboard could show more predictive analytics
   Recommendation: Add forecasting for peak usage
   Benefit: Better capacity planning
   Effort: 3 hours

   [View Details] [Implement]

═══════════════════════════════════════════════════════════════

OPTIMIZATION QUICK ACTIONS:

[1-Click: Optimize Rent Collection]
  → Applies CRM query optimization
  → Adds result caching
  → Monitors results
  → Rollback available if issues

[Auto-Fix Email Redundancy]
  → Enables secondary email service
  → Configures fallback logic
  → Tests failover
  → Activates with monitoring

[Enable Advanced Monitoring]
  → Adds predictive metrics
  → Enables trend forecasting
  → Creates custom dashboards
```

## Step 10: Scheduled Reports & Exports

Automate report delivery:

```
SCHEDULED REPORTS:

Daily Digest (9 AM):
  ✓ Enabled
  Recipients: ops-team@company.com
  Includes: Success rate, errors, performance summary
  Format: Email with inline charts

Weekly Report (Monday 8 AM):
  ✓ Enabled
  Recipients: ops-team@company.com, executives@company.com
  Includes: Full performance analysis, trends, recommendations
  Format: PDF (10 pages)

Monthly Business Review (1st of month, 10 AM):
  ✓ Enabled
  Recipients: C-suite, finance@company.com
  Includes: ROI, cost analysis, strategic recommendations
  Format: PowerPoint presentation

Custom Reports:
  ☐ On-demand export (CSV, JSON)
  ☐ Slack weekly notification
  ☐ SMS critical alerts

[Add Schedule] [Edit Schedule] [Preview Report]
```

---

**Uses**: monitoring-dashboard-agent, analytics-engine
**Model**: Haiku (fast metrics and alerts)
**Dashboard Refresh**: Real-time
**Data Retention**: 90 days detailed, 1 year aggregated
**Typical Analysis Time**: 2-5 minutes
