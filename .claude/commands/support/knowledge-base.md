---
description: Generate knowledge base articles from resolved tickets or AI assistance
argument-hint: [--from-ticket <ticket-id>] [--topic "<topic>"] [--format <zoho|markdown|html>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Write, Bash
---

Generate knowledge base article: **${ARGUMENTS}**

## Knowledge Base Generation

**AI-Powered Article Creation**:

- Generate from resolved support tickets
- Create from scratch with AI assistance
- SEO optimization for help center
- Multi-format output (Zoho Desk, Markdown, HTML)
- Automatic categorization and tagging

Routes to **frontend-architect** + **documentation-expert-agent**:

```javascript
await Task({
  subagent_type: 'frontend-architect',
  description: 'Generate KB article',
  prompt: `Generate knowledge base article:

Source: ${FROM_TICKET ? 'Ticket #' + FROM_TICKET : 'New topic: ' + TOPIC}
Format: ${FORMAT || 'zoho'}

Execute KB article generation workflow:

## 1. Gather Source Content

${FROM_TICKET ? \`
### From Resolved Ticket

Fetch ticket data:
\\\`\\\`\\\`bash
# Get ticket details
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}" \\\\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}"

# Get ticket thread (all messages)
curl "https://desk.zoho.com/api/v1/tickets/\${TICKET_ID}/threads" \\\\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}"

# Extract:
# - Original question
# - Resolution steps
# - Screenshots/attachments
# - Final outcome
\\\`\\\`\\\`

Analyze thread to extract:
- **Question**: What was the user trying to do?
- **Problem**: What went wrong?
- **Root Cause**: Why did it happen?
- **Solution**: Step-by-step resolution
- **Outcome**: What was the result?
\` : \`
### New Topic (AI-Assisted)

Topic: \${TOPIC}

AI will research and create article from scratch.

Research areas:
- Product documentation
- Similar help center articles
- Common user questions
- Best practices
- Screenshots needed
\`}

## 2. Determine Article Type

**Types of KB Articles**:

**How-To Guide** (Step-by-step instructions)
- "How to set up X"
- "How to configure Y"
- Structure: Goal → Prerequisites → Steps → Verification

**Troubleshooting** (Problem resolution)
- "Can't login to account"
- "Error message: X"
- Structure: Symptom → Cause → Solution → Prevention

**FAQ** (Quick answers)
- "What is X?"
- "Where can I find Y?"
- Structure: Question → Short Answer → Details (optional)

**Reference** (Comprehensive documentation)
- "API documentation"
- "Feature overview"
- Structure: Overview → Details → Examples → Notes

**Announcement** (New features, changes)
- "Introducing feature X"
- "Changes to pricing"
- Structure: Summary → What's New → How to Use → Migration Guide

Auto-detect article type based on content.

## 3. Generate Article Content

Create comprehensive KB article:

\`\`\`markdown
# [Article Title - Clear, Descriptive, 50-70 chars]

**Last Updated**: [Date]
**Difficulty**: [Beginner/Intermediate/Advanced]
**Est. Time**: [X minutes]

## Overview

[2-3 sentence summary of what this article covers]

## Prerequisites

- [Item 1 - What you need before starting]
- [Item 2 - Required access/permissions]
- [Item 3 - Tools needed]

## Step-by-Step Instructions

### Step 1: [Action Title]

[Clear explanation of what to do]

\\\`\\\`\\\`
[Code example or screenshot]
\\\`\\\`\\\`

**Expected Result**: [What should happen]

### Step 2: [Next Action]

[Detailed instructions]

**Tip**: [Helpful hint or best practice]

### Step 3: [Final Action]

[Instructions]

**Warning**: [Common mistake to avoid]

## Verification

How to confirm it worked:
1. [Check 1]
2. [Check 2]
3. [Check 3]

## Troubleshooting

**Problem**: [Common issue]
**Solution**: [How to fix]

**Problem**: [Another issue]
**Solution**: [How to fix]

## Related Articles

- [Link to related article 1]
- [Link to related article 2]
- [Link to related article 3]

## Still Need Help?

If this article didn't solve your problem:
- [Contact support](mailto:support@example.com)
- [Submit a ticket](/support/ticket)
- [Join community forum](https://community.example.com)

---
**Helpful?** [👍 Yes](#) [👎 No](#)
\`\`\`

## 4. SEO Optimization

Optimize article for search:

**Title Optimization**:
- Include primary keyword
- 50-70 characters
- Clear and descriptive
- Action-oriented for how-tos

**Good**: "How to Reset Your Password in 3 Easy Steps"
**Bad**: "Password Reset"

**Meta Description** (155 chars):
- Summarize article content
- Include target keywords
- Compelling call-to-action

**Headings (H2, H3)**:
- Use keyword variations
- Descriptive and scannable
- Logical hierarchy

**Internal Linking**:
- Link to related articles
- Use descriptive anchor text
- 3-5 related links per article

**Keywords to Include**:
\`\`\`javascript
// Extract keywords from ticket/topic
const keywords = extractKeywords(\${CONTENT});
// Example: ["password reset", "account access", "login", "forgot password"]

// Use naturally throughout article:
// - In title
// - In first paragraph
// - In headings
// - In image alt text
\`\`\`

## 5. Add Visuals

**Screenshots**:
- Annotated with arrows/highlights
- Compressed for fast loading
- Alt text for accessibility
- Numbered to match steps

**Diagrams**:
- Workflow diagrams (Mermaid)
- Architecture diagrams
- Process flows

**Videos** (optional):
- Screen recordings for complex tasks
- < 3 minutes per video
- Captions for accessibility

**Code Blocks**:
- Syntax highlighting
- Copy button
- Language specified

## 6. Categorize and Tag

**Categories**:
- Getting Started
- Account Management
- Billing & Payments
- Integrations
- Troubleshooting
- API & Development
- Security & Privacy

**Tags** (5-10 per article):
- Primary feature tags
- Use case tags
- Problem tags
- Platform tags (web, mobile, API)

Auto-generate tags from content:
\`\`\`javascript
const tags = generateTags(\${CONTENT});
// Example: ["password", "reset", "login", "security", "account", "web"]
\`\`\`

## 7. Create in Zoho Desk

\`\`\`bash
# Create KB article in Zoho Desk
curl "https://desk.zoho.com/api/v1/articles" \\
  -X POST \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "'\${ARTICLE_TITLE}'",
    "category": "'\${CATEGORY}'",
    "answer": "'\${ARTICLE_CONTENT_HTML}'",
    "keywords": ["'\${TAG1}'", "'\${TAG2}'", "'\${TAG3}'"],
    "locale": "en",
    "status": "Draft",
    "authorId": "'\${AUTHOR_ID}'",
    "seoTitle": "'\${SEO_TITLE}'",
    "seoDescription": "'\${SEO_DESCRIPTION}'"
  }'

echo "✓ KB article created: \${ARTICLE_ID}"
echo "Preview: https://desk.zoho.com/support/kb/articles/\${ARTICLE_ID}"
\`\`\`

## 8. Quality Checklist

Before publishing:

**Content Quality**:
- [ ] Clear, concise language (8th grade reading level)
- [ ] Steps are numbered and sequential
- [ ] Screenshots/diagrams included where helpful
- [ ] Code examples tested and working
- [ ] All links functional
- [ ] No jargon without explanation

**Completeness**:
- [ ] Prerequisites listed
- [ ] All steps included
- [ ] Verification section included
- [ ] Troubleshooting section included
- [ ] Related articles linked

**SEO**:
- [ ] Title includes primary keyword
- [ ] Meta description written (155 chars)
- [ ] Headings use keyword variations
- [ ] Internal links added (3-5)
- [ ] Alt text on all images

**Accessibility**:
- [ ] Headings in logical order (H1 → H2 → H3)
- [ ] Alt text on images
- [ ] Sufficient color contrast
- [ ] Links descriptive (not "click here")
- [ ] Code blocks have language specified

**Technical**:
- [ ] Grammar and spelling checked
- [ ] Consistent formatting
- [ ] Mobile-friendly
- [ ] Fast page load (< 2s)

## 9. Get Approval

Show preview to reviewer:

Use AskUserQuestion:
- Option 1: "Publish now" → Publish to help center
- Option 2: "Save as draft" → Keep in draft, iterate
- Option 3: "Request changes" → Show what needs fixing

## 10. Publish and Promote

### Publish to Zoho Desk

\`\`\`bash
# Update article status to Published
curl "https://desk.zoho.com/api/v1/articles/\${ARTICLE_ID}" \\
  -X PATCH \\
  -H "Authorization: Zoho-oauthtoken \${ZOHO_DESK_TOKEN}" \\
  -d '{"status": "Published"}'

echo "✓ Article published"
\`\`\`

### Promote Article

**Email to Customers** (if major update):
\`\`\`markdown
Subject: New Help Article: \${ARTICLE_TITLE}

Hi there,

We just published a new help article that might be useful:

**\${ARTICLE_TITLE}**

Learn how to: [Brief description]

[Read Article]

This article was created based on feedback from customers like you. Let us know if it's helpful!

Best,
Support Team
\`\`\`

**Share Internally** (Slack):
\`\`\`
📚 New KB Article Published

Title: \${ARTICLE_TITLE}
Category: \${CATEGORY}
URL: \${ARTICLE_URL}

Now live in help center. Share with customers who ask about this!
\`\`\`

**Link from Related Tickets**:
\`\`\`bash
# Add KB article link to similar open tickets
# Helps resolve tickets faster
\`\`\`

## 11. Track Performance

**Metrics to Monitor**:
- Page views (weekly/monthly)
- Helpfulness votes (👍 / 👎)
- Time on page
- Bounce rate
- Search rankings (for target keywords)
- Ticket deflection (did it reduce tickets?)

**Update Schedule**:
- Review quarterly
- Update if process changes
- Refresh screenshots if UI changes
- Add new troubleshooting as discovered

## 12. Generate Article Report

\`\`\`markdown
# KB Article Created

**Title**: \${ARTICLE_TITLE}
**Article ID**: #\${ARTICLE_ID}
**Created**: \${DATE}
**Author**: \${AUTHOR_NAME}

## Article Details

**Category**: \${CATEGORY}
**Tags**: \${TAGS.join(', ')}
**Type**: \${ARTICLE_TYPE}
**Reading Time**: \${READING_TIME} minutes
**Difficulty**: \${DIFFICULTY}

## Content Summary

**Word Count**: \${WORD_COUNT}
**Screenshots**: \${SCREENSHOT_COUNT}
**Code Examples**: \${CODE_BLOCK_COUNT}
**Internal Links**: \${LINK_COUNT}

## SEO

**Title**: \${SEO_TITLE} (\${SEO_TITLE.length} chars)
**Meta Description**: \${SEO_DESCRIPTION} (\${SEO_DESCRIPTION.length} chars)
**Primary Keywords**: \${PRIMARY_KEYWORDS.join(', ')}
**Target Search Terms**: \${SEARCH_TERMS.join(', ')}

## Quality Score: \${QUALITY_SCORE}/100

**Breakdown**:
- Content clarity: [\${CLARITY_SCORE}/25]
- Completeness: [\${COMPLETENESS_SCORE}/25]
- SEO optimization: [\${SEO_SCORE}/25]
- Visual aids: [\${VISUAL_SCORE}/15]
- Accessibility: [\${A11Y_SCORE}/10]

## Publication

**Status**: Published
**URL**: \${ARTICLE_URL}
**Preview**: https://desk.zoho.com/support/kb/articles/\${ARTICLE_ID}

## Promotion

- [ ] Email sent to customers (if applicable)
- [ ] Shared in Slack
- [ ] Linked from related tickets
- [ ] Added to onboarding sequence (if relevant)

## Performance Tracking

**Expected Impact**:
- Ticket deflection: Reduce \${RELATED_TICKET_TYPE} tickets by 20-30%
- Search traffic: 50-100 views/month
- Helpfulness: > 80% positive votes

**Review Date**: \${REVIEW_DATE} (3 months from now)

---
Edit article: https://desk.zoho.com/support/kb/articles/\${ARTICLE_ID}/edit
\`\`\`

Save to: support-kb/kb-article-\${ARTICLE_ID}-\${DATE}.md

Also save article content to: support-kb/articles/\${ARTICLE_SLUG}.md
  `
})
```

## Usage Examples

```bash
# Generate KB from resolved ticket
/support/knowledge-base --from-ticket 12345

# Create new article from scratch
/support/knowledge-base --topic "How to integrate with Stripe API"

# Generate in markdown format (for local storage)
/support/knowledge-base --topic "Setting up SSO" --format markdown

# Generate in HTML format (for external help center)
/support/knowledge-base --from-ticket 67890 --format html
```

## Article Types Generated

**How-To Guides**: Step-by-step instructions

- "How to reset your password"
- "How to set up two-factor authentication"
- "How to export your data"

**Troubleshooting**: Problem resolution

- "Why can't I login?"
- "Error: Invalid API key"
- "Payment failed - what to do"

**FAQ**: Quick answers

- "What is the difference between Pro and Enterprise?"
- "How much does it cost?"
- "Is my data secure?"

**Reference**: Comprehensive docs

- "API documentation"
- "Webhook events reference"
- "Pricing calculator guide"

## Success Criteria

- ✓ Article content generated (clear, concise, complete)
- ✓ SEO optimized (title, meta, keywords)
- ✓ Properly categorized and tagged
- ✓ Visuals included (screenshots, diagrams, code)
- ✓ Quality score > 80/100
- ✓ Accessibility compliant
- ✓ Published to Zoho Desk (or saved as markdown/HTML)
- ✓ Performance tracking configured
- ✓ Article report saved
- ✓ Expected ticket deflection: 20-30%

## ROI Calculation

**Without KB Articles**:

- 100 tickets/month about topic X
- 15 min average handling time per ticket
- Cost: 100 × 15 min = 25 hours/month

**With KB Article**:

- 30% ticket deflection (customers find answer)
- 70 tickets/month (30 self-served)
- Cost: 70 × 15 min = 17.5 hours/month
- **Savings**: 7.5 hours/month per article

**Total Impact** (with 50 articles):

- 50 articles × 7.5 hours = 375 hours/month saved
- At $50/hour = $18,750/month
- **Annual Savings**: $225,000

---
**Uses**: frontend-architect, documentation-expert-agent
**Output**: Published KB article + performance tracking
**Next Commands**: `/support/autorespond` (use KB in auto-responses)
**Metrics**: 20-30% ticket deflection per article
