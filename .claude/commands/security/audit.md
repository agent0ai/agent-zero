---
description: Comprehensive security audit for codebase and infrastructure
argument-hint: [--scope <code|infra|full>] [--severity <critical|high|all>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Grep, Read, Write
---

Security audit: **${ARGUMENTS}**

## Comprehensive Security Audit

**Audit Areas**:

- 🔐 Authentication & Authorization
- 🔒 Data encryption (at rest & in transit)
- 🚨 Input validation & XSS prevention
- 💉 SQL injection prevention
- 🔑 Secrets management
- 🛡️ Dependency vulnerabilities
- 🌐 API security (rate limiting, CORS)
- 📝 Audit logging
- 🔧 Infrastructure security (IAM, network)

Routes to **gcp-security-compliance** + **code-reviewer**:

```javascript
await Task({
  subagent_type: 'gcp-security-compliance',
  description: 'Execute security audit',
  prompt: `Execute comprehensive security audit:

Scope: ${SCOPE || 'full'}
Severity filter: ${SEVERITY || 'all'}

## 1. Authentication & Authorization Audit

### Check Authentication Implementation

Search for auth patterns:
\`\`\`bash
# Find authentication code
grep -r "authenticate\|login\|password\|token" --include="*.js" --include="*.ts" --include="*.py"

# Check for common auth vulnerabilities:
# - Hardcoded credentials
# - Weak password requirements
# - Missing MFA
# - Insecure session management
# - Missing CSRF protection
\`\`\`

**Security Checklist**:
- [ ] Passwords hashed with bcrypt/argon2 (not MD5/SHA1)
- [ ] Password requirements: 12+ chars, complexity
- [ ] MFA available for sensitive operations
- [ ] Session tokens: secure, httpOnly, sameSite
- [ ] CSRF tokens on state-changing operations
- [ ] Account lockout after failed attempts
- [ ] Secure password reset flow

### Check Authorization Implementation

\`\`\`bash
# Find authorization checks
grep -r "authorize\|permission\|role\|rbac" --include="*.js" --include="*.ts"

# Look for authorization bypass vulnerabilities:
# - Missing authorization checks
# - Insecure direct object references (IDOR)
# - Privilege escalation paths
\`\`\`

**Security Checklist**:
- [ ] Authorization checked on every protected route
- [ ] User can only access their own data
- [ ] Admin routes require admin role
- [ ] API endpoints validate permissions
- [ ] No client-side only authorization

## 2. Data Encryption Audit

### At Rest

\`\`\`bash
# Check database encryption
# GCP Cloud SQL
gcloud sql instances describe \${INSTANCE_NAME} \\
  --format="value(diskEncryptionConfiguration)"

# Cloud Storage
gsutil encryption get gs://\${BUCKET_NAME}

# Check for sensitive data in plaintext
grep -r "password\|ssn\|credit.card\|api.key" --include="*.sql" --include="*.json"
\`\`\`

**Security Checklist**:
- [ ] Database encrypted at rest (GCP CMEK or Google-managed)
- [ ] File storage encrypted (Cloud Storage encryption)
- [ ] Sensitive fields encrypted in database (PII, payment info)
- [ ] Encryption keys rotated regularly
- [ ] Backups encrypted

### In Transit

\`\`\`bash
# Check TLS configuration
curl -I https://\${DOMAIN} | grep -i "strict-transport-security"

# Check for insecure HTTP endpoints
grep -r "http://" --include="*.js" --include="*.html"
\`\`\`

**Security Checklist**:
- [ ] All traffic over HTTPS/TLS 1.2+
- [ ] HSTS header enabled (max-age ≥ 31536000)
- [ ] No mixed content (HTTP resources on HTTPS pages)
- [ ] Certificate valid and not expired
- [ ] Internal API calls use TLS

## 3. Input Validation & XSS Prevention

### Find User Input Points

\`\`\`bash
# Find user input handling
grep -r "req.body\|req.query\|req.params\|input\|textarea" --include="*.js" --include="*.ts"

# Check for XSS vulnerabilities
grep -r "innerHTML\|dangerouslySetInnerHTML\|eval\|document.write" --include="*.js" --include="*.jsx"
\`\`\`

**Security Checklist**:
- [ ] All user input validated and sanitized
- [ ] Input length limits enforced
- [ ] Content-Type validation on file uploads
- [ ] HTML entities escaped in output
- [ ] CSP header configured
- [ ] No dangerouslySetInnerHTML without sanitization
- [ ] No eval() on user input

### Check Output Encoding

\`\`\`bash
# Verify output is escaped
# React (automatic escaping)
# Templates (check for proper escaping)
grep -r "raw\|unescape\|safe" --include="*.html" --include="*.ejs"
\`\`\`

## 4. SQL Injection Prevention

### Check Database Queries

\`\`\`bash
# Find SQL queries
grep -r "SELECT\|INSERT\|UPDATE\|DELETE" --include="*.js" --include="*.ts" --include="*.py"

# Look for string concatenation in queries (red flag)
grep -r "query.*+.*req\\.\|\\$.*SELECT" --include="*.js" --include="*.ts"
\`\`\`

**Security Checklist**:
- [ ] All queries use parameterized statements
- [ ] No string concatenation in SQL queries
- [ ] ORM used correctly (no raw queries with user input)
- [ ] Input validated before database operations
- [ ] Least privilege database users
- [ ] No dynamic table/column names from user input

## 5. Secrets Management

### Scan for Hardcoded Secrets

\`\`\`bash
# Use gitleaks or truffleHog
docker run --rm -v $(pwd):/code trufflesecurity/trufflehog:latest filesystem /code

# Manual patterns to check
grep -rE "api[_-]?key|password|secret|token.*=.*['\"]" \\
  --include="*.js" --include="*.ts" --include="*.py" \\
  --exclude-dir=node_modules --exclude-dir=.git

# Check for .env in git
git ls-files | grep -E "\.env$|credentials\\.json$"
\`\`\`

**Security Checklist**:
- [ ] No hardcoded API keys or passwords
- [ ] Secrets in environment variables or Secret Manager
- [ ] .env files in .gitignore
- [ ] No secrets in git history
- [ ] Secrets rotated regularly
- [ ] Different secrets per environment (dev/staging/prod)

### Verify GCP Secret Manager Usage

\`\`\`bash
# List secrets
gcloud secrets list

# Check secret access permissions
gcloud secrets get-iam-policy \${SECRET_NAME}
\`\`\`

## 6. Dependency Vulnerabilities

### Scan Dependencies

\`\`\`bash
# Node.js
npm audit --json > npm-audit.json
npm audit fix --dry-run

# Python
pip-audit --format json > pip-audit.json

# Check for outdated packages
npm outdated
pip list --outdated

# Use Snyk for comprehensive scanning
snyk test --json > snyk-report.json
\`\`\`

**Security Checklist**:
- [ ] No critical or high severity vulnerabilities
- [ ] Dependencies updated regularly (monthly)
- [ ] Automated vulnerability scanning in CI/CD
- [ ] Package lock files committed (package-lock.json, requirements.txt)
- [ ] Only trusted sources for packages

### Analyze Dependency Report

\`\`\`javascript
// Parse npm audit results
const audit = JSON.parse(fs.readFileSync('npm-audit.json'));

const critical = audit.vulnerabilities.filter(v => v.severity === 'critical');
const high = audit.vulnerabilities.filter(v => v.severity === 'high');
const medium = audit.vulnerabilities.filter(v => v.severity === 'medium');

console.log(\`Critical: \${critical.length}\`);
console.log(\`High: \${high.length}\`);
console.log(\`Medium: \${medium.length}\`);

// Generate fix recommendations
critical.forEach(v => {
  console.log(\`🚨 CRITICAL: \${v.name} - \${v.title}\`);
  console.log(\`   Fix: npm update \${v.name}\`);
});
\`\`\`

## 7. API Security

### Check Rate Limiting

\`\`\`bash
# Find API endpoints
grep -r "app.get\|app.post\|@app.route" --include="*.js" --include="*.py"

# Check for rate limiting middleware
grep -r "rateLimit\|rate_limit\|throttle" --include="*.js" --include="*.py"
\`\`\`

**Security Checklist**:
- [ ] Rate limiting on all public APIs
- [ ] Authentication required for sensitive endpoints
- [ ] CORS properly configured (not *)
- [ ] API keys validated
- [ ] Request size limits enforced
- [ ] Timeout configurations set

### Check CORS Configuration

\`\`\`bash
# Find CORS configuration
grep -r "cors\|Access-Control" --include="*.js"

# Check for overly permissive CORS
grep -r "origin.*\\*\|Access-Control-Allow-Origin.*\\*"
\`\`\`

## 8. Audit Logging

### Check Logging Implementation

\`\`\`bash
# Find logging code
grep -r "logger\|console.log\|log.info" --include="*.js" --include="*.ts"

# Check for sensitive data in logs
grep -r "log.*password\|log.*token\|log.*ssn" --include="*.js"
\`\`\`

**Security Checklist**:
- [ ] Authentication events logged (login, logout, failed attempts)
- [ ] Authorization failures logged
- [ ] Data access logged (who accessed what, when)
- [ ] Configuration changes logged
- [ ] No sensitive data in logs (passwords, tokens, PII)
- [ ] Logs centralized (GCP Cloud Logging)
- [ ] Log retention policy configured

### Verify GCP Audit Logging

\`\`\`bash
# Check if audit logs are enabled
gcloud logging logs list | grep audit

# View recent audit logs
gcloud logging read "logName:cloudaudit.googleapis.com" --limit 10
\`\`\`

## 9. Infrastructure Security (GCP)

### IAM Audit

\`\`\`bash
# List all IAM bindings
gcloud projects get-iam-policy \${PROJECT_ID}

# Check for overly permissive roles
gcloud projects get-iam-policy \${PROJECT_ID} \\
  --flatten="bindings[].members" \\
  --filter="bindings.role:roles/owner OR bindings.role:roles/editor"

# Check service account keys
gcloud iam service-accounts keys list \\
  --iam-account=\${SERVICE_ACCOUNT}
\`\`\`

**Security Checklist**:
- [ ] Principle of least privilege (no unnecessary Owner/Editor roles)
- [ ] Service accounts used instead of user accounts
- [ ] Service account keys rotated regularly (<90 days)
- [ ] No public access to Cloud Storage buckets
- [ ] IAM conditions used for fine-grained access

### Network Security

\`\`\`bash
# Check firewall rules
gcloud compute firewall-rules list

# Look for overly permissive rules
gcloud compute firewall-rules list \\
  --filter="sourceRanges=0.0.0.0/0 AND allowed.ports=*"

# Check VPC configuration
gcloud compute networks list
\`\`\`

**Security Checklist**:
- [ ] No 0.0.0.0/0 access to sensitive ports
- [ ] VPC configured with private subnets
- [ ] Cloud NAT for outbound traffic
- [ ] VPC firewall rules follow least privilege
- [ ] Cloud Armor enabled for DDoS protection

## 10. Security Score Calculation

\`\`\`javascript
function calculateSecurityScore(findings) {
  let score = 100;

  // Deduct points based on severity
  score -= findings.critical.length * 20;
  score -= findings.high.length * 10;
  score -= findings.medium.length * 5;
  score -= findings.low.length * 2;

  return Math.max(0, score);
}

const findings = {
  critical: \${CRITICAL_FINDINGS},
  high: \${HIGH_FINDINGS},
  medium: \${MEDIUM_FINDINGS},
  low: \${LOW_FINDINGS}
};

const score = calculateSecurityScore(findings);
console.log(\`Security Score: \${score}/100\`);

// Grade
if (score >= 90) console.log('Grade: A (Excellent)');
else if (score >= 80) console.log('Grade: B (Good)');
else if (score >= 70) console.log('Grade: C (Fair - Needs Improvement)');
else if (score >= 60) console.log('Grade: D (Poor - Action Required)');
else console.log('Grade: F (Critical - Immediate Action Required)');
\`\`\`

## 11. Generate Security Report

\`\`\`markdown
# Security Audit Report

**Project**: \${PROJECT_NAME}
**Date**: \${DATE}
**Auditor**: AI Security Agent
**Scope**: \${SCOPE}

## Executive Summary

**Security Score**: \${SCORE}/100 (\${GRADE})
**Risk Level**: \${RISK_LEVEL}

**Findings Summary**:
- 🚨 Critical: \${CRITICAL_COUNT}
- 🔴 High: \${HIGH_COUNT}
- 🟡 Medium: \${MEDIUM_COUNT}
- 🟢 Low: \${LOW_COUNT}

**Compliance Status**:
- OWASP Top 10: \${OWASP_STATUS}
- HIPAA (if applicable): \${HIPAA_STATUS}
- PCI DSS (if applicable): \${PCI_STATUS}

## Critical Findings (Immediate Action Required)

### Finding 1: [Title]
**Severity**: Critical
**Category**: [Authentication/Encryption/Injection/etc.]
**Description**: [What's wrong]
**Impact**: [Potential damage]
**Location**: [File:Line]
**Recommendation**: [How to fix]
**Effort**: [Time estimate]

## High Severity Findings

[Same structure as critical]

## Medium Severity Findings

[Same structure]

## Security Checklist Status

### Authentication & Authorization
- ✓ Passwords properly hashed
- ✓ MFA available
- ✗ Session timeout not configured ← FIX
- ✓ CSRF protection enabled

### Data Encryption
- ✓ Database encrypted at rest
- ✓ TLS 1.2+ enforced
- ✗ Some sensitive fields not encrypted ← FIX
- ✓ HSTS enabled

[Continue for all categories]

## Dependency Vulnerabilities

**Total Packages**: \${TOTAL_PACKAGES}
**Vulnerable Packages**: \${VULNERABLE_PACKAGES}

**Critical Vulnerabilities**:
- [\${PACKAGE_NAME}] \${VULNERABILITY_TITLE}
  - Fix: npm update \${PACKAGE_NAME}

## Infrastructure Security (GCP)

**IAM**:
- ✓ Service accounts used
- ✗ 2 users have Owner role ← REVIEW
- ✓ Service account keys rotated

**Network**:
- ✓ VPC configured
- ✗ Firewall rule allows 0.0.0.0/0 on port 22 ← FIX
- ✓ Cloud Armor enabled

## Remediation Roadmap

### Week 1 (Critical)
1. Fix hardcoded API key in auth.js
2. Add rate limiting to public APIs
3. Rotate compromised service account keys

### Week 2 (High)
1. Implement input validation on user forms
2. Add CSP header
3. Update vulnerable dependencies

### Week 3-4 (Medium)
1. Encrypt sensitive database fields
2. Add audit logging for data access
3. Review and tighten firewall rules

## Compliance Recommendations

**OWASP Top 10**:
- [x] A01: Broken Access Control - PASS
- [x] A02: Cryptographic Failures - PASS
- [ ] A03: Injection - NEEDS WORK (SQL injection risk in reports.js)
- [x] A04: Insecure Design - PASS
- [ ] A05: Security Misconfiguration - NEEDS WORK (firewall rules)
- [x] A06: Vulnerable Components - PARTIAL (3 high-severity vulns)
[Continue...]

## Next Steps

1. **Immediate** (Next 24 hours):
   - Address all critical findings
   - Patch known exploits

2. **Short-term** (Next week):
   - Fix high severity findings
   - Update vulnerable dependencies

3. **Medium-term** (Next month):
   - Address medium severity findings
   - Implement additional security controls

4. **Ongoing**:
   - Monthly dependency scans
   - Quarterly security audits
   - Annual penetration testing

---
**Next Audit**: \${NEXT_AUDIT_DATE}
**Contact**: security@example.com
\`\`\`

Save to: security-audits/audit-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Full security audit
/security/audit

# Code-only audit (skip infrastructure)
/security/audit --scope code

# Infrastructure-only audit
/security/audit --scope infra

# Show only critical findings
/security/audit --severity critical
```

## Integration Points

This command is automatically triggered in:

- `/dev/review` - Security check before PR approval
- `/dev/full-cycle` - Security check before deployment
- `/devops/deploy` - Pre-deployment security verification
- CI/CD pipelines - Automated on every commit

## Success Criteria

- ✓ All 9 security areas audited
- ✓ Vulnerabilities identified and categorized
- ✓ Security score calculated (0-100)
- ✓ Compliance status checked (OWASP, HIPAA, PCI)
- ✓ Remediation roadmap generated
- ✓ Report saved with findings
- ✓ Critical findings: 0 (before production)
- ✓ High findings: <3 (acceptable risk)
- ✓ Security score: >80 (minimum for production)

---
**Uses**: gcp-security-compliance, code-reviewer
**Output**: Comprehensive security report with remediation plan
**Next Commands**: `/security/scan` (vulnerability scanning), `/dev/implement` (fix findings)
**Target**: Security Score >80, Zero Critical Findings
