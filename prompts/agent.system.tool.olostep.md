### olostep:
web scraping and search tool via Olostep API
scrape: extract markdown/html/text from any url
search: AI-powered web search with answers
google: structured Google search results
map: discover all urls on a website

**Example usages**:
~~~json
{
    "thoughts": ["I need webpage content"],
    "headline": "Scraping webpage",
    "tool_name": "olostep",
    "tool_method": "scrape",
    "tool_args": {
        "url": "https://example.com/article"
    }
}
~~~

~~~json
{
    "thoughts": ["I need to search for information"],
    "headline": "Searching web",
    "tool_name": "olostep",
    "tool_method": "search",
    "tool_args": {
        "query": "What is the capital of France?"
    }
}
~~~

~~~json
{
    "thoughts": ["I need Google search results"],
    "headline": "Google search",
    "tool_name": "olostep",
    "tool_method": "google",
    "tool_args": {
        "query": "best python libraries 2024"
    }
}
~~~

~~~json
{
    "thoughts": ["I need to find all pages on this site"],
    "headline": "Mapping website",
    "tool_name": "olostep",
    "tool_method": "map",
    "tool_args": {
        "url": "https://docs.example.com"
    }
}
~~~
