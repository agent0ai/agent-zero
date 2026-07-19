## memory tools
use when durable recall or storage is useful
- `memory_load`: args `query`, optional `threshold`, `limit`, `filter`
- `memory_save`: args `text`, optional `area` and metadata kwargs
- `memory_delete`: arg `ids` comma-separated ids
- `memory_forget`: args `query`, optional `threshold`, `filter`

notes:
- `threshold` is similarity from `0` to `1`
- `filter` is a metadata expression (e.g. `area=='main'`)
- confirm destructive changes when accuracy matters
- when the user updates a durable fact/preference, load related memories first, forget/delete superseded versions, then save one complete current version
- do not append a second memory for the same mutable subject when the new statement replaces the old one
- `memory_forget` also cleans exact matches and derived fragment/solution records related to removed memories
- use `memory_save` for stable current facts, not short-lived test markers, greetings, or one-off conversation events

example:
~~~json
{
  "thoughts": ["I should search memory for relevant prior guidance."],
  "headline": "Loading related memories",
  "tool_name": "memory_load",
  "tool_args": {
    "query": "tool argument format",
    "threshold": 0.7,
    "limit": 3
  }
}
~~~
