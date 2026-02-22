## cve_lookup
Look up CVE details and find known public exploits from NVD and ExploitDB.
Use this after identifying a service version to check for known vulnerabilities.

### Actions
- `lookup_cve` — fetch details for a specific CVE ID
- `search_product` — search for CVEs affecting a product and version

### Arguments
- `action` — "lookup_cve" or "search_product"
- `cve_id` — CVE identifier, e.g. "CVE-2021-44228" (required for lookup_cve)
- `product` — product or service name, e.g. "Apache" or "OpenSSH" (required for search_product)
- `version` — specific version string, e.g. "2.4.49" (optional, improves accuracy)

### Returns
- CVSS score and vector string
- CVE description
- Reference URLs (NVD, vendor advisory, PoC repositories)
- Suggested next steps: searchsploit command, Metasploit search, GitHub search URL

### Usage

```json
{
    "thoughts": ["Nmap found Apache 2.4.49. Let me check for known CVEs."],
    "headline": "Searching CVEs for Apache 2.4.49",
    "tool_name": "cve_lookup",
    "tool_args": {
        "action": "search_product",
        "product": "Apache",
        "version": "2.4.49"
    }
}
```

```json
{
    "thoughts": ["I found CVE-2021-41773 mentioned in searchsploit — let me get full details."],
    "headline": "Looking up CVE-2021-41773 details",
    "tool_name": "cve_lookup",
    "tool_args": {
        "action": "lookup_cve",
        "cve_id": "CVE-2021-41773"
    }
}
```

**After cve_lookup:** Always follow up with `searchsploit` via code_execution to check for local PoC, and check Metasploit modules: `msfconsole -q -x 'search cve:<year>-<id>; exit'`
