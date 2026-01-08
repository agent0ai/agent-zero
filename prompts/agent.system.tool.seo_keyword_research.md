## seo_keyword_research tool

comprehensive keyword research and analysis for seo strategy

### tool capabilities
- generate keyword suggestions from seed keywords
- analyze keyword metrics and intent
- find related questions people also ask
- create local seo keyword variations
- assess keyword difficulty (basic or api-based)
- competitor keyword analysis (with api integration)

### api integration support
supports optional api integration for advanced features:
- semrush_api_key for semrush data
- ahrefs_api_key for ahrefs data
- store api keys using memory_save tool

### usage examples

keyword suggestions:
```json
{
    "tool_name": "seo_keyword_research",
    "tool_args": {
        "action": "suggest_keywords",
        "seed_keyword": "wordpress seo"
    }
}
```

analyze specific keyword:
```json
{
    "tool_name": "seo_keyword_research",
    "tool_args": {
        "action": "analyze_keyword",
        "keyword": "best wordpress seo plugins"
    }
}
```

find related questions:
```json
{
    "tool_name": "seo_keyword_research",
    "tool_args": {
        "action": "related_questions",
        "keyword": "wordpress optimization"
    }
}
```

local keyword variations:
```json
{
    "tool_name": "seo_keyword_research",
    "tool_args": {
        "action": "local_keyword_suggestions",
        "keyword": "seo services",
        "location": "New York"
    }
}
```

keyword difficulty:
```json
{
    "tool_name": "seo_keyword_research",
    "tool_args": {
        "action": "keyword_difficulty",
        "keyword": "wordpress seo"
    }
}
```

### keyword analysis features
- classifies keywords by length short-tail medium-tail long-tail
- identifies search intent informational commercial transactional
- provides google autocomplete suggestions
- generates question-based variations
- offers optimization tips and content strategy

### best practices
- start with broad seed keywords then narrow down
- focus on long-tail keywords for easier ranking
- match content to search intent
- target local keywords for local businesses
- analyze competitor keywords for gap analysis
- track keyword performance over time
