## report_generator
Generate a professional penetration test report from structured findings data.
Use at the end of the engagement after all findings have been logged via findings_tracker.

### Actions
- `generate` — produce a full report in the requested format
- `preview` — generate executive summary only (useful for quick status update)

### Arguments
- `action` — "generate" (default) or "preview"
- `target` — engagement name (same as used in engagement_init)
- `format` — "markdown" (default), "html", or "pdf"
- `title` — report title (default: "Penetration Test Report")
- `client` — client / organization name (default: "[Client Name]")
- `tester` — tester name (default: "Agent Zero Security Assessment")

### Report Sections Generated
1. Cover page with metadata and overall risk rating
2. Executive summary (non-technical, top 3 findings highlighted)
3. Risk rating matrix (severity definitions and CVSS ranges)
4. Findings (sorted by CVSS score, each with description, PoC steps, evidence, remediation)

### Output Paths
- Markdown: `engagements/<target>/reports/report.md`
- HTML: `engagements/<target>/reports/report.html`
- PDF: `engagements/<target>/reports/report.pdf` (requires weasyprint)

### Usage

```json
{
    "thoughts": ["All findings are logged. Time to generate the final client report."],
    "headline": "Generating penetration test report for client",
    "tool_name": "report_generator",
    "tool_args": {
        "action": "generate",
        "target": "corp-external",
        "format": "html",
        "title": "External Penetration Test Report",
        "client": "Acme Corporation",
        "tester": "Agent Zero Red Team"
    }
}
```

```json
{
    "thoughts": ["Let me preview the executive summary before full report generation."],
    "headline": "Previewing executive summary",
    "tool_name": "report_generator",
    "tool_args": {
        "action": "preview",
        "target": "corp-external"
    }
}
```
