---
description: Generate sales proposal with ROI calculator and terms
argument-hint: <lead-id> [--type quote|contract|pilot]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Write, AskUserQuestion
---

Generate proposal for: **${ARGUMENTS}**

## Proposal Generation

**Executive Summary** - Business case in 1 page
**Problem/Solution Fit** - Their pain, our solution
**Scope of Work** - What's included
**Pricing Breakdown** - Transparent pricing
**ROI Calculator** - Quantified value
**Implementation Timeline** - What happens when
**Terms & Conditions** - Legal framework

Routes to **prompt-engineering-agent**:

```javascript
await Task({
  subagent_type: 'prompt-engineering-agent',
  description: 'Generate sales proposal',
  prompt: `Generate proposal for lead: ${LEAD_ID}

Type: ${TYPE || 'quote'}

Read lead data from Zoho CRM.
Read product pricing from products/[product]-pricing.md.

Generate comprehensive proposal document:

## PROPOSAL STRUCTURE

### Cover Page
- Prepared for: [Company Name]
- Attention: [Decision Maker Name, Title]
- Prepared by: [Your Company]
- Date: [Today's Date]
- Valid Until: [30 days from today]

### Executive Summary (1 page)

[Company] is facing [specific challenges] which is costing [time/money]. [Your Product] will solve this by [solution], delivering [quantified benefit].

**Investment**: $[Total]
**Expected ROI**: [X]x in [timeframe]
**Implementation**: [Timeline]

### Problem Statement

**Current State**:
- [Pain point 1 - quantified]
- [Pain point 2 - quantified]
- [Pain point 3 - quantified]

**Total Cost of Current Solution**: $[Amount]/month or [Hours]/month

### Proposed Solution

**[Your Product]** will:
1. [Benefit 1] → Saves [metric]
2. [Benefit 2] → Increases [metric]
3. [Benefit 3] → Reduces [metric]

**Key Features Included**:
- [Feature 1 relevant to their needs]
- [Feature 2 relevant to their needs]
- [Feature 3 relevant to their needs]

### Scope of Work

**What's Included**:
- [Product tier selected]
- [Number of seats/users]
- Onboarding and training
- Email/chat support
- [Additional services]

**What's NOT Included**:
- Custom development
- On-site training
- Dedicated account manager (Enterprise only)

### Pricing

**[Tier Name]** - $[Price]/month (or /year)

Breakdown:
- Base subscription: $[Amount]
- [Additional item if any]: $[Amount]
- Setup fee: $[Amount] (one-time)
- Training (optional): $[Amount]

**Subtotal**: $[Amount]
**Annual Prepay Discount** (if applicable): -$[Amount] (17%)
**Total**: $[Amount]

**Payment Terms**:
- Monthly/Annual billing
- Net 30 payment terms
- Credit card or invoice

### ROI Calculator

**Current State** (monthly):
| Item | Cost |
|------|------|
| Manual process time | [X hours] × $[hourly rate] = $[total] |
| Current software | $[amount] |
| Error/rework costs | $[amount] |
| **Total Current Cost** | **$[total]/month** |

**With [Product]** (monthly):
| Item | Savings |
|------|---------|
| Automation saves [X hours] | $[amount] |
| Replace current software | $[amount] |
| Reduce errors by [%] | $[amount] |
| **Total Savings** | **$[total]/month** |

**Investment**: $[your price]/month
**Net Benefit**: $[savings - price]/month
**ROI**: [X]x return
**Payback Period**: [X] months

### Implementation Timeline

**Week 1**:
- Kickoff call
- Account setup
- Initial training

**Week 2-3**:
- Data migration (if needed)
- Integration setup
- Team onboarding

**Week 4**:
- Go-live
- Post-launch support
- Success review

**Total Time to Value**: 30 days

### Success Metrics

We'll track:
- [Metric 1]: Target [value]
- [Metric 2]: Target [value]
- [Metric 3]: Target [value]

Review progress at 30, 60, 90 days.

### Why [Your Company]

**Proven Results**:
- [Customer 1] achieved [result]
- [Customer 2] achieved [result]
- [Customer 3] achieved [result]

**Support**:
- [Response time SLA]
- [Availability hours]
- [Dedicated support team]

### Terms & Conditions

**Contract Term**: 12 months (minimum)
**Auto-Renewal**: Yes (30-day notice to cancel)
**Data Ownership**: Customer retains all data
**SLA**: [Uptime guarantee]
**Cancellation**: 30-day notice required

### Next Steps

1. **Review this proposal** - Any questions? Let's discuss.
2. **Sign agreement** - We'll send DocuSign/Zoho Sign
3. **Kickoff** - Within 3 business days of signing
4. **Go-live** - 30 days from kickoff

### Signature

**Accepted By**:
Name: _______________________
Title: _______________________
Date: _______________________
Signature: _______________________

**[Your Company]**:
Name: [Your Name]
Title: [Your Title]
Date: [Today]
Signature: _______________________

---

**Questions?**
Email: [your@email.com]
Phone: [your phone]
Calendar: [booking link]

**Valid Until**: [30 days from today]

Generate complete proposal and save to: proposals/[company]-proposal-[date].md
  `
})
```

## Success Criteria

- ✓ Executive summary (1-page business case)
- ✓ Problem/solution fit clearly stated
- ✓ Transparent pricing breakdown
- ✓ ROI calculator with real numbers
- ✓ Implementation timeline provided
- ✓ Terms & conditions included
- ✓ Next steps clear
- ✓ Professional formatting
- ✓ Saved as PDF and sent for e-signature

---
**Uses**: prompt-engineering-agent
**Output**: Complete proposal (PDF) + Zoho Sign request
**Next Commands**: `/sales/follow-up`, `/sales/close`
