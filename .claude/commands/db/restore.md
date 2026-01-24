---
description: Restore database from backup with verification and safety checks
argument-hint: <environment> <backup-file> [--verify-only]
allowed-tools: Task, Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1800
retry: 1
cost_estimate: 0.15-0.25

validation:
  input:
    environment:
      required: true
      allowed_values: ["production", "staging", "development", "dev", "prod"]
      error_message: "Environment must be one of: production, staging, development"
    backup_file:
      required: true
      file_pattern: "backup_.*\\.(sql|dump|tar\\.gz)(\\.gz)?$"
      error_message: "Backup file must match pattern: backup_*.{sql,dump,tar.gz}"
  output:
    schema: .claude/validation/schemas/db/restore-output.json
    required_files:
      - 'restores/${environment}_restore_report.json'
    min_file_size: 200
    quality_threshold: 0.95
    content_requirements:
      - "Restore status (success/failed/verify-only)"
      - "Safety backup created before restore"
      - "Backup integrity verified"
      - "Approval obtained (if production)"
      - "Database connectivity verified"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for environment and backup file"
      - "Added output validation for restore reports"
      - "Streamlined from 531 lines to focused workflow"
      - "Enhanced safety checks and approval workflows"
  - version: 1.0.0
    date: 2025-09-10
    changes:
      - "Initial implementation with safety checks"
---

# Database Restore

Environment: **$ARGUMENTS**

## Step 1: Validate Input

```bash
ARGS="$ARGUMENTS"
ENVIRONMENT=$(echo "$ARGS" | awk '{print $1}')
BACKUP_FILE=$(echo "$ARGS" | awk '{print $2}')
VERIFY_ONLY=$(echo "$ARGS" | grep -q '\-\-verify-only' && echo "true" || echo "false")

# Check environment provided
if [ -z "$ENVIRONMENT" ]; then
  echo "❌ ERROR: Missing environment"
  echo ""
  echo "Usage: /db/restore <environment> <backup-file> [--verify-only]"
  echo "Example: /db/restore staging backup_mydb_20240115.sql.gz"
  echo "Example: /db/restore production backup_mydb_20240115.sql.gz --verify-only"
  exit 1
fi

# Check backup file provided
if [ -z "$BACKUP_FILE" ]; then
  echo "❌ ERROR: Missing backup file"
  echo ""
  echo "Usage: /db/restore <environment> <backup-file> [--verify-only]"
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

# Validate backup file pattern
if ! echo "$BACKUP_FILE" | grep -qE "backup_.*\.(sql|dump|tar\.gz)(\.gz)?$"; then
  echo "❌ ERROR: Invalid backup file format"
  echo "Expected pattern: backup_*.{sql,dump,tar.gz}"
  echo "Provided: $BACKUP_FILE"
  exit 1
fi

echo "✓ Input validated: $ENVIRONMENT, $BACKUP_FILE"
echo "  Verify-only mode: $VERIFY_ONLY"
```

## Step 2: Execute Restore Using Agent

```javascript
const ENVIRONMENT = process.env.ENVIRONMENT;
const BACKUP_FILE = process.env.BACKUP_FILE;
const VERIFY_ONLY = process.env.VERIFY_ONLY === 'true';

await Task({
  subagent_type: 'general-purpose',
  description: `${VERIFY_ONLY ? 'Verify' : 'Restore'} database from backup`,
  prompt: `Execute ${VERIFY_ONLY ? 'verification of' : 'restore from'} database backup for ${ENVIRONMENT} environment.

RESTORE REQUIREMENTS:
- Environment: ${ENVIRONMENT}
- Backup File: ${BACKUP_FILE}
- Mode: ${VERIFY_ONLY ? 'VERIFY ONLY (no actual restore)' : 'FULL RESTORE (destructive)'}

⚠️ CRITICAL SAFETY WARNING ⚠️
Database restore is a DESTRUCTIVE operation that will:
- Delete all current data in the database
- Replace with data from backup
- Cannot be easily undone

${ENVIRONMENT === 'production' ? `
🚨 PRODUCTION RESTORE - EXTREME CAUTION 🚨
This is a PRODUCTION database restore.
- Team lead approval MANDATORY
- Stakeholder notification REQUIRED
- Maintenance window scheduled
- Rollback plan documented
- Never restore production without explicit approval
` : ''}

RESTORE WORKFLOW:

**1. Pre-Restore Validation**:
- Download backup file from cloud storage (if gs:// or s3:// path)
- Verify backup file exists and is accessible
- Check backup integrity (SHA256 checksum if available)
- Validate backup structure (pg_restore --list / mysqldump check)
- Verify backup is compatible with database version
- Estimate restore time and check disk space
- Display backup metadata (timestamp, size, source environment)

**2. Safety Approval** (${ENVIRONMENT === 'production' ? 'MANDATORY' : 'REQUIRED'}):
${VERIFY_ONLY ? `
- VERIFY-ONLY MODE: Skip approval (read-only operation)
- Test backup integrity
- Report any issues
- DO NOT actually restore database
` : `
- Use AskUserQuestion to request approval
- Display what will be restored:
  * Environment: ${ENVIRONMENT}
  * Backup File: ${BACKUP_FILE}
  * Backup Date: [from filename/metadata]
  * Current data will be LOST
- For production: Require typing "RESTORE PRODUCTION" to confirm
- For staging/dev: Require "yes" confirmation
- Log approval decision with timestamp
`}

**3. Pre-Restore Safety Backup**:
${VERIFY_ONLY ? '- Skip (verify-only mode)' : `
- Create safety backup of current database state
- Tag as "before-restore-\${TIMESTAMP}"
- Upload to cloud storage
- Verify safety backup completed successfully
- Log safety backup location (for emergency rollback)
`}

**4. Execute Restore**:
${VERIFY_ONLY ? `
**VERIFY-ONLY MODE**:
- Test backup file integrity (checksum)
- Validate backup structure (list tables/objects)
- Check for corruption
- Verify backup is restorable
- Report validation results
- DO NOT actually modify database
` : `
**FULL RESTORE MODE**:
- Terminate active database connections
- Drop existing database (if --clean) or truncate tables
- Restore from backup file:
  * PostgreSQL: pg_restore --clean --if-exists --no-owner --no-acl
  * MySQL: gunzip < backup | mysql
  * MongoDB: mongorestore --drop --gzip
- Use parallel restore if supported (--jobs=4)
- Monitor restore progress
- Log restore operations
`}

**5. Post-Restore Verification**:
${VERIFY_ONLY ? '- Skip (verify-only mode)' : `
- Check database connectivity
- Verify critical tables exist
- Compare record counts with backup metadata
- Run database health checks
- Test application connectivity
- Verify indexes rebuilt successfully
- Check sequences/auto-increment values updated
`}

**6. Generate Restore Report**:
Save restore report to: restores/${ENVIRONMENT}_restore_report.json
{
  "environment": "${ENVIRONMENT}",
  "backup_file": "${BACKUP_FILE}",
  "restore_status": "${VERIFY_ONLY ? 'verify-only' : 'success|failed'}",
  "restore_mode": "${VERIFY_ONLY ? 'verify-only' : 'full|partial|table-level'}",
  "safety_backup_created": ${VERIFY_ONLY ? 'false' : 'true'},
  "backup_integrity_verified": true,
  "approval_obtained": ${VERIFY_ONLY ? 'false' : 'true'},
  "tables_restored": 0,
  "records_restored": 0,
  "restore_duration_seconds": 0,
  "safety_backup_location": "gs://path or s3://path",
  "restored_at": "ISO timestamp",
  "verified": true
}

**Database Type Detection**:
- Auto-detect from backup file extension or database config
- PostgreSQL: .dump → pg_restore
- MySQL: .sql.gz → gunzip | mysql
- MongoDB: .tar.gz → extract + mongorestore

**Error Handling**:
- If backup verification fails: Stop immediately, report error
- If approval denied: Cancel restore, exit cleanly
- If safety backup fails: Abort restore (too risky without safety net)
- If restore fails: Attempt rollback from safety backup
- If verification fails: Mark as failed, provide detailed error

Provide:
- Restore status (success/failed/verify-only)
- Tables restored (if applicable)
- Records restored (if applicable)
- Any errors or warnings`,

  context: {
    environment: ENVIRONMENT,
    backup_file: BACKUP_FILE,
    verify_only: VERIFY_ONLY,
    restore_report_output: `restores/${ENVIRONMENT}_restore_report.json`
  }
});
```

## Step 3: Validate Output

```bash
ENVIRONMENT="$ENVIRONMENT"
RESTORE_REPORT="restores/${ENVIRONMENT}_restore_report.json"

# Check restore report created
if [ ! -f "$RESTORE_REPORT" ]; then
  echo "❌ ERROR: Restore report not created"
  exit 1
fi

# Validate JSON
if ! jq empty "$RESTORE_REPORT" 2>/dev/null; then
  echo "❌ ERROR: Restore report is not valid JSON"
  exit 1
fi

# Check restore status
RESTORE_STATUS=$(jq -r '.restore_status' "$RESTORE_REPORT")
BACKUP_VERIFIED=$(jq -r '.backup_integrity_verified' "$RESTORE_REPORT")
SAFETY_BACKUP=$(jq -r '.safety_backup_created' "$RESTORE_REPORT")

if [ -z "$RESTORE_STATUS" ] || [ "$RESTORE_STATUS" = "null" ]; then
  echo "❌ ERROR: No restore status in report"
  exit 1
fi

# Check backup was verified
if [ "$BACKUP_VERIFIED" != "true" ]; then
  echo "❌ ERROR: Backup integrity not verified"
  exit 1
fi

# For full restores, check safety backup was created
if [ "$RESTORE_STATUS" != "verify-only" ] && [ "$SAFETY_BACKUP" != "true" ]; then
  echo "⚠️  WARNING: Safety backup not created (risky)"
fi

# Check restore succeeded (if not verify-only)
if [ "$RESTORE_STATUS" = "failed" ]; then
  echo "❌ ERROR: Restore failed"
  echo "Check restore report for details: $RESTORE_REPORT"
  exit 1
fi

echo "✓ Output validation complete"
echo "  Status: $RESTORE_STATUS"
echo "  Backup verified: $BACKUP_VERIFIED"
echo "  Safety backup: $SAFETY_BACKUP"
```

## Completion

```
═══════════════════════════════════════════════════
        DATABASE RESTORE COMPLETE ✓
═══════════════════════════════════════════════════

Environment: $ENVIRONMENT
Command: /db/restore
Version: 2.0.0

Restore Status: [status]
  ${VERIFY_ONLY ? '✓ Verification only (no restore performed)' : '✓ Full restore completed'}
  ✓ Backup integrity verified
  ${VERIFY_ONLY ? '' : '✓ Safety backup created'}
  ${VERIFY_ONLY ? '' : '✓ Approval obtained'}
  ✓ Database connectivity verified

Tables Restored: [count]
Records Restored: [count]
Duration: [seconds]

Validations Passed:
  ✓ Input validation (environment + backup file)
  ✓ Output validation (restore report created)
  ✓ Backup integrity verified
  ✓ Restore status confirmed
  ✓ Quality threshold (≥0.95)

${VERIFY_ONLY ?
'VERIFICATION RESULTS:
→ Backup is valid and restorable
→ No issues found
→ Safe to proceed with actual restore if needed' :
'NEXT STEPS:
→ Verify application functionality
→ Test critical workflows
→ Monitor for any issues
→ Safety backup available for emergency rollback'}

═══════════════════════════════════════════════════
```

## Guidelines

- **Always Verify First**: Use --verify-only before production restores
- **Safety Backup**: Always create safety backup before restore
- **Approval Required**: Production restores require explicit approval
- **Test on Staging**: Test production backups on staging first
- **Monitor After Restore**: Watch for application errors after restore
- **Rollback Plan**: Keep safety backup until restore confirmed successful
- **Communication**: Notify team before/during/after production restores
