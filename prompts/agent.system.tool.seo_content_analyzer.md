## seo_content_analyzer tool

analyze content for seo optimization and provide actionable recommendations

### tool capabilities
- comprehensive content seo analysis
- keyword density and usage analysis
- heading structure and hierarchy evaluation
- readability assessment flesch score
- seo score calculation 0-100
- identify missing seo elements
- multi-keyword analysis

### usage examples

comprehensive content analysis:
```json
{
    "tool_name": "seo_content_analyzer",
    "tool_args": {
        "action": "analyze_content",
        "content": "<h1>Page Title</h1><p>Content here...</p>",
        "target_keyword": "wordpress seo"
    }
}
```

check keyword density:
```json
{
    "tool_name": "seo_content_analyzer",
    "tool_args": {
        "action": "check_keyword_density",
        "content": "Your content text here",
        "keywords": ["seo", "wordpress", "optimization"]
    }
}
```

analyze heading structure:
```json
{
    "tool_name": "seo_content_analyzer",
    "tool_args": {
        "action": "analyze_headings",
        "content": "<h1>Title</h1><h2>Section</h2>"
    }
}
```

check readability:
```json
{
    "tool_name": "seo_content_analyzer",
    "tool_args": {
        "action": "check_readability",
        "content": "Your content text to analyze for readability"
    }
}
```

find missing elements:
```json
{
    "tool_name": "seo_content_analyzer",
    "tool_args": {
        "action": "find_missing_elements",
        "content": "<html>page content</html>"
    }
}
```

### analysis features
- word count sentence count character count
- keyword density optimal range 0.5-2.5%
- keyword placement first paragraph headings
- heading hierarchy h1 h2 h3 structure
- flesch reading ease score
- overall seo score with rating
- actionable recommendations prioritized

### seo scoring criteria
- word count 300-3000 words optimal
- keyword in h1 title first paragraph
- proper heading hierarchy one h1 multiple h2
- adequate keyword density not stuffing
- content quality links images readability

### best practices recommendations
- aim for 600-2000 words for competitive keywords
- keyword density 0.5-2.5% natural usage
- one h1 per page multiple h2 h3 for structure
- include keyword in first 100 words
- flesch score above 50 for web content
- add internal external links
- include images with alt text
- write for users first seo second
