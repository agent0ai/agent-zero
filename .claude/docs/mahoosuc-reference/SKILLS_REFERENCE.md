# Skills Reference

Comprehensive documentation of all available skills and how to use them.

## Available Skills

### 1. Stripe Revenue Analyzer

**Name**: `stripe-revenue-analyzer`

**Description**: Analyzes Stripe revenue data for trends, growth patterns, top customers, churn rates, payment success metrics, and subscription health. Provides AI-powered insights and actionable recommendations.

**When to Use**:

- Analyzing Stripe payment data and transaction history
- Identifying revenue trends and growth patterns
- Finding top customers and revenue concentration
- Tracking churn rates and subscription health
- Analyzing payment success metrics and failure rates
- Making data-driven pricing or subscription decisions

**Quick Start**:

```bash
Skill("stripe-revenue-analyzer")
```

**Typical Workflow**:

1. Invoke the skill
2. Connect your Stripe API credentials (read-only access)
3. Specify the time period for analysis
4. Select metrics to analyze (revenue, churn, payment success, etc.)
5. Receive AI-powered insights and recommendations

**Output Examples**:

- Revenue growth rate (month-over-month, year-over-year)
- Top 10 customers by revenue
- Churn rate analysis by cohort
- Payment success rate trends
- Subscription health indicators
- Actionable recommendations for optimization

**Project Integration**: Use for `/devops:cost-analyze` comparisons and financial planning.

---

### 2. Brand Voice

**Name**: `brand-voice`

**Description**: Maintains consistent AI solutioning brand voice across all client-facing content, proposals, social media, and communications. Applies data-driven, practical, authority-building tone with real results and proof points.

**When to Use**:

- Creating marketing materials and proposals
- Writing client-facing emails and communications
- Developing content for social media platforms
- Building thought leadership articles and blog posts
- Creating product copy and value propositions
- Ensuring consistency across all client communications

**Quick Start**:

```bash
Skill("brand-voice")
```

**Brand Voice Characteristics**:

- **Tone**: Data-driven, practical, authority-building
- **Style**: Clear, confident, results-oriented
- **Approach**: Real results and proof points over hype
- **Audience**: C-suite, technical leads, decision-makers
- **Key Values**: Transparency, expertise, measurable outcomes

**Typical Workflow**:

1. Invoke the skill
2. Provide content type (proposal, email, social, article, etc.)
3. Specify target audience and context
4. Supply source material or topic
5. Receive brand-aligned content with tone consistent across all channels

**Output Examples**:

- Client proposals with authority and credibility
- Email templates maintaining consistent voice
- Social media content with brand personality
- Blog articles with thought leadership positioning
- Product copy emphasizing real value and ROI

**Project Integration**: Use for all external communications, `/product:*` commands, and marketing content.

---

### 3. Content Optimizer

**Name**: `content-optimizer`

**Description**: Optimizes content for specific platforms (Reddit, LinkedIn, Twitter, HackerNews, Discord) with platform-specific formatting, tone, hashtags, and engagement strategies. Applies best practices for hooks, structure, calls-to-action, and virality patterns.

**When to Use**:

- Creating social media content for specific platforms
- Writing Reddit posts or comments with platform conventions
- Crafting LinkedIn articles and updates
- Composing Twitter/X threads with engagement hooks
- Posting on HackerNews with technical credibility
- Managing Discord community discussions
- Optimizing content structure for platform algorithms

**Quick Start**:

```bash
Skill("content-optimizer")
```

**Platform-Specific Optimization**:

**LinkedIn**:

- Professional tone, thought leadership
- 3-5 line posts with line breaks for readability
- Relevant hashtags (#AI #DataEngineering, etc.)
- Call-to-action encouraging engagement
- Focus on career growth and industry insights

**Twitter/X**:

- Concise, punchy language (280 character limit)
- Thread format with hooks (1/n, 2/n, etc.)
- Relevant trending hashtags
- Emoji for visual interest
- Link to longer content when applicable

**Reddit**:

- Authentic, conversational tone
- Subreddit-specific conventions and culture
- Helpful context and source links
- Natural mention of products (never spammy)
- Engagement through questions and discussion

**HackerNews**:

- Technical depth and credibility
- Focus on novel/interesting approaches
- Show work and learnings
- Humble, educational tone
- Minimal self-promotion

**Discord**:

- Community-oriented, casual tone
- Format-friendly messages with code blocks
- Emoji reactions and engagement
- Thread-based discussions for organization
- Community participation and support focus

**Typical Workflow**:

1. Invoke the skill
2. Specify target platform (LinkedIn, Twitter, Reddit, etc.)
3. Define content topic or provide draft
4. Indicate target audience and goals
5. Receive platform-optimized content with:
   - Platform-specific formatting
   - Optimal length and structure
   - Engagement hooks and CTAs
   - Appropriate tone and voice
   - Hashtag recommendations
   - Timing suggestions

**Output Examples**:

- LinkedIn articles with 5K+ engagement potential
- Twitter threads with high retweet/engagement rates
- Reddit posts that spark thoughtful discussions
- HackerNews submissions that gain traction
- Discord messages that build community
- Multi-platform content variations from single source

**Project Integration**: Use for all social media marketing, community engagement, and thought leadership positioning.

---

### 4. Vercel Landing Page Builder

**Name**: `vercel-landing-page-builder`

**Description**: Automates landing page creation using v0.dev for AI-powered design and Vercel for instant deployment. Handles product landing pages, SaaS marketing pages, launch pages, and conversion-optimized pages.

**When to Use**:

- Creating new product landing pages
- Building SaaS marketing pages
- Designing launch pages for new features
- Creating conversion-optimized landing pages
- Building rapid prototypes for A/B testing
- Deploying static marketing sites instantly
- Creating mobile-responsive web pages

**Quick Start**:

```bash
Skill("vercel-landing-page-builder")
```

**Capabilities**:

**AI-Powered Design** (v0.dev):

- Automatic responsive design generation
- Component-based architecture
- Modern UI patterns and layouts
- Accessibility compliance built-in
- Dark mode support
- Mobile-first approach

**Instant Deployment** (Vercel):

- One-click deployment
- Global CDN distribution
- Zero configuration needed
- Automatic SSL/TLS
- Git integration for updates
- Environment variables support

**Typical Workflow**:

1. Invoke the skill
2. Specify page type (product landing, SaaS, launch, etc.)
3. Provide content (headlines, copy, features, CTA, etc.)
4. Define design preferences (style, color, theme)
5. Skill generates page design using v0.dev
6. Review and customize if needed
7. Deploy to Vercel with one click
8. Get live URL instantly

**Page Types Supported**:

- **Product Landing Pages**: Feature showcase, pricing, testimonials
- **SaaS Marketing Pages**: Hero, features, benefits, plans, FAQ
- **Launch Pages**: Countdown, early access signup, product demo
- **Feature Pages**: Deep dive into specific product features
- **Pricing Pages**: Multiple tiers, comparison, FAQ
- **Case Study Pages**: Results, metrics, customer testimonials
- **Event Pages**: Conference, webinar, workshop details
- **Waitlist Pages**: Early access capture and newsletter signup

**Optimization Features**:

- **Conversion Optimization**: CTA placement, scarcity messaging, social proof
- **SEO Ready**: Meta tags, structured data, Open Graph
- **Analytics Integration**: Google Analytics, Segment, Mixpanel ready
- **A/B Testing**: Easy variant creation and testing
- **Performance**: Optimized images, lazy loading, code splitting

**Output Examples**:

- Fully deployed landing page with live URL
- Mobile-responsive design (works on all devices)
- SEO-optimized with meta tags
- Integrated CTA with conversion tracking
- Analytics-ready for measurement
- Easy to update and iterate

**Project Integration**: Use for `/startup:gtm`, `/product:define`, and all marketing page creation.

---

## Skill Usage Patterns

### Using Skills in Claude Code

To invoke any skill during your work:

```bash
Skill("skill-name")
```

The skill will load and provide its full interface for you to interact with.

### Integrating Skills with Slash Commands

Skills are often used in conjunction with slash commands:

- `Brand voice` → `/product:positioning`, `/startup:gtm`
- `Content optimizer` → `/scripts:video`, `/social:post`
- `Vercel landing page builder` → `/product:define`, `/startup:generate`
- `Stripe revenue analyzer` → `/finance:report`, `/devops:cost-analyze`

### Combining Multiple Skills

For complex tasks, combine multiple skills:

1. **Product Launch**:
   - Use `vercel-landing-page-builder` to create landing page
   - Use `brand-voice` to write copy
   - Use `content-optimizer` to create social media announcements
   - Use `stripe-revenue-analyzer` to track conversion metrics

2. **Content Marketing**:
   - Use `brand-voice` to establish tone and messaging
   - Use `content-optimizer` for platform-specific versions
   - Use `vercel-landing-page-builder` for supporting landing pages

3. **Sales & Marketing**:
   - Use `brand-voice` for proposal development
   - Use `stripe-revenue-analyzer` for customer insights
   - Use `content-optimizer` for social selling content

## Skill Best Practices

1. **Start Simple**: Use skills one at a time when first learning
2. **Understand Output**: Review skill outputs carefully before acting on them
3. **Iterate**: Use skill outputs as starting points, customize as needed
4. **Combine**: Stack skills for more complex workflows
5. **Measure**: Track outcomes of skill-generated content or decisions
6. **Feedback**: Provide feedback to improve skill recommendations
7. **Documentation**: Keep notes on what works for your use case

## Troubleshooting Skills

### Skill Not Responding

- Check if skill name is spelled correctly
- Ensure you have necessary API credentials (Stripe, etc.)
- Verify network connectivity for external APIs
- Check Claude Code subscription status

### Unexpected Output

- Provide more specific instructions or context
- Break complex requests into smaller parts
- Review skill documentation for limitations
- Try different input formats or phrasings

### Performance Issues

- Stripe data analysis may take longer with large datasets
- Content optimization works better with specific platform focus
- Landing page builder needs clear, detailed requirements
- Consider breaking large jobs into smaller batch jobs

## Resource Links

- **Stripe API Documentation**: <https://stripe.com/docs>
- **v0.dev**: <https://v0.dev>
- **Vercel Documentation**: <https://vercel.com/docs>
- **Brand Guidelines**: See `/guides/` in project repo
- **Content Best Practices**: See `/guides/unified-best-practices__claude_sonnet_4.md`

---

**Last Updated**: 2025-12-05
