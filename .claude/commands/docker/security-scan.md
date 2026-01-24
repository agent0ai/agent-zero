---
description: Scan Docker images for vulnerabilities, misconfigurations, and security issues with automated remediation
argument-hint: [--severity <low|medium|high|critical>] [--fix] [--report-format <json|html|sarif>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

Docker Security Scan: **${ARGUMENTS}**

## Scanning Docker Images for Security Issues

Use the Task tool with subagent_type=docker-specialist to perform comprehensive security scanning with the following specifications:

### Input Parameters

**Severity Threshold**: ${SEVERITY:-medium} (Only report issues >= this severity)
**Auto-Fix**: ${FIX:-false} (Automatically fix issues where possible)
**Report Format**: ${REPORT_FORMAT:-html} (json, html, sarif, markdown)
**Image**: ${IMAGE:-current} (Image to scan, or current Dockerfile)

### Objectives

You are tasked with comprehensive security scanning and hardening of Docker images. Your implementation must:

#### 1. Multi-Tool Security Scanning

**Scanning Tools Integration**:

**1. Docker Scout** (Official Docker security tool):

```bash
# Enable Docker Scout
docker scout enroll

# Scan image for CVEs
docker scout cves myapp:latest

# Compare with base image
docker scout compare --to myapp:latest myapp:previous

# Get recommendations
docker scout recommendations myapp:latest
```

**2. Trivy** (Comprehensive vulnerability scanner):

```bash
# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Scan image
trivy image myapp:latest

# Scan with severity filtering
trivy image --severity HIGH,CRITICAL myapp:latest

# Output as JSON
trivy image --format json --output results.json myapp:latest

# Scan Dockerfile
trivy config Dockerfile

# Scan for secrets
trivy fs --scanners secret .
```

**3. Snyk** (Developer-friendly security):

```bash
# Install Snyk
npm install -g snyk

# Authenticate
snyk auth

# Scan image
snyk container test myapp:latest

# Monitor for new vulnerabilities
snyk container monitor myapp:latest

# Get fix recommendations
snyk container test myapp:latest --json | jq '.vulnerabilities[] | select(.fixedIn != null)'
```

**4. Grype** (Fast vulnerability scanning):

```bash
# Install Grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh

# Scan image
grype myapp:latest

# Output SARIF for GitHub integration
grype myapp:latest -o sarif > grype-results.sarif
```

#### 2. Comprehensive Security Scan Report

**Vulnerability Assessment**:

```markdown
# Docker Security Scan Report

**Image**: myapp:latest
**Scan Date**: 2024-11-15 14:30 UTC
**Tools Used**: Docker Scout, Trivy, Snyk, Grype

---

## Executive Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 3 | ⚠️ Action Required |
| HIGH | 12 | ⚠️ Review Needed |
| MEDIUM | 45 | ℹ️ Monitor |
| LOW | 120 | ✅ Acceptable |

**Overall Risk Score**: 7.2/10 (High)
**Recommendation**: **Fix critical issues before deployment**

---

## Critical Vulnerabilities (3)

### CVE-2024-1234: Remote Code Execution in libssl
**Severity**: CRITICAL (CVSS 9.8)
**Package**: openssl 3.0.1
**Fixed In**: openssl 3.0.8
**Impact**: Remote code execution via malformed certificate

**Remediation**:
```dockerfile
# Update base image
FROM node:20.10.0-alpine  # Current
FROM node:20.11.0-alpine  # Fixed (includes openssl 3.0.8)
```

**Auto-fix Available**: ✅ Yes

---

### CVE-2024-5678: SQL Injection in pg library

**Severity**: CRITICAL (CVSS 9.1)
**Package**: pg@8.11.0
**Fixed In**: pg@8.11.3
**Impact**: SQL injection in parameterized queries

**Remediation**:

```json
// package.json
"dependencies": {
  "pg": "^8.11.3"  // Upgrade from 8.11.0
}
```

**Auto-fix Available**: ✅ Yes

---

### CVE-2024-9012: Path Traversal in express

**Severity**: CRITICAL (CVSS 8.6)
**Package**: express@4.18.0
**Fixed In**: express@4.18.2
**Impact**: Directory traversal in static file serving

**Remediation**:

```bash
npm update express
```

**Auto-fix Available**: ✅ Yes

---

## High Severity Vulnerabilities (12)

Summary of HIGH severity issues:

- 8 in npm dependencies
- 3 in OS packages (Alpine)
- 1 in Python libraries

**Recommended Actions**:

1. Update all npm packages: `npm update`
2. Upgrade Alpine version: `FROM node:20.11-alpine3.19`
3. Remove unused dependencies

---

## Configuration Issues

### 🔴 Running as Root User

**Risk**: High
**Impact**: Container escape vulnerability

**Current**:

```dockerfile
# No USER directive - runs as root
CMD ["node", "index.js"]
```

**Fix**:

```dockerfile
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
USER nodejs
CMD ["node", "index.js"]
```

---

### 🔴 Exposed Secrets in Layers

**Risk**: Critical
**Impact**: API keys visible in image layers

**Found**:

- Layer 12: `ENV API_KEY=sk_live_abc123...`
- Layer 15: `.env` file containing credentials

**Fix**:

```dockerfile
# Use build secrets instead
RUN --mount=type=secret,id=api_key \
    API_KEY=$(cat /run/secrets/api_key) npm run build

# Build with:
docker build --secret id=api_key,src=.env .
```

---

### 🟡 Unnecessary Capabilities

**Risk**: Medium
**Impact**: Excessive container permissions

**Current**: Default capabilities include NET_RAW, SYS_CHROOT
**Recommended**: Drop all, add only necessary

**Fix**:

```yaml
# docker-compose.yml
services:
  app:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if binding to port <1024
```

---

### 🟡 No Health Check Defined

**Risk**: Medium
**Impact**: No container health monitoring

**Fix**:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node healthcheck.js
```

---

## Best Practices Violations

### ❌ Using 'latest' Tag

```dockerfile
FROM node:latest  # Don't use 'latest'
FROM node:20.10.0-alpine  # Use specific version
```

### ❌ Installing Unnecessary Packages

```dockerfile
# Removes build tools after use
RUN apk add --no-cache --virtual .build-deps gcc musl-dev && \
    pip install requirements.txt && \
    apk del .build-deps
```

### ❌ Not Using Read-Only Filesystem

```yaml
# docker-compose.yml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
```

---

## Automated Fixes

### Quick Fixes (Auto-apply available)

```bash
# 1. Update vulnerable npm packages
npm update

# 2. Update base image
sed -i 's/node:20.10.0-alpine/node:20.11.0-alpine/' Dockerfile

# 3. Add non-root user
cat >> Dockerfile << 'EOF'
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
USER nodejs
EOF

# 4. Add health check
cat >> Dockerfile << 'EOF'
HEALTHCHECK --interval=30s CMD node healthcheck.js
EOF
```

Apply all fixes:

```bash
./security-fixes.sh --auto-apply
```

---

## Compliance Status

### CIS Docker Benchmark

| Check | Status | Details |
|-------|--------|---------|
| 4.1 Create a user for container | ❌ FAIL | Running as root |
| 4.2 Use trusted base images | ✅ PASS | Using official node image |
| 4.3 Do not install unnecessary packages | ⚠️ WARN | 12 unused packages found |
| 4.4 Scan images for vulnerabilities | ✅ PASS | Regular scanning |
| 4.5 Enable Content Trust | ❌ FAIL | Not configured |
| 4.6 Add HEALTHCHECK | ❌ FAIL | No health check |
| 4.7 Do not use update without version | ✅ PASS | Versions pinned |

**Score**: 3/7 (43%)

### OWASP Docker Top 10

1. ❌ Secure User Mapping - Running as root
2. ✅ Patch Management - Dependencies tracked
3. ⚠️ Network Segmentation - Needs review
4. ✅ Secure Defaults - Good defaults
5. ❌ Secrets Management - Secrets in layers
6. ✅ Vulnerability Scanning - Regular scans
7. ⚠️ Integrity & Confidentiality - Partial
8. ✅ Container Resources - Limits set
9. ❌ Logging - Inadequate logging
10. ✅ Deny Communications - Network policies

**Score**: 5/10 (50%)

---

## Prioritized Remediation Plan

### Phase 1: Critical (Fix Immediately) - 1 hour

1. **Update base image** (15 min)

   ```dockerfile
   FROM node:20.11.0-alpine3.19
   ```

2. **Update vulnerable packages** (20 min)

   ```bash
   npm update express pg
   npm audit fix
   ```

3. **Add non-root user** (10 min)

   ```dockerfile
   RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
   USER nodejs
   ```

4. **Remove secrets from layers** (15 min)
   - Use build secrets
   - Add to .dockerignore

**Impact**: Fixes 3 CRITICAL + 4 HIGH vulnerabilities

---

### Phase 2: High Priority (Fix This Week) - 2 hours

1. **Add health checks** (30 min)
2. **Implement least privilege** (30 min)
3. **Enable read-only filesystem** (30 min)
4. **Configure logging** (30 min)

**Impact**: Improves security score 43% → 75%

---

### Phase 3: Medium Priority (Fix This Month) - 4 hours

1. **Enable Docker Content Trust**
2. **Implement image signing**
3. **Set up runtime security monitoring**
4. **Configure AppArmor/SELinux**

**Impact**: Achieves production-grade security (90%+)

---

## Continuous Security

### Automated Scanning in CI/CD

```yaml
# .github/workflows/security-scan.yml
name: Docker Security Scan

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Fail on critical vulnerabilities
        run: |
          CRITICAL=$(trivy image --severity CRITICAL --format json myapp:${{ github.sha }} | jq '.Results[].Vulnerabilities | length')
          if [ "$CRITICAL" -gt 0 ]; then
            echo "❌ Found $CRITICAL critical vulnerabilities"
            exit 1
          fi
```

### Runtime Security Monitoring

```yaml
# Enable Falco for runtime security
services:
  app:
    security_opt:
      - apparmor:docker-default
      - seccomp:runtime-default
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
```

---

## Security Score

**Before Fixes**: 43/100 (High Risk)
**After Phase 1**: 75/100 (Medium Risk)
**After All Phases**: 92/100 (Low Risk)

**Recommendation**:

- ✅ Complete Phase 1 immediately (1 hour)
- ✅ Schedule Phase 2 this week (2 hours)
- ℹ️ Plan Phase 3 for next sprint (4 hours)

```

#### 3. Security Hardening Recommendations

**Dockerfile Security Template**:
```dockerfile
# syntax=docker/dockerfile:1

# Use specific, tested base image version
FROM node:20.11.0-alpine3.19 AS base

# Build stage
FROM base AS builder

WORKDIR /app

# Install dependencies with integrity checks
COPY package*.json ./
RUN npm ci --only=production=false && \
    npm audit fix && \
    npm cache clean --force

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM base AS production

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Copy only necessary files
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --chown=nodejs:nodejs package*.json ./

# Drop all capabilities
USER nodejs

# Use specific port (non-privileged)
EXPOSE 3000

# Health check for monitoring
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node healthcheck.js || exit 1

# Labels for metadata
LABEL maintainer="team@example.com" \
      version="1.0.0" \
      description="Production Node.js application"

# Read-only filesystem (where possible)
# Enable via docker-compose or k8s

# Start application
CMD ["node", "dist/index.js"]
```

### Implementation Steps

**Step 1: Scan**

1. Run multiple security scanners (Trivy, Snyk, Docker Scout)
2. Aggregate results
3. Deduplicate findings
4. Categorize by severity

**Step 2: Analysis**

1. Analyze vulnerabilities for false positives
2. Determine exploitability
3. Assess business impact
4. Prioritize fixes

**Step 3: Remediation**

1. Generate fix recommendations
2. Create automated fix scripts
3. Apply fixes (if auto-fix enabled)
4. Validate fixes

**Step 4: Reporting**

1. Generate comprehensive security report
2. Create remediation roadmap
3. Export in requested format (JSON/HTML/SARIF)
4. Integrate with security dashboards

**Step 5: Continuous Monitoring**

1. Set up automated daily scans
2. Configure CI/CD integration
3. Enable vulnerability alerts
4. Track security metrics over time

### Output Requirements

**Generated Files**:

- `security-report.html` - Detailed security report
- `security-report.json` - Machine-readable report
- `security-report.sarif` - SARIF format for GitHub
- `security-fixes.sh` - Automated fix script
- `SECURITY.md` - Security documentation

## ROI Impact

**Risk Mitigation**:

- **Prevent data breaches**: $4M average cost per breach
- **Compliance violations**: $500K average fine
- **Reputation damage**: Immeasurable

**Cost Savings**:

- **Automated scanning**: $40,000/year (vs manual audits)
- **Early detection**: $100,000/year (fixes pre-production)
- **Compliance**: $30,000/year (automated compliance checks)

**Time Savings**:

- **Manual security reviews**: 8 hours → 15 minutes (automated)
- **Vulnerability tracking**: Automatic monitoring
- **Remediation**: Auto-fix for 70% of issues

**Total Value**: $170,000/year

- Risk mitigation: $100,000/year
- Automated security: $40,000/year
- Time savings: $30,000/year

## Success Criteria

✅ **All CRITICAL vulnerabilities fixed**
✅ **HIGH vulnerabilities < 5**
✅ **Security score > 80/100**
✅ **CIS benchmark > 80% compliance**
✅ **Automated scanning in CI/CD**
✅ **No secrets in image layers**

**Security Targets**:

- Zero critical vulnerabilities
- < 10 high severity issues
- Daily automated scans
- Fix time < 24 hours for critical

## Next Steps

1. Run initial security scan
2. Review and prioritize findings
3. Apply critical fixes
4. Integrate into CI/CD
5. Schedule regular scans

---

**Security Status**: ⚠️ Action Required
**Current Score**: 43/100
**Target Score**: 90/100
**Annual ROI**: $170,000 (risk mitigation + automation)
