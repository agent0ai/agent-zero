---
description: Generate go-to-market strategy and launch plan
argument-hint: [--idea <description>] [--budget <amount>] [--timeline <months>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Go-To-Market Strategy & Launch Plan Generator

Generate a comprehensive, day-by-day GTM playbook for product launches including pre-launch strategy, launch day timeline, post-launch optimization, and 30-60-90 day content calendar.

## ROI: $70,000/year

- **Manual GTM Planning**: $15K-25K (consulting fees) + 3-4 weeks
- **AI-Assisted GTM**: $2K-5K (tools) + 3-5 days
- **Savings**: $10K-20K per launch + 2-3 weeks faster to market
- **Typical launches per year**: 3-4 products
- **Annual savings**: $30K-80K + 6-12 weeks of time

---

## Command Syntax

```bash
# Basic usage
/startup:gtm --idea "AI email productivity tool" --budget 10000 --timeline 90

# With specific target audience
/startup:gtm \
  --idea "SaaS project management for remote teams" \
  --target "B2B, 50-500 employee companies" \
  --budget 25000 \
  --timeline 120

# With product details
/startup:gtm \
  --product "CRM for real estate agents" \
  --price 99 \
  --audience "Real estate professionals, USA" \
  --budget 15000 \
  --channels "linkedin,google,facebook"
```

### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--idea` or `--product` | Yes | Product description | "AI email assistant" |
| `--budget` | Yes | Total marketing budget (USD) | 10000, 25000, 50000 |
| `--timeline` | Yes | Days until launch | 30, 60, 90, 120 |
| `--target` or `--audience` | No | Target customer segment | "B2B SaaS companies" |
| `--price` | No | Product price point | 29, 99, 299 |
| `--channels` | No | Marketing channels (comma-separated) | "linkedin,google,twitter" |
| `--stage` | No | Business stage | "mvp", "beta", "launch", "growth" |

---

## What This Command Generates

### Output Structure

```
/gtm-plans/[product-name]/
├── 1-pre-launch/
│   ├── beta-program-plan.md (Beta recruitment, onboarding, feedback loops)
│   ├── waitlist-strategy.md (Landing page, lead magnets, nurture sequences)
│   ├── press-outreach.md (Journalist lists, pitch templates, embargo strategy)
│   └── community-building.md (Reddit, Discord, Slack communities to engage)
│
├── 2-launch-day/
│   ├── hour-by-hour-timeline.md (Every hour from 6 AM to 10 PM)
│   ├── product-hunt-playbook.md (Timing, hunter selection, comment strategy)
│   ├── social-media-posts.md (Pre-written posts for all platforms)
│   └── community-engagement.md (Where to post, what to say, response templates)
│
├── 3-post-launch/
│   ├── week-1-priorities.md (First 7 days: monitoring, responding, iterating)
│   ├── feedback-loops.md (How to collect, analyze, act on user feedback)
│   ├── pricing-experiments.md (A/B tests, discount strategies, upsell tactics)
│   └── growth-loops.md (Referral programs, viral mechanics, retention hooks)
│
├── 4-content-calendar/
│   ├── days-1-30.md (Daily posting schedule with themes)
│   ├── days-31-60.md (Weekly themes and content pillars)
│   ├── days-61-90.md (Strategic announcements and milestones)
│   └── evergreen-content.md (Reusable content library)
│
└── 5-metrics-dashboard/
    ├── kpi-tracking.md (What to measure, tools to use)
    ├── channel-attribution.md (Which channels drive best users)
    └── weekly-reports.md (Template for stakeholder updates)
```

### Execution Time

- **Input collection**: 2-3 minutes (answer strategic questions)
- **GTM generation**: 4-6 minutes (AI creates complete plan)
- **Review & customization**: 10-15 minutes (adjust for your context)
- **Total**: 15-20 minutes vs. 3-4 weeks manually
*(Time varies by product complexity: 10-25 minutes typical)*

---

## Step 1: Product & Market Analysis

Before generating the GTM plan, Claude will ask you strategic questions:

### Product Questions

```
1. What problem does your product solve?
   - Example: "Email overload - professionals waste 10+ hours/week"

2. What's your unique solution?
   - Example: "AI email triage that auto-categorizes and prioritizes"

3. What's your unfair advantage?
   - Example: "Proprietary algorithm trained on 15K SaaS professionals' inboxes"

4. What's your pricing model?
   - Options: Free trial → Paid, Freemium, One-time purchase, Usage-based
   - Example: "$29/month after 14-day free trial"

5. What's your current product stage?
   - MVP (core features only)
   - Beta (feature-complete, needs testing)
   - Launch (ready for public release)
   - Growth (launched, scaling now)
```

### Market Questions

```
1. Who is your ideal customer?
   - Demographics: Age, location, job title, income
   - Psychographics: Values, pain points, goals
   - Example: "Founders/CEOs of 10-100 person SaaS companies, USA, overwhelmed by email"

2. What's your total addressable market (TAM)?
   - Example: "500K SaaS companies in USA, 30% have email pain point = 150K TAM"

3. Who are your top 3 competitors?
   - Example: "Superhuman, Spark, SaneBox"

4. What's your differentiation?
   - Example: "We're 1/3 the price of Superhuman, 3x better AI than SaneBox"

5. What channels does your audience use?
   - Example: "LinkedIn (professional), Twitter (tech community), Product Hunt (early adopters)"
```

### Budget Questions

```
1. What's your total marketing budget?
   - Example: "$10,000 for 90-day launch period"

2. How should budget be split?
   - Paid ads: 40-50% ($4K-5K)
   - Content/influencer: 20-30% ($2K-3K)
   - Tools/software: 10-15% ($1K-1.5K)
   - Contingency: 10-20% ($1K-2K)

3. What's your customer acquisition cost (CAC) target?
   - Example: "Under $50 per trial signup, under $150 per paying customer"

4. What's your expected customer lifetime value (LTV)?
   - Example: "$29/month × 12 months avg retention = $348 LTV"

5. What's your LTV:CAC ratio target?
   - Rule of thumb: 3:1 or better
   - Example: "$348 LTV ÷ $150 CAC = 2.3:1 (acceptable, aim for 3:1)"
```

---

## Pre-Launch Strategy (Weeks -4 to 0)

### Week -4: Beta Program Setup

**Goal**: Recruit 50-100 beta users who will provide feedback AND become launch day advocates

#### Beta Recruitment Strategy

```markdown
**Target Beta User Profile**:
- Early adopter mindset (loves trying new products)
- Experiences the problem acutely (email pain daily)
- Active in communities (will share on social media)
- Decision-maker (can purchase if they love it)
- Diverse use cases (different industries, team sizes)

**Recruitment Channels**:
1. LinkedIn outreach (50 targeted DMs to ideal customers)
2. Twitter/X thread (share problem + solution, ask for beta testers)
3. Reddit posts (r/SaaS, r/productivity, r/startups)
4. Indie Hackers post (community loves beta testing)
5. Personal network (friends, former colleagues, advisors)

**Beta Application Form** (Typeform/Google Forms):
- Name, Email, Company, Role
- "Describe your email pain in one sentence"
- "How many hours per week do you spend on email?"
- "What tools have you tried? What didn't work?"
- "If selected, can you commit to 2 weeks of active testing?"
- "Will you share your experience on social media?"
```

#### Beta Program Structure

```markdown
**Week 1: Onboarding**
- Day 1: Welcome email + Loom video walkthrough
- Day 2: Calendar invite for 1:1 onboarding call (15 min)
- Day 3: Check-in email: "Any questions so far?"
- Day 5: Feature highlight email: "Did you know you can...?"
- Day 7: First feedback survey (NPS + open-ended)

**Week 2: Deep Engagement**
- Day 8: Slack/Discord invite (private beta community)
- Day 10: Feature request brainstorm (what's missing?)
- Day 12: Bug report check-in (anything broken?)
- Day 14: Final survey + testimonial request

**Beta Incentives**:
- Lifetime 50% discount (if they become paying customers)
- First 10 users: Lifetime free (power user advocates)
- Recognition: "Founding Member" badge in product
- Exclusive: Early access to all future features

**Beta Success Metrics**:
- 70%+ activation rate (actually use the product)
- 50%+ weekly active users (WAU)
- 30%+ complete feedback surveys
- 20%+ willing to give testimonials
- 10%+ willing to do video testimonials
```

---

### Week -3: Waitlist Building

**Goal**: Build waitlist of 500-1,000 qualified leads before launch

#### Landing Page Strategy

```markdown
**Landing Page Elements**:
1. **Hero Section** (Above the fold):
   - Headline: Problem + Solution in 10 words
     Example: "Stop wasting 10 hours/week on email. Let AI handle it."
   - Subheadline: Unique value proposition (1 sentence)
     Example: "AI email triage saves professionals 8.5 hours/week by auto-organizing, prioritizing, and responding."
   - CTA: "Join the Waitlist" (bright button, high contrast)
   - Social Proof: "Join 1,247 professionals already on the waitlist"

2. **Problem Section** (Visual storytelling):
   - Show the pain: GIF of overflowing inbox, frustrated person
   - Stats: "The average professional spends 28% of their workday on email"
   - Relatable: "Sound familiar? You're not alone."

3. **Solution Section** (Product demo):
   - 30-second product demo video (Loom, no audio needed)
   - "How It Works" (3 steps):
     1. Connect your inbox
     2. AI learns your priorities
     3. Save 8.5 hours per week
   - Screenshots with annotations

4. **Social Proof Section**:
   - Beta user testimonials (photos, names, companies)
   - "Trusted by teams at: [logos of beta users' companies]"
   - Video testimonials (if available)

5. **Pricing Preview** (Build anticipation):
   - "Launch Price: $29/month"
   - "Waitlist Members: $19/month (limited time)"
   - "First 100 signups: Lifetime $19/month"

6. **Final CTA** (High-converting):
   - "Get Early Access + 34% Off Forever"
   - Email signup form (email only, keep friction low)
   - Privacy note: "We'll never spam you. Unsubscribe anytime."
```

#### Waitlist Growth Tactics

```markdown
**Week -3: Organic Channels** (0-200 signups):
1. Personal LinkedIn post (share founder story, problem, solution)
2. Twitter thread (10-tweet breakdown of problem + beta results)
3. Indie Hackers post (transparent founder journey)
4. Reddit posts (r/SaaS, r/productivity - focus on value, not promotion)
5. Email personal network (friends, former colleagues, advisors)

**Week -2: Community Engagement** (200-500 signups):
1. Slack communities (SaaS Growth, Founder communities)
2. Discord servers (Indie Hackers, startup communities)
3. Facebook Groups (SaaS founders, productivity hackers)
4. Quora answers (answer email productivity questions, link in bio)
5. Hacker News "Show HN" (if product is dev-focused)

**Week -1: Influencer/Partner Outreach** (500-1,000 signups):
1. Micro-influencers (10K-50K followers in productivity niche)
   - Offer: Free lifetime access + $500 for honest review
   - Platform: Twitter, LinkedIn, YouTube
2. Newsletter sponsorships (productivity, SaaS, founder newsletters)
   - Cost: $200-500 per newsletter (5K-20K subscribers)
3. Podcast guest appearances (SaaS, productivity, startup podcasts)
4. Co-marketing with complementary tools (Calendly, Notion, Slack)
5. Affiliate program setup (20% lifetime commission for referrals)
```

#### Waitlist Nurture Sequence

```markdown
**Email Sequence** (Send every 3-5 days):

**Email 1: Welcome** (Sent immediately):
Subject: "You're on the list! 🎉 Here's what happens next"
- Thank you for joining
- What to expect: Launch date, exclusive early access
- Ask: "What's your biggest email pain point?" (reply to this email)
- CTA: Share on social media (Twitter, LinkedIn pre-written posts)

**Email 2: Founder Story** (Day 3):
Subject: "Why I built this (after wasting 15 hours/week on email)"
- Personal story: founder's email pain
- Aha moment: realization that AI could solve this
- Beta results: "Our beta users save 8.5 hours/week on average"
- CTA: Reply with your email horror story

**Email 3: Sneak Peek** (Day 7):
Subject: "First look: How [Product] organizes your inbox in 60 seconds"
- 60-second product demo video
- Highlight: AI auto-categorization feature
- Beta testimonial: "I went from 3,482 unread to inbox zero in one day"
- CTA: Join our Slack community (early access to ask questions)

**Email 4: Social Proof** (Day 11):
Subject: "What beta users are saying (spoiler: they love it)"
- 5 beta user testimonials with photos
- Stats: "92% of beta users say they can't go back to manual email"
- Case study: "How Sarah saved 12 hours/week and closed 30% more deals"
- CTA: Refer a friend, move up the waitlist

**Email 5: Launch Countdown** (Day 15):
Subject: "We're launching in 7 days 🚀 Here's your exclusive offer"
- Launch date announcement
- Exclusive waitlist offer: "$19/month forever (33% off $29)"
- Urgency: "Offer ends 24 hours after launch"
- CTA: Mark your calendar, set reminder

**Email 6: Launch Announcement** (Launch Day):
Subject: "We're live! 🎉 Claim your $19/month lifetime deal now"
- Product is live, link to signup
- Restate exclusive offer and urgency
- Launch day bonuses: "First 100: Free 1:1 onboarding call"
- CTA: Sign up now (big button)
```

---

### Week -2 to -1: Press & Influencer Outreach

**Goal**: Secure 3-5 media mentions and 5-10 influencer posts for launch day

#### Press Outreach Strategy

```markdown
**Target Publications**:
- Tier 1: TechCrunch, The Verge, Ars Technica (hard to get, high impact)
- Tier 2: VentureBeat, Mashable, Lifehacker (moderate difficulty, good reach)
- Tier 3: Niche blogs (SaaS Mag, Productivity blogs) (easy, targeted audience)

**Journalist Research** (Use SparkToro, Twitter, LinkedIn):
1. Find journalists who cover: SaaS, productivity, AI, email tools
2. Read their recent articles (understand their beat, style, interests)
3. Identify their pitch preferences (email, Twitter DM, press release)
4. Personalize outreach (reference their recent work)

**Pitch Email Template**:
```

Subject: [Exclusive] AI email tool saves professionals 8.5 hrs/week (beta results)

Hi [First Name],

I saw your recent piece on [article title] - loved your take on [specific insight].

I'm reaching out because I built something your readers might find interesting: an AI email tool that saves professionals 8.5 hours/week (backed by data from 100 beta users).

**The Problem**: The average professional spends 28% of their workday on email. Existing solutions (Superhuman, SaneBox) are either too expensive ($30/month) or too basic (simple filtering).

**Our Solution**: AI email triage that learns your priorities and auto-organizes, prioritizes, and drafts responses. Beta users saved 8.5 hours/week on average.

**The Data**:

- 100 beta users tested for 2 weeks
- 92% said they "can't go back" to manual email
- Average time saved: 8.5 hours/week
- 78% said it increased their deal close rate (for sales professionals)

**Why Now**: We're launching on Product Hunt on [Date] and offering lifetime pricing at $19/month (vs. $29 regular).

**What I'm Offering**:

- Exclusive early access for you to test (before public launch)
- 1:1 interview with me (founder story, AI insights)
- Access to beta user data/testimonials
- Embargo until [Date] if you'd like exclusivity

Would you be interested in covering this? Happy to provide whatever you need.

Best,
[Your Name]
[Product Name] Founder
[Email] | [Twitter] | [Product URL]

```

**Follow-Up Strategy**:
- Day 3: Polite follow-up if no response
- Day 7: Share additional traction data (new beta results, waitlist growth)
- Day 10: Offer different angle (founder story, AI technical deep-dive)
- Day 14: Final follow-up, then move on

**Press Kit** (Hosted on website):
- Founder high-res photos (3-5 headshots, action shots)
- Product screenshots (high-res, annotated)
- Product demo video (60 seconds, no audio needed)
- Company logos (PNG, SVG in various sizes)
- Beta user testimonials (quotes, photos, permissions)
- Press release (standard format, ready to publish)
- Fact sheet (one-pager: problem, solution, traction, pricing)
```

#### Influencer Collaboration

```markdown
**Influencer Tiers**:
- **Micro (10K-50K followers)**: $500-2K per post, highest engagement
- **Mid-tier (50K-200K followers)**: $2K-10K per post, good reach
- **Macro (200K+ followers)**: $10K-50K per post, broad awareness

**Budget Allocation** (Assuming $10K marketing budget):
- 5-10 micro-influencers: $500-1K each = $5K-10K
- 1-2 mid-tier influencers: $2K-5K each = $2K-10K
- Skip macro (too expensive for early-stage)

**Influencer Outreach Template**:
```

Subject: Collaboration: [Product] launch (free lifetime + $500)

Hi [First Name],

I've been following your content on [Platform] for a while - your [specific post/video] on [topic] really resonated.

I'm launching [Product], an AI email tool that saves professionals 8.5 hours/week, and I think your audience would love it.

**What I'm Proposing**:

- Free lifetime access for you (worth $348/year)
- $500 flat fee for an honest review/post
- No script - share your genuine experience (good or bad)
- Timeline: 1 week to test, then post on launch day ([Date])

**Why Your Audience Will Care**:

- [Insight about their audience's pain point]
- Beta users saved 8.5 hours/week on average
- 92% say they "can't go back" to manual email

Would you be interested? Happy to send you early access to test.

Best,
[Your Name]

```

**Influencer Brief** (What to send if they agree):
- Product overview (1-page summary)
- Key features to highlight (top 3-5 features)
- Talking points (pain point, solution, results)
- Hashtags to use (#productivity, #AI, #emailhacks)
- Posting guidelines (when to post, how to tag, disclosure requirements)
- Content examples (show what good posts look like)
- Review by date (give them 1 week to test)
- Post date (launch day)
```

---

### Week -1: Launch Day Preparation

**Goal**: Have everything ready for a smooth, coordinated launch

#### Pre-Launch Checklist

```markdown
**Product Readiness**:
□ All critical bugs fixed
□ Onboarding flow tested (5+ people)
□ Payment processing tested (Stripe test mode → live mode)
□ Analytics implemented (Mixpanel, Amplitude, or PostHog)
□ Error tracking enabled (Sentry)
□ Customer support ready (Intercom, help docs, FAQ)

**Marketing Assets**:
□ Landing page live and tested (mobile + desktop)
□ Product Hunt page drafted (not published yet)
□ Social media posts pre-written (Twitter, LinkedIn, Facebook)
□ Community posts pre-written (Reddit, Indie Hackers, Hacker News)
□ Email to waitlist drafted (ready to send at launch)
□ Press release finalized and embargoed

**Team Coordination**:
□ Launch day timeline shared with team
□ Roles assigned (who posts where, who monitors feedback)
□ Communication channel set up (Slack channel #launch-day)
□ Backup plans for common issues (server down, payment failures)

**Metrics Dashboard**:
□ Real-time dashboard set up (Datadog, Grafana, or Mixpanel Live View)
□ KPIs defined (signups, conversions, revenue, engagement)
□ Alert thresholds set (if signups < X, investigate)

**Community Prep**:
□ Reply templates for common questions
□ Response strategy for negative feedback
□ Engagement plan for positive feedback (thank, ask for testimonial)
```

---

## Launch Day Playbook (Day 0)

### Hour-by-Hour Timeline (All times in your local timezone)

```markdown
**6:00 AM - Pre-Launch Final Check**
□ Product live and tested (do a full signup flow yourself)
□ Analytics firing correctly (test a conversion)
□ Payment processing working (test with real card, refund immediately)
□ Team briefed and ready (everyone knows their role)
□ Launch day Slack channel active
□ Coffee brewed ☕

**7:00 AM - Product Hunt Launch**
□ Submit to Product Hunt (maker account, not hunter)
□ Publish launch post (title, tagline, description, images, video)
□ Share with team: "We're live! Here's the link"
□ Pin Product Hunt link in all social bios
□ Monitor for early comments (first 10 comments critical)

**8:00 AM - Email Waitlist**
□ Send "We're Live!" email to entire waitlist (500-1,000 people)
□ Monitor email open rates (Mailchimp, ConvertKit dashboard)
□ Respond to email replies within 15 minutes
□ Track signups from email (UTM: source=email, campaign=launch)

**9:00 AM - Social Media Blitz (Twitter)**
□ Founder posts launch tweet (personal account)
  - Problem statement
  - Solution overview
  - Link to Product Hunt
  - Ask for upvote + feedback
□ Company account retweets
□ Ask team/advisors to retweet and comment
□ Engage with every reply (thank, answer questions)

**10:00 AM - Social Media Blitz (LinkedIn)**
□ Founder posts on LinkedIn (longer-form story)
  - Founder journey: Why I built this
  - Beta results: 8.5 hours/week saved
  - Link to Product Hunt (ask for support)
□ Company page posts
□ Tag beta users (if they gave permission)
□ Engage with every comment

**11:00 AM - Community Engagement (Reddit)**
□ Post to r/SaaS, r/productivity, r/startups
  - Follow subreddit rules (some require "Show & Tell" flair)
  - Focus on value, not promotion
  - Be transparent: "I'm the founder, built this to solve my own problem"
□ Respond to every comment within 30 minutes
□ Provide value in responses (not just "thank you")

**12:00 PM - Community Engagement (Indie Hackers)**
□ Post launch update in Indie Hackers
  - Title: "🚀 Launched: [Product] on Product Hunt today!"
  - Share metrics: Waitlist size, beta results, traction
  - Ask for feedback: "What would make this a must-have for you?"
□ Engage with community (Indie Hackers loves transparency)

**1:00 PM - Check Product Hunt Ranking**
□ Monitor Product Hunt ranking (goal: top 5 for the day)
□ If slipping: Ask team/network to upvote and comment
□ Engage with EVERY comment on Product Hunt page
□ Answer questions transparently
□ Thank people for upvotes and feedback

**2:00 PM - Influencer Coordination**
□ Check in with influencers (DM: "We're live! Here's the link")
□ Share their posts immediately when they go live
□ Thank them publicly (retweet, comment, tag)
□ Monitor traffic from influencer posts (UTM tracking)

**3:00 PM - Press Check-In**
□ Email journalists who showed interest
□ Share early traction: "We hit #3 on Product Hunt today!"
□ Offer fresh angle: "Our users are already saving 8.5 hrs/week"
□ Be available for quick interviews

**4:00 PM - Monitor & Respond**
□ Check all channels: Twitter, LinkedIn, Reddit, Indie Hackers, PH
□ Respond to every mention, question, comment
□ Document common questions (update FAQ)
□ Escalate critical issues to team (Slack #launch-day)

**5:00 PM - Metrics Review**
□ Check KPIs:
  - Product Hunt rank (#1-5 = success, #6-10 = good, #11+ = improve)
  - Signups (goal: 100-500 on launch day)
  - Conversion rate (trial signups → paid)
  - Revenue (if charging upfront)
  - Website traffic (10K-50K visits = good)
□ Share progress with team (celebrate wins!)

**6:00 PM - Evening Push (Twitter Spaces/LinkedIn Live)**
□ Host Twitter Space or LinkedIn Live (optional but high-engagement)
  - Topic: "Behind the scenes of our Product Hunt launch"
  - Invite: Waitlist, Twitter followers, LinkedIn connections
  - Format: 30-min AMA (ask me anything)
  - Goal: Build deeper relationships with early users

**7:00 PM - Community Engagement (Facebook Groups)**
□ Post in relevant Facebook Groups (SaaS, productivity, startup groups)
□ Follow group rules (some have "promo days")
□ Provide value: "Here's what we learned launching on Product Hunt today"

**8:00 PM - Final Push (Product Hunt)**
□ Product Hunt voting slows after 8 PM PST
□ Make final push: "2 hours left! We're at #5, help us get to #3"
□ Thank everyone who supported
□ Share top comments and testimonials

**9:00 PM - Wrap-Up & Reflection**
□ Send thank-you email to team
□ Share final metrics:
  - Product Hunt rank
  - Total signups
  - Revenue (if applicable)
  - Social media engagement (impressions, clicks, shares)
□ Document what worked and what didn't
□ Plan for tomorrow (Day 1 priorities)

**10:00 PM - Wind Down**
□ Respond to any final messages
□ Set up monitoring for overnight (alerts for critical issues)
□ Celebrate! You just launched 🎉
□ Get sleep (you'll need energy for Day 1)
```

### Product Hunt Strategy (Detailed)

```markdown
**Optimal Launch Timing**:
- **Day**: Tuesday, Wednesday, or Thursday (most traffic)
- **Time**: 12:01 AM PST (start of PH day)
- **Avoid**: Friday (low traffic), Monday (competitive), weekends (dead)

**Product Hunt Submission Checklist**:
□ **Name**: Clear and memorable (e.g., "EmailZero" not "Email Management Tool Pro")
□ **Tagline**: 60 chars, benefit-focused (e.g., "Save 8.5 hours/week on email with AI triage")
□ **Thumbnail**: 240×240px, eye-catching, professional
□ **Gallery**: 4-6 images (screenshots, GIFs showing product in action)
□ **Video**: 60-90 seconds, no audio needed, show core workflow
□ **First Comment**: Founder post explaining why you built this, beta results, special offer
□ **Topics**: Choose 3 relevant topics (e.g., "Productivity", "Artificial Intelligence", "Email")

**First Comment Template**:
```

Hey Product Hunt! 👋

I'm [Your Name], founder of [Product]. I built this because I was wasting 10+ hours/week on email and couldn't find a solution that actually worked.

**The Problem**:
The average professional spends 28% of their workday on email. Existing tools are either too expensive ($30/month for Superhuman) or too basic (simple filters).

**Our Solution**:
AI email triage that learns your priorities and auto-organizes, prioritizes, and drafts responses.

**Beta Results** (100 users, 2 weeks):

- 92% said they "can't go back" to manual email
- Average time saved: 8.5 hours/week
- 78% said it increased their productivity

**Product Hunt Exclusive**:
First 100 signups get lifetime pricing at $19/month (vs. $29 regular).

Try it free for 14 days: [link]

Happy to answer any questions! 🙏

```

**Comment Engagement Strategy**:
- Respond to EVERY comment within 15 minutes (first 2 hours critical)
- Upvote every comment (shows engagement)
- Provide value in responses (not just "thank you")
- Ask follow-up questions (build relationships)
- Tag relevant team members (e.g., "@jane from our team can answer that")
- Pin important questions/answers (highlight key features)

**Upvote Strategy**:
- Ask close network to upvote in first hour (momentum is critical)
- Don't spam - Product Hunt detects and penalizes fake upvotes
- Quality over quantity - engaged users > silent upvotes
- Post in communities after gaining initial traction (200+ upvotes)

**Expected Results**:
- Top 5 Product of the Day: 300-800 upvotes, 10K-30K website visits
- Top 10 Product of the Day: 150-300 upvotes, 5K-15K website visits
- Featured: 50-150 upvotes, 2K-5K website visits
```

---

## Post-Launch Optimization (Days 1-30)

### Week 1 Priorities

**Goal**: Respond to feedback, fix critical issues, maintain momentum

```markdown
**Day 1-3: Firefighting**
□ Monitor product stability (uptime, errors, performance)
□ Respond to every support request within 2 hours
□ Fix critical bugs immediately (payment, signup, core features)
□ Collect feedback from early users (survey, interviews)
□ Post launch recap: "We launched yesterday! Here's what happened"
  - Share metrics: Signups, Product Hunt rank, revenue
  - Lessons learned: What worked, what didn't
  - Thank everyone who supported

**Day 4-7: Iteration**
□ Analyze user behavior (Mixpanel/Amplitude dashboards)
  - Where do users drop off? (onboarding, pricing page, feature adoption)
  - What features are used most? (double down on these)
  - What features are ignored? (consider removing or improving)
□ A/B test key pages (landing page, pricing page)
□ Implement quick wins (based on feedback)
□ Send follow-up email to trial users:
  - "How's it going? Any questions?"
  - Feature highlight: "Did you know you can...?"
  - Ask for feedback: "What would make this a 10/10 for you?"

**Week 1 Metrics to Track**:
- Signups: 100-500 target (launch week)
- Activation rate: 70%+ (users complete onboarding)
- Trial-to-paid conversion: 10-20% target (after 14 days)
- Churn rate: <5% in first month
- NPS score: 40+ (good), 50+ (great), 70+ (amazing)
- Support ticket volume: Expect 3-5x normal (launch spike)
```

### Week 2-4: Optimization & Growth

```markdown
**Feedback Loop System**:

**1. Collect Feedback**:
□ In-app surveys (after key actions: onboarding, feature use)
□ Email surveys (NPS, feature requests, pain points)
□ User interviews (1:1 calls with power users and churned users)
□ Support ticket analysis (common issues, feature requests)
□ Social media monitoring (Twitter, Reddit mentions)

**2. Categorize Feedback**:
□ **Critical bugs** (fix immediately)
□ **Quick wins** (high impact, low effort - do next)
□ **Feature requests** (prioritize by user demand + strategic fit)
□ **Nice-to-haves** (backlog)

**3. Act on Feedback**:
□ Communicate fixes: "You asked, we listened!"
  - Email users who requested feature
  - Post on social media
  - Update changelog
□ Close the loop: Thank users who provided feedback
□ Build in public: Share progress on roadmap

**Pricing Optimization**:

**Experiments to Run**:
1. **Trial length**: 7-day vs. 14-day vs. 30-day
   - Hypothesis: Longer trial = higher conversion (users form habit)
   - Measure: Trial-to-paid conversion rate

2. **Pricing tiers**: Single plan vs. 3 tiers (Basic, Pro, Enterprise)
   - Hypothesis: 3 tiers increase ACV (anchor effect)
   - Measure: Average revenue per user (ARPU)

3. **Discounts**: First month $1 vs. 20% off vs. no discount
   - Hypothesis: Low barrier to entry increases conversions
   - Measure: CAC, LTV, payback period

4. **Annual billing**: Monthly vs. Annual (2 months free)
   - Hypothesis: Annual prepay improves cash flow and retention
   - Measure: % of users choosing annual, churn rate

**Growth Loops to Implement**:

**1. Referral Program**:
- Incentive: "Give $10, get $10" (or 1 month free for both)
- Mechanism: Unique referral link in product
- Trigger: After user completes onboarding (day 7)
- Goal: 15-20% of users refer at least 1 person

**2. Content Flywheel**:
- User generates value in product (e.g., organized inbox)
- Offer to share achievement on social media
- Template: "I saved 8.5 hours this week with [Product]!"
- Goal: 5-10% of users share organically

**3. Network Effects**:
- Invite team members (e.g., "Your team can save 8.5 hrs/week each")
- Team dashboard (see everyone's productivity gains)
- Viral trigger: "Your teammate [Name] saved 12 hours last week!"

**Week 2-4 Metrics**:
- Weekly signups: 50-200 target (post-launch steady state)
- Activation rate: 75%+ (improving with onboarding tweaks)
- Trial-to-paid conversion: 15-25% (improving with optimization)
- MRR growth: 20-30% week-over-week
- Virality coefficient: 0.3-0.5 (each user brings 0.3-0.5 new users)
```

---

## 30-60-90 Day Content Calendar

### Days 1-30: Launch Momentum

**Weekly Themes**:

- **Week 1**: Launch celebration & social proof
- **Week 2**: User success stories & testimonials
- **Week 3**: Deep-dive features & how-tos
- **Week 4**: Lessons learned & transparency

```markdown
**Week 1: Launch Celebration** (7 posts)

**Day 1 (Launch Day)**:
Platform: Twitter, LinkedIn
Content: "🚀 We're live on Product Hunt! [Product] helps professionals save 8.5 hours/week on email. Show us some love! [link]"
Goal: Drive Product Hunt upvotes
CTA: "Check it out and let me know what you think!"

**Day 2**:
Platform: LinkedIn
Content: "Yesterday we launched [Product] on Product Hunt. Here's what happened in the first 24 hours: [metrics]. The biggest lesson? [insight]. Full recap: [link to blog post]"
Goal: Share lessons learned (provides value)
CTA: "What would you do differently?"

**Day 3**:
Platform: Twitter thread
Content: "3 things I learned launching on Product Hunt yesterday: 1) [lesson] 2) [lesson] 3) [lesson]. Thread 👇"
Goal: Educate + build authority
CTA: "Have you launched on PH? What did you learn?"

**Day 4**:
Platform: LinkedIn
Content: "Meet [Beta User Name], one of our beta users. Before [Product]: 10+ hours/week on email. After: 2 hours/week. Here's how: [brief story + testimonial + screenshot]"
Goal: Social proof via case study
CTA: "Want to save time like [Name]? Try free: [link]"

**Day 5**:
Platform: Twitter
Content: "The average professional wastes 28% of their workday on email. That's 11 hours/week. Here's how AI can cut that to 2 hours: [infographic or video]"
Goal: Educational content (problem awareness)
CTA: "Try it yourself: [link]"

**Day 6**:
Platform: Reddit (r/SaaS or r/productivity)
Content: "I launched my SaaS on Product Hunt 5 days ago. Here's the exact strategy I used to hit #3 Product of the Day: [detailed breakdown]"
Goal: Provide immense value to community
CTA: "Happy to answer questions!"

**Day 7**:
Platform: LinkedIn, Twitter
Content: "Week 1 recap: [X] signups, [Y] paying customers, [Z] hours saved for users. Biggest surprise: [insight]. Biggest challenge: [challenge]. What's next: [roadmap hint]"
Goal: Transparency + build in public
CTA: "Join us: [link]"
```

```markdown
**Week 2: User Success Stories** (7 posts)

**Day 8**:
Platform: Twitter
Content: "User spotlight: [Name] is a founder who was spending 15 hrs/week on email. Now? 3 hours. Here's what changed: [video testimonial or quote]"
Goal: Concrete transformation story
CTA: "Want similar results? [link]"

**Day 9**:
Platform: LinkedIn
Content: "What do our happiest users have in common? I analyzed 50 power users. Here's what I found: [3 patterns or insights]"
Goal: Data-driven storytelling
CTA: "Which one resonates with you?"

**Day 10**:
Platform: Twitter thread
Content: "How to save 8.5 hours/week on email (step-by-step): 1) [step] 2) [step] 3) [step] 4) [step] 5) [step]. Thread 👇"
Goal: Educational how-to
CTA: "Or let AI do it for you: [link]"

**Day 11**:
Platform: LinkedIn
Content: "[Product] just helped its 100th customer save 8.5 hours/week. That's 850 hours total. What could you do with 850 extra hours? [aspirational message]"
Goal: Milestone celebration + emotional appeal
CTA: "Be customer #101: [link]"

**Day 12**:
Platform: Twitter
Content: "Real talk: [Product] isn't for everyone. It's NOT a good fit if: [3 anti-patterns]. But if [ideal customer profile], it's a game-changer."
Goal: Honest positioning (builds trust)
CTA: "See if it's right for you: [link]"

**Day 13**:
Platform: Reddit (r/Entrepreneur or r/startups)
Content: "We analyzed 100 professionals' email habits. Here's what we learned about email productivity: [3-5 insights with data]"
Goal: Value-first, data-backed content
CTA: "Full report: [link to blog post]"

**Day 14**:
Platform: LinkedIn, Twitter
Content: "2-week update: [X] paying customers, [Y] total hours saved, [Z] revenue. Here's what we're working on next: [feature sneak peek]"
Goal: Momentum + roadmap transparency
CTA: "Feature requests? Reply below!"
```

```markdown
**Week 3: Deep-Dive Features** (7 posts)

**Day 15**:
Platform: Twitter with GIF/video
Content: "Did you know [Product] can [feature]? Here's how it works: [10-second demo GIF]"
Goal: Feature awareness
CTA: "Try it: [link]"

**Day 16**:
Platform: LinkedIn with video
Content: "Tutorial: How to [achieve specific outcome] with [Product] in 60 seconds [Loom video walkthrough]"
Goal: Onboarding education
CTA: "Questions? Drop them below"

**Day 17**:
Platform: Twitter thread
Content: "5 hidden [Product] features you're probably not using: 1) [feature + benefit] 2) [feature + benefit] ... Thread 👇"
Goal: Increase feature adoption
CTA: "Which one will you try first?"

**Day 18**:
Platform: LinkedIn
Content: "Power user tip: Combine [Feature A] with [Feature B] to [achieve outcome]. Here's how: [step-by-step]"
Goal: Advanced use cases
CTA: "Share your power user tips below!"

**Day 19**:
Platform: Twitter
Content: "Most common question: 'Is my email data secure?' YES. Here's how we protect your data: [3 security measures]"
Goal: Address objections
CTA: "Other questions? Ask away!"

**Day 20**:
Platform: Reddit (r/productivity)
Content: "I analyzed 10K emails to understand productivity patterns. Here's what I found: [insights + data visualization]"
Goal: Thought leadership
CTA: "Full research: [link to blog]"

**Day 21**:
Platform: LinkedIn, Twitter
Content: "3-week update: $[X]k MRR, [Y] customers, [Z]% week-over-week growth. Lesson learned: [key insight]"
Goal: Transparency + milestone
CTA: "AMA in the comments!"
```

```markdown
**Week 4: Lessons & Transparency** (7 posts)

**Day 22**:
Platform: Twitter
Content: "Biggest mistake we made post-launch: [mistake]. Cost us [impact]. Here's how we fixed it: [solution]"
Goal: Vulnerability builds trust
CTA: "Learn from our mistakes!"

**Day 23**:
Platform: LinkedIn long-form post
Content: "The complete launch playbook: everything I learned launching [Product]. [detailed breakdown with metrics, lessons, templates]"
Goal: Massive value dump
CTA: "Bookmark this for your launch!"

**Day 24**:
Platform: Twitter
Content: "What I'd do differently if I launched today: 1) [change] 2) [change] 3) [change]. Save this if you're launching soon."
Goal: Actionable advice
CTA: "Launching soon? DM me, happy to help"

**Day 25**:
Platform: LinkedIn
Content: "Behind the scenes: Our product roadmap for the next 90 days [visual roadmap]. What should we prioritize?"
Goal: Community involvement
CTA: "Vote in the comments!"

**Day 26**:
Platform: Twitter
Content: "Real customer feedback we got this week: '[positive testimonial]' and '[constructive criticism]'. Both are gold."
Goal: Show you listen
CTA: "Keep the feedback coming!"

**Day 27**:
Platform: Reddit (Indie Hackers)
Content: "30-day post-launch update: $[X]k MRR, [Y] customers, [Z]% growth. Here's the full breakdown: [detailed metrics + what worked + what didn't]"
Goal: Radical transparency
CTA: "Questions? AMA!"

**Day 28-30**:
Platform: LinkedIn, Twitter
Content: "We just hit [milestone]! 🎉 Thank you to our [X] customers. You're the reason we do this. Here's what's next: [teaser for next month]"
Goal: Celebration + gratitude
CTA: "Join us: [link]"
```

---

### Days 31-60: Sustained Growth

**Content Pillars** (Post 3x per week on each platform):

```markdown
**Pillar 1: Product Updates** (1x per week)
- New features released
- Bug fixes and improvements
- Roadmap sneak peeks
- Beta programs for upcoming features

Example posts:
- "New feature alert: [Feature] is live! Here's what it does: [demo]"
- "You asked, we built it: [Feature request] is now available"
- "Sneak peek: We're working on [feature]. Thoughts?"

**Pillar 2: User Success Stories** (1x per week)
- Case studies with metrics
- Video testimonials
- Before/after comparisons
- Power user spotlights

Example posts:
- "[Name] saved 12 hours this week with [Product]. Here's how: [story]"
- "Video: Watch [Name] walk through how they use [Product] daily"
- "Before [Product]: [pain]. After [Product]: [transformation]"

**Pillar 3: Educational Content** (1x per week)
- How-to tutorials
- Industry insights
- Productivity tips
- Email best practices

Example posts:
- "How to achieve inbox zero in 7 days (step-by-step guide)"
- "5 email productivity myths debunked by data"
- "The psychology of email overwhelm (and how to fix it)"

**Platform-Specific Strategy**:

**LinkedIn** (Professional, longer-form):
- Post 2-3x per week
- Best times: Tue-Thu, 8-10 AM or 12-1 PM EST
- Format: Long-form text (1,000+ chars), images, carousels
- Topics: Founder lessons, company building, thought leadership
- Engagement: Respond to all comments within 24 hours

**Twitter** (Real-time, conversational):
- Post 1-2x per day
- Best times: 9 AM-3 PM EST
- Format: Short text (100-200 chars), threads, GIFs, polls
- Topics: Product updates, quick tips, community engagement
- Engagement: Respond within 1-2 hours, retweet mentions

**Reddit** (Value-first, no self-promotion):
- Post 1-2x per week
- Subreddits: r/SaaS, r/productivity, r/startups, r/Entrepreneur
- Format: Long-form, data-backed, genuinely helpful
- Topics: Launch lessons, data analysis, transparent metrics
- Engagement: Respond to every comment, provide additional value
```

---

### Days 61-90: Scale & Optimize

**Strategic Announcements**:

```markdown
**Milestone Posts** (Celebrate achievements):
- $10K MRR milestone
- 500 customers milestone
- 1M emails processed milestone
- Partnership announcements
- Funding announcements (if applicable)
- Team expansion announcements

**Example Milestone Post**:
"🎉 We just hit $10K MRR!

60 days ago we launched [Product].
Today: 347 paying customers, $10.2K MRR.

What got us here:
- Product Hunt launch: #3 Product of the Day
- 92% of trial users convert to paid
- Referrals: 28% of new signups

What we learned:
[3 key lessons]

Thank you to our customers. You're incredible.

What's next: [roadmap hint]"

**Feature Announcements**:
- Launch week: Build hype with 5-day feature release countdown
- Behind-the-scenes: Show the making of a feature
- User-requested: "You asked for it, here it is!"
- Beta access: Exclusive early access for power users

**Partnership Announcements**:
- Integration launches (e.g., "We now integrate with Slack!")
- Co-marketing with complementary tools
- Affiliate partnerships
- Influencer collaborations
```

**Content Repurposing**:

```markdown
**Turn 1 piece of content into 10**:

1 Blog Post (1,500 words) →
1. Twitter thread (10 tweets)
2. LinkedIn post (long-form)
3. LinkedIn carousel (10 slides)
4. Instagram carousel (10 slides)
5. YouTube video (5-10 min)
6. TikTok video (30-60 sec clips)
7. Reddit post (adapt for each subreddit)
8. Email newsletter (weekly digest)
9. Podcast episode (if you have one)
10. Infographic (visual summary)

**Example**:
Blog post: "How We Hit $10K MRR in 60 Days"
→ Twitter thread: "10 lessons from $0 to $10K MRR"
→ LinkedIn post: "The complete playbook for $10K MRR"
→ Carousel: "10 slides: $0 → $10K MRR"
→ Video: "Behind the scenes of our first $10K month"
```

---

## Channel Strategy Matrix

### Which Channels to Use When

```markdown
| Channel | Best For | Budget Required | Time to Results | Skill Level |
|---------|----------|-----------------|-----------------|-------------|
| **Product Hunt** | Launch day awareness | $0-500 | 1 day | Medium |
| **SEO/Content** | Long-term organic traffic | $1K-5K | 6-12 months | High |
| **Twitter** | Community building, thought leadership | $0-2K | 2-4 weeks | Medium |
| **LinkedIn Ads** | B2B lead generation | $3K-10K | 1-2 weeks | Medium |
| **Google Ads** | High-intent search traffic | $3K-10K | 1-2 weeks | High |
| **Facebook/Instagram Ads** | B2C brand awareness | $2K-8K | 1-2 weeks | Medium |
| **Referral Program** | Viral growth | $1K-3K (dev cost) | 2-4 weeks | Low |
| **Influencer Marketing** | Instant credibility | $5K-20K | 1-2 weeks | Medium |
| **PR/Media** | Brand credibility | $0-10K | 2-8 weeks | High |
| **Cold Email** | B2B outbound sales | $0-2K | 1-2 weeks | Medium |
| **Partnerships** | Co-marketing opportunities | $0-5K | 4-8 weeks | High |
```

### Budget Allocation by Stage

```markdown
**Pre-Launch (Budget: $2K-5K)**:
- Community building: $0 (organic)
- Landing page/website: $500-1K (Webflow, Framer)
- Email tools: $200-500 (ConvertKit, Mailchimp)
- Design tools: $300-500 (Figma, Canva)
- Analytics: $200-500 (Mixpanel, PostHog)

**Launch (Budget: $5K-10K)**:
- Product Hunt promotion: $0-500 (optional: upvote service)
- Influencer collaborations: $3K-5K (5-10 micro-influencers)
- Paid ads: $1K-3K (initial testing)
- PR tools: $200-500 (press release distribution)
- Video production: $500-1K (product demo, testimonials)

**Growth (Budget: $10K-30K/month)**:
- Paid ads: $5K-15K (scale what works)
- Content/SEO: $2K-5K (writer, SEO tools)
- Influencer/affiliates: $2K-5K (ongoing)
- Tools/software: $1K-2K (analytics, automation)
- Contingency: $1K-3K (experiments)
```

---

## Metrics & KPIs

### Launch Metrics (Day 0-30)

```markdown
**Traffic Metrics**:
- Website visitors: 10K-50K target (launch month)
- Traffic sources: Product Hunt 30-40%, Social 20-30%, Direct 20-30%, Referral 10-20%
- Bounce rate: <60% (good), <50% (great)
- Time on site: 2-3 minutes average

**Conversion Metrics**:
- Signup rate: 5-15% (visitors → trial signups)
- Activation rate: 60-80% (signups → activated users)
- Trial-to-paid: 10-25% (activated users → paying customers)
- Overall conversion: 0.5-3% (visitors → paying customers)

**Product Metrics**:
- Daily active users (DAU): 40-60% of signups
- Weekly active users (WAU): 60-80% of signups
- Monthly active users (MAU): 70-90% of signups
- Feature adoption: 50%+ users use core feature
- Time to value: <24 hours (user gets first "aha" moment)

**Revenue Metrics**:
- MRR (Monthly Recurring Revenue): $1K-10K target (first month)
- ARPU (Average Revenue Per User): $29-99/month
- CAC (Customer Acquisition Cost): $50-200 target
- LTV (Lifetime Value): $348-1,188 (1-year retention)
- LTV:CAC ratio: 3:1 target (2:1 acceptable early stage)

**Engagement Metrics**:
- NPS (Net Promoter Score): 40+ (good), 50+ (great), 70+ (amazing)
- CSAT (Customer Satisfaction): 80%+ satisfied
- Support tickets: 10-20% of users contact support (first month)
- Response time: <2 hours (business hours)
```

### Growth Metrics (Day 31-90)

```markdown
**Growth Rate**:
- Week-over-week signups: 10-30% growth
- Week-over-week revenue: 15-40% growth
- Month-over-month: 50-100% growth (early stage)

**Retention Metrics**:
- Day 1 retention: 80%+ (user returns next day)
- Day 7 retention: 60%+ (user active after 1 week)
- Day 30 retention: 40%+ (user active after 1 month)
- Churn rate: <5% monthly churn (early stage)

**Viral Metrics**:
- Viral coefficient (K): 0.3-0.7 target (each user brings 0.3-0.7 new users)
- Referral rate: 15-25% of users refer someone
- Share rate: 5-10% of users share on social media

**Channel Metrics**:
- CAC by channel (know your best channels)
- ROAS (Return on Ad Spend): 3:1 target (paid ads)
- Organic traffic growth: 20-40% month-over-month
- Email open rate: 30-40%
- Email click rate: 3-5%
```

---

## Common Pitfalls to Avoid

```markdown
**Pre-Launch Mistakes**:
❌ Building for too long (6+ months) without customer feedback
✅ Launch MVP in 1-3 months, iterate based on real users

❌ Waiting for "perfect" product before launch
✅ Launch at 80% done, fix 20% based on feedback

❌ Not building waitlist (launching to crickets)
✅ Build 500-1,000 person waitlist before launch

❌ Launching without beta users
✅ Get 50-100 beta users, gather testimonials

**Launch Day Mistakes**:
❌ Launching on Friday or weekend (low traffic)
✅ Launch Tuesday-Thursday for maximum attention

❌ Not responding to comments/feedback
✅ Respond to EVERY comment within 30 minutes

❌ Being defensive about criticism
✅ Thank critics, show you're listening, explain roadmap

❌ Not tracking metrics
✅ Real-time dashboard, monitor signups/conversions

**Post-Launch Mistakes**:
❌ Disappearing after launch day
✅ Maintain momentum with daily posts

❌ Ignoring churned users
✅ Interview churned users, fix their pain points

❌ Building features nobody asked for
✅ Build what users request most

❌ Not testing pricing
✅ A/B test pricing, trial length, discounts

**Growth Mistakes**:
❌ Trying every channel at once
✅ Focus on 1-2 channels, master them, then expand

❌ Scaling paid ads too fast (before unit economics work)
✅ Prove LTV:CAC >3:1, then scale

❌ Neglecting existing customers (chasing new)
✅ Retention > acquisition (keep customers happy)

❌ Not building in public
✅ Share metrics, lessons, transparency builds trust
```

---

## Execution

When you run this command, Claude will:

1. **Ask Strategic Questions** (2-3 min)
   - Product details, target audience, budget, timeline
   - Validate assumptions, identify risks
   - Clarify channel strategy and priorities

2. **Generate Complete GTM Plan** (4-6 min)
   - All 5 folders with detailed files
   - Customized for your product, audience, budget
   - Includes templates, timelines, metrics

3. **Output Files** (structured markdown)
   - Save to `/gtm-plans/[product-name]/`
   - Ready to use immediately
   - Customizable for your specific needs

### Example Usage

```bash
$ /startup:gtm --idea "AI email productivity tool for SaaS founders" --budget 10000 --timeline 60

Claude: I'll help you create a comprehensive GTM plan for your AI email tool. Let me ask a few strategic questions...

1. What's your pricing model?
   a) Free trial → Paid ($29/month after 14 days)
   b) Freemium (free tier + paid upgrades)
   c) One-time purchase
   d) Usage-based pricing

2. What's your unfair advantage over competitors like Superhuman and SaneBox?

3. Do you have beta users? If yes, how many and what results have they seen?

4. What channels does your audience use most? (LinkedIn, Twitter, Product Hunt, etc.)

5. What's your expected customer lifetime value (LTV)?

[After you answer, Claude generates the complete GTM plan...]

✅ GTM plan generated: /gtm-plans/ai-email-tool/
✅ 19 files created
✅ Ready to execute

Your launch is planned for [Date]. Here's your week-by-week breakdown...
```

---

## Next Steps

After generating your GTM plan:

1. **Review & Customize** (15-20 min)
   - Read through each file
   - Adjust for your specific context
   - Add company-specific details

2. **Share with Team** (30 min)
   - Walk through launch plan
   - Assign responsibilities
   - Get buy-in and feedback

3. **Execute Pre-Launch** (Weeks -4 to -1)
   - Follow beta program plan
   - Build waitlist (500-1,000 signups)
   - Prep launch day assets

4. **Launch!** (Day 0)
   - Follow hour-by-hour timeline
   - Engage with every comment
   - Track metrics in real-time

5. **Iterate Post-Launch** (Days 1-30)
   - Collect feedback
   - Fix critical issues
   - Optimize based on data

6. **Scale** (Days 31-90)
   - Double down on what works
   - Cut what doesn't
   - Build momentum

**Remember**: Perfect is the enemy of good. Launch at 80%, iterate to 100% with real user feedback.

---

## Implementation Instructions

When this command is executed, perform the following steps:

**IMPORTANT**: Output progress messages to the user at the start and end of each step using the format:

- ⏳ = Step starting
- ✅ = Step complete (with summary)
- 📝 = Files being generated (with count)

---

### Step 1: Collect Product Information (2-3 min)

**Output to user**: `⏳ Step 1/11: Gathering product and market information...`

Use AskUserQuestion tool to gather strategic information:

**Question 1: Pricing Model**

- Header: "Pricing"
- Question: "What's your pricing model for [product-name]?"
- Options:
  - Free trial → Paid subscription
  - Freemium (free tier + paid upgrades)
  - One-time purchase
  - Usage-based pricing
- MultiSelect: false

**Question 2: Unfair Advantage**

- Header: "Advantage"
- Question: "What's your unfair advantage vs. competitors?"
- Options:
  - Proprietary technology
  - Exclusive partnerships
  - Network effects
  - First-mover advantage
  - (Other - user can specify)
- MultiSelect: false

**Question 3: Beta Users Status**

- Header: "Beta"
- Question: "Do you have beta users? If yes, how many and what results have they seen?"
- Options:
  - Yes, 10-50 beta users with positive results
  - Yes, 50+ beta users with positive results
  - No, launching without beta
  - Planning to start beta program
- MultiSelect: false

**Question 4: Primary Channels**

- Header: "Channels"
- Question: "Where does your target audience spend time? (Select all that apply)"
- Options:
  - LinkedIn (professionals, B2B)
  - Twitter/X (tech-savvy, early adopters)
  - Product Hunt (product launches)
  - Reddit (niche communities)
  - Indie Hackers (indie founders)
  - HackerNews (developers, founders)
  - Facebook Groups (communities)
  - Instagram (visual products, B2C)
- MultiSelect: true

**Question 5: Expected LTV**

- Header: "LTV"
- Question: "What's your expected customer lifetime value (LTV)?"
- Options:
  - $0-100 (low-ticket)
  - $100-500 (mid-ticket)
  - $500-2,000 (high-ticket)
  - $2,000+ (enterprise)
  - (Other - user can specify)
- MultiSelect: false

**Output to user**: `✅ Step 1/11: Product information collected`

---

### Step 2: Calculate Key Metrics

**Output to user**: `⏳ Step 2/11: Calculating key metrics and targets...`

Based on inputs from Step 1 and command parameters:

```javascript
const metrics = {
  budget: params.budget, // from --budget parameter
  timeline: params.timeline, // from --timeline parameter (days)

  // Calculate daily budget
  dailyBudget: params.budget / params.timeline,

  // Estimate target CAC (Customer Acquisition Cost)
  // Rule: CAC should be < 1/3 of LTV for healthy unit economics
  targetCAC: expectedLTV / 3,

  // Estimate number of conversions needed
  targetConversions: params.budget / targetCAC,

  // Calculate LTV:CAC ratio (should be > 3:1)
  ltvCacRatio: expectedLTV / targetCAC,

  // Pre-launch timeline
  preLaunchWeeks: Math.floor(params.timeline / 30) * 4, // 4 weeks before launch

  // Launch date
  launchDate: calculateDate(params.timeline)
};
```

**Output to user**: `✅ Step 2/11: Metrics calculated (Target CAC: $[X], Expected conversions: [X])`

---

### Step 3: Generate Directory Structure (1 min)

**Output to user**: `⏳ Step 3/11: Creating GTM plan directory structure...`

Create GTM plan directory:

```bash
mkdir -p /home/webemo-aaron/projects/prompt-blueprint/gtm-plans/[product-name-slug]/
mkdir -p /home/webemo-aaron/projects/prompt-blueprint/gtm-plans/[product-name-slug]/1-pre-launch/
mkdir -p /home/webemo-aaron/projects/prompt-blueprint/gtm-plans/[product-name-slug]/2-launch-day/
mkdir -p /home/webemo-aaron/projects/prompt-blueprint/gtm-plans/[product-name-slug]/3-post-launch/
mkdir -p /home/webemo-aaron/projects/prompt-blueprint/gtm-plans/[product-name-slug]/4-content-calendar/
mkdir -p /home/webemo-aaron/projects/prompt-blueprint/gtm-plans/[product-name-slug]/5-metrics-dashboard/
```

**Output to user**: `✅ Step 3/11: Directory structure created`

---

### Step 4: Generate Pre-Launch Files (4 files)

**Output to user**: `⏳ Step 4/11: Generating pre-launch files...`
**Output to user**: `📝 Creating 4 pre-launch strategy documents`

Using content from lines 170-510 of this command file, generate customized pre-launch files:

**File 1: `1-pre-launch/beta-program-plan.md`**

Content should include:

- Beta recruitment strategy (from lines 172-228)
- Customized for product type and target audience
- Beta application form template with product-specific questions
- Beta program structure (2-week onboarding schedule)
- Beta incentives (e.g., "Lifetime 50% off for first 20 beta users")
- Beta success metrics (70%+ activation rate, NPS > 50)
- Budget allocation: $[calculated from total budget × 0.10]

**File 2: `1-pre-launch/waitlist-strategy.md`**

Content should include:

- Landing page strategy (from lines 232-348)
- 6 landing page sections with [product-name] examples
- Waitlist growth tactics:
  - Week -3: 0-200 signups (organic: LinkedIn, Twitter, communities)
  - Week -2: 200-500 signups (community: Reddit, Indie Hackers, Discord)
  - Week -1: 500-1,000 signups (influencer: micro-influencers in niche)
- Waitlist nurture sequence (6 emails customized for product)
- Budget allocation: $[calculated from total budget × 0.15]

**File 3: `1-pre-launch/press-outreach.md`**

Content should include:

- Press outreach strategy (from lines 352-469)
- Tier 1 publications (TechCrunch, The Verge, etc.) for product category
- Tier 2 publications (industry-specific blogs)
- Tier 3 publications (niche newsletters)
- Journalist research methodology
- Pitch email template customized with [product-name] and value prop
- Follow-up schedule (Days 3, 7, 10, 14)
- Press kit checklist (7 assets)
- Influencer collaboration strategy
  - Micro-influencers: $500-2K (10K-50K followers)
  - Mid-tier: $2K-10K (50K-200K followers)
- Budget allocation: $[calculated from total budget × 0.20]

**File 4: `1-pre-launch/community-building.md`**

Content should include:

- Community engagement strategy
- Platform selection from Step 1, Question 4 (user-selected channels)
- Posting templates for each selected platform
- Engagement tactics (comment on relevant threads, answer questions)
- Community building timeline (4 weeks before launch)
- Budget allocation: $[calculated from total budget × 0.05] (mostly time)

**Output to user**: `✅ Step 4/11: Pre-launch files complete (4 files created)`

---

### Step 5: Generate Launch Day Files (4 files)

**Output to user**: `⏳ Step 5/11: Generating launch day files...`
**Output to user**: `📝 Creating 4 launch day planning documents`

Using content from lines 514-703, generate launch day playbook:

**File 1: `2-launch-day/hour-by-hour-timeline.md`**

Content should include:

- Hour-by-hour schedule (from lines 517-641)
- Customized for [product-name] and selected channels
- Timeline from 6:00 AM to 10:00 PM
- Each hour with specific tasks:
  - 6:00 AM: Pre-launch final check
  - 7:00 AM: Product Hunt launch
  - 8:00 AM: Email waitlist (personalized with product benefits)
  - 9:00 AM: Twitter blitz (thread about why you built this)
  - 10:00 AM: LinkedIn posts
  - 11:00 AM: Reddit engagement (relevant subreddits from Step 1)
  - 12:00 PM: Indie Hackers post
  - 1:00-8:00 PM: Continuous engagement
  - 9:00 PM: Wrap-up & reflection
  - 10:00 PM: Wind down & celebrate

**File 2: `2-launch-day/product-hunt-playbook.md`**

Content should include:

- Product Hunt strategy (from lines 643-703)
- Optimal launch timing (Tuesday-Thursday, 12:01 AM PST)
- Product Hunt submission checklist customized for [product-name]:
  - Tagline (< 60 chars)
  - Thumbnail (240×240px)
  - Gallery images (4-6 images)
  - First comment template
  - Maker intro
- Comment engagement strategy
- Upvote strategy (friends, family, network)
- Expected results by ranking:
  - #1-5: 400-800 upvotes, 50K+ page views
  - #6-10: 200-400 upvotes, 20K+ page views
  - #11-20: 100-200 upvotes, 10K+ page views

**File 3: `2-launch-day/social-media-posts.md`**

Content should include:

- Pre-written posts for each platform (from selected channels in Step 1)
- Platform-specific formatting
- For each platform:
  - Morning announcement post
  - Mid-day update post
  - Evening thank you post
- Hashtag strategy
- Mention strategy (tag relevant accounts)

**File 4: `2-launch-day/community-engagement.md`**

Content should include:

- Where to post (Reddit, Indie Hackers, HackerNews, Discord, Slack)
- What to say (authentic, story-driven, not salesy)
- Response templates for common questions/feedback
- Engagement metrics to track

**Output to user**: `✅ Step 5/11: Launch day files complete (4 files created)`

---

### Step 6: Generate Post-Launch Files (4 files)

**Output to user**: `⏳ Step 6/11: Generating post-launch files...`
**Output to user**: `📝 Creating 4 post-launch optimization documents`

Using content from lines 707-815, generate post-launch optimization files:

**File 1: `3-post-launch/week-1-priorities.md`**

Content should include:

- Week 1 priorities (from lines 709-743)
- Day 1-3: Firefighting phase
  - Ensure product stability
  - Respond to all support requests < 2 hours
  - Fix critical bugs immediately
  - Monitor analytics hourly
- Day 4-7: Iteration phase
  - Analyze user behavior (what features are used most?)
  - Run A/B tests (pricing page, signup flow, onboarding)
  - Implement quick wins (UI improvements, copy tweaks)
  - Start feedback calls with early users
- Week 1 metrics to track:
  - Total signups
  - Activation rate (% who complete onboarding)
  - Conversion rate (trial → paid)
  - Churn rate (% who cancel)
  - NPS score

**File 2: `3-post-launch/feedback-loops.md`**

Content should include:

- Feedback loop system (collect → categorize → act)
- Collection methods:
  - In-app surveys (NPS, feature requests)
  - User interviews (5-10 per week)
  - Support ticket analysis
  - Social media monitoring
  - Product analytics (Mixpanel, Amplitude)
- Categorization framework:
  - Critical bugs (fix in 24 hours)
  - High-impact features (prioritize in roadmap)
  - Nice-to-haves (backlog)
  - Edge cases (defer)
- Action plan:
  - Weekly review of all feedback
  - Assign priority scores
  - Add to sprint planning
  - Close the loop (respond to users)

**File 3: `3-post-launch/pricing-experiments.md`**

Content should include:

- Pricing optimization framework (from lines 745-815)
- 4 experiments to run:
  - a. Trial length (7-day vs. 14-day vs. 30-day)
  - b. Pricing tiers (single tier vs. 3 tiers vs. usage-based)
  - c. Discounts (first month $1 vs. 20% off vs. no discount)
  - d. Annual billing (offer 2 months free for annual vs. monthly only)
- Experiment structure for each:
  - Hypothesis
  - Test design (A/B split)
  - Success metrics
  - Duration (minimum 2 weeks)
  - Decision criteria (when to declare winner)
- Customized for pricing model from Step 1, Question 1

**File 4: `3-post-launch/growth-loops.md`**

Content should include:

- 3 growth loops to implement:
  - a. Referral program
    - Give $10, get $10 structure
    - Or: Give 1 month free for each referral
    - Track referral conversions
  - b. Content flywheel
    - Users share achievements (e.g., "I just saved 5 hours with [product]")
    - Auto-generate shareable images
    - Track viral coefficient
  - c. Network effects
    - Team invites (invite teammates to collaborate)
    - Multiplayer features
    - Public profiles/templates
- For each loop:
  - Implementation steps
  - Expected viral coefficient (1.1-1.5x)
  - Measurement plan

**Output to user**: `✅ Step 6/11: Post-launch files complete (4 files created)`

---

### Step 7: Generate Content Calendar Files (4 files)

**Output to user**: `⏳ Step 7/11: Generating content calendar files...`
**Output to user**: `📝 Creating 4 content planning documents`

Using content from lines 819-1144, generate content calendar:

**File 1: `4-content-calendar/days-1-30.md`**

Content should include:

- Days 1-30 content calendar (from lines 821-1011)
- Week 1: Launch celebration & social proof (7 posts)
  - Each post pre-written with [product-name] customization
  - Platform-specific formatting
  - Best posting times
- Week 2: User success stories & testimonials (7 posts)
- Week 3: Deep-dive features & how-tos (7 posts)
- Week 4: Lessons learned & transparency (7 posts)
- Total: 28 posts with templates

**File 2: `4-content-calendar/days-31-60.md`**

Content should include:

- Days 31-60 content strategy (from lines 1015-1075)
- 3 content pillars (post 1x/week per pillar):
  - Pillar 1: Product updates & new features
  - Pillar 2: User success stories & case studies
  - Pillar 3: Educational content & thought leadership
- Platform-specific strategies:
  - LinkedIn: Professional insights, company updates
  - Twitter: Quick tips, threads, engagement
  - Reddit: Deep dives, AMAs, community building
- Posting frequency: 3x/week (down from daily in Days 1-30)

**File 3: `4-content-calendar/days-61-90.md`**

Content should include:

- Days 61-90 content strategy (from lines 1079-1144)
- Strategic announcements:
  - Milestone posts (e.g., "We hit 1,000 users!")
  - Feature launches
  - Partnership announcements
  - Community highlights
- Example milestone post template (customized for [product-name])
- Content repurposing strategy:
  - 1 blog post → 10 pieces of content
  - Tweet thread → LinkedIn article → Blog post → Email newsletter
- Posting frequency: 2x/week (sustainable long-term)

**File 4: `4-content-calendar/evergreen-content.md`**

Content should include:

- Evergreen content library
- Reusable post templates for:
  - Feature highlights
  - Customer testimonials
  - How-to guides
  - FAQ answers
  - Industry insights
- Refresh schedule (update quarterly)

**Output to user**: `✅ Step 7/11: Content calendar files complete (4 files created)`

---

### Step 8: Generate Metrics Dashboard Files (3 files)

**Output to user**: `⏳ Step 8/11: Generating metrics dashboard files...`
**Output to user**: `📝 Creating 3 metrics tracking documents`

Using content from lines 1195-1258, generate metrics tracking:

**File 1: `5-metrics-dashboard/kpi-tracking.md`**

Content should include:

- Launch metrics (Day 0-30) from lines 1195-1258
- Traffic metrics:
  - Unique visitors: [target based on budget]
  - Traffic sources: Organic, paid, referral, social
  - Bounce rate: <50% target
- Conversion metrics:
  - Signup rate: 2-5% target
  - Activation rate: 50-70% target (complete onboarding)
  - Trial-to-paid: 10-20% target
- Product metrics:
  - DAU (Daily Active Users)
  - WAU (Weekly Active Users)
  - MAU (Monthly Active Users)
  - Feature adoption rates
- Revenue metrics:
  - MRR (Monthly Recurring Revenue)
  - ARPU (Average Revenue Per User)
  - CAC (Customer Acquisition Cost): $[calculated target]
  - LTV (Lifetime Value): $[from Step 1, Question 5]
  - LTV:CAC ratio: >3:1 target
- Engagement metrics:
  - NPS (Net Promoter Score): >50 target
  - CSAT (Customer Satisfaction): >80% target
  - Support tickets per user: <0.5 target

**File 2: `5-metrics-dashboard/channel-attribution.md`**

Content should include:

- Growth metrics (Day 31-90)
- Channel performance tracking:
  - CAC by channel (Product Hunt, LinkedIn, Twitter, etc.)
  - ROAS by channel (Return on Ad Spend)
  - Organic growth rate
  - Referral conversion rate
- Channel prioritization:
  - Double down on channels with CAC < target
  - Optimize channels with CAC near target
  - Pause channels with CAC > 2x target

**File 3: `5-metrics-dashboard/weekly-reports.md`**

Content should include:

- Weekly report template for stakeholders
- Key metrics summary (traffic, conversions, revenue)
- Wins of the week
- Challenges/blockers
- Next week priorities
- Example report filled out with [product-name] data

**Output to user**: `✅ Step 8/11: Metrics dashboard files complete (3 files created)`

---

### Step 9: Generate Main README

**Output to user**: `⏳ Step 9/11: Creating main README...`

Create `/gtm-plans/[product-name]/README.md`:

```markdown
# GTM Launch Plan: [Product Name]
**Created**: [Current Date]
**Launch Date**: [Calculated from timeline parameter]
**Budget**: $[budget]
**Timeline**: [timeline] days

## Executive Summary

**Product**: [Product name and brief description from user input]
**Target Audience**: [From Step 1, Question 2 if provided, or inferred]
**Pricing**: [From Step 1, Question 1]
**Unfair Advantage**: [From Step 1, Question 2]

**Launch Strategy**: 4-week pre-launch → Launch day → 30-day optimization → 60-day growth

**Expected Results**:
- Waitlist: 500-1,000 signups (pre-launch)
- Launch day: 100-300 signups
- Month 1: [calculated target conversions]
- Month 3: [calculated target conversions × 3]

**Budget Allocation**:
- Pre-launch: $[budget × 0.30] (30%)
  - Beta program: $[budget × 0.10]
  - Waitlist building: $[budget × 0.15]
  - Press/influencer: $[budget × 0.20]
  - Community: $[budget × 0.05]
- Launch day: $[budget × 0.20] (20%)
- Post-launch: $[budget × 0.50] (50%)

## Timeline Overview

### Pre-Launch (Weeks -4 to -1)
- **Week -4**: Beta program setup and recruitment
- **Week -3**: Waitlist building (0-200 signups)
- **Week -2**: Press outreach + waitlist growth (200-500 signups)
- **Week -1**: Influencer outreach + final prep (500-1,000 signups)

### Launch Day (Day 0)
- **Hour-by-hour**: 6 AM - 10 PM playbook
- **Product Hunt**: Launch at 12:01 AM PST
- **Multi-platform**: LinkedIn, Twitter, Reddit, Indie Hackers, etc.

### Post-Launch Optimization (Days 1-30)
- **Week 1**: Firefighting + quick iterations
- **Weeks 2-4**: Pricing experiments + growth loops

### Sustained Growth (Days 31-90)
- **Content marketing**: 3 pillars, 3x/week posts
- **Channel optimization**: Double down on winners
- **Feature releases**: Ship 1-2 new features per month

## Files Overview

| Directory | Purpose | Files |
|-----------|---------|-------|
| `1-pre-launch/` | Pre-launch strategy | 4 files |
| `2-launch-day/` | Launch day playbook | 4 files |
| `3-post-launch/` | Post-launch optimization | 4 files |
| `4-content-calendar/` | Content calendar (90 days) | 4 files |
| `5-metrics-dashboard/` | Metrics tracking | 3 files |

**Total**: 19 files + this README

## Quick Start

1. **This Week**: Review all files, customize for your context
2. **Week -4**: Begin beta program (if not already done)
3. **Week -3**: Launch waitlist landing page
4. **Week -2**: Start press outreach
5. **Week -1**: Final preparations
6. **Day 0**: LAUNCH! Follow hour-by-hour playbook
7. **Week 1**: Monitor metrics, respond to feedback
8. **Weeks 2-4**: Optimize and iterate
9. **Months 2-3**: Scale what works, cut what doesn't

## Success Criteria

**Pre-Launch Success**:
- ✅ 500-1,000 waitlist signups
- ✅ 10-20 beta users with positive feedback (NPS > 50)
- ✅ 3-5 press mentions (Tier 2-3 publications)
- ✅ Active community presence (Reddit, Indie Hackers)

**Launch Day Success**:
- ✅ Product Hunt: Top 5 ranking
- ✅ 100-300 signups on Day 0
- ✅ <5% bounce rate on landing page
- ✅ 10+ testimonials/reviews

**30-Day Success**:
- ✅ [target conversions] total conversions
- ✅ CAC < $[calculated target CAC]
- ✅ Activation rate > 50%
- ✅ Trial-to-paid > 10%
- ✅ NPS > 50

**90-Day Success**:
- ✅ [target conversions × 3] total conversions
- ✅ MRR: $[calculated MRR target]
- ✅ LTV:CAC ratio > 3:1
- ✅ Organic growth > 20% of signups
- ✅ Churn rate < 5%

## Next Steps

**Today**:
1. ✅ GTM plan generated
2. [ ] Review all 19 files
3. [ ] Customize for your product/audience
4. [ ] Share with team for feedback

**This Week**:
1. [ ] Set launch date
2. [ ] Assign responsibilities
3. [ ] Begin pre-launch activities
4. [ ] Set up tracking/analytics

**Next Month**:
1. [ ] Execute pre-launch plan
2. [ ] Build waitlist
3. [ ] Engage press/influencers
4. [ ] Prepare launch day assets

═══════════════════════════════════════════════
           GTM PLAN READY TO EXECUTE 🚀
═══════════════════════════════════════════════

**Your Launch Date**: [Calculated date]

**Remember**: Launch at 80%, iterate to 100% with real user feedback.
```

**Output to user**: `✅ Step 9/11: Main README created`

---

### Step 10: Output Verification

**Output to user**: `⏳ Step 10/11: Verifying all files...`

Verify all 20 files created:

- [ ] `/gtm-plans/[product-name]/README.md`
- [ ] `/gtm-plans/[product-name]/1-pre-launch/beta-program-plan.md`
- [ ] `/gtm-plans/[product-name]/1-pre-launch/waitlist-strategy.md`
- [ ] `/gtm-plans/[product-name]/1-pre-launch/press-outreach.md`
- [ ] `/gtm-plans/[product-name]/1-pre-launch/community-building.md`
- [ ] `/gtm-plans/[product-name]/2-launch-day/hour-by-hour-timeline.md`
- [ ] `/gtm-plans/[product-name]/2-launch-day/product-hunt-playbook.md`
- [ ] `/gtm-plans/[product-name]/2-launch-day/social-media-posts.md`
- [ ] `/gtm-plans/[product-name]/2-launch-day/community-engagement.md`
- [ ] `/gtm-plans/[product-name]/3-post-launch/week-1-priorities.md`
- [ ] `/gtm-plans/[product-name]/3-post-launch/feedback-loops.md`
- [ ] `/gtm-plans/[product-name]/3-post-launch/pricing-experiments.md`
- [ ] `/gtm-plans/[product-name]/3-post-launch/growth-loops.md`
- [ ] `/gtm-plans/[product-name]/4-content-calendar/days-1-30.md`
- [ ] `/gtm-plans/[product-name]/4-content-calendar/days-31-60.md`
- [ ] `/gtm-plans/[product-name]/4-content-calendar/days-61-90.md`
- [ ] `/gtm-plans/[product-name]/4-content-calendar/evergreen-content.md`
- [ ] `/gtm-plans/[product-name]/5-metrics-dashboard/kpi-tracking.md`
- [ ] `/gtm-plans/[product-name]/5-metrics-dashboard/channel-attribution.md`
- [ ] `/gtm-plans/[product-name]/5-metrics-dashboard/weekly-reports.md`

**Total Expected Files**: 20 (19 plan files + 1 README)

**Output to user**: `✅ Step 10/11: File verification complete ([X] files created)`

---

### Step 11: Display Success Message

**Output to user**: `⏳ Step 11/11: Finalizing GTM plan...`

```
════════════════════════════════════════════════════════════
   ✅ GTM PLAN GENERATED: [Product Name]
════════════════════════════════════════════════════════════

📁 Location: /gtm-plans/[product-name-slug]/
📄 Files Created: 20 files across 5 directories

📅 Launch Timeline:
   • Pre-launch: [Calculated dates for Weeks -4 to -1]
   • Launch date: [Calculated target date]
   • Post-launch: [Calculated dates for Days 1-30]
   • Growth phase: [Calculated dates for Days 31-90]

💰 Budget Allocation:
   • Pre-launch: $[budget × 0.30] (30%)
   • Launch day: $[budget × 0.20] (20%)
   • Post-launch: $[budget × 0.50] (50%)

📊 Expected Results:
   • Waitlist signups: 500-1,000
   • Launch day signups: 100-300
   • 30-day conversions: [calculated target]
   • 90-day conversions: [calculated target × 3]
   • Target CAC: $[calculated]
   • LTV:CAC ratio: [calculated]:1

📋 What Was Generated:
   ✓ Pre-launch strategy (4 files)
     - Beta program plan
     - Waitlist building strategy
     - Press & influencer outreach
     - Community engagement

   ✓ Launch day playbook (4 files)
     - Hour-by-hour timeline
     - Product Hunt strategy
     - Social media posts
     - Community engagement plan

   ✓ Post-launch optimization (4 files)
     - Week 1 priorities
     - Feedback loops
     - Pricing experiments
     - Growth loops

   ✓ Content calendar (4 files)
     - Days 1-30 (28 posts)
     - Days 31-60 (content pillars)
     - Days 61-90 (milestones)
     - Evergreen content library

   ✓ Metrics dashboard (3 files)
     - KPI tracking
     - Channel attribution
     - Weekly reports

🚀 Next Steps:
   1. Review README.md for complete overview
   2. Customize each file for your specific context
   3. Share with team and assign responsibilities
   4. Begin pre-launch activities (Week -4)
   5. Set up tracking and analytics
   6. Execute launch day playbook on [launch date]

⏱️  Time Investment:
   • Review & customize: 15-20 minutes
   • Team alignment: 30 minutes
   • Execution: Follow weekly timeline

💰 Expected ROI:
   • Manual GTM planning: $15K-25K + 3-4 weeks
   • AI-assisted (this): $2K-5K + 3-5 days
   • Savings: $10K-20K + 2-3 weeks faster to market

════════════════════════════════════════════════════════════
              GTM PLAN READY TO EXECUTE 🎯
════════════════════════════════════════════════════════════

View your plan: /gtm-plans/[product-name-slug]/README.md

**Remember**: Launch at 80%, iterate to 100% with real user feedback.
```

**Output to user**: `✅ Step 11/11: GTM plan complete!`
**Output to user**: ``
**Output to user**: `🎉 All files successfully generated! Review /gtm-plans/[product-name-slug]/README.md to get started.`

---

**Ready to generate your GTM plan?** Run `/startup:gtm` with your product details and let's build your launch playbook!
