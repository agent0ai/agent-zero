## Academic paper search tool:

### semantic_scholar
Search Semantic Scholar API for academic papers and research literature.
Returns paper metadata including titles, authors, citations, and abstracts.

usage:
~~~json
{
    "thoughts": [
        "I need to search for papers about transformer architectures",
        "I'll use semantic_scholar to find relevant research",
    ],
    "headline": "Searching academic papers about transformer architectures",
    "tool_name": "semantic_scholar",
    "tool_args": {
        "query": "transformer architecture attention mechanisms",
        "limit": 10,
        "fields": "title,authors,year,abstract,citationCount"
    }
}
~~~

Parameters:
- query (required): Search query string
- limit (optional): Maximum number of results (default: 10)
- fields (optional): Comma-separated fields to return (default: "title,authors,year,abstract,citationCount")

Available fields:
- title, authors, year, abstract
- citationCount, influentialCitationCount
- venue, publicationDate
- paperId, url, externalIds

Returns formatted list of papers with:
- Paper title and authors
- Publication year and citation count
- Abstract preview (truncated to 300 chars)

Note: Rate limited to 1 req/sec without API key, 10 req/sec with S2_API_KEY in .env
