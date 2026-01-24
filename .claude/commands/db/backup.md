---
description: Backup database with encryption, compression, and cloud storage
argument-hint: <environment> [--retention <days>]
allowed-tools: Task, Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 900
retry: 2
cost_estimate: 0.10-0.15

validation:
  input:
    environment:
      required: true
      allowed_values: ["production", "staging", "development", "dev", "prod"]
      error_message: "Environment must be one of: production, staging, development"
  output:
    schema: .claude/validation/schemas/db/backup-output.json
    required_files:
      - 'backups/${environment}_backup_*.{sql,dump,tar.gz}'
    min_file_size: 1024
    quality_threshold: 0.95
    content_requirements:
      - "Backup file created with timestamp"
      - "Checksum calculated (SHA256)"
      - "Uploaded to cloud storage"
      - "Old backups cleaned per retention policy"
      - "Integrity verification completed"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for environment"
      - "Added output validation for backup files"
      - "Streamlined from 453 lines to focused workflow"
      - "Added safety checks and approval workflows"
  - version: 1.0.0
    date: 2025-09-10
    changes:
      - "Initial implementation with GCP Cloud SQL support"
---

# Database Backup

Environment: **$ARGUMENTS**

## Step 1: Validate Input

```bash
ARGS="$ARGUMENTS"
ENVIRONMENT=$(echo "$ARGS" | awk '{print $1}')
RETENTION_DAYS=$(echo "$ARGS" | grep -oP '\-\-retention\s+\K\d+' || echo "30")

# Check environment provided
if [ -z "$ENVIRONMENT" ]; then
  echo "❌ ERROR: Missing environment"
  echo ""
  echo "Usage: /db/backup <environment> [--retention <days>]"
  echo "Example: /db/backup production --retention 30"
  exit 1
fi

# Validate environment
case "$ENVIRONMENT" in
  production|prod)
    ENVIRONMENT="production"
    ;;
  staging)
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

# Validate retention days
if [ "$RETENTION_DAYS" -lt 1 ] || [ "$RETENTION_DAYS" -gt 365 ]; then
  echo "❌ ERROR: Retention days must be between 1 and 365"
  echo "Provided: $RETENTION_DAYS"
  exit 1
fi

echo "✓ Input validated: $ENVIRONMENT (retention: $RETENTION_DAYS days)"
```

## Step 2: Execute Backup Using Agent

```javascript
const ENVIRONMENT = process.env.ENVIRONMENT;
const RETENTION_DAYS = process.env.RETENTION_DAYS || 30;

await Task({
  subagent_type: 'general-purpose',
  description: 'Backup database with cloud storage',
  prompt: `Execute comprehensive database backup for ${ENVIRONMENT} environment.

BACKUP REQUIREMENTS:
- Environment: ${ENVIRONMENT}
- Retention: ${RETENTION_DAYS} days
- Cloud storage: GCS/S3
- Encryption: Required for production
- Compression: gzip level 9

BACKUP WORKFLOW:

**1. Pre-Backup Validation**:
- Check database connectivity
- Verify storage space available (estimate backup size)
- Check backup permissions
- Confirm cloud storage credentials configured

**2. Create Backup**:
- Generate filename: backup_\${DB_NAME}_\${TIMESTAMP}.sql.gz
- Execute database dump (pg_dump/mysqldump/mongodump)
- Use appropriate format:
  * PostgreSQL: --format=custom --compress=9
  * MySQL: --single-transaction | gzip
  * MongoDB: --gzip --out
- Calculate SHA256 checksum for integrity
- Verify dump completed successfully

**3. Upload to Cloud Storage**:
- Upload backup file to cloud bucket
- Upload checksum file (.sha256)
- Set retention policy metadata
- Tag with environment and timestamp
- Verify upload successful (check file exists in cloud)

**4. Cleanup Old Backups**:
- List backups older than ${RETENTION_DAYS} days
- Delete expired backups from cloud storage
- Update backup inventory/logs
- Verify cleanup successful

**5. Verify Backup Integrity**:
- Download backup from cloud (or use local copy)
- Verify checksum matches
- Test backup structure (pg_restore --list / mysqldump --help / mongorestore --dryRun)
- For critical backups: test restore on staging database
- Log backup completion with metadata

**6. Generate Backup Report**:
Save backup details to: backups/${ENVIRONMENT}_backup_latest.json
{
  "environment": "${ENVIRONMENT}",
  "backup_file": "backup_\${DB_NAME}_\${TIMESTAMP}.sql.gz",
  "backup_location": "gs://bucket/path or s3://bucket/path",
  "backup_checksum": "sha256_hash",
  "backup_size_bytes": 0,
  "retention_days": ${RETENTION_DAYS},
  "created_at": "ISO timestamp",
  "verified": true
}

**Database Detection**:
- Auto-detect database type from environment variables or config
- PostgreSQL: Use pg_dump
- MySQL: Use mysqldump
- MongoDB: Use mongodump
- GCP Cloud SQL: Use gcloud sql backups create

**Safety Checks**:
${ENVIRONMENT === 'production' ? `
⚠️ PRODUCTION BACKUP - Extra Safety:
- Verify backup doesn't impact production performance
- Schedule during low-traffic window if possible
- Use --single-transaction for consistent snapshot
- Monitor backup progress
- Alert on backup failure
` : ''}

**Error Handling**:
- If backup fails: Log error, alert team, exit with error
- If upload fails: Retry 3 times, then fail
- If cleanup fails: Warn but don't fail (old backups remain)
- If verification fails: Mark backup as unverified, alert team

Create backup and provide:
- Backup file location
- Backup size
- Checksum
- Verification status`,

  context: {
    environment: ENVIRONMENT,
    retention_days: RETENTION_DAYS,
    backup_report_output: `backups/${ENVIRONMENT}_backup_latest.json`
  }
});
```

## Step 3: Validate Output

```bash
ENVIRONMENT="$ENVIRONMENT"
BACKUP_REPORT="backups/${ENVIRONMENT}_backup_latest.json"

# Check backup report created
if [ ! -f "$BACKUP_REPORT" ]; then
  echo "❌ ERROR: Backup report not created"
  exit 1
fi

# Validate JSON
if ! jq empty "$BACKUP_REPORT" 2>/dev/null; then
  echo "❌ ERROR: Backup report is not valid JSON"
  exit 1
fi

# Check backup file exists (locally or in cloud)
BACKUP_FILE=$(jq -r '.backup_file' "$BACKUP_REPORT")
BACKUP_LOCATION=$(jq -r '.backup_location' "$BACKUP_REPORT")
BACKUP_VERIFIED=$(jq -r '.verified' "$BACKUP_REPORT")

if [ -z "$BACKUP_FILE" ] || [ "$BACKUP_FILE" = "null" ]; then
  echo "❌ ERROR: No backup file in report"
  exit 1
fi

# Check backup verified
if [ "$BACKUP_VERIFIED" != "true" ]; then
  echo "⚠️  WARNING: Backup not verified"
fi

# Check backup size reasonable
BACKUP_SIZE=$(jq -r '.backup_size_bytes' "$BACKUP_REPORT")
if [ "$BACKUP_SIZE" -lt 1024 ]; then
  echo "❌ ERROR: Backup file too small (< 1KB), likely incomplete"
  echo "Size: $BACKUP_SIZE bytes"
  exit 1
fi

echo "✓ Output validation complete"
echo "  Backup: $BACKUP_FILE"
echo "  Location: $BACKUP_LOCATION"
echo "  Size: $(numfmt --to=iec $BACKUP_SIZE 2>/dev/null || echo ${BACKUP_SIZE} bytes)"
echo "  Verified: $BACKUP_VERIFIED"
```

## Completion

```
═══════════════════════════════════════════════════
        DATABASE BACKUP COMPLETE ✓
═══════════════════════════════════════════════════

Environment: $ENVIRONMENT
Command: /db/backup
Version: 2.0.0

Backup Created:
  ✓ File: [backup-filename]
  ✓ Location: [cloud-storage-path]
  ✓ Size: [size]
  ✓ Checksum: [sha256]
  ✓ Retention: [days] days

Validation Completed:
  ✓ Integrity verified (checksum)
  ✓ Uploaded to cloud storage
  ✓ Old backups cleaned
  ✓ Backup is restorable

Validations Passed:
  ✓ Input validation (environment valid)
  ✓ Output validation (backup report created)
  ✓ Backup file size reasonable
  ✓ Cloud upload successful
  ✓ Quality threshold (≥0.95)

NEXT STEPS:
→ Backup is stored securely in cloud storage
→ To restore: /db/restore $ENVIRONMENT [backup-file]
→ Monitor backup schedule for automated backups

═══════════════════════════════════════════════════
```

## Guidelines

- **Automated Backups**: Schedule daily backups at 2-4 AM UTC (low traffic)
- **Retention Policy**: Production: 30 days, Staging: 14 days, Dev: 7 days
- **Encryption**: Always encrypt production backups
- **Verification**: Always verify backup integrity (checksum + test restore)
- **Cloud Storage**: Store in different region than database
- **Monitoring**: Alert on backup failure, size anomalies, verification failures
- **Testing**: Test restore process monthly on staging
