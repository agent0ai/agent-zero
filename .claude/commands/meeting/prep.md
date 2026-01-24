---
description: Auto-prep before meetings (context, agenda, talking points)
argument-hint: <meeting-title> [--calendar <google|outlook|apple>] [--duration <minutes>] [--participants <list>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash, WebFetch
---

# Meeting Prep - Intelligent Pre-Meeting Preparation

## Overview

Meeting Prep is an AI-powered meeting preparation system that transforms you from unprepared to over-prepared in minutes. It automatically gathers context, generates relevant talking points, creates focused agendas, and identifies potential obstacles before you step into any meeting.

For solo entrepreneurs, every meeting is high-stakes: investor pitches, client calls, partnership discussions, team interviews. This system ensures you never walk into a meeting underprepared, giving you the confidence and material to make every meeting count.

**ROI: $45,000/year** through improved meeting outcomes (closed deals, avoided bad partnerships, stronger negotiations), reduced prep time (15 hours/month saved), and eliminated post-meeting regret from missed opportunities.

## Key Benefits

**Meeting Confidence & Performance**

- Walk into every meeting fully prepared with context and talking points
- Anticipate questions and objections before they're raised
- Identify decision-maker priorities and communication preferences
- Close more deals through thorough preparation (20-35% improvement)

**Time Efficiency**

- Automated research replaces 30-60 minutes of manual prep work
- Context aggregation from emails, CRM, calendar, documents
- Template-based agenda generation adapted to meeting type
- Pre-written talking points customized to participant profiles

**Strategic Advantage**

- Research participant backgrounds, companies, and recent activity
- Identify common ground, mutual connections, and rapport opportunities
- Uncover potential obstacles or concerns to address proactively
- Develop multiple conversation paths based on possible directions

**Reduced Meeting Anxiety**

- Comprehensive preparation eliminates uncertainty and worry
- Clear objectives and success criteria provide focus
- Backup topics and questions prevent awkward silence
- Post-meeting action items pre-defined for immediate follow-through

## Implementation Steps

### Step 1: Initiate Meeting Prep

Run the meeting prep command with meeting title and optional context:

```bash
# Investor pitch meeting
/meeting:prep "Series A Pitch - Acme Ventures" --calendar google --duration 30

# Client discovery call
/meeting:prep "Discovery Call - TechCorp" --participants "Sarah Johnson, Mike Chen" --type discovery

# Partnership discussion
/meeting:prep "Partnership Proposal - SaaS Integration" --type partnership --calendar outlook

# Job interview
/meeting:prep "Senior Engineer Interview - Jane Smith" --type interview --duration 60
```

The system will:

- Retrieve meeting details from calendar (time, participants, location, description)
- Extract participant email addresses and LinkedIn profiles
- Search CRM for relationship history and previous interactions
- Scan email threads for relevant context and discussion points
- Identify linked documents, proposals, or presentations

### Step 2: Context Aggregation & Research

System automatically gathers comprehensive context:

**Calendar Analysis:**

- Meeting time, duration, location (in-person, Zoom, phone)
- Participant list with email addresses and roles
- Meeting description and any pre-shared agenda
- Previous meetings with same participants (frequency, topics, outcomes)
- Calendar conflicts or tight scheduling that may affect meeting tone

**CRM Research:**

- Company profile (size, industry, funding stage, revenue)
- Contact profiles (roles, tenure, decision-making authority)
- Deal stage and pipeline status (if sales meeting)
- Previous interactions (emails, calls, meetings, proposals sent)
- Notes from past meetings and action items completed/pending

**Email Context:**

- Recent email threads with participants (last 30 days)
- Key discussion points, questions raised, concerns expressed
- Attachments shared (proposals, decks, contracts, documents)
- Communication tone and responsiveness patterns
- Outstanding questions or requests requiring follow-up

**Public Research:**

- LinkedIn profiles (background, experience, interests, mutual connections)
- Company news (funding rounds, product launches, leadership changes)
- Industry trends relevant to meeting topic
- Competitive landscape and market positioning
- Recent content published (blog posts, tweets, interviews)

**Document Analysis:**

- Review linked proposals, presentations, or contracts
- Extract key points, pricing, terms, and open questions
- Identify areas requiring clarification or negotiation
- Flag potential objections based on document feedback

### Step 3: Generate Meeting Agenda

Create structured agenda tailored to meeting type:

**Investor Pitch Agenda (30 minutes):**

```
Opening (2 minutes):
- Thank them for their time
- Brief personal connection or mutual introduction context
- State meeting objective: Discuss Series A funding for [Company]

Problem & Solution (5 minutes):
- Market problem we're solving (with specific metrics/examples)
- Our solution and unique approach
- Why now? (Market timing and opportunity)

Traction & Metrics (5 minutes):
- Revenue: $XXK MRR, XX% MoM growth
- Customers: XXX paying customers, XX% net retention
- Team: X employees, key hires completed
- Key milestones achieved since last update

The Ask (3 minutes):
- Raising $XXM at $XXM valuation
- Use of funds: XX% product, XX% sales, XX% operations
- Timeline: Closing in XX weeks
- Existing commitments: $XXX committed from [investors]

Discussion & Questions (15 minutes):
- Open floor for investor questions
- Address concerns proactively (competition, market risk, go-to-market)
- Discuss investor involvement beyond capital (network, expertise, board)
```

**Client Discovery Agenda (45 minutes):**

```
Warm-up (5 minutes):
- Icebreaker and rapport building
- Confirm meeting objective and agenda
- Set expectations for call outcome

Situation Analysis (10 minutes):
- Current situation and challenges
- What prompted this meeting?
- Previous solutions tried and why they fell short
- Impact of problem on business metrics

Needs Assessment (10 minutes):
- Primary objectives and success criteria
- Timeline and urgency
- Budget range and approval process
- Key stakeholders and decision-makers

Solution Discussion (10 minutes):
- How we've solved similar problems for others
- Our approach and methodology
- Relevant case studies and results
- Potential fit for their situation

Next Steps (10 minutes):
- Proposal timeline and format
- Additional information needed
- Follow-up meeting to present solution
- Questions they have for us
```

**Partnership Discussion Agenda (60 minutes):**

```
Introduction (10 minutes):
- Company overviews and current state
- Previous touchpoints or connections
- Alignment on meeting goals

Partnership Vision (15 minutes):
- Mutual value proposition
- Target outcomes for both parties
- Strategic alignment and shared objectives
- Market opportunity and timing

Integration Approach (15 minutes):
- Technical integration requirements
- Go-to-market collaboration
- Resource commitments from each side
- Timeline and phases

Commercial Terms (10 minutes):
- Revenue sharing or fee structure
- Marketing/sales commitments
- Exclusivity considerations
- Contract term and renewal

Action Items & Next Steps (10 minutes):
- Follow-up items and owners
- Due diligence process
- Timeline for decision and launch
- Next meeting scheduled
```

### Step 4: Develop Talking Points

Generate specific talking points for each agenda item:

**Problem & Solution Talking Points:**

- Primary: "74% of marketing teams report difficulty measuring ROI across channels"
- Support: "This leads to $50K-200K/year in wasted ad spend for SMBs"
- Solution: "We consolidate attribution data and use ML to show true channel contribution"
- Differentiation: "Unlike Google Analytics or HubSpot, we integrate offline conversions"
- Proof: "Customers see 28% improvement in marketing efficiency within 90 days"

**Objection Handling:**

- Objection: "Why wouldn't we just build this internally?"
  - Response: "Most teams spend 6-12 months and $200K+ trying, then buy anyway"
  - Support: "Our tech includes 3 patents and 4 years of ML model training"
  - Offer: "Happy to partner on custom features specific to your needs"

- Objection: "We're not ready to make a decision yet"
  - Response: "Totally understand, what additional information would help?"
  - Probe: "What's the timeline for evaluating solutions?"
  - Offer: "We can do a 30-day pilot so you can see results before committing"

### Step 5: Participant Profiling

Create profiles for key participants with communication strategies:

**Sarah Johnson - VP of Marketing, TechCorp**

- Background: 12 years in B2B SaaS marketing, previously at Salesforce
- Style: Data-driven, appreciates case studies and ROI metrics
- Priorities: Marketing attribution, campaign performance, team efficiency
- Recent activity: Posted on LinkedIn about marketing analytics challenges
- Mutual connections: John Smith (former colleague at Salesforce)
- Communication strategy:
  - Lead with specific metrics and case study data
  - Reference attribution challenges she's mentioned publicly
  - Offer to connect her with similar customers for reference calls
  - Mention John Smith if appropriate for rapport building

**Mike Chen - CTO, TechCorp**

- Background: Engineering leader, 8 years at TechCorp, promoted internally
- Style: Technical depth, security-conscious, interested in architecture
- Priorities: Integration complexity, data security, scalability, API reliability
- Concerns: Adding another vendor to tech stack (already has 40+ tools)
- Communication strategy:
  - Address integration simplicity upfront (single API, pre-built connectors)
  - Discuss security certifications (SOC 2, GDPR compliance)
  - Offer technical deep-dive with engineering team
  - Emphasize reduction in overall tool complexity (replaces 2-3 existing tools)

### Step 6: Prepare Questions to Ask

Develop strategic questions for different meeting phases:

**Opening Questions (Build Rapport):**

- "I saw you recently [recent company news/personal update]. How did that go?"
- "How long have you been with [Company]? What attracted you originally?"
- "We have a mutual connection in [Name]. How do you know them?"

**Discovery Questions (Understand Situation):**

- "What prompted you to take this meeting / start looking at solutions?"
- "Walk me through your current process. Where does it break down?"
- "If you could wave a magic wand, what would your ideal solution look like?"
- "What's the business impact of not solving this problem?"
- "Who else is affected by this? Who cares most about solving it?"

**Qualification Questions (Assess Fit):**

- "What's your timeline for making a decision?"
- "What's your process for evaluating and selecting solutions?"
- "Who else needs to be involved in the decision?"
- "Have you allocated budget for this? What range are you considering?"
- "What criteria will you use to choose between alternatives?"

**Closing Questions (Drive Action):**

- "Based on what we've discussed, do you see this being a good fit?"
- "What concerns or questions do you still have?"
- "What would you need to see from us to move forward?"
- "What are the next steps from your perspective?"
- "When should we reconnect to [next action]?"

### Step 7: Identify Success Criteria

Define clear success metrics for the meeting:

**Primary Objective (Must Achieve):**

- Investor Meeting: Secure commitment to next meeting with full partnership
- Sales Meeting: Get agreement to proposal presentation meeting
- Partnership Meeting: Agree on joint LOI or term sheet discussion
- Interview: Determine mutual fit and advance candidate to next round

**Secondary Objectives (Highly Desired):**

- Build personal rapport with key decision-maker
- Surface and address primary objection or concern
- Get introduction to additional stakeholder
- Learn competitive situation (who else they're considering)
- Gather specific information needed for next step

**Information Gathering (Essential):**

- Confirm decision timeline and process
- Understand budget parameters and approval authority
- Identify other stakeholders not present
- Surface potential deal-breakers or obstacles
- Gauge enthusiasm and likelihood of moving forward

**Relationship Building (Valuable):**

- Find common ground (personal interests, mutual connections)
- Demonstrate expertise and thought leadership
- Establish credibility through relevant examples
- Create memorable interaction (humor, insight, generosity)

### Step 8: Risk Assessment & Mitigation

Identify potential obstacles and prepare responses:

**Timing Risks:**

- Risk: "They're not ready to decide for 6 months"
- Mitigation: Propose pilot program to demonstrate value during evaluation period
- Alternative: Secure permission to check in monthly with relevant updates

**Budget Risks:**

- Risk: "Budget allocated to different priority this year"
- Mitigation: Show ROI that justifies budget reallocation (pays for itself in 4 months)
- Alternative: Propose phased approach with smaller initial commitment

**Authority Risks:**

- Risk: Key decision-maker not in the meeting
- Mitigation: Ask to schedule follow-up including that person
- Alternative: Gather champion's support to bring back to decision-maker

**Competitive Risks:**

- Risk: Already evaluating competitor with head start
- Mitigation: Differentiate on specific dimensions we win on (not feature comparison)
- Alternative: Position as complementary or superior in key areas they care about

**Technical Risks:**

- Risk: Integration complexity or timeline concerns
- Mitigation: Offer proof-of-concept showing integration working in their environment
- Alternative: Provide references from similar tech stack customers

### Step 9: Create Meeting Materials Checklist

Ensure all necessary materials are ready:

**Required Materials:**

- [ ] Meeting agenda (share 24 hours before, or bring printed copy)
- [ ] Pitch deck or presentation (tested on meeting platform)
- [ ] Product demo environment (tested, data loaded, backup plan if demo breaks)
- [ ] Proposal or pricing sheet (if appropriate stage)
- [ ] Case studies or customer references (1-2 most relevant)
- [ ] Leave-behind materials (one-pager, business card, next steps document)

**Technical Preparation:**

- [ ] Video conferencing link tested and working (Zoom, Teams, Google Meet)
- [ ] Screen sharing permissions confirmed
- [ ] Audio and video quality verified
- [ ] Backup computer or hotspot in case of technical issues
- [ ] Calendar invite accepted and confirmed by all participants
- [ ] Recording consent obtained (if planning to record)

**Reference Materials:**

- [ ] Participant profiles printed or on second screen
- [ ] Talking points and objection handling guide accessible
- [ ] Questions to ask checklist
- [ ] Company research notes
- [ ] Previous meeting notes and action items (if follow-up meeting)

### Step 10: Pre-Meeting Routine

Execute final preparation steps day-of:

**Morning of Meeting:**

- Review full meeting prep document (10 minutes)
- Practice opening 2 minutes out loud (build confidence)
- Review participant profiles and identify 2-3 rapport opportunities
- Check meeting link and technical setup (5 minutes before)
- Prepare physical space (quiet room, good lighting, professional background)

**15 Minutes Before:**

- Close unnecessary browser tabs and applications
- Put phone on silent (out of sight)
- Have water available
- Open meeting materials and notes on second screen
- Take 3 deep breaths, visualize successful meeting

**Meeting Start:**

- Join 2-3 minutes early (shows respect for their time)
- Be first to smile and greet participants as they join
- Have opening lines ready to start confidently
- Set positive tone with enthusiasm and appreciation

## Usage Examples

### Example 1: Investor Pitch Preparation

**Command:**

```bash
/meeting:prep "Series A Pitch - Sequoia Capital" --calendar google --duration 30 --type investor
```

**Output:**

```
Meeting Prep Complete: Series A Pitch - Sequoia Capital

MEETING DETAILS:
Date: Tomorrow, 2:00 PM PST
Duration: 30 minutes
Platform: Zoom (link copied to clipboard)
Participants:
  - Jessica Lee (Partner, jessica@sequoia.com)
  - David Park (Principal, david@sequoia.com)

PARTICIPANT PROFILES:

Jessica Lee - Partner, Sequoia Capital
- Focus: B2B SaaS, marketplace models, Series A-B
- Portfolio: 12 companies, 3 unicorns (DataCorp, SalesAI, CloudTech)
- Background: Former operator, VP Sales at SalesforceBefore Sequoia
- LinkedIn: 24K followers, active poster on SaaS metrics
- Recent activity: Tweeted about importance of net revenue retention
- Communication style: Metric-driven, values operational expertise
- Strategy: Lead with NRR (our strongest metric at 125%), reference operator background

David Park - Principal, Sequoia Capital
- Focus: Technical diligence, product evaluation
- Background: Stanford CS, PM at Google for 6 years
- Evaluation criteria: Product differentiation, technical moat, team quality
- Recent activity: Published article on "Building category-defining products"
- Strategy: Emphasize our unique ML approach and 3 patents, strong engineering team

CONTEXT SUMMARY:

Previous Interactions:
- Intro email from Alex Chen (mutual connection) 3 weeks ago
- Jessica responded positively, asked for deck
- We sent deck 2 weeks ago, she replied "interesting traction"
- Scheduled this meeting via email 1 week ago

Email Thread Analysis:
- Jessica specifically called out our growth rate and retention metrics
- Asked about competitive landscape in last email
- Mentioned they're actively looking at marketing analytics space

CRM Notes:
- Warm intro from Alex Chen (Sequoia LP, knows them well)
- Deck sent 2/10, they've reviewed it (Docsend analytics show 8 minutes)
- They've invested in competitor (AnalyticsAI) but it's different segment

MEETING AGENDA:

Opening (2 min):
- Thank them for taking the meeting
- Reference Alex's intro and why he thought this was good fit
- State objective: Discuss Series A funding for PropelMetrics

Problem & Solution (5 min):
Talking Points:
✓ "Marketing teams waste $50-200K/year on ineffective channels"
✓ "Current attribution tools miss 40% of conversions (offline, dark social)"
✓ "We use ML to unify online and offline attribution with 95% accuracy"
✓ "Only solution that integrates POS, call tracking, and digital in single view"

Traction & Metrics (5 min):
Key Numbers:
✓ Revenue: $42K MRR, 35% MoM growth (emphasize consistency)
✓ Customers: 47 paying customers, 125% net revenue retention (Jessica's focus!)
✓ Team: 8 employees, VP Eng from Google (David will appreciate)
✓ Milestones: Achieved product-market fit, repeatableGTM motion

The Ask (3 min):
✓ Raising $3M Series A at $12M pre-money valuation
✓ Use of funds: 50% engineering, 30% sales, 20% ops
✓ Timeline: Closing in 6 weeks
✓ Committed: $1.2M from existing angels, seeking $1.8M from lead

Discussion & Questions (15 min):
Anticipated Questions & Responses:

Q: "Who else are you talking to?"
A: "We're in conversations with 4 firms. Looking for lead who brings SaaS GTM expertise and can help with next round (Series B in 18 months)."

Q: "What about AnalyticsAI? They're in similar space"
A: "Different customer: they focus on enterprise ($50K+ ACV), we're SMB/mid-market ($8K ACV). They're API-first, we're end-user app. Not competitive."

Q: "How do you compete with Google Analytics or HubSpot?"
A: "We integrate with them. They're traffic sources; we're attribution layer. Customers use us + GA, not either/or. HubSpot is marketing automation, we're analytics."

Q: "Your churn is 8% monthly. Why so high?"
A: "Gross churn 8%, but net retention 125% means expansion more than covers it. Churn is small customers (<$200/mo) who aren't good fit. Raising prices 2x next quarter to focus upmarket."

Q: "What's your unfair advantage? Why won't bigger player crush you?"
A: "3 patents on ML attribution model. 4 years of training data. Pre-built integrations with 40+ platforms took 2 years. Would take competitor 18-24 months to replicate. Moving fast to build moat."

SUCCESS CRITERIA:

Primary Objective:
✓ Secure commitment to partner meeting within 1 week

Secondary Objectives:
✓ Get confirmation that we fit their investment thesis
✓ Surface and address any deal-killer concerns
✓ Learn timeline for their decision process
✓ Get introduction to portfolio company for reference/partnership

QUESTIONS TO ASK:

Opening:
- "I know you've looked at the marketing analytics space. What's your current thesis on the opportunity?"

Discovery:
- "What would make this a compelling investment for Sequoia?"
- "What concerns or gaps do you see based on the deck?"

Qualification:
- "What's your typical timeline from first meeting to term sheet?"
- "What diligence would you need to complete before moving forward?"

Closing:
- "Based on what we've discussed, does this fit your portfolio thesis?"
- "What would be the next step if you're interested in moving forward?"

RISK MITIGATION:

Risk: They're concerned about market size
Response: "SMB marketing spend is $150B, growing 12% annually. We're capturing 0.01% now with path to 0.1% ($150M revenue) at maturity. That's venture-scale outcome."

Risk: They think we're too early stage
Response: "We've proven product-market fit: 35% MoM growth, 125% NRR, <5% logo churn past 6 months. GTM motion is repeatable. This is Series A risk profile."

Risk: They're concerned about competition
Response: "We welcome competition—validates market. Our moat is data (4 years), integrations (40+ platforms), and patents (3 filed, 1 granted). Speed is our advantage."

MATERIALS CHECKLIST:
- [x] Updated pitch deck (v3.2, sent 2/10)
- [x] Financial model (with scenarios)
- [x] Product demo environment (tested this morning)
- [x] Customer references (3 prepared to intro)
- [x] Cap table and current investor list
- [x] Data room link (ready to share if requested)

PRE-MEETING REMINDERS:
- Review latest SaaS metrics benchmarks (Jessica values this)
- Practice explaining ML model simply (for David)
- Prepare to discuss Series B vision (18-month plan)
- Have competitor matrix ready if asked
- Know exact numbers: MRR, growth %, NRR, churn, ACV, LTV:CAC

⏱️ TIMING: Meeting tomorrow at 2:00 PM PST (27 hours away)
🎯 ROI Impact: $3M funding unlocks $25M+ business value
⚡ Confidence Level: HIGH (strong metrics, warm intro, good fit)
```

### Example 2: Client Discovery Call Preparation

**Command:**

```bash
/meeting:prep "Discovery Call - Enterprise Tech Solutions" --type discovery --duration 45
```

**Output:**

```
Meeting Prep Complete: Discovery Call - Enterprise Tech Solutions

MEETING DETAILS:
Date: Today, 3:30 PM EST
Duration: 45 minutes
Platform: Google Meet (link below)
Participants:
  - Robert Martinez (CTO, robert@enterprisetech.com)
  - Lisa Wong (VP Marketing, lisa@enterprisetech.com)

PARTICIPANT PROFILES:

Robert Martinez - CTO, Enterprise Tech Solutions
- Company: B2B software, 150 employees, $30M revenue
- Background: 20-year tech veteran, 5 years at Enterprise Tech
- Priorities: Technical integration, security, scalability, vendor consolidation
- Recent activity: Attended AWS re:Invent last month
- Pain points: Managing 50+ marketing tools, data silos, attribution gaps
- Decision style: Thorough diligence, values references and security certifications
- Strategy: Emphasize security (SOC 2, GDPR), simple integration, vendor consolidation

Lisa Wong - VP Marketing, Enterprise Tech Solutions
- Company: Leads 12-person marketing team, $3M annual budget
- Background: 8 years in marketing, promoted internally 2 years ago
- Priorities: Marketing ROI, channel optimization, team efficiency, reporting to CEO
- Challenges: Justifying budget, proving marketing contribution to revenue
- Decision style: Data-driven, wants case studies and trial period
- Strategy: Lead with ROI metrics from similar customers, offer 30-day pilot

CONTEXT SUMMARY:

How They Found Us:
- Inbound lead from website download (Marketing Attribution Guide)
- Downloaded guide 1 week ago, requested demo same day
- Email sequence: Received 2 nurture emails, clicked "book demo" in second email

Email Context:
- Lisa's demo request: "Looking for better way to track marketing performance across channels. Current setup is mess of spreadsheets and disconnected tools."
- Pain point signals: mentioned "spreadsheets," "disconnected," "CEO asking hard questions"
- Urgency signal: "Would love to chat this week if possible"

Company Research:
- B2B software company, 150 employees, $30M revenue, Series B funded
- Tech stack: Salesforce, HubSpot, Google Ads, LinkedIn Ads, 6Sense, Marketo
- Recent news: Hired new CEO 6 months ago (Michael Stevens, former CFO background)
- LinkedIn company page: Posting about growth, hiring for sales team
- Competitive intel: Their competitor (TechRival) is our customer, great reference

Website Analysis:
- Downloaded our attribution guide (7-day email sequence initiated)
- Visited pricing page 3 times (strong buying signal)
- Viewed customer stories page, specifically case study from similar company

MEETING AGENDA:

Warm-up (5 min):
- Thank them for taking the time
- Acknowledge Lisa's attribution guide download: "What resonated most?"
- Confirm agenda: Understand situation, explore fit, determine next steps
- Set expectation: "I'll probably ask more questions than I answer. Want to make sure we're good fit before pitching anything."

Situation Analysis (10 min):
Discovery Questions:
✓ "Lisa, you mentioned your current setup is a mess of spreadsheets. Walk me through what you're doing today."
✓ "What prompted you to start looking for a solution now?"
✓ "Robert, from a technical perspective, what's your biggest frustration with current tools?"
✓ "What have you tried already to solve this problem?"
✓ "If you don't solve this, what's the business impact over the next 6-12 months?"

Expected Answers (based on research):
- Using Salesforce + HubSpot + Google Sheets for attribution
- CEO (CFO background) asking hard questions about marketing ROI
- Can't connect offline conversions (trade shows, call tracking) to digital
- Spending 10-15 hours/week on manual reporting
- Risk: Can't justify current $3M marketing budget, may face cuts

Needs Assessment (10 min):
Qualification Questions:
✓ "What would a successful solution look like? How would you know it's working?"
✓ "What's your timeline? When do you need this solved by?"
✓ "What's your process for evaluating and selecting a solution?"
✓ "Who else needs to be involved in the decision?" (get CEO involved?)
✓ "Have you allocated budget for this? What range are you working with?"

Expected Answers:
- Success: CEO confident in marketing spend, Lisa has clean reports
- Timeline: Want solution in place by Q2 (6 weeks away) for quarterly review
- Process: Robert does technical diligence, Lisa owns vendor selection, CEO final approval
- Budget: $20-40K/year range (our mid-tier plan $28K is perfect fit)

Solution Discussion (10 min):
Talking Points:
✓ "We work with several B2B software companies your size (name TechRival as reference)"
✓ "Average customer sees complete attribution picture within 2 weeks of setup"
✓ "Typical ROI: 15-30% improvement in marketing efficiency within 90 days"
✓ "We integrate with Salesforce, HubSpot, Google Ads, LinkedIn (all your stack)"
✓ "SOC 2 Type II certified, GDPR compliant, enterprise security standards" (for Robert)
✓ "Replaces your current spreadsheet process with automated dashboards"

Case Study to Reference:
"SoftwarePlus is similar to you—B2B software, $25M revenue, Salesforce + HubSpot stack. They were spending 15 hours/week on attribution reporting across 8 channels. Within 30 days of implementing our solution:
- Reporting time: 15 hours → 2 hours per week
- Marketing efficiency: +22% (reallocated budget from low-ROI channels)
- CFO confidence: Went from skeptical to advocate, approved 20% budget increase
- Integration: 1 week to full deployment, zero ongoing maintenance

Happy to intro you to their VP Marketing for a reference call."

Next Steps (10 min):
Proposed Path Forward:
✓ "Based on what we've discussed, I think we can definitely help. Here's what I propose:"
✓ "Step 1: I'll send detailed proposal with pricing, implementation plan, and ROI projection"
✓ "Step 2: We'll schedule technical deep-dive with Robert's team (30 min)"
✓ "Step 3: Assuming technical fit, we start 30-day pilot so you see results before committing"
✓ "Step 4: If pilot is successful, we move to annual contract"

Questions for Them:
✓ "Does that timeline work for you?"
✓ "What concerns or questions do you have at this point?"
✓ "Would a reference call with SoftwarePlus be valuable?"
✓ "Should we include your CEO in the proposal presentation?"

SUCCESS CRITERIA:

Primary Objective:
✓ Schedule proposal presentation meeting (include CEO if possible)

Secondary Objectives:
✓ Confirm budget range ($20-40K/year = we fit)
✓ Identify timeline and urgency (Q2 deadline = 6 weeks)
✓ Build rapport with both Lisa (user) and Robert (technical buyer)
✓ Surface any deal-killer objections (none expected based on fit)

Information Gathering:
✓ Confirm CEO involvement in decision (likely given CFO background)
✓ Understand competitive evaluation (are they talking to others?)
✓ Learn procurement process (legal, security review, contracting timeline)
✓ Identify internal champion (Lisa seems eager based on emails)

Disqualification Signals to Watch For:
✗ Budget under $15K/year (below our minimum, not good fit)
✗ Timeline beyond 6 months (not urgent, should deprioritize)
✗ Already selected competitor (evaluation is theater, waste of time)
✗ No CEO involvement (Lisa/Robert can't actually buy)
✗ Looking for services/agency (we're software product, wrong fit)

RISK MITIGATION:

Risk: They're talking to competitors
Response: "That makes sense. Most customers evaluate 2-3 solutions. What we hear from customers who choose us: easiest integration, best support, most accurate attribution. Happy to position us against whoever you're considering."

Risk: They want to see product before discussing needs
Pushback: "Totally understand. I do want to show you product, but I'd hate to waste your time showing features you don't need. Can we spend 10 minutes on your situation first, then I'll show exactly what's relevant?"

Risk: They're not ready to buy for 6+ months
Response: "No problem. When you say 6 months, is that when you'd start using it, or when you'd make the decision? Either way, would a 30-day pilot now make sense so you have data to support the decision when the time comes?"

Risk: Budget concerns (CEO former CFO, might be cheap)
Response: "I hear you on budget. Here's how to think about ROI: You're spending 15 hours/week on reporting (cost: $25K/year). You're likely wasting 15-20% of $3M budget on wrong channels (cost: $450-600K/year). Our solution is $28K/year. If we improve efficiency by just 5%, you've 5x'd your investment."

Risk: Robert concerned about integration complexity
Response: "Great question. Integration is actually our strength. We have pre-built connectors for all your tools (Salesforce, HubSpot, Google Ads, LinkedIn). Typical implementation: 1 week, mostly configuration. I'll have our solutions architect join the technical deep-dive to walk through specifics."

QUESTIONS TO ASK:

Opening (Build Rapport):
- "Lisa, I saw you downloaded our attribution guide last week. What specifically resonated with you?"
- "How long have you both been at Enterprise Tech? What's the company journey been like?"
- "I noticed you hired a new CEO 6 months ago. Has that changed priorities for marketing?"

Discovery (Understand Problem):
- "Walk me through your current attribution process from end to end."
- "What's working well with your current setup? What's not?"
- "When did you first realize this was a problem that needed solving?"
- "What's the impact on your team? On your relationship with the CEO?"
- "Have you looked at other solutions before? What happened?"

Qualification (Assess Fit):
- "What would make this a home run solution for you?"
- "What's your timeline for making a decision?"
- "Who else needs to be part of the evaluation and decision?"
- "What's your budget range for a solution like this?"
- "What criteria will you use to choose between alternatives?"

Technical (For Robert):
- "What are your top 3 technical requirements or concerns?"
- "How do you typically evaluate vendor security and compliance?"
- "What's your process for approving new vendors and integrations?"
- "Any other tools or projects you're evaluating that might conflict?"

Closing (Drive Action):
- "Based on what we've discussed, do you see this being a good fit?"
- "What concerns or questions do you have at this point?"
- "Would a 30-day pilot make sense so you can see results before committing?"
- "What would you need from me to move forward with next steps?"

MATERIALS CHECKLIST:
- [x] Screen share presentation prepared (company overview, product tour)
- [x] SoftwarePlus case study (similar customer reference)
- [x] ROI calculator spreadsheet (to show their specific numbers)
- [x] Security documentation (SOC 2 report, compliance overview)
- [x] Integration overview (Salesforce + HubSpot connectors)
- [x] Pricing sheet (show $28K/year tier, annual vs. monthly)
- [x] Proposal template ready to customize after call
- [x] Calendly link for follow-up meeting (technical deep-dive)

PRE-MEETING REMINDERS:
- Review SoftwarePlus case study details (reference customer)
- Prepare screen share: product demo environment with mock data
- Have TechRival reference ready to mention (their competitor is our customer)
- Review their tech stack (Salesforce, HubSpot, Google Ads, LinkedIn, 6Sense, Marketo)
- Prepare to discuss CEO involvement (former CFO, likely cares about ROI)
- Have 30-day pilot details ready (implementation plan, success metrics)

⏱️ TIMING: Meeting today at 3:30 PM EST (2 hours away)
🎯 ROI Impact: $28K annual contract, $336K total LTV (3-year average)
⚡ Confidence Level: HIGH (strong fit, urgent timeline, budget matches)
```

## Quality Control Checklist

**Context Gathering Complete:**

- [ ] Calendar event retrieved with all participant details
- [ ] CRM records reviewed for relationship history and notes
- [ ] Email threads analyzed for discussion context and tone
- [ ] LinkedIn profiles researched for background and communication style
- [ ] Company research completed (news, funding, competitive position)
- [ ] Relevant documents reviewed (proposals, decks, contracts shared)

**Meeting Agenda Prepared:**

- [ ] Agenda structure appropriate for meeting type (pitch, discovery, partnership)
- [ ] Time allocations realistic and properly paced
- [ ] Each agenda section has clear objectives
- [ ] Transitions between sections planned (avoid awkward jumps)
- [ ] Buffer time included for overruns or extended discussion

**Talking Points Developed:**

- [ ] Key messages prepared for each agenda section
- [ ] Supporting data and metrics included (specific, credible)
- [ ] Differentiation from competitors clearly articulated
- [ ] Value proposition tailored to participant priorities
- [ ] Objection responses prepared for likely concerns

**Participant Profiling:**

- [ ] Profile created for each key participant
- [ ] Background research includes role, tenure, decision authority
- [ ] Communication preferences and style identified
- [ ] Personal rapport opportunities identified (mutual connections, interests)
- [ ] Individual priorities and concerns noted with response strategies

**Questions Prepared:**

- [ ] Opening questions ready to build rapport
- [ ] Discovery questions prepared to understand situation deeply
- [ ] Qualification questions ready to assess fit and timeline
- [ ] Technical questions prepared for technical stakeholders
- [ ] Closing questions ready to drive next actions

**Success Criteria Defined:**

- [ ] Primary objective clearly stated (must achieve)
- [ ] Secondary objectives identified (highly desired)
- [ ] Information gathering goals specified (essential to learn)
- [ ] Relationship building targets set (rapport milestones)
- [ ] Disqualification signals identified (know when to walk away)

**Risk Assessment Complete:**

- [ ] Potential obstacles identified for this specific meeting
- [ ] Mitigation strategies prepared for each risk
- [ ] Alternative paths planned if primary approach blocked
- [ ] Deal-breaker scenarios identified with response plans

**Materials Ready:**

- [ ] All presentations, demos, documents prepared and tested
- [ ] Technical setup verified (video, audio, screen sharing)
- [ ] Leave-behind materials prepared (follow-up email, documents)
- [ ] Reference materials accessible (notes, participant profiles)
- [ ] Backup plans ready for technical failures

**Timing & Logistics:**

- [ ] Meeting time confirmed and calendar reminder set
- [ ] Time zone conversions verified if participants in different zones
- [ ] Pre-meeting routine planned (15 minutes before)
- [ ] Post-meeting debrief scheduled (capture notes immediately)
- [ ] Follow-up actions pre-planned (email template ready)

## Best Practices

**Over-Prepare, Then Relax**
Thorough preparation is the antidote to meeting anxiety. Spend 30-45 minutes preparing for high-stakes meetings, then trust your preparation and be present. The goal isn't to script every word, but to be so prepared that you can be spontaneous and authentic while having all the information you need at your fingertips.

**Focus on Understanding, Not Pitching**
The best meetings are 70% listening, 30% talking. Use your preparation to ask better questions, not to talk more. Your research enables you to ask informed questions that demonstrate respect for their time and context, building trust faster than any pitch can.

**Prepare Multiple Conversation Paths**
Meetings rarely follow the planned agenda exactly. Prepare for 3-4 likely conversation directions based on their priorities. If they want to dive deep on technical integration, have that path ready. If they want to focus on ROI, have that conversation prepared. Flexibility backed by preparation is powerful.

**Treat Preparation as Pattern Learning**
Meeting prep compounds over time. The first investor pitch takes 60 minutes to prepare. The tenth takes 15 minutes because you've internalized the pattern. Build templates for recurring meeting types (investor, client, partner, interview) and refine them based on what works.

**Schedule Prep Time, Don't Wing It**
Block 30-45 minutes on your calendar before important meetings for formal preparation. Treat this time as sacred—resist the urge to "wing it" even when you're busy. The ROI on preparation time is 10-20x in meeting outcomes and confidence.

**Share Agendas in Advance (Sometimes)**
For collaborative meetings (partnerships, client work sessions), share the agenda 24 hours in advance so participants can prepare. For sales or negotiation meetings, consider keeping agenda internal so you maintain control of conversation flow. Context matters.

**Rehearse Opening and Closing**
The first 2 minutes and last 5 minutes of meetings are disproportionately important. Practice your opening greeting and context-setting out loud. Prepare your closing summary and call-to-action. Everything else can be more flexible, but nail the bookends.

**Prepare to Be Wrong**
Your research and assumptions might be incorrect. Prepare questions that test your assumptions early in the meeting. Be ready to pivot if you learn their situation is different than you expected. Flexibility is a strength, not a weakness.

## Integration Points

**Calendar Integration:**

- Google Calendar API for meeting details, participant lists, scheduling
- Outlook Calendar for enterprise customers using Microsoft stack
- Apple Calendar for solopreneurs using Mac ecosystem
- Automatic meeting detection and prep suggestions based on calendar patterns

**CRM Integration:**

- Salesforce for enterprise customer and deal history
- HubSpot for contact profiles and interaction history
- Zoho CRM for small business relationship tracking
- Pipeline for lightweight deal tracking and notes

**Email Integration:**

- Gmail API for email thread analysis and context
- Outlook for enterprise email integration
- Email parsing to extract discussion points and concerns
- Sentiment analysis on email tone and urgency

**Research Tools:**

- LinkedIn for participant profiles and mutual connections
- Crunchbase for company funding and growth data
- Google News for recent company announcements
- Company website scraping for products, team, values

**Document Management:**

- Google Drive for shared presentations and proposals
- Dropbox for document access and collaboration
- DocSend for deck analytics (who viewed, time spent, drop-off points)
- Notion for meeting notes and knowledge management

**Communication Platforms:**

- Zoom integration for video meeting links and recording
- Google Meet for GSuite-based meeting platforms
- Microsoft Teams for enterprise meeting coordination
- Slack for team collaboration on meeting prep

## Success Criteria

**Preparation Quality:**

- Comprehensive context gathered from all available sources (CRM, email, calendar, web)
- Participant profiles complete with communication strategies
- Meeting agenda tailored to meeting type with realistic time allocations
- Talking points prepared with supporting data and objection responses
- Success criteria clearly defined with primary, secondary, and information gathering objectives

**Time Efficiency:**

- Preparation time reduced from 45-60 minutes (manual) to 15-20 minutes (AI-assisted)
- Context aggregation automated (no manual searching through emails/CRM)
- Template-based agenda generation adapted to specific meeting
- Reusable participant profiles for recurring contacts (build once, reference forever)

**Meeting Outcomes:**

- Primary meeting objective achieved in 75%+ of prepared meetings
- Reduction in "we should have discussed X" post-meeting regrets
- Increase in closed deals, advanced partnerships, or successful hires (20-35% improvement)
- Fewer surprise objections or questions (better anticipation through prep)
- Stronger rapport building through research-informed conversation

**Confidence & Performance:**

- Measurable reduction in pre-meeting anxiety (self-reported)
- Increased confidence in meeting performance (self-assessment)
- Positive feedback from meeting participants on preparation and professionalism
- Fewer meetings where you feel caught off-guard or unprepared
- More meetings where you drive the conversation proactively

**Strategic Value:**

- Better qualification of opportunities before investing time (avoid bad-fit meetings)
- Improved negotiating leverage through research and preparation
- Stronger positioning against competitors through differentiation prep
- More effective objection handling through pre-prepared responses
- Higher-value meetings through strategic question preparation

## Common Use Cases

**Use Case 1: Investor Pitch (Seed/Series A)**
Solo founder preparing for first institutional investor meeting. Use meeting prep to research investor background, portfolio companies, investment thesis, and recent activity. Prepare responses to likely questions (market size, competition, team gaps, unit economics). Develop multiple conversation paths based on investor focus (product, traction, team, market). Expected outcome: Advance to partner meeting or secure term sheet discussion.

**Use Case 2: High-Stakes Client Sales Call**
Enterprise deal worth $50K-500K requiring C-level approval. Research all participants (CTO, VP Marketing, CFO), understand company priorities and recent challenges, prepare business case with ROI calculations specific to their situation. Develop technical responses for CTO concerns, ROI justification for CFO, and value messaging for VP Marketing. Expected outcome: Advance to proposal stage or pilot program.

**Use Case 3: Strategic Partnership Discussion**
Meeting with potential technology partner for product integration or co-marketing. Research company positioning, competitive landscape, partnership portfolio, and integration requirements. Prepare mutual value proposition, technical integration approach, go-to-market collaboration plan, and commercial terms framework. Expected outcome: Agreement on LOI or term sheet for partnership.

**Use Case 4: Key Hire Interview (Senior Role)**
Interviewing senior engineering, sales, or operations hire. Research candidate background, previous companies, mutual connections, and public work (GitHub, blog posts, talks). Prepare questions to assess technical competency, cultural fit, and motivation. Develop compelling pitch for why they should join your company. Expected outcome: Advance candidate to final round or extend offer.

**Use Case 5: Board Meeting or Investor Update**
Quarterly update to board of directors or key investors. Review previous meeting notes and action items, prepare performance metrics and variance analysis, develop strategic discussion topics, and anticipate tough questions on challenges or missed targets. Expected outcome: Maintain investor confidence, secure support for key decisions, get strategic advice on challenges.

**Use Case 6: Damage Control or Difficult Conversation**
Meeting to address customer complaint, partnership conflict, or team performance issue. Research history of relationship, specific incidents causing tension, and perspective of other party. Prepare empathetic opening, acknowledgment of legitimate concerns, proposed solutions with specific actions, and rebuild trust plan. Expected outcome: Preserve relationship, agree on resolution path, restore goodwill.

## Troubleshooting

**Problem: Not enough context available for participant research**

- Solution: Use LinkedIn, company website, Google search, and mutual connections for public information. Ask your network for introductions or insights. Check if they've published content (blog posts, tweets, talks). Even minimal research is better than none.

**Problem: Meeting agenda doesn't fit meeting type**

- Solution: Use template agendas for common meeting types (investor, client, partnership, interview). Customize based on your specific goals. Ask the meeting organizer what they want to cover if unclear.

**Problem: Too many talking points, overwhelming prep doc**

- Solution: Prioritize top 3-5 key messages. Move detailed points to appendix for reference if needed. Focus on what you must communicate, not everything you could say. Less is more.

**Problem: Participant profiles reveal conflicting priorities**

- Solution: Acknowledge different stakeholder concerns explicitly in meeting. Address each person's priority at some point. Prepare responses that satisfy multiple concerns simultaneously when possible.

**Problem: Research reveals this is likely a bad-fit meeting**

- Solution: Use meeting to disqualify politely and quickly (15 minutes), rather than investing full time. Offer to refer them to better-fit alternative if possible. Your time is valuable—don't waste it on poor-fit opportunities.

**Problem: Meeting scheduled too soon, not enough prep time**

- Solution: Use quick prep template (10 minutes): Who are they? What do they want? What's my goal? What are my top 3 points? What's my call-to-action? Better than nothing.

**Problem: Prep document too long to review before meeting**

- Solution: Create executive summary at the top: 3 key participant insights, 3 main talking points, 1 primary objective. Full prep doc is reference material, not required reading.
