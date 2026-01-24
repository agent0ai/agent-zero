---
description: Gracefully pause swarm operations with state checkpoint
argument-hint: "<swarm-id> [--reason <reason>]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, AskUserQuestion, Task
---

# Pause Swarm

Gracefully pause autonomous swarm operations, creating a checkpoint for later resumption.

## Execution Steps

### 1. Parse Arguments

Extract from `$ARGUMENTS`:

- **swarm-id**: Required - the swarm instance to pause
- **--reason**: Optional - reason for pausing (maintenance, debugging, etc.)

### 2. Verify Swarm Exists and is Running

Check the swarm is active:

```bash
# Get swarm instance status
curl -s -X GET "http://localhost:3001/api/v1/swarm/instances/$SWARM_ID" \
  -H "x-workspace-id: default" | jq .
```

Verify status is "running" or "active".

### 3. Get Current State Before Pause

Capture metrics before pausing:

```bash
# Get current signal stats
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/stats?timeWindowDays=1" \
  -H "x-workspace-id: default" | jq .

# Get current learning metrics
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/metrics?periodDays=1" \
  -H "x-workspace-id: default" | jq .

# Get pending work items
curl -s -X GET "http://localhost:3001/api/v1/swarm/instances/$SWARM_ID/work-items?status=pending" \
  -H "x-workspace-id: default" | jq .
```

### 4. Stop Learning Loops

Stop the automatic learning loops:

```bash
# Stop learning loops
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge/loops/stop" \
  -H "x-workspace-id: default" | jq .
```

### 5. Run Final Pattern Extraction

Extract patterns before pausing:

```bash
# Run final pattern extraction
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge/patterns/extract?timeWindowDays=1" \
  -H "x-workspace-id: default" | jq .
```

### 6. Pause Swarm via Orchestrator

Call the orchestrator pause endpoint:

```bash
# Pause swarm with checkpoint
curl -s -X POST "http://localhost:3001/api/v1/swarm/instances/$SWARM_ID/pause" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "reason": "$REASON",
    "createCheckpoint": true
  }' | jq .
```

This will:

- Set swarm status to "paused"
- Create a checkpoint with current state
- Return the checkpoint ID

### 7. Record Pause Event in Knowledge Base

Create a knowledge entry for the pause:

```bash
# Record pause as knowledge entry
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "category": "workflow",
    "subcategory": "checkpoint",
    "tags": ["pause", "checkpoint", "swarm"],
    "title": "Swarm Pause Checkpoint",
    "content": "Swarm paused for: $REASON. Checkpoint created for resumption.",
    "structuredData": {
      "swarmId": "$SWARM_ID",
      "pausedAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "reason": "$REASON",
      "checkpointType": "pause"
    },
    "source": {
      "type": "manual",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "confidence": 100
    }
  }' | jq .
```

### 8. Display Pause Confirmation

```
═══════════════════════════════════════════════════════════
                    SWARM PAUSED
═══════════════════════════════════════════════════════════

✅ Swarm Paused Successfully

Swarm ID:       $SWARM_ID
Paused At:      2025-01-15T14:30:00Z
Reason:         $REASON

─────────────────────────────────────────────────────────────
OPERATIONS STOPPED
─────────────────────────────────────────────────────────────

✓ Learning loops stopped
✓ Final pattern extraction completed
✓ Checkpoint created
✓ Swarm status set to PAUSED

─────────────────────────────────────────────────────────────
STATE AT PAUSE
─────────────────────────────────────────────────────────────

Work Items:
  ├── Completed:    [count]
  ├── In Progress:  [count]
  └── Pending:      [count]

Signals Processed Today: [count]
Decisions Made Today:    [count]

─────────────────────────────────────────────────────────────
CHECKPOINT INFO
─────────────────────────────────────────────────────────────

Checkpoint ID:   [checkpoint_id]
Checkpoint Time: 2025-01-15T14:30:00Z

─────────────────────────────────────────────────────────────
RESUME INFORMATION
─────────────────────────────────────────────────────────────

To resume operations:
  /swarm:resume $SWARM_ID

The swarm will:
  • Restart learning loops
  • Resume signal processing
  • Continue from checkpoint

⚠️  NOTE: Signals created during pause will be queued
     and processed on resume.

═══════════════════════════════════════════════════════════
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/swarm/instances/:id` | Verify swarm exists |
| `GET /api/v1/swarm/instances/:id/work-items` | Get pending work |
| `POST /api/v1/swarm/instances/:id/pause` | Pause swarm |
| `POST /api/v1/swarm-knowledge/loops/stop` | Stop learning loops |
| `POST /api/v1/swarm-knowledge/patterns/extract` | Final extraction |
| `POST /api/v1/swarm-knowledge` | Record pause event |

## Error Handling

| Error | Resolution |
|-------|------------|
| Swarm not found | Check swarm ID is correct |
| Swarm already paused | Already in paused state |
| Checkpoint creation failed | Check disk space and permissions |
| Learning loops won't stop | Force stop with retry |

---

**Uses**: SwarmOrchestrator, SwarmKnowledgeService
**Model**: Sonnet (pause orchestration)
