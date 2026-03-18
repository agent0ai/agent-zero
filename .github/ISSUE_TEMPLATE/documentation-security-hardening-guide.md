---
    title: "📝 Documentation: Security Hardening Guide"
    labels: "documentation, security"
    ---

    ## Purpose

    This guide documents **how to securely deploy Agent Zero in production**.

    It consolidates all security recommendations into a single, actionable checklist.

    ## Target Audience

    - DevOps engineers deploying Agent Zero
    - Security teams reviewing the platform
    - System administrators maintaining production instances

    ## Checklist

    > **⚠️ WARNING:** Agent Zero out-of-the-box is **NOT SECURE** for internet-facing deployments.

    ### Pre-Deployment

    - [ ] Review and understand the threat model
    - [ ] Read all security-related issues in GitHub
    - [ ] Apply all security patches from upstream
    - [ ] Fork repository and maintain your own security patches
    - [ ] Set up vulnerability scanning (Snyk, Dependabot)
    - [ ] Enable Docker content trust (Notary)
    - [ ] Use private container registry with access controls

    ### Container Hardening

    - [ ] **NON-ROOT USER:** Container runs as UID/GID 1000+ (not 0)
    - [ ] **CAPABILITIES:** Drop ALL except `CAP_NET_BIND_SERVICE` if needed
    - [ ] **SECCOMP:** Apply seccomp profile restricting syscalls
    - [ ] **APPARMOR/SELINUX:** Enabled and profiles loaded
    - [ ] **READ-ONLY FS:** Filesystem mounted read-only except `/tmp`, `/run`, `/usr/data`
    - [ ] **NO NEW PRIVILEGES:** Set `no-new-privileges: true` in Docker
    - [ ] **RESOURCE LIMITS:** Set `mem_limit`, `cpu_quota`, `pids_limit`
    - [ ] **USER NS REMAP:** Enable user namespace remapping (kernel 4.9+)

    Example docker-compose security section:

    ```yaml
    services:
      agent-zero:
        user: "1000:1000"
        cap_drop:
          - ALL
        cap_add:
          - NET_BIND_SERVICE  # Only if binding to ports <1024
        security_opt:
          - no-new-privileges:true
          - seccomp:/path/to/seccomp-profile.json
          - apparmor:docker-agent-zero
        read_only: true
        tmpfs:
          - /tmp
          - /run
        mem_limit: 2g
        cpu_quota: 50000  # 50% of one core
        pids_limit: 100
    ```

    ### Secret Management

    - [ ] **ENCRYPTION AT REST:** All secrets encrypted (Docker secrets, Vault)
    - [ ] **NO PLAINTEXT FILES:** No `secrets.env` with clear text
    - [ ] **SECRET SCANNING:** Run `truffleHog` or `git-secrets` on repo
    - [ ] **ROTATION:** Process for rotating API keys, passwords
    - [ ] **ACCESS CONTROL:** Only owner and RBAC roles can access secrets
    - [ ] **AUDIT LOGGING:** All secret access logged

    ### Network Security

    - [ ] **FIREWALL:** Only expose necessary ports (typically 80/443)
    - [ ] **SSH:** Disabled if not needed, or bind to 127.0.0.1 only
    - [ ] **WAF:** Place behind Web Application Firewall (Cloudflare, ModSecurity)
    - [ ] **VPN/TUNNEL:** Consider private network access only
    - [ ] **RATE LIMITING:** Per-IP rate limits on API endpoints
    - [ ] **TLS 1.3:** Enforce modern TLS, disable weak ciphers
    - [ ] **HSTS:** HTTP Strict Transport Security headers

    ### Authentication & Authorization

    - [ ] **STRONG PASSWORDS:** Default passwords changed
    - [ ] **MFA:** Enable multi-factor auth for web UI (if implemented)
    - [ ] **SESSION SECURITY:** Secure cookies, HttpOnly, SameSite=Strict
    - [ ] **CSRF TOKENS:** All state-changing operations require CSRF token
    - [ ] **JWT EXPIRY:** Short-lived tokens (1 hour max)
    - [ ] **RBAC:** Implement role-based access control
    - [ ] **AUDIT LOG:** All authentication events logged

    ### Data Protection

    - [ ] **ENCRYPTION IN TRANSIT:** All external APIs use TLS
    - [ ] **PII REDACTION:** Personal data in logs redacted
    - [ ] **BACKUP ENCRYPTION:** Backups encrypted at rest
    - [ ] **DATA RETENTION:** Automated cleanup of old logs/chats
    - [ ] **GDPR/CCPA:** Mechanisms for data export/deletion
    - [ ] **ENCRYPT FAISS:** Memory indexes encrypted (future)

    ### LLM Provider Security

    - [ ] **API KEYS:** Stored in secrets system (not .env)
    - [ ] **PER-MODEL KEYS:** Different keys per provider (no sharing)
    - [ ] **LEAK PREVENTION:** LLM prompts filtered to not leak keys
    - [ ] **COST LIMITS:** Set monthly budgets per provider
    - [ ] **WEBHOOK VERIFICATION:** If using webhooks, verify signatures
    - [ ] **ALLOWLIST:** Restrict to approved models only

    Example config:

    ```json
    {
      "allowed_models": [
        "openai/gpt-4",
        "anthropic/claude-3-opus"
      ],
      "provider_cost_limits": {
        "openai": 1000,  // $1000/month
        "anthropic": 500
      }
    }
    ```

    ### Monitoring & Alerting

    - [ ] **LOG COLLECTION:** All JSON logs shipped to SIEM (Loki, ELK)
    - [ ] **METRICS:** Prometheus scraping configured
    - [ ] **ALERTS:** Critical alerts defined (high error rate, auth failures)
    - [ ] **AUDIT TRAIL:** Immutable audit log for compliance
    - [ ] **INTRUSION DETECTION:** File integrity monitoring (Aide, Tripwire)
    - [ ] **VULNERABILITY SCANNING:** Daily scans, auto-PR for updates

    ### Dependency Security

    - [ ] **PINNED VERSIONS:** All dependencies have exact versions
    - [ ] **SCAN FOR VULNS:** `safety check` or `snyk test` in CI
    - [ ] **UPDATE POLICY:** Weekly dependency review
    - [ ] **LICENSE COMPLIANCE:** All licenses compatible with your use
    - [ ] **NO DEV DEPS IN PROD:** `requirements.txt` excludes dev packages

    ### Access Control

    - [ ] **MINIMAL PRINCIPLE:** Grant minimum necessary access
    - [ ] **SEPARATION OF DUTIES:** Different credentials for dev/prod
    - [ ] **ACCESS REVIEW:** Quarterly review of who has access
    - [ ] **OFFBOARDING:** Immediate revocation when employee leaves
    - [ ] **PRIVILEGED ACCESS:** Session recording for admin actions

    ### Backup & Disaster Recovery

    - [ ] **ENCRYPTED BACKUPS:** Backups encrypted with separate key
    - [ ] **OFFSITE REPLICATION:** Backups stored in different region
    - [ ] **RESTORE DRILLS:** Test restore quarterly
    - [ ] **RPO/RTO:** Defined recovery point/objectives
    - [ ] **BACKUP RETENTION:** 30+ days with incremental
    - [ ] **BACKUP ENCRYPTION:** Separate key from runtime secrets

    ### Compliance (if applicable)

    - [ ] **SOC2 Type II:**审计日志、访问控制、加密
    - [ ] **ISO 27001:** 信息安全管理
    - [ ] **HIPAA:** 医疗数据处理（如果适用）
    - [ ] **PCI DSS:** 支付卡数据（如果适用）
    - [ ] **GDPR:** 数据主体权利、隐私影响评估
    - [ ] **CCPA:** 加州消费者隐私法

    ## Threat Model

    | Threat | Likelihood | Impact | Mitigation |
    |--------|------------|--------|------------|
    | Container escape | Low | Critical | Non-root, seccomp, AppArmor |
    | Secrets theft | Medium | Critical | Encryption, access control |
    | Data breach | Medium | High | Network isolation, WAF |
    | LLM prompt injection | High | Medium | Input validation, sandboxing |
    | DoS via tool abuse | Medium | Medium | Rate limiting, resource caps |
    | Insider threat | Low | Critical | RBAC, audit logs, separation |

    ## Incident Response

    If you suspect a security incident:

    1. **Contain:** Stop container, isolate network
    2. **Investigate:** Review audit logs, check for unauthorized access
    3. **Eradicate:** Revoke all secrets, rotate keys, rebuild from clean image
    4. **Recover:** Restore from clean backup, apply patches
    5. **Post-mortem:** Document lessons learned

    ## Security Contacts

    - **Security Issues:** GitHub Security Advisory (private)
    - **Questions:** security@agent-zero.ai (hypothetical)
    - **Status Page:** status.agent-zero.ai

    ## References

    - [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker/)
    - [OWASP Docker Top 10](https://owasp.org/www-project-docker-top-10/)
    - [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
    - [Anthropic Security Best Practices](https://docs.anthropic.com/claude/docs/security-best-practices)

    ---
    *Last updated: 2024-01-15*

    *This document is a living guide - update as security landscape evolves.*
    