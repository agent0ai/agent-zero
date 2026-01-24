---
description: Generate and optimize XML sitemaps with automatic updates, image/video sitemaps, and search engine submission
argument-hint: [--type <standard|image|video|news>] [--auto-update] [--submit]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

SEO Sitemap Generation: **${ARGUMENTS}**

## Generating Optimized XML Sitemaps

Use the Task tool with subagent_type=seo-specialist to generate comprehensive sitemaps with the following specifications:

### Input Parameters

**Sitemap Type**: ${TYPE:-standard} (standard, image, video, news, or all)
**Auto-Update**: ${AUTO_UPDATE:-true} (Regenerate on content changes)
**Submit**: ${SUBMIT:-true} (Submit to search engines)
**Split Large**: ${SPLIT:-true} (Split into multiple if >50k URLs)

### Objectives

You are tasked with creating optimized XML sitemaps that help search engines discover and index your content efficiently. Your implementation must:

#### 1. Standard XML Sitemap Generation

**Basic Sitemap Structure**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">

  <!-- Homepage -->
  <url>
    <loc>https://example.com/</loc>
    <lastmod>2024-11-15</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>

  <!-- Product pages (high priority) -->
  <url>
    <loc>https://example.com/products/pm-pro</loc>
    <lastmod>2024-11-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>

  <!-- Blog posts (medium priority) -->
  <url>
    <loc>https://example.com/blog/pm-guide-2024</loc>
    <lastmod>2024-11-10</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>

  <!-- Static pages (lower priority) -->
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2024-10-01</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.5</priority>
  </url>

</urlset>
```

**Priority Guidelines**:

```javascript
const calculatePriority = (page) => {
  const priorities = {
    homepage: 1.0,
    mainProducts: 0.9,
    categoryPages: 0.8,
    blogPosts: 0.7,
    productPages: 0.8,
    guides: 0.7,
    staticPages: 0.5,
    legalPages: 0.3
  };

  // Adjust based on traffic
  if (page.monthlyTraffic > 1000) {
    return Math.min(priorities[page.type] + 0.1, 1.0);
  }

  // Adjust based on freshness
  const daysSinceUpdate = (Date.now() - page.lastModified) / (1000 * 60 * 60 * 24);
  if (daysSinceUpdate < 7) {
    return Math.min(priorities[page.type] + 0.1, 1.0);
  }

  return priorities[page.type] || 0.5;
};

const calculateChangeFreq = (page) => {
  const avgUpdateInterval = page.updateHistory.reduce((sum, update, i, arr) => {
    if (i === 0) return 0;
    return sum + (arr[i].date - arr[i-1].date);
  }, 0) / (page.updateHistory.length - 1);

  const daysInterval = avgUpdateInterval / (1000 * 60 * 60 * 24);

  if (daysInterval < 1) return 'hourly';
  if (daysInterval < 7) return 'daily';
  if (daysInterval < 30) return 'weekly';
  if (daysInterval < 365) return 'monthly';
  return 'yearly';
};
```

#### 2. Image Sitemap

**Image Sitemap Extension**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">

  <url>
    <loc>https://example.com/products/pm-pro</loc>

    <!-- Image 1 -->
    <image:image>
      <image:loc>https://example.com/images/pm-pro-dashboard.jpg</image:loc>
      <image:caption>Project management dashboard interface showing task kanban board</image:caption>
      <image:title>PM Pro Dashboard</image:title>
      <image:geo_location>San Francisco, CA</image:geo_location>
      <image:license>https://example.com/image-license</image:license>
    </image:image>

    <!-- Image 2 -->
    <image:image>
      <image:loc>https://example.com/images/pm-pro-mobile.jpg</image:loc>
      <image:caption>Mobile app interface for on-the-go project management</image:caption>
      <image:title>PM Pro Mobile App</image:title>
    </image:image>

    <!-- Can have up to 1,000 images per URL -->
  </url>

</urlset>
```

**Image Extraction**:

```javascript
const extractImages = (pageUrl) => {
  const page = fetchPage(pageUrl);
  const images = page.querySelectorAll('img');

  return Array.from(images)
    .filter(img => {
      // Exclude small images (likely icons)
      return img.width > 200 && img.height > 200;
    })
    .filter(img => {
      // Exclude external images
      return img.src.startsWith('https://example.com');
    })
    .map(img => ({
      loc: img.src,
      caption: img.alt || extractCaptionFromContext(img),
      title: img.title || generateTitleFromFilename(img.src)
    }));
};
```

#### 3. Video Sitemap

**Video Sitemap Structure**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">

  <url>
    <loc>https://example.com/guides/getting-started</loc>

    <video:video>
      <video:thumbnail_loc>https://example.com/videos/thumbs/getting-started.jpg</video:thumbnail_loc>
      <video:title>Getting Started with Project Management</video:title>
      <video:description>5-minute tutorial on setting up your first project and inviting team members</video:description>
      <video:content_loc>https://example.com/videos/getting-started.mp4</video:content_loc>
      <video:player_loc allow_embed="yes" autoplay="ap=1">
        https://www.youtube.com/embed/abc123
      </video:player_loc>
      <video:duration>300</video:duration>
      <video:publication_date>2024-10-15T08:00:00+00:00</video:publication_date>
      <video:family_friendly>yes</video:family_friendly>
      <video:restriction relationship="allow">US CA GB</video:restriction>
      <video:platform relationship="allow">web mobile</video:platform>
      <video:requires_subscription>no</video:requires_subscription>
      <video:uploader info="https://example.com/about">Acme Inc</video:uploader>
      <video:live>no</video:live>
      <video:tag>project management</video:tag>
      <video:tag>tutorial</video:tag>
      <video:tag>getting started</video:tag>
      <video:category>Education</video:category>
      <video:view_count>12500</video:view_count>
      <video:rating>4.8</video:rating>
    </video:video>

  </url>

</urlset>
```

#### 4. News Sitemap (for news publishers)

**News Sitemap Structure**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">

  <url>
    <loc>https://example.com/news/industry-update-nov-2024</loc>
    <news:news>
      <news:publication>
        <news:name>Acme Tech News</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>2024-11-15T09:00:00+00:00</news:publication_date>
      <news:title>Major Industry Update: AI Adoption Reaches 80% in Tech Sector</news:title>
      <news:keywords>AI, technology, adoption, industry trends</news:keywords>
    </news:news>
  </url>

</urlset>
```

**News Sitemap Rules**:

- Only include articles from last 2 days
- Maximum 1,000 URLs per sitemap
- Update frequently (every 15-30 minutes for active sites)
- Include only news content (not evergreen)

#### 5. Sitemap Index (for large sites)

**Sitemap Index Structure**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

  <sitemap>
    <loc>https://example.com/sitemap-main.xml</loc>
    <lastmod>2024-11-15T10:00:00+00:00</lastmod>
  </sitemap>

  <sitemap>
    <loc>https://example.com/sitemap-products.xml</loc>
    <lastmod>2024-11-14T15:30:00+00:00</lastmod>
  </sitemap>

  <sitemap>
    <loc>https://example.com/sitemap-blog.xml</loc>
    <lastmod>2024-11-15T08:00:00+00:00</lastmod>
  </sitemap>

  <sitemap>
    <loc>https://example.com/sitemap-images.xml</loc>
    <lastmod>2024-11-15T10:00:00+00:00</lastmod>
  </sitemap>

  <sitemap>
    <loc>https://example.com/sitemap-videos.xml</loc>
    <lastmod>2024-11-10T12:00:00+00:00</lastmod>
  </sitemap>

</sitemapindex>
```

**When to Use Sitemap Index**:

- Site has >50,000 URLs
- Sitemap file >50 MB uncompressed
- Logical content separation (products, blog, etc.)
- Different update frequencies

**Auto-Split Logic**:

```javascript
const generateSitemaps = async (pages) => {
  const MAX_URLS = 50000;
  const MAX_SIZE = 50 * 1024 * 1024; // 50 MB

  // Group pages by type
  const groups = {
    main: pages.filter(p => p.type === 'page'),
    products: pages.filter(p => p.type === 'product'),
    blog: pages.filter(p => p.type === 'blog'),
    images: extractAllImages(pages),
    videos: extractAllVideos(pages)
  };

  const sitemaps = [];

  for (const [type, urls] of Object.entries(groups)) {
    if (urls.length === 0) continue;

    // Split if too many URLs
    const chunks = chunkArray(urls, MAX_URLS);

    for (let i = 0; i < chunks.length; i++) {
      const filename = chunks.length > 1
        ? `sitemap-${type}-${i + 1}.xml`
        : `sitemap-${type}.xml`;

      const content = generateSitemapXML(chunks[i], type);

      sitemaps.push({
        filename,
        content,
        lastmod: new Date().toISOString(),
        urlCount: chunks[i].length
      });
    }
  }

  // Generate sitemap index
  if (sitemaps.length > 1) {
    const indexContent = generateSitemapIndex(sitemaps);
    sitemaps.push({
      filename: 'sitemap.xml',
      content: indexContent,
      isIndex: true
    });
  }

  return sitemaps;
};
```

#### 6. Dynamic Sitemap Generation

**For CMS/Dynamic Sites**:

```javascript
// Express.js route example
app.get('/sitemap.xml', async (req, res) => {
  const pages = await database.getAllPublishedPages();

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${pages.map(page => `
  <url>
    <loc>${page.url}</loc>
    <lastmod>${page.updatedAt.toISOString().split('T')[0]}</lastmod>
    <changefreq>${calculateChangeFreq(page)}</changefreq>
    <priority>${calculatePriority(page)}</priority>
  </url>
`).join('')}
</urlset>`;

  res.header('Content-Type', 'application/xml');
  res.send(sitemap);
});

// Cache for 1 hour
const cachedSitemap = cache(generateSitemap, { ttl: 3600 });
```

#### 7. Sitemap Optimization Rules

**Best Practices**:

```javascript
const sitemapBestPractices = {
  // 1. Exclude low-value pages
  shouldInclude: (page) => {
    return !page.url.match(/(login|admin|cart|checkout|search)/i) &&
           !page.noindex &&
           page.status === 200 &&
           !page.isCanonicalizedAway;
  },

  // 2. Accurate lastmod dates
  getLastModified: (page) => {
    // Use actual content modification date, not template change
    return page.contentLastModified || page.publishedDate;
  },

  // 3. Realistic change frequency
  calculateChangeFreq: (page) => {
    // Based on actual update history, not wishful thinking
    const updates = page.updateHistory;
    if (updates.length < 2) return 'monthly';

    const avgDays = calculateAverageUpdateInterval(updates);
    // Return realistic frequency
  },

  // 4. Priority hierarchy
  setPriority: (page) => {
    // Homepage: 1.0
    // Main category: 0.8
    // Subcategory: 0.6
    // Individual pages: 0.4-0.7 based on traffic
    // Utility pages: 0.3
  },

  // 5. Canonical URLs only
  useCanonicalUrl: true,

  // 6. Compression
  gzip: true  // Serve as sitemap.xml.gz
};
```

#### 8. Sitemap Submission

**Submit to Search Engines**:

```bash
#!/bin/bash

# Submit sitemap to Google
curl "https://www.google.com/ping?sitemap=https://example.com/sitemap.xml"

# Submit to Bing
curl "https://www.bing.com/ping?sitemap=https://example.com/sitemap.xml"

# Or via Search Console API
gcloud auth activate-service-account --key-file=credentials.json

curl -X POST \
  "https://searchconsole.googleapis.com/v1/urlNotifications:publish" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/sitemap.xml",
    "type": "URL_UPDATED"
  }'
```

**robots.txt Integration**:

```
# robots.txt
User-agent: *
Allow: /

# Sitemap locations
Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-images.xml
Sitemap: https://example.com/sitemap-videos.xml
```

#### 9. Validation & Monitoring

**Sitemap Validation**:

```javascript
const validateSitemap = (sitemapXml) => {
  const validation = {
    errors: [],
    warnings: [],
    stats: {}
  };

  // Parse XML
  const doc = parseXML(sitemapXml);

  // Check file size
  const size = Buffer.byteLength(sitemapXml, 'utf8');
  if (size > 50 * 1024 * 1024) {
    validation.errors.push(`Sitemap too large: ${size} bytes (max 50MB)`);
  }

  // Check URL count
  const urls = doc.querySelectorAll('url');
  if (urls.length > 50000) {
    validation.errors.push(`Too many URLs: ${urls.length} (max 50,000)`);
  }

  // Validate each URL
  urls.forEach((url, i) => {
    const loc = url.querySelector('loc')?.textContent;

    // Check required fields
    if (!loc) {
      validation.errors.push(`URL ${i}: Missing <loc>`);
    }

    // Validate URL format
    if (loc && !isValidUrl(loc)) {
      validation.errors.push(`URL ${i}: Invalid URL format: ${loc}`);
    }

    // Check for HTTPS
    if (loc && !loc.startsWith('https://')) {
      validation.warnings.push(`URL ${i}: Not HTTPS: ${loc}`);
    }

    // Validate lastmod format
    const lastmod = url.querySelector('lastmod')?.textContent;
    if (lastmod && !isValidDate(lastmod)) {
      validation.errors.push(`URL ${i}: Invalid date format: ${lastmod}`);
    }

    // Check priority range
    const priority = parseFloat(url.querySelector('priority')?.textContent);
    if (priority && (priority < 0 || priority > 1)) {
      validation.errors.push(`URL ${i}: Priority out of range: ${priority}`);
    }
  });

  validation.stats = {
    totalUrls: urls.length,
    fileSize: size,
    valid: validation.errors.length === 0
  };

  return validation;
};
```

**Monitoring Sitemap Health**:

```javascript
const monitorSitemap = async () => {
  // Check sitemap accessibility
  const response = await fetch('https://example.com/sitemap.xml');
  if (response.status !== 200) {
    alert('Sitemap not accessible!');
  }

  // Parse and analyze
  const xml = await response.text();
  const validation = validateSitemap(xml);

  // Check Google Search Console
  const gscData = await fetchSearchConsoleData();
  const submittedUrls = gscData.sitemaps.totalSubmitted;
  const indexedUrls = gscData.sitemaps.totalIndexed;

  return {
    accessible: response.status === 200,
    valid: validation.errors.length === 0,
    submitted: submittedUrls,
    indexed: indexedUrls,
    indexationRate: (indexedUrls / submittedUrls * 100).toFixed(1) + '%',
    issues: validation.errors.concat(validation.warnings)
  };
};
```

### Implementation Steps

**Step 1: Content Discovery**

1. Crawl website to discover all pages
2. Extract images and videos
3. Get metadata (lastmod, priority)
4. Filter excluded pages

**Step 2: Generation**

1. Generate standard sitemap
2. Generate image sitemap (if images found)
3. Generate video sitemap (if videos found)
4. Create sitemap index if needed

**Step 3: Optimization**

1. Calculate accurate priorities
2. Set realistic change frequencies
3. Compress sitemaps (gzip)
4. Split if over limits

**Step 4: Submission**

1. Upload to website root
2. Add to robots.txt
3. Submit to Google Search Console
4. Submit to Bing Webmaster Tools
5. Ping search engines

**Step 5: Monitoring**

1. Check sitemap accessibility
2. Monitor indexation rates
3. Track errors in Search Console
4. Auto-regenerate on content changes

### Output Requirements

**Generated Files**:

- `sitemap.xml` - Main sitemap or sitemap index
- `sitemap-products.xml` - Product pages
- `sitemap-blog.xml` - Blog posts
- `sitemap-images.xml` - Image sitemap
- `sitemap-videos.xml` - Video sitemap
- `SITEMAP_REPORT.md` - Generation report

## ROI Impact

**Indexation Improvements**:

- **Faster discovery** of new content (hours vs days)
- **Better indexation rate** (+15-25%)
- **Priority guidance** to search engines

**Traffic Impact**:

- New pages indexed faster: +10% traffic
- Image search visibility: +20% image traffic
- Video search visibility: +25% video traffic

**Crawl Efficiency**:

- Reduced crawl budget waste
- Focused on high-value pages
- Better crawl frequency

**Total Value**: $35,000/year

- Faster indexation: $20,000/year
- Image/video traffic: $10,000/year
- Crawl efficiency: $5,000/year

## Success Criteria

✅ **Sitemaps generated for all content types**
✅ **Submitted to search engines**
✅ **Zero validation errors**
✅ **Indexation rate >90%**
✅ **Auto-update on content changes**

**Sitemap Quality Targets**:

- All URLs return 200 status
- Accurate lastmod dates
- Realistic priorities
- No orphan pages
- Images/videos included

## Next Steps

1. Generate sitemaps
2. Validate XML
3. Upload to website
4. Submit to search engines
5. Monitor indexation in Search Console

---

**Sitemap Status**: 🟢 Ready to Generate
**Indexation Impact**: +15-25%
**Annual ROI**: $35,000
