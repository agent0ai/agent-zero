---
description: Browse and install pre-built automation workflows from marketplace
argument-hint: [--category property-management|crm|communications|data|all] [--search keyword] [--sort trending|newest|most-used]
model: claude-3-5-haiku-20241022
allowed-tools: Bash, AskUserQuestion
---

# Automation Marketplace

Browse and install pre-built, production-ready workflows to accelerate your automation.

## Step 1: Determine Search Strategy

Choose how to explore the marketplace:

**Browse Options**:

1. Browse by category (property management, CRM, communications, etc.)
2. Search for specific keywords (lead management, tenant onboarding, etc.)
3. View trending workflows (most installed, highest rated)
4. View my installed workflows + recent updates
5. View created by recommended partners (n8n, Zapier integrations)

## Step 2: Display Marketplace Catalog

### Featured Workflows (Popular & Recommended)

```
════════════════════════════════════════════════════════════
                    FEATURED WORKFLOWS
════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ #1 PROPERTY LEAD AUTOMATION                             │
├─────────────────────────────────────────────────────────┤
│ Category: Property Management                            │
│ Status: FEATURED ⭐⭐⭐⭐⭐ (4.9/5 stars)                 │
│ Installs: 2,847 active users                            │
│ Creator: Real Estate Automation Team                    │
│ Updated: 2 weeks ago                                    │
│                                                         │
│ Automates:                                              │
│ ✓ Web form → CRM lead creation                          │
│ ✓ Lead qualification & scoring                          │
│ ✓ Automatic property assignment                         │
│ ✓ Tenant onboarding sequence                            │
│ ✓ Welcome email + SMS                                   │
│ ✓ Calendar scheduling                                   │
│ ✓ Slack team notifications                              │
│                                                         │
│ Integrations: Zoho CRM, Zoho Mail, Slack, Google       │
│ Estimated Setup Time: 15 minutes                        │
│ ROI: 40+ hours/month saved per team                     │
│                                                         │
│ [Install] [View Details] [Reviews] [Documentation]     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ #2 MAINTENANCE REQUEST TICKETING                        │
├─────────────────────────────────────────────────────────┤
│ Category: Property Management                            │
│ Status: NEW ✨                                          │
│ Installs: 634 active users                              │
│ Creator: Maintenance Automation Lab                     │
│ Updated: 3 days ago                                     │
│                                                         │
│ Automates:                                              │
│ ✓ Mobile/web request submission                         │
│ ✓ Category & priority detection (AI)                    │
│ ✓ Contractor assignment                                 │
│ ✓ Push notifications                                    │
│ ✓ Photo documentation & tracking                        │
│ ✓ Completion verification                               │
│ ✓ Invoice generation                                    │
│                                                         │
│ Integrations: Zoho CRM, Firebase, Twilio, Stripe       │
│ Estimated Setup Time: 20 minutes                        │
│ ROI: 25+ hours/month saved                              │
│                                                         │
│ [Install] [View Details] [Reviews] [Documentation]     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ #3 RENT COLLECTION & ACCOUNTING SYNC                    │
├─────────────────────────────────────────────────────────┤
│ Category: Financial Automation                           │
│ Status: TRUSTED ✓ (Enterprise-grade)                    │
│ Installs: 1,203 active users                            │
│ Creator: Accounting Automation Solutions                │
│ Updated: 1 week ago                                     │
│                                                         │
│ Automates:                                              │
│ ✓ Monthly rent reminders (email + SMS)                  │
│ ✓ Payment processing & verification                     │
│ ✓ Late payment escalation                               │
│ ✓ Receipt generation & delivery                         │
│ ✓ Accounting system sync (QuickBooks, Xero)             │
│ ✓ Financial reporting                                   │
│ ✓ Tax compliance documentation                          │
│                                                         │
│ Integrations: Stripe, PayPal, QuickBooks, Zoho Books   │
│ Estimated Setup Time: 25 minutes                        │
│ ROI: 50+ hours/month saved + 99.2% collection rate     │
│                                                         │
│ [Install] [View Details] [Reviews] [Documentation]     │
└─────────────────────────────────────────────────────────┘
```

## Step 3: Browse by Category

### Category: Property Management (15 workflows)

```
Property Management Workflows:

1. Property Lead Automation
   ⭐⭐⭐⭐⭐ 4.9/5 | 2,847 installs | Lead-to-tenant automation

2. Maintenance Request Ticketing
   ⭐⭐⭐⭐⭐ 4.8/5 | 634 installs | Request → Assignment → Completion

3. Rent Collection & Accounting
   ⭐⭐⭐⭐⭐ 4.9/5 | 1,203 installs | Monthly rent automation + sync

4. Property Listing Publisher
   ⭐⭐⭐⭐ 4.7/5 | 456 installs | MLS + social media automation

5. Tenant Communication Hub
   ⭐⭐⭐⭐ 4.6/5 | 892 installs | Multi-channel tenant notifications

6. Lease Document Automation
   ⭐⭐⭐⭐ 4.8/5 | 345 installs | Auto-generate, sign, and store leases

7. Security Deposit Tracking
   ⭐⭐⭐⭐ 4.5/5 | 234 installs | Deposit collection, interest, return

8. Property Inspection Workflow
   ⭐⭐⭐⭐ 4.7/5 | 289 installs | Move-in/move-out inspections

9. Vendor Management System
   ⭐⭐⭐⭐ 4.6/5 | 178 installs | Maintenance vendors + contract management

10. Tenant Application Screening
    ⭐⭐⭐⭐⭐ 4.8/5 | 567 installs | Credit check, background, approval

[Show More]
```

### Category: CRM Integration (12 workflows)

```
CRM Workflows:

1. Lead Scoring & Ranking
   ⭐⭐⭐⭐ 4.7/5 | 934 installs | AI-based lead qualification

2. Contact Auto-Sync
   ⭐⭐⭐⭐ 4.6/5 | 1,245 installs | Multi-source contact synchronization

3. Deal Pipeline Automation
   ⭐⭐⭐⭐ 4.7/5 | 678 installs | Stage-based actions and notifications

4. Email Campaign Manager
   ⭐⭐⭐⭐⭐ 4.8/5 | 2,103 installs | Email sequences + tracking

5. Customer Success Onboarding
   ⭐⭐⭐⭐ 4.6/5 | 456 installs | New customer automated sequence

[Show More]
```

### Category: Communications (8 workflows)

```
Communication Workflows:

1. Multi-Channel Notifications
   ⭐⭐⭐⭐ 4.7/5 | 1,678 installs | Email, SMS, Slack, push

2. Customer Support Ticketing
   ⭐⭐⭐⭐ 4.6/5 | 892 installs | Support request routing + responses

3. Team Alerts & Escalation
   ⭐⭐⭐⭐ 4.5/5 | 567 installs | Critical alert management

[Show More]
```

## Step 4: View Workflow Details

**Selected Workflow**: Property Lead Automation

```
═══════════════════════════════════════════════════════════
               PROPERTY LEAD AUTOMATION
═══════════════════════════════════════════════════════════

OVERVIEW:
⭐⭐⭐⭐⭐ 4.9/5 stars (847 reviews)
Category: Property Management → Lead Management
Creator: Real Estate Automation Team (Verified ✓)
Updated: 2 weeks ago | Version 3.2.1

2,847 ACTIVE INSTALLATIONS | 156,000+ LEADS PROCESSED

DESCRIPTION:
Complete workflow to convert property leads into tenants.
Handles form submission, CRM creation, qualification,
approval routing, and automated onboarding sequence.
Industry-best lead-to-tenant conversion rates.

═══════════════════════════════════════════════════════════

WHAT THIS WORKFLOW DOES:

1. Web Form Submission
   - Captures lead details via customizable form
   - Validates required fields
   - Stores in temp storage

2. CRM Lead Creation
   - Creates lead in Zoho CRM
   - Auto-categorizes by property interest
   - Assigns to property manager
   - Triggers initial workflow

3. Lead Qualification
   - Checks credit score requirements
   - Verifies income (if available)
   - Scores application automatically
   - Flags for manual review if needed

4. Approval Routing
   - Pre-approved leads: Auto-onboard
   - Needs review: Route to manager (timeout: 24h)
   - Rejected: Auto-notify applicant

5. Onboarding Automation
   - Create tenant account in portal
   - Generate lease documents
   - Schedule property walk-through
   - Create calendar events
   - Send welcome package (email/SMS)

6. Notifications
   - Property manager alerts
   - Tenant confirmations
   - Team Slack updates
   - Status tracking

7. Follow-up Tracking
   - Track document signing
   - Monitor move-in checklist
   - Schedule follow-ups
   - Request feedback

═══════════════════════════════════════════════════════════

TECHNICAL SPECIFICATIONS:

Trigger: Webhook (form submission) OR Manual OR Scheduled
Integrations: Zoho CRM, Zoho Mail, Google Sheets, Slack
Execution Time: 2-5 minutes per lead
Error Handling: Retry 3x, then escalate to support queue
Logs: Full audit trail, searchable

Prerequisites:
✓ Zoho CRM account (free tier supported)
✓ Zoho Mail access (uses your domain)
✓ Slack workspace (optional, for notifications)
✓ Google Sheets (optional, for reporting)

DATA REQUIREMENTS:

Input Fields:
- Full Name (required)
- Email Address (required)
- Phone Number (required)
- Property Interest (required)
- Move-in Date (required)
- Credit Score (optional)
- Annual Income (optional)
- Employment Status (optional)
- Desired Lease Length (optional)

Output Data:
- CRM Lead ID
- Application Status
- Approval Decision
- Onboarding Start Date
- Tenant Portal URL
- Document Status

═══════════════════════════════════════════════════════════

REVIEWS & RATINGS:

⭐⭐⭐⭐⭐ (482 reviews) "Game changer for our team"
"Reduced lead processing time from 3 days to 30 minutes.
Highly recommended!" - Sarah M., Property Manager

⭐⭐⭐⭐⭐ (156 reviews) "Outstanding support and updates"
"The workflow is constantly improving. Support team
is responsive and helpful." - John K., Property Company Owner

⭐⭐⭐⭐ (209 reviews) "Great with minor customizations"
"Works great out of the box. We customized for our
specific approval process." - Maria G., Real Estate Team

═══════════════════════════════════════════════════════════

INSTALLATION & SETUP:

Estimated Time: 15-20 minutes
Difficulty: Easy (pre-configured)

Setup Steps:
1. Click [Install] button below
2. Authorize Zoho CRM access
3. Authorize Zoho Mail access (optional)
4. Configure form fields
5. Customize approval settings
6. Test with sample lead
7. Activate workflow

No coding required. All configuration is visual.

═══════════════════════════════════════════════════════════

PRICING:

Free Tier: Up to 100 leads/month
Pro: $29/month, 1,000 leads/month, priority support
Enterprise: Custom pricing, unlimited leads, 24/7 support

Current Marketplace: INCLUDED with your plan

═══════════════════════════════════════════════════════════

[Install Now] [Configure] [Read Full Documentation] [Ask Questions]
```

## Step 5: Search & Filter Options

```
SEARCH & FILTER:

Search: _____________________ [Search]

Category:
  ☐ Property Management
  ☐ CRM Integration
  ☐ Communications
  ☐ Financial
  ☐ Data Sync
  ☐ All Categories

Sort By:
  ⦿ Trending (Most installed this month)
  ○ Newest (Recently added)
  ○ Highest Rated (4.8+ stars)
  ○ Most Reviewed
  ○ Most Customized

Filter:
  ☐ Show only verified/trusted
  ☐ Show only free workflows
  ☐ Show only enterprise-ready
  ☐ Show only with support
  ☐ Show my installed workflows

Results: Showing 1-10 of 47 matching workflows
```

## Step 6: Installation Confirmation

```
═══════════════════════════════════════════════════════════
           INSTALLATION CONFIRMATION
═══════════════════════════════════════════════════════════

WORKFLOW: Property Lead Automation v3.2.1

REQUIRED PERMISSIONS:
✓ Zoho CRM: Read/Write leads, contacts, deals
✓ Zoho Mail: Send emails from your account
○ Slack: Post notifications (optional)
○ Google Sheets: Write reports (optional)

FEATURES INCLUDED:
✓ Web form builder (customizable)
✓ CRM lead creation
✓ Lead scoring AI
✓ Approval routing
✓ Automated onboarding
✓ Multi-channel notifications
✓ Document generation
✓ Activity logging
✓ Performance dashboard
✓ 24/7 technical support

WHAT WILL BE CREATED:
- 1 webhook endpoint (for form submissions)
- 1 CRM form integration
- 15 automation rules
- 8 email templates
- 2 Slack notification templates
- 1 reporting dashboard

INSTALLATION AGREEMENT:
By installing, you accept:
- Privacy policy and data handling
- Permission to use your CRM data for workflow
- Automatic updates to workflow (backward compatible)

[Authorize & Install] [View Permissions] [Cancel]
```

## Step 7: Post-Installation

```
═══════════════════════════════════════════════════════════
         WORKFLOW INSTALLED SUCCESSFULLY!
═══════════════════════════════════════════════════════════

✓ Property Lead Automation v3.2.1 is now active

NEXT STEPS:

1. Review and Customize:
   /automation:configure lead-automation

2. Test with Sample Data:
   /automation:test-workflow lead-automation --dry-run

3. Set Up Monitoring:
   /automation:monitor lead-automation

4. View Performance Dashboard:
   /automation:dashboard lead-automation

5. View Webhook URL:
   Webhook endpoint created and ready
   POST https://api.automation-hub.app/webhook/lead-form-abc123

   Add this to your landing page form action:
   <form action="https://api.automation-hub.app/webhook/lead-form-abc123"
         method="POST">

DOCUMENTATION:
- Getting Started Guide
- Configuration Options
- Customization Examples
- Troubleshooting Guide
- API Documentation

SUPPORT:
- Email: support@automation-team.com
- Chat: Available in-app
- Knowledge Base: 150+ articles
- Community: Active Slack channel

═══════════════════════════════════════════════════════════
```

## Popular Workflow Categories

### Property Management (15 workflows)

- Lead automation, maintenance ticketing, rent collection, inspections

### CRM Integration (12 workflows)

- Lead scoring, contact sync, deal pipeline, email campaigns

### Communications (8 workflows)

- Multi-channel alerts, support ticketing, team notifications

### Financial (10 workflows)

- Invoice automation, expense management, accounting sync

### Data Integration (9 workflows)

- Data sync, report generation, backup, ETL processes

### HR & Team Management (7 workflows)

- Employee onboarding, time tracking, approvals

---

**Uses**: n8n-mcp, automation-marketplace-agent
**Model**: Haiku (fast browsing and installation)
**Typical Browsing Time**: 5-15 minutes
**Installation Time**: 15-30 minutes per workflow
