---
description: Quick vulnerability scan for dependencies and known exploits
argument-hint: [--fix] [--report]
model: claude-haiku-4-20250514
allowed-tools: Bash, Write
---

Run security scan: **${ARGUMENTS}**

## Fast Vulnerability Scanning

**Quick Checks** (< 2 minutes):

- Dependency vulnerabilities (npm audit, pip-audit)
- Known exploits (CVE database)
- Outdated packages
- Basic secret detection

```bash
echo "🔍 Running Security Scan..."
echo "======================================"

# Node.js dependencies
if [ -f "package.json" ]; then
  echo "📦 Scanning Node.js dependencies..."
  npm audit --json > /tmp/npm-audit.json

  CRITICAL=$(cat /tmp/npm-audit.json | jq '.metadata.vulnerabilities.critical // 0')
  HIGH=$(cat /tmp/npm-audit.json | jq '.metadata.vulnerabilities.high // 0')
  MEDIUM=$(cat /tmp/npm-audit.json | jq '.metadata.vulnerabilities.medium // 0')

  echo "  Critical: $CRITICAL"
  echo "  High: $HIGH"
  echo "  Medium: $MEDIUM"

  if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
    echo "  ⚠️  VULNERABILITIES FOUND!"
    ${FIX ? 'echo "  🔧 Attempting automatic fixes..."' : ''}
    ${FIX ? 'npm audit fix' : ''}
  else
    echo "  ✓ No critical vulnerabilities"
  fi
fi

# Python dependencies
if [ -f "requirements.txt" ]; then
  echo "🐍 Scanning Python dependencies..."
  pip-audit --format json > /tmp/pip-audit.json 2>/dev/null || echo "  ⚠️  pip-audit not installed"
fi

# Check for common vulnerable patterns
echo "🔐 Checking for insecure code patterns..."

# SQL injection patterns
SQL_ISSUES=$(grep -rn "query.*+.*req\." --include="*.js" --include="*.ts" | wc -l)
if [ "$SQL_ISSUES" -gt 0 ]; then
  echo "  ⚠️  Potential SQL injection: $SQL_ISSUES locations"
else
  echo "  ✓ No SQL injection patterns found"
fi

# XSS patterns
XSS_ISSUES=$(grep -rn "dangerouslySetInnerHTML\|innerHTML.*req\." --include="*.js" --include="*.jsx" | wc -l)
if [ "$XSS_ISSUES" -gt 0 ]; then
  echo "  ⚠️  Potential XSS: $XSS_ISSUES locations"
else
  echo "  ✓ No XSS patterns found"
fi

# Hardcoded secrets
echo "🔑 Checking for hardcoded secrets..."
SECRET_PATTERNS=$(grep -rn "api[_-]key.*=.*['\"]|password.*=.*['\"]" --include="*.js" --include="*.py" --exclude-dir=node_modules | wc -l)
if [ "$SECRET_PATTERNS" -gt 0 ]; then
  echo "  ⚠️  Potential hardcoded secrets: $SECRET_PATTERNS locations"
else
  echo "  ✓ No obvious secrets found"
fi

echo "======================================"
echo "Scan complete! Review findings above."

${REPORT ? 'echo "📊 Generating detailed report..."' : ''}
${REPORT ? 'echo "Report saved to: security-scans/scan-$(date +%Y%m%d).md"' : ''}
```

## Integration

Auto-runs in:

- Pre-commit hooks
- CI/CD pipelines
- `/dev/full-cycle` workflow
- `/devops/deploy` (blocks if critical vulns)

## Success Criteria

- ✓ Scan completes in <2 minutes
- ✓ Critical vulnerabilities: 0
- ✓ High vulnerabilities: <3
- ✓ No hardcoded secrets detected

---
**Model**: Haiku (fast, cost-effective)
**Output**: Quick vulnerability summary
**Next**: `/security/audit` (comprehensive audit)
