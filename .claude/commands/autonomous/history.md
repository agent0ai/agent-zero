---
description: View decision audit trail with filtering and approval actions
argument-hint: "[<decision-id>] [--domain <domain>] [--status pending|completed|failed] [--approve] [--reject]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, AskUserQuestion
---

# Decision History

View the complete audit trail of autonomous decisions with filtering, approval actions, and outcome tracking.

## Execution Steps

### 1. Parse Arguments

Options:

- **decision-id**: Optional - view specific decision details
- **--domain**: Filter by domain
- **--status**: Filter by status (pending, completed, failed, all)
- **--period**: Time period (today, week, month)
- **--type**: Decision type filter
- **--approve**: Approve a pending decision
- **--reject**: Reject a pending decision with reason

### 2. Single Decision View

When decision-id provided:

```
═══════════════════════════════════════════════════════════════════════════════
                         DECISION DETAILS
═══════════════════════════════════════════════════════════════════════════════

Decision ID:    dec_xyz789
Created:        2025-01-15T14:30:00Z (2 hours ago)
Status:         ✓ COMPLETED

───────────────────────────────────────────────────────────────────────────────
CONTEXT
───────────────────────────────────────────────────────────────────────────────

Type:           intervention
Domain:         customer_success
Target:         Acme Corp (cust_abc123)

Question:
  Should we trigger intervention for this customer?

Input Signals:
  • Health score dropped to 48 (from 68)
  • Usage declined 40% over 7 days
  • NPS score: 5 (detractor)
  • 4 open support tickets

───────────────────────────────────────────────────────────────────────────────
OPTIONS EVALUATED
───────────────────────────────────────────────────────────────────────────────

1. ✓ [SELECTED] Trigger immediate intervention
   Risk Score: 35
   Confidence: 82%
   Reasoning: Fastest time to action, 72% historical success rate

2. ○ Continue monitoring
   Risk Score: 45
   Confidence: 68%
   Reasoning: Lower cost but risk of delayed action

3. ○ Automated outreach
   Risk Score: 25
   Confidence: 75%
   Reasoning: Low cost but may not be sufficient

───────────────────────────────────────────────────────────────────────────────
RISK ASSESSMENT
───────────────────────────────────────────────────────────────────────────────

Overall Risk Score: 37.35 (Low-Medium)

Factor                  Weight    Value    Contribution
─────────────────────────────────────────────────────────
Financial Impact        0.20      45       9.0
Customer Count          0.15      30       4.5
Data Scope              0.15      40       6.0
Reversibility           0.15      20       3.0
Compliance Impact       0.10      10       1.0
Security Impact         0.10      15       1.5
Confidence Score        0.05      82       4.1
Data Quality            0.05      90       4.5
Precedent Count         0.05      75       3.75
─────────────────────────────────────────────────────────
TOTAL                                      37.35

───────────────────────────────────────────────────────────────────────────────
DECISION
───────────────────────────────────────────────────────────────────────────────

Autonomy Level:   FULLY_AUTONOMOUS
Chosen Option:    Trigger immediate intervention
Confidence:       82%

Reasoning:
  Customer health dropped significantly (48) with high churn risk (72%).
  Usage decline of 40% combined with NPS detractor status indicates
  serious engagement issues. Similar patterns in past led to churn
  68% of the time without intervention. Immediate intervention has
  72% success rate for this profile.

───────────────────────────────────────────────────────────────────────────────
EXECUTION
───────────────────────────────────────────────────────────────────────────────

Executed At:      2025-01-15T14:30:05Z
Duration:         4.2 seconds

Actions Taken:
  ✓ 14:30:05 - Triggered playbook: at-risk-intervention
  ✓ 14:30:06 - Assigned CSM: Sarah Johnson
  ✓ 14:30:07 - Created task: Urgent check-in call
  ✓ 14:30:08 - Sent notification to #customer-health
  ✓ 14:30:09 - Logged to audit trail

───────────────────────────────────────────────────────────────────────────────
OUTCOME TRACKING
───────────────────────────────────────────────────────────────────────────────

Current Status:   In Progress
Playbook Status:  Step 3 of 6

Progress:
  ✓ Step 1: CSM Alert (completed 2h ago)
  ✓ Step 2: Executive Email (opened, replied)
  ⏳ Step 3: Recovery Call (scheduled for tomorrow)
  ○ Step 4: Health Check
  ○ Step 5: Success/Escalation
  ○ Step 6: Close Out

Customer Response:
  • Email opened and replied within 2 hours
  • Agreed to recovery call
  • Tone: Receptive

Interim Metrics:
  • Health Score: 48 → 52 (+4)
  • Engagement: 3 touchpoints since intervention
  • Support Tickets: 4 → 2 (2 resolved)

───────────────────────────────────────────────────────────────────────────────
AUDIT TRAIL
───────────────────────────────────────────────────────────────────────────────

Created By:       swarm_orchestrator (agent_master_001)
Approved By:      N/A (autonomous)
Reviewed By:      N/A

Related Decisions:
  • dec_xyz788: Previous health alert (7 days ago)
  • dec_xyz750: Last intervention for this customer (90 days ago)

Similar Decisions (Last 30 days):
  • 12 similar interventions triggered
  • 9 successful (75%)
  • 2 in progress
  • 1 unsuccessful (customer churned anyway)

═══════════════════════════════════════════════════════════════════════════════
```

### 3. List View

Default history view:

```
═══════════════════════════════════════════════════════════════════════════════
                         DECISION HISTORY
                         Last 24 Hours
═══════════════════════════════════════════════════════════════════════════════

Filter: All domains | All statuses | Last 24 hours
Total: 156 decisions

───────────────────────────────────────────────────────────────────────────────
PENDING APPROVAL (3)
───────────────────────────────────────────────────────────────────────────────

ID          Type                Target              Pending   Approvers
─────────────────────────────────────────────────────────────────────────────
dec_003     deprecation         Legacy API v1       2h 15m    product_lead,
                                                              engineering_lead
dec_004     deployment          api-service v2.5.0  48m       tech_lead
dec_005     contract-concession GlobalCo            33m       sales_director,
                                                              finance_lead

Actions:
  /autonomous:history dec_003 --approve
  /autonomous:history dec_004 --reject --reason "Need more testing"

───────────────────────────────────────────────────────────────────────────────
REVIEW REQUIRED (8)
───────────────────────────────────────────────────────────────────────────────

ID          Type                 Target              Executed   Status
─────────────────────────────────────────────────────────────────────────────
dec_015     deployment_strategy  AI Dashboard        45m ago    ✓ Awaiting review
dec_018     playbook_selection   TechStart Inc       1h ago     ✓ Awaiting review
dec_022     priority_change      CompetitorX alert   2h ago     ✓ Awaiting review
...

───────────────────────────────────────────────────────────────────────────────
COMPLETED (142)
───────────────────────────────────────────────────────────────────────────────

ID          Type                  Target              Time       Outcome
─────────────────────────────────────────────────────────────────────────────
dec_xyz789  intervention_trigger  Acme Corp           2h ago     ✓ In progress
dec_xyz788  intervention_trigger  TechStart Inc       2h ago     ✓ Completed
dec_xyz787  priority_change       AI Dashboard        3h ago     ✓ Completed
dec_xyz786  priority_change       CompetitorX         3h ago     ✓ Completed
dec_xyz785  playbook_selection    InnovateCorp        4h ago     ✓ Completed
dec_xyz784  intervention_trigger  GlobalCo            4h ago     ✓ Completed
dec_xyz783  deployment_strategy   Mobile App v2       5h ago     ✓ Completed
dec_xyz782  deployment_strategy   api-service v2.4.9  6h ago     ✓ Approved
...

Showing 20 of 142. Use --limit to see more.

───────────────────────────────────────────────────────────────────────────────
FAILED (3)
───────────────────────────────────────────────────────────────────────────────

ID          Type                  Target              Time       Error
─────────────────────────────────────────────────────────────────────────────
dec_xyz770  playbook_selection    OldCorp             8h ago     ✗ Customer deleted
dec_xyz755  intervention_trigger  TestAccount         12h ago    ✗ Timeout
dec_xyz742  deployment_strategy   staging-test        18h ago    ✗ Gate failure

───────────────────────────────────────────────────────────────────────────────
SUMMARY STATISTICS
───────────────────────────────────────────────────────────────────────────────

By Autonomy Level:
  Fully Autonomous:    142  (91.0%)
  Review Required:     11   (7.1%)
  Approval Required:   3    (1.9%)

By Domain:
  Customer Success:    89   (57.1%)
  Feature Lifecycle:   34   (21.8%)
  Market Intelligence: 21   (13.5%)
  DevOps Pipeline:     12   (7.7%)

Success Rate:          94.2% (142/151 non-pending)
Avg Decision Time:     2.3 seconds
Avg Execution Time:    4.8 seconds

═══════════════════════════════════════════════════════════════════════════════
```

### 4. Approval Action

When `--approve` specified:

```
/autonomous:history dec_003 --approve

═══════════════════════════════════════════════════════════
                    APPROVING DECISION
═══════════════════════════════════════════════════════════

Decision ID:    dec_003
Type:           feature_deprecation
Target:         Legacy API v1 (feat_legacy_api)

Description:
  Initiate deprecation announcement for Legacy API v1.
  47 customers affected, migration support planned.

Risk Score:     58 (Medium)
Confidence:     78%

Current Approvals:
  ✓ product_lead (approved 10m ago)
  ⏳ engineering_lead (you are approving)
  ⏳ cs_lead (pending)

─────────────────────────────────────────────────────────────

You are approving as: engineering_lead

Add comment (optional): Reviewed migration plan, LGTM

─────────────────────────────────────────────────────────────

✓ Approval recorded

Status:
  ✓ product_lead
  ✓ engineering_lead (you, just now)
  ⏳ cs_lead (1 approval remaining)

Decision will execute when all approvals received.

═══════════════════════════════════════════════════════════
```

### 5. Rejection Action

When `--reject` specified:

```
/autonomous:history dec_004 --reject --reason "Need load testing results"

═══════════════════════════════════════════════════════════
                    REJECTING DECISION
═══════════════════════════════════════════════════════════

Decision ID:    dec_004
Type:           deployment_strategy
Target:         api-service v2.5.0

⚠️  This will REJECT the decision and block execution.

Reason provided: "Need load testing results"

─────────────────────────────────────────────────────────────

✗ Decision Rejected

Status:         REJECTED
Rejected By:    tech_lead
Reason:         Need load testing results

Next Steps:
  • Requestor notified
  • Can resubmit after addressing concerns
  • Rejection logged to audit trail

═══════════════════════════════════════════════════════════
```

### 6. Filtering Options

Examples:

```bash
# Show only pending decisions
/autonomous:history --status pending

# Show customer success decisions
/autonomous:history --domain customer_success

# Show this week's decisions
/autonomous:history --period week

# Show failed decisions
/autonomous:history --status failed

# Show deployment decisions
/autonomous:history --type deployment

# Combine filters
/autonomous:history --domain devops --status completed --period week
```

### 7. Export Options

```bash
# Export to JSON
/autonomous:history --export decisions-2025-01-15.json

# Export to CSV
/autonomous:history --export decisions.csv --format csv
```

## Outcome Tracking

For completed decisions, track outcomes:

```yaml
outcome_tracking:
  decision_id: "dec_xyz789"
  predicted_outcome: "successful_intervention"
  actual_outcome: "successful"  # To be updated
  outcome_date: null  # When outcome confirmed
  confidence_adjustment: null  # Learning feedback
  notes: null
```

## Learning Integration

System learns from decision outcomes:

- Successful patterns reinforced
- Failed patterns analyzed
- Risk weights adjusted
- Confidence calibrated

## API Integration

### 1. Get Decision List

```bash
# Get all decisions with optional filters
# Note: Use valid workspace UUID for database queries, "default" for mock responses
curl -s -X GET "http://localhost:3001/api/v1/autonomous/decisions?limit=50" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Filter by domain
curl -s -X GET "http://localhost:3001/api/v1/autonomous/decisions?domain=customer_success&limit=50" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Filter by decision type (see valid types below)
curl -s -X GET "http://localhost:3001/api/v1/autonomous/decisions?decisionType=intervention_trigger&limit=50" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Filter by status (pending, approved, rejected, executed)
curl -s -X GET "http://localhost:3001/api/v1/autonomous/decisions?status=pending&limit=50" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Filter by autonomy level
curl -s -X GET "http://localhost:3001/api/v1/autonomous/decisions?autonomyLevel=approval_required&limit=50" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Filter by date range
curl -s -X GET "http://localhost:3001/api/v1/autonomous/decisions?startDate=2025-01-01&endDate=2025-01-15&limit=50" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Valid decision types:
# intervention_trigger, playbook_selection, pricing_recommendation (customer_success)
# feature_deprecation (feature_lifecycle)
# deployment_strategy, rollback (devops_pipeline)
# architecture_choice, dependency_upgrade, refactor_scope, priority_change, resource_allocation (general)
# escalation, approval_bypass (cross_domain)
#
# Valid domains: customer_success, feature_lifecycle, market_intelligence, devops_pipeline, general, cross_domain
```

### 2. Get Single Decision Details

```bash
# Get full decision details including options, reasoning, and execution info
curl -s -X GET "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

Response includes:

- Decision context and question
- Options evaluated with risk scores
- Chosen option and reasoning
- Risk assessment factors
- Execution status and duration
- Approval status (if applicable)
- Outcome details (if recorded)

### 3. Approve Decision

```bash
# Approve a pending decision
# Note: approvedBy must be a valid user UUID from the users table
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID/approve" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "approvedBy": "20000000-0000-0000-0000-000000000001",
    "notes": "Reviewed and approved - LGTM"
  }' | jq .
```

### 4. Reject Decision

```bash
# Reject a pending decision
# Note: rejectedBy must be a valid user UUID from the users table
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID/reject" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "rejectedBy": "20000000-0000-0000-0000-000000000001",
    "reason": "Need load testing results before proceeding"
  }' | jq .
```

### 5. Execute Decision

```bash
# Execute an approved decision
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID/execute" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "chosenOptionIndex": 0,
    "reasoning": "Selected first option based on highest success probability"
  }' | jq .
```

### 6. Record Decision Outcome

```bash
# Record decision outcome (for learning)
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID/outcome" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "outcome": "successful",
    "details": "Customer responded positively, health score improved to 68",
    "metrics": {
      "healthScoreChange": 20,
      "responseTime": "2h",
      "customerSatisfaction": "positive"
    }
  }' | jq .
```

Outcome values: `successful`, `failed`, `rolled_back`, `cancelled`

### 7. Get Decision Statistics

```bash
# Get comprehensive decision statistics for period
curl -s -X GET "http://localhost:3001/api/v1/autonomous/stats?periodDays=30" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

Response includes:

- Total decisions count
- Breakdown by autonomy level (fullyAutonomous, reviewRequired, approvalRequired)
- Breakdown by outcome (successful, failed, pending)
- Autonomy rate percentage
- Success rate percentage
- Override rate percentage
- Average confidence score
- Average execution time
- Breakdown by domain and decision type

### 8. Get Decision Learning Metrics

```bash
# Get decision accuracy metrics from knowledge service
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/metrics/decisions?periodDays=30" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

### 9. Search Knowledge Base for Decision Patterns

```bash
# Search for decision patterns in knowledge base
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/search?query=decision%20intervention_trigger&category=decision&limit=10" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

### 10. Check Autonomous Service Health

```bash
# Check autonomous decisions service health
curl -s -X GET "http://localhost:3001/api/v1/autonomous/health" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/autonomous/decisions` | List decisions with filters |
| `GET /api/v1/autonomous/decisions/:id` | Get decision details |
| `POST /api/v1/autonomous/decisions/:id/approve` | Approve decision |
| `POST /api/v1/autonomous/decisions/:id/reject` | Reject decision |
| `POST /api/v1/autonomous/decisions/:id/execute` | Execute decision |
| `POST /api/v1/autonomous/decisions/:id/outcome` | Record outcome |
| `GET /api/v1/autonomous/stats` | Decision statistics |
| `GET /api/v1/autonomous/health` | Service health check |
| `GET /api/v1/swarm-knowledge/metrics/decisions` | Learning metrics |
| `GET /api/v1/swarm-knowledge/search` | Search patterns |

## Error Handling

| Error | Resolution |
|-------|------------|
| Decision not found | Verify decision ID |
| Not authorized to approve | Check permissions |
| Already decided | Cannot change completed decisions |
| Approval expired | Decision may need resubmission |
| Invalid status filter | Use: pending, completed, failed, all |
| Export too large | Use smaller time period |

---

**Uses**: DecisionClassifier, SwarmKnowledgeService, ApprovalWorkflow
**Model**: Sonnet (history analysis)
