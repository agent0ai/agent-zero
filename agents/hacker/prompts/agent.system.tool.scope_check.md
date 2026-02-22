## scope_check
Verify that a target IP, domain, or URL is within the defined engagement scope before testing.
Always run this before active scanning or exploitation of any host.

### Actions
- `check` — verify a specific value against scope.txt
- `show` — display all current scope entries

### Arguments
- `action` — "check" (default) or "show"
- `target` — engagement name (same as used in engagement_init)
- `value` — IP, CIDR, domain, or URL to check (required for "check")

### Scope Entry Formats Supported
- Individual IP: `192.168.1.1`
- CIDR range: `10.10.10.0/24`
- Domain: `example.com`
- Wildcard subdomain: `*.example.com` (matches sub.example.com, dev.example.com, etc.)

### Usage

```json
{
    "thoughts": ["Before scanning, I must confirm 10.10.10.5 is in scope."],
    "headline": "Verifying target is within engagement scope",
    "tool_name": "scope_check",
    "tool_args": {
        "action": "check",
        "target": "corp-external",
        "value": "10.10.10.5"
    }
}
```

```json
{
    "thoughts": ["Let me review what is in scope for this engagement."],
    "headline": "Displaying engagement scope",
    "tool_name": "scope_check",
    "tool_args": {
        "action": "show",
        "target": "corp-external"
    }
}
```

**Important:** If scope_check returns OUT OF SCOPE, do not proceed with active testing against that target. Report the out-of-scope finding to the user and request scope confirmation.
