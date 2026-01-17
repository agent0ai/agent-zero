### calendar_hub

Calendar Hub for mock-friendly calendar integration. Supports event CRUD and account linking.

Actions:
- `connect_account(provider, mock=true)`
- `list_accounts()`
- `get_auth_url(provider)`
- `list_calendars(account_id)`
- `list_events(calendar_id=null, limit=25)`
- `create_event(calendar_id, title, start, end, attendees=[], notes="")`
- `set_rules(account_id, rules={...})`
- `get_rules(account_id)`
- `generate_prep(event_id, sources=["gmail"])`
- `create_followup(event_id, summary, due_at)`
- `update_event(event_id, updates={...})`
- `delete_event(event_id)`

Examples:
```
{{calendar_hub(action="connect_account", provider="google", mock=true)}}
{{calendar_hub(action="list_calendars", account_id=1)}}
{{calendar_hub(action="create_event", calendar_id=1, title="Kickoff", start="2025-01-01T10:00:00Z", end="2025-01-01T10:30:00Z")}}
```
