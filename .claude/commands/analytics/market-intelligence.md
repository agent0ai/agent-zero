---
description: Aggregate data from Reddit, Discord, Twitter/X, LinkedIn and other sources to identify AI solutioning opportunities
argument-hint: "[--sources <reddit|discord|twitter|linkedin|all>] [--topics <ai,automation,productivity>] [--export]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - WebFetch
---

# Market Intelligence Command

## Overview

Aggregates data from Reddit, Discord, Twitter/X, LinkedIn, and other platforms to identify:

- **Pain points** people are trying to solve with AI
- **Trending topics** in AI/automation/productivity
- **Common questions** that your methodology answers
- **Competitor positioning** and messaging
- **Market opportunities** for your AI solutioning services

**Purpose**: Develop market-informed **AI Solutioning Voice** based on real community conversations.

## What This Command Does

- ✅ Monitors Reddit communities (r/productivity, r/AI, r/automation, etc.)
- ✅ Tracks Discord servers (AI/productivity communities)
- ✅ Analyzes Twitter/X discussions (#AI, #productivity, #automation)
- ✅ Monitors LinkedIn posts and comments
- ✅ Identifies trending pain points and opportunities
- ✅ Extracts common questions and objections
- ✅ Generates content ideas and positioning insights
- ✅ Builds authority-building response library

## Usage

```bash
# Aggregate from all sources
/analytics:market-intelligence

# Specific source
/analytics:market-intelligence --sources reddit
/analytics:market-intelligence --sources discord,twitter

# Specific topics
/analytics:market-intelligence --topics ai,automation,productivity

# Export insights
/analytics:market-intelligence --export insights

# Generate content ideas
/analytics:market-intelligence --export content-ideas
```

## Data Sources

### 1. Reddit Communities

**Monitored Subreddits**:

- r/productivity (2.5M members)
- r/Notion (500K members)
- r/gtd (Getting Things Done)
- r/automation (200K members)
- r/AI (3M members)
- r/ChatGPT (5M members)
- r/ClaudeAI (100K members)
- r/SaaS (entrepreneurs)
- r/Entrepreneur (productivity for business)
- r/smallbusiness (SMB pain points)

**Data Collected**:

```javascript
const redditData = {
  posts: {
    title: "How do you handle email overload?",
    subreddit: "r/productivity",
    upvotes: 342,
    comments: 87,
    sentiment: "frustrated",
    painPoints: ["email overload", "time management"],
    solutions: ["tried triage apps", "not working well"]
  },
  trends: {
    topicFrequency: { "email automation": 45, "AI assistants": 78 },
    growingTopics: ["AI email replies", "task prediction"],
    decliningTopics: ["manual scheduling"]
  },
  commonQuestions: [
    "Best AI tool for email management?",
    "How to automate task creation from emails?",
    "Is Motion worth the price?"
  ]
};
```

**Insights Generated**:

- Most discussed pain points
- Popular solutions (and their shortcomings)
- Unmet needs and gaps
- Price sensitivity and ROI expectations
- Tool adoption barriers

### 2. Discord Servers

**Monitored Servers**:

- Notion Community (official)
- Productivity Den
- AI Automation Hub
- Indie Hackers
- SaaS Growth
- Claude AI (official)
- ChatGPT Community

**Data Collected**:

```javascript
const discordData = {
  channels: {
    "#automation-help": {
      activeUsers: 1500,
      messagesPerDay: 200,
      commonTopics: ["workflow automation", "zapier alternatives"],
      sentimentTrend: "positive" // Growing interest
    }
  },
  realTimeConversations: {
    painPoint: "I spend 2 hours/day on email",
    responses: [
      "Try AI email triage",
      "I use Claude for replies",
      "Still manual for me"
    ],
    resolution: "No clear winner, people still struggling"
  },
  influencers: {
    user: "@ProductivityGuru",
    followers: 5000,
    topics: ["AI automation", "productivity systems"],
    engagement: "high"
  }
};
```

**Insights Generated**:

- Real-time pain points and frustrations
- What solutions people are trying
- Influencer opinions and recommendations
- Community sentiment on specific tools
- Emerging trends before they hit mainstream

### 3. Twitter/X Discussions

**Monitored Hashtags & Accounts**:

- #productivity
- #AI
- #automation
- #AItools
- #productivityhacks
- Key influencers (e.g., @naval, @davidperell, productivity thought leaders)

**Data Collected**:

```javascript
const twitterData = {
  tweets: {
    content: "Just saved 10 hours this week with AI email automation 🤖",
    engagement: { likes: 450, retweets: 89, comments: 34 },
    sentiment: "positive",
    topic: "email automation success"
  },
  trending: {
    "#AIproductivity": { volume: 15000, trend: "up 45%" },
    "#MotionApp": { volume: 2000, trend: "steady" }
  },
  influencerOpinions: {
    "@influencer": "AI task prediction changed my life",
    reach: 50000,
    engagement: "very high"
  }
};
```

**Insights Generated**:

- Viral productivity topics
- Influencer positioning and messaging
- What resonates with audiences
- Competitor mentions and sentiment
- Trending tools and solutions

### 4. LinkedIn Posts & Comments

**Monitored**:

- Hashtags: #productivity, #AI, #automation, #digitaltransformation
- Influencers: Productivity coaches, AI consultants, SaaS founders
- Groups: Productivity & Time Management, AI in Business, SaaS Entrepreneurs

**Data Collected**:

```javascript
const linkedinData = {
  posts: {
    author: "AI Consultant with 10K followers",
    content: "3 ways AI can save your team 20 hours/week",
    engagement: { likes: 500, comments: 45, shares: 67 },
    audienceType: "B2B decision makers",
    commonComments: [
      "Which AI tools do you recommend?",
      "What's the ROI?",
      "How long to implement?"
    ]
  },
  professionalSentiment: {
    topic: "AI automation for SMBs",
    sentiment: "cautiously optimistic",
    concerns: ["cost", "implementation complexity", "ROI proof"]
  }
};
```

**Insights Generated**:

- B2B pain points and priorities
- Decision-maker concerns and objections
- Professional positioning examples
- Case study effectiveness
- Content that drives engagement

## AI-Powered Analysis

### 1. Pain Point Extraction

```javascript
const painPointAnalysis = await claude.analyze({
  prompt: `Analyze these 500 Reddit/Discord/Twitter posts and extract pain points:

  Posts: ${aggregatedPosts}

  Extract:
  1. Top 10 pain points (ranked by frequency and intensity)
  2. For each pain point:
     - How many people mentioned it
     - Severity (1-10)
     - Current solutions being tried
     - Why current solutions fail
     - Willingness to pay (if mentioned)

  Return JSON with pain points ranked by "opportunity score"
  (frequency × severity × willingness_to_pay)
  `
});

// Example output:
{
  painPoints: [
    {
      description: "Email overload - spending 2+ hours/day on email",
      frequency: 342, // mentions
      severity: 8.5, // out of 10
      currentSolutions: [
        "Manual triage (65% of people)",
        "Gmail filters (40%)",
        "Email apps like Superhuman (20%)"
      ],
      failures: [
        "Still manual work required",
        "Filters too rigid",
        "Expensive ($30/mo) with limited AI"
      ],
      willingnessToPay: "$50-100/month for real solution",
      opportunityScore: 95 // High!
    }
  ]
}
```

### 2. Trend Identification

```javascript
const trendAnalysis = await claude.analyzeTrends({
  prompt: `Analyze these topics over the last 3 months:

  Data: ${topicFrequencyOverTime}

  Identify:
  1. Growing trends (momentum gaining)
  2. Declining trends (losing interest)
  3. Emerging trends (new, early stage)
  4. Stable trends (consistent interest)

  For each trend, explain why it's growing/declining.
  `
});

// Example output:
{
  growing: [
    {
      topic: "AI email replies",
      growth: "+145% mentions in 3 months",
      reason: "ChatGPT and Claude have proven AI can write well",
      opportunity: "High - people ready to adopt"
    },
    {
      topic: "Task prediction AI",
      growth: "+89% mentions",
      reason: "Recurring task fatigue, Motion AI gaining traction",
      opportunity: "Medium - Still early, education needed"
    }
  ],
  declining: [
    {
      topic: "Manual productivity systems",
      decline: "-32% mentions",
      reason: "AI automation making manual systems obsolete",
      opportunity: "Replacement market - convert manual users"
    }
  ]
}
```

### 3. Content Gap Analysis

```javascript
const contentGaps = await claude.findContentGaps({
  prompt: `Find unanswered questions and content opportunities:

  Common Questions: ${commonQuestions}
  Existing Content: ${competitorContent}

  Identify:
  1. Questions asked frequently but poorly answered
  2. Topics with high interest but low quality content
  3. Misconceptions that need correction
  4. Opportunities to demonstrate your unique methodology

  Return content ideas ranked by opportunity.
  `
});

// Example output:
{
  contentOpportunities: [
    {
      question: "What's the actual ROI of AI productivity tools?",
      frequency: 78, // times asked
      currentAnswers: "Mostly vague, no real data",
      yourAdvantage: "You have 3 months of real data (25 hrs/week saved, 1,184% ROI)",
      contentIdea: "Case study post: 'I tracked AI productivity tools for 3 months. Here's the real ROI with data.'",
      estimatedEngagement: "Very High"
    },
    {
      question: "How long does it take to see results from AI automation?",
      frequency: 54,
      currentAnswers: "Generic 'it depends' responses",
      yourAdvantage: "You have week-by-week data showing learning curve",
      contentIdea: "Blog post: 'The AI Automation Learning Curve: What to expect Week 1-12 (with data)'",
      estimatedEngagement: "High"
    }
  ]
}
```

### 4. Competitive Intelligence

```javascript
const competitorAnalysis = await claude.analyzeCompetitors({
  prompt: `Analyze competitor positioning and messaging:

  Competitors: ${competitorMentions}

  For each competitor, extract:
  1. How they position themselves
  2. What they emphasize (features, ROI, ease of use)
  3. Common complaints/criticisms
  4. Gaps in their offering
  5. Your differentiation opportunities
  `
});

// Example output:
{
  competitors: [
    {
      name: "Motion",
      positioning: "AI-powered calendar and task manager",
      emphasis: ["Automatic scheduling", "AI task planning"],
      complaints: [
        "Expensive ($34/mo)",
        "Learning curve steep",
        "Limited integrations"
      ],
      gaps: [
        "No email automation",
        "No cross-context analysis",
        "No continuous optimization"
      ],
      yourDifferentiation: [
        "Complete system (email + tasks + calendar + optimization)",
        "Proven ROI with real data",
        "Methodology for implementation (not just a tool)"
      ]
    }
  ]
}
```

## Generated Insights Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MARKET INTELLIGENCE REPORT
Period: Last 30 days
Sources: Reddit (15K posts), Discord (5K messages), Twitter (8K tweets), LinkedIn (2K posts)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 TOP 10 PAIN POINTS (By Opportunity Score)

[1] Email Overload (Opportunity Score: 95/100)
    • Mentioned: 342 times
    • Severity: 8.5/10 (very high frustration)
    • Current Solutions: Gmail filters (limited), Superhuman ($30/mo but still manual)
    • Failure Reasons: "Still spend 2 hours/day on email"
    • Willingness to Pay: $50-100/month for real solution
    • Your Solution: /email:smart-reply + /email:triage (saves 1-2 hrs/day, proven)
    • Your Advantage: Real data showing 80%+ time savings

[2] Task Management Overwhelm (Opportunity Score: 89/100)
    • Mentioned: 287 times
    • Severity: 7.8/10
    • Current Solutions: Notion, Trello, Asana (all manual)
    • Failure Reasons: "Too much manual planning, miss recurring tasks"
    • Willingness to Pay: $30-60/month
    • Your Solution: /autopilot:predict-tasks + Motion integration
    • Your Advantage: Proactive vs reactive (predict tasks before user thinks of them)

[3] Meeting Scheduling Hell (Opportunity Score: 82/100)
    • Mentioned: 198 times
    • Severity: 6.9/10
    • Current Solutions: Calendly (limited AI), back-and-forth emails
    • Failure Reasons: "Takes 15-20 min to schedule one meeting"
    • Willingness to Pay: $20-40/month
    • Your Solution: /schedule:smart (AI finds optimal time across timezones)
    • Your Advantage: Context-aware (considers energy levels, prep time, etc.)

[4] Context Switching Fatigue (Opportunity Score: 78/100)
    • Mentioned: 156 times
    • Severity: 8.2/10
    • Current Solutions: Time blocking (manual), focus apps
    • Failure Reasons: "Lose 2+ hours/day to context switching"
    • Willingness to Pay: $40-80/month
    • Your Solution: /context:analyze + /optimize:auto (automated rebalancing)
    • Your Advantage: Quantified impact (15-20 min lost per switch) + AI fixes it

[5] AI Tool Overwhelm (Opportunity Score: 75/100)
    • Mentioned: 234 times
    • Severity: 6.5/10
    • Current Solutions: "Trying 5 different AI tools, too fragmented"
    • Failure Reasons: "Need to switch between tools, data not synced"
    • Willingness to Pay: $100-150/month for unified system
    • Your Solution: Complete integrated system (21 commands, all tools synced)
    • Your Advantage: "One system to rule them all" + proven methodology

... [remaining 5 pain points]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 TRENDING TOPICS (Last 90 Days)

GROWING (Momentum Gaining):
  [1] AI Email Replies: +145% mentions
      Why: ChatGPT/Claude proven AI can write well
      Opportunity: HIGH - People ready to adopt
      Your Position: Real data (82% draft selection rate after 3 weeks)

  [2] Task Prediction AI: +89% mentions
      Why: Motion AI gaining traction, recurring task fatigue
      Opportunity: MEDIUM - Early stage, education needed
      Your Position: Case study (90% prediction accuracy after 3 months)

  [3] Continuous Optimization: +67% mentions
      Why: "Set and forget" productivity appealing
      Opportunity: HIGH - Your /optimize:auto is unique
      Your Position: Only complete daily auto-optimization system

DECLINING (Losing Interest):
  [1] Manual Productivity Systems: -32% mentions
      Why: AI making manual obsolete
      Opportunity: Replacement market (convert manual users)
      Your Position: "AI-powered productivity is the new standard"

  [2] Single-Purpose Tools: -28% mentions
      Why: Users want integrated systems
      Opportunity: Consolidation play
      Your Position: 21 integrated commands across all productivity areas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 CONTENT OPPORTUNITIES (High Engagement Potential)

[1] "I tracked AI productivity tools for 3 months. Here's the real ROI with data."
    Question Answered: "What's the actual ROI?" (asked 78 times)
    Current Content: Vague, no real data
    Your Advantage: 25 hrs/week saved, 1,184% ROI, 3 months of data
    Estimated Engagement: VERY HIGH (5K+ views, 200+ shares)
    Platforms: LinkedIn (B2B decision makers), Reddit (r/productivity)

[2] "The AI Automation Learning Curve: What to expect Week 1-12 (with data)"
    Question Answered: "How long to see results?" (asked 54 times)
    Current Content: Generic "it depends"
    Your Advantage: Week-by-week accuracy data (60% → 92%)
    Estimated Engagement: HIGH (3K+ views, 150+ shares)
    Platforms: Reddit (r/AI, r/productivity), Twitter

[3] "Why Your Productivity System Needs AI Autopilot (Not Just AI Tools)"
    Question Answered: "How to manage multiple AI tools?" (asked 43 times)
    Current Content: Tool comparisons (fragmented view)
    Your Advantage: Complete integrated system + methodology
    Estimated Engagement: HIGH (4K+ views, 100+ shares)
    Platforms: LinkedIn (thought leadership), Medium

[4] "Email Takes 2 Hours/Day? Here's How AI Cut Mine to 15 Minutes"
    Question Answered: "How to handle email overload?" (asked 342 times!)
    Current Content: Generic tips, no AI solutions
    Your Advantage: /email:smart-reply data (5-10 hrs/week saved)
    Estimated Engagement: VERY HIGH (8K+ views, 300+ shares)
    Platforms: Reddit (r/productivity - high pain point), Twitter, LinkedIn

[5] "Context Switching Costs You 2 Hours/Day. Here's the Data (and the Fix)"
    Question Answered: "How to reduce context switching?" (asked 156 times)
    Current Content: Time blocking advice (manual)
    Your Advantage: Quantified impact (15-20 min/switch) + AI solution
    Estimated Engagement: HIGH (3K+ views, 120+ shares)
    Platforms: Reddit (r/productivity), LinkedIn (B2B angle)

... [20+ more content ideas]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 COMPETITIVE LANDSCAPE

Motion ($34/month)
  Positioning: "AI-powered calendar and task manager"
  Strengths: Good AI scheduling, attractive UI
  Weaknesses: Expensive, limited integrations, no email automation
  Common Complaints: "Steep learning curve", "Worth the price?"
  Your Differentiation:
    • Complete system (email + tasks + calendar + auto-optimization)
    • Proven ROI data (not just promises)
    • Implementation methodology (not just a tool)
    • Better value (complete system vs single tool)

Superhuman ($30/month)
  Positioning: "The fastest email experience ever made"
  Strengths: Great UX, keyboard shortcuts, speed
  Weaknesses: Still mostly manual, limited AI
  Common Complaints: "Expensive for what it is", "AI features basic"
  Your Differentiation:
    • True AI email automation (not just shortcuts)
    • Smart replies (saves 1-2 hrs/day vs Superhuman's minutes)
    • Email → Task workflows (end-to-end automation)
    • Better AI (Claude Sonnet 4 vs basic categorization)

... [more competitors]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎤 YOUR AI SOLUTIONING VOICE (Market-Informed Positioning)

Based on 30 days of market intelligence:

WHAT RESONATES:
  ✅ Real data (not theory) - "I tracked it for 3 months"
  ✅ Honest about challenges - "Learning curve is 2-4 weeks"
  ✅ Specific numbers - "25 hrs/week saved, not 'a lot of time'"
  ✅ Methodology (not just tools) - "Here's how to implement"
  ✅ Complete systems - "Integrated, not fragmented"

WHAT DOESN'T RESONATE:
  ❌ Vague promises - "AI will save you time" (too generic)
  ❌ Over-hyped - "10X your productivity!" (skepticism high)
  ❌ Tool-focused only - "This app is great" (people want systems)
  ❌ No proof - Claims without data (trust is low)

YOUR UNIQUE POSITIONING:
  "I built a 21-command AI productivity system that saves 25 hours/week.
   I measured it daily for 3 months. Here's the data, the methodology,
   and how you can implement it."

KEY MESSAGES:
  • Data-driven (not theoretical): "3 months of real data"
  • Complete system (not fragmented): "21 integrated commands"
  • Proven ROI: "1,184% return, 5-week payback"
  • Honest methodology: "Here's what works and what doesn't"
  • Your secret weapon: "I use this myself every day"

CONTENT STRATEGY:
  1. Lead with data (case studies, reports, metrics)
  2. Teach methodology (how-to guides, implementation steps)
  3. Address objections (learning curve, cost, complexity)
  4. Build authority (consistent posting, helpful responses)
  5. Engage communities (Reddit/Discord, add value first)

CALL TO ACTION:
  "Want the complete implementation guide? [link]"
  "See the full 3-month data report? [link]"
  "Ready to build your own AI productivity system? Let's talk."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next Actions:
[1] Create content from top opportunities
[2] Engage in high-traffic discussions
[3] Build authority-building response library
[4] Monitor competitor mentions
[5] Track trending topics weekly
```

## Authority-Building Response Library

Generate ready-to-use responses for common questions:

```javascript
const responseLibrary = {
  "How to handle email overload?": {
    response: `I struggled with this too - spent 2 hours/day on email.

Here's what actually worked for me (with data):

1. AI email triage at 6 AM daily
   - Auto-archives 30-40 low-priority emails
   - Categorizes by urgency (Eisenhower Matrix)
   - Saves 30-45 min/day

2. Smart AI replies for responses
   - Generates 2-3 draft replies per email
   - Matches my writing style (learned over 3 weeks)
   - Saves 5-10 min per email

Result: Email time reduced from 2 hrs/day → 15-20 min/day

I tracked this daily for 3 months. Happy to share the full data if useful.`,

    followUp: "Want to see the implementation details? I documented everything.",

    credibilitySignals: [
      "Real data (time tracked daily)",
      "Specific numbers (not vague)",
      "Honest about learning curve",
      "Offer to help (not selling)"
    ]
  },

  // ... more responses for top 50 questions
};
```

## Integration

### With Internal Analytics

```bash
# Combine internal + external data
/analytics:ai-insights --export report
/analytics:market-intelligence --export insights

# Generate combined positioning document
```

### With Content Creation

```bash
# Generate content ideas from pain points
/analytics:market-intelligence --export content-ideas

# Output: 20+ blog post/LinkedIn post ideas ranked by engagement potential
```

## Related Commands

- `/analytics:ai-insights` - Internal productivity data
- All 21 automation commands - Your proof points
- Content creation commands (future)

## Notes

**Frequency**: Run weekly to stay current with trends

**Privacy**: Publicly available data only (Reddit/Twitter/LinkedIn public posts)

**Ethics**: Add value to communities, don't just mine for data

---

*Your market tells you what they need. Listen with data, respond with proof.*
