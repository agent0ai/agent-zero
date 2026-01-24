---
description: AI-powered lead qualification with enrichment and scoring
argument-hint: <email> [--source zoho|manual|import]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, AskUserQuestion
---

Qualify lead: **${ARGUMENTS}**

## Lead Qualification System

**Data Enrichment** - Clearbit/Hunter API for company data
**AI Scoring** - 4-dimension lead score (0-100)
**ICP Matching** - Ideal Customer Profile fit analysis
**Auto-Routing** - Hot/Warm/Cold classification with actions
**Zoho CRM Integration** - Create lead with enriched data

## Qualification Process

```javascript
await Task({
  subagent_type: 'agent-router',
  description: 'Qualify and score lead',
  prompt: `Qualify lead: ${EMAIL}

Execute comprehensive lead qualification:

## 1. Data Enrichment
- Email domain → Company lookup (Clearbit/Hunter)
- Extract: Company size, industry, revenue, tech stack
- LinkedIn profile analysis (if available)
- Website analysis (what tech they use)

## 2. Lead Scoring (0-100)

**Fit Score** (0-25): ICP Match
- Company size matches target? (+10)
- Industry matches? (+5)
- Tech stack compatible? (+5)
- Revenue range appropriate? (+5)

**Intent Score** (0-25): Buying Signals
- Multiple page views? (+10)
- Downloaded content? (+5)
- Pricing page visit? (+5)
- Demo request? (+5)

**Authority Score** (0-25): Decision Maker
- C-level / VP title? (+15)
- Director level? (+10)
- Manager / IC? (+5)
- Budget authority? (+10)

**Urgency Score** (0-25): Timeline
- Recent activity (last 24hrs)? (+10)
- Competitor research? (+5)
- Engaged with sales content? (+5)
- Specific deadline mentioned? (+5)

## 3. Classification

Total Score → Action:
- **90-100**: 🔥 Hot Lead → Immediate personal outreach
- **70-89**: ⚡ Warm Lead → Outreach within 24hrs
- **50-69**: 💡 Qualified → Add to nurture sequence
- **0-49**: ❄️ Cold → Long-term drip campaign

## 4. Recommended Actions

For each classification, provide:
- Next step (call, email, demo)
- Message template to use
- Timeline (immediate, 24hrs, this week)
- Success probability

## 5. Create in Zoho CRM

Request approval to create lead:
- Show enriched data
- Display score breakdown
- Suggest lead owner assignment
- Propose follow-up workflow

After approval, create lead in Zoho CRM with all data.
  `
})
```

## Example Output

```
Lead Qualification Report
═══════════════════════════════════
Lead: john.smith@acme.com
Company: Acme Corp

Enriched Data:
  • Company Size: 50-200 employees ✓ Matches ICP
  • Industry: SaaS / B2B Software ✓ Perfect fit
  • Revenue: $5M-$10M (estimated)
  • Tech Stack: React, AWS, Stripe ✓ Compatible
  • Location: San Francisco, CA
  • Website: acme.com

Lead Profile:
  • Name: John Smith
  • Title: VP of Engineering ✓ Decision maker
  • LinkedIn: linkedin.com/in/johnsmith
  • Twitter: @johnsmith (500 followers)

Activity:
  • First Visit: 3 days ago
  • Page Views: 7 pages
  • Key Pages: Pricing (3x), Docs, Demo
  • Downloads: Whitepaper, Case Study
  • Referrer: Google search "AI code review tools"

Lead Score: 87/100 🔥 HOT LEAD
═══════════════════════════════════
Fit Score: 23/25 ✓ Excellent ICP match
  • Company size matches (50-200 employees) [10]
  • Industry perfect fit (SaaS) [5]
  • Tech stack compatible (React/AWS) [5]
  • Revenue appropriate ($5-10M) [3]

Intent Score: 22/25 ⚡ High buying intent
  • Multiple pricing page views [10]
  • Downloaded 2 resources [5]
  • Viewed demo page [5]
  • Recent activity (last 24hrs) [2]

Authority Score: 22/25 ✓ Decision maker
  • VP-level title [15]
  • Engineering department [5]
  • Budget authority (likely) [2]

Urgency Score: 20/25 📅 Active evaluation
  • Activity in last 3 days [5]
  • Competitor comparison searches [5]
  • Engaged with ROI calculator [5]
  • Timeline: 30-60 days (estimated) [5]

═══════════════════════════════════
Recommended Action: IMMEDIATE OUTREACH

Next Steps:
1. Personal email from founder (use /sales/outreach)
2. Offer exclusive demo within 24 hours
3. Mention specific pages viewed (pricing, docs)
4. Include custom ROI analysis for Acme

Success Probability: 65% (close within 60 days)
Expected Deal Size: $5,000-$10,000 ARR

[Create Lead in Zoho CRM]
[Send Personalized Outreach]
[Schedule Follow-up Task]
```

## Success Criteria

- ✓ Lead data enriched from external sources
- ✓ Comprehensive 4-dimension score calculated
- ✓ Clear classification (Hot/Warm/Qualified/Cold)
- ✓ Specific next actions recommended
- ✓ Lead created in Zoho CRM (after approval)
- ✓ Follow-up tasks automatically created

---
**Uses**: agent-router
**Output**: Lead qualification report + Zoho CRM lead
**Next Commands**: `/sales/outreach`, `/sales/demo-prep`
