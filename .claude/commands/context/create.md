---
description: Create a new business context with guided setup
argument-hint: "<context-name> [--type property|consulting|startup|personal] [--template standard|property|startup|consulting] [--quick]"
model: claude-3-5-haiku-20241022
allowed-tools: ["Read", "Write", "Bash", "AskUserQuestion"]
---

# Create New Business Context

Set up a new business context with guided configuration, templates, and automatic integration setup.

## What This Command Does

Quickly establish a new business context with everything you need:

- **Guided Setup**: Step-by-step interactive configuration
- **Templates**: Pre-built context structures for common business types
- **Integration Ready**: Automatic Zoho CRM, Google Calendar, and other setup
- **Data Structure**: Automatic folder and file creation
- **Quick Mode**: Fast setup for experienced users (--quick flag)
- **Validation**: Automatic checks to ensure valid configuration

## Why This Matters for Growing Operators

As you add new properties, clients, or projects, you need a fast way to set up new contexts:

- Don't manually create folders and configs
- Don't forget to connect integrations
- Don't lose time on setup - get productive in minutes
- Don't miss critical configuration steps

**Time Saved**: 15-30 minutes per new context setup (vs manual approach)

## Usage

```bash
# Interactive guided setup for new property
/context:create my-new-property --type property

# Create using template with prompts
/context:create client-xyz --type consulting --template consulting

# Fast setup for experienced users
/context:create rental-unit-5 --type property --quick

# Personal finance context
/context:create personal-finances --type personal

# Startup project context
/context:create saas-alpha --type startup --template startup

# From existing context (copy and modify)
/context:create project-2 --type startup --from startup-project
```

## Setup Process

### Interactive Mode (Default)

```
Creating new business context...

=== CONTEXT BASICS ===

1. Context Name
   [Pre-filled: my-new-property]
   Name format: lowercase, hyphens OK (e.g., client-acme, property-123-main)

2. Business Type (Select one)
   ○ Property Management (rental properties, commercial real estate)
   ○ Consulting/Agency (client work, retainers, projects)
   ○ Startup/Side Business (SaaS, products, apps)
   ○ Personal (finances, admin, learning)
   Selected: Property Management

3. Business Name
   What do you call this business/property?
   [e.g., "123 Main Street Apartments"]
   Entered: 456 Elm Street - 5 Unit Apartment

=== PROPERTY-SPECIFIC INFO ===

4. Property Details
   Address:          456 Elm Street, Denver, CO 80202
   Units:            5
   Property Type:    Apartment Complex
   Acquisition Date: 2024-06-15
   Total Value:      $875,000
   Mortgage/Loan:    Yes - $625,000 @ 4.25%

=== FINANCIAL SETUP ===

5. Financial Configuration
   Currency:         USD
   Tax Rate:         7.62% (Colorado)
   Fiscal Year:      Calendar (Jan-Dec)
   Banking:          QuickBooks connected
   Accounting:       QuickBooks Online

=== INTEGRATION SETUP ===

6. Connect Integrations
   ✓ Zoho CRM (Ready to connect)
     → Create contact for this property
     → Set up pipeline for leads/tenants

   ✓ Google Calendar (Ready to connect)
     → Create calendar: "456 Elm St - Schedule"
     → Add to main property calendar

   ✓ QuickBooks (Ready to connect)
     → Create account structure
     → Set up income/expense categories

   Optional: Stripe (Payments), Slack (Notifications)

=== INITIAL DATA ===

7. Ready to Create Context?
   Context Name:     456-elm-street
   Business Type:    Property Management
   Business Name:    456 Elm Street - 5 Unit Apartment
   Location:         Denver, CO
   Units:            5
   Integrations:     Zoho CRM, Google Calendar, QuickBooks

   Create now? (y/n)
   Confirmed: Yes

=== CREATION COMPLETE ===

✓ Context created successfully!

Context Details:
  Name:             456-elm-street
  Type:             Property Management
  ID:               PROP-00156
  Created:          2025-01-25 14:45:00 UTC
  Status:           Ready

Integrations Created:
  ✓ Zoho CRM entry created (ID: 98765)
  ✓ Google Calendar created (456 Elm St - Schedule)
  ✓ QuickBooks account structure created

Files Created:
  ✓ ~/.claude/contexts/456-elm-street.json
  ✓ ~/properties/456-elm-street/ (working directory)
  ✓ ~/properties/456-elm-street/docs/ (documents)
  ✓ ~/properties/456-elm-street/finance/ (financial records)
  ✓ ~/properties/456-elm-street/tenants/ (tenant files)
  ✓ ~/properties/456-elm-street/maintenance/ (maintenance logs)

Next Steps:
  1. /context:switch 456-elm-street    (Start working in this context)
  2. /property:setup-tenants           (Add tenant information)
  3. /finance:setup-accounts           (Configure financial accounts)
  4. /property:add-maintenance         (Create maintenance schedule)

Ready to switch to new context? (y/n)
```

### Quick Mode Output

```
Creating context: my-new-property
Type: Property | Template: property

Using property template...
✓ Context file created
✓ Directory structure created
✓ Zoho CRM entry created (ID: 98765)
✓ Google Calendar created
✓ Configuration saved

Context ready. Next: /context:switch my-new-property
```

## Context Templates

### Property Management Template

```json
{
  "name": "property-name",
  "type": "property",
  "business_name": "Property Name",
  "created": "2025-01-25T14:45:00Z",
  "state": {
    "environment_vars": {
      "PROPERTY_ADDRESS": "",
      "PROPERTY_UNITS": 0,
      "PROPERTY_TYPE": "",
      "MONTHLY_TARGET_REVENUE": 0,
      "MANAGEMENT_TYPE": "self-managed",
      "MORTGAGE_AMOUNT": 0,
      "MORTGAGE_RATE": 0
    },
    "active_projects": [],
    "todo_list": [
      "Add tenant information",
      "Configure maintenance schedule",
      "Set up financial accounts",
      "Create lease templates"
    ]
  },
  "integrations": {
    "zoho_crm": "auto-setup",
    "google_calendar": "auto-setup",
    "quickbooks": "auto-setup"
  },
  "metadata": {
    "folder_structure": [
      "docs/",
      "tenants/",
      "finance/",
      "maintenance/",
      "leases/"
    ]
  }
}
```

### Consulting/Agency Template

```json
{
  "name": "client-name",
  "type": "consulting",
  "business_name": "Client Name",
  "created": "2025-01-25T14:45:00Z",
  "state": {
    "environment_vars": {
      "CLIENT_NAME": "",
      "CLIENT_INDUSTRY": "",
      "CONTRACT_VALUE": 0,
      "CONTRACT_TYPE": "retainer",
      "MONTHLY_HOURS": 0,
      "PROJECT_MANAGER": ""
    },
    "active_projects": [],
    "todo_list": [
      "Create project list",
      "Define deliverables",
      "Set up communication channels",
      "Configure billing cycles"
    ]
  },
  "integrations": {
    "zoho_crm": "auto-setup",
    "google_calendar": "auto-setup",
    "slack": "optional"
  },
  "metadata": {
    "folder_structure": [
      "contracts/",
      "deliverables/",
      "communications/",
      "invoices/",
      "project-files/"
    ]
  }
}
```

### Startup/Product Template

```json
{
  "name": "product-name",
  "type": "startup",
  "business_name": "Product Name",
  "created": "2025-01-25T14:45:00Z",
  "state": {
    "environment_vars": {
      "PRODUCT_NAME": "",
      "PRODUCT_STAGE": "mvp",
      "LAUNCH_DATE": "",
      "TARGET_MARKET": "",
      "TEAM_SIZE": 0
    },
    "active_projects": [],
    "todo_list": [
      "Define MVP features",
      "Create development roadmap",
      "Set up team structure",
      "Plan launch strategy"
    ]
  },
  "integrations": {
    "zoho_crm": "auto-setup",
    "google_calendar": "auto-setup",
    "github": "optional"
  },
  "metadata": {
    "folder_structure": [
      "planning/",
      "development/",
      "marketing/",
      "financials/",
      "team/"
    ]
  }
}
```

### Personal/Admin Template

```json
{
  "name": "personal",
  "type": "personal",
  "business_name": "Personal",
  "created": "2025-01-25T14:45:00Z",
  "state": {
    "environment_vars": {
      "PRIMARY_LOCATION": "",
      "TAX_STATUS": "individual",
      "FISCAL_YEAR_START": "01-01"
    },
    "active_projects": [],
    "todo_list": [
      "Organize financial documents",
      "Set up budget tracking",
      "Create goal milestones",
      "Schedule quarterly reviews"
    ]
  },
  "integrations": {
    "google_calendar": "auto-setup"
  },
  "metadata": {
    "folder_structure": [
      "finance/",
      "tax/",
      "health/",
      "learning/",
      "goals/"
    ]
  }
}
```

## Step-by-Step Execution

### 1. Validate Context Name

```bash
# Check name format and uniqueness
if [[ ! $context_name =~ ^[a-z0-9-]+$ ]]; then
  echo "Invalid name. Use lowercase letters, numbers, hyphens."
  exit 1
fi

if [ -f ~/.claude/contexts/${context_name}.json ]; then
  echo "Context already exists!"
  exit 1
fi
```

### 2. Determine Context Type

```bash
# If not specified, ask user
# If --type specified, validate
# If --template specified, infer type from template
```

### 3. Load Template

```bash
# Load base template for type
# If --from specified, use existing context as base
# Apply any customizations from arguments
```

### 4. Interactive Configuration (unless --quick)

```bash
# Present questions in order:
# 1. Business name / Description
# 2. Location / Geographic details
# 3. Financial setup (currency, tax rate, etc)
# 4. Integration preferences
# 5. Initial data
```

### 5. Create Directory Structure

```bash
# Create home directory: ~/[category]/[context-name]/
# Create subdirectories based on type
# Initialize empty files for key documents
```

### 6. Create Context File

```bash
# Save to ~/.claude/contexts/${context_name}.json
# Include all configuration and metadata
# Set timestamps and status
```

### 7. Setup Integrations

```bash
# For each enabled integration:
# - Create entry in Zoho CRM
# - Create Google Calendar
# - Create QuickBooks account structure
# - Configure API connections
```

### 8. Generate Initial Todo

```bash
# Create context-specific todo list
# Based on type (properties need tenant setup, consulting needs contract setup, etc)
# Mark as pending
```

### 9. Confirm and Offer Next Steps

```bash
# Show summary of what was created
# Offer to switch to new context immediately
# Suggest typical next actions for this context type
```

## Context File Structure

```json
{
  "name": "context-name",
  "id": "CTX-00001",
  "type": "property|consulting|startup|personal",
  "business_name": "Full Business Name",
  "description": "Optional description",
  "created": "ISO-8601 timestamp",
  "last_active": "ISO-8601 timestamp",
  "status": "active|paused|archived",
  "location": {
    "address": "street address",
    "city": "city",
    "state": "state",
    "country": "country",
    "timezone": "America/Chicago"
  },
  "state": {
    "environment_vars": {},
    "active_projects": [],
    "open_files": [],
    "todo_list": [],
    "notes": ""
  },
  "integrations": {
    "zoho_crm": "enabled|disabled",
    "google_calendar": "enabled|disabled",
    "quickbooks": "enabled|disabled",
    "slack": "enabled|disabled"
  },
  "metadata": {
    "created_by": "user",
    "version": "1.0",
    "folder_structure": []
  }
}
```

## Business Value

**Setup Time**:

- Manual setup: 30-45 minutes
- With this command: 3-5 minutes (interactive) or <1 minute (quick)
- **Saves**: 25-40 minutes per new context

**Error Prevention**:

- Guided setup prevents missing steps
- Automatic integration connection
- Validated configuration
- **Impact**: 100% setup success rate

**Productivity**:

- New contexts ready to use immediately
- No "wait, what should I set up?" paralysis
- Templates ensure consistency
- **Improvement**: 50% faster to first productive work

**Cost**:

- Reduces onboarding time for new properties/clients
- Consistent structure across all contexts
- **Value**: $500+ per new business unit

## Success Metrics

✅ Context created within 1-2 seconds (quick mode)
✅ All required fields captured
✅ Directory structure created correctly
✅ All enabled integrations configured
✅ Context file is valid JSON
✅ Initial todo list created
✅ User can immediately switch and work

## Related Commands

- `/context:switch` - Switch to new context and start working
- `/context:list` - See all contexts including new one
- `/context:current` - View new context details
- `/property:setup-tenants` - Add tenant data (properties)
- `/client:setup-contract` - Configure client details (consulting)

## Notes

**Validation**: All inputs validated against context schema before creation.

**Rollback**: If setup fails partway, automatic cleanup and option to retry.

**Customization**: Templates can be extended with project-specific configurations.

**Security**: Integration setup prompts for credentials in secure manner; never logs sensitive data.

---

*Set up a new business context in seconds, not hours. Templates + guided setup = consistent, complete contexts every time.*
