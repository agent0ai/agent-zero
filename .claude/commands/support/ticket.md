---
description: Create and manage support tickets with AI categorization
argument-hint: <ticket-description> [--customer-id <id>] [--priority <low|medium|high|urgent>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, AskUserQuestion
---

Create support ticket: **${ARGUMENTS}**

## Support Ticket Management

**AI-Powered Features**:

- Auto-categorization (bug, feature request, question, billing)
- Priority detection (urgent, high, medium, low)
- Sentiment analysis (frustrated, neutral, happy)
- Auto-assignment to right team
- SLA tracking and alerting

Routes to **agent-router**:

```javascript
await Task({
  subagent_type: 'agent-router',
  description: 'Create and manage support ticket',
  prompt: `Create support ticket: ${TICKET_DESCRIPTION}

Customer ID: ${CUSTOMER_ID || 'Not provided'}
Manual Priority: ${PRIORITY || 'Auto-detect'}

Execute comprehensive ticket creation workflow:

## 1. AI Analysis

Analyze ticket description and extract:

**Category Detection**:
- 🐛 Bug Report: Error messages, "not working", crashes
- ✨ Feature Request: "would be nice", "can you add", enhancement
- ❓ Question: "how do I", "what is", "where can I find"
- 💳 Billing: "charge", "invoice", "payment", "subscription"
- 🔐 Access: "can't login", "password", "permission denied"
- ⚡ Performance: "slow", "timeout", "loading"
- 🔗 Integration: "API", "webhook", "third-party"

**Priority Detection**:
- 🚨 URGENT (P0): "down", "broken", "can't access", "data loss"
- 🔴 HIGH (P1): "affecting all users", "blocking", "critical feature"
- 🟡 MEDIUM (P2): "some users", "workaround exists"
- 🟢 LOW (P3): "nice to have", "enhancement", "question"

**Sentiment Analysis**:
- 😠 Frustrated: "frustrated", "disappointed", "terrible", urgent tone
- 😐 Neutral: Factual description, no emotion
- 😊 Happy: "love the product", positive feedback included

**Urgency Indicators**:
- Customer is paying customer? (+priority)
- Enterprise plan? (+priority)
- Mentioned deadline? (note in ticket)
- Multiple tickets from same user? (escalation risk)

## 2. Enrich Customer Context

If customer ID provided:
\`\`\`bash
# Fetch customer data from Zoho CRM
curl "https://www.zohoapis.com/crm/v2/Contacts/\${CUSTOMER_ID}" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}"

# Get previous tickets
curl "https://desk.zoho.com/api/v1/tickets?contact=\${CUSTOMER_ID}" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}"

# Analyze:
- Customer lifetime value (CLV)
- Current plan (Free/Pro/Enterprise)
- Previous ticket count
- Average response time
- Satisfaction score
\`\`\`

## 3. Generate Ticket Summary

Create concise ticket summary:

**Title**: [Auto-generated from description, 50-70 chars]
**Category**: [Detected category]
**Priority**: [P0/P1/P2/P3 with reasoning]
**Sentiment**: [Frustrated/Neutral/Happy]

**AI-Detected Context**:
- Affected Feature: [Product area]
- Error Messages: [If any]
- Browser/Platform: [If mentioned]
- Steps to Reproduce: [If bug]
- Expected Behavior: [If bug]
- Workaround Available: [Yes/No]

## 4. Assign to Team

Auto-assignment rules:

**By Category**:
- Bug → Engineering team
- Feature Request → Product team
- Billing → Finance team
- Access/Login → Support tier 2
- Question → Support tier 1
- Integration → Engineering (API team)

**By Priority**:
- P0 (Urgent) → On-call engineer + manager notification
- P1 (High) → Senior support + engineering escalation path
- P2 (Medium) → Support team queue
- P3 (Low) → Self-service queue (try KB first)

**By Customer Type**:
- Enterprise → Dedicated success manager
- Pro → Premium support queue
- Free → Standard queue

## 5. Create Ticket in Zoho Desk

\`\`\`bash
# Create ticket
curl "https://desk.zoho.com/api/v1/tickets" \\
  -X POST \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "contactId": "'\${CUSTOMER_ID}'",
    "subject": "'\${TICKET_TITLE}'",
    "description": "'\${TICKET_DESCRIPTION}'",
    "departmentId": "'\${DEPARTMENT_ID}'",
    "category": "'\${CATEGORY}'",
    "priority": "'\${PRIORITY}'",
    "status": "Open",
    "assigneeId": "'\${ASSIGNEE_ID}'",
    "cf": {
      "sentiment": "'\${SENTIMENT}'",
      "ai_category_confidence": '\${CONFIDENCE}',
      "affected_feature": "'\${FEATURE}'",
      "has_workaround": '\${HAS_WORKAROUND}'
    },
    "dueDate": "'\${DUE_DATE}'"
  }'

echo "✓ Ticket created: \${TICKET_ID}"
\`\`\`

## 6. SLA Calculation

Calculate SLA based on priority and customer tier:

\`\`\`javascript
function calculateSLA(priority, customerTier) {
  const slaMatrix = {
    'P0': {
      'Enterprise': { response: '15 min', resolution: '4 hours' },
      'Pro': { response: '30 min', resolution: '8 hours' },
      'Free': { response: '1 hour', resolution: '24 hours' }
    },
    'P1': {
      'Enterprise': { response: '1 hour', resolution: '1 day' },
      'Pro': { response: '2 hours', resolution: '2 days' },
      'Free': { response: '4 hours', resolution: '3 days' }
    },
    'P2': {
      'Enterprise': { response: '4 hours', resolution: '2 days' },
      'Pro': { response: '8 hours', resolution: '3 days' },
      'Free': { response: '24 hours', resolution: '5 days' }
    },
    'P3': {
      'Enterprise': { response: '8 hours', resolution: '3 days' },
      'Pro': { response: '24 hours', resolution: '5 days' },
      'Free': { response: '48 hours', resolution: '7 days' }
    }
  };

  return slaMatrix[priority][customerTier];
}

const sla = calculateSLA('\${PRIORITY}', '\${CUSTOMER_TIER}');
console.log(\`Response SLA: \${sla.response}\`);
console.log(\`Resolution SLA: \${sla.resolution}\`);
\`\`\`

## 7. Send Notifications

**To Customer**:
\`\`\`markdown
Subject: Ticket #\${TICKET_ID} Created - We're On It!

Hi \${CUSTOMER_NAME},

Thank you for contacting us! We've received your request and created ticket #\${TICKET_ID}.

**What we're working on**:
\${TICKET_TITLE}

**Priority**: \${PRIORITY_NAME}
**Category**: \${CATEGORY}
**Assigned to**: \${ASSIGNED_TEAM}

**Expected Response**: Within \${RESPONSE_SLA}
**Expected Resolution**: Within \${RESOLUTION_SLA}

You can track your ticket here: \${TICKET_URL}

We'll keep you updated as we make progress.

Best,
\${ASSIGNED_AGENT}
Support Team
\`\`\`

**To Assigned Agent** (Slack/Email):
\`\`\`
🎫 New Ticket Assigned: #\${TICKET_ID}

Priority: \${PRIORITY} (\${PRIORITY_EMOJI})
Category: \${CATEGORY}
Sentiment: \${SENTIMENT} (\${SENTIMENT_EMOJI})

Customer: \${CUSTOMER_NAME} (\${CUSTOMER_TIER})
Subject: \${TICKET_TITLE}

SLA: Respond within \${RESPONSE_SLA}

[View Ticket] [Claim Ticket] [Escalate]
\`\`\`

**If P0 (Urgent)** → Page on-call engineer:
\`\`\`bash
# Send PagerDuty alert
curl -X POST "https://api.pagerduty.com/incidents" \\
  -H "Authorization: Token token=\${PAGERDUTY_TOKEN}" \\
  -d '{
    "incident": {
      "type": "incident",
      "title": "P0 Support Ticket: \${TICKET_TITLE}",
      "service": { "id": "'\${SERVICE_ID}'", "type": "service_reference" },
      "urgency": "high",
      "body": {
        "type": "incident_body",
        "details": "Urgent customer issue: \${TICKET_DESCRIPTION}"
      }
    }
  }'
\`\`\`

## 8. Auto-Response Suggestions

If similar tickets exist, suggest responses:

\`\`\`bash
# Search for similar resolved tickets
curl "https://desk.zoho.com/api/v1/tickets/search?searchStr=\${TICKET_KEYWORDS}" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}"

# If found:
# - Extract resolution from previous tickets
# - Suggest KB articles
# - Recommend canned responses
# - Provide to assigned agent
\`\`\`

## 9. Ticket Report

Generate comprehensive ticket summary:

\`\`\`markdown
# Support Ticket Created

**Ticket ID**: #\${TICKET_ID}
**Created**: \${TIMESTAMP}
**Customer**: \${CUSTOMER_NAME} (\${CUSTOMER_TIER})

## Ticket Details

**Subject**: \${TICKET_TITLE}
**Category**: \${CATEGORY} (Confidence: \${CONFIDENCE}%)
**Priority**: \${PRIORITY}
**Sentiment**: \${SENTIMENT}

## AI Analysis

**Detected Issue**: \${ISSUE_TYPE}
**Affected Feature**: \${FEATURE}
**Error Messages**: \${ERRORS || 'None'}
**Workaround Available**: \${HAS_WORKAROUND ? 'Yes' : 'No'}

## Assignment

**Assigned to**: \${ASSIGNED_AGENT}
**Team**: \${TEAM_NAME}
**SLA Response**: \${RESPONSE_SLA}
**SLA Resolution**: \${RESOLUTION_SLA}

## Customer Context

**Lifetime Value**: $\${CLV}
**Plan**: \${PLAN}
**Previous Tickets**: \${TICKET_COUNT}
**Avg Satisfaction**: \${CSAT_SCORE}/5
**Last Contact**: \${LAST_CONTACT_DATE}

## Next Steps

1. Agent to respond within \${RESPONSE_SLA}
2. Investigate issue and provide updates
3. Resolve within \${RESOLUTION_SLA}
4. Follow up for satisfaction survey

## Similar Tickets

\${SIMILAR_TICKETS || 'No similar tickets found'}

## Suggested KB Articles

\${SUGGESTED_KB || 'No suggestions'}

---
Track ticket: \${TICKET_URL}
\`\`\`

Save to: support-tickets/ticket-\${TICKET_ID}-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Create ticket from customer email
/support/ticket "User can't login after password reset" --customer-id 12345

# Create urgent ticket
/support/ticket "Production site is down" --priority urgent

# Create feature request
/support/ticket "Add dark mode to dashboard"

# Create billing ticket
/support/ticket "Charged twice for monthly subscription" --customer-id 67890
```

## Workflow Diagram

```
Customer Issue
    ↓
AI Analysis (category, priority, sentiment)
    ↓
Enrich Context (CLV, plan, history)
    ↓
Auto-Assign (team, agent)
    ↓
Calculate SLA (response + resolution)
    ↓
Create in Zoho Desk
    ↓
Notify (customer + agent)
    ↓
[P0?] → Page on-call engineer
    ↓
Suggest auto-responses (if available)
    ↓
Track to resolution
```

## Success Criteria

- ✓ AI categorization accuracy > 90%
- ✓ Priority detection accuracy > 85%
- ✓ Ticket created in Zoho Desk
- ✓ SLA calculated correctly
- ✓ Customer notified (email)
- ✓ Agent notified (Slack/email)
- ✓ P0 tickets trigger page within 5 minutes
- ✓ Similar tickets identified (if exist)
- ✓ KB articles suggested (if relevant)
- ✓ Ticket report saved
- ✓ Average time to create: < 30 seconds

## Metrics to Track

**Categorization Accuracy**:

- AI vs Human categorization match rate
- Target: > 90%

**Response Time**:

- Actual vs SLA response time
- Target: 95% within SLA

**Resolution Time**:

- Actual vs SLA resolution time
- Target: 90% within SLA

**Customer Satisfaction**:

- CSAT score per ticket
- Target: > 4.5/5

**Auto-Response Rate**:

- % tickets auto-resolved via KB
- Target: 30-40%

---
**Uses**: agent-router (AI analysis) → Zoho Desk API
**Output**: Support ticket created + notifications sent
**Next Commands**: `/support/autorespond` (generate response), `/support/knowledge-base` (create KB article after resolution)
**Time Savings**: 5 min manual categorization → 30 sec automated
