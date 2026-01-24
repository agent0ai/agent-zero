---
description: Import Zapier workflows and convert to native automation with full feature support
argument-hint: [--zapier-url url] [--import-all] [--auto-convert] [--test-first]
model: claude-3-5-haiku-20241022
allowed-tools: Bash, AskUserQuestion
---

# Zapier Workflow Import & Migration

Seamlessly import your Zapier workflows and convert them to native automation with enhanced capabilities.

## Step 1: Authentication & Connection

Connect your Zapier account:

```yaml
Zapier Integration Setup:
  1. Authorize Zapier API access
     - Scopes: read:zap, read:history, read:invitations
  2. Verify API key is secured
  3. Get list of active Zaps
  4. Check integration compatibility
```

**Supported Zapier Integrations** (95%+ of Zapier apps):

```
✓ CRM: Zoho CRM, Salesforce, HubSpot, Pipedrive
✓ Email: Gmail, Outlook, SendGrid, Mailgun
✓ Chat: Slack, Teams, Discord, Telegram
✓ Spreadsheets: Google Sheets, Excel, Airtable
✓ Storage: Google Drive, Dropbox, Box, AWS S3
✓ Forms: Typeform, JotForm, Google Forms
✓ Finance: Stripe, PayPal, QuickBooks, Xero
✓ CMS: WordPress, Webflow, Shopify
✓ Analytics: Google Analytics, Mixpanel
✓ Project Management: Asana, Monday.com, Jira
✓ 1000+ more integrations supported
```

## Step 2: Browse Your Zapier Zaps

Discover what workflows you have:

```
═══════════════════════════════════════════════════════════
              YOUR ZAPIER WORKFLOWS
═══════════════════════════════════════════════════════════

ACTIVE ZAPS: 12

┌──────────────────────────────────────────────────────────┐
│ #1 - Property Lead to CRM                                │
├──────────────────────────────────────────────────────────┤
│ Status: ACTIVE (enabled)                                 │
│ Created: 2024-06-15                                      │
│ Last Run: 5 minutes ago                                  │
│ Total Runs: 3,247                                        │
│ Success Rate: 98.2%                                      │
│                                                          │
│ Trigger: Webhook (form submission)                       │
│ Actions:                                                 │
│   1. Create lead in Zoho CRM                            │
│   2. Send welcome email (Gmail)                          │
│   3. Create Slack message                                │
│                                                          │
│ CONVERSION READINESS: Excellent (100%)                  │
│ Estimated Benefits:                                      │
│   • 60% faster execution (native vs Zapier)             │
│   • No Zapier subscription needed                        │
│   • Better error handling & retries                      │
│   • Direct integrations (no API intermediary)            │
│                                                          │
│ [View Details] [Import & Convert] [Compare]             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ #2 - Maintenance Request Workflow                        │
├──────────────────────────────────────────────────────────┤
│ Status: ACTIVE                                           │
│ Created: 2024-08-22                                      │
│ Last Run: 2 hours ago                                    │
│ Total Runs: 1,843                                        │
│ Success Rate: 96.8%                                      │
│                                                          │
│ Trigger: Google Forms (form submission)                  │
│ Actions:                                                 │
│   1. Create CRM ticket                                   │
│   2. Send Slack notification                             │
│   3. Assign to Google Calendar                           │
│   4. Send SMS (Twilio)                                   │
│                                                          │
│ CONVERSION READINESS: Excellent (98%)                   │
│ Note: Requires Twilio setup (included)                  │
│                                                          │
│ [View Details] [Import & Convert] [Compare]             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ #3 - Monthly Rent Reminder Automation                   │
├──────────────────────────────────────────────────────────┤
│ Status: ACTIVE                                           │
│ Created: 2024-07-10                                      │
│ Last Run: 1 day ago                                      │
│ Total Runs: 12                                           │
│ Success Rate: 100%                                       │
│                                                          │
│ Trigger: Schedule (Monthly on 1st)                       │
│ Actions:                                                 │
│   1. Query CRM for due rents                             │
│   2. Generate invoice (Stripe)                           │
│   3. Send email reminder                                 │
│   4. Log in Airtable                                     │
│                                                          │
│ CONVERSION READINESS: Good (95%)                        │
│ Benefits:                                                │
│   • Add conditional approval routing                    │
│   • Enhanced error recovery                             │
│   • Direct payment processing                           │
│                                                          │
│ [View Details] [Import & Convert] [Compare]             │
└──────────────────────────────────────────────────────────┘

[Show More] (9 more active zaps)
```

## Step 3: Select Zaps to Import

Choose which Zaps to migrate:

```
SELECT ZAPS TO IMPORT:

☑ Property Lead to CRM
☑ Maintenance Request Workflow
☑ Monthly Rent Reminder Automation
☐ Email Campaign Distribution
☐ Data Backup to Google Drive
☐ Customer Feedback Survey
☐ Invoice Auto-Filing
☐ Team Alert System
☐ Expense Report Processing
☐ Document Collection Form

Selected: 3 zaps
Estimated Import Time: 5 minutes
Estimated Setup Time: 15 minutes

[Import Selected] [Select All] [Deselect All] [Preview Details]
```

## Step 4: Preview Conversions

See what each Zap will become:

```
═══════════════════════════════════════════════════════════
        CONVERSION PREVIEW: Property Lead to CRM
═══════════════════════════════════════════════════════════

CURRENT ZAP (Zapier):
┌──────────────────────┐
│ Trigger: Webhook     │
│ Step 1: Zoho CRM     │
│ Step 2: Gmail        │
│ Step 3: Slack        │
└──────────────────────┘

CONVERTED WORKFLOW (Native Automation):
┌──────────────────────┐
│ Trigger: Webhook     │
│ Step 1: Zoho CRM     │
│ Step 2: Zoho Mail ←─ UPGRADED (direct instead of Gmail)
│ Step 3: Slack        │
│ Step 4: Error Mgmt   │
│ Step 5: Approval Opt │
│ Step 6: Monitoring   │
└──────────────────────┘

ENHANCEMENTS INCLUDED:
✓ Direct Zoho Mail (skip Gmail intermediary)
✓ Built-in error handling & retries
✓ Optional approval routing
✓ Execution monitoring dashboard
✓ Performance analytics
✓ Automatic logging & audit trail

CONFIGURATION MAPPING:
✓ Trigger settings: Identical
✓ CRM fields: Auto-mapped (100% match)
✓ Email templates: Imported and preserved
✓ Slack formatting: Preserved with enhancements
✓ Custom mappings: Converted to native format

ESTIMATED PERFORMANCE IMPROVEMENTS:
• Execution speed: 40% faster (0.8s vs 1.3s)
• Success rate: 99.5% (vs 98.2% in Zapier)
• Retry mechanism: Automatic (vs Zapier delays)
• Cost: Eliminates Zapier task usage

DATA MIGRATION:
✓ Webhook history: Not migrated (fresh start)
✓ Task usage: No longer counted toward Zapier limits
✓ Configuration: 100% preserved
✓ Custom fields: Automatically mapped

═══════════════════════════════════════════════════════════

[Confirm Conversion] [View Detailed Mapping] [Cancel]
```

## Step 5: Import Configuration Details

See exact field mappings:

```yaml
Webhook Trigger Configuration:
  Original (Zapier):
    - Endpoint: https://hooks.zapier.com/hooks/catch/...
    - Method: POST
    - Expected Fields: name, email, phone, property_id

  Converted (Native):
    - Endpoint: https://automation-hub.example.com/webhook/prop-lead
    - Method: POST
    - Expected Fields: name, email, phone, property_id
    - Headers: Authorization (optional)
    - Error Handling: Automatic retry (3x)

Action 1: Zoho CRM - Create Lead
  Original Mapping:
    • First Name: ${trigger.first_name}
    • Email: ${trigger.email_address}
    • Phone: ${trigger.phone_number}
    • Property: ${trigger.property}

  Converted Mapping:
    • First Name: ${json.name}
    • Email: ${json.email}
    • Phone: ${json.phone}
    • Property Interest: ${json.property_id}
    • Source: Form Submission
    • Created Date: ${now()}
    • Owner: Auto-assign (no change)

Action 2: Email - Send Welcome Email
  Original (Gmail via Zapier):
    • To: ${trigger.email}
    • Subject: Welcome to Properties!
    • Body: Custom HTML template
    • From: noreply@propertymanagement.com
    • Track Opens: Yes

  Converted (Zoho Mail - Direct):
    • To: ${json.email}
    • From: Your Zoho domain
    • Subject: Welcome to Properties!
    • Body: Imported HTML (exactly same)
    • Template: Preserved
    • Track Opens: Enhanced tracking
    • Reply-to: Auto-configured

Action 3: Chat - Slack Notification
  Original (Zapier format):
    • Channel: #new-leads
    • Username: ZapierBot
    • Message: "New lead from {{name}}"
    • Formatting: Basic

  Converted (Native Slack integration):
    • Channel: #new-leads
    • Username: AutomationHub
    • Message: "New lead from {{name}}"
    • Rich formatting: Enhanced with buttons
    • Attachments: Lead details card
    • Threads: Organize conversations
    • Reactions: Enable team collaboration

═══════════════════════════════════════════════════════════
```

## Step 6: Test Conversions

Verify each converted Zap works identically:

```bash
# Test converted workflow with sample data
POST https://automation-hub.example.com/webhook/prop-lead

Sample Data:
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "555-9876",
  "property_id": "PROP-005"
}

Execution Results:

✓ Step 1: Webhook received (0.1s)
✓ Step 2: CRM lead created (0.8s)
  - Lead ID: L-98765
  - Assigned to: John Manager
  - Status: New

✓ Step 3: Email sent (1.2s)
  - Subject: Welcome to Properties!
  - Status: Delivered
  - Opens tracked

✓ Step 4: Slack notification posted (0.9s)
  - Channel: #new-leads
  - Message: "New lead from Jane Smith"
  - Reactions enabled

TOTAL EXECUTION TIME: 3.0s (vs Zapier avg 4.5s)
SUCCESS RATE: 100%
ERROR HANDLING: Ready for production

Comparison with Original Zap:
• Same output: ✓ Yes (identical results)
• Faster execution: ✓ Yes (33% faster)
• Better error handling: ✓ Yes (auto-retry included)
• More features: ✓ Yes (approval gate available)

[Confirm & Activate] [Test More Scenarios] [Adjust Mapping]
```

## Step 7: Batch Import

Import all selected Zaps at once:

```
═══════════════════════════════════════════════════════════
              IMPORTING ZAPS TO AUTOMATION HUB
═══════════════════════════════════════════════════════════

Zaps Selected: 3
Estimated Import Time: 5-10 minutes

Progress:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 67% (4/6 steps)

Current Step: Converting field mappings...

Details:
✓ 1/3: Property Lead to CRM (100%)
  - Webhook configured
  - CRM mapping completed
  - Email template imported
  - Slack format converted

✓ 2/3: Maintenance Request (75%)
  - Google Forms trigger parsing...
  - CRM ticket mapping in progress
  - Twilio SMS configuration pending

○ 3/3: Rent Reminder (0%)
  - Waiting...

═══════════════════════════════════════════════════════════
```

## Step 8: Update Webhook URLs

If using webhooks, update your forms/systems:

```
OLD WEBHOOK (Zapier):
https://hooks.zapier.com/hooks/catch/123456789/abcdefg

NEW WEBHOOK (Native Automation):
https://automation-hub.example.com/webhook/property-lead-abc123

Update your form's action attribute:
OLD: <form action="https://hooks.zapier.com/hooks/catch/123456789/abcdefg">
NEW: <form action="https://automation-hub.example.com/webhook/property-lead-abc123">

Update JavaScript fetch:
OLD: fetch('https://hooks.zapier.com/hooks/catch/123456789/abcdefg', ...)
NEW: fetch('https://automation-hub.example.com/webhook/property-lead-abc123', ...)

Testing:
1. Update one form/system
2. Run test submission
3. Verify execution in dashboard
4. Update remaining forms
5. Deactivate old Zapier zap (keep running 7 days to verify)
6. Delete Zapier zap when confident
```

## Step 9: Cost Analysis & Benefits

See why migration saves money and improves performance:

```
═══════════════════════════════════════════════════════════
            ZAPIER → NATIVE AUTOMATION COMPARISON
═══════════════════════════════════════════════════════════

COST ANALYSIS (Annual):

Zapier Pricing:
  • 3 active zaps × $19.99 (Starter) = $59.97/month
  • Or estimate by task usage:
    - 3,247 + 1,843 + 12 = 5,102 tasks/month
    - Average task cost: $0.04-0.12
    - Estimated: $200-600/month = $2,400-7,200/year

Native Automation (Free or Self-Hosted):
  • Self-hosted n8n: $0-500/year (infrastructure)
  • Or included in existing platform
  • Estimated total: $0-500/year

ANNUAL SAVINGS: $1,900 - $7,200 per year

PERFORMANCE IMPROVEMENTS:

Execution Speed:
  Zapier Average: 1.3-4.5 seconds per execution
  Native Average: 0.8-2.0 seconds per execution
  Improvement: 38-56% faster execution

Success Rate:
  Zapier: 96.8% - 98.2% (as shown in your zaps)
  Native: 99.5%+ (with built-in retry logic)
  Improvement: 1.3-2.7% higher success

Reliability:
  Zapier: Manual retry, support delays
  Native: Automatic retry with exponential backoff
  Improvement: Faster recovery from failures

Feature Enhancements:
  Zapier: Limited error handling
  Native: Rich error handling, approval gates, monitoring
  Improvement: Greater control and visibility

EXAMPLE ROI (12-month period):

Year 1:
  • Zapier cost saved: $4,000 (conservative estimate)
  • Setup & migration: 2 hours × $50/hr = $100
  • Faster executions save: 80 hours × $25/hr = $2,000
  • Fewer failures saved: 300 failed tasks × $0.05 = $15
  Total Benefit: $6,015
  Net Benefit (Year 1): $5,915

Year 2+:
  • Annual Zapier savings: $4,000
  • Faster execution savings: $2,000+
  • Improved reliability: $500+
  • Total Annual Benefit: $6,500+

═══════════════════════════════════════════════════════════
```

## Step 10: Deactivation Strategy

Safely transition away from Zapier:

```yaml
Transition Plan:

Week 1 (Parallel Run):
  - Import and test all zaps
  - Keep both Zapier and native running
  - Monitor for any discrepancies
  - Verify data integrity

Week 2 (Gradual Activation):
  - Activate property lead zap (native)
  - Keep Zapier running as backup
  - Monitor execution rate
  - Verify all leads processing

Week 3 (Full Migration):
  - Activate remaining zaps (native)
  - Reduce Zapier monitoring
  - Document any issues
  - Plan Zapier cancellation

Week 4 (Cleanup):
  - Verify all native zaps stable (14 days data)
  - Cancel Zapier account
  - Redirect documentation
  - Archive Zapier knowledge

Rollback Plan (if issues):
  - If native zap fails: Activate Zapier zap
  - If data mismatch: Run data verification
  - If performance degrades: Adjust configurations
  - Contact support for troubleshooting
```

## Step 11: Post-Import Monitoring

Track migration success:

```
═══════════════════════════════════════════════════════════
          MIGRATION MONITORING DASHBOARD
═══════════════════════════════════════════════════════════

Property Lead to CRM:
  Status: ✓ ACTIVE (Native)
  Executions (24h): 47
  Success Rate: 100% (47/47)
  Avg Execution: 0.9s
  Zapier equivalent was: 1.2s (25% faster!)
  Status: HEALTHY

Maintenance Request:
  Status: ✓ ACTIVE (Native)
  Executions (24h): 12
  Success Rate: 100% (12/12)
  Avg Execution: 1.8s
  Zapier equivalent was: 2.3s (22% faster!)
  Status: HEALTHY

Rent Reminder:
  Status: ✓ ACTIVE (Native)
  Last Run: 2 hours ago
  Success: ✓ Yes
  Executions (7d): 3
  Success Rate: 100%
  Status: HEALTHY

Overall Migration:
  ✓ 3/3 zaps successfully imported
  ✓ 0 failed executions (24h)
  ✓ 100% success rate
  ✓ 28% average speed improvement
  ✓ Ready to cancel Zapier subscription

Recommendations:
  1. Monitor for 7-14 more days
  2. Document any process changes
  3. Train team on new platform
  4. Cancel Zapier subscription
  5. Celebrate cost savings!

═══════════════════════════════════════════════════════════
```

## Advanced: Manual Workflow Conversion

For complex Zaps requiring custom logic:

```yaml
Custom Conversion Example - Advanced Zap:

Original Zapier Zap:
  Trigger: Scheduled (Daily 9 AM)
  Step 1: Code by Zapier (JavaScript transform)
  Step 2: Spreadsheet (query for due items)
  Step 3: Loop (for each item)
    Step 3a: CRM API (fetch details)
    Step 3b: Logic (check conditions)
    Step 3c: Email (send customized)
  Step 4: Slack (summary notification)

Converted to Native Workflow:
  1. Trigger: Schedule (Daily 9 AM)
  2. Action: Code node (same JavaScript - works identically)
  3. Action: Google Sheets (query unchanged)
  4. Logic: Loop (iterate items)
     - Action: CRM API call
     - Logic: Conditional checks
     - Action: Send email (from template)
  5. Action: Slack notification
  6. Action: Error handling & logging
  7. Action: Performance monitoring

Benefits:
  ✓ Same logic converted directly
  ✓ No functionality lost
  ✓ Better error handling added
  ✓ Performance monitoring included
  ✓ Cost savings achieved
```

---

**Uses**: zapier-import-agent, workflow-migration-engine
**Model**: Haiku (fast Zapier operations)
**Migration Time**: 5-30 minutes depending on zap complexity
**Cost Savings**: Typical $2,400-$7,200 annually
