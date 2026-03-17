### profile_update:

Update the structured survey profile (stored in SQLite) by deep-merging a JSON patch.

- **profile_id**: profile identifier (default: `"default"`)
- **patch_json**: JSON object to merge into the profile

Example (set email):
```json
{
  "tool_name": "profile_update",
  "tool_args": {
    "profile_id": "default",
    "patch_json": "{\"contact\":{\"email\":\"<your-email>\"}}"
  }
}
```

Tip: you can also set env `A0_PROFILE_EMAIL` and the survey answerer will use it as a fallback for email fields.

