---
description: Detect hardcoded secrets and credentials in codebase
argument-hint: [--scan-history]
model: claude-haiku-4-20250514
allowed-tools: Bash, Grep, Write
---

Check for secrets: **${ARGUMENTS}**

## Secret Detection

**Scans for**:

- API keys
- Passwords
- Tokens (JWT, OAuth, API)
- Private keys
- Database credentials
- AWS/GCP service account keys

```bash
echo "🔍 Scanning for hardcoded secrets..."
echo "======================================"

# Common secret patterns
PATTERNS=(
  "api[_-]?key"
  "password"
  "secret"
  "token"
  "private[_-]?key"
  "access[_-]?key"
  "client[_-]?secret"
  "bearer"
  "authorization"
  "credentials"
)

TOTAL_FINDINGS=0

for PATTERN in "${PATTERNS[@]}"; do
  COUNT=$(grep -rni "$PATTERN.*=.*['\"][^'\"]*['\"]" \
    --include="*.js" --include="*.ts" --include="*.py" --include="*.env*" \
    --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist \
    | grep -v "process.env\|process.getenv\|os.environ" \
    | wc -l)

  if [ "$COUNT" -gt 0 ]; then
    echo "⚠️  $PATTERN: $COUNT potential findings"
    TOTAL_FINDINGS=$((TOTAL_FINDINGS + COUNT))
  fi
done

# Check for .env files in git
ENV_IN_GIT=$(git ls-files | grep -E "\.env$|credentials\.json$" | wc -l)
if [ "$ENV_IN_GIT" -gt 0 ]; then
  echo "🚨 CRITICAL: .env or credentials files tracked in git!"
  git ls-files | grep -E "\.env$|credentials\.json$"
fi

# Check git history for leaked secrets (if --scan-history)
${SCAN_HISTORY ? 'echo "📜 Scanning git history..."' : ''}
${SCAN_HISTORY ? 'git log -p | grep -i "password\|api_key\|secret" | head -20' : ''}

echo "======================================"
if [ "$TOTAL_FINDINGS" -eq 0 ] && [ "$ENV_IN_GIT" -eq 0 ]; then
  echo "✅ No obvious secrets detected"
else
  echo "⚠️  Found $TOTAL_FINDINGS potential secrets"
  echo "👉 Review findings and move secrets to environment variables"
fi
```

## Best Practices

**DO**:

- Store secrets in GCP Secret Manager
- Use environment variables
- Add .env to .gitignore
- Rotate secrets regularly

**DON'T**:

- Hardcode API keys
- Commit .env files
- Share secrets in Slack/email
- Use same secrets in dev/prod

---
**Output**: List of potential hardcoded secrets
**Action**: Move to environment variables or Secret Manager
