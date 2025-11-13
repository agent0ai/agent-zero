# 🚀 Agent Zero SEO - WordPress SEO Specialist Agent

## Overview

Agent Zero has been transformed into a specialized **WordPress SEO consultant agent** with comprehensive capabilities for managing, analyzing, optimizing, and improving SEO performance for WordPress websites.

This agent combines the power of Agent Zero's dynamic framework with focused SEO expertise, WordPress integration, and actionable optimization strategies.

---

## ✨ Key Features

### 🔍 **SEO Analysis & Research**
- **Keyword Research**: Discover high-value keywords, analyze search intent, and identify content opportunities
- **Competitor Analysis**: Understand what competitors rank for and find content gaps
- **Content Optimization**: Analyze existing content for SEO best practices
- **Technical Audits**: Comprehensive site health checks covering all critical SEO factors

### 📝 **WordPress Integration**
- **REST API Integration**: Fetch and manage WordPress content, posts, pages, and media
- **Metadata Management**: Update titles, descriptions, slugs, and SEO tags
- **Content Updates**: Modify post content with SEO improvements
- **Image Optimization**: Bulk update alt text for better image SEO
- **Plugin Compatibility**: Works with Yoast SEO, RankMath, and All in One SEO

### 📊 **Technical SEO**
- **Site Audits**: Automated checks for robots.txt, sitemaps, SSL, meta tags, schema markup
- **Mobile Optimization**: Verify mobile-friendliness and responsive design
- **Page Speed Analysis**: Basic performance metrics and recommendations
- **Structured Data**: Detect and validate schema markup
- **Security Checks**: HTTPS verification and security best practices

### 🎯 **Strategic Recommendations**
- **Content Strategy**: Data-driven recommendations for new content
- **Priority Rankings**: Issues sorted by impact and effort
- **Action Plans**: Step-by-step implementation guides
- **Best Practices**: Industry-standard SEO guidance
- **ROI Focus**: Emphasis on high-impact optimizations

---

## 🛠️ Available Tools

### 1. **wordpress_api**
Interact with WordPress via REST API
- Fetch site information, posts, pages, categories, tags
- Retrieve media items and check alt text
- Search content across the site
- Extract SEO metadata from Yoast/RankMath

### 2. **wordpress_seo_manager**
Manage WordPress SEO metadata
- Update post titles, excerpts, and slugs
- Modify post content
- Bulk update image alt text
- Manage categories and tags
- **Safety**: Requires explicit user confirmation

### 3. **seo_keyword_research**
Comprehensive keyword research
- Generate keyword suggestions from seed keywords
- Analyze keyword metrics and difficulty
- Find "People Also Ask" questions
- Create local SEO keyword variations
- Support for SEMrush/Ahrefs API integration

### 4. **seo_content_analyzer**
Analyze and optimize content
- Keyword density and placement analysis
- Heading structure evaluation
- Readability scoring (Flesch Reading Ease)
- SEO score calculation (0-100)
- Identify missing SEO elements
- Actionable improvement recommendations

### 5. **seo_technical_audit**
Technical SEO auditing
- Full site technical audit with scoring
- Robots.txt verification
- XML sitemap detection
- SSL/HTTPS configuration
- Meta tags analysis
- Schema markup detection
- Mobile responsiveness check
- Page speed basics

---

## 📚 Documentation

### Essential Guides
- **[Setup Guide](docs/SEO_AGENT_SETUP.md)** - Complete setup and configuration instructions
- **[Example Interactions](docs/SEO_AGENT_EXAMPLES.md)** - Real-world usage examples and workflows

### Quick Links
- **System Prompts**: `prompts/agent.system.seo.main.md`
- **Tool Descriptions**: `prompts/agent.system.tool.*.md`
- **Tool Implementations**: `python/tools/seo_*.py` and `python/tools/wordpress_*.py`

---

## 🚀 Quick Start

### 1. Activate SEO Mode

**Method A: Configuration**
```python
agent.system_prompt_file = "prompts/agent.system.seo.main.md"
```

**Method B: Ask Agent Zero**
```
Create a subordinate agent specialized in WordPress SEO using the
prompts/agent.system.seo.main.md system prompt
```

### 2. Configure WordPress Access

```
I want to connect to my WordPress site at https://mysite.com

Username: admin
App Password: abcd 1234 efgh 5678
```

### 3. Run Your First Audit

```
Run a complete SEO audit on my WordPress site and provide prioritized recommendations
```

---

## 💡 Common Use Cases

### 🔍 **Site Audit**
```
Perform a comprehensive SEO audit of https://example.com
```
The agent will check:
- Technical SEO (SSL, sitemap, robots.txt, meta tags)
- Content quality and optimization
- Keyword targeting
- Site structure and navigation
- Mobile responsiveness
- Page speed

### 📝 **Content Optimization**
```
Analyze my blog post about "WordPress Security" and suggest SEO improvements
```
The agent will:
- Analyze keyword usage and density
- Check heading structure
- Evaluate readability
- Identify missing elements
- Provide specific optimization steps

### 🎯 **Keyword Research**
```
Help me find good keywords for WordPress tutorial content
```
The agent will:
- Generate keyword suggestions
- Analyze search intent
- Assess keyword difficulty
- Provide content ideas
- Create content calendar

### 🖼️ **Image Optimization**
```
Check all my WordPress images and suggest alt text improvements
```
The agent will:
- Fetch all media items
- Identify missing alt text
- Evaluate existing alt text quality
- Generate keyword-rich suggestions
- Bulk update with confirmation

### 📍 **Local SEO**
```
Optimize my WordPress site for local SEO in [City, State]
```
The agent will:
- Research local keywords
- Recommend local schema markup
- Suggest local content strategy
- Provide Google Business Profile tips
- Create local citation plan

---

## 🔒 Safety Features

### User Confirmation Required
All write operations require explicit confirmation:
```json
{
    "confirmed": "true"
}
```

### Backup Recommendations
- Test on staging environment first
- Backup site before bulk changes
- Review all changes before applying
- Use version control for content

### API Rate Limiting
- Respectful API usage
- Error handling and retries
- Timeout configurations

---

## 🔧 Configuration Options

### Required
- **WordPress URL**: Your WordPress site URL
- **WordPress Username**: Admin username
- **Application Password**: Generated from WordPress admin

### Optional APIs
- **SEMrush API**: Advanced keyword metrics
- **Ahrefs API**: Backlink analysis
- **Google Analytics**: Traffic data
- **Google Search Console**: Search performance

Store API credentials using the memory_save tool.

---

## 📊 SEO Scoring System

### Technical Audit Score (100 points)
- SSL/HTTPS: 20 points
- Robots.txt: 10 points
- XML Sitemap: 15 points
- Meta Tags: 25 points
- Schema Markup: 15 points
- Mobile Responsive: 15 points

### Content Score (100 points)
- Word Count: 20 points
- Keyword Optimization: 30 points
- Heading Structure: 20 points
- Content Quality: 30 points

### Rating Scale
- 80-100: **Excellent** ✅
- 60-79: **Good** 👍
- 40-59: **Fair** ⚠️
- 0-39: **Needs Improvement** ❌

---

## 🎓 SEO Best Practices Enforced

### Content
- 600-2000 words for competitive keywords
- 0.5-2.5% keyword density (natural usage)
- One H1 per page, multiple H2/H3 for structure
- Keyword in first 100 words
- Flesch reading ease score above 50

### Technical
- HTTPS required for all pages
- Mobile-responsive design
- Page speed under 3 seconds
- Valid schema markup
- Clean URL structure

### WordPress
- SEO plugin installed and configured
- Optimized permalinks
- Image compression
- Caching enabled
- Regular updates

---

## 🚧 Troubleshooting

### WordPress API 401 Error
- Verify application password is correct
- Check username is exact (case-sensitive)
- Ensure REST API is enabled
- Check for security plugin restrictions

### Tool Not Found
- Verify files in `python/tools/` directory
- Check tool names match exactly
- Restart Agent Zero

### Limited Keyword Data
- Consider integrating paid APIs
- Use Google Keyword Planner
- Supplement with manual research

---

## 📈 Roadmap & Future Enhancements

### Planned Features
- [ ] Google Analytics 4 integration
- [ ] Google Search Console API integration
- [ ] Backlink analysis tool
- [ ] Automated reporting (PDF/HTML export)
- [ ] Multi-site support
- [ ] Automated A/B testing suggestions
- [ ] Social media optimization integration
- [ ] Voice search optimization
- [ ] Core Web Vitals monitoring

### API Integrations
- [ ] SEMrush full integration
- [ ] Ahrefs full integration
- [ ] Moz API support
- [ ] DataForSEO integration
- [ ] Screaming Frog API

---

## 🤝 Contributing

Contributions are welcome! Areas to improve:

1. **Additional Tools**: Create new SEO-focused tools
2. **API Integrations**: Add support for more SEO services
3. **Prompts**: Improve system prompts and tool descriptions
4. **Documentation**: Expand examples and use cases
5. **Testing**: Add test cases for SEO tools

---

## 📄 License

This SEO specialization maintains the same license as Agent Zero core project.

---

## 🙏 Acknowledgments

Built on top of:
- **Agent Zero**: Dynamic AI agent framework
- **WordPress REST API**: Content management
- **Google Search Guidelines**: SEO best practices
- **Yoast SEO / RankMath**: Metadata standards

---

## 📞 Support

For issues or questions:

1. Check [SEO Agent Setup Guide](docs/SEO_AGENT_SETUP.md)
2. Review [Example Interactions](docs/SEO_AGENT_EXAMPLES.md)
3. Consult main [Agent Zero Documentation](docs/README.md)
4. WordPress REST API: https://developer.wordpress.org/rest-api/

---

## 🎯 Example Interaction

```
User: Hi, I need help optimizing my WordPress blog for SEO

Agent: Hello! I'm Agent Zero, specialized in WordPress SEO. I can help you with:

- Technical SEO audits and fixes
- Keyword research and content strategy
- WordPress content optimization
- Performance and mobile optimization

To get started, what would you like to focus on first?
1. Run a complete SEO audit
2. Optimize existing content
3. Research keywords for new content
4. Fix specific SEO issues

User: Let's start with a complete audit

Agent: Great! I'll need your WordPress site URL to begin.
Have you set up WordPress REST API access yet?

[... continues with setup and audit ...]
```

---

## 🌟 Key Differentiators

Unlike generic SEO tools, Agent Zero SEO:

✅ **Conversational Interface**: Natural language interaction
✅ **Context Aware**: Remembers previous conversations and decisions
✅ **Customizable**: Fully extensible with custom tools and prompts
✅ **WordPress Native**: Deep integration with WordPress ecosystem
✅ **Action Oriented**: Provides specific, implementable recommendations
✅ **Safety First**: Confirmation required before any changes
✅ **Learning System**: Can save successful strategies to memory

---

**Ready to optimize your WordPress site for search engines?**

Start with the [Setup Guide](docs/SEO_AGENT_SETUP.md) and begin your SEO journey! 🚀
