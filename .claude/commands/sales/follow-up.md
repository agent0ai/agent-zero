---
description: Generate personalized follow-up emails based on deal stage and activity
argument-hint: <deal-id> [--type <initial|check-in|proposal|closing|re-engage>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, AskUserQuestion
---

Sales follow-up: **${ARGUMENTS}**

## Intelligent Follow-Up

**Generates**:

- Personalized follow-up emails
- Subject line variations (A/B test)
- Follow-up timing recommendations
- Next action suggestions
- Email templates by stage and scenario

Routes to **agent-router**:

```javascript
await Task({
  subagent_type: 'agent-router',
  description: 'Generate intelligent sales follow-up',
  prompt: `Generate sales follow-up for deal: ${DEAL_ID}

Follow-up type: ${TYPE || 'auto-detect based on stage and activity'}

Execute intelligent follow-up generation:

## 1. Fetch Deal Context from Zoho CRM

\`\`\`bash
# Get deal details
curl "https://www.zohoapis.com/crm/v2/Deals/\${DEAL_ID}" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}"

# Get contact details
curl "https://www.zohoapis.com/crm/v2/Contacts/\${CONTACT_ID}" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}"

# Get recent activity history
curl "https://www.zohoapis.com/crm/v2/Deals/\${DEAL_ID}/Activities" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}"

# Get email history
curl "https://www.zohoapis.com/crm/v2/Deals/\${DEAL_ID}/Emails" \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}"
\`\`\`

Extract context:
- Contact name, title, company
- Deal stage and value
- Last interaction date and type
- Days since last contact
- Previous email topics
- Pain points discussed
- Proposal status (if sent)
- Objections or concerns raised

## 2. Determine Follow-Up Type

${TYPE ? \`
Use specified type: \${TYPE}
\` : \`
Auto-detect follow-up type based on deal context:

\\\`\\\`\\\`javascript
function determineFollowUpType(deal, activities, daysSinceContact) {
  const stage = deal.stage;

  // No prior contact → Initial outreach
  if (activities.length === 0) {
    return 'initial';
  }

  // Proposal sent, no response → Proposal follow-up
  if (activities.some(a => a.type === 'Proposal Sent') &&
      daysSinceContact > 3) {
    return 'proposal';
  }

  // In negotiation → Closing follow-up
  if (stage === 'Negotiation') {
    return 'closing';
  }

  // Stale deal (>14 days no contact) → Re-engage
  if (daysSinceContact > 14) {
    return 're-engage';
  }

  // Default → Check-in
  return 'check-in';
}

const followUpType = determineFollowUpType(deal, activities, daysSinceContact);
\\\`\\\`\\\`
\`}

## 3. Generate Personalized Follow-Up Email

### Email Structure by Type

**Initial Outreach**:
\`\`\`markdown
Subject: [Personalized - Reference their company/industry]

Hi [First Name],

[Line 1: Personalized observation about their company/industry]

[Line 2-3: Identify pain point relevant to them]

[Line 4-5: Brief intro to solution and value prop]

[Line 6: Social proof - similar company]

[Line 7: Soft CTA - "Would love to show you how [Company X] achieved [Result]"]

Best,
[Your Name]

P.S. [Value-add: Relevant resource, insight, or offer]
\`\`\`

**Check-In (Mid-Conversation)**:
\`\`\`markdown
Subject: Quick follow-up on [Topic from last conversation]

Hi [First Name],

Hope you're doing well! Following up on our conversation about [specific topic].

[Reference specific pain point or goal they mentioned]

I wanted to share [relevant resource/insight/update] that might help with [their goal].

[If applicable: "Also, I noticed [trigger event - funding, new hire, news]"]

Would it make sense to [specific next action]? I have availability [specific times].

Looking forward to hearing from you!

Best,
[Your Name]
\`\`\`

**Proposal Follow-Up**:
\`\`\`markdown
Subject: Thoughts on the proposal?

Hi [First Name],

I wanted to follow up on the proposal I sent last [day of week].

I know you're busy, so I'll keep this brief:

**Quick Recap**:
- [Key benefit 1]: [Specific outcome]
- [Key benefit 2]: [Specific outcome]
- Investment: $[Amount]
- Timeline: [Implementation timeframe]

**Next Steps**:
I'd love to hear your thoughts and answer any questions. Are you available for a quick 15-min call [Day/Time]?

**Common Questions** (in case helpful):
1. **Implementation**: [Quick answer]
2. **Integrations**: [Quick answer]
3. **Support**: [Quick answer]

Let me know what works for you!

Best,
[Your Name]

P.S. If there's anyone else who should be involved in this decision, I'm happy to loop them in.
\`\`\`

**Closing Follow-Up (Negotiation Stage)**:
\`\`\`markdown
Subject: Ready to get started?

Hi [First Name],

We're excited to get started! Just wanted to confirm next steps:

**To finalize**:
1. ✅ Pricing agreed: $[Amount]/[period]
2. ✅ Implementation plan: [Timeframe]
3. ⏳ Contract: [Status]

**What happens next**:
- Week 1: Kickoff call and account setup
- Week 2: [Key milestone]
- Week 3: [Key milestone]
- Week 4: Go-live!

I've attached the final contract for your review. Once signed, we can kick things off as soon as [Target Date].

Any final questions before we get started?

Best,
[Your Name]

P.S. Our onboarding team is already prepping for your account - can't wait to see the results!
\`\`\`

**Re-Engagement (Stale Deal)**:
\`\`\`markdown
Subject: Is this still a priority?

Hi [First Name],

I know things get busy - I haven't heard from you in a few weeks, so I wanted to check in.

When we last spoke, you mentioned [specific pain point]. Is that still something you're looking to solve?

**If timing isn't right**: No worries at all! I'll check back in [timeframe].

**If still interested**: I'd love to catch up. We've launched [new feature/update] that specifically addresses [their pain point].

**If not interested**: I completely understand. If you know anyone else who might benefit, I'd appreciate an introduction!

Either way, hope all is well!

Best,
[Your Name]

P.S. [Relevant industry insight or helpful resource]
\`\`\`

## 4. Personalization Layer

Add personalization based on context:

\`\`\`javascript
function personalizeEmail(template, context) {
  let email = template;

  // Replace placeholders
  email = email.replace('[First Name]', context.firstName);
  email = email.replace('[Company]', context.company);

  // Add personalized opening
  const personalizedOpening = generatePersonalizedOpening(context);
  email = email.replace('[Personalized observation]', personalizedOpening);

  // Add social proof
  if (context.industry) {
    const similarCustomer = findSimilarCustomer(context.industry, context.companySize);
    if (similarCustomer) {
      email += \`\n\nP.S. \${similarCustomer.name} (similar to \${context.company}) saw \${similarCustomer.result} in their first 90 days.\`;
    }
  }

  // Add trigger events
  if (context.triggerEvent) {
    const triggerLine = generateTriggerLine(context.triggerEvent);
    email = email.replace('[trigger event]', triggerLine);
  }

  return email;
}

// Example personalized opening
function generatePersonalizedOpening(context) {
  const openings = [
    \`I saw \${context.company} just \${context.recentEvent} - congrats!\`,
    \`I noticed \${context.company} is hiring for \${context.jobPosting} - sounds like you're scaling!\`,
    \`Read your recent blog post on \${context.blogTopic} - great insights on \${context.takeaway}.\`,
    \`Saw \${context.company} mentioned in \${context.publication} - exciting times!\`
  ];

  // Return first applicable opening
  if (context.recentEvent) return openings[0];
  if (context.jobPosting) return openings[1];
  if (context.blogTopic) return openings[2];
  if (context.publication) return openings[3];

  return \`Hope you're doing well!\`; // Fallback
}
\`\`\`

## 5. Generate Subject Line Variations

Create 3-5 subject line options for A/B testing:

\`\`\`javascript
function generateSubjectLines(dealContext, emailType) {
  const subjects = {
    'initial': [
      \`Quick question about \${dealContext.painPoint}\`,
      \`\${dealContext.company} + \${ourCompany} ?\`,
      \`How \${similarCompany} saved \${result}\`,
      \`[First Name] - saw your \${recentActivity}\`,
      \`Reducing \${painPoint} by \${percentage}%\`
    ],
    'check-in': [
      \`Following up on \${lastTopic}\`,
      \`Quick update for \${dealContext.company}\`,
      \`Thoughts on \${lastDiscussion}?\`,
      \`[First Name] - new insight on \${painPoint}\`,
      \`Still interested in \${solution}?\`
    ],
    'proposal': [
      \`Thoughts on the proposal?\`,
      \`Following up: \${dealContext.company} proposal\`,
      \`Quick questions on proposal?\`,
      \`Ready to move forward?\`,
      \`[First Name] - proposal next steps\`
    ],
    'closing': [
      \`Ready to get started?\`,
      \`Next steps for \${dealContext.company}\`,
      \`Contract and kickoff timeline\`,
      \`Let's finalize the details\`,
      \`Starting \${dealContext.company} implementation\`
    ],
    're-engage': [
      \`Is this still a priority?\`,
      \`Checking in - \${dealContext.company}\`,
      \`Quick check-in, \${firstName}\`,
      \`Following up from \${lastContactDate}\`,
      \`New update: \${newFeature}\`
    ]
  };

  return subjects[emailType] || subjects['check-in'];
}

const subjectLineOptions = generateSubjectLines(dealContext, followUpType);
\`\`\`

## 6. Determine Optimal Send Time

\`\`\`javascript
function calculateOptimalSendTime(contactContext, previousEmails) {
  // Analyze when they typically open emails
  const openTimes = previousEmails
    .filter(e => e.opened)
    .map(e => new Date(e.openedAt).getHours());

  const avgOpenHour = openTimes.length > 0
    ? Math.round(openTimes.reduce((sum, h) => sum + h, 0) / openTimes.length)
    : 10; // Default to 10 AM

  // Best days to send (avoid Mondays, Fridays)
  const bestDays = [2, 3, 4]; // Tuesday, Wednesday, Thursday

  // Calculate next optimal send time
  const now = new Date();
  const nextSend = new Date(now);

  // Move to next optimal day
  while (!bestDays.includes(nextSend.getDay())) {
    nextSend.setDate(nextSend.getDate() + 1);
  }

  // Set to optimal hour
  nextSend.setHours(avgOpenHour, 0, 0, 0);

  return nextSend;
}

const optimalSendTime = calculateOptimalSendTime(contact, emailHistory);
console.log(\`Recommended send time: \${optimalSendTime}\`);
\`\`\`

## 7. Suggest Next Actions

\`\`\`javascript
function suggestNextActions(dealContext, followUpType) {
  const actions = {
    'initial': [
      { type: 'Email', timing: 'Send now', priority: 'High' },
      { type: 'LinkedIn Connection', timing: 'After email sent', priority: 'Medium' },
      { type: 'Follow-up Call', timing: '2 days if no response', priority: 'High' }
    ],
    'check-in': [
      { type: 'Send Email', timing: 'Now', priority: 'High' },
      { type: 'Schedule Call', timing: 'Suggest time in email', priority: 'High' },
      { type: 'Follow-up', timing: '3 days if no response', priority: 'Medium' }
    ],
    'proposal': [
      { type: 'Send Proposal Follow-Up', timing: 'Now', priority: 'High' },
      { type: 'Call to Discuss', timing: '1 day after email', priority: 'High' },
      { type: 'Final Follow-Up', timing: '1 week if no response', priority: 'Medium' }
    ],
    'closing': [
      { type: 'Send Contract', timing: 'Now', priority: 'High' },
      { type: 'Schedule Kickoff', timing: 'Once signed', priority: 'High' },
      { type: 'Intro to Customer Success', timing: 'Before go-live', priority: 'Medium' }
    ],
    're-engage': [
      { type: 'Send Re-Engagement Email', timing: 'Now', priority: 'Medium' },
      { type: 'Move to Nurture', timing: 'If no response in 1 week', priority: 'Low' },
      { type: 'Disqualify', timing: 'If no response in 2 weeks', priority: 'Low' }
    ]
  };

  return actions[followUpType] || actions['check-in'];
}

const nextActions = suggestNextActions(dealContext, followUpType);
\`\`\`

## 8. Generate Follow-Up Report

\`\`\`markdown
# Sales Follow-Up: \${CONTACT_NAME}

**Deal**: \${DEAL_NAME} (#\${DEAL_ID})
**Company**: \${COMPANY_NAME}
**Stage**: \${STAGE}
**Value**: $\${DEAL_VALUE}
**Days Since Last Contact**: \${DAYS_SINCE_CONTACT}

---

## Follow-Up Type: \${FOLLOW_UP_TYPE}

**Why**: \${REASON_FOR_TYPE}

---

## Recommended Email

**Subject Line Options** (A/B test):
1. \${SUBJECT_1} ← **Recommended**
2. \${SUBJECT_2}
3. \${SUBJECT_3}

**Email Body**:

\`\`\`
\${EMAIL_BODY}
\`\`\`

---

## Send Timing

**Optimal Send Time**: \${OPTIMAL_SEND_TIME}

**Why**: Based on \${CONTACT_NAME}'s email open patterns, they typically engage \${ENGAGEMENT_PATTERN}.

**Send Strategy**:
- ✅ **Best**: \${BEST_DAY} at \${BEST_TIME}
- ⚠️ **Avoid**: Mondays before 10 AM, Fridays after 3 PM

---

## Next Actions

| Action | Timing | Priority |
|--------|--------|----------|
${nextActions.map(a => \`| \${a.type} | \${a.timing} | \${a.priority} |\`).join('\\n')}

---

## Context Summary

**Last Interaction**: \${LAST_INTERACTION_TYPE} on \${LAST_INTERACTION_DATE}

**Topics Discussed**:
- \${TOPIC_1}
- \${TOPIC_2}
- \${TOPIC_3}

**Pain Points Identified**:
- \${PAIN_1}
- \${PAIN_2}

**Objections/Concerns**:
- \${OBJECTION_1}
- \${OBJECTION_2}

**Decision Timeline**: \${DECISION_TIMELINE}
**Budget**: \${BUDGET_STATUS}
**Stakeholders**: \${STAKEHOLDER_LIST}

---

## Follow-Up Cadence

If no response:
- **Day 3**: Follow-up email (brief, value-add)
- **Day 7**: Phone call
- **Day 14**: Final email (re-engage or disqualify)

---

## Approval

Review and approve before sending:

**Email Preview**: [Show above]

**Send Now** or **Schedule for \${OPTIMAL_SEND_TIME}**?

Use AskUserQuestion:
- Option 1: "Send now"
- Option 2: "Schedule for optimal time (\${OPTIMAL_SEND_TIME})"
- Option 3: "Edit email first"
- Option 4: "Skip this follow-up"
\`\`\`

## 9. Send Email via Zoho Mail

If approved:

\`\`\`bash
# Send email via Zoho Mail API
curl "https://mail.zoho.com/api/accounts/\${ACCOUNT_ID}/messages" \\
  -X POST \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "fromAddress": "'\${FROM_EMAIL}'",
    "toAddress": "'\${TO_EMAIL}'",
    "subject": "'\${SUBJECT}'",
    "content": "'\${EMAIL_BODY}'",
    "mailFormat": "plaintext"
  }'

# Log activity in Zoho CRM
curl "https://www.zohoapis.com/crm/v2/Deals/\${DEAL_ID}/Emails" \\
  -X POST \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_TOKEN}" \\
  -d '{
    "data": [{
      "Subject": "'\${SUBJECT}'",
      "Content": "'\${EMAIL_BODY}'",
      "Sent_Time": "'\$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "Type": "Follow-up"
    }]
  }'

echo "✓ Follow-up email sent to \${CONTACT_NAME}"
echo "✓ Activity logged in CRM"
\`\`\`

Save to: sales-follow-ups/follow-up-\${DEAL_ID}-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Auto-detect follow-up type
/sales/follow-up 12345

# Specific follow-up type
/sales/follow-up 12345 --type proposal

# Re-engagement email
/sales/follow-up 67890 --type re-engage

# Check-in email
/sales/follow-up 11111 --type check-in
```

## Follow-Up Types

**Initial**: First outreach to new lead
**Check-In**: Mid-conversation follow-up
**Proposal**: After sending proposal
**Closing**: Negotiation/finalizing deal
**Re-Engage**: Reviving stale deal (>14 days)

## Personalization Elements

- Contact's first name, title, company
- Recent company events (funding, hiring, news)
- Industry-specific pain points
- Similar customer success stories
- Previous conversation topics
- Trigger events (job postings, blog posts, news)

## Success Criteria

- ✓ Follow-up type detected
- ✓ Email personalized with context
- ✓ 3-5 subject line variations generated
- ✓ Optimal send time calculated
- ✓ Next actions suggested
- ✓ Human approval requested
- ✓ Email sent via Zoho Mail (if approved)
- ✓ Activity logged in CRM

## Best Practices

**Timing**:

- Wait 2-3 days after last contact
- Send Tuesday-Thursday, 10 AM - 2 PM
- Avoid Mondays before 10 AM, Fridays after 3 PM

**Personalization**:

- Reference specific conversation topics
- Add value (insight, resource, update)
- Keep it brief (< 150 words)

**Cadence**:

- Follow-up 1: 3 days after initial
- Follow-up 2: 7 days (phone call)
- Follow-up 3: 14 days (final re-engage or disqualify)

**Tone**:

- Helpful, not pushy
- Focused on their goals, not your product
- Make it easy to respond (yes/no questions)

---
**Uses**: agent-router (Zoho CRM, Zoho Mail, email generation)
**Output**: Personalized follow-up email + next actions
**Next Commands**: `/sales/pipeline` (review all follow-ups needed)
**Automation**: Can be triggered automatically for stale deals
