---
description: Generate personalized sales outreach emails with AI
argument-hint: <lead-email> [--template cold|warm|demo|followup]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, AskUserQuestion
---

Generate sales outreach: **${ARGUMENTS}**

## Outreach Generation

**Personalized at Scale** - Founder-quality emails, AI-generated
**Multiple Channels** - Email, LinkedIn, Twitter DM
**Follow-up Sequences** - 3-5 email sequence with timing
**A/B Testing** - Multiple subject line variants
**Compliance** - CAN-SPAM compliant with unsubscribe

## Generate Outreach

```javascript
await Task({
  subagent_type: 'prompt-engineering-agent',
  description: 'Generate personalized sales outreach',
  prompt: `Generate personalized outreach for: ${LEAD_EMAIL}

Template type: ${TEMPLATE || 'cold'}

Read lead data from Zoho CRM.
Read product summary from products/[product]-summaries.md

Generate personalized outreach:

## 1. Research Summary
- Company: [Name, size, industry]
- Lead: [Name, title, LinkedIn activity]
- Trigger: [Why reaching out now]
- Pain Point: [Specific problem they likely have]

## 2. Email Subject Lines (5 variants)
1. [Benefit-driven]: Focus on outcome
2. [Question-based]: Ask about pain point
3. [Curiosity]: Intriguing statement
4. [Social proof]: Mention similar customer
5. [Personalized]: Reference specific activity

## 3. Email Body (personalized)

Template: ${TEMPLATE}

Cold Email Structure:
- Line 1: Personalized observation (company news, LinkedIn activity)
- Line 2-3: Identify pain point (relevant to their role/company)
- Line 4-5: Introduce solution briefly
- Line 6: Social proof (similar company result)
- Line 7: Soft CTA (ask question or offer demo)
- P.S.: Value-add (free resource, analysis)

Keep under 150 words, 5-7 sentences max.

## 4. Follow-up Sequence
Day 0: Initial email
Day 3: Value-add follow-up (send case study)
Day 7: Social proof (customer testimonial)
Day 14: Break-up email (last chance)
Day 21: Re-engagement (new angle)

## 5. LinkedIn Message (if applicable)
Shorter version for LinkedIn InMail (300 char limit).

## 6. Compliance Check
- Includes company name and address
- Has unsubscribe link
- Accurate from address
- CAN-SPAM compliant

Show preview and request approval before sending.
  `
})
```

## Success Criteria

- ✓ 5 subject line variants generated
- ✓ Personalized email body (under 150 words)
- ✓ 3-5 email follow-up sequence
- ✓ LinkedIn message variant
- ✓ CAN-SPAM compliance verified
- ✓ Preview shown for approval
- ✓ Sent via Zoho Mail (after approval)
- ✓ Opens/clicks tracked in CRM

---
**Uses**: prompt-engineering-agent
**Input**: Lead data from Zoho CRM
**Output**: Personalized outreach email + sequence
**Next Commands**: `/sales/follow-up`, `/sales/demo-prep`
