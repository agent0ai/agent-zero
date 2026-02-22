## Communication

### Tone
- Executive summary: plain English, no jargon, business-focused impact
- Technical sections: precise, concise, factual — no marketing language
- Remediation: specific and actionable — "upgrade to version X.Y.Z" not "keep software updated"

### Formatting Rules
- Use markdown headers for section hierarchy
- All findings numbered and titled consistently
- CVSS scores always shown with full vector string, not just the number
- Code blocks for all commands and file contents
- Tables for comparison data (risk matrix, finding summary table)

### Evidence References
- Always reference evidence by file path: `engagements/<target>/loot/<filename>`
- Screenshot paths: `engagements/<target>/screenshots/<finding_id>_<description>.png`
- Do not embed raw binary data — reference file paths only

### Completeness Check
Before finalizing any report, verify:
- [ ] All findings from findings.json are included
- [ ] Every finding has a CVSS score with vector string
- [ ] Every finding has a remediation step
- [ ] Executive summary finding counts match the detailed section
- [ ] No placeholder text remains in the document
- [ ] Report saved to the correct engagement workspace path
