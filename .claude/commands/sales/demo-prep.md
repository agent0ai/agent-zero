---
description: Prepare for sales demo with AI-powered research and script
argument-hint: <lead-id-or-email>
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Bash
---

Prepare demo for: **${ARGUMENTS}**

## Demo Preparation

**Company Research** - Deep dive into prospect's business
**Pain Point Analysis** - Identify specific challenges
**Custom Demo Script** - Tailored presentation flow
**Objection Handling** - Anticipate and prepare responses
**Success Story Matching** - Find similar customer wins

Routes to **agent-router**:

```javascript
await Task({
  subagent_type: 'agent-router',
  description: 'Prepare sales demo',
  prompt: `Prepare demo for lead: ${LEAD_ID}

Read lead data from Zoho CRM (email, company, title, activity).

Generate comprehensive demo preparation:

## 1. Company Research Summary
- Company overview (size, industry, funding)
- Recent news (acquisitions, launches, challenges)
- Tech stack (what they currently use)
- Competitors they're similar to

## 2. Lead Profile
- Name, title, department
- LinkedIn activity
- Pages visited on our site
- Content downloaded
- Pain points inferred from activity

## 3. Custom Demo Script (30-45 minutes)

**Opening** (5 min):
- Intro and build rapport
- Confirm their pain point
- Set agenda and time check

**Discovery Questions** (10 min):
- What's your current process for [X]?
- What's working well? What's not?
- What would success look like?
- What's your timeline for solving this?

**Demo Flow** (20 min):
Focus on THEIR pain points, not all features:
- Start with their biggest pain point
- Show solution to that specific problem
- Demo 2-3 key features that solve their needs
- Keep it concise, interactive

**Next Steps** (5 min):
- Answer questions
- Discuss pricing/fit
- Propose trial or next meeting
- Send follow-up resources

## 4. Objection Handling

Common objections with responses:
- "Too expensive" → ROI calculator, pilot program
- "Need more time" → Urgency framing, competitor risk
- "Need to think about it" → Address real concern
- "Not a priority" → Quantify cost of delay

## 5. Similar Success Stories

Find 2-3 customers similar to this prospect:
- Same industry
- Similar company size
- Comparable use case
- Impressive results (metrics)

Format: "[Company] reduced [pain point] by [metric] using [Product]"

## 6. Demo Checklist

**Pre-Demo**:
- [ ] Test demo environment working
- [ ] Prepare custom demo data (their company name, industry examples)
- [ ] Calendar invite sent with agenda
- [ ] Demo link ready (Zoom/Meet)
- [ ] Backup plan if tech fails

**During Demo**:
- [ ] Screen share ready
- [ ] Demo script open (but don't read from it)
- [ ] Customer success story ready
- [ ] Pricing sheet ready

**Post-Demo**:
- [ ] Send follow-up email within 1 hour
- [ ] Include: Recap, next steps, resources
- [ ] Update CRM with demo notes
- [ ] Schedule follow-up task

Generate complete demo prep document.
  `
})
```

## Success Criteria

- ✓ Company research summary generated
- ✓ Lead profile analyzed (pain points identified)
- ✓ Custom demo script created (30-45 min flow)
- ✓ Objection responses prepared
- ✓ 2-3 relevant success stories identified
- ✓ Demo checklist provided
- ✓ All prep materials in one document

---
**Uses**: agent-router
**Output**: Demo prep document
**Next Commands**: `/sales/proposal`, `/sales/follow-up`
