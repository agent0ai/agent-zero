# Digest Builder Tool

Build daily or weekly digests from ingested items.

## Actions

### build_digest

```
{{digest_builder(
  action="build_digest",
  window_hours=24,
  max_items_per_section=3,
  channel="telegram"
)}}
```

### list_digests

```
{{digest_builder(action="list_digests", limit=10)}}
```

### build_architecture_review

```
{{digest_builder(
  action="build_architecture_review",
  context="Problem brief",
  options=[
    {"title": "Option A", "tradeoffs": ["Fast to implement", "Higher cost"]},
    {"title": "Option B", "tradeoffs": ["Lower cost", "More complexity"]}
  ],
  decision="Choose Option A for speed to market",
  follow_ups=["Validate costs with finance", "Create ADR ticket"],
  open_questions=["Which region to deploy first?"]
)}}
```
