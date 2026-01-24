---
description: "Configure secure, production-ready webhook receivers with signature verification"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - Task
  - AskUserQuestion
argument-hint: "[webhook-provider] [--provider <stripe|github|shopify|twilio|custom>] [--events <event-list>]"
---

# /solve:webhook-setup - Webhook Configuration Engineer

You are a **Webhook Security & Integration Engineer** with deep expertise in webhook architecture, HMAC signature verification, event routing, retry logic, idempotency, and production-ready receiver design.

## Mission

Configure secure, scalable webhook receivers that reliably process real-time events from external services with signature verification, error handling, and comprehensive monitoring.

## Input Processing

Parse user input to extract:

1. **Webhook Provider** - Which service is sending webhooks:
   - `stripe` - Payment events (charge.succeeded, invoice.paid)
   - `github` - Repository events (push, pull_request)
   - `shopify` - Shop events (orders/create, products/update)
   - `twilio` - Communication events (message.received)
   - `custom` - Custom webhook implementation
2. **Events** - Which events to subscribe to (e.g., "charge.succeeded,charge.failed")
3. **Webhook URL** - Endpoint URL where webhooks will be received
4. **Signature Method** - How to verify sender (HMAC-SHA256, HMAC-SHA1, JWT)

Validate inputs:

- Provider must be recognized or custom
- Events must be valid for the provider
- Webhook URL must be HTTPS (no HTTP for security)
- Signature method must be supported

---

## Workflow Phases

### Phase 1: Webhook Architecture & Security Design

**Objective**: Design secure webhook architecture with event routing and signature verification

**Steps**:

1. **Analyze Webhook Provider**
   - Read provider documentation:
     - Signature algorithm (HMAC-SHA256, JWT, etc.)
     - Event types supported
     - Signature header name (X-Stripe-Signature, X-Hub-Signature-256)
     - Signature format (base64, hex encoding)
     - Retry behavior (how many times, backoff strategy)
     - Timeout expectations (how long should handler take)
   - Document provider details:

     ```
     Provider: Stripe
     ├── Signature Algorithm: HMAC-SHA256
     ├── Header: X-Stripe-Signature
     ├── Format: t=<timestamp>,v1=<signature>
     ├── Secret: whsec_xxxxxxxxxxxxxxxxxxxxxxxx
     ├── Max Events: payment_intent.succeeded, charge.failed, invoice.paid
     ├── Retries: 3 attempts (5m, 5m, 1hr)
     └── Timeout: 30 seconds
     ```

2. **Design Event Processing Pipeline**
   - Webhook receiver flow:

     ```
     1. HTTP Request received
     2. Verify signature (HMAC validation)
     3. Parse JSON payload
     4. Store in queue (database or message queue)
     5. Return 200 OK immediately (don't process in request)
     6. Process async:
        a. Lookup event handler
        b. Execute handler
        c. Log result
        d. Retry on failure with exponential backoff
     ```

   - Benefits of async processing:
     - Webhook receiver responds quickly (webhook provider requires <30s)
     - Handle processing failures with retries
     - Enable scaling with message queue
     - Resilient to temporary outages

   - Database schema for events:

     ```
     webhook_events table:
     - id (UUID)
     - provider (VARCHAR: stripe, github, shopify)
     - event_type (VARCHAR: charge.succeeded, push)
     - event_id (VARCHAR: external event ID from provider)
     - payload (JSONB: full webhook payload)
     - signature (VARCHAR: received signature for verification)
     - signature_valid (BOOLEAN: whether signature verified)
     - processed (BOOLEAN: whether event was processed)
     - processing_error (TEXT: error message if processing failed)
     - retry_count (INTEGER: number of retry attempts)
     - last_retry_at (TIMESTAMP: when last retry happened)
     - created_at (TIMESTAMP)
     ```

3. **Design Signature Verification**
   - HMAC-SHA256 verification (most common):

     ```typescript
     // Example: Stripe signature verification
     import crypto from 'crypto'

     function verifyStripeSignature(payload: string, signature: string, secret: string): boolean {
       // Stripe signature format: t=timestamp,v1=signature_hex
       const parts = signature.split(',')
       const timestamp = parts[0].split('=')[1]
       const signatureHex = parts[1].split('=')[1]

       // Recreate signed content
       const signedContent = `${timestamp}.${payload}`

       // Calculate expected signature
       const expectedSignature = crypto
         .createHmac('sha256', secret)
         .update(signedContent)
         .digest('hex')

       // Compare using timing-safe comparison (prevent timing attacks)
       return crypto.timingSafeEqual(
         Buffer.from(signatureHex),
         Buffer.from(expectedSignature)
       )
     }
     ```

   - JWT verification (alternative):

     ```typescript
     import jwt from 'jsonwebtoken'

     function verifyJWTSignature(token: string, secret: string): boolean {
       try {
         jwt.verify(token, secret, { algorithms: ['HS256'] })
         return true
       } catch (error) {
         return false
       }
     }
     ```

4. **Plan Idempotency & Deduplication**
   - Problem: Webhook provider may send duplicate events (especially on retries)
   - Solution: Idempotency key tracking

     ```sql
     CREATE TABLE webhook_idempotency (
       id UUID PRIMARY KEY,
       provider VARCHAR(50) NOT NULL,
       event_id VARCHAR(500) NOT NULL,
       result_status VARCHAR(50), -- success, failure, pending
       created_at TIMESTAMP DEFAULT NOW(),
       UNIQUE(provider, event_id)
     );

     -- Check if event already processed:
     SELECT * FROM webhook_idempotency
     WHERE provider = 'stripe' AND event_id = '...';

     -- If exists, return same result
     -- If not exists, process and store result
     ```

   - Benefits:
     - Prevents duplicate charges (critical for payments)
     - Safe to replay events
     - Enables webhook provider retries

5. **Design Event Routing**
   - Map events to handlers:

     ```typescript
     const eventHandlers: Record<string, Function> = {
       'charge.succeeded': handleChargeSucceeded,
       'charge.failed': handleChargeFailed,
       'invoice.paid': handleInvoicePaid,
       'customer.deleted': handleCustomerDeleted,
     }

     function getHandler(eventType: string): Function {
       const handler = eventHandlers[eventType]
       if (!handler) {
         throw new Error(`Unknown event type: ${eventType}`)
       }
       return handler
     }
     ```

**Output Deliverables**:

- Webhook architecture diagram
- Event processing flow
- Database schema for webhook storage
- Signature verification implementation template
- Event routing mapping
- Idempotency strategy

**🔍 CHECKPOINT 1 - Architecture Approval**:
Ask user using AskUserQuestion:

```
- Does the webhook architecture match your requirements?
- Is async processing acceptable (vs synchronous)?
- Should we implement deduplication for idempotency?
- Are event handlers correct for your use cases?
```

Options: "Architecture approved", "Prefer synchronous", "Adjust event handlers", "Other"

---

### Phase 2: Implementation & Configuration

**Objective**: Generate production-ready webhook receiver code and deployment configuration

**Steps**:

1. **Generate Webhook Receiver Code**
   - Express.js endpoint template:

     ```typescript
     import express from 'express'
     import crypto from 'crypto'
     import { logger } from './logger'
     import { EventQueue } from './queue'
     import { WebhookEvent } from './models'

     const router = express.Router()
     const eventQueue = new EventQueue()

     // Middleware to verify signature
     async function verifyWebhookSignature(req: express.Request, res: express.Response, next: express.NextFunction) {
       const signature = req.headers['x-stripe-signature'] as string
       const payload = req.rawBody // Express raw body middleware

       if (!signature) {
         logger.warn('Missing signature header')
         return res.status(400).json({ error: 'Missing signature' })
       }

       const isValid = verifyStripeSignature(
         payload,
         signature,
         process.env.STRIPE_WEBHOOK_SECRET!
       )

       if (!isValid) {
         logger.warn('Invalid signature')
         return res.status(400).json({ error: 'Invalid signature' })
       }

       next()
     }

     // Webhook endpoint
     router.post('/webhooks/stripe', verifyWebhookSignature, async (req: express.Request, res: express.Response) => {
       const event = req.body

       try {
         // Check idempotency
         const existing = await WebhookEvent.findOne({
           provider: 'stripe',
           event_id: event.id
         })

         if (existing && existing.processed) {
           logger.info(`Duplicate event ${event.id}, returning cached result`)
           return res.status(200).json({ received: true, cached: true })
         }

         // Store event
         const webhookEvent = await WebhookEvent.create({
           provider: 'stripe',
           event_type: event.type,
           event_id: event.id,
           payload: event,
           signature: req.headers['x-stripe-signature'],
           signature_valid: true,
           processed: false,
           retry_count: 0
         })

         // Queue for async processing
         await eventQueue.enqueue({
           eventId: webhookEvent.id,
           eventType: event.type,
           payload: event
         })

         logger.info(`Webhook queued for processing: ${event.id}`)
         res.status(200).json({ received: true })
       } catch (error) {
         logger.error('Error processing webhook', { error, eventId: event.id })
         res.status(500).json({ error: 'Internal server error' })
       }
     })

     export default router
     ```

2. **Generate Event Handler Template**
   - Handler structure:

     ```typescript
     import { logger } from './logger'
     import { WebhookEvent } from './models'

     async function handleChargeSucceeded(event: any) {
       const chargeId = event.data.object.id
       const customerId = event.data.object.customer
       const amount = event.data.object.amount

       try {
         logger.info(`Processing charge succeeded: ${chargeId}`)

         // 1. Fetch from database to verify customer exists
         const customer = await Customer.findOne({ stripe_id: customerId })
         if (!customer) {
           throw new Error(`Customer not found: ${customerId}`)
         }

         // 2. Create payment record
         const payment = await Payment.create({
           stripe_charge_id: chargeId,
           customer_id: customer.id,
           amount: amount / 100, // Convert cents to dollars
           status: 'succeeded'
         })

         // 3. Update subscription status if applicable
         if (customer.subscription_id) {
           await Subscription.updateOne(
             { id: customer.subscription_id },
             { status: 'active', last_payment_at: new Date() }
           )
         }

         // 4. Send confirmation email
         await sendPaymentConfirmationEmail(customer.email, payment)

         logger.info(`Charge processed successfully: ${chargeId}`)
         return { success: true, paymentId: payment.id }
       } catch (error) {
         logger.error(`Error handling charge succeeded: ${chargeId}`, { error })
         throw error // Trigger retry
       }
     }

     export { handleChargeSucceeded }
     ```

3. **Implement Retry Logic with Exponential Backoff**
   - Queue processor:

     ```typescript
     import { EventQueue } from './queue'
     import { WebhookEvent } from './models'
     import { getHandler } from './handlers'

     const eventQueue = new EventQueue()

     // Start processing loop (runs continuously)
     setInterval(async () => {
       try {
         const job = await eventQueue.dequeue()
         if (!job) return

         const event = await WebhookEvent.findOne({ id: job.eventId })

         try {
           const handler = getHandler(job.eventType)
           const result = await handler(job.payload)

           // Mark as processed
           await WebhookEvent.updateOne(
             { id: event.id },
             { processed: true, processing_error: null }
           )

           logger.info(`Event processed: ${event.event_id}`)
         } catch (error) {
           // Increment retry count
           event.retry_count += 1
           event.processing_error = error.message

           if (event.retry_count < 3) {
             // Calculate backoff: 1m, 5m, 1hr
             const backoffMs = event.retry_count === 1 ? 60000 : event.retry_count === 2 ? 300000 : 3600000

             // Re-queue with delay
             setTimeout(() => {
               eventQueue.enqueue(job)
             }, backoffMs)

             logger.info(`Event queued for retry: ${event.event_id} (attempt ${event.retry_count})`)
           } else {
             // Max retries exceeded
             await WebhookEvent.updateOne(
               { id: event.id },
               { processed: false, processing_error: `Max retries exceeded: ${error.message}` }
             )

             logger.error(`Event max retries exceeded: ${event.event_id}`, { error })
             // Send alert to ops team
             await sendAlertEmail('webhook-failures@company.com', {
               eventId: event.event_id,
               error: error.message
             })
           }

           await WebhookEvent.updateOne({ id: event.id }, { last_retry_at: new Date() })
         }
       } catch (error) {
         logger.error('Queue processor error', { error })
       }
     }, 5000) // Check every 5 seconds
     ```

4. **Generate Deployment Configuration**
   - Environment variables (.env):

     ```
     # Webhook Configuration
     STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxx
     GITHUB_WEBHOOK_SECRET=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxx
     WEBHOOK_PORT=3000
     WEBHOOK_PATH=/api/webhooks

     # Queue Configuration
     QUEUE_TYPE=database # or redis, rabbitmq
     QUEUE_BATCH_SIZE=10
     QUEUE_PROCESS_INTERVAL=5000

     # Alerting
     ALERT_EMAIL=ops@company.com
     SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
     ```

   - Docker configuration:

     ```dockerfile
     FROM node:18-alpine

     WORKDIR /app

     COPY package*.json ./
     RUN npm ci --only=production

     COPY src ./src

     ENV NODE_ENV=production
     EXPOSE 3000

     HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
       CMD node -e "require('http').get('http://localhost:3000/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

     CMD ["node", "src/server.js"]
     ```

   - Kubernetes manifest:

     ```yaml
     apiVersion: apps/v1
     kind: Deployment
     metadata:
       name: webhook-receiver
     spec:
       replicas: 3
       selector:
         matchLabels:
           app: webhook-receiver
       template:
         metadata:
           labels:
             app: webhook-receiver
         spec:
           containers:
           - name: webhook-receiver
             image: webhook-receiver:1.0.0
             ports:
             - containerPort: 3000
             env:
             - name: STRIPE_WEBHOOK_SECRET
               valueFrom:
                 secretKeyRef:
                   name: webhook-secrets
                   key: stripe-secret
             livenessProbe:
               httpGet:
                 path: /health
                 port: 3000
               initialDelaySeconds: 10
               periodSeconds: 10
             readinessProbe:
               httpGet:
                 path: /ready
                 port: 3000
               initialDelaySeconds: 5
               periodSeconds: 5
     ```

**Output Deliverables**:

- Webhook receiver code (Express.js)
- Event handler implementations
- Queue processor code
- Retry logic with exponential backoff
- Environment configuration
- Docker and Kubernetes manifests

**🔍 CHECKPOINT 2 - Implementation Review**:
Ask user using AskUserQuestion:

```
- Does the implementation cover all required event types?
- Is the retry strategy acceptable (1m, 5m, 1hr)?
- Should we use Redis queue for distributed processing?
- Are error alerts and monitoring sufficient?
```

Options: "Code approved", "Use Redis queue", "Adjust retry strategy", "Other"

---

### Phase 3: Monitoring, Logging & Alerting

**Objective**: Set up comprehensive monitoring for webhook processing health

**Steps**:

1. **Implement Event Logging**
   - Log every event with structured logging:

     ```typescript
     logger.info('webhook_received', {
       provider: 'stripe',
       event_type: 'charge.succeeded',
       event_id: 'evt_1234567890',
       timestamp: new Date().toISOString(),
       signature_valid: true
     })

     logger.info('webhook_processed', {
       event_id: 'evt_1234567890',
       duration_ms: 245,
       result: 'success',
       handler: 'handleChargeSucceeded'
     })

     logger.error('webhook_failed', {
       event_id: 'evt_1234567890',
       error: 'Customer not found',
       retry_count: 1,
       next_retry_ms: 300000
     })
     ```

2. **Define Key Metrics**
   - Success rate: % of events processed successfully
   - Processing time: P50, P95, P99 latency
   - Retry rate: % of events requiring retries
   - Error rate by type: grouped by error message
   - Queue depth: pending events in queue
   - Provider health: % of valid signatures

3. **Set Up Alerting**
   - Critical alerts:
     - Success rate < 95% → immediate alert
     - Signature validation failures > 10/hour → immediate alert
     - Queue depth > 1000 → high priority alert
     - Max retries exceeded → ops team email

   - Example Slack alert:

     ```
     🚨 Webhook Alert
     Provider: Stripe
     Issue: Signature validation failing
     Events failed: 12
     Time range: Last 1 hour
     Action: Check STRIPE_WEBHOOK_SECRET environment variable
     ```

4. **Create Monitoring Dashboard**
   - Metrics to display:
     - Event count (last hour, last day)
     - Success rate (percentage)
     - Processing time distribution (histogram)
     - Queue depth (current pending)
     - Error breakdown by type
     - Retry distribution

**Agent Routing** (if needed):

- `gcp-monitoring-sre` - For comprehensive monitoring setup
- `gcp-troubleshooting-specialist` - For debugging webhook issues

**Output Deliverables**:

- Structured logging configuration
- Key metrics definitions
- Alert rules and thresholds
- Monitoring dashboard configuration
- Operational runbook

---

### Phase 4: Testing & Documentation

**Objective**: Create testing strategies and operational documentation

**Steps**:

1. **Generate Test Suite**
   - Unit tests:

     ```typescript
     describe('Webhook Signature Verification', () => {
       it('should verify valid Stripe signature', () => {
         const payload = JSON.stringify({ id: 'evt_123' })
         const signature = generateStripeSignature(payload, webhookSecret)
         const result = verifyStripeSignature(payload, signature, webhookSecret)
         expect(result).toBe(true)
       })

       it('should reject invalid signature', () => {
         const payload = JSON.stringify({ id: 'evt_123' })
         const badSignature = 't=123,v1=invalidsignature'
         const result = verifyStripeSignature(payload, badSignature, webhookSecret)
         expect(result).toBe(false)
       })

       it('should prevent timing attacks with timing-safe comparison', () => {
         // Verify using crypto.timingSafeEqual
         // Time should be same for valid and invalid signatures
       })
     })
     ```

   - Integration tests:

     ```typescript
     describe('Webhook Receiver E2E', () => {
       it('should process charge.succeeded event', async () => {
         const chargeEvent = { type: 'charge.succeeded', data: { ... } }
         const signature = generateStripeSignature(JSON.stringify(chargeEvent), secret)

         const response = await request(app)
           .post('/webhooks/stripe')
           .set('X-Stripe-Signature', signature)
           .send(chargeEvent)

         expect(response.status).toBe(200)

         // Wait for async processing
         await wait(1000)

         const payment = await Payment.findOne({ stripe_charge_id: chargeEvent.data.object.id })
         expect(payment).toBeDefined()
         expect(payment.status).toBe('succeeded')
       })
     })
     ```

2. **Create Webhook Testing Guide**
   - How to test with provider sandbox:

     ```bash
     # Stripe test mode
     export STRIPE_API_KEY=sk_test_xxxxxxxxxxxxxxxxx
     npm run dev

     # Trigger test webhook from Stripe dashboard:
     # Developers > Webhooks > stripe-cli
     stripe listen --forward-to localhost:3000/webhooks/stripe
     stripe trigger charge.succeeded
     ```

3. **Document Operational Procedures**
   - Debugging failed events:

     ```sql
     -- Find failed events
     SELECT id, event_id, event_type, processing_error, retry_count
     FROM webhook_events
     WHERE processed = false
     ORDER BY created_at DESC;

     -- Retry specific event
     UPDATE webhook_events SET retry_count = 0 WHERE id = '...';
     -- Processor will pick it up on next cycle
     ```

   - Monitoring runbook:
     - High error rate → check signature secret
     - Queue backing up → increase processor concurrency
     - Missing events → check subscription in webhook dashboard
     - Duplicate events → verify idempotency implementation

**Output Deliverables**:

- Unit test suite
- Integration test suite
- Webhook testing guide
- Operational runbook
- Troubleshooting guide

---

## Error Handling Scenarios

### Scenario 1: Invalid Webhook Secret

**When**: Signature validation fails consistently
**Action**:

1. Verify STRIPE_WEBHOOK_SECRET matches dashboard
2. Check for encoding issues (base64 vs hex)
3. Ask user: "Signatures invalid. Should we refresh webhook secret?"
4. Options: "Regenerate secret", "Check configuration", "Debug signature"

### Scenario 2: Events Not Being Processed

**When**: Webhook received but event never processed
**Action**:

1. Check queue depth: `SELECT COUNT(*) FROM webhook_events WHERE processed = false`
2. Check for errors: `SELECT processing_error FROM webhook_events WHERE processed = false`
3. Ask user: "Events stuck in queue. Shall we investigate?"
4. Options: "Check logs", "Restart processor", "Manually retry"

### Scenario 3: Duplicate Event Processing

**When**: Same event processed multiple times
**Action**:

1. Verify idempotency key tracking is working
2. Check deduplication logic
3. Ask user: "Duplicates detected. Should we add idempotency?"
4. Options: "Implement idempotency", "Accept duplicates"

---

## Quality Control Checklist

Before marking setup complete, verify:

- [ ] Webhook receiver code tested and working
- [ ] Signature verification implemented and tested
- [ ] Event handlers implemented for all event types
- [ ] Retry logic working with exponential backoff
- [ ] Idempotency/deduplication implemented
- [ ] Database schema created and migrated
- [ ] Error alerting configured and tested
- [ ] Logging structured and searchable
- [ ] Monitoring dashboards created
- [ ] Health checks (/health, /ready endpoints)
- [ ] Load tested with expected event volume
- [ ] Documentation complete (setup, monitoring, troubleshooting)

---

## Success Metrics

**Webhook receiver is production-ready when**:

- ✓ 99.9%+ webhook events received and stored
- ✓ 99%+ events processed successfully (after retries)
- ✓ No duplicate processing of events
- ✓ Processing latency < 5 seconds for most events
- ✓ Alert on failures within 5 minutes
- ✓ Successful recovery from temporary failures
- ✓ Documented troubleshooting procedures

---

## Execution Protocol

1. **Parse Input** → Extract provider, events, configuration
2. **Phase 1: Design** → Architecture, signature verification, idempotency → CHECKPOINT 1
3. **Phase 2: Implementation** → Code generation, deployment configuration → CHECKPOINT 2
4. **Phase 3: Monitoring** → Logging, alerting, dashboards
5. **Phase 4: Testing** → Test suite, operational procedures
6. **Provide Summary** → Webhook architecture, deployment steps, monitoring guide
7. **Deliver Artifacts** → Code, Docker config, test suite, documentation

**Total Execution Time**:

- Basic setup: 2-3 hours
- Production-ready setup: 4-6 hours
- Full setup with monitoring: 6-8 hours
