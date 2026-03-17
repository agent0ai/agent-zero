### persona_create:

Create and store a persona for survey answering (primarily for testing/synthetic scenarios).

- **name**: persona name
- **description**: short description
- **constraints_json**: JSON object with stable constraints (demographics/preferences/traits)
- **generate**: if `true`, drafts persona from **seed** using the utility model
- **seed**: prompt/seed text used when generating

usage:
```json
{
  "thoughts": ["I need a testing persona for a synthetic survey."],
  "tool_name": "persona_create",
  "tool_args": {
    "generate": true,
    "seed": "A 32-year-old software engineer in Berlin who prefers Android and avoids alcohol."
  }
}
```

