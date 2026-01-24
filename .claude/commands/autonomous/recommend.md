---
description: Get AI-powered recommendations based on current signals and patterns
argument-hint: "[--domain <domain>] [--target <id>] [--type strategic|tactical|operational]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Task
---

# Autonomous Recommendations

Generate AI-powered recommendations based on current signals, patterns, and cross-domain intelligence.

## Recommendation Types

| Type | Focus | Time Horizon |
|------|-------|--------------|
| `strategic` | Long-term initiatives, major decisions | Weeks to months |
| `tactical` | Specific actions, immediate improvements | Days to weeks |
| `operational` | Day-to-day optimizations | Hours to days |

## Execution Steps

### 1. Parse Request

Extract:

- **--domain**: Optional - focus on specific domain
- **--target**: Optional - recommendations for specific entity
- **--type**: strategic, tactical, or operational (default: all)

### 2. Analyze Current Signals

Collect active signals:

```yaml
signal_analysis:
  customer_success:
    active_signals: 23
    critical: 3
    high: 8
    medium: 12
    patterns:
      - "5 enterprise customers showing churn signals"
      - "Support ticket volume up 25%"
      - "NPS trending down in SMB segment"

  feature_lifecycle:
    active_signals: 8
    critical: 1
    high: 3
    medium: 4
    patterns:
      - "AI Dashboard adoption below target"
      - "Legacy API v1 usage declining"
      - "Mobile app feature requests increasing"

  market_intelligence:
    active_signals: 5
    critical: 1
    high: 2
    medium: 2
    patterns:
      - "CompetitorX launched AI analytics"
      - "Market trend: AI automation accelerating"
      - "Pricing pressure in mid-market"

  devops:
    active_signals: 2
    critical: 0
    high: 1
    medium: 1
    patterns:
      - "Deployment frequency increased 40%"
      - "Error rate stable but near threshold"
```

### 3. Correlate Cross-Domain Patterns

Identify connections:

```yaml
correlations:
  - pattern: "Enterprise churn + CompetitorX AI launch"
    domains: ["customer_success", "market_intelligence"]
    insight: "AI feature gap may be driving enterprise churn risk"
    confidence: 0.78

  - pattern: "Support tickets + AI Dashboard adoption"
    domains: ["customer_success", "feature_lifecycle"]
    insight: "Dashboard complexity may be causing support burden"
    confidence: 0.72

  - pattern: "Deployment frequency + Error rate"
    domains: ["devops"]
    insight: "Faster deployments maintaining quality, capacity stable"
    confidence: 0.85
```

### 4. Generate Recommendations

```
═══════════════════════════════════════════════════════════════════════════════
                         AI RECOMMENDATIONS
                         2025-01-15
═══════════════════════════════════════════════════════════════════════════════

Based on 38 active signals across 4 domains

───────────────────────────────────────────────────────────────────────────────
STRATEGIC RECOMMENDATIONS
───────────────────────────────────────────────────────────────────────────────

1. 🎯 ACCELERATE AI FEATURE DEVELOPMENT
   Priority: CRITICAL
   Confidence: 82%
   Time Horizon: 3-6 months

   Insight:
     CompetitorX's AI analytics launch coincides with enterprise churn
     signals. 5 enterprise customers showing risk patterns typically
     associated with competitive displacement.

   Evidence:
     • CompetitorX launched AI analytics (detected 2 days ago)
     • 3 enterprise customers mentioned "AI capabilities" in feedback
     • Market trend shows AI automation at 45% CAGR
     • Current AI feature adoption at 23% (target: 50%)

   Recommended Actions:
     □ Prioritize AI roadmap items in Q1 sprint
     □ Launch competitive response campaign to at-risk enterprise
     □ Accelerate AI Dashboard feature completion
     □ Consider AI vendor partnership for faster delivery

   Impact:
     • Revenue protected: ~$450,000 ARR (at-risk enterprise)
     • Competitive positioning: Close gap with CompetitorX
     • Market opportunity: $15B AI automation TAM

   Decision Required: APPROVAL (Product strategy change)

   ─────────────────────────────────────────────────────────────────────────

2. 📊 SIMPLIFY AI DASHBOARD ONBOARDING
   Priority: HIGH
   Confidence: 76%
   Time Horizon: 1-2 months

   Insight:
     Support ticket correlation with AI Dashboard usage suggests
     onboarding complexity is creating friction and support burden.

   Evidence:
     • 45% of AI Dashboard support tickets in first 7 days
     • Starter segment activation only 41% (target: 60%)
     • "Confusing" mentioned in 23 support tickets
     • Competitor has simplified wizard-based onboarding

   Recommended Actions:
     □ Create step-by-step onboarding wizard
     □ Add interactive tutorials
     □ Simplify initial configuration
     □ Create segment-specific onboarding paths

   Impact:
     • Support ticket reduction: ~30%
     • Activation improvement: +15-20%
     • Time-to-value reduction: 3 days → 1 day

   Decision Required: REVIEW (UX enhancement)

───────────────────────────────────────────────────────────────────────────────
TACTICAL RECOMMENDATIONS
───────────────────────────────────────────────────────────────────────────────

3. 👥 PROACTIVE ENTERPRISE OUTREACH
   Priority: HIGH
   Confidence: 85%
   Time Horizon: This week

   Insight:
     5 enterprise customers showing early churn indicators need
     immediate proactive engagement before signals escalate.

   Customers at Risk:
     • Acme Corp (Health: 52, ARR: $48,000)
     • TechStart Inc (Health: 48, ARR: $36,000)
     • GlobalCo (Health: 45, ARR: $72,000)
     • InnovateCorp (Health: 55, ARR: $65,000)
     • MegaSystems (Health: 58, ARR: $89,000)

   Recommended Actions:
     □ Schedule executive check-ins within 48 hours
     □ Prepare value demonstration materials
     □ Identify and address specific pain points
     □ Offer extended support or training

   Impact:
     • Revenue protected: $310,000 ARR
     • Churn prevention: 3-4 customers likely saved
     • NPS improvement opportunity

   Decision Required: AUTONOMOUS (standard intervention protocol)
   Status: ✓ Interventions already triggered for 3 customers

   ─────────────────────────────────────────────────────────────────────────

4. 🔄 LEGACY API V1 DEPRECATION ACCELERATION
   Priority: MEDIUM
   Confidence: 71%
   Time Horizon: 2-4 weeks

   Insight:
     Legacy API v1 usage declining organically. Good opportunity to
     accelerate deprecation timeline and reduce maintenance burden.

   Evidence:
     • Active users down 35% in 90 days
     • 68% of customers already migrated
     • Maintenance cost: $8,000/month
     • No new integrations in 60 days

   Recommended Actions:
     □ Move deprecation announcement up 30 days
     □ Increase migration support for remaining 32%
     □ Offer migration office hours
     □ Prepare sunset communication

   Impact:
     • Cost reduction: $96,000/year
     • Engineering focus: 2 FTEs freed
     • Technical debt reduction

   Decision Required: APPROVAL (customer impact)

───────────────────────────────────────────────────────────────────────────────
OPERATIONAL RECOMMENDATIONS
───────────────────────────────────────────────────────────────────────────────

5. ⚡ SCALE HEALTH MONITORING AGENTS
   Priority: MEDIUM
   Confidence: 88%
   Time Horizon: Today

   Insight:
     Health-monitor agents approaching capacity. Scaling now prevents
     queue backup during peak periods.

   Current State:
     • Agents: 3 active
     • Utilization: 78% average, 85% peak
     • Queue depth: 45 items
     • Processing time: 4.2s (trending up from 3.1s)

   Recommended Actions:
     □ Spawn 2 additional health-monitor agents
     □ Rebalance work queue
     □ Adjust scaling thresholds

   Impact:
     • Queue reduction: 45 → 15 items
     • Processing time: 4.2s → 2.8s
     • Headroom for growth

   Decision Required: AUTONOMOUS (infrastructure scaling)
   Status: ⏳ Pending execution (will auto-scale at 85%)

   ─────────────────────────────────────────────────────────────────────────

6. 📧 PROCESS PENDING APPROVALS
   Priority: MEDIUM
   Confidence: 95%
   Time Horizon: Today

   Insight:
     3 decisions pending approval for >2 hours. Blocking downstream
     work items and slowing decision velocity.

   Pending Decisions:
     • dec_003: Deprecation announcement (2h pending)
     • dec_004: Production deployment (45m pending)
     • dec_005: Contract concession (30m pending)

   Recommended Actions:
     □ Remind approvers via Slack
     □ Escalate if not approved by EOD
     □ Consider delegated approval authority

   Impact:
     • Unblock 12 dependent work items
     • Improve decision velocity
     • Maintain 90%+ autonomy rate

   Decision Required: AUTONOMOUS (reminder workflow)

───────────────────────────────────────────────────────────────────────────────
SUMMARY
───────────────────────────────────────────────────────────────────────────────

Total Recommendations: 6
  Strategic:   2 (require approval)
  Tactical:    2 (1 in progress, 1 requires approval)
  Operational: 2 (autonomous)

Potential Impact:
  Revenue Protected:  $760,000 ARR
  Cost Reduction:     $96,000/year
  Efficiency Gain:    30% support ticket reduction

Immediate Actions:
  ✓ Enterprise outreach triggered (3 customers)
  ⏳ Agent scaling queued
  ⏳ Approval reminders scheduled

Actions Requiring Approval:
  • AI feature acceleration (strategic)
  • Legacy API deprecation acceleration (tactical)

───────────────────────────────────────────────────────────────────────────────

To execute a recommendation:
  /autonomous:decide <recommendation-type> --target <id>

To view recommendation history:
  /autonomous:history --recommendations

═══════════════════════════════════════════════════════════════════════════════
```

### 5. Domain-Specific Recommendations

When `--domain` specified, provide deeper analysis:

```
Example: /autonomous:recommend --domain customer_success

Shows only customer success recommendations with:
  - Detailed customer-by-customer analysis
  - Specific playbook recommendations
  - Health trend predictions
  - CSM workload optimization
```

### 6. Target-Specific Recommendations

When `--target` specified:

```
Example: /autonomous:recommend --target cust_abc123

Shows recommendations for specific customer:
  - Current health analysis
  - Risk factors
  - Recommended interventions
  - Expansion opportunities
  - Similar customer patterns
```

## Recommendation Confidence Levels

| Confidence | Meaning | Action |
|------------|---------|--------|
| 90-100% | High certainty, strong evidence | Execute autonomously |
| 75-89% | Good confidence, solid patterns | Execute with review |
| 60-74% | Moderate confidence | Requires approval |
| <60% | Low confidence, investigate more | Gather more data |

## API Integration

### 1. Get AI-Powered Recommendations

```bash
# Get AI-powered recommendations based on active signals
# Note: Use a valid workspace UUID for database persistence, or "default" for mock responses
curl -s -X GET "http://localhost:3001/api/v1/autonomous/recommendations?limit=10&includeSignals=true" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Get recommendations for specific domain
curl -s -X GET "http://localhost:3001/api/v1/autonomous/recommendations?domain=$DOMAIN&limit=10" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

Response includes:

- Prioritized recommendations based on signal severity
- Risk scores and autonomy levels
- Suggested actions for each recommendation
- Related signals that triggered the recommendation
- Detected cross-domain patterns

### 2. Get Active Signals by Domain

```bash
# Get all active signals
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/signals?limit=100" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Get signals for specific domain
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/signals?sourceDomain=$DOMAIN&limit=50" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Get unprocessed signals only
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/signals?actionTriggered=false&limit=50" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

### 3. Get Signal Statistics

```bash
# Get signal statistics
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/stats?timeWindowDays=7" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

### 4. Detect Pattern Correlations

```bash
# Get registered patterns
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/patterns" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .

# Run pattern detection on current signals
curl -s -X POST "http://localhost:3001/api/v1/cross-domain/detect-patterns" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

### 5. Get Decision Statistics

```bash
# Get decision statistics to understand past performance
curl -s -X GET "http://localhost:3001/api/v1/autonomous/stats?periodDays=30" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

Response includes:

- Total decisions by autonomy level
- Success/failure rates
- Autonomy rate and override rate
- Decisions by domain and type

### 6. Query Knowledge Base for Similar Patterns

```bash
# Semantic search for similar recommendations
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/search?query=recommendation%20$DOMAIN&limit=10" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

### 7. Get Learning Metrics

```bash
# Get decision metrics to inform recommendations
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/metrics/decisions?periodDays=30" \
  -H "x-workspace-id: $WORKSPACE_UUID" | jq .
```

### 8. Log Recommendation Access

```bash
# Log that recommendations were generated (for learning)
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: $WORKSPACE_UUID" \
  -d '{
    "category": "recommendation",
    "subcategory": "strategic",
    "tags": ["recommendation", "customer_success", "'$(date +%Y-%m-%d)'"],
    "title": "Recommendations Generated: strategic for customer_success",
    "content": "Generated recommendations based on active signals",
    "structuredData": {
      "recommendationType": "strategic",
      "domain": "customer_success",
      "targetId": "all",
      "signalCount": 38,
      "recommendationCount": 6,
      "generatedAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
    },
    "source": {
      "type": "recommendation_engine",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "confidence": 80
    }
  }' | jq .
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/autonomous/recommendations` | Get AI-powered recommendations |
| `GET /api/v1/autonomous/stats` | Decision statistics |
| `GET /api/v1/cross-domain/signals` | Get active signals |
| `GET /api/v1/cross-domain/stats` | Signal statistics |
| `GET /api/v1/cross-domain/patterns` | Pattern registry |
| `POST /api/v1/cross-domain/detect-patterns` | Detect pattern correlations |
| `GET /api/v1/swarm-knowledge/search` | Search knowledge base |
| `GET /api/v1/swarm-knowledge/metrics/decisions` | Decision metrics |
| `POST /api/v1/swarm-knowledge` | Log recommendation access |

## Error Handling

| Error | Resolution |
|-------|------------|
| Insufficient signals | Wait for more data |
| No patterns found | Check domain health |
| Conflicting recommendations | Present trade-offs |
| Target not found | Verify target ID |
| Domain unavailable | Check service health |

---

**Uses**: CrossDomainIntelligence, SwarmKnowledgeService, RecommendationEngine
**Model**: Sonnet (recommendation synthesis)
