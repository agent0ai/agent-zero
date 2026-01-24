---
description: Optimize content for AI-powered search engines (ChatGPT, Claude, Perplexity, Google SGE)
argument-hint: [--page <path>] [--ai-engines <chatgpt|claude|perplexity|sge|all>] [--preview]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# AI Search Optimization Command

Optimize your content for AI-powered search engines including ChatGPT, Claude, Perplexity, and Google's Search Generative Experience (SGE). This command analyzes your content and applies optimization strategies specifically designed for AI retrieval and citation.

## Overview

**Purpose**: Transform traditional SEO content into AI-friendly formats that maximize citation probability in AI-generated responses.

**Key Difference from Traditional SEO**:

- Traditional SEO: Optimize for rankings and click-through rates
- AI Search Optimization: Optimize for being cited, summarized, and attributed by AI

**Target AI Search Engines**:

1. **ChatGPT** (with Browse/Bing integration)
2. **Claude** (with web search capabilities)
3. **Perplexity** (AI-native search engine)
4. **Google SGE** (Search Generative Experience)
5. **Microsoft Bing Chat** (Copilot)

## When to Use This Command

Use `/ai-search/optimize` when you want to:

1. **Increase AI Citations**: Get your content cited in AI-generated responses
2. **Prepare for AI Search Era**: Future-proof content as search shifts to AI
3. **Answer-Focused Content**: Transform content to directly answer questions
4. **Authority Building**: Establish your site as a reliable source for AI engines
5. **Conversational Format**: Adapt content for natural language queries

## Command Syntax

```bash
# Optimize current page for all AI engines
/ai-search/optimize

# Optimize specific page
/ai-search/optimize --page src/pages/blog/post.html

# Target specific AI engine
/ai-search/optimize --ai-engines chatgpt

# Preview changes without applying
/ai-search/optimize --preview

# Optimize multiple pages
/ai-search/optimize --page "src/pages/**/*.html"

# Focus on specific content type
/ai-search/optimize --type article --ai-engines perplexity
```

## What This Command Does

### 1. Content Structure Analysis

**Analyzes Your Content For**:

- Question-answer pairs
- Clear, concise statements
- Source credibility markers
- Structured data presence
- Citation-worthy facts and statistics
- Conversational tone

**Example Analysis**:

```javascript
const contentAnalysis = {
  page: "blog/machine-learning-guide.html",
  currentState: {
    questionAnswerPairs: 3,
    directAnswers: 12,
    structuredData: ["Article"],
    statistics: 8,
    sources: 2,
    conversationalScore: 45, // Out of 100
    citationReadiness: 52    // Out of 100
  },
  aiSearchScore: 48, // Out of 100
  issues: [
    "Missing FAQ schema",
    "Answers buried in paragraphs",
    "No clear attribution for statistics",
    "Limited conversational phrasing"
  ]
};
```

### 2. AI-Optimized Content Transformation

**Applies These Optimizations**:

#### A. Direct Answer Formatting

```markdown
Before (Traditional SEO):
"Machine learning has become increasingly important in recent years.
Companies across industries are adopting ML technologies to improve
their operations..."

After (AI-Optimized):
**What is machine learning?**
Machine learning is a type of artificial intelligence that enables
computers to learn and improve from experience without being
explicitly programmed.

**Key benefits of machine learning:**
- Automates complex decision-making
- Identifies patterns in large datasets
- Improves accuracy over time
- Reduces human error
```

#### B. FAQ Schema Implementation

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the difference between supervised and unsupervised learning?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data. Supervised learning is used for classification and regression tasks, while unsupervised learning is used for clustering and dimensionality reduction."
      }
    },
    {
      "@type": "Question",
      "name": "How long does it take to train a machine learning model?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Training time varies from minutes to weeks depending on model complexity, dataset size, and computing resources. Simple models on small datasets can train in minutes, while deep learning models on large datasets may require days or weeks with GPU acceleration."
      }
    }
  ]
}
```

#### C. Statistical Attribution

```markdown
Before:
"Studies show that machine learning can reduce costs by up to 40%."

After:
"Machine learning can reduce operational costs by up to 40%
(Source: McKinsey Global Institute, 2023)."
```

#### D. Conversational Phrasing

```markdown
Before:
"The implementation of neural networks requires consideration of
various architectural parameters including layer depth, activation
functions, and optimization algorithms."

After:
"When you're building a neural network, you need to make three key
decisions: how many layers to include, which activation function to
use, and which optimization algorithm works best for your data."
```

### 3. AI Engine-Specific Optimization

**ChatGPT Optimization**:

- Concise, authoritative answers
- Clear section headings
- Numbered lists and steps
- Recent publication dates
- External source citations

**Claude Optimization**:

- Detailed explanations with context
- Balanced perspectives
- Ethical considerations
- Nuanced information
- Clear methodology descriptions

**Perplexity Optimization**:

- Fact-dense content
- Multiple viewpoints
- Strong source attribution
- Data-driven insights
- Comparison tables

**Google SGE Optimization**:

- Featured snippet format
- People Also Ask optimization
- Rich media integration
- Local context when relevant
- E-E-A-T signals (Experience, Expertise, Authoritativeness, Trust)

### 4. Citation Probability Enhancement

**Elements That Increase Citation Probability**:

```javascript
const citationEnhancers = {
  credibility: {
    authorBio: "Include author expertise and credentials",
    publicationDate: "Keep content fresh (updated within 12 months)",
    sources: "Link to authoritative primary sources",
    statistics: "Include specific, sourced data points"
  },

  structure: {
    clearHeadings: "Use descriptive H2/H3 headings with keywords",
    bulletPoints: "Break complex info into scannable lists",
    tables: "Present comparisons and data in tables",
    summaries: "Include TL;DR or key takeaways"
  },

  content: {
    directAnswers: "Answer questions in first 2 sentences",
    definitions: "Define technical terms clearly",
    examples: "Provide concrete examples",
    steps: "Present how-to content as numbered steps"
  },

  technical: {
    schema: "Implement FAQ, HowTo, Article schemas",
    metadata: "Optimize title and description for questions",
    semanticHTML: "Use proper HTML5 semantic elements",
    accessibility: "Ensure ARIA labels and alt text"
  }
};
```

### 5. Automated Content Restructuring

**Example Transformation**:

**Original Article**:

```html
<article>
  <h1>Understanding Neural Networks</h1>
  <p>Neural networks have revolutionized artificial intelligence.
  They consist of layers of interconnected nodes that process
  information...</p>

  <p>The history of neural networks dates back to the 1940s...</p>

  <p>In modern applications, neural networks are used for image
  recognition, natural language processing, and more...</p>
</article>
```

**AI-Optimized Article**:

```html
<article itemscope itemtype="https://schema.org/Article">
  <h1 itemprop="headline">Understanding Neural Networks: A Complete Guide</h1>

  <div class="quick-answer">
    <h2>What is a neural network?</h2>
    <p itemprop="abstract">A neural network is a machine learning model
    inspired by the human brain, consisting of layers of interconnected
    nodes (neurons) that process and learn from data to make predictions
    or decisions.</p>
  </div>

  <div itemscope itemtype="https://schema.org/FAQPage">
    <h2>Frequently Asked Questions</h2>

    <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
      <h3 itemprop="name">How do neural networks work?</h3>
      <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
        <p itemprop="text">Neural networks work in three steps:
          <ol>
            <li><strong>Input layer</strong>: Receives raw data</li>
            <li><strong>Hidden layers</strong>: Process and transform data through weighted connections</li>
            <li><strong>Output layer</strong>: Produces final predictions</li>
          </ol>
        </p>
      </div>
    </div>

    <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
      <h3 itemprop="name">What are neural networks used for?</h3>
      <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
        <p itemprop="text">Common applications include:
          <ul>
            <li>Image recognition (facial recognition, medical imaging)</li>
            <li>Natural language processing (chatbots, translation)</li>
            <li>Speech recognition (voice assistants)</li>
            <li>Recommendation systems (Netflix, Amazon)</li>
            <li>Autonomous vehicles (self-driving cars)</li>
          </ul>
        </p>
      </div>
    </div>
  </div>

  <section>
    <h2>Key Statistics</h2>
    <ul>
      <li>Neural networks can achieve 95%+ accuracy in image classification tasks
          (Source: ImageNet Challenge, 2023)</li>
      <li>The global AI market is projected to reach $190 billion by 2025
          (Source: Markets and Markets, 2023)</li>
    </ul>
  </section>

  <div class="author-bio" itemprop="author" itemscope itemtype="https://schema.org/Person">
    <p><strong itemprop="name">Dr. Sarah Johnson</strong>, PhD in Machine Learning,
    15 years of experience in neural network research at MIT and Google Brain.</p>
  </div>

  <meta itemprop="datePublished" content="2024-01-15">
  <meta itemprop="dateModified" content="2024-01-15">
</article>
```

### 6. Performance Metrics

**Tracks Optimization Results**:

```javascript
const optimizationResults = {
  before: {
    aiSearchScore: 48,
    citationProbability: 32,
    directAnswers: 12,
    faqSchemas: 0,
    sources: 2,
    conversationalTone: 45
  },

  after: {
    aiSearchScore: 87,  // +81% improvement
    citationProbability: 78,  // +144% improvement
    directAnswers: 28,  // +133% improvement
    faqSchemas: 3,      // New
    sources: 15,        // +650% improvement
    conversationalTone: 89  // +98% improvement
  },

  improvements: [
    "Added 3 FAQ schemas with 12 Q&A pairs",
    "Restructured 16 paragraphs into direct answer format",
    "Added source attribution to all statistics",
    "Converted 8 sections to conversational tone",
    "Created summary boxes for key concepts"
  ],

  estimatedImpact: {
    aiCitations: "+250% in first 3 months",
    organicTraffic: "+35% from AI-referred traffic",
    brandAuthority: "+40% citation as expert source"
  }
};
```

## Implementation Steps

When you run `/ai-search/optimize`, Claude Code will:

### Step 1: Analyze Current Content

```bash
# Scans your content for:
- Question-answer opportunities
- Unstructured information that could be FAQ
- Statistics without attribution
- Complex paragraphs that could be simplified
- Missing schema markup
- Conversational tone gaps
```

### Step 2: Generate Optimization Report

```markdown
# AI Search Optimization Report
Page: blog/machine-learning-guide.html
Current AI Search Score: 48/100

## Critical Issues (Fix First)
1. ❌ Missing FAQ schema - Add 3+ Q&A pairs
2. ❌ No source attribution for 8 statistics
3. ❌ Answers buried in long paragraphs

## High Priority
4. ⚠️  Limited conversational phrasing
5. ⚠️  No author credentials displayed
6. ⚠️  Missing structured data for article

## Optimization Opportunities
7. 💡 12 questions can be extracted from content
8. 💡 16 paragraphs can be reformatted as direct answers
9. 💡 5 sections can be converted to comparison tables

Estimated Time to Fix: 2-3 hours
Potential Citation Increase: +250%
```

### Step 3: Apply Optimizations

```bash
# Automatically or with preview:
- Adds FAQ schema markup
- Restructures content into Q&A format
- Adds source citations
- Converts to conversational tone
- Implements structured data
- Adds author credibility markers
```

### Step 4: Validate Changes

```bash
# Validates:
- Schema markup is valid
- All statistics have sources
- Questions are clearly formatted
- Answers are concise (<150 words)
- Conversational tone is maintained
- E-E-A-T signals are present
```

### Step 5: Generate Implementation Guide

```markdown
# Next Steps

## Immediate Actions (Do Today)
1. ✅ FAQ schema added to page
2. ✅ 16 sections restructured as direct answers
3. ✅ Source citations added to all statistics

## Manual Review Required
1. 📝 Review author bio for accuracy
2. 📝 Verify statistic sources are current
3. 📝 Ensure conversational tone matches brand voice

## Ongoing Optimization
1. 🔄 Update statistics quarterly
2. 🔄 Add new Q&A pairs based on search queries
3. 🔄 Monitor AI citation performance

## Testing
1. 🧪 Ask ChatGPT questions related to your content
2. 🧪 Search Perplexity for your topic keywords
3. 🧪 Check Google SGE for citation appearance
```

## AI Engine-Specific Strategies

### ChatGPT Optimization

```javascript
const chatgptStrategy = {
  focus: "Clear, authoritative answers",

  contentStructure: {
    openingSummary: "Provide TL;DR in first paragraph",
    headings: "Use question-based H2 headings",
    lists: "Prefer numbered lists for steps, bullets for features",
    length: "Aim for 150-300 words per answer"
  },

  credibility: {
    sources: "Link to .edu, .gov, and authoritative .com sites",
    dates: "Show last updated date prominently",
    author: "Display author credentials",
    statistics: "Use recent data (within 2 years)"
  },

  format: {
    paragraphs: "Keep to 2-3 sentences maximum",
    definitions: "Define technical terms in-line",
    examples: "Provide 1-2 concrete examples per concept"
  }
};
```

### Perplexity Optimization

```javascript
const perplexityStrategy = {
  focus: "Fact-dense, well-sourced content",

  contentStructure: {
    factDensity: "Aim for 1 fact per 25 words",
    citations: "Inline citations after each claim",
    comparisons: "Use tables for side-by-side comparisons",
    data: "Include charts and statistics"
  },

  sources: {
    diversity: "Cite 5+ different authoritative sources",
    recency: "Prefer sources from last 12 months",
    types: "Mix academic, news, and industry sources",
    quality: "Prioritize peer-reviewed and expert sources"
  },

  presentation: {
    headlines: "Specific, keyword-rich headings",
    summaries: "Key points box at top",
    depth: "Provide both quick answer and deep dive"
  }
};
```

### Google SGE Optimization

```javascript
const sgeStrategy = {
  focus: "Featured snippet + E-E-A-T signals",

  featuredSnippet: {
    format: "Paragraph (40-50 words) OR List (5-8 items) OR Table",
    position: "Answer question in first 2 sentences after H2",
    keywords: "Include question keywords in answer",
    completeness: "Provide full answer without needing to click"
  },

  eeat: {
    experience: "Share first-hand experience and case studies",
    expertise: "Display author credentials and qualifications",
    authoritativeness: "Link to and from authoritative sites",
    trust: "Show contact info, privacy policy, security badges"
  },

  technicalSEO: {
    schema: "Implement Article, FAQ, HowTo, Person schemas",
    coreWebVitals: "Ensure LCP <2.5s, FID <100ms, CLS <0.1",
    mobile: "Optimize for mobile-first indexing",
    https: "Ensure all content is HTTPS"
  }
};
```

## Output Examples

### Before Optimization

```html
<article>
  <h1>Cloud Computing Benefits</h1>
  <p>Cloud computing has transformed how businesses operate. Companies
  can now scale their infrastructure without massive upfront investments.
  The flexibility offered by cloud platforms enables rapid innovation
  and deployment.</p>

  <p>Cost savings are significant when moving to the cloud...</p>
</article>
```

### After Optimization

```html
<article itemscope itemtype="https://schema.org/Article">
  <h1 itemprop="headline">Cloud Computing Benefits: Complete Guide for Businesses</h1>

  <div class="quick-answer">
    <h2>What are the main benefits of cloud computing?</h2>
    <p itemprop="abstract">Cloud computing offers three primary benefits:
    <strong>cost reduction</strong> (30-50% lower IT costs),
    <strong>scalability</strong> (scale resources up or down instantly), and
    <strong>accessibility</strong> (access data from anywhere).
    (Source: Gartner Cloud Computing Survey, 2023)</p>
  </div>

  <div itemscope itemtype="https://schema.org/FAQPage">
    <h2>Cloud Computing FAQs</h2>

    <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
      <h3 itemprop="name">How much can businesses save with cloud computing?</h3>
      <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
        <p itemprop="text">Businesses typically save 30-50% on IT infrastructure
        costs by moving to the cloud. This includes reduced hardware purchases,
        lower maintenance costs, and decreased energy consumption. For example,
        a medium-sized company spending $500K/year on on-premise infrastructure
        can reduce costs to $250-350K with cloud migration.
        (Source: Forrester Total Economic Impact Study, 2023)</p>
      </div>
    </div>

    <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
      <h3 itemprop="name">What are the types of cloud computing?</h3>
      <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
        <p itemprop="text">There are three main types:
          <ol>
            <li><strong>Public Cloud</strong> (AWS, Azure, GCP): Shared infrastructure, pay-as-you-go</li>
            <li><strong>Private Cloud</strong>: Dedicated infrastructure for single organization</li>
            <li><strong>Hybrid Cloud</strong>: Combination of public and private clouds</li>
          </ol>
        </p>
      </div>
    </div>
  </div>

  <section>
    <h2>Cost Comparison Table</h2>
    <table>
      <thead>
        <tr>
          <th>Cost Factor</th>
          <th>On-Premise</th>
          <th>Cloud</th>
          <th>Savings</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Hardware</td>
          <td>$200K/year</td>
          <td>$0</td>
          <td>100%</td>
        </tr>
        <tr>
          <td>Maintenance</td>
          <td>$100K/year</td>
          <td>$0</td>
          <td>100%</td>
        </tr>
        <tr>
          <td>Computing Resources</td>
          <td>$200K/year</td>
          <td>$150K/year</td>
          <td>25%</td>
        </tr>
        <tr>
          <td><strong>Total</strong></td>
          <td><strong>$500K/year</strong></td>
          <td><strong>$150K/year</strong></td>
          <td><strong>70%</strong></td>
        </tr>
      </tbody>
    </table>
    <p><em>Source: Cloud Economics Report, McKinsey 2023</em></p>
  </section>

  <div class="author-bio" itemprop="author" itemscope itemtype="https://schema.org/Person">
    <img itemprop="image" src="/authors/james-chen.jpg" alt="James Chen">
    <p><strong itemprop="name">James Chen</strong>,
    <span itemprop="jobTitle">Cloud Architect</span> at
    <span itemprop="worksFor">Amazon Web Services</span>.
    12 years of experience helping Fortune 500 companies migrate to the cloud.</p>
  </div>

  <meta itemprop="datePublished" content="2024-01-10">
  <meta itemprop="dateModified" content="2024-01-15">
  <time itemprop="dateModified" datetime="2024-01-15">Last updated: January 15, 2024</time>
</article>
```

## Best Practices

### Content Guidelines

1. **Answer Questions Directly**
   - Put answer in first 1-2 sentences
   - Use clear, simple language
   - Avoid marketing fluff

2. **Use Conversational Tone**
   - Write as if explaining to a colleague
   - Use "you" and "your"
   - Include examples and analogies

3. **Provide Complete Information**
   - Don't force users to click for basic info
   - Include context and caveats
   - Explain technical terms

4. **Cite Your Sources**
   - Link to original research
   - Include publication dates
   - Prefer authoritative sources

5. **Keep Content Fresh**
   - Update statistics regularly
   - Add new Q&A pairs based on trends
   - Archive outdated information

### Technical Guidelines

1. **Implement Structured Data**

   ```json
   {
     "required": ["FAQPage", "Article"],
     "recommended": ["HowTo", "Person", "Organization"],
     "optional": ["Review", "Rating", "Video"]
   }
   ```

2. **Optimize Page Speed**
   - Core Web Vitals are ranking factors
   - Faster pages get cited more often
   - Target: LCP <2.5s, FID <100ms, CLS <0.1

3. **Ensure Mobile Optimization**
   - Most AI searches happen on mobile
   - Responsive design is essential
   - Touch targets minimum 44x44px

4. **Implement Proper HTML Semantics**

   ```html
   <main>
     <article>
       <header>
         <h1>Main heading</h1>
         <time datetime="2024-01-15">Jan 15, 2024</time>
       </header>
       <section>
         <h2>Section heading</h2>
         <!-- Content -->
       </section>
     </article>
   </main>
   ```

## Success Metrics

### AI Citation Metrics

```javascript
const successMetrics = {
  aiCitations: {
    target: "Appear in 15% of relevant AI searches",
    measurement: "Manual search tests + citation tracking tools",
    timeline: "3-6 months to see significant impact"
  },

  trafficFromAI: {
    target: "+35% traffic from AI-referred sources",
    measurement: "GA4 referral traffic from AI platforms",
    timeline: "2-4 months"
  },

  brandMentions: {
    target: "5x increase in brand mentions by AI",
    measurement: "Brand monitoring tools + manual testing",
    timeline: "4-6 months"
  },

  conversionRate: {
    target: "+20% conversion from AI-referred traffic",
    measurement: "Higher intent traffic from AI engines",
    timeline: "Immediate for existing traffic"
  }
};
```

### Content Quality Metrics

```javascript
const qualityMetrics = {
  aiSearchScore: {
    target: "85+/100",
    current: "48/100",
    improvement: "+77%"
  },

  directAnswers: {
    target: "25+ per page",
    current: "12 per page",
    improvement: "+108%"
  },

  faqCoverage: {
    target: "3+ FAQ schemas per page",
    current: "0",
    improvement: "New"
  },

  sourceAttribution: {
    target: "100% of statistics cited",
    current: "25%",
    improvement: "+300%"
  }
};
```

## ROI Calculation

### Time Savings

```javascript
const timeSavings = {
  manualOptimization: {
    timePerPage: "4-6 hours",
    automatedTime: "15 minutes",
    savings: "3.75-5.75 hours per page"
  },

  monthlyPages: {
    pages: 20,
    totalTimeSaved: "75-115 hours/month",
    costSavings: "$7,500-11,500/month @ $100/hour"
  },

  annualSavings: "$90,000-138,000/year"
};
```

### Revenue Impact

```javascript
const revenueImpact = {
  increasedTraffic: {
    currentMonthly: 50000,
    aiReferredIncrease: "+35%",
    newVisitors: 17500,
    conversionRate: "3%",
    avgOrderValue: "$150",
    monthlyRevenue: "$78,750",
    annualRevenue: "$945,000"
  },

  brandAuthority: {
    consultingLeads: "+20 per month",
    avgProjectValue: "$25,000",
    monthlyRevenue: "$125,000",
    annualRevenue: "$1,500,000"
  },

  totalAnnualImpact: "$2,445,000"
};
```

### Total ROI

```markdown
**Annual Investment**: $138,000 (time cost)
**Annual Return**: $2,445,000 (revenue impact)
**Net ROI**: 1,672% or **$2,307,000 net benefit**
```

## Troubleshooting

### Common Issues

**Issue**: AI engines don't cite my content

```markdown
**Diagnosis**:
- Check if content answers questions directly
- Verify FAQ schema is implemented correctly
- Ensure sources are recent and authoritative
- Confirm page loads in <3 seconds

**Fix**:
1. Add more Q&A formatted content
2. Validate schema with Google's Rich Results Test
3. Update statistics to within 12 months
4. Optimize Core Web Vitals
```

**Issue**: Conversion rate from AI traffic is low

```markdown
**Diagnosis**:
- AI-referred users expect quick answers
- May be research phase, not buying phase
- Content may not align with user intent

**Fix**:
1. Add clear next steps and CTAs
2. Provide downloadable resources (PDFs, checklists)
3. Include related articles for further reading
4. Implement chatbot for immediate assistance
```

**Issue**: Citations favor competitors

```markdown
**Diagnosis**:
- Competitors may have stronger E-E-A-T signals
- Their content may be more comprehensive
- They may have better source diversity

**Fix**:
1. Enhance author credentials display
2. Add expert quotes and interviews
3. Expand content with unique insights
4. Build backlinks from authoritative sites
```

## Advanced Features

### Multi-Language Optimization

```javascript
const multiLanguage = {
  strategy: "Optimize for AI search in each language",

  implementation: {
    hreflang: "Implement proper hreflang tags",
    localizedFAQ: "Create language-specific Q&A pairs",
    culturalContext: "Adapt examples for local audience",
    localSources: "Cite sources from target country"
  },

  aiEngines: {
    chatgpt: "Works well in 50+ languages",
    claude: "Excellent in English, Spanish, French, German, Japanese",
    perplexity: "Strong in major European and Asian languages"
  }
};
```

### Industry-Specific Optimization

```javascript
const industryOptimization = {
  healthcare: {
    focus: "Medical accuracy and credibility",
    required: "Cite medical journals and clinical studies",
    schema: ["MedicalWebPage", "MedicalCondition", "Drug"],
    compliance: "HIPAA-compliant, no PHI in examples"
  },

  finance: {
    focus: "Accuracy and regulatory compliance",
    required: "Disclaimer about financial advice",
    schema: ["FinancialProduct", "InvestmentOrDeposit"],
    compliance: "SEC regulations, risk disclosures"
  },

  ecommerce: {
    focus: "Product details and reviews",
    required: "Pricing, availability, specifications",
    schema: ["Product", "Review", "AggregateRating", "Offer"],
    optimization: "Comparison tables, feature lists"
  }
};
```

### Competitive Analysis

```javascript
const competitiveAnalysis = {
  analyzes: [
    "Which competitors are cited most often",
    "What content formats they use",
    "Their source diversity and quality",
    "FAQ coverage and depth",
    "Structured data implementation"
  ],

  output: {
    gapAnalysis: "Topics competitors cover that you don't",
    opportunities: "Questions they don't answer well",
    strategy: "Differentiation tactics",
    benchmark: "Your score vs. top 3 competitors"
  }
};
```

## Integration with Other Commands

### Works With

- `/seo/optimize` - Traditional SEO + AI search optimization
- `/seo/schema` - Structured data implementation
- `/content/generate` - AI-optimized content creation
- `/analytics/track` - Monitor AI citation performance

### Workflow Example

```bash
# 1. Traditional SEO audit
/seo/audit

# 2. Optimize for traditional search
/seo/optimize

# 3. Add AI search optimization
/ai-search/optimize

# 4. Implement structured data
/seo/schema --types FAQPage,Article

# 5. Monitor performance
/ai-search/monitor
```

## Command Implementation

```markdown
When you run this command, Claude Code will use the Task tool with subagent_type: "ai-search-optimizer" to:

1. **Analyze Content**
   - Read specified page(s)
   - Extract questions and answers
   - Identify optimization opportunities
   - Calculate current AI search score

2. **Generate Optimizations**
   - Create FAQ schema markup
   - Restructure content as direct answers
   - Add source citations
   - Convert to conversational tone
   - Implement E-E-A-T signals

3. **Apply Changes** (if --preview not used)
   - Update HTML with optimized content
   - Add structured data
   - Enhance credibility markers
   - Validate schema markup

4. **Report Results**
   - Before/after comparison
   - AI search score improvement
   - Estimated citation impact
   - Next steps and recommendations

Use `--preview` to see proposed changes before applying.
Use `--ai-engines` to optimize for specific platforms.
```

## Real-World Example

### E-commerce Product Page

**Before**:

```html
<h1>Premium Wireless Headphones</h1>
<p>Our headphones offer superior sound quality and comfort...</p>
```

**After**:

```html
<div itemscope itemtype="https://schema.org/Product">
  <h1 itemprop="name">Premium Wireless Headphones</h1>

  <div class="quick-specs">
    <h2>What makes these headphones special?</h2>
    <ul>
      <li><strong>40-hour battery life</strong> - Longest in class (Source: CNET, 2024)</li>
      <li><strong>Active noise cancellation</strong> - Blocks 99% of ambient noise</li>
      <li><strong>Premium comfort</strong> - Memory foam ear cups, only 220g</li>
    </ul>
  </div>

  <div itemscope itemtype="https://schema.org/FAQPage">
    <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
      <h3 itemprop="name">How long does the battery last?</h3>
      <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
        <p itemprop="text">Up to 40 hours with ANC on, 60 hours with ANC off.
        Charges fully in 2.5 hours via USB-C, or get 5 hours of playback from
        a 10-minute quick charge.</p>
      </div>
    </div>
  </div>

  <div itemprop="aggregateRating" itemscope itemtype="https://schema.org/AggregateRating">
    <span itemprop="ratingValue">4.8</span>/5 stars
    (<span itemprop="reviewCount">2,847</span> reviews)
  </div>
</div>
```

**Result**: Product appears in ChatGPT recommendations, Perplexity comparisons, and Google SGE shopping results.

---

**Ready to optimize for AI search?** Run `/ai-search/optimize` to transform your content for the AI-powered search era.
