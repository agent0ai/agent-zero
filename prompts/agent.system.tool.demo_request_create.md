### demo_request_create:
Create a demo request in the shared demo-request store used by the web dashboard and API.

Use this when the user asks to submit or create a new demo request.

Expected `tool_args`:
- `company` (required)
- `email` (required)
- `industry` (optional)
- `teamSize` (optional)
- Other request metadata fields are accepted and stored.

Example:
```json
{
  "tool_name": "demo_request_create",
  "tool_args": {
    "company": "Acme Health",
    "email": "ops@acmehealth.example",
    "industry": "healthcare",
    "teamSize": "50-500"
  }
}
```
