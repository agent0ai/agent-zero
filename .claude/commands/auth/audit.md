---
description: Security audit of authentication system with compliance validation
argument-hint: [--framework hipaa|pci-dss|soc2|all]
model: claude-opus-4-20250514
allowed-tools: Task, Bash, AskUserQuestion
---

Security audit authentication: **${ARGUMENTS}**

## Audit Frameworks

**OWASP Top 10** - Common web security vulnerabilities
**PCI DSS** - Payment card industry standards
**HIPAA** - Healthcare data protection
**SOC 2** - Service organization controls
**NIST** - National Institute of Standards framework

## Integration Points

**Development Workflow**:

- `/dev/review` → Includes basic security checks
- `/auth/setup` → Generates security checklist
- `/auth/test` → Tests security vulnerabilities

**Compliance**:

- Run quarterly security audits
- Before major deployments
- After security incidents

## Security Audit

Routes to **healthcare-security-compliance** for comprehensive audit:

```javascript
await Task({
  subagent_type: 'healthcare-security-compliance',
  description: 'Security audit authentication system',
  prompt: `Perform comprehensive security audit of authentication system

Compliance frameworks: ${FRAMEWORK || 'all (OWASP, PCI DSS, HIPAA, SOC 2)'}

Conduct thorough security audit:

1. **Password Security**:
   ✓ Bcrypt with cost factor ≥ 12 (OWASP, PCI DSS)
   ✓ Minimum password length (12+ characters)
   ✓ Password complexity requirements enforced
   ✓ Password history (prevent reuse of last 5)
   ✓ No passwords stored in plain text
   ✓ No default/weak passwords allowed

2. **Token Security**:
   ✓ JWT signed with RS256 (asymmetric, not HS256)
   ✓ Access token expiry ≤ 15 minutes (PCI DSS)
   ✓ Refresh token expiry ≤ 7 days
   ✓ Refresh tokens rotated on use
   ✓ Token includes required claims (sub, exp, iat, iss)
   ✓ No sensitive data in JWT payload
   ✓ Token signature verified on every request

3. **Secret Management**:
   ✓ Secrets stored in Secret Manager/KMS (PCI DSS 3.5)
   ✓ No secrets in code or config files
   ✓ No secrets in version control
   ✓ Secrets rotated quarterly (PCI DSS 3.6.4)
   ✓ Access to secrets logged and audited

4. **Authentication Endpoints**:
   ✓ Rate limiting on login (OWASP A07)
   ✓ Account lockout after N failed attempts (5-10)
   ✓ CAPTCHA on repeated failures
   ✓ Login timing constant (prevent user enumeration)
   ✓ HTTPS only (no plain HTTP)
   ✓ CSRF protection enabled
   ✓ CORS properly configured

5. **Session Management**:
   ✓ Session timeout ≤ 30 minutes idle (PCI DSS 8.1.8)
   ✓ Absolute session timeout ≤ 8 hours
   ✓ Secure session cookies (httpOnly, secure, sameSite)
   ✓ Session invalidated on logout
   ✓ No session fixation vulnerabilities

6. **Access Control**:
   ✓ Role-based access control (RBAC) implemented
   ✓ Principle of least privilege enforced
   ✓ Authorization checked on every request
   ✓ No IDOR vulnerabilities (test with different user IDs)
   ✓ Proper 403 vs 404 responses

7. **Multi-Factor Authentication**:
   ${FRAMEWORK?.includes('hipaa') || FRAMEWORK === 'all' ? `
   ✓ MFA available (HIPAA 164.312(a)(2)(i))
   ✓ MFA required for admin accounts
   ✓ MFA enforcement configurable per role
   ✓ Backup codes provided
   ` : ''}

8. **Audit Logging** (HIPAA, SOC 2):
   ✓ All authentication events logged
   ✓ Logs include: timestamp, user, action, result, IP
   ✓ Failed login attempts logged
   ✓ Password changes logged
   ✓ Role changes logged
   ✓ Logs tamper-proof (immutable)
   ✓ Logs retained 90+ days (HIPAA 365+ days)

9. **Data Protection**:
   ✓ Passwords never returned in API responses
   ✓ Passwords not logged
   ✓ Sensitive data encrypted at rest (PCI DSS 3.4)
   ✓ Sensitive data encrypted in transit (TLS 1.2+)
   ✓ No sensitive data in URLs or query params

10. **Vulnerability Testing**:
    ✓ SQL injection tested and prevented
    ✓ XSS tested and prevented
    ✓ CSRF tested and prevented
    ✓ Clickjacking prevented (X-Frame-Options)
    ✓ No information disclosure in errors
    ✓ Security headers configured (CSP, HSTS, etc.)

11. **Compliance-Specific Checks**:
    ${FRAMEWORK?.includes('pci-dss') || FRAMEWORK === 'all' ? `
    **PCI DSS**:
    ✓ Unique ID per user (Req 8.1)
    ✓ Strong authentication (Req 8.2)
    ✓ MFA for admin (Req 8.3)
    ✓ Password complexity (Req 8.2.3)
    ✓ Password rotation (Req 8.2.4)
    ✓ Account lockout (Req 8.1.6)
    ` : ''}

    ${FRAMEWORK?.includes('hipaa') || FRAMEWORK === 'all' ? `
    **HIPAA**:
    ✓ Unique user IDs (164.312(a)(2)(i))
    ✓ Emergency access procedures
    ✓ Automatic logoff (164.312(a)(2)(iii))
    ✓ Encryption and decryption (164.312(a)(2)(iv))
    ✓ Audit controls (164.312(b))
    ✓ Person/entity authentication (164.312(d))
    ` : ''}

    ${FRAMEWORK?.includes('soc2') || FRAMEWORK === 'all' ? `
    **SOC 2**:
    ✓ Logical access controls
    ✓ Authentication mechanisms documented
    ✓ Access reviews performed quarterly
    ✓ Privileged access monitored
    ✓ User access provisioning/deprovisioning
    ` : ''}

12. **Findings Report**:
    - Generate comprehensive audit report
    - List all findings by severity (Critical, High, Medium, Low)
    - Provide remediation steps for each finding
    - Assign risk scores
    - Recommend priority order for fixes
    - Estimate remediation time

Output format:
  - Executive summary
  - Compliance score per framework
  - Detailed findings list
  - Remediation roadmap
  `
})
```

## Audit Report Example

```markdown
# Authentication Security Audit Report
Date: 2024-01-15
Auditor: AI Security Agent
Frameworks: OWASP Top 10, PCI DSS, HIPAA, SOC 2

## Executive Summary

Overall Security Score: **87/100** (B+)

- ✓ Strong: Password hashing, token security, secret management
- ⚠️ Needs Attention: MFA not enforced, session timeout too long
- ✗ Critical: Rate limiting not configured on login endpoint

## Compliance Scores

| Framework   | Score | Status        | Critical Issues |
|-------------|-------|---------------|-----------------|
| OWASP Top 10| 92/100| ✓ Passed      | 0               |
| PCI DSS     | 85/100| ⚠️ Conditional| 1               |
| HIPAA       | 88/100| ✓ Passed      | 0               |
| SOC 2       | 84/100| ⚠️ Conditional| 1               |

## Critical Findings (Fix Immediately)

### 1. [CRITICAL] No Rate Limiting on Login Endpoint
**Risk**: Brute force attacks
**Framework**: OWASP A07, PCI DSS 8.1.6
**Evidence**:
```bash
# Test: Made 1000 login attempts in 10 seconds
# Expected: Should be blocked after 5 attempts
# Actual: All 1000 attempts processed
```

**Remediation**:

```javascript
// Add rate limiting middleware
const rateLimit = require('express-rate-limit');

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: 'Too many login attempts, please try again later'
});

app.post('/auth/login', loginLimiter, authController.login);
```

**Estimated Time**: 2 hours
**Priority**: 1 (Immediate)

## High Findings (Fix Within 7 Days)

### 2. [HIGH] MFA Not Enforced for Admin Accounts

**Risk**: Compromised admin credentials = full system access
**Framework**: PCI DSS 8.3, HIPAA 164.312(a)(2)(i)
**Evidence**: Admin login succeeded with only password
**Remediation**:

- Implement TOTP-based MFA
- Require MFA for all admin role accounts
- Provide backup codes for account recovery
**Estimated Time**: 2 days
**Priority**: 2

### 3. [HIGH] Session Timeout 24 Hours (Too Long)

**Risk**: Unattended sessions remain active
**Framework**: PCI DSS 8.1.8
**Current**: 24 hours
**Required**: ≤ 30 minutes idle, ≤ 8 hours absolute
**Remediation**:

```javascript
session({
  cookie: {
    maxAge: 8 * 60 * 60 * 1000, // 8 hours absolute
    rolling: true // Reset on activity
  },
  rolling: true,
  resave: false,
  saveUninitialized: false
})
```

**Estimated Time**: 4 hours
**Priority**: 3

## Medium Findings (Fix Within 30 Days)

### 4. [MEDIUM] No Password History

**Risk**: Users can immediately reuse old passwords
**Framework**: PCI DSS 8.2.5
**Remediation**: Store hash of last 5 passwords, prevent reuse
**Estimated Time**: 1 day
**Priority**: 4

### 5. [MEDIUM] Insufficient Audit Logging

**Risk**: Cannot trace security incidents
**Framework**: HIPAA 164.312(b), SOC 2
**Current**: Only successful logins logged
**Required**: Log all auth events (success, failure, password change, etc.)
**Estimated Time**: 1 day
**Priority**: 5

## Low Findings (Fix Within 60 Days)

### 6. [LOW] Security Headers Not Configured

**Risk**: Clickjacking, XSS via injection
**Framework**: OWASP A01
**Missing Headers**:

- X-Frame-Options
- Content-Security-Policy
- X-Content-Type-Options
- Strict-Transport-Security
**Remediation**:

```javascript
app.use(helmet({
  frameguard: { action: 'deny' },
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"]
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true
  }
}));
```

**Estimated Time**: 2 hours
**Priority**: 6

## Strengths

✓ **Password Hashing**: Bcrypt with cost factor 12 (excellent)
✓ **Token Security**: RS256 signing, 15min expiry (excellent)
✓ **Secret Management**: All secrets in Secret Manager (excellent)
✓ **HTTPS Only**: No plain HTTP allowed (excellent)
✓ **CSRF Protection**: Enabled and tested (good)

## Remediation Roadmap

**Week 1** (Critical):

- Day 1: Add rate limiting to login endpoint
- Day 2-3: Implement and test

**Week 2** (High):

- Day 1-2: Implement MFA for admin accounts
- Day 3: Update session timeout configuration
- Day 4-5: Test and validate

**Week 3-4** (Medium):

- Week 3: Add password history tracking
- Week 4: Enhance audit logging

**Month 2** (Low):

- Add security headers
- Perform follow-up audit

## Compliance Status

**PCI DSS**:

- Current: 85/100 (Conditional Pass)
- After Fixes: 95/100 (Full Compliance)
- Blocker: Rate limiting (Critical #1)

**HIPAA**:

- Current: 88/100 (Compliant)
- After Fixes: 96/100 (Highly Compliant)
- Recommendation: Implement MFA for all users

**SOC 2**:

- Current: 84/100 (Conditional)
- After Fixes: 92/100 (Full Compliance)
- Blocker: Audit logging gaps (Medium #5)

## Recommendations

1. **Immediate**: Implement rate limiting (Critical #1)
2. **This Sprint**: MFA for admins, session timeout
3. **Next Sprint**: Password history, audit logging
4. **Ongoing**: Quarterly security audits, annual penetration testing

## Sign-Off

This audit was performed using automated security scanning tools and manual code review.
Re-audit recommended after implementing Critical and High findings.

Next Audit Due: 2024-04-15 (90 days)

```

## Automated Security Scanning

```bash
#!/bin/bash
# security-audit.sh

echo "Running authentication security audit..."

# 1. OWASP Dependency Check
echo "Checking for vulnerable dependencies..."
npm audit --audit-level=moderate

# 2. Static code analysis
echo "Running static code analysis..."
eslint src/auth --rule "no-eval: error" \
                 --rule "no-implied-eval: error"

# 3. Secret scanning
echo "Scanning for hardcoded secrets..."
trufflehog filesystem src/ --json | jq '.[] | select(.Verified == true)'

# 4. SQL injection testing
echo "Testing for SQL injection..."
sqlmap -u "http://localhost:3000/auth/login" \
       --data="email=test&password=test" \
       --batch --level=5

# 5. JWT security check
echo "Checking JWT configuration..."
node << 'EOF'
const jwt = require('jsonwebtoken');
const fs = require('fs');

// Check for HS256 (symmetric, less secure)
const config = require('./src/auth/jwt');
if (config.algorithm === 'HS256') {
  console.error('❌ CRITICAL: Using HS256 (symmetric). Use RS256 (asymmetric)');
  process.exit(1);
}

// Check token expiry
if (config.accessTokenExpiry > 900) { // 15 minutes
  console.error('⚠️  WARNING: Access token expiry too long (>15min)');
}

console.log('✓ JWT configuration secure');
EOF

# 6. Password hashing check
echo "Checking password hashing..."
node << 'EOF'
const bcrypt = require('bcrypt');

// Check bcrypt rounds
const rounds = bcrypt.getRounds('$2b$12$...sample...');
if (rounds < 12) {
  console.error('❌ CRITICAL: Bcrypt rounds < 12');
  process.exit(1);
}

console.log('✓ Password hashing secure (bcrypt rounds: ' + rounds + ')');
EOF

echo ""
echo "✓ Security audit complete"
echo "Review findings above and address Critical/High issues immediately."
```

## Best Practices

**DO**:

- ✓ Run security audits quarterly
- ✓ Automate security scanning in CI/CD
- ✓ Fix critical findings immediately
- ✓ Document all findings and remediations
- ✓ Re-audit after implementing fixes
- ✓ Keep audit reports for compliance
- ✓ Test for OWASP Top 10 vulnerabilities

**DON'T**:

- ✗ Skip security audits before production deployment
- ✗ Ignore findings without documented justification
- ✗ Use automated tools only (manual review needed)
- ✗ Audit only once (quarterly minimum)
- ✗ Forget to test fixes

## Commands

**`/auth/audit`** - Full security audit (all frameworks)
**`/auth/audit --framework pci-dss`** - PCI DSS audit only
**`/auth/audit --framework hipaa`** - HIPAA audit only
**`/auth/test`** - Run security tests
**`/auth/rotate-keys`** - Rotate keys if audit finds old keys

## Success Criteria

- ✓ Comprehensive audit report generated
- ✓ All findings categorized by severity
- ✓ Compliance scores calculated per framework
- ✓ Remediation steps provided for each finding
- ✓ Critical findings (if any) have immediate action plan
- ✓ Audit report saved for compliance records
- ✓ Next audit scheduled (90 days)

---
**Uses**: healthcare-security-compliance, gcp-security-compliance, code-reviewer
