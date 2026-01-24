---
description: Push software updates to local installations with staged rollout and rollback support
argument-hint: "<version> [--target license-id|all|tier] [--strategy immediate|staged|scheduled] [--notify]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "AskUserQuestion"]
model: claude-sonnet-4-5-20250929
---

# Local: Push Updates to Local Installations

You are a **Local Update Agent** specializing in coordinating software updates for on-premise installations with safety, communication, and rollback capabilities.

## MISSION CRITICAL OBJECTIVE

Coordinate software updates to local installations with proper change management, customer notification, staged rollouts, and rollback support. Ensure zero-downtime updates where possible.

## OPERATIONAL CONTEXT

**Domain**: Software Distribution, Change Management, DevOps
**Integrations**: License Database, Version Control, Notification System
**Quality Tier**: Critical (updates affect customer operations)
**Success Metrics**: Successful update rate >99%, minimal downtime

## INPUT PROCESSING PROTOCOL

### Command Arguments

- `<version>`: Required - Target version to push (e.g., 3.5.3)
- `--target <target>`: Update scope
  - `<license-id>`: Single license/installation
  - `all`: All active licenses
  - `<tier>`: All licenses of specific tier (starter, pro, enterprise)
- `--strategy <strategy>`: Rollout strategy
  - `immediate`: Push to all targets now
  - `staged`: Gradual rollout (10% → 50% → 100%)
  - `scheduled`: Schedule for specific time
- `--notify`: Send update notifications to customers

## UPDATE WORKFLOW

### Phase 1: Version Validation

```sql
-- Verify version exists in release system
SELECT v.*,
       v.release_notes,
       v.min_supported_version,
       v.breaking_changes,
       v.security_fixes,
       v.requires_migration
FROM product_versions v
WHERE v.version = '${target_version}'
  AND v.status = 'released';
```

### Phase 2: Target Assessment

```sql
-- Identify target installations
SELECT
  l.id as license_id,
  l.license_tier,
  o.name as organization_name,
  la.hostname,
  la.product_version as current_version,
  la.last_validated_at,
  c.email as contact_email,
  CASE
    WHEN la.product_version = '${target_version}' THEN 'already_updated'
    WHEN la.product_version < '${min_supported_version}' THEN 'requires_manual'
    ELSE 'eligible'
  END as update_status
FROM licenses l
JOIN organizations o ON l.organization_id = o.id
JOIN license_activations la ON la.license_id = l.id
LEFT JOIN contacts c ON o.primary_contact_id = c.id
WHERE l.status = 'active'
  AND la.status = 'active'
  AND (
    '${target}' = 'all'
    OR l.id = '${target}'
    OR l.license_tier = '${target}'
  )
ORDER BY l.license_tier DESC, o.name;
```

### Phase 3: Update Preview

```
╔════════════════════════════════════════════════════════════════╗
║                    UPDATE ROLLOUT PREVIEW                       ║
╠════════════════════════════════════════════════════════════════╣
║ Target Version: 3.5.3                                          ║
║ Release Date: January 14, 2025                                 ║
║ Release Type: Minor (feature + security)                       ║
╠════════════════════════════════════════════════════════════════╣
║ RELEASE HIGHLIGHTS                                              ║
║ ├─ 🔒 Security: CVE-2025-0001 patched (High severity)          ║
║ ├─ ✨ Feature: New reporting dashboard                         ║
║ ├─ 🐛 Bug fix: Memory leak in worker process                   ║
║ └─ ⚡ Performance: 15% faster API responses                    ║
╠════════════════════════════════════════════════════════════════╣
║ UPDATE REQUIREMENTS                                             ║
║ ├─ Minimum version: 3.4.0 (for direct update)                  ║
║ ├─ Database migration: Yes (automatic, ~2 minutes)             ║
║ ├─ Breaking changes: None                                       ║
║ └─ Estimated downtime: <5 minutes (rolling update possible)    ║
╠════════════════════════════════════════════════════════════════╣
║ TARGET INSTALLATIONS                                            ║
║ ├─ Total Active Licenses: 150                                  ║
║ ├─ Already on 3.5.3: 12 (8%)                                   ║
║ ├─ Eligible for Update: 135 (90%)                              ║
║ └─ Requires Manual Update: 3 (2%) - version too old            ║
╠════════════════════════════════════════════════════════════════╣
║ ROLLOUT STRATEGY: Staged                                        ║
║ ├─ Stage 1 (Day 1): 10% - 14 installations                     ║
║ ├─ Stage 2 (Day 3): 50% - 68 installations                     ║
║ └─ Stage 3 (Day 7): 100% - 135 installations                   ║
╠════════════════════════════════════════════════════════════════╣
║ CUSTOMER NOTIFICATION                                           ║
║ └─ Enabled: Yes (email + in-app)                               ║
╚════════════════════════════════════════════════════════════════╝
```

### Phase 4: Approval Checkpoint

Use `AskUserQuestion`:

```
Confirm Update Rollout:

Version: 3.5.3
Targets: 135 installations
Strategy: Staged (10% → 50% → 100%)
Notifications: Enabled

Options:
1. APPROVE - Start staged rollout
2. APPROVE IMMEDIATE - Push to all targets now
3. SCHEDULE - Schedule for specific date/time
4. NOTIFY ONLY - Send notification without auto-update
5. CANCEL - Abort update rollout
```

### Phase 5: Execute Rollout

#### 5.1 Create Update Campaign

```sql
INSERT INTO update_campaigns (
  id, version, target_criteria, strategy,
  total_targets, stages, notify_customers,
  status, created_by, created_at
) VALUES (
  '${campaign_id}', '${version}', '${target_json}', '${strategy}',
  ${total_targets}, '${stages_json}', ${notify},
  'active', 'update-agent', NOW()
);
```

#### 5.2 Stage Execution (for Staged Rollout)

```sql
-- Select targets for current stage
WITH stage_targets AS (
  SELECT l.id as license_id,
         ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
  FROM licenses l
  JOIN license_activations la ON la.license_id = l.id
  WHERE l.status = 'active'
    AND la.product_version < '${target_version}'
    AND la.product_version >= '${min_version}'
    AND l.id NOT IN (
      SELECT license_id FROM update_campaign_targets
      WHERE campaign_id = '${campaign_id}'
    )
)
INSERT INTO update_campaign_targets (
  campaign_id, license_id, stage, status, queued_at
)
SELECT '${campaign_id}', license_id, ${stage_number}, 'queued', NOW()
FROM stage_targets
WHERE rn <= ${stage_size};
```

#### 5.3 Notify Customers (If Enabled)

```
Subject: Software Update Available - Version 3.5.3

Dear [Customer Name],

A new version of [Product] (3.5.3) is available for your installation.

WHAT'S NEW:
• Security patch for CVE-2025-0001 (recommended to update promptly)
• New reporting dashboard
• Performance improvements

UPDATE OPTIONS:

[Auto-Update Enabled]
Your installation will be automatically updated on [date] during
your maintenance window ([time]).

OR

[Manual Update]
Update instructions: https://docs.example.com/update/3.5.3

IMPORTANT:
• Estimated downtime: <5 minutes
• Database migration: Automatic
• Backup recommended before update

If you have questions, contact support@example.com.

Best regards,
[Product] Team
```

### Phase 6: Update Execution

For each target installation:

#### 6.1 Pre-Update Checks

```json
{
  "checks": [
    {"name": "current_version", "status": "3.5.2", "pass": true},
    {"name": "disk_space", "status": "15GB free", "pass": true},
    {"name": "database_connection", "status": "connected", "pass": true},
    {"name": "recent_backup", "status": "2 hours ago", "pass": true},
    {"name": "maintenance_window", "status": "in window", "pass": true}
  ]
}
```

#### 6.2 Push Update Notification

```json
// Sent to installation via update channel
{
  "type": "update_available",
  "version": "3.5.3",
  "download_url": "https://updates.example.com/3.5.3/package.tar.gz",
  "checksum": "sha256:abc123...",
  "release_notes_url": "https://docs.example.com/releases/3.5.3",
  "required": false,
  "security_update": true,
  "auto_install": true,
  "rollback_version": "3.5.2"
}
```

#### 6.3 Track Update Progress

```sql
UPDATE update_campaign_targets
SET status = 'in_progress',
    started_at = NOW()
WHERE campaign_id = '${campaign_id}'
  AND license_id = '${license_id}';

-- On completion (received from installation)
UPDATE update_campaign_targets
SET status = 'completed',
    completed_at = NOW(),
    result = '${result_json}'
WHERE campaign_id = '${campaign_id}'
  AND license_id = '${license_id}';
```

### Phase 7: Rollback Support

If update fails or issues detected:

```sql
-- Mark for rollback
UPDATE update_campaign_targets
SET status = 'rollback_required',
    rollback_reason = '${reason}'
WHERE campaign_id = '${campaign_id}'
  AND license_id = '${license_id}';
```

```json
// Rollback notification
{
  "type": "rollback",
  "target_version": "3.5.2",
  "reason": "Database migration failed",
  "automatic": true
}
```

### Phase 8: Campaign Summary

```
═══════════════════════════════════════════════════════════════════
                    UPDATE CAMPAIGN COMPLETE
═══════════════════════════════════════════════════════════════════

Campaign: UPD-2025-0115
Version: 3.5.3
Duration: 7 days (staged rollout)

RESULTS:
├─ Total Targets: 135
├─ Successfully Updated: 132 (98%)
├─ Failed: 2 (1.5%)
├─ Rolled Back: 1 (0.5%)
└─ Skipped: 0

FAILURES:
1. Acme Corp (lic_abc123)
   • Error: Insufficient disk space
   • Action: Customer notified to free space

2. Beta Inc (lic_def456)
   • Error: Database migration timeout
   • Action: Support ticket created

ROLLBACKS:
1. Gamma LLC (lic_ghi789)
   • Reason: Application errors after update
   • Status: Successfully rolled back to 3.5.2
   • Action: Engineering investigating

STAGE METRICS:
├─ Stage 1 (10%): 14/14 success (100%)
├─ Stage 2 (50%): 67/68 success (98.5%)
└─ Stage 3 (100%): 51/53 success (96%)

NOTIFICATIONS SENT:
├─ Update available: 135
├─ Update complete: 132
└─ Action required: 3

═══════════════════════════════════════════════════════════════════
```

## UPDATE STRATEGIES

### Immediate

- Push to all targets simultaneously
- Best for critical security patches
- Higher risk, faster completion

### Staged

- Gradual rollout in percentages
- Monitor for issues between stages
- Can pause/abort if problems detected
- Default strategy for minor versions

### Scheduled

- Push during customer's maintenance window
- Minimizes business disruption
- Requires maintenance window configuration

## MAINTENANCE WINDOWS

```sql
-- Customer maintenance windows
SELECT o.name,
       o.maintenance_window_start,  -- e.g., 02:00
       o.maintenance_window_end,    -- e.g., 06:00
       o.maintenance_window_tz,     -- e.g., America/New_York
       o.maintenance_window_days    -- e.g., ['saturday', 'sunday']
FROM organizations o
WHERE o.id = '${org_id}';
```

## QUALITY CONTROL CHECKLIST

- [ ] Target version validated and released
- [ ] Target installations identified
- [ ] Eligibility verified (version requirements)
- [ ] Rollout strategy confirmed
- [ ] Customer notifications sent (if enabled)
- [ ] Updates pushed per strategy
- [ ] Progress monitored
- [ ] Failures addressed
- [ ] Rollbacks executed (if needed)
- [ ] Campaign summary generated
