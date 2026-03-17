### survey_fill:

Fill out an online survey in the built-in Playwright browser and store answers to a local profile database for later refinement.

- **url**: survey URL to open (optional if a page is already open)
- **profile_id**: profile identifier (default: `"default"`)
- **persona_id**: optional persona ID created via `persona_create`
- **allow_persona**: set `true` only if you have explicit permission to answer as a persona (default: `false`)
- **allow_external**: set `true` only for domains you own/are authorized to automate (default: `false`)
- **max_pages**: safety cap for multi-page surveys (default: `12`)
- **use_llm**: allow utility model to refine the action plan (default: `true`)

External domains are blocked unless:

- env `A0_SURVEY_ALLOWED_DOMAINS` includes the survey host (comma-separated), and
- `allow_external=true` is provided.

usage:
```json
{
  "thoughts": ["I'll open the survey and answer using the stored profile."],
  "tool_name": "survey_fill",
  "tool_args": {
    "url": "https://example.com/survey",
    "profile_id": "default",
    "allow_external": true,
    "max_pages": 10,
    "use_llm": true
  }
}
```

