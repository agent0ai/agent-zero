# Agent Jumbo: Deployment & Operations Guide

**Document Version**: 1.0
**Last Updated**: 2026-01-17
**Audience**: DevOps engineers, SREs, operations teams

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Procedures](#deployment-procedures)
3. [Environment Configuration](#environment-configuration)
4. [Monitoring & Observability](#monitoring--observability)
5. [Incident Response](#incident-response)
6. [Scaling & Performance Tuning](#scaling--performance-tuning)
7. [Backup & Disaster Recovery](#backup--disaster-recovery)
8. [Security Operations](#security-operations)
9. [Maintenance Schedule](#maintenance-schedule)
10. [Troubleshooting Guide](#troubleshooting-guide)

---

## Pre-Deployment Checklist

### Code Readiness (48 hours before deployment)

- [ ] All tests passing: `pytest tests/ -v` (480 tests minimum)
- [ ] Code coverage >90%: `pytest tests/ --cov=python --cov-report=term`
- [ ] No security vulnerabilities: `bandit -r python/`
- [ ] No credential exposure: `detect-secrets scan`
- [ ] Linting passes: `ruff check python/`
- [ ] Type checking passes: `mypy python/ --strict`
- [ ] Documentation updated for new features
- [ ] CHANGELOG.md updated with version notes
- [ ] Git history clean: No untracked files in deployment branch

### Infrastructure Readiness (72 hours before deployment)

- [ ] Database migrations tested in staging
- [ ] Load test completed (target: 1000 concurrent agents)
- [ ] Backup systems verified and tested
- [ ] Monitoring dashboards created and validated
- [ ] Alerting rules configured for critical metrics
- [ ] SSL certificates valid (>30 days expiry)
- [ ] DNS records pointing to staging (for final test)
- [ ] API rate limiting configured
- [ ] External service credentials rotated
- [ ] Disaster recovery plan reviewed

### Team Readiness (24 hours before deployment)

- [ ] Deployment lead assigned and trained
- [ ] On-call schedule updated
- [ ] Incident response team briefed
- [ ] Rollback procedures documented and tested
- [ ] Communication plan established (Slack, email, dashboard)
- [ ] Stakeholders notified of maintenance window
- [ ] Product team approved release notes
- [ ] Finance team confirmed resource costs

---

## Deployment Procedures

### Automated Deployment Pipeline

**Trigger**: Git tag push to main branch

```bash
# Create annotated release tag
git tag -a v1.4.0 -m "Phase 4A: Specialist Agent Framework Release"
git push origin v1.4.0

# Pipeline automatically:
# 1. Runs full test suite
# 2. Builds Docker image: agent-jumbo:1.4.0
# 3. Pushes to registry
# 4. Updates staging environment
# 5. Runs smoke tests
# 6. Awaits manual approval
# 7. Deploys to production
# 8. Monitors for errors (30 minutes)
# 9. Rolls back if critical errors detected
```

### Blue-Green Deployment

**Goal**: Zero-downtime deployments with instant rollback capability

**Process**:

```
Time 0:
  Blue (v1.3.0): 100% traffic ✓
  Green (v1.4.0): 0% traffic (warming up)

Time T+5min (health checks pass):
  Blue (v1.3.0): 50% traffic
  Green (v1.4.0): 50% traffic (canary)

Time T+15min (no errors, metrics good):
  Blue (v1.3.0): 0% traffic
  Green (v1.4.0): 100% traffic ✓

Time T+30min (all monitoring green):
  Finalize deployment
  Decommission Blue

If errors detected at any point:
  Blue (v1.3.0): 100% traffic (instant rollback)
  Green (v1.4.0): Decommissioned
```

**Commands**:

```bash
# Prepare blue-green deployment
./scripts/deploy_bluegreen.sh --version=1.4.0 --environment=production

# Monitor canary phase
watch -n 5 'kubectl logs -l app=agent-jumbo,version=1.4.0 | tail -20'

# Finalize deployment (after manual approval)
kubectl patch service agent-jumbo -p '{"spec":{"selector":{"version":"1.4.0"}}}'

# Rollback if needed (instant)
kubectl patch service agent-jumbo -p '{"spec":{"selector":{"version":"1.3.0"}}}'
```

### Manual Deployment (Emergency Only)

```bash
# 1. Build image
docker build -t agent-jumbo:1.4.0-manual .

# 2. Tag and push
docker tag agent-jumbo:1.4.0-manual gcr.io/project/agent-jumbo:1.4.0-manual
docker push gcr.io/project/agent-jumbo:1.4.0-manual

# 3. Update deployment
kubectl set image deployment/agent-jumbo \
  agent-jumbo=gcr.io/project/agent-jumbo:1.4.0-manual --record

# 4. Monitor rollout
kubectl rollout status deployment/agent-jumbo

# 5. Verify health
curl https://api.agent-jumbo.io/health
# Expected: {"status": "healthy", "version": "1.4.0-manual"}
```

### Database Migrations

**Procedure**: Run migrations BEFORE code deployment

```bash
# 1. Backup production database
pg_dump production_db > backups/prod_$(date +%Y%m%d_%H%M%S).sql

# 2. Test migration on staging
./scripts/migrate.sh --environment=staging --version=1.4.0

# 3. Verify staging functionality (smoke tests)
pytest tests/e2e/ -m production_like

# 4. Run migration on production
./scripts/migrate.sh --environment=production --version=1.4.0

# 5. Verify production functionality
curl https://api.agent-jumbo.io/health/database
# Expected: {"status": "ok", "migrations_applied": "1.4.0"}

# 6. Monitor error rates for 5 minutes
# If errors increase >5%, run rollback migration
./scripts/migrate.sh --environment=production --rollback --version=1.4.0
```

**Migration Best Practices**:

- Always create backward-compatible migrations
- Test rollback scripts in staging
- Use feature flags to control behavior during migration
- Keep migrations small (<10 seconds execution)
- Never lock tables for >1 minute in production

---

## Environment Configuration

### Development Environment

**Purpose**: Local development, rapid iteration

```yaml
# .env.development
DATABASE_URL: sqlite:///./agent_jumbo.db
LLM_MODEL: claude-3-5-sonnet-20241022
LLM_API_KEY: sk-ant-...
ENVIRONMENT: development
LOG_LEVEL: DEBUG
ENABLE_PROFILING: true
MEMORY_CONSOLIDATION_INTERVAL: 3600  # 1 hour
```

**Key Features**:

- Local SQLite (no external dependencies)
- Detailed logging for debugging
- Profiling enabled for performance analysis
- Hot reload for Python code changes
- Mock external services available

### Staging Environment

**Purpose**: Pre-production validation, performance testing

```yaml
# .env.staging
DATABASE_URL: postgresql://user:pass@staging-db:5432/agent_jumbo
LLM_MODEL: claude-3-5-sonnet-20241022
LLM_API_KEY: sk-ant-...
ENVIRONMENT: staging
LOG_LEVEL: INFO
ENABLE_PROFILING: false
MEMORY_CONSOLIDATION_INTERVAL: 3600

# TLS configuration
TLS_CERT_PATH: /etc/tls/staging-cert.pem
TLS_KEY_PATH: /etc/tls/staging-key.pem
```

**Infrastructure**:

- PostgreSQL database (single node, development-like)
- Real external service integrations (test credentials)
- ELK stack for log aggregation
- Prometheus/Grafana for metrics

### Production Environment

**Purpose**: Live system serving users

```yaml
# .env.production (stored in Vault)
DATABASE_URL: postgresql://...@prod-db-cluster:5432/agent_jumbo
DATABASE_REPLICA_URL: postgresql://...@prod-db-replica:5432/agent_jumbo
LLM_MODEL: claude-3-5-sonnet-20241022
LLM_API_KEY: ${VAULT_CLAUDE_API_KEY}
ENVIRONMENT: production
LOG_LEVEL: WARNING
ENABLE_PROFILING: false
MEMORY_CONSOLIDATION_INTERVAL: 86400  # 24 hours

# HA Configuration
DATABASE_POOL_SIZE: 100
DATABASE_POOL_TIMEOUT: 30
CACHE_REDIS_CLUSTER: redis-cluster-1:6379,redis-cluster-2:6379,redis-cluster-3:6379

# Security
ENCRYPTION_KEY: ${VAULT_ENCRYPTION_KEY}
JWT_SECRET: ${VAULT_JWT_SECRET}
TLS_CERT_PATH: /etc/tls/production-cert.pem
TLS_KEY_PATH: /etc/tls/production-key.pem

# Cost Management
LLM_TOKEN_BUDGET_PER_DAY: 500000  # ~$100
LLM_COST_ALERT_THRESHOLD: 80  # % of budget

# Operational
MAX_CONCURRENT_AGENTS: 1000
REQUEST_TIMEOUT: 30
SHUTDOWN_TIMEOUT: 60
```

**Secret Management**:

```bash
# Store secrets in HashiCorp Vault
vault kv put secret/agent-jumbo/prod \
  claude_api_key=sk-ant-... \
  encryption_key=... \
  jwt_secret=...

# Load at deployment time
export $(vault kv get -format=env secret/agent-jumbo/prod)
```

---

## Monitoring & Observability

### Key Metrics Dashboard

**System Health Metrics**:

| Metric | Target | Alert | Dashboard |
|--------|--------|-------|-----------|
| **API Latency (p95)** | <200ms | >500ms | Real-time |
| **Error Rate** | <0.1% | >1% | Real-time |
| **Database Latency** | <50ms | >100ms | Real-time |
| **Memory Usage** | <80% | >90% | System |
| **CPU Usage** | <70% | >85% | System |
| **Disk Space** | <80% | >90% | System |

**Business Metrics**:

| Metric | Target | Alert | Dashboard |
|--------|--------|-------|-----------|
| **Agents Running** | >100 | <50 | Operations |
| **Tasks Completed** | >10k/day | <5k/day | Operations |
| **LLM Cost/Day** | <$100 | >$120 | Cost |
| **User Satisfaction** | >4.5/5 | <4.0/5 | Product |

### Log Aggregation (ELK Stack)

**Log Fields** (all logs include):

```json
{
  "@timestamp": "2026-01-17T10:30:00Z",
  "level": "ERROR",
  "logger": "agent_jumbo.tools.calendar_sync",
  "message": "Failed to sync calendar",
  "environment": "production",
  "agent_id": "research_001",
  "request_id": "req_abc123",
  "user_id": "user_456",
  "duration_ms": 1234,
  "status_code": 500,
  "error_type": "CalendarSyncError",
  "stack_trace": "..."
}
```

**Common Searches**:

```
# Find all errors in past hour
level:ERROR AND @timestamp:[now-1h TO now]

# Find slow queries
duration_ms:[1000 TO *] AND logger:*database*

# Find user's activity
user_id:user_456 AND @timestamp:[now-24h TO now]

# Find agent issues
agent_id:research_001 AND level:(ERROR OR WARN)
```

### Distributed Tracing (Jaeger)

**Setup**: All requests have unique trace ID

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_reservation") as span:
    span.set_attribute("reservation_id", "r123")
    span.set_attribute("property_id", "p456")
    # Operation traced end-to-end across services
```

**Visualization**: Jaeger UI shows complete request flow with latency breakdown

### Alerting Rules

**Critical Alerts** (immediate escalation):

```yaml
# Alert if API error rate exceeds 1%
alert: HighErrorRate
expr: increase(http_requests_total{status=~"5.."}[5m]) / increase(http_requests_total[5m]) > 0.01
for: 1m
annotations:
  severity: critical
  summary: "High error rate detected"
  action: "Page on-call engineer"

# Alert if database is unreachable
alert: DatabaseDown
expr: pg_up == 0
for: 30s
annotations:
  severity: critical
  summary: "Database is down"
  action: "Activate disaster recovery"
```

**Warning Alerts** (notify team):

```yaml
# Alert if API latency p95 > 500ms
alert: HighLatency
expr: histogram_quantile(0.95, http_request_duration_seconds) > 0.5
for: 5m

# Alert if memory usage > 80%
alert: HighMemoryUsage
expr: memory_usage_percent > 80
for: 10m
```

---

## Incident Response

### Incident Severity Classification

| Severity | Impact | Response Time | Example |
|----------|--------|---------------|---------|
| **P1 (Critical)** | Complete service down | <5 min | API returns 500s for all users |
| **P2 (High)** | Major functionality impaired | <15 min | Agent response time 10x normal |
| **P3 (Medium)** | Some users affected | <1 hour | Specific calendar sync failing |
| **P4 (Low)** | Minor issue, workaround exists | <24 hours | Slow dashboard loading |

### Incident Command System (ICS)

**Roles During Incident**:

- **Incident Commander**: Coordinates response, decides escalation/rollback
- **Technical Lead**: Diagnoses issue, directs fixes
- **Comms Lead**: Updates stakeholders every 5 minutes
- **Scribe**: Documents timeline and decisions

**Activation**:

```bash
# Trigger incident response
/incident-start P1 "API returning 500 errors" @oncall-team

# Automatically:
# 1. Creates Slack war room
# 2. Pages on-call engineer
# 3. Starts incident tracking
# 4. Notifies management
# 5. Starts status page update
```

### Common Incident Playbooks

#### Playbook 1: High Error Rate

```
1. CHECK: What's the error rate? (should be <0.1%)
   curl https://prometheus.internal:9090/api/v1/query?query=rate(http_errors_total[5m])

2. IDENTIFY: Is it affecting all endpoints or specific endpoints?
   - Check logs: level:ERROR AND @timestamp:[now-5m TO now]
   - Filter by endpoint: path:"/api/agents" vs. all endpoints

3. INVESTIGATE:
   - If recent deployment: ROLLBACK immediately
   - If database issue: Check postgres connection pool
   - If external service: Check status page

4. MITIGATE:
   - Scale up API servers if CPU high
   - Kill stuck database connections if needed
   - Enable circuit breaker if external service is flaky

5. RESOLVE:
   - Once error rate <0.1% for 5 minutes, declare resolved
   - Post-incident review within 24 hours
   - Update monitoring to catch earlier next time
```

#### Playbook 2: Database Slow/Unavailable

```
1. VERIFY: Is database actually down?
   psql -h prod-db-primary.internal -U operator -c "SELECT 1"

2. CHECK: If unavailable, failover to replica
   # Promote read replica to primary
   kubectl exec -it postgres-primary -- \
     pg_ctl promote -D /var/lib/postgresql/data

3. CHECK: If slow, identify slow queries
   SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

4. MITIGATE:
   - Kill long-running queries: SELECT pg_terminate_backend(pid) ...
   - Check index usage: SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0
   - Review recent migrations for lock contention

5. RESOLVE:
   - Once latency <50ms stable, declare resolved
   - Add monitoring for slow query detection
```

#### Playbook 3: Memory Leak / High Memory Usage

```
1. CHECK: Memory trend
   kubectl top pod agent-jumbo-xxx
   # Compare to baseline (should be <2GB)

2. IDENTIFY: Is it growing? Take memory dumps
   jmap -dump:live,format=b,file=heap.bin <PID>

3. ANALYZE: Use memory profiler
   python -m memory_profiler agent.py

4. MITIGATE:
   - Restart pod (temporary): kubectl delete pod agent-jumbo-xxx
   - Enable memory consolidation: POST /admin/consolidate-memory
   - Reduce concurrent agents if needed

5. RESOLVE:
   - Identify root cause (memory leak in code)
   - Create fix, test in staging, deploy
```

### Post-Incident Review (PIR)

**Timeline** (30 mins after incident resolved):

```markdown
## Incident: API Returning 500 Errors
**Date**: 2026-01-17 10:30-10:45 UTC
**Duration**: 15 minutes
**Impact**: 2,500 API requests failed
**Status**: RESOLVED

### Timeline
10:30 - Error rate alert triggered (1% of requests)
10:31 - IC activated, tech lead investigating
10:33 - Identified: Recent deployment v1.4.0 has bug in memory consolidation
10:35 - Rollback initiated to v1.3.0
10:38 - Rollback complete, error rate returned to <0.1%
10:45 - All checks green, incident resolved

### Root Cause
Async memory consolidation not awaiting properly, causing event loop to hang

### Action Items
- [ ] Fix memory consolidation bug in v1.4.0
- [ ] Add unit tests for consolidation edge cases
- [ ] Add alert for event loop lag (5s latency jump)
- [ ] Improve pre-deployment testing of memory-intensive operations

### Prevention
- Always profile memory usage before deployment
- Add integration tests for concurrent operations
- Implement circuit breaker for memory consolidation
```

---

## Scaling & Performance Tuning

### Horizontal Scaling

**Add More API Servers**:

```bash
# Current state
kubectl get pods -l app=agent-jumbo
# NAME                      READY   STATUS    REPLICAS
# agent-jumbo-1              1/1     Running   1
# agent-jumbo-2              1/1     Running   1
# agent-jumbo-3              1/1     Running   1

# Scale to 5 replicas
kubectl scale deployment agent-jumbo --replicas=5

# Monitor scaling progress
watch kubectl get pods -l app=agent-jumbo
```

**Load Balancer Configuration**:

```nginx
upstream agent_jumbo_backend {
    # Round-robin load balancing
    server api-1.internal:8000 weight=1;
    server api-2.internal:8000 weight=1;
    server api-3.internal:8000 weight=1;

    # Health check: remove unhealthy servers
    check interval=3000 rise=2 fall=5 timeout=1000 type=http;
    check_http_send "GET /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}

server {
    listen 443 ssl http2;
    ssl_certificate /etc/tls/cert.pem;
    ssl_certificate_key /etc/tls/key.pem;

    location /api {
        proxy_pass http://agent_jumbo_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

### Vertical Scaling

**Increase Server Resources**:

```bash
# Update pod resource requests/limits
kubectl set resources deployment agent-jumbo \
  --requests=cpu=2,memory=4Gi \
  --limits=cpu=4,memory=8Gi

# Verify
kubectl describe deployment agent-jumbo
```

**Database Scaling**:

```yaml
# Kubernetes manifests for database scaling
apiVersion: postgres-operator.crunchydata.com/v1beta1
kind: PostgresCluster
metadata:
  name: agent-jumbo-db
spec:
  imagePrefix: registry.developers.crunchydata.com/crunchydata
  postgresVersion: 15
  instances:
    - name: postgres
      replicas: 3  # Primary + 2 replicas
      resources:
        requests:
          cpu: 4
          memory: 16Gi
        limits:
          cpu: 8
          memory: 32Gi
  backups:
    pgbackrest:
      repos:
        - name: repo1
          s3:
            bucket: agent-jumbo-backups
```

### Performance Tuning

**Database Connection Pool**:

```python
# In production configuration
DATABASE_POOL_SIZE = 100  # Max connections per instance
DATABASE_POOL_TIMEOUT = 30  # Wait 30s for available connection

# Monitor pool usage
SELECT count(*) FROM pg_stat_activity;
# Should stay <80 of pool_size
```

**Memory Consolidation Tuning**:

```python
# Run consolidation less frequently in production
MEMORY_CONSOLIDATION_INTERVAL = 86400  # Once per day

# But consolidate more aggressively per consolidation
CONSOLIDATION_BATCH_SIZE = 5000  # Consolidate 5000 at a time
CONSOLIDATION_TIMEOUT = 300  # Max 5 minutes per consolidation
```

**LLM API Optimization**:

```python
# Enable prompt caching
llm_config = {
    "model": "claude-3-5-sonnet-20241022",
    "cache_control": {
        "type": "ephemeral"  # Cache prompts for 5 minutes
    }
}
# Expected savings: ~30% of token costs

# Batch LLM calls when possible
results = await llm.batch_generate([
    {"prompt": "Summarize: ..."},
    {"prompt": "Analyze: ..."},
    {"prompt": "Classify: ..."},
])
# Expected savings: ~20% of API calls
```

---

## Backup & Disaster Recovery

### Backup Strategy

**Backup Schedule**:

| Type | Frequency | Retention | Target RPO |
|------|-----------|-----------|-----------|
| **Continuous WAL** | Every 1 min | 30 days | <1 min |
| **Full Daily Backup** | 02:00 UTC | 90 days | 24 hours |
| **Weekly Snapshot** | Sunday 03:00 | 1 year | 7 days |

**Backup Procedure**:

```bash
# Full database backup (automated daily)
pg_basebackup -h prod-db.internal \
  -D /backups/agent_jumbo_$(date +%Y%m%d) \
  -Ft -z -P

# Verify backup integrity
pg_verify_backup -b /backups/agent_jumbo_20260117

# Upload to S3 with encryption
aws s3 cp /backups/agent_jumbo_20260117.tar.gz \
  s3://agent-jumbo-backups/ \
  --sse AES256 \
  --metadata "backup_date=2026-01-17,checksum=abc123"
```

### Disaster Recovery Procedures

**Scenario 1: Database Corruption (Recoverable)**

```bash
# 1. Stop application
kubectl scale deployment agent-jumbo --replicas=0

# 2. Restore from latest backup (within 1 min due to WAL)
pg_ctl stop
rm -rf /var/lib/postgresql/data
pg_basebackup -h backup-server -D /var/lib/postgresql/data

# 3. Replay WAL logs from time of backup to time of corruption
pg_ctl start
# PostgreSQL automatically replays WAL logs

# 4. Verify data integrity
psql -c "SELECT COUNT(*) FROM agents;"
psql -c "PRAGMA integrity_check;" # If SQLite

# 5. Restart application
kubectl scale deployment agent-jumbo --replicas=3
```

**Scenario 2: Complete Regional Failure (Multi-region Setup)**

```bash
# 1. Detect primary region down (health check timeout)
curl https://api.agent-jumbo.io/health
# No response for >2 minutes

# 2. Automatic failover to secondary region (DNS update)
# Terraform automatically updates Route53 to point to us-west-2 region
# Expected time: <3 minutes

# 3. Verify secondary region is healthy
curl https://api-secondary.agent-jumbo.io/health
# Expected: {"status": "healthy", "region": "us-west-2"}

# 4. Database read replica promotes to primary
# Managed by RDS Multi-AZ failover (automatic)

# 5. Manually restore primary region once stable
aws ec2 create-instances --image-id ami-agent-jumbo --count 3 --region us-east-1
kubectl apply -f manifests/agent-jumbo-east.yaml
```

### Testing Disaster Recovery

**RTO (Recovery Time Objective)**: <1 hour
**RPO (Recovery Point Objective)**: <15 minutes

**Monthly DR Test**:

```bash
# Simulate disaster recovery
1. Backup current database: pg_dump production_db > current.sql
2. Restore to clean database: psql recovery_db < current.sql
3. Run smoke tests against recovery database
4. Measure recovery time: _end - _start
5. Document any issues

# Acceptance criteria:
- Recovery time <1 hour
- Data loss <15 minutes
- All critical systems operational post-recovery
- No manual intervention during recovery
```

---

## Security Operations

### Secrets Rotation

**Quarterly Rotation**:

```bash
# 1. Generate new secrets
NEW_JWT_SECRET=$(openssl rand -base64 32)
NEW_ENCRYPTION_KEY=$(openssl rand -hex 32)

# 2. Store in Vault
vault kv put secret/agent-jumbo/prod \
  jwt_secret=$NEW_JWT_SECRET \
  encryption_key=$NEW_ENCRYPTION_KEY

# 3. Deploy new version with both old and new keys (for grace period)
# Application validates with both keys for 24 hours

# 4. Deploy version with only new key after grace period
# Old tokens/data will fail (expected)

# 5. Verify all systems working
curl https://api.agent-jumbo.io/health
```

### Credential Scanning

**Pre-commit Hook** (prevents credential leaks):

```bash
# In .git/hooks/pre-commit
detect-secrets scan --all-files --force-addition
if [ $? -ne 0 ]; then
    echo "Credentials detected in staged files"
    echo "Run: git reset HEAD <file> to unstage"
    exit 1
fi
```

**Ongoing Scanning**:

```bash
# Daily scan for leaked credentials
0 2 * * * /opt/scripts/scan_repos.sh

# Alert if any credentials found
if [ $? -ne 0 ]; then
    /opt/scripts/notify_security_team.sh "Credentials found in repo"
    # Automatic rotation of exposed credentials
    /opt/scripts/rotate_secrets.sh
fi
```

### Access Control & Audit

**Production Access Restrictions**:

```bash
# Only on-call engineer can SSH to production
ssh -i ~/.ssh/prod-onecall.key admin@api-1.internal

# All SSH sessions logged to audit system
# Commands recorded and searchable by user/timestamp

# sudo access requires MFA and approval
sudo su - agent_jumbo
# Prompt: "MFA code: " + "Approval needed from: ops-team-lead@company.com"
```

**Audit Log Archival**:

```bash
# Logs shipped to immutable S3 bucket
# Locked with governance lock (can't delete for 90 days)
aws s3api put-object-lock-legal-hold \
    --bucket agent-jumbo-audit-logs \
    --key logs/2026-01-17.tar.gz \
    --legal-hold Status=ON

# Quarterly review of access logs
# Report on: Who accessed what, when, why
```

---

## Maintenance Schedule

### Daily Tasks

- [ ] **08:00 UTC**: Check critical metrics (error rate, latency, uptime)
- [ ] **16:00 UTC**: Review alerts and resolve any P3/P4 issues
- [ ] **20:00 UTC**: Backup verification (at least 1 backup succeeded)

### Weekly Tasks

- [ ] **Monday 09:00 UTC**: Code scan for security vulnerabilities
- [ ] **Wednesday 02:00 UTC**: Database optimization (VACUUM, ANALYZE)
- [ ] **Friday 15:00 UTC**: Performance review (latency trends, capacity)

### Monthly Tasks

- [ ] **First Monday**: DR testing (restore database from backup)
- [ ] **Second Thursday**: Security audit (access logs, credential rotation)
- [ ] **Third Tuesday**: Capacity planning review (growth projections)
- [ ] **Last Friday**: Team training on new tools/processes

### Quarterly Tasks

- [ ] Secrets rotation (JWT, encryption keys, API credentials)
- [ ] SSL certificate renewal check (ensure >90 days validity)
- [ ] Database index analysis and optimization
- [ ] Load test (validate scaling capacity)
- [ ] Disaster recovery drill (full scenario)

### Annual Tasks

- [ ] Security audit by third party (SOC 2, HIPAA, PCI compliance)
- [ ] Architecture review (identify bottlenecks, plan improvements)
- [ ] Cost optimization review (reserved instances, CDN usage)
- [ ] Team training and certification renewal

---

## Troubleshooting Guide

### Problem: API Latency Increased 10x

**Step 1: Check system resources**

```bash
kubectl top pods -l app=agent-jumbo
# Check CPU and memory usage

free -h
# Check available memory on node

df -h
# Check disk space
```

**Step 2: Check database**

```bash
# Active connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Slow queries
psql -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Indexes
psql -c "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0;"
```

**Step 3: Check application logs**

```bash
# Last 100 error logs
kubectl logs -l app=agent-jumbo --tail=100 | grep ERROR

# Trace specific request
export REQUEST_ID=req_xyz
kubectl logs -l app=agent-jumbo | grep $REQUEST_ID
```

**Step 4: Check external services**

```bash
# Check LLM API latency
curl -w "Time: %{time_total}s\n" https://api.anthropic.com/

# Check calendar API
curl -w "Time: %{time_total}s\n" https://www.googleapis.com/calendar/v3/
```

### Problem: High Memory Usage

**Step 1: Identify memory leak**

```bash
# Take memory snapshot
kubectl exec agent-jumbo-1 -- \
  python -c "import tracemalloc; tracemalloc.start(); ..." > memory_trace.txt

# Analyze top memory consumers
python -c "
import sys
lines = open('memory_trace.txt').readlines()
for line in sorted(lines, reverse=True)[:10]:
    print(line)
"
```

**Step 2: Force memory consolidation**

```bash
curl -X POST https://api.internal:8000/admin/consolidate-memory

# Monitor memory drop
kubectl top pod agent-jumbo-1 --containers --watch
```

**Step 3: Restart if needed**

```bash
kubectl delete pod agent-jumbo-1
# Pod automatically respawns
```

### Problem: Database Connection Pool Exhausted

**Step 1: Identify blocked connections**

```bash
psql -c "
SELECT pid, usename, state, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start DESC;"
```

**Step 2: Kill long-running queries**

```bash
psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE query LIKE '%SELECT%' AND query_start < now() - interval '5 minutes';"
```

**Step 3: Increase pool size if legitimate load**

```yaml
# Update deployment
DATABASE_POOL_SIZE: 150  # Increase from 100

# Redeploy
kubectl set env deployment/agent-jumbo \
  DATABASE_POOL_SIZE=150
```

### Problem: Agent Not Responding to Requests

**Step 1: Check agent status**

```bash
curl https://api.internal:8000/agents/research_001
# Expected: {"status": "ready", "tasks_completed": 1234}

# If no response, check if pod is running
kubectl get pods -l app=agent-jumbo
```

**Step 2: Check for deadlock**

```bash
# Look for "task_started" but no "task_completed" events
kubectl logs -l app=agent-jumbo | grep research_001 | tail -20

# Check for hung message loop
if last event >5 minutes old without completion:
    kubectl delete pod agent-jumbo-1
fi
```

**Step 3: Check tool execution**

```bash
# Find which tool is stuck
curl https://api.internal:8000/admin/debug/agent/research_001
# Response shows current operation and duration

# If tool is stuck >30s, kill it
curl -X POST https://api.internal:8000/admin/kill-task/research_001
```

---

## Emergency Contacts & Escalation

**On-Call Schedule**: See Opsgenie for current on-call engineer

**Escalation Path**:

1. On-call engineer (P1-P2)
2. SRE lead (P1 after 15 min)
3. VP Engineering (P1 after 30 min, all customer impact)
4. CTO (P1 after 1 hour, reputation risk)

**Incident Slack Channel**: #incidents-agent-jumbo

**Status Page**: <https://status.agent-jumbo.io>

---

**Maintained by**: DevOps & SRE Team
**Questions**: #devops-questions Slack channel or <ops-team@company.com>
