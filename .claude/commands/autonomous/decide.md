---
description: Make an autonomous decision with full reasoning and audit trail
argument-hint: "<decision-type> --target <id> [--context <json>] [--force-level <autonomous|review|approval>]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, AskUserQuestion, Task
---

# Autonomous Decision

Execute the autonomous decision-making framework to evaluate options, calculate risk, and take appropriate action.

## Decision Types

| Type | Domain | Description |
|------|--------|-------------|
| `intervention_trigger` | customer_success | Trigger customer intervention (at-risk, churn prevention) |
| `playbook_selection` | customer_success | Select and execute appropriate playbook |
| `pricing_recommendation` | customer_success | Recommend pricing or contract changes |
| `feature_deprecation` | feature_lifecycle | Initiate feature sunset/deprecation workflow |
| `deployment_strategy` | devops_pipeline | Approve/configure deployment approach |
| `rollback` | devops_pipeline | Execute emergency rollback |
| `architecture_choice` | general | Select architectural approach or pattern |
| `dependency_upgrade` | general | Approve dependency version upgrades |
| `refactor_scope` | general | Define scope of refactoring effort |
| `priority_change` | general | Change task/feature priority |
| `resource_allocation` | general | Allocate team or compute resources |
| `escalation` | cross_domain | Escalate to human decision-maker |
| `approval_bypass` | cross_domain | Request bypass of standard approval flow |

**Valid Domains:** `customer_success`, `feature_lifecycle`, `market_intelligence`, `devops_pipeline`, `general`, `cross_domain`

## Execution Steps

### 1. Parse Decision Request

Extract:

- **decision-type**: Required - type of decision to make
- **--target**: Required - target entity ID
- **--context**: Optional - additional context as JSON
- **--force-level**: Optional - override autonomy calculation

### 2. Gather Decision Context

Collect relevant data:

```yaml
context_gathering:
  target_data:
    - Load target entity details
    - Fetch current state
    - Get historical data

  signals:
    - Active alerts for target
    - Related signals from other domains
    - Correlated patterns

  constraints:
    - Active policies
    - Resource availability
    - Pending dependencies
```

### 3. Evaluate Options

Generate and score options:

```yaml
options_evaluation:
  option_1:
    id: "opt_immediate_intervention"
    description: "Trigger immediate intervention"
    risk_score: 35
    confidence: 0.82
    pros:
      - "Fastest time to action"
      - "High success probability"
    cons:
      - "Higher resource cost"
      - "May be unnecessary"

  option_2:
    id: "opt_wait_and_monitor"
    description: "Continue monitoring, act if worse"
    risk_score: 45
    confidence: 0.68
    pros:
      - "Lower cost"
      - "Avoids false positive"
    cons:
      - "Risk of delayed action"
      - "Customer may churn"

  option_3:
    id: "opt_automated_outreach"
    description: "Send automated check-in email"
    risk_score: 25
    confidence: 0.75
    pros:
      - "Low cost"
      - "Non-intrusive"
    cons:
      - "May not be sufficient"
```

### 4. Calculate Risk Score

Apply 10-factor weighted algorithm:

```
Risk Score Calculation:

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
TOTAL RISK SCORE                           37.35

Classification: LOW-MEDIUM
Autonomy Level: FULLY_AUTONOMOUS
```

### 5. Determine Autonomy Level

Based on risk score:

```
Risk Score    Autonomy Level      Action
──────────────────────────────────────────────
0-30          FULLY_AUTONOMOUS    Execute immediately
31-60         REVIEW_REQUIRED     Execute, queue review
61-85         APPROVAL_REQUIRED   Block until approved
86-100        ESCALATION          Escalate to executive
```

### 6. Execute Decision

**If FULLY_AUTONOMOUS:**

```
Executing Decision...

Decision: Trigger intervention for customer cust_abc123
Type:     intervention_trigger
Target:   Acme Corp (cust_abc123)
Action:   Execute playbook 'at-risk-intervention'

[1/4] Creating playbook execution...     ✓
[2/4] Assigning to CSM (Sarah Johnson)... ✓
[3/4] Sending notification...            ✓
[4/4] Logging decision to audit trail... ✓

Decision Executed Successfully ✓
```

**If REVIEW_REQUIRED:**

```
Decision Executed (Pending Review)

Decision: Progress rollout to 50%
Target:   AI Dashboard (feat_abc)
Status:   ✓ Executed (Review Required)

Review Queue:
  Reviewer:  tech_lead
  Due:       2025-01-15T18:00:00Z
  Priority:  Medium

To approve: /autonomous:history --approve dec_xyz789
```

**If APPROVAL_REQUIRED:**

```
Decision Blocked (Approval Required)

Decision: Deprecation announcement for Legacy API v1
Target:   feat_legacy_api (feat_xyz)
Status:   ⏳ Pending Approval

Required Approvers:
  □ product_lead
  □ engineering_lead
  □ cs_lead

To approve: /autonomous:history --approve dec_xyz789
```

### 7. Generate Decision Record

```yaml
decision_record:
  decision_id: "dec_xyz789"
  decision_type: "intervention_trigger"
  domain: "customer_success"

  question: "Should we trigger intervention for Acme Corp?"

  target:
    type: "customer"
    id: "cust_abc123"
    name: "Acme Corp"

  context:
    health_score: 48
    churn_risk: 72
    arr: 48000
    recent_signals:
      - "Usage declined 40%"
      - "Support tickets increasing"
      - "NPS dropped to 5"

  options_evaluated:
    - id: "opt_1"
      description: "Trigger immediate intervention"
      risk_score: 35
      recommended: true
    - id: "opt_2"
      description: "Continue monitoring"
      risk_score: 45
      recommended: false
    - id: "opt_3"
      description: "Automated outreach"
      risk_score: 25
      recommended: false

  chosen_option: "opt_1"

  reasoning: |
    Customer health dropped significantly (48) with high churn risk (72%).
    Usage decline of 40% combined with NPS detractor status indicates
    serious engagement issues. Similar patterns in past led to churn
    68% of the time without intervention. Immediate intervention has
    72% success rate for this profile.

  risk_assessment:
    score: 37.35
    level: "low-medium"
    factors:
      - name: "financial_impact"
        value: 48000
        contribution: 9.0
      - name: "customer_count"
        value: 1
        contribution: 4.5
      # ... other factors

  autonomy_level: "fully_autonomous"
  confidence_score: 0.82

  execution:
    status: "completed"
    executed_at: "2025-01-15T14:30:00Z"
    actions_taken:
      - "Playbook 'at-risk-intervention' triggered"
      - "CSM Sarah Johnson assigned"
      - "First outreach scheduled"

  audit:
    created_at: "2025-01-15T14:30:00Z"
    created_by: "swarm_orchestrator"
    reviewed_by: null
    approved_by: null
```

### 8. Display Summary

```
═══════════════════════════════════════════════════════════
                    DECISION SUMMARY
═══════════════════════════════════════════════════════════

Decision ID:    dec_xyz789
Type:           intervention_trigger
Target:         Acme Corp (cust_abc123)

─────────────────────────────────────────────────────────────
ANALYSIS
─────────────────────────────────────────────────────────────

Question: Should we trigger intervention for this customer?

Options Considered:
  ✓ [SELECTED] Trigger immediate intervention (risk: 35)
    - Fastest time to action
    - 72% historical success rate
  ○ Continue monitoring (risk: 45)
    - Risk of delayed action
  ○ Automated outreach (risk: 25)
    - May not be sufficient

Risk Assessment:
  Score:      37.35 (Low-Medium)
  Confidence: 82%

─────────────────────────────────────────────────────────────
DECISION
─────────────────────────────────────────────────────────────

Autonomy Level: FULLY_AUTONOMOUS
Decision:       Execute intervention
Status:         ✓ COMPLETED

Reasoning:
  Customer health dropped significantly (48) with high churn risk
  (72%). Usage decline of 40% combined with NPS detractor status
  indicates serious engagement issues. Immediate intervention
  recommended based on 72% historical success rate.

─────────────────────────────────────────────────────────────
ACTIONS TAKEN
─────────────────────────────────────────────────────────────

✓ Triggered playbook: at-risk-intervention
✓ Assigned CSM: Sarah Johnson
✓ Scheduled first outreach: 2025-01-15T15:00:00Z
✓ Created audit trail entry

─────────────────────────────────────────────────────────────

View history: /autonomous:history dec_xyz789

═══════════════════════════════════════════════════════════
```

## API Integration

### 1. Create Decision Request

```bash
# Create a new decision with automatic risk scoring and classification
# Note: x-workspace-id must be a valid UUID for database persistence
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "decisionType": "intervention_trigger",
    "domain": "customer_success",
    "question": "Should we trigger intervention for TechStart Inc?",
    "targetId": "cust_techstart_001",
    "targetType": "customer",
    "context": {
      "healthScore": 48,
      "churnRisk": 72,
      "arr": 48000
    },
    "forceLevel": "approval_required"
  }' | jq .

# Valid decision types:
# - intervention_trigger, playbook_selection, pricing_recommendation (customer_success)
# - feature_deprecation (feature_lifecycle)
# - deployment_strategy, rollback (devops_pipeline)
# - architecture_choice, dependency_upgrade, refactor_scope, priority_change, resource_allocation (general)
# - escalation, approval_bypass (cross_domain)
#
# Valid domains: customer_success, feature_lifecycle, market_intelligence, devops_pipeline, general, cross_domain
```

Response includes:

- Decision ID
- Calculated risk score
- Autonomy level classification
- Generated options
- Requires approval flag

### 2. Get Related Signals

```bash
# Get related domain signals for context
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/signals?limit=10" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

### 3. Execute Decision

```bash
# Execute the decision (for autonomous or approved decisions)
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID/execute" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "chosenOptionIndex": 0,
    "reasoning": "Customer health dropped significantly with high churn risk. Immediate intervention recommended."
  }' | jq .
```

### 4. Approve Decision (if approval required)

```bash
# Approve a pending decision
# Note: approvedBy must be a valid user UUID from the users table
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID/approve" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "approvedBy": "20000000-0000-0000-0000-000000000001",
    "notes": "Approved for execution"
  }' | jq .
```

### 5. Reject Decision (if needed)

```bash
# Reject a pending decision
# Note: rejectedBy must be a valid user UUID from the users table
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID/reject" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "rejectedBy": "20000000-0000-0000-0000-000000000001",
    "reason": "Insufficient data for this decision"
  }' | jq .
```

### 6. Record Outcome

```bash
# Record the outcome of an executed decision
curl -s -X POST "http://localhost:3001/api/v1/autonomous/decisions/$DECISION_ID/outcome" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "outcome": "successful",
    "details": "Customer responded positively, health score improved from 42 to 58",
    "metrics": {
      "healthScoreChange": 16,
      "responseTime": "4h",
      "customerSatisfaction": "positive"
    }
  }' | jq .

# Valid outcome values: successful, failed, rolled_back, cancelled
```

### 7. Record Decision to Knowledge Base

```bash
# Record decision as knowledge entry for learning
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "category": "decision",
    "subcategory": "intervention_trigger",
    "tags": ["autonomous", "intervention_trigger", "customer_success"],
    "title": "Decision: intervention_trigger for cust_techstart_001",
    "content": "Customer health dropped significantly with high churn risk. Immediate intervention recommended.",
    "structuredData": {
      "decisionId": "'$DECISION_ID'",
      "riskScore": 65,
      "autonomyLevel": "approval_required",
      "chosenOption": "opt_1",
      "outcome": "successful"
    },
    "source": {
      "type": "autonomous_decision",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "confidence": 84
    }
  }' | jq .
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/autonomous/decisions` | Create decision with auto risk scoring |
| `GET /api/v1/autonomous/decisions` | List decisions with filtering |
| `GET /api/v1/autonomous/decisions/:id` | Get specific decision |
| `POST /api/v1/autonomous/decisions/:id/execute` | Execute decision |
| `POST /api/v1/autonomous/decisions/:id/approve` | Approve pending decision |
| `POST /api/v1/autonomous/decisions/:id/reject` | Reject pending decision |
| `POST /api/v1/autonomous/decisions/:id/outcome` | Record outcome |
| `GET /api/v1/cross-domain/signals` | Get related signals |
| `POST /api/v1/swarm-knowledge` | Record to knowledge base |

## Error Handling

| Error | Resolution |
|-------|------------|
| Invalid decision type | Use supported decision type |
| Target not found | Verify target ID exists |
| Insufficient data | Gather more context |
| Conflicting decisions | Resolve conflicts first |
| Approval timeout | Escalate or retry |
| Risk score too high | Requires human approval |

---

**Uses**: RiskScoringEngine, DecisionClassifier, CrossDomainIntelligence, SwarmKnowledgeService
**Model**: Sonnet (decision reasoning)
