---
description: Send email via Zoho Mail with approval workflow and template support
argument-hint: <recipient> [template-name]
model: claude-sonnet-4-5-20250929
allowed-tools: AskUserQuestion, Read
---

Send email via Zoho Mail with the following workflow:

## Step 1: Parse Input & Determine Mode

**Input Options**:

- `/send-email john@example.com welcome` - Recipient + template name
- `/send-email john@example.com` - Recipient only (interactive compose)
- `/send-email` - Fully interactive mode

Parse $ARGUMENTS to determine:

- Recipient email(s)
- Template to use (if specified)
- Compose mode (template vs custom)

## Step 2: Recipient Management

Use **AskUserQuestion** to collect/confirm recipients:

**Single Recipient Mode**:

- Email address
- Display name (optional)
- Contact type (Lead, Contact, Vendor, Other)

**Multiple Recipients** (if requested):

- Primary recipients (To:)
- CC recipients
- BCC recipients

**Validation**:

- Verify email format
- Check for common typos
- Warn if sending to multiple recipients
- Confirm if sending outside organization

## Step 3: Email Content Creation

### Option A: Use Template (if template name provided)

1. **Check for template file**:
   - Look in `/templates/email/[template-name].md`
   - If found, read template content
   - If not found, list available templates

2. **Template Structure**:

   ```markdown
   ---
   subject: [Email subject with {{merge fields}}]
   category: [welcome|followup|newsletter|campaign]
   ---

   # Email Body

   Hi {{firstName}},

   [Email content with {{merge fields}}]

   Best regards,
   {{senderName}}
   ```

3. **Merge Fields**: Use **AskUserQuestion** to collect values for merge fields:
   - {{firstName}}, {{lastName}}, {{company}}, etc.
   - Pre-fill from Zoho CRM if recipient is a known contact/lead

### Option B: Custom Email (if no template)

Use **AskUserQuestion** to collect:

- **Subject line**: Clear, compelling subject
- **Email body**: Compose email content
- **Format**: Plain text or HTML
- **Attachments**: Any files to attach (list paths)

Provide AI assistance:

- Suggest subject line based on context
- Help draft professional email body
- Recommend best practices (clear CTA, personalization, etc.)

## Step 4: Email Enhancement

Enhance the email with:

1. **Personalization**:
   - Use recipient's first name
   - Reference their company if known
   - Customize based on lead source/status

2. **Professional Formatting**:
   - Proper greeting
   - Clear structure (paragraphs, spacing)
   - Professional signature
   - Unsubscribe link (if campaign email)

3. **Quality Check**:
   - Grammar and spelling check
   - Tone analysis (professional, friendly, urgent, etc.)
   - Length optimization (not too long/short)
   - Mobile-friendly formatting

4. **Compliance**:
   - CAN-SPAM compliance for campaigns
   - GDPR compliance for EU recipients
   - Unsubscribe mechanism included

## Step 5: Email Preview

Display comprehensive preview:

```
═══════════════════════════════════════════════════
              EMAIL PREVIEW
═══════════════════════════════════════════════════

FROM: [your-email@domain.com] ([Your Name])
TO: [recipient@email.com] ([Recipient Name])
CC: [cc-recipients if any]
BCC: [bcc-recipients if any]

SUBJECT: [Email Subject Line]

───────────────────────────────────────────────────

[Email Body Content
with formatting preserved
and merge fields populated]

───────────────────────────────────────────────────

ATTACHMENTS: [list attachments if any]

TRACKING:
- Open tracking: Enabled
- Click tracking: Enabled
- Category: [category]
- Tags: [tags]

═══════════════════════════════════════════════════

QUALITY SCORE: [X]/100
✓ Professional tone
✓ Clear call-to-action
✓ Mobile-friendly
✓ Compliance verified
⚠ [Any warnings or suggestions]

ESTIMATED METRICS:
- Predicted open rate: ~X%
- Predicted click rate: ~X%
- Read time: ~X seconds
```

## Step 6: Request Approval

Use **AskUserQuestion** with options:

**Question**: "Ready to send this email via Zoho Mail?"

**Options**:

1. **"Send Now"** - Send immediately
2. **"Schedule Send"** - Choose date/time to send
3. **"Save as Draft"** - Save to drafts for later
4. **"Edit Email"** - Modify content
5. **"Cancel"** - Don't send

If "Schedule Send" selected:

- Use **AskUserQuestion** to collect:
  - Send date
  - Send time
  - Timezone

## Step 7: Execute Based on Approval

**If "Send Now" Approved**:

1. Simulate Zoho Mail API call:

   ```
   POST https://mail.zoho.com/api/accounts/{accountId}/messages
   Headers:
     Authorization: Zoho-oauthtoken {token}
   Body: {
     "fromAddress": "sender@domain.com",
     "toAddress": "recipient@email.com",
     "ccAddress": "",
     "bccAddress": "",
     "subject": "Subject",
     "content": "Email body",
     "mailFormat": "html",
     "attachments": []
   }
   ```

2. Display success confirmation:

   ```
   ✓ Email Sent Successfully!

   To: [Recipient Name] <recipient@email.com>
   Subject: [Subject]
   Sent at: [Timestamp]
   Message ID: MSG-12345

   Tracking:
   - View email status: [link]
   - Open/click tracking enabled
   - Category: [category]

   Next Steps:
   - [ ] Log activity in CRM
   - [ ] Schedule follow-up
   - [ ] Monitor email engagement
   ```

3. Offer follow-up actions:
   - Log this email in Zoho CRM?
   - Create follow-up task?
   - Add to email sequence?

**If "Schedule Send" Approved**:

1. Confirm scheduled time
2. Save email to send queue
3. Display confirmation with cancel instructions

**If "Save as Draft"**:

1. Save to Zoho Mail drafts
2. Provide draft ID for later access
3. Offer to set reminder to complete

**If "Edit Email"**:

1. Return to Step 3
2. Pre-fill with current content
3. Allow modifications

**If "Cancel"**:

1. Confirm cancellation
2. Ask if they want to save draft anyway

## Step 8: CRM Integration

After successful send, offer to log in Zoho CRM:

1. **Link to Contact/Lead**:
   - Search for recipient in CRM
   - Create activity record
   - Update last contact date

2. **Activity Details**:
   - Type: Email
   - Subject: [email subject]
   - Date/time sent
   - Content snapshot
   - Attachments list

3. **Update Lead/Contact**:
   - Lead Status: "Contacted" (if was "New")
   - Last Activity: Today
   - Notes: Email sent summary

## Quality Checklist

Before requesting approval, verify:

- [ ] Recipient email(s) valid
- [ ] Subject line compelling (30-50 characters ideal)
- [ ] Email body clear and concise
- [ ] Call-to-action included
- [ ] Professional tone maintained
- [ ] Personalization included
- [ ] Grammar/spelling correct
- [ ] Compliance requirements met (unsubscribe, etc.)
- [ ] Attachments included if referenced
- [ ] Mobile-friendly formatting
- [ ] No sensitive information exposed (if BCC recipients)

## Email Templates Library

Common templates available:

- **welcome** - Welcome new leads/contacts
- **followup** - Follow-up after meeting/call
- **newsletter** - Regular company updates
- **promotion** - Product/service promotions
- **event-invite** - Event invitations
- **thankyou** - Thank you messages
- **survey** - Feedback/survey requests

To create new template:

1. Create file `/templates/email/[name].md`
2. Use frontmatter for metadata
3. Include merge fields in {{curly braces}}

## Error Handling

Common errors and solutions:

**Invalid Email**:

- Show which email(s) are invalid
- Suggest corrections
- Allow re-entry

**Attachment Not Found**:

- List missing attachments
- Offer to continue without them
- Allow file selection

**Template Not Found**:

- List available templates
- Offer to create new template
- Allow custom email composition

**API Error**:

- Display clear error message
- Suggest retry options
- Save draft automatically
- Log error for troubleshooting

## Best Practices

**Subject Lines**:

- Keep under 50 characters
- Create urgency without being spammy
- Personalize when possible
- A/B test different versions

**Email Body**:

- Start with recipient's name
- Clear purpose in first sentence
- One primary call-to-action
- Keep under 200 words for cold emails
- Use short paragraphs (2-3 sentences)

**Timing**:

- Best send times: Tue-Thu, 10 AM-2 PM
- Avoid Mondays and Fridays
- Consider recipient's timezone

**Follow-up**:

- Wait 3-5 days before follow-up
- Reference previous email
- Add new value in follow-up
- Max 3 follow-ups before moving on

## Notes

- **IMPORTANT**: This command currently simulates Zoho Mail API. Actual integration will be added in Phase 4.
- All emails are logged for compliance and audit
- Tracking data available via Zoho Mail dashboard
- Templates support full markdown formatting

## Example Usage

```
/send-email john@acme.com welcome
# Send welcome email using template

/send-email jane@company.com
# Compose custom email interactively

/send-email
# Fully interactive mode - choose recipient and compose
```
