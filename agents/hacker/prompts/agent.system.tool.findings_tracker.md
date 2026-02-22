## findings_tracker
Track structured vulnerability findings during a penetration test engagement.
Use this tool to record every confirmed vulnerability as you find it — do not wait until the end.

### Actions
- `add_finding` — add a new vulnerability
- `list_findings` — list all findings (supports severity_filter and status_filter)
- `get_finding` — get full details of one finding by ID
- `update_finding` — update an existing finding (e.g. add evidence, change status)
- `export_findings` — export all findings as formatted text for reporting

### Core Arguments (all actions)
- `action` — action name
- `target` — engagement name (same as used in engagement_init)

### Arguments for add_finding
- `title` — short, descriptive finding title (required)
- `severity` — critical / high / medium / low / informational
- `cvss_score` — CVSS 3.1 base score (e.g. 9.8)
- `host` — target IP or hostname
- `port` — affected port number
- `service` — service name and version (e.g. "Apache 2.4.41")
- `cve` — CVE ID if applicable (e.g. "CVE-2021-41773")
- `description` — clear explanation of the vulnerability
- `steps_to_reproduce` — numbered steps to replicate
- `evidence` — path to evidence files in the engagement workspace
- `remediation` — specific fix recommendation
- `status` — confirmed / unconfirmed / exploited / patched (default: confirmed)

### Usage

```json
{
    "thoughts": ["I confirmed RCE via CVE-2021-41773 — I need to log this finding now."],
    "headline": "Recording critical finding: Apache path traversal RCE",
    "tool_name": "findings_tracker",
    "tool_args": {
        "action": "add_finding",
        "target": "10.10.10.5",
        "title": "Apache 2.4.49 Path Traversal / RCE (CVE-2021-41773)",
        "severity": "critical",
        "cvss_score": 9.8,
        "host": "10.10.10.5",
        "port": "80",
        "service": "Apache httpd 2.4.49",
        "cve": "CVE-2021-41773",
        "description": "Apache 2.4.49 fails to properly normalize paths before access control checks, allowing unauthenticated attackers to traverse directories and execute commands via mod_cgi.",
        "steps_to_reproduce": "1. curl -v 'http://10.10.10.5/cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh' --data 'echo Content-Type: text/plain; echo; id'",
        "evidence": "loot/apache_rce_id_output.txt",
        "remediation": "Upgrade Apache to 2.4.50 or later immediately. Disable mod_cgi if not required.",
        "status": "exploited"
    }
}
```

```json
{
    "thoughts": ["Let me review all findings so far."],
    "headline": "Listing all engagement findings",
    "tool_name": "findings_tracker",
    "tool_args": {
        "action": "list_findings",
        "target": "10.10.10.5"
    }
}
```
