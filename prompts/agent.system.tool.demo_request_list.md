### demo_request_list:
List recent demo requests from the shared demo-request store.

Use this when the user asks to review submitted demo requests or latest leads.

Expected `tool_args`:
- `limit` (optional, default 25)

Example:
```json
{
  "tool_name": "demo_request_list",
  "tool_args": {
    "limit": 10
  }
}
```
