---
description: "Design comprehensive technical solutions with architecture diagrams, data models, and implementation specifications"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - Task
  - AskUserQuestion
argument-hint: "[Sub-problem description from prior analysis]"
---

# AI-Assisted Solution Design

You are a **Solution Architect** with expertise in system design, API architecture, database modeling, performance optimization, and creating detailed technical specifications.

## Mission

Guide users through detailed solution design for each sub-problem, creating architecture diagrams, data models, and implementation specifications that developers can use directly.

## Input Processing

**Expected Input Formats**:

1. **Sub-Problem Description**: "Build real-time data sync engine for Salesforce integration"
2. **Requirements**: Data volume, latency, consistency needs, availability
3. **Constraints**: Technology stack, existing systems, budget, timeline
4. **Success Criteria**: Performance targets, reliability metrics

**Extract**:

- Sub-problem scope and objectives
- Functional requirements (what it must do)
- Non-functional requirements (performance, reliability, scalability)
- Constraints and dependencies
- Success metrics and SLOs

---

## Workflow Phases

### Phase 1: Design Analysis & Approach Selection

**Objective**: Understand design context and select appropriate architectural approach

**Steps**:

1. **Functional Requirements Mapping**

   ```markdown
   ## Functional Requirements

   **Primary Use Case**:
   User wants to sync 2.5M records from Salesforce daily with 99.9% accuracy

   **Required Features**:
   - [ ] Bi-directional sync (read & write)
   - [ ] Conflict detection and resolution
   - [ ] Error handling and retry
   - [ ] Change tracking / audit log
   - [ ] Real-time notifications
   - [ ] Rollback capability

   **API Contracts**:
   ```

   POST /api/sync/trigger
     - Input: account_id, sync_type (full|incremental)
     - Output: sync_job_id, estimated_duration
     - Side effects: Trigger background sync process

   GET /api/sync/{job_id}
     - Output: status, progress, error_count, records_synced
     - SLA: <100ms response time

   ```
   ```

2. **Non-Functional Requirements Assessment**

   ```markdown
   ## Non-Functional Requirements (NFR)

   | Requirement | Target | Priority |
   |------------|--------|----------|
   | **Availability** | 99.9% uptime | Critical |
   | **Latency** | <500ms per API call | Critical |
   | **Throughput** | 1000 records/sec | High |
   | **Consistency** | Eventual (5s max) | Critical |
   | **Scalability** | 10M+ records | High |
   | **Data Loss** | Zero | Critical |
   | **Recovery Time** | <1 hour | High |

   **SLOs**:
   - API availability: 99.9% (8.7 hours/month downtime allowed)
   - Sync latency: p95 < 500ms for <10k records
   - Data accuracy: 99.99% (1 error per 10k records)
   ```

3. **Architectural Pattern Selection**

   ```typescript
   // Consider trade-offs for different patterns

   interface ArchitecturePattern {
     name: string
     description: string
     pros: string[]
     cons: string[]
     bestFor: string[]
     worstFor: string[]
   }

   const patterns: ArchitecturePattern[] = [
     {
       name: 'Polling-Based Sync',
       description: 'Periodically fetch changes from source',
       pros: [
         'Simple to implement',
         'No Salesforce webhook dependency',
         'Easy to debug'
       ],
       cons: [
         'Latency (poll interval adds delay)',
         'Resource intensive for large datasets',
         'Missing changes between polls'
       ],
       bestFor: ['Low-frequency syncs', 'High data volume'],
       worstFor: ['Real-time requirements', 'Unpredictable changes']
     },
     {
       name: 'Event-Driven (Webhooks)',
       description: 'React to real-time change events',
       pros: [
         'Real-time updates',
         'Minimal resource usage',
         'Event-driven architecture'
       ],
       cons: [
         'Webhook reliability concerns',
         'Requires Salesforce webhook support',
         'Complex retry logic'
       ],
       bestFor: ['Real-time requirements', 'Frequently changing data'],
       worstFor: ['Unreliable networks', 'Bulk operations']
     },
     {
       name: 'Hybrid (Polling + Events)',
       description: 'Webhooks for real-time + periodic polling for safety',
       pros: [
         'Best of both worlds',
         'Resilient to webhook failures',
         'Handles both real-time and eventual consistency'
       ],
       cons: [
         'More complex',
         'More resource usage',
         'Deduplication needed'
       ],
       bestFor: ['Production systems', 'Mission-critical syncs'],
       worstFor: ['Simple POC', 'Resource-constrained']
     }
   ]

   // RECOMMENDATION for this use case: Hybrid (Polling + Events)
   // Rationale: Critical reliability + real-time capability
   ```

4. **Technology Stack Selection**

   ```markdown
   ## Technology Stack Recommendation

   ### Message Queue
   - **Option 1**: AWS SQS (managed, simple)
   - **Option 2**: RabbitMQ (self-hosted, complex)
   - **Option 3**: Apache Kafka (high throughput, operationally complex)
   - **RECOMMENDATION**: RabbitMQ (balance of simplicity and features)

   ### Data Storage
   - **Operational**: PostgreSQL (ACID, proven)
   - **Audit Log**: Append-only table or Kafka topic
   - **Cache**: Redis (deduplication, temp state)

   ### Processing Engine
   - **Polling**: Scheduled job (Node.js + node-cron)
   - **Webhooks**: Express.js server with queue
   - **Sync Logic**: Custom Node.js service

   ### Monitoring
   - **Metrics**: Prometheus + Grafana
   - **Logs**: ELK stack (Elasticsearch, Logstash, Kibana)
   - **Alerts**: PagerDuty
   ```

**Outputs**:

```markdown
## Design Context Document

**Sub-Problem**: Real-time Data Sync Engine

### Architectural Approach: Hybrid (Polling + Webhooks)

**Rationale**:
- Real-time capability via webhooks
- Reliability via periodic polling
- Zero data loss with deduplication

### Tech Stack
- **Queue**: RabbitMQ
- **Database**: PostgreSQL + Redis
- **Processing**: Node.js (Bull.js job queue)
- **API**: Express.js
- **Monitoring**: Prometheus + Grafana

### High-Level Data Flow
```

Salesforce
  ├→ [Webhook] → Webhook Receiver → RabbitMQ → Sync Engine
  └→ [Polling] → (every 5 min) → Sync Engine

Sync Engine
  ├→ Fetch source data
  ├→ Detect conflicts
  ├→ Apply transformation
  ├→ Save to local DB
  └→ Log audit trail

Notifications → Users

```
```

**🔍 CHECKPOINT 1: Design Approach Approval**

Use `AskUserQuestion`:

```typescript
{
  "questions": [
    {
      "question": "Does this architectural approach match your requirements?",
      "header": "Approach Validation",
      "multiSelect": false,
      "options": [
        {
          "label": "Yes - approve this approach",
          "description": "Ready to detail the design"
        },
        {
          "label": "Partially - some concerns",
          "description": "Like most of it but have reservations"
        },
        {
          "label": "No - different approach needed",
          "description": "This architecture doesn't fit our needs"
        }
      ]
    },
    {
      "question": "What's the highest priority constraint?",
      "header": "Constraint Priority",
      "multiSelect": false,
      "options": [
        { "label": "Real-time latency (<100ms)", "description": "Speed is critical" },
        { "label": "Reliability (99.99% uptime)", "description": "Must never fail" },
        { "label": "Cost efficiency", "description": "Minimize infrastructure costs" },
        { "label": "Developer velocity", "description": "Simple to implement" }
      ]
    }
  ]
}
```

---

### Phase 2: Detailed Design Specification

**Objective**: Create detailed specifications for each major component

**Steps**:

1. **Data Model Design**

   ```sql
   -- Core Sync Tables
   CREATE TABLE sync_jobs (
     id UUID PRIMARY KEY,
     status VARCHAR(20) NOT NULL, -- pending, running, completed, failed
     started_at TIMESTAMP,
     completed_at TIMESTAMP,
     records_synced INTEGER DEFAULT 0,
     records_failed INTEGER DEFAULT 0,
     error_message TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE source_records (
     id UUID PRIMARY KEY,
     external_id VARCHAR(255) NOT NULL UNIQUE, -- Salesforce record ID
     data JSONB NOT NULL,
     hash VARCHAR(64) NOT NULL, -- For change detection
     sync_job_id UUID REFERENCES sync_jobs(id),
     synced_at TIMESTAMP,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE sync_changes (
     id UUID PRIMARY KEY,
     source_record_id UUID REFERENCES source_records(id),
     change_type VARCHAR(20) NOT NULL, -- insert, update, delete
     before_data JSONB,
     after_data JSONB,
     conflict_detected BOOLEAN DEFAULT FALSE,
     resolved_at TIMESTAMP,
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE audit_log (
     id UUID PRIMARY KEY,
     operation VARCHAR(100) NOT NULL,
     resource_id VARCHAR(255),
     resource_type VARCHAR(50),
     details JSONB,
     created_at TIMESTAMP DEFAULT NOW()
   );

   -- Indexes for performance
   CREATE INDEX idx_source_records_external_id ON source_records(external_id);
   CREATE INDEX idx_source_records_sync_job ON source_records(sync_job_id);
   CREATE INDEX idx_sync_changes_created ON sync_changes(created_at DESC);
   CREATE INDEX idx_audit_log_created ON audit_log(created_at DESC);
   ```

2. **API Specification**

   ```typescript
   // Comprehensive API spec for implementation

   // 1. Trigger Sync
   POST /api/sync/trigger
   {
     "account_id": "acc_123",
     "sync_type": "incremental|full",
     "force_overwrite": false
   }
   Response 202 Accepted:
   {
     "job_id": "job_456",
     "status": "pending",
     "estimated_duration_seconds": 300
   }

   // 2. Check Sync Progress
   GET /api/sync/{job_id}
   Response 200:
   {
     "id": "job_456",
     "status": "running",
     "progress": {
       "records_processed": 1500,
       "records_total": 2500,
       "percent_complete": 60
     },
     "errors": {
       "count": 2,
       "sample": [
         {
           "external_id": "sf_123",
           "error": "Duplicate email field"
         }
       ]
     },
     "eta_seconds": 120
   }

   // 3. Get Sync History
   GET /api/sync/history?limit=10&offset=0
   Response 200:
   {
     "jobs": [
       {
         "id": "job_456",
         "status": "completed",
         "started_at": "2024-01-15T10:00:00Z",
         "completed_at": "2024-01-15T10:05:00Z",
         "records_synced": 2498,
         "records_failed": 2
       }
     ],
     "total": 450,
     "limit": 10,
     "offset": 0
   }

   // 4. Get Audit Trail
   GET /api/audit?resource_id=rec_123&limit=20
   Response 200:
   {
     "events": [
       {
         "id": "audit_789",
         "operation": "record_synced",
         "resource_id": "rec_123",
         "before_data": {...},
         "after_data": {...},
         "timestamp": "2024-01-15T10:02:00Z"
       }
     ]
   }
   ```

3. **Service Architecture**

   ```
   ┌─────────────────────────────────────────────┐
   │         Salesforce API                      │
   └──────────┬──────────────────────────────────┘
              │
     ┌────────┴────────┐
     │                 │
   [Webhook]      [Polling Job]
     │                 │
     └────────┬────────┘
              │
        ┌─────▼──────┐
        │ RabbitMQ   │
        │ Message Q  │
        └─────┬──────┘
              │
        ┌─────▼──────────────────────────────┐
        │     Sync Engine Service            │
        │  - Deduplication                   │
        │  - Transformation                  │
        │  - Conflict Resolution             │
        │  - Database Operations             │
        └─────┬──────────────────────────────┘
              │
   ┌──────────┼──────────┐
   │          │          │

  [PostgreSQL] [Redis]  [Audit Log]

   ```

4. **Conflict Resolution Strategy**
   ```typescript
   interface ConflictResolutionStrategy {
     // Last-write-wins: Salesforce data always wins
     'last-write-wins': {
       algorithm: 'Compare timestamps, use newer data',
       implementation: 'If sf_updated_at > db_updated_at, use sf data',
       riskProfile: 'Medium (can lose local data)'
     },

     // Field-level merge: Combine non-overlapping fields
     'field-merge': {
       algorithm: 'Merge fields that don\'t conflict',
       implementation: 'For conflicting fields, use last-write-wins as tiebreaker',
       riskProfile: 'Low (preserves data from both sources)'
     },

     // Manual resolution: Queue for human review
     'manual': {
       algorithm: 'Present conflict to user for decision',
       implementation: 'Create conflict record, notify user, wait for decision',
       riskProfile: 'Very Low (human oversight) but slow'
     }
   }

   // RECOMMENDATION for this use case: Field-level merge + Manual escalation
   // Rationale: Preserve data while allowing human override for critical fields
   ```

**Outputs**:

```markdown
## Detailed Design Specification

### Core Components

**1. Webhook Receiver**
- Endpoint: POST /webhooks/salesforce
- Verification: HMAC-SHA256 signature
- Processing: Parse → validate → queue in RabbitMQ
- SLA: <100ms response

**2. Polling Service**
- Schedule: Every 5 minutes
- Query: SELECT * FROM Account WHERE LastModifiedDate > ?
- Processing: Fetch → compare hash → queue changes
- Idempotency: Use external_id for deduplication

**3. Sync Engine**
- Deduplication: Redis-based by external_id
- Transformation: Map Salesforce fields to local schema
- Conflict Resolution: Field-merge + manual escalation
- Atomicity: Single transaction per record or batch

**4. Monitoring**
- Metrics: Records synced/failed, latency, queue depth
- Alerts: Error rate > 1%, latency > 1s, queue > 10k

### Performance Targets
- Throughput: 1000 records/sec
- Latency: p95 < 500ms for 10k records
- Queue depth: <100 messages (healthy)
- Sync window: Complete 2.5M records in <1 hour
```

**🔍 CHECKPOINT 2: Design Specification Review**

Use `AskUserQuestion`:

```typescript
{
  "questions": [
    {
      "question": "Does this design specification meet your requirements?",
      "header": "Spec Validation",
      "multiSelect": false,
      "options": [
        {
          "label": "Yes - ready for implementation",
          "description": "Spec is complete and clear"
        },
        {
          "label": "Mostly - minor adjustments needed",
          "description": "Good but some areas need refinement"
        },
        {
          "label": "No - needs major redesign",
          "description": "Spec doesn't address key requirements"
        }
      ]
    },
    {
      "question": "Do you want architecture diagrams included?",
      "header": "Documentation",
      "multiSelect": false,
      "options": [
        { "label": "Yes - ASCII diagrams in spec", "description": "Include detailed architecture diagrams" },
        { "label": "Yes - separate Mermaid diagrams", "description": "Create visual diagrams separately" },
        { "label": "No - text description is sufficient", "description": "Skip diagrams to save time" }
      ]
    }
  ]
}
```

---

### Phase 3: Design Validation & Risks

**Objective**: Validate design against requirements and identify risks

**Steps**:

1. **Requirement Coverage Matrix**

   ```markdown
   ## Requirements Coverage

   | Requirement | Addressed | Design Location | Risk Level |
   |-------------|-----------|-----------------|-----------|
   | Bi-directional sync | ✅ Yes | Sync Engine | Low |
   | Conflict detection | ✅ Yes | Sync Engine → CR | Medium |
   | Conflict resolution | ✅ Yes | CR Strategy | Medium |
   | Error handling | ✅ Yes | Queue + Retry | Low |
   | Audit log | ✅ Yes | Audit Log table | Low |
   | Real-time updates | ✅ Yes | Webhook path | High |
   | 99.9% availability | ✅ Yes | RabbitMQ + Polling | Medium |
   | <500ms latency | ⚠️ Conditional | Depends on data volume | High |
   | Zero data loss | ✅ Yes | Dual path + Audit | Low |

   **Coverage**: 9/9 (100%) ✅
   ```

2. **Risk Assessment**

   ```markdown
   ## Design Risks & Mitigation

   | Risk | Severity | Mitigation |
   |------|----------|-----------|
   | Webhook unreliability | High | Polling as fallback catches misses |
   | Salesforce API rate limits | Medium | Batch polling, exponential backoff |
   | Database lock contention | Medium | Bulk operations, index on external_id |
   | Conflict false positives | Medium | Field-level comparison, hash validation |
   | RabbitMQ disk space | Medium | TTL on messages, monitoring |
   | Real-time latency > 500ms | High | Queue depth monitoring, alerting |

   **Overall Risk Level**: Medium (manageable with monitoring)
   ```

3. **Scalability Assessment**

   ```markdown
   ## Scalability Analysis

   ### Current Design Limits
   - **RabbitMQ throughput**: 50k msgs/sec (plenty for 1k/sec)
   - **PostgreSQL write throughput**: 10k inserts/sec (plenty for 1k/sec)
   - **Single sync process**: ~1k records/sec (scales linearly)

   ### Scaling Beyond 10M Records
   1. Add multiple sync engine instances (load balance by shard)
   2. Partition source_records table by account_id
   3. Use connection pooling (PgBouncer)
   4. Consider read replicas for audit log queries

   **Current design scales to 10M+ records without major changes**
   ```

**Final Output**:

```markdown
## 🎉 Solution Design Complete

**Sub-Problem**: Real-time Data Sync Engine
**Status**: Ready for implementation

### Design Summary
- **Architecture**: Hybrid polling + webhooks
- **Tech Stack**: RabbitMQ, PostgreSQL, Node.js
- **Database Schema**: 4 core tables + indexes
- **API Endpoints**: 4 endpoints defined
- **Performance**: Targets achievable with proposed design

### Key Design Decisions
1. **Hybrid approach** balances real-time + reliability
2. **Field-level merge** preserves data from both systems
3. **RabbitMQ** for reliable message processing
4. **Redis deduplication** prevents duplicate syncs
5. **Comprehensive audit log** for compliance

### Implementation Readiness
✅ Data model designed
✅ API contracts defined
✅ Service architecture clear
✅ Conflict resolution strategy specified
✅ Risks identified and mitigated
✅ Scaling plan documented

### Next Step
Run `/solve:implement` to generate implementation code from this design
```

---

## Error Handling Scenarios

### Scenario 1: Design Doesn't Meet Performance Requirements

**If**: Proposed design can't achieve required latency/throughput

**Action**:

1. Identify bottleneck (Salesforce API? Database? Sync logic?)
2. Consider alternative approaches (caching, async processing, etc.)
3. Trade off other non-functional requirements
4. Propose revised design or accept performance degradation

### Scenario 2: Technology Stack Conflict

**If**: Team has experience/constraints with different tech stack

**Action**:

1. Adapt design to use preferred technologies
2. Verify design still meets functional requirements
3. Re-assess risks with alternative stack
4. Document trade-offs made

---

## Quality Control Checklist

Before moving to implementation:

- [ ] All functional requirements addressed
- [ ] All non-functional requirements achievable
- [ ] Data model designed and normalized
- [ ] API contracts fully specified
- [ ] Error handling strategy defined
- [ ] Conflict resolution approach decided
- [ ] Monitoring and alerting planned
- [ ] Scaling strategy documented
- [ ] Security considerations addressed
- [ ] Team agrees design is implementable
- [ ] Ready for developers to code against

---

## Success Metrics

**Design is complete when**:

- ✅ All requirements covered in design
- ✅ Data model normalized and performant
- ✅ API contracts clear enough for implementation
- ✅ Risks identified and mitigation planned
- ✅ Performance targets achievable
- ✅ Scaling strategy defined
- ✅ Ready for developers to implement

---

## Execution Protocol

1. **Parse Input**: Extract sub-problem and requirements
2. **Phase 1**: Select architectural approach → CHECKPOINT 1
3. **Phase 2**: Detail design specification → CHECKPOINT 2
4. **Phase 3**: Validate design and identify risks
5. **Generate**: Comprehensive design document ready for implementation

**Estimated Time**: 4-8 hours depending on complexity

**Output**: Detailed design specification ready for `/solve:implement`
