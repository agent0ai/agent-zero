---
description: Generate AI-powered product summaries for different audiences and channels
argument-hint: <product-name> [--length short|medium|long] [--audience founder|investor|customer|developer]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Write
---

Generate product summary: **${ARGUMENTS}**

## Summary Types

**Elevator Pitch** (30 seconds) - Quick verbal pitch
**Sales Email** (150 words) - Cold outreach email
**Landing Page Copy** - Hero, features, benefits, CTA
**Product Hunt Description** (260 chars) - Launch announcement
**LinkedIn Post** - Social media version with hooks
**Technical Documentation** - For developer audiences
**Investor Pitch** - For fundraising presentations

## Generate Summaries

Routes to **prompt-engineering-agent** for copywriting:

```javascript
await Task({
  subagent_type: 'prompt-engineering-agent',
  description: 'Generate product marketing copy',
  prompt: `Generate marketing copy for product: ${PRODUCT_NAME}

Audience: ${AUDIENCE || 'customer'}
Length: ${LENGTH || 'medium'}

Read product definition from: products/${PRODUCT_NAME}-definition.md

Generate the following summaries:

## 1. Elevator Pitch (30 seconds)
[Product Name] helps [target customer] [solve problem] by [unique solution]. Unlike [competitors], we [key differentiator]. [Impressive metric or result].

## 2. Sales Email Subject Lines (5 variants)
1. [Benefit-driven subject]
2. [Question-based subject]
3. [Curiosity-driven subject]
4. [Social proof subject]
5. [Urgency subject]

## 3. Sales Email Body (150 words)
Hi [First Name],

[Opening hook - problem or pain point]

[Introduce solution]

[Key benefit with proof point]

[Call to action]

Best,
[Your Name]

## 4. Landing Page Copy

**Hero Headline**: [Benefit-driven, 6-12 words]
**Sub-headline**: [How it works, 15-25 words]
**CTA Button**: [Action-oriented, 2-4 words]

**Features Section** (3-5 features):
For each feature:
- Feature Name (2-4 words)
- Benefit (one sentence)
- Icon suggestion

**Social Proof**:
- Testimonial template
- Key metrics to highlight

## 5. Product Hunt Description (260 characters max)
[Hook] [What it does] [Key benefit] [Differentiator]

## 6. LinkedIn Post (with hooks)
[Attention-grabbing opening]

[Problem statement]

[Solution introduction]

[Key benefits]

[Call to action]

[Relevant hashtags]

## 7. Technical Documentation (for developers)
**Overview**: [Technical description]
**Key Features**: [Developer-focused features]
**Integration**: [How it integrates]
**API**: [API availability]

Save all summaries to: products/${PRODUCT_NAME}-summaries.md
  `
})
```

## Example Output

```markdown
# AI Meeting Assistant - Marketing Copy

## Elevator Pitch
AI Meeting Assistant helps busy executives reclaim 10 hours per week by automatically transcribing, summarizing, and extracting action items from every meeting. Unlike traditional note-taking tools, our AI understands context and follows up automatically. Our customers close deals 30% faster with perfect meeting follow-through.

## Sales Email Subject Lines
1. Reclaim 10 hours/week from meetings?
2. Question: How do you track meeting action items?
3. The meeting tool your competitors don't want you to know about
4. How [Company Name] closed 30% more deals
5. Last chance: Meeting AI early access ends Friday

## Sales Email (Cold Outreach)
Hi John,

I noticed your team at Acme scaled to 50+ people recently—congrats! But I'm guessing your calendar is now back-to-back meetings, and important action items are slipping through the cracks.

AI Meeting Assistant automatically captures, summarizes, and follows up on every meeting. No more "wait, what did we decide?" or forgotten tasks.

VP Engs like you are saving 10+ hours/week and closing deals 30% faster because nothing falls through the cracks.

Want a 10-minute demo? I can show you exactly how it works with your actual calendar.

Best,
[Your Name]

## Landing Page Copy

### Hero Section
**Headline**: Never miss a meeting action item again
**Sub-headline**: AI-powered meeting assistant that automatically captures decisions, extracts action items, and follows up—so you can focus on the conversation, not taking notes.
**CTA**: Start Free Trial →

### Features
1. **Auto-Transcription**
   Real-time transcription with speaker identification. Works with Zoom, Meet, Teams.

2. **Smart Summaries**
   Get a 5-minute meeting summarized in 30 seconds. AI extracts key decisions and action items.

3. **Automatic Follow-up**
   AI drafts and sends follow-up emails with action items to all attendees. Set it and forget it.

4. **CRM Integration**
   Syncs meeting notes and tasks to Salesforce, HubSpot, or Zoho CRM automatically.

5. **Analytics**
   Track meeting effectiveness, time spent in meetings, and follow-through rates.

### Social Proof
"AI Meeting Assistant helped us close 30% more deals by ensuring perfect follow-through on every sales call."
— Sarah Chen, VP Sales at TechCorp

**Metrics to Highlight**:
- 10,000+ meetings transcribed daily
- 4.9/5 average rating
- 10 hours saved per user per week

## Product Hunt Description
AI Meeting Assistant auto-transcribes, summarizes & follows up on meetings. Never forget action items again. Works with Zoom/Meet/Teams. 10hrs/week saved. 30% faster deal cycles. Try free →

## LinkedIn Post
Ever finish a meeting and think "wait, what did we decide?"

You're not alone. The average exec spends 23 hours/week in meetings, but 40% of action items are forgotten within 24 hours.

That's $2,400/week in wasted meeting time per person.

We built AI Meeting Assistant to solve this:
✅ Auto-transcribes every meeting
✅ Extracts decisions & action items
✅ Sends follow-up emails automatically
✅ Syncs to your CRM

Result? Our customers save 10 hours/week and close deals 30% faster.

Try it free for 14 days (no credit card needed):
[link]

#ProductivityHacks #SalesTech #AITools #MeetingManagement

## Technical Documentation
**Overview**: REST API and WebSocket integration for real-time meeting transcription and analysis.

**Key Features**:
- Real-time WebSocket transcription stream
- Speaker diarization with 95%+ accuracy
- Named entity recognition for action items
- Webhook notifications for meeting events
- OAuth 2.0 authentication

**Integration**:
```javascript
import { MeetingAI } from '@meeting-ai/sdk';

const client = new MeetingAI({ apiKey: process.env.API_KEY });

// Start transcription
const session = await client.transcribe({
  meetingId: 'zoom-meeting-123',
  language: 'en-US'
});

// Get summary
const summary = await client.summarize(session.id);
```

**API Documentation**: <https://docs.meetingai.com>

```

## Commands

**`/product/summarize "AI Meeting Assistant"`** - All summaries
**`/product/summarize "AI Meeting Assistant" --length short`** - Concise versions
**`/product/summarize "AI Meeting Assistant" --audience investor`** - Investor pitch
**`/product/summarize "AI Meeting Assistant" --audience developer`** - Technical docs

## Success Criteria

- ✓ Elevator pitch under 30 seconds
- ✓ 5 email subject line variants
- ✓ Sales email under 150 words
- ✓ Landing page copy (hero, features, social proof)
- ✓ Product Hunt description under 260 chars
- ✓ LinkedIn post with engagement hooks
- ✓ Technical documentation (if developer audience)
- ✓ All summaries saved to file

---
**Uses**: prompt-engineering-agent
**Input**: Product definition file
**Output**: Marketing copy file (products/[name]-summaries.md)
**Next Commands**: `/landing/create`, `/sales/outreach`
