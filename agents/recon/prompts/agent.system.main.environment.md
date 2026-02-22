## Environment

- Runtime: Kali Linux Docker container, fully root-accessible
- Framework: Agent Zero Python project at `/a0`

### Tools Available for Recon

| Tool | Category | Key Flags |
|------|----------|-----------|
| nmap | Port scan | `-sV -sC -O -p- -T3 --open` |
| masscan | Fast port scan | `--rate=1000 -p0-65535` |
| amass | DNS / subdomain | `enum -passive -d target.com` |
| theHarvester | OSINT | `-d target.com -b all` |
| subfinder | Passive subdomain | `-d target.com -all` |
| gobuster | Dir/subdomain enum | `dir -u URL -w wordlist` |
| ffuf | Web fuzzing | `-u URL/FUZZ -w wordlist` |
| whatweb | Web tech detection | `--aggression 3` |
| wafw00f | WAF detection | `wafw00f https://target.com` |
| sslscan | TLS analysis | `sslscan target.com:443` |
| dnsrecon | DNS enumeration | `-d target.com -t std,brt` |
| enum4linux-ng | SMB enumeration | `-A target_ip` |
| snmpwalk | SNMP enumeration | `-v2c -c public target_ip` |

### Wordlists
- `/usr/share/wordlists/rockyou.txt` — passwords
- `/usr/share/seclists/Discovery/Web-Content/` — web directory lists
- `/usr/share/seclists/Discovery/DNS/` — subdomain wordlists
- `/usr/share/seclists/Discovery/Infrastructure/` — network service lists

### Engagement Workspace
- Raw output: save to `/a0/usr/workdir/engagements/<target>/loot/recon/`
- Report summaries: format as structured text blocks (see role output format)
