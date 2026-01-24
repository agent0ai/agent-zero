---
description: Generate AI-powered automatic responses for support tickets
argument-hint: <ticket-id> [--confidence-threshold <0.7-0.95>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, AskUserQuestion
---

Generate auto-response for ticket: **${ARGUMENTS}**

## AI-Powered Auto-Response

**Intelligent Response Generation**:

- Intent detection and classification
- Confidence scoring (0-100%)
- KB article matching
- Personalized response generation
- Sentiment-aware tone adjustment
- Fallback to human agent if low confidence

Routes to **agent-router**:

```javascript
await Task({
  subagent_type: 'agent-router',
  description: 'Generate automated support response',
  prompt: `Generate auto-response for ticket: ${TICKET_ID}

Confidence threshold: ${CONFIDENCE_THRESHOLD || 0.80}

Execute intelligent auto-response workflow:

## 1. Fetch Ticket Context

\`\`\`bash
# Get ticket details
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}"

# Get ticket thread
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}/threads" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}"

# Get customer context
curl "https://www.zohoapis.com/crm/v2/Contacts/\${CONTACT_ID}" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}"
\`\`\`

Extract:
- Ticket description
- Customer name and tier
- Previous ticket history
- Current sentiment
- Urgency indicators

## 2. Intent Detection

Analyze ticket to determine user intent:

**Common Intents** (with examples):

**Password Reset** (Confidence: High)
- "can't login"
- "forgot password"
- "password not working"
→ KB: How to reset password

**Billing Question** (Confidence: High)
- "when am I charged"
- "how much does it cost"
- "cancel subscription"
→ KB: Billing FAQ + Pricing page

**Feature Request** (Confidence: Medium)
- "can you add X"
- "would be nice to have Y"
- "any plans to support Z"
→ Response: Thank you, logged for product team

**Bug Report** (Confidence: Medium)
- "not working"
- "error message"
- "broken"
→ Response: Needs investigation, ask for details

**How-To Question** (Confidence: High)
- "how do I..."
- "where can I find..."
- "what's the process for..."
→ KB: Relevant how-to article

**Integration Help** (Confidence: Medium)
- "API documentation"
- "webhook setup"
- "third-party integration"
→ KB: API docs + Code examples

**Account Access** (Confidence: High)
- "can't access account"
- "permission denied"
- "need admin access"
→ Response: Escalate to admin

**Data Export** (Confidence: High)
- "download my data"
- "export to CSV"
- "get all my information"
→ KB: Data export guide

**Refund Request** (Confidence: High)
- "want a refund"
- "cancel and refund"
- "money back"
→ Response: Escalate to billing team (requires human)

**General Inquiry** (Confidence: Low)
- Vague or unclear intent
→ Response: Ask clarifying questions

## 3. Confidence Scoring

Score confidence in auto-response:

\`\`\`javascript
function calculateConfidence(intent, ticketData) {
  let confidence = 0.5; // Base confidence

  // Intent clarity (+0 to +0.3)
  if (strongKeywordMatch) confidence += 0.3;
  else if (weakKeywordMatch) confidence += 0.15;

  // KB article available? (+0 to +0.2)
  if (exactMatchKBArticle) confidence += 0.2;
  else if (relatedKBArticle) confidence += 0.1;

  // Customer history (+0 to +0.1)
  if (similarPreviousTickets && resolved) confidence += 0.1;

  // Ticket complexity (-0 to -0.2)
  if (multipleQuestions) confidence -= 0.1;
  if (customOrEdgeCase) confidence -= 0.2;

  // Sentiment (-0 to -0.15)
  if (frustrated || angry) confidence -= 0.15;

  return Math.max(0, Math.min(1, confidence));
}

const confidence = calculateConfidence(\${INTENT}, \${TICKET_DATA});
const confidencePercent = Math.round(confidence * 100);

console.log(\`Confidence: \${confidencePercent}%\`);
\`\`\`

**Confidence Thresholds**:
- **95-100%**: Auto-send immediately (password resets, KB lookups)
- **80-94%**: Send with "Was this helpful?" follow-up
- **70-79%**: Draft response, human reviews before sending
- **Below 70%**: Escalate to human agent

## 4. Search Knowledge Base

Find relevant KB articles:

\`\`\`bash
# Search KB for relevant articles
curl "https://desk.zoho.com/api/v1/articles/search?searchStr=\${TICKET_KEYWORDS}" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}"

# Rank by relevance:
# 1. Title match (exact or partial)
# 2. Tag match
# 3. Category match
# 4. Content match
# 5. Popularity (view count, helpfulness)
\`\`\`

Select top 1-3 most relevant articles.

## 5. Generate Response

Create personalized response based on intent and KB articles:

### Response Template Structure

\`\`\`markdown
Hi \${CUSTOMER_FIRST_NAME},

[Personalized greeting based on sentiment]
[Frustrated] → "I understand this is frustrating. Let me help you resolve this quickly."
[Neutral] → "Thanks for reaching out! I'm happy to help."
[Positive] → "Great question! Here's what you need to know."

[Direct answer to question - 2-3 sentences]

[If KB article exists]
**Here's a helpful guide**: [Article Title]
[Article URL]

This article covers:
- [Key point 1]
- [Key point 2]
- [Key point 3]

[Step-by-step if simple enough, otherwise link to KB]

[Verification step]
Let me know if this resolves your issue!

[If needs follow-up]
If you need further assistance, just reply to this ticket and I'll be happy to help.

[Closing]
Best regards,
\${AGENT_NAME}
\${TEAM_NAME}

[Helpful resources]
📚 Help Center: [URL]
💬 Live Chat: [URL]
📧 Email: support@example.com
\`\`\`

### Intent-Specific Responses

**Password Reset** (High Confidence: 95%):
\`\`\`markdown
Hi \${CUSTOMER_FIRST_NAME},

I can help you reset your password right away!

**To reset your password**:
1. Go to [Login Page URL]
2. Click "Forgot Password"
3. Enter your email: \${CUSTOMER_EMAIL}
4. Check your inbox for reset link (arrives in 2-3 minutes)
5. Click link and set new password

**Didn't receive the email?**
- Check spam folder
- Make sure you're using \${CUSTOMER_EMAIL}
- Try again after 5 minutes

**Still having trouble?** Reply to this ticket and I'll manually reset it for you.

Best regards,
Support Team

---
📚 Full Guide: [How to Reset Your Password](KB_ARTICLE_URL)
\`\`\`

**Billing Question** (High Confidence: 90%):
\`\`\`markdown
Hi \${CUSTOMER_FIRST_NAME},

Happy to answer your billing question!

**Your current plan**: \${PLAN_NAME} - \${PLAN_PRICE}/month
**Next billing date**: \${NEXT_BILLING_DATE}
**Payment method**: \${PAYMENT_METHOD} ending in \${LAST_4}

[Answer specific question based on intent]

**Need to make changes?**
- Update payment method: [URL]
- Change plan: [URL]
- Cancel subscription: [URL]

Let me know if you have any other questions!

Best regards,
Billing Team
\`\`\`

**Feature Request** (Medium Confidence: 75%):
\`\`\`markdown
Hi \${CUSTOMER_FIRST_NAME},

Thank you for the suggestion! We really appreciate feedback from customers like you.

I've logged your request for "\${FEATURE_DESCRIPTION}" with our product team. Here's what happens next:

1. **Product team reviews** (within 2 weeks)
2. **Prioritized based on demand** (votes from multiple customers)
3. **Roadmap planning** (quarterly reviews)
4. **You'll be notified** if it's added to roadmap

**Want to increase visibility?**
- Upvote on our roadmap: [URL]
- Share your use case (helps us understand the need)

**In the meantime**, here are some workarounds:
- [Alternative approach 1]
- [Alternative approach 2]

We'll keep you posted!

Best regards,
Product Team
\`\`\`

**Bug Report** (Low Confidence: 65% - Needs Human Review):
\`\`\`markdown
Hi \${CUSTOMER_FIRST_NAME},

Thank you for reporting this issue. I want to make sure we investigate this thoroughly.

To help us diagnose the problem, could you provide:

1. **What were you trying to do?**
2. **What happened instead?**
3. **Error message** (if any - screenshot helpful)
4. **When did this start?** (today, yesterday, ongoing)
5. **Browser/device**: (Chrome, Safari, iOS, Android)

**Temporary workaround** (if we know one):
[Workaround steps]

A member of our engineering team will investigate and respond within \${SLA_TIME}.

Best regards,
Support Team

[Auto-assigned to engineering team]
\`\`\`

## 6. Tone Adjustment

Adjust response tone based on customer sentiment:

**Frustrated Customer** (sentiment: frustrated/angry):
- More empathetic language
- Acknowledge frustration explicitly
- Faster resolution promise
- Personal touch (not canned)
- Offer escalation if needed

**Example**:
"I understand how frustrating this must be, especially when you need to get work done. Let me help you resolve this right away."

**Happy Customer**:
- Friendly, casual tone
- Keep it brief
- Match their energy

**Example**:
"Great question! Here's exactly what you need..."

**Neutral Customer**:
- Professional, helpful tone
- Clear and concise
- No unnecessary fluff

**Example**:
"Thanks for reaching out. Here's how to..."

## 7. Decision: Auto-Send or Human Review?

Based on confidence score:

\`\`\`javascript
const threshold = \${CONFIDENCE_THRESHOLD || 0.80};

if (confidence >= 0.95) {
  // AUTO-SEND: Very high confidence
  action = 'send_immediately';

} else if (confidence >= threshold) {
  // SEND WITH FOLLOW-UP: Good confidence
  action = 'send_with_followup';
  followupMessage = "Was this helpful? [Yes] [No, I need more help]";

} else if (confidence >= 0.70) {
  // DRAFT FOR REVIEW: Medium confidence
  action = 'draft_for_human_review';
  reviewNote = "AI generated response - please review before sending";

} else {
  // ESCALATE: Low confidence
  action = 'escalate_to_human';
  reason = "Complex question requiring human judgment";
}
\`\`\`

## 8. Execute Action

### If Auto-Send (Confidence ≥ 95%)

\`\`\`bash
# Send response via Zoho Desk
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}/sendReply" \\
  -X POST \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}" \\
  -d '{
    "content": "'\${RESPONSE_CONTENT}'",
    "contentType": "html",
    "isPublic": true,
    "status": "Waiting on Customer"
  }'

# Log as auto-resolved
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}" \\
  -X PATCH \\
  -d '{
    "cf": {
      "auto_responded": true,
      "ai_confidence": '\${CONFIDENCE}',
      "response_time_seconds": '\${RESPONSE_TIME}'
    }
  }'

echo "✓ Auto-response sent (confidence: \${CONFIDENCE}%)"
\`\`\`

### If Send with Follow-Up (Confidence 80-94%)

Send response + add follow-up check:

\`\`\`bash
# Send response
[Same as above]

# Schedule follow-up check (1 hour)
curl "https://desk.zoho.com/api/v1/tasks" \\
  -X POST \\
  -d '{
    "subject": "Check if auto-response resolved ticket #\${TICKET_ID}",
    "dueDate": "'\$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)'",
    "ticketId": "'\${TICKET_ID}'"
  }'
\`\`\`

### If Draft for Review (Confidence 70-79%)

Save as internal note for human review:

\`\`\`bash
# Add as private note (not sent to customer)
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}/threads" \\
  -X POST \\
  -d '{
    "content": "AI-Generated Response (Confidence: \${CONFIDENCE}%): <br><br>\${RESPONSE_CONTENT}",
    "contentType": "html",
    "isPublic": false
  }'

# Assign to human agent
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}" \\
  -X PATCH \\
  -d '{
    "assigneeId": "'\${AGENT_ID}'",
    "status": "Open",
    "cf": {
      "ai_draft_available": true,
      "ai_confidence": '\${CONFIDENCE}'
    }
  }'

echo "✓ Draft saved for human review"
\`\`\`

### If Escalate (Confidence < 70%)

Assign to human immediately:

\`\`\`bash
# Add internal note explaining why escalated
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}/threads" \\
  -X POST \\
  -d '{
    "content": "AI Analysis: <br>Intent: \${INTENT}<br>Confidence: \${CONFIDENCE}%<br>Reason for escalation: \${ESCALATION_REASON}",
    "isPublic": false
  }'

# Assign to appropriate team
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}" \\
  -X PATCH \\
  -d '{
    "assigneeId": "'\${AGENT_ID}'",
    "status": "Open"
  }'

echo "✓ Escalated to human agent"
\`\`\`

## 9. Track Performance

Monitor auto-response effectiveness:

\`\`\`javascript
const metrics = {
  tickets_analyzed: \${TOTAL_TICKETS},
  auto_sent: \${AUTO_SENT_COUNT},
  human_reviewed: \${HUMAN_REVIEW_COUNT},
  escalated: \${ESCALATED_COUNT},

  avg_confidence: \${AVG_CONFIDENCE},

  resolution_rate: {
    auto_sent: \${AUTO_RESOLVED_COUNT} / \${AUTO_SENT_COUNT}, // Target: 70-80%
    overall: \${TOTAL_RESOLVED} / \${TOTAL_TICKETS} // Target: 40-50%
  },

  customer_satisfaction: {
    auto_responses: \${CSAT_AUTO}, // Target: > 4.0/5
    human_responses: \${CSAT_HUMAN} // Comparison
  },

  time_saved: {
    avg_response_time_auto: '30 seconds',
    avg_response_time_human: '15 minutes',
    tickets_auto_resolved: \${AUTO_RESOLVED_COUNT},
    hours_saved: \${AUTO_RESOLVED_COUNT} * 15 / 60 // hours
  }
};
\`\`\`

## 10. Generate Report

\`\`\`markdown
# Auto-Response Report

**Ticket**: #\${TICKET_ID}
**Customer**: \${CUSTOMER_NAME} (\${CUSTOMER_TIER})
**Generated**: \${TIMESTAMP}

## Intent Analysis

**Detected Intent**: \${INTENT}
**Confidence**: \${CONFIDENCE}% (\${CONFIDENCE_LEVEL})
**Sentiment**: \${SENTIMENT}

**Keywords Matched**: \${KEYWORDS.join(', ')}
**KB Articles Found**: \${KB_ARTICLES.length}

## Response Details

**Action Taken**: \${ACTION}
- ✓ Auto-sent immediately (confidence ≥ 95%)
- ✓ Sent with follow-up (confidence 80-94%)
- ✓ Drafted for review (confidence 70-79%)
- ✓ Escalated to human (confidence < 70%)

**Response Time**: \${RESPONSE_TIME} seconds

**KB Articles Included**:
${KB_ARTICLES.map(a => \`- [\${a.title}](\${a.url})\`).join('\\n') || 'None'}

## Response Content

\`\`\`
\${RESPONSE_CONTENT}
\`\`\`

## Expected Outcome

**Resolution Probability**: \${RESOLUTION_PROBABILITY}%
**Follow-Up Needed**: \${FOLLOWUP_NEEDED ? 'Yes' : 'No'}
**Escalation Risk**: \${ESCALATION_RISK}

## Performance Impact

**Time Saved**: \${TIME_SAVED} minutes (vs human response)
**Cost Saved**: $\${COST_SAVED}

---
View ticket: https://desk.zoho.com/support/tickets/\${TICKET_ID}
\`\`\`

Save to: support-responses/auto-response-\${TICKET_ID}-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Generate auto-response with default confidence (80%)
/support/autorespond 12345

# High confidence threshold (only very confident responses)
/support/autorespond 12345 --confidence-threshold 0.90

# Low confidence threshold (more aggressive automation)
/support/autorespond 12345 --confidence-threshold 0.75
```

## Response Examples

**Password Reset** (Confidence: 95% → Auto-sent):

```
Hi Sarah,

I can help you reset your password right away!

**To reset your password**:
1. Go to https://app.example.com/login
2. Click "Forgot Password"
3. Enter your email: sarah@example.com
4. Check your inbox for reset link

Let me know if you need any help!

Best regards,
Support Team
```

**Billing Question** (Confidence: 88% → Sent with follow-up):

```
Hi John,

Your next billing date is March 15, 2024 for $99/month.

You'll be charged to the card ending in 4242.

[Full response...]

Was this helpful? [Yes] [No, I need more help]
```

**Complex Bug** (Confidence: 65% → Escalated):

```
[Internal note to agent:]
AI Analysis:
Intent: Bug Report
Confidence: 65%
Reason: Complex multi-step issue, needs engineering investigation

Suggested response available, but requires human review before sending.
```

## Success Criteria

- ✓ Intent detected with confidence score
- ✓ KB articles searched and ranked
- ✓ Response generated (personalized, tone-adjusted)
- ✓ Action taken based on confidence (auto-send/draft/escalate)
- ✓ Performance tracked (resolution rate, CSAT)
- ✓ Report saved
- ✓ Auto-resolution rate: 40-50% of tickets
- ✓ CSAT for auto-responses: > 4.0/5
- ✓ Time savings: 85-95% (30 seconds vs 15 minutes)

## ROI Calculation

**Current State (No Auto-Response)**:

- 500 tickets/month
- 15 min average response time
- Cost: 500 × 15 min = 125 hours/month
- At $50/hour = $6,250/month

**With Auto-Response** (50% automation):

- 250 tickets auto-responded (30 seconds each)
- 250 tickets human-responded (15 min each)
- Cost: (250 × 0.5 min) + (250 × 15 min) = 63.5 hours/month
- At $50/hour = $3,175/month
- **Savings**: $3,075/month = **$36,900/year**

**Time Savings**: 61.5 hours/month = **50% reduction**

---
**Uses**: agent-router (intent detection, response generation)
**Output**: Auto-response sent or drafted + performance tracking
**Next Commands**: `/support/knowledge-base` (improve KB for better auto-responses)
**Metrics**: 40-50% auto-resolution, > 4.0/5 CSAT, 50% time savings
