---
description: Create a new lead in Zoho CRM with human approval workflow
argument-hint: <lead details or interactive>
model: claude-sonnet-4-5-20250929
allowed-tools: AskUserQuestion
---

Create a new lead in Zoho CRM with the following workflow:

## Step 1: Gather Lead Information

If lead details were provided in $ARGUMENTS, parse them.
If not provided or incomplete, use **AskUserQuestion** tool to collect:

**Required Fields:**

- Company Name
- Contact First Name
- Contact Last Name
- Email Address
- Phone Number

**Optional Fields:**

- Job Title
- Industry
- Lead Source
- Annual Revenue
- Number of Employees
- Description/Notes

Present the questions in a user-friendly format that collects all necessary information.

## Step 2: Enrich Lead Data

Based on the provided information:

1. **Industry Classification**: If industry not provided, suggest based on company name
2. **Lead Scoring**: Calculate initial lead score (1-100) based on:
   - Company size (revenue + employees)
   - Contact seniority (job title)
   - Lead source quality
3. **Lead Status**: Recommend initial status:
   - "New" - Just entered system
   - "Contacted" - If follow-up planned
   - "Qualified" - If meets qualification criteria
4. **Assignment**: Recommend team member based on:
   - Industry expertise
   - Geographic territory
   - Current workload

## Step 3: Display Lead Preview

Show a formatted preview of the lead to be created:

```
═══════════════════════════════════════════════════
           ZOHO CRM LEAD PREVIEW
═══════════════════════════════════════════════════

COMPANY INFORMATION:
- Company Name: [name]
- Industry: [industry]
- Annual Revenue: [revenue]
- Employees: [count]

CONTACT INFORMATION:
- Name: [First] [Last]
- Title: [job title]
- Email: [email]
- Phone: [phone]

LEAD DETAILS:
- Source: [source]
- Status: [status]
- Lead Score: [score]/100
- Assigned To: [owner]
- Description: [notes]

CUSTOM FIELDS:
- [Any additional fields]

═══════════════════════════════════════════════════
```

## Step 4: Request Approval

Use **AskUserQuestion** tool to request approval:

**Question**: "Ready to create this lead in Zoho CRM?"

**Options**:

1. **"Approve & Create"** - Proceed with lead creation
2. **"Edit Details"** - Modify information before creating
3. **"Cancel"** - Do not create lead

## Step 5: Execute Based on Approval

**If Approved**:

1. Simulate Zoho CRM API call (since actual integration not yet built):

   ```
   POST https://www.zohoapis.com/crm/v2/Leads
   Headers:
     Authorization: Zoho-oauthtoken {token}
   Body: {lead_data}
   ```

2. Display success confirmation:

   ```
   ✓ Lead Created Successfully!

   Lead ID: LEAD-12345
   Company: [Company Name]
   Contact: [First Last]
   Status: [Status]
   Assigned To: [Owner]

   Next Steps:
   - [ ] Send welcome email (/zoho/send-email)
   - [ ] Schedule follow-up call
   - [ ] Add to nurture campaign
   ```

3. Offer follow-up actions via **AskUserQuestion**:
   - Send welcome email now?
   - Schedule task for follow-up?
   - Add to email campaign?

**If Edit Requested**:

1. Return to Step 1 with current data pre-filled
2. Allow modifications to any fields
3. Return to Step 3 (preview) → Step 4 (approval)

**If Cancelled**:

1. Confirm cancellation
2. Display message: "Lead creation cancelled. No changes made to Zoho CRM."
3. Ask if they want to save draft for later

## Step 6: Log the Transaction

Document the lead creation for audit trail:

- Timestamp
- User who created
- Lead details
- Approval status
- API response (success/error)

## Quality Checklist

Before requesting approval, verify:

- [ ] All required fields are populated
- [ ] Email format is valid
- [ ] Phone format is correct
- [ ] Company name is not duplicate (check for existing)
- [ ] Lead score calculation is reasonable
- [ ] Assignment recommendation makes sense
- [ ] No obvious data quality issues

## Error Handling

If any issues occur:

1. Display clear error message
2. Suggest corrective actions
3. Offer retry options
4. Log error for troubleshooting

## Notes

- **IMPORTANT**: This command currently simulates Zoho API integration. Actual API implementation will be added in Phase 4.
- All approvals are logged for compliance and audit purposes
- Lead data follows Zoho CRM standard field structure
- Custom fields can be added based on your Zoho CRM configuration

## Example Usage

```
/create-lead
# Interactive mode - will ask for all details

/create-lead Company: Acme Corp, Contact: John Smith, Email: john@acme.com
# Partial details provided - will ask for missing fields
```
