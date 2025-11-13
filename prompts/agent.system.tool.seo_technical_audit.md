## seo_technical_audit tool

perform comprehensive technical seo audits and site health checks

### tool capabilities
- full technical seo audit with scoring
- robots txt verification
- xml sitemap detection and analysis
- ssl https configuration check
- meta tags analysis title description viewport
- structured data schema markup detection
- mobile responsiveness check
- basic page speed analysis

### usage examples

full technical audit:
```json
{
    "tool_name": "seo_technical_audit",
    "tool_args": {
        "action": "full_audit",
        "site_url": "https://example.com"
    }
}
```

check robots txt:
```json
{
    "tool_name": "seo_technical_audit",
    "tool_args": {
        "action": "check_robots",
        "site_url": "https://example.com"
    }
}
```

check sitemap:
```json
{
    "tool_name": "seo_technical_audit",
    "tool_args": {
        "action": "check_sitemap",
        "site_url": "https://example.com"
    }
}
```

check meta tags:
```json
{
    "tool_name": "seo_technical_audit",
    "tool_args": {
        "action": "check_meta_tags",
        "site_url": "https://example.com"
    }
}
```

### audit scoring
full audit provides score out of 100:
- ssl https 20 points
- robots txt 10 points
- xml sitemap 15 points
- meta tags 25 points
- schema markup 15 points
- mobile responsive 15 points

rating scale:
- 80-100 excellent
- 60-79 good
- 40-59 fair
- 0-39 poor needs immediate attention

### critical checks
- https ssl certificate required for ranking
- robots txt guides search engines
- xml sitemap helps indexing
- meta tags title description critical
- mobile responsiveness required
- page speed affects rankings

### recommendations output
provides actionable recommendations for each issue found
prioritizes critical issues first
