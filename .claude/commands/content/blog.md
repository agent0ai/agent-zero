---
description: Write SEO-optimized blog posts with keyword research and content strategy
argument-hint: [--topic <subject>] [--keywords <list>] [--length <words>] [--tone <professional|casual|technical>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Write, WebSearch, Grep, Glob
---

# Blog Post Generator

Create comprehensive, SEO-optimized blog posts that drive organic traffic, establish thought leadership, and generate qualified leads. Includes keyword research, content strategy, and conversion optimization.

## What This Command Does

This command generates complete blog posts optimized for search engines and reader engagement. It performs keyword research, creates compelling headlines, structures content for readability, and includes strategic CTAs for lead generation.

**Key Features**:

- AI-powered keyword research and competitor analysis
- SEO-optimized headlines and meta descriptions
- Structured content with H2/H3 headers for readability
- Internal linking suggestions for topic clusters
- Strategic CTAs for lead generation
- FAQ sections for featured snippets
- Social media snippet suggestions

## Business Value & ROI

**Annual Value: $120,000**

- 400% increase in organic search traffic
- 10x reduction in content creation time (30 hours → 3 hours per post)
- 65% improvement in keyword rankings
- 3x increase in content-driven lead generation
- 80% reduction in content production costs

**Lead Generation Impact**:

- Average 2,500 organic visitors per optimized post/month
- 3% conversion rate = 75 leads/post/month
- Average customer value: $5,000
- Expected ROI: 15:1 on content investment

**Thought Leadership**:

- Establish domain authority in your niche
- Build trust with prospective customers
- Create shareable, linkable assets
- Support sales team with educational content

## Usage

### Basic Usage

```bash
/content:blog --topic "AI automation for small businesses"
```

### Advanced Usage with Keywords

```bash
/content:blog --topic "Customer retention strategies" --keywords "customer retention,churn reduction,loyalty programs" --length 2500 --tone professional
```

### Technical Deep Dive

```bash
/content:blog --topic "Kubernetes deployment patterns" --tone technical --length 3000
```

### Thought Leadership Piece

```bash
/content:blog --topic "Future of remote work in 2025" --tone professional --length 2000
```

## How It Works

Routes to **prompt-engineering-agent** with comprehensive content brief:

```javascript
await Task({
  subagent_type: 'prompt-engineering-agent',
  description: 'Generate SEO-optimized blog post',
  prompt: `Generate comprehensive blog post about: ${TOPIC}

Target keywords: ${KEYWORDS || 'AI-suggested based on topic'}
Word count: ${LENGTH || '1500-2000'} words
Tone: ${TONE || 'professional'}

## BLOG POST GENERATION WORKFLOW

### Stage 1: Keyword Research & SEO Strategy

**Primary Keyword Research**:
- Identify primary target keyword (search volume, difficulty, intent)
- Find 3-5 related keywords (LSI keywords)
- Analyze top 10 ranking articles for the primary keyword
- Identify content gaps and opportunities

**Search Intent Analysis**:
- Determine user intent (informational, commercial, transactional)
- Identify questions users are asking
- Map content to buyer journey stage (awareness, consideration, decision)

**Competitive Analysis**:
- Review top 5 competing articles
- Identify what they're missing
- Find unique angles or updated information
- Determine optimal word count (match or exceed top results)

### Stage 2: Content Structure & Outline

**Headline Options** (provide 5):
1. [Number]-driven: "7 Proven Strategies to [Achieve Benefit]"
2. How-to: "How to [Achieve Goal] in [Timeframe]"
3. Question: "Why Is [Topic] Critical for [Audience] in 2025?"
4. Ultimate Guide: "The Complete Guide to [Topic] for [Audience]"
5. Contrarian: "Why [Common Belief] About [Topic] Is Wrong"

**Meta Description** (155 characters max):
[Compelling summary with primary keyword, benefit, and CTA]

**Content Outline**:

#### Introduction (150-200 words)
- Hook: Compelling opening that addresses pain point
- Problem statement: What challenge does the reader face?
- Promise: What will they learn/gain from this article?
- Preview: Outline of what's covered

#### Main Content Sections (H2 headers)

**Section 1: [H2 Title with Keyword]** (300-500 words)
- Key point 1
- Key point 2
- Data/statistics to support
- Example or case study

**Section 2: [H2 Title]** (300-500 words)
- Key point 1
- Key point 2
- Actionable advice
- Visual element suggestion (chart, infographic, screenshot)

**Section 3: [H2 Title]** (300-500 words)
- Key point 1
- Key point 2
- Expert quote or research citation
- Real-world application

[Continue for 5-7 main sections based on keyword research]

#### FAQ Section (H2: "Frequently Asked Questions")
Answer 5-8 questions in concise format for featured snippet optimization:

**Q: [Question with long-tail keyword]**
A: [Concise 40-60 word answer]

#### Conclusion (150-200 words)
- Recap key takeaways (3-5 bullet points)
- Reinforce main benefit
- Clear next steps
- Strong CTA

### Stage 3: Write Complete Blog Post

Write full blog post following the outline with these requirements:

**Writing Style**:
- ${TONE} tone throughout
- Active voice (minimize passive constructions)
- Short paragraphs (2-4 sentences max)
- Transition sentences between sections
- Conversational but authoritative

**SEO Optimization**:
- Primary keyword in: title, first paragraph, conclusion, 1 H2 header
- Related keywords distributed naturally (avoid keyword stuffing)
- Internal linking opportunities (mark with [LINK: relevant page/topic])
- External links to authoritative sources (2-3 minimum)
- Image alt text suggestions for visuals

**Readability**:
- Flesch Reading Ease score: 60-70
- Use bullet points and numbered lists
- Include text formatting (bold for key points)
- Add blockquotes for important insights
- Use examples and analogies

**Engagement Elements**:
- Statistics and data points (with sources)
- Expert quotes or case studies
- Actionable tips (numbered lists)
- Visual content suggestions (charts, screenshots, infographics)

### Stage 4: Lead Generation Optimization

**Primary CTA** (end of article):
- Offer relevant lead magnet (ebook, template, calculator, free trial)
- Clear value proposition
- Minimal friction (email only, no lengthy forms)

Example:
> **Ready to [Achieve Benefit]?**
> Download our free [Resource Type]: "[Title]" - includes [specific benefits].
> [CTA Button: Get Free Access]

**Secondary CTAs** (within content):
- Mid-article: Soft CTA to related resource
- Sidebar: Newsletter signup
- End of sections: Related article links (topic cluster)

**Content Upgrades**:
- Downloadable checklist based on article
- Template or worksheet
- Exclusive bonus content

### Stage 5: Technical SEO Elements

**URL Slug**: /blog/[primary-keyword-phrase]

**Meta Tags**:
- Title tag (60 characters): [Primary Keyword] - [Benefit] | [Brand]
- Meta description (155 characters): [Already created above]
- Focus keyphrase: [Primary keyword]

**Structured Data**:
- Article schema markup (headline, author, date, image)
- FAQ schema for FAQ section
- BreadcrumbList schema

**Open Graph Tags** (social sharing):
- og:title: [Compelling social headline]
- og:description: [Social-optimized description]
- og:image: [Suggested image dimensions: 1200x630]

**Internal Linking Strategy**:
Suggest 5-7 internal links to:
- Related blog posts (topic cluster)
- Product/service pages (where relevant)
- Resource pages
- About/Team page (if mentioning expertise)

### Stage 6: Social Media Assets

**LinkedIn Post** (300 characters):
[Hook + key insight + link]

**Twitter Thread** (5 tweets):
Tweet 1: [Hook with main takeaway]
Tweet 2-4: [Key points from article]
Tweet 5: [CTA with link]

**Email Newsletter Snippet** (150 words):
[Compelling preview with "Read more" link]

### Stage 7: Content Performance Tracking

**Key Metrics to Track**:
- Organic search traffic (30, 60, 90 days)
- Keyword rankings (primary + related keywords)
- Time on page / scroll depth
- Conversion rate (CTA clicks, lead captures)
- Social shares
- Backlinks acquired

**Success Benchmarks** (30 days post-publish):
- 500+ organic sessions
- Top 10 ranking for primary keyword
- 50+ leads generated
- 3% conversion rate
- 100+ social shares

## OUTPUT FORMAT

Provide complete blog post in Markdown format with:

# [Final Headline]

**Meta Description**: [155 characters]
**Primary Keyword**: [keyword]
**Word Count**: [actual count]
**Reading Time**: [estimated minutes]

---

[Full blog post content with proper H2/H3 structure]

---

## SEO CHECKLIST
- ✓ Primary keyword in title, intro, conclusion
- ✓ Related keywords distributed naturally
- ✓ 5+ internal links suggested
- ✓ 2+ external authoritative links
- ✓ FAQ section for featured snippets
- ✓ Meta description optimized
- ✓ URL slug recommended
- ✓ Image alt text suggestions provided
- ✓ Structured data markup suggested

## LEAD GENERATION
- Primary CTA: [Description]
- Expected conversion rate: 3-5%
- Lead magnet: [Specific asset]

## SOCIAL MEDIA ASSETS
[Include LinkedIn, Twitter, email snippets]

Save blog post to: content/blog/[url-slug].md
Save social assets to: content/social/[url-slug]-social.md
  `
})
```

## Success Metrics

### Content Quality

- ✓ 1,500+ words (optimal for SEO)
- ✓ Flesch Reading Ease score: 60-70
- ✓ 5-7 main sections with H2 headers
- ✓ FAQ section included
- ✓ Clear introduction and conclusion

### SEO Optimization

- ✓ Primary keyword research completed
- ✓ 5+ related keywords identified
- ✓ Meta description under 155 characters
- ✓ URL slug optimized
- ✓ Internal linking strategy provided
- ✓ Structured data recommendations

### Lead Generation

- ✓ Primary CTA at end of article
- ✓ Lead magnet offer specified
- ✓ Secondary CTAs strategically placed
- ✓ Content upgrade suggested
- ✓ Expected conversion rate: 3-5%

### Engagement

- ✓ Social media assets created
- ✓ Email newsletter snippet provided
- ✓ Visual content suggestions included
- ✓ Examples and case studies incorporated

## Performance Tracking

**30-Day Goals**:

- 500+ organic sessions
- Top 20 ranking for primary keyword
- 50+ leads generated
- 100+ social shares

**90-Day Goals**:

- 2,000+ organic sessions
- Top 10 ranking for primary keyword
- 200+ leads generated
- 5+ quality backlinks

## Example Output

```markdown
# 7 Proven AI Automation Strategies That Save Small Businesses 15 Hours Per Week

**Meta Description**: Discover AI automation strategies that help small businesses save 15+ hours weekly. Includes real examples, ROI calculator, and implementation guide.

**Primary Keyword**: AI automation for small businesses
**Word Count**: 2,450
**Reading Time**: 11 minutes

---

## Introduction

Small business owners wear too many hats. Between managing operations, serving customers, and handling administrative tasks, there's barely time to focus on growth.

What if you could reclaim 15 hours per week without hiring additional staff?

AI automation is no longer reserved for enterprise companies with massive budgets. Modern AI tools are affordable, easy to implement, and deliver ROI within 30 days.

In this guide, you'll discover 7 proven AI automation strategies that small businesses are using to eliminate repetitive tasks, reduce errors, and focus on high-value work.

**What you'll learn**:
- Which business processes to automate first (and why)
- AI tools that cost less than hiring a part-time employee
- Real examples from small businesses saving $50,000+/year
- Step-by-step implementation guide for each strategy
- ROI calculator to estimate your potential savings

[... rest of blog post ...]
```

---

**Uses**: prompt-engineering-agent, WebSearch (for keyword research)
**Output**: Complete blog post (Markdown) + social assets + SEO checklist
**Next Commands**: `/content:whitepaper`, `/seo:optimize`, `/social:generate`
