---
description: Real-time note-taking with action item extraction
argument-hint: [--meeting <title>] [--template <standard|sales|technical|interview>] [--auto-transcribe]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Meeting Notes - AI-Powered Note-Taking & Action Item Extraction

## Overview

Meeting Notes is an intelligent real-time note-taking system that captures key discussion points, decisions, action items, and next steps during meetings. It transforms scattered notes into structured, actionable documents while you focus on the conversation.

For solo entrepreneurs juggling multiple roles, taking thorough notes while actively participating in meetings is nearly impossible. This system handles note-taking so you can be fully present, then automatically extracts action items, assigns owners, sets deadlines, and generates follow-up tasks.

**ROI: $35,000/year** through reduced meeting follow-up time (10 hours/month saved), fewer missed action items (preventing costly delays and dropped balls), improved meeting accountability, and better decision documentation for future reference.

## Key Benefits

**Full Meeting Presence**

- Actively participate without splitting attention between conversation and notes
- Maintain eye contact and engagement with participants
- Capture discussion nuances (tone, concerns, enthusiasm) you'd miss while typing
- Ask better questions because you're listening, not transcribing

**Structured Documentation**

- Convert messy real-time notes into organized, readable documents
- Standardized format makes information easy to find later
- Key decisions, action items, and next steps prominently highlighted
- Meeting context preserved for team members who weren't present

**Automatic Action Item Extraction**

- AI identifies commitments, tasks, and next steps from discussion
- Action items assigned to specific owners with clear accountability
- Deadlines extracted or suggested based on context
- Follow-up tasks automatically created in task management system

**Searchable Knowledge Base**

- All meeting notes stored in centralized, searchable repository
- Find previous discussions, decisions, or commitments instantly
- Track pattern of topics across multiple meetings
- Reference history when similar issues arise in future

## Implementation Steps

### Step 1: Start Meeting Notes Session

Initiate note-taking during or immediately after meeting:

```bash
# During meeting - real-time capture
/meeting:notes --meeting "Board Meeting Q1 2024" --template standard

# After meeting - structured documentation from rough notes
/meeting:notes --meeting "Client Call - TechCorp" --template sales --source notes.txt

# With auto-transcription (if supported)
/meeting:notes --auto-transcribe --meeting "Investor Pitch - Sequoia" --template investor

# Technical deep-dive meeting
/meeting:notes --meeting "Architecture Review" --template technical
```

The system will:

- Create structured note template based on meeting type
- Prompt for key information (participants, date, objectives)
- Provide interface for real-time note capture
- Automatically save and backup notes continuously

### Step 2: Capture Meeting Notes (Real-Time or Batch)

**Real-Time Capture Mode:**
System provides structured prompts during meeting:

```
Meeting Notes: Board Meeting Q1 2024
===========================================

Participants: [Auto-filled from calendar]
- John Smith (CEO) - Present
- Sarah Johnson (CFO) - Present
- Michael Lee (Board Member, Sequoia) - Present
- Emily Chen (Board Observer) - Present

Meeting Objective:
> Q1 performance review and strategic planning for Q2

=== DISCUSSION SECTION 1: Q1 Performance Review ===
[Capture key points below]

> Revenue: $485K MRR (target was $500K, missed by 3%)
> Churn: 4.2% monthly (up from 3.8% last quarter - concerning trend)
> New customers: 47 (target was 50, close)
> Team: Hired 3 engineers, still need VP Sales

Michael Lee comment: "Churn increase is worrying. What's the root cause?"
CEO response: "Two factors: (1) early customers outgrowing us, (2) some bad-fit deals to hit numbers"

Decision: Focus on customer success and qualification, not just growth
Action: Sarah to analyze churn cohorts and present at next board meeting

=== DISCUSSION SECTION 2: Q2 Strategy ===
[Capture key points below]

> Focus: Improve retention over growth for Q2
> Target: Reduce churn to 3% monthly
> Initiatives: (1) Customer success team (hire 2), (2) Better onboarding, (3) Stricter qualification

Emily question: "How does this affect revenue targets?"
CEO: "We'll grow slower (15% vs 20%) but with better foundation"

Board vote: Approved Q2 strategy (unanimous)
Action: CEO to send updated Q2 plan by Friday

=== NEXT STEPS ===
[Action items auto-extracted, verify and assign]

1. Sarah (CFO): Analyze churn by cohort, identify patterns - Due: Next board meeting
2. CEO: Send updated Q2 plan to board - Due: Friday, March 15
3. CEO: Hire 2 customer success team members - Due: End of Q1
4. Board: Review Q2 plan async and provide feedback - Due: Weekend after Friday send

Next Meeting: April 15, 2024 @ 2:00 PM PST
```

**Batch Processing Mode (Post-Meeting):**
If you captured rough notes during meeting, system structures them:

```
Input (Your Rough Notes):
--------------------------
board meeting today
john, sarah, michael, emily present

q1 numbers:
- 485K MRR (missed 500K target)
- churn up to 4.2%, bad sign
- 47 new customers
- hired 3 engineers

michael concerned about churn
- early customers outgrowing us
- some bad fits to hit numbers
- need focus on retention

q2 strategy approved:
- focus retention over growth
- target 3% churn
- hire 2 CS people
- better onboarding

actions:
- sarah analyze churn cohorts (next meeting)
- CEO send q2 plan (friday)
- hire CS team (end of q1)

next meeting april 15 @ 2pm

Output (Structured Notes):
--------------------------
[System generates same structured format as real-time example above]
```

### Step 3: AI-Enhanced Note Structuring

System automatically enhances raw notes with:

**Context Addition:**

- Links to previous meeting notes with same participants
- References to related documents or decisions
- Background on topics discussed (from company knowledge base)
- Relevant metrics or data mentioned (pulled from dashboards)

**Clarification & Expansion:**

- Expands abbreviations and shorthand into full phrases
- Adds context for ambiguous pronouns or references
- Identifies and clarifies technical terms or jargon
- Fills in implied information from discussion context

**Organization & Formatting:**

- Groups related discussion points into coherent sections
- Sequences topics in logical order (may differ from actual meeting flow)
- Highlights key decisions, concerns, and agreements
- Creates visual hierarchy with headers, bullets, and emphasis

**Action Item Extraction:**

- Identifies all commitments made during meeting
- Assigns to specific person (explicit or inferred)
- Extracts or infers deadline based on context
- Tags with priority level (urgent, important, routine)
- Links to related projects or goals

**Example Enhancement:**

```
Raw Note:
"michael worried about churn"

Enhanced:
Michael Lee (Board Member, Sequoia Capital) expressed concern about the increase in monthly churn rate from 3.8% (Q4 2023) to 4.2% (Q1 2024). This represents a 10.5% relative increase and could impact the company's ability to reach cash flow positive status by Q4 2024 as planned.

Related:
- Previous discussion on churn (Board Meeting Dec 2023): Link
- Q4 2024 cash flow positive target (Strategic Plan): Link
- Customer success initiative proposal (Exec Team Meeting Feb 2024): Link
```

### Step 4: Automatic Action Item Extraction

System identifies and structures all commitments:

**Action Item Components:**

1. **Task Description**: Clear, actionable statement of what needs to be done
2. **Owner**: Person responsible for completion (explicit or inferred)
3. **Deadline**: Due date (explicit, inferred, or suggested)
4. **Priority**: Urgency and importance assessment
5. **Dependencies**: Other tasks that must complete first
6. **Context**: Why this matters, background, related decisions

**Example Action Item Extraction:**

```
From Discussion:
"Sarah, can you pull together a churn analysis by customer cohort and present it at the next board meeting? We need to understand if this is a product issue, customer success issue, or sales qualification issue."

Extracted Action Item:
-----------------------
Task: Analyze customer churn by cohort (sign-up date, customer segment, ACV, product usage) and identify root cause patterns. Prepare presentation for board review.

Owner: Sarah Johnson (CFO)

Deadline: April 15, 2024 (next board meeting)

Priority: HIGH
- Critical for Q2 strategic planning
- Board concern requiring immediate attention
- Affects hiring and budget decisions

Dependencies:
- Access to churn data (available in Salesforce)
- Customer usage metrics (available in Mixpanel)
- May need engineering support for data extraction

Deliverable:
- Presentation deck with churn analysis
- Recommendations for retention improvement
- Resource requirements (budget, headcount) to implement solutions

Context:
Churn increased from 3.8% to 4.2% in Q1, raising board concerns. Michael Lee specifically flagged this as potential risk to Q4 cash flow positive target. Analysis will inform whether Q2 focus should be customer success, sales qualification, or product improvements.

Related Discussions:
- Q1 Performance Review (this meeting)
- Q2 Strategy Discussion (this meeting)
- Q4 Cash Flow Positive Target (Strategic Plan 2024)
```

**Action Item Categories:**

- **Deliverables**: Documents, presentations, analyses to produce
- **Decisions**: Approvals, sign-offs, choices to be made
- **Communication**: Emails to send, calls to make, updates to share
- **Research**: Information to gather, questions to answer
- **Tasks**: Specific work to complete (hiring, implementation, etc.)
- **Follow-ups**: Check-ins, status updates, recurring items

### Step 5: Decision Documentation

Capture and highlight key decisions made:

**Decision Format:**

```
DECISION: Focus Q2 on customer retention over growth

Context:
Q1 churn increased to 4.2%, raising concerns about growth sustainability. Board debated whether to continue aggressive growth targets or slow down to improve retention.

Discussion Points:
- Pro growth: Market opportunity window may close, competitors raising funds
- Pro retention: High churn makes growth expensive, risks long-term viability
- Compromise: Modest growth (15%) while investing heavily in retention

Decision Maker: Board of Directors (unanimous vote)

Rationale:
Sustainable growth at 15% with 3% churn is better foundation than 20% growth with 4%+ churn. Current trajectory risks customer base churning faster than we can replace, making profitability impossible.

Impact:
- Q2 revenue target: $560K MRR (15% growth vs 20% planned)
- Hiring: Prioritize 2 CS hires over 2 sales hires
- Product: Focus engineering time on retention features vs new feature development
- Board expectations reset: Retention metrics > growth metrics for Q2

Related Actions:
- Update Q2 plan to reflect retention focus (CEO, Due Friday)
- Hire customer success team (CEO, Due end of Q1)
- Churn analysis to inform CS strategy (CFO, Due next board meeting)

Reversal Conditions:
If churn returns to <3.5% by end of Q2, return to aggressive growth stance for Q3.
```

**Decision Categories:**

- **Strategic**: Major direction changes, priorities, focus areas
- **Financial**: Budget allocations, pricing changes, investment decisions
- **Personnel**: Hiring, firing, promotions, org structure
- **Product**: Feature prioritization, technical direction, architecture
- **Partnerships**: Vendor selection, partnership terms, integrations
- **Process**: Operational changes, policy updates, workflow modifications

### Step 6: Participant Insights & Sentiment

Track participant engagement and sentiment:

**Participant Analysis:**

```
Michael Lee (Board Member, Sequoia Capital)
-------------------------------------------
Engagement: HIGH (asked 8 questions, made 5 comments)
Sentiment: CONCERNED (about churn, cautiously supportive of retention strategy)

Key Themes:
- Churn trajectory and sustainability (mentioned 4 times)
- Comparison to portfolio companies (referenced 2 similar situations)
- Long-term profitability path (asked about path to cash flow positive)

Notable Quotes:
- "Churn increase is worrying. What's the root cause?"
- "I've seen this pattern before - grow fast, then hit wall with retention"
- "Smart to focus on retention now rather than 12 months from now when it's crisis"

Action Items Assigned: None (board member, advisor role)

Follow-up Needed:
- Share customer success hiring plan (addresses his concerns)
- Monthly churn metric updates (keep him informed on improvement)
```

**Overall Meeting Sentiment:**

- Tone: Serious, constructive
- Energy: Medium (concern about metrics, but optimism about strategy)
- Agreement Level: High (unanimous decision, aligned on priorities)
- Concerns Raised: Churn trajectory, competitive pressure, hiring timeline
- Opportunities Identified: Retention focus could improve unit economics significantly

### Step 7: Create Meeting Summary

Generate executive summary for quick reference:

**Meeting Summary Template:**

```
MEETING SUMMARY: Board Meeting Q1 2024
Date: March 10, 2024
Duration: 90 minutes
Participants: John Smith (CEO), Sarah Johnson (CFO), Michael Lee (Board Member), Emily Chen (Board Observer)

=== KEY TAKEAWAYS ===

1. Q1 Performance: Missed revenue target by 3% ($485K vs $500K MRR), churn increased to 4.2%

2. Board Concern: Churn trajectory unsustainable, risks long-term viability despite strong growth

3. Strategic Shift: Q2 will prioritize retention over growth (15% growth target vs 20%)

4. Major Decisions:
   - Focus Q2 on reducing churn to 3% monthly
   - Hire 2 customer success team members (prioritize over sales hires)
   - Engineering focus: Retention features > new feature development

5. Critical Action Items:
   - CFO to analyze churn patterns and present at next meeting
   - CEO to send updated Q2 plan by Friday
   - Hire customer success team by end of Q1

=== SENTIMENT & DYNAMICS ===

Board is supportive of leadership team but concerned about churn trend. Michael Lee (Sequoia) drew parallels to portfolio companies that struggled with similar patterns. Decision to slow growth and focus on retention was unanimous and supported by board's experience.

Emily Chen (observer) asked good questions about revenue impact of slower growth—shows she's engaged and thinking strategically. Consider inviting her to more operational meetings.

=== NEXT MEETING ===

Date: April 15, 2024 @ 2:00 PM PST
Agenda Preview:
- Q1 final results and Q2 progress (1 month in)
- Churn analysis presentation (Sarah)
- Customer success team update (hiring, onboarding, early wins)
- Q2 strategic initiatives review

=== DECISIONS LOG ===

1. Q2 Strategy: Focus retention over growth (Board Vote: Unanimous)
2. Q2 Revenue Target: $560K MRR (15% growth) - Approved
3. Hiring Priority: 2 CS team members before additional sales hires - Approved

=== ACTION ITEMS (4 Total) ===

HIGH PRIORITY (2):
1. Sarah Johnson: Churn cohort analysis → Due: April 15 (Next Board Meeting)
2. John Smith: Updated Q2 plan → Due: Friday, March 15

MEDIUM PRIORITY (2):
3. John Smith: Hire 2 CS team members → Due: March 31 (End of Q1)
4. Board Members: Review Q2 plan and provide async feedback → Due: March 16-17

=== RESOURCES & LINKS ===

- Q1 Performance Dashboard: [Link]
- Q2 Strategic Plan (Draft): [Link]
- Previous Board Meeting Notes (Dec 2023): [Link]
- Customer Churn Data (Salesforce): [Link]
```

### Step 8: Action Item Integration

Export action items to task management system:

**Integration Options:**

- Todoist, Asana, Trello for personal task management
- Jira, Linear, ClickUp for team project management
- Google Tasks, Microsoft To-Do for calendar integration
- Notion, Coda for knowledge base task embedding

**Export Format:**

```
Action Item Export → Asana

Project: Board of Directors
Section: Q1 2024 - March Meeting

Task 1: Churn Cohort Analysis for Board
Assignee: Sarah Johnson
Due Date: April 15, 2024
Priority: High
Description:
Analyze customer churn by cohort (sign-up date, segment, ACV, usage) and identify root cause patterns. Prepare presentation deck for board review at April 15 meeting.

Board is concerned about churn increase from 3.8% to 4.2%. Analysis should answer: Is this product issue, CS issue, or sales qualification issue?

Deliverables:
- Churn analysis by cohort
- Root cause identification
- Retention improvement recommendations
- Resource requirements (budget/headcount)

Subtasks:
- [ ] Extract churn data from Salesforce
- [ ] Pull usage metrics from Mixpanel
- [ ] Analyze patterns by cohort
- [ ] Identify root causes
- [ ] Develop recommendations
- [ ] Create presentation deck
- [ ] Review with CEO before board meeting

Related: Q1 Board Meeting Notes [Link]

---

Task 2: Updated Q2 Strategic Plan
Assignee: John Smith
Due Date: March 15, 2024 (Friday)
Priority: High
Description:
Update Q2 strategic plan to reflect board decision: Focus on retention over growth. Send to board for async review over weekend.

Key changes:
- Revenue target: $560K MRR (15% growth vs 20%)
- Hiring: Prioritize 2 CS hires over sales hires
- Product: Focus retention features over new development
- Success metrics: Churn reduction to 3% monthly

Deliverable: Updated Q2 plan document shared with board by EOD Friday

Related: Q1 Board Meeting Notes [Link]

---

[Additional tasks formatted similarly]
```

### Step 9: Meeting Notes Storage & Search

Store notes in centralized, searchable repository:

**Storage Options:**

- Google Drive folder structure (Meetings / Board / 2024 / Q1)
- Notion database with tags and filters
- Confluence wiki with hierarchy
- Dedicated meeting notes app (Fellow, Hugo, Grain)
- Company knowledge base (Guru, Slab, Tettra)

**Metadata for Search:**

- Meeting type (board, client, team, investor, partner)
- Participants (names, roles, companies)
- Date and duration
- Key topics discussed
- Decisions made
- Action items and owners
- Related projects or initiatives
- Tags (strategy, product, sales, hiring, etc.)

**Search Capabilities:**

```bash
# Find all meetings with specific participant
search:meetings participant:"Michael Lee"

# Find meetings where specific topic discussed
search:meetings topic:"churn" OR topic:"retention"

# Find all action items assigned to person
search:action-items owner:"Sarah Johnson" status:open

# Find decisions made in date range
search:decisions date:2024-01-01..2024-03-31 type:strategic

# Find meetings by type
search:meetings type:board date:2024
```

### Step 10: Meeting Notes Review & Improvement

Continuously improve note quality and process:

**Post-Meeting Review:**

- Read through notes within 24 hours while memory is fresh
- Fill in any gaps or clarify ambiguous points
- Verify action items are correctly assigned and scoped
- Confirm deadlines are realistic and agreed-upon
- Add any post-meeting insights or realizations

**Pattern Analysis:**

- Review notes from past 3 months quarterly
- Identify recurring topics or unresolved issues
- Track action item completion rate by owner
- Note which meeting types produce best outcomes
- Identify meetings that could have been emails

**Template Refinement:**

- Customize note templates based on meeting type
- Add prompts for information frequently forgotten
- Remove sections that are never used
- Adjust format based on stakeholder feedback
- Create new templates for recurring meeting patterns

**Continuous Improvement:**

- Survey meeting participants on note quality
- Compare note-taking methods (real-time vs batch)
- Experiment with transcription tools
- Benchmark note-taking speed and completeness
- Train team members on consistent note format

## Usage Examples

### Example 1: Sales Meeting Notes

**Command:**

```bash
/meeting:notes --meeting "Discovery Call - TechCorp" --template sales
```

**Output:**

```
MEETING NOTES: Discovery Call - TechCorp
Date: March 12, 2024
Duration: 45 minutes
Participants:
- Robert Martinez (CTO, TechCorp)
- Lisa Wong (VP Marketing, TechCorp)
- You (Founder, Your Company)

=== MEETING OBJECTIVE ===
Understand TechCorp's marketing attribution challenges and determine if our solution is good fit.

=== COMPANY CONTEXT ===
Company: Enterprise Tech Solutions
Size: 150 employees, $30M revenue, Series B funded
Tech Stack: Salesforce, HubSpot, Google Ads, LinkedIn Ads, 6Sense, Marketo
Pain Point: Cannot connect offline conversions to digital marketing, CEO asking hard questions about marketing ROI

=== DISCOVERY NOTES ===

Current Situation:
- Using Salesforce + HubSpot + Google Sheets for attribution (manual process)
- Marketing team spends 10-15 hours/week on reporting
- CEO (CFO background) skeptical of $3M marketing budget
- Cannot attribute trade show leads or phone calls to digital touchpoints
- Tried Google Analytics and HubSpot attribution, but missing offline data

Business Impact:
- Marketing budget at risk if can't prove ROI
- Lisa (VP Marketing) under pressure to justify spend
- Missing optimization opportunities (don't know which channels actually work)
- Waste estimated at 15-20% of budget ($450-600K/year) on ineffective channels

What They've Tried:
- Google Analytics: Only tracks web, missing offline
- HubSpot attribution: Works for HubSpot traffic, but they use 8+ channels
- Custom Salesforce reporting: Too complex, requires engineering time
- Hired consultant: Spent $30K, got spreadsheet they can't maintain

=== NEEDS ASSESSMENT ===

Must-Haves:
✓ Integrate with their full tech stack (Salesforce, HubSpot, Google Ads, LinkedIn, 6Sense)
✓ Include offline conversions (trade shows, call tracking, in-person meetings)
✓ Reduce reporting time from 15 hours/week to <2 hours/week
✓ Automated dashboards (no manual data entry or Google Sheets)
✓ Enterprise security (SOC 2, GDPR) - Robert's requirement

Nice-to-Haves:
- Predictive analytics (which leads likely to close)
- Budget optimization recommendations
- Multi-touch attribution (not just last-touch)
- Team access controls (different dashboards for different roles)

Success Criteria:
- CEO confident in marketing spend and approves budget
- Lisa has clean, automated reports for executive team
- Can reallocate budget from low-ROI to high-ROI channels
- Spend <30 minutes/week on attribution reporting

Timeline:
- Need solution in place by Q2 (6 weeks) for quarterly review with CEO
- CFO will ask hard questions about marketing in Q2 review
- Urgent: Lisa's job potentially at risk if can't justify spend

Budget:
- Range: $20-40K/year (our $28K mid-tier plan is perfect fit)
- Have allocated budget (not a constraint)
- Procurement process: Robert technical diligence, Lisa vendor selection, CEO final approval

Decision Process:
- Week 1: Technical deep-dive with Robert's engineering team
- Week 2: Proposal presentation to Lisa + Robert + CEO
- Week 3: 30-day pilot if technical diligence passes
- Week 4-5: Pilot evaluation
- Week 6: Decision and contract (if pilot successful)

=== SOLUTION DISCUSSION ===

What Resonated:
✓ Integration with their exact tech stack (we support all their tools)
✓ Offline conversion tracking (they've been looking for this 2+ years)
✓ SOC 2 certification (Robert's top concern addressed)
✓ Reference customer (TechRival, their competitor) uses us successfully
✓ 30-day pilot approach (low-risk way to prove value)

Objections / Concerns:
1. "Another tool to manage" (they have 50+ tools already)
   Response: We actually replace 2-3 tools (Google Sheets reporting, consultant, manual processes)
   Resolution: Robert satisfied with this answer

2. "Integration complexity and timeline"
   Response: Pre-built connectors for all their tools, 1-week implementation typical
   Resolution: Agreed to technical deep-dive to validate

3. "What if it doesn't work after pilot?"
   Response: No long-term commitment until pilot proves value, 30-day money-back guarantee
   Resolution: This de-risked decision significantly

Case Study Shared:
SoftwarePlus (similar company: B2B software, $25M revenue, same tech stack)
- Before: 15 hours/week on reporting, 8 channels, no offline attribution
- After: 2 hours/week reporting, 22% marketing efficiency improvement, CFO became advocate
- Outcome: Marketing budget increased 20% based on proven ROI
- Offered to introduce them for reference call

=== NEXT STEPS ===

Agreed Path Forward:
1. Technical deep-dive scheduled for March 18 @ 2pm (Robert + his engineering team)
2. Proposal presentation March 22 @ 10am (Lisa + Robert + CEO Michael Stevens)
3. 30-day pilot starting April 1 (if technical diligence passes)
4. Decision by April 30 for Q2 deployment

Deliverables from Us:
- Technical integration doc for March 18 meeting (pre-read for Robert's team)
- Formal proposal with pricing, ROI projection, implementation plan for March 22
- Reference call intro to SoftwarePlus VP Marketing (Lisa requested this)

Deliverables from Them:
- Tech stack documentation and API access details for deep-dive prep
- Attendee list for March 22 proposal meeting (confirm CEO will attend)
- Sample data for pilot setup

=== ACTION ITEMS ===

HIGH PRIORITY (3):
1. [You] Create technical integration doc → Due: March 16 (2 days before deep-dive)
   - Detail: Pre-built connectors, implementation timeline, API requirements, security protocols

2. [You] Prepare formal proposal → Due: March 20 (2 days before presentation)
   - Detail: Pricing ($28K/year mid-tier plan), ROI calculation ($450-600K waste → 20% improvement = $90-120K value), implementation plan

3. [You] Arrange reference call with SoftwarePlus → Due: March 19 (before proposal meeting)
   - Detail: Intro email to SoftwarePlus VP Marketing + Lisa Wong, schedule for Week of March 18

MEDIUM PRIORITY (2):
4. [Robert] Share tech stack details and API access → Due: March 15
   - Detail: Documentation on Salesforce, HubSpot, Google Ads, LinkedIn integrations

5. [Lisa] Confirm CEO attendance at March 22 proposal → Due: March 14
   - Detail: Critical that CEO Michael Stevens attends to approve decision

=== QUALIFICATION SUMMARY ===

FIT SCORE: 95/100 (EXCELLENT FIT)

Positive Signals:
✓ Clear, urgent pain (CEO pressure, Q2 deadline)
✓ Budget allocated ($20-40K range, we're $28K)
✓ Technical fit (we support their entire tech stack)
✓ Decision authority (CEO, CTO, VP Marketing all engaged)
✓ Timeline alignment (need solution in 6 weeks, we can deliver)
✓ Strong buying signals (asked about pilot, mentioned budget, set up meetings)

Risk Factors:
⚠ Tight timeline (6 weeks to close and implement)
⚠ CEO approval required (adding stakeholder risk)
⚠ Competitor evaluation unknown (are they talking to others?)

Recommended Priority: HIGH
- Move quickly through technical diligence and proposal
- Over-deliver on responsiveness and detail
- Secure CEO meeting attendance (critical for close)
- Prepare for competitor questions
- Make pilot setup seamless (first impression is everything)

Estimated Close Probability: 75%
Deal Value: $28K annual ($84K over 3-year LTV)
Sales Cycle: 3-4 weeks (fast for enterprise)

=== MEETING SENTIMENT ===

Robert Martinez (CTO):
- Engagement: HIGH (asked 12 technical questions, took detailed notes)
- Sentiment: CAUTIOUSLY OPTIMISTIC (concerned about integration, but satisfied with answers)
- Key Concern: "Another tool to manage"—addressed by positioning as tool consolidation
- Buy-In Level: 70% (pending technical deep-dive validation)

Lisa Wong (VP Marketing):
- Engagement: VERY HIGH (this is her problem, her budget, potentially her job)
- Sentiment: ENTHUSIASTIC (smiled multiple times, leaned forward, took extensive notes)
- Key Excitement: Offline attribution (she's been looking for this for 2+ years)
- Buy-In Level: 90% (she's already convinced, needs CEO approval)

Overall Meeting Tone: Professional, collaborative, problem-solving
Energy Level: HIGH (they're eager to solve this problem)
Decision Likelihood: STRONG (assuming technical diligence passes and CEO approves)

=== FOLLOW-UP CHECKLIST ===

Within 24 Hours:
- [ ] Send thank-you email to Robert and Lisa
- [ ] Confirm March 18 technical deep-dive details (attendees, agenda, Zoom link)
- [ ] Confirm March 22 proposal meeting (attendees including CEO, agenda, Zoom link)
- [ ] Begin technical integration documentation

Within 1 Week:
- [ ] Deliver technical integration doc by March 16
- [ ] Arrange SoftwarePlus reference call by March 19
- [ ] Complete formal proposal by March 20
- [ ] Prepare proposal presentation deck

Before Next Meeting (March 18):
- [ ] Review Robert's tech stack documentation
- [ ] Prepare demo environment with their tech stack configuration
- [ ] Research CEO Michael Stevens (CFO background, what matters to him?)
- [ ] Develop response to "what if competitors offer same thing?" question

=== NOTES FOR NEXT INTERACTION ===

Rapport Opportunities:
- Lisa mentioned she's from Seattle (you went to college there—mention this)
- Robert attended AWS re:Invent last month (ask what sessions he liked)
- Company recently hired new CEO with CFO background (emphasize ROI and cost-savings angle)

Potential Objections to Prepare For:
- CEO: "Why not build this internally?" (respond with time, cost, and expertise required)
- CEO: "What's your customer retention rate?" (our 95% NRR is strong proof point)
- Robert: "What if we need custom features?" (discuss professional services and roadmap process)

Competitive Positioning:
- Research their competitor TechRival's attribution solution (they use ours, great reference)
- Prepare comparison to Google Analytics and HubSpot (complementary, not competitive)
- Anticipate questions about other attribution vendors (Bizible, Ruler Analytics, attribution)

=== MEETING RECORDING & TRANSCRIPT ===

[If recorded/transcribed, link here]
Recording: Link
Transcript: Link
```

### Example 2: Team Meeting Notes (Stand-up / Sprint Planning)

**Command:**

```bash
/meeting:notes --meeting "Sprint Planning - Q2 Features" --template technical
```

**Output:**

```
MEETING NOTES: Sprint Planning - Q2 Features
Date: March 11, 2024
Duration: 90 minutes
Participants:
- Sarah (Product Manager)
- Alex (Engineering Lead)
- Jamie (Senior Engineer)
- Chris (Designer)
- Taylor (QA Lead)

=== SPRINT GOAL ===
Plan Q2 feature development priorities and allocate engineering resources to highest-impact initiatives based on customer feedback and retention goals.

=== CONTEXT ===
Following board decision to focus Q2 on retention over growth, need to reprioritize product roadmap. Customer feedback from 15 churn interviews identified top 3 issues: onboarding friction, missing integrations, slow performance on large datasets.

=== FEATURES DISCUSSED ===

Feature 1: Improved Onboarding Flow
- Problem: 30% of trial users never complete setup (friction point)
- Solution: Guided onboarding wizard with sample data pre-loaded
- Impact: Increase trial-to-paid conversion 15% → 25% (based on tests)
- Effort: 3 weeks (1 engineer + 1 designer)
- Priority: HIGH (directly impacts retention)
- Decision: APPROVED for Sprint 1 (April 1-21)
- Owner: Jamie (Engineering), Chris (Design)

Feature 2: Slack Integration
- Problem: #2 most requested feature (47 customer requests)
- Solution: Two-way Slack integration for alerts and commands
- Impact: Improves daily engagement, reduces churn risk
- Effort: 2 weeks (1 engineer)
- Priority: MEDIUM-HIGH
- Decision: APPROVED for Sprint 2 (April 22-May 12)
- Owner: Alex (Engineering Lead) will assign

Feature 3: Performance Optimization (Large Datasets)
- Problem: Customers with >100K records experience slow load times (5-10 sec)
- Solution: Database query optimization + caching layer + pagination
- Impact: Reduces churn risk for enterprise customers (20% of MRR)
- Effort: 4 weeks (2 engineers, complex backend work)
- Priority: HIGH (enterprise retention risk)
- Decision: APPROVED for Sprint 1-2 (parallel with onboarding)
- Owner: Alex (Engineering Lead) + Jamie

Feature 4: Salesforce Custom Objects Support
- Problem: Enterprise customers need to sync custom objects, not just standard
- Solution: Dynamic object mapping interface in settings
- Impact: Removes deal-blocker for 3 enterprise prospects ($150K ARR pipeline)
- Effort: 3 weeks (1 engineer)
- Priority: MEDIUM (sales pipeline enabler, not retention)
- Decision: DEFERRED to Q3 (not retention-focused)

Feature 5: Mobile App (iOS)
- Problem: Requested by 12 customers
- Solution: Native iOS app for dashboards and alerts
- Impact: Nice-to-have, but doesn't address retention issues
- Effort: 8-12 weeks (major project)
- Priority: LOW for Q2 (not retention-critical)
- Decision: DEFERRED to Q3 or Q4

=== TECHNICAL DECISIONS ===

Decision 1: Use React Flow library for onboarding wizard
- Rationale: Faster than building from scratch, good UX out of box
- Alternative Considered: Custom build (would take 2x longer)
- Trade-off: External dependency, but maintained by large community
- Owner: Jamie to prototype and validate this week

Decision 2: Implement Redis caching layer for performance
- Rationale: Fastest path to performance improvement without database migration
- Alternative Considered: Move to PostgreSQL from MySQL (too risky mid-quarter)
- Trade-off: Adds infrastructure complexity, but manageable
- Owner: Alex to set up staging environment with Redis

Decision 3: Defer mobile app until Q3 at earliest
- Rationale: Not retention-critical, team too small for parallel mobile development
- Alternative Considered: Hire mobile contractor (decided against for Q2)
- Trade-off: Disappoints some customers, but right priority call
- Communicated: Sarah to update customers requesting mobile app

=== RESOURCE ALLOCATION ===

Sprint 1 (April 1-21):
- Jamie: Onboarding wizard (3 weeks full-time)
- Alex + Jamie: Performance optimization (4 weeks, Alex 50%, Jamie 50% after onboarding)
- Chris: Onboarding design + performance UI improvements (3 weeks)
- Taylor: QA for both features + regression testing (3 weeks)

Sprint 2 (April 22-May 12):
- [TBD]: Slack integration (2 weeks, engineer to be assigned)
- Alex: Performance optimization continued (2 weeks to complete)
- Taylor: QA for Slack integration

Sprint 3 (May 13-June 2):
- Open for emerging priorities or continued performance work

Total Capacity: 2.5 engineers (Alex 50% leadership, Jamie full-time, +1 TBD)

=== RISKS & DEPENDENCIES ===

Risk 1: Performance optimization may take longer than 4 weeks
- Mitigation: Alex to timebox investigation to 1 week, get estimate before full commitment
- Backup Plan: If >4 weeks, defer to Sprint 3 and prioritize onboarding + Slack

Risk 2: Jamie assigned to 150% capacity (onboarding + performance in Sprint 1)
- Mitigation: Onboarding completes week 3, then shift 50% to performance
- Alex to monitor workload and adjust if Jamie overloaded

Risk 3: No engineer assigned to Slack integration yet (Sprint 2)
- Mitigation: Recruiting pipeline has 2 candidates in final rounds, hope to hire by April 1
- Backup Plan: Alex takes Slack integration if no hire (delays other work)

Dependency 1: Design work (Chris) must complete before engineering starts onboarding
- Timeline: Chris to finish designs by March 22 (before Sprint 1 start)
- Status: On track, Chris already started

Dependency 2: Redis infrastructure setup before performance work can begin
- Timeline: Alex to complete staging Redis setup by March 29
- Status: In progress, no blockers

=== ACTION ITEMS ===

HIGH PRIORITY (5):
1. [Jamie] Prototype React Flow for onboarding wizard → Due: March 15 (This Friday)
2. [Chris] Complete onboarding wizard designs → Due: March 22
3. [Alex] Set up Redis caching layer in staging → Due: March 29
4. [Sarah] Write PRDs for onboarding, performance, Slack features → Due: March 18
5. [Alex] Timeboxed performance investigation and effort estimate → Due: March 16

MEDIUM PRIORITY (3):
6. [Sarah] Communicate mobile app deferral to requesting customers → Due: March 20
7. [Taylor] Create QA test plans for Sprint 1 features → Due: March 25
8. [Alex] Assign Slack integration owner (or plan to take it himself) → Due: April 1

ADMINISTRATIVE (2):
9. [Sarah] Update product roadmap doc to reflect Q2 priorities → Due: March 13
10. [Sarah] Send sprint planning summary to entire team → Due: March 12 (today)

=== DECISIONS LOG ===

1. Q2 Feature Priority: Onboarding + Performance + Slack (Approved)
2. Deferred Features: Salesforce custom objects (to Q3), Mobile app (to Q3/Q4)
3. Technical Stack: React Flow for onboarding wizard (Approved)
4. Infrastructure: Redis caching layer for performance (Approved)
5. Resource Allocation: Jamie on onboarding, Alex+Jamie on performance, TBD on Slack

=== NEXT MEETING ===

Date: March 25, 2024 @ 10:00 AM (Sprint 1 Kick-off)
Agenda:
- Review completed PRDs for Sprint 1 features
- Validate designs and technical approach
- Confirm resource allocation and timelines
- Address any blockers before April 1 sprint start

Weekly Check-ins: Tuesdays @ 10:00 AM (stand-up format)
```

## Quality Control Checklist

**Comprehensive Capture:**

- [ ] All participants listed with roles and attendance status
- [ ] Meeting objective and context documented
- [ ] Key discussion points captured for each agenda item
- [ ] All decisions made during meeting recorded with rationale
- [ ] Action items extracted with owners, deadlines, and priority
- [ ] Next steps and follow-up meeting details included

**Action Item Quality:**

- [ ] Each action item has clear, actionable task description
- [ ] Owner explicitly assigned (not ambiguous)
- [ ] Deadline specified or suggested based on context
- [ ] Priority level assessed (high, medium, low)
- [ ] Dependencies identified if task blocked by other work
- [ ] Context provided (why this matters, what triggered it)

**Decisions Documented:**

- [ ] Decision statement clear and unambiguous
- [ ] Context provided (what prompted this decision)
- [ ] Alternatives considered documented
- [ ] Rationale explained (why this option chosen)
- [ ] Impact described (what changes as a result)
- [ ] Decision-maker identified (who had authority)

**Participant Insights:**

- [ ] Individual engagement levels noted
- [ ] Sentiment and concerns captured per participant
- [ ] Key quotes or comments attributed correctly
- [ ] Follow-up needs identified based on participant concerns
- [ ] Stakeholder alignment assessed

**Formatting & Readability:**

- [ ] Consistent structure and formatting throughout
- [ ] Clear section headers for easy navigation
- [ ] Bullet points and numbering used appropriately
- [ ] Emphasis (bold, italics) used to highlight key points
- [ ] White space and visual hierarchy make document scannable

**Completeness & Accuracy:**

- [ ] No significant discussion points omitted
- [ ] Numbers, dates, and names verified for accuracy
- [ ] Ambiguous statements clarified or flagged for follow-up
- [ ] Technical terms or jargon explained if needed
- [ ] Links to related documents and resources included

**Actionability:**

- [ ] Summary section provides quick overview for busy readers
- [ ] Action items exportable to task management system
- [ ] Next meeting details clear (date, time, agenda preview)
- [ ] Follow-up checklist provided with specific tasks and timing
- [ ] Document stored in searchable, accessible location

## Best Practices

**Focus on Decisions and Actions, Not Transcript**
Notes should capture what was decided and what happens next, not a word-for-word transcript. Participants don't need to relive the meeting—they need to know what changed and what they're responsible for. Aim for 70% decisions/actions, 30% context.

**Assign Action Items During Meeting, Not After**
When someone commits to something, verbally confirm owner and deadline in the meeting. "Just to confirm, Sarah, you'll have the churn analysis ready for the next board meeting on April 15?" This prevents post-meeting confusion and creates accountability in real-time.

**Use Templates for Recurring Meeting Types**
Create standard templates for meetings you have regularly (board meetings, sprint planning, client calls, investor updates). Templates ensure you capture the same information consistently and make notes more scannable for people who read multiple meetings of the same type.

**Capture Verbatim Quotes Sparingly**
Only capture exact quotes when they're particularly insightful, controversial, or represent a strong position. Most discussion can be paraphrased. Overusing quotes makes notes harder to read and gives false sense of transcript completeness.

**Tag Action Items with Context, Not Just Task**
Don't just write "Sarah: Analyze churn." Write "Sarah: Analyze churn by cohort to understand root cause (board concern about sustainability). Due: April 15." The context makes it clear why this matters and helps prioritize if workload gets heavy.

**Send Notes Within 24 Hours**
Meeting notes lose value rapidly. Send within 24 hours while everyone's memory is fresh and action items are still top-of-mind. After 3-4 days, notes become historical record rather than actionable document.

**Make Action Items Specific and Measurable**
"Improve onboarding" is not actionable. "Design new onboarding wizard with sample data pre-loaded, increasing trial-to-paid conversion from 15% to 25%, complete by March 31" is actionable. Specificity prevents future disagreement about what was committed.

**Create Summary Section at Top**
Busy people (especially execs) won't read full notes. Put 3-5 key takeaways at the top: decisions made, major action items, critical information. This respects their time while ensuring key points aren't missed.

## Integration Points

**Calendar Integration:**

- Google Calendar, Outlook, Apple Calendar for meeting details
- Automatic note creation when meeting ends (calendar event trigger)
- Meeting participants auto-filled from attendee list
- Related meetings linked automatically (same participants, recurring series)

**Task Management:**

- Asana, Todoist, Trello, ClickUp for action item export
- Automatic task creation with assignee, deadline, description, context
- Two-way sync: Mark task complete → Updates meeting notes
- Project linking: Associate action items with relevant projects

**CRM Integration:**

- Salesforce, HubSpot, Zoho CRM for client meeting notes
- Automatic logging of sales calls, client check-ins, partnership discussions
- Link notes to contact, account, opportunity records
- Track meeting history and customer relationship progression

**Communication Platforms:**

- Slack, Teams for meeting summary distribution
- Automatic posting of action items to relevant channels
- @mention assignees for action item notifications
- Meeting notes accessible via slash command (/meeting-notes [title])

**Document Storage:**

- Google Drive, Dropbox, Notion for centralized storage
- Folder organization by meeting type, date, participants
- Version control and edit history
- Search functionality across all historical notes

**Transcription Services:**

- Zoom, Google Meet, Microsoft Teams for automatic transcription
- Otter.ai, Grain, Fireflies for dedicated transcription
- AI processing of transcript to extract key points and action items
- Timestamp linking: Click action item → Jump to relevant moment in recording

## Success Criteria

**Note Quality:**

- 95%+ of action items correctly extracted and assigned
- Decisions documented with rationale and impact in 100% of cases
- Key discussion points captured (verified by participant spot-checks)
- Notes readable and useful to people who weren't in meeting

**Time Efficiency:**

- Note-taking time reduced from 30-45 minutes post-meeting to 10-15 minutes
- Real-time capture allows full participation without distraction
- No second pass required to "clean up" notes for sharing

**Actionability:**

- Action items exported to task management within 1 hour of meeting end
- Notes distributed to participants within 24 hours
- 90%+ of action items completed by deadline (increased accountability)
- Reduction in "wait, who was supposed to do that?" confusion

**Knowledge Management:**

- 100% of meetings documented in searchable repository
- Easy retrieval of previous discussions and decisions
- Pattern identification across multiple meetings
- Onboarding value: New team members can read meeting history for context

**Behavior Change:**

- Meeting participants feel heard (their points captured accurately)
- Increased follow-through on commitments (public accountability)
- Fewer follow-up meetings to clarify what was decided
- Better meeting culture (people know notes will be distributed, so they stay focused)

## Common Use Cases

**Use Case 1: Board Meeting Documentation**
Quarterly board meetings with directors, investors, and exec team. Capture performance review, strategic decisions, guidance from board, and action items for management team. Critical for legal/compliance (board decisions documented), continuity (what was decided last quarter?), and accountability (who committed to what?).

**Use Case 2: Client Sales Call Notes**
Discovery calls, demos, proposal presentations with prospective clients. Document pain points, requirements, objections, buying process, decision-makers, timeline, and next steps. Essential for deal progression, team handoffs (AE → implementation), and post-sale context (what did we promise?).

**Use Case 3: Sprint Planning & Standups**
Engineering team planning sessions and daily/weekly standups. Capture feature prioritization, resource allocation, technical decisions, blockers, and progress updates. Keeps distributed team aligned, creates record of technical decisions, and tracks velocity/capacity over time.

**Use Case 4: Investor Update Meetings**
Monthly or quarterly check-ins with investors, advisors, or mentors. Document metrics reviewed, challenges discussed, advice given, connections offered, and follow-up actions. Maintains relationship history, tracks pattern of advice over time, and ensures accountability to investor commitments.

**Use Case 5: Partnership Negotiations**
Multi-meeting negotiation of partnership terms, integration approach, go-to-market strategy, and commercial terms. Capture each meeting's progress, points of agreement/disagreement, open items, and decision timeline. Essential for complex deals where many details discussed over weeks/months.

**Use Case 6: Team Retrospectives**
Post-sprint, post-project, or post-incident retrospectives. Document what went well, what didn't, lessons learned, and process improvements to implement. Critical for continuous improvement and ensuring lessons learned don't get forgotten.

## Troubleshooting

**Problem: Can't capture notes fast enough during meeting**

- Solution: Use voice recorder or transcription tool (Otter.ai, Zoom transcription) and process after meeting. Or switch to bullet points only—full sentences can come later. Or designate scribe role if recurring meeting.

**Problem: Action items unclear or ambiguous**

- Solution: Verbally confirm action items at end of meeting. "Before we end, let me recap action items: Sarah, you're analyzing churn by April 15. John, you're sending updated Q2 plan by Friday. Everyone agree?" Get explicit confirmation.

**Problem: Too many meetings to document comprehensively**

- Solution: Triage by importance. Board meetings, client calls, strategic planning: comprehensive notes. Daily standups, quick syncs: bullet points only. Routine check-ins: skip notes entirely (just capture actions in email).

**Problem: Notes too long, nobody reads them**

- Solution: Add executive summary at top (3-5 key points). Send summary in email body with full notes attached. Use formatting (bold, sections, bullets) to make scannable. Consider separate doc for detailed discussion vs action-only doc.

**Problem: Participants dispute what was decided**

- Solution: Send notes within 24 hours and explicitly say "please review and correct if anything is inaccurate." Give 48-hour window for corrections. After that, notes are official record. Consider recording sensitive meetings for reference.

**Problem: Action items not getting completed**

- Solution: Export to task management system immediately. Send weekly action item digest to all owners. Include action item review as first agenda item in next meeting (creates accountability). Escalate chronic non-completion to manager or exec team.

**Problem: Notes duplicated across multiple systems**

- Solution: Choose single source of truth (Google Docs, Notion, CRM, etc.). Link from other systems rather than copying. Set up automation to sync action items to task management, but keep full notes in one location only.
