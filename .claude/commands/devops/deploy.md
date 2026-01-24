---
description: Deploy application to multi-environment infrastructure with safety checks
argument-hint: <environment> [--skip-tests] [--skip-backup]
allowed-tools: Task, Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1800
retry: 1
cost_estimate: 0.20-0.35

validation:
  input:
    environment:
      required: true
      allowed_values: ["production", "staging", "development", "prod", "stage", "dev"]
      error_message: "Environment must be one of: production, staging, development"
  output:
    schema: .claude/validation/schemas/devops/deploy-output.json
    required_files:
      - 'deployments/${environment}_deployment_report.json'
    min_file_size: 300
    quality_threshold: 0.95
    content_requirements:
      - "Deployment status (success/failed/rolled-back)"
      - "Pre-deployment backup created"
      - "Health checks passed"
      - "Deployment URL accessible"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for environment"
      - "Added output validation for deployment reports"
      - "Streamlined from 449 lines to focused workflow"
      - "Enhanced safety checks and rollback procedures"
  - version: 1.0.0
    date: 2025-09-20
    changes:
      - "Initial implementation with multi-environment support"
---

# Deploy Application

Environment: **$ARGUMENTS**

## Step 1: Validate Input & Parse Arguments

```bash
ARGS="$ARGUMENTS"
ENVIRONMENT=$(echo "$ARGS" | awk '{print $1}')
SKIP_TESTS=$(echo "$ARGS" | grep -q '\-\-skip-tests' && echo "true" || echo "false")
SKIP_BACKUP=$(echo "$ARGS" | grep -q '\-\-skip-backup' && echo "false" || echo "true")

# Check environment provided
if [ -z "$ENVIRONMENT" ]; then
  echo "❌ ERROR: Missing environment"
  echo ""
  echo "Usage: /devops/deploy <environment> [--skip-tests] [--skip-backup]"
  echo "Example: /devops/deploy production"
  echo "Example: /devops/deploy staging --skip-tests"
  exit 1
fi

# Validate environment
case "$ENVIRONMENT" in
  production|prod)
    ENVIRONMENT="production"
    ;;
  staging|stage)
    ENVIRONMENT="staging"
    ;;
  development|dev)
    ENVIRONMENT="development"
    ;;
  *)
    echo "❌ ERROR: Invalid environment: $ENVIRONMENT"
    echo "Valid environments: production, staging, development"
    exit 1
    ;;
esac

echo "✓ Input validated: $ENVIRONMENT"
echo "  Skip tests: $SKIP_TESTS"
echo "  Create backup: $SKIP_BACKUP"
```

## Step 2: Pre-Deployment Approval (Production Only)

```bash
ENVIRONMENT="$ENVIRONMENT"

if [ "$ENVIRONMENT" = "production" ]; then
  echo ""
  echo "⚠️⚠️⚠️ PRODUCTION DEPLOYMENT ⚠️⚠️⚠️"
  echo "You are about to deploy to PRODUCTION."
  echo ""
  read -p "Type 'DEPLOY TO PRODUCTION' to confirm: " CONFIRMATION

  if [ "$CONFIRMATION" != "DEPLOY TO PRODUCTION" ]; then
    echo "❌ Deployment cancelled"
    exit 1
  fi

  echo "✓ Production deployment approved"
fi
```

## Step 3: Execute Deployment Using Agent

```javascript
const ENVIRONMENT = process.env.ENVIRONMENT;
const SKIP_TESTS = process.env.SKIP_TESTS === 'true';
const CREATE_BACKUP = process.env.SKIP_BACKUP !== 'false';

await Task({
  subagent_type: 'general-purpose',
  description: `Deploy to ${ENVIRONMENT} environment`,
  prompt: `Execute deployment to ${ENVIRONMENT} environment with comprehensive safety checks.

DEPLOYMENT REQUIREMENTS:

**1. Pre-Deployment Checks**:
- Verify Git repository is clean (no uncommitted changes)
- Check current branch matches deployment branch:
  * Production: main/master only
  * Staging: main/develop
  * Development: any branch
- Verify all tests passing (unless --skip-tests)
- Check build succeeds
- Verify environment variables configured

**2. Pre-Deployment Backup** ${CREATE_BACKUP ? '(ENABLED)' : '(SKIPPED)'}:
${CREATE_BACKUP ? `
- Backup database: /db/backup ${ENVIRONMENT}
- Backup current deployment artifacts
- Tag backup with deployment ID
- Verify backup successful
` : '- Skipped (--skip-backup flag)'}

**3. Build & Package**:
- Run build command (npm run build, docker build, etc.)
- Create deployment package
- Tag with version/commit hash
- Verify build artifacts

**4. Deploy**:
Deploy based on infrastructure:

**Container-based (Docker/Kubernetes)**:
- Build Docker image
- Tag image with version
- Push to container registry
- Update Kubernetes deployment
- Monitor rollout status

**Serverless (Cloud Functions)**:
- Package function code
- Deploy to cloud provider (GCP/AWS/Azure)
- Update function configuration
- Verify function deployed

**Traditional (VM/Server)**:
- Upload build artifacts via rsync/scp
- Run deployment scripts on server
- Restart services
- Verify services running

**5. Health Checks**:
Critical checks after deployment:
- HTTP health endpoint responding (200 OK)
- Database connectivity working
- External API integrations functioning
- Critical workflows testable

Retry health checks 3 times with 10s delay.

**6. Smoke Tests**:
Run basic functional tests:
- Homepage loads
- API endpoints respond
- Authentication works
- Critical user flows functional

**7. Rollback Plan** (if deployment fails):
${CREATE_BACKUP ? `
- Stop failed deployment
- Restore database from backup
- Revert to previous deployment
- Verify rollback successful
- Notify team of rollback
` : '- Manual rollback required (no backup)'}

**8. Post-Deployment**:
- Update deployment logs
- Tag Git commit with deployment
- Notify team (Slack/Discord)
- Update status page (if applicable)

**9. Generate Deployment Report**:
Save to: deployments/${ENVIRONMENT}_deployment_report.json
{
  "environment": "${ENVIRONMENT}",
  "deployment_status": "success|failed|rolled-back",
  "deployment_url": "https://...",
  "deployment_id": "unique-id",
  "pre_deployment_backup": ${CREATE_BACKUP},
  "tests_run": ${!SKIP_TESTS},
  "health_checks_passed": true|false,
  "smoke_tests_passed": true|false,
  "deployment_duration_seconds": 0,
  "deployed_at": "ISO timestamp",
  "git_commit": "hash",
  "version": "semver"
}

${ENVIRONMENT === 'production' ? `
⚠️ PRODUCTION DEPLOYMENT - Extra Monitoring:
- Monitor error rates for 15 minutes
- Watch system metrics (CPU, memory, requests)
- Be ready to rollback if issues detected
- Communicate with team during deployment
` : ''}

Provide:
- Deployment status
- Deployment URL
- Health check results
- Any warnings or issues`,

  context: {
    environment: ENVIRONMENT,
    skip_tests: SKIP_TESTS,
    create_backup: CREATE_BACKUP,
    deployment_report: `deployments/${ENVIRONMENT}_deployment_report.json`
  }
});
```

## Step 4: Validate Output

```bash
ENVIRONMENT="$ENVIRONMENT"
DEPLOYMENT_REPORT="deployments/${ENVIRONMENT}_deployment_report.json"

# Check deployment report created
if [ ! -f "$DEPLOYMENT_REPORT" ]; then
  echo "❌ ERROR: Deployment report not created"
  exit 1
fi

# Validate JSON
if ! jq empty "$DEPLOYMENT_REPORT" 2>/dev/null; then
  echo "❌ ERROR: Deployment report is not valid JSON"
  exit 1
fi

# Check deployment status
DEPLOYMENT_STATUS=$(jq -r '.deployment_status' "$DEPLOYMENT_REPORT")
HEALTH_CHECKS=$(jq -r '.health_checks_passed' "$DEPLOYMENT_REPORT")

if [ "$DEPLOYMENT_STATUS" != "success" ]; then
  echo "❌ ERROR: Deployment failed"
  echo "Status: $DEPLOYMENT_STATUS"
  exit 1
fi

if [ "$HEALTH_CHECKS" != "true" ]; then
  echo "⚠️  WARNING: Health checks failed"
fi

echo "✓ Output validation complete"
echo "  Status: $DEPLOYMENT_STATUS"
echo "  Health checks: $HEALTH_CHECKS"
```

## Completion

```
═══════════════════════════════════════════════════
        DEPLOYMENT COMPLETE ✓
═══════════════════════════════════════════════════

Environment: $ENVIRONMENT
Command: /devops/deploy
Version: 2.0.0

Deployment Status: [status]
  ✓ Pre-deployment checks passed
  ${CREATE_BACKUP ? '✓ Backup created' : '○ Backup skipped'}
  ✓ Build successful
  ✓ Deployed to infrastructure
  ✓ Health checks passed
  ✓ Smoke tests passed

Deployment URL: [url]
Deployment ID: [id]
Version: [version]
Git Commit: [hash]

Validations Passed:
  ✓ Input validation (environment valid)
  ✓ Output validation (deployment report created)
  ✓ Deployment successful
  ✓ Quality threshold (≥0.95)

NEXT STEPS:
${ENVIRONMENT === 'production' ?
'→ Monitor production metrics for 15 minutes
→ Watch error rates and system health
→ Be ready to rollback if issues arise
→ Notify stakeholders of deployment' :
'→ Test deployed application
→ Verify all features working
→ Run integration tests if available'}

═══════════════════════════════════════════════════
```

## Guidelines

- **Test Before Deploy**: Always run tests before deploying
- **Backup Production**: Always backup production before deploying
- **Approve Production**: Require explicit approval for production
- **Health Checks**: Verify health checks pass before considering success
- **Monitor After Deploy**: Watch metrics for 15+ minutes after production deploy
- **Rollback Ready**: Have rollback plan and be ready to execute
- **Communicate**: Notify team before/during/after production deployments
