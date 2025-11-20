# Agent Zero SEO - Setup and Configuration Guide

## Overview

Agent Zero has been transformed into a specialized WordPress SEO agent with capabilities for keyword research, content optimization, technical audits, and WordPress management via REST API.

## Table of Contents

1. [Activation](#activation)
2. [WordPress Configuration](#wordpress-configuration)
3. [Optional API Integrations](#optional-api-integrations)
4. [Available Tools](#available-tools)
5. [Example Workflows](#example-workflows)
6. [Best Practices](#best-practices)

---

## Activation

### Method 1: Use SEO System Prompt Directly

To activate the SEO-specialized agent, modify your agent initialization to use the SEO system prompt:

**Option A: Via Configuration File**

Edit your configuration to point to the SEO system prompt:

```python
# In your agent configuration or initialization
agent.system_prompt_file = "prompts/agent.system.seo.main.md"
```

**Option B: Via Environment Variable**

You can specify the prompt file when starting Agent Zero.

### Method 2: Subordinate Agent Approach

You can also use the main Agent Zero and ask it to create a specialized subordinate for SEO:

```
Create a subordinate agent specialized in WordPress SEO with expertise in keyword research,
content optimization, and technical audits. Use the SEO system prompt from
prompts/agent.system.seo.main.md
```

---

## WordPress Configuration

### 1. Generate WordPress Application Password

1. Log in to your WordPress admin panel
2. Navigate to **Users → Profile**
3. Scroll to **Application Passwords** section
4. Enter a name (e.g., "Agent Zero SEO")
5. Click **Add New Application Password**
6. **Copy the generated password** (you won't see it again)

### 2. Store Credentials in Agent Memory

Use the memory_save tool to securely store your WordPress credentials:

```json
{
    "tool_name": "memory_save",
    "tool_args": {
        "memory_name": "wp_username",
        "memory_text": "your_wordpress_username"
    }
}
```

```json
{
    "tool_name": "memory_save",
    "tool_args": {
        "memory_name": "wp_app_password",
        "memory_text": "xxxx xxxx xxxx xxxx xxxx xxxx"
    }
}
```

**Important:** Store the application password exactly as provided by WordPress (with spaces).

---

## Optional API Integrations

For advanced features, you can integrate with third-party SEO services:

### SEMrush API

Store your API key:

```json
{
    "tool_name": "memory_save",
    "tool_args": {
        "memory_name": "semrush_api_key",
        "memory_text": "your_semrush_api_key"
    }
}
```

### Ahrefs API

```json
{
    "tool_name": "memory_save",
    "tool_args": {
        "memory_name": "ahrefs_api_key",
        "memory_text": "your_ahrefs_api_key"
    }
}
```

### Google Analytics API

Follow Google's OAuth 2.0 setup and store credentials as needed.

---

## Available Tools

### 1. **wordpress_api**

Fetch WordPress site data via REST API.

**Actions:**
- `get_site_info` - Site name, description, URL
- `get_posts` - Posts with SEO metadata (Yoast, RankMath)
- `get_pages` - Site pages
- `get_post` - Specific post with full content
- `get_categories` - All categories
- `get_tags` - All tags
- `get_media` - Media items and alt text
- `search_content` - Search site content

**Example:**

```json
{
    "tool_name": "wordpress_api",
    "tool_args": {
        "action": "get_posts",
        "site_url": "https://yoursite.com"
    }
}
```

### 2. **wordpress_seo_manager**

Manage and update WordPress SEO metadata.

⚠️ **Requires confirmation:** All write operations require `"confirmed": "true"`

**Actions:**
- `update_post_meta` - Update title, excerpt, slug
- `update_post_content` - Update post content
- `bulk_update_alt_text` - Update image alt text
- `update_categories` - Assign categories
- `update_tags` - Assign tags

**Example:**

```json
{
    "tool_name": "wordpress_seo_manager",
    "tool_args": {
        "action": "update_post_meta",
        "site_url": "https://yoursite.com",
        "post_id": "123",
        "title": "SEO Optimized Title - Keyword Rich",
        "excerpt": "Compelling meta description under 160 characters",
        "confirmed": "true"
    }
}
```

### 3. **seo_keyword_research**

Keyword research and analysis.

**Actions:**
- `suggest_keywords` - Generate keyword suggestions
- `analyze_keyword` - Analyze keyword metrics
- `related_questions` - Find "People Also Ask" questions
- `local_keyword_suggestions` - Location-based keywords
- `keyword_difficulty` - Assess ranking difficulty

**Example:**

```json
{
    "tool_name": "seo_keyword_research",
    "tool_args": {
        "action": "suggest_keywords",
        "seed_keyword": "wordpress seo"
    }
}
```

### 4. **seo_content_analyzer**

Analyze content for SEO optimization.

**Actions:**
- `analyze_content` - Comprehensive SEO analysis
- `check_keyword_density` - Keyword usage analysis
- `analyze_headings` - Heading structure
- `check_readability` - Readability score
- `find_missing_elements` - Missing SEO elements

**Example:**

```json
{
    "tool_name": "seo_content_analyzer",
    "tool_args": {
        "action": "analyze_content",
        "content": "<h1>Post Title</h1><p>Content here...</p>",
        "target_keyword": "wordpress optimization"
    }
}
```

### 5. **seo_technical_audit**

Technical SEO audits and site health checks.

**Actions:**
- `full_audit` - Complete technical audit
- `check_robots` - Verify robots.txt
- `check_sitemap` - Check XML sitemap
- `check_ssl` - SSL/HTTPS verification
- `check_meta_tags` - Meta tag analysis
- `check_schema` - Structured data check
- `check_mobile` - Mobile responsiveness
- `check_page_speed` - Page speed analysis

**Example:**

```json
{
    "tool_name": "seo_technical_audit",
    "tool_args": {
        "action": "full_audit",
        "site_url": "https://yoursite.com"
    }
}
```

---

## Example Workflows

### Workflow 1: Complete Site SEO Audit

**User Request:**
```
Perform a complete SEO audit of my WordPress site at https://example.com
```

**Agent Actions:**
1. Use `seo_technical_audit` with `full_audit` action
2. Use `wordpress_api` to fetch posts and analyze SEO metadata
3. Use `seo_content_analyzer` on top posts
4. Generate comprehensive report with prioritized recommendations

### Workflow 2: Keyword Research and Content Optimization

**User Request:**
```
Help me optimize my blog post about "WordPress security" for better SEO
```

**Agent Actions:**
1. Use `seo_keyword_research` to find related keywords and questions
2. Use `wordpress_api` to fetch the post content
3. Use `seo_content_analyzer` to analyze current content
4. Provide recommendations for:
   - Title optimization
   - Meta description
   - Keyword placement
   - Content structure
   - Internal linking

### Workflow 3: Bulk Image Alt Text Optimization

**User Request:**
```
Check all images on my site and suggest alt text improvements for SEO
```

**Agent Actions:**
1. Use `wordpress_api` with `get_media` action
2. Analyze each image:
   - Check for missing alt text
   - Evaluate alt text quality
   - Suggest keyword-rich alternatives
3. Use `wordpress_seo_manager` with `bulk_update_alt_text` (with user confirmation)

### Workflow 4: Competitor Analysis

**User Request:**
```
Analyze what keywords my competitor ranks for and suggest content gaps
```

**Agent Actions:**
1. Use `seo_keyword_research` with `competitor_keywords` (requires API)
2. Compare with your site's keyword targeting
3. Identify keyword gaps
4. Suggest new content topics
5. Provide content strategy recommendations

### Workflow 5: Local SEO Optimization

**User Request:**
```
Optimize my site for local SEO in Austin, Texas
```

**Agent Actions:**
1. Use `seo_keyword_research` with `local_keyword_suggestions`
2. Analyze current posts for local keyword usage
3. Check for:
   - NAP (Name, Address, Phone) consistency
   - Local schema markup
   - Location-specific content
4. Provide recommendations for local optimization

---

## Best Practices

### 1. Safety First

- **Always review changes** before confirming write operations
- **Test on staging site** before production
- **Backup your site** before bulk operations
- **Use version control** for content changes

### 2. SEO Strategy

- **Focus on long-tail keywords** for easier ranking
- **Match content to search intent**
- **Prioritize user experience** over keyword density
- **Build quality backlinks** naturally
- **Monitor and iterate** based on performance data

### 3. Content Optimization

- **Aim for 600-2000 words** for competitive keywords
- **Use 0.5-2.5% keyword density**
- **One H1 per page**, multiple H2/H3 for structure
- **Include keyword in first 100 words**
- **Optimize for featured snippets** with concise answers

### 4. Technical SEO

- **Ensure HTTPS** for all pages
- **Optimize page speed** (< 3 seconds)
- **Make site mobile-responsive**
- **Use schema markup** for rich results
- **Submit sitemap** to Search Console
- **Fix broken links** regularly

### 5. WordPress-Specific

- **Use SEO plugins** (Yoast, RankMath) for metadata management
- **Optimize permalinks** for readability
- **Use categories and tags** strategically
- **Compress images** before upload
- **Enable caching** for performance
- **Regular updates** for security and SEO

---

## Troubleshooting

### WordPress API Returns 401 Error

- Verify application password is correct
- Check that username is exact (case-sensitive)
- Ensure WordPress REST API is enabled
- Check for security plugins blocking API access

### Tool Not Found Error

- Verify tool files are in `python/tools/` directory
- Check that tool names match exactly
- Restart Agent Zero to reload tools

### Keyword Research Returns Limited Data

- Consider integrating paid APIs (SEMrush, Ahrefs)
- Use Google Keyword Planner for search volume
- Supplement with manual competitor analysis

### Technical Audit Shows Errors

- Review each recommendation individually
- Prioritize by impact (SSL > meta tags > schema)
- Some checks may require server-level changes
- Consult WordPress developer for complex issues

---

## Support and Resources

- **Agent Zero Documentation:** [docs/README.md](./README.md)
- **WordPress REST API:** https://developer.wordpress.org/rest-api/
- **Google SEO Guide:** https://developers.google.com/search/docs
- **Yoast SEO:** https://yoast.com/wordpress/plugins/seo/
- **SEMrush Academy:** https://www.semrush.com/academy/

---

## Next Steps

1. **Complete initial setup** (WordPress credentials)
2. **Run full audit** on your site
3. **Address critical issues** first (HTTPS, meta tags)
4. **Develop content strategy** based on keyword research
5. **Monitor progress** and iterate

Happy optimizing! 🚀
