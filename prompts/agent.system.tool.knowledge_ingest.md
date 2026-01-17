# Knowledge Ingest Tool

Ingest knowledge from RSS feeds, web pages, or direct text into the knowledge base and tracking database.

## Actions

### register_source

```
{{knowledge_ingest(
  action="register_source",
  name="Cloud Architecture RSS",
  source_type="rss",
  uri="https://example.com/rss.xml",
  tags=["architecture", "cloud"],
  cadence="daily",
  config={}
)}}
```

### list_sources

```
{{knowledge_ingest(action="list_sources")}}
```

### ingest_source

```
{{knowledge_ingest(action="ingest_source", source_id=1, max_items=10)}}
```

### ingest_all

```
{{knowledge_ingest(action="ingest_all", max_items=10)}}
```

### ingest_text

```
{{knowledge_ingest(
  action="ingest_text",
  title="Architecture Note",
  content="Short insight or decision",
  tags=["architecture"],
  confidence=0.8
)}}
```

### ingest_mcp

```
{{knowledge_ingest(
  action="ingest_mcp",
  tool_name="brave-search.search",
  tool_args={"query": "cloud architecture trends", "count": 5},
  title="Brave Search: Cloud Architecture",
  tags=["architecture", "search"]
)}}
```
