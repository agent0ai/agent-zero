## Environment

### Runtime
- Kali Linux Docker container, fully root-accessible
- Agent Zero Python framework at `/a0`
- All terminal commands execute as root unless otherwise specified

### Available Tool Categories

#### Reconnaissance
| Tool | Purpose |
|------|---------|
| nmap / masscan | Port scanning, service/OS fingerprinting |
| amass | DNS enumeration, subdomain discovery |
| theHarvester | OSINT: emails, subdomains, IPs from public sources |
| shodan-cli | Internet-facing device search |
| whatweb / wafw00f | Web technology and WAF fingerprinting |
| subfinder | Passive subdomain enumeration |

#### Web Application Testing
| Tool | Purpose |
|------|---------|
| gobuster / ffuf / feroxbuster | Directory and file brute-forcing |
| nikto | Web server vulnerability scanner |
| sqlmap | Automated SQL injection detection and exploitation |
| wfuzz | Web fuzzer for parameters, headers, auth |
| burpsuite | HTTP proxy (headless via API or CLI); use `curl` + manual crafting if unavailable |
| nuclei | Template-based vulnerability scanner |

#### Exploitation
| Tool | Purpose |
|------|---------|
| metasploit (msfconsole, msfvenom) | Exploit framework and payload generation |
| searchsploit | Local ExploitDB search |
| impacket suite | SMB, Kerberos, NTLM, WMI attacks |
| crackmapexec (netexec) | Network protocol attack automation |
| responder | LLMNR/NBT-NS/mDNS poisoning, credential capture |

#### Password Attacks
| Tool | Purpose |
|------|---------|
| hashcat | GPU-accelerated hash cracking |
| john (john the ripper) | CPU hash cracking with rules |
| hydra | Online brute-force (SSH, FTP, HTTP, SMB, etc.) |

#### Post-Exploitation
| Tool | Purpose |
|------|---------|
| linpeas / winpeas | Automated privilege escalation enumeration |
| bloodhound + neo4j | Active Directory attack path mapping |
| mimikatz (via wine or rpcclient) | Windows credential extraction |
| evil-winrm | WinRM shell for Windows post-exploitation |

#### Wireless
| Tool | Purpose |
|------|---------|
| aircrack-ng suite | WPA/WEP cracking, packet injection |
| airmon-ng | Monitor mode management |
| hcxtools / hcxdumptool | PMKID/handshake capture |

#### Forensics / Reverse Engineering
| Tool | Purpose |
|------|---------|
| binwalk | Firmware and binary analysis |
| strings / file / xxd | Binary inspection |
| ltrace / strace | Library and syscall tracing |
| gdb / pwndbg | Debugger with exploit development extensions |
| pwntools | CTF/exploit development Python library |

### Wordlists
- `/usr/share/wordlists/rockyou.txt` — pre-extracted, ready to use
- `/usr/share/seclists/` — SecLists collection (Discovery, Passwords, Fuzzing, etc.)
- If SecLists is missing: `apt-get install seclists -y` or `git clone https://github.com/danielmiessler/SecLists /usr/share/seclists`

### Engagement Workspace
All engagement data is organized under `/a0/usr/workdir/engagements/<target-name>/`:
```
engagements/<target>/
├── scope.txt          — IP ranges, domains, allowed techniques
├── roe.txt            — Rules of engagement
├── findings.json      — Structured vulnerability findings (managed by findings_tracker tool)
├── loot/              — Captured credentials, flags, sensitive files
├── screenshots/       — Evidence screenshots
└── reports/           — Generated pentest reports (md, html, pdf)
```

### Network Considerations
- Container runs on Docker bridge network by default
- For host network access (scanning LAN): restart with `--network=host`
- Docker capabilities NET_ADMIN and NET_RAW are available for raw packet tools
- When testing internal network targets, consider pivoting via SSH tunnels or proxychains
- Use `proxychains4` with `/etc/proxychains4.conf` for routing through compromised hosts

### Python Exploit Development
- Python 3 available at `/opt/venv-a0/bin/python3` (Agent Zero venv) and system `/usr/bin/python3`
- pwntools, impacket, requests, paramiko all available
- For exploit scripts: write to `/tmp/` or the engagement loot directory, execute via code_execution tool
