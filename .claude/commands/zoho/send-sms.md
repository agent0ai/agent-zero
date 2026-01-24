---
description: Send SMS via Zoho CRM/SMS with approval workflow and compliance checks
argument-hint: <phone-number> [message or template]
model: claude-sonnet-4-5-20250929
allowed-tools: AskUserQuestion
---

Send SMS via Zoho SMS system with the following workflow:

## Step 1: Parse Input & Collect Details

**Input Options**:

- `/send-sms +1234567890 "Your message here"` - Phone + message
- `/send-sms +1234567890 appointment-reminder` - Phone + template
- `/send-sms` - Fully interactive mode

Use **AskUserQuestion** to collect missing information:

- Phone number(s)
- Message content or template name
- Send timing (immediate or scheduled)

## Step 2: Phone Number Validation

Validate and format phone numbers:

1. **Format Check**:
   - Accept formats: +1234567890, (123) 456-7890, 123-456-7890
   - Normalize to E.164 format: +1234567890
   - Validate country code

2. **Duplicate Check**:
   - Remove duplicate numbers if sending to multiple
   - Warn if number appears multiple times

3. **Opt-In Verification**:
   - ⚠️ **CRITICAL**: Verify recipient has opted in to receive SMS
   - Check against opt-in database
   - Display opt-in status and date
   - **BLOCK** if no opt-in consent exists

4. **Do-Not-Contact Check**:
   - Check against DNC list
   - Block if number is on DNC list
   - Display warning for flagged numbers

**If Opt-In Status Unknown**:

```
⚠️ OPT-IN CONSENT VERIFICATION REQUIRED

Phone: +1234567890
Status: Unknown

You MUST verify consent before sending SMS.

Has this recipient opted in to receive SMS messages?
1. Yes - Has explicit opt-in consent
2. No - No consent, do not send
3. Check CRM - Look up in Zoho CRM records
```

## Step 3: Message Composition

### Option A: Use Template

**Common SMS Templates**:

- `appointment-reminder` - Appointment reminders
- `order-confirmation` - Order confirmations
- `shipping-update` - Shipping notifications
- `payment-reminder` - Payment reminders
- `event-reminder` - Event reminders
- `verification-code` - 2FA/verification codes
- `welcome` - Welcome new customers
- `followup` - Follow-up after service

**Template Structure**:

```
Template: appointment-reminder
Length: 145 characters (1 SMS segment)

Hi {{firstName}}, reminder: {{appointmentType}} appointment on {{date}} at {{time}}. Reply CONFIRM or call {{phone}}. Reply STOP to opt out.
```

Use **AskUserQuestion** to collect template merge fields.

### Option B: Custom Message

Use **AskUserQuestion** to collect message content.

Provide AI assistance:

- Draft professional SMS message
- Optimize for character count
- Ensure clarity and proper tone
- Include call-to-action

## Step 4: Message Optimization

Optimize the message for SMS:

1. **Character Count Analysis**:
   - Standard SMS: 160 characters = 1 segment
   - With special chars (émojis): 70 characters = 1 segment
   - Calculate total segments needed
   - Warn if multiple segments (higher cost)

2. **Cost Calculation**:
   - Number of recipients × Number of segments
   - Display total cost estimate
   - Compare template vs custom message costs

3. **Compliance Requirements**:
   - Include opt-out instructions: "Reply STOP to opt out"
   - Include sender identification (if required by regulation)
   - Avoid prohibited content (loans, cannabis, etc.)
   - Respect quiet hours (no sends 9 PM - 8 AM recipient local time)

4. **Message Enhancement**:
   - Add personalization (first name)
   - Include clear call-to-action
   - Add link shortening if URL included
   - Ensure mobile-friendly

5. **Quality Checks**:
   - No excessive CAPS or exclamation marks!!!
   - Professional tone maintained
   - Clear and concise
   - No spam trigger words

## Step 5: Message Preview

Display comprehensive preview:

```
═══════════════════════════════════════════════════
              SMS PREVIEW
═══════════════════════════════════════════════════

TO: +1 (234) 567-8900
    [Contact Name from CRM]
    ✓ Opt-in verified: [Date]
    ✓ Not on DNC list

MESSAGE (145/160 characters - 1 segment):
───────────────────────────────────────────────────
Hi John, reminder: Dental appointment on Jan 15 at
2:00 PM. Reply CONFIRM or call (555) 123-4567.
Reply STOP to opt out.
───────────────────────────────────────────────────

DETAILS:
- Segments: 1 (standard rate)
- Cost per SMS: $0.01
- Total cost: $0.01 (1 recipient × 1 segment)
- Estimated delivery: <2 seconds
- Template: appointment-reminder

COMPLIANCE:
✓ Opt-in consent verified
✓ Opt-out instructions included
✓ Sender identified
✓ Quiet hours respected (sending at [current time])
✓ No prohibited content
✓ Professional tone

SENDING FROM: [Your Business Name]
CAMPAIGN: [Campaign name if part of campaign]

═══════════════════════════════════════════════════

QUALITY SCORE: 95/100
✓ Personalized
✓ Clear call-to-action
✓ Under 160 characters
✓ Compliance verified
⚠ Consider adding urgency ("today" vs "Jan 15")
```

## Step 6: Request Approval

Use **AskUserQuestion** with options:

**Question**: "Ready to send this SMS via Zoho?"

**Options**:

1. **"Send Now"** - Send immediately
2. **"Schedule Send"** - Choose date/time
3. **"Edit Message"** - Modify content
4. **"Test Send"** - Send test to your number first
5. **"Cancel"** - Don't send

**If "Schedule Send"** selected:

- Collect send date/time
- Verify quiet hours compliance
- Consider recipient's timezone

**If "Test Send"** selected:

- Send to your own number first
- Review actual SMS appearance
- Then approve final send

## Step 7: Execute Based on Approval

**If "Send Now" Approved**:

1. Simulate Zoho SMS API call:

   ```
   POST https://www.zohoapis.com/crm/v2/functions/sendsms/actions/execute
   Headers:
     Authorization: Zoho-oauthtoken {token}
   Body: {
     "to": "+1234567890",
     "message": "SMS content",
     "from": "BusinessName",
     "campaign_id": "CAMP-123"
   }
   ```

2. Display success confirmation:

   ```
   ✓ SMS Sent Successfully!

   To: +1 (234) 567-8900 ([Contact Name])
   Segments: 1
   Cost: $0.01
   Sent at: [Timestamp]
   Message ID: SMS-12345

   Delivery Status: Sent (delivery confirmation pending)

   Tracking:
   - View delivery status: [link]
   - Track engagement: [link]
   - Campaign: [campaign name]

   Next Steps:
   - [ ] Log activity in CRM
   - [ ] Monitor delivery status
   - [ ] Track response rate
   - [ ] Schedule follow-up if no response
   ```

3. Offer follow-up actions:
   - Log this SMS in Zoho CRM?
   - Create follow-up task if no response in X days?
   - Add to SMS campaign sequence?

**If "Schedule Send" Approved**:

1. Confirm scheduled time (with timezone)
2. Verify quiet hours compliance
3. Save to send queue
4. Display confirmation with cancel instructions

**If "Edit Message"**:

1. Return to Step 3
2. Pre-fill current content
3. Allow modifications
4. Re-validate and preview

**If "Test Send"**:

1. Ask for test number
2. Send test SMS
3. Wait for confirmation
4. Return to approval step

**If "Cancel"**:

1. Confirm cancellation
2. Ask if they want to save as draft

## Step 8: CRM Integration & Logging

After successful send:

1. **Log in Zoho CRM**:
   - Link to Contact/Lead record
   - Create SMS activity
   - Update last contact date
   - Log message content
   - Record delivery status

2. **Update Contact Record**:
   - Last SMS sent: [Date/time]
   - SMS engagement score: [calculated]
   - Preferred contact method: [if responds]

3. **Campaign Tracking** (if part of campaign):
   - Total sent
   - Delivery rate
   - Response rate
   - Opt-out rate
   - Cost per engagement

## Quality Checklist

Before requesting approval, verify:

- [ ] Phone number(s) valid and formatted correctly
- [ ] **Opt-in consent verified** (CRITICAL - legal requirement)
- [ ] Not on Do-Not-Contact list
- [ ] Message under 160 chars (or intentionally multi-segment)
- [ ] Opt-out instructions included
- [ ] Sender identified
- [ ] Professional tone
- [ ] Clear call-to-action
- [ ] Respects quiet hours (8 AM - 9 PM recipient timezone)
- [ ] No prohibited content
- [ ] Cost calculated and acceptable
- [ ] Personalization included (if applicable)

## Compliance & Regulations

**TCPA Compliance** (US):

- ✓ Prior express written consent required
- ✓ Opt-out mechanism (STOP, END, CANCEL, UNSUBSCRIBE, QUIT)
- ✓ Quiet hours: 8 AM - 9 PM recipient local time
- ✓ Clear sender identification
- ⚠️ Violations: $500-$1,500 per message

**GDPR Compliance** (EU):

- ✓ Explicit consent documented
- ✓ Right to withdraw consent (opt-out)
- ✓ Data processing lawful basis
- ✓ Privacy policy provided

**CAN-SPAM Act** (if SMS contains marketing):

- ✓ Clear sender identification
- ✓ Opt-out mechanism
- ✓ Honor opt-outs within 10 business days

## Best Practices

**Message Content**:

- Keep under 160 characters when possible
- Personalize with recipient's name
- Include clear call-to-action
- Use URL shorteners for links
- Test messages on different devices

**Timing**:

- Best send times: 10 AM - 8 PM
- Avoid early morning (<8 AM) and late evening (>9 PM)
- Consider recipient's timezone
- Avoid weekends for business SMS

**Frequency**:

- Max 4-6 marketing messages per month
- Transactional messages: As needed
- Monitor opt-out rates (>5% is concerning)

**Engagement**:

- Track delivery and response rates
- A/B test message variations
- Segment audiences for targeting
- Follow up on responses promptly

## Error Handling

**No Opt-In Consent**:

```
❌ BLOCKED: No Opt-In Consent

This number has not opted in to receive SMS.
Sending without consent violates TCPA regulations.

Options:
1. Request opt-in first
2. Remove from send list
3. Verify consent manually
```

**Number on DNC List**:

```
❌ BLOCKED: Do-Not-Contact List

This number is on your DNC list.

Reason: [User requested no contact on [date]]
Added by: [User name]

Cannot send SMS to this number.
```

**Invalid Phone Number**:

- Show formatting error
- Suggest correct format
- Offer to lookup in CRM

**API Error**:

- Display clear error message
- Offer retry
- Save draft automatically
- Log error for troubleshooting

## Notes

- **IMPORTANT**: This command currently simulates Zoho SMS API. Actual integration will be added in Phase 4.
- **LEGAL**: SMS opt-in consent is LEGALLY REQUIRED. Never bypass this check.
- All SMS sends are logged for compliance and audit
- Opt-out requests are processed automatically
- Cost estimates are approximate

## Example Usage

```
/send-sms +12345678900 "Hi John, your order shipped! Track: bit.ly/abc123"
# Quick SMS send

/send-sms +12345678900 appointment-reminder
# Use template

/send-sms
# Interactive mode - guided SMS composition
```
