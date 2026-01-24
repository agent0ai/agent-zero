---
description: Create outreach request for qualified leads with human approval workflow
argument-hint: [lead-contact-id] --template [template-id]
allowed-tools: [Bash, Read, Write]
---

# Create Outreach Request

Create a personalized outreach message for a qualified lead with human approval required.

## Usage

```bash
/leads/outreach [lead-contact-id] --template [template-id]
```

## Arguments

- `lead-contact-id`: The UUID of the lead contact to reach out to (required)
- `--template`: Message template ID to use (required)

## Implementation Steps

1. Validate lead contact exists and is qualified (score >= 60)
2. Load message template for platform type
3. Run AI personalization to generate custom intro
4. Run compliance checks (TCPA, quiet hours, rate limits, opt-in status)
5. Create approval request with message preview
6. Wait for human approval via WebSocket
7. If approved, send message via platform API
8. Track response and update lead status

## Compliance Checks

Before creating outreach, the system verifies:

✅ **TCPA Consent**: Lead has implied or explicit consent
✅ **Opt-Out Status**: Lead has not opted out
✅ **Quiet Hours**: Current time is between 8 AM - 9 PM (recipient timezone)
✅ **Rate Limits**: Platform rate limits not exceeded
✅ **Platform TOS**: Message complies with platform policies

## Example Output

```
📤 Creating outreach request...

Lead: John Smith (@johnsmith on Reddit)
Score: 85/100 (Grade: A)
Platform: Reddit DM
Project Scope: Medium ($5k-$10k)

🤖 Generating personalized message...
✅ Personalization complete (confidence: 85%)

🔒 Running compliance checks...
  ✅ TCPA Consent: implied_consent (public forum)
  ✅ Opt-Out Status: active
  ✅ Quiet Hours: 2:45 PM EST (within 8 AM - 9 PM)
  ✅ Rate Limits: 3/10 messages in past hour
  ✅ Platform TOS: compliant

📋 Message Preview:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subject: Re: Looking for help with React authentication

Hi John,

I noticed your question about JWT refresh tokens in
React. The race condition you mentioned with concurrent
requests is a common challenge.

I'd be happy to help with your authentication flow if
you're still working on this. Feel free to DM me if
you'd like to discuss further.

Best regards
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔔 Approval Required
Approval request created: #12345

⏳ Waiting for approval decision...
   • Approve to send message
   • Reject to cancel outreach

[User approves via UI]

✅ Approval received! Sending message...
📨 Message sent successfully (Message ID: abc123)

📊 Updated lead status: contacted
```

## Notes

- All outreach requires human approval (TCPA compliance)
- Messages are personalized using Claude AI
- Compliance checks prevent TCPA violations
- Response tracking is automatic via response-monitoring-service
- Opt-outs are detected and processed immediately
