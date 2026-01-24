---
description: Comprehensive health check across all project systems
argument-hint: [--category code|deps|infra|db|security|monitoring|all] [--fix-auto] [--save]
model: claude-sonnet-4-5-20250929
allowed-tools: [Bash, Read, Task]
---

# /system:health-check

System health check: **${ARGUMENTS:-all systems}**

## Step 1: Detect Project Services

Identify active systems:

- Backend API (Express, Fastify, Next.js)
- Frontend (React, Vue, Angular)
- Database (PostgreSQL, MySQL, MongoDB)
- Cache (Redis, Memcached)
- Background jobs (Bull, Agenda)

## Step 2: Code Health Checks

```bash
# Linter
npm run lint 2>&1

# Type check
npx tsc --noEmit 2>&1

# Tests
npm test -- --coverage 2>&1

# Build
npm run build 2>&1
```

Score: Passing tests × 40 + No lint errors × 30 + Types valid × 30

## Step 3: Dependency Health

```bash
npm outdated --json
npm audit --json
```

Check for:

- Outdated packages (>6 months old)
- Security vulnerabilities
- License compliance issues

## Step 4: Infrastructure Health

```bash
# Docker services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Disk space
df -h | grep -E '^/dev'

# Memory
free -h
```

## Step 5: Database Health

```bash
# PostgreSQL
psql -c "SELECT version();"
psql -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# Check connections
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

## Step 6: Security Scan

- Check for exposed secrets (grep -r "API_KEY\|SECRET\|PASSWORD" --exclude-dir=node_modules)
- Check SSL certificates (expiry)
- Review authentication config

## Step 7: Generate Report

```markdown
# 🏥 System Health Report

## Overall Health: ${score}/100 ${emoji}

### Code Health: ${codeScore}/40
- ✅ Tests: ${testsPassing}/${testsTotal} passing
- ${lintStatus} Linter: ${lintErrors} errors
- ${typeStatus} Types: ${typeErrors} errors

### Dependencies: ${depsScore}/30
- Outdated: ${outdatedCount} packages
- Security: ${vulnCount} vulnerabilities (${criticalCount} critical)

### Infrastructure: ${infraScore}/20
- Services: ${runningServices}/${totalServices} running
- Disk: ${diskUsage}% used
- Memory: ${memUsage}% used

### Database: ${dbScore}/10
- Status: ${dbStatus}
- Size: ${dbSize}
- Connections: ${dbConnections}/${dbMaxConnections}

## Action Items
${actionItems.map(i => `- [${i.priority}] ${i.description}`).join('\n')}
```

**Command Complete** 🏥
