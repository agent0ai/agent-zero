---
description: Auto-optimize meta tags, headings, images, and content for SEO with one-click fixes and detailed recommendations
argument-hint: [--target <page|site>] [--auto-apply] [--focus <technical|content|both>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Edit, Bash
---

SEO Optimization: **${ARGUMENTS}**

## Auto-Optimizing SEO Elements

Use the Task tool with subagent_type=seo-specialist to automatically optimize your website for search engines with the following specifications:

### Input Parameters

**Target**: ${TARGET:-site} (single page or entire site)
**Auto-Apply**: ${AUTO_APPLY:-false} (preview changes vs auto-apply)
**Focus**: ${FOCUS:-both} (technical, content, or both)
**Backup**: ${BACKUP:-true} (create backup before changes)

### Objectives

You are tasked with automatically optimizing SEO elements across your website. Your implementation must:

#### 1. Meta Tag Optimization

**Title Tag Optimization**:

```javascript
// Current title analysis and optimization
const optimizeTitle = (currentTitle, page) => {
  const analysis = {
    current: "Blog Post",
    issues: [
      "Too generic - no keywords",
      "Too short (9 chars, should be 50-60)",
      "No branding",
      "Not unique (used on 12 pages)"
    ],

    optimized: "Complete Guide to Project Management Software 2024 | CompanyName",

    improvements: {
      length: "9 → 62 characters ✅",
      keywords: "None → 3 target keywords ✅",
      branding: "Missing → Added ✅",
      uniqueness: "Duplicate → Unique ✅"
    },

    seoImpact: "+15 points (45 → 60/100)",
    ctrImpact: "+2.5% click-through rate (estimated)"
  };

  return analysis;
};

// Title tag formula
const generateTitle = (page) => {
  const { primaryKeyword, secondaryKeyword, brand } = page;

  // Homepage
  if (page.isHomepage) {
    return `${primaryKeyword} | ${secondaryKeyword} - ${brand}`;
    // Example: "Project Management Software | Team Collaboration Tools - Acme"
  }

  // Blog posts
  if (page.isBlog) {
    return `${page.headline} [${new Date().getFullYear()}] | ${brand}`;
    // Example: "10 Best PM Tools for Remote Teams [2024] | Acme"
  }

  // Product pages
  if (page.isProduct) {
    return `${page.productName} - ${primaryKeyword} | ${brand}`;
    // Example: "Premium Plan - Enterprise Project Management | Acme"
  }

  // Category pages
  if (page.isCategory) {
    return `${page.categoryName}: ${primaryKeyword} (${page.itemCount}) | ${brand}`;
    // Example: "Templates: Project Management Templates (50+) | Acme"
  }
};
```

**Meta Description Optimization**:

```javascript
const optimizeMetaDescription = (page) => {
  const analysis = {
    current: null,  // Missing

    optimized: "Discover the best project management software for 2024. Compare features, pricing, and user reviews. Free 14-day trial. No credit card required. Join 10,000+ teams.",

    formula: {
      hook: "Discover the best project management software for 2024",  // 0-60 chars
      value: "Compare features, pricing, and user reviews",  // Value proposition
      cta: "Free 14-day trial. No credit card required",  // Call-to-action
      social_proof: "Join 10,000+ teams"  // Credibility
    },

    length: 155,  // characters (optimal: 150-160)

    improvements: {
      existence: "Missing → Added ✅",
      keywords: "0 → 3 keywords ✅",
      cta: "None → 2 CTAs ✅",
      persuasiveness: "N/A → High ✅"
    },

    ctrImpact: "+3.5% (from search results)"
  };

  return analysis;
};
```

**Open Graph & Twitter Cards**:

```html
<!-- Before: Missing social meta tags -->

<!-- After: Complete social optimization -->
<!-- Open Graph -->
<meta property="og:title" content="Complete Guide to Project Management Software 2024">
<meta property="og:description" content="Compare the top 10 PM tools. Features, pricing, pros & cons. Free trial available.">
<meta property="og:image" content="https://example.com/images/og-pm-guide.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="article">
<meta property="og:url" content="https://example.com/guides/pm-software">
<meta property="og:site_name" content="CompanyName">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Complete Guide to Project Management Software 2024">
<meta name="twitter:description" content="Compare the top 10 PM tools. Features, pricing, pros & cons.">
<meta name="twitter:image" content="https://example.com/images/twitter-pm-guide.jpg">
<meta name="twitter:site" content="@companyname">

<!-- Impact: Better social sharing, +15% social traffic -->
```

#### 2. Heading Structure Optimization

**Heading Hierarchy Fix**:

```html
<!-- Before: Poor structure -->
<h1>Welcome</h1>
<h3>Features</h3>  <!-- ❌ Skipped H2 -->
<h3>Task Management</h3>
<h2>Pricing</h2>
<h1>Get Started</h1>  <!-- ❌ Multiple H1s -->

<!-- After: Logical hierarchy -->
<h1>Project Management Made Simple</h1>
  <h2>Features</h2>
    <h3>Task Management</h3>
    <h3>Team Collaboration</h3>
    <h3>Reporting</h3>
  <h2>Pricing</h2>
    <h3>Plans Comparison</h3>
  <h2>Get Started</h2>
    <h3>Free Trial</h3>
```

**Keyword Optimization in Headings**:

```javascript
const optimizeHeadings = (headings, targetKeywords) => {
  return headings.map(h => {
    // Current: Generic headings without keywords
    if (h.text === "Features" && h.level === 2) {
      return {
        original: "Features",
        optimized: "Project Management Features",
        reasoning: "Added primary keyword",
        impact: "+5 relevance score"
      };
    }

    if (h.text === "Learn More" && h.level === 2) {
      return {
        original: "Learn More",
        optimized: "How Project Management Software Works",
        reasoning: "Specific, keyword-rich, descriptive",
        impact: "+8 relevance score"
      };
    }

    return h;
  });
};
```

#### 3. Content Optimization

**Keyword Density & Placement**:

```javascript
const optimizeContent = (content, keywords) => {
  const analysis = {
    primaryKeyword: "project management software",

    current: {
      density: 0.3,  // Too low
      firstParagraph: false,  // ❌ Not in intro
      h1: false,  // ❌ Not in H1
      metaTitle: false,  // ❌ Not in title
      url: false  // ❌ Not in URL
    },

    optimized: {
      density: 1.8,  // ✅ Optimal (1-2%)
      firstParagraph: true,  // ✅ Added to intro
      h1: true,  // ✅ Added to H1
      metaTitle: true,  // ✅ Added to title
      url: true,  // ✅ Suggested URL update

      placements: [
        "First 100 words",
        "H1 heading",
        "H2 heading (1-2 times)",
        "Image alt text (2 times)",
        "Meta title",
        "Meta description",
        "Conclusion paragraph"
      ]
    },

    lsiKeywords: [
      "PM tools",
      "team collaboration",
      "task management",
      "project tracking",
      "workflow automation",
      "agile methodology",
      "kanban boards",
      "gantt charts"
    ],

    lsiAdded: 6  // Added 6 LSI keywords naturally
  };

  return analysis;
};
```

**Content Enhancement**:

```markdown
## Content Quality Improvements

### Before:
**Word Count**: 450 words
**Readability**: 45 (Difficult)
**Images**: 1
**Internal Links**: 2
**External Links**: 0

### After:
**Word Count**: 1,850 words (+311%)
**Readability**: 68 (Easy)
**Images**: 8 (+700%)
**Internal Links**: 12 (+500%)
**External Links**: 5 (authoritative sources)

### Enhancements Made:

1. **Expanded Introduction** (50 → 200 words)
   - Added hook and value proposition
   - Included primary keyword in first 100 words
   - Added clear article outline

2. **Added Comprehensive Sections**:
   - "What is Project Management Software?" (300 words)
   - "Top Features to Look For" (400 words)
   - "How to Choose the Right Tool" (350 words)
   - "Implementation Best Practices" (300 words)
   - "Common Challenges & Solutions" (250 words)

3. **Improved Readability**:
   - Shorter paragraphs (3-4 sentences max)
   - Bullet points and numbered lists
   - Subheadings every 200-300 words
   - Bold key phrases
   - Added examples and case studies

4. **Added Visual Elements**:
   - Feature comparison table
   - Screenshots of interfaces
   - Infographic: "PM Software Selection Process"
   - Video: "5-Minute Product Tour"
   - Before/After team productivity chart

5. **Enhanced Internal Linking**:
   - Link to related blog posts (5 links)
   - Link to product pages (3 links)
   - Link to case studies (2 links)
   - Link to pricing page (2 links)

6. **Added External Authority Links**:
   - Link to industry studies
   - Link to reputable sources
   - Link to complementary tools
   - Proper nofollow on commercial links
```

#### 4. Image Optimization

**Automated Image SEO**:

```javascript
const optimizeImages = async (images) => {
  const optimizations = [];

  for (const img of images) {
    const optimization = {
      src: img.src,

      // Alt text generation
      altText: {
        before: null,  // Missing
        after: "Project management dashboard showing task kanban board with team assignments and progress tracking",
        method: "AI-generated from image content + page context"
      },

      // File name optimization
      filename: {
        before: "IMG_1234.jpg",  // ❌ Non-descriptive
        after: "project-management-dashboard-kanban-board.jpg",  // ✅ SEO-friendly
        suggestion: "Rename file before upload"
      },

      // Size optimization
      fileSize: {
        before: 850,  // KB
        after: 145,  // KB
        reduction: "83%",
        method: "WebP conversion + compression"
      },

      // Format optimization
      format: {
        before: "JPG",
        after: "WebP",
        fallback: "JPG for older browsers"
      },

      // Responsive images
      srcset: `
        project-management-dashboard-480w.webp 480w,
        project-management-dashboard-800w.webp 800w,
        project-management-dashboard-1200w.webp 1200w
      `,

      // Lazy loading
      loading: "lazy",

      // Dimensions (prevent CLS)
      dimensions: {
        width: 1200,
        height: 675,
        aspectRatio: "16/9"
      },

      // Structured data
      schema: {
        "@type": "ImageObject",
        "url": "https://example.com/images/pm-dashboard.webp",
        "width": 1200,
        "height": 675,
        "caption": "Project management dashboard interface"
      }
    };

    optimizations.push(optimization);
  }

  return optimizations;
};

// Auto-generate alt text using AI
const generateAltText = (imageSrc, pageContext) => {
  const imageAnalysis = analyzeImage(imageSrc);  // Using AI vision
  const contextKeywords = pageContext.keywords;

  return `${imageAnalysis.description} - ${contextKeywords.join(', ')}`;
  // Example: "Modern project dashboard interface - task management, team collaboration, progress tracking"
};
```

#### 5. Internal Linking Optimization

**Smart Internal Link Suggestions**:

```javascript
const generateInternalLinks = (currentPage, sitemap) => {
  const suggestions = [
    {
      from: currentPage.url,
      to: "/features/task-management",
      anchorText: "task management features",
      context: "Learn more about our advanced task management features including...",
      relevance: 95,
      reasoning: "Highly relevant to current page topic",
      placement: "After paragraph 3 (natural context)"
    },
    {
      from: currentPage.url,
      to: "/blog/pm-best-practices",
      anchorText: "project management best practices",
      context: "Following project management best practices can improve...",
      relevance: 88,
      reasoning: "Supports current topic, adds value",
      placement: "In 'Implementation' section"
    },
    {
      from: currentPage.url,
      to: "/case-studies/tech-startup",
      anchorText: "see how TechCorp increased productivity by 40%",
      context: "Real results speak louder than features - see how TechCorp...",
      relevance: 82,
      reasoning: "Social proof, related industry",
      placement: "Before conclusion"
    }
  ];

  return suggestions;
};

// Detect orphan pages and suggest links
const findOrphanPages = (sitemap) => {
  return sitemap.pages.filter(page => page.internalLinks === 0);
  // Create linking opportunities for orphan pages
};
```

#### 6. URL Structure Optimization

**SEO-Friendly URLs**:

```javascript
const optimizeUrl = (currentUrl, page) => {
  return {
    current: "/blog/post.php?id=123&cat=5",

    optimized: "/blog/project-management-software-guide-2024",

    improvements: {
      structure: "Dynamic → Static ✅",
      keywords: "None → 3 keywords ✅",
      readability: "Poor → Excellent ✅",
      length: "Optimal (< 60 chars) ✅",
      specialChars: "Removed (&, ?, =) ✅",
      hyphens: "Used for word separation ✅"
    },

    rules: [
      "Use hyphens (-) not underscores (_)",
      "Lowercase only",
      "Include primary keyword",
      "Keep under 60 characters",
      "No stop words (a, the, and, etc.)",
      "Descriptive and human-readable"
    ],

    301Redirect: {
      from: "/blog/post.php?id=123",
      to: "/blog/project-management-software-guide-2024",
      preserve: "link juice and rankings"
    }
  };
};
```

#### 7. Automated Optimization Script

**One-Click SEO Optimization**:

```javascript
// Comprehensive SEO optimization script
const autoOptimizeSEO = async (options) => {
  const { target, autoApply, backup } = options;

  // Step 1: Backup original files
  if (backup) {
    await createBackup(target);
  }

  // Step 2: Scan and analyze
  const analysis = await analyzePage(target);

  // Step 3: Generate optimizations
  const optimizations = {
    metaTags: await optimizeMetaTags(analysis),
    headings: await optimizeHeadings(analysis),
    content: await enhanceContent(analysis),
    images: await optimizeImages(analysis),
    internalLinks: await addInternalLinks(analysis),
    urls: await optimizeUrls(analysis)
  };

  // Step 4: Preview or apply changes
  if (autoApply) {
    await applyOptimizations(optimizations);
    return { status: "applied", optimizations };
  } else {
    return { status: "preview", optimizations };
  }
};

// Generate optimization report
const generateReport = (before, after) => {
  return {
    summary: {
      totalChanges: 47,
      categoriesOptimized: 6,
      estimatedImpact: "+25% organic traffic",
      timeToImplement: "15 minutes (automated)"
    },

    changes: {
      metaTags: {
        titleTags: "8 updated",
        metaDescriptions: "12 added, 3 updated",
        openGraph: "15 pages added",
        impact: "+3.5% CTR"
      },

      headings: {
        h1Fixed: "6 pages",
        hierarchyFixed: "12 pages",
        keywordsAdded: "18 headings",
        impact: "+8 relevance score"
      },

      content: {
        wordsAdded: "4,200 words",
        lsiKeywordsAdded: 45,
        readabilityImproved: "12 pages",
        impact: "+15% rankings"
      },

      images: {
        altTextAdded: "34 images",
        filesOptimized: "28 images",
        sizeSaved: "2.4 MB",
        impact: "+12 image search traffic"
      },

      internalLinks: {
        linksAdded: 56,
        orphanPagesFixed: 8,
        impact: "+10% pageviews per session"
      },

      urls: {
        urlsOptimized: 5,
        redirectsCreated: 5,
        impact: "+5% clickthrough from search"
      }
    },

    seoScoreChange: {
      before: 62,
      after: 87,
      improvement: "+25 points"
    }
  };
};
```

### Implementation Steps

**Step 1: Analysis**

1. Scan target pages or entire site
2. Identify optimization opportunities
3. Prioritize by impact
4. Estimate implementation time

**Step 2: Generate Optimizations**

1. Create optimized meta tags
2. Restructure headings
3. Enhance content
4. Optimize images
5. Add internal links
6. Suggest URL improvements

**Step 3: Preview Changes**

1. Show before/after comparison
2. Highlight impact of each change
3. Allow selective application
4. Provide rollback option

**Step 4: Apply Changes** (if auto-apply)

1. Create backup
2. Update files
3. Verify changes
4. Generate report

**Step 5: Monitor Results**

1. Track rankings
2. Monitor traffic
3. Measure engagement
4. Report on ROI

### Output Requirements

**Generated Files**:

- `SEO_OPTIMIZATION_PREVIEW.html` - Before/after comparison
- `optimizations.json` - All proposed changes
- `backup/` - Original files backup
- `SEO_OPTIMIZATION_REPORT.md` - Impact report

## ROI Impact

**Organic Traffic Growth**:

- **+25% traffic** from on-page optimization
- **+3.5% CTR** from meta tag improvements
- **+15% rankings** from content enhancements

**Conversion Improvements**:

- **Better user experience** from improved content
- **Higher engagement** from internal linking
- **More time on site** from quality content

**Time Savings**:

- **Manual optimization**: 40 hours → 15 minutes (automated)
- **Continuous monitoring**: Automated tracking
- **Scalable**: Optimize 100s of pages instantly

**Total Value**: $75,000/year

- Incremental traffic: $50,000/year
- Improved conversions: $15,000/year
- Time savings: $10,000/year

## Success Criteria

✅ **All pages optimized**
✅ **Meta tags complete and unique**
✅ **Heading structure logical**
✅ **Images have alt text and optimized**
✅ **Internal linking improved**
✅ **SEO score increased >20 points**

**Quality Targets**:

- Title tags: 50-60 characters, unique
- Meta descriptions: 150-160 characters
- H1: Single, keyword-rich per page
- Images: 100% with alt text
- Content: >1000 words for key pages

## Next Steps

1. Review optimization preview
2. Select changes to apply
3. Apply optimizations
4. Monitor impact (30 days)
5. Iterate and improve

---

**Optimization Status**: 🟢 Ready to Apply
**Est. SEO Score Improvement**: +25 points
**Annual ROI**: $75,000
