# 🚀 Email Integration Quick Start Guide

Choose your setup path based on your needs:

---

## Option 1: Basic Email (Phase 1) - 2 Minutes ⚡

**Best for:** Simple sending, getting started quickly

### Setup Steps

1. **Get Gmail App Password**

   ```
   → Go to https://myaccount.google.com/security
   → Enable 2-Factor Authentication
   → Create app password for "Mail"
   → Copy 16-character password
   ```

2. **Configure Environment**

   ```bash
   # Add to .env file
   GMAIL_FROM_EMAIL="your-email@gmail.com"
   GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
   ```

3. **Test**

   ```bash
   python3 -m pytest tests/test_email_standalone.py -v
   ```

**You're done!** Use the `email` tool with actions: `send`, `read`, `search`, `bulk_send`

**Limitations:**

- Single Gmail account only
- 500 emails/day (personal Gmail)
- Basic organization only

---

## Option 2: Multi-Account + Labels (Phase 2) - 10 Minutes 🏢

**Best for:** Multiple departments, email organization, drafts

### Prerequisites

- Phase 1 setup complete
- Google Cloud account

### Setup Steps

1. **Create Google Cloud Project**

   ```
   → Go to https://console.cloud.google.com
   → Create new project "email-automation"
   → Note the Project ID
   ```

2. **Enable Gmail API**

   ```
   → In Google Cloud Console
   → Navigate to "APIs & Services" > "Library"
   → Search "Gmail API"
   → Click "Enable"
   ```

3. **Create OAuth2 Credentials**

   ```
   → Go to "APIs & Services" > "Credentials"
   → Click "Create Credentials" > "OAuth 2.0 Client ID"
   → Application type: "Desktop app"
   → Download credentials.json
   → Save to project root: agent-jumbo/credentials.json
   ```

4. **Install Dependencies**

   ```bash
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```

5. **Authenticate First Account**

   ```python
   # Agent Jumbo will guide you through OAuth2 flow
   {
     "tool": "email_advanced",
     "args": {
       "action": "authenticate",
       "account_name": "sales"
     }
   }
   ```

   - Browser will open automatically
   - Sign in with <sales@company.com>
   - Grant permissions
   - Token saved to `data/gmail_credentials/token_sales.pickle`

6. **Test**

   ```python
   {
     "tool": "email_advanced",
     "args": {
       "action": "send_gmail",
       "account_name": "sales",
       "to": "test@example.com",
       "subject": "Test from Gmail API",
       "body": "This is a test email",
       "labels": ["test"]
     }
   }
   ```

**You're done!** Now you can:

- ✅ Use multiple accounts (sales@, support@, dev@)
- ✅ Organize with labels
- ✅ Create drafts for review
- ✅ Advanced search (8+ filters)
- ✅ 2,000 emails/day per account

---

## Option 3: Real-Time Notifications (Phase 3) - 15 Minutes ⚡🔔

**Best for:** Support tickets, instant responses, webhooks

### Prerequisites

- Phase 2 setup complete
- Google Cloud project from Phase 2

### Setup Steps

1. **Enable Pub/Sub API**

   ```
   → In Google Cloud Console
   → Navigate to "APIs & Services" > "Library"
   → Search "Cloud Pub/Sub API"
   → Click "Enable"
   ```

2. **Create Service Account**

   ```
   → Go to "IAM & Admin" > "Service Accounts"
   → Click "Create Service Account"
   → Name: "gmail-pubsub"
   → Grant role: "Pub/Sub Admin"
   → Click "Create Key" > JSON
   → Download and save to: agent-jumbo/service-account.json
   ```

3. **Set Environment Variable**

   ```bash
   # Add to .env file
   GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"
   ```

4. **Install Dependency**

   ```bash
   pip install google-cloud-pubsub
   ```

5. **Enable Push Notifications**

   ```python
   {
     "tool": "email_advanced",
     "args": {
       "action": "enable_push",
       "account_name": "support",
       "project_id": "email-automation",
       "topic_name": "support-emails"
     }
   }
   ```

6. **Register Callback (Optional)**

   ```python
   # In your custom code
   from python.helpers.gmail_push_notifications import GmailPushNotifications

   push = GmailPushNotifications(
       project_id="email-automation",
       topic_name="support-emails"
   )

   def handle_new_email(notification):
       print(f"New email! History ID: {notification['historyId']}")
       # Create support ticket, send auto-reply, etc.

   push.register_message_handler(handle_new_email)
   await push.start_listening()
   ```

**You're done!** Now you can:

- ✅ Get instant notifications (<2 seconds)
- ✅ Trigger automated workflows
- ✅ Create support tickets instantly
- ✅ Webhook integrations

---

## 📋 Quick Reference

### Phase 1: Basic Email Tool

```python
# Send email
{
  "tool": "email",
  "args": {
    "action": "send",
    "to": "customer@example.com",
    "subject": "Welcome!",
    "body": "Welcome to our platform",
    "attachments": ["/path/to/file.pdf"]
  }
}

# Read emails
{
  "tool": "email",
  "args": {
    "action": "read",
    "folder": "INBOX",
    "limit": 10,
    "unread_only": true
  }
}
```

### Phase 2: Advanced Email Tool

```python
# Send with labels
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "sales",
    "to": "customer@example.com",
    "subject": "Proposal",
    "body": "Please review attached proposal",
    "labels": ["proposal", "Q1-2025"],
    "attachments": ["/path/to/proposal.pdf"]
  }
}

# Create draft for review
{
  "tool": "email_advanced",
  "args": {
    "action": "create_draft",
    "account_name": "sales",
    "to": "bigcustomer@enterprise.com",
    "subject": "Enterprise Proposal",
    "body": "Proposal details...",
    "attachments": ["/path/to/proposal.pdf"]
  }
}

# Search with filters
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "support",
    "sender": "customer@example.com",
    "after": "2025/01/01",
    "has_attachment": true,
    "label": "urgent"
  }
}
```

### Phase 3: Push Notifications

```python
# Enable notifications
{
  "tool": "email_advanced",
  "args": {
    "action": "enable_push",
    "account_name": "support",
    "project_id": "company-support",
    "topic_name": "support-emails"
  }
}

# Disable notifications
{
  "tool": "email_advanced",
  "args": {
    "action": "disable_push",
    "account_name": "support"
  }
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Sales Team (Phase 2)

```python
# 1. Authenticate sales account
email_advanced.authenticate("sales")

# 2. Send proposal with label
email_advanced.send_gmail(
    account_name="sales",
    to="customer@example.com",
    subject="Your Custom Proposal",
    labels=["proposal", "high-value"],
    attachments=["proposal.pdf"]
)

# 3. Create follow-up draft
email_advanced.create_draft(
    account_name="sales",
    to="customer@example.com",
    subject="Follow-up: Proposal Review"
)
```

### Use Case 2: Support Team (Phase 3)

```python
# 1. Authenticate support account
email_advanced.authenticate("support")

# 2. Enable instant notifications
email_advanced.enable_push(
    account_name="support",
    project_id="company-support",
    topic_name="support-tickets"
)

# 3. Callback will trigger when customer emails
# → Create ticket in <2 seconds
# → Send auto-reply
# → Notify team
```

### Use Case 3: Multi-Department (Phase 2)

```python
# Authenticate all departments
email_advanced.authenticate("sales")
email_advanced.authenticate("support")
email_advanced.authenticate("dev")

# Each department gets 2,000 emails/day = 6,000 total
# Each has independent labels and organization
# Each can have separate push notifications
```

---

## 🔧 Troubleshooting

### Phase 1 Issues

**"Authentication failed"**

- Check Gmail app password is correct (16 chars)
- Verify 2FA enabled on Gmail account
- Check environment variables loaded

**"Connection refused"**

- Verify internet connection
- Check firewall allows SMTP (port 587)
- Ensure Gmail not blocking "less secure apps"

### Phase 2 Issues

**"OAuth2 credentials not found"**

- Ensure `credentials.json` in project root
- Download from Google Cloud Console
- Check file permissions (should be readable)

**"Invalid grant"**

- Delete token file: `data/gmail_credentials/token_*.pickle`
- Re-authenticate: `email_advanced.authenticate(...)`

**"API not enabled"**

- Go to Google Cloud Console
- Enable Gmail API in "APIs & Services"

### Phase 3 Issues

**"Pub/Sub permission denied"**

- Check service account has "Pub/Sub Admin" role
- Verify `GOOGLE_APPLICATION_CREDENTIALS` set correctly
- Ensure service account key downloaded

**"Watch expired"**

- Gmail watch expires after 7 days
- Re-enable: `email_advanced.enable_push(...)`
- Consider auto-renewal in production

---

## 📚 Full Documentation

- **Overview:** `docs/EMAIL_COMPLETE.md`
- **Implementation Details:** `docs/IMPLEMENTATION_SUMMARY.md`
- **Phase 1 Guide:** `docs/EMAIL_INTEGRATION_PHASE1.md`
- **Phase 2/3 Guide:** `docs/GMAIL_API_PHASE2_PHASE3.md`
- **Quick Reference:** `docs/EMAIL_QUICK_REFERENCE.md`

---

## ✅ Next Steps

1. **Choose your phase** based on requirements
2. **Follow setup steps** above
3. **Test with sample email**
4. **Integrate with your workflows**
5. **Monitor and optimize**

**Questions?** See full documentation or check troubleshooting section.

---

**Last Updated:** January 2025
**Status:** ✅ All phases production ready
