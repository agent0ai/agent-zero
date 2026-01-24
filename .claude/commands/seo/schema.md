---
description: Generate and implement Schema.org structured data (JSON-LD) for rich snippets and enhanced search results
argument-hint: [--type <auto|organization|article|product|faq|breadcrumb>] [--validate]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, WebFetch, Bash
---

SEO Schema Markup: **${ARGUMENTS}**

## Generating Schema.org Structured Data

Use the Task tool with subagent_type=seo-specialist to generate comprehensive schema markup with the following specifications:

### Input Parameters

**Schema Type**: ${TYPE:-auto} (Auto-detect or specify type)
**Validate**: ${VALIDATE:-true} (Validate with Google's testing tool)
**Multiple Types**: ${MULTIPLE:-true} (Combine multiple schema types)

### Objectives

You are tasked with generating proper Schema.org structured data to enhance search engine understanding and enable rich snippets. Your implementation must:

#### 1. Schema Type Detection & Generation

**Organization Schema**:

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Acme Inc",
  "legalName": "Acme Incorporated",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "foundingDate": "2015",
  "founders": [
    {
      "@type": "Person",
      "name": "Jane Doe"
    }
  ],
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "San Francisco",
    "addressRegion": "CA",
    "postalCode": "94102",
    "addressCountry": "US"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-415-555-0123",
    "contactType": "customer service",
    "email": "support@example.com",
    "areaServed": "US",
    "availableLanguage": ["en", "es"]
  },
  "sameAs": [
    "https://www.facebook.com/acmeinc",
    "https://www.twitter.com/acmeinc",
    "https://www.linkedin.com/company/acme-inc",
    "https://www.instagram.com/acmeinc"
  ]
}
```

**Article Schema** (Blog Posts):

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Complete Guide to Project Management Software 2024",
  "alternativeHeadline": "How to Choose the Best PM Tool for Your Team",
  "image": [
    "https://example.com/images/article-16x9.jpg",
    "https://example.com/images/article-4x3.jpg",
    "https://example.com/images/article-1x1.jpg"
  ],
  "datePublished": "2024-01-15T08:00:00+00:00",
  "dateModified": "2024-11-15T14:30:00+00:00",
  "author": {
    "@type": "Person",
    "name": "John Smith",
    "url": "https://example.com/authors/john-smith",
    "image": "https://example.com/authors/john-smith.jpg",
    "jobTitle": "Senior Product Manager",
    "sameAs": [
      "https://twitter.com/johnsmith",
      "https://linkedin.com/in/johnsmith"
    ]
  },
  "publisher": {
    "@type": "Organization",
    "name": "Acme Inc",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo-amp.png",
      "width": 600,
      "height": 60
    }
  },
  "description": "Comprehensive guide to selecting and implementing project management software. Compare features, pricing, and user reviews of top PM tools.",
  "articleBody": "Full article text here...",
  "wordCount": 2500,
  "articleSection": "Guides",
  "inLanguage": "en-US",
  "keywords": ["project management", "PM software", "team collaboration"]
}
```

**Product Schema**:

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Acme Project Manager Pro",
  "image": [
    "https://example.com/products/pm-pro-main.jpg",
    "https://example.com/products/pm-pro-interface.jpg",
    "https://example.com/products/pm-pro-mobile.jpg"
  ],
  "description": "Professional project management software for teams of 10-100. Includes advanced features like resource planning, time tracking, and custom workflows.",
  "brand": {
    "@type": "Brand",
    "name": "Acme"
  },
  "sku": "PM-PRO-001",
  "mpn": "925872",
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/products/pm-pro",
    "priceCurrency": "USD",
    "price": "99.00",
    "priceValidUntil": "2024-12-31",
    "availability": "https://schema.org/InStock",
    "itemCondition": "https://schema.org/NewCondition",
    "seller": {
      "@type": "Organization",
      "name": "Acme Inc"
    }
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "reviewCount": "287",
    "bestRating": "5",
    "worstRating": "1"
  },
  "review": [
    {
      "@type": "Review",
      "reviewRating": {
        "@type": "Rating",
        "ratingValue": "5",
        "bestRating": "5"
      },
      "author": {
        "@type": "Person",
        "name": "Sarah Johnson"
      },
      "datePublished": "2024-11-10",
      "reviewBody": "Best PM tool we've used. Intuitive interface and powerful features. Highly recommended for growing teams."
    }
  ]
}
```

**FAQ Schema**:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is project management software?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Project management software is a digital tool that helps teams plan, organize, track, and collaborate on projects. It typically includes features like task management, scheduling, resource allocation, and reporting."
      }
    },
    {
      "@type": "Question",
      "name": "How much does PM software cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "PM software pricing varies widely. Free plans support basic features for small teams. Paid plans range from $10-50 per user per month, with enterprise solutions costing $100+ per user. Most offer 14-day free trials."
      }
    },
    {
      "@type": "Question",
      "name": "What features should I look for?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Essential features include: task management, team collaboration, time tracking, file sharing, reporting/analytics, integrations, mobile access, and customizable workflows. Consider your team size and specific needs when evaluating options."
      }
    }
  ]
}
```

**Breadcrumb Schema**:

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://example.com/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Blog",
      "item": "https://example.com/blog"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Guides",
      "item": "https://example.com/blog/guides"
    },
    {
      "@type": "ListItem",
      "position": 4,
      "name": "PM Software Guide",
      "item": "https://example.com/blog/guides/pm-software"
    }
  ]
}
```

**HowTo Schema**:

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to Set Up Project Management Software",
  "description": "Step-by-step guide to implementing PM software in your organization",
  "image": "https://example.com/images/howto-setup.jpg",
  "totalTime": "PT2H",
  "estimatedCost": {
    "@type": "MonetaryAmount",
    "currency": "USD",
    "value": "0"
  },
  "tool": [
    {
      "@type": "HowToTool",
      "name": "Project Management Software"
    },
    {
      "@type": "HowToTool",
      "name": "Team Email Addresses"
    }
  ],
  "step": [
    {
      "@type": "HowToStep",
      "name": "Create Account",
      "text": "Sign up for a free trial account and verify your email address.",
      "image": "https://example.com/images/step1.jpg",
      "url": "https://example.com/guides/setup#step1"
    },
    {
      "@type": "HowToStep",
      "name": "Invite Team",
      "text": "Add team members by entering their email addresses. They'll receive invitation links.",
      "image": "https://example.com/images/step2.jpg",
      "url": "https://example.com/guides/setup#step2"
    },
    {
      "@type": "HowToStep",
      "name": "Create First Project",
      "text": "Click 'New Project', enter project details, and add initial tasks.",
      "image": "https://example.com/images/step3.jpg",
      "url": "https://example.com/guides/setup#step3"
    },
    {
      "@type": "HowToStep",
      "name": "Customize Workflow",
      "text": "Configure project stages, task statuses, and automation rules to match your workflow.",
      "image": "https://example.com/images/step4.jpg",
      "url": "https://example.com/guides/setup#step4"
    }
  ]
}
```

**Review/Rating Schema**:

```json
{
  "@context": "https://schema.org",
  "@type": "Review",
  "itemReviewed": {
    "@type": "SoftwareApplication",
    "name": "Acme Project Manager",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web, iOS, Android"
  },
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "4.8",
    "bestRating": "5",
    "worstRating": "1"
  },
  "author": {
    "@type": "Person",
    "name": "Tech Review Pro"
  },
  "datePublished": "2024-11-01",
  "reviewBody": "Acme Project Manager excels in user experience and feature completeness. The interface is intuitive, making onboarding quick. Advanced features like resource planning and time tracking are well-implemented. Highly recommended for teams of 10-100.",
  "publisher": {
    "@type": "Organization",
    "name": "Tech Reviews Daily"
  }
}
```

**Video Schema**:

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "Acme Project Manager - Product Tour",
  "description": "5-minute guided tour of Acme Project Manager features and interface",
  "thumbnailUrl": "https://example.com/videos/tour-thumbnail.jpg",
  "uploadDate": "2024-10-15T08:00:00+00:00",
  "duration": "PT5M",
  "contentUrl": "https://example.com/videos/product-tour.mp4",
  "embedUrl": "https://www.youtube.com/embed/abc123",
  "interactionStatistic": {
    "@type": "InteractionCounter",
    "interactionType": "https://schema.org/WatchAction",
    "userInteractionCount": 12500
  },
  "publisher": {
    "@type": "Organization",
    "name": "Acme Inc",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  }
}
```

#### 2. Rich Snippet Opportunities

**Search Result Enhancements**:

```markdown
## Rich Snippet Types You Can Achieve

### Star Ratings
**Schema**: Product, Review, AggregateRating
**Appearance**: ⭐⭐⭐⭐⭐ (4.6) · 287 reviews
**CTR Impact**: +15-20%
**Example**: Product pages, review pages

### FAQ Accordion
**Schema**: FAQPage
**Appearance**: Expandable Q&A in search results
**CTR Impact**: +10-15%
**Example**: Support pages, guide pages

### Breadcrumbs
**Schema**: BreadcrumbList
**Appearance**: Home > Blog > Guides > Article
**CTR Impact**: +5-8%
**Example**: All internal pages

### Article Rich Results
**Schema**: Article
**Appearance**: Published date, author, featured image
**CTR Impact**: +8-12%
**Example**: Blog posts, news articles

### Product Rich Results
**Schema**: Product, Offer, AggregateRating
**Appearance**: Price, availability, ratings, reviews
**CTR Impact**: +20-30%
**Example**: E-commerce product pages

### HowTo Rich Results
**Schema**: HowTo
**Appearance**: Step-by-step instructions with images
**CTR Impact**: +12-18%
**Example**: Tutorial pages, guides

### Video Rich Results
**Schema**: VideoObject
**Appearance**: Video thumbnail, duration, upload date
**CTR Impact**: +15-25%
**Example**: Pages with embedded videos

### Event Rich Results
**Schema**: Event
**Appearance**: Date, location, ticket price
**CTR Impact**: +18-25%
**Example**: Webinar, conference pages
```

#### 3. Implementation Methods

**JSON-LD Implementation** (Recommended):

```html
<!DOCTYPE html>
<html>
<head>
  <title>Best Project Management Software 2024</title>

  <!-- Organization Schema -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Acme Inc",
    "url": "https://example.com",
    "logo": "https://example.com/logo.png"
  }
  </script>

  <!-- Article Schema -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Best Project Management Software 2024",
    "author": {
      "@type": "Person",
      "name": "John Smith"
    },
    "datePublished": "2024-01-15"
  }
  </script>

  <!-- Breadcrumb Schema -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [...]
  }
  </script>
</head>
<body>
  <!-- Page content -->
</body>
</html>
```

**Multiple Schema Types on One Page**:

```javascript
// Combine multiple schemas
const generatePageSchema = (pageData) => {
  const schemas = [];

  // Always include Organization
  schemas.push({
    "@context": "https://schema.org",
    "@type": "Organization",
    ...organizationData
  });

  // Add breadcrumbs if not homepage
  if (!pageData.isHomepage) {
    schemas.push(generateBreadcrumbs(pageData));
  }

  // Add page-specific schema
  if (pageData.type === 'article') {
    schemas.push(generateArticleSchema(pageData));
  } else if (pageData.type === 'product') {
    schemas.push(generateProductSchema(pageData));
  } else if (pageData.type === 'faq') {
    schemas.push(generateFAQSchema(pageData));
  }

  // Add video schema if video present
  if (pageData.hasVideo) {
    schemas.push(generateVideoSchema(pageData.videoData));
  }

  return schemas;
};
```

#### 4. Automated Schema Generation

**Smart Schema Detection**:

```javascript
const autoGenerateSchema = async (url) => {
  // Fetch and analyze page
  const page = await fetchPage(url);
  const pageType = detectPageType(page);

  let schemas = [];

  // Base schema (always include)
  schemas.push(generateOrganizationSchema());

  // Page-type specific schema
  switch (pageType) {
    case 'homepage':
      schemas.push(generateWebSiteSchema(page));
      break;

    case 'blog-post':
      schemas.push(generateArticleSchema(page));
      schemas.push(generateBreadcrumbSchema(page));
      if (extractFAQs(page).length > 0) {
        schemas.push(generateFAQSchema(page));
      }
      break;

    case 'product':
      schemas.push(generateProductSchema(page));
      schemas.push(generateBreadcrumbSchema(page));
      if (page.reviews.length > 0) {
        schemas.push(generateReviewSchema(page));
      }
      break;

    case 'guide':
      schemas.push(generateHowToSchema(page));
      schemas.push(generateBreadcrumbSchema(page));
      break;

    case 'faq':
      schemas.push(generateFAQPageSchema(page));
      break;
  }

  return schemas;
};

// Extract data from page content
const extractFAQs = (page) => {
  // Find FAQ patterns in content
  const faqPatterns = [
    /##?\s*(.+\?)\s*\n+(.+)/g,  // Markdown FAQ
    /<h[23]>(.+\?)<\/h[23]>\s*<p>(.+)<\/p>/g,  // HTML FAQ
  ];

  const faqs = [];
  // ... extraction logic
  return faqs;
};
```

#### 5. Validation & Testing

**Google Rich Results Test**:

```javascript
const validateSchema = async (url, schema) => {
  // Test with Google's Rich Results Test
  const testUrl = `https://search.google.com/test/rich-results?url=${encodeURIComponent(url)}`;

  // Or use API
  const validation = await fetch('https://validator.schema.org/validate', {
    method: 'POST',
    body: JSON.stringify(schema)
  });

  const results = await validation.json();

  return {
    valid: results.errors.length === 0,
    errors: results.errors,
    warnings: results.warnings,
    eligibleFor: results.richSnippetTypes || []
  };
};
```

**Common Schema Errors**:

```markdown
## Common Issues & Fixes

### Error: Missing required field
**Problem**: "@type": "Article" missing "headline"
**Fix**: Add required fields for schema type
```json
{
  "@type": "Article",
  "headline": "Article Title",  // ✅ Required
  "author": {...},              // ✅ Required
  "datePublished": "2024-01-15" // ✅ Required
}
```

### Warning: Recommended field missing

**Problem**: No "image" in Article schema
**Fix**: Add recommended fields for rich results

```json
{
  "@type": "Article",
  "image": [  // ⭐ Recommended for rich results
    "https://example.com/image-16x9.jpg",
    "https://example.com/image-4x3.jpg",
    "https://example.com/image-1x1.jpg"
  ]
}
```

### Error: Invalid URL

**Problem**: Relative URLs in schema
**Fix**: Use absolute URLs only

```json
// ❌ Wrong
"url": "/products/item"

// ✅ Correct
"url": "https://example.com/products/item"
```

### Error: Invalid date format

**Problem**: Date not in ISO 8601 format
**Fix**: Use proper date format

```json
// ❌ Wrong
"datePublished": "01/15/2024"

// ✅ Correct
"datePublished": "2024-01-15T08:00:00+00:00"
```

```

### Implementation Steps

**Step 1: Detect Schema Opportunities**
1. Analyze page content and type
2. Identify applicable schema types
3. Extract data from content
4. Prioritize by rich snippet impact

**Step 2: Generate Schema**
1. Create base Organization schema
2. Add page-specific schema
3. Add breadcrumbs
4. Add supplementary schemas (FAQ, Video, etc.)

**Step 3: Validate**
1. Test with Google Rich Results Test
2. Check for errors and warnings
3. Verify required fields
4. Test rich snippet eligibility

**Step 4: Implement**
1. Add JSON-LD to <head> section
2. Deploy to production
3. Request indexing in Search Console
4. Monitor for rich snippets (7-14 days)

**Step 5: Monitor**
1. Track rich snippet appearance
2. Monitor click-through rates
3. Test regularly for errors
4. Update schema as content changes

### Output Requirements

**Generated Files**:
- `schema.json` - Generated schema markup
- `schema-validation-report.md` - Validation results
- `rich-snippet-opportunities.md` - Available enhancements
- `implementation-guide.md` - How to add to site

## ROI Impact

**Search Visibility**:
- **Rich snippets** increase CTR by 15-30%
- **Better understanding** by search engines
- **Featured snippets** opportunities

**CTR Improvements by Schema Type**:
- Product with ratings: +20-30% CTR
- FAQ rich results: +10-15% CTR
- HowTo rich results: +12-18% CTR
- Article with image: +8-12% CTR
- Breadcrumbs: +5-8% CTR

**Traffic Impact**:
- Current traffic: 10,000/month
- Average CTR improvement: +15%
- New traffic: 11,500/month (+1,500)
- At 2.5% conversion: +37 conversions/month
- At $120/conversion: +$4,440/month

**Total Value**: $53,000/year
- Incremental revenue: $45,000/year
- Improved brand visibility: $8,000/year

## Success Criteria

✅ **Schema implemented on all key pages**
✅ **Zero validation errors**
✅ **Eligible for rich snippets**
✅ **Rich snippets appearing in search** (7-14 days)
✅ **CTR increased >10%**

**Schema Coverage Targets**:
- Homepage: Organization, WebSite
- Blog posts: Article, Breadcrumb, FAQ
- Products: Product, Offer, Review, Breadcrumb
- Guides: HowTo, Breadcrumb
- All pages: Organization, Breadcrumb

## Next Steps

1. Generate schema for key pages
2. Validate with Google's testing tool
3. Implement schema markup
4. Request indexing in Search Console
5. Monitor for rich snippet appearance

---

**Schema Status**: 🟢 Ready to Generate
**Rich Snippet Potential**: High
**Annual ROI**: $53,000
