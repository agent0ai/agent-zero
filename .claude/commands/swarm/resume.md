---
description: Resume swarm operations from a checkpoint
argument-hint: "<swarm-id> [--checkpoint <checkpoint-id>] [--skip-validation]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, AskUserQuestion, Task
---

# Resume Swarm

Resume autonomous swarm operations from a saved checkpoint, restoring full operational state.

## Execution Steps

### 1. Parse Arguments

Extract from `$ARGUMENTS`:

- **swarm-id**: Required - the swarm instance to resume
- **--checkpoint**: Optional - specific checkpoint ID to resume from
- **--skip-validation**: Optional - skip service health validation

### 2. Verify Swarm Exists and is Paused

Check the swarm is in paused state:

```bash
# Get swarm instance status
curl -s -X GET "http://localhost:3001/api/v1/swarm/instances/$SWARM_ID" \
  -H "x-workspace-id: default" | jq .
```

Verify status is "paused".

### 3. Validate Services (unless --skip-validation)

Verify all services are healthy:

```bash
# Check swarm orchestrator health
curl -s -X GET "http://localhost:3001/api/v1/swarm/health" \
  -H "x-workspace-id: default" | jq .

# Check cross-domain intelligence health
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/health" \
  -H "x-workspace-id: default" | jq .

# Check knowledge service health
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/health" \
  -H "x-workspace-id: default" | jq .
```

### 4. Resume Swarm via Orchestrator

Call the orchestrator resume endpoint:

```bash
# Resume swarm from checkpoint
curl -s -X POST "http://localhost:3001/api/v1/swarm/instances/$SWARM_ID/resume" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "checkpointId": "$CHECKPOINT_ID",
    "processQueuedSignals": true
  }' | jq .
```

This will:

- Set swarm status to "running"
- Restore state from checkpoint
- Queue any pending work items

### 5. Restart Learning Loops

Resume the automatic learning loops:

```bash
# Start learning loops
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge/loops/start" \
  -H "x-workspace-id: default" | jq .
```

### 6. Run Initial Pattern Extraction

Extract any patterns from signals during pause period:

```bash
# Run pattern extraction for signals during pause
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge/patterns/extract?timeWindowDays=1" \
  -H "x-workspace-id: default" | jq .
```

### 7. Check for Queued Signals

Get signals that arrived during pause:

```bash
# Get unprocessed signals
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/signals?limit=20&actionTriggered=false" \
  -H "x-workspace-id: default" | jq '.data | length'
```

### 8. Detect Patterns on Queued Signals

Process any queued signals:

```bash
# Run pattern detection on queued signals
curl -s -X POST "http://localhost:3001/api/v1/cross-domain/detect-patterns" \
  -H "x-workspace-id: default" | jq .
```

### 9. Record Resume Event in Knowledge Base

Create a knowledge entry for the resume:

```bash
# Record resume as knowledge entry
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "category": "workflow",
    "subcategory": "checkpoint",
    "tags": ["resume", "checkpoint", "swarm"],
    "title": "Swarm Resume from Checkpoint",
    "content": "Swarm resumed from pause checkpoint. All services operational.",
    "structuredData": {
      "swarmId": "$SWARM_ID",
      "resumedAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "checkpointId": "$CHECKPOINT_ID",
      "checkpointType": "resume"
    },
    "source": {
      "type": "manual",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "confidence": 100
    }
  }' | jq .
```

### 10. Display Resume Confirmation

```
═══════════════════════════════════════════════════════════
                    SWARM RESUMED
═══════════════════════════════════════════════════════════

✅ Swarm Resumed Successfully

Swarm ID:        $SWARM_ID
Resumed At:      2025-01-15T16:45:00Z
From Checkpoint: $CHECKPOINT_ID

─────────────────────────────────────────────────────────────
SERVICES RESTORED
─────────────────────────────────────────────────────────────

Swarm Orchestrator:         🟢 Running
Cross-Domain Intelligence:  🟢 Active
  ✓ Patterns active (6)
Knowledge Service:          🟢 Active
  ✓ Learning loops started

─────────────────────────────────────────────────────────────
OPERATIONS RESUMED
─────────────────────────────────────────────────────────────

✓ Swarm status set to RUNNING
✓ Checkpoint state restored
✓ Learning loops restarted
  • Intervention Feedback (daily)
  • Playbook Analysis (weekly)
  • Pattern Extraction (daily)
✓ Pattern extraction run
✓ Signal processing active

─────────────────────────────────────────────────────────────
QUEUED SIGNALS
─────────────────────────────────────────────────────────────

Signals created during pause: [count]
Patterns detected:           [count]
Work items created:          [count]

─────────────────────────────────────────────────────────────

Current Status: 🟢 RUNNING

Monitor with: /swarm:status
Pause again:  /swarm:pause $SWARM_ID

═══════════════════════════════════════════════════════════
```

## Recovery Scenarios

### Normal Resume

All services healthy, checkpoint valid - standard resume.

### Services Unavailable

```
⚠️  Some services are unavailable:

  ✗ Cross-Domain Intelligence: Connection refused
  ✓ Knowledge Service: Healthy

Waiting for services...
  [Retry in 5 seconds]
```

### Swarm Not Paused

```
⚠️  Swarm is not in paused state

Current Status: RUNNING

The swarm is already running. No action needed.
```

### No Checkpoint Found

```
⚠️  No checkpoint found for swarm

The swarm has no saved checkpoint. Resume will start fresh.

Options:
  1. Continue with fresh state
  2. Cancel and check checkpoint ID
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/swarm/instances/:id` | Verify swarm state |
| `POST /api/v1/swarm/instances/:id/resume` | Resume swarm |
| `GET /api/v1/swarm/health` | Orchestrator health |
| `GET /api/v1/cross-domain/health` | Cross-domain health |
| `GET /api/v1/swarm-knowledge/health` | Knowledge health |
| `POST /api/v1/swarm-knowledge/loops/start` | Start learning loops |
| `POST /api/v1/swarm-knowledge/patterns/extract` | Run pattern extraction |
| `GET /api/v1/cross-domain/signals` | Get queued signals |
| `POST /api/v1/cross-domain/detect-patterns` | Process queued signals |
| `POST /api/v1/swarm-knowledge` | Record resume event |

## Error Handling

| Error | Resolution |
|-------|------------|
| Swarm not found | Check swarm ID is correct |
| Swarm not paused | Swarm is already running |
| Checkpoint not found | Use latest or specify valid checkpoint |
| Services unavailable | Wait for services or restart backend |
| Learning loops won't start | Check service health |

---

**Uses**: SwarmOrchestrator, CrossDomainIntelligence, SwarmKnowledgeService
**Model**: Sonnet (resume orchestration)
